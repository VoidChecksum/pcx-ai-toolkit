import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PCX = REPO_ROOT / "tools" / "pcx.py"


def run_plan(*words: str):
    r = subprocess.run([sys.executable, str(PCX), "re-plan", *words], cwd=REPO_ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(r.stdout)


class RePlanTest(unittest.TestCase):
    def test_vmprotect_plan_uses_vmp2_docs_and_warns(self):
        payload = run_plan("vmprotect", "vmp2", "devirtualization")
        self.assertEqual(payload["workflow"], "vmprotect_devirtualization")
        self.assertIn("knowledge/re-workflows/vmp2-static-analysis.md", payload["docs"])
        self.assertTrue(any("handler matching" in warning for warning in payload["warnings"]))

    def test_themida_plan_uses_guided_symbolic_eval(self):
        payload = run_plan("themida", "guided", "symbolic", "evaluation")
        self.assertEqual(payload["workflow"], "themida_guided_symbolic_eval")
        self.assertIn("knowledge/re-workflows/themida-guided-symbolic-eval.md", payload["docs"])

    def test_unsafe_words_set_warning_not_refusal(self):
        payload = run_plan("unauthorized", "live", "target", "exploit")
        self.assertTrue(payload["safety"]["remote_or_offensive_warning"])
        self.assertTrue(payload["safety"]["authorized_scope_required"])


if __name__ == "__main__":
    unittest.main()
