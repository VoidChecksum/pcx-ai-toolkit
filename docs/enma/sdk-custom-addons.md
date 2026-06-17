> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/custom-addons.md).

# Custom Addons

Walkthrough from a single function to a full type with operators.

{% stepper %}
{% step %}
**A Single Function**

**Native side:**

```cpp
#include "sdk.h"
using namespace enma;

int32_t square(int32_t x) {
    return x * x;
}

void register_addon_mymath(engine_t* e) {
    register_native(e, "int32 square(int32)", (void*)&square);
}
```

**Enma side:**

```cpp
int32 main() {
    println(square(5));  // 25
    return 0;
}
```

**Host setup:**

```cpp
engine_t* e = create();
register_all_addons(e);
register_addon_mymath(e);
```

`register_native(e, sig, (void*)fn)` is type-safe and works at any arity. The signature string drives how args and returns are placed per Win64 ABI - ints / pointers / bools go in int regs, floats / doubles go in xmm regs, narrow-int returns get sign/zero-extended on the way back. Declare your C function with the exact types in the signature - no int64 bit-casting, no trampolines.

There's a template shortcut `register_typed<&fn>(e, sig)` that's equivalent - the `&fn` template parameter exists only to capture the function at compile time. Either form works; pick whichever reads better.
{% endstep %}

{% step %}
**Multiple Functions**

```cpp
double lerp(double a, double b, double t) {
    return a + (b - a) * t;
}

double distance(double x1, double y1, double x2, double y2) {
    double dx = x2 - x1, dy = y2 - y1;
    return std::sqrt(dx*dx + dy*dy);
}

void register_addon_mymath(engine_t* e) {
    register_native(e, "int32 square(int32)",                             (void*)&square);
    register_native(e, "float64 lerp(float64, float64, float64)",         (void*)&lerp);
    register_native(e, "float64 distance(float64, float64, float64, float64)", (void*)&distance);
}
```

{% endstep %}

{% step %}
**A Custom Type**

A `color_t` with fields, constructor, methods, and operators.

**The native struct:**

```cpp
struct color_t {
    uint8_t r, g, b, a;
};
```

**Factory + destructor + methods:**

```cpp
color_t* color_create(int32_t r, int32_t g, int32_t b, int32_t a) {
    auto* c = static_cast<color_t*>(heap_alloc(sizeof(color_t)));
    c->r = (uint8_t)r; c->g = (uint8_t)g; c->b = (uint8_t)b; c->a = (uint8_t)a;
    return c;
}

void color_destroy(color_t* c) {
    heap_free(c);
}

int64_t color_to_hex(color_t* c) {
    return (int64_t)((c->r << 24) | (c->g << 16) | (c->b << 8) | c->a);
}

color_t* color_blend(color_t* a, color_t* b) {
    return color_create((a->r + b->r) / 2, (a->g + b->g) / 2,
                        (a->b + b->b) / 2, (a->a + b->a) / 2);
}
```

**Operators:**

```cpp
bool color_eq(color_t* a, color_t* b) {
    return a->r == b->r && a->g == b->g && a->b == b->b && a->a == b->a;
}

color_t* color_add(color_t* a, color_t* b) {
    return color_create(std::min(255, a->r + b->r),
                        std::min(255, a->g + b->g),
                        std::min(255, a->b + b->b),
                        std::min(255, a->a + b->a));
}
```

**Registration:**

```cpp
void register_addon_color(engine_t* e) {
    type_builder(e, "color_t", type_id::t_struct)
        .field("r", offsetof(color_t, r), type_id::t_uint8)
        .field("g", offsetof(color_t, g), type_id::t_uint8)
        .field("b", offsetof(color_t, b), type_id::t_uint8)
        .field("a", offsetof(color_t, a), type_id::t_uint8)
        .factory((void*)&color_create,
                 { type_id::t_int32, type_id::t_int32, type_id::t_int32, type_id::t_int32 })
        .destructor((void*)&color_destroy)
        .method("int64 to_hex()",            (void*)&color_to_hex)
        .method("color_t blend(color_t)",    (void*)&color_blend)
        .bin_add((void*)&color_add)
        .bin_eq ((void*)&color_eq)
        .finish();
}
```

Pass per-arg enma type IDs to `.factory(fn, { ... })` so the Win64 ABI router knows which args to place in int regs vs xmm regs. For types without float params `.factory(fn, count)` still works - it defaults everything to int placement, fine for integer / pointer args.

**Enma side:**

```cpp
int32 main() {
    color_t red = color_t(255, 0, 0, 255);
    color_t blue = color_t(0, 0, 255, 255);
    color_t purple = red + blue;

    println(purple.r);  // 255
    println(purple.b);  // 255

    color_t blended = red.blend(blue);
    println(blended.r);  // 127
    println(blended.b);  // 127

    int64 hex = red.to_hex();
    println(hex);  // 4278190335

    if (red == red) println("equal");

    return 0;
}
```

{% endstep %}
{% endstepper %}

## Value-Type Types (Performance Opt-In)

For small POD-like types (vec3, color, quat, etc.) the default handle layout — every script value is an 8-byte pointer to a heap allocation — costs more than the actual work. Three opt-in `type_builder` hooks turn a typereg into a **value type**:

```cpp
type_builder(e, "color_t", type_id::t_int64)
    .value_type(sizeof(color_t))                  // (1) inline storage
    .factory_in_place((void*)&color_construct)    // (2) write-into-buffer ctor
    .inline_property("r", (void*)&color_get_r, (void*)&color_set_r,
                     type_id::t_uint8, offsetof(color_t, r))  // (3) inline accessor
    // ... regular factory / methods / operators stay the same ...
    .finish();
```

What you get:

* **No per-instance heap alloc** for non-escaping locals — the compiler stack-allocates the value.
* **Inline container storage** — `color_t[]` lays out N × `sizeof(color_t)` bytes contiguously, no handle indirection (arrays only; maps/sets still 8-byte handles).
* **Direct property reads/writes** — `c.r` compiles to a single `mov` instead of a native call when the property has an `inline_offset`.

`factory_in_place` ctor signature: `int64_t fn(int64_t dst, args...)` — write into `dst`, return `dst`. The regular `.factory(...)` is still used for explicit `new color(args)`. See [Type Registration](sdk-type-registration.md#value-type-registration) for the full walkthrough, constraints, and benchmark numbers.

## Source-Level Modules

For small POD types like `vec3` and `color` the typereg path still pays a per-operation heap\_alloc — every `a + b` invokes a native that returns a fresh `Vec3*`.

A faster pattern: ship the type as **Enma source** registered via `register_module`. The compiler treats it like any user struct — stack-allocates non-escaping locals and inlines field reads/writes. The trick is:

1. Write the type as a static `R"(...)"` literal in your addon `.cpp`. NEVER allocated, never copied — the engine keeps a `string_view` into the literal.
2. Call `register_module(engine, "modname", k_src)` in your addon registration function.
3. Scripts opt in with `import "modname";` at the top of the file.

```cpp
// em_addon_my_math.cpp
static const char* k_my_math_src = R"(
struct point2 {
    float64 x;
    float64 y;
    point2() { x = 0.0; y = 0.0; }
    point2(float64 a, float64 b) { x = a; y = b; }
    point2 operator+(point2 o) {
        // Local-and-return — NO heap alloc.
        point2 r; r.x = x + o.x; r.y = y + o.y; return r;
    }
    float64 dot(point2 o) { return x * o.x + y * o.y; }
}
)";

void register_addon_my_math(engine_t* e) {
    register_module(e, "my_math", k_my_math_src);
}
```

```enma
import "my_math";
int64 main() {
    point2 a = point2(1.0, 2.0);
    point2 b = point2(3.0, 4.0);
    point2 c = a + b;          // zero heap allocations
    return cast<int64>(c.x);    // 4
}
```

### Why this beats the typereg path

Built-in modules give the compiler everything it has on user structs: stack promotion, register promotion, escape analysis, RAII. For `vec3 c = a + b` the entire add path stays in stack locals — no `heap_alloc(24)`, no `heap_free(24)`, no native call. Across a 1000-iter loop of vec3 add operations, the typereg path performs 1000 heap\_alloc/free pairs; the source-module path performs zero.

### Critical: use the local-and-return pattern

Inside operator/method bodies, write the result as a local then return it:

```enma
// GOOD — local r is stack-promoted, return copies into the caller's slot.
vec3 operator+(vec3 o) {
    vec3 r; r.x = x + o.x; r.y = y + o.y; r.z = z + o.z;
    return r;
}

// BAD — inner `vec3(...)` ctor-temp gets heap-allocated then copied into
// the return slot then freed. Costs one heap_alloc per call.
vec3 operator+(vec3 o) {
    return vec3(x + o.x, y + o.y, z + o.z);
}
```

### Resolution order

When the preprocessor encounters `import "name";`:

1. **Built-in modules** registered via `register_module` (this wins first)
2. **Host import resolver** installed via `set_import_resolver` (callback returns malloc'd buffer)
3. **`module_paths` / `include_paths` filesystem search** for `name.em` / `name.emb`

Built-in modules are emitted at top level — `import "math";` makes `vec3`, `quat`, `mat4` etc. directly accessible without a prefix. The addon author owns the namespace-collision rules across all shipped modules.

### Coexistence with the typereg

A type can be registered both via `type_builder` and as part of a source module simultaneously — when the script `import`s the module, the source struct definition takes precedence; otherwise the typereg is used as a fallback. Useful for gradual migration paths where some hosts ship the typereg-only variant.

### Already shipped

* **`math`** (`em_addon_math.cpp` — registered with `register_addon_math`). Defines `vec2`, `vec3`, `vec4`, `quat`, `mat4` as value structs plus the scalar math natives (`sin`, `cos`, `sqrt`, `pow`, `floor`, `ceil`, `rand`, ...). See [Math](addon-math.md), [Vectors](addon-vec.md), [3D Math](addon-math3d.md).
* **`color`** (perception's `enma_render_api.cpp` — registered by `register_render_api`). `[[packed]]` 4-byte struct matching the C `pixelcolor4` layout, with `r`/`g`/`b`/`a` fields and `with_alpha(uint8)`. Used by every `draw_*` native.

## Addon Registration Pattern

Follow this pattern for all addons:

```cpp
// header: addon_color.h
void register_addon_color(engine_t* e);

// source: addon_color.cpp
void register_addon_color(engine_t* e) {
    // register native functions
    // register types via type_builder
}

// host main.cpp
engine_t* e = create();
register_all_addons(e);
register_addon_color(e);
// ...
```

## Standalone Addon Model

Custom addons are `.cpp` source files compiled with your app. The only dependency is `sdk.h`. The shipped lib already includes the built-in addons; your custom addon goes on the link line alongside it.

```cpp
project/
  app.cpp
  sdk.h
  addons/addon_color.cpp
  addons/addon_color.h
```

```bash
# /MT
clang-cl /I. /MT app.cpp addons/addon_color.cpp windows/enma_x64static_mt.lib /Fe:app.exe

# /MD
clang-cl /I. /MD app.cpp addons/addon_color.cpp windows/enma_x64static_md.lib /Fe:app.exe
```

Statically linked. No plugin loading, no ABI concerns.

## Heap Allocation for Addons

Use these (not `new`/`malloc`) so Enma's stats and memory budget track the allocation:

```cpp
void* ptr = heap_alloc(128);
ptr = heap_realloc(ptr, 256);
heap_free(ptr);
```

| Function                  | Purpose                                                                           |
| ------------------------- | --------------------------------------------------------------------------------- |
| `heap_alloc(size)`        | Allocate from tracked heap (malloc + 16-byte header)                              |
| `heap_realloc(ptr, size)` | Resize tracked allocation                                                         |
| `heap_free(ptr)`          | Free tracked allocation                                                           |
| `heap_is_tracked(ptr)`    | True if `ptr` has Enma's magic marker; check before freeing pool/literal pointers |

Frees happen on explicit `heap_free`, scope-dtor, or cleanup-stack unwind (throw / JIT fault).

### Deterministic Scope-Drop

Types with a registered destructor get automatic scope-exit cleanup on script locals. Add `.pure_methods()` so the compiler can emit drop calls safely.

```cpp
void my_type_drop(my_type_t* obj) {
    if (!obj) return;
    if (obj->data) heap_free(obj->data);
    heap_free(obj);
}

type_builder(e, "my_type", type_id::t_struct)
    .factory((void*)&create_my_type, 0)
    .destructor((void*)&my_type_drop)
    .pure_methods()
    .method("...", (void*)&some_method);
```

See [Type Registration](sdk-type-registration.md) for the full lifecycle flow.

### Copy Hook (for ref-counted / COW types)

By default, `T b = a;` shares the int64 handle, both copies point at the same heap object. For types that need copy semantics (ref-counted `shared_ptr`-style, copy-on-write, arena-backed), register a copy hook:

```cpp
int64_t rc_copy(int64_t h) {
    if (!h) return 0;
    auto* o = reinterpret_cast<refcount_obj*>(h);
    ++o->count;
    return h;   // return the same handle, caller and callee share ownership
}

type_builder(e, "rc", type_id::t_int64)
    .factory((void*)&rc_create, 1)
    .copy((void*)&rc_copy)
    .destructor((void*)&rc_dtor);
```

The compiler emits a call to `copy_fn(src)` at `T b = a;` when the source is an identifier of the same type. Plain assignment (`b = a;`) and by-value argument passing still share the handle directly, use an explicit call if you need copy semantics there.

### Serialization Hooks

Let walkers (JSON writers, debuggers, pretty-printers) dispatch through reflection instead of hardcoding per-type logic:

```cpp
int64_t date_serialize(int64_t h) {
    auto* d = reinterpret_cast<date_t*>(h);
    char buf[32];
    int n = std::snprintf(buf, sizeof(buf), "%04d-%02d-%02d", d->y, d->m, d->d);
    auto* out = (char*)std::malloc(n + 1);
    std::memcpy(out, buf, n + 1);
    return (int64_t)out;
}

int64_t date_deserialize(int64_t str_ptr) {
    auto* s = reinterpret_cast<const char*>(str_ptr);
    int y, m, d;
    if (std::sscanf(s, "%d-%d-%d", &y, &m, &d) != 3) return 0;
    auto* r = (date_t*)std::malloc(sizeof(date_t));
    r->y = y; r->m = m; r->d = d;
    return (int64_t)r;
}

type_builder(e, "date", type_id::t_int64)
    .factory(...)
    .destructor(...)
    .serialize((void*)&date_serialize)
    .deserialize((void*)&date_deserialize);
```

Generic walker code reads the hook via reflection:

```cpp
auto* fn = type_reg_serialize(find_type_reg(e, some_type_id));
if (fn) {
    int64_t str = ((int64_t(*)(int64_t))fn)(value);
    // ... consume str, then std::free(str) ...
}
```

Return a heap-allocated `char*`; caller decides whether to `free` or let it flow into a larger buffer. Use `std::malloc` for walker integration (can run outside `execute()`) or `heap_alloc` for script-visible buffers during execution.

### Interface Declaration

Mark a type as an interface with `.as_interface()`; other types declare they implement it with `.implements(name)`:

```cpp
type_builder(e, "Stream", type_id::t_int64).as_interface().finish();

type_builder(e, "file_stream", type_id::t_int64)
    .factory(...)
    .destructor(...)
    .implements("Stream")
    .implements("Writer")
    .finish();
```

A native with an interface-typed parameter accepts any implementer at the call site. The compiler auto-injects the concrete `type_id` as an extra int64 argument before the value, so native signatures are `(int64 concrete_tid, int64 value, ...)`. Resolve a per-concrete-type method pointer with `enma::interface_method_fn(engine, tid, "name")`.

**Script-level dispatch.** An interface-typed local also works from script: `Stream s = file_stream(...); s.write("hi");` resolves the concrete method at runtime. Reassigning `s = mem_stream(...)` swaps the dispatch target.

Reflection:

```cpp
const type_reg_t* reg = find_type_reg_by_name(e, "file_stream");
if (type_reg_implements(reg, "Stream")) { ... }
for (uint32_t i = 0; i < type_reg_implements_count(reg); ++i)
    printf("%s\n", type_reg_implements_at(reg, i));
```

### Type-Registry Reflection

Addons can query any registered type's hooks without knowing about the type at compile time:

```cpp
const type_reg_t* reg = find_type_reg(e, some_type_id);
// or: find_type_reg_by_name(e, "date");

const char* name = type_reg_name(reg);
void* factory = type_reg_factory(reg);
void* dtor    = type_reg_dtor(reg);
void* copy    = type_reg_copy(reg);
void* hash    = type_reg_hash(reg);
void* compare = type_reg_compare(reg);
void* ser     = type_reg_serialize(reg);
void* method  = type_reg_method(reg, "methodName");

uint32_t nmethods = type_reg_method_count(reg);
const char* method_name = type_reg_method_name_at(reg, 0);
```

All accessors are null-safe: pass `nullptr` and get a sensible default. Use this surface to write generic containers (`hash_set`, `sorted_map`), serializers, debuggers, or any cross-addon infrastructure that needs to dispatch through registered hooks without a compile-time dependency on the concrete type.

## Per-Context Helpers

Addon natives called from within `execute()`/`call()` can reach per-context state without taking the engine/context as an argument:

```cpp
engine_t*  e    = active_engine();        // the engine driving this call
context_t* ctx  = active_context();       // the context driving this call
uint64_t   bits = random_u64();           // per-context mt19937_64
double     r    = random_double();        // [0, 1)
int64_t    n    = random_int_range(0, 100);
random_seed(42);                          // seeds per-context rng
```

All are thread-safe under concurrent engines because they read the per-thread TLS slot set by `execute()`. Outside `execute()` they return `nullptr` / 0.

## Invoking Script Closures from Background Threads

When a host needs to tick a script-side callback on its own thread (e.g., a periodic task, a routine that draws every frame, a worker pool) the invocation has to run inside an `execution_scope`. The scope sets up per-thread TLS (heap, runtime\_state, engine, events, rng, JIT code range, active context) that Enma's JIT and built-in natives rely on. Without it, the first native that touches TLS (heap\_alloc, string concat, variant boxing, etc.) dereferences nullptr and takes down the host.

```cpp
struct tick_data_t {
    context_t* ctx;
    int64_t    fn_handle;    // closure ptr - cast<int64>(my_callback) from script
    int32_t    cb_id;
};

// Call a 2-arg script closure (typical: id, user_data) via the stack-push
// calling convention Enma uses for closures.
static int64_t invoke_fn2(int64_t fn_handle, int64_t a, int64_t b) {
    int64_t result = 0;
    int64_t* closure = reinterpret_cast<int64_t*>(fn_handle);
    void* fn = reinterpret_cast<void*>(closure[0]);
    __asm__ volatile(
        "push %2\n\t"
        "push %3\n\t"
        "push %4\n\t"
        "call *%1\n\t"
        "add $24, %%rsp\n\t"
        : "=a"(result)
        : "r"(fn), "r"(fn_handle), "r"(a), "r"(b)
        : "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11", "memory"
    );
    return result;
}

void worker_thread(tick_data_t* td) {
    execution_scope scope(td->ctx);      // TLS setup for the whole tick loop
    while (!thread_should_stop(td)) {
        invoke_fn2(td->fn_handle, (int64_t)td->cb_id, 0);
        sleep_ms(1);
    }
    // scope dtor restores prev TLS on the way out
}
```

`execution_scope` is RAII and nestable - the destructor restores whatever state was active before. Safe to wrap a single closure call or an entire tick loop; the setup cost is one-time so scoping across the whole loop is usually what you want.

## Weak References. `alive_token(ptr)`

Returns a shared `uint64_t*` tied to this allocation's lifetime. Non-zero while the allocation is live; flipped to 0 when `heap_free(ptr)` runs. Repeat calls for the same pointer return the same token.

```cpp
void* p = heap_alloc(sizeof(MyObj));
uint64_t* tok = alive_token(p);           // tok points at a 1 (alive)
// ... later ...
if (*tok) { /* safe to use p */ }
heap_free(p);                              // *tok flips to 0
```

Tokens are never freed - weak-ref wrappers can hold the token pointer beyond the original allocation.

## Event API

Events keyed by `int64_t` ID; callbacks are `int64_t` function refs.

```cpp
register_event(ctx, 1, callback_fn);
fire_event(ctx, 1);         // fires all callbacks for event 1
clear_events(ctx);          // unregister all
```

| Function                                                         | Description                     |
| ---------------------------------------------------------------- | ------------------------------- |
| `register_event(context_t*, int64_t event_id, int64_t callback)` | Register an event callback      |
| `fire_event(context_t*, int64_t event_id)`                       | Fire all callbacks for an event |
| `clear_events(context_t*)`                                       | Remove all registered events    |

From script, use `register_event(id, handler)` + `fire_event(id, arg)`. `handler` is a function reference (script function name or lambda).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/custom-addons.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
