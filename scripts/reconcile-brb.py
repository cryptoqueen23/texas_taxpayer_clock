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
if __name__=="__main__":
    report = {"reports":[reconcile(entity_id,2025) for entity_id in ("050-101-03","050-000-00")], "school_discovery":inspect_school()}
    output = json.dumps(report,indent=2)
    (OUT/"report.json").write_text(output)
    print(output)
