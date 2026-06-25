# Anti-Hallucination Rails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the smallest mechanical rails that make Perception Enma API metadata harder to drift or hallucinate.

**Architecture:** Keep source docs canonical. Add schema-backed validation for `knowledge/perception-symbol-versions.json`, generate a lightweight `docs/COVERAGE.md` dashboard from existing artifacts, and include both in existing deterministic checks. No vector DB, no new runtime dependency.

**Tech Stack:** Python stdlib, `unittest`/`pytest`, existing `tools/build-llms-index.py`, existing docs/provenance JSON.

---

### Task 1: Symbol metadata schema test

**Files:**
- Create: `schemas/perception-symbol-versions.schema.json`
- Create: `tests/test_symbol_metadata.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_symbol_metadata.py` that loads `knowledge/perception-symbol-versions.json` and asserts: required top-level fields, required per-symbol fields, unique `(language, symbol)`, valid version strings, valid source paths, valid optional changelog paths, and permission/deprecation types.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_symbol_metadata.py -q`
Expected before schema file exists: FAIL because `schemas/perception-symbol-versions.schema.json` is missing.

- [ ] **Step 3: Add minimal schema file**

Create `schemas/perception-symbol-versions.schema.json` documenting the enforced fields and value shapes. Keep it descriptive and test-owned; do not add `jsonschema` dependency.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_symbol_metadata.py -q`
Expected: PASS.

### Task 2: Coverage dashboard generator

**Files:**
- Create: `tools/build-coverage-dashboard.py`
- Create/Update: `docs/COVERAGE.md`
- Create: `tests/test_coverage_dashboard.py`

- [ ] **Step 1: Write failing dashboard test**

Test that `docs/COVERAGE.md` contains symbol count from `knowledge/perception-symbol-versions.json`, Perception API page coverage from `docs/INDEX.md`, known hallucination count from `knowledge/unsupported-symbols.json`, and provenance freshness from `docs/PROVENANCE.json`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_coverage_dashboard.py -q`
Expected: FAIL because dashboard is absent or stale.

- [ ] **Step 3: Add generator**

Implement `tools/build-coverage-dashboard.py` with stdlib only. It reads existing JSON/docs, writes deterministic Markdown, and supports `--check` for CI-style drift checks.

- [ ] **Step 4: Generate dashboard**

Run: `python3 tools/build-coverage-dashboard.py`
Expected: writes `docs/COVERAGE.md`.

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/test_coverage_dashboard.py -q`
Expected: PASS.

### Task 3: Bundle inclusion and final checks

**Files:**
- Modify: `tools/build-llms-index.py` only if `docs/COVERAGE.md` is not included by existing docs globs.
- Update generated docs bundles if needed.

- [ ] **Step 1: Run drift/generator checks**

Run: `python3 tools/build-llms-index.py --check`
Expected: either PASS or clear drift list.

- [ ] **Step 2: Regenerate bundle outputs if drift appears**

Run: `python3 tools/build-llms-index.py`
Expected: updates `docs/llms*.md/txt`, `docs/COUNTS.json`, `docs/PROVENANCE.json`.

- [ ] **Step 3: Final targeted verification**

Run: `python3 -m pytest tests/test_symbol_metadata.py tests/test_coverage_dashboard.py tests/test_enma_docs_coverage.py tests/test_api_lookup.py -q`
Expected: PASS.
