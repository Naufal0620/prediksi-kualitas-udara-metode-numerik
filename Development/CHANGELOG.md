# Log Perkembangan Proyek: Sistem Prediksi PM2.5 & Web GIS

Dokumen ini mencatat seluruh perubahan kode sumber, arsitektur data, dan riwayat fetching multi-kota di Indonesia.

---

## [2026-11-19] - Inisialisasi Arsitektur Multi-Kota Indonesia & Standardisasi Script

### 1. Keputusan Desain & Arsitektur
* **Opsi Terpilih:** **Solusi 1 (Multi-Model per Kota / City-Specific Models)**.
  * Setiap kota memiliki dataset latih yang bersih dan model Random Forest spesifik untuk menghindari *spatial mismatch*.
  * UI Web GIS akan menampilkan peta dunia/Indonesia interaktif ala IQAir, dengan kartu prediktif analitis mendalam pada kota-kota utama yang didukung.
* **Target Kota Prioritas Utama:**
  1. **Medan** (Stasiun USU, Lat: 3.5391, Lon: 98.6154) - Representasi Sumatera Utara (Pesisir & Pengaruh Karhutla).
  2. **Jakarta Pusat / Selatan** (Stasiun Jakarta Central / South, Lat: -6.1825, Lon: 106.8342) - Representasi Ibukota Metropolitan & Emisi Urban Padat.
  3. **Palembang** (Stasiun SD Muhammadiyah, Lat: -2.9230, Lon: 104.7129) - Representasi Sumatera Selatan / Titik Karhutla Gambut.

---

### 2. Standardisasi Struktur Direktori Data
Folder `project/data/` distrukturkan secara rapi berdasarkan nama kota (`city_slug`):
```text
project/data/
├── raw/
│   ├── air_quality/
│   │   ├── pm25_medan_hourly.csv
│   │   ├── pm25_jakarta_hourly.csv
│   │   └── pm25_palembang_hourly.csv
│   ├── weather/
│   │   ├── weather_medan_hourly.csv
│   │   ├── weather_jakarta_hourly.csv
│   │   └── weather_palembang_hourly.csv
│   └── hotspots/
│       ├── viirs-jpss1_2025_Indonesia.csv (Dataset Nasional Master)
│       ├── hotspots_medan_2025.csv
│       ├── hotspots_jakarta_2025.csv
│       └── hotspots_palembang_2025.csv
└── processed/
    ├── master_dataset_medan.csv
    ├── master_dataset_jakarta.csv
    └── master_dataset_palembang.csv
```

---

### 5. Ekspansi Dataset Multi-Wilayah Indonesia (6 Wilayah Representatif)

Untuk memperluas cakupan wilayah nasional sesuai instruksi pengguna, dipilih stasiun-stasiun representatif terbaik dari pulau Sumatera, Jawa, dan Bali yang memiliki data jam historis padat:

| Wilayah / Kota | Nama Stasiun | Kategori Geografis | Total Data Siap Latih | Berkas Master |
| :--- | :--- | :--- | :--- | :--- |
| **Sumatera Utara** | Medan (USU) | Pesisir Selat Malaka & Pengaruh Asap | **4.112 jam** | `master_dataset_medan.csv` |
| **Sumatera Selatan** | Palembang | Kawasan Karhutla Gambut Sumatera | **3.619 jam** | `master_dataset_palembang.csv` |
| **DKI Jakarta** | Jakarta (Central) | Ibukota Metropolitan Padat | **868 jam** | `master_dataset_jakarta.csv` |
| **Jawa Barat** | Depok | Penyangga Urban Jabodetabek | **7.609 jam** | `master_dataset_depok.csv` |
| **Jawa Timur** | Malang | Kawasan Dataran Tinggi / Pegunungan | **8.270 jam** | `master_dataset_malang.csv` |
| **Bali** | Bali (Ubud) | Wisata Tropis / Udara Pesisir | **3.923 jam** | `master_dataset_bali_ubud.csv` |

**Total Data Jam Nasional Terkumpul:** **28.411 baris jam** data sinkron (PM2.5 + Cuaca Open-Meteo + Hotspot Geofencing VIIRS).
Semua kode modular di `scripts/` telah diperbarui dan berjalan otomatis tanpa kesalahan.

