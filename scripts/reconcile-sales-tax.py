"""Compare normalized candidate snapshots; no publication side effects."""
import json, pathlib, re, math, sys
FIELDS=["type","name","county","ratePercent","paymentCents","priorPaymentCents","ytdCents","priorYtdCents"]
def index(data):
    if data["fields"]!=FIELDS or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])",data["latestPeriod"]): raise ValueError("Invalid schema or period")
    result={}
    for row in data["records"]:
        if len(row)!=8: raise ValueError("Invalid row width")
        typ,name,county,rate,*amounts=row
        if typ not in ("CITY","COUNTY","MTA","SPD") or not isinstance(name,str) or not name.strip(): raise ValueError("Invalid identity")
        if county is not None and not isinstance(county,str): raise ValueError("Invalid county")
        if type(rate) not in (int,float) or not math.isfinite(rate) or rate<0 or rate>100: raise ValueError("Invalid rate")
        if any(type(v)!=int or abs(v)>9007199254740991 for v in amounts): raise ValueError("Invalid integer cents")
        key=(typ,name.strip().casefold(),(county or "").strip().casefold())
        if key in result: raise ValueError("Duplicate identity")
        result[key]=row
    if not result: raise ValueError("Empty dataset")
    return result
def compare(old,new):
    a,b=index(old),index(new)
    if new["latestPeriod"]<old["latestPeriod"]: raise ValueError("Reporting period regression")
    same=new["latestPeriod"]==old["latestPeriod"]
    missing=sorted(a.keys()-b.keys())
    added=sorted(b.keys()-a.keys())
    changed=[{"key":k,"old":a[k],"new":b[k]} for k in sorted(a.keys()&b.keys()) if a[k]!=b[k]]
    return {"old_period":old["latestPeriod"],"new_period":new["latestPeriod"],"old_count":len(a),"new_count":len(b),"missing":missing,"added":added,"same_period_revisions":changed if same else [],"changed_records":len(changed),"requires_review":True,"published":False}
if __name__=="__main__":
    old,new=(json.loads(pathlib.Path(p).read_text()) for p in sys.argv[1:3])
    print(json.dumps(compare(old,new),indent=2))
