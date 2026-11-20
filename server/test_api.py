"""
Test Suite Otomatis untuk Backend REST API Web GIS
Menguji:
1. Endpoint /api/health
2. Endpoint /api/stations
3. Endpoint /api/predict/<city> (Default 24 Jam dan 7 Hari / 168 Jam)
4. Endpoint /api/hotspots/<city>
"""

import unittest
from app import app
from config_cities import CITIES

class TestWebGISBackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_01_health_check(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "online")
        self.assertEqual(data.get("max_horizon_days"), 7)
        print("\n[✓] Test 1: Health check endpoint passed.")

    def test_02_stations_catalog(self):
        res = self.client.get('/api/stations')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("total"), len(CITIES))
        self.assertTrue(len(data.get("stations", [])) >= 6)
        print(f"[✓] Test 2: Stations endpoint passed ({data.get('total')} stations verified).")

    def test_03_prediction_24h_all_stations(self):
        for city_key in CITIES.keys():
            res = self.client.get(f'/api/predict/{city_key}')
            self.assertEqual(res.status_code, 200, f"Gagal pada kota: {city_key}")
            data = res.get_json()
            # Verifikasi 24 titik
            self.assertEqual(len(data.get("raw_predictions", [])), 24)
            self.assertEqual(len(data.get("ma24_discrete", [])), 24)
            # Verifikasi kurva kontinu polinomial
            self.assertIn("polynomial_curve", data)
            self.assertTrue(len(data["polynomial_curve"]["points_y"]) > 24)
            # Verifikasi hasil metode secant
            secant = data.get("secant_analysis", {})
            self.assertIn(secant.get("status"), ["SAFE", "THRESHOLD_EXCEEDED", "HAZARDOUS"])
            print(f"  [✓] Predict 24h passed for: {city_key} (Status Secant: {secant.get('status')})")

    def test_04_prediction_7_days_horizon(self):
        # Uji ramalan 7 hari (168 jam)
        res = self.client.get('/api/predict/medan?days=7')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("forecast_horizon", {}).get("hours"), 168)
        self.assertEqual(len(data.get("raw_predictions", [])), 168)
        self.assertEqual(len(data.get("ma24_discrete", [])), 168)
        print("[✓] Test 4: 7-day multi-horizon forecast (168 hours) passed.")

    def test_05_hotspots_endpoint(self):
        res = self.client.get('/api/hotspots/medan')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("hotspots", data)
        self.assertTrue(data.get("total") > 0)
        print(f"[✓] Test 5: Hotspots endpoint passed ({data.get('total')} hotspots loaded).")

if __name__ == '__main__':
    unittest.main()
