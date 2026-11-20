# Log Perkembangan Proyek: Sistem Prediksi PM2.5 & Web GIS

Dokumen ini mencatat seluruh perubahan kode sumber, arsitektur data, riwayat pelatihan model, dan implementasi fitur.

---

## [2026-11-20] - Optimasi Feature Engineering, Reduksi Error, Peramalan 7 Hari & Deployment Setup

### 1. Perubahan Skema Training & Evaluasi Error
* **Pembagian Data:** Diperbarui dari 80:20 menjadi **90% Data Latih (*Training Set*)** dan **10% Data Uji (*Testing Set*)** berbasis urutan waktu (*Chronological Split*).
* **Metrik Baru Ditambahkan:**
  - **MAPE (*Mean Absolute Percentage Error*)**: Menghitung rata-rata persentase selisih error terhadap nilai riil.
  - **Akurasi Prediksi (%)**: $100\% - \text{MAPE}$.
  - Dilengkapi *small divisor protection* untuk menghindari distorsi persentase pada konsentrasi polusi mendekati 0.

---

### 2. Teknik Optimasi & Reduksi Error (Advanced Feature Engineering)
* **Cyclic Trigonometric Encoding:** Mengubah jam (0–23) menjadi `hour_sin` dan `hour_cos` menggunakan transformasi $2\pi \cdot \text{hour} / 24$ untuk menangkap ritme sirkadian harian polusi tanpa lonjakan diskontinuitas.
* **Rolling Momentum Lags:** Menambahkan `pm25_roll_mean3`, `pm25_roll_mean6`, dan `pm25_roll_std6` untuk menjaga stabilitas tren polusi jangka menengah.
* **Multi-Lag Expansion:** Menambahkan `pm25_lag3` melengkapi `lag1`, `lag2`, dan `lag24`.
* **Interaksi Termal:** Menambahkan `temp_rh_interaction = temperature * relative_humidity` untuk memodelkan inversi lapisan batas atmosfer.
* **Tuning Model Random Forest:**
  - `n_estimators` dinaikkan ke **200 Decision Trees**.
  - `max_depth = 20`, `min_samples_leaf = 2`, `max_features = 'sqrt'`.
* **Hasil Reduksi Error:**
  - **Medan (USU):** MAE turun menjadi **6.36 µg/m³** (RMSE: 11.03 µg/m³), akurasi naik menjadi **78.76%** (error turun ke 21.24%).
  - **Jakarta (Central):** MAE turun menjadi **4.95 µg/m³** (RMSE: 6.80 µg/m³), akurasi mencapai **71.20%**.
  - **Malang (Jatim):** MAE **5.33 µg/m³**, akurasi tertinggi mencapai **81.60%**.

---

### 3. Fitur Multi-Horizon Forecasting (Hingga 7 Hari / 168 Jam)
* `server/app.py` kini mendukung parameter query `?days=1|3|7` atau `?hours=168`.
* Open-Meteo Forecast ditarik hingga 7 hari ke depan.
* Modul `server/numerical_engine.py` otomatis menyesuaikan derajat curve fitting (Orde 3 untuk 24 jam, Orde 4 untuk 7 hari) dan mengeksekusi Metode Secant di sepanjang rentang horizon tersebut.

---

### 4. Automated Test Suite & Live Demo Web GIS
* Dibuat file pengujian otomatis `server/test_api.py` (5 pengujian mencakup health, stations, predict 24h seluruh stasiun, predict 7 hari, dan hotspots) -> **Status: 5/5 PASSED (100% Lulus)**.
* Dibuat halaman demo interaktif di `server/templates/index.html` dengan Dark Mode, Leaflet.js, tombol horizon (24 Jam, 3 Hari, 7 Hari), dan Chart.js live data.
* Disiapkan berkas `Procfile` dan dependensi `gunicorn` untuk kesiapan deployment instan ke Render.com (Rp 0).

---

## [2026-11-19] - Inisialisasi Arsitektur Multi-Kota Indonesia & Standardisasi Script

### 1. Keputusan Desain & Arsitektur
* **Opsi Terpilih:** **Solusi 1 (Multi-Model per Kota / City-Specific Models)** untuk menghindari *spatial mismatch*.
* **Cakupan 6 Wilayah Representatif:**
  1. Medan (USU) - Sumatera Utara
  2. Palembang - Sumatera Selatan
  3. Jakarta (Central) - DKI Jakarta
  4. Depok - Jawa Barat
  5. Malang - Jawa Timur
  6. Bali (Ubud) - Bali

### 2. Hasil Pipeline Pengumpulan Data Terpadu
* Total 28.411 baris jam data bersih sinkron terkumpul:
  - `master_dataset_medan.csv`: 4.112 jam
  - `master_dataset_palembang.csv`: 3.619 jam
  - `master_dataset_jakarta.csv`: 868 jam
  - `master_dataset_depok.csv`: 7.609 jam
  - `master_dataset_malang.csv`: 8.270 jam
  - `master_dataset_bali_ubud.csv`: 3.923 jam
