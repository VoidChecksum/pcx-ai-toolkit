# pcx-ai-toolkit

**The complete AI-assisted scripting toolkit for [Perception.cx](https://perception.cx).**

Turn any LLM — Claude, GPT, Gemini, Copilot, or a local model — into an expert Perception.cx script developer. This toolkit gives the AI full knowledge of the Enma language, AngelScript, Lua, and every Perception.cx platform API, so it writes correct code on the first try instead of hallucinating APIs that don't exist.

---

## Why This Exists

LLMs don't know Enma. They don't know the Perception.cx API. When you ask them to write a PCX script, they guess — and they guess wrong.

This toolkit fixes that by giving the AI:
- **33,580 lines of real documentation** — every type, function, and parameter
- **Coding rules** that prevent the 12 most common mistakes in PCX scripting
- **Working code patterns** it can reference instead of inventing syntax
- **MCP server configs** so the AI can connect directly to Perception's live tooling

The result: the AI reads the actual docs before writing code, follows the platform's real API signatures, and produces scripts that compile and run.

---

## What's Inside

```
pcx-ai-toolkit/
│
├── docs/                            33,580 lines of documentation
│   ├── enma/                        Enma language, standard library, SDK
│   │   ├── llms-language.md         Complete language reference (single file, 2,861 lines)
│   │   ├── llms-sdk.md              Complete SDK embedding reference (832 lines)
│   │   ├── lang-*.md                Language guide (10 files: basics → semantics)
│   │   ├── addon-*.md               All 18 standard library addons
│   │   └── sdk-*.md                 SDK guide (17 files: quick-start → API reference)
│   └── perception/                  Perception.cx platform APIs
│       ├── *.md                     Enma APIs: proc, render, gui, input, cpu, zydis,
│       │                            unicorn, net, win, filesystem, sound, lifecycle, mcp
│       ├── angelscript/             AngelScript APIs (23 files, 10,820 lines)
│       └── lua/                     Lua APIs (17 files, 5,779 lines)
│
├── .claude/skills/                  AI skills for Claude Code / oh-my-claudecode
│   ├── game-hacking-pcx/            API doc index — tells the AI which file to read
│   └── game-cheat-guidelines/       12 behavioral rules (Karpathy-style)
│
├── knowledge/                       Quick references and working examples
│   ├── enma-cheatsheet.md           Language quick reference card
│   ├── pcx-api-cheatsheet.md        Every PCX API at a glance
│   ├── common-patterns.md           Working code for overlays, menus, angle math, radar
│   └── offset-methodology.md        Pattern scanning, RIP resolution, pointer chains
│
├── rules/                           Drop-in project rules
│   ├── CLAUDE.md                    For Claude Code projects
│   └── AGENTS.md                    Agent role definitions
│
├── mcp/                             MCP server configurations
│   ├── perception-mcp-config.json   Perception.cx MCP (42 tools)
│   ├── claude-code-setup.md         Integration guide for Claude Code
│   └── cursor-setup.md             Integration guide for Cursor
│
├── lsp/                             Language servers (git submodules)
│   ├── enma-lsp/                    Enma: syntax, completion, hover, diagnostics
│   └── angel-lsp-pcx/              AngelScript+PCX: completion, hover, diagnostics
│
├── signatures/                      Byte signature methodology and examples
│   └── source-engine/
│       └── common-sigs.md
│
├── setup.sh                         One-command install
├── LICENSE                          MIT
└── README.md
```

---

## Quick Start

### 1. Clone

```bash
git clone --recursive https://github.com/VoidChecksum/pcx-ai-toolkit.git
cd pcx-ai-toolkit
```

### 2. Install

```bash
./setup.sh
```

This clones and builds the LSP servers, and installs AI skills to `~/.claude/skills/` if Claude Code is detected.

### 3. Use

Copy `rules/CLAUDE.md` into your scripting project directory. The AI now reads docs before writing code.

```bash
cp rules/CLAUDE.md /path/to/your/pcx-project/
```

---

## Documentation Coverage

Every API function, every type, every parameter — documented and offline.

### Enma Language (48 files, 13,166 lines)

| Category | Files | Lines | Coverage |
|----------|-------|-------|----------|
| Complete Language Reference | 1 | 2,861 | Every type, operator, control flow, struct, class, template, coroutine, exception, heap, FFI, annotation, module — single file |
| Complete SDK Reference | 1 | 832 | Full C++ embedding API — single file |
| Language Guide | 10 | 3,150 | Basics, functions, pointers, structs/classes, templates, advanced, annotations, modules, preprocessor, semantics |
| Standard Library Addons | 18 | 2,528 | core, strings, arrays, maps, math, SIMD, vectors, 3D math, variant, atomic, bits, time, regex, file, thread, hash_set, sorted_map, list, JSON |
| SDK Guide | 17 | 3,795 | Engine lifecycle, compilation, execution, type registration, native functions, hot reload, serialization, introspection, RAII, debug, safety, custom addons, API reference |

### Perception.cx Platform APIs

| Language | Files | Lines | APIs Covered |
|----------|-------|-------|-------------|
| **Enma** | 16 | 3,815 | Proc, Render, GUI, Input, CPU, Zydis, Unicorn, Net, Win, Filesystem, Sound, Lifecycle, MCP, IDE, Extensions, Analyzer |
| **AngelScript** | 23 | 10,820 | All of the above + Intrinsics, Zydis Encoder, Bit Reinterpret, Mutex, Atomic Types, CS2 Extended |
| **Lua** | 17 | 5,779 | All core APIs in Lua syntax |
| **Total** | **104** | **33,580** | |

---

## AI Skills

### `game-hacking-pcx` — Documentation Index

Tells the AI exactly which file to read before writing any code. Contains:
- File-by-file index of all 104 docs with paths and line counts
- Critical Enma rules (type system, conversions, RAII, address types)
- API-specific notes (Proc, Render, GUI, Input, etc.)
- LSP server locations

**Triggers on:** Enma scripting, AngelScript scripting, Perception.cx, PCX, `.em` files, `.as` files, overlay rendering, process memory operations

### `game-cheat-guidelines` — 12 Behavioral Rules

Karpathy-style coding guidelines written specifically for PCX scripting. Every rule includes a wrong/right code example grounded in real Perception.cx APIs.

| # | Rule | What It Prevents |
|---|------|-----------------|
| 1 | **Ground every offset** | Wasting hours on stale offsets from an old SDK |
| 2 | **`uint64` for all addresses** | Sign-extension on high usermode addresses |
| 3 | **Validate every pointer** | Silent null reads returning garbage |
| 4 | **Separate update from render** | Overlay stutter from blocking reads |
| 5 | **Sigs over hardcodes** | Script breaking on every game patch |
| 6 | **One feature, one file** | Monolith scripts that can't be hot-reloaded |
| 7 | **Construct colors/vecs every frame** | Pointless globals for 4-byte stack structs |
| 8 | **`f` suffix on float32** | Truncation bugs in vertex buffers |
| 9 | **Minimize memory writes** | Unnecessary detection surface |
| 10 | **W2S once, correctly** | Behind-camera mirroring, wrong matrix layout |
| 11 | **GUI for all tunables** | Recompiling to change a threshold |
| 12 | **Verify with the binary** | Trusting stale offsets over live reality |

---

## Knowledge Base

### `enma-cheatsheet.md` — Language Quick Reference (164 lines)

Every primitive type, conversion rule, control flow construct, function signature pattern, struct/class syntax, template syntax, and annotation — condensed into a single scannable reference card.

### `pcx-api-cheatsheet.md` — Platform API Quick Reference (232 lines)

Every PCX API function with its signature and return type. One section per API: Proc, Render, GUI, Input, CPU, Zydis, Unicorn, Net, Win, Filesystem, Sound, Lifecycle.

### `common-patterns.md` — Working Code Examples (339 lines)

Complete, copy-paste-ready code for:
- Process attachment and module resolution
- Pattern scanning with RIP-relative address resolution
- Entity list iteration with null guards
- World-to-screen projection (Source Engine 4x4 matrix)
- 2D box overlay with health bars
- Snapline drawing
- Distance calculation and display
- Angle calculation (atan2-based)
- Smooth angle interpolation
- GUI menu with all widget types
- Config file save/load
- Minimap / radar with rotation
- Complete script skeleton (main + update + render)

### `offset-methodology.md` — Finding and Maintaining Offsets (130 lines)

- When to pattern scan vs hardcode
- Signature construction methodology (what to wildcard, how to verify uniqueness)
- RIP-relative address resolution (table of common instruction shapes)
- Pointer chain walking strategy
- Using `struct_dump` for field discovery
- Cross-referencing with IDA/Ghidra
- Offset table maintenance format
- What breaks on game updates (stability table)

---

## MCP Integration

### Perception.cx MCP Server

The Perception IDE exposes 42+ tools via JSON-RPC that any MCP-compatible AI can call:

**Process Memory:** `read_memory`, `read_typed_value`, `find_pattern`, `read_pointer_chain`, `read_string`, `memory_write`

**Analysis:** `disassemble`, `struct_dump`, `find_xrefs`, `find_string_refs`, `find_function_bounds`, `analyze_function`, `trace_register`, `analyze_vtable`, `read_rtti`, `generate_signature`, `build_call_graph`

**Scanning:** `scan_string`, `scan_wstring`, `scan_pointer_to`, `scan_value`, `scan_changed`, `diff_memory`

**Process Info:** `list_processes`, `get_process_info`, `get_module_exports`, `get_module_imports`

**Files & Scripts:** `read_file`, `write_file`, `edit_file`, `search_text`, `find_references`, `check_script`, `validate_script`, `execute_script`, `get_script_api`

Config: [`mcp/perception-mcp-config.json`](mcp/perception-mcp-config.json)

### Supported AI Tools

| Tool | Integration Method | Setup Guide |
|------|-------------------|-------------|
| **Claude Code** | Skills + CLAUDE.md + MCP | [`mcp/claude-code-setup.md`](mcp/claude-code-setup.md) |
| **Cursor** | .cursorrules + MCP + docs | [`mcp/cursor-setup.md`](mcp/cursor-setup.md) |
| **Cline** | MCP + system prompt | Use MCP config, paste CLAUDE.md as system prompt |
| **Perception IDE** | Native AI chat | Built-in — add `docs/` as workspace folder for extra context |
| **Any OpenAI-compatible** | System prompt + docs | Paste `rules/CLAUDE.md` + relevant docs into system prompt |

---

## LSP Language Servers

Both servers provide syntax highlighting, autocompletion, hover documentation, and diagnostics.

| Server | Language | Source |
|--------|----------|--------|
| [enma-lsp](https://github.com/sinnafuls/enma-lsp) | Enma (.em) | Includes predefined Enma stdlib + Perception API surface |
| [angel-lsp-pcx](https://github.com/sinnafuls/angel-lsp-pcx) | AngelScript (.as) | Includes predefined Perception API surface |

Built automatically by `setup.sh`. To use in your editor:

```
Enma:        node lsp/enma-lsp/server/dist/server.js --stdio
AngelScript: node lsp/angel-lsp-pcx/server/out/server.js --stdio
```

---

## Project Rules

### `rules/CLAUDE.md`

Drop this into any PCX scripting project. It tells the AI:
- What languages and APIs are in play
- Where to find documentation
- Coding standards (address types, float literals, conversions, RAII)
- The 12 guidelines in condensed form
- Recommended project structure

### `rules/AGENTS.md`

Defines five specialist agent roles for multi-agent workflows:
- **reverse-engineer** — binary analysis, sig generation, offset discovery
- **script-writer** — Enma/AngelScript implementation following all rules
- **offset-maintainer** — post-patch offset table updates
- **feature-builder** — feature implementation using common patterns
- **reviewer** — correctness, style, and detection surface review with checklist

---

## Contributing

1. Fork and clone with `--recursive` (pulls LSP submodules)
2. Add or improve: docs, patterns, templates, sigs, knowledge files
3. Test with `./setup.sh` on a clean clone
4. Open a PR

Documentation improvements and new working patterns are especially welcome. If you've mapped a new API, reversed a struct, or found a better pattern — add it.

---

## License

[MIT](LICENSE)

---

## Credits

- [Perception.cx](https://perception.cx) — platform and Enma language
- [Enma Documentation](https://enma-1.gitbook.io/enma) — official language specification
- [sinnafuls/enma-lsp](https://github.com/sinnafuls/enma-lsp) — Enma language server
- [sinnafuls/angel-lsp-pcx](https://github.com/sinnafuls/angel-lsp-pcx) — AngelScript+PCX language server
