"""Regression tests for tools/api-lookup.py."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
API_LOOKUP = REPO_ROOT / "tools" / "api-lookup.py"


class ApiLookupTest(unittest.TestCase):
    def test_exact_lookup_returns_source(self):
        result = subprocess.run(
            [sys.executable, str(API_LOOKUP), "draw_text", "--lang", "enma", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["found"])
        self.assertTrue(data["signatures"])
        self.assertTrue(all(sig["source"].startswith("https://docs.perception.cx/")
                            for sig in data["signatures"]))

    def test_typo_lookup_fails_with_suggestions(self):
        result = subprocess.run(
            [sys.executable, str(API_LOOKUP), "draw_texxt", "--lang", "enma", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        data = json.loads(result.stdout)
        self.assertFalse(data["found"])
        self.assertIn("draw_text", data["suggestions"])

    def test_angelscript_lookup_is_unsupported(self):
        result = subprocess.run(
            [sys.executable, str(API_LOOKUP), "register_callback", "--lang", "angelscript", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported", result.stderr.lower() + result.stdout.lower())
    def test_enma_language_addon_lookup_returns_source(self):
        result = subprocess.run(
            [sys.executable, str(API_LOOKUP), "json_object", "--lang", "enma", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["found"])
        self.assertTrue(data["signatures"])
        self.assertTrue(any(sig["source"].startswith("https://enma-1.gitbook.io/enma/")
                            for sig in data["signatures"]))


if __name__ == "__main__":
    unittest.main()
