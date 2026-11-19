"""
Script Filter Titik Api NASA FIRMS Berdasarkan Radius Stasiun Kota-Kota Besar
Menggunakan formula Haversine untuk geofencing per kota
"""

import os
import pandas as pd
import numpy as np
from config_cities import CITIES

def haversine_distance(lat1, lon1, lat2, lon2):
    """Menghitung jarak geosfer (km) antara titik stasiun dan titik api"""
    r = 6371.0  # radius bumi km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return r * c

def filter_hotspots_for_cities():
    base_dir = os.path.dirname(__file__)
    master_firms = os.path.join(base_dir, '..', 'data', 'raw', 'hotspots', 'viirs-jpss1_2025_Indonesia.csv')

    if not os.path.exists(master_firms):
        print(f"[!] File master FIRMS tidak ditemukan: {master_firms}")
        return

    print(f"[*] Membaca berkas master titik api VIIRS Indonesia (94.000+ baris)...")
    df_raw = pd.read_csv(master_firms)

    # 1. Standarisasi Timestamp UTC -> WIB (UTC+7)
    print("[*] Melakukan parsing waktu satelit ke WIB (UTC+7)...")
    df_raw['acq_time_str'] = df_raw['acq_time'].astype(str).str.zfill(4)
    df_raw['datetime_utc'] = pd.to_datetime(
        df_raw['acq_date'] + ' ' + df_raw['acq_time_str'],
        format='%Y-%m-%d %H%M'
    )
    df_raw['timestamp'] = df_raw['datetime_utc'] + pd.Timedelta(hours=7)

    output_dir = os.path.join(base_dir, '..', 'data', 'raw', 'hotspots')
    os.makedirs(output_dir, exist_ok=True)

    # 2. Filter per kota berdasarkan radius
    for city_key, cfg in CITIES.items():
        lat_c, lon_c = cfg["latitude"], cfg["longitude"]
        radius = cfg["hotspot_radius_km"]

        print(f"\n[*] Memfilter hotspot untuk {cfg['name']} (Radius {radius} km)...")
        dist = haversine_distance(lat_c, lon_c, df_raw['latitude'], df_raw['longitude'])
        df_city = df_raw[dist <= radius].copy()

        cols = ['timestamp', 'latitude', 'longitude', 'bright_ti4', 'confidence', 'frp']
        df_city = df_city[cols].sort_values('timestamp').reset_index(drop=True)

        out_path = os.path.join(output_dir, f"hotspots_{city_key}_2025.csv")
        df_city.to_csv(out_path, index=False)
        print(f"[✓] {len(df_city):,} titik api ditemukan dalam radius {radius} km dari {cfg['name']} -> {os.path.basename(out_path)}")

if __name__ == "__main__":
    filter_hotspots_for_cities()
