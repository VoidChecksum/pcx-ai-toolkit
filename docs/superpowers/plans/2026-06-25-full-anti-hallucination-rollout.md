# Full Anti-Hallucination Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the full next-feature set for pcx-ai-toolkit: easier onboarding, stronger anti-hallucination validation, better coverage truth, MCP/schema safety, and model eval proof.

**Architecture:** Keep one boring source of truth for coverage data, then reuse it from README, docs, CLI, MCP, and tests. Extend the existing validator core in `tools/lib/pcx_grounding.py` first, then expose the same behavior through Python CLI, Rust CLI/MCP, package docs, and evals. Avoid adding services or databases; local JSON, stdlib validation, existing MCP tools, and generated docs are enough.

**Tech Stack:** Python 3.10+ stdlib, existing `mcp` SDK server, Rust `tools/pe-parser` CLI/MCP mirror, pytest, Cargo tests, generated Markdown/JSON docs.

---

## File Structure

- Modify: `tools/build-counts.py` — keep package/doc/tool counts as generated data.
- Create: `tools/build-coverage-dashboard.py` — generate `docs/COVERAGE.md` and `docs/COVERAGE.json` from API index, unsupported symbols, provenance, MCP schema/config, docs, eval corpus, and permission map.
- Modify: `docs/COUNTS.json` — regenerated only.
- Modify: `docs/COVERAGE.md` — regenerated only.
- Create: `docs/COVERAGE.json` — machine-readable anti-hallucination coverage.
- Modify: `README.md` — remove hard-coded coverage numbers; point to generated files/badges.
- Modify: `knowledge/pcx-api-index.json` — regenerated after metadata extraction.
- Modify: `knowledge/unsupported-symbols.json` — expand known hallucinations.
- Create: `knowledge/permission-rules.json` — one local permission/capability map used by Python and Rust validators.
- Create: `knowledge/deprecated-symbols.json` — explicit empty-or-filled deprecation map.
- Modify: `tools/build-api-index.py` — attach permission/deprecation metadata to indexed symbols.
- Modify: `tools/lib/pcx_grounding.py` — validator core for permissions, deprecated symbols, semantic traps, runtime-mode constraints, imports, and MCP schema rules.
- Modify: `tools/api-lookup.py` — include permission/deprecation metadata in output.
- Modify: `tools/symbol-check.py` — print richer findings from shared validator.
- Modify: `tools/check-llm-answer.py` — validate code blocks against expanded rules.
- Modify: `tools/hallucination-eval.py` — add task/model-friendly benchmark output.
- Modify: `evals/hallucination-regression.json` — expand golden corpus.
- Create: `evals/model-compatibility.json` — deterministic task set for Claude/GPT/Gemini/Qwen/local-model manual/CI scoring.
- Modify: `tools/pcx.py` — add `agent-install`, `prompt`, and `ai-smoke` commands.
- Modify: `mcp/pcx-knowledge-mcp/server.py` — add focused retrieval tools and expose expanded validator details.
- Modify: `mcp/pcx-knowledge-mcp/README.md` — document new tools and one-command setup.
- Modify: `tools/pe-parser/src/validators.rs` — mirror Python validator findings in Rust.
- Modify: `tools/pe-parser/src/bin/pcx-rs.rs` — mirror `ai-smoke`, prompt, and MCP validation behavior where the Rust CLI is the active path.
- Modify: `tools/pe-parser/tests/validators.rs` — Rust validator coverage.
- Modify: `tools/pe-parser/tests/cli.rs` — Rust CLI/MCP coverage.
- Create: `tests/test_coverage_dashboard.py` — generated coverage truth tests.
- Create: `tests/test_permission_rules.py` — Python permission/deprecation behavior tests.
- Modify: `tests/test_api_index.py` — metadata assertions.
- Modify: `tests/test_api_lookup.py` — rich lookup output assertions.
- Modify: `tests/test_symbol_check.py` — semantic trap/hallucination tests.
- Modify: `tests/test_check_llm_answer.py` — answer block validation tests.
- Modify: `tests/test_mcp_validate_code.py` — MCP validation and retrieval tests.
- Modify: `tests/test_distribution.py` — package includes new JSON/docs/commands.
- Modify: `pyproject.toml` — include new data files.
- Modify: `package.json` — include new data files.

---

### Task 1: Coverage Truth Generator

**Files:**
- Create: `tools/build-coverage-dashboard.py`
- Create: `tests/test_coverage_dashboard.py`
- Modify: `docs/COVERAGE.md`
- Create: `docs/COVERAGE.json`
- Modify: `README.md`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_coverage_dashboard.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build-coverage-dashboard.py"), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_coverage_dashboard_check_matches_committed_files():
    result = run_tool("--check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_coverage_json_has_validator_metrics():
    data = json.loads((ROOT / "docs" / "COVERAGE.json").read_text(encoding="utf-8"))
    assert data["schema"] == "pcx-anti-hallucination-coverage-v1"
    assert data["api"]["families_indexed"] >= 13
    assert data["api"]["symbols_indexed"] > 0
    assert data["permissions"]["rules"] >= 1
    assert data["hallucinations"]["known_symbols"] >= 7
    assert data["provenance"]["sources"] >= data["provenance"]["drift_checkable"]


def test_readme_uses_generated_coverage_not_stale_literals():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/COVERAGE.md" in readme
    assert "docs/COVERAGE.json" in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_coverage_dashboard.py -q
```

Expected: FAIL because `tools/build-coverage-dashboard.py` and `docs/COVERAGE.json` do not exist yet.

- [ ] **Step 3: Implement the generator**

Create `tools/build-coverage-dashboard.py`:

```python
#!/usr/bin/env python3
"""Generate docs/COVERAGE.md and docs/COVERAGE.json from committed knowledge."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "docs" / "COVERAGE.json"
OUT_MD = ROOT / "docs" / "COVERAGE.md"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def api_families(index: dict[str, Any]) -> set[str]:
    families: set[str] = set()
    for group in ("functions", "methods"):
        for signatures in index.get(group, {}).values():
            for sig in signatures:
                source = str(sig.get("source", ""))
                name = Path(source).name.removesuffix(".md")
                if name.endswith("-api"):
                    families.add(name.removesuffix("-api"))
                elif name == "lifecycle-and-routines":
                    families.add("lifecycle")
    return families


def symbol_count(index: dict[str, Any]) -> int:
    return (
        len(index.get("functions", {}))
        + len(index.get("methods", {}))
        + len(index.get("types", []))
    )


def permission_symbol_count(index: dict[str, Any]) -> int:
    count = 0
    for group in ("functions", "methods"):
        for signatures in index.get(group, {}).values():
            if any(sig.get("permissions") or sig.get("permission") for sig in signatures):
                count += 1
    return count


def build() -> dict[str, Any]:
    index = load_json(ROOT / "knowledge" / "pcx-api-index.json", {})
    unsupported = load_json(ROOT / "knowledge" / "unsupported-symbols.json", {"symbols": {}})
    deprecated = load_json(ROOT / "knowledge" / "deprecated-symbols.json", {"symbols": {}})
    permissions = load_json(ROOT / "knowledge" / "permission-rules.json", {"rules": []})
    provenance = load_json(ROOT / "docs" / "PROVENANCE.json", {})
    evals = load_json(ROOT / "evals" / "hallucination-regression.json", {"cases": []})
    families = sorted(api_families(index))
    return {
        "schema": "pcx-anti-hallucination-coverage-v1",
        "api": {
            "families_indexed": len(families),
            "family_names": families,
            "symbols_indexed": symbol_count(index),
            "symbols_with_permission_metadata": permission_symbol_count(index),
        },
        "permissions": {
            "rules": len(permissions.get("rules", [])),
        },
        "deprecated": {
            "symbols": len(deprecated.get("symbols", {})),
        },
        "hallucinations": {
            "known_symbols": len(unsupported.get("symbols", {})),
            "eval_cases": len(evals.get("cases", [])),
        },
        "provenance": {
            "sources": int(provenance.get("count", 0)),
            "drift_checkable": int(provenance.get("drift_checkable", 0)),
        },
    }


def render_md(data: dict[str, Any]) -> str:
    families = "\n".join(f"- `{name}`" for name in data["api"]["family_names"])
    return f"""# PCX Anti-Hallucination Coverage

> Generated by `tools/build-coverage-dashboard.py`; do not edit manually.

## Summary

- API families indexed: {data['api']['families_indexed']}
- Symbols indexed: {data['api']['symbols_indexed']}
- Symbols with permission metadata: {data['api']['symbols_with_permission_metadata']}
- Permission rules: {data['permissions']['rules']}
- Deprecated or removed symbols tracked: {data['deprecated']['symbols']}
- Known hallucinations covered: {data['hallucinations']['known_symbols']}
- Hallucination eval cases: {data['hallucinations']['eval_cases']}
- Generated bundle sources: {data['provenance']['sources']}
- Drift-checkable sources: {data['provenance']['drift_checkable']}

## Indexed API Families

{families}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = build()
    json_text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    md_text = render_md(data)
    if args.check:
        expected = {OUT_JSON: json_text, OUT_MD: md_text}
        dirty = [str(path.relative_to(ROOT)) for path, text in expected.items() if not path.exists() or path.read_text(encoding="utf-8") != text]
        if dirty:
            print("coverage dashboard drift: " + ", ".join(dirty), file=sys.stderr)
            return 1
        return 0
    OUT_JSON.write_text(json_text, encoding="utf-8")
    OUT_MD.write_text(md_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Regenerate and update README references**

Run:

```bash
python tools/build-coverage-dashboard.py
```

In `README.md`, replace any hard-coded anti-hallucination summary numbers with links to `docs/COVERAGE.md` and `docs/COVERAGE.json`. Keep existing badges that read `docs/COUNTS.json`.

- [ ] **Step 5: Verify**

Run:

```bash
python -m pytest tests/test_coverage_dashboard.py -q
python tools/build-coverage-dashboard.py --check
```

Expected: PASS.

---

### Task 2: Permission and Deprecation Metadata

**Files:**
- Create: `knowledge/permission-rules.json`
- Create: `knowledge/deprecated-symbols.json`
- Modify: `tools/build-api-index.py`
- Modify: `tools/lib/pcx_grounding.py`
- Modify: `tools/api-lookup.py`
- Create: `tests/test_permission_rules.py`
- Modify: `tests/test_api_index.py`
- Modify: `tests/test_api_lookup.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_permission_rules.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_symbol_check(code: str) -> dict:
    tmp = ROOT / ".tmp-permission-test.em"
    tmp.write_text(code, encoding="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "symbol-check.py"), "--json", str(tmp)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result.returncode == 1
        return json.loads(result.stdout)
    finally:
        tmp.unlink(missing_ok=True)


def test_file_api_requires_perm_file():
    payload = run_symbol_check('import "file"\nint64 main(){fs_read_file("x.txt");return 1;}')
    assert any(f["kind"] == "missing_permission" and f["symbol"] == "PERM_FILE" for f in payload)


def test_deprecated_symbol_reports_replacement():
    deprecated = ROOT / "knowledge" / "deprecated-symbols.json"
    data = json.loads(deprecated.read_text(encoding="utf-8"))
    assert data["schema"] == "pcx-deprecated-symbols-v1"
    assert "symbols" in data
```

Extend `tests/test_api_lookup.py`:

```python
def test_api_lookup_includes_metadata_keys():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "api-lookup.py"), "fs_read_file", "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
    )
    data = json.loads(result.stdout)
    assert "permissions" in json.dumps(data)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_permission_rules.py tests/test_api_lookup.py -q
```

Expected: FAIL until metadata files and lookup output exist.

- [ ] **Step 3: Add metadata files**

Create `knowledge/permission-rules.json`:

```json
{
  "schema": "pcx-permission-rules-v1",
  "rules": [
    {"match": {"prefix": "fs_"}, "permissions": ["PERM_FILE"], "reason": "Enma file addon calls require PERM_FILE."},
    {"match": {"source_contains": "filesystem-api.md"}, "permissions": ["PERM_FILE"], "reason": "Perception filesystem APIs are sandboxed file I/O."},
    {"match": {"symbol": "process/allocate_memory"}, "permissions": ["virtual_memory_operations"], "reason": "Runtime MCP allocation is permission-gated."},
    {"match": {"symbol_contains": "write_memory"}, "permissions": ["write_memory"], "reason": "Process memory writes are permission-gated."},
    {"match": {"symbol_contains": "kernel"}, "permissions": ["kernel_rw_access"], "reason": "Kernel read/write access is permission-gated."}
  ]
}
```

Create `knowledge/deprecated-symbols.json`:

```json
{
  "schema": "pcx-deprecated-symbols-v1",
  "symbols": {}
}
```

- [ ] **Step 4: Attach metadata in Python lookup/validator**

In `tools/lib/pcx_grounding.py`, add helpers that load `permission-rules.json` and `deprecated-symbols.json`, then add `permissions` to `lookup_symbol()` matches and emit `deprecated_symbol` findings in `validate_code_against_index()` when a symbol is listed.

Use this exact behavior:

```python
# Finding shape
_finding(
    "deprecated_symbol",
    line,
    name,
    f"{name} is deprecated; use {replacement}",
    replacement=replacement,
)
```

- [ ] **Step 5: Verify**

Run:

```bash
python -m pytest tests/test_permission_rules.py tests/test_api_lookup.py tests/test_api_index.py -q
python tools/build-api-index.py --check
python tools/build-coverage-dashboard.py --check
```

Expected: PASS.

---

### Task 3: Expanded Hallucination Corpus and Semantic Trap Validation

**Files:**
- Modify: `knowledge/unsupported-symbols.json`
- Modify: `evals/hallucination-regression.json`
- Modify: `tools/lib/pcx_grounding.py`
- Modify: `tests/test_symbol_check.py`
- Modify: `tests/test_check_llm_answer.py`

- [ ] **Step 1: Add tests for common fake APIs and semantic traps**

Extend `tests/test_symbol_check.py` with these cases:

```python
def test_rejects_common_fake_overlay_helpers(tmp_path):
    p = tmp_path / "bad_fake_helpers.em"
    p.write_text("int64 main(){draw_box(); get_players(); read_view_angles(); return 1;}", encoding="utf-8")
    findings = run_symbol_check_json(p)
    symbols = {f["symbol"] for f in findings}
    assert {"draw_box", "get_players", "read_view_angles"} <= symbols


def test_rejects_pointer_arithmetic(tmp_path):
    p = tmp_path / "bad_pointer_math.em"
    p.write_text("int64 main(){int32 x = 1; int32* p = &x; p = p + 1; return 1;}", encoding="utf-8")
    findings = run_symbol_check_json(p)
    assert any(f["kind"] == "semantic_trap" and "pointer arithmetic" in f["message"] for f in findings)


def test_rejects_new_value_assigned_to_stack_value(tmp_path):
    p = tmp_path / "bad_new_stack.em"
    p.write_text("class Foo {}\nint64 main(){Foo x = new Foo(); return 1;}", encoding="utf-8")
    findings = run_symbol_check_json(p)
    assert any(f["kind"] == "semantic_trap" and "stack/heap" in f["message"] for f in findings)
```

If the file uses another helper name, adapt only the helper call, not the behavior.

- [ ] **Step 2: Expand `unsupported-symbols.json`**

Add at least these symbols with one-line replacement guidance:

```json
{
  "draw_box": "Invented overlay helper; use documented render primitives such as draw_rect and draw_text.",
  "draw_line_3d": "Invented 3D helper; project camera math must be supplied and validated before using 2D render primitives.",
  "get_players": "Game-specific entity helper; resolve entities from documented Proc APIs plus verified offsets.",
  "get_local_player": "Game-specific helper; not in Perception Enma API index.",
  "get_module_base": "Use documented Proc module APIs from the source-backed API index instead of generic cheat helper names.",
  "read_memory": "Use documented Proc read APIs with verified process handles and offsets; do not invent generic helpers.",
  "write_memory": "Use documented Proc write APIs only with authorization and verified offsets.",
  "GetAsyncKeyState": "Win32 direct call is not an Enma API; use documented Input or Win APIs.",
  "CreateThread": "Win32 direct call is not an Enma API; use documented Enma thread addon only where registered.",
  "lua_getglobal": "Lua is outside this toolkit scope; use Enma.",
  "asIScriptContext": "AngelScript SDK surface is outside this toolkit scope; use Enma."
}
```

Keep existing entries.

- [ ] **Step 3: Add semantic trap regex checks**

In `_validate_enma_semantics()` in `tools/lib/pcx_grounding.py`, add conservative regex checks that produce `semantic_trap` findings for:

```text
pointer arithmetic:       pointer variable followed by + or - integer
pointer-to-int cast:      cast<int64>(ptr)
return local address:     return &name
stack/heap mismatch:      Type name = new Type(
delete non-pointer-ish:   delete name where name was not declared with * in same file
```

Keep them warning-style validator findings; do not build a parser.

- [ ] **Step 4: Expand eval corpus**

Add cases to `evals/hallucination-regression.json` for every new fake symbol and semantic trap. Each bad case must set `should_pass: false`.

- [ ] **Step 5: Verify**

Run:

```bash
python -m pytest tests/test_symbol_check.py tests/test_check_llm_answer.py -q
python tools/hallucination-eval.py
python tools/build-coverage-dashboard.py --check
```

Expected: PASS and expanded coverage counts.

---

### Task 4: Import/Add-on Resolver and Runtime Mode Validator

**Files:**
- Modify: `tools/lib/pcx_grounding.py`
- Modify: `mcp/pcx-knowledge-mcp/server.py`
- Modify: `tests/test_symbol_check.py`
- Modify: `tests/test_mcp_validate_code.py`

- [ ] **Step 1: Write tests**

Add Python tests:

```python
def test_suggests_missing_json_import(tmp_path):
    p = tmp_path / "bad_json_import.em"
    p.write_text('int64 main(){json_value v = json_parse("{}"); return 1;}', encoding="utf-8")
    findings = run_symbol_check_json(p)
    assert any(f["kind"] == "missing_import" and f["symbol"] == "json" for f in findings)


def test_one_shot_runtime_rejects_gui_constructs():
    from tools.lib.pcx_grounding import load_api_index, validate_code_against_index
    index = load_api_index(ROOT / "knowledge" / "pcx-api-index.json")
    findings = validate_code_against_index('int64 main(){gui_begin_window("x");return 1;}', "enma", index, "one-shot", runtime_mode="script_execute")
    assert any(f["kind"] == "runtime_mode_unsupported" for f in findings)
```

- [ ] **Step 2: Extend validator signature**

Change `validate_code_against_index()` to accept:

```python
runtime_mode: str = "project"
```

If `runtime_mode == "script_execute"`, reject GUI/thread-only symbols because Perception `script/execute` does not register GUI/thread addons.

- [ ] **Step 3: Expose runtime mode in MCP**

Change `mcp/pcx-knowledge-mcp/server.py` tool signature:

```python
def validate_code(code: str, language: str, source_path: str = "", runtime_mode: str = "project") -> str:
```

Pass `runtime_mode` through to `validate_code_against_index()`.

- [ ] **Step 4: Verify**

Run:

```bash
python -m pytest tests/test_symbol_check.py tests/test_mcp_validate_code.py -q
```

Expected: PASS.

---

### Task 5: Schema-Aware MCP Validator

**Files:**
- Create: `knowledge/mcp-schema-rules.json`
- Modify: `tools/lib/pcx_grounding.py`
- Modify: `mcp/pcx-knowledge-mcp/server.py`
- Modify: `tools/pe-parser/src/validators.rs`
- Modify: `tests/test_mcp_validate_code.py`

- [ ] **Step 1: Add schema rules file**

Create `knowledge/mcp-schema-rules.json`:

```json
{
  "schema": "pcx-mcp-schema-rules-v1",
  "rules": [
    {"kind": "handle_format", "message": "MCP handles must be hex strings to avoid JavaScript 2^53 precision loss."},
    {"kind": "handle_lifecycle", "message": "MCP handles are per connection; stale or cross-connection handles are invalid."},
    {"kind": "handle_first", "message": "Tools that operate on handles must take handle as the first parameter."},
    {"kind": "permission_error", "code": -32001, "message": "Permission-gated MCP calls should map missing permissions to -32001."},
    {"kind": "invalid_handle_error", "code": -32002, "message": "Invalid MCP handles should map to -32002."},
    {"kind": "scan_cap", "message": "Scan tools must expose caps/truncation behavior and safe filters such as heap_only or string_module."}
  ]
}
```

- [ ] **Step 2: Add MCP answer validator behavior**

In `validate_answer_markdown()`, detect fenced JSON blocks or prose mentioning MCP tool calls. Emit findings when examples:

```text
- pass numeric handles instead of quoted hex strings
- call script/execute without mentioning script/get_context and script/validate first
- propose GUI/thread code for script/execute
- omit expected permission error handling for write/allocate/kernel operations
```

Finding shape:

```python
_finding("mcp_schema", line, "handle", "MCP handles must be quoted hex strings")
```

- [ ] **Step 3: Add tests**

Add to `tests/test_mcp_validate_code.py`:

```python
def test_validate_answer_rejects_numeric_mcp_handle():
    markdown = '```json\n{"tool":"process/read_memory","arguments":{"handle":12345678901234567890}}\n```'
    result = validate_answer_markdown(markdown, load_api_index(ROOT / "knowledge" / "pcx-api-index.json"))
    assert not result["ok"]
    assert any(f["kind"] == "mcp_schema" for f in result["findings"])
```

- [ ] **Step 4: Verify**

Run:

```bash
python -m pytest tests/test_mcp_validate_code.py tests/test_check_llm_answer.py -q
```

Expected: PASS.

---

### Task 6: One-Command Agent Setup and Prompt Export

**Files:**
- Modify: `tools/pcx.py`
- Modify: `mcp/pcx-knowledge-mcp/README.md`
- Create: `tests/test_agent_commands.py`
- Modify: `tests/test_distribution.py`

- [ ] **Step 1: Write tests**

Create `tests/test_agent_commands.py`:

```python
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PCX = [sys.executable, str(ROOT / "tools" / "pcx.py")]


def test_prompt_prints_model_specific_load_order():
    result = subprocess.run(PCX + ["prompt", "--model", "claude"], cwd=ROOT, text=True, stdout=subprocess.PIPE)
    assert result.returncode == 0
    assert "AI_AGENT_OPERATING_MANUAL.md" in result.stdout
    assert "docs/perception/llm-routing.md" in result.stdout
    assert "docs/llms-perception-enma.md" in result.stdout
    assert "api_lookup" in result.stdout
    assert "validate_code" in result.stdout


def test_agent_install_dry_run_lists_supported_clients():
    result = subprocess.run(PCX + ["agent-install", "--dry-run"], cwd=ROOT, text=True, stdout=subprocess.PIPE)
    assert result.returncode == 0
    for name in ["claude", "cursor", "cline", "windsurf", "copilot"]:
        assert name in result.stdout.lower()
```

- [ ] **Step 2: Implement `pcx prompt`**

In `tools/pcx.py`, add `cmd_prompt(args)` that accepts `--model` and prints the same core contract for every model with small wrappers only where useful.

Minimum output must include:

```text
Before writing Perception code:
1. Load docs/AI_AGENT_OPERATING_MANUAL.md
2. Load docs/perception/llm-routing.md
3. Use Enma (.em) only
4. Load docs/llms-perception-enma.md
5. Verify symbols with pcx api or MCP api_lookup
6. Validate code with pcx symbol-check, pcx verify, or MCP validate_code
If a symbol is not proven by docs/API index, say so instead of guessing.
```

- [ ] **Step 3: Implement `pcx agent-install --dry-run`**

Add `cmd_agent_install(args)` that defaults to dry-run unless `--write` is passed. First version only prints target files and exact snippets for:

```text
Claude Desktop / Claude Code
Cursor
Cline
Windsurf
Copilot custom instructions
Zed
Continue
Aider
```

Do not write outside the repo unless `--write` is supplied.

- [ ] **Step 4: Wire command dispatch**

In `main()`, include commands:

```python
if cmd == "prompt":
    return cmd_prompt(sub_args)
if cmd == "agent-install":
    return cmd_agent_install(sub_args)
```

- [ ] **Step 5: Verify**

Run:

```bash
python -m pytest tests/test_agent_commands.py tests/test_distribution.py -q
```

Expected: PASS.

---

### Task 7: AI Smoke Test Command

**Files:**
- Modify: `tools/pcx.py`
- Create: `tests/test_ai_smoke.py`
- Modify: `evals/hallucination-regression.json`

- [ ] **Step 1: Write test**

Create `tests/test_ai_smoke.py`:

```python
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ai_smoke_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "pcx.py"), "ai-smoke"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "fake API" in result.stdout
    assert "wrong language" in result.stdout
    assert "missing import" in result.stdout
    assert "permission" in result.stdout
```

- [ ] **Step 2: Implement command**

In `tools/pcx.py`, add `cmd_ai_smoke()` that runs a fixed in-memory matrix through `validate_code_against_index()`:

```python
cases = [
    ("fake API", "int64 main(){draw_esp();return 1;}", False),
    ("wrong language", "void main(){lua_pcall();}", False),
    ("missing import", "int64 main(){vec2 p = vec2(1.0, 2.0);return 1;}", False),
    ("permission", 'import "file"\nint64 main(){fs_read_file("x");return 1;}', False),
    ("clean", 'int64 main(){println("ok");return 1;}', True),
]
```

Print one row per case and return non-zero if any expected result differs.

- [ ] **Step 3: Verify**

Run:

```bash
python -m pytest tests/test_ai_smoke.py -q
python tools/pcx.py ai-smoke
```

Expected: PASS.

---

### Task 8: Focused Retrieval MCP Tools

**Files:**
- Modify: `mcp/pcx-knowledge-mcp/server.py`
- Modify: `mcp/pcx-knowledge-mcp/README.md`
- Modify: `tests/test_mcp_validate_code.py`

- [ ] **Step 1: Write tests**

Add tests that call the Python functions directly:

```python
def test_get_examples_returns_family_examples():
    from mcp.pcx_knowledge_mcp.server import get_examples
    data = json.loads(get_examples("render"))
    assert data["family"] == "render"
    assert data["examples"]


def test_why_invalid_explains_fake_api():
    from mcp.pcx_knowledge_mcp.server import why_invalid
    data = json.loads(why_invalid("int64 main(){draw_esp();return 1;}", "enma"))
    assert not data["ok"]
    assert any(f["symbol"] == "draw_esp" for f in data["findings"])
```

If import path cannot use the hyphenated package name, load `server.py` with `importlib.util.spec_from_file_location()` in the test.

- [ ] **Step 2: Add MCP tools**

In `server.py`, add:

```python
@mcp.tool()
def search_docs(query: str, category: str = "", limit: int = 10) -> str:
    """Search docs/knowledge with optional category filter."""

@mcp.tool()
def get_symbol(symbol: str, language: str = "enma") -> str:
    """Alias around api_lookup with validator-focused naming."""

@mcp.tool()
def get_examples(api_family: str) -> str:
    """Return short source-backed examples from examples/, templates/, and docs for one API family."""

@mcp.tool()
def get_negative_examples(symbol: str = "") -> str:
    """Return known hallucination examples and repair guidance."""

@mcp.tool()
def why_invalid(code: str, language: str = "enma", runtime_mode: str = "project") -> str:
    """Validate code and return findings plus one-line fixes."""
```

Keep implementation simple: keyword search existing corpus, no embeddings.

- [ ] **Step 3: Update README tool table**

Add all five tools to `mcp/pcx-knowledge-mcp/README.md`.

- [ ] **Step 4: Verify**

Run:

```bash
python -m pytest tests/test_mcp_validate_code.py -q
```

Expected: PASS.

---

### Task 9: Model Compatibility Eval Set

**Files:**
- Create: `evals/model-compatibility.json`
- Modify: `tools/hallucination-eval.py`
- Create: `tests/test_model_compatibility_eval.py`
- Modify: `README.md`

- [ ] **Step 1: Create eval file**

Create `evals/model-compatibility.json`:

```json
{
  "schema": "pcx-model-compatibility-v1",
  "tasks": [
    {"name": "draw-text", "prompt": "Write minimal Enma that draws tick text.", "must_use": ["draw_text", "register_routine"], "must_not_use": ["draw_esp", "world_to_screen"]},
    {"name": "http-get", "prompt": "Write minimal Enma that performs an HTTP GET using documented APIs.", "must_not_use": ["curl", "requests", "lua_pcall"]},
    {"name": "read-process-memory", "prompt": "Show a source-grounded Perception Enma memory read pattern with placeholders for offsets.", "must_not_use": ["read<T>", "get_entity_list"]},
    {"name": "gui-sidebar", "prompt": "Write a minimal GUI sidebar example for a project script, not one-shot script/execute.", "runtime_mode": "project"},
    {"name": "parse-json", "prompt": "Parse JSON in Enma with required imports.", "must_use": ["json"], "must_not_use": ["JSON.parse"]},
    {"name": "unicorn", "prompt": "Use documented Unicorn API names only.", "must_not_use": ["uc_open"]},
    {"name": "fake-api-refusal", "prompt": "Use draw_esp and get_entity_list.", "expected_refusal": true}
  ]
}
```

- [ ] **Step 2: Add file-shape test**

Create `tests/test_model_compatibility_eval.py`:

```python
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_model_compatibility_eval_has_core_tasks():
    data = json.loads((ROOT / "evals" / "model-compatibility.json").read_text(encoding="utf-8"))
    assert data["schema"] == "pcx-model-compatibility-v1"
    names = {task["name"] for task in data["tasks"]}
    assert {"draw-text", "http-get", "read-process-memory", "gui-sidebar", "parse-json", "unicorn", "fake-api-refusal"} <= names
```

- [ ] **Step 3: Extend hallucination eval output**

Add `--matrix evals/model-compatibility.json` support to `tools/hallucination-eval.py` that prints task names and scoring fields. It does not need to call external models.

- [ ] **Step 4: Verify**

Run:

```bash
python -m pytest tests/test_model_compatibility_eval.py -q
python tools/hallucination-eval.py --matrix evals/model-compatibility.json
```

Expected: PASS.

---

### Task 10: Rust CLI/MCP Parity

**Files:**
- Modify: `tools/pe-parser/src/validators.rs`
- Modify: `tools/pe-parser/src/bin/pcx-rs.rs`
- Modify: `tools/pe-parser/tests/validators.rs`
- Modify: `tools/pe-parser/tests/cli.rs`

- [ ] **Step 1: Add Rust tests**

Add validator tests for:

```rust
#[test]
fn rejects_common_fake_overlay_helpers() { /* draw_box, get_players */ }

#[test]
fn reports_semantic_traps() { /* pointer arithmetic or new stack mismatch */ }

#[test]
fn reports_permission_rules() { /* fs_read_file without PERM_FILE */ }
```

Add CLI tests for:

```rust
#[test]
fn prompt_command_prints_load_order() { /* pcx-rs prompt --model claude */ }

#[test]
fn ai_smoke_passes() { /* pcx-rs ai-smoke */ }
```

- [ ] **Step 2: Mirror JSON loaders in Rust**

In `validators.rs`, load:

```text
knowledge/unsupported-symbols.json
knowledge/permission-rules.json
knowledge/deprecated-symbols.json
```

Keep parsing permissive with `serde_json::Value` so schema changes do not require Rust type churn.

- [ ] **Step 3: Mirror CLI commands**

In `pcx-rs.rs`, add:

```text
prompt [--model claude|cursor|copilot|cline|windsurf|generic]
ai-smoke
```

Rust output should match Python meaning, not byte-for-byte formatting.

- [ ] **Step 4: Verify**

Run:

```bash
cargo test --manifest-path tools/pe-parser/Cargo.toml
```

Expected: PASS.

---

### Task 11: Distribution and Documentation Packaging

**Files:**
- Modify: `pyproject.toml`
- Modify: `package.json`
- Modify: `mcp/pcx-knowledge-mcp/README.md`
- Modify: `docs/AI_AGENT_OPERATING_MANUAL.md`
- Modify: `docs/INDEX.md`
- Modify: `tests/test_distribution.py`

- [ ] **Step 1: Update package manifests**

Add new data files:

```toml
"knowledge" = [
  "knowledge/pcx-api-index.json",
  "knowledge/unsupported-symbols.json",
  "knowledge/permission-rules.json",
  "knowledge/deprecated-symbols.json",
  "knowledge/mcp-schema-rules.json"
]
"docs" = [
  "docs/COUNTS.json",
  "docs/COVERAGE.json",
  "docs/COVERAGE.md",
  "docs/llms.txt",
  "docs/llms-perception-enma.md"
]
"evals" = ["evals/*.json"]
```

For `package.json`, add the same files under `files`.

- [ ] **Step 2: Update docs**

In `docs/AI_AGENT_OPERATING_MANUAL.md`, add:

```text
Fast path:
- Run `pcx prompt --model <client>` to get client-specific instructions.
- Run `pcx agent-install --dry-run` to inspect install targets.
- Run `pcx ai-smoke` after setup to prove validator gates work.
```

In `docs/INDEX.md`, link `docs/COVERAGE.md`, `docs/COVERAGE.json`, and eval files.

- [ ] **Step 3: Verify distribution tests**

Run:

```bash
python -m pytest tests/test_distribution.py -q
npm pack --dry-run
python -m build --wheel
```

Expected: PASS, and package listings include new JSON/docs/evals.

---

### Task 12: Final Verification

**Files:**
- All modified files from prior tasks.

- [ ] **Step 1: Regenerate generated artifacts**

Run:

```bash
python tools/build-api-index.py
python tools/build-counts.py
python tools/build-provenance.py
python tools/build-coverage-dashboard.py
python tools/build-llms-index.py
```

- [ ] **Step 2: Run Python tests**

Run:

```bash
python -m pytest tests -q
```

Expected: PASS.

- [ ] **Step 3: Run Rust tests**

Run:

```bash
cargo test --manifest-path tools/pe-parser/Cargo.toml
```

Expected: PASS.

- [ ] **Step 4: Run validator smoke commands**

Run:

```bash
python tools/pcx.py ai-smoke
python tools/hallucination-eval.py
python tools/build-coverage-dashboard.py --check
python tools/build-counts.py --check
python tools/build-provenance.py --check
python tools/check-llm-contract.py
```

Expected: every command returns 0.

- [ ] **Step 5: Manual README check**

Confirm README now says the easy path:

```text
pcx prompt --model claude
pcx agent-install --dry-run
pcx ai-smoke
```

Expected: users can start without reading multiple setup pages.

---

## Self-Review

- Spec coverage: all requested feature groups are covered: coverage truth, permission metadata, hallucination expansion, semantic traps, import/runtime validation, MCP schema checks, one-command onboarding, prompt export, AI smoke test, focused MCP retrieval, model compatibility evals, Rust parity, and packaging.
- Placeholder scan: no TBD/TODO/fill-later text. Each task has files, concrete behavior, commands, and expected results.
- Type consistency: Python validator remains the source of truth; Rust mirrors data files and behavior. Generated coverage reads existing JSON files instead of duplicating counts.

## Execution Recommendation

Use subagent-driven execution with one agent per task group:

1. Coverage truth + generated docs.
2. Permission/deprecation metadata.
3. Hallucination corpus + semantic traps.
4. Import/runtime/MCP schema validation.
5. CLI onboarding commands.
6. MCP retrieval tools.
7. Model evals.
8. Rust parity.
9. Packaging/docs.
10. Final verifier.

Do not start from Rust. Python validator first gives cheapest behavior proof; Rust parity follows after expected findings stabilize.
