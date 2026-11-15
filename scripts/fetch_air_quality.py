import os
import requests
import pandas as pd
from dotenv import load_dotenv

# 1. Memuat konfigurasi dari environtment
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

API_KEY = os.getenv('OPENAQ_API_KEY')
LATITUDE = float(os.getenv('MEDAN_LAT', 3.5952))
LONGITUDE = float(os.getenv('MEDAN_LON', 98.6722))

if not API_KEY or API_KEY == "masukkan_api_key_openaq_anda":
    print("[!] PERINGATAN: OPENAQ_API_KEY belum diisi di file project/.env!")
    exit(1)

HEADERS = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

def find_locations():
    """Mencari stasion pemantau kualitas udara di sekitar lokasi"""
    print(f"[*] Mencari stasiun pemantau di sekitar lokasi ({LATITUDE}, {LONGITUDE})...")
    url = "https://api.openaq.org/v3/locations"
    params = {
        "coordinates": f"{LATITUDE},{LONGITUDE}",
        "radius": 25000,  # radius 25 km
        "limit": 10
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if (response.status_code != 200):
        print(f"[!] Gagal mencari stasiun: HTTP {response.status_code}")
        print(response.text)
        return []

    results = response.json().get("results", [])
    print(f"[✓] Ditemukan {len(results)} stasion di sekitar lokasi:")
    for location in results:
        sensors = [sensor.get("parameter", {}).get('name') for sensor in location.get("sensors", [])]
        print(f" - ID: {location['id']} | Nama: {location.get('name')} | Parameter: {sensors}")
    return results

def fetch_pm25_measurements(location_id, start_date="2025-10-10", end_date="2026-11-15"):
    """Mengunduh seluruh rekaman pengukuran PM2.5 per jam menggunakan pagination"""
    print(f"\n[*] Mengambil data PM2.5 dari Location ID: {location_id}...")

    # 1. Temukan sensor_id untuk PM2.5 di lokasi tersebut
    location_url = f"https://api.openaq.org/v3/locations/{location_id}"
    response = requests.get(location_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"[!] Gagal membaca detail lokasi: HTTP {response.status_code}")
        return None

    sensors = response.json().get("results", [{}])[0].get("sensors", [])
    pm25_sensor = next((sensor for sensor in sensors if sensor.get("parameter", {}).get("name") == "pm25"), None)

    if not pm25_sensor:
        print(f"[!] Lokasi {location_id} tidak memiliki sensor PM2.5")
        return None

    sensor_id = pm25_sensor["id"]
    print(f"[✓] Sensor PM2.5 ditemukan (Sensor ID: {sensor_id}). Mengunduh seluruh measurements via pagination...")

    # 2. Loop Pagination untuk mengambil semua halaman data
    records = []
    page = 1
    url = f"https://api.openaq.org/v3/sensors/{sensor_id}/hours"

    while True:
        params = {
            "datetime_from": f"{start_date}T00:00:00Z",
            "datetime_to": f"{end_date}T23:59:59Z",
            "limit": 1000,
            "page": page
        }

        print(f"    -> Mengambil Halaman {page}...", end="", flush=True)
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code != 200:
            print(f" [!] Gagal HTTP {response.status_code}")
            break

        data = response.json().get("results", [])
        if not data:
            print(" [Tuntas: tidak ada data lagi]")
            break

        print(f" [Dapat {len(data)} baris]")

        for item in data:
            period = item.get("period", {})
            dt = period.get("datetimeFrom", {}).get("local") or period.get("datetimeFrom", {}).get("utc")
            value = item.get("value")
            if dt and value is not None:
                records.append({"timestamp": dt, "pm25": value})

        # Jika data yang dikembalikan kurang dari 1.000, berarti ini halaman terakhir
        if len(data) < 1000:
            print("    -> Semua halaman berhasil diunduh!")
            break

        page += 1

    if not records:
        print("[!] Tidak ada data pengukuran yang berhasil dikumpulkan.")
        return None

    # 3. Konversi ke DataFrame & Bersihkan Duplikat
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    # 4. Simpan ke data/raw/air_quality/
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'air_quality')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "pm25_medan_hourly.csv")

    df.to_csv(output_path, index=False)
    print(f"\n[✓] Berhasil menyimpan seluruh data PM2.5 ke: {os.path.abspath(output_path)}")
    print(f"[✓] Total baris data terkumpul: {len(df):,} jam")
    print(f"[✓] Rentang data: {df['timestamp'].min()} s/d {df['timestamp'].max()}")
    print(f"\n[Preview 5 Baris Pertama]:\n{df.head()}")
    return df

def main():
    locations = find_locations()
    if not locations:
        print("[!] Tidak ditemukan stasiun di OpenAQ dengan koordinat tersebut.")
        return

    # Pilih lokasi pertama (biasanya stasiun resmi terdekat)
    chosen_id = locations[0]["id"]
    fetch_pm25_measurements(chosen_id)

if __name__ == "__main__":
    main()