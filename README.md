# Dashboard KBLI 2025 – KI BRIN

Update visual dan UX:
- Filter OR/TKT/search di atas; seluruh KPI dan chart mengikuti filter.
- Pie chart TKT menampilkan jumlah dan persentase.
- Statistik KBLI 2025 top 8.
- Ringkasan TKT per OR dengan highlight.
- Detail KI dengan pagination dan page size 10/20/50.
- Penjelasan TRL 1–9.
- Logo BRIN sudah di-crop.
- Chart TKT 7–9 khusus dihapus; KPI TKT 7–9 tetap tersedia.

## Automation
`data/input/KBLI_2025_Dashboard_Master_5OR_QA_Corrected.xlsx` is the current master source.
Push an updated master workbook to `data/input/` and GitHub Actions will regenerate `data.json`.

The generator reads only the `Dashboard Data` sheet of the master workbook.
TRL/TRL is taken from `TKT Terverifikasi`.
For ORPP/ORHL, KBLI 46xxx / Perdagangan Besar is excluded.


## Dashboard UX v3
- Global filter bar is sticky and drives KPIs, charts, KBLI statistics and tables.
- Summary table uses TKT ranges 1–3, 4–6, 7–9.
- TRL explanation uses readiness colors from low readiness (1) to highest readiness (9).
- Detail KI pagination supports 10/20/50 rows per page.


### Summary table scroll fix
Removed sticky positioning from the TKT-per-OR summary header to prevent rows from rendering behind/above the header when the page is scrolled to this section.
