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

#### Related platform docs

* [Extensions](extensions-api.md) — extension-only APIs and explicit exclusions from the Enma script host.
* [Analyzer](analyzer.md) — integrated disassembly, decompilation, source reconstruction, hex view, scanning, and structure editing.
* [Perception IDE](ide.md) — built-in editor and AI assistant setup.
* [Changelogs](changelogs.md) — platform changelog archive; Enma language feature introduction dates are not fully versioned.
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

See [Lifecycle and Routines](lifecycle-and-routines.md) for the entry point, return-value semantics, and how routines tick.

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

| Area | Enma scripts | Extensions |
|------|--------------|------------|
| Process memory | yes | no |
| Script GUI | yes | no |
| Render | yes | partial / extension-specific |
| Input | yes | yes |
| Unicorn | yes | no |
| Callbacks and routines | yes | no |
| Filesystem | yes | yes |
| HTTP, clipboard, editor APIs | no | yes |

See [Extensions](extensions-api.md) for the authoritative extension API boundary.

## Tooling workflow

1. Use [Analyzer](analyzer.md) to inspect the target process.
2. Use [Perception IDE](ide.md) to write Enma.
3. Use [Lifecycle and Routines](lifecycle-and-routines.md) to run script entry points.
4. Use Proc, CPU, Zydis, Render, GUI, and Custom Draw APIs as needed.
5. Use [MCP](mcp-api.md) for AI-agent automation.

## SDK

Perception's Enma SDK is not public yet. Until it is published, treat upstream Enma SDK pages as language-runtime background only: they do not document Perception host registration, build/link steps, SDK headers/libraries, local test harness setup, package distribution, or whether `.emb` binaries can be compiled outside Perception and loaded by the platform.


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
