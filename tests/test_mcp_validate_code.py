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

from server import (  # noqa: E402
    api_lookup,
    explain_finding,
    generate_script_plan,
    get_skill,
    list_project_templates,
    list_skills,
    offset_drift_report,
    recommend_context,
    scaffold_project,
    suggest_imports,
    search as mcp_search,
    validate_answer,
    validate_code,
)

def mcp_payload(value):
    return json.loads(value) if isinstance(value, str) else value



class ValidateCodeTest(unittest.TestCase):
    def test_catches_hallucinated_function(self):
        code = 'import "vec";\nimport "color";\nvoid r(int64 d){ draw_esp(vec2(0,0), color(255,0,0,255)); }\nint64 main(){ register_routine(cast<int64>(r),0); return 1; }'
        result = mcp_payload(validate_code(code, "enma"))
        self.assertFalse(result["ok"])
        self.assertTrue(any(f["symbol"] == "draw_esp" for f in result["findings"]))

    def test_allows_real_api_calls(self):
        code = 'import "vec";\nimport "color";\nvoid r(int64 d){ draw_text("hi", vec2(0,0), color(255,0,0,255), get_font20(), 0, color(0,0,0,0), 0.0); }\nint64 main(){ register_routine(cast<int64>(r),0); return 1; }'
        result = mcp_payload(validate_code(code, "enma"))
        self.assertTrue(result["ok"], result["findings"])

    def test_enma_addon_symbols_require_imports(self):
        code = 'int64 main(){ float64 a = atan2(1.0, 2.0); return 1; }'
        result = mcp_payload(validate_code(code, "enma"))
        self.assertFalse(result["ok"])
        finding = next(f for f in result["findings"] if f["symbol"] == "atan2")
        self.assertEqual(finding["kind"], "missing_import")
        self.assertEqual(finding["fix"], 'import "math";')

    def test_documented_enma_addons_require_imports(self):
        cases = [
            ('int64 main(){ variant v = variant_int(1); return 1; }', "variant", 'import "variant";'),
            ('int64 main(){ regex r = regex("[0-9]+"); return 1; }', "regex", 'import "regex";'),
            ('int64 main(){ hash_set<int64> s; return 1; }', "hash_set", 'import "hash_set";'),
            ('int64 main(){ sorted_map<int64, int64> m; return 1; }', "sorted_map", 'import "sorted_map";'),
            ('int64 main(){ list<int64> xs; return 1; }', "list", 'import "list";'),
        ]
        for code, symbol, fix in cases:
            with self.subTest(symbol=symbol):
                result = mcp_payload(validate_code(code, "enma"))
                self.assertFalse(result["ok"])
                finding = next(f for f in result["findings"] if f["symbol"] == symbol)
                self.assertEqual(finding["kind"], "missing_import")
                self.assertEqual(finding["fix"], fix)

    def test_enma_addon_symbols_pass_with_imports(self):
        code = 'import "math";\nint64 main(){ float64 a = atan2(1.0, 2.0); return 1; }'
        result = mcp_payload(validate_code(code, "enma"))
        self.assertTrue(result["ok"], result["findings"])

    def test_rejects_wrong_draw_text_shape(self):
        code = 'import "vec";\nimport "color";\nint64 main(){ draw_text("hi", 20, 20); return 1; }'
        result = mcp_payload(validate_code(code, "enma"))
        self.assertFalse(result["ok"])
        kinds = {f["kind"] for f in result["findings"]}
        self.assertIn("argument_count_mismatch", kinds)

    def test_rejects_wrong_routine_shape(self):
        code = 'void draw(){ }\nint64 main(){ register_routine(draw, 0); return true; }'
        result = mcp_payload(validate_code(code, "enma"))
        self.assertFalse(result["ok"])
        kinds = {f["kind"] for f in result["findings"]}
        self.assertIn("routine_missing_cast", kinds)
        self.assertIn("invalid_entrypoint_return", kinds)

    def test_accepts_angelscript_mode(self):
        code = 'int main(){ register_callback(on_tick, 16, 0); return 1; } void on_tick(int id, int data_index){ draw_text("hi", 20, 20, 255,255,255,255, get_font20(), TE_SHADOW, 0,0,0,180, 1.0f); }'
        result = mcp_payload(validate_code(code, "angelscript"))
        self.assertTrue(result["ok"], result["findings"])

    def test_accepts_lua_mode(self):
        code = 'function main() log("loaded") return 1 end function on_frame() draw_text("hi", 20, 20, 255, 255, 255, 255, get_font20(), TE_SHADOW, 0, 0, 0, 180, 1.0) end'
        result = mcp_payload(validate_code(code, "lua"))
        self.assertTrue(result["ok"], result["findings"])


    def test_api_lookup_returns_source_backed_signature(self):
        result = mcp_payload(api_lookup("draw_text", "enma"))
        self.assertTrue(result["found"])
        self.assertTrue(result["signatures"])
        self.assertTrue(all(sig["source"].startswith("https://docs.perception.cx/") for sig in result["signatures"]))

    def test_api_lookup_suggests_near_matches(self):
        result = mcp_payload(api_lookup("draw_texxt", "enma"))
        self.assertFalse(result["found"])
        self.assertIn("draw_text", result["suggestions"])

    def test_mcp_tools_return_structured_payloads_by_default(self):
        self.assertIsInstance(api_lookup("draw_text", "enma"), dict)
        self.assertIsInstance(mcp_search("register_routine lifecycle", 1), list)

    def test_list_and_get_skill(self):
        skills = mcp_payload(list_skills())
        names = {item["name"] for item in skills}
        self.assertIn("pcx-enma-discipline", names)
        skill = get_skill("pcx-enma-discipline")
        self.assertIn("# Enma", skill)

    def test_recommend_context_for_enma_esp(self):
        result = mcp_payload(recommend_context("write an ESP overlay", "enma"))
        self.assertIn("pcx-enma-discipline", result["skills"])
        self.assertIn("game-cheat-script-master", result["skills"])
        self.assertIn("api_lookup", result["mcp_tools"])

    def test_recommend_context_for_forum_changelog(self):
        result = mcp_payload(recommend_context("explain the overlay changelog", ""))
        self.assertIn("knowledge/perception-forum-insights.md", result["docs"])
        self.assertIn("docs/perception/changelogs.md", result["docs"])
        self.assertIn("validate_answer", result["mcp_tools"])

    def test_validate_answer_checks_markdown_code_blocks(self):
        answer = '''```enma
void r(int64 d) { draw_texxt("hi"); }
```'''
        result = mcp_payload(validate_answer(answer, "draft.md"))
        self.assertFalse(result["ok"])
        self.assertEqual(result["blocks_checked"], 1)
        self.assertTrue(any(f["symbol"] == "draw_texxt" for f in result["findings"]))

    def test_project_template_tools_are_available(self):
        templates = mcp_payload(list_project_templates("enma"))
        self.assertTrue(any(t["kind"] == "full" for t in templates))
        plan = mcp_payload(generate_script_plan("ESP scaffold", "enma", "full", "game.exe", "source2"))
        self.assertEqual(plan["language"], "enma")
        self.assertIn("pcx verify-project . --allow-placeholders --allow-unverified", plan["commands"])

    def test_scaffold_project_supports_angelscript_overlay(self):
        result = mcp_payload(scaffold_project("Dry Run", "angelscript", "overlay"))
        self.assertEqual(result["language"], "angelscript")
        self.assertEqual(result["entrypoint"], "main.as")

    def test_scaffold_project_write_requires_explicit_env_opt_in(self):
        result = mcp_payload(scaffold_project("Unsafe Write", "enma", "hello", output_dir="/tmp/pcx-unsafe-write", dry_run=False))
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "mcp_writes_disabled")
        self.assertIn("PCX_MCP_ALLOW_WRITES=1", result["message"])

    def test_suggest_imports_from_missing_enma_addon(self):
        result = mcp_payload(suggest_imports("int64 main(){ float64 x = atan2(1.0, 2.0); return 1; }", "enma"))
        self.assertIn('import "math";', result["imports"])

    def test_explain_finding_and_offset_drift_report(self):
        explanation = mcp_payload(explain_finding(json.dumps({"kind": "missing_import", "symbol": "atan2", "fix": 'import "math";'}), "enma"))
        self.assertEqual(explanation["symbol"], "atan2")
        self.assertIn("Add the exact Enma import", explanation["next_action"])

        drift = mcp_payload(offset_drift_report('{"A":"0x1000","B":"0x2000"}', '{"A":"0x1010","C":"0x3000"}'))
        self.assertEqual(drift["summary"]["moved"], 1)
        self.assertEqual(drift["summary"]["missing"], 1)
        self.assertEqual(drift["summary"]["added"], 1)

    def test_search_uses_fts_backend_when_available(self):
        result = mcp_payload(mcp_search("register_routine lifecycle", 3))
        self.assertTrue(result)
        self.assertEqual(result[0]["backend"], "fts")
        self.assertIn("path", result[0])


if __name__ == "__main__":
    unittest.main()
