"""
Server REST API Web GIS: Prediksi PM2.5 & Mesin Metode Numerik
Menyediakan Endpoint untuk UI/UX Frontend:
- GET  /api/health
- GET  /api/stations
- GET  /api/predict/<city_key>
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
CORS(app)  # Memungkinkan diakses oleh frontend mana pun (React, Vue, Vite, atau HTML statis)

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, '..', 'models')
PROCESSED_DIR = os.path.join(BASE_DIR, '..', 'data', 'processed')
RAW_DIR = os.path.join(BASE_DIR, '..', 'data', 'raw')

# Cache model dalam memori server agar inferensi berkecepatan tinggi (< 0.05 detik)
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
        "service": "PM2.5 Numerical & Predictive Web GIS API",
        "supported_stations": len(CITIES)
    })

@app.route('/api/stations', methods=['GET'])
def get_stations():
    """Mengembalikan daftar seluruh stasiun pemantau yang didukung sistem"""
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
    """Mengembalikan titik-titik api satelit NASA FIRMS di sekitar stasiun"""
    if city_key not in CITIES:
        return jsonify({"error": f"Stasiun '{city_key}' tidak ditemukan."}), 404

    hotspot_file = os.path.join(RAW_DIR, 'hotspots', f"hotspots_{city_key}_2025.csv")
    if not os.path.exists(hotspot_file):
        return jsonify({"city": city_key, "total": 0, "hotspots": []})

    df = pd.read_csv(hotspot_file)
    # Batasi ke 100 titik terbaru untuk efisiensi transfer data UI
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
    Endpoint Utama:
    1. Ambil prakiraan cuaca 24 jam ke depan dari Open-Meteo Forecast API
    2. Prediksi 24 titik PM2.5 menggunakan Random Forest
    3. Hitung Moving Average 24 Jam (PP 22/2021)
    4. Curve Fitting Polinomial Orde 3
    5. Metode Secant untuk deteksi waktu pelampauan 55 µg/m³
    """
    if city_key not in CITIES:
        return jsonify({"error": f"Stasiun '{city_key}' tidak ditemukan."}), 404

    cfg = CITIES[city_key]
    model = get_model(city_key)
    if not model:
        return jsonify({"error": f"Model untuk '{city_key}' belum dilatih."}), 500

    # 1. Ambil Data Historis Terakhir untuk Lag PM2.5
    processed_file = os.path.join(PROCESSED_DIR, f"master_dataset_{city_key}.csv")
    if not os.path.exists(processed_file):
        return jsonify({"error": "Dataset historis tidak ditemukan."}), 500

    df_hist = pd.read_csv(processed_file)
    last_pm25_series = df_hist['pm25'].values[-24:].tolist()
    last_timestamp = pd.to_datetime(df_hist['timestamp'].iloc[-1])

    # 2. Ambil Prakiraan Cuaca 24 Jam ke Depan (Open-Meteo Forecast)
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": cfg["latitude"],
        "longitude": cfg["longitude"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "wind_direction_10m"],
        "forecast_days": 2,
        "timezone": cfg.get("timezone", "Asia/Jakarta")
    }

    try:
        res = requests.get(forecast_url, params=params, timeout=10)
        weather_forecast = res.json().get("hourly", {})
    except Exception as e:
        weather_forecast = {}

    # Jika API forecast gagal, gunakan pola cuaca rata-rata historis (fallback robust)
    fallback_temp = df_hist['temperature_2m'].mean()
    fallback_rh = df_hist['relative_humidity_2m'].mean()
    fallback_precip = 0.0
    fallback_ws = df_hist['wind_speed_10m'].mean()
    fallback_wd = df_hist['wind_direction_10m'].mean()

    # 3. Prediksi Multi-Step Autoregressive (t = 1 .. 24 jam)
    predictions_24h = []
    future_timestamps = []
    current_lags = list(last_pm25_series)  # 24 nilai terakhir

    start_future_time = pd.Timestamp.now().floor('h') + pd.Timedelta(hours=1)

    for h in range(24):
        step_time = start_future_time + pd.Timedelta(hours=h)
        future_timestamps.append(step_time.strftime('%Y-%m-%d %H:00'))

        # Nilai fitur
        pm25_lag1 = current_lags[-1]
        pm25_lag2 = current_lags[-2] if len(current_lags) >= 2 else pm25_lag1
        pm25_lag24 = current_lags[-24] if len(current_lags) >= 24 else pm25_lag1

        temp = weather_forecast.get("temperature_2m", [fallback_temp])[h] if h < len(weather_forecast.get("temperature_2m", [])) else fallback_temp
        rh = weather_forecast.get("relative_humidity_2m", [fallback_rh])[h] if h < len(weather_forecast.get("relative_humidity_2m", [])) else fallback_rh
        precip = weather_forecast.get("precipitation", [fallback_precip])[h] if h < len(weather_forecast.get("precipitation", [])) else fallback_precip
        ws = weather_forecast.get("wind_speed_10m", [fallback_ws])[h] if h < len(weather_forecast.get("wind_speed_10m", [])) else fallback_ws
        wd = weather_forecast.get("wind_direction_10m", [fallback_wd])[h] if h < len(weather_forecast.get("wind_direction_10m", [])) else fallback_wd

        feature_df = pd.DataFrame([{
            'pm25_lag1': pm25_lag1,
            'pm25_lag2': pm25_lag2,
            'pm25_lag24': pm25_lag24,
            'hour': step_time.hour,
            'day_of_week': step_time.dayofweek,
            'temperature_2m': temp,
            'relative_humidity_2m': rh,
            'precipitation': precip,
            'wind_speed_10m': ws,
            'wind_direction_10m': wd,
            'hotspot_count': 0
        }])

        pred_val = float(model.predict(feature_df)[0])
        pred_val = max(0.0, pred_val)  # Tidak boleh bernilai negatif
        predictions_24h.append(round(pred_val, 2))
        current_lags.append(pred_val)

    # 4. Integrasi Metode Numerik: Moving Average 24 Jam
    ma24_points = compute_ma24(last_pm25_series, predictions_24h)

    # 5. Integrasi Metode Numerik: Curve Fitting Polinomial Orde 3
    x_hours = list(range(1, 25))
    poly_func, poly_coeffs = polynomial_curve_fitting(x_hours, ma24_points, degree=3)

    # Titik kurva mulus untuk grafik kontinu Chart.js (60 titik)
    curve_x = np.linspace(1, 24, 60).tolist()
    curve_y = [round(float(poly_func(x)), 2) for x in curve_x]

    # 6. Integrasi Metode Numerik: Metode Secant Pencari Akar (Baku Mutu 55 µg/m³)
    secant_result = secant_root_finding(poly_func, threshold=55.0)

    # Susun respons terpadu untuk UI/UX
    return jsonify({
        "station": {
            "key": city_key,
            "name": cfg["name"],
            "city": cfg["city"],
            "province": cfg["province"],
            "coordinates": {"latitude": cfg["latitude"], "longitude": cfg["longitude"]}
        },
        "forecast_hours": future_timestamps,
        "raw_predictions": predictions_24h,
        "ma24_discrete": [round(v, 2) for v in ma24_points],
        "polynomial_curve": {
            "degree": 3,
            "coefficients": poly_coeffs,
            "points_x": [round(x, 2) for x in curve_x],
            "points_y": curve_y
        },
        "air_quality_threshold": 55.0,
        "secant_analysis": secant_result,
        "generated_at": pd.Timestamp.now().isoformat()
    })

if __name__ == '__main__':
    # Default port 5000
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Menjalankan Server REST API Web GIS di port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
