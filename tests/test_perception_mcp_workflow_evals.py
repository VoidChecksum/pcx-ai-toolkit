import json
import unittest
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_mcp_workflows import plan_perception_workflow  # noqa: E402


class PerceptionMcpWorkflowEvalTest(unittest.TestCase):
    def test_workflow_evals(self) -> None:
        corpus = json.loads((REPO_ROOT / "evals" / "perception-mcp-workflows.json").read_text())
        for case in corpus["cases"]:
            with self.subTest(case=case["name"]):
                plan = plan_perception_workflow(case["task"], "target.exe", capabilities=case.get("capabilities"))
                tools = [step["tool"] for step in plan["steps"]]
                self.assertEqual(plan["workflow"], case["workflow"])
                for tool in case.get("must_include", []):
                    self.assertIn(tool, tools)
                for tool in case.get("must_not_include", []):
                    self.assertNotIn(tool, tools)
                text = "\n".join(plan["warnings"])
                for warning in case.get("must_warn", []):
                    self.assertIn(warning, text)
                self.assertTrue(any("dereference" in c or "cleanup" in c for c in plan["cleanup"]))


if __name__ == "__main__":
    unittest.main()
