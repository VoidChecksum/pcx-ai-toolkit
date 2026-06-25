# Rust-First PCX CLI Design

## Goal

Make `pcx` the finished user-facing CLI for pcx-ai-toolkit, with `pcx update` working from Claude Code, PowerShell, and normal terminals after PyPI/npm/source installation.

## Current state

- Python entrypoint: `pcx = tools.pcx:main` in `pyproject.toml`.
- npm entrypoint: `npm/bin/pcx.js` runs `tools/pcx.py` through Python.
- Rust CLI exists as `tools/pe-parser/src/bin/pcx-rs.rs` and already implements much of the command surface.
- Current update scripts assume a git checkout, so installed PyPI/npm users do not get a registry-aware self-update path.
- Roadmap already targets a Rust-first migration.

## Approach

Use a Rust-first CLI with compatibility fallback.

`pcx` stays the only command users need. Launchers prefer the Rust binary when present and fall back to Python only when a command has not yet been ported or the installed artifact lacks the binary. This avoids a risky full rewrite while moving practical command logic to Rust.

## Command contract

`pcx update` auto-detects install mode:

1. npm package install: run the package manager update path (`npm install -g pcx-ai-toolkit@latest`, or matching npm-compatible tool when detectable).
2. PyPI/pip/pipx/uv install: run `python -m pip install --upgrade pcx-ai-toolkit` using the current Python executable.
3. source checkout: keep the existing git update behavior, including dirty-tree safety and optional rebuild steps.
4. unknown install: print a precise manual update command and return non-zero.

Flags stay boring and shared across platforms:

- `--check`: report if update is available without changing files when practical.
- `--force`: rerun source checkout post-update steps.
- `--skip-lsp`, `--skip-skills`, `--skip-bundles`: source checkout only.

## Packaging contract

- npm `bin.pcx` should launch Rust `pcx-rs` if packaged; Python fallback remains temporary.
- PyPI console script may remain Python for now, but it should delegate to Rust when the Rust binary is packaged.
- Release artifacts must include the Rust binary or clearly fall back without breaking existing users.

## Testing

Add/update tests before implementation:

- Rust unit/integration tests for update mode detection and command planning, without executing real package managers.
- Existing Python update-script tests remain for source checkout behavior.
- npm shim behavior gets a minimal test or static packaging check if runnable testing is too heavy.

## Non-goals

- No custom package manager abstraction beyond install detection and command planning.
- No deleting Python fallback in this pass.
- No new user-facing command names besides strengthening `pcx update`.
