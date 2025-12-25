import json
import os
import re
import time
import requests # Wajib: pip install requests
import pyperclip 

# --- KONFIGURASI DATABASE ---
ROOT_FOLDER = "Data_Indonesia"
FOLDER_OUTPUT = "Database_Pecahan"
FILE_INDEX = "spatial_index.js"

# Header agar request kita sopan dan tidak diblokir OSM
HEADERS_OSM = {
    'User-Agent': 'ProyekPetaDesaIndonesia/1.0 (contact: email_anda@example.com)'
}

def bersihkan_teks(teks):
    bersih = re.sub(r'[^\w\s]', '', teks).strip()
    return bersih.replace(" ", "_").lower()

# ==========================================
# 1. FITUR PENCARIAN ONLINE (OPENSTREETMAP)
# ==========================================
def cari_batas_desa_online(desa, kecamatan, kabupaten, provinsi):
    print(f"   [SEARCHING] Mencari batas '{desa}' di server OpenStreetMap...", end=" ")
    
    # URL Server Nominatim (OpenStreetMap)
    url = "https://nominatim.openstreetmap.org/search"
    
    # Kita menyamar sebagai Browser Chrome agar tidak diblokir
    headers_browser = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://google.com'
    }

    # Query pencarian
    query = f"Desa {desa}, {kecamatan}, {kabupaten}, {provinsi}"
    
    params = {
        'q': query,
        'format': 'json',
        'polygon_geojson': 1,
        'limit': 1
    }

    try:
        # verify=False digunakan untuk melewati error SSL/Certificate
        # timeout=10 agar script tidak bengong selamanya jika internet lemot
        response = requests.get(url, params=params, headers=headers_browser, verify=False, timeout=10)
        
        # Cek status kode (200 artinya OK)
        if response.status_code != 200:
            print(f"GAGAL (Kode: {response.status_code}). ❌")
            return None

        data = response.json()

        if not data:
            # Coba cari tanpa kata "Desa" (Kadang di OSM namanya cuma "Banjarworo")
            if "Desa" in query:
                print("...", end=" ") # Coba lagi diam-diam
                params['q'] = f"{desa}, {kecamatan}, {kabupaten}, {provinsi}"
                response = requests.get(url, params=params, headers=headers_browser, verify=False, timeout=10)
                data = response.json()

        if not data:
            print("TIDAK KETEMU DI DATABASE OSM. ❌")
            return None

        result = data[0]
        geojson = result.get('geojson')

        if not geojson or geojson['type'] not in ['Polygon', 'MultiPolygon']:
            print("ADA, TAPI BUKAN WILAYAH (HANYA TITIK). ⚠️")
            return None

        # --- PROSES KONVERSI GEOJSON KE FORMAT KITA ---
        coords_final = []
        raw_coords = []
        
        if geojson['type'] == 'Polygon':
            raw_coords = geojson['coordinates'][0]
        elif geojson['type'] == 'MultiPolygon':
            # Cari pulau terbesar jika wilayahnya terpecah
            max_len = 0
            for poly in geojson['coordinates']:
                if len(poly[0]) > max_len:
                    raw_coords = poly[0]
                    max_len = len(poly[0])

        # OSM Urutannya [Longitude, Latitude] -> Kita butuh [Latitude, Longitude]
        for point in raw_coords:
            lng, lat = point[0], point[1]
            coords_final.append([str(lat), str(lng)])

        print("KETEMU! ✅")
        print(f"   -> Mendapatkan {len(coords_final)} titik batas wilayah.")
        return coords_final

    except Exception as e:
        # Print error detailnya supaya kita tahu kenapa
        print(f"\n   [ERROR SYSTEM]: {e}")
        return None

# ==========================================
# 2. LOGIKA DATABASE (SMART LOADING)
# ==========================================
def update_database_smart():
    # ... (Sama persis dengan kode sebelumnya) ...
    # Agar tidak kepanjangan, saya ringkas. 
    # LOGIKA INI TIDAK BERUBAH DARI INPUT_HYBRID_TAHAP2
    print(f"   [AUTO-UPDATE] Menyusun Index Spatial...", end=" ")
    pengelompokan = {}
    for root, dirs, files in os.walk(ROOT_FOLDER):
        for filename in files:
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(root, filename), 'r') as f:
                        data = json.load(f)
                        if "Koordinat" in data:
                            key = f"{bersihkan_teks(data['Kabupaten'])}_{bersihkan_teks(data['Kecamatan'])}"
                            if key not in pengelompokan:
                                pengelompokan[key] = {
                                    "kab": data['Kabupaten'], "kec": data['Kecamatan'], "list": [],
                                    "min_lat": 90, "max_lat": -90, "min_lng": 180, "max_lng": -180
                                }
                            for c in data['Koordinat']:
                                lat, lng = float(c[0]), float(c[1])
                                if lat < pengelompokan[key]["min_lat"]: pengelompokan[key]["min_lat"] = lat
                                if lat > pengelompokan[key]["max_lat"]: pengelompokan[key]["max_lat"] = lat
                                if lng < pengelompokan[key]["min_lng"]: pengelompokan[key]["min_lng"] = lng
                                if lng > pengelompokan[key]["max_lng"]: pengelompokan[key]["max_lng"] = lng
                            pengelompokan[key]["list"].append(data)
                except: pass

    if not os.path.exists(FOLDER_OUTPUT): os.makedirs(FOLDER_OUTPUT)
    idx = []
    for key, info in pengelompokan.items():
        fname = f"db_{key}.js"
        with open(os.path.join(FOLDER_OUTPUT, fname), 'w') as f:
            f.write(f"terimaDataPecahan({json.dumps(info['list'], indent=None)});")
        idx.append({"file": fname, "kecamatan": info['kec'], "kabupaten": info['kab'], "bounds": [[info["min_lat"], info["min_lng"]], [info["max_lat"], info["max_lng"]]]})
    
    with open(FILE_INDEX, 'w') as f: f.write(f"var spatialIndex = {json.dumps(idx, indent=None)};")
    print("SELESAI! ✅")

# ==========================================
# 3. INPUT MANUAL (JIKA ONLINE GAGAL)
# ==========================================
def rekam_manual_hybrid():
    print("\n   [MODE MANUAL AKTIF] Silakan gambar di Editor atau Copy dari Maps...")
    pyperclip.copy("") 
    last_paste = ""
    manual_list = []
    
    try:
        while True:
            current = pyperclip.paste()
            if current != last_paste and current.strip() != "":
                # Mode Editor Peta (Polygon)
                if "\n" in current or current.count(',') > 3:
                    print("   [DETEKSI] Data Polygon Editor diterima!")
                    coords = []
                    for line in current.split('\n'):
                        if "," in line:
                            parts = line.split(',')
                            try: coords.append([parts[0].strip(), parts[1].strip()])
                            except: pass
                    if len(coords) > 2: return coords
                
                # Mode Manual (Satu titik)
                elif "," in current:
                     parts = current.split(',')
                     if len(parts) >= 2 and any(c.isdigit() for c in parts[0]):
                         manual_list.append([parts[0].strip(), parts[1].strip()])
                         print(f"      [+] Titik Manual ke-{len(manual_list)}")
                
                last_paste = current
            time.sleep(0.5)
    except KeyboardInterrupt:
        if len(manual_list) > 0: return manual_list
        return None

# ==========================================
# PROGRAM UTAMA
# ==========================================
def main():
    print("="*60)
    print("  INPUT SUPER OTOMATIS (AUTO-SEARCH + HYBRID)")
    print("="*60)
    update_database_smart()

    while True:
        try:
            print("\n" + "-"*30)
            print("INPUT WILAYAH BARU")
            provinsi = input("1. Provinsi : ").strip()
            if not provinsi: continue
            kabupaten = input("2. Kabupaten: ").strip()
            kecamatan = input("3. Kecamatan: ").strip()
            desa      = input("4. Nama Desa: ").strip()

            if not (provinsi and desa): continue

            # --- TAHAP 1: CARI ONLINE DULU ---
            coords = cari_batas_desa_online(desa, kecamatan, kabupaten, provinsi)

            # --- TAHAP 2: JIKA TIDAK KETEMU, PAKAI CARA LAMA ---
            if not coords:
                print("   [INFO] Beralih ke Input Manual/Editor...")
                coords = rekam_manual_hybrid()

            if not coords: 
                print("Dibatalkan."); continue

            # Simpan
            path_folder = os.path.join(ROOT_FOLDER, bersihkan_teks(provinsi), bersihkan_teks(kabupaten), bersihkan_teks(kecamatan))
            os.makedirs(path_folder, exist_ok=True)
            path_file = os.path.join(path_folder, bersihkan_teks(desa) + ".json")
            
            data = {"Provinsi": provinsi, "Kabupaten": kabupaten, "Kecamatan": kecamatan, "Desa": desa, "Koordinat": coords}
            with open(path_file, 'w') as f: json.dump(data, f, indent=4)
            
            print(f"\n[SUKSES] Desa {desa} tersimpan.")
            update_database_smart()
            
        except KeyboardInterrupt:
            print("\nKeluar."); break

if __name__ == "__main__":
    main()