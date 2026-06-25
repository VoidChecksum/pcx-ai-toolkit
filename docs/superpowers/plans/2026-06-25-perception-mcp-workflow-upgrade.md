# Perception MCP Workflow Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make pcx-ai-toolkit teach safe Perception MCP + Enma workflows, then expose a planner tool any LLM can call.

**Architecture:** Keep the first sprint docs-heavy and boring: Markdown playbooks and deterministic JSON metadata first, then a small planner function in the existing knowledge MCP/CLI. Do not build a runtime session manager yet; document handle lifecycle and error recovery so no transport assumptions leak into this sprint.

**Tech Stack:** Markdown docs, existing Python MCP server (`mcp/pcx-knowledge-mcp/server.py`), existing CLI (`tools/pcx.py`), repo-local pytest.

---

### Task 1: Upgrade task playbooks

**Files:**
- Modify: `docs/tasks/proc-read.md`
- Modify: `docs/tasks/pattern-scan.md`
- Modify: `docs/tasks/render-overlay.md`
- Modify: `docs/tasks/gui-config.md`
- Modify: `docs/tasks/filesystem-config.md`
- Modify: `docs/tasks/net-http.md`
- Modify: `docs/tasks/custom-draw.md`
- Modify: `docs/tasks/zydis-disasm.md`
- Modify: `docs/tasks/unicorn-emulation.md`

- [ ] Replace placeholder examples with copy-paste-safe Enma examples.
- [ ] Each doc includes exact imports, symbols, permissions, sentinels, validation command, MCP equivalent, common hallucinations, related skills, and related MCP tools.
- [ ] Keep examples generic: use `target.exe`, `0x1234`, and `E-001 verified offset` comments instead of fake game offsets.

### Task 2: Add Perception MCP workflow docs

**Files:**
- Create: `docs/perception/two-mcp-workflow.md`
- Create: `docs/perception/mcp-workflows.md`
- Create: `docs/perception/mcp-error-recovery.md`
- Create: `docs/perception/mcp-safety-policy.md`
- Create: `docs/perception/mcp-script-bridge.md`
- Create: `docs/perception/mcp-transcripts/attach-and-read.md`
- Create: `docs/perception/mcp-transcripts/string-xref.md`
- Create: `docs/perception/mcp-transcripts/validate-script.md`

- [ ] Document knowledge MCP vs Perception runtime MCP handoff.
- [ ] Document handle lifecycle, stale handle recovery, permission denied recovery, target-not-found recovery.
- [ ] Document safe automation rules for write/alloc/kernel tools.
- [ ] Document script/get_context, script/validate, script/execute, and how they differ from pcx validate_code.
- [ ] Add transcript examples weak models can imitate.

### Task 3: Add MCP structured tool schema and planner data

**Files:**
- Create: `docs/perception/mcp-tool-schemas.json`
- Create: `docs/perception/mcp-tool-reference.md`
- Create: `mcp/perception-mcp-examples.json`

- [ ] Include every tool from `mcp/perception-mcp-config.json`.
- [ ] Classify no-handle tools, handle tools, permission-gated tools, script bridge tools, and expensive scan tools.
- [ ] Include example params for common tools: reference, module lookup, typed read, string xref, disassemble, script validate.

### Task 4: Add workflow planner tool

**Files:**
- Modify: `mcp/pcx-knowledge-mcp/server.py`
- Modify: `tools/pcx.py`
- Test: `tests/test_perception_mcp_contract.py`

- [ ] Add shared workflow plan data as small Python dictionaries.
- [ ] Add MCP tool `plan_perception_mcp_workflow(task, target_process="", permissions="")` returning JSON steps and warnings.
- [ ] Add CLI command `pcx mcp-plan "task" --target target.exe` if it fits existing CLI style with minimal code.
- [ ] Tests cover string xref, attach/read, script validate, and permission/write warnings.

### Task 5: Add MCP contract tests

**Files:**
- Create: `tests/fixtures/perception_mcp/tools_list.json`
- Create: `tests/fixtures/perception_mcp/errors.json`
- Modify: `tests/test_perception_mcp_contract.py`

- [ ] Test config tools are all represented in `docs/perception/mcp-tool-schemas.json`.
- [ ] Test schema tools are all represented in config.
- [ ] Test every tool has example params or explicit empty params.
- [ ] Test error codes `-32001`, `-32002`, `-32003`, `-32004` appear in recovery docs.

### Task 6: Regenerate docs and verify

**Files:**
- Regenerate: `docs/llms.txt`
- Regenerate: `docs/llms-full.txt`
- Regenerate: `docs/llms-perception-enma.md`
- Regenerate: `docs/llms-knowledge.md`
- Regenerate: `docs/COUNTS.json`

- [ ] Run `.venv-test/bin/python tools/build-llms-index.py`.
- [ ] Run `.venv-test/bin/python tools/build-counts.py`.
- [ ] Run `.venv-test/bin/python tools/pcx.py docs-check`.
- [ ] Run `.venv-test/bin/python -m pytest tests/test_perception_mcp_contract.py tests/test_project_workflow.py -q`.

---

## Self-review

- Scope is one sprint: docs + deterministic planner + sync tests only.
- Explicitly deferred: runtime session manager, evidence graph CLI, engine-specific workflow pack, MCP record/replay.
- All touched files are listed.
- Verification commands are exact.
