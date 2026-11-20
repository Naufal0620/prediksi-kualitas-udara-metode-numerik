# 📊 Laporan Hasil Evaluasi Pelatihan Model Random Forest

Evaluasi menggunakan metode **Chronological Split (90% Data Latih, 10% Data Uji)** sesuai urutan waktu deret historis.

### 📌 Definisi Metrik:
- **MAE (*Mean Absolute Error*)**: Rata-rata selisih absolut antara nilai prediksi dan aktual fisik (dalam satuan $\mu g/m^3$).
- **RMSE (*Root Mean Squared Error*)**: Akar rata-rata kuadrat error, memberi penalti lebih besar pada lonjakan polusi ekstrem (dalam $\mu g/m^3$).
- **MAPE (*Mean Absolute Percentage Error*)**: **Persentase error rata-rata model** relatif terhadap konsentrasi aktual (%). Semakin kecil nilainya, semakin akurat.
- **Akurasi (%)**: Tingkat akurasi prediksi model ($100\% - \text{MAPE}$).

### 📈 Tabel Evaluasi Seluruh Stasiun:

| No | Wilayah & Stasiun | Total Data | Latih (90%) | Uji (10%) | MAE (µg/m³) | RMSE (µg/m³) | **Persentase Error (MAPE)** | **Akurasi Prediksi** |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **Medan (USU)** | 4,088 | 3,679 | 409 | 7.32 | 14.77 | **23.66%** | **76.34%** |
| 2 | **Palembang** | 3,595 | 3,235 | 360 | 49.4 | 75.34 | **33.65%** | **66.35%** |
| 3 | **Jakarta (Central)** | 844 | 759 | 85 | 5.01 | 7.23 | **29.92%** | **70.08%** |
| 4 | **Depok** | 7,585 | 6,826 | 759 | 7.02 | 9.7 | **36.31%** | **63.69%** |
| 5 | **Malang** | 8,246 | 7,421 | 825 | 5.46 | 9.13 | **18.23%** | **81.77%** |
| 6 | **Bali (Ubud)** | 3,899 | 3,509 | 390 | 2.84 | 4.2 | **55.05%** | **44.95%** |

> *Catatan: Model dilatih pada data historis awal dan diuji murni pada data masa depan (10% kronologis akhir) tanpa data leakage.*
