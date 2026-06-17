> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/engine-lifecycle.md).

# Engine Lifecycle

### Creating an Engine

```cpp
engine_t* e = create();
```

Holds compiler state, type registrations, native function bindings, and configuration. Typically one engine per application.

`create()` auto-registers built-in script-level natives: `heap_collect`, `heap_count`, `set_budget`, `set_memory_budget`, `register_event`/`fire_event`/`clear_events`, `assert`, `time_ms`, `co_create` + type `coroutine_t`, type `counter_t`. The `throw` keyword and try/catch are wired in via the exception runtime.

### Configuration

Configure the engine before compiling any scripts.

#### Addons

```cpp
register_all_addons(e);
// or selectively:
register_addon_core(e);
register_addon_string(e);
register_addon_array(e);
register_addon_map(e);
register_addon_math(e);
register_addon_simd(e);
```

#### Optimization

```cpp
set_optimize(e, true);   // enable optimizer (default: on, set by create())
set_debug(e, false);     // enable debug info (default: off)
```

#### Preprocessor Defines

```cpp
define(e, "DEBUG", "1");
define(e, "VERSION", "2");
define(e, "PLATFORM", "windows");
```

These are available in scripts via `#ifdef`:

```cpp
#ifdef DEBUG
    println("debug build");
#endif
```

#### Include & Module Paths

```cpp
add_include_path(e, "includes/");  // for #include
add_module_path(e, "modules/");    // for import
```

#### Resolve Callbacks

Override how `#include` and `import` find files. Return `true` to provide the buffer, `false` to fall back to filesystem resolution.

```cpp
bool my_include_resolver(const char* path, char** out_data, size_t* out_len, void* userdata) {
    auto* vfs = static_cast<VirtualFS*>(userdata);
    std::string content;
    if (!vfs->read(path, content)) return false;
    *out_data = static_cast<char*>(malloc(content.size()));
    memcpy(*out_data, content.data(), content.size());
    *out_len = content.size();
    return true;
}

set_include_resolver(e, my_include_resolver, &my_vfs);
set_import_resolver(e, my_import_resolver, &my_vfs);
```

Import resolver tries `.emb` (binary) first, then `.em` (source), then the bare name. The engine frees the returned buffer after use.

#### Permissions

```cpp
set_permissions(e, PERM_FFI);            // allow [[dll(...)]] FFI calls
set_permissions(e, PERM_FFI | PERM_FILE); // also allow the file addon
```

Two flags today:

* `PERM_FFI` (`0x01`) gates `[[dll(...)]]`.
* `PERM_FILE` (`0x02`) gates the file addon.

Scripts fail to compile any call to a gated feature when the matching flag isn't set.

```cpp
uint32_t flags = get_permissions(e);
```

### Destroying an Engine

```cpp
destroy(e);
```

Destroy all modules and contexts first, the engine does not track child objects.

### DLL Shutdown

If you load enma inside a DLL/plugin that may be unloaded while the host process keeps running, call `shutdown()` once from your `DllMain` `DLL_PROCESS_DETACH` handler before the DLL unloads:

```cpp
BOOL APIENTRY DllMain(HMODULE, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_DETACH) {
        enma::shutdown();
    }
    return TRUE;
}
```

This removes enma's process-global fault handler, which holds a function pointer into the DLL's text segment. If you skip this and the DLL unloads, the next unrelated exception anywhere in the process walks into freed memory and crashes — usually delayed, looking like a spontaneous crash much later. Safe to call when no engines exist. Don't execute any enma script code after `shutdown()` — without the fault handler, JIT faults take down the host. Static-linked exes and long-lived hosts that never unload don't need this.

### Typical Lifecycle

```cpp
engine_t* e = create();

// configure
register_all_addons(e);
set_optimize(e, true);
add_module_path(e, "scripts/");

// register custom types and functions
register_typed<&get_hp_fn>(e, "int32 get_hp(int32 player_id)");

// compile and run scripts (possibly many times)
module_t* mod = compile_file(e, "game.em");
context_t* ctx = create_context(mod);
execute(ctx, "main");
destroy_context(mod, ctx);
module_destroy(mod);

// shutdown
destroy(e);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/engine-lifecycle.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
