import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class DistributionTest(unittest.TestCase):
    def test_mcp_publish_workflow_uses_trusted_publishing(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "publish-mcp.yml"
        self.assertTrue(workflow.exists(), "missing MCP publish workflow")
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("id-token: write", text)
        self.assertIn("pypa/gh-action-pypi-publish", text)
        self.assertNotIn("session_id", text)


if __name__ == "__main__":
    unittest.main()
