#!/usr/bin/env python3
from pathlib import Path
import json,re,pandas as pd

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"data"/"input"
LEGACY=ROOT/"data"/"legacy.json"
OUT=ROOT/"data.json"
ALLOWED={"ORPP","ORHL","OREM","OREI","ORNM"}

def clean(v):
    if pd.isna(v): return None
    s=str(v).strip()
    return s or None

def numbered(v):
    s=clean(v)
    if not s:return []
    m=re.findall(r"\[\s*(\d+)\s*\]\s*(.*?)(?=\n\s*\[\s*\d+\s*\]\s*|$)",s,flags=re.S)
    if m:return [x[1].strip() for x in sorted(m,key=lambda z:int(z[0])) if x[1].strip()]
    return [x.strip() for x in re.split(r";|\n",s) if x.strip()]

def codes(v):
    out=[]
    for x in numbered(v):
        m=re.search(r"\b(\d{5})\b",x)
        if m:out.append(m.group(1))
    return out

def filter_kbli(orv,items):
    if orv not in {"ORHL","ORPP"}: return items
    items=[x for x in items if not str(x.get("kode") or "").startswith("46") and "perdagangan besar" not in (x.get("judul") or "").lower()]
    for i,x in enumerate(items,1):x["rank"]=i
    return items

def parse_tkt(v):
    if pd.isna(v): return None
    import datetime
    if isinstance(v,(pd.Timestamp,datetime.datetime,datetime.date)): return v.day
    s=str(v).strip()
    if not s: return None
    if re.fullmatch(r"\d+",s):
        n=int(s); return n if 1<=n<=9 else None
    return s if re.fullmatch(r"\d+\s*-\s*\d+",s) else None

def parse_tkt(v):
    if pd.isna(v): return None
    import datetime
    if isinstance(v,(pd.Timestamp,datetime.datetime,datetime.date)): return v.day
    s=str(v).strip()
    if not s: return None
    if re.fullmatch(r"\d+",s):
        n=int(s)
        return n if 1<=n<=9 else None
    return None

def read_xlsx(path):
    sheets=pd.ExcelFile(path).sheet_names
    # ORPP/ORHL latest workbook stores the same dashboard fields in Copy-of-Sort ORHL.
    if "Verifikasi Manual" in sheets:
        sheet="Verifikasi Manual"
    elif "Copy-of-Sort ORHL" in sheets and ("ORPP" in path.stem.upper() or "ORHL" in path.stem.upper()):
        sheet="Copy-of-Sort ORHL"
    else:
        raise ValueError(f"{path.name}: expected 'Verifikasi Manual' sheet")
    df=pd.read_excel(path,sheet_name=sheet,dtype=object)
    df.columns=[str(c).strip() for c in df.columns]
    default=next((x for x in ALLOWED if x in path.stem.upper()),None)
    aliases={
        "judul_ki":["Judul atau nama KI"],
        "nomor_ki":["Nomor kekayaan intelektual (KI)"],
        "jenis_ki":["Jenis kekayaan intelektual (KI)"],
        "tkt":["TKT Terverifikasi","TKT Terverifikasi.1","TKT Terverifikasi [TRL Verified]"],
        "nomor_kbli":["Nomor KBLI 2025","Nomor KBLI 2025 (Potensi Komersialisasi)","Nomor KBLI 2025\n(Potensi Komersialisasi)"],
        "judul_kbli":["Judul KBLI 2025 (Resmi BPS)"],
        "justifikasi":["Justifikasi","Justifikasi / Kondisi Komersialisasi"],
        "sektor":["Sektor Utama","Sektor Industri"],
        "or":["OR"]
    }
    def pick(names, required=True):
        for n in names:
            if n in df.columns:return n
        if required: raise ValueError(f"{path.name}: missing one of {names}")
        return None
    c={k:pick(v, k not in {"tkt","or"}) for k,v in aliases.items()}
    tkt_cols=[x for x in aliases["tkt"] if x in df.columns]
    out=[]
    for _,r in df.iterrows():
        title=clean(r[c["judul_ki"]]); ki=clean(r[c["nomor_ki"]])
        if not title and not ki: continue
        orv=(clean(r[c["or"]]) if c["or"] else None) or default
        if orv not in ALLOWED: raise ValueError(f"{path.name}: invalid/missing OR={orv!r}")
        tkt=None
        for tc in tkt_cols:
            v=parse_tkt(r[tc])
            if v is not None: tkt=v; break
        cs,ts=codes(r[c["nomor_kbli"]]),numbered(r[c["judul_kbli"]])
        kb=[{"rank":j+1,"kode":code,"judul":ts[j] if j<len(ts) else None} for j,code in enumerate(cs)]
        out.append({"or":orv,"nomor_ki":ki,"judul_ki":title,"jenis_ki":clean(r[c["jenis_ki"]]),
                    "trl":tkt,"sektor_utama":clean(r[c["sektor"]]),"justifikasi":clean(r[c["justifikasi"]]),
                    "kbli":filter_kbli(orv,kb)})
    return out

def main():
    rows=json.loads(LEGACY.read_text(encoding="utf-8")).get("records",[]) if LEGACY.exists() else []
    for p in sorted(INPUT.glob("*.xlsx")): rows.extend(read_xlsx(p))
    dedup={}
    for x in rows:
        # Keep distinct KI titles even when an organization reuses the same
        # registration/record number across separate KI entries.
        key=(x.get("or"), (x.get("nomor_ki") or "").strip(), (x.get("judul_ki") or "").strip().casefold())
        dedup[key]=x
    rows=list(dedup.values())
    for x in rows:x["kbli"]=filter_kbli(x.get("or"),x.get("kbli") or [])
    for x in rows:
        x["trl_6_plus"] = isinstance(x.get("trl"), int) and x.get("trl") >= 6
    rows.sort(key=lambda x:(x.get("or") or "",x.get("nomor_ki") or "",x.get("judul_ki") or ""))
    if any(x.get("or") not in ALLOWED or not x.get("judul_ki") for x in rows):raise ValueError("Validation failed")
    meta={
        "dashboard":"KBLI 2025 – Potensi Komersialisasi KI BRIN 2026",
        "schema_version":"1.1.0",
        "organizations":sorted(ALLOWED),
        "trl_6_plus_definition":"TKT Terverifikasi >= 6",
        "trl_6_plus_total":sum(1 for x in rows if x.get("trl_6_plus")),
        "trl_6_plus_by_or":{o:sum(1 for x in rows if x.get("or")==o and x.get("trl_6_plus")) for o in sorted(ALLOWED)}
    }
    OUT.write_text(json.dumps({"meta":meta,"records":rows},ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Generated {len(rows)} records; TKT >= 6: {meta['trl_6_plus_total']}")

if __name__=="__main__":main()
