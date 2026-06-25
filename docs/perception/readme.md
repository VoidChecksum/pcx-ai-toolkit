> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/readme.md).

# Enma - Overview

Enma is perception's proprietary full-module AOT and JIT-compiled scripting language. This site covers the APIs perception registers on top of Enma, not the language reference itself. For syntax, types, templates, pointers, modules, and SDK embedding, see the upstream [Enma docs](https://enma-1.gitbook.io/enma).

Use this page as the Perception API map. Use the related platform docs below for tooling and extension boundaries.

## What's registered

#### Enma Pre-Shipped

* [Core](https://enma-1.gitbook.io/enma/addons/core)
* [String](https://enma-1.gitbook.io/enma/addons/strings)
* [Arrays](https://enma-1.gitbook.io/enma/addons/arrays)
* [Maps](https://enma-1.gitbook.io/enma/addons/maps)
* [Math](https://enma-1.gitbook.io/enma/addons/math)
* [3D Math (quat + mat4)](https://enma-1.gitbook.io/enma/addons/math3d)
* [SIMD](https://enma-1.gitbook.io/enma/addons/simd)
* [Variant](https://enma-1.gitbook.io/enma/addons/variant)
* [Atomic](https://enma-1.gitbook.io/enma/addons/atomic)
* [Bits](https://enma-1.gitbook.io/enma/addons/bits)
* [Time](https://enma-1.gitbook.io/enma/addons/time)
* [Regex](https://enma-1.gitbook.io/enma/addons/regex)
* [Thread](https://enma-1.gitbook.io/enma/addons/thread)
* [Vectors](https://enma-1.gitbook.io/enma/addons/vec)
* [Hash Set](https://enma-1.gitbook.io/enma/addons/hash_set)
* [Sorted Map](https://enma-1.gitbook.io/enma/addons/sorted_map)
* [List](https://enma-1.gitbook.io/enma/addons/list)
* [JSON](https://enma-1.gitbook.io/enma/addons/json)

#### **Perception API**

* [Lifecycle and Routines](lifecycle-and-routines.md)
* [Render](render-api.md)
  * [Custom Draw](custom-draw-api.md) — D3D11 pipeline access: HLSL shaders, buffers, textures, render targets, depth buffers, primitive topology, and encrypted `int64` GPU handles.
* [Proc](proc-api.md)
* [CPU](cpu-api.md)
* [Filesystem](filesystem-api.md)
* [Sound](sound-api.md)
* [Zydis](zydis-api.md)
* [Win](win-api.md)
* [Input](input-api.md)
* [Unicorn](unicorn-api.md)
* [Net](net-api.md)
* [GUI](gui-api.md)

#### Related Perception platform docs

* [Custom Draw](custom-draw-api.md) — first-class D3D11 GPU pipeline API registered through Render.
* [Perception IDE](ide.md) — built-in editor, AI assistant, tool calls, and project workflow.
* [Extensions API](extensions-api.md) — extension-only API surface and limitations.
* [Perception Analyzer](analyzer.md) — disassembler, decompiler, memory analysis, and structure tooling.
* [Changelogs](changelogs.md) — release history and API/version provenance.
* [SDK status](sdk-status.md) — what local compilation and `.emb` workflows are currently supported.
* [Versioning and migration](versioning-and-migration.md) — symbol provenance, unknown introduction dates, and legacy AngelScript-to-Enma migration notes.
* [llms.txt](https://docs.perception.cx/perception/llms.txt) — complete machine-readable page index.

#### AI agent surface

* [MCP](mcp-api.md) — JSON-RPC over local TCP / HTTP for Claude Code, Cline, etc.

## Minimal example

```cpp
int64 g_tick;

void my_draw(int64 data) {
    g_tick = g_tick + 1;
    color white = color(255, 255, 255, 255);
    color noeffect = color(0, 0, 0, 0);

    string text = "tick=" + cast<string>(g_tick);
    draw_text(text, vec2(40.0, 40.0), white, get_font20(), 0, noeffect, 0.0);
}

int64 main() {
    g_tick = 0;
    register_routine(cast<int64>(my_draw), 0);
    return 1;
}
```

See [Lifecycle and Routines](lifecycle-and-routines.md) for the entry point, return-value semantics, and how routines tick. For advanced GPU work, use [Custom Draw](custom-draw-api.md).

Minimum checklist:

* Define `int64 main()`.
* Initialize globals before registering persistent work.
* Register a routine when the script needs to keep ticking.
* Return `1` to stay loaded; return `0` to unload immediately.
* Use unload cleanup hooks when you own external or long-lived resources.
* Do not inspect encrypted `int64` handles.
* Wrap colors/vectors (`color(...)`, `vec2(...)`).
* Use `0.2f` for `float32` literals.

## Before writing Perception Enma scripts

Read these upstream Enma pages first if you are new to PCX Enma scripting:

* [Basics](https://enma-1.gitbook.io/enma/language/basics), types, and casts.
* [Functions](https://enma-1.gitbook.io/enma/language/functions).
* [Modules and imports](https://enma-1.gitbook.io/enma/language/modules).
* [Structs and classes](https://enma-1.gitbook.io/enma/language/structs-and-classes).
* [Pointers](https://enma-1.gitbook.io/enma/language/pointers). Pointer arithmetic is typed: `p + n` scales by `sizeof(T)`, so use the Proc/CPU APIs for raw byte-offset memory workflows.
* [Templates](https://enma-1.gitbook.io/enma/language/templates). Some C++-style patterns are unsupported; see this toolkit's [upstream suggestions](../enma/UPSTREAM-SUGGESTIONS.md) for known limits around nested template fields, overloaded function templates, packed strings, and LSP template diagnostics.
* Addons commonly used by PCX scripts: [Core](https://enma-1.gitbook.io/enma/addons/core), [String](https://enma-1.gitbook.io/enma/addons/strings), [Arrays](https://enma-1.gitbook.io/enma/addons/arrays), [Maps](https://enma-1.gitbook.io/enma/addons/maps), [Math](https://enma-1.gitbook.io/enma/addons/math), [Vec](https://enma-1.gitbook.io/enma/addons/vec), [JSON](https://enma-1.gitbook.io/enma/addons/json), [Bits](https://enma-1.gitbook.io/enma/addons/bits), and [Time](https://enma-1.gitbook.io/enma/addons/time).

Perception-side entry points live in [Lifecycle and Routines](lifecycle-and-routines.md).

## Before writing Perception Enma scripts

Read these upstream Enma pages first if you are new to PCX Enma scripting:

* [Basics](https://enma-1.gitbook.io/enma/language/basics), types, and casts.
* [Functions](https://enma-1.gitbook.io/enma/language/functions).
* [Modules and imports](https://enma-1.gitbook.io/enma/language/modules).
* [Structs and classes](https://enma-1.gitbook.io/enma/language/structs-and-classes).
* [Pointers](https://enma-1.gitbook.io/enma/language/pointers). Pointer arithmetic is typed: `p + n` scales by `sizeof(T)`, so use the Proc/CPU APIs for raw byte-offset memory workflows.
* [Templates](https://enma-1.gitbook.io/enma/language/templates). Some C++-style patterns are unsupported; see this toolkit's [upstream suggestions](../enma/UPSTREAM-SUGGESTIONS.md) for known limits around nested template fields, overloaded function templates, packed strings, and LSP template diagnostics.
* Addons commonly used by PCX scripts: [Core](https://enma-1.gitbook.io/enma/addons/core), [String](https://enma-1.gitbook.io/enma/addons/strings), [Arrays](https://enma-1.gitbook.io/enma/addons/arrays), [Maps](https://enma-1.gitbook.io/enma/addons/maps), [Math](https://enma-1.gitbook.io/enma/addons/math), [Vec](https://enma-1.gitbook.io/enma/addons/vec), [JSON](https://enma-1.gitbook.io/enma/addons/json), [Bits](https://enma-1.gitbook.io/enma/addons/bits), and [Time](https://enma-1.gitbook.io/enma/addons/time).

Perception-side entry points live in [Lifecycle and Routines](lifecycle-and-routines.md).

## Conventions

* **Colors and positions**: always wrap. `color(255, 255, 255, 255)`, `vec2(10.0, 20.0)`. Freshly constructed each frame is fine; Enma drops the temporaries at scope exit.
* **Float32 literals**: `0.2f`, not `cast<float32>(0.2)`. Required for vertex buffers.
* **Handles**: all `create_*` / `load_*` natives return an encrypted `int64`. Pass it back into draw / bind / destroy. Don't inspect.

## Extension vs Enma script surface

| Capability | Enma script | Extension |
|------------|-------------|-----------|
| `proc_t` / process memory | yes | no |
| Render API | yes | partial / extension-specific |
| Input API | yes | yes |
| PCX script GUI widgets | yes | no |
| Unicorn | yes | no |
| Zydis | yes | yes / partial |
| Filesystem | yes | yes |
| HTTP | Net API | extension-specific sync HTTP |
| Clipboard | Win API | yes |
| Register routine / callback | yes | no |
| Editor manipulation | no | yes |

See [Extensions](extensions-api.md) for the authoritative extension API boundary.

## Tooling workflow

1. Use [Analyzer](analyzer.md) to inspect the target process.
2. Use [Perception IDE](ide.md) to write Enma.
3. Use [Lifecycle and Routines](lifecycle-and-routines.md) to run script entry points.
4. Use Proc, CPU, Zydis, Render, GUI, and Custom Draw APIs as needed.
5. Use [MCP](mcp-api.md) for AI-agent automation.

## Permissions and gates

| Permission | Affects | Failure behavior | Docs |
|------------|---------|------------------|------|
| `file_system_access` | FS read/write/list | `false` / `0` / empty | [Filesystem](filesystem-api.md) |
| `kernel_rw_access` | kernel process access such as `get_eprocess` | `0` / log | [Proc](proc-api.md) |
| `write_memory` | process memory writes | `false` / no-op | [Proc](proc-api.md) |
| MCP tool permissions | local agent calls | JSON-RPC `-32001` with missing permission | [MCP](mcp-api.md) |
| `PERM_FFI` | Enma FFI | compile/runtime permission error | [Enma advanced](../enma/lang-advanced.md) |

## Return-value conventions

| Return | Common meaning | Disambiguate with |
|--------|----------------|-------------------|
| `0` address / handle / size | missing, invalid, denied, or failed allocation | validity and permission checks |
| empty string | empty data or failure | existence check first |
| empty array | no results or failure | separate existence/status check if available |
| `false` | validation failure, permission failure, missing target, or I/O failure | logs and precondition checks |

## Resource lifetime

| Resource | Created by | Destroyed by | Auto-cleanup on unload | User can inspect? |
|----------|------------|--------------|------------------------|-------------------|
| Font handle | `create_font`, `create_font_mem`, built-in getters | unload / owner cleanup | yes | no |
| Bitmap handle | `create_bitmap` | unload / owner cleanup | yes | no |
| Custom Draw resources | `create_shader`, buffers, textures, states | matching `destroy_*` or unload | yes | no |
| GUI handle | GUI add/create calls | unload | yes | no |
| Sound resource | load/play calls | stop/unload where exposed | yes | no |
| Net socket / WebSocket handle | connect/create calls | close/unload where exposed | specify per API | no |
| `proc_t` | `ref_process` | scope/unload | yes | no |

Handles are encrypted `int64` values. Pass them back unchanged; never branch on their internal value except `0` failure checks.

## Language boundary

These pages describe Enma bindings. Legacy AngelScript examples may differ. Do not copy AngelScript handle syntax, array syntax, callback syntax, or GUI patterns into Enma without checking the Enma page or API index first.

## SDK

Perception's Enma SDK is not public yet. See [SDK status](sdk-status.md) for the current local-development boundary.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/readme.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
