# Rust-Only Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove project-owned Python from pcx-ai-toolkit and make Rust the only implementation/runtime surface.

**Architecture:** Keep `tools/pe-parser` as the Rust workspace and make `pcx-rs` the single CLI. Delete compatibility wrappers, packages, tests, and MCP server surfaces instead of preserving compatibility shims. Add Rust repository-hygiene tests so Python does not return accidentally.

**Tech Stack:** Rust 2021, Cargo integration tests, shell/PowerShell launchers, npm package launcher for prebuilt or locally built `pcx-rs`.

---

### Task 1: Add Rust-only guard tests

**Files:**
- Create: `tools/pe-parser/tests/rust_only.rs`

- [ ] Write integration tests that scan the repository and fail while project-owned Python files, `pyproject.toml`, Python CI setup, npm jobs, or Python npm launchers remain.
- [ ] Run `cargo test --manifest-path tools/pe-parser/Cargo.toml --test rust_only` and confirm the tests fail for the current tree.

### Task 2: Remove Python source and package surfaces

**Files:**
- Delete: `tools/**/*.py`, `tests/**/*.py`, `pcx-rs mcpserver.py`, `pcx-rs mcppyproject.toml`, root `pyproject.toml`
- Modify: `package.json`, `README.md`, `docs/INDEX.md`, `docs/AI_AGENT_OPERATING_MANUAL.md`, skills/rules docs that point at Rust tools

- [ ] Delete project-owned Python implementation/test/package files.
- [ ] Remove Rust command metadata and npm publishing references.
- [ ] Replace Rust tool paths in docs with `pcx-rs` or `tools/bin/<native-tool>`.

### Task 3: Make packaging Rust-only

**Files:**
- Modify: `npm/bin/pcx.js`, `package.json`, `.github/workflows/release.yml`, `.github/workflows/publish-mcp.yml`

- [ ] Make the npm launcher execute `tools/bin/pcx-rs` or a platform binary path, never Python.
- [ ] Remove root npm and MCP npm publishing jobs.
- [ ] Keep npm package files limited to Rust binary/docs/templates/knowledge.

### Task 4: Make CI Rust-only

**Files:**
- Modify: `.github/workflows/ci.yml`, `.github/workflows/doc-drift.yml`, `tools/test-runner.sh`

- [ ] Remove Python setup/typecheck/unittest steps.
- [ ] Replace JSON/YAML validation and generated-file checks with Rust/Cargo checks where supported.
- [ ] Update smoke tests to call Rust binaries only.

### Task 5: Update Rust command surface and tests

**Files:**
- Modify: `tools/pe-parser/src/bin/pcx-rs.rs`, `tools/pe-parser/tests/*.rs`

- [ ] Remove fallback functions and help text.
- [ ] Make unknown commands fail clearly instead of delegating to Python.
- [ ] Update Rust tests for the new no-Python command contract.

### Task 6: Regenerate and verify

**Files:**
- Modify generated docs/index/count/provenance artifacts as needed.

- [ ] Run Rust test suite.
- [ ] Run repository hygiene tests.
- [ ] Run `git diff --check`.
- [ ] Commit as `refactor!: remove Python runtime surfaces`.
