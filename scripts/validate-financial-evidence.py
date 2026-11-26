import json
import re
from pathlib import Path
from decimal import Decimal

root = Path(__file__).resolve().parents[1]
data = json.loads((root / "data/metadata/financial-evidence.json").read_text(), parse_float=Decimal)
assert data["schema_version"] == 1
ids = set()
for r in data["records"]:
    assert r["id"] not in ids, r["id"]
    ids.add(r["id"])
    assert r["status"] in {"pending", "source_verified", "reconciled", "discrepancy", "unavailable", "modeled"}
    assert r["entity"] and r["metric"] and r["period"] and r["unit"]
    if r["status"] in {"source_verified", "reconciled", "discrepancy"}:
        for key in ("entity_id", "agency", "original_url", "filename", "sha256", "retrieved_at", "locator", "scope", "reviewer", "reviewed_at"):
            assert r[key], (r["id"], key)
        assert r["original_url"].startswith("https://")
        assert re.fullmatch(r"[0-9a-f]{64}", r["sha256"])
        assert r["reported_value"] is not None
    if r["status"] in {"reconciled", "discrepancy"}:
        assert r["formula"]
        assert all(r[k] is not None for k in ("published_value", "recalculated_value", "difference"))
        assert r["difference"] == r["recalculated_value"] - r["published_value"]
        assert (r["difference"] == 0) == (r["status"] == "reconciled")
    if r["status"] == "modeled":
        assert r["formula"] and r["scope"]
    if r["status"] == "pending":
        assert r["reviewed_at"] is None
print(f"Evidence registry structure validated: {len(ids)} records; this does not verify original sources.")
