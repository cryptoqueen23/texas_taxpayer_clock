import json
from pathlib import Path
import duckdb
root = Path(__file__).resolve().parents[1]
sources = json.loads((root / "data/metadata/sources.json").read_text())
assert len({s["id"] for s in sources}) == len(sources)
assert all(s["url"].startswith("https://") for s in sources)
db = duckdb.connect(":memory:")
db.execute((root / "database/schema.sql").read_text())
print("Source registry and database schema validated; financial records not yet ingested.")
