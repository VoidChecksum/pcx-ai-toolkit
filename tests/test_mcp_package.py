"""Regression tests for the pcx-knowledge-mcp package metadata."""
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "mcp" / "pcx-knowledge-mcp" / "pyproject.toml"


class McpPackageTest(unittest.TestCase):
    def test_console_script_points_at_packaged_module(self):
        data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        self.assertEqual(data["project"]["scripts"]["pcx-knowledge-mcp"], "server:main")
        self.assertIn("server", data["tool"]["setuptools"]["py-modules"])
        self.assertTrue((PYPROJECT.parent / "server.py").exists())


if __name__ == "__main__":
    unittest.main()
