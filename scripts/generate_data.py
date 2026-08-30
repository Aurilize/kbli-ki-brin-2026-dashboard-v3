#!/usr/bin/env python3
"""
Generate dashboard data from the Excel master.
Single source for current dashboard:
  - Dashboard Data sheet in the master workbook
  - TKT/TRL = TKT Terverifikasi
  - Sektor Utama = first sector ([1]) when multiple sectors are stored
  - ORPP/ORHL: exclude wholesale KBLI 46xxx
"""
from pathlib import Path
import json, re, sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "input"
OUT = ROOT / "data.json"

MASTER_CANDIDATES = [
    INPUT / "KBLI_2025_Dashboard_Master_5OR_QA_Corrected_RESTORED302.xlsx",
    INPUT / "KBLI_2025_Dashboard_Master_5OR_QA_Corrected_RESTORED302.xlsx",
    INPUT / "KBLI_2025_Dashboard_Master_5OR_REVIEW_REANALYZED_FINAL.xlsx",
    INPUT / "master.xlsx",
]

def clean(v):
    if pd.isna(v):
        return None
    s = str(v).strip()
    return s or None

def numbered(s):
    s = clean(s) or ""
    pairs = re.findall(r"\[\s*(\d+)\s*\]\s*(.*?)(?=\n\s*\[\s*\d+\s*\]\s*|$)", s, flags=re.S)
    if pairs:
        return [(int(i), v.strip()) for i, v in pairs if v.strip()]
    return [(i+1, x.strip()) for i, x in enumerate(re.split(r";|\n", s)) if x.strip()]

def first_sector(s):
    s = clean(s)
    if not s:
        return None
    pairs = numbered(s)
    if pairs:
        return pairs[0][1]
    return s

def valid_kbli(code):
    return re.sub(r"\D", "", str(code)) if code is not None else ""

def wholesale(code, title):
    c = valid_kbli(code)
    t = (title or "").lower()
    return c.startswith("46") or "perdagangan besar" in t

def pick_master():
    for p in MASTER_CANDIDATES:
        if p.exists():
            return p
    xs = sorted(INPUT.glob("*.xlsx"))
    if len(xs) == 1:
        return xs[0]
    raise FileNotFoundError(
        "Tidak menemukan master workbook. Upload salah satu workbook master ke data/input/."
    )

def main():
    master = pick_master()
    df = pd.read_excel(master, sheet_name="Dashboard Data", dtype=object)
    required = [
        "OR","Nomor KI","Judul KI","Jenis KI","TKT Terverifikasi",
        "Sektor Utama","Nomor KBLI 2025","Judul KBLI 2025","Justifikasi"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom wajib hilang dari {master.name}: {missing}")

    rows = []
    for _, r in df.iterrows():
        orv = clean(r["OR"])
        title = clean(r["Judul KI"])
        if not orv or not title:
            continue

        # TKT/TRL must come from verified TKT only.
        raw_tkt = clean(r["TKT Terverifikasi"])
        try:
            tkt = int(float(raw_tkt)) if raw_tkt is not None else None
        except Exception:
            tkt = None

        kc = numbered(r["Nomor KBLI 2025"])
        kt = dict(numbered(r["Judul KBLI 2025"]))
        kblis = []
        for rank, code in kc[:3]:
            code = valid_kbli(code)
            if not code:
                continue
            title_kbli = kt.get(rank)
            if orv in {"ORPP", "ORHL"} and wholesale(code, title_kbli):
                continue
            kblis.append({"rank": rank, "kode": code, "judul": title_kbli})

        rows.append({
            "or": orv,
            "nomor_ki": clean(r["Nomor KI"]),
            "judul_ki": title,
            "jenis_ki": clean(r["Jenis KI"]),
            "trl": tkt,
            "sektor_utama": first_sector(r["Sektor Utama"]),
            "kbli": kblis,
            "justifikasi": clean(r["Justifikasi"]),
        })

    # Deduplicate on OR + KI number/title, retaining the last row (latest adjustment).
    dedup = {}
    for row in rows:
        key = (row["or"], row["nomor_ki"] or row["judul_ki"].casefold())
        dedup[key] = row
    rows = list(dedup.values())

    for row in rows:
        row["trl_6_plus"] = isinstance(row["trl"], int) and row["trl"] >= 6

    rows.sort(key=lambda x: (x["or"], x["nomor_ki"] or "", x["judul_ki"]))

    payload = {
        "meta": {
            "dashboard": "KBLI 2025 – KI BRIN",
            "source_workbook": master.name,
            "source_sheet": "Dashboard Data",
            "trl_source": "TKT Terverifikasi",
            "sector_rule": "Sektor Utama menggunakan item [1] jika sumber berisi beberapa sektor",
            "wholesale_rule": "ORPP/ORHL mengecualikan kode 46xxx dan judul Perdagangan Besar",
            "total_records": len(rows),
            "trl_6_plus_total": sum(1 for r in rows if r["trl_6_plus"]),
        },
        "records": rows,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(rows)} records from {master.name}")

if __name__ == "__main__":
    main()
