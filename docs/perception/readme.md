> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/readme.md).

# Enma - Overview

Enma is perception's proprietary full-module AOT and JIT-compiled scripting language. This site covers the APIs perception registers on top of Enma. For the language itself see [enma docs](https://enma-1.gitbook.io/enma).

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

* [Lifecycle and Routines](/perception/enma/lifecycle-and-routines.md)
* [Render](/perception/enma/render-api.md)
* [Proc](/perception/enma/proc-api.md)
* [CPU](/perception/enma/cpu-api.md)
* [Filesystem](/perception/enma/filesystem-api.md)
* [Sound](/perception/enma/sound-api.md)
* [Zydis](/perception/enma/zydis-api.md)
* [Win](/perception/enma/win-api.md)
* [Input](/perception/enma/input-api.md)
* [Unicorn](/perception/enma/unicorn-api.md)
* [Net](/perception/enma/net-api.md)
* [GUI](/perception/enma/gui-api.md)

#### AI agent surface

* [MCP](/perception/enma/mcp-api.md) — JSON-RPC over local TCP / HTTP for Claude Code, Cline, etc.

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

See [Lifecycle and Routines](/perception/enma/lifecycle-and-routines.md) for the entry point, return-value semantics, and how routines tick.

## Conventions

* **Colors and positions**: always wrap. `color(255, 255, 255, 255)`, `vec2(10.0, 20.0)`. Freshly constructed each frame is fine; Enma drops the temporaries at scope exit.
* **Float32 literals**: `0.2f`, not `cast<float32>(0.2)`. Required for vertex buffers.
* **Handles**: all `create_*` / `load_*` natives return an encrypted `int64`. Pass it back into draw / bind / destroy. Don't inspect.

## SDK

Perception's Enma SDK is not public yet.


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
