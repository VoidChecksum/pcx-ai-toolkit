# Security Policy

## Scope

This policy covers vulnerabilities in **pcx-ai-toolkit's own code** — the Python tools under `tools/`, the `pcx-knowledge-mcp` server (`mcp/pcx-knowledge-mcp/`), the shell setup scripts (`setup.sh`, `setup.ps1`, and `tools/*.sh`), and the LSP wiring under `lsp/`. It does **not** cover end-user scripts written *with* the toolkit (Enma / AngelScript), the Perception.cx product itself, or any third-party RE tools the installers reference.

## Reporting a Vulnerability

**Do not open a public issue for security reports.**

Report privately instead:

- **Preferred:** open a private report via the repository's **Security → Report a vulnerability** tab (GitHub's private security-advisory flow).
- Or send a private GitHub message to [`@VoidChecksum`](https://github.com/VoidChecksum).

Please include, at minimum:

- **Affected file(s)** — exact path(s) within this repo (e.g. `tools/resolve-api-hashes.py`, `mcp/pcx-knowledge-mcp/...`, `setup.sh`).
- **A reproduction or proof of concept** — the smallest set of steps or script that triggers the issue.
- **Impact** — what an attacker could achieve (arbitrary code execution, data leak, supply-chain compromise, broken verification, etc.) and any preconditions.

## Response Expectations

- **Acknowledgement:** within **72 hours** of the report.
- **Fix or advisory:** within **30 days** for issues in `tools/` scripts and the MCP server; longer for lower-severity items in documentation-only paths, with a public advisory if a fix cannot land in that window.
- Reports are triaged by severity and exploitability. If the report is out of scope (see below), we will tell you so and, where useful, point you at the right upstream.

## In Scope / Out of Scope

**In scope:**

- Bugs in `tools/*.py` (e.g. `resolve-api-hashes.py`, `script-linter.py`, `sig-uniqueness-checker.py`, `pe-section-analyzer.py`, `offset-diff.py`, `pattern-format-converter.py`, `binary-diff-summary.py`).
- Bugs in `tools/*.sh` and `tools/pe-parser/`.
- Bugs in `mcp/pcx-knowledge-mcp/` (the knowledge-MCP server) and `mcp/setup-binary-analysis.{sh,ps1}`.
- Bugs in `setup.sh` / `setup.ps1`.
- Bugs in LSP config under `lsp/` (`enma-lsp/`, `angel-lsp-pcx/`).

**Out of scope:**

- User-written Enma / AngelScript scripts produced *with* the toolkit — those are the user's responsibility.
- The Perception.cx product itself — report to its vendor, not here.
- Third-party RE tools invoked by the installers (IDA, Ghidra, etc.) — report upstream.
- Any IDA-related installer layer — that layer was **removed** from this repository and is no longer maintained here. Do not file reports against it.

## Safe Harbor

Good-faith security research on the toolkit's own tooling is welcomed. We will not pursue legal action against reporters who follow this policy, avoid harming users or data, and give us reasonable time to remediate before any public disclosure.

## License

This project is distributed under the **MIT License** (see `LICENSE`). Security fixes are released under the same MIT License.
