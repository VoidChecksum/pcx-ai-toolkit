"""Regression tests for the pcx-knowledge-mcp package metadata."""
import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "mcp" / "pcx-knowledge-mcp" / "pyproject.toml"
CONFIG = REPO_ROOT / "mcp" / "perception-mcp-config.json"


class McpPackageTest(unittest.TestCase):
    def test_console_script_points_at_packaged_module(self):
        data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        self.assertEqual(data["project"]["scripts"]["pcx-knowledge-mcp"], "server:main")
        self.assertIn("server", data["tool"]["setuptools"]["py-modules"])
        self.assertTrue((PYPROJECT.parent / "server.py").exists())

    def test_runtime_mcp_config_uses_streamable_http_endpoint(self):
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
        server = data["mcpServers"]["perception"]
        self.assertEqual(server["url"], "http://127.0.0.1:42069/mcp")
        self.assertEqual(server["transport"], "http")
        self.assertNotIn("command", server)
        self.assertNotIn("args", server)


if __name__ == "__main__":
    unittest.main()
