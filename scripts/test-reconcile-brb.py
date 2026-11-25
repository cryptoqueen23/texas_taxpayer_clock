import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("brb", Path(__file__).with_name("reconcile-brb.py"))
brb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brb)

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "public/data/local-debt-2025.json"
        self.path.parent.mkdir(parents=True)
        self.baseline = {"fiscalYear":2025,"records":[{"id":"TEST","count":1,"principal":100,"interest":20,"repayment":120}]}
        self.rows = [{"row_id":"1","govid":"TEST","fiscalyear":"2025","totalprincipaloutstanding":"100","totalinterestoutstanding":"20","totaldebtserviceoutstanding":"120"}]
        self.expected = 1
    def run_case(self):
        self.path.write_text(json.dumps(self.baseline))
        def fetch(params):
            return ([{"n":str(self.expected)}] if params["$select"]=="count(*) AS n" else self.rows), {}
        with patch.object(brb,"ROOT",self.root), patch.object(brb,"fetch",side_effect=fetch):
            return brb.statewide()
    def test_exact(self):
        self.assertTrue(self.run_case()["all_match"])
    def test_one_dollar(self):
        self.baseline["records"][0]["principal"] += 1
        self.assertFalse(self.run_case()["all_match"])
    def test_missing_government(self):
        self.baseline["records"][0]["id"]="OTHER"
        r=self.run_case()
        self.assertEqual(r["missing_from_source"],["OTHER"])
        self.assertEqual(r["missing_from_website"],["TEST"])
        self.assertFalse(r["all_match"])
    def test_duplicate_source(self):
        self.rows *= 2
        self.expected=2
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            self.run_case()
    def test_incomplete(self):
        self.expected=2
        with self.assertRaisesRegex(ValueError,"Incomplete"):
            self.run_case()
    def test_invalid_value(self):
        self.rows[0]["totalprincipaloutstanding"]="NaN"
        with self.assertRaisesRegex(ValueError,"Nonfinite"):
            self.run_case()
    def test_wrong_year(self):
        self.rows[0]["fiscalyear"]="2024"
        with self.assertRaisesRegex(ValueError,"invalid source row"):
            self.run_case()
    def test_wrong_baseline_year(self):
        self.baseline["fiscalYear"]=2024
        with self.assertRaisesRegex(ValueError,"year mismatch"):
            self.run_case()
    def test_count_mismatch(self):
        self.baseline["records"][0]["count"]=2
        self.assertFalse(self.run_case()["all_match"])
    def test_duplicate_baseline(self):
        self.baseline["records"] *= 2
        with self.assertRaisesRegex(ValueError,"Duplicate baseline"):
            self.run_case()

if __name__=="__main__":
    unittest.main(verbosity=2)
