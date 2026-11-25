"""Prepare a review-only release bundle, never modify published data."""
import hashlib, json, pathlib, datetime, importlib.util
root=pathlib.Path("staged-sales-tax")
baseline=pathlib.Path("public/data/local-sales-tax-2026-11.json")
candidate=root/"candidate.json"
spec=importlib.util.spec_from_file_location("reconcile",pathlib.Path(__file__).with_name("reconcile-sales-tax.py"))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
old=json.loads(baseline.read_text());new=json.loads(candidate.read_text())
report=mod.compare(old,new)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
release={"prepared_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"baseline_path":str(baseline),"baseline_sha256":digest(baseline),"candidate_sha256":digest(candidate),"old_period":report["old_period"],"new_period":report["new_period"],"old_count":report["old_count"],"new_count":report["new_count"],"missing_count":len(report["missing"]),"added_count":len(report["added"]),"changed_count":report["changed_records"],"same_period_revision_count":len(report["same_period_revisions"]),"status":"review_required","published":False,"automatic_publication":False}
(root/"release-review.json").write_text(json.dumps(release,indent=2))
print(json.dumps(release,indent=2))
