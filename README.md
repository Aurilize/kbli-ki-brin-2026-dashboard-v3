# KBLI 2025 – Potensi Komersialisasi KI BRIN 2026

Dashboard data-driven untuk ORPP, ORHL, OREM, OREI, dan ORNM.

## Isi
- `index.html`: dashboard statis yang membaca `data.json`.
- `data.json`: master dataset 5 OR saat paket dibuat.
- `data/legacy.json`: baseline normalized dataset untuk menjaga data tetap ada saat workflow berjalan.
- `data/kbli_2025_combined.json`: referensi KBLI 2025.
- `scripts/generate_data.py`: generator dari workbook `Verifikasi Manual`.
- `.github/workflows/generate-data.yml`: otomatis regenerate `data.json`.

## Sumber TRL

Nilai TRL pada dashboard diambil langsung dari kolom **`TKT Terverifikasi`** pada sheet `Verifikasi Manual`. Nilai tidak dihitung atau diinferensikan dari kolom lain. Workbook lama yang menggunakan header `TKT Terverifikasi [TRL Verified]` diperlakukan sebagai padanan kolom tersebut.

## Aturan bisnis
Untuk ORPP dan ORHL, semua KBLI perdagangan besar dikeluarkan: kode `46xxx` atau judul mengandung `Perdagangan Besar`.

## Update data
Taruh workbook baru di `data/input/`, push ke `main`, dan GitHub Actions akan regenerate `data.json`.

## GitHub Pages
Settings → Pages → Build and deployment → Deploy from a branch → `main` / `/ (root)` → Save.


### Catatan TKT
Beberapa export Excel memiliki duplikasi header `TKT Terverifikasi`, sehingga pandas dapat membaca kolom kedua sebagai `TKT Terverifikasi.1`. Generator memilih nilai terverifikasi yang terisi. Jika angka TKT tersimpan dengan format tanggal Excel, hari tanggal dikonversi kembali menjadi angka TKT (mis. 2026-05-06 → 6).
