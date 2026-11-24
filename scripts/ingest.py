"""Import explicitly mapped CSV/XLSX records into a normalized staging file."""
import argparse, csv, hashlib, json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from openpyxl import load_workbook
def normalize(rows, mapping):
    seen=set()
    for row in rows:
        gid=str(row[mapping["government_id"]] or "").strip()
        period=str(row[mapping["period"]] or "").strip()
        if not gid or not period: raise ValueError("Missing identifier or period")
        raw=row[mapping["amount"]]
        amount=None if raw is None or str(raw).strip()=="" else Decimal(str(raw).replace(",","").replace("$",""))
        if amount is not None and not amount.is_finite(): raise ValueError("Nonfinite amount")
        key=(gid,period,mapping["metric"])
        if key in seen: raise ValueError(f"Duplicate observation: {key}")
        seen.add(key)
        yield {"government_id":gid,"period":period,"metric":mapping["metric"],"amount":str(amount) if amount is not None else None,"unit":mapping["unit"],"status":mapping["status"] if amount is not None else "unavailable"}
def read_rows(path,mapping):
    if path.suffix.lower()==".csv":
        with path.open(encoding="utf-8-sig",newline="") as f:
            yield from csv.DictReader(f)
    elif path.suffix.lower()==".xlsx":
        wb=load_workbook(path,read_only=True,data_only=True)
        try:
            rows=wb[mapping["sheet"]].iter_rows(min_row=mapping.get("header_row",1),values_only=True)
            headers=next(rows)
            for values in rows:
                if any(v is not None for v in values): yield dict(zip(headers,values))
        finally: wb.close()
    else: raise ValueError("Unsupported format")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("file",type=Path);p.add_argument("mapping",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args(); m=json.loads(a.mapping.read_text())
    if m["status"] not in ("reported","provisional"): raise ValueError("Invalid status")
    records=list(normalize(read_rows(a.file,m),m))
    if not records: raise ValueError("Empty dataset")
    result={"source_id":m["source_id"],"source_sha256":hashlib.sha256(a.file.read_bytes()).hexdigest(),"records":records}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2))
if __name__=="__main__": main()
