import os
import requests
import pandas as pd
from dotenv import load_dotenv

# 1. Memuat konfigurasi dari environtment
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

LATITUDE = float(os.getenv('MEDAN_LAT', 3.5952))
LONGITUDE = float(os.getenv('MEDAN_LON', 98.6722))
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Jakarta')

# rentang waktu data historis 1 tahun (2024)
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

def fetch_weather_data():
    print(f"[*] Menghubungi Open-Meteo Archive API untuk Posisi ({LATITUDE}, {LONGITUDE})...")
    print(f"[*] Rentang waktu: {START_DATE} s/d {END_DATE} (Timezone: {TIMEZONE})")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m"
        ],
        "timezone": TIMEZONE
    }

    response = requests.get(url, params=params, timeout=60)

    if response.status_code != 200:
        print(f"[!] Error saat mengambil data: HTTP {response.status_code}")
        print(response.text)
        return

    data = response.json()
    hourly = data.get("hourly", {})

    # 2. konversi data ke DataFrame Pandas
    df = pd.DataFrame({
        "timestamp": hourly["time"],
        "temperature_2m": hourly["temperature_2m"],
        "relative_humidity_2m": hourly["relative_humidity_2m"],
        "precipitation": hourly["precipitation"],
        "wind_speed_10m": hourly["wind_speed_10m"],
        "wind_direction_10m": hourly["wind_direction_10m"],
    })

    # konversi kolom timestamp ke datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 3. simpan ke folder raw/weather
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'weather')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "weather_medan_hourly.csv")

    df.to_csv(output_path, index=False)
    print(f"[✓] Berhasil menyimpan data cuaca ke: {os.path.abspath(output_path)}")
    print(f"[✓] Total baris data: {len(df)} jam (~{len(df)//24} hari)")
    print(f"\n[Preview 5 Baris Pertama]:\n{df.head()}")

if __name__ == "__main__":
    fetch_weather_data()