<div align="center">

# pcx-ai-toolkit

### The Complete AI-Powered Scripting Toolkit for Perception.cx

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/Docs-107%20pages-brightgreen.svg)](#documentation-coverage)
[![Lines](https://img.shields.io/badge/Doc%20Lines-34%2C000%2B-brightgreen.svg)](#documentation-coverage)
[![Languages](https://img.shields.io/badge/Languages-Enma%20%7C%20AngelScript%20%7C%20Lua%20%7C%20C%2B%2B-orange.svg)](#)
[![MCP Tools](https://img.shields.io/badge/MCP%20Tools-42%2B-purple.svg)](#perception-mcp-server)
[![Skills](https://img.shields.io/badge/AI%20Skills-2-yellow.svg)](#ai-skills)

**Turn any LLM into an expert Perception.cx developer.**<br>
Complete Enma language docs, every PCX API, coding guidelines, MCP configs, and LSP servers — in one package.

[Quick Start](#quick-start) · [Documentation](#documentation-coverage) · [AI Skills](#ai-skills) · [MCP Integration](#mcp-integration) · [Contributing](#contributing)

</div>

---

## The Problem

LLMs don't know Enma. They don't know the Perception.cx API. Ask them to write a PCX script and they hallucinate function names, invent parameters, and produce code that doesn't compile.

## The Solution

Give the AI **34,000+ lines of real documentation** and **12 coding rules** that prevent the most common mistakes. The AI reads the actual docs before writing code, follows real API signatures, and produces scripts that work.

```
Before:  "Write me an ESP overlay"
AI:      *invents draw_esp(), uses int for addresses, forgets null checks*
Result:  Doesn't compile. Wrong types. Silent crashes.

After:   "Write me an ESP overlay"  (with pcx-ai-toolkit loaded)
AI:      *reads render-api.md, uses draw_rect + draw_text, uint64 addresses, validates pointers*
Result:  Compiles. Runs. Correct API calls.
```

---

## Quick Start

```bash
# 1. Clone
git clone --recursive https://github.com/VoidChecksum/pcx-ai-toolkit.git
cd pcx-ai-toolkit

# 2. Install (builds LSPs, installs Claude Code skills)
./setup.sh

# 3. Add to your project
cp rules/CLAUDE.md /path/to/your/pcx-project/
```

That's it. The AI now reads docs before writing code.

---

## What's Inside

<table>
<tr>
<td width="50%" valign="top">

### Documentation
107 pages, 34,000+ lines

- Complete Enma language spec
- All 18 standard library addons
- Full C++ SDK embedding guide
- Every PCX API (Enma, AngelScript, Lua)
- IDE, Extensions, Analyzer docs

</td>
<td width="50%" valign="top">

### AI Skills
2 Claude Code / OMC skills

- **game-hacking-pcx** — doc index, API rules
- **game-cheat-guidelines** — 12 behavioral rules

Auto-trigger on `.em`/`.as` work and PCX topics

</td>
</tr>
<tr>
<td width="50%" valign="top">

### Knowledge Base
4 reference files, 865 lines

- Enma language cheatsheet
- PCX API cheatsheet
- Working code patterns (13 recipes)
- Offset-finding methodology

</td>
<td width="50%" valign="top">

### Tooling
MCP + LSP + Rules

- Perception MCP config (42+ tools)
- Enma LSP (syntax, completion, hover)
- AngelScript+PCX LSP
- Drop-in CLAUDE.md / AGENTS.md

</td>
</tr>
</table>

---

## Directory Structure

```
pcx-ai-toolkit/
│
├── docs/                             107 pages of documentation
│   ├── enma/                         ── Enma language, addons, SDK (50 files)
│   │   ├── llms-language.md              Complete language reference (2,861 lines)
│   │   ├── llms-sdk.md                   Complete SDK reference (832 lines)
│   │   ├── lang-*.md                     Language guide (10 files)
│   │   ├── addon-*.md                    18 standard library addons
│   │   └── sdk-*.md                      SDK embedding guide (17 files)
│   │
│   └── perception/                   ── Perception.cx platform APIs
│       ├── *.md                          Enma APIs (17 files)
│       ├── angelscript/                  AngelScript APIs (23 files)
│       └── lua/                          Lua APIs (17 files)
│
├── .claude/skills/                   ── AI Skills
│   ├── game-hacking-pcx/                Doc index + coding rules
│   └── game-cheat-guidelines/           12 behavioral guidelines
│
├── knowledge/                        ── Quick References
│   ├── enma-cheatsheet.md                Language quick-ref card
│   ├── pcx-api-cheatsheet.md             All APIs at a glance
│   ├── common-patterns.md                13 working code recipes
│   └── offset-methodology.md             Sig scanning methodology
│
├── rules/                            ── Project Rules
│   ├── CLAUDE.md                         Drop-in for Claude Code
│   └── AGENTS.md                         5 agent role definitions
│
├── mcp/                              ── MCP Configs
│   ├── perception-mcp-config.json        42+ tool definitions
│   ├── claude-code-setup.md              Claude Code guide
│   └── cursor-setup.md                   Cursor guide
│
├── lsp/                              ── Language Servers (submodules)
│   ├── enma-lsp/                         Enma: completion + diagnostics
│   └── angel-lsp-pcx/                   AngelScript: completion + diagnostics
│
├── signatures/source-engine/         ── Signature Examples
│
├── setup.sh                          One-command install
├── CONTRIBUTING.md                   Contribution guide
└── LICENSE                           MIT
```

---

## Documentation Coverage

> **107 out of 107 gitbook pages — 100% coverage of both the Enma and Perception.cx documentation.**

<table>
<tr>
<th>Corpus</th>
<th>Files</th>
<th>Lines</th>
<th>Coverage</th>
</tr>
<tr>
<td><strong>Enma Language</strong></td>
<td align="center">50</td>
<td align="center">13,518</td>
<td>Every type, operator, control flow, function, pointer, struct, class, template, coroutine, exception, FFI, annotation, module, preprocessor + all 18 addons + full SDK</td>
</tr>
<tr>
<td><strong>PCX Enma APIs</strong></td>
<td align="center">17</td>
<td align="center">3,915</td>
<td>Proc, Render, GUI, Input, CPU, Zydis, Unicorn, Net, Win, Filesystem, Sound, Lifecycle, MCP, IDE, Extensions, Analyzer</td>
</tr>
<tr>
<td><strong>PCX AngelScript APIs</strong></td>
<td align="center">23</td>
<td align="center">10,820</td>
<td>All of the above + Intrinsics, Zydis Encoder, Bit Reinterpret, Mutex, Atomic Types, CS2 Extended</td>
</tr>
<tr>
<td><strong>PCX Lua APIs</strong></td>
<td align="center">17</td>
<td align="center">5,779</td>
<td>All core APIs in Lua syntax</td>
</tr>
<tr>
<td><strong>Total</strong></td>
<td align="center"><strong>107</strong></td>
<td align="center"><strong>34,032</strong></td>
<td></td>
</tr>
</table>

### Enma Language Docs Breakdown

<details>
<summary><strong>Language Guide</strong> — 10 files, 3,150 lines (click to expand)</summary>

| File | Lines | Topics |
|------|------:|--------|
| `lang-basics.md` | 267 | Types, variables, constants, operators, control flow |
| `lang-functions.md` | 247 | Parameters, defaults, refs, out, variadic, lambdas, closures |
| `lang-pointers.md` | 357 | Heap pointers, address-of, member access, null, return-by-ref |
| `lang-structs-and-classes.md` | 912 | Value/ref types, inheritance, vtable, interfaces, mixins, operators |
| `lang-templates.md` | 173 | Generic structs and functions, monomorphization |
| `lang-advanced.md` | 562 | Delegates, namespaces, coroutines, exceptions, smart ptrs, FFI |
| `lang-annotations.md` | 209 | packed, align, reflect, serialize, export, dll, custom |
| `lang-modules.md` | 100 | Import system, aliased imports, .emb, multi-module linking |
| `lang-pre-processor.md` | 77 | #define, #ifdef, #include, #pragma |
| `lang-semantics-and-limits.md` | 181 | Guarantees, compile-time rejects, what doesn't exist |

</details>

<details>
<summary><strong>Standard Library Addons</strong> — 18 files, 2,528 lines (click to expand)</summary>

| Addon | Lines | Key Types / Functions |
|-------|------:|----------------------|
| Core | 42 | `print`, `println` |
| Strings | 165 | `format`, `to_int`, `split`, `replace`, `substr`, interpolation |
| Arrays | 119 | `T[]`, `push`, `pop`, `sort`, `contains`, `slice` |
| Maps | 200 | `map<K,V>`, `imap<V>`, `get`, `set`, iteration |
| Math | 137 | `sin`, `cos`, `atan2`, `sqrt`, `clamp`, `lerp`, `random` |
| SIMD | 128 | SSE2: `f32x4`, `i32x4` vector ops |
| Vectors | 135 | `vec2`, `vec3`, `vec4` |
| 3D Math | 182 | `quat`, `mat4` |
| Variant | 130 | Type-erased value container |
| Atomic | 94 | `aint32`, `aint64` atomic ops |
| Bits | 117 | `popcount`, `clz`, `ctz`, `bswap`, `rotl` |
| Time | 95 | `time_ms`, `time_us`, ISO 8601, `sleep` |
| Regex | 61 | `match`, `find`, `replace`, `split`, captures |
| File | 125 | Sandboxed file I/O (permission-gated) |
| Thread | 120 | `mutex`, `lock_guard`, `condition_variable` |
| Hash Set | 89 | `hash_set<T>` |
| Sorted Map | 89 | `sorted_map<K,V>` ordered iteration |
| List | 192 | Double-ended O(1) push/pop |
| JSON | 108 | `json_parse`, `json_stringify`, `json_value` |

</details>

<details>
<summary><strong>SDK Embedding Guide</strong> — 17 files, 3,795 lines (click to expand)</summary>

| File | Lines | Topic |
|------|------:|-------|
| `sdk-quick-start.md` | 126 | Minimal embedding example |
| `sdk-engine-lifecycle.md` | 166 | Create, configure, destroy |
| `sdk-compilation.md` | 65 | Compile from source/files |
| `sdk-execution.md` | 103 | Contexts, execute, read returns |
| `sdk-calling-functions.md` | 82 | Pass arguments from host |
| `sdk-globals.md` | 79 | Read/write script globals |
| `sdk-type-registration.md` | 862 | type_builder — expose native types |
| `sdk-native-functions.md` | 446 | Register host-callable functions |
| `sdk-hot-reload.md` | 64 | Replace code at runtime |
| `sdk-serialization-and-linking.md` | 97 | .emb binaries, multi-module |
| `sdk-introspection.md` | 317 | List functions, annotations, IR dump |
| `sdk-lifecycle.md` | 227 | Deterministic RAII, no GC |
| `sdk-debug-and-gc.md` | 202 | Debug hooks, budgets, heap stats |
| `sdk-error-handling.md` | 116 | Compile/runtime error reporting |
| `sdk-safety.md` | 121 | Fault trapping, sandboxing, permissions |
| `sdk-custom-addons.md` | 576 | Build your own addon |
| `sdk-api-reference.md` | 411 | Complete function listing |

</details>

---

## AI Skills

### `game-hacking-pcx` — Documentation Router

Forces the AI to read the correct doc file before writing any PCX API call.

```
User:  "Write me a render overlay"
AI:    → reads docs/perception/render-api.md (264 lines)
       → reads docs/perception/lifecycle-and-routines.md (134 lines)
       → writes code using real function signatures
```

Contains: file-by-file index of all 107 docs, critical Enma type rules, address type requirements, RAII notes.

### `game-cheat-guidelines` — 12 Behavioral Rules

<table>
<tr><td width="5%" align="center"><strong>#</strong></td><td width="30%"><strong>Rule</strong></td><td><strong>What It Prevents</strong></td></tr>
<tr><td align="center">1</td><td>Ground every offset</td><td>Hours wasted on stale offsets from an old SDK version</td></tr>
<tr><td align="center">2</td><td><code>uint64</code> for all addresses</td><td>Sign-extension corruption on high usermode addresses</td></tr>
<tr><td align="center">3</td><td>Validate every pointer</td><td>Silent null reads returning plausible-looking garbage</td></tr>
<tr><td align="center">4</td><td>Separate update from render</td><td>Overlay stutter when memory reads block the draw path</td></tr>
<tr><td align="center">5</td><td>Sigs over hardcodes</td><td>Script breaking on every game patch</td></tr>
<tr><td align="center">6</td><td>One feature, one file</td><td>2000-line monoliths that can't be hot-reloaded</td></tr>
<tr><td align="center">7</td><td>Construct colors/vecs per frame</td><td>Pointless globals for 4-byte stack-allocated structs</td></tr>
<tr><td align="center">8</td><td><code>f</code> suffix on float32</td><td>Silent float64→float32 truncation in vertex buffers</td></tr>
<tr><td align="center">9</td><td>Minimize memory writes</td><td>Unnecessary detection surface area</td></tr>
<tr><td align="center">10</td><td>W2S once, correctly</td><td>Behind-camera coordinate mirroring, wrong matrix layout</td></tr>
<tr><td align="center">11</td><td>GUI for all tunables</td><td>Recompiling just to change a distance threshold</td></tr>
<tr><td align="center">12</td><td>Verify with the binary</td><td>Trusting stale cached offsets over live reality</td></tr>
</table>

Each rule includes wrong/right code examples using real Perception.cx APIs.

---

## Knowledge Base

<table>
<tr>
<td width="50%" valign="top">

### Enma Cheatsheet
> `knowledge/enma-cheatsheet.md` — 164 lines

Every primitive type with size, all conversion rules, control flow, functions, structs vs classes, templates, arrays, maps, strings, pointers, coroutines, exceptions, modules, preprocessor, annotations.

### PCX API Cheatsheet
> `knowledge/pcx-api-cheatsheet.md` — 232 lines

Every function signature across all 13 Perception.cx APIs: Proc, Render, GUI, Input, CPU, Zydis, Unicorn, Net, Win, Filesystem, Sound, Lifecycle, MCP.

</td>
<td width="50%" valign="top">

### Common Patterns
> `knowledge/common-patterns.md` — 339 lines

13 complete working examples:
- Process attach + module resolve
- Pattern scan + RIP resolution
- Entity list with null guards
- World-to-screen (4x4 matrix)
- Box overlay + health bars
- Snaplines, distance text
- Angle calc, smooth interp
- GUI menu, config save/load
- Minimap / radar with rotation
- Full script skeleton

### Offset Methodology
> `knowledge/offset-methodology.md` — 130 lines

Pattern scanning, wildcard strategy, RIP-relative resolution table, pointer chain walking, struct_dump discovery, IDA/Ghidra cross-referencing, offset table format, patch stability analysis.

</td>
</tr>
</table>

---

## MCP Integration

### Perception MCP Server

> 42+ tools exposed via JSON-RPC — connect any MCP-compatible AI to Perception's live tooling.

<details>
<summary><strong>Full tool list</strong> (click to expand)</summary>

**Process Memory**
`read_memory` · `read_typed_value` · `find_pattern` · `read_pointer_chain` · `read_string` · `memory_write`

**Analysis**
`disassemble` · `struct_dump` · `find_xrefs` · `find_string_refs` · `find_function_bounds` · `analyze_function` · `trace_register` · `analyze_vtable` · `read_rtti` · `generate_signature` · `build_call_graph`

**Scanning**
`scan_string` · `scan_wstring` · `scan_pointer_to` · `scan_value` · `scan_changed` · `diff_memory`

**Process Info**
`list_processes` · `get_process_info` · `get_module_exports` · `get_module_imports`

**Files & Scripts**
`read_file` · `write_file` · `edit_file` · `search_text` · `find_references` · `check_script` · `validate_script` · `execute_script` · `get_script_api` · `web_search`

</details>

Config: [`mcp/perception-mcp-config.json`](mcp/perception-mcp-config.json)

### Supported AI Tools

| Tool | How | Guide |
|:-----|:----|:------|
| **Claude Code** | Skills + CLAUDE.md + MCP | [`claude-code-setup.md`](mcp/claude-code-setup.md) |
| **Cursor** | .cursorrules + MCP + docs | [`cursor-setup.md`](mcp/cursor-setup.md) |
| **Cline** | MCP config + system prompt | Use MCP config, paste CLAUDE.md |
| **Perception IDE** | Native — built-in AI chat | Add `docs/` as workspace folder |
| **Any OpenAI-compatible** | System prompt + docs | Paste `rules/CLAUDE.md` into prompt |

---

## LSP Language Servers

| Server | Language | Features |
|:-------|:---------|:---------|
| [enma-lsp](https://github.com/sinnafuls/enma-lsp) | Enma (`.em`) | Syntax highlighting, completion, hover docs, diagnostics, Perception API surface |
| [angel-lsp-pcx](https://github.com/sinnafuls/angel-lsp-pcx) | AngelScript (`.as`) | Syntax highlighting, completion, hover docs, diagnostics, Perception API surface |

Built automatically by `setup.sh`. Editor config:

```
Enma:        node lsp/enma-lsp/server/dist/server.js --stdio
AngelScript: node lsp/angel-lsp-pcx/server/out/server.js --stdio
```

---

## Project Rules

### `rules/CLAUDE.md` — Drop-In Project Config

Copy into any PCX scripting project. Covers:
- Language and API declarations
- Documentation paths
- Coding standards (address types, float suffixes, RAII, conversions)
- The 12 guidelines in one-line form
- Recommended file structure

### `rules/AGENTS.md` — Multi-Agent Role Definitions

Five specialist roles for orchestrated workflows:

| Agent | Responsibility |
|:------|:---------------|
| **reverse-engineer** | Binary analysis, sig generation, offset discovery |
| **script-writer** | Enma/AngelScript implementation following all rules |
| **offset-maintainer** | Post-patch offset table updates and verification |
| **feature-builder** | Feature implementation using common patterns |
| **reviewer** | Correctness, style, and detection surface review |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

1. Fork and clone with `--recursive`
2. Add or improve: docs, patterns, templates, sigs, knowledge files
3. Test with `./setup.sh` on a clean clone
4. Open a PR

New working patterns and documentation improvements are especially welcome.

---

<div align="center">

## License

[MIT](LICENSE)

---

**Credits**

[Perception.cx](https://perception.cx) · [Enma Language](https://enma-1.gitbook.io/enma) · [enma-lsp](https://github.com/sinnafuls/enma-lsp) · [angel-lsp-pcx](https://github.com/sinnafuls/angel-lsp-pcx)

</div>
