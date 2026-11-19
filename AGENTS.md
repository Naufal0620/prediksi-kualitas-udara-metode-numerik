# 🤖 AGENTS.md - Panduan Integrasi UI/UX & Roadmap Frontend

Dokumen ini ditujukan bagi **Pengembang Frontend / Desainer UI/UX (Rekan Tim)** dan agen AI yang bertugas membangun antarmuka Web GIS. Dokumen ini mendefinisikan kontrak data API, spesifikasi visual, dan roadmap pengembangan frontend.

---

## 🧭 Roadmap Pengembangan Frontend UI/UX

```mermaid
flowchart LR
    M1["Milestone 1: Setup Proyek Frontend & Peta Dasar Leaflet"] --> M2["Milestone 2: Konsumsi API Stasiun & Hotspot Markers"]
    M2 --> M3["Milestone 3: Panel Analitik Chart.js & Garis 55 µg/m³"]
    M3 --> M4["Milestone 4: Kartu Peringatan Dini Hasil Metode Secant"]
    M4 --> M5["Milestone 5: Polishing Tampilan ala IQAir & Deployment"]
```

### Milestone 1: Setup Proyek Frontend (Estimasi: 1-2 Hari)
* Pilihan teknologi frontend bebas: HTML5/Tailwind/Bootstrap murni, atau React/Next.js/Vue.
* Inisialisasi peta interaktif menggunakan **Leaflet.js** (Tile: OpenStreetMap atau CartoDB Dark/Positron ala IQAir).
* Pusatkan peta di koordinat Indonesia (`lat: -2.5, lon: 118.0`, zoom level: 5).

### Milestone 2: Marker Stasiun & Sebaran Titik Api (Estimasi: 2 Hari)
* Panggil `GET http://localhost:5000/api/stations` saat aplikasi dimuat.
* Buat marker lingkaran (*CircleMarker*) pada setiap stasiun.
* Berikan warna marker berdasarkan tingkat polusi atau status stasiun.
* Panggil `GET http://localhost:5000/api/hotspots/<city_key>` untuk menampilkan titik api NASA FIRMS dengan ikon api merah/oranye.

### Milestone 3: Visualisasi Grafik Deret Waktu Chart.js (Estimasi: 2 Hari)
* Ketika user mengklik salah satu stasiun di peta, panggil `GET http://localhost:5000/api/predict/<city_key>`.
* Tampilkan grafik dengan **3 layer garis**:
  1. **Titik Diskrit Prediksi (Garis Biru/Teal):** Menggunakan `raw_predictions`.
  2. **Kurva Kontinu Polinomial MA24 (Garis Mulus Cyan/Ungu):** Menggunakan `polynomial_curve.points_x` dan `points_y`.
  3. **Garis Ambang Batas Nasional (Garis Putus-putus Merah):** Nilai statis `55.0` µg/m³.

### Milestone 4: Kartu Analisis Metode Secant & Early Warning (Estimasi: 1 Hari)
* Baca objek `secant_analysis`:
  * Jika `status == "THRESHOLD_EXCEEDED"`: Tampilkan badge merah dengan pesan:  
    ⚠️ *"Peringatan: Polusi diprediksi melampaui baku mutu 55 µg/m³ dalam **{crossing_hour}** jam ke depan!"*
  * Jika `status == "SAFE"`: Tampilkan badge hijau:  
    ✅ *"Kualitas udara diprediksi aman di bawah baku mutu nasional selama 24 jam ke depan."*
  * Tampilkan informasi matematis: Jumlah iterasi Secant (`iterations`) dan residual error (`residual`).

### Milestone 5: Polishing UI & Deployment (Estimasi: 1-2 Hari)
* Tambahkan panel pencarian stasiun / dropdown kota.
* Deploy frontend ke Vercel/Netlify atau digabung ke folder `server/templates/` Flask.

---

## 📡 Kontrak Spesifikasi REST API (API Contract)

Base URL: `http://localhost:5000` (atau URL server produksi Render)

### 1. `GET /api/stations`
Mengembalikan daftar seluruh stasiun pemantau yang aktif.

**Contoh Response:**
```json
{
  "total": 6,
  "stations": [
    {
      "key": "medan",
      "name": "Medan (USU)",
      "city": "Medan",
      "province": "Sumatera Utara",
      "region_group": "Sumatera",
      "coordinates": {
        "latitude": 3.539102,
        "longitude": 98.615361
      },
      "hotspot_radius_km": 100.0,
      "metrics": {
        "mae": 8.66,
        "rmse": 17.16
      }
    }
  ]
}
```

---

### 2. `GET /api/predict/<city_key>`
Mengembalikan hasil inferensi Random Forest 24 jam ke depan, interpolasi kurva polinomial, dan hasil akar Metode Secant.

**Parameter URL:**
* `city_key`: `medan` | `jakarta` | `palembang` | `depok` | `malang` | `bali_ubud`

**Contoh Response:**
```json
{
  "station": {
    "key": "medan",
    "name": "Medan (USU)",
    "city": "Medan",
    "coordinates": {
      "latitude": 3.539102,
      "longitude": 98.615361
    }
  },
  "air_quality_threshold": 55.0,
  "forecast_hours": [
    "2026-11-20 00:00",
    "2026-11-20 01:00"
  ],
  "raw_predictions": [38.2, 41.5, 45.1],
  "ma24_discrete": [32.1, 34.0, 37.8],
  "polynomial_curve": {
    "degree": 3,
    "coefficients": [0.0021, -0.084, 1.45, 29.8],
    "points_x": [1.0, 1.39, 1.78],
    "points_y": [31.17, 31.85, 32.55]
  },
  "secant_analysis": {
    "status": "THRESHOLD_EXCEEDED",
    "crossing_hour": 19.7,
    "iterations": 1,
    "residual": 0.000018,
    "message": "Diprediksi melampaui baku mutu 55 µg/m³ pada t = 19.70 jam ke depan."
  },
  "generated_at": "2026-11-19T22:10:48.123456"
}
```

---

### 3. `GET /api/hotspots/<city_key>`
Mengembalikan sebaran titik api satelit NASA FIRMS pada radius pemantauan stasiun kota.

**Contoh Response:**
```json
{
  "city": "medan",
  "station_name": "Medan (USU)",
  "total": 50,
  "hotspots": [
    {
      "latitude": 3.1205,
      "longitude": 98.4512,
      "brightness": 328.4,
      "confidence": "nominal",
      "timestamp": "2025-08-14 13:20:00"
    }
  ]
}
```

---

## 🎨 Panduan Gaya Desain Visual (UI/UX Guidelines)

1. **Skema Warna Rekomendasi:**
   * Latar Belakang: Dark Mode (`#0F172A` / `#1E293B`) atau Clean White (`#F8FAFC`).
   * Primary Accent: Teal (`#0D9488`) & Deep Navy (`#1A365D`).
   * Garis Ambang Batas (55 µg/m³): Coral Red (`#EF4444`).
   * Titik Api Hotspot: Amber/Flame (`#F97316`).
2. **Kategori Kualitas Udara (Indikator Warna Indeks):**
   * $0 - 15.5\ \mu g/m^3$ : 🟢 **Baik / Baik Sekali** (`#10B981`)
   * $15.6 - 55.0\ \mu g/m^3$ : 🟡 **Sedang / Moderat** (`#F59E0B`)
   * $> 55.0\ \mu g/m^3$ : 🔴 **Tidak Sehat (Baku Mutu Terlampaui)** (`#EF4444`)
