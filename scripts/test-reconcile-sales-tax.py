import unittest, importlib.util, pathlib, json, copy
spec=importlib.util.spec_from_file_location("reconcile",pathlib.Path(__file__).with_name("reconcile-sales-tax.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.old=json.loads(pathlib.Path("public/data/local-sales-tax-2026-11.json").read_text())
    def test_baseline(self):
        r=m.compare(self.old,self.old)
        self.assertEqual(r["old_count"],1827)
        self.assertEqual(r["changed_records"],0)
    def test_duplicate(self):
        n=copy.deepcopy(self.old);n["records"].append(n["records"][0])
        with self.assertRaises(ValueError): m.compare(self.old,n)
    def test_missing(self):
        n=copy.deepcopy(self.old);n["records"].pop()
        self.assertEqual(len(m.compare(self.old,n)["missing"]),1)
    def test_revision(self):
        n=copy.deepcopy(self.old);n["records"][0][4]+=1
        self.assertEqual(len(m.compare(self.old,n)["same_period_revisions"]),1)
    def test_regression(self):
        n=copy.deepcopy(self.old);n["latestPeriod"]="2026-10"
        with self.assertRaises(ValueError): m.compare(self.old,n)
    def test_invalid_cents(self):
        n=copy.deepcopy(self.old);n["records"][0][4]=1.5
        with self.assertRaises(ValueError): m.compare(self.old,n)
if __name__=="__main__": unittest.main()
