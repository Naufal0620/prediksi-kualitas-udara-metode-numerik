"""
Script Fetching Data PM2.5 Multi-Kota dari OpenAQ API v3 dengan Pagination Otomatis
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
from config_cities import CITIES

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

API_KEY = os.getenv('OPENAQ_API_KEY')
if not API_KEY or API_KEY == "masukkan_api_key_openaq_anda":
    print("[!] PERINGATAN: OPENAQ_API_KEY belum diisi di file project/.env!")
    exit(1)

HEADERS = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

def fetch_pm25_for_city(city_key):
    if city_key not in CITIES:
        print(f"[!] Kota '{city_key}' tidak ada dalam konfigurasi.")
        return None

    cfg = CITIES[city_key]
    sensor_id = cfg["openaq_sensor_id"]
    print(f"\n[*] Mengambil data PM2.5 OpenAQ untuk {cfg['name']} (Sensor ID: {sensor_id})...")
    print(f"[*] Rentang waktu: {cfg['start_date']} s/d {cfg['end_date']}")

    records = []
    page = 1
    url = f"https://api.openaq.org/v3/sensors/{sensor_id}/hours"

    while True:
        params = {
            "datetime_from": f"{cfg['start_date']}T00:00:00Z",
            "datetime_to": f"{cfg['end_date']}T23:59:59Z",
            "limit": 1000,
            "page": page
        }

        print(f"    -> Halaman {page}...", end="", flush=True)
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            if response.status_code != 200:
                print(f" [!] Gagal HTTP {response.status_code}")
                break

            data = response.json().get("results", [])
            if not data:
                print(" [Selesai: data tuntas]")
                break

            print(f" [Dapat {len(data)} baris]")

            for item in data:
                period = item.get("period", {})
                dt = period.get("datetimeFrom", {}).get("local") or period.get("datetimeFrom", {}).get("utc")
                value = item.get("value")
                if dt and value is not None and value >= 0:
                    records.append({"timestamp": dt, "pm25": value})

            if len(data) < 1000:
                print("    -> Seluruh halaman berhasil diunduh!")
                break

            page += 1

        except Exception as e:
            print(f" [!] Error koneksi: {e}")
            break

    if not records:
        print(f"[!] Tidak ada data PM2.5 yang berhasil diperoleh untuk {cfg['name']}.")
        return None

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'air_quality')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"pm25_{city_key}_hourly.csv")

    df.to_csv(output_file, index=False)
    print(f"[✓] Berhasil menyimpan {len(df):,} baris PM2.5 {cfg['name']} -> {os.path.basename(output_file)}")
    return df

def main():
    for city_key in CITIES.keys():
        fetch_pm25_for_city(city_key)

if __name__ == "__main__":
    main()
