# GitHub Copilot Rules — Perception.cx Scripting

Drop-in custom instructions for GitHub Copilot. Sibling to `rules/CLAUDE.md` (Claude Code), `rules/CURSOR.md` (Cursor), `rules/CLINE.md` (Cline). Copilot reads `.github/copilot-instructions.md` for repo-wide rules and a per-workspace custom-instructions field for IDE-side rules — both apply on every completion request, so this file is intentionally tight.

## How to Use

Either:

1. Save as `.github/copilot-instructions.md` at the repo root — Copilot picks it up automatically for any developer working in the repo, no per-workspace config needed.
2. Paste into your IDE's Copilot custom-instructions field (VS Code: `Settings → GitHub Copilot → Chat: Custom Instructions`) — per-workspace, applies only to your editor.

Most projects want option 1; option 2 is for adding personal preferences on top of the shared repo rules.

---

## Project Context

- **Languages.** Enma (`.em`) and AngelScript (`.as`).
- **Platform.** Perception.cx scripting runtime.
- **API docs.** Live under `docs/`:
  - `docs/perception/llm-routing.md` — load first; choose Enma vs AngelScript before using API names
  - `docs/enma/` — Enma language + standard library + SDK
  - `docs/perception/` — Enma APIs
  - `docs/perception/angelscript/` — AngelScript APIs
- **Read before writing API calls.** Copilot does not have these APIs in pretraining; it will hallucinate confident-looking names. Always grep / link the relevant doc file when an API is needed.

## Coding Standards

- Addresses are `uint64`. No `int64`, no `int` for memory addresses.
- Float literals get the `f` suffix for `float32` (`1.5f`); bare `1.5` is `float64`.
- After `ref_process` check `.alive()`; after any `ru64` / `find_code_pattern` / `get_module_base` check for `0`.
- Update routines do reads + logic; render routines do drawing only. Never mix.
- Sigs (`find_code_pattern`) over hardcoded offsets; resolve RIP-relative displacements correctly.
- One feature per file (`esp.em`, `aim.em`, `radar.em`); shared state in `globals.em`.
- Construct `color`, `vec2`, `vec3` per frame.
- Mark unverified offsets with `// UNVERIFIED` and cite `// E-NNN` evidence entry.

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

Recommended layout (`templates/full-project/`):

```
project/
├── globals.em       # process handle, base address, entity cache, config state
├── offsets.em       # all sigs + resolved addresses (with E-NNN cross-refs)
├── esp.em           # one feature per file
├── aim.em
├── menu.em          # GUI sidebar — every tunable bound here
├── main.em          # entry: attach, resolve, register routines
└── evidence/        # per-binary evidence log
```

## What Copilot Is Good At Here

- Inline completions: routine boilerplate, GUI sections with N widgets, common loop shapes.
- Doc-comment generation: turn a one-line description into a documented function header.
- Pattern-following: once you've written one feature module the right way, Copilot mimics its shape well in the next module.
- Test scaffolding for validation tooling around scripts.
- Rote refactors confined to a single file (renames within scope, extracting a helper).

## What Copilot Is Bad At Here

- **Multi-file refactors.** Use Cursor / Cline / Aider for cross-file changes; Copilot's window is too narrow.
- **API names from less-common APIs.** It will hallucinate `proc.read_mat3x4_fl32` because the more common APIs follow that shape. Verify every API name against `docs/`.
- **Enforcing the 12 guidelines unprompted.** It does not scan its own completions for `int64`-on-an-address or missing `f` suffixes. You must.
- **Choosing between Enma / AngelScript.** See `docs/perception/llm-routing.md` for the decision; Copilot will produce whichever language the file extension suggests, which is sometimes the wrong choice.
- **MCP-aware work.** Copilot does not speak MCP. Binary-level RE (find_pattern, disassemble, struct_dump) happens in another tool; Copilot handles only the script-side editing.

## Workflow Notes

- **Inline vs Chat.** Use Copilot Chat (sidebar) for explanation and review; use inline completions for typing-out. Different surfaces, different strengths.
- **Steer with comments.** When Copilot hallucinates an API, write `// from: docs/perception/render-api.md` as a comment above the cursor — Copilot reads it as context for the next completion.
- **Pair with an MCP-aware tool.** Use the Perception IDE (or Cursor with MCP) for binary discovery; bring the resolved sig back into your editor; let Copilot complete the script around it.
- **Diff-review every multi-line completion.** Pattern to scan for:
  - `int64` or `int32` near `addr` / `offset` / `base` / `ptr` (rule #2 violation)
  - Bare float literals in `draw_*` calls (rule #8)
  - `proc.ru64(...)` without a subsequent `if ... == 0` check (rule #3)
  - `color(...)` / `vec2(...)` / `vec3(...)` constructed outside a render routine (rule #7)
- **Don't accept long completions.** A 60-line block is too much to review in flight; accept 5-15 lines at a time and check each one.

## Karpathy Workflow

Long form: `rules/KARPATHY.md`. Short form:

1. **Think before coding.** Surface assumptions; ask if uncertain.
2. **Simplicity first.** Minimum code that solves the problem.
3. **Surgical changes.** Touch only what you must.
4. **Goal-driven execution.** Define "done" before starting.

Copilot completions tend to over-suggest (more code than asked for). The Karpathy second principle is the right counterweight — when a completion grows beyond the request, trim it before accepting.

## Cross-References

- `rules/CLAUDE.md` — Claude Code drop-in
- `rules/CURSOR.md` — Cursor drop-in
- `rules/CLINE.md` — Cline drop-in
- `rules/KARPATHY.md` — workflow discipline
- `rules/AGENTS.md` — agent role definitions for multi-agent workflows
- `.claude/skills/ai-pair-programming/SKILL.md` — the cross-tool workflow that wraps all four IDE drop-ins
