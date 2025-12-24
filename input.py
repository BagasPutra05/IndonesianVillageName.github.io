import json
import os
import re
import time
import pyperclip 

# --- KONFIGURASI TAHAP 2 (SMART LOADING) ---
ROOT_FOLDER = "Data_Indonesia"
FOLDER_OUTPUT = "Database_Pecahan"
FILE_INDEX = "spatial_index.js"

def bersihkan_teks(teks):
    bersih = re.sub(r'[^\w\s]', '', teks).strip()
    return bersih.replace(" ", "_").lower()

# ==========================================
# LOGIKA DATABASE (SMART SPLIT)
# ==========================================
def update_database_smart():
    print(f"   [AUTO-UPDATE] Menyusun Index Spatial...", end=" ")
    pengelompokan = {}
    
    for root, dirs, files in os.walk(ROOT_FOLDER):
        for filename in files:
            if filename.endswith(".json"):
                path_lengkap = os.path.join(root, filename)
                try:
                    with open(path_lengkap, 'r') as f:
                        data = json.load(f)
                        if all(k in data for k in ("Koordinat", "Kecamatan", "Kabupaten")):
                            key = f"{bersihkan_teks(data['Kabupaten'])}_{bersihkan_teks(data['Kecamatan'])}"
                            if key not in pengelompokan:
                                pengelompokan[key] = {
                                    "kabupaten": data['Kabupaten'], "kecamatan": data['Kecamatan'], "desa_list": [],
                                    "min_lat": 90, "max_lat": -90, "min_lng": 180, "max_lng": -180
                                }
                            
                            # Hitung batas wilayah (bounding box)
                            for coord in data['Koordinat']:
                                lat, lng = float(coord[0]), float(coord[1])
                                if lat < pengelompokan[key]["min_lat"]: pengelompokan[key]["min_lat"] = lat
                                if lat > pengelompokan[key]["max_lat"]: pengelompokan[key]["max_lat"] = lat
                                if lng < pengelompokan[key]["min_lng"]: pengelompokan[key]["min_lng"] = lng
                                if lng > pengelompokan[key]["max_lng"]: pengelompokan[key]["max_lng"] = lng
                            
                            pengelompokan[key]["desa_list"].append(data)
                except: pass 

    if not os.path.exists(FOLDER_OUTPUT): os.makedirs(FOLDER_OUTPUT)
    spatial_index = []

    for key, info in pengelompokan.items():
        nama_file = f"db_{key}.js"
        isi_js = f"terimaDataPecahan({json.dumps(info['desa_list'], indent=None)});"
        with open(os.path.join(FOLDER_OUTPUT, nama_file), 'w') as f: f.write(isi_js)

        spatial_index.append({
            "file": nama_file, "kecamatan": info['kecamatan'], "kabupaten": info['kabupaten'],
            "bounds": [[info["min_lat"], info["min_lng"]], [info["max_lat"], info["max_lng"]]]
        })

    with open(FILE_INDEX, 'w') as f:
        f.write(f"var spatialIndex = {json.dumps(spatial_index, indent=None)};")
    print(f"SELESAI! ✅")

# ==========================================
# LOGIKA INPUT HYBRID (MANUAL + OTOMATIS)
# ==========================================
def rekam_koordinat_hybrid():
    print("\n   [MODE INPUT AKTIF]")
    print("   1. Jika Copy Polygon (Editor) -> Otomatis Simpan.")
    print("   2. Jika Copy Manual (Maps)    -> Ditampung dulu.")
    print("   >> TEKAN 'Ctrl + C' JIKA SUDAH SELESAI INPUT MANUAL.")
    
    list_manual = []
    pyperclip.copy("") 
    last_paste = ""

    try:
        while True:
            current = pyperclip.paste()
            
            if current != last_paste and current.strip() != "":
                
                # --- KASUS A: DETEKSI POLYGON (EDITOR) ---
                # Ciri: Ada baris baru (\n) ATAU komanya banyak sekali
                if "\n" in current or current.count(',') > 3:
                    print("   [DETEKSI] Data Polygon Editor! Langsung proses...")
                    coords = []
                    for line in current.split('\n'):
                        if "," in line:
                            parts = line.split(',')
                            try: coords.append([parts[0].strip(), parts[1].strip()])
                            except: pass
                    if len(coords) > 2: 
                        return coords # Langsung kembali (Auto Save)
                
                # --- KASUS B: DETEKSI MANUAL (SATU TITIK) ---
                # Ciri: Hanya ada satu koma, dan isinya angka
                elif "," in current:
                    parts = current.split(',')
                    if len(parts) >= 2:
                        lat = parts[0].strip()
                        lng = parts[1].strip()
                        # Validasi angka sederhana
                        if any(c.isdigit() for c in lat):
                            list_manual.append([lat, lng])
                            print(f"      [+] Titik Manual ke-{len(list_manual)}: {lat}, {lng}")

                last_paste = current
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        # User menekan Ctrl+C, artinya input manual selesai
        if len(list_manual) > 0:
            print(f"\n   [OK] {len(list_manual)} titik manual dikumpulkan.")
            return list_manual
        else:
            return None

# ==========================================
# MAIN LOOP
# ==========================================
def main():
    print("="*60)
    print("  INPUT HYBRID (AUTO + MANUAL)")
    print("="*60)
    
    update_database_smart() # Update awal

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

            # Masuk ke fungsi Hybrid
            coords = rekam_koordinat_hybrid()
            
            if not coords: 
                print("Dibatalkan."); continue

            path_folder = os.path.join(ROOT_FOLDER, bersihkan_teks(provinsi), bersihkan_teks(kabupaten), bersihkan_teks(kecamatan))
            os.makedirs(path_folder, exist_ok=True)
            path_file = os.path.join(path_folder, bersihkan_teks(desa) + ".json")
            
            data = {"Provinsi": provinsi, "Kabupaten": kabupaten, "Kecamatan": kecamatan, "Desa": desa, "Koordinat": coords}
            with open(path_file, 'w') as f: json.dump(data, f, indent=4)
            
            print(f"\n[SUKSES] Desa {desa} tersimpan.")
            update_database_smart()
            
        except KeyboardInterrupt:
            print("\nKeluar program.")
            break

if __name__ == "__main__":
    main()