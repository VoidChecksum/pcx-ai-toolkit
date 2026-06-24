import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class EnmaDocsCoverageTest(unittest.TestCase):
    def test_enma_llms_mirrors_are_drift_checkable(self):
        provenance = json.loads((REPO_ROOT / "docs" / "PROVENANCE.json").read_text(encoding="utf-8"))
        files = provenance["files"]
        for path in ("docs/enma/llms-language.md", "docs/enma/llms-sdk.md"):
            with self.subTest(path=path):
                self.assertIn(path, files)
                self.assertTrue(files[path]["drift_check"])
                self.assertEqual(files[path]["source"], "gitbook")


if __name__ == "__main__":
    unittest.main()
