import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PCX = REPO_ROOT / "tools" / "pcx.py"


class SkillsToolTest(unittest.TestCase):
    def test_recommend_returns_relevant_skill_and_docs(self):
        r = subprocess.run([sys.executable, str(PCX), "skills", "recommend", "vmprotect devirtualization workflow"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = json.loads(r.stdout)
        self.assertIn("pcx re-plan", payload["commands"])
        self.assertTrue(any("devirtualization" in doc or "vmprotect" in doc for doc in payload["docs"]))
        self.assertTrue(payload["skills"])

    def test_lint_reports_json_shape(self):
        r = subprocess.run([sys.executable, str(PCX), "skills", "lint"], cwd=REPO_ROOT, capture_output=True, text=True)
        payload = json.loads(r.stdout)
        self.assertIn("ok", payload)
        self.assertIn("findings", payload)
        self.assertGreater(payload["skills"], 0)


if __name__ == "__main__":
    unittest.main()
