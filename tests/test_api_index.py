"""Regression tests for knowledge/pcx-api-index.json.

Ensures the generated API index contains the core symbols every PCX script
needs, and that build-api-index.py can regenerate it without crashing.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"
BUILDER = REPO_ROOT / "tools" / "build-api-index.py"


class ApiIndexTest(unittest.TestCase):
    def test_index_file_exists(self):
        self.assertTrue(INDEX_FILE.exists(), f"{INDEX_FILE} missing; run python3 {BUILDER}")

    def test_core_symbols_present(self):
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        funcs = set(data.get("functions", {}).keys())
        methods = set(data.get("methods", {}).keys())
        types = set(data.get("types", []))

        required_functions = {
            "draw_rect", "draw_text", "register_routine", "ref_process",
            "get_fps", "key_fired", "main",
        }
        self.assertTrue(required_functions.issubset(funcs),
                        f"missing functions: {required_functions - funcs}")

        required_methods = {"base_address", "add_item", "alive", "attach"}
        self.assertTrue(required_methods.issubset(methods),
                        f"missing methods: {required_methods - methods}")

        required_types = {"vec2", "vec3", "vec4", "color", "quat", "mat4", "proc_t", "uint64"}
        self.assertTrue(required_types.issubset(types),
                        f"missing types: {required_types - types}")

    def test_angelscript_symbols_present(self):
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        funcs = data.get("functions", {})
        methods = data.get("methods", {})

        self.assertGreaterEqual(data.get("doc_count", 0), 39)
        self.assertTrue(any(sig.get("language") == "angelscript"
                            for sig in funcs.get("register_callback", [])))
        self.assertTrue(any(sig.get("language") == "angelscript"
                            for sig in funcs.get("ref_process", [])))
        self.assertTrue(any(sig.get("language") == "angelscript"
                            for sig in methods.get("deref", [])))
        self.assertTrue(any(sig.get("language") == "angelscript"
                            for sig in methods.get("get_all_tebs", [])))

    def test_language_addon_symbols_present(self):
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        funcs = data.get("functions", {})
        methods = data.get("methods", {})

        self.assertTrue(any(sig.get("language") == "enma"
                            for sig in funcs.get("atan2", [])))
        self.assertTrue(any(sig.get("language") == "enma"
                            for sig in funcs.get("json_object", [])))
        self.assertTrue(any(sig.get("language") == "enma"
                            for sig in methods.get("pretty", [])))
        self.assertTrue(any(sig.get("language") == "angelscript"
                            for sig in funcs.get("closeTo", [])))

    def test_builder_check_passes(self):
        result = subprocess.run(
            [sys.executable, str(BUILDER), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0,
                         f"build-api-index --check failed:\n{result.stdout}\n{result.stderr}")
        self.assertIn("is up to date", result.stdout)


if __name__ == "__main__":
    unittest.main()
