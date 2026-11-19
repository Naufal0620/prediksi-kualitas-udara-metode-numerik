"""
Modul Komputasi Metode Numerik:
1. Moving Average 24 Jam (MA24) sesuai PP No. 22 Tahun 2021 (Baku mutu 55 µg/m³)
2. Curve Fitting Polinomial Orde 3/4 (Pencocokan Kurva Kontinu)
3. Metode Secant (Pencarian Akar Waktu Pelampauan Ambang Batas 55 µg/m³)
"""

import numpy as np

def compute_ma24(historical_pm25, predicted_pm25_24h):
    """
    Menghitung Moving Average 24 jam untuk 24 jam ke depan.
    historical_pm25: list/array 24 jam terakhir sebelum t=0
    predicted_pm25_24h: list/array 24 nilai prediksi (t=1..24)
    """
    combined = list(historical_pm25[-23:]) + list(predicted_pm25_24h)
    ma24_series = []
    
    # Hitung rata-rata bergerak 24 jam untuk setiap t = 1..24
    for i in range(24):
        window = combined[i : i + 24]
        ma24_series.append(float(np.mean(window)))
        
    return ma24_series

def polynomial_curve_fitting(x_points, y_points, degree=3):
    """
    Membentuk fungsi kontinu polinomial P(t) dari titik diskrit menggunakan Least Squares.
    x_points: [1, 2, ..., 24] (jam ke depan)
    y_points: nilai MA24 pada tiap jam
    Return: fungsi callable P(t) dan koefisien polinomial
    """
    coeffs = np.polyfit(x_points, y_points, deg=degree)
    poly_func = np.poly1d(coeffs)
    return poly_func, coeffs.tolist()

def secant_root_finding(poly_func, threshold=55.0, x0=1.0, x1=2.0, max_iter=50, tol=1e-4):
    """
    Menerapkan Metode Secant untuk mencari akar f(t) = P(t) - threshold = 0
    t* menunjukkan waktu eksak (jam) ketika MA24 menyentuh baku mutu 55 µg/m³.
    """
    def f(t):
        return poly_func(t) - threshold

    # Evaluasi awal
    f0 = f(x0)
    f1 = f(x1)

    # Deteksi apakah kurva memotong ambang batas dalam domain t in [1, 24]
    domain_t = np.linspace(1, 24, 231)
    vals = poly_func(domain_t)
    has_crossing = np.any(vals >= threshold) and np.any(vals <= threshold)

    if not has_crossing and np.all(vals < threshold):
        return {
            "status": "SAFE",
            "message": "Kualitas udara diprediksi aman di bawah baku mutu (55 µg/m³) selama 24 jam ke depan.",
            "crossing_hour": None,
            "iterations": 0
        }
    
    if not has_crossing and np.all(vals > threshold):
        return {
            "status": "HAZARDOUS",
            "message": "Kualitas udara sudah melampaui baku mutu berbahaya sejak awal periode.",
            "crossing_hour": 0.0,
            "iterations": 0
        }

    # Cari pendekatan awal yang mengapit/dekat dengan akar
    sign_changes = np.where(np.diff(np.sign(vals - threshold)))[0]
    if len(sign_changes) > 0:
        idx = sign_changes[0]
        x0 = float(domain_t[idx])
        x1 = float(domain_t[idx + 1])
        f0 = f(x0)
        f1 = f(x1)

    # Algoritma Secant Iteratif
    for i in range(1, max_iter + 1):
        if abs(f1 - f0) < 1e-12:
            break
        
        # Rumus Secant: x_next = x1 - f1 * (x1 - x0) / (f1 - f0)
        x_next = x1 - f1 * (x1 - x0) / (f1 - f0)
        f_next = f(x_next)

        if abs(x_next - x1) < tol or abs(f_next) < tol:
            return {
                "status": "THRESHOLD_EXCEEDED",
                "message": f"Diprediksi melampaui baku mutu 55 µg/m³ pada t = {x_next:.2f} jam ke depan.",
                "crossing_hour": round(float(x_next), 2),
                "iterations": i,
                "residual": round(float(f_next), 6)
            }

        x0, x1 = x1, x_next
        f0, f1 = f1, f_next

    return {
        "status": "THRESHOLD_EXCEEDED",
        "message": f"Estimasi pelampauan ambang batas pada t = {x1:.2f} jam ke depan.",
        "crossing_hour": round(float(x1), 2),
        "iterations": max_iter,
        "residual": round(float(f1), 6)
    }
