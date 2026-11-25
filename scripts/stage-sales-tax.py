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
        url=f"https://data.texas.gov/resource/{id}.csv?$limit=50000&$order=:id"
        chunks=[]
        offset=0
        header_line=None
        while True:
            page=fetch(url+f"&$offset={offset}",50_000_000)
            lines=list(csv.reader(page.decode("utf-8-sig").splitlines(keepends=True)))
            if not lines: raise ValueError("Empty response")
            if header_line is None: header_line=lines[0]
            if lines[0]!=header_line: raise ValueError("Header changed between pages")
            chunks.extend(lines[1:])
            if len(lines)-1<50000: break
            offset+=50000
            if offset>1000000: raise ValueError("Row limit exceeded")
        import io
        buf=io.StringIO(newline="")
        writer=csv.writer(buf)
        writer.writerow(header_line)
        writer.writerows(chunks)
        raw=buf.getvalue().encode("utf-8")
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
