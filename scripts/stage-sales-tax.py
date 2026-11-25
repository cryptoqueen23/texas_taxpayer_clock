"""Stage official sales tax CSVs with provenance and structural validation."""
import csv, hashlib, json, pathlib, urllib.request, datetime, sys
ROOT=pathlib.Path("staged-sales-tax")
ROOT.mkdir(exist_ok=True)
SOURCES={"city_county":"53pa-m7sm","county_mta_spd":"qsh8-tby8"}
report={"retrieved_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"sources":[],"published":False}
def fetch(url,limit):
    req=urllib.request.Request(url,headers={"User-Agent":"TexasTaxpayerClock/1.0"})
    with urllib.request.urlopen(req,timeout=120) as response:
        if not response.geturl().startswith("https://data.texas.gov/"):
            raise ValueError("Unexpected redirect")
        data=response.read(limit+1)
    if len(data)>limit: raise ValueError("Download exceeds size limit")
    return data
for name,id in SOURCES.items():
    entry={"name":name,"id":id}
    try:
        meta_url=f"https://data.texas.gov/api/views/{id}.json"
        before=json.loads(fetch(meta_url,5_000_000))
        if before.get("id")!=id: raise ValueError("Dataset identity mismatch")
        url=f"https://data.texas.gov/api/views/{id}/rows.csv?accessType=DOWNLOAD"
        raw=fetch(url,100_000_000)
        if raw.lstrip().startswith((b"<",b"{")): raise ValueError("Not CSV")
        file=ROOT/(name+".csv")
        file.write_bytes(raw)
        with file.open(encoding="utf-8-sig",newline="") as stream:
            reader=csv.reader(stream)
            header=next(reader)
            if len(header)<4 or len(set(header))!=len(header): raise ValueError("Invalid headers")
            count=0
            for row in reader:
                if len(row)!=len(header): raise ValueError("Malformed row")
                count+=1
        if count<1000: raise ValueError("Unexpectedly small dataset")
        after=json.loads(fetch(meta_url,5_000_000))
        if before.get("rowsUpdatedAt")!=after.get("rowsUpdatedAt"): raise ValueError("Source changed during download")
        entry.update(status="staged",url=url,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),rows=count,headers=header,rows_updated_at=after.get("rowsUpdatedAt"))
    except Exception as exc:
        entry.update(status="error",error=str(exc))
    report["sources"].append(entry)
(ROOT/"manifest.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if any(x["status"]!="staged" for x in report["sources"]): sys.exit(1)
