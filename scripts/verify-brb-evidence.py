import hashlib
import json
import re
import tempfile
import unittest
import sys
from pathlib import Path

def verify_file(root, evidence):
    digest = evidence["sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid SHA-256")
    path = root / (digest + ".json")
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or invalid evidence file: " + digest)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("Evidence checksum mismatch: " + digest)
    return digest

def verify_archive(root):
    report = json.loads((root / "report.json").read_text())
    statewide = report["statewide"]
    entries = [statewide["count_evidence"], statewide["end_count_evidence"], *statewide["page_evidence"]]
    if len(statewide["page_evidence"]) != (statewide["source_rows"] + 4999)//5000:
        raise ValueError("Missing page evidence")
    for pilot in report["reports"]:
        entries.extend([pilot["source_evidence"],pilot["count_evidence"]])
    entries.extend([report["school_discovery"]["evidence"],report["school_discovery"]["historical_evidence"]])
    verified = {verify_file(root,e) for e in entries}
    print(f"Verified {len(verified)} unique evidence files across {len(entries)} references")

class IntegrityTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        raw = b'{"n":1}'
        self.evidence = {"sha256":hashlib.sha256(raw).hexdigest()}
        self.path = self.root / (self.evidence["sha256"] + ".json")
        self.path.write_bytes(raw)
    def test_valid(self):
        self.assertEqual(verify_file(self.root,self.evidence),self.evidence["sha256"])
    def test_tampered(self):
        self.path.write_bytes(b'{"n":2}')
        with self.assertRaisesRegex(ValueError,"checksum mismatch"):
            verify_file(self.root,self.evidence)
    def test_missing(self):
        self.path.unlink()
        with self.assertRaisesRegex(ValueError,"Missing"):
            verify_file(self.root,self.evidence)
    def test_invalid_digest(self):
        with self.assertRaisesRegex(ValueError,"Invalid SHA"):
            verify_file(self.root,{"sha256":"../report"})

if __name__=="__main__":
    if sys.argv[1:]==["--test"]:
        unittest.main(argv=[sys.argv[0]],verbosity=2)
    else:
        verify_archive(Path(__file__).resolve().parents[1]/"brb-reconciliation")
