# BLUEPRINT PERANGKAT LUNAK: GeoRisk Quadtree Analysis

## 1. Deskripsi Sistem
Aplikasi berbasis Python untuk memetakan zonasi risiko gempa bumi menggunakan algoritma **Divide and Conquer (Quadtree)**. Sistem ini mengolah data gempa historis dan fitur geologis statis (sesar, gunung api) menggunakan 7 parameter risiko.

## 2. Tech Stack & Library
*   **Language:** Python 3.9+
*   **Data Processing:** `pandas` (untuk CSV), `numpy` (untuk kalkulasi matriks/bobot).
*   **Math:** `math` (Haversine formula untuk jarak koordinat).
*   **Visualization:** `matplotlib.pyplot` (untuk plotting Quadtree & Heatmap).

---

## 3. Struktur Direktori (Folder)
```text
project-georisk/
│
├── data/
│   ├── earthquake_history.csv  # Data latih (Lat, Lon, Mag, Depth, Date)
│   ├── faults_data.csv         # Data koordinat Sesar Aktif (Garis/Titik)
│   └── volcanoes_data.csv      # Data koordinat Gunung Api Aktif
│
├── src/
│   ├── __init__.py
│   ├── boundary.py             # Class untuk mendefinisikan area (Persegi)
│   ├── quadtree.py             # CORE ALGORITHM (Divide & Conquer Logic)
│   ├── risk_calculator.py      # Logic perhitungan 7 parameter
│   └── visualizer.py           # Logic untuk menggambar plot
│
├── main.py                     # Entry point (Program utama)
├── requirements.txt            # List library
└── README.md
```

---

## 4. Desain Struktur Data (Class Diagram)

### A. Class `Point` & `Rectangle` (di `boundary.py`)
Objek dasar untuk geometri spasial.
*   **Point:** Menyimpan `x` (longitude), `y` (latitude), dan `userData` (data gempa row).
*   **Rectangle:** Menyimpan `x`, `y` (titik pusat), `w` (lebar), `h` (tinggi).
    *   *Method:* `contains(point)` (Cek apakah titik ada di dalam kotak).
    *   *Method:* `intersects(range)` (Cek apakah dua kotak bersinggungan).

### B. Class `QuadTree` (di `quadtree.py`) - **INTI ALGORITMA**
Merepresentasikan node dalam pohon.
*   **Attributes:**
    *   `boundary`: Rectangle (batas wilayah node ini).
    *   `capacity`: int (max titik sebelum di-divide, misal: 4).
    *   `points`: list (menampung data gempa jika belum penuh).
    *   `divided`: boolean (status apakah sudah membelah).
    *   `northWest`, `northEast`, `southWest`, `southEast`: QuadTree (anak cabang).
*   **Methods:**
    *   `insert(point)`:
        1. Cek apakah point masuk `boundary`? Jika tidak, return.
        2. Jika kapasitas belum penuh, tambahkan ke `points`.
        3. Jika penuh & belum `divided`, panggil `subdivide()`.
        4. Jika sudah `divided`, panggil `insert()` ke 4 anak cabang secara rekursif.
    *   `subdivide()`: Membagi kotak menjadi 4 kuadran dan inisialisasi node anak.
    *   `query(range)`: Mengambil semua point dalam area tertentu (untuk analisis lokal).

### C. Class `RiskEngine` (di `risk_calculator.py`)
Modul untuk menghitung skor berdasarkan **7 Parameter**.
*   **Methods:**
    *   `calculate_risk(quake_point, fault_list, volcano_list)`:
        *   Input: Satu titik gempa historis.
        *   Process:
            1.  **Mag:** Ambil nilai Magnitude (Normalisasi 0-1).
            2.  **Depth:** Ambil nilai Depth (Normalisasi terbalik, makin dangkal makin tinggi).
            3.  **Intensity:** Estimasi MMI dari Mag & Depth.
            4.  **Freq:** Hitung kepadatan titik di node Quadtree tersebut.
            5.  **Fault Dist:** Loop `fault_list`, cari jarak minimum (Haversine).
            6.  **Plate Dist:** (Optional) Cek koordinat terhadap polygon lempeng.
            7.  **Volcano Dist:** Loop `volcano_list`, cari jarak minimum.
        *   Output: `Final Score` (Float 0.0 - 100.0).

---

## 5. Alur Logika Program (Pseudocode)

### Langkah 1: Inisialisasi
```python
# Load Data
gempa_data = load_csv("data/earthquake.csv")
sesar_data = load_csv("data/faults.csv")
gunung_data = load_csv("data/volcanoes.csv")

# Setup Peta (Bounding Box Indonesia)
domain = Rectangle(pusat_x, pusat_y, lebar, tinggi)
qtree = QuadTree(domain, capacity=4)
```

### Langkah 2: Konstruksi Quadtree (Divide Phase)
```python
# Masukkan semua data gempa ke tree
FOR setiap data IN gempa_data:
    point = Point(data.lat, data.lon, data.details)
    qtree.insert(point)
# Saat ini, data sudah terpartisi secara spasial.
# Area padat gempa akan memiliki node yang sangat dalam (kotak kecil).
```

### Langkah 3: Kalkulasi Risiko (Conquer Phase)
```python
risk_zones = []

FUNCTION traverse_and_calculate(node):
    IF node is Leaf (tidak punya anak):
        # Hitung rata-rata risiko di kotak ini
        local_score = 0
        FOR point IN node.points:
            # Hitung 7 Parameter untuk tiap titik
            score = RiskEngine.calculate(point, sesar_data, gunung_data)
            local_score += score
        
        avg_score = local_score / len(node.points)
        risk_zones.append({box: node.boundary, score: avg_score})
    ELSE:
        # Rekursif ke anak-anaknya
        traverse_and_calculate(node.northWest)
        traverse_and_calculate(node.northEast)
        ...
```

### Langkah 4: Visualisasi
```python
draw_map_background()
# Gambar kotak-kotak Quadtree
FOR zone IN risk_zones:
    color = get_color_by_score(zone.score) # Hijau/Kuning/Merah
    draw_rectangle(zone.box, color)
plot_show()
```

---

## 6. Detail Implementasi 7 Parameter (Rumus)
Untuk standardisasi, semua nilai harus dinormalisasi menjadi 0.0 s/d 1.0 sebelum dikalikan bobot ($W$).

$$ \text{Total Risk} = (M \cdot W_1) + (D \cdot W_2) + (I \cdot W_3) + (F \cdot W_4) + (S_{dist} \cdot W_5) + (P_{zone} \cdot W_6) + (V_{dist} \cdot W_7) $$

1.  **Magnitudo ($M$):** $Mag / 9.0$
2.  **Kedalaman ($D$):** $1 - (Depth / 700)$ *(Makin dangkal skor makin 1)*
3.  **Intensitas ($I$):** Konversi empiris Mag & Depth ke skala MMI (lalu / 12).
4.  **Frekuensi ($F$):** Jumlah titik di node tersebut / Max threshold.
5.  **Jarak Sesar ($S_{dist}$):** $1 - (\text{JarakKm} / \text{MaxRadiusCheck})$
6.  **Zona Lempeng ($P_{zone}$):** 1.0 jika di Megathrust, 0.5 jika Intraslab.
7.  **Jarak Gunung ($V_{dist}$):** $1 - (\text{JarakKm} / \text{MaxRadiusCheck})$

---

## 7. Rencana Pengujian (Analisis untuk Paper)

Program harus memiliki fitur **timer** untuk mencatat waktu eksekusi:

1.  **Skenario 1 (Tanpa Quadtree):**
    Hitung risiko dengan meloop seluruh array data secara linear.
    `start_time = time.now()` -> `linear_process()` -> `end_time`
2.  **Skenario 2 (Dengan Quadtree):**
    Hitung risiko dengan traversals tree.
    `start_time = time.now()` -> `qtree.insert()` -> `traverse()` -> `end_time`

Outputkan perbandingan waktunya ke console untuk disalin ke grafik laporan.