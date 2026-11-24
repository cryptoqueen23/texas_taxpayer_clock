import unittest
from scripts.reconcile import debt_check, combine_debt, validate_batch
class TestReconcile(unittest.TestCase):
    def test_debt(self):
        self.assertEqual(debt_check(100,20,120)["status"],"exact")
        self.assertEqual(debt_check(100,20,121)["status"],"rounding_review")
        self.assertEqual(debt_check(100,20,130)["status"],"blocked")
    def test_consolidation(self):
        rows=[{"government_id":"a","period":"2025","amount":"100"},{"government_id":"b","period":"2025","amount":"20"}]
        self.assertEqual(combine_debt(rows)["status"],"unconsolidated")
        with self.assertRaises(ValueError): combine_debt(rows,True)
        with self.assertRaises(ValueError): combine_debt(rows+[rows[0]])
        with self.assertRaises(ValueError): combine_debt([rows[0],dict(rows[1],period="2024")])
    def test_batch(self):
        row={"government_id":"a","period":"2025","metric":"levy","amount":None,"status":"unavailable","unit":"USD"}
        b={"source_id":"x","source_sha256":"a"*64,"records":[row]}
        self.assertEqual(validate_batch(b,{"x"})["publication"],"pending reconciliation and approval")
        with self.assertRaises(ValueError): validate_batch(dict(b,records=[dict(row,amount="0")]),{"x"})
        with self.assertRaises(ValueError): validate_batch(dict(b,records=[row,row]),{"x"})
        with self.assertRaises(ValueError): validate_batch(b,{"y"})
