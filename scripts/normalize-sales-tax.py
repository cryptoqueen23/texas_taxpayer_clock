"""Normalize staged monthly allocations; fail closed on unknown formats."""
import csv, json, pathlib, hashlib, calendar, importlib.util
from decimal import Decimal
root=pathlib.Path("staged-sales-tax")
spec=importlib.util.spec_from_file_location("reconcile",pathlib.Path(__file__).with_name("reconcile-sales-tax.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
manifest=json.loads((root/"manifest.json").read_text())
def period(row):
    m=row["report_month"].strip()
    if m.isdigit(): month=int(m)
    else: month={n.lower():i for i,n in enumerate(calendar.month_name) if i}[m.lower()]
    if not 1<=month<=12: raise ValueError("Invalid month")
    return f'{int(row["report_year"]):04d}-{month:02d}'
def cents(s):
    v=Decimal(s.replace(",","").replace("$","").strip())*100
    if not v.is_finite() or v!=v.to_integral_value(): raise ValueError("Invalid cents")
    return int(v)
def normalize(row,city):
    typ="CITY" if city else row["type"].strip().upper()
    name=row["city" if city else "name"].strip()
    county=row["county"].strip() if city else None
    rate=float(Decimal(row["current_rate"].strip().rstrip("%")))
    return [typ,name,county,rate,*[cents(row[k]) for k in ("net_payment_this_period","comparable_payment_prior_year","payments_to_date","previous_payments_to_date")]]
groups=[]
for source in manifest["sources"]:
    if source["status"]!="staged": raise ValueError("Unverified source")
    file=root/(source["name"]+".csv")
    if hashlib.sha256(file.read_bytes()).hexdigest()!=source["sha256"]: raise ValueError("Checksum mismatch")
    with file.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=source["rows"]: raise ValueError("Row count mismatch")
    latest=max(map(period,rows))
    selected=[r for r in rows if period(r)==latest]
    print(source["name"],latest,"period types",sorted({r["report_period_type"] for r in selected}),"rows",len(selected))
    groups.append((latest,[normalize(r,source["name"]=="city_county") for r in selected]))
if len({p for p,_ in groups})!=1: raise ValueError("Source periods differ")
candidate={"latestPeriod":groups[0][0],"fields":mod.FIELDS,"sources":manifest["sources"],"records":[r for _,rows in groups for r in rows]}
old=json.loads(pathlib.Path("public/data/local-sales-tax-2026-11.json").read_text())
report=mod.compare(old,candidate)
(root/"candidate.json").write_text(json.dumps(candidate))
(root/"reconciliation.json").write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ("missing","added","same_period_revisions")},indent=2))
print("Missing:",len(report["missing"]),"Added:",len(report["added"]),"Revisions:",len(report["same_period_revisions"]))
