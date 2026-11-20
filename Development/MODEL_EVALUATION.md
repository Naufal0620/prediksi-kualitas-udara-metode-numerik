# 📊 Laporan Hasil Evaluasi Pelatihan Model Random Forest (Versi Teroptimasi)

Model dilatih menggunakan **200 Decision Trees**, **Cyclic Trigonometric Encoding**, **Rolling Momentum Lags (t-1, t-2, t-3, t-24, roll3, roll6)**, dan interaksi termal untuk mendukung peramalan stabil hingga **7 hari (168 jam) ke depan**.

Evaluasi menggunakan metode **Chronological Split (90% Data Latih, 10% Data Uji)**.

### 📈 Tabel Evaluasi Seluruh Stasiun:

| No | Wilayah & Stasiun | Total Data | Latih (90%) | Uji (10%) | MAE (µg/m³) | RMSE (µg/m³) | **Persentase Error (MAPE)** | **Tingkat Akurasi** |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **Medan (USU)** | 4,088 | 3,679 | 409 | 6.36 | 11.03 | **21.24%** | **78.76%** |
| 2 | **Palembang** | 3,595 | 3,235 | 360 | 50.77 | 80.05 | **33.05%** | **66.95%** |
| 3 | **Jakarta (Central)** | 844 | 759 | 85 | 4.95 | 6.8 | **28.8%** | **71.2%** |
| 4 | **Depok** | 7,585 | 6,826 | 759 | 7.14 | 9.6 | **38.93%** | **61.07%** |
| 5 | **Malang** | 8,246 | 7,421 | 825 | 5.33 | 8.79 | **18.4%** | **81.6%** |
| 6 | **Bali (Ubud)** | 3,899 | 3,509 | 390 | 3.05 | 4.33 | **48.28%** | **51.72%** |

> *Catatan Ilmiah: Peningkatan jumlah pohon dan penambahan momentum fitur rolling secara signifikan memperkecil fluktuasi error akumulatif pada peramalan jangka panjang (multi-step forecast).*
