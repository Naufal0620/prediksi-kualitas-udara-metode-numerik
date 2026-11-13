import os
import pandas as pd

# Path file mentah dan output
input_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'hotspots', 'viirs-jpss1_2025_Indonesia.csv')
output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'hotspots', 'hotspots_medan_sumut_2025.csv')

print(f"[*] Membaca dataset NASA FIRMS Indonesia: {input_file}...")
df = pd.read_csv(input_file)
print(f"[*] Total titik api seluruh Indonesia: {len(df):,} baris")

# 1. Filter Bounding Box Sumatera Utara / Sekitar Medan
# Min Lon: 97.0, Max Lon: 100.0 | Min Lat: 2.0, Max Lat: 4.5
lat_min, lat_max = 2.0, 4.5
lon_min, lon_max = 97.0, 100.0

df_filtered = df[
    (df['latitude'] >= lat_min) & (df['latitude'] <= lat_max) &
    (df['longitude'] >= lon_min) & (df['longitude'] <= lon_max)
].copy()

print(f"[✓] Berhasil memfilter area Sumut: {len(df_filtered):,} titik api ditemukan!")

# 2. Standarisasi Timestamp (UTC -> WIB / UTC+7)
df_filtered['acq_time_str'] = df_filtered['acq_time'].astype(str).str.zfill(4)
df_filtered['datetime_utc'] = pd.to_datetime(
    df_filtered['acq_date'] + ' ' + df_filtered['acq_time_str'],
    format='%Y-%m-%d %H%M'
)
df_filtered['timestamp'] = df_filtered['datetime_utc'] + pd.Timedelta(hours=7)

# 3. Pilih kolom penting saja
kolom_dipakai = ['timestamp', 'latitude', 'longitude', 'bright_ti4', 'confidence', 'frp']
df_clean = df_filtered[kolom_dipakai].sort_values('timestamp').reset_index(drop=True)

# 4. Simpan hasil filter
df_clean.to_csv(output_file, index=False)
print(f"[✓] File bersih berhasil disimpan ke: {os.path.abspath(output_file)}")
print(f"\n[Preview 5 Data Titik Api Pertama di Sumut]:\n{df_clean.head()}")