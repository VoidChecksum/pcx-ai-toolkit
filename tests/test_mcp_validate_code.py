"""Regression test for the pcx-knowledge-mcp validate_code tool."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent

# Stub the mcp SDK before importing server.
sys.modules.setdefault("mcp", MagicMock())
sys.modules.setdefault("mcp.server", MagicMock())
sys.modules.setdefault("mcp.server.fastmcp", MagicMock())


class FakeFastMCP:
    def __init__(self, _name: str) -> None:
        pass

    def tool(self):
        return lambda f: f

    def resource(self, *_args, **_kwargs):
        return lambda f: f

    def run(self) -> None:
        pass


sys.modules["mcp.server.fastmcp"].FastMCP = FakeFastMCP
sys.path.insert(0, str(REPO_ROOT / "mcp" / "pcx-knowledge-mcp"))

from server import validate_code  # noqa: E402


class ValidateCodeTest(unittest.TestCase):
    def test_catches_hallucinated_function(self):
        code = 'import "vec";\nimport "color";\nvoid r(int64 d){ draw_esp(vec2(0,0), color(255,0,0,255)); }\nint64 main(){ register_routine(cast<int64>(r),0); return 1; }'
        result = json.loads(validate_code(code, "enma"))
        self.assertFalse(result["ok"])
        self.assertTrue(any(f["symbol"] == "draw_esp" for f in result["findings"]))

    def test_allows_real_api_calls(self):
        code = 'import "vec";\nimport "color";\nvoid r(int64 d){ draw_text("hi", vec2(0,0), color(255,0,0,255), get_font20(), 0, color(0,0,0,0), 0.0); }\nint64 main(){ register_routine(cast<int64>(r),0); return 1; }'
        result = json.loads(validate_code(code, "enma"))
        self.assertTrue(result["ok"], result["findings"])


if __name__ == "__main__":
    unittest.main()
