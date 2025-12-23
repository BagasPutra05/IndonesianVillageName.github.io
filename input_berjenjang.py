import json
import os
import re
import time
import pyperclip # pip install pyperclip

ROOT_FOLDER = "Data_Indonesia"

def bersihkan_teks(teks):
    bersih = re.sub(r'[^\w\s]', '', teks).strip()
    return bersih.replace(" ", "_").lower()

def is_valid_coord(text):
    """Cek apakah teks terlihat seperti koordinat (ada angka dan koma)"""
    if not text or "," not in text: return False
    # Cek apakah ada angka
    return any(char.isdigit() for char in text)

def rekam_satu_satu():
    """Looping untuk merekam clipboard berkali-kali"""
    list_koordinat = []
    last_clipboard = ""
    
    print("\n   [MODE REKAM AKTIF] Silakan COPY titik koordinat satu per satu...")
    print("   >> Tekan 'Ctrl+C' di Terminal ini jika sudah selesai merekam desa ini.")
    
    # Kosongkan clipboard dulu
    pyperclip.copy("") 
    
    try:
        while True:
            current_clipboard = pyperclip.paste()
            
            # Jika ada data baru yang berbeda dari sebelumnya
            if current_clipboard != last_clipboard and current_clipboard.strip() != "":
                
                # Cek apakah ini koordinat valid
                if is_valid_coord(current_clipboard):
                    parts = current_clipboard.split(',')
                    if len(parts) >= 2:
                        lat = parts[0].strip()
                        long = parts[1].strip()
                        
                        # Tambahkan ke list
                        list_koordinat.append([lat, long])
                        print(f"      [+] Titik ke-{len(list_koordinat)} Masuk: {lat}, {long}")
                
                # Update last_clipboard agar tidak duplikat baca
                last_clipboard = current_clipboard
            
            time.sleep(0.5) # Cek setiap setengah detik
            
    except KeyboardInterrupt:
        # Ini akan jalan saat user tekan Ctrl+C untuk menyudahi rekaman
        return list_koordinat

def main():
    print("="*50)
    print("  INPUT KOORDINAT SATU-SATU (AKUMULASI)")
    print("  Cara Stop per Desa: Tekan Ctrl+C di terminal")
    print("="*50)

    while True:
        try:
            print("\n" + "-"*30)
            print("INPUT WILAYAH BARU")
            provinsi = input("1. Provinsi : ").strip()
            kabupaten = input("2. Kabupaten: ").strip()
            kecamatan = input("3. Kecamatan: ").strip()
            desa      = input("4. Nama Desa: ").strip()

            if not (provinsi and kabupaten and kecamatan and desa):
                print("[!] Data tidak boleh kosong!")
                continue

            # --- MULAI REKAM KOORDINAT ---
            coords = rekam_satu_satu()

            if not coords:
                print("\n[INFO] Tidak ada koordinat yang tersimpan. Data desa dibatalkan.")
                continue

            # --- SIMPAN DATA ---
            path_folder = os.path.join(ROOT_FOLDER, bersihkan_teks(provinsi), bersihkan_teks(kabupaten), bersihkan_teks(kecamatan))
            os.makedirs(path_folder, exist_ok=True)
            
            nama_file = bersihkan_teks(desa) + ".json"
            path_file_lengkap = os.path.join(path_folder, nama_file)

            data_json = {
                "Provinsi": provinsi,
                "Kabupaten": kabupaten,
                "Kecamatan": kecamatan,
                "Desa": desa,
                "Koordinat": coords
            }

            with open(path_file_lengkap, 'w') as f:
                json.dump(data_json, f, indent=4)

            print(f"\n[SUKSES] Desa {desa} disimpan dengan {len(coords)} titik!")
            
        except KeyboardInterrupt:
            print("\n\n[KELUAR] Program dihentikan. Sampai jumpa!")
            break

if __name__ == "__main__":
    main()