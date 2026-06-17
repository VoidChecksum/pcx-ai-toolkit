> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/native-functions.md).

# Native Functions

Expose host functions to scripts. The sig string drives compile-time type checking at every call site and per-arg ABI routing at the native boundary.

## Registering a Function

Declare the native with real types. `register_native` passes the function through directly - the Win64 ABI placement follows the signature (int-like args in `rcx`/`rdx`/`r8`/`r9`, floats in `xmm0-3`, args 5+ on stack, narrow-int returns sign/zero-extended).

```cpp
int32_t add(int32_t a, int32_t b) { return a + b; }
register_native(e, "int32 add(int32, int32)", (void*)&add);
```

## Attaching a Description

Every `register_native` overload takes an optional trailing `description` string, surfaced via `extract_documentation` and `extract_intellisense` (see [Introspection](sdk-introspection.md)). Use it for natives whose behavior isn't obvious from the signature alone.

```cpp
register_native(e, "int64 log(string msg)", (void*)&log,
    0 /* no permissions */,
    "print a message to the host's stdout");
```

Descriptions are optional. If omitted, the entry still appears in doc output without a comment.

```cpp
double lerp(double a, double b, double t) { return a + (b - a) * t; }
register_native(e, "float64 lerp(float64, float64, float64)", (void*)&lerp);
```

Script usage:

```cpp
int32 r = add(10, 20);              // 30
float64 m = lerp(0.0, 100.0, 0.5);  // 50.0
```

Any arity, any type mix (ints / bools / chars / floats / doubles / pointers / enums / registered structs / `string` / `array` / `map`) works. The native is called directly - no int64 bit-casting, no trampolines.

There's also a template form `register_typed<&fn>(e, sig)` - equivalent to `register_native(e, sig, (void*)&fn)` but captures the function as a template parameter so the binding is one token. Pick whichever reads better.

## Supported Types

Keywords resolve to the built-in type IDs:

| Category    | Keywords                                                                                 |
| ----------- | ---------------------------------------------------------------------------------------- |
| Integers    | `int8`, `int16`, `int32`, `int64`, `uint8`, `uint16`, `uint32`, `uint64`, `char`, `bool` |
| Floats      | `float32`, `float`, `float64`, `double`                                                  |
| Strings     | `string`, `wstring`                                                                      |
| Containers  | `array`, `map`                                                                           |
| Generic     | `struct`, `class`, `pointer`, `lambda`, `function`, `void`                               |
| Placeholder | `element` (in container-method signatures)                                               |

Structs, enums, and types registered via `struct_builder`, `type_builder`, or `enum_builder` are also recognized by name - see the [Custom Types in Signatures](#custom-types-in-signatures) section below.

## Floats

Declare your C function with `float` or `double`. The JIT routes those args through xmm regs per Win64 ABI, and reads float returns from xmm0:

```cpp
double my_sqrt(double x) { return std::sqrt(x); }
register_native(e, "float64 my_sqrt(float64)", (void*)&my_sqrt);
```

```cpp
float mix(float a, float b, float t) { return a + (b - a) * t; }
register_native(e, "float32 mix(float32, float32, float32)", (void*)&mix);
```

Mix int and float args freely - placement is per-position:

```cpp
void draw(int32_t id, double x, double y, int32_t color) { ... }
register_native(e, "void draw(int32, float64, float64, int32)", (void*)&draw);
//                            ^rcx    ^xmm1    ^xmm2     ^r9
```

## Strings

String arguments pass as `const char*`:

```cpp
void greet(const char* s) {
    printf("Hello, %s!\n", s);
}
register_native(e, "void greet(string)", (void*)&greet);
```

## No-Parameter Functions

```cpp
int64_t get_time() {
    return static_cast<int64_t>(time(nullptr));
}
register_native(e, "int64 get_time()", (void*)&get_time);
```

## Custom Types in Signatures

After registering a struct, enum, or `type_builder` type, you can reference it by name in subsequent registration calls. Pass struct args as typed pointers:

```cpp
struct_builder(e, "proc_t")
    .field("pid",      type_id::t_int64)
    .field("priority", type_id::t_int64);

struct proc_t { int64_t pid; int64_t priority; };

int64_t inspect_proc(proc_t* p) {
    return p->pid;
}

register_native(e, "int64 inspect_proc(proc_t)", (void*)&inspect_proc);
```

Script usage:

```cpp
proc_t p;
p.pid = 42;
int64 x = inspect_proc(p);  // 42
```

Passing a different struct is a compile error:

```cpp
item_t i;
inspect_proc(i);   // error: inspect_proc() parameter 'arg0' expects proc_t, got item_t
```

The sig accepts `T`, `T&`, `T*` with optional parameter name. The native always receives a pointer:

| Signature | Semantics    | Native sees                              |
| --------- | ------------ | ---------------------------------------- |
| `T`       | by-value     | pointer to a copy of the caller's struct |
| `T&`      | by-reference | pointer to the caller's struct           |
| `T*`      | by-pointer   | pointer to the caller's struct           |

Mutations through `T&` or `T*` are visible to the caller; mutations through bare `T` are not.

```cpp
int64_t mutate_proc(proc_t* p) {
    p->pid += 100;
    return p->pid;
}
```

```c
// sig "int64 mutate_proc(proc_t)" by-value: p.pid stays 5
// sig "int64 mutate_proc(proc_t&)" by-ref: p.pid becomes 105
proc_t p;  p.pid = 5;
int64 r = mutate_proc(p);
```

By-value copies the struct fields at the call site (one load/store per 8 bytes).

Enums resolve to `int64` at the ABI level, but the compiler enforces enum identity at call sites:

```cpp
enum_builder(e, "Priority")
    .value("Low",    1)
    .value("Medium", 5)
    .value("High",  10);
enum_builder(e, "Color")
    .value("Red", 0).value("Green", 1).value("Blue", 2);

register_native(e, "int64 enum_double(Priority)", (void*)&enum_double_fn);
```

```cpp
int64 x  = enum_double(Priority::High);   // OK → 20
int64 y  = enum_double(42);               // compile error: expects Priority, got int32
int64 z  = enum_double(Color::Red);       // compile error: expects Priority, got Color

Priority p = Priority::Medium;
int64 w  = enum_double(p);                // OK, local is typed Priority
```

Raw ints and values from a *different* enum are rejected at compile time. Declaring a local with the enum type (`Priority p = ...;`) preserves the enum identity through the rest of the scope.

Script-side enums work too:

```cpp
enum State { Idle = 0, Running = 1, Done = 2 }
```

```cpp
register_native(e, "int64 on_state(State)", (void*)&on_state);
```

The same call-site checks fire whether the enum was registered via `enum_builder` or declared in the script.

## Delegate-Typed Parameters

Script-declared delegates work directly in native signatures:

```cpp
delegate int64 Handler(int64 x);
```

```cpp
int64_t take_handler(void* fn_ptr) {
    return fn_ptr != nullptr ? 1 : 0;
}

register_native(e, "int64 take_handler(Handler)", (void*)&take_handler);
```

```cpp
int64 doubler(int64 x) { return x * 2; }
int32 main() {
    Handler h = doubler;
    return take_handler(h);   // 1
}
```

Delegate names resolve at IR-build time (after the script is parsed), so registrations that reference delegates declared *later* in the script still work. The compiler will reject mismatched arg types at the call site (`take_handler("hello")` → compile error).

## Overloading

Register two natives with the same name but different **arities** or different **argument types** and they coexist:

```cpp
register_native(e, "int64 combine(int64)",                       (void*)&combine_1);
register_native(e, "int64 combine(int64, int64)",                (void*)&combine_2);
register_native(e, "int64 combine(int64, int64, int64)",         (void*)&combine_3);

register_native(e, "int64 pairsum(int64, int64)",                (void*)&int_sum);
register_native(e, "float64 pairsum(float64, float64)",          (void*)&float_sum);
```

```cpp
combine(5);            // → combine_1
combine(3, 4);         // → combine_2
combine(1, 2, 3);      // → combine_3
combine(1, 2, 3, 4);   // compile error: no overload for 4 arg(s)

pairsum(3, 4);         // → int_sum (int args → int overload)
pairsum(1.5, 2.5);     // → float_sum (float args → float overload)
pairsum("a", "b");     // compile error: no overload matches string
```

Resolution rules:

1. **Exact-type mangle**: first try `name$<arity>$<t1>$<t2>...`; if it exists, use it.
2. **Scored compatible match**: otherwise iterate overloads with matching arity; pick the one with the lowest conversion score. Same-category conversions (int→int64, float→float64) score 1 per arg; cross-category (int→float) scores 4.
3. **Ambiguous tie**: if two overloads have the same score, emit *"call is ambiguous across overloads"* and fail to compile.
4. **No compat match**: emit *"has no overload matching N argument(s) with given types"*.

Same arity + same types = the second registration clobbers the first.

## Typed Containers (`array<T>` and `map<K, V>`)

Specify element types in container args and returns:

```cpp
register_native(e, "int64 sum_ints(array<int64>)",           (void*)&sum_ints);
register_native(e, "int64 lookup(map<string, int64>)",       (void*)&lookup);
register_native(e, "array<int64> make_ints()",               (void*)&make_ints);
```

Script-side mismatches reject at compile:

```cpp
int64[] xs;     sum_ints(xs);    // OK
string[] ys;    sum_ints(ys);    // error: expects array<int64>, got array<string>
map<string, int64> m;  lookup(m);   // OK
map<int64, int64> n;   lookup(n);   // error: expects map<string, int64>, got map<int64, int64>

string[] bad = make_ints();      // error: returns array<int64>, cannot assign to array<string>
int64[] good = make_ints();      // OK
```

Bare `array` / `map` (no `<...>`) accepts any element type, useful for generic helpers. Overload resolution: `process(array<int>)` and `process(array<string>)` coexist and dispatch by caller's element type.

The native receives an `int64` handle. Use the addon array helpers declared in `sdk/addons/array.h` (length, get, set, push, etc.) to read or mutate.

## `const` Parameters

Mark a param as read-only:

```cpp
register_native(e, "int64 read_pid(const proc_t)", (void*)&read_pid);
```

Script-side: assigning to a field of a `const` arg inside that fn rejects at compile (`cannot assign through const ...`). Combine with `const T&` for non-mutating reference args.

## Variadic Natives

End the arg list with `...` to accept any number of additional args:

```cpp
int64_t vsum(int64_t argc, int64_t* argv) {
    int64_t s = 0;
    for (int64_t i = 0; i < argc; ++i) s += argv[i];
    return s;
}

register_native(e, "int64 vsum(...)", (void*)&vsum);
```

```cpp
vsum(1, 2, 3, 4, 5);   // 15
vsum();                // 0, no args
```

The native function takes `(int64_t argc, int64_t* argv)`. `argv` is a heap buffer of raw int64 values for every passed arg (including formal-arg prefix). Freed after the call.

Formal args may precede `...`:

```cpp
register_native(e, "int64 vlog(string fmt, ...)", (void*)&vlog);
```

```cpp
vlog("hello");              // argc=1, argv[0]=string_ptr("hello")
vlog("%d + %d", 3, 4);      // argc=3, argv=[fmt_ptr, 3, 4]
vlog();                     // compile error: expects at least 1 arg
```

The formal args are still type-checked. The variadic portion accepts any value and is always int64-boxed - use `memcpy(&d, &argv[i], 8)` to recover float args as doubles from the raw buffer.

## Default Arguments

Give natives default values via `= literal` in the sig:

```cpp
register_native(e, "int64 sum3(int64 a, int64 b = 10, int64 c = 100)", (void*)&sum3);
```

```c
sum3(1);         // b = 10, c = 100  → 111
sum3(1, 2);      // c = 100          → 103
sum3(1, 2, 3);   // all explicit     → 6
sum3();          // error: expects 1-3 argument(s), got 0
```

Int and float literals are supported (e.g. `int64 n = 42`, `float64 f = 3.14`). All defaulted args must come after all required args.

## Returning a Struct by Value

Struct returns write into a caller-supplied return slot: the native takes a hidden first arg pointing at the caller's buffer:

```cpp
struct proc_t { int64_t pid; int64_t priority; };

void make_proc(proc_t* out) {
    out->pid = 42;
    out->priority = 7;
}

register_native(e, "proc_t make_proc()", (void*)&make_proc);
```

```c
proc_t p = make_proc();   // Enma allocates the buffer, native fills it
int64  x = p.pid;         // 42
```

The first native arg is the return-slot pointer (matches the standard ABI for structs larger than a register).

## Permission-Gated Functions

Restrict a function to scripts that have specific permissions:

```cpp
register_native(e, "int64 read_memory(int64, int64, int64)", (void*)&rpm_fn, PERM_FFI);
```

On a `type_builder` method, chain `.permission(...)`:

```cpp
type_builder(e, "socket_t", ...)
    .method("int64 send_raw(int64)", (void*)&send_raw_fn).permission(PERM_FFI)
    .finish();
```

Calling a permission-gated function from a script without the matching bit in `set_permissions(engine, ...)` is a compile error.

## Registration-Time Validation

If the sig string references a type that hasn't been registered (typo like `proc_T` for `proc_t`), Enma prints a warning to stderr at registration time:

```cpp
[enma] warning: arg 0 'proc_T' in sig 'int64 inspect(proc_T)' - unresolved type; it will accept any value
```

Catches type-name typos at engine setup rather than at script call time.

## Compile-Time Syntax Validation. `ENMA_SIG(...)`

For structural errors in the sig string (missing paren, empty arg slot, illegal characters), wrap the literal in `ENMA_SIG(...)` to fail at **host compile time** via a `consteval` check:

```cpp
register_native(e, ENMA_SIG("int64 add(int64, int64)"), (void*)&add_fn);  // compiles
register_native(e, ENMA_SIG("int64 bad(,)"),            (void*)&bad_fn);  // static_assert fires
register_native(e, ENMA_SIG("int64 no_close("),         (void*)&fn);      // static_assert fires
```

The checker catches:

* Missing `(` or `)`, or trailing junk after `)`.
* Empty function name (`"() foo"`).
* Empty arg segments: `"bad(,)"`, `"bad(int,,int)"`.
* Non-identifier characters (anything outside `[A-Za-z0-9_&*=.+-]`).

`...` is accepted as a variadic arg. Type-name typos (`"int64 f(int6q)"`) aren't caught here - that's the registration-time stderr warning above. Use `ENMA_SIG` for the syntax-only layer.

## Invoking Script Closures from Background Threads

Native code that wants to call a script-side closure from a thread that isn't driving `execute()` / `call()` needs to set up per-thread state first. Use `execution_scope`:

```cpp
#include "sdk.h"
using namespace enma;

void worker_tick(context_t* ctx, int64_t fn_handle, int64_t user_data) {
    execution_scope scope(ctx);   // sets up tls heap/state/engine/... for this thread
    // ...invoke the closure via inline-asm trampoline or SDK helper...
}
```

See the [Invoking Script Closures from Background Threads](sdk-custom-addons.md#invoking-script-closures-from-background-threads) section in the custom-addons guide for the full trampoline pattern.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/native-functions.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
