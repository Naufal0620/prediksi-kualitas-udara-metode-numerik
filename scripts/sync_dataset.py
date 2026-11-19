"""
Script Sinkronisasi Dataset Multi-Kota: PM2.5 + Cuaca + Hotspot Count
Menghasilkan master_dataset_<city_key>.csv siap latih untuk Machine Learning
"""

import os
import pandas as pd
import numpy as np
from config_cities import CITIES

def sync_city_data(city_key):
    if city_key not in CITIES:
        print(f"[!] Kota '{city_key}' tidak ditemukan.")
        return None

    cfg = CITIES[city_key]
    base_dir = os.path.dirname(__file__)

    pm25_path = os.path.join(base_dir, '..', 'data', 'raw', 'air_quality', f'pm25_{city_key}_hourly.csv')
    weather_path = os.path.join(base_dir, '..', 'data', 'raw', 'weather', f'weather_{city_key}_hourly.csv')
    hotspots_path = os.path.join(base_dir, '..', 'data', 'raw', 'hotspots', f'hotspots_{city_key}_2025.csv')

    print(f"\n[*] Melakukan sinkronisasi data untuk {cfg['name']}...")

    if not os.path.exists(pm25_path):
        print(f"[!] File PM2.5 belum ada: {pm25_path}")
        return None
    if not os.path.exists(weather_path):
        print(f"[!] File Cuaca belum ada: {weather_path}")
        return None
    if not os.path.exists(hotspots_path):
        print(f"[!] File Hotspot belum ada: {hotspots_path}")
        return None

    df_pm25 = pd.read_csv(pm25_path)
    df_weather = pd.read_csv(weather_path)
    df_hotspots = pd.read_csv(hotspots_path)

    # 1. Standarisasi Timestamp tanpa timezone offset (UTC+7 konsisten)
    df_pm25['timestamp'] = pd.to_datetime(df_pm25['timestamp']).dt.tz_localize(None).dt.floor('h')
    df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp']).dt.tz_localize(None).dt.floor('h')
    df_hotspots['timestamp'] = pd.to_datetime(df_hotspots['timestamp']).dt.tz_localize(None).dt.floor('h')

    df_pm25 = df_pm25.drop_duplicates(subset=['timestamp'])
    df_weather = df_weather.drop_duplicates(subset=['timestamp'])

    # 2. Agregasi Hotspot per Jam
    hotspot_hourly = df_hotspots.groupby('timestamp').size().reset_index(name='hotspot_count')

    # 3. Penggabungan Data (Inner Join PM2.5 & Cuaca, Left Join Hotspot)
    df_merged = pd.merge(df_pm25, df_weather, on='timestamp', how='inner')
    df_merged = pd.merge(df_merged, hotspot_hourly, on='timestamp', how='left')
    df_merged['hotspot_count'] = df_merged['hotspot_count'].fillna(0).astype(int)

    # Urutkan secara kronologis
    df_merged = df_merged.sort_values('timestamp').reset_index(drop=True)

    # 4. Interpolasi Linear untuk Nilai Kosong Pendek (Proposal Bab 1.4 butir 6)
    numeric_cols = ['pm25', 'temperature_2m', 'relative_humidity_2m', 'precipitation', 'wind_speed_10m', 'wind_direction_10m']
    df_merged[numeric_cols] = df_merged[numeric_cols].interpolate(method='linear', limit_direction='both')

    # 5. Simpan Hasil ke data/processed/master_dataset_<city>.csv
    output_dir = os.path.join(base_dir, '..', 'data', 'processed')
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"master_dataset_{city_key}.csv")

    df_merged.to_csv(out_file, index=False)
    print(f"[✓✓✓] Selesai sinkronisasi {cfg['name']}!")
    print(f"[✓] Berkas: {os.path.basename(out_file)} | Baris siap latih: {len(df_merged):,} jam")
    print(f"[✓] Rentang: {df_merged['timestamp'].min()} s/d {df_merged['timestamp'].max()}")
    return df_merged

def main():
    for city_key in CITIES.keys():
        sync_city_data(city_key)

if __name__ == "__main__":
    main()
