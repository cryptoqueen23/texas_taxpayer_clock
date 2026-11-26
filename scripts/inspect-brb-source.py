"""Inspect official BRB dataset metadata before selecting financial columns."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlparse

URL = "https://data.texas.gov/api/views/3qmf-seku.json"
def fetch(url, max_bytes=5_000_000):
    with urlopen(Request(url, headers={"User-Agent":"TexasTaxpayerClock/1.0 evidence research"}), timeout=45) as response:
        parsed = urlparse(response.geturl())
        if parsed.scheme != "https" or parsed.hostname != "data.texas.gov":
            raise ValueError("Unexpected final source host")
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ValueError("Response exceeds limit")
        return raw

def main():
    raw = fetch(URL)
    metadata = json.loads(raw)
    if metadata.get("id") != "3qmf-seku":
        raise ValueError("Dataset identifier mismatch")
    digest = hashlib.sha256(raw).hexdigest()
    destination = Path("brb-source-inspection")
    destination.mkdir(exist_ok=True)
    (destination / (digest + ".json")).write_bytes(raw)
    report = {"url":URL,"retrieved_at":datetime.now(timezone.utc).isoformat(),
              "sha256":digest,"dataset_name":metadata.get("name"),
              "columns":[{"name":c.get("name"),"field":c.get("fieldName"),"type":c.get("dataTypeName")} for c in metadata.get("columns",[])],
              "published_data_changed":False,"financial_verification_completed":False}
    if not report["columns"]:
        raise ValueError("No source columns returned")
    (destination / "inspection.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__ == "__main__":
    main()
