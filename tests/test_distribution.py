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

    def test_release_publishes_root_pypi_with_trusted_publishing(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "release.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("id-token: write", text)
        self.assertIn("Build root Python package", text)
        self.assertIn("python -m build", text)
        self.assertIn("twine check dist/*", text)
        self.assertIn("pypa/gh-action-pypi-publish@release/v1", text)
        self.assertIn("packages-dir: dist", text)
        self.assertNotIn("TWINE_PASSWORD", text)
        self.assertNotIn("password:", text)

    def test_release_publishes_npm_with_trusted_publishing(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "release.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("Build npm package", text)
        self.assertIn('node-version: "24"', text)
        self.assertIn("npm-version", text)
        self.assertIn("npm pack --dry-run", text)
        self.assertIn("npm publish", text)
        self.assertNotIn("NODE_AUTH_TOKEN", text)
        self.assertNotIn("NPM_TOKEN", text)

    def test_readme_documents_registry_trusted_publishers(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("PyPI Trusted Publisher", readme)
        self.assertIn("npm Trusted Publisher", readme)
        self.assertIn("Workflow filename: `release.yml`", readme)

    def test_readme_documents_pcx_update(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("pcx update", readme)
        self.assertIn("npm install -g pcx-ai-toolkit@latest", readme)
        self.assertIn("python -m pip install --upgrade pcx-ai-toolkit", readme)

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

    def test_release_packages_stage_rust_cli_for_registries(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "release.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("mkdir -p pcx-bin", text)
        self.assertIn("cp tools/pe-parser/target/release/pcx-rs pcx-bin/pcx-rs", text)
        self.assertLess(text.index("cargo build --release --bin pcx-rs"), text.index("python -m build"))
        self.assertLess(text.index("cargo build --release --bin pcx-rs"), text.index("npm pack --dry-run"))

    def test_root_python_package_ships_rust_cli(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"pcx-bin" = ["pcx-bin/pcx-rs"]', pyproject)

    def test_root_python_package_ships_runtime_data(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"knowledge" = ["knowledge/pcx-api-index.json", "knowledge/unsupported-symbols.json"]', pyproject)
        self.assertIn('"templates/full-project"', pyproject)
        self.assertIn('"tools" = ["tools/update-toolkit.sh", "tools/update-toolkit.ps1"]', pyproject)

    def test_npm_package_exposes_pcx_bin_for_node_and_bun(self):
        package = (REPO_ROOT / "package.json").read_text(encoding="utf-8")
        launcher = REPO_ROOT / "npm" / "bin" / "pcx.js"
        self.assertTrue(launcher.exists(), "missing npm pcx launcher")
        self.assertIn('"name": "pcx-ai-toolkit"', package)
        self.assertIn('"pcx": "npm/bin/pcx.js"', package)
        self.assertIn('"knowledge/*.json"', package)
        self.assertIn('"templates/**/*"', package)
        self.assertIn('"pcx-bin/pcx-rs*"', package)

    def test_npm_shim_prefers_rust_cli(self):
        shim = (REPO_ROOT / "npm" / "bin" / "pcx.js").read_text(encoding="utf-8")
        self.assertIn("pcx-rs", shim)
        self.assertLess(shim.index("pcx-rs"), shim.index("pcx.py"))


if __name__ == "__main__":
    unittest.main()
