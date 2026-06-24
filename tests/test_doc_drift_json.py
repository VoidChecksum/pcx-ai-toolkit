"""Regression tests for machine-readable doc drift output."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_DRIFT = REPO_ROOT / "tools" / "check-doc-drift.py"


class DocDriftJsonTest(unittest.TestCase):
    def test_json_mode_outputs_parseable_json(self):
        result = subprocess.run(
            [sys.executable, str(CHECK_DRIFT), "--json", "--limit", "1"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["checked"], 1)
        self.assertIn("results", data)
        self.assertEqual(data["mode"], "offline")
        self.assertEqual(data["snapshot"], "docs/PROVENANCE.json")


if __name__ == "__main__":
    unittest.main()
