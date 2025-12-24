import json
import os
import re
import time
import pyperclip 

# --- KONFIGURASI TAHAP 2 ---
ROOT_FOLDER = "Data_Indonesia"
FOLDER_OUTPUT = "Database_Pecahan"  # Folder penyimpanan file JS kecil
FILE_INDEX = "spatial_index.js"     # Peta Harta Karun (Index Lokasi)

def bersihkan_teks(teks):
    bersih = re.sub(r'[^\w\s]', '', teks).strip()
    return bersih.replace(" ", "_").lower()

# ==========================================
# LOGIKA UPDATE DATABASE (SMART SPLIT)
# ==========================================
def update_database_smart():
    print(f"   [AUTO-UPDATE] Menyusun Index Pintar (Tahap 2)...", end=" ")
    
    pengelompokan = {}
    
    # 1. Scan & Kelompokkan Data per Kecamatan
    for root, dirs, files in os.walk(ROOT_FOLDER):
        for filename in files:
            if filename.endswith(".json"):
                path_lengkap = os.path.join(root, filename)
                try:
                    with open(path_lengkap, 'r') as f:
                        data = json.load(f)
                        if all(k in data for k in ("Koordinat", "Kecamatan", "Kabupaten")):
                            
                            # Kunci Unik: tuban_bangilan
                            kab_clean = bersihkan_teks(data['Kabupaten'])
                            kec_clean = bersihkan_teks(data['Kecamatan'])
                            key = f"{kab_clean}_{kec_clean}"
                            
                            if key not in pengelompokan:
                                pengelompokan[key] = {
                                    "kabupaten": data['Kabupaten'],
                                    "kecamatan": data['Kecamatan'],
                                    "desa_list": [],
                                    # Variabel untuk menghitung kotak batas (bounding box) kecamatan
                                    "min_lat": 90, "max_lat": -90, 
                                    "min_lng": 180, "max_lng": -180
                                }
                            
                            # Update Bounding Box Kecamatan
                            # Kita cari titik paling ujung utara/selatan/barat/timur dari kecamatan ini
                            for coord in data['Koordinat']:
                                lat, lng = float(coord[0]), float(coord[1])
                                if lat < pengelompokan[key]["min_lat"]: pengelompokan[key]["min_lat"] = lat
                                if lat > pengelompokan[key]["max_lat"]: pengelompokan[key]["max_lat"] = lat
                                if lng < pengelompokan[key]["min_lng"]: pengelompokan[key]["min_lng"] = lng
                                if lng > pengelompokan[key]["max_lng"]: pengelompokan[key]["max_lng"] = lng

                            pengelompokan[key]["desa_list"].append(data)
                except: pass 

    # 2. Buat File Pecahan & Index Spatial
    if not os.path.exists(FOLDER_OUTPUT): os.makedirs(FOLDER_OUTPUT)
    
    spatial_index = []

    for key, info in pengelompokan.items():
        # Nama file pecahan
        nama_file = f"db_{key}.js"
        path_out = os.path.join(FOLDER_OUTPUT, nama_file)
        
        # Simpan file JS kecil
        isi_js = f"terimaDataPecahan({json.dumps(info['desa_list'], indent=None)});"
        with open(path_out, 'w') as f:
            f.write(isi_js)

        # Catat di Index: "Kecamatan A ada di koordinat sekian, filenya ini."
        spatial_index.append({
            "file": nama_file,
            "kecamatan": info['kecamatan'],
            "kabupaten": info['kabupaten'],
            # Simpan kotak batas agar HTML tau kapan harus memuat file ini
            "bounds": [
                [info["min_lat"], info["min_lng"]], # Sudut Kiri Bawah
                [info["max_lat"], info["max_lng"]]  # Sudut Kanan Atas
            ]
        })

    # Simpan Index Utama
    with open(FILE_INDEX, 'w') as f:
        f.write(f"var spatialIndex = {json.dumps(spatial_index, indent=None)};")

    print(f"SELESAI! ({len(spatial_index)} Kecamatan) ✅")

# ==========================================
# INPUT (REKAM GAMBAR / MANUAL)
# ==========================================
def rekam_koordinat_pintar():
    print("\n   [STANDBY] Menunggu Copy Koordinat (Editor / Manual)...")
    pyperclip.copy("") 
    last_paste = ""
    try:
        while True:
            current = pyperclip.paste()
            if current != last_paste and current.strip() != "":
                # Deteksi Multi-line (Dari Editor)
                if "\n" in current or len(current.split(',')) > 3:
                    print("   [DETEKSI] Data Polygon Masuk!")
                    coords = []
                    for line in current.split('\n'):
                        if "," in line:
                            parts = line.split(',')
                            if len(parts) >= 2:
                                try: coords.append([parts[0].strip(), parts[1].strip()])
                                except: pass
                    if len(coords) > 2: return coords
                last_paste = current
            time.sleep(0.5)
    except KeyboardInterrupt: return None

def main():
    print("="*60)
    print("  INPUT TAHAP 2: SMART LOADING SYSTEM")
    print("  (Database dipecah + Index Pintar)")
    print("="*60)
    
    # Update awal untuk migrasi data lama
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

            coords = rekam_koordinat_pintar()
            if not coords: print("Batal."); continue

            path_folder = os.path.join(ROOT_FOLDER, bersihkan_teks(provinsi), bersihkan_teks(kabupaten), bersihkan_teks(kecamatan))
            os.makedirs(path_folder, exist_ok=True)
            path_file = os.path.join(path_folder, bersihkan_teks(desa) + ".json")
            
            data = {"Provinsi": provinsi, "Kabupaten": kabupaten, "Kecamatan": kecamatan, "Desa": desa, "Koordinat": coords}
            with open(path_file, 'w') as f: json.dump(data, f, indent=4)
            
            print(f"\n[SUKSES] Desa {desa} tersimpan.")
            update_database_smart()
            
        except KeyboardInterrupt: break

if __name__ == "__main__":
    main()