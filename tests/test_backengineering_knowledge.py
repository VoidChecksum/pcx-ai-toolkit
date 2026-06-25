import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class BackEngineeringKnowledgeTest(unittest.TestCase):
    def test_devirtualization_docs_capture_modern_guidance(self):
        generic = (REPO_ROOT / "knowledge/re-workflows/devirtualization-generic.md").read_text(encoding="utf-8")
        vmp2 = (REPO_ROOT / "knowledge/re-workflows/vmp2-static-analysis.md").read_text(encoding="utf-8")
        themida = (REPO_ROOT / "knowledge/re-workflows/themida-guided-symbolic-eval.md").read_text(encoding="utf-8")
        combined = "\n".join([generic, vmp2, themida]).lower()
        self.assertIn("github.com/backengineering/vmp2", combined)
        self.assertIn("back.engineering/blog/09/05/2026", combined)
        self.assertIn("handler", combined)
        self.assertIn("brittle", combined)
        self.assertIn("constant folding", combined)
        self.assertIn("dead store", combined)
        self.assertIn("behavior", combined)


if __name__ == "__main__":
    unittest.main()
