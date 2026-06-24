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

    def test_extension_release_uploads_checksummed_vsix(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "release.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("sha256sum *.vsix > SHA256SUMS.txt", text)
        self.assertIn("release-artifacts/*.vsix", text)
        self.assertIn("release-artifacts/SHA256SUMS.txt", text)

    def test_release_uploads_rust_cli_artifact(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "release.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("Build Rust CLI", text)
        self.assertIn("cargo build --release --bin pcx-rs", text)
        self.assertIn("release-artifacts/pcx-rs", text)


if __name__ == "__main__":
    unittest.main()
