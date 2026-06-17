> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/llms-sdk.md).

# LLMS - SDK

Enma is a full-module AOT and JIT-compiled scripting language you embed in a native host. The SDK is one header plus a static library. Everything lives in namespace `enma`.

## Ship Layout

```cpp
shipped/
├── include/sdk.h
├── enma.h                          (umbrella header)
├── windows/enma_x64static_mt.lib   (/MT static CRT - match your project's CRT flag)
├── windows/enma_x64static_md.lib   (/MD dynamic CRT)
├── linux/libenma.a                 (Linux)
└── addons/em_addon_*.cpp           (source; reference / customization only)
```

Build: link the lib that matches your project's `/MT` or `/MD` flag - mixing them produces a `RuntimeLibrary` mismatch at link. All 17 built-in addons are bundled into both `.lib` variants, so a single link is enough. The standalone `addons/em_addon_*.cpp` files still ship if you want to read, modify, or build a custom subset.

## Minimal Embed

```cpp
#include "sdk.h"
using namespace enma;

int main() {
    engine_t* e = create();
    register_all_addons(e);
    set_optimize(e, true);

    const char* src = R"(
        int32 main() {
            println("hi");
            return 42;
        }
    )";
    module_t* mod = compile(e, src, std::strlen(src), "hi.em");
    if (!mod) {
        auto err = last_error(e);
        fprintf(stderr, "compile: %s at %s:%d\n", err.message.c_str(), err.file.c_str(), err.line);
        destroy(e);
        return 1;
    }

    context_t* ctx = create_context(mod);
    if (!execute(ctx, "main")) {
        auto err = last_error(e);
        fprintf(stderr, "run: %s\n", err.message.c_str());
    }
    int64_t r = return_value(ctx);

    destroy_context(mod, ctx);
    module_destroy(mod);
    destroy(e);
    return (int)r;
}
```

Lifetime order: engine → module → context. Destroy in reverse.

## Engine Lifecycle

```cpp
engine_t* create();
void      destroy(engine_t* e);

void set_optimize(engine_t* e, bool enabled);    // IR opts + JIT optimization
void set_debug(engine_t* e, bool enabled);       // enables source maps, stack traces
void define(engine_t* e, const char* name, const char* value);  // preprocessor
void add_include_path(engine_t* e, const char* path);   // for #include
void add_module_path(engine_t* e, const char* path);    // for import
void set_permissions(engine_t* e, uint32_t flags);      // PERM_FFI | PERM_FILE
uint32_t get_permissions(engine_t* e);

// Optional: override how #include / import resolve paths
using resolve_fn = bool(*)(const char* path, char** out_data, size_t* out_len, void* userdata);
void set_include_resolver(engine_t* e, resolve_fn fn, void* userdata);
void set_import_resolver(engine_t* e, resolve_fn fn, void* userdata);
```

Permissions:

```cpp
inline constexpr uint32_t PERM_FFI  = 0x01;   // gates [[dll(...)]]
inline constexpr uint32_t PERM_FILE = 0x02;   // gates file addon
```

## Compilation

```cpp
module_t* compile(engine_t* e, const char* src, size_t len, const char* filename);
module_t* compile_file(engine_t* e, const char* path);
void      module_destroy(module_t* m);

// Hot replace source without tearing down contexts:
bool      reload(module_t* m, const char* src, size_t len, const char* filename);

// Binary serialization. keep_debug=false strips source_map + debug_functions
// (drops uploader's source paths from the .emb for marketplace publishing);
// body is XOR-obfuscated with per-file salt regardless.
bool      serialize(module_t* m, std::vector<uint8_t>& out, bool keep_debug = true);
module_t* deserialize(engine_t* e, const uint8_t* data, size_t len);

// Multi-module linking:
module_t* link(engine_t* e, const char** names, module_t** modules, uint32_t count);
```

Compile errors surface via `last_error(e)`.

## Execution

```cpp
context_t* create_context(module_t* m);
void       destroy_context(module_t* m, context_t* ctx);

bool execute(context_t* ctx, const char* fn_name);                                     // no args
bool call(context_t* ctx, const char* fn_name, const int64_t* args, uint32_t count);   // with args

int64_t     return_value(context_t* ctx);   // integer result
const char* return_string(context_t* ctx);  // string result
double      return_float(context_t* ctx);   // float result (bit-cast from int64 slot)

int64_t alloc_string(context_t* ctx, const char* str);  // alloc scripts-visible string
void*   fn_address(module_t* m, const char* name);       // raw JIT fn ptr (for direct call)
```

All args are `int64_t`. Floats bit-cast:

```cpp
double d = 3.14;
int64_t a;
std::memcpy(&a, &d, 8);
call(ctx, "set_value", &a, 1);
```

Return types are read via `return_value` / `return_string` / `return_float` based on the declared script return type.

`execute()` / `call()` return `false` on any JIT-thrown hardware fault (null deref, divide-by-zero, OOB array access, stack overflow, double-delete). The engine remains usable — call `last_error(engine)` for the message + file:line, or `__enma_jit_get_last_fault(&code, &rip, &address, &access_type)` for the raw OS exception data. dtors registered for value-struct locals on the faulting frame run via the cleanup-stack unwind, so heap resources don't leak. Process stays alive; the host can retry, log, or abort just that engine.

## Context Userdata (16 slots)

Slot 0 is shared between the single-slot and multi-slot accessors.

```cpp
void  set_userdata(context_t* ctx, void* data);                        // slot 0
void* get_userdata(context_t* ctx);                                     // slot 0
void  set_userdata_at(context_t* ctx, uint32_t slot, void* data);       // slots 0-15
void* get_userdata_at(context_t* ctx, uint32_t slot);
```

Out-of-range slots: no-op on set, `nullptr` on get. Multiple addons coexist by picking distinct slots.

## Globals

```cpp
bool     set_global(module_t* m, const char* name, int64_t value);
int64_t  get_global(module_t* m, const char* name);
bool     has_global(module_t* m, const char* name);
int64_t* get_global_ptr(module_t* m, const char* name);   // direct pointer to the slot
void     list_globals(module_t* m, std::vector<std::string>& names, std::vector<int64_t>& values);
```

## Native Function Registration (three forms)

**Typed (recommended, arity 0-6):**

```cpp
int32_t add(int32_t a, int32_t b) { return a + b; }
register_typed<&add>(e, "int32 add(int32, int32)");
```

The trampoline is generated at compile time. Supports int8/16/32/64, uint\*, float/double, bool, char, pointer, enum.

**Sig-string form:**

```cpp
int64_t my_fn(int64_t a, int64_t b) { return a + b; }
register_native(e, "int64 my_fn(int64, int64)", (void*)my_fn);
```

**Full descriptor form:**

```cpp
native_param params[] = {
    { "a", type_id::t_int32 },
    { "b", type_id::t_int32 },
};
register_native(e, "add", (void*)my_fn, type_id::t_int32, params, 2);
```

**Permissions:** `register_typed<&fn>(e, sig, PERM_FFI)` - script fails to compile the call without matching permission.

**Compile-time sig check:**

```cpp
register_native(e, ENMA_SIG("int64 foo(int64, int64)"), (void*)foo);
// Malformed sigs fail as static_asserts at native compile time.
```

**Sig syntax cheatsheet:**

| Pattern                              | Meaning                                                     |
| ------------------------------------ | ----------------------------------------------------------- |
| `int64 name(int64, float64)`         | Basic                                                       |
| `int64 name(int64 a, int64 b)`       | With param names (shows in error messages)                  |
| `int64 name(int64 a = 10)`           | Default argument                                            |
| `int64 name(...)`                    | Variadic - native takes `(int64 argc, int64* argv)`         |
| `int64 name(string fmt, ...)`        | Required + variadic                                         |
| `array name()` / `array<int> name()` | Typed array return                                          |
| `map<string,int64> name()`           | Typed map return                                            |
| `void name(const proc_t p)`          | Read-only param                                             |
| `void name(const vec3& v)`           | Pass-by-reference                                           |
| `void name(out vec3 v)`              | Write-only reference                                        |
| `struct_t name()`                    | Struct return — hidden first arg is the return-slot pointer |

## Overloading

Same name, different arities or types:

```cpp
register_native(e, "int64 pair(int64, int64)",      (void*)pair_ii);
register_native(e, "int64 pair(float64, float64)",  (void*)pair_ff);
register_native(e, "int64 pair(string, string)",    (void*)pair_ss);
```

Overload resolution picks at script call site by arg types. Ambiguous calls = compile error.

## Type Registration (`type_builder`)

Full fluent API for exposing a native type to scripts.

```cpp
type_builder(e, "vec3_t", type_id::t_struct)
    .field("x", offsetof(vec3_t, x), type_id::t_float64)
    .field("y", offsetof(vec3_t, y), type_id::t_float64)
    .field("z", offsetof(vec3_t, z), type_id::t_float64)

    .factory_typed<&vec3_create>(3)
    .destructor_typed<&vec3_destroy>()

    .method_typed<&vec3_length_sq>("float64 length_sq()")
    .method_typed<&vec3_scale>("vec3_t scale(float64)")

    .property_typed<&get_magnitude>("magnitude", type_id::t_float64)       // read-only
    .property_typed<&get_x, &set_x>("xp", type_id::t_float64)              // read/write

    .subscript_typed<&bag_get, &bag_set>()                                  // [idx] access

    .bin_add_typed<&vec3_add>()
    .bin_sub_typed<&vec3_sub>()
    .bin_mul_typed<&vec3_mul>()
    .bin_eq_typed<&vec3_eq>()
    .compare_typed<&vec3_compare>()

    .copy_typed<&vec3_copy>()
    .hash_typed<&vec3_hash>()

    .iterable((void*)vec3_len, (void*)vec3_at)
    .convert(type_id::t_int64, (void*)vec3_from_int)

    .pure_methods()      // methods don't retain receiver (container hint)
    .pure_args()         // methods don't retain args (value-type hint)
    .permission(PERM_FILE);
// `.finish()` is implicit when the builder goes out of scope; call explicitly
// if you need to chain `type_reg_t*` lookups right after.
```

### Value-type opt-in (vec3, color, quat, etc.)

Three hooks turn a typereg into a value type — non-escaping locals stack-allocate, `T[]` stores values inline, property reads compile to direct loads:

```cpp
type_builder(e, "vec3_t", type_id::t_int64)
    .value_type(sizeof(vec3_t))                       // inline storage size
    .factory_in_place((void*)&vec3_construct)         // int64_t fn(int64_t dst, args...)
    .inline_property("x", (void*)&vec3_get_x, (void*)&vec3_set_x,
                     type_id::t_float64, offsetof(vec3_t, x));
```

`factory_in_place` writes directly into the buffer (`dst` is stack or heap depending on escape analysis). `inline_property` swaps the `call_native` getter/setter for `op_load_field` / `op_store_field` at the given offset — use only when the native impl is a trivial field read.

vec2/vec3/vec4/quat in the shipped addons all opt in.

### Hook Reference

| Hook                                                                         | Typed form                                            | Signature (native)                            | Script usage                                                                                                                                                           |
| ---------------------------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.field(n, off, t)`                                                          | -                                                     | -                                             | `x.field`                                                                                                                                                              |
| `.method(sig, fn)`                                                           | `.method_typed<&Fn>(sig)`                             | `R(U*, args...)`                              | `x.method(args)`                                                                                                                                                       |
| `.property(n, g, s, t)`                                                      | `.property_typed<&Get, &Set>(n, t)`                   | `T(U*)` / `void(U*, T)`                       | `x.prop`, `x.prop = v`                                                                                                                                                 |
| `.subscript(g, s, er?)`                                                      | `.subscript_typed<&Get, &Set>(er?)`                   | `T(U*, int64)` / `void(U*, int64, T)`         | `x[i]`, `x[i] = v`                                                                                                                                                     |
| `.iterable(len, get)`                                                        | -                                                     | `int64(U*)` / `T(U*, int64)`                  | `for (v : x) { }`                                                                                                                                                      |
| `.kv_iterable(len, k, v)`                                                    | -                                                     | `int64(U*)` / `K(U*, int64)` / `V(U*, int64)` | `for (k, v : x) { }`                                                                                                                                                   |
| `.factory(fn, N)`                                                            | `.factory_typed<&Fn>(N)`                              | `U*(args...)`                                 | `T x = T(args)`                                                                                                                                                        |
| `.destructor(fn)`                                                            | `.destructor_typed<&Fn>()`                            | `void(U*)`                                    | scope-drop                                                                                                                                                             |
| `.init_push(fn)`                                                             | -                                                     | `void(U*, val)`                               | brace-init                                                                                                                                                             |
| `.bin_add(fn)` ... `_mod`                                                    | `.bin_*_typed<&Fn>()`                                 | `U*(U*, U*)`                                  | `x + y`, etc.                                                                                                                                                          |
| `.bin_eq/lt/gt/le/ge`                                                        | `.bin_*_typed<&Fn>()`                                 | `bool(U*, U*)`                                | `x == y`, etc.                                                                                                                                                         |
| `.compare(fn)`                                                               | `.compare_typed<&Fn>()`                               | `int64(U*, U*)` (-1/0/+1)                     | three-way, comparison fallback                                                                                                                                         |
| `.bin_*_assign(fn)` (arith)                                                  | `.bin_*_assign_typed<&Fn>()`                          | `U*(U*, U*)`                                  | `x += y`, etc. Falls back to `bin_*` if unset                                                                                                                          |
| `.bit_and_assign / bit_or_assign / bit_xor_assign / shl_assign / shr_assign` | -                                                     | `U*(U*, U*)`                                  | `x &= y`, `x \|= y`, `x ^= y`, `x <<= y`, `x >>= y`. Falls back to the matching `bit_*` / `shl` / `shr` if unset                                                       |
| `.increment / decrement`                                                     | `.increment_typed<&Fn>()` / `.decrement_typed<&Fn>()` | `U*(U*)`                                      | `++x` (prefix) / `--x`. Also handles postfix when no separate `post_*` is registered                                                                                   |
| `.post_increment / post_decrement`                                           | -                                                     | `U*(U*)`                                      | `x++` / `x--`. C++ int-dummy-param convention; declare for distinct postfix semantics                                                                                  |
| `.unary_neg / unary_bit_not`                                                 | `.unary_*_typed<&Fn>()`                               | `U*(U*)`                                      | `-x`, `~x`                                                                                                                                                             |
| `.unary_log_not(fn)`                                                         | -                                                     | `bool(U*)`                                    | `!x`                                                                                                                                                                   |
| `.unary_deref(fn)`                                                           | -                                                     | `T(U*)` (T = whatever you return)             | `*x` smart-pointer-style. Pointer deref of `T*` keeps memberwise-copy semantics                                                                                        |
| `.bit_and / or / xor / shl / shr`                                            | `.bit_*_typed<&Fn>()` / `.shl_typed<&Fn>()`           | `U*(U*, U*)`                                  | `&`, `\|`, `^`, `<<`, `>>`                                                                                                                                             |
| `.call(fn)`                                                                  | -                                                     | variadic                                      | `obj(args...)` — function-call. Pull args via the standard native ABI. Useful for `m(i, j)` matrix element access                                                      |
| `.arrow(fn)`                                                                 | -                                                     | `void*(U*)`                                   | `obj->member` — smart-pointer arrow. Returns a pointer the IR resolves the following `member` against                                                                  |
| `.copy_assign(fn)`                                                           | -                                                     | `void(U*, U*)`                                | `b = a;` for already-constructed `b`. Lets the type release b's old resources before adopting a's                                                                      |
| `.compare(fn)`                                                               | `.compare_typed<&Fn>()`                               | `int64(U*, U*)` (-1/0/+1)                     | Three-way `<=>`. Single registration auto-derives all six comparison ops                                                                                               |
| `.copy(fn)`                                                                  | `.copy_typed<&Fn>()`                                  | `U*(U*)`                                      | called on `T b = a;` (copy ctor)                                                                                                                                       |
| `.hash(fn)`                                                                  | `.hash_typed<&Fn>()`                                  | `int64(U*)`                                   | map keys, hash\_set                                                                                                                                                    |
| `.serialize(fn)`                                                             | -                                                     | `int64(U*) -> char*`                          | reflection-driven                                                                                                                                                      |
| `.deserialize(fn)`                                                           | -                                                     | `U*(int64 str_ptr)`                           | reflection-driven                                                                                                                                                      |
| `.convert(from_t, fn)`                                                       | -                                                     | `U*(from_T)`                                  | implicit conversion *INTO* this type from `from_T`                                                                                                                     |
| `.cast_to(target_t, fn)`                                                     | -                                                     | `T(U*)`                                       | implicit conversion *FROM* this type to `target_t`. Mirror of `.convert()`. Fires on `cast<T>(obj)` and at variable init when target is a primitive or registered type |
| `.implements(name)`                                                          | -                                                     | -                                             | marks iface compliance                                                                                                                                                 |
| `.as_interface()`                                                            | -                                                     | -                                             | marks type as interface                                                                                                                                                |
| `.generic_param(name)`                                                       | -                                                     | -                                             | template param `T`                                                                                                                                                     |
| `.requires_iface(p, i)`                                                      | -                                                     | -                                             | constraint on `p`                                                                                                                                                      |
| `.pure_methods()`                                                            | -                                                     | -                                             | retention hint (container)                                                                                                                                             |
| `.pure_args()`                                                               | -                                                     | -                                             | retention hint (value-type)                                                                                                                                            |
| `.captures_arg(idx)`                                                         | -                                                     | -                                             | arg `idx` outlives call                                                                                                                                                |
| `.permission(flags)`                                                         | -                                                     | -                                             | `PERM_FFI` / `PERM_FILE`                                                                                                                                               |

### `type_builder` vs `struct_builder`

`struct_builder` is the lightweight form for data-only types (no ctor, no methods):

```cpp
struct_builder(e, "point_t")
    .field("x", type_id::t_int64)
    .field("y", type_id::t_int64)
    .packed()                 // optional; sets packed layout
    .finish();
```

`enum_builder` for enums:

```cpp
enum_builder(e, "log_level")
    .value("DEBUG", 0)
    .value("INFO",  1)
    .value("WARN",  2)
    .value("ERROR", 3)
    .finish();
```

## Interfaces

Native:

```cpp
type_builder(e, "Stream", type_id::t_int64).as_interface();

type_builder(e, "file_stream", type_id::t_int64)
    .factory_typed<&file_create>(1)
    .destructor_typed<&file_destroy>()
    .method_typed<&file_write>("int64 write(string)")
    .implements("Stream")
    .finish();
```

A native with a `Stream` parameter accepts any implementer. The compiler auto-injects the concrete `type_id` before the value at the ABI, so the native signature is `(int64 concrete_tid, int64 value, ...)`.

Resolve a method pointer at runtime:

```cpp
void* fn = enma::interface_method_fn(active_engine(), (type_id)tid, "write");
```

**Script-level iface dispatch:**

```c
Stream s = file_stream("a.txt");   // concrete -> iface
int64 n = s.write("hi");           // dispatches to file_stream.write
s = mem_stream();
int64 m = s.write("hi");           // dispatches to mem_stream.write
```

Each iface-typed local carries a hidden companion int64 holding the concrete tid, updated on every assignment. Runtime resolves fn\_ptr per call.

## Generics + Constraints

```cpp
type_builder(e, "hash_set", type_id::t_int64)
    .generic_param("T")
    .requires_iface("T", "Hashable")    // optional constraint
    .factory_typed<&hset_create>(0)
    .destructor_typed<&hset_destroy>()
    .method("void add(T)", (void*)hset_add)
    .method("bool contains(T)", (void*)hset_contains)
    .finish();
```

Script binds at var-decl:

```c
hash_set<int64> s;   // T = int64
s.add(42);           // checked against T
```

Violations rejected at compile time (wrong type, or T doesn't implement the constrained interface).

## Reflection (`type_reg_t`)

```cpp
const type_reg_t* find_type_reg(engine_t* e, type_id id);
const type_reg_t* find_type_reg_by_name(engine_t* e, const char* name);

const char* type_reg_name(const type_reg_t*);
type_id     type_reg_id(const type_reg_t*);
void*       type_reg_factory(const type_reg_t*);
uint32_t    type_reg_factory_param_count(const type_reg_t*);
void*       type_reg_dtor(const type_reg_t*);
void*       type_reg_copy(const type_reg_t*);
void*       type_reg_hash(const type_reg_t*);
void*       type_reg_compare(const type_reg_t*);
void*       type_reg_op_eq(const type_reg_t*);
void*       type_reg_serialize(const type_reg_t*);
void*       type_reg_deserialize(const type_reg_t*);
void*       type_reg_convert_from(const type_reg_t*, type_id from);
void*       type_reg_method(const type_reg_t*, const char* name);
uint32_t    type_reg_method_count(const type_reg_t*);
const char* type_reg_method_name_at(const type_reg_t*, uint32_t idx);

bool        type_reg_implements(const type_reg_t*, const char* iface);
uint32_t    type_reg_implements_count(const type_reg_t*);
const char* type_reg_implements_at(const type_reg_t*, uint32_t idx);
bool        type_reg_is_interface(const type_reg_t*);

uint32_t    type_reg_generic_param_count(const type_reg_t*);
const char* type_reg_generic_param_at(const type_reg_t*, uint32_t idx);
uint32_t    type_reg_generic_constraint_count(const type_reg_t*);
const char* type_reg_generic_constraint_param_at(const type_reg_t*, uint32_t idx);
const char* type_reg_generic_constraint_iface_at(const type_reg_t*, uint32_t idx);

void*       interface_method_fn(engine_t*, type_id concrete, const char* method);

bool     has_type(engine_t*, const char* name);
uint32_t list_types(engine_t*, std::vector<std::string>& out);
bool     has_struct(engine_t*, const char* name);
uint32_t list_structs(engine_t*, std::vector<std::string>& out);
```

All accessors are null-safe. `nullptr` returns `0` / `""` / `false`.

## Introspection

```cpp
bool     has_function(module_t*, const char* name);
uint32_t function_param_count(module_t*, const char* name);
uint32_t function_count(module_t*);
void     list_functions(module_t*, std::vector<std::string>& out);

char*    tokenize_dump(engine_t*, const char* src, size_t len, const char* file);
char*    ir_dump(engine_t*, const char* src, size_t len, const char* file);
void     free_string(char* str);   // free result of above

// Annotations [[...]] in source:
uint32_t get_annotated_functions(module_t*, const char* annotation, std::vector<std::string>& out);
uint32_t get_annotations(module_t*, const char* fn, std::vector<annotation_info>& out);
```

`annotation_info { const char* name; const char** args; uint32_t arg_count; }`.

## Per-Context Helpers (for addon authors)

Called from a native executing inside `execute()`/`call()`:

```cpp
engine_t*  active_engine();    // engine driving this execute; nullptr outside
context_t* active_context();   // context driving this execute; nullptr outside

uint64_t random_u64();
double   random_double();
int64_t  random_int_range(int64_t lo, int64_t hi);
void     random_seed(uint64_t seed);
```

All read per-thread TLS set by `execute()`, so they're thread-safe across concurrent engines.

## Heap + Weak References

```cpp
void*    heap_alloc(size_t size);
void*    heap_realloc(void* ptr, size_t new_size);
void     heap_free(void* ptr);
bool     heap_is_tracked(void* ptr);
void     heap_collect(module_t* m);                 // no-op, deterministic model
heap_stats heap_get_stats(module_t* m);
void     heap_set_memory_budget(module_t* m, size_t bytes);

// Weak-reference primitive: shared uint64 token tied to the allocation.
// Non-zero while alive, 0 after heap_free. Same pointer for repeat calls.
// Tokens are never freed (weak-ref wrappers may outlive the target).
uint64_t* alive_token(void* ptr);
```

`heap_stats { alloc_count, total_bytes, freed_count, freed_bytes }` - all `uint64_t`.

## Event API (context-scoped, int64 IDs → int64 fn refs)

```cpp
void register_event(context_t*, int64_t event_id, int64_t callback);
void fire_event(context_t*, int64_t event_id);
void clear_events(context_t*);
```

## Exceptions

```cpp
bool    exception_pending(module_t* m);
int64_t exception_value(module_t* m);
int64_t exception_type(module_t* m);      // type hash of the thrown value
void    exception_clear(module_t* m);
```

Raise from native:

```cpp
void runtime_error(const char* msg);       // maps to execute()→false
void runtime_exception(const char* msg);   // throws, catchable by script try/catch
```

## Debug + Budget

```cpp
void set_budget(module_t* m, int64_t instructions);   // 0 = disabled
void set_debug_hook(module_t* m, void(*hook)(const char* file, uint32_t line, int64_t* frame));

struct stack_frame { const char* function; const char* file; uint32_t line; };
uint32_t get_stack_trace(context_t* ctx, stack_frame* out, uint32_t max);

int64_t get_last_executed_line(module_t* m);   // crash diagnostic
```

`set_debug(e, true)` is required for meaningful stack traces and line mapping. Must be called BEFORE compile so `op_debug_line` instructions are emitted.

## IDE debugger SDK

For IDEs that need breakpoints, stepping, and local-variable inspection. All opt-in via `set_debug(true)`. When off, none of these code paths fire (zero cost).

For full debugger fidelity (locals visible in their declared frame slots) you should ALSO disable optimization: `set_optimize(e, false)`. Otherwise the optimizer promotes locals to registers and they never land in their declared slots.

```cpp
// Source map / function lookup
struct em_debug_fn_t;   // opaque
const em_debug_fn_t* find_fn_at(module_t*, const char* file, uint32_t line);
const char* debug_fn_name        (const em_debug_fn_t*);
uint32_t    debug_fn_local_count (const em_debug_fn_t*);
uint32_t    debug_fn_param_count (const em_debug_fn_t*);

void find_code_offsets(module_t*, const char* file, uint32_t line,
                       size_t* out_offsets, uint32_t* out_count, uint32_t max);

// Local readback. frame is the rbp the hook receives.
struct em_local_info { const char* name; type_id type; uint32_t slot; };
uint32_t enumerate_locals(const em_debug_fn_t*, em_local_info* out, uint32_t max);

int64_t     read_local_int    (int64_t* frame, uint32_t slot);
double      read_local_float  (int64_t* frame, uint32_t slot);
const char* read_local_string (int64_t* frame, uint32_t slot);
void*       read_local_pointer(int64_t* frame, uint32_t slot);

// Breakpoints (per module).
int32_t set_breakpoint    (module_t*, const char* file, uint32_t line);
void    clear_breakpoint  (module_t*, int32_t bp_id);
void    enable_breakpoint (module_t*, int32_t bp_id, bool enabled);
bool    is_breakpoint_at  (module_t*, const char* file, uint32_t line);

struct em_breakpoint_info { int32_t id; const char* file; uint32_t line; bool enabled; };
uint32_t list_breakpoints(module_t*, em_breakpoint_info* out, uint32_t max);

// Stepping (per context). Multi-thread routines get independent state.
enum class step_mode : int32_t { step_none, step_over, step_in, step_out };
void      set_step_mode           (context_t*, step_mode);
step_mode get_step_mode           (context_t*);
void      set_step_baseline_depth (context_t*, int32_t depth);
int32_t   get_step_baseline_depth (context_t*);
int32_t   get_call_depth          (int64_t* frame, module_t*);

// Pause / resume (per context).
void request_pause       (context_t*);
void resume              (context_t*);
bool is_pause_requested  (context_t*);

// Convenience: combines breakpoint + pause + step logic. Returns true if
// the host hook should pause execution at this line.
bool should_pause_at(context_t*, module_t*, int64_t* frame,
                      const char* file, uint32_t line);
```

Typical IDE pattern inside the debug hook:

```cpp
void on_line(const char* file, uint32_t line, int64_t* frame) {
    context_t* ctx = active_context();
    module_t* mod = ...;
    if (should_pause_at(ctx, mod, frame, file, line)) {
        // 1. Notify IDE: paused at file:line
        // 2. Inspect locals
        auto* fn = find_fn_at(mod, file, line);
        em_local_info infos[64];
        uint32_t n = enumerate_locals(fn, infos, 64);
        for (uint32_t i = 0; i < n; ++i) {
            switch (infos[i].type) {
                case type_id::t_int64: read_local_int(frame, infos[i].slot); break;
                case type_id::t_string: read_local_string(frame, infos[i].slot); break;
                /* ... */
            }
        }
        // 3. Wait for IDE command (continue / step / etc.)
        // 4. Before returning to script:
        //    set_step_baseline_depth(ctx, get_call_depth(frame, mod));
        //    set_step_mode(ctx, step_mode::step_over);
        //    resume(ctx);   // clears pause_requested
    }
}
```

## Error Handling

```cpp
struct error_info {
    int         code;
    std::string message;
    std::string file;
    uint32_t    line;
    uint32_t    column;
};

error_info  last_error(engine_t*);
const char* last_error_message(engine_t*);
```

Error codes are set on `compile()` / `execute()` failure. Codes: `0` = ok; non-zero = fail. `message` + `file:line:column` pinpoint the problem.

## Built-in Addons (registration)

```cpp
void register_all_addons(engine_t*);   // registers everything below

void register_addon_core(engine_t*);        // print / println
void register_addon_string(engine_t*);      // string methods
void register_addon_array(engine_t*);       // array methods
void register_addon_map(engine_t*);         // map methods
void register_addon_math(engine_t*);        // scalar math + vec2/3/4 + quat + mat4
void register_addon_simd(engine_t*);        // SSE2 memops, packed ops (stride 1/2/4/8)
void register_addon_variant(engine_t*);     // open tagged union
void register_addon_atomic(engine_t*);      // atomic_int32/64
void register_addon_bits(engine_t*);        // popcount/clz/ctz/rotl/rotr/bswap
void register_addon_time(engine_t*);        // time_ms, calendar
void register_addon_regex(engine_t*);       // regex type
void register_addon_file(engine_t*);        // needs PERM_FILE
void register_addon_hash_set(engine_t*);    // hash_set<T>
void register_addon_sorted_map(engine_t*);  // sorted_map<K,V>
void register_addon_thread(engine_t*);      // mutex, cond_var, lock_guard
void register_addon_json(engine_t*);        // json_parse, json_value
void register_addon_list(engine_t*);        // list<T>
```

## Building a Custom Addon

### Stateless functions

```cpp
int32_t square(int32_t x) { return x * x; }

void register_addon_mymath(engine_t* e) {
    register_typed<&square>(e, "int32 square(int32)");
}
```

### A new custom type

```cpp
struct color_t { uint8_t r, g, b, a; };

color_t* color_create(int32_t r, int32_t g, int32_t b, int32_t a) {
    auto* c = static_cast<color_t*>(heap_alloc(sizeof(color_t)));
    c->r = (uint8_t)r; c->g = (uint8_t)g; c->b = (uint8_t)b; c->a = (uint8_t)a;
    return c;
}
void     color_destroy(color_t* c) { heap_free(c); }
int64_t  color_to_hex(color_t* c)  { return (c->r << 24) | (c->g << 16) | (c->b << 8) | c->a; }
color_t* color_blend(color_t* a, color_t* b) {
    return color_create((a->r + b->r) / 2, (a->g + b->g) / 2,
                        (a->b + b->b) / 2, (a->a + b->a) / 2);
}
bool     color_eq(color_t* a, color_t* b) {
    return a->r == b->r && a->g == b->g && a->b == b->b && a->a == b->a;
}
color_t* color_add(color_t* a, color_t* b) {
    return color_create(std::min(255, a->r + b->r), std::min(255, a->g + b->g),
                        std::min(255, a->b + b->b), std::min(255, a->a + b->a));
}

void register_addon_color(engine_t* e) {
    type_builder(e, "color_t", type_id::t_int64)
        .factory_typed<&color_create>(4)
        .destructor_typed<&color_destroy>()
        .method_typed<&color_to_hex>("int64 to_hex()")
        .method_typed<&color_blend>("color_t blend(color_t)")
        .bin_eq_typed<&color_eq>()
        .bin_add_typed<&color_add>()
        .finish();
}
```

Use from script:

```c
color_t c = color_t(255, 128, 0, 255);
int64 h  = c.to_hex();
color_t d = c + color_t(0, 128, 128, 0);
```

### Weak references in an addon

```cpp
struct weak_ref { uint64_t* tok; void* ptr; };

int64_t weak_make(int64_t target) {
    auto* w = static_cast<weak_ref*>(heap_alloc(sizeof(weak_ref)));
    w->ptr = reinterpret_cast<void*>(target);
    w->tok = alive_token(w->ptr);        // lazy token per allocation
    return reinterpret_cast<int64_t>(w);
}
bool weak_alive(weak_ref* w) { return w && w->tok && *w->tok != 0; }
int64_t weak_get(weak_ref* w) {
    if (!weak_alive(w)) return 0;
    return reinterpret_cast<int64_t>(w->ptr);
}
```

## Thread Safety

* Engines are independent, no shared mutable state. Separate threads → separate engines.
* Multiple contexts off the same module can execute concurrently.
* Per-thread TLS heap. `execute()` sets TLS before running and restores on exit.
* All `active_*` / `random_*` / `alive_token` helpers are thread-safe.
* Tested under ASAN/TSAN with 32+ threads.

## Safety Layers

* **Fault trapping**: JIT null-deref, out-of-bounds, use-after-free caught by the runtime fault handler. `execute()` returns `false`, host process stays alive.
* **Execution budget**: `set_budget(mod, N)` halts after N loop iterations.
* **Memory budget**: `heap_set_memory_budget(mod, bytes)` caps live heap.
* **Permissions**: `PERM_FFI` / `PERM_FILE` - scripts fail to compile calls without the permission.
* **Sandboxing**: scripts see only what you register. Default addons minimal; skip `register_addon_file`, don't grant `PERM_FFI`, register only your native functions.
* **Type verification**: every native call-site checks arg types, struct identity, enum identity, typed-container element types at compile.

## Scripts Ship As

* `.em` source: compile at startup with `compile`.
* `.emb` binary: `serialize()` after compile, `deserialize()` on next run. Faster startup; binary may become incompatible with SDK upgrades that change IR.

## Cheat Sheet

```cpp
// minimum
engine_t* e = create(); register_all_addons(e);
module_t* m = compile(e, src, len, "x.em");
context_t* c = create_context(m);
execute(c, "main");
int64_t r = return_value(c);
destroy_context(m, c); module_destroy(m); destroy(e);

// args
int64_t a[] = { 1, 2 };
call(c, "add", a, 2);

// userdata
set_userdata_at(c, 3, &my_state);
// inside native:
auto* s = static_cast<MyState*>(get_userdata_at(active_context(), 3));

// native fn
register_typed<&my_fn>(e, "int64 my_fn(int64, int64)");

// custom type
type_builder(e, "my_t", type_id::t_int64)
    .factory_typed<&my_create>(1)
    .destructor_typed<&my_destroy>()
    .method_typed<&my_method>("int64 method()")
    .finish();

// globals
set_global(m, "config_level", 5);

// serialization
std::vector<uint8_t> bin; serialize(m, bin);
module_t* m2 = deserialize(e, bin.data(), bin.size());

// errors
if (!compile(e, src, len, "f.em")) {
    auto err = last_error(e);
    fprintf(stderr, "%s at %s:%d:%d\n", err.message.c_str(), err.file.c_str(), err.line, err.column);
}
```

## Pitfalls

* `register_typed<&Fn>` only handles arity ≤ 6. More args → manual `register_native` with int64 ABI.
* Floats passed via `call(ctx, ...)` must be bit-cast to int64. Same for return (`return_float` bit-casts back).
* Pointer/handle args must be valid at call time, the SDK does not track ownership across the boundary. Prefer heap-owned values when crossing repeatedly.
* `destroy_context` requires the module pointer. Don't destroy the module before its contexts.
* `register_all_addons` grants nothing special. `PERM_FILE` is separate from registration. File addon calls fail to compile without the permission.
* Calling a script function before compile succeeded = undefined behavior. Always check `compile` return.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/llms-sdk.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
