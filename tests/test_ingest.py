import unittest
from scripts.ingest import normalize
M={"government_id":"id","period":"year","amount":"value","metric":"levy","unit":"USD","status":"reported"}
class TestIngest(unittest.TestCase):
    def test_missing_not_zero(self):
        rows=list(normalize([{"id":"001","year":2025,"value":None},{"id":"002","year":2025,"value":0}],M))
        self.assertIsNone(rows[0]["amount"])
        self.assertEqual(rows[1]["amount"],"0")
    def test_duplicate(self):
        row={"id":"001","year":2025,"value":1}
        with self.assertRaises(ValueError): list(normalize([row,row],M))
    def test_precision(self):
        self.assertEqual(list(normalize([{"id":"001","year":2025,"value":"1,234.56"}],M))[0]["amount"],"1234.56")
