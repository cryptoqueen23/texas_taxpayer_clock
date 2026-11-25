"""Read-only official Socrata metadata monitoring; never publishes financial values."""
import json, urllib.request, datetime, pathlib, sys
sources={"city_county_sales_tax":"53pa-m7sm","county_mta_spd_sales_tax":"qsh8-tby8"}
report={"checked_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"sources":[]}
for name,id in sources.items():
    url=f"https://data.texas.gov/api/views/{id}.json"
    item={"name":name,"id":id,"url":url}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"TexasTaxpayerClock source monitor/1.0","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=45) as response:
            data=json.load(response)
        if data.get("id")!=id: raise ValueError("Unexpected dataset ID")
        item.update(status="reachable",title=data.get("name"),rows_updated_at=data.get("rowsUpdatedAt"),metadata_updated_at=data.get("viewLastModified"))
    except Exception as exc:
        item.update(status="error",error=str(exc))
    report["sources"].append(item)
pathlib.Path("source-monitor-report.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if any(s["status"]!="reachable" for s in report["sources"]): sys.exit(1)
