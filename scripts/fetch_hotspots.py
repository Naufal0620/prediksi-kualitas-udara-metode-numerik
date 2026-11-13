import os
import requests
import pandas as pd
import io
from dotenv import load_dotenv

# 1. Memuat konfigurasi dari project/.env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

MAP_KEY = os.getenv('NASA_FIRMS_MAP_KEY')
if not MAP_KEY or MAP_KEY == "masukkan_map_key_nasa_firms_anda":
    print("[!] PERINGATAN: NASA_FIRMS_MAP_KEY belum diisi di file project/.env!")
    exit(1)

# Bounding Box Sumatera Utara sekitar Medan: min_lon, min_lat, max_lon, max_lat
BBOX_SUMUT = "97.0,2.0,100.0,4.5"

# Instrumen Satelit: VIIRS_SNPP_NRT atau VIIRS_NOAA20_NRT atau MODIS_NRT
SOURCE = "VIIRS_SNPP_NRT"

# Rentang hari (1-5 hari terakhir untuk API NRT realtime)
DAYS = 5

# tanggal pengambilan data
TARGET_DATE = "2026-11-01"

def fetch_firms_hotspots():
    print(f"[*] Menghubungi NASA FIRMS API untuk Area Sumatera Utara (BBOX: {BBOX_SUMUT})...")
    print(f"[*] Sumber sensor: {SOURCE} | Rentang: {DAYS} hari terakhir...")

    # URL API FIRMS untuk area koordinat (format CSV response)
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{BBOX_SUMUT}/{DAYS}/{TARGET_DATE}"

    response = requests.get(url)

    if response.status_code != 200:
        print(f"[!] Gagal mengambil data FIRMS: HTTP {response.status_code}")
        print(response.text)
        return None

    # Respons FIRMS berbentuk teks CSV langsung
    csv_data = response.text
    if not csv_data.strip() or "latitude" not in csv_data:
        print("[!] Tidak ada data titik panas ditemukan atau respons tidak valid.")
        print("Detail respons:", csv_data[:200])
        return None

    # Parsing teks CSV ke DataFrame Pandas
    df = pd.read_csv(io.StringIO(csv_data))

    # Gabungkan kolom 'acq_date' dan 'acq_time' menjadi satu kolom 'timestamp'
    # Format acq_time di FIRMS biasanya 4 digit (misal: 0630 = 06:30 UTC)
    df['acq_time_str'] = df['acq_time'].astype(str).str.zfill(4)
    df['datetime_utc'] = pd.to_datetime(df['acq_date'] + ' ' + df['acq_time_str'], format='%Y-%m-%d %H%M')

    # Konversi UTC ke Waktu Indonesia Barat (WIB / UTC+7)
    df['timestamp'] = df['datetime_utc'] + pd.Timedelta(hours=7)

    # Simpan ke data/raw/hotspots/
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'hotspots')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "hotspots_sumut.csv")

    df.to_csv(output_path, index=False)
    bright_col = 'bright_ti4' if 'bright_ti4' in df.columns else 'brightness'
    print(f"[✓] Berhasil menyimpan data titik panas ke: {os.path.abspath(output_path)}")
    print(f"[✓] Total titik panas terdeteksi: {len(df)} titik api")
    print(f"\n[Preview 5 Baris Pertama]:\n{df[['latitude', 'longitude', bright_col, 'confidence', 'timestamp']].head()}")
    return df

if __name__ == "__main__":
    fetch_firms_hotspots()