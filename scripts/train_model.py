"""
Script Pelatihan Model Machine Learning: Random Forest Regressor Multi-Stasiun
Menerapkan Chronological Split: 90% Data Latih & 10% Data Uji
Evaluasi Metrik:
  - MAE  (Mean Absolute Error dalam µg/m³)
  - RMSE (Root Mean Squared Error dalam µg/m³)
  - MAPE (Mean Absolute Percentage Error dalam %)
  - Accuracy Percentage (100% - MAPE)
Ekspor: models/rf_model_<city>.joblib dan models/meta_<city>.json
Laporan: Development/MODEL_EVALUATION.md
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

    # Chronological Split (90% Train, 10% Test)
    split_idx = int(len(X) * 0.9)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"[*] Total Baris Fitur : {len(X):,} jam")
    print(f"[*] Data Latih (90%)  : {len(X_train):,} jam (Kronologis Awal)")
    print(f"[*] Data Uji   (10%)  : {len(X_test):,} jam (Kronologis Akhir)")

    # Konfigurasi Random Forest Regressor
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Prediksi Data Uji
    y_pred = model.predict(X_test)

    # Evaluasi Metrik Absolut
    mae = mean_absolute_error(y_test, y_pred)
    rmse = root_mean_squared_error(y_test, y_pred)

    # Evaluasi Persentase Error (MAPE & Akurasi)
    # Hindari pembagian dengan nol dengan memfilter data PM2.5 > 0.5 µg/m³
    valid_mask = y_test > 0.5
    if np.sum(valid_mask) > 0:
        mape = float(np.mean(np.abs((y_test[valid_mask] - y_pred[valid_mask]) / y_test[valid_mask])) * 100.0)
    else:
        mape = float(np.mean(np.abs(y_test - y_pred) / (y_test + 1.0)) * 100.0)

    accuracy_pct = max(0.0, 100.0 - mape)

    print(f"\n[HASIL EVALUASI ERROR DATA UJI (10% KRONOLOGIS AKHIR)]:")
    print(f"  • MAE (Mean Absolute Error)      : {mae:.2f} µg/m³")
    print(f"  • RMSE (Root Mean Squared Error) : {rmse:.2f} µg/m³")
    print(f"  • MAPE (Persentase Error Rerata) : {mape:.2f}%")
    print(f"  • Akurasi Prediksi Model         : {accuracy_pct:.2f}%")

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
        "metrics": {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape_percent": round(mape, 2),
            "accuracy_percent": round(accuracy_pct, 2)
        },
        "total_samples": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "split_ratio": "90% Train / 10% Test (Chronological)",
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

    # Rekap ke Development/MODEL_EVALUATION.md
    rekap_path = os.path.join(os.path.dirname(__file__), '..', 'Development', 'MODEL_EVALUATION.md')
    with open(rekap_path, 'w', encoding='utf-8') as f:
        f.write("# 📊 Laporan Hasil Evaluasi Pelatihan Model Random Forest\n\n")
        f.write("Evaluasi menggunakan metode **Chronological Split (90% Data Latih, 10% Data Uji)** sesuai urutan waktu deret historis.\n\n")
        f.write("### 📌 Definisi Metrik:\n")
        f.write("- **MAE (*Mean Absolute Error*)**: Rata-rata selisih absolut antara nilai prediksi dan aktual fisik (dalam satuan $\\mu g/m^3$).\n")
        f.write("- **RMSE (*Root Mean Squared Error*)**: Akar rata-rata kuadrat error, memberi penalti lebih besar pada lonjakan polusi ekstrem (dalam $\\mu g/m^3$).\n")
        f.write("- **MAPE (*Mean Absolute Percentage Error*)**: **Persentase error rata-rata model** relatif terhadap konsentrasi aktual (%). Semakin kecil nilainya, semakin akurat.\n")
        f.write("- **Akurasi (%)**: Tingkat akurasi prediksi model ($100\\% - \\text{MAPE}$).\n\n")
        f.write("### 📈 Tabel Evaluasi Seluruh Stasiun:\n\n")
        f.write("| No | Wilayah & Stasiun | Total Data | Latih (90%) | Uji (10%) | MAE (µg/m³) | RMSE (µg/m³) | **Persentase Error (MAPE)** | **Akurasi Prediksi** |\n")
        f.write("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        for idx, res in enumerate(results, 1):
            m = res['metrics']
            f.write(f"| {idx} | **{res['station_name']}** | {res['total_samples']:,} | {res['train_samples']:,} | {res['test_samples']:,} | {m['mae']} | {m['rmse']} | **{m['mape_percent']}%** | **{m['accuracy_percent']}%** |\n")
        f.write("\n> *Catatan: Model dilatih pada data historis awal dan diuji murni pada data masa depan (10% kronologis akhir) tanpa data leakage.*\n")

    print(f"\n[✓✓✓] Seluruh model berhasil dilatih dengan rasio 90:10!")
    print(f"[✓] Laporan lengkap tersimpan di: {os.path.abspath(rekap_path)}")

if __name__ == "__main__":
    main()
