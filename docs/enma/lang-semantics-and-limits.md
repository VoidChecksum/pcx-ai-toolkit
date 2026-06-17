> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/semantics-and-limits.md).

# Semantics & Limits

Single-page answer to "can I do X?" grouped by area, with the verdict and where the rule lives.

## Pointers

Enma supports pointers as typed handles to heap objects. Pointer **arithmetic and manipulation are not in the language**. Pointers only participate in creation, member access, and deletion.

| Operation                                     | Allowed | Notes                                                              |
| --------------------------------------------- | :-----: | ------------------------------------------------------------------ |
| `T* p = new T(args);`                         |    ✓    | Heap allocation with ctor                                          |
| `p->field` (pointer access)                   |    ✓    | Use `->` on pointers, `.` on values (style); parser accepts either |
| `delete p;`                                   |    ✓    | Manual free; no-op on null                                         |
| `T* q = p;` (pointer copy)                    |    ✓    | Two pointers to the same object                                    |
| `T* q = null;`                                |    ✓    | Null literal assignable to any pointer type                        |
| `int64 i = 0x1000; T* p = i;`                 |    ✓    | int64/uint64 ↔ pointer is implicit (8-byte slot, lossless on x64)  |
| `int64 addr = cast<int64>(p);`                |    ✓    | Pointer → int64 is implicit; the explicit cast also works          |
| `int64 fn = my_function;` (or `&my_function`) |    ✓    | function → int64/pointer is implicit (closure handle)              |
| `T* p = &s + 8;` (pointer arithmetic)         |    ✗    | Compile error                                                      |
| `T* p = &local;` (address-of must feed ptr)   |  ✗ / ✓  | Must assign to pointer type; storing to non-pointer is an error    |
| `T x = new T();`                              |    ✗    | Pick stack (`T x;`) or heap (`T* x = new T();`)                    |
| `delete` on non-pointer                       |    ✗    | Compile error                                                      |
| Double delete / delete null                   |    -    | No-op                                                              |
| Storing pointer-to-local in a global/field    |    ✗    | Compile error (would dangle)                                       |
| Returning pointer to local                    |    ✗    | Compile error (would dangle)                                       |

The escape analyzer is conservative, if it can't prove the pointer is safe, it rejects. Moving to `new T()` is the escape hatch.

## Memory model

| Feature                                    | Status                                                                       |
| ------------------------------------------ | ---------------------------------------------------------------------------- |
| Stack-allocated structs (`T x;`)           | Default for value-type structs                                               |
| Heap-allocated structs (`T* x = new T();`) | Explicit via `new` / `delete`                                                |
| RAII / scope-drop                          | Built-in for all addon types with a registered dtor                          |
| Tracing garbage collector                  | **None**. Cleanup is deterministic (compile-time scope / explicit `delete`). |
| Manual `free`                              | Use `delete p` for `new`-allocated pointers                                  |
| Double-free                                | Runtime error (for array types); no-op for `delete null`                     |
| Use-after-free                             | Trapped where possible; `execute()` returns `false`                          |
| Budget (instruction / memory)              | Opt-in per module                                                            |

## Integer semantics

| Behavior                           | Rule                                                                                                      |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Overflow                           | Silent wrap at int64 width, script-level arithmetic evaluates at 64 bits regardless of declared int width |
| Division by zero                   | Runtime trap                                                                                              |
| Shift by >= bit-width              | Implementation-defined (x64: modulo the width)                                                            |
| Signed ↔ unsigned (any width)      | **Compile error** without `cast<T>(x)`. Integer/float literals are exempt - `uint32 a = 5;` is fine.      |
| `int32 → int64` (same-sign widen)  | Implicit                                                                                                  |
| `int64 → int32` (same-sign narrow) | Implicit (runtime is 64-bit-slot regardless; narrowing is purely a declared-type thing)                   |

## Float semantics

| Behavior                     | Rule                                                                                                                                                                                   |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| NaN propagation              | Standard IEEE-754 (`NaN != NaN`, arithmetic propagates NaN)                                                                                                                            |
| `float32` ABI                | Native boundary narrows to 32-bit; script keeps 64-bit view (round-trip bits preserved for `cast<float32>(x)` literals)                                                                |
| `float32 → float64` (widen)  | Implicit                                                                                                                                                                               |
| `float64 → float32` (narrow) | **Compile error** without `cast<float32>(x)`. Float literals are exempt - `float32 a = 1.5;` is fine.                                                                                  |
| Float literal `float32` form | `1.5f` / `1.5F` - the suffix narrows the literal to `float32` at parse time. Bare `1.5` is `float64`. The suffix is literal-only; runtime narrowing still needs `cast<float32>(expr)`. |
| `int → float`                | Implicit                                                                                                                                                                               |
| `float → int`                | **Compile error** without `cast<int>(x)`. Truncation is too easy to miss silently.                                                                                                     |
| Infinity                     | Standard IEEE, operations follow IEEE rules                                                                                                                                            |

## Type system

| Feature                                    | Supported                                                                                                                                                               |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Structs (value type, stack-default)        | ✓                                                                                                                                                                       |
| Classes (reference type with vtable)       | ✓                                                                                                                                                                       |
| Single inheritance + virtual methods       | ✓ (classes; structs don't vtable unless marked)                                                                                                                         |
| Multiple inheritance (C++-style)           | ✓ (`class C : A, B { ... }`. Diamond rejected, ctor/dtor chain in declaration / reverse order, this-adjusted dispatch, vtable thunks for override-via-non-primary-base) |
| Templates (`template<typename T>`)         | ✓ (duck-typed at instantiation)                                                                                                                                         |
| Concepts / requires clauses (script-level) | ✗ (generic addon types support `.requires_iface(param, iface)` constraints SDK-side)                                                                                    |
| Variadic templates (`Ts...`)               | ✗ (but functions accept `...` with `__va_count` / `__va_arg(i)` for runtime varargs)                                                                                    |
| `decltype(expr)`                           | ✓                                                                                                                                                                       |
| Designated initializers (`{.x=1, .y=2}`)   | ✓                                                                                                                                                                       |
| User-defined literals (`42_km`)            | ✓ (rewritten to `_km(42)` at parse)                                                                                                                                     |
| RTTI (`typeid`)                            | ✗ (but addon-type reflection via `find_type_reg`)                                                                                                                       |
| rvalue references / move semantics         | partial — `move(x)` intrinsic transfers + nulls source; no `&&` rvalue-reference type                                                                                   |
| Reflection at script level                 | ✗ (SDK-side only, via `find_type_reg`)                                                                                                                                  |
| Modules (`import` / `#include`)            | ✓                                                                                                                                                                       |
| Namespaces / `using`                       | ✓                                                                                                                                                                       |
| Operator overloading                       | ✓ on script structs (`operator+` etc.) and addon types (via `bin_*` / `unary_*`)                                                                                        |
| Exceptions (`try` / `catch` / `throw`)     | ✓ (throw any int / string / struct; multiple typed `catch` clauses dispatched on thrown type)                                                                           |
| Match expression (`match (x) { ... }`)     | ✓ (returns a value; arms use `=> expr,` or `_` wildcard)                                                                                                                |
| Ternary (`cond ? a : b`)                   | ✓                                                                                                                                                                       |
| Coroutines (`coroutine` / `yield`)         | ✓                                                                                                                                                                       |
| Delegates                                  | ✓                                                                                                                                                                       |
| Lambdas / closures                         | ✓ (closure escape rules enforced)                                                                                                                                       |
| Mixins / properties                        | ✓                                                                                                                                                                       |
| Nullable types (`nullable T`)              | ✓                                                                                                                                                                       |
| Fixed-size arrays (`int32[2] buf`)         | ✗ (use `int32[] buf = new int32[N]` or brace init `{...}`)                                                                                                              |

## Unsafe operations (rejected at compile time)

These produce a compile error, not a runtime fault:

* Raw int → pointer assignment
* Pointer arithmetic (`&s + 8`, `p + 1`)
* `cast<int64>(ptr)` - pointer to int
* Escaping a stack local (into a global, a field, or out of a return)
* Calling a non-`const` method on a `const` receiver
* Assigning through a `const` parameter
* Native call with wrong-typed arg (integer where string expected, etc.)
* Native call with wrong enum identity (raw int or cross-enum)
* Template method call with wrong element/key/value type
* `new` on a non-addon-registered, non-struct, non-class type
* `delete` on a non-pointer
* `T x = new T();` (must pick stack or heap)
* `[[noescape]]` violation (allocation that escapes)
* Function lacking a matching signature / ambiguous overload
* Calling a native that requires a permission the module doesn't have

## Runtime traps

These are caught at runtime and reported via `execute()` returning `false`:

* Null deref on array or struct pointer (script-catchable via `try`/`catch (string e)` when using `->`; see [Catching null-pointer dereferences](lang-advanced.md#catching-null-pointer-dereferences))
* Out-of-bounds array subscript (positive or negative index)
* Access to a freed array
* Division by zero
* Stack overflow
* Double-free on arrays (reported as a runtime error)
* Use-after-free where the freed-marker is still readable

Inside a native function: **not trapped.** Validate your inputs before dereferencing; use `heap_is_tracked(ptr)` for heap-allocated values.

## Permissions

Two bits today. A script cannot call any permission-gated native unless the permission was granted via `set_permissions(engine, flags)` on the engine:

| Flag        | Value  | Gates                       |
| ----------- | ------ | --------------------------- |
| `PERM_FFI`  | `0x01` | `[[dll(...)]]` extern decls |
| `PERM_FILE` | `0x02` | All file-addon operations   |

Scripts without the right permission fail to compile any call that requires it, the check happens at module compile, not at runtime.

## Thread safety

* Each engine is independent, no shared mutable state across engines
* Multiple contexts off the same module run concurrently
* Per-thread TLS heap (cleaned up when the thread exits)
* The `thread` addon gives you mutex / cond\_var / lock\_guard for cross-thread coordination. Native functions that touch Enma's heap must be called on a thread that has an active context; raw mutex operations don't need one.
* Tested under ASAN and TSAN with 32+ concurrent threads

## Things that simply don't exist

* **Module system beyond `import`** - no separately-compiled binary modules at the language level (the SDK's `link()` function lets host code join modules)
* **Async / await / futures** - use coroutines + the thread addon
* **Networking addon** - not shipped; host can write one as a standalone addon
* **Custom allocators per scope** - one heap per thread, not pluggable
* **Built-in annotations**: `[[inline]]`, `[[noinline]]`, `[[noopt]]`, `[[dll]]`, `[[packed]]`, `[[align]]`, `[[serialize]]`, `[[reflect]]`, `[[export]]`, `[[noescape]]`. Custom names parse and are queryable from the host but carry no compiler semantics.
* **RTTI / `typeid`** - use `find_type_reg` on the SDK side instead
* **Script-level reflection** - SDK-only
* **Inline assembly** - fixed whitelist of intrinsics only: `__asm_rdtsc`, `__asm_pause`, `__asm_mfence`, `__asm_nop`. Arbitrary user-provided asm is not supported.
* **Fold expressions** (`(args + ...)`) - not supported. Use `__va_arg(i)` + a loop for runtime fold.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/semantics-and-limits.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
