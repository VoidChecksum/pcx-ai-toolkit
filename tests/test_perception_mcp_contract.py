import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG = REPO_ROOT / "mcp" / "perception-mcp-config.json"
SCHEMA = REPO_ROOT / "docs" / "perception" / "mcp-tool-schemas.json"
EXAMPLES = REPO_ROOT / "mcp" / "perception-mcp-examples.json"
ERROR_DOC = REPO_ROOT / "docs" / "perception" / "mcp-error-recovery.md"
PCX = REPO_ROOT / "tools" / "pcx.py"

NO_HANDLE = {
    "process/list",
    "process/info_by_pid",
    "process/info_by_name",
    "process/reference_by_pid",
    "process/reference_by_name",
    "process/dereference",
    "process/cleanup_references",
    "process/list_references",
    "system/info",
    "system/list_drivers",
    "script/get_context",
    "script/validate",
    "script/execute",
}


class PerceptionMcpContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config_tools = json.loads(CONFIG.read_text())["mcpServers"]["perception"]["tools"]
        self.schema = json.loads(SCHEMA.read_text())
        self.examples = json.loads(EXAMPLES.read_text())["examples"]

    def test_schema_matches_config_tools(self) -> None:
        schema_tools = [row["name"] for row in self.schema["tools"]]
        self.assertEqual(sorted(schema_tools), sorted(self.config_tools))
        self.assertEqual(len(schema_tools), len(set(schema_tools)))

    def test_examples_cover_every_tool(self) -> None:
        self.assertEqual(sorted(self.examples), sorted(self.config_tools))
        for tool, example in self.examples.items():
            self.assertEqual(example["method"], "tools/call")
            self.assertEqual(example["params"]["name"], tool)
            self.assertIn("arguments", example["params"])

    def test_handle_classification(self) -> None:
        by_name = {row["name"]: row for row in self.schema["tools"]}
        for tool in self.config_tools:
            self.assertEqual(by_name[tool]["requires_handle"], tool not in NO_HANDLE, tool)

    def test_error_recovery_documents_core_codes(self) -> None:
        text = ERROR_DOC.read_text()
        for code in ("-32001", "-32002", "-32003", "-32004"):
            self.assertIn(code, text)

    def test_cli_plans_string_xref(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PCX), "mcp-plan", "find xrefs to PlayerHealth", "--target", "target.exe"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        tools = [step["tool"] for step in payload["steps"]]
        self.assertEqual(payload["workflow"], "string_xref")
        self.assertIn("process/find_string_refs", tools)
        self.assertIn("process/dereference", tools)

    def test_cli_plans_script_validation(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PCX), "mcp-plan", "validate an Enma script"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        tools = [step["tool"] for step in payload["steps"]]
        self.assertEqual(payload["workflow"], "script_validate")
        self.assertIn("script/get_context", tools)
        self.assertIn("script/validate", tools)


if __name__ == "__main__":
    unittest.main()
