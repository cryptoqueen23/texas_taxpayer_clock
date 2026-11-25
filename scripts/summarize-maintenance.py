"""Report staging outcome without implying publication."""
import json, os
from pathlib import Path
p=Path("staged-sales-tax/release-review.json")
lines=["## Sales tax maintenance", "", "Published website data was not modified."]
if p.is_file():
    d=json.loads(p.read_text())
    lines += ["", "**Review required; not published.**", "", "| Check | Result |", "|---|---|"]
    for k in ("old_period","new_period","old_count","new_count","missing_count","added_count","changed_count","same_period_revision_count","baseline_sha256","candidate_sha256"):
        lines.append(f"| {k} | {d[k]} |")
else:
    lines += ["", "**No completed release review.** Inspect failed or skipped acquisition and validation steps before retrying."]
summary="\n".join(lines)+"\n"
print(summary)
if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as out: out.write(summary)
