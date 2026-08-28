# KBLI 2025 – Potensi Komersialisasi KI BRIN 2026

Dashboard data-driven untuk ORPP, ORHL, OREM, OREI, dan ORNM.

## Isi
- `index.html`: dashboard statis yang membaca `data.json`.
- `data.json`: master dataset 5 OR saat paket dibuat.
- `data/legacy.json`: baseline normalized dataset untuk menjaga data tetap ada saat workflow berjalan.
- `data/kbli_2025_combined.json`: referensi KBLI 2025.
- `scripts/generate_data.py`: generator dari workbook `Verifikasi Manual`.
- `.github/workflows/generate-data.yml`: otomatis regenerate `data.json`.

## Aturan bisnis
Untuk ORPP dan ORHL, semua KBLI perdagangan besar dikeluarkan: kode `46xxx` atau judul mengandung `Perdagangan Besar`.

## Update data
Taruh workbook baru di `data/input/`, push ke `main`, dan GitHub Actions akan regenerate `data.json`.

## GitHub Pages
Settings → Pages → Build and deployment → Deploy from a branch → `main` / `/ (root)` → Save.
