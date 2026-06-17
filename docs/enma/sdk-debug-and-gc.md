> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/debug-and-gc.md).

# Debug & Heap

## Debug Hooks

Callback fires at every source line:

```cpp
void my_debug_hook(const char* file, uint32_t line, int64_t* frame) {
    printf("[%s:%d]\n", file, line);
}

set_debug_hook(mod, my_debug_hook);
```

`frame` indexes into the current function's locals by slot number. Enable debug mode for source maps:

```cpp
set_debug(e, true);
```

## Execution Budget

```cpp
set_budget(mod, 1000000);  // max 1 million instructions; 0 = disabled
```

When exhausted, `execute()` returns `false`.

## Memory Model

Deterministic. No tracing collector. See [Lifecycle & RAII](/enma/sdk-guide/lifecycle.md) for the full model.

`heap_*` SDK entry points exist for stats and budget control only:

```cpp
heap_collect(mod);                 // no-op; cleanup is deterministic
heap_set_memory_budget(mod, ...);  // hard limit on live heap bytes
heap_stats stats = heap_get_stats(mod);
```

### Stats

```cpp
heap_stats stats = heap_get_stats(mod);
printf("live allocs: %llu\n", stats.alloc_count);   // currently-alive heap objects
printf("live bytes:  %llu\n", stats.total_bytes);
printf("total freed: %llu\n", stats.freed_count);
printf("freed bytes: %llu\n", stats.freed_bytes);
```

| Field         | Description                         |
| ------------- | ----------------------------------- |
| `alloc_count` | Currently-live heap allocations     |
| `total_bytes` | Currently-live heap bytes           |
| `freed_count` | Cumulative frees since engine start |
| `freed_bytes` | Cumulative bytes freed              |

Unbounded `alloc_count` growth indicates a leak, typically a `new` whose handle isn't stored in a scope-tracked local or a pointer global that isn't reset.

### Memory Budget

Set a hard limit on total live heap bytes. `alloc()` returns null when exceeded.

```cpp
heap_set_memory_budget(mod, 1024 * 1024 * 64);  // 64 MB cap
heap_set_memory_budget(mod, 0);                  // unlimited (default)
```

## Stack Traces

Requires `set_debug(e, true)`.

```cpp
stack_frame frames[32];
uint32_t count = get_stack_trace(ctx, frames, 32);
for (uint32_t i = 0; i < count; ++i) {
    printf("  %s (%s:%d)\n", frames[i].function, frames[i].file, frames[i].line);
}
```

`stack_frame` fields: `function` (`const char*`), `file` (`const char*`), `line` (`uint32_t`).

`get_stack_trace` is best-effort. The JIT doesn't push fixed frame metadata, so the implementation iterates the module's `debug_functions` table. Treat it as a "what functions are visible in this module" snapshot rather than a true call-frame walk - it does not reflect real recursion depth or invocation order.

## Last-Executed Line

For pinpointing exactly where a JIT fault hit, use `get_last_executed_line(mod)`:

```cpp
set_debug(e, true);              // must be set BEFORE compile so op_debug_line is emitted
module_t* mod = compile_file(e, "script.em");
context_t* ctx = create_context(mod);

if (!execute(ctx, "main")) {
    int64_t line = get_last_executed_line(mod);
    printf("crashed at line %lld\n", line);
}
```

The JIT records the source line before each statement runs, so the value persists across a fault — pointing at the exact source line the JIT was on. Returns `-1` when no line has executed yet, `0` when debug wasn't enabled at compile time. More reliable than `get_stack_trace` for crash diagnostics.

## IDE Debugger SDK

A debugger SDK on top of the per-line hook foundation. All opt-in via `set_debug(e, true)` BEFORE compile.

For full local-variable visibility you should ALSO call `set_optimize(e, false)`. Otherwise the optimizer promotes locals to registers and they never land in their declared frame slots, so `read_local_*` returns garbage.

```cpp
// Source map + function lookup
struct em_debug_fn_t;   // opaque
const em_debug_fn_t* find_fn_at(module_t*, const char* file, uint32_t line);
const char* debug_fn_name        (const em_debug_fn_t*);
uint32_t    debug_fn_local_count (const em_debug_fn_t*);
uint32_t    debug_fn_param_count (const em_debug_fn_t*);

void find_code_offsets(module_t*, const char* file, uint32_t line,
                       size_t* out_offsets, uint32_t* out_count, uint32_t max);

// Local readback (frame is the rbp the hook receives)
struct em_local_info { const char* name; type_id type; uint32_t slot; };
uint32_t enumerate_locals(const em_debug_fn_t*, em_local_info* out, uint32_t max);
int64_t     read_local_int    (int64_t* frame, uint32_t slot);
double      read_local_float  (int64_t* frame, uint32_t slot);
const char* read_local_string (int64_t* frame, uint32_t slot);
void*       read_local_pointer(int64_t* frame, uint32_t slot);

// Breakpoints (per module)
int32_t set_breakpoint    (module_t*, const char* file, uint32_t line);
void    clear_breakpoint  (module_t*, int32_t bp_id);
void    enable_breakpoint (module_t*, int32_t bp_id, bool enabled);
bool    is_breakpoint_at  (module_t*, const char* file, uint32_t line);

struct em_breakpoint_info { int32_t id; const char* file; uint32_t line; bool enabled; };
uint32_t list_breakpoints(module_t*, em_breakpoint_info* out, uint32_t max);

// Stepping (per context)
enum class step_mode : int32_t { step_none, step_over, step_in, step_out };
void      set_step_mode           (context_t*, step_mode);
step_mode get_step_mode           (context_t*);
void      set_step_baseline_depth (context_t*, int32_t depth);
int32_t   get_step_baseline_depth (context_t*);
int32_t   get_call_depth          (int64_t* frame, module_t*);

// Pause/resume (per context)
void request_pause      (context_t*);
void resume             (context_t*);   // also clears step_mode
bool is_pause_requested (context_t*);

// Convenience: combines breakpoint hit, pause, and step-mode logic.
bool should_pause_at(context_t*, module_t*, int64_t* frame,
                      const char* file, uint32_t line);
```

State is per-context, so multi-thread routines each get independent step/pause state. The IDE host implements its DAP / VS Code adapter on top of these primitives.

Typical hook:

```cpp
void on_line(const char* file, uint32_t line, int64_t* frame) {
    context_t* ctx = active_context();
    module_t* mod = my_module;
    if (!should_pause_at(ctx, mod, frame, file, line)) return;

    auto* fn = find_fn_at(mod, file, line);
    em_local_info infos[64];
    uint32_t n = enumerate_locals(fn, infos, 64);
    for (uint32_t i = 0; i < n; ++i) {
        switch (infos[i].type) {
            case type_id::t_int64:   inspect(read_local_int   (frame, infos[i].slot)); break;
            case type_id::t_float64: inspect(read_local_float (frame, infos[i].slot)); break;
            case type_id::t_string:  inspect(read_local_string(frame, infos[i].slot)); break;
            default:                 inspect(read_local_pointer(frame, infos[i].slot));
        }
    }
    // ... wait for IDE command, then either:
    set_step_baseline_depth(ctx, get_call_depth(frame, mod));
    set_step_mode(ctx, step_mode::step_over);   // or step_in / step_out / step_none
    resume(ctx);   // clears pause_requested
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/debug-and-gc.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
