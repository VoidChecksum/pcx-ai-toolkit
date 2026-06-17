> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/execution.md).

# Execution

## Creating a Context

Holds execution state (stack, locals, TLS). Each context is independent.

```cpp
context_t* ctx = create_context(mod);
```

You can create multiple contexts from the same module for concurrent execution.

The full signature is `create_context(module_t* mod, size_t stack_size = 0)`. Default `stack_size = 0` runs JIT'd code on the OS thread stack, which is what you want for almost every host - it keeps OS guard pages and full C++ EH unwinding through native boundaries. Pass a non-zero `stack_size` to allocate a separate JIT stack via `set_stack_allocators`. Caveat: a switched stack breaks C++ exception unwinding across the JIT boundary because the OS dispatcher validates frames against the thread's TEB stack range. Only use it if every native call your scripts hit catches its own C++ exceptions before returning.

## Running a Function

```cpp
bool ok = execute(ctx, "main");
```

`true` on success; `false` on runtime fault, budget exceeded, or missing function.

## Reading Return Values

```cpp
int64_t  i = return_value(ctx);   // integer return
const char* s = return_string(ctx); // string return
double   f = return_float(ctx);    // float return
```

Use the function that matches the return type of the called function.

## Context Userdata

Attach application state to a context. It's accessible from native functions; 16 slots available so multiple addons can coexist without stomping each other.

```cpp
struct game_state { int32_t level; int32_t score; };
game_state state = { 5, 1000 };

set_userdata(ctx, &state);                 // slot 0 (aliased)
set_userdata_at(ctx, 1, &some_other_ptr);  // slot 1

// inside a native function:
auto* gs = static_cast<game_state*>(get_userdata(ctx));           // slot 0
auto* p  = get_userdata_at(ctx, 1);                                // slot 1

// or via active_context(), no need to thread ctx through:
auto* gs2 = static_cast<game_state*>(get_userdata(active_context()));
```

Slots are 0-15; out-of-range is a no-op / `nullptr`. Slot 0 is the same storage as `set_userdata`/`get_userdata`.

## Context Cleanup

```cpp
destroy_context(mod, ctx);
```

## Calling Script Code from Background Threads

`execute()` and `call()` set up enma's per-thread TLS automatically. If you need to invoke a script-side closure from a thread that *isn't* already inside one of those, wrap the invocation in an `execution_scope` first - see [Custom Addons / Invoking Script Closures from Background Threads](sdk-custom-addons.md#invoking-script-closures-from-background-threads). Without it, the first native that touches TLS (heap\_alloc, string concat, etc.) dereferences nullptr.

## Example

```cpp
module_t* mod = compile(e, src, len, "game.em");

context_t* ctx = create_context(mod);
execute(ctx, "init");

// game loop
while (running) {
    execute(ctx, "update");
    execute(ctx, "render");
}

execute(ctx, "shutdown");
destroy_context(mod, ctx);
module_destroy(mod);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/execution.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
