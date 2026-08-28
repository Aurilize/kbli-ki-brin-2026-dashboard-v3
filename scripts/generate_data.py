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
    default=next((x for x in ALLOWED if x in path.stem.upper()),None)

    # Response workbooks keep KI identity in "Form Responses 1" while
    # verified TKT + KBLI are stored in "Verifikasi Manual". The rows are
    # aligned, so join by row index. This is the critical source mapping.
    if "Form Responses 1" in sheets and "Verifikasi Manual" in sheets:
        form=pd.read_excel(path,sheet_name="Form Responses 1",dtype=object)
        ver=pd.read_excel(path,sheet_name="Verifikasi Manual",dtype=object)
        if "Judul atau nama KI" not in form.columns or "Nomor kekayaan intelektual (KI)" not in form.columns:
            raise ValueError(f"{path.name}: identity columns missing from Form Responses 1")
        tkt_col=next((c for c in ver.columns if str(c).strip()=="TKT Terverifikasi"),None)
        if tkt_col is None:
            raise ValueError(f"{path.name}: missing 'TKT Terverifikasi' in Verifikasi Manual")
        out=[]
        n=min(len(form),len(ver))
        for i in range(n):
            fr=form.iloc[i]; vr=ver.iloc[i]
            title=clean(fr["Judul atau nama KI"]); ki=clean(fr["Nomor kekayaan intelektual (KI)"])
            if not title and not ki: continue
            orv=(clean(vr["OR"]) if "OR" in ver.columns else None) or default
            if orv not in ALLOWED: raise ValueError(f"{path.name}: invalid/missing OR={orv!r}")
            tkt=parse_tkt(vr[tkt_col])
            cs,ts=codes(vr.get("Nomor KBLI 2025")),numbered(vr.get("Judul KBLI 2025 (Resmi BPS)"))
            kb=[{"rank":j+1,"kode":c,"judul":ts[j] if j<len(ts) else None} for j,c in enumerate(cs)]
            out.append({"or":orv,"nomor_ki":ki,"judul_ki":title,
                        "jenis_ki":clean(fr.get("Jenis kekayaan intelektual (KI)")),
                        "trl":tkt,"sektor_utama":clean(vr.get("Sektor Utama")),
                        "justifikasi":clean(vr.get("Justifikasi")),"kbli":filter_kbli(orv,kb)})
        return out

    # Legacy/ORPP-ORHL workbooks: use identity columns directly if present.
    df=pd.read_excel(path,sheet_name="Copy-of-Sort ORHL" if "Copy-of-Sort ORHL" in sheets else sheets[0],dtype=object)
    df.columns=[str(c).strip() for c in df.columns]
    required=["Judul atau nama KI","Nomor kekayaan intelektual (KI)","Jenis kekayaan intelektual (KI)",
              "Nomor KBLI 2025","Judul KBLI 2025 (Resmi BPS)","Justifikasi","Sektor Utama"]
    missing=[x for x in required if x not in df.columns]
    if missing: raise ValueError(f"{path.name}: missing {missing}")
    tkt_col=next((c for c in ["TKT Terverifikasi","TKT Terverifikasi.1","TKT Terverifikasi [TRL Verified]"] if c in df.columns),None)
    out=[]
    for _,r in df.iterrows():
        title=clean(r["Judul atau nama KI"]); ki=clean(r["Nomor kekayaan intelektual (KI)"])
        if not title and not ki: continue
        orv=(clean(r["OR"]) if "OR" in df.columns else None) or default
        if orv not in ALLOWED: raise ValueError(f"{path.name}: invalid/missing OR={orv!r}")
        tkt=parse_tkt(r[tkt_col]) if tkt_col else None
        cs,ts=codes(r["Nomor KBLI 2025"]),numbered(r["Judul KBLI 2025 (Resmi BPS)"])
        kb=[{"rank":j+1,"kode":c,"judul":ts[j] if j<len(ts) else None} for j,c in enumerate(cs)]
        out.append({"or":orv,"nomor_ki":ki,"judul_ki":title,
                    "jenis_ki":clean(r["Jenis kekayaan intelektual (KI)"]),
                    "trl":tkt,"sektor_utama":clean(r["Sektor Utama"]),
                    "justifikasi":clean(r["Justifikasi"]),"kbli":filter_kbli(orv,kb)})
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
