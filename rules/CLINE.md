Start here: `docs/perception/llm-routing.md`.

# Cline Rules — Perception.cx Scripting

Drop-in custom instructions for [Cline](https://github.com/cline/cline), the VS Code AI agent. Sibling to `rules/CLAUDE.md` (Claude Code drop-in) and `rules/CURSOR.md` (Cursor drop-in). Cline reads its custom instructions on every turn, so this file is intentionally tight — long rules eat the token budget without changing behavior.

## How to Use

Either:

1. Paste the contents below into Cline's `Custom Instructions` field
   (`Settings → Cline → Custom Instructions`), or
2. Save as `.clinerules` at the project root if your Cline version supports auto-loading.

Cline will apply these rules on every message in the project.

---

## Project Context

- **Languages.** Enma (`.em`) only.
- **Platform.** Perception.cx scripting runtime (`perception.cx`).
- **API docs.** Live under `docs/`:
  - `docs/enma/` — Enma language + standard library + SDK (50 files)
  - `docs/perception/` — Enma APIs (17 files)
- **Read before writing API calls.** Cline does not have these APIs in its pretraining; it must `@`-reference the relevant doc file before producing code.

## Coding Standards

- Addresses are `uint64`. Always. No `int64` for memory addresses.
- Float literals get the `f` suffix for `float32` (`1.5f`); bare `1.5` is `float64`.
- After `ref_process` check `.alive()`; after any `ru64` / `find_code_pattern` / `get_module_base` check for `0`.
- Update routines do reads + logic; render routines do drawing only. Never mix.
- Use sigs (`find_code_pattern`) over hardcoded offsets; resolve RIP-relative displacements correctly.
- One feature per file (`esp.em`, `aim.em`, `radar.em`); shared state in `globals.em`.
- Construct `color`, `vec2`, `vec3` per frame — they're stack structs, no cost.
- Mark unverified offsets with `// UNVERIFIED` and cite their evidence entry (`// E-NNN`).

## The 12 Guidelines (one-line form)

Long form: `.claude/skills/game-cheat-guidelines/SKILL.md`.

1. Ground every offset — cite sig + source.
2. `uint64` for all addresses.
3. Null-check every pointer chain link.
4. Update routine reads; render routine draws.
5. Sigs over hardcoded offsets.
6. One feature, one file.
7. Construct render primitives per frame.
8. `f` suffix on float32 literals.
9. Minimize memory writes.
10. World-to-screen once, correctly (check `w > 0.001`).
11. GUI for every tunable, no magic constants.
12. Verify against the live binary.

## File Structure

Recommended layout (`templates/full-project/` is the scaffold):

```
project/
├── globals.em       # proc_t, base address, entity cache, config state
├── offsets.em       # all sigs + resolved addresses (E-NNN cross-refs)
├── esp.em           # one feature per file
├── aim.em
├── menu.em          # GUI sidebar — every tunable bound here
├── main.em          # entry: attach, resolve, register routines
└── evidence/        # per-binary evidence log (skill://re-evidence-log)
```

Bundle order respects the layered import graph: `globals → offsets → feature(s) → menu → main`. See `.claude/skills/script-bundler/SKILL.md`.

## MCP Setup

Wire the Perception MCP server into Cline via `cline_mcp_settings.json` (Cline's MCP config file path is in `Settings → MCP Servers → Configure MCP Servers`):

```json
{
  "mcpServers": {
    "perception": {
      "transport": "http",
      "url": "http://127.0.0.1:42069",
      "description": "Perception.cx MCP — live process / memory / disasm tools"
    }
  }
}
```

Authoritative tool list: `mcp/perception-mcp-config.json`. Routing guide for which of the 37 tools to use when: `.claude/skills/mcp-tool-routing/SKILL.md`. The Perception IDE must be running with MCP enabled (`Settings → MCP → Enabled`).

## Karpathy Workflow

Long form: `rules/KARPATHY.md`. Short form:

1. **Think before coding.** Surface assumptions; ask if uncertain.
2. **Simplicity first.** Minimum code that solves the problem.
3. **Surgical changes.** Touch only what you must.
4. **Goal-driven execution.** Define "done" before starting.

## Cline-Specific Notes

- **Auto-approval.** Read-only MCP tools (`process/read_virtual_memory`, `process/read_typed_value`, `process/read_string`, `process/read_pointer_chain`, `process/list`, `process/info_by_*`, `process/list_module_exports`, `process/get_module_imports`, `process/disassemble`, `process/find_pattern`, `process/find_xrefs`, `process/scan_*`) are safe to auto-approve. Keep write / execute tools gated (`process/write_virtual_memory`, `process/write_typed_value`, `process/write_string`, `process/copy_memory`, `process/fill_memory`, `process/allocate_memory`, `process/free_memory`, `script/execute`).
- **Plan / Act split.** For multi-step RE work, start in **Plan** mode; produce the workflow as a sequence of MCP calls; approve; switch to **Act**. The 12 Guidelines shape the plan most usefully *in Plan mode* — they catch the wrong instinct before any tool runs.
- **Token budget.** Documentation is ~35k lines across `docs/`. Do not preload it all into context. Instead, `@`-reference *specific* doc files when needed: `@docs/perception/render-api.md`, `@docs/enma/addon-math.md`. For per-task lookups, prefer `@knowledge/pcx-api-cheatsheet.md` (15 KB, all APIs at a glance) over the full corpus.
- **Workflow checkpoints.** Cline supports checkpoint/restore. Use checkpoints before any operation touching `process/write_virtual_memory` (or any `process/write_*` / `process/allocate_memory`), `script/execute`, or external state; the rollback path is the safety net.
- **Diff review.** Cline shows file diffs before applying. Read them — never blanket-approve a multi-file change; the 12 Guidelines (especially #2 `uint64`, #4 update/render split, #8 `f` suffix) are the highest-value pattern matches to scan for.

## Cross-References

- `rules/CLAUDE.md` — Claude Code drop-in
- `rules/CURSOR.md` — Cursor drop-in
- `rules/AGENTS.md` — agent role definitions for multi-agent workflows
- `rules/KARPATHY.md` — workflow discipline (4 principles)
- `mcp/cline-setup.md` — does not exist; this file is the Cline setup guide
- `mcp/cursor-setup.md`, `mcp/claude-code-setup.md`, `mcp/aider-setup.md` — sibling IDE setups
