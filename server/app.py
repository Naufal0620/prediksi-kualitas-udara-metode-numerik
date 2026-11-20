"""
Server REST API Web GIS: Prediksi PM2.5 & Mesin Metode Numerik (Versi Teroptimasi)
Mendukung:
- Prediksi Fleksibel: Horizon 24 Jam (Default) hingga 7 Hari (168 Jam) via query param ?days=7 atau ?hours=168
- Fitur Lanjut: Lags (t-1, t-2, t-3, t-24), Rolling Means (3h, 6h), Cyclic Hour Encoding (Sin/Cos), Temp-RH Interaction
- Metode Numerik: Moving Average 24 Jam (PP 22/2021), Curve Fitting Polinomial Orde 3/4, & Metode Secant
- REST API:
  - GET  /api/health
  - GET  /api/stations
  - GET  /api/predict/<city_key>?days=1|3|7
  - GET  /api/hotspots/<city_key>
"""

import os
import sys
import json
import requests
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib

# Impor konfigurasi kota dan mesin numerik (dengan fallback impor modular)
try:
    from config_cities import CITIES
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from config_cities import CITIES

try:
    from numerical_engine import compute_ma24, polynomial_curve_fitting, secant_root_finding
except ImportError:
    from server.numerical_engine import compute_ma24, polynomial_curve_fitting, secant_root_finding

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, '..', 'models')
PROCESSED_DIR = os.path.join(BASE_DIR, '..', 'data', 'processed')
RAW_DIR = os.path.join(BASE_DIR, '..', 'data', 'raw')

LOADED_MODELS = {}

def get_model(city_key):
    if city_key not in LOADED_MODELS:
        model_path = os.path.join(MODELS_DIR, f"rf_model_{city_key}.joblib")
        if os.path.exists(model_path):
            LOADED_MODELS[city_key] = joblib.load(model_path)
    return LOADED_MODELS.get(city_key)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "service": "PM2.5 Numerical & Predictive Web GIS API (Optimized Multi-Horizon)",
        "supported_stations": len(CITIES),
        "max_horizon_days": 7
    })

@app.route('/api/stations', methods=['GET'])
def get_stations():
    stations_list = []
    for key, cfg in CITIES.items():
        meta_path = os.path.join(MODELS_DIR, f"meta_{key}.json")
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                meta = json.load(f)

        stations_list.append({
            "key": key,
            "name": cfg["name"],
            "city": cfg["city"],
            "province": cfg["province"],
            "region_group": cfg.get("region_group", "Indonesia"),
            "coordinates": {
                "latitude": cfg["latitude"],
                "longitude": cfg["longitude"]
            },
            "hotspot_radius_km": cfg["hotspot_radius_km"],
            "metrics": meta.get("metrics", {})
        })
    return jsonify({"total": len(stations_list), "stations": stations_list})

@app.route('/api/hotspots/<city_key>', methods=['GET'])
def get_hotspots(city_key):
    if city_key not in CITIES:
        return jsonify({"error": f"Stasiun '{city_key}' tidak ditemukan."}), 404

    hotspot_file = os.path.join(RAW_DIR, 'hotspots', f"hotspots_{city_key}_2025.csv")
    if not os.path.exists(hotspot_file):
        return jsonify({"city": city_key, "total": 0, "hotspots": []})

    df = pd.read_csv(hotspot_file)
    df_sample = df.tail(100)
    hotspots = []
    for _, row in df_sample.iterrows():
        hotspots.append({
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "brightness": float(row.get("bright_ti4", 300)),
            "confidence": str(row.get("confidence", "nominal")),
            "timestamp": str(row.get("timestamp"))
        })

    return jsonify({
        "city": city_key,
        "station_name": CITIES[city_key]["name"],
        "total": len(hotspots),
        "hotspots": hotspots
    })

@app.route('/api/predict/<city_key>', methods=['GET'])
def predict_pm25(city_key):
    """
    Endpoint Prediksi Multi-Horizon:
    Query Params:
      - days: 1 .. 7 (default: 1 hari / 24 jam. Maksimal: 7 hari / 168 jam)
      - hours: 1 .. 168 (alternatif parameter jam)
    """
    if city_key not in CITIES:
        return jsonify({"error": f"Stasiun '{city_key}' tidak ditemukan."}), 404

    cfg = CITIES[city_key]
    model = get_model(city_key)
    if not model:
        return jsonify({"error": f"Model untuk '{city_key}' belum dilatih."}), 500

    # 1. Tentukan Horizon Prediksi (1 hari s.d. 7 hari)
    days_param = request.args.get('days', type=int)
    hours_param = request.args.get('hours', type=int)

    if hours_param:
        target_hours = min(max(hours_param, 12), 168)
    elif days_param:
        target_hours = min(max(days_param * 24, 24), 168)
    else:
        target_hours = 24  # Default 24 jam

    forecast_days_needed = int(np.ceil(target_hours / 24.0)) + 1

    # 2. Ambil Riwayat Lags Historis Terakhir
    processed_file = os.path.join(PROCESSED_DIR, f"master_dataset_{city_key}.csv")
    if not os.path.exists(processed_file):
        return jsonify({"error": "Dataset historis tidak ditemukan."}), 500

    df_hist = pd.read_csv(processed_file)
    last_pm25_series = df_hist['pm25'].values[-24:].tolist()

    # 3. Ambil Prakiraan Cuaca Open-Meteo Forecast (Hingga 7 Hari ke Depan)
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": cfg["latitude"],
        "longitude": cfg["longitude"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "wind_direction_10m"],
        "forecast_days": min(forecast_days_needed, 8),
        "timezone": cfg.get("timezone", "Asia/Jakarta")
    }

    try:
        res = requests.get(forecast_url, params=params, timeout=12)
        weather_forecast = res.json().get("hourly", {})
    except Exception:
        weather_forecast = {}

    fallback_temp = float(df_hist['temperature_2m'].mean())
    fallback_rh = float(df_hist['relative_humidity_2m'].mean())
    fallback_precip = 0.0
    fallback_ws = float(df_hist['wind_speed_10m'].mean())
    fallback_wd = float(df_hist['wind_direction_10m'].mean())

    # 4. Multi-Step Autoregressive Prediction dengan Advanced Features
    predictions = []
    future_timestamps = []
    current_history = list(last_pm25_series)

    start_future_time = pd.Timestamp.now().floor('h') + pd.Timedelta(hours=1)

    for h in range(target_hours):
        step_time = start_future_time + pd.Timedelta(hours=h)
        future_timestamps.append(step_time.strftime('%Y-%m-%d %H:00'))

        # Lags
        p_lag1 = current_history[-1]
        p_lag2 = current_history[-2] if len(current_history) >= 2 else p_lag1
        p_lag3 = current_history[-3] if len(current_history) >= 3 else p_lag2
        p_lag24 = current_history[-24] if len(current_history) >= 24 else current_history[0]

        # Rolling Momentum
        roll_3 = float(np.mean(current_history[-3:]))
        roll_6 = float(np.mean(current_history[-6:]))
        roll_std6 = float(np.std(current_history[-6:]))

        # Cyclic Waktu
        h_sin = np.sin(2 * np.pi * step_time.hour / 24.0)
        h_cos = np.cos(2 * np.pi * step_time.hour / 24.0)
        dow = step_time.dayofweek
        is_wknd = 1 if dow >= 5 else 0

        # Cuaca Jam ke-h
        t_list = weather_forecast.get("temperature_2m", [])
        rh_list = weather_forecast.get("relative_humidity_2m", [])
        p_list = weather_forecast.get("precipitation", [])
        ws_list = weather_forecast.get("wind_speed_10m", [])
        wd_list = weather_forecast.get("wind_direction_10m", [])

        temp = t_list[h] if h < len(t_list) else fallback_temp
        rh = rh_list[h] if h < len(rh_list) else fallback_rh
        precip = p_list[h] if h < len(p_list) else fallback_precip
        ws = ws_list[h] if h < len(ws_list) else fallback_ws
        wd = wd_list[h] if h < len(wd_list) else fallback_wd

        feature_df = pd.DataFrame([{
            'pm25_lag1': p_lag1,
            'pm25_lag2': p_lag2,
            'pm25_lag3': p_lag3,
            'pm25_lag24': p_lag24,
            'pm25_roll_mean3': roll_3,
            'pm25_roll_mean6': roll_6,
            'pm25_roll_std6': roll_std6,
            'hour_sin': h_sin,
            'hour_cos': h_cos,
            'day_of_week': dow,
            'is_weekend': is_wknd,
            'temperature_2m': temp,
            'relative_humidity_2m': rh,
            'temp_rh_interaction': temp * rh,
            'precipitation': precip,
            'wind_speed_10m': ws,
            'wind_direction_10m': wd,
            'hotspot_count': 0
        }])

        pred_val = float(model.predict(feature_df)[0])
        pred_val = max(0.5, pred_val)
        predictions.append(round(pred_val, 2))
        current_history.append(pred_val)

    # 5. Integrasi Metode Numerik: Moving Average 24 Jam
    combined_for_ma = list(last_pm25_series[-23:]) + list(predictions)
    ma24_points = []
    for i in range(len(predictions)):
        win = combined_for_ma[i : i + 24]
        ma24_points.append(round(float(np.mean(win)), 2))

    # 6. Curve Fitting Polinomial (Derajat 3 untuk <= 24 jam, Derajat 4 untuk horizon lebih panjang)
    x_hours = list(range(1, target_hours + 1))
    poly_deg = 3 if target_hours <= 24 else 4
    poly_func, poly_coeffs = polynomial_curve_fitting(x_hours, ma24_points, degree=poly_deg)

    # Titik kurva mulus untuk Chart.js (proporsional terhadap jam)
    num_curve_pts = min(120, target_hours * 3)
    curve_x = np.linspace(1, target_hours, num_curve_pts).tolist()
    curve_y = [round(float(poly_func(x)), 2) for x in curve_x]

    # 7. Metode Secant (Pencarian Akar Pelampauan Baku Mutu 55 µg/m³)
    secant_result = secant_root_finding(poly_func, threshold=55.0, x0=1.0, x1=min(2.0, float(target_hours)))

    return jsonify({
        "station": {
            "key": city_key,
            "name": cfg["name"],
            "city": cfg["city"],
            "province": cfg["province"],
            "coordinates": {"latitude": cfg["latitude"], "longitude": cfg["longitude"]}
        },
        "forecast_horizon": {
            "hours": target_hours,
            "days": round(target_hours / 24.0, 1),
            "start_time": future_timestamps[0],
            "end_time": future_timestamps[-1]
        },
        "forecast_hours": future_timestamps,
        "raw_predictions": predictions,
        "ma24_discrete": ma24_points,
        "polynomial_curve": {
            "degree": poly_deg,
            "coefficients": poly_coeffs,
            "points_x": [round(x, 2) for x in curve_x],
            "points_y": curve_y
        },
        "air_quality_threshold": 55.0,
        "secant_analysis": secant_result,
        "generated_at": pd.Timestamp.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Server REST API Aktif di port {port} (Mendukung Peramalan hingga 7 Hari)...")
    app.run(host='0.0.0.0', port=port, debug=True)
