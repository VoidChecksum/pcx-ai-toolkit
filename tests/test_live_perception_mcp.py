"""Optional live Perception MCP integration tests.

Set PCX_MCP_URL to a running Perception MCP endpoint, e.g.
http://127.0.0.1:42069/mcp. Tests are skipped by default so public CI does not
need Perception installed.
"""
from __future__ import annotations

import json
import os
import unittest
import urllib.request


PCX_MCP_URL = os.environ.get("PCX_MCP_URL", "").strip()


def mcp_call(method: str, params: dict | None = None) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode("utf-8")
    req = urllib.request.Request(
        PCX_MCP_URL,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8")
    if raw.startswith("data:"):
        raw = raw.removeprefix("data:").strip()
    return json.loads(raw)


@unittest.skipUnless(PCX_MCP_URL, "set PCX_MCP_URL to run live Perception MCP tests")
class LivePerceptionMcpTest(unittest.TestCase):
    def test_script_context_is_available(self) -> None:
        result = mcp_call("script/get_context")
        self.assertNotIn("error", result)
        context = result.get("result", {}).get("context", "")
        self.assertIn("Enma", context)
        self.assertIn("register_routine", context)

    def test_script_validate_accepts_minimal_enma(self) -> None:
        source = 'int64 main() { println("hello"); return 1; }'
        result = mcp_call("script/validate", {"source": source})
        self.assertNotIn("error", result)
        self.assertTrue(result.get("result", {}).get("ok"), result)


if __name__ == "__main__":
    unittest.main()
