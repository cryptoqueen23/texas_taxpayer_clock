import json
import hashlib
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "brb-reconciliation"
OUT.mkdir(exist_ok=True)
BASE = "https://data.texas.gov/resource/3qmf-seku.json"
FIELDS = {"principal":"totalprincipaloutstanding","interest":"totalinterestoutstanding","repayment":"totaldebtserviceoutstanding"}
def fetch(params):
    url = BASE + "?" + urlencode(params)
    with urlopen(Request(url, headers={"User-Agent":"TexasTaxpayerClock/1.0"}), timeout=60) as response:
        if response.geturl() != url:
            raise ValueError("Unexpected redirect")
        raw = response.read(20_000_001)
    if len(raw)>20_000_000:
        raise ValueError("Response too large")
    digest = hashlib.sha256(raw).hexdigest()
    (OUT / (digest+".json")).write_bytes(raw)
    return json.loads(raw), {"url":url,"sha256":digest,"retrieved_at":datetime.now(timezone.utc).isoformat()}
def reconcile(entity_id, year):
    where = f"govid = '{entity_id}' AND fiscalyear = {year}"
    count, count_evidence = fetch({"$where":where,"$select":"count(*) AS n"})
    expected = int(count[0]["n"])
    if not 0 < expected < 10000:
        raise ValueError(f"Unexpected record count: {expected}")
    rows, evidence = fetch({"$where":where,"$limit":10000,"$order":":id"})
    if len(rows)!=expected or any(r.get("govid")!=entity_id or int(r["fiscalyear"])!=year for r in rows):
        raise ValueError("Source count or identity mismatch")
    dataset = json.loads((ROOT/"public/data/local-debt-2025.json").read_text())
    if dataset["fiscalYear"]!=year:
        raise ValueError("Published fiscal year mismatch")
    baseline = next(r for r in dataset["records"] if r["id"]==entity_id)
    results = {}
    for metric, field in FIELDS.items():
        values = [Decimal(str(r[field])) for r in rows]
        if not all(v.is_finite() for v in values):
            raise ValueError("Nonfinite financial value")
        total = sum(values, Decimal(0))
        published = Decimal(str(baseline[metric]))
        results[metric] = {"source_total":str(total),"published":str(published),"difference":str(total-published),"matches":total==published}
    return {"entity_id":entity_id,"year":year,"source_count":len(rows),"published_count":baseline["count"],"source_evidence":evidence,"count_evidence":count_evidence,"metrics":results,"all_match":all(r["matches"] for r in results.values()) and len(rows)==baseline["count"],"published_data_changed":False,"review_required":True}
def inspect_school():
    where = "fiscalyear = 2025 AND (govid = '050-910-02' OR upper(governmentname) like '%COPPERAS COVE%')"
    rows, evidence = fetch({"$where":where,"$select":"govid,governmentname,governmenttype,count(*) AS n","$group":"govid,governmentname,governmenttype","$limit":1000})
    historical, historical_evidence = fetch({"$where":"(govid = '050-910-02' OR upper(governmentname) like '%COPPERAS COVE%') AND fiscalyear >= 2020","$select":"fiscalyear,govid,governmentname,governmenttype,count(*) AS n","$group":"fiscalyear,govid,governmentname,governmenttype","$limit":1000})
    return {"historical_results":historical,"historical_evidence":historical_evidence,"query_results":rows,"evidence":evidence,"published_baseline_available":False,"review_required":True,"note":"Missing published debt row is not zero debt. Confirm identity and source coverage before reconciliation."}
def statewide():
    where = "fiscalyear = 2025"
    count, ce = fetch({"$where":where,"$select":"count(*) AS n"})
    expected = int(count[0]["n"])
    if not 0 < expected <= 500000:
        raise ValueError("Unexpected statewide source count")
    groups = {}
    evidence = []
    seen = set()
    for offset in range(0, expected, 5000):
        rows, ev = fetch({"$where":where,"$select":":id AS row_id,govid,fiscalyear,totalprincipaloutstanding,totalinterestoutstanding,totaldebtserviceoutstanding","$order":":id","$limit":5000,"$offset":offset})
        evidence.append(ev)
        if len(rows) != min(5000, expected-offset):
            raise ValueError("Incomplete source page")
        for row in rows:
            rid = row["row_id"]
            if rid in seen or int(row["fiscalyear"]) != 2025 or not row.get("govid"):
                raise ValueError("Duplicate or invalid source row")
            seen.add(rid)
            g = groups.setdefault(row["govid"], {"count":0, **{m:Decimal(0) for m in FIELDS}})
            g["count"] += 1
            for m, field in FIELDS.items():
                v = Decimal(str(row[field]))
                if not v.is_finite():
                    raise ValueError("Nonfinite source value")
                g[m] += v
    end, end_evidence = fetch({"$where":where,"$select":"count(*) AS n"})
    if len(seen) != expected or int(end[0]["n"]) != expected:
        raise ValueError("Source count changed or incomplete retrieval")
    data = json.loads((ROOT/"public/data/local-debt-2025.json").read_text())
    if data["fiscalYear"] != 2025:
        raise ValueError("Baseline year mismatch")
    baseline = {r["id"]:r for r in data["records"]}
    if len(baseline) != len(data["records"]):
        raise ValueError("Duplicate baseline IDs")
    missing = sorted(baseline.keys()-groups.keys())
    extra = sorted(groups.keys()-baseline.keys())
    differences = []
    for gid in sorted(baseline.keys() & groups.keys()):
        a,b = groups[gid],baseline[gid]
        delta = {m:str(a[m]-Decimal(str(b[m]))) for m in ("count", *FIELDS)}
        if any(Decimal(v)!=0 for v in delta.values()):
            differences.append({"id":gid,"difference":delta})
    totals = {m:{"source":str(sum(g[m] for g in groups.values())),"published":str(sum(Decimal(str(r[m])) for r in baseline.values()))} for m in FIELDS}
    for t in totals.values():
        t["difference"] = str(Decimal(t["source"])-Decimal(t["published"]))
    return {"source_rows":expected,"source_entities":len(groups),"published_entities":len(baseline),"exact_matches":len(baseline.keys() & groups.keys())-len(differences),"missing_from_source":missing,"missing_from_website":extra,"differences":differences,"totals":totals,"all_match":not (missing or extra or differences),"count_evidence":ce,"end_count_evidence":end_evidence,"page_evidence":evidence,"published_data_changed":False,"review_required":True}
if __name__=="__main__":
    report = {"reports":[reconcile(entity_id,2025) for entity_id in ("050-101-03","050-000-00")], "school_discovery":inspect_school(), "statewide":statewide()}
    output = json.dumps(report,indent=2)
    (OUT/"report.json").write_text(output)
    print(output)
