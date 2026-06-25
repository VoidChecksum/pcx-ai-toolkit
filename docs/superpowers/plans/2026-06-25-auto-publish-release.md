# Auto Publish Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `v*` tag automatically publishes root `pcx-ai-toolkit` to PyPI and npm, while keeping existing GitHub Release assets.

**Architecture:** Extend the existing `.github/workflows/release.yml` tag workflow. Use OIDC trusted publishing for PyPI and npm; do not use long-lived publish tokens. Guard behavior with small text-based distribution tests, matching the existing `tests/test_distribution.py` style.

**Tech Stack:** GitHub Actions, PyPI Trusted Publishing (`pypa/gh-action-pypi-publish`), npm Trusted Publishing (Node 24/npm 11), Python `unittest`, YAML workflow config.

---

## File Structure

- Modify `.github/workflows/release.yml`: add OIDC permission, root PyPI build/publish job, npm build/publish job, release-note install guidance.
- Modify `tests/test_distribution.py`: add workflow regression tests for root PyPI and npm publish automation.
- Modify `README.md`: add registry setup notes for PyPI and npm trusted publishers.
- Keep `.github/workflows/publish-mcp.yml` unchanged; it owns only `mcp/pcx-knowledge-mcp`.

---

### Task 1: Add failing release workflow tests

**Files:**
- Modify: `tests/test_distribution.py`

- [ ] **Step 1: Add root PyPI release assertions**

Add this test after `test_mcp_publish_workflow_uses_trusted_publishing`:

```python
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
        self.assertNotIn("pypi-", text)
```

- [ ] **Step 2: Add npm release assertions**

Add this test after the PyPI release test:

```python
    def test_release_publishes_npm_with_trusted_publishing(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "release.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("Build npm package", text)
        self.assertIn("node-version: \"24\"", text)
        self.assertIn("npm-version", text)
        self.assertIn("npm pack --dry-run", text)
        self.assertIn("npm publish", text)
        self.assertNotIn("NODE_AUTH_TOKEN", text)
        self.assertNotIn("NPM_TOKEN", text)
```

- [ ] **Step 3: Add docs setup assertion**

Add this test after the npm release test:

```python
    def test_readme_documents_registry_trusted_publishers(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("PyPI Trusted Publisher", readme)
        self.assertIn("npm Trusted Publisher", readme)
        self.assertIn("Workflow filename: `release.yml`", readme)
```

- [ ] **Step 4: Run red tests**

Run:

```bash
python3 -m unittest tests.test_distribution -v
```

Expected: new tests fail because `release.yml` does not publish root PyPI/npm yet and README lacks trusted-publisher setup notes.

---

### Task 2: Implement release automation

**Files:**
- Modify: `.github/workflows/release.yml`
- Modify: `README.md`

- [ ] **Step 1: Add OIDC permission**

Change workflow permissions to:

```yaml
permissions:
  contents: write
  id-token: write
```

- [ ] **Step 2: Add root PyPI publish job**

Add this job after `build-rust-cli`:

```yaml
  publish-pypi:
    name: Publish root PyPI package
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Build root Python package
        run: |
          python -m pip install --upgrade build twine
          python -m build
          twine check dist/*

      - name: Upload root Python package
        uses: actions/upload-artifact@v4
        with:
          name: root-python-package
          path: dist/*
          retention-days: 1

      - name: Publish root Python package to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist
```

- [ ] **Step 3: Add npm publish job**

Add this job after `publish-pypi`:

```yaml
  publish-npm:
    name: Publish npm package
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "24"
          registry-url: "https://registry.npmjs.org"
          cache: "npm"

      - name: Use npm trusted publishing CLI
        run: npm install -g npm@latest

      - name: Build npm package
        run: |
          npm --version
          npm pack --dry-run
          npm pack

      - name: Upload npm package
        uses: actions/upload-artifact@v4
        with:
          name: npm-package
          path: pcx-ai-toolkit-*.tgz
          retention-days: 1

      - name: Publish npm package
        run: npm publish
```

- [ ] **Step 4: Mention package registries in release body**

Add this section to the GitHub Release body before `### Rust CLI`:

```markdown
            ### Package Managers
            - PyPI: `python -m pip install pcx-ai-toolkit`
            - npm: `npm install -g pcx-ai-toolkit`
            - Bun: `bun add -g pcx-ai-toolkit`
```

- [ ] **Step 5: Add README trusted-publisher setup notes**

Add this section after Quick Start:

```markdown
## Registry Publishing Setup

For automatic package publishing from GitHub Actions, configure trusted publishers once in each registry.

PyPI Trusted Publisher for `pcx-ai-toolkit`:
- Owner: `VoidChecksum`
- Repository: `pcx-ai-toolkit`
- Workflow filename: `release.yml`

npm Trusted Publisher for `pcx-ai-toolkit`:
- Owner/user: `VoidChecksum`
- Repository: `pcx-ai-toolkit`
- Workflow filename: `release.yml`
- Allowed action: `npm publish`
```

---

### Task 3: Verify and commit

**Files:**
- Verify: `.github/workflows/release.yml`
- Verify: `README.md`
- Verify: `tests/test_distribution.py`

- [ ] **Step 1: Run focused distribution tests**

Run:

```bash
python3 -m unittest tests.test_distribution -v
```

Expected: all distribution tests pass.

- [ ] **Step 2: Run full regression slice**

Run:

```bash
python3 -m unittest discover -s tests -v && python3 tools/build-counts.py --check && python3 tools/build-llms-index.py --check && python3 tools/build-provenance.py --check
```

Expected: test suite passes and generated files are in sync.

- [ ] **Step 3: Commit**

Run:

```bash
git add .github/workflows/release.yml README.md tests/test_distribution.py docs/superpowers/specs/2026-06-25-auto-publish-release-design.md docs/superpowers/plans/2026-06-25-auto-publish-release.md
git commit -m "ci: auto publish pcx packages"
```

- [ ] **Step 4: Push**

Run:

```bash
git push origin main
```

Expected: branch pushes cleanly.
