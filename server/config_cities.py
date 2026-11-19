"""
Konfigurasi Stasiun Kualitas Udara Representatif di Berbagai Wilayah Indonesia
Mencakup: Sumatera Utara, Sumatera Selatan, DKI Jakarta, Jawa Barat, Jawa Timur, dan Bali
"""

CITIES = {
    # 1. Sumatera Utara
    "medan": {
        "name": "Medan (USU)",
        "city": "Medan",
        "province": "Sumatera Utara",
        "region_group": "Sumatera",
        "latitude": 3.539102,
        "longitude": 98.615361,
        "openaq_location_id": 5586536,
        "openaq_sensor_id": 14336462,
        "timezone": "Asia/Jakarta",
        "hotspot_radius_km": 100.0,
        "start_date": "2025-10-10",
        "end_date": "2026-11-15"
    },
    # 2. Sumatera Selatan (Gambut / Karhutla)
    "palembang": {
        "name": "Palembang",
        "city": "Palembang",
        "province": "Sumatera Selatan",
        "region_group": "Sumatera",
        "latitude": -2.9230,
        "longitude": 104.7129,
        "openaq_location_id": 6103913,
        "openaq_sensor_id": 14439936,
        "timezone": "Asia/Jakarta",
        "hotspot_radius_km": 100.0,
        "start_date": "2025-10-22",
        "end_date": "2026-09-09"
    },
    # 3. DKI Jakarta (Metropolitan)
    "jakarta": {
        "name": "Jakarta (Central)",
        "city": "Jakarta",
        "province": "DKI Jakarta",
        "region_group": "Jawa",
        "latitude": -6.1825,
        "longitude": 106.8342,
        "openaq_location_id": 8637,
        "openaq_sensor_id": 25072,
        "timezone": "Asia/Jakarta",
        "hotspot_radius_km": 80.0,
        "start_date": "2025-01-01",
        "end_date": "2025-12-31"
    },
    # 4. Jawa Barat (Penyangga Ibukota / Urban)
    "depok": {
        "name": "Depok",
        "city": "Depok",
        "province": "Jawa Barat",
        "region_group": "Jawa",
        "latitude": -6.4095,
        "longitude": 106.8562,
        "openaq_location_id": 1367443,
        "openaq_sensor_id": 6658670,
        "timezone": "Asia/Jakarta",
        "hotspot_radius_km": 80.0,
        "start_date": "2025-01-01",
        "end_date": "2025-12-31"
    },
    # 5. Jawa Timur (Kawasan Dataran Tinggi)
    "malang": {
        "name": "Malang",
        "city": "Malang",
        "province": "Jawa Timur",
        "region_group": "Jawa",
        "latitude": -7.9185,
        "longitude": 112.6513,
        "openaq_location_id": 6144741,
        "openaq_sensor_id": 14739443,
        "timezone": "Asia/Jakarta",
        "hotspot_radius_km": 80.0,
        "start_date": "2025-11-27",
        "end_date": "2026-11-15"
    },
    # 6. Bali (Kawasan Wisata & Udara Pesisir Tropis)
    "bali_ubud": {
        "name": "Bali (Ubud)",
        "city": "Gianyar / Ubud",
        "province": "Bali",
        "region_group": "Kepulauan Nusa Tenggara / Bali",
        "latitude": -8.5304,
        "longitude": 115.2693,
        "openaq_location_id": 4826556,
        "openaq_sensor_id": 13397855,
        "timezone": "Asia/Makassar",
        "hotspot_radius_km": 80.0,
        "start_date": "2025-06-22",
        "end_date": "2026-10-03"
    }
}
