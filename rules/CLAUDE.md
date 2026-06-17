# Perception.cx Scripting Project

Languages: Enma (.em), AngelScript (.as), C++

## Documentation

Full API docs at `docs/` in this toolkit. **Read the relevant doc before writing any API call.**

- Enma language: `docs/enma/llms-language.md` (complete single-page reference)
- PCX Enma APIs: `docs/perception/*.md` (proc, render, gui, input, cpu, zydis, unicorn, net, win, fs, sound, lifecycle, mcp)
- PCX AngelScript APIs: `docs/perception/angelscript/*.md`
- Quick references: `knowledge/enma-cheatsheet.md`, `knowledge/pcx-api-cheatsheet.md`
- Common patterns: `knowledge/common-patterns.md`

## Coding Standards

- **Addresses are `uint64`** — never `int64`. Sign-extension breaks high usermode addresses.
- **`float32` literals need `f` suffix**: `0.2f` not `0.2`. GPU and vertex buffers care.
- **`color(r,g,b,a)` and `vec2(x,y)` are value types** — construct fresh every frame, no globals needed.
- **`import "vec"; import "color";`** required before using those types.
- **`main()` returns `> 0` to stay loaded**, `<= 0` to unload immediately.
- **Routines**: `register_routine(cast<int64>(fn), data)` — separate update and render routines.
- **`signed ↔ unsigned` is a compile error** — use `cast<uint64>(x)`.
- **`float → int` is a compile error** — use `cast<int32>(f)`.
- **Failed reads return 0** — validate every pointer in a chain before dereferencing.
- **Pattern scans over hardcoded offsets** — sigs survive game patches.
- **RAII**: `proc_t` releases on scope exit. No GC. Destructors are deterministic.

## Project Structure

```
project/
├── main.em         # Entry point, setup, routine registration
├── globals.em      # Shared state (proc handle, entity cache, config)
├── offsets.em      # Named sig constants + resolver functions
├── features/       # One file per feature
├── menu.em         # GUI sidebar widgets + config load/save
└── config.txt      # Persisted settings
```

## The 12 Guidelines (condensed)

1. **Ground every offset** — cite the source (sig, SDK header, IDA xref)
2. **`uint64` for all addresses** — no sign-extension bugs
3. **Validate every pointer** — check for 0 before dereferencing
4. **Separate update from render** — no memory reads in the draw path
5. **Sigs over hardcodes** — survive game patches
6. **One feature, one file** — no monolith scripts
7. **Construct colors/vecs every frame** — they're 4-8 byte stack values
8. **`f` suffix on float32 literals** — the GPU cares
9. **Minimize memory writes** — reads are detection-invisible
10. **World-to-screen once, correctly** — check `w > 0`, match engine matrix layout
11. **GUI for all tunables** — no magic constants in code
12. **Verify with live reads** — trust the binary, not cached offsets

## LSP Servers

- Enma: `lsp/enma-lsp/server/dist/server.js` (node)
- AngelScript: `lsp/angel-lsp-pcx/server/out/server.js` (node)
