import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = REPO_ROOT / "docs" / "COVERAGE.md"
GENERATOR = REPO_ROOT / "tools" / "build-coverage-dashboard.py"


class CoverageDashboardTest(unittest.TestCase):
    def test_dashboard_is_generated_from_current_artifacts(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dashboard_reports_key_anti_hallucination_counts(self):
        text = DASHBOARD.read_text(encoding="utf-8")
        symbols = json.loads((REPO_ROOT / "knowledge" / "perception-symbol-versions.json").read_text(encoding="utf-8"))["symbols"]
        unsupported = json.loads((REPO_ROOT / "knowledge" / "unsupported-symbols.json").read_text(encoding="utf-8"))["symbols"]
        provenance = json.loads((REPO_ROOT / "docs" / "PROVENANCE.json").read_text(encoding="utf-8"))

        self.assertIn(f"Symbols indexed: {len(symbols)}", text)
        self.assertIn(f"Known hallucinations covered: {len(unsupported)}", text)
        self.assertIn(f"Generated bundle sources: {provenance['count']}", text)
        self.assertIn(f"Drift-checkable sources: {provenance['drift_checkable']}", text)
        self.assertIn("Perception API pages indexed:", text)


if __name__ == "__main__":
    unittest.main()
