# Windsurf Rules — Perception.cx Scripting

Drop-in project rules for Windsurf (the IDE) and Cascade. Parallel to `rules/CLAUDE.md` and `rules/CURSOR.md` but tailored for Windsurf's context system and Cascade agent.

**How to use this.** Save as `.windsurfrules` at your project root. Windsurf/Cascade reads `.windsurfrules` automatically as persistent instructions on every prompt. Keep it concise to save Cascade's context token budget.

---

## Project Context

- **Languages:** Enma (`.em`) and AngelScript (`.as`). Enma is the primary scripting language.
- **Platform:** Perception.cx. Scripts attach to a game process, read state, and draw an overlay.
- **Read the relevant doc before writing any API call.** Point Windsurf/Cascade to these files:
  - Routing first: `docs/perception/llm-routing.md` (choose Enma vs AngelScript before using API names)
  - Enma language: `docs/enma/llms-language.md` (complete single-page reference)
  - PCX Enma APIs: `docs/perception/` (proc, render, gui, input, cpu, zydis, unicorn, net, win, fs, sound, lifecycle, mcp)
  - PCX AngelScript APIs: `docs/perception/angelscript/`
  - Quick references: `knowledge/enma-cheatsheet.md`, `knowledge/pcx-api-cheatsheet.md`
  - Common patterns: `knowledge/common-patterns.md`

---

## Coding Standards

- **Addresses are `uint64`** — never `int64`. Sign-extension breaks high usermode addresses.
- **`float32` literals need an `f` suffix**: `0.2f`, not `0.2`. Vertex buffers and the GPU care.
- **`color(r,g,b,a)` and `vec2(x,y)` are value types** — construct fresh every frame, no globals.
- **`import "vec"; import "color";`** required before using those types.
- **`main()` returns `> 0` to stay loaded**, `<= 0` to unload immediately.
- **Routines:** `register_routine(cast<int64>(fn), 0)` — separate update and render routines.
- **`signed ↔ unsigned` is a compile error** — use `cast<uint64>(x)`.
- **`float → int` is a compile error** — use `cast<int32>(f)`.
- **Failed reads return 0** — validate every pointer in a chain before dereferencing.
- **Pattern scans over hardcoded offsets** — sigs survive game patches.
- **RAII:** `proc_t` releases on scope exit. No GC. Destructors are deterministic.

---

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

---

## File Structure

One feature per file. Use Cascade to scaffold across these without merging features into one file:

```
project/
├── main.em         # Entry point, setup, routine registration
├── globals.em      # Shared state (proc handle, entity cache, config)
├── offsets.em      # Named sig constants + resolver functions
├── features/       # One file per feature (esp.em, aim.em, radar.em)
├── menu.em         # GUI sidebar widgets + config load/save
└── config.txt      # Persisted settings
```

---

## Windsurf / Cascade Specifics

- **Using Cascade's Agent Mode:** Cascade can run commands and edit files. Safe to auto-approve read-only MCP commands. Gating is recommended for write/execute operations.
- **Context Pinning:** In Windsurf, you can pin specific reference files (like `knowledge/pcx-api-cheatsheet.md`) to the Cascade context so it keeps them active in chat history.
- **LSP Setup:** Refer to the LSP section in the setup docs for editor compilation diagnostics.
