"""Acquire explicitly registered official file endpoints, preserving immutable copies."""
import hashlib, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
HOSTS = {"comptroller.texas.gov", "www.brb.texas.gov", "brb.texas.gov"}
def allowed(url):
    p = urllib.parse.urlsplit(url)
    return p.scheme == "https" and p.hostname in HOSTS and not p.username and not p.password
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl):
            raise ValueError("Unapproved redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)
def acquire(source):
    url = source["url"]
    if not allowed(url):
        raise ValueError("Unapproved source")
    with urllib.request.build_opener(Redirect()).open(url, timeout=90) as response:
        data = response.read(100_000_001)
        if len(data)>100_000_000: raise ValueError("File too large")
    if data.lstrip().lower().startswith((b"<!doctype html",b"<html")):
        raise ValueError("HTML received instead of dataset")
    if source["format"] == "xlsx" and not data.startswith(b"PK"):
        raise ValueError("Invalid workbook signature")
    digest = hashlib.sha256(data).hexdigest()
    folder = ROOT / "data/raw" / source["id"] / digest
    folder.mkdir(parents=True, exist_ok=True)
    (folder / ("source." + source["format"])).write_bytes(data)
    (folder / "manifest.json").write_text(json.dumps({"url":url,"sha256":digest,"retrieved_at":datetime.now(timezone.utc).isoformat()},indent=2))
    return digest
if __name__ == "__main__":
    sources=json.loads((ROOT/"data/metadata/sources.json").read_text())
    active=[s for s in sources if s.get("status")=="download_verified"]
    if not active: print("No verified direct file endpoints registered; no downloads attempted.")
    for source in active: print(source["id"], acquire(source))
