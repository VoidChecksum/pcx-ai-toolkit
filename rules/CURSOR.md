# Cursor Rules — Perception.cx Scripting

Drop-in project rules for Cursor (the IDE), parallel to `CLAUDE.md` but tailored for Cursor's context system.

**How to use this.** Either copy this file's body into your project root as `.cursorrules`, or paste it into Cursor's `Rules for AI` setting (`Cursor Settings → Rules for AI`). `.cursorrules` is read as persistent system instructions on every request — keep it tight so it doesn't burn context on every prompt. This file is the project-level version of those instructions; the global setting is the per-user version.

## Project Context

- Languages: Enma (`.em`), AngelScript (`.as`), C++. Enma is the primary scripting language.
- Platform: Perception.cx. Scripts attach to a game process, read state, and draw an overlay.
- **Read the relevant doc before writing any API call.** Point Cursor at these with `@`:
  - Enma language: `@docs/enma/llms-language.md` (complete single-page reference)
  - PCX Enma APIs: `@docs/perception/` (proc, render, gui, input, cpu, zydis, unicorn, net, win, fs, sound, lifecycle, mcp)
  - PCX AngelScript APIs: `@docs/perception/angelscript/`
  - Quick references: `@knowledge/enma-cheatsheet.md`, `@knowledge/pcx-api-cheatsheet.md`
  - Common patterns: `@knowledge/common-patterns.md`

## Coding Standards

- Addresses are `uint64` — never `int64`. Sign-extension breaks high usermode addresses.
- `float32` literals need an `f` suffix: `0.2f`, not `0.2`. Vertex buffers and the GPU care.
- `color(r,g,b,a)` and `vec2(x,y)` are value types — construct fresh every frame, no globals.
- `import "vec"; import "color";` required before using those types.
- `main()` returns `> 0` to stay loaded, `<= 0` to unload immediately.
- Routines: `register_routine(cast<int64>(fn), 0)` — separate update and render routines.
- `signed ↔ unsigned` is a compile error — use `cast<uint64>(x)`.
- `float → int` is a compile error — use `cast<int32>(f)`.
- Failed reads return 0 — validate every pointer in a chain before dereferencing.
- Pattern scans over hardcoded offsets — sigs survive game patches.
- RAII: `proc_t` releases on scope exit. No GC. Destructors are deterministic.

## The 12 Guidelines (one-line form)

Long form with WRONG/RIGHT examples: `.claude/skills/game-cheat-guidelines/SKILL.md`.

1. Ground every offset — cite the source (sig, SDK header, IDA xref); mark guesses `UNVERIFIED`.
2. `uint64` for all addresses — no sign-extension bugs.
3. Validate every pointer — check for 0 after every `ru64` / `find_code_pattern` / `ref_process`.
4. Separate update from render — no memory reads in the draw path.
5. Sigs over hardcodes — survive game patches.
6. One feature, one file — no monolith scripts.
7. Construct colors/vecs every frame — they're 4-8 byte stack values.
8. `f` suffix on float32 literals — the GPU cares.
9. Minimize memory writes — reads are detection-invisible.
10. World-to-screen once, correctly — check `w > 0.001`, match the engine matrix layout.
11. GUI for all tunables — no magic constants in code.
12. Verify with live reads — trust the binary, not cached offsets.

## File Structure

One feature per file. Use the AI Composer to scaffold across these without merging features into one file:

```
project/
├── main.em         # Entry point, setup, routine registration
├── globals.em      # Shared state (proc handle, entity cache, config)
├── offsets.em      # Named sig constants + resolver functions
├── features/       # One file per feature (esp.em, aim.em, radar.em)
├── menu.em         # GUI sidebar widgets + config load/save
└── config.txt      # Persisted settings
```

## MCP Setup

The Perception MCP wiring (`.cursor/mcp.json`), docs-to-workspace, and LSP `settings.json` steps live in `mcp/cursor-setup.md`. Follow that file once per project — don't reproduce the steps here.

## Karpathy Workflow

How to work (not what the code looks like) is in `rules/KARPATHY.md`. The short version:

1. Think before coding — name the target, the offset source, and the tradeoff first.
2. Simplicity first — ship the box, not the framework.
3. Surgical changes — one feature, one diff; clean only your own orphans.
4. Goal-driven execution — done = visible criteria met on the live target, not "it compiles."

## What Cursor Does Best Here

- **Tab completion for `.em`/`.as`** — sharp once the Enma and AngelScript language servers are wired (see the LSP step in `mcp/cursor-setup.md`); without that, completions fall back to generic text.
- **`@` referencing docs by path** — pull the exact API page into context before generating a call, e.g. `@docs/perception/render.md` before writing `draw_*`, instead of letting the model guess signatures.
- **AI Composer for multi-file edits** — adding a feature means a new file under `features/` plus a routine registration in `main.em` and a GUI section in `menu.em`. Composer handles that spread while respecting one-feature-per-file; reject any diff that folds the new feature into an existing module.
- **`.cursorrules` persistence** — these standards apply to every generation automatically, so prompts can stay short ("add a distance-filtered box ESP") and still produce code that null-checks chains, suffixes float32, and binds tunables to GUI widgets.
