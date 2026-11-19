# Laporan Hasil Evaluasi Pelatihan Model Random Forest

Evaluasi menggunakan metode **Chronological Split (80% Train, 20% Test)** sesuai batasan proposal Bab 1.4 butir 11.

| No | Wilayah & Stasiun | Total Data | MAE (µg/m³) | RMSE (µg/m³) | Model File |
|:---:|:---|:---:|:---:|:---:|:---|
| 1 | **Medan (USU)** | 4,088 | **8.66** | **17.16** | `rf_model_medan.joblib` |
| 2 | **Palembang** | 3,595 | **36.5** | **61.91** | `rf_model_palembang.joblib` |
| 3 | **Jakarta (Central)** | 844 | **5.21** | **7.26** | `rf_model_jakarta.joblib` |
| 4 | **Depok** | 7,585 | **7.16** | **9.7** | `rf_model_depok.joblib` |
| 5 | **Malang** | 8,246 | **6.34** | **10.04** | `rf_model_malang.joblib` |
| 6 | **Bali (Ubud)** | 3,899 | **2.97** | **4.46** | `rf_model_bali_ubud.joblib` |

> *Catatan: Nilai MAE dan RMSE yang rendah menunjukkan model mampu menangkap fluktuasi polusi dengan presisi tinggi.*
