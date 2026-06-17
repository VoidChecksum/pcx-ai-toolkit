> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/readme.md).

# Introduction - Enma

Enma is a full-module AOT and JIT-compiled scripting language targeting x64. Compiles to native machine code through an optimizing pipeline. Designed to embed in native applications.

```cpp
int32 fib(int32 n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}

int32 main() {
    println(fib(30));
    return 0;
}
```

### Features

**Primitives:** `bool`, `char`, `wchar`, `int8`/16/32/64, `uint8`/16/32/64, `aint8`/16/32/64 (atomic), `float32`, `float64`, `string`, `wstring`, `void`, `null`, `auto`

**Variables:** `const`, `constexpr`, `nullable`, `auto` inference

**Operators:** arithmetic, comparison, logical, bitwise, compound assign (`+=` etc.), `++`/`--`, ternary, `cast<T>()`, `sizeof`, `offsetof`

**Control flow:** `if`/`else`, `while`, `do-while`, `for`, `for-each`, `switch`, `match`, `break`, `continue`, `goto`, `defer`

**Functions:** default args, reference (`&`), out (`out`), variadic (`...` + `__va_count` / `__va_arg`), `extern`, `const` methods, function references

**Lambdas:** `[caps](p) -> T { }` and arrow `(p) => expr`

**Arrays:** dynamic with `push`/`pop`/`insert`/`remove`/`sort`/`reverse`/`contains`/`index_of`/`slice`/`join`/iteration; brace init; typed `T[]`

**Maps:** key-value with `get`/`set`/`contains`/`remove`/`length`/iteration; typed `map<K,V>`

**Strings:** interpolation `f"v={x}"`, concat with `+`, methods: `length`, `substr`, `find`, `contains`, `starts_with`, `ends_with`, `char_at`, `to_int`, `to_float`, `to_upper`, `to_lower`, `trim`, `replace`, `split`, `repeat`

**Structs:** value types, fields, ctor, dtor, methods, operator overloading, bitfields, packed/aligned

**Classes:** reference types, multi-inheritance (no virtual / no diamonds), implicit virtual dispatch with vtable thunks for non-primary base overrides, `override`, RAII

**Interfaces:** abstract method contracts

**Mixins:** add methods externally

**Properties:** getter/setter syntax

**Templates:** generic structs and functions, monomorphization, reference params, nesting

**Enums:** `Enum::Value` access with preserved identity

**Typedefs:** `using Alias = Type` or `typedef Type Alias`

**Delegates:** typed function references

**Namespaces:** `namespace`, `using namespace`, `::`

**Coroutines:** `coroutine` + `yield`, driven via `coroutine_t.next()` / `value()`

**Exceptions:** `try`/`catch`/`throw` with stack unwinding, dtors and `defer` run during unwind

**Heap allocation:** `new T(args)`, `new T[N]`, `new T[N](ctor_args)`, `delete`, `delete[]`

**Inline asm intrinsics:** `__asm_rdtsc`, `__asm_pause`, `__asm_mfence`, `__asm_nop`

**Annotations:** `[[packed]]`, `[[align(N)]]`, `[[reflect]]`, `[[serialize]]`, `[[export]]`, `[[noopt]]`, `[[noinline]]`, `[[inline]]`, `[[dll(...)]]` (FFI), custom annotations queryable from host

**Modules:** `import` with aliasing, precompiled `.emb`, source fallback, multi-module linking

**Preprocessor:** `#define`/`#undef`, `#ifdef`/`#ifndef`/`#elif`/`#else`/`#endif`, `#include`, `#pragma`

**FFI:** `[[dll("lib.so")]]` gated by `PERM_FFI`

**Static assert:** `static_assert(expr, "message")`

**SDK:** C++ embedding API. Type registration with fields, methods, properties, subscript, iteration, factory, destructor, full operator set (arithmetic, comparison, three-way `compare()`, compound assign, ++/--, bitwise), implicit conversion, hash, copy. Typed `_typed<&Fn>` wrappers for every hook. Interfaces with auto-injected `type_id`. Generic type parameters with interface constraints (`.requires_iface`). Native function binding with sig strings supporting `array<T>`, `map<K,V>`, `const T&`, default args, variadic, overloading by arity / types / element type. Hot reload, serialization, introspection, debug hooks, sandboxing, permission gating.

### Current Benchmark

Median of 11 runs, Windows x64. Six workloads: `fib(35)`, `sum 100M`, `nested 2K²`, `sieve 1M`, `collatz 100K`, `bubble 3K`. Pure execution time (script-internal `time_ms()`).

| Benchmark    | Rust -O | C++ -O2 | **Enma** | Node V8 | LuaJIT | Lua 5.4 | AngelScript |
| ------------ | ------- | ------- | -------- | ------- | ------ | ------- | ----------- |
| fib(35)      | 14.9    | 11.3    | **26**   | 44.9    | 50     | 316     | 444.8       |
| sum 100M     | 21.5    | 9.1     | **20**   | 52.9    | 51     | 208     | 537.8       |
| nested 2K²   | 0.8     | 9.9     | **1**    | 2.5     | 2      | 8       | 19.1        |
| sieve 1M     | 0.6     | 10.9    | **6**    | 4.5     | 6      | 30      | 30.4        |
| collatz 100K | 6.5     | 10.2    | **25**   | 13.3    | 31     | 147     | 156.7       |
| bubble 3K    | 1.7     | 9.6     | **11**   | 5.0     | 2      | 55      | 159.8       |
| **Total**    | 46.0    | 61.0    | **89**   | 123.1   | 142    | 764     | 1348.6      |

Matches or beats LuaJIT on 5/6 workloads (only bubble trails).

### Safety

**Fault trapping:** Null deref, invalid memory access caught via SIGSEGV/SEH and mapped to source. Host doesn't crash.

**Execution budget:** Per-loop instruction count via `set_budget()`. Prevents infinite loops.

**Memory budget:** Cap total allocations with `set_memory_budget()`.

**Permission gating:** `PERM_FFI` controls `[[dll(...)]]` access; `PERM_FILE` controls file-addon calls; per-method permissions on registered types.

**Sandboxing:** Scripts only see functions explicitly registered by the host.

**Type verification:** Native sig types checked at script call sites: wrong arg type, wrong struct identity, wrong enum, or wrong container element type are all rejected at compile time. Const correctness for parameters and methods. Implicit conversion via registered `convert_from` functions.

**Memory model:** Deterministic. Structs stack-allocated by default; `new T(...)` for explicit heap. Destructors run at scope exit (normal flow, exception unwind, JIT fault unwind). No tracing GC. Escape patterns (return pointer to stack struct, store to struct-typed global, closure capturing a stack struct) are compile errors.

**Thread safety:** Per-thread TLS, independent engines, concurrent contexts from same module. Tested under ASAN/TSAN with 32+ threads.

### Getting Started

Writing scripts: [basics](/enma/language-guide/basics.md)

Embedding: [SDK Quick Start](/enma/sdk-guide/quick-start.md)


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/readme.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
