import json
import re
from pathlib import Path
from decimal import Decimal

root = Path(__file__).resolve().parents[1]
report = json.loads((root/"brb-reconciliation/report.json").read_text())["statewide"]
data = json.loads((root/"public/data/local-debt-2025.json").read_text())
page = (root/"src/components/FinancialEvidence.astro").read_text()
def require(condition, message):
    if not condition:
        raise ValueError(message)
require(data["fiscalYear"] == 2025, "Reporting year mismatch")
require(report["all_match"] and not report["differences"], "Reconciliation not exact")
require(not report["missing_from_source"] and not report["missing_from_website"], "Missing entities")
n = report["exact_matches"]
require(n == report["source_entities"] == report["published_entities"] == len(data["records"]), "Entity count mismatch")
require(report["source_rows"] == sum(r["count"] for r in data["records"]), "Issuance count mismatch")
for metric in ("principal","interest","repayment"):
    total = sum(Decimal(str(r[metric])) for r in data["records"])
    values = report["totals"][metric]
    require(total == Decimal(values["source"]) == Decimal(values["published"]) and Decimal(values["difference"]) == 0, "Financial mismatch: "+metric)
section = page.split('<article aria-labelledby="source-verification">',1)[1].split("</article>",1)[0]
expected = [f'{report["source_rows"]:,}',f'{n:,} / {n:,}',f'{3*n:,} / {3*n:,}',"0","$0 / $0 / $0"]
actual = re.findall(r"<dd>([^<]+)</dd>",section)
require(actual[:5] == expected, "Public verification snapshot counts differ from current reconciliation")
for phrase in ("FY2025 source reconciliation","Conciliación con la fuente del AF2025","formal evidence review pending","revisión formal de evidencia pendiente","not all liabilities or current balances","no todos los pasivos ni los saldos actuales"):
    require(phrase in section,"Missing public scope disclosure: "+phrase)
print("Public FY2025 verification claims match current reconciliation; bilingual scope disclosures present")
