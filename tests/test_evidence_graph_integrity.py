import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PCX = REPO_ROOT / "tools" / "pcx.py"

class EvidenceGraphIntegrityTest(unittest.TestCase):
    def test_verify_rejects_missing_and_duplicate_evidence(self):
        path = REPO_ROOT / "tmp-bad-evidence.json"
        path.write_text(json.dumps({"schema":"pcx-evidence-graph-v1","target":{"process":"game.exe"},"claims":[{"id":"C-001","claim":"x","status":"confirmed","evidence":["E-001","E-404"]}],"evidence":[{"id":"E-001","type":"address_validation","tool":"process/is_valid_address","params":{},"result":{}},{"id":"E-001","type":"address_validation","tool":"process/is_valid_address","params":{},"result":{}}]}))
        result = subprocess.run([sys.executable, str(PCX), "evidence", "--file", str(path), "verify"], cwd=REPO_ROOT, capture_output=True, text=True)
        path.unlink(missing_ok=True)
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["duplicate_evidence_ids"])
        self.assertTrue(payload["missing_references"])

    def test_import_transcript_creates_graph(self):
        transcript = REPO_ROOT / "tmp-transcript.jsonl"
        graph = REPO_ROOT / "tmp-imported-evidence.json"
        transcript.write_text(json.dumps({"ts":"2026-06-25T00:00:00Z","target":"game.exe","tool":"process/is_valid_address","params":{"address":"0x401000"},"result":{"valid":True},"error":None,"elapsed_ms":1.0}) + "\n")
        result = subprocess.run([sys.executable, str(PCX), "evidence", "import-transcript", str(transcript), "--claim", "C-001", "--out", str(graph)], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(graph.read_text())
        self.assertEqual(data["claims"][0]["evidence"], ["E-001"])
        self.assertEqual(data["evidence"][0]["type"], "address_validation")
        transcript.unlink(missing_ok=True); graph.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
