# Perception.cx Scripting Project

Languages: Enma (.em), AngelScript (.as)

## Documentation

Full API docs at `docs/` in this toolkit. **Read the relevant doc before writing any API call.**

- Start here for every task: `docs/perception/llm-routing.md` — choose Enma vs AngelScript before using any API name.
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

## Work Discipline (Karpathy)

*What the code looks like* is above; *how to work* is here. Full rules in `KARPATHY.md`.

1. **Think before coding** — name target, offset source, and tradeoff before the first line; mark guesses `UNVERIFIED`.
2. **Simplicity first** — ship the minimum feature; no speculative prediction, config, or framework.
3. **Surgical changes** — one feature, one diff; don't churn working offsets or reformat unrelated files.
4. **Goal-driven execution** — done = visible success criteria met on the live target, not "it compiles."
## Anti-Hallucination Rule

Do not invent PCX, Enma, or AngelScript API names. Every function,
method, type, and import must be traceable to one of these two upstream
sources:

1. `https://docs.perception.cx/perception/enma/overview` — Enma API surface
2. `https://docs.perception.cx/perception/angel-script/overview` — AngelScript API surface

Use the `.md` variant of any sub-page (e.g. `.../enma/proc-api.md`) for
structured markdown. Prefer reading the live upstream doc over the local
`docs/` mirror; the mirror is drift-checked, but the upstream is the authority.

The generated `knowledge/pcx-api-index.json` is an acceptable shortcut once
you have confirmed the symbol exists in the upstream docs. Before delivering
code, run `pcx verify <file>`. Fix every `unknown_call`, `unknown_type`,
`missing_import`, `wrong_language_symbol`, and `wrong_language_type` by reading
the relevant upstream doc — do not rename symbols to silence the checker.

See `knowledge/pcx-doc-roots.md` for the full sourcing policy.

## LSP Servers

- Enma: `lsp/enma-lsp/server/dist/server.js` (node)
- AngelScript: `lsp/angel-lsp-pcx/server/out/server.js` (node)
