import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "perception-symbol-versions.schema.json"
DATA_PATH = REPO_ROOT / "knowledge" / "perception-symbol-versions.json"
VERSION_RE = re.compile(r"^(unknown|\d{4}-\d{2}-\d{2}(?:\([ab]\))?|<=\d{4}-\d{2}-\d{2}(?:\([ab]\))?|\d{4}-\d{2}-\d{2}-or-earlier)$")


class SymbolMetadataTest(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    def test_schema_file_documents_enforced_contract(self):
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        required = set(self.schema["required"])
        self.assertGreaterEqual(required, {"schema", "last_verified", "symbols"})
        symbol_required = set(self.schema["properties"]["symbols"]["items"]["required"])
        self.assertGreaterEqual(symbol_required, {
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
        })

    def test_symbol_rows_are_complete_and_source_backed(self):
        self.assertEqual(self.data["schema"], 1)
        self.assertRegex(self.data["last_verified"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertIsInstance(self.data["symbols"], list)
        self.assertGreater(len(self.data["symbols"]), 50)

        required = set(self.schema["properties"]["symbols"]["items"]["required"])
        seen = set()
        for row in self.data["symbols"]:
            key = (row.get("language"), row.get("symbol"))
            with self.subTest(symbol=key):
                self.assertFalse(required - row.keys())
                self.assertNotIn(key, seen)
                seen.add(key)
                self.assertIsInstance(row["symbol"], str)
                self.assertTrue(row["symbol"].strip())
                self.assertEqual(row["language"], "enma")
                self.assertIsInstance(row["api_family"], str)
                self.assertTrue(row["api_family"].strip())
                self.assertRegex(row["introduced"], VERSION_RE)
                self.assertRegex(row["first_documented"], VERSION_RE)
                self.assertIsInstance(row["permissions"], list)
                self.assertIsInstance(row["deprecated"], bool)
                self.assertIsInstance(row["removed"], bool)
                self.assertTrue((REPO_ROOT / row["source"]).exists())
                if row["changelog_source"] is not None:
                    self.assertTrue((REPO_ROOT / row["changelog_source"]).exists())
                if row["deprecated"] or row["removed"]:
                    self.assertIn("replacement", row)


if __name__ == "__main__":
    unittest.main()
