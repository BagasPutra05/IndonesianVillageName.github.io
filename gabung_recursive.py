import os
import json

ROOT_FOLDER = "Data_Indonesia"
FILE_OUTPUT = "db_desa.js"

def main():
    semua_desa = []
    jumlah_file = 0

    print(f"Sedang menelusuri folder '{ROOT_FOLDER}'...")

    # os.walk akan masuk ke semua sub-folder secara otomatis
    for root, dirs, files in os.walk(ROOT_FOLDER):
        for filename in files:
            if filename.endswith(".json"):
                path_lengkap = os.path.join(root, filename)
                
                try:
                    with open(path_lengkap, 'r') as f:
                        data = json.load(f)
                        # Validasi sederhana: pastikan ada koordinat
                        if "Koordinat" in data:
                            semua_desa.append(data)
                            jumlah_file += 1
                except Exception as e:
                    print(f"[ERROR] Gagal baca {filename}: {e}")

    # Simpan ke JS
    json_str = json.dumps(semua_desa, indent=None)
    isi_file = f"var dataSeluruhIndonesia = {json_str};"

    with open(FILE_OUTPUT, 'w') as f:
        f.write(isi_file)

    print("-" * 30)
    print(f"[SELESAI] Total {jumlah_file} desa berhasil digabung.")
    print(f"Database siap digunakan di: {FILE_OUTPUT}")

if __name__ == "__main__":
    main()