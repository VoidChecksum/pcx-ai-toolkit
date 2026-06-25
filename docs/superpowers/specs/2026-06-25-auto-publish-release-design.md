# Auto Publish Release Design

Goal: one `v*` tag publishes the toolkit package surfaces that are ready today.

## Scope

- Keep existing GitHub Release asset build in `.github/workflows/release.yml`.
- Add root PyPI package build/check/publish to the same tag workflow.
- Add npm package build/check/publish to the same tag workflow.
- Keep `publish-mcp.yml` separate for `mcp/pcx-knowledge-mcp`.
- Do not add long-lived PyPI tokens to CI.
- Prefer npm trusted publishing/OIDC. If npm trusted publisher is not configured yet, the job should fail clearly rather than silently using a bad token.

## Release flow

1. `push` tag `v*` or manual workflow dispatch starts `.github/workflows/release.yml`.
2. Existing jobs build VS Code VSIX, Visual Studio VSIX, and `pcx-rs`.
3. New Python job builds root package with `python -m build`, checks it with `twine check`, uploads package artifacts, then publishes via `pypa/gh-action-pypi-publish` using GitHub OIDC.
4. New npm job uses Node 24/npm 11, runs `npm pack --dry-run`, uploads the generated `.tgz`, then publishes with `npm publish` using npm trusted publishing/OIDC.
5. GitHub Release job downloads and attaches VSIX/Rust artifacts as before. Package registries remain source of truth for pip/npm installs.

## Required external registry setup

PyPI project `pcx-ai-toolkit`:
- Trusted Publisher: GitHub Actions
- Owner: `VoidChecksum`
- Repository: `pcx-ai-toolkit`
- Workflow filename: `release.yml`
- Optional environment: none for now

npm package `pcx-ai-toolkit`:
- Trusted Publisher: GitHub Actions
- Owner/user: `VoidChecksum`
- Repository: `pcx-ai-toolkit`
- Workflow filename: `release.yml`
- Allowed action: `npm publish`

## Tests

Add distribution tests that fail unless:
- `release.yml` grants `id-token: write`.
- `release.yml` publishes root PyPI through `pypa/gh-action-pypi-publish`.
- `release.yml` publishes npm with Node 24/npm 11 and `npm publish`.
- Release docs mention PyPI and npm trusted-publisher setup.
- No PyPI cookies, PyPI API token names, or `NODE_AUTH_TOKEN` publish path appears in release workflow.

## Non-goals

- No TestPyPI staging.
- No npm token fallback.
- No MCP package merge into root release flow.
- No version bump automation.
