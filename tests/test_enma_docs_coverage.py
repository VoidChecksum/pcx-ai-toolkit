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

    def test_required_local_perception_docs_are_indexed(self):
        provenance = json.loads((REPO_ROOT / "docs" / "PROVENANCE.json").read_text(encoding="utf-8"))
        files = provenance["files"]
        for path in (
            "docs/perception/sdk-status.md",
            "docs/perception/versioning-and-migration.md",
        ):
            with self.subTest(path=path):
                self.assertIn(path, files)
                self.assertFalse(files[path]["drift_check"])
                self.assertEqual(files[path]["source"], "local")

    def test_perception_symbol_versions_schema(self):
        data = json.loads((REPO_ROOT / "knowledge" / "perception-symbol-versions.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], 1)
        self.assertRegex(data["last_verified"], r"^\d{4}-\d{2}-\d{2}$")
        version_re = r"^(unknown|\d{4}-\d{2}-\d{2}(?:\([ab]\))?|<=\d{4}-\d{2}-\d{2}(?:\([ab]\))?|\d{4}-\d{2}-\d{2}-or-earlier)$"
        required = {
            "symbol",
            "introduced",
            "first_documented",
            "source",
            "changelog_source",
            "language",
            "api_family",
            "permissions",
            "deprecated",
            "removed",
            "replacement",
        }
        seen = set()
        for row in data["symbols"]:
            with self.subTest(symbol=row.get("symbol")):
                self.assertFalse(required - row.keys())
                self.assertNotIn(row["symbol"], seen)
                seen.add(row["symbol"])
                self.assertEqual(row["language"], "enma")
                self.assertRegex(row["introduced"], version_re)
                self.assertRegex(row["first_documented"], version_re)
                self.assertIsInstance(row["permissions"], list)
                self.assertIsInstance(row["deprecated"], bool)
                self.assertIsInstance(row["removed"], bool)
                self.assertTrue((REPO_ROOT / row["source"]).exists())
                if row["changelog_source"] is not None:
                    self.assertTrue((REPO_ROOT / row["changelog_source"]).exists())

    def test_perception_overview_has_no_duplicate_headings(self):
        path = REPO_ROOT / "docs/perception/readme.md"
        seen = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith(("## ", "### ")):
                continue
            heading = line.lstrip("#").strip()
            with self.subTest(heading=heading):
                self.assertNotIn(heading, seen)
            seen.add(heading)


if __name__ == "__main__":
    unittest.main()
