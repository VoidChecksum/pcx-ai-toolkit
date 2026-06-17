> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/type-registration.md).

# Type Registration

`type_builder` exposes native types to scripts: fields, methods, properties, operators (full set including `opCmp`, compound assign, `++`/`--`), subscript, iteration, conversion, factory, destructor.

## Descriptions

Every hook that takes a signature or name also takes an optional trailing `const char* description`. These surface via [`extract_documentation`](/enma/sdk-guide/introspection.md) and `extract_intellisense` for IDE tooling and auto-generated docs.

```cpp
type_builder(e, "color", type_id::t_int64, "RGBA color, 8 bits per channel")
    .factory((void*)&color_create,
        { type_id::t_uint8, type_id::t_uint8, type_id::t_uint8, type_id::t_uint8 },
        "construct color(r, g, b, a) with each channel in 0..255")
    .destructor((void*)&color_dtor, "free color memory")
    .method("uint8 r()", (void*)&color_r, "red channel")
    .method("uint8 g()", (void*)&color_g, "green channel")
    .method("uint8 b()", (void*)&color_b, "blue channel")
    .method("uint8 a()", (void*)&color_a, "alpha channel")
    .field("pad", offsetof(color_t, pad), type_id::t_uint32, "reserved - do not read")
    .property("rgba", (void*)&color_rgba_get, (void*)&color_rgba_set,
              type_id::t_uint32, "packed 32-bit RGBA form");
```

Descriptions are purely documentation - omit them if the name/signature is self-explanatory.

## Walkthrough: Building a Complete Type

{% stepper %}
{% step %}
**The Native Type**

```cpp
struct vec3_t {
    double x, y, z;
};
```

{% endstep %}

{% step %}
**Starting the Builder**

```cpp
type_builder(e, "vec3_t", type_id::t_struct)
```

The first argument is the engine, the second is the name visible in scripts, and the third is the base type category. Use `t_struct` for custom value types.
{% endstep %}

{% step %}
**Fields**

Expose struct fields so scripts can read/write them directly:

```cpp
    .field("x", offsetof(vec3_t, x), type_id::t_float64)
    .field("y", offsetof(vec3_t, y), type_id::t_float64)
    .field("z", offsetof(vec3_t, z), type_id::t_float64)
```

Script usage:

```cpp
vec3_t v = vec3_t(1.0, 2.0, 3.0);
println(v.x);  // 1.0
v.y = 5.0;
```

{% endstep %}

{% step %}
**Factory (Constructor)**

Returns a pointer to the new object. Use `heap_alloc` so Enma tracks the allocation; `factory_typed<&Fn>` skips the int64 cast:

```cpp
vec3_t* vec3_create(double x, double y, double z) {
    auto* v = static_cast<vec3_t*>(heap_alloc(sizeof(vec3_t)));
    v->x = x; v->y = y; v->z = z;
    return v;
}
```

```cpp
    .factory_typed<&vec3_create>(3)   // 3 = param count
```

Script usage:

```cpp
vec3_t v = vec3_t(1.0, 2.0, 3.0);
```

Manual form: `int64_t vec3_create(...)` returning a `reinterpret_cast<int64_t>` of the pointer, registered with `.factory((void*)vec3_create, 3)`.
{% endstep %}

{% step %}
**Destructor**

Runs deterministically at scope exit. `destructor_typed<&Fn>` takes a typed pointer:

```cpp
void vec3_destroy(vec3_t* self) {
    heap_free(self);
}
```

```cpp
    .destructor_typed<&vec3_destroy>()
```

Fires on: scope exit (normal flow), exception unwind, JIT fault unwind, context destroy. All cleanup is **deterministic**; no tracing GC. If you don't register a destructor, memory is reclaimed without your teardown running.

**`.pure_methods()`**

Methods don't retain the receiver. Enables deterministic scope-drop for collection-like types where methods may store value args but never the receiver. Used by `array`, `map`. Don't set if any method does `g = self;`.

**`.pure_args()` (implies `.pure_methods()`)**

No method retains *any* arg. Use for value-like types: strings, math (`vec2`, `complex`), immutable records.

With `.pure_args()` set, the compiler's safety pass allows scope-drop even when a local is passed as a non-receiver argument to its type's own methods/operators:

```cpp
vec2 a = vec2(1, 2);
vec2 b = vec2(3, 4);
vec2 c = a + b;           // both a and b safely dropped at scope exit
```

Rule of thumb: use `.pure_methods()` for containers, `.pure_args()` for values/math. The built-in types:

| Type          | Flag              |
| ------------- | ----------------- |
| `string`      | `.pure_args()`    |
| `array`       | `.pure_methods()` |
| `map`         | `.pure_methods()` |
| {% endstep %} |                   |

{% step %}
**Methods**

Methods receive `self` as the first argument. `method_typed<&Fn>` is a thin wrapper that forwards `Fn` to `.method(sig, (void*)Fn)` - the native is called directly via Win64 ABI (no trampoline, no int64 bit-casting). Any arity, any type mix.

```cpp
double vec3_length_sq(vec3_t* self) {
    return self->x*self->x + self->y*self->y + self->z*self->z;
}

vec3_t* vec3_scale(vec3_t* self, double f) {
    self->x *= f; self->y *= f; self->z *= f;
    return self;
}
```

```cpp
    .method_typed<&vec3_length_sq>("float64 length_sq()")
    .method_typed<&vec3_scale>    ("vec3_t scale(float64)")
```

Any arity, any type mix (int / bool / char / float / double / pointer / enum / registered struct), since the native is called directly via Win64 ABI.

**Manual signature-string form**: pass an `int64_t`-returning function and cast yourself:

```cpp
int64_t vec3_length_sq_manual(int64_t self) {
    auto* v = reinterpret_cast<vec3_t*>(self);
    double r = v->x*v->x + v->y*v->y + v->z*v->z;
    int64_t bits; memcpy(&bits, &r, 8); return bits;
}

    .method("float64 length_sq()", (void*)vec3_length_sq_manual)
```

The compiler extracts the method name from the string and checks arg count + per-arg type at call sites. `v.scale("hello")` and `v.scale()` both fail at compile.

For generic container types (arrays, maps), use the `element` keyword as a placeholder, it resolves to the receiver's element type at the call site:

```cpp
    .method("void push(element)",             (void*)arr_push)
    .method("element pop()",                  (void*)arr_pop)
    .method("element get(int64)",             (void*)arr_get)
    .method("void insert(int64, element)",    (void*)arr_ins)
```

`element` in return position automatically sets `returns_element_type = true`. If the receiver's element type can't be determined, `element` falls back to `auto` (matches anything).

Custom types registered earlier with `struct_builder`, `type_builder`, or `enum_builder` work by name too:

```cpp
struct_builder(e, "proc_t").field("pid", type_id::t_int64);
// ...
    .method("proc_t make_child(int64)",  (void*)proc_make_child)
    .method("int64 inspect(proc_t)",     (void*)proc_inspect)
```

The sig-string form above (`"vec3_t scale(float64)"`) is the canonical registration syntax — types come from the parsed signature.

Script usage:

```cpp
vec3_t v = vec3_t(3.0, 4.0, 0.0);
println(v.length_sq());  // 25.0
v.scale(2.0);
```

{% endstep %}

{% step %}
**Properties**

Properties provide field-style read/write access via getter + setter callbacks. The getter signature is `T(int64_t self)` and the setter is `void(int64_t self, T value)` — Win64 ABI is honored, so floats return in `xmm0` and float setters receive the value in `xmm1` directly. No bit-casting required.

```cpp
double vec3_get_magnitude(int64_t self) {
    auto* v = reinterpret_cast<vec3_t*>(self);
    return sqrt(v->x * v->x + v->y * v->y + v->z * v->z);
}

double vec3_get_x(int64_t self) { return reinterpret_cast<vec3_t*>(self)->x; }
void   vec3_set_x(int64_t self, double v) { reinterpret_cast<vec3_t*>(self)->x = v; }
```

```cpp
    .property("magnitude", (void*)vec3_get_magnitude, nullptr, type_id::t_float64)
    .property("x", (void*)vec3_get_x, (void*)vec3_set_x, type_id::t_float64)
```

Pass `nullptr` for the setter to make the property read-only. Field-style writes (`v.x = 5.0`) call the setter directly; reads (`v.x`) call the getter. The fourth arg (`type_id`) flows through to the codegen so `cast<int64>(v.x)` does a real float→int convert instead of bit-preserving.

Script usage:

```cpp
println(v.magnitude);   // read-only — getter only
v.x = 5.0;              // setter
float64 x = v.x;        // getter; same as v.x()
```

{% endstep %}

{% step %}
**Arithmetic Operators**

Use the typed form `bin_*_typed<&Fn>()` to write operators with real types. Like `method_typed`, the wrapper just forwards `Fn` to the underlying `.bin_add` / etc. - Win64 ABI is honored directly:

```cpp
vec3_t* vec3_add(vec3_t* a, vec3_t* b) {
    return vec3_create(a->x + b->x, a->y + b->y, a->z + b->z);
}
vec3_t* vec3_sub(vec3_t* a, vec3_t* b) { /* ... */ }
vec3_t* vec3_mul(vec3_t* a, vec3_t* b) { /* ... */ }
vec3_t* vec3_div(vec3_t* a, vec3_t* b) { /* ... */ }
vec3_t* vec3_mod(vec3_t* a, vec3_t* b) { /* ... */ }
```

```cpp
    .bin_add_typed<&vec3_add>()
    .bin_sub_typed<&vec3_sub>()
    .bin_mul_typed<&vec3_mul>()
    .bin_div_typed<&vec3_div>()
    .bin_mod_typed<&vec3_mod>()
```

Manual form takes two `int64_t` args and returns an `int64_t`:

```cpp
int64_t vec3_add_raw(int64_t a, int64_t b) {
    auto* va = reinterpret_cast<vec3_t*>(a);
    auto* vb = reinterpret_cast<vec3_t*>(b);
    return reinterpret_cast<int64_t>(vec3_create(va->x + vb->x, va->y + vb->y, va->z + vb->z));
}
    .bin_add((void*)vec3_add_raw)
```

Script usage:

```cpp
vec3_t a = vec3_t(1.0, 2.0, 3.0);
vec3_t b = vec3_t(4.0, 5.0, 6.0);
vec3_t c = a + b;  // vec3_t(5.0, 7.0, 9.0)
vec3_t d = a * b;  // vec3_t(4.0, 10.0, 18.0)
```

{% endstep %}

{% step %}
**Comparison Operators**

Return `true` / `false`:

```cpp
bool vec3_eq(vec3_t* a, vec3_t* b) {
    return a->x == b->x && a->y == b->y && a->z == b->z;
}
bool vec3_lt(vec3_t* a, vec3_t* b) {
    double la = a->x*a->x + a->y*a->y + a->z*a->z;
    double lb = b->x*b->x + b->y*b->y + b->z*b->z;
    return la < lb;
}
bool vec3_gt(vec3_t* a, vec3_t* b) { return vec3_lt(b, a); }
bool vec3_le(vec3_t* a, vec3_t* b) { return !vec3_gt(a, b); }
bool vec3_ge(vec3_t* a, vec3_t* b) { return !vec3_lt(a, b); }
```

```cpp
    .bin_eq_typed<&vec3_eq>()
    .bin_lt_typed<&vec3_lt>()
    .bin_gt_typed<&vec3_gt>()
    .bin_le_typed<&vec3_le>()
    .bin_ge_typed<&vec3_ge>()
```

Script usage:

```cpp
if (a == b) { println("equal"); }
if (a < b)  { println("a is shorter"); }
```

{% endstep %}

{% step %}
**Unary Operators**

```cpp
vec3_t* vec3_neg(vec3_t* v) {
    return vec3_create(-v->x, -v->y, -v->z);
}
```

```cpp
    .unary_neg_typed<&vec3_neg>()
    .unary_bit_not_typed<&vec3_bit_not>()
```

Script usage:

```cpp
vec3_t neg = -v;
```

{% endstep %}

{% step %}
**Bitwise Operators**

```cpp
    .bit_and_typed<&vec3_bit_and>()
    .bit_or_typed<&vec3_bit_or>()
    .bit_xor_typed<&vec3_bit_xor>()
    .shl_typed<&vec3_shl>()
    .shr_typed<&vec3_shr>()
```

{% endstep %}

{% step %}
**Three-Way Compare (opCmp)**

Register one function returning `-1` / `0` / `+1`. Used as fallback for `<`, `>`, `<=`, `>=`, `==`, `!=` when no specific op (`bin_lt`, etc.) is registered.

```cpp
int32_t vec3_cmp(vec3_t* a, vec3_t* b) {
    double la = mag_sq(a), lb = mag_sq(b);
    return la < lb ? -1 : la > lb ? 1 : 0;
}
```

```cpp
    .compare_typed<&vec3_cmp>()
```

{% endstep %}

{% step %}
**Compound Assignment (`+=`, `-=`, `*=`, `/=`, `%=`)**

Optional dedicated hooks. If unset, falls back to `bin_add` / `bin_sub` / etc.

```cpp
    .bin_add_assign_typed<&vec3_add_assign>()   // a += b
    .bin_sub_assign_typed<&vec3_sub_assign>()
    .bin_mul_assign_typed<&vec3_mul_assign>()
    .bin_div_assign_typed<&vec3_div_assign>()
    .bin_mod_assign_typed<&vec3_mod_assign>()
```

{% endstep %}

{% step %}
**Increment / Decrement (`++`, `--`)**

Arity-1 functions returning the new value. Cover both pre and post forms.

```cpp
counter_t* counter_inc(counter_t* self) { /* returns updated counter */ }
counter_t* counter_dec(counter_t* self) { /* returns updated counter */ }
```

```cpp
    .increment_typed<&counter_inc>()
    .decrement_typed<&counter_dec>()
```

{% endstep %}

{% step %}
**Subscript Access**

Allow `v[0]`, `v[1]`, `v[2]` syntax:

```cpp
int64_t vec3_get_idx(int64_t self, int64_t idx) {
    auto* v = reinterpret_cast<vec3_t*>(self);
    double val = (idx == 0) ? v->x : (idx == 1) ? v->y : v->z;
    int64_t bits;
    memcpy(&bits, &val, 8);
    return bits;
}

int64_t vec3_set_idx(int64_t self, int64_t idx, int64_t val) {
    auto* v = reinterpret_cast<vec3_t*>(self);
    double d;
    memcpy(&d, &val, 8);
    if (idx == 0) v->x = d;
    else if (idx == 1) v->y = d;
    else v->z = d;
    return 0;
}
```

```cpp
    .subscript((void*)vec3_get_idx, (void*)vec3_set_idx)
```

Script usage:

```cpp
println(v[0]);  // x component
v[2] = 99.0;          // set z component
```

{% endstep %}

{% step %}
**Iteration**

Make the type usable in `for` loops:

```cpp
int64_t vec3_iter_len(int64_t self) { return 3; }

int64_t vec3_iter_get(int64_t self, int64_t idx) {
    return vec3_get_idx(self, idx);
}
```

```cpp
    .iterable((void*)vec3_iter_len, (void*)vec3_iter_get)
```

Script usage:

```cpp
for (float64 component : v) {
    println(component);
}
```

For key-value iteration (like maps), use `kv_iterable`:

```cpp
    .kv_iterable((void*)len_fn, (void*)key_fn, (void*)val_fn)
```

{% endstep %}

{% step %}
**Init-Push**

Support brace initialization `vec3_t v = {1.0, 2.0, 3.0}` by pushing elements during construction:

```cpp
int64_t vec3_push(int64_t self, int64_t val) {
    auto* v = reinterpret_cast<vec3_t*>(self);
    if (v->x == 0 && v->y == 0 && v->z == 0) { double d; memcpy(&d, &val, 8); v->x = d; }
    // ... push logic
    return 0;
}
```

```cpp
    .init_push((void*)vec3_push)
```

{% endstep %}

{% step %}
**Hash**

Return a hash value for use in map keys:

```cpp
int64_t vec3_hash(vec3_t* v) {
    uint64_t h;
    memcpy(&h, &v->x, 8);
    h ^= *reinterpret_cast<uint64_t*>(&v->y) * 2654435761ULL;
    h ^= *reinterpret_cast<uint64_t*>(&v->z) * 40503ULL;
    return static_cast<int64_t>(h);
}
```

```cpp
    .hash_typed<&vec3_hash>()
```

{% endstep %}

{% step %}
**Implicit Conversion**

`.convert(from, fn)` registers an implicit converter. Fires automatically at:

* Binary ops: `vec3_t + 5` → if `vec3 op_add(vec3, vec3)`, the int 5 is converted to vec3 first.
* Native call args: `sum_components(7)` where the native expects `vec3` → 7 converts.
* Var-decl: `vec3 v = 9;` → invokes the converter.

```cpp
int64_t vec3_from_int(int64_t val) {
    double d = static_cast<double>(val);
    return reinterpret_cast<int64_t>(vec3_create(d, d, d));
}
```

```cpp
    .convert(type_id::t_int64, (void*)vec3_from_int)
```

Compatible types fall through (e.g. `t_int32` matches a `t_int64` converter).
{% endstep %}

{% step %}
**Const Methods**

Append `const` to the sig to mark a method as non-mutating. Calling a non-const method on a `const` receiver is a compile error.

```cpp
    .method("float64 length() const",  (void*)vec3_length)
    .method("void scale(float64)",     (void*)vec3_scale)
```

```cpp
int32 observe(const vec3_t v) {
    float64 len = v.length();   // OK: const
    v.scale(2.0);                // compile error: non-const on const receiver
    return 0;
}
```

{% endstep %}

{% step %}
**Per-Method Permission**

Gate a method behind a permission flag (e.g. `PERM_FFI` or custom).

```cpp
    .method("void secure(int64)", (void*)secure_op).permission(PERM_FFI)
```

Calls from modules without that permission rejected at compile.
{% endstep %}

{% step %}
**`.captures_arg(i)`**

Tells the compiler the last-registered method captures argument index `i` past the call. Calling that method with a stack-local struct as the captured arg is rejected (would dangle).

```cpp
    .method("void push(element)", (void*)arr_push).captures_arg(0)
```

{% endstep %}

{% step %}
**Finishing**

Every type builder must end with `.finish()`:

```cpp
    .finish();
```

{% endstep %}
{% endstepper %}

## Lifecycle Hooks (copy / serialize / deserialize)

Beyond factory + destructor, the builder exposes three more lifecycle hooks for types with non-trivial semantics:

* **`.copy(fn)`** - called when a variable is copy-constructed from another of the same type (`T b = a;` at var-decl). Useful for reference-counted / copy-on-write / shared-state types. `fn(src_int64) -> int64` returning the copy.
* **`.serialize(fn)`** - `fn(value_int64) -> int64` returning a `char*` string representation. Reflected via `type_reg_serialize(reg)`.
* **`.deserialize(fn)`** - `fn(str_ptr_int64) -> int64` returning a fresh value from a serialized representation.

These hooks are metadata only at the SDK level; they're invoked by callers that explicitly look them up via reflection (`type_reg_copy` / `_serialize` / `_deserialize`). Generic walkers can serialize/deserialize any registered type without knowing its concrete shape.

## Interfaces

Mark a type as an interface with `.as_interface()`. Other types declare they implement it with `.implements("Name")`:

```cpp
type_builder(e, "Stream", type_id::t_int64).as_interface();

type_builder(e, "file_t", type_id::t_int64)
    .factory_typed<&file_create>(1)
    .destructor_typed<&file_destroy>()
    .implements("Stream")
    // ...
    .finish();
```

Natives can accept `Stream` as a parameter type. The compiler accepts any type whose `.implements` list contains `"Stream"`. At the call-site ABI boundary the compiler auto-injects the concrete `type_id` before the value, so the native's signature is `(int64 concrete_tid, int64 value, ...)`. Resolve the per-concrete-type method pointer via:

```cpp
void* fn = enma::interface_method_fn(engine, (type_id)tid, "method_name");
```

**Script-level dispatch.** An interface-typed local dispatches method calls at runtime to the concrete impl, including across reassignment:

```c
Stream s = file_stream("path");   // concrete impl assigned to iface var
int64 n = s.write("hello");       // dispatches to file_stream.write
s = mem_stream(...);
int64 m = s.write("...");         // dispatches to mem_stream.write
```

The compiler emits a hidden tid slot alongside the iface local, updated on every assignment. Method calls resolve at runtime through the concrete type's method table.

## Generic Type Parameters

Declare a type parameter with `.generic_param("T")`. The parameter can be referenced in method signatures:

```cpp
type_builder(e, "hash_set", type_id::t_int64)
    .generic_param("T")
    .factory_typed<&hset_create>(0)
    .destructor_typed<&hset_destroy>()
    .method("void add(T)",      (void*)hset_add)
    .method("bool contains(T)", (void*)hset_contains)
    // ...
    .finish();
```

Script binds T at the variable declaration:

```c
hash_set<int64> s;
s.add(42);            // compile-checked: 42 is int64 ✓
s.add("oops");        // compile error: expected int64
```

The same native function serves all bindings - there's no monomorphization. The type parameter only affects compile-time type-checking at method call sites. For multi-parameter generics, call `.generic_param` multiple times (`sorted_map` declares both `"K"` and `"V"`).

### Constraining a Type Parameter

Attach an interface constraint with `.requires_iface(param, iface)`. The compiler rejects bindings whose concrete type doesn't `.implements(iface)`:

```cpp
type_builder(e, "Hashable", type_id::t_int64).as_interface().finish();

type_builder(e, "hset", type_id::t_int64)
    .generic_param("T")
    .requires_iface("T", "Hashable")
    .factory_typed<&hset_create>(0)
    // ...
    .finish();
```

```c
hset<my_hashable_t> s;   // OK, my_hashable_t implements Hashable
hset<plain_t> s;         // compile error: "type 'plain_t' does not satisfy 'T: Hashable' on hset"
```

For multiple constraints, call `.requires_iface` once per (param, iface) pair.

## Complete Registration

```cpp
type_builder(e, "vec3_t", type_id::t_struct)
    .field("x", offsetof(vec3_t, x), type_id::t_float64)
    .field("y", offsetof(vec3_t, y), type_id::t_float64)
    .field("z", offsetof(vec3_t, z), type_id::t_float64)
    .factory_typed<&vec3_create>(3)
    .destructor_typed<&vec3_destroy>()
    .method_typed<&vec3_length_sq>("float64 length_sq()")
    .method_typed<&vec3_normalize>("vec3_t normalize()")
    .property("magnitude", (void*)vec3_get_magnitude, nullptr, type_id::t_float64)
    .bin_add_typed<&vec3_add>()
    .bin_sub_typed<&vec3_sub>()
    .bin_mul_typed<&vec3_mul>()
    .bin_div_typed<&vec3_div>()
    .bin_mod_typed<&vec3_mod>()
    .bin_eq_typed<&vec3_eq>()
    .bin_lt_typed<&vec3_lt>()
    .bin_gt_typed<&vec3_gt>()
    .bin_le_typed<&vec3_le>()
    .bin_ge_typed<&vec3_ge>()
    .unary_neg_typed<&vec3_neg>()
    .subscript((void*)vec3_get_idx, (void*)vec3_set_idx)
    .iterable((void*)vec3_iter_len, (void*)vec3_iter_get)
    .hash_typed<&vec3_hash>()
    .finish();
```

Every hook with a `_typed<&Fn>()` form forwards `Fn` to the underlying raw-`void*` registration. The native is called directly via Win64 ABI - no trampoline, no int64 bit-casting. Available `_typed` variants: `factory`, `destructor`, `method`, `property`, `subscript`, `bin_add/sub/mul/div/mod`, `bin_eq/lt/gt/le/ge`, `bin_*_assign`, `increment`, `decrement`, `unary_neg`, `unary_bit_not`, `bit_and/or/xor`, `shl`, `shr`, `compare`, `copy`, `hash`.

**Typed property:**

```cpp
int64_t vec3_get_x(vec3_t* self)               { return bits_of(self->x); }
void    vec3_set_x(vec3_t* self, int64_t bits) { self->x = double_from_bits(bits); }

type_builder(e, "vec3_t", type_id::t_struct)
    .property_typed<&vec3_get_x, &vec3_set_x>("x", type_id::t_float64);
```

Pass `nullptr` (the default `SetFn`) for a read-only property:

```cpp
.property_typed<&get_magnitude>("magnitude", type_id::t_float64);   // read-only
```

**Typed subscript:** getter signature `T(U*, int64_t)`, setter `void(U*, int64_t, T)`:

```cpp
.subscript_typed<&bag_get, &bag_set>();
```

## Struct Builder

Lightweight registration for data-only structs (no methods or custom lifecycle).

```cpp
struct_builder(e, "point_t")
    .field("x", type_id::t_int64)
    .field("y", type_id::t_int64)
    .finish();
```

Field sizes use `__util_type_size` (int32 = 4, etc.) but each field rounds up to an 8-byte slot by default. Append `.packed()` for C-compatible packed layout.

```cpp
struct_builder(e, "point_t").packed()
    .field("x", type_id::t_int32)
    .field("y", type_id::t_int32)
    .finish();
```

Script usage:

```cpp
point_t p = point_t(10, 20);
println(p.x);
```

Generated constructor takes args in field declaration order.

## Enum Builder

Register named integer constants grouped under a type name. Scripts access values with `::` syntax.

```cpp
enum_builder(e, "Color")
    .value("Red", 0)
    .value("Green", 1)
    .value("Blue", 2)
    .finish();
```

Script usage:

```cpp
int32 c = Color::Red;
if (c == Color::Green) {
    println("green");
}
```

## Value-Type Registration

By default, `type_builder` registers a **reference type**: every script value is an 8-byte handle pointing at a heap allocation. `vec3 v` is a pointer; `vec3[]` is an array of pointers; passing `v` to a function copies the pointer, not the data.

For small POD-like types (vec3, quat, mat4, color, etc.) the heap overhead dominates the actual work. Opt in to **value-type semantics** with three builder hooks:

```cpp
type_builder(e, "vec3", type_id::t_int64)
    .value_type(sizeof(vec3_t))              // (1) declare size — enables inline storage
    .factory_in_place((void*)vec3_construct) // (2) write-into-buffer ctor
    .inline_property("x", (void*)vec3_get_x, (void*)vec3_set_x,
                     type_id::t_float64, offsetof(vec3_t, x))   // (3) inline accessor
    .inline_property("y", (void*)vec3_get_y, (void*)vec3_set_y,
                     type_id::t_float64, offsetof(vec3_t, y))
    .inline_property("z", (void*)vec3_get_z, (void*)vec3_set_z,
                     type_id::t_float64, offsetof(vec3_t, z))
    // ... factory / methods / operators stay the same ...
    .finish();
```

What each hook does:

1. **`.value_type(N)`** marks the typereg as inline-storable. Containers (`vec3[]`, future `list<vec3>`) will allocate `N` bytes per slot and store the value's bits directly — no handle indirection, no per-element heap alloc. Reads through `xs[i]` return a pointer to the slot; writes propagate through it. `N` must match `sizeof(YourType)` exactly.
2. **`.factory_in_place(fn)`** registers a ctor that **writes into a provided buffer** instead of allocating one. The signature is `int64_t fn(int64_t dst, args...)` — `dst` is the destination buffer (heap or stack), `args` match the factory signature. Return `dst` for chaining. Compared to the regular `.factory()`, this version skips `heap_alloc(N)` per call:

   ```cpp
   int64_t vec3_construct(int64_t dst, double x, double y, double z) {
       auto* v = reinterpret_cast<vec3_t*>(dst);
       v->x = x; v->y = y; v->z = z;
       return dst;
   }
   ```

   When the script writes `vec3 v = vec3(1, 2, 3)`, the compiler stack-allocates the value (if it doesn't escape) and calls `construct_in_place_fn` once to fill it. `new vec3(...)` still routes through the regular `.factory()` so explicit heap allocations work.
3. **`.inline_property(name, getter, setter, type, byte_offset)`** swaps the native getter/setter for a direct field load/store at the given offset. When the getter is a trivial field read (`return reinterpret_cast<T*>(h)->field`), the offset is enough — the compiler emits a direct memory load. The native fn pointers stay registered as fallbacks (interop, reflection, host-side calls). Use the normal `.property(...)` form for non-trivial getters (computed properties, validation, etc.).

### What this buys you

For `vec3 v = vec3(1.0, 2.0, 3.0); float64 s = v.x + v.y + v.z;`:

|                                                          | Per call cost                                                   |
| -------------------------------------------------------- | --------------------------------------------------------------- |
| Regular `.property` + `.factory` (handle type)           | heap\_alloc(24) + ctor + 3× native getter call + heap\_free(24) |
| `.value_type` + `.factory_in_place` + `.inline_property` | stack alloc + ctor + 3× direct field load                       |

In a 10M-iter benchmark of `acc + v.x + v.y + v.z`, the value-type version runs in \~67ms vs \~145ms for the handle version (\~2.2× faster). The bigger win is in containers: a `vec3[]` of N elements stores N × 24 bytes contiguously instead of N × 8B handles to N scattered 24B heap blocks — cache-friendly iteration plus zero per-element allocation.

### Constraints

* Your native type must be POD-shaped (no constructor, no destructor, no virtual methods on the C++ side). The Enma compiler / runtime treats the bytes as opaque storage.
* `.value_type(N)` is mutually compatible with `.destructor()` — the dtor still fires on scope exit for heap-allocated instances (the runtime distinguishes stack vs heap addresses).
* Inline storage applies to **arrays** (`T[]`) and **lists** (`list<T>`). Maps, sorted\_maps, and hash\_sets store 8B handles for now.
* Property reads/writes only inline when `inline_offset >= 0`. The default `.property(...)` keeps the native-call path — opt in explicitly via `.inline_property(...)` only for trivial accessors.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/type-registration.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
