"""
Script Fetching Data Cuaca Historis Multi-Kota dari Open-Meteo Archive API
Parameter: Suhu (2m), Kelembapan Relatif (2m), Presipitasi, Kecepatan Angin (10m), Arah Angin (10m)
"""

import os
import requests
import pandas as pd
from config_cities import CITIES

def fetch_weather_for_city(city_key):
    if city_key not in CITIES:
        print(f"[!] Kota '{city_key}' tidak ditemukan di konfigurasi.")
        return None

    cfg = CITIES[city_key]
    print(f"\n[*] Mengambil data cuaca Open-Meteo untuk {cfg['name']} ({cfg['latitude']}, {cfg['longitude']})...")
    print(f"[*] Periode: {cfg['start_date']} s/d {cfg['end_date']}")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": cfg["latitude"],
        "longitude": cfg["longitude"],
        "start_date": cfg["start_date"],
        "end_date": cfg["end_date"],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m"
        ],
        "timezone": cfg.get("timezone", "Asia/Jakarta")
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        if response.status_code != 200:
            print(f"[!] Gagal mengambil cuaca {cfg['name']}: HTTP {response.status_code}")
            return None

        data = response.json()
        hourly = data.get("hourly", {})
        if not hourly or "time" not in hourly:
            print(f"[!] Data hourly cuaca kosong untuk {cfg['name']}.")
            return None

        df = pd.DataFrame({
            "timestamp": hourly["time"],
            "temperature_2m": hourly["temperature_2m"],
            "relative_humidity_2m": hourly["relative_humidity_2m"],
            "precipitation": hourly["precipitation"],
            "wind_speed_10m": hourly["wind_speed_10m"],
            "wind_direction_10m": hourly["wind_direction_10m"]
        })

        df["timestamp"] = pd.to_datetime(df["timestamp"])

        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'weather')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"weather_{city_key}_hourly.csv")

        df.to_csv(output_file, index=False)
        print(f"[✓] Cuaca {cfg['name']} berhasil disimpan ({len(df):,} baris) -> {os.path.basename(output_file)}")
        return df

    except Exception as e:
        print(f"[!] Error koneksi Open-Meteo untuk {cfg['name']}: {e}")
        return None

def main():
    for city_key in CITIES.keys():
        fetch_weather_for_city(city_key)

if __name__ == "__main__":
    main()
