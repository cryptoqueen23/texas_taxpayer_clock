"""Report acquisition readiness without publishing or claiming a refresh."""
import json
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
def readiness(sources):
    return {"registered":len(sources),"verified_downloads":sum(s.get("status")=="download_verified" for s in sources),"sources":[{"id":s["id"],"url":s["url"],"status":s.get("status","unknown")} for s in sources]}
if __name__=="__main__":
    report=readiness(json.loads((ROOT/"data/metadata/sources.json").read_text()))
    report["checked_at"]=datetime.now(timezone.utc).isoformat()
    report["status"]="ready_for_attempt" if report["verified_downloads"] else "blocked_no_verified_endpoints"
    report["published_data_changed"]=False
    (ROOT/"acquisition-readiness.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
