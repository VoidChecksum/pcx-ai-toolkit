> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/safety.md).

# Safety

Safety mechanisms at every layer.

## JIT Fault Trapping

Script faults (null deref, invalid memory access) are caught by a signal/SEH handler and mapped to source via the source map. The host receives a clean error; the application doesn't crash.

```cpp
bool ok = execute(ctx, "main");
if (!ok) {
    // fault was caught, error info has the source location
    error_info err = last_error(e);
    printf("fault at %s:%d\n", err.file.c_str(), err.line);
}
```

## Execution Budget

Prevent infinite loops and runaway scripts:

```cpp
set_budget(mod, 1000000);
```

The compiler inserts `check_budget` instructions in loop headers. When the budget reaches zero, execution halts cleanly.

## Permission System

Two flags. `PERM_FFI` (`0x01`) gates `[[dll(...)]]` calls. `PERM_FILE` (`0x02`) gates the file addon. Without the matching flag, the script can't call any function gated on it - rejected at compile.

```cpp
// user scripts: no FFI, no file I/O
set_permissions(e, 0);

// trusted addons: FFI only
set_permissions(e, PERM_FFI);

// host with file access too
set_permissions(e, PERM_FFI | PERM_FILE);
```

Custom natives can opt into the same gating via the trailing `permission` arg of `register_native` or `.permission(flags)` on a `type_builder` method.

## Memory Safety

Deterministic model. Structs stack-allocated by default. Escape patterns that would produce dangling stack pointers (return-pointer-to-local, store-to-global, escaping-closure-capture) are **compile errors**, not runtime bugs. Heap allocations have deterministic dtor + free. See [Lifecycle & RAII](/enma/sdk-guide/lifecycle.md).

## Type Verification

The native sig string drives compile-time type checking at every call site:

* Wrong arg type, rejected.
* Wrong struct/class identity, rejected.
* Wrong enum identity (raw int or cross-enum): rejected.
* Wrong typed-container element (`array<T>` / `map<K, V>`): rejected, including return-side var-decl.
* Calling a non-`const` method on a `const` receiver, rejected.
* Assigning through a `const` parameter, rejected.

Implicit conversion via `.convert()` registered functions fires automatically at native arg, var-decl, and binary-op sites when the source/dest types differ.

## Thread Safety

* Each engine is independent, no shared mutable state between engines.
* Multiple contexts from the same module can execute concurrently.
* Per-thread TLS prevents cross-thread state corruption.
* Tested under ASAN and TSAN with 32+ concurrent threads.

## Sandboxing

For untrusted scripts, combine these techniques:

```cpp
engine_t* e = create();
register_addon_core(e);    // print only
// skip string, array, map, math, simd
set_permissions(e, 0);     // no FFI
set_budget(mod, 100000);

register_typed<&get_score_fn>(e, "int32 get_score()");
```

The script only sees what you register. No file I/O, no network, no native library access.

## Raw Pointer Safety

All values are 64-bit integers at the ABI. Pointers (strings, arrays, structs) are raw addresses. Scripts can pass arbitrary integer values to natives. Validate pointer args before dereferencing:

```cpp
int64_t my_native_fn(MyType* obj) {
    if (!obj) return 0;
    if (!heap_is_tracked(obj)) return 0;   // only for heap-tracked allocs
    // safe to use obj
}
```

Invalid pointer deref inside JIT code is caught by the runtime fault handler; `execute()` returns `false`, host stays alive. Invalid pointer deref inside a native function is **not** caught, validate on the native side.

Scripts can't call arbitrary addresses as functions. Delegates resolve at compile time to known function indices. No `invoke_fn` equivalent exists.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/safety.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
