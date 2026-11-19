"""
Script Pelatihan Model Machine Learning: Random Forest Regressor Multi-Stasiun
Menerapkan Chronological Split (80:20) sesuai batasan proposal Bab 1.4 butir 11
Evaluasi: Mean Absolute Error (MAE) & Root Mean Square Error (RMSE)
Ekspor: models/rf_model_<city>.joblib
"""

import os
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
import joblib
from config_cities import CITIES

def build_features(df):
    """
    Membangun fitur lag dan fitur waktu untuk deret waktu PM2.5
    """
    df_feat = df.copy()
    df_feat['timestamp'] = pd.to_datetime(df_feat['timestamp'])
    df_feat = df_feat.sort_values('timestamp').reset_index(drop=True)

    # 1. Temporal / Cyclic features
    df_feat['hour'] = df_feat['timestamp'].dt.hour
    df_feat['day_of_week'] = df_feat['timestamp'].dt.dayofweek

    # 2. Lagged PM2.5 features
    df_feat['pm25_lag1'] = df_feat['pm25'].shift(1)
    df_feat['pm25_lag2'] = df_feat['pm25'].shift(2)
    df_feat['pm25_lag24'] = df_feat['pm25'].shift(24)

    # 3. Hapus baris awal yang bernilai NaN akibat shift
    df_feat = df_feat.dropna().reset_index(drop=True)

    feature_cols = [
        'pm25_lag1', 'pm25_lag2', 'pm25_lag24',
        'hour', 'day_of_week',
        'temperature_2m', 'relative_humidity_2m', 'precipitation',
        'wind_speed_10m', 'wind_direction_10m',
        'hotspot_count'
    ]

    X = df_feat[feature_cols]
    y = df_feat['pm25']
    timestamps = df_feat['timestamp']

    return X, y, timestamps, feature_cols

def train_city_model(city_key):
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, '..', 'data', 'processed', f'master_dataset_{city_key}.csv')

    if not os.path.exists(data_path):
        print(f"[!] File dataset {data_path} tidak ditemukan.")
        return None

    cfg = CITIES[city_key]
    print(f"\n=======================================================")
    print(f"[*] Melatih Model Random Forest untuk: {cfg['name']}")
    print(f"=======================================================")

    df = pd.read_csv(data_path)
    X, y, timestamps, feature_cols = build_features(df)

    # Chronological Split (80% Train, 20% Test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"[*] Total Baris Fitur : {len(X):,} jam")
    print(f"[*] Data Latih (80%)  : {len(X_train):,} jam (Kronologis Awal)")
    print(f"[*] Data Uji   (20%)  : {len(X_test):,} jam (Kronologis Akhir)")

    # Konfigurasi Random Forest Regressor
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Prediksi & Evaluasi Data Uji
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = root_mean_squared_error(y_test, y_pred)

    print(f"\n[HASIL EVALUASI METRIK PENGUJIAN]:")
    print(f"  • MAE  (Mean Absolute Error)     : {mae:.2f} µg/m³")
    print(f"  • RMSE (Root Mean Squared Error) : {rmse:.2f} µg/m³")

    # Simpan Model & Metadata Fitur
    models_dir = os.path.join(base_dir, '..', 'models')
    os.makedirs(models_dir, exist_ok=True)

    model_filename = f"rf_model_{city_key}.joblib"
    meta_filename = f"meta_{city_key}.json"

    model_save_path = os.path.join(models_dir, model_filename)
    meta_save_path = os.path.join(models_dir, meta_filename)

    joblib.dump(model, model_save_path)

    metadata = {
        "city_key": city_key,
        "station_name": cfg["name"],
        "coordinates": {"latitude": cfg["latitude"], "longitude": cfg["longitude"]},
        "features": feature_cols,
        "metrics": {"mae": round(mae, 2), "rmse": round(rmse, 2)},
        "total_samples": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "trained_at": pd.Timestamp.now().isoformat()
    }

    with open(meta_save_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"[✓] Model serial tersimpan -> {model_filename}")
    return metadata

def main():
    results = []
    for city_key in CITIES.keys():
        meta = train_city_model(city_key)
        if meta:
            results.append(meta)

    # Rekap ke Development
    rekap_path = os.path.join(os.path.dirname(__file__), '..', 'Development', 'MODEL_EVALUATION.md')
    with open(rekap_path, 'w', encoding='utf-8') as f:
        f.write("# Laporan Hasil Evaluasi Pelatihan Model Random Forest\n\n")
        f.write("Evaluasi menggunakan metode **Chronological Split (80% Train, 20% Test)** sesuai batasan proposal Bab 1.4 butir 11.\n\n")
        f.write("| No | Wilayah & Stasiun | Total Data | MAE (µg/m³) | RMSE (µg/m³) | Model File |\n")
        f.write("|:---:|:---|:---:|:---:|:---:|:---|\n")
        for idx, res in enumerate(results, 1):
            f.write(f"| {idx} | **{res['station_name']}** | {res['total_samples']:,} | **{res['metrics']['mae']}** | **{res['metrics']['rmse']}** | `rf_model_{res['city_key']}.joblib` |\n")
        f.write("\n> *Catatan: Nilai MAE dan RMSE yang rendah menunjukkan model mampu menangkap fluktuasi polusi dengan presisi tinggi.*\n")

    print(f"\n[✓✓✓] Seluruh model berhasil dilatih! Rekap metrik tersimpan di Development/MODEL_EVALUATION.md")

if __name__ == "__main__":
    main()
