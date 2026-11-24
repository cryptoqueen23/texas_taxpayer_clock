"""Fail-closed financial publication checks. Never infer consolidation."""
from decimal import Decimal
import re
def money(value):
    if value is None: raise ValueError("Missing financial amount")
    d=Decimal(str(value))
    if not d.is_finite(): raise ValueError("Nonfinite amount")
    return d
def debt_check(principal, interest, repayment, tolerance="1"):
    p,i,r=map(money,(principal,interest,repayment))
    if min(p,i,r)<0: raise ValueError("Negative debt component")
    delta=r-p-i
    return {"difference":str(delta),"status":"exact" if delta==0 else "rounding_review" if abs(delta)<=money(tolerance) else "blocked"}
def combine_debt(records, consolidated=False):
    if not records: raise ValueError("No records")
    if consolidated: raise ValueError("Consolidation requires a separate verified elimination schedule")
    periods={r["period"] for r in records}
    if len(periods)!=1: raise ValueError("Mixed reporting periods")
    ids=[r["government_id"] for r in records]
    if len(set(ids))!=len(ids): raise ValueError("Duplicate government")
    return {"amount":str(sum((money(r["amount"]) for r in records),Decimal(0))),"period":records[0]["period"],"status":"unconsolidated","warning":"Potential overlapping obligations; not consolidated debt"}
def validate_batch(batch, sources):
    if batch["source_id"] not in sources: raise ValueError("Unknown source")
    if not re.fullmatch(r"[0-9a-f]{64}",batch["source_sha256"]): raise ValueError("Invalid checksum")
    seen=set()
    if not batch["records"]: raise ValueError("Empty batch")
    for r in batch["records"]:
        key=(r["government_id"],r["period"],r["metric"])
        if not all(key) or key in seen: raise ValueError("Missing or duplicate observation key")
        seen.add(key)
        if not re.fullmatch(r"(?:FY)?20[0-9]{2}(?:-P[12])?",r["period"]): raise ValueError("Unsupported reporting period")
        if r["status"]=="unavailable":
            if r["amount"] is not None: raise ValueError("Unavailable must be null")
        elif r["status"] in ("reported","provisional"):
            money(r["amount"])
        else: raise ValueError("Invalid source observation status")
        if not r["unit"]: raise ValueError("Missing unit")
    return {"records":len(seen),"status":"structurally_valid","publication":"pending reconciliation and approval"}
