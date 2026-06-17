> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/quick-start.md).

# Quick Start

Minimal code to embed Enma in your application.

## Files You Need

* `enma.h` (umbrella) or `include/sdk.h` (just the SDK)
* One Windows lib - pick the one matching your project's CRT flag:
  * `windows/enma_x64static_mt.lib` for `/MT` (static CRT)
  * `windows/enma_x64static_md.lib` for `/MD` (dynamic CRT)
  * Mixing them produces a `RuntimeLibrary` mismatch at link time.
* Linux: `libenma.a`

All 19 shipped addons are pre-compiled into both `.lib` variants, so linking the lib is enough. Standalone `addons/em_addon_*.cpp` files still ship for reference and customization.

## Minimal Example

```cpp
#include "sdk.h"
using namespace enma;

int main() {
    // 1. Create engine
    engine_t* e = create();
    register_all_addons(e);
    set_optimize(e, true);

    // 2. Compile a script
    const char* src = R"(
        int32 main() {
            println("Hello from Enma!");
            return 42;
        }
    )";
    module_t* mod = compile(e, src, strlen(src), "hello.em");

    // 3. Execute
    context_t* ctx = create_context(mod);
    execute(ctx, "main");
    int64_t result = return_value(ctx);
    printf("result: %lld\n", result);  // 42

    // 4. Cleanup
    destroy_context(mod, ctx);
    module_destroy(mod);
    destroy(e);
    return 0;
}
```

## Compile & Link

Just link the lib - addons are bundled into it.

```bash
# Windows (clang-cl, /MT)
clang-cl /I. /MT app.cpp windows/enma_x64static_mt.lib /Fe:app.exe

# Windows (clang-cl, /MD)
clang-cl /I. /MD app.cpp windows/enma_x64static_md.lib /Fe:app.exe

# Windows (MSVC)
cl /std:c++latest /O2 /MD main.cpp windows/enma_x64static_md.lib

# Linux
g++ -std=c++23 -O2 main.cpp -lenma -o app
```

If you want a smaller binary with only specific addons, you can instead compile the `addons/em_addon_*.cpp` files you need yourself - they're standalone TUs depending only on `sdk.h`.

## What Just Happened

1. `create()` initializes the Enma JIT engine.
2. `register_all_addons()` loads all 19 shipped addons (core, string, array, map, math, simd, variant, atomic, bits, time, regex, file, hash\_set, sorted\_map, list, thread, json, vec, math3d). You can register selectively instead.
3. `compile()` takes source and produces a module of native x64 machine code.
4. `create_context()` creates an execution context (stack, locals, TLS).
5. `execute()` runs a named function.
6. `return_value()` retrieves the int64 return (use `return_string()` / `return_float()` for other types).
7. Cleanup in reverse order: context, module, engine.

## Selective Addon Registration

If you don't need all addons:

```cpp
engine_t* e = create();
register_addon_core(e);     // print functions
register_addon_string(e);   // string methods
register_addon_math(e);     // math functions
// skip array, map, simd
```

## Error Handling

If compilation fails, `compile()` returns `nullptr`. Check for errors:

```cpp
module_t* mod = compile(e, src, len, "script.em");
error_info err = last_error(e);
if (err.code != 0) {
    printf("error: %s at %s:%d:%d\n",
        err.message.c_str(), err.file.c_str(), err.line, err.column);
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/quick-start.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
