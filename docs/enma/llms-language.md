> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/llms-language.md).

# LLMS - Language

## LLMS-Language: Complete Language Reference

Enma is a statically-typed, full-module AOT and JIT-compiled scripting language. File extension is `.em`. Source compiles to native x64 machine code.

This page covers the whole language plus every shipped addon. For embedding and addon authoring, see `LLMS-SDK.md`.

***

### 1. Program Structure

A `.em` file contains top-level declarations: functions, structs, classes, enums, globals, `import`, `using`, `namespace`, preprocessor directives, annotations.

Entry point is `int32 main()` (or any function the host chooses to execute).

```c
int32 main() {
    println("hello");
    return 0;
}
```

No file-level module header required. Multiple files can be imported (see Modules).

***

### 2. Primitive Types

| Type      | Size | Notes                                                           |
| --------- | ---- | --------------------------------------------------------------- |
| `bool`    | 1B   | `true` / `false`                                                |
| `char`    | 1B   | 8-bit character                                                 |
| `wchar`   | 2B   | Wide character                                                  |
| `int8`    | 1B   | Signed 8-bit                                                    |
| `int16`   | 2B   | Signed 16-bit                                                   |
| `int32`   | 4B   | Signed 32-bit                                                   |
| `int64`   | 8B   | Signed 64-bit (native arithmetic width)                         |
| `uint8`   | 1B   | Unsigned 8-bit                                                  |
| `uint16`  | 2B   | Unsigned 16-bit                                                 |
| `uint32`  | 4B   | Unsigned 32-bit                                                 |
| `uint64`  | 8B   | Unsigned 64-bit                                                 |
| `aint8`   | 1B   | Atomic 8-bit                                                    |
| `aint16`  | 2B   | Atomic 16-bit                                                   |
| `aint32`  | 4B   | Atomic 32-bit                                                   |
| `aint64`  | 8B   | Atomic 64-bit                                                   |
| `float32` | 4B   | IEEE single                                                     |
| `float64` | 8B   | IEEE double                                                     |
| `string`  | ptr  | UTF-8 heap string                                               |
| `wstring` | ptr  | UTF-16 heap string (uint16\_t code units, Win32 wchar\_t shape) |
| `void`    | 0    | No value                                                        |
| `null`    | -    | Null literal (assignable to any pointer/nullable)               |
| `auto`    | -    | Type inferred from initializer                                  |

**Integer semantics:** All arithmetic evaluates at 64-bit width internally. Overflow wraps silently at 64 bits. The declared int width controls storage size but not arithmetic precision.

**Implicit-conversion rules** (all enforced at compile time):

* Same-sign widen / narrow: implicit. `int32 ↔ int64`, `uint32 ↔ uint64` all fine.
* Signed ↔ unsigned (any width): **compile error** without `cast<T>(x)`. Catches `uint64 b = -1;` and friends.
* `int → float`: implicit.
* `float → int`: **compile error** without `cast<int>(x)`. Truncation is too easy to miss.
* `float32 → float64`: implicit.
* `float64 → float32`: **compile error** without `cast<float32>(x)`.
* Integer / float **literals** are exempt from the strict checks. `uint32 a = 5;` and `float32 f = 1.5;` both compile.
* `pointer ↔ int64 / uint64`: implicit (both 8-byte slots).
* `function → int64 / uint64 / pointer`: implicit. Lets you pass script-side function references to int64 native parameters as `register_callback(my_fn, ...)`, `register_callback(&my_fn, ...)`, or `register_callback(cast<int64>(my_fn), ...)`.

**Float semantics:** Standard IEEE-754. `float32` is narrowed at the native ABI but script-side values keep 64-bit view for precision.

***

### 3. Variables & Constants

```c
int32 x = 42;
const float64 PI = 3.14;
constexpr int32 MAX = 100;
auto y = x + 1;           // y inferred as int32
nullable int32 n = null;  // n can hold null
```

`const`: runtime-initialized, not reassignable after init. `constexpr`: compile-time evaluated. Only compile-time constants allowed in the initializer. `nullable T`: a distinct type that can hold `null`. Non-nullable types cannot. `auto`: right-hand side must have a definite type.

**Global variables** are top-level declarations. Initialized before `main` runs:

```c
int32 counter = 0;
Player g_player = Player();

int32 main() {
    counter = counter + 1;
    return counter;
}
```

***

### 4. Operators

| Category   | Operators                                                              |
| ---------- | ---------------------------------------------------------------------- |
| Arithmetic | `+ - * / %`                                                            |
| Comparison | `== != < > <= >=`                                                      |
| Logical    | \`&&                                                                   |
| Bitwise    | `& \| ^ ~ << >>`                                                       |
| Assignment | `= += -= *= /= %= &= \|= ^= <<= >>=`                                   |
| Inc/Dec    | `++ --` (prefix and postfix)                                           |
| Ternary    | `cond ? a : b`                                                         |
| Cast       | `cast<T>(x)`                                                           |
| Sizeof     | `sizeof(T)` (bytes)                                                    |
| Offsetof   | `offsetof(Struct, field)` (bytes)                                      |
| Heap       | `new T(args)`, `new T[N]`, `new T[N](ctor_args)`, `delete`, `delete[]` |
| Deref      | `*pt` — independent shallow copy of `T*` pointee (memberwise)          |
| Move       | `move(x)` — transfer ownership; source nulled                          |
| Member     | `x.field`, `p->field`, `x.method()`, `p->method()`                     |
| Address-of | `&var` (must be assigned to pointer type)                              |
| Scope      | `Namespace::name`, `Enum::Value`                                       |
| Subscript  | `a[i]`, `m[k]`                                                         |

**Cast targets:** int↔float, int↔bool, numeric narrowing/widening. `cast<string>(int8..int64 / uint8..uint64 / float / bool / char)` via string addon's registered converters — narrow uints (uint8/uint16) routed through the same int\_to\_str path since values live zero-extended in 64-bit register slots.

`sizeof` and `offsetof` are compile-time constants, usable in `constexpr`.

***

### 5. Control Flow

#### if / else

```c
if (x > 0)       { println("positive"); }
else if (x == 0) { println("zero"); }
else             { println("negative"); }
```

#### while / do-while

```c
while (x > 0) x = x - 1;

do { x = x + 1; } while (x < 10);
```

#### for

```c
for (int32 i = 0; i < 10; i++) println(i);
```

#### for-each

```c
int32[] arr = {1, 2, 3};
for (int32 v : arr) println(v);

map<string, int64> m;
for (int64 v : m) println(v);              // values
for (string k, int64 v : m) println(k);    // keys + values
```

#### switch

```c
switch (x) {
    case 1: println("one"); break;
    case 2: println("two"); break;
    default: println("other");
}
```

No implicit fallthrough; add `break` explicitly or let the arm end.

#### match (expression)

```c
int32 r = match (x) {
    1 => 10,
    2 => 20,
    _ => 0
};

int32 r2 = match (x) {
    case 1 => { return 10; },
    _ => { return 0; }
};
```

`case` keyword optional. `_` is the default arm. Returns a value.

#### defer

Runs at scope exit, including during stack unwinding from an exception.

```c
int64 h = open_resource();
defer { close_resource(h); }
```

#### goto

```c
goto done;
println("skipped");
done:
println("reached");
```

#### break / continue

Exit or skip the innermost loop.

***

### 6. Functions

```c
int32 add(int32 a, int32 b) { return a + b; }
```

#### Default parameters

```c
int32 add(int32 a, int32 b = 10) { return a + b; }
add(5);     // 15
```

#### Overloading (by parameter type or arity)

Free functions, methods, and constructors may share a name as long as the parameter lists differ — by **type**, by **count**, or both. The call site picks the variant from the argument types.

```c
int64   area(int64 side)  { return side * side; }
float64 area(float64 r)   { return 3.14159 * r * r; }
area(4);       // -> int64 overload
area(2.0);     // -> float64 overload

struct Vec { int64 x; int64 y; }
int64 mag(Vec v)  { return v.x * v.x + v.y * v.y; }   // by struct type
int64 mag(int64 n){ return n < 0 ? 0 - n : n; }       // vs scalar
```

Works for methods and constructors too:

```c
class Box {
    int64 tag;
    Box(int64 v) { tag = v; }
    Box(string s) { tag = cast<int64>(s.length()); }   // ctor overload
    int64 put(int64 n) { return n; }
    int64 put(string s) { return cast<int64>(s.length()); }   // method overload
}
Box b = Box("hi");      // string ctor
b.put(5);               // int64 method
```

Resolution: an **exact** type match wins; otherwise a single widening step is applied — `int → int`, `float → float`, `int → float`, or derived→base. `int → int` is preferred over `int → float`, so `area(4)` (an `int` literal) chooses the `int64` overload, not `float64`. A call that matches no variant, or two equally, is a **compile error** (never a silent mis-dispatch).

You **cannot** overload on return type alone — two functions with identical parameter types but different return types is a compile error. (A plain forward declaration followed by its definition is *not* an overload.)

#### Reference parameters (`&`)

Pass-by-reference; callee mutates caller's variable. No `&` at call site.

```c
void swap(int32& a, int32& b) {
    int32 t = a; a = b; b = t;
}
int32 x = 1; int32 y = 2;
swap(x, y);    // x=2, y=1
```

#### Out parameters (`out`)

Like `&` but signals the param is write-only; caller's initial value is not read.

```c
bool try_parse(string s, out int32 v) {
    if (s == "42") { v = 42; return true; }
    return false;
}
```

#### Local references & return-by-reference

`T& r = x;` aliases a variable, field, or another reference (initializer required; expressions/temporaries rejected). `T& f()` returns a reference the caller reads (auto-dereferenced) or assigns through.

```c
int64 x = 5;
int64& r = x; r = 9;             // x is now 9

class Counter { int64 v; int64& slot() { return v; } }
Counter c; c.slot() = 42;        // writes c.v
```

A reference can also bind to an **array element** — `T& e = arr[i]` — for value-struct elements and 8-byte scalar elements (`int64` / `uint64` / `float64`). Writes through the reference hit the live element in place.

```c
struct P { int64 x; int64 y; }
P[] a; a.push(P{.x=1, .y=2});
P& e = a[0]; e.x = 77;           // a[0].x is now 77

int64[] ns; ns.push(5);
int64& s = ns[0]; s = s + 4;     // ns[0] is now 9
```

A function may return a scalar element by reference (the `at()` / `operator[]` pattern): `int64& at(int64 i) { return data[i]; }`. **Narrow** scalar element references (`int32`, `int16`, `int8`, `float32`) and `atomic` elements are rejected at compile time — they would need width-aware reference I/O.

#### Pointer-to-member functions (`.*` / `->*`)

`R (Cls::*pmf)(args)` holds a method address; the receiver is supplied at the call. Take it with `@Cls::method` or `&Cls::method`; call with `(obj.*pmf)(args)` or `(ptr->*pmf)(args)`. Dispatch is non-virtual.

```c
class Foo { int64 dbl(int64 a) { return a * 2; } }
typedef int64 (Foo::*Fn)(int64);
Foo f; Fn pmf = &Foo::dbl;
int64 r = (f.*pmf)(21);          // 42
```

A **null PMF call is recoverable** — `Pmf p = 0; (obj.*p)(args);` raises a runtime error caught by a script `try`/`catch`, never a host AV. (Previously the indirect call to address 0 faulted past the JIT-range SEH guard; a null-check is now inserted before the indirect call.)

#### Variadic (`...` with `__va_count` / `__va_arg`)

```c
int64 sum(...) {
    int64 s = 0;
    int64 i = 0;
    while (i < __va_count) { s = s + __va_arg(i); i = i + 1; }
    return s;
}
sum(1, 2, 3);     // 6
```

All args passed as int64 slots. Mixed types, callee interprets each.

#### Forward declarations

```c
int32 foo(int32);          // forward declared

int32 bar() { return foo(5); }
int32 foo(int32 x) { return x * 2; }
```

#### extern (host to script boundary)

```c
extern int32 host_fn(int32);   // resolved by SDK-registered native
```

#### `const` methods

Mark a method that doesn't mutate `this`. Callable on `const` receivers.

```c
struct Vec { int32 x; int32 y; int32 get_x() const { return x; } }

const Vec v;
int32 a = v.get_x();   // OK
```

#### Function references

Assign a function to a variable of its matching delegate type.

```c
delegate int32 BinOp(int32 a, int32 b);
int32 add(int32 a, int32 b) { return a + b; }
BinOp op = add;
int32 r = op(3, 4);
```

#### Lambdas (bracket style)

```c
delegate int32 Transform(int32 x);
Transform fn = [](int32 x) -> int32 { return x * 2; };
int32 r = fn(21);     // 42
```

#### Lambdas (arrow style)

Expression body:

```c
Transform fn = (int32 x) => x * 2;
```

Block body:

```c
int64 fn = (int32 a, int32 b) => {
    int32 s = a + b;
    return s * 2;
};
```

Zero params:

```c
int64 fn = () => 42;
```

Struct-returning lambdas:

```c
struct Box { int64 v; Box(int64 x) { v = x; } }

auto make = (int64 x) => Box(x);     // returns value-struct into caller's slot
Box b = make(42);                     // caller-allocated buffer
```

The compiler detects struct return types (explicit or inferred) and writes the value directly into the caller's return slot, rather than escaping the local. No `new` needed for value-struct returns from lambdas. Use `new` only when the caller wants a heap pointer (`auto make = (int64 x) => new Box(x);` returns `Box*`).

#### Closures

Auto-capture variables from enclosing scope:

```c
int32 base = 100;
Transform adder = [](int32 x) -> int32 { return base + x; };
adder(5);   // 105
```

Explicit captures:

```c
Transform fn = [base](int32 x) -> int32 { return base + x; };
Transform fn = [&base](int32 x) -> int32 { return base + x; };   // by reference
```

***

### 7. Pointers

Heap pointers are typed handles. Allocate with `new`, free with `delete`. Access fields/methods with `->` (idiomatic for pointers) or `.` — the parser accepts either form for both pointers and value structs; follow the convention for readability. Pointer arithmetic (`p + n`, `++p`, `p[i]`, `p - q`) is supported on typed pointers, scaled by the element. Pointer ↔ `int64`/`uint64` is implicit (both 8-byte slots).

#### Allocation

```c
struct Node { int32 v; Node(int32 x) { v = x; } }

Node* p = new Node(42);
println(p->v);         // 42. use `->` for pointer access; `.` is for value structs
delete p;
```

#### Null

```c
Node* p = null;
if (p == null) { }
if (p != null) { delete p; }
```

#### Aliasing

```c
Node* a = new Node(1);
Node* b = a;           // same object
b->v = 99;             // visible through a
delete a;              // b now dangles
```

#### Copy via `*pt`

Dereference produces a fresh heap-allocated copy of the pointee. Field-by-field shallow copy (matches C++ default copy ctor): primitives by value, inline struct fields recurse, pointer fields stay shallow.

```c
Pt* a = new Pt(1, 2);
Pt  b = *a;            // independent copy
b.x = 99;
println(a->x);         // still 1
```

For deep copy of heap-managed sub-objects (string, array, nested class held by reference), define an explicit `clone()` on the class.

#### Move via `move(x)`

Transfers ownership: returns x's value AND nullifies the source slot. Subsequent access null-faults.

```c
Pt* a = new Pt(1, 2);
Pt* b = move(a);       // b inherits, a becomes null
println(b->x);         // 1
// println(a->x);      // null deref - traps
```

Distinct from `*pt` which copies and leaves the source intact. Currently `move()` only accepts a simple variable name (subscript / field expressions error at compile time).

#### Heap arrays

```c
struct P { int32 x; int32 y; P() { x = 0; y = 0; } }
P* ps = new P[10];              // default-ctor each
delete[] ps;                     // dtor each, then free

P* ys = new P[4](3, 5);          // every elem ctor'd with (3, 5)
delete[] ys;
```

Args after `[N]` evaluated once and forwarded to each element's ctor.

#### Address-of

`&var` must feed a pointer type. Taking the address and storing it where it could dangle is a compile error.

```c
int32 a = 5;
int32* p = &a;           // OK, p lives for a's lifetime
return p;                // compile error if &a is a local (escape)
```

#### Reference parameters (not pointers)

`T& param` - see Functions: Reference parameters.

#### Escape errors, rejected at compile time

```c
struct Pt { int32 x; int32 y; }
Pt g;
Pt* g_ptr;

int32 bad() {
    Pt p;
    g_ptr = &p;          // error: stack ptr escapes
    return 0;
}

int32 ok() {
    Pt* p = new Pt();
    g_ptr = p;           // OK (heap)
    return 0;
}
```

#### Rejected operations

| Pattern                                | Result        |
| -------------------------------------- | ------------- |
| `int64 i = 0x100; T* p = i;`           | compile error |
| `int64 a = cast<int64>(p);`            | compile error |
| `T* p = &s + 8;`                       | compile error |
| `T x = new T();`                       | compile error |
| `delete x;` where `x` is a value       | compile error |
| Returning `&local`                     | compile error |
| Storing `&local` to a global           | compile error |
| Escaping closure captures stack struct | compile error |

#### Runtime traps

* Null deref through pointer
* Out-of-bounds on `T[]` array
* Use-after-free while marker still set
* Double `delete[]` on heap arrays

***

### 8. Structs

Value types. Stack-allocated by default, heap with `new`.

```c
struct Point {
    int32 x;
    int32 y;
    Point(int32 ix, int32 iy) { x = ix; y = iy; }
    int32 sum() { return x + y; }
    ~Point() { /* dtor runs at scope exit */ }
}

Point p;            // default-ctor or zero-init
Point q = Point(3, 4);
Point r = {5, 6};                 // positional init
Point s = {.x = 7, .y = 8};       // designated init
Point t = {.y = 5};               // .x zero-init
```

#### Fields + bitfields

```c
struct Flags {
    uint32 ready : 1;
    uint32 mode  : 3;
    uint32 reserved : 28;
}
```

#### Packed + aligned

Struct-level annotations:

```c
[[packed]] struct Header { uint8 kind; uint32 size; }       // no padding (1+4 = 5 bytes)
[[align(16)]] struct Vec4 { float32 x, y, z, w; }            // total size rounded to 16
```

Per-field annotations — useful for matching reverse-engineered game-struct layouts (FVector, FRotator, hand-crafted packets, etc.):

```c
// [[align(N)]] forces THIS field's offset to N-byte alignment
// (also bumps the struct's total alignment to >= N).
struct Lane {
    int64 hdr;
    [[align(16)]] vec3 pos;     // pos at offset 16, not 8
    int64 ftr;
}

// [[offset(N)]] forces an exact byte offset (decimal or hex).
// Compile error if it would overlap a prior field.
struct GameEntity {
    [[offset(0x10)]] int64 health;
    [[offset(0x40)]] vec3  position;
    [[offset(0x80)]] int64 team_id;
}

// Combined for Unreal-style FVector (3 float32, 16-byte aligned for SIMD):
[[packed]] [[align(16)]] struct FVector { float32 x; float32 y; float32 z; }
// → size=16, x=0, y=4, z=8
```

Without `[[packed]]`, primitive field sizes are bumped to 8 bytes for handle compatibility. Use `[[packed]]` to match exact C/C++ layouts (each primitive at its natural width).

#### Constructors and destructors

Member fields with constructors auto-fire when their parent constructs (declaration order); destructors fire in reverse declaration order between the user dtor body and any base class dtor chain. Mirrors C++ exactly.

```c
struct Inner {
    int64 v;
    Inner() { v = 42; }
    ~Inner() { /* fires automatically when parent goes out of scope */ }
}

struct Outer {
    Inner a;
    Inner b;
    Outer() { /* a.ctor + b.ctor have already fired by now */ }
    ~Outer() {
        // user body runs first
        // ...then b.~Inner(), a.~Inner() fire in reverse declaration order
        // ...then any base class dtor chain
    }
}

{ Outer o; }   // → a.ctor, b.ctor, Outer.ctor; then ~Outer, ~b, ~a
```

Containers as fields (`string`, `list<T>`, `map<K,V>`, `hash_set<T>`, `sorted_map<K,V>`, `imap<V>`, `vec3`, `T[]`) auto-init to empty at parent construction and clean up on destruction. Class-V elements (`list<Player>`, `map<string, Item>`, etc.) get their `~T()` called per element before the container's heap is freed — so RAII state nested inside elements doesn't leak.

Ctor init list overrides default auto-init: `Outer() : a(arg) {}` runs `Inner(arg)` for `a` instead of the no-arg default. **Init order follows declaration order, not init-list source order** (matches C++). `Owner() : c(), b(0) {}` with declared layout `A a; B b; C c;` runs `a.ctor → b.ctor(0) → c.ctor → body`. Init-list source order controls *what* runs for each field, not *when*.

#### Passing semantics

C++ value semantics. Pass-by-value is a copy; assignment is a copy; return is a copy. Mutating a param's fields does NOT touch the caller. Use `T*` if you want reference semantics.

```c
struct Box { int64 v; Box(int64 x) { v = x; } }
void mutate(Box b)       { b.v = 999; }    // b is a local copy
void mutate_ref(Box* b)  { b->v = 999; }   // pointer to caller's Box

Box a = Box(7);
mutate(a);          // a.v still 7
mutate_ref(&a);     // a.v now 999

Box c = a;          // independent copy
c.v = 1;            // a.v unchanged
```

Same inside operator overloads — `operator+(T other)` receives a copy of `other`; the caller's value is not affected by writes to `other`.

#### Methods, operators, properties

Method receivers have access to fields directly or via `this->field`.

```c
struct Vec2 {
    int32 x;
    int32 y;
    Vec2 operator+(Vec2 o) { return Vec2(x + o.x, y + o.y); }   // via .bin_add on SDK types
    property int32 mag_sq { get { return x*x + y*y; } }
}

Vec2 a = Vec2(1, 2);
int32 m = a.mag_sq;    // no parens; calls the getter
```

Overloadable operators on script structs:

* Binary arithmetic: `+ - * / %` — `T operator+(T o)`
* Comparison: `== != < > <= >=` — `bool operator==(T o)`. `!=` auto-negates `==` if not defined.
* Bitwise / shift: `& | ^ << >>` — `T operator&(T o)`
* Compound assign: `+= -= *= /= %= &= |= ^= <<= >>=` — `void operator+=(T o)` (mutates `*this`). Auto-falls-back to `a = a + b` if only the binary form is defined.
* Copy assignment: `=` — `void operator=(T o)` for already-constructed receiver (`b = a;` after `T b;`). Distinct from copy ctor (`T b = a;` constructs b). Lets the type release b's old resources before adopting a's.
* Increment / decrement: `++ --` — `T operator++()` is prefix (`++a`); `T operator++(int)` is postfix (`a++`). Int dummy param matches C++. If only one form is declared, both prefix and postfix dispatch through it.
* Unary: `- ~ ! *` — `T operator-()` / `bool operator!()` (zero user args). `U operator*()` is smart-pointer-style deref: when the operand is a value struct (not a `T*`), `*obj` dispatches to it; pointer deref of `T*` keeps memberwise-copy semantics.
* Three-way comparison: `<=>` — `int64 operator<=>(T o)`. Define one, all six comparison ops (`< > <= >= == !=`) auto-derive: `a < b` becomes `(a <=> b) < 0`. Negative/zero/positive convention. Explicit specific overloads (e.g. `bool operator<`) take priority over `<=>` when both are defined. Derived classes inherit `operator<=>` from any base in the chain — `Derived a, b; a < b;` works as long as some base defines it.
* Subscript: `[]` (read) and `[]=` (write, declared separately) — `T operator[](int64 i)` and `void operator[]=(int64 i, T v)`.
* Function call: `()` — `T operator()(args...)` makes the type callable: `obj(arg1, arg2)`.
* Type conversion: `operator T()` — fires on `cast<T>(obj)` AND implicitly at four sites: variable init (`T2 v = obj`), function-argument binding (`f(obj)` where f takes T2), return statements (`T2 g() { return obj; }`), and arithmetic operands (`obj + 5` falls back to `cast<int64>(obj) + 5` when no `operator+` is defined). T can be a primitive (int64, bool, float64, ...) OR another struct (cross-struct conversion: `B y = a;` for A defining `operator B()`).
* Copy constructor: `T(const T& other)` — overrides default memberwise copy on `T c = a;`. Source remains valid.
* Move constructor: `T(T&& other)` — fires on `T c = move(a);`. Source is nulled after the call. Falls back to copy ctor if move ctor is missing.
* Smart-pointer `operator->`: `U* operator->()` — `obj->member` reads a field on the returned pointer; `obj->method(args...)` calls a method on it. Both forms resolve through the operator's declared return type (`U`).
* `explicit` ctor / conversion op: `explicit T(arg)` / `explicit operator U()` — blocks implicit conversion through it; only direct construction `T(arg)` and `cast<U>(x)` invoke it. Implicit use (`T t = arg;`, by-value arg, return) is a compile error. Without `explicit`, those conversions fire implicitly.
* Free-function operators: declared at module / namespace scope rather than inside a struct: `bool operator==(P a, P b) { ... }` / `P operator+(P a, P b) { ... }`. Take both operands explicitly (no `this`). Inside a `namespace`, free operators are found via **Argument-Dependent Lookup (ADL)** — `ns::P x, y; if (x == y)` resolves `ns::operator==` even though the call site is unqualified and outside the namespace. The compiler walks the operand type's enclosing namespace chain. Member operators on the receiver type take priority over free operators. Free operators returning a value-struct go through the same SRET / NRVO path as struct-method operators, and their return type is visible to `auto z = x + y;` and `return x + y;`.

Not overloadable: logical (`&& ||`, short-circuit), comma (`,`).

#### Syntax differences from C++

**Works the same as C++:** `auto`, range-based `for (auto x : c)`, lambdas, ternary `a ? b : c`, C-style cast `(T)x` and `static_cast<T>(x)`, `nullptr` (also `null`), `default` param values, `constexpr`, `typedef`, `using` aliases, `switch / case`, `throw / catch`, `new T[N]` / `delete[]`, struct field default init `int64 x = 5;`, ctor delegation `T() : T(0)`, init lists `T p = {1, 2}`, designated init `T p = {.x=1}`, hex `0xFF`, binary `0b1010`.

**Different / Enma-specific:**

* Arrays: `int64[]` not `array<int64>`; `arr.push(x)` not `push_back(x)`. `array<T>` is the SDK type for type-builder registrations; in scripts you use the `T[]` syntax.
* Cast: `cast<T>(x)` is the idiomatic form (also accepts `(T)x` and `static_cast<T>(x)`).
* `reinterpret_cast<T>(x)` — bit-pattern reinterpret (no value conversion); source and target must be the same byte width. **Pointer↔pointer (any pointee types), pointer↔int64, and `void*` all work**, so you can take a raw address as `int64` and turn it back into a typed pointer: `int64 addr = reinterpret_cast<int64>(p); T* q = reinterpret_cast<T*>(addr);`. `const_cast<T>(x)` strips const for write access (same-width identity at runtime).
* `defer expr;` (Go-style) — NOT in C++.
* `namespace` supports nested struct / class declarations; access as `ns::Inner(args)` or via `using namespace ns;` then `Inner(args)`.
* Underscore digit separators are supported in all numeric literal forms: `1_000_000`, `0xFF_FF`, `0b1010_1100`, `1_234.567_8`, `1_000e3`. Underscores are stripped at lex time. UDL suffixes like `42_km` (alpha after `_`) still terminate the number cleanly.
* Trailing return types are supported: `auto add(int64 a, int64 b) -> int64 { return a + b; }` works the same as the leading form.
* `enum class X { ... }` and `enum struct X { ... }` are accepted as syntactic aliases for plain `enum X { ... }`. Enma's enums are already strongly typed (no implicit conversion to int — you must `cast<int64>(Color::Red)`), so the scoped-enum keyword is purely cosmetic.
* `<=>` (three-way comparison) IS supported on script-defined classes — see operator overloading below.
* C++17 if-init: `if (T x = expr; cond) { ... }`. `x` scopes over both the body and the else branch.
* Direct uniform init: `T t = T{1, 2}`, `f(T{1, 2})`, `return T{1, 2};`. Same shape as `T(1, 2)` ctor call. (Statement-level `T { ... }` is intentionally still parsed as `T;` followed by a block to avoid breaking existing scripts.)
* `friend` declarations are accepted and ignored — Enma doesn't enforce private/public access controls at the script level, so friend is vestigial.
* `final` (after class name) and `virtual` (on methods) are accepted as no-ops — Enma's method dispatch is already vtable-based for inherited classes, and there's no concept of a sealed class.

**Real gaps (don't compile in Enma but exist in C++):**

* `typeid`, `if constexpr`, structured bindings (`auto [a, b] = pair;`), lambda init-captures (`[x = expr]`), `T&&` rvalue refs (return position), rethrow `throw;`, `extern "C"`, `thread_local`. (Concepts/`requires`, SFINAE, template explicit AND partial specialization, alias/default/member templates, variadic function AND class templates incl. zero-element packs, recursive variadic with either a non-template or a 1-arg template base, a parameter pack used as struct fields (`Ts... members`), overloaded function templates, CTAD, explicit deduction guides, template-template parameters, NTTP incl. enum constants, fold expressions, AND **ADL — Argument-Dependent Lookup including for templated operators** DO work — see §15.) `dynamic_cast<T*>(ptr)` is supported via vtable identity (no RTTI strings leaked) — see §4.

**Parsed but not enforced (silent no-op):**

* `private:` / `public:` — accepted in struct/class bodies but fields are always accessible
* `static` on global variables — accepted (globals are already module-scoped)

***

### 9. Classes

Reference types with single OR multiple inheritance, virtual dispatch, and RAII. Methods are virtual by default when the class participates in inheritance; there's no explicit `virtual` keyword. Mark the override with `override`.

```c
class Entity {
    int32 hp;
    Entity(int32 h) { hp = h; }
    int32 get_hp() { return hp; }
    ~Entity() {}
}

class Player : Entity {
    int32 xp;
    Player(int32 h, int32 x) { hp = h; xp = x; }  // set base fields directly
    int32 get_hp() override { return hp + xp * 10; }
}

Player p = Player(100, 5);
p.get_hp();       // 150
```

* No explicit `virtual` keyword. Dispatch is virtual for methods overridden in a derived class.
* **Multiple inheritance** is supported: `class C : A, B { ... }`. Each base contributes its own subobject in declaration order; ctors fire in declaration order, dtors in reverse. Diamond inheritance is rejected at compile time. If two bases declare the same method name, the derived class must `override` it. Upcast (`A* a = new C();` or `B* b = c;`) shifts the pointer to the right base subobject. Works in var-decl, function args, assignment, and return contexts. Virtual dispatch through any base pointer (primary or non-primary) reaches the derived override via auto-synthesized `this`-adjusting thunks. A class with BOTH a concrete data base AND an interface dispatches correctly through an interface **reference** or **pointer** regardless of base declaration order (`class Task : Base, P` works the same as `class Task : P, Base`). Remaining caveat: passing such an object **by value** to an interface parameter (`int64 f(P p)` where `P` is a non-primary base) can still misdispatch — pass by reference (`P&`) or pointer (`P*`) instead.
* `override` required when overriding.
* Derived constructors can chain base ctors with a `: Base(args), Other(args)` initializer list (runs before the body, in base declaration order) — `class C : A, B { C(int x, int y) : A(x), B(y) { } }`. You can also just set inherited base fields directly in the body. A base with no init-list entry is default-constructed (needs a no-arg ctor).
* Destructor chain runs derived-then-base automatically (LIFO base order for multi-inheritance).

#### Static members

A `static` field has ONE shared slot for the whole class — not a per-instance field. Read or write it through the class (`C::field`), through any instance (`c.field`), or by the bare name inside a method; every route hits the same storage, so a write through one is visible through all. Compound assignment works. An initializer is optional.

```c
class Widget {
    static int64 alive = 0;          // shared across all Widgets
    int64 id;
    Widget() { alive = alive + 1; id = alive; }   // bare name = the static
}

Widget a; Widget b;
int64 n = Widget::alive;             // 2
Widget::alive = 0;                   // write through the class name
b.alive = b.alive + 5;               // ...or through an instance
```

***

### 10. Interfaces

Method-signature contracts. Implementers must provide each method.

```c
interface Shape {
    int32 area();
    int32 kind();
}

struct Rect : Shape {
    int32 w;
    int32 h;
    Rect(int32 w_, int32 h_) { w = w_; h = h_; }
    int32 area() override { return w * h; }
    int32 kind() override { return 1; }
}
```

SDK-registered interfaces (`.as_interface()` + `.implements(...)`) support script-level runtime dispatch:

```c
Stream s = file_stream(path);     // concrete assigned to iface var
int64 n = s.write("hi");          // dispatches to file_stream.write
s = mem_stream();
int64 m = s.write("hi");          // dispatches to mem_stream.write
```

Each iface-typed local carries a hidden tid companion, updated on every assignment.

***

### 11. Mixins

Add methods to an existing struct from outside its definition.

```c
struct Rect { int32 x; int32 y; int32 w; int32 h; }

mixin int32 Rect::area()      { return w * h; }
mixin int32 Rect::perimeter() { return 2 * (w + h); }

Rect r = Rect(1, 2, 10, 5);
int32 a = r.area();
```

***

### 12. Properties

Getter/setter syntax. Called without `()` on access.

```c
struct Rect {
    int32 w;
    int32 h;
    property int32 area { get { return w * h; } }
    property int32 side {
        get { return w; }
        set { w = value; h = value; }   // implicit `value` holds the RHS
    }
}

Rect r = Rect(10, 5);
int32 a = r.area;    // calls getter
r.side = 7;          // calls setter with value=7
```

***

### 13. Enums

```c
enum Color { Red = 0, Green = 1, Blue = 2 }

Color c = Color::Red;
if (c == Color::Green) { }
```

Enums are distinct types. Implicit convert-to-int but cross-enum assignment is rejected at compile.

***

### 14. Typedefs

```c
using ID = int32;           // preferred form
using Point = Vec2;

typedef int32 CID;          // C-style form also works

ID player_id = 42;
Point pos = Vec2(1.0, 2.0);
```

***

### 15. Templates

Generic structs and functions. Monomorphized at instantiation.

#### Template struct

```c
template<typename T>
struct Box {
    T value;
    Box(T v) { value = v; }
    T get() { return value; }
}

Box<int32> bi = Box<int32>(42);
Box<string> bs = Box<string>("hello");
```

#### Template function

```c
template<typename T>
T max(T a, T b) { return a > b ? a : b; }

int32 m1 = max<int32>(3, 7);
float64 m2 = max<float64>(1.5, 2.5);
```

Usually type inference picks up the template arg from call-site types.

#### Reference params in templates

```c
template<typename T>
void swap(T& a, T& b) { T t = a; a = b; b = t; }
```

#### Nested templates

```c
template<typename T>
struct List {
    Box<T> head;
}
```

Duck-typing at instantiation: template methods that reference `T` must be callable with the bound type's operations. A type arg may itself be a templated/pointer type — `Box<array<int64>>`, `Box<int64*>` — and the element type / pointer-ness is preserved.

#### Non-type template parameters (NTTP)

An integral value parameter, e.g. for a fixed array dimension:

```c
template<typename T, int64 N>
struct Arr {
    T data[N];
    int64 cap() { return N; }
}
Arr<int64, 4> a;        // distinct value args = distinct instantiations
```

An **enum constant** also works as a value argument — it resolves to the enum's integer value at instantiation (bare, type-qualified, namespaced, or nested-class forms all work):

```c
enum Color { RED = 0, GREEN = 2, BLUE = 4 }
template<typename T, int64 N> struct Tag { int64 get() { return N; } }
Tag<int64, Color::GREEN> t;   // t.get() == 2
```

(Pointer NTTP — `template<int* P>` with `&global` — is not supported.)

#### Default template arguments

```c
template<typename T = int64>
struct Box { T v; }
Box<> b;                          // T defaults to int64

template<typename K, typename V = int64>
struct Pair { K k; V v; }
Pair<string> p;                   // V defaults to int64

template<typename T, typename U = T>   // a default may name an earlier param
struct Two { T a; U b; }
```

#### Alias templates

```c
template<typename T> using Ptr = T*;
Ptr<int64> p = new int64[1];      // Ptr<int64> == int64*
```

A target that is itself a template (`using Vec = vector<T>`) instantiates too.

#### Member templates

A method with its OWN template params inside a (possibly non-template) class. Call with **explicit** args:

```c
class C {
    template<typename T> T identity(T x) { return x; }
}
C c;
int64 r = c.identity<int64>(5);
```

Value/NTTP args on a member-template call work: `c.scale<int64,3>(x)`. **Deduced** member-template calls also work — `c.identity(5)` (no `<...>`) infers each type param from the matching argument, exactly like a deduced free-function call. A literal, cast, arithmetic, **or a plain local/parameter variable** argument is all inferable (`int64 v = 5; c.identity(v)`); a struct value built from a temporary or a more complex expression still needs the explicit `c.identity<T>(...)` form.

#### Template specialization (explicit / full)

Pick a concrete implementation for a specific type, over the generic:

```c
template<typename T> T describe(T x) { return x; }            // generic
template<> int64 describe<int64>(int64 x) { return x * 100; } // chosen for int64

template<typename T> struct Holder { int64 tag() { return 1; } }
template<> struct Holder<int64> { int64 tag() { return 99; } }
```

Both explicit (`describe<int64>(5)`) and deduced (`describe(5)`) calls select the specialization; other types fall back to the generic.

#### Partial specialization

A class/struct template can be partially specialized on a pattern — most commonly a pointer:

```c
template<typename T> struct C { int64 tag() { return 1; } }         // primary
template<typename T> struct C<T*> { T deref; int64 tag() { return 2; } }   // C<anything*>

int64 main() {
    C<int64>  a;   // primary  → tag() == 1
    C<int64*> b;   // C<T*>    → tag() == 2, and `b.deref` has type int64
    return a.tag() * 10 + b.tag();   // 12
}
```

The pattern is matched against the concrete argument: a bare param `T` matches anything, `T*` (or `T**`) matches a pointer of that depth and binds `T` to the pointee, and a concrete position (`int64`) must match exactly. When several partials match, the **most specialized** wins (e.g. `C<T**>` over `C<T*>` for `C<int**>`); if none match, the primary is used. Multi-parameter patterns work too (`P<A, int64>`, `Q<A*, B>`).

#### Variadic function templates

A type parameter pack `typename... Ts` and a function parameter pack `Ts... args`. `sizeof...` gives the count; `args...` expands the pack:

```c
template<typename... Ts>
int64 count(Ts... args) { return sizeof...(args); }   // count(1,2,3) == 3

int64 add3(int64 a, int64 b, int64 c) { return a + b + c; }
template<typename... Ts>
int64 fwd(Ts... args) { return add3(args...); }       // fwd(10,20,30) == 60

template<typename... Ts>
int64 mklen(Ts... args) { int64[] xs = {args...}; return cast<int64>(xs.length()); }
```

A leading non-pack param binds 1:1, the trailing pack binds the rest. Both explicit (`count<int64,int64>(a,b)`) and deduced (`count(a,b)`) work — deduced calls infer each type from a literal, cast, arithmetic, or a plain local/parameter variable argument.

**Variadic class templates** work at any arity, and `sizeof...(Ts)` folds inside their methods:

```c
template<typename... Ts> struct Tup { int64 count() { return sizeof...(Ts); } }
Tup<int64, float64, string> t;   // t.count() == 3
```

**Zero-element packs** — a pure variadic called with no args (`count()` / `count<>()`) instantiates an empty pack (`sizeof...` is 0).

**Recursive variadic** — the classic base-case + recurse idiom works with a *non-template* base, including heterogeneous argument types:

```c
int64 sum() { return 0; }                                  // base case
template<typename T, typename... Ts>
int64 sum(T first, Ts... rest) { return cast<int64>(first) + sum(rest...); }

int64 r = sum(10, 2.5, 30);   // 42  (int + float + int)
```

Recursive variadic with a *1-arg template* base also works now — `sm(T x)` alongside `sm(T, Ts...)` — via overloaded function templates (see below):

```c
template<typename T> int64 sm(T x) { return cast<int64>(x); }              // template base
template<typename T, typename... Ts>
int64 sm(T first, Ts... rest) { return cast<int64>(first) + sm(rest...); }
int64 r = sm(1, 2, 3);   // 6
```

Not yet: a parameter pack used directly as struct *fields* (`Ts... members`).

#### Fold expressions

Reduce a parameter pack with a binary operator:

```c
template<typename... Ts> int64 sum(Ts... a) { return (a + ...); }       // right fold
template<typename... Ts> int64 lsum(Ts... a) { return (... + a); }      // left fold
template<typename... Ts> int64 prod(Ts... a) { return (a * ... * 1); }  // binary fold w/ seed
template<typename... Ts> bool  all(Ts... a) { return (a && ...); }      // logical fold
```

The operand may be any expression mentioning the pack, e.g. `(a * a + ...)` for a sum of squares.

#### Overloaded function templates

Two function templates can share a name and be told apart by their **template-argument signature** or their **call arity**:

```c
template<typename T>            int64 g(T x)        { return cast<int64>(x); }            // 1 type param
template<typename T, typename U> int64 g(T x, U y) { return cast<int64>(x) + cast<int64>(y); } // 2 type params
g<int64>(5);          // -> g(T)
g<int64,int64>(5, 6); // -> g(T, U)

template<typename T> int64 f(T x)       { return 1; }   // same template params [T],
template<typename T> int64 f(T x, T y)  { return 2; }   // distinguished by call arity
f(5);     // -> f(T)     == 1
f(5, 6);  // -> f(T, T)  == 2
```

This is what lets a recursive variadic bottom out on a 1-arg template base (the `sm` example above). Still not supported: an **explicit** overloaded call `f<int64>(5, 6)` when the overloads share the same template-param count (the explicit form can't see the call arity); use the deduced form `f(5, 6)`.

#### CTAD (class template argument deduction)

A class template's arguments can be deduced from a constructor call, so you don't have to spell `<...>` on the variable:

```c
template<typename T> struct Box {
    T v;
    Box(T x) { v = x; }
    T get() { return v; }
}

int64 main() {
    Box  b = Box(42);     // deduces Box<int64>
    auto c = Box(2.5);    // deduces Box<float64>
    int64 x = 7;
    Box  d = Box(x);      // deduces from a variable too
    return b.get() + cast<int64>(c.get()) + d.get();
}
```

The constructor whose arity matches the call drives deduction (each type param is taken from the first ctor parameter declared with that type); a template with **no** constructor deduces from its fields in declaration order (`template<typename T> struct Agg { T val; }` → `Agg a = Agg(9)`). Multi-parameter templates work (`Pair p = Pair(7, 3.0)` → `Pair<int64, float64>`). The argument may be a literal, cast, arithmetic, or a plain local/parameter variable; a struct value built from a temporary still needs explicit args (`Wrap<Point> w = Wrap<Point>(...)`).

#### Explicit deduction guides

When the constructor doesn't reference `T` (so CTAD can't deduce it implicitly), or when you want to override the implicit choice, write a user-supplied **deduction guide**:

```c
template<typename T> struct V {
    int64 tag;
    V(int64 x) { tag = x * 10; }   // ctor doesn't reference T
}
V(int64) -> V<int64>;              // non-template guide enables CTAD

template<typename T> struct Box {
    T v;
    Box(T x) { v = x; }
    T get() { return v; }
}
template<typename U> Box(U) -> Box<U>;   // template-prefixed guide

int64 main() {
    V vv = V(7);                   // 70 — guide enables this
    Box b = Box(42);               // template guide binds U=int64
    return vv.tag + cast<int64>(b.get());   // 112
}
```

Guides at file or namespace scope; consulted by CTAD **before** the implicit ctor/aggregate deduction. The first guide whose param-list signature matches wins; template-prefixed guides bind their own params from the call args and substitute into the target.

#### Variadic class templates with pack-as-fields

A class-template parameter pack can be used directly as a sequence of **fields**, expanded at instantiation into N concrete members named `<name>__0..<name>__{N-1}`:

```c
template<typename... Ts> struct Tup { public Ts... members; }

int64 main() {
    Tup<int64, int64, int64> t;
    t.members__0 = 10;
    t.members__1 = 20;
    t.members__2 = 12;
    return t.members__0 + t.members__1 + t.members__2;   // 42
}
```

Combine with `sizeof...(Ts)` and the expanded names to hand-iterate the pack. Heterogeneous element types are fine (`Tup<int64, float64, string>`). A `std::get<I>(t)` accessor is not provided — access the generated names directly.

#### Template template parameters

A template parameter that is itself a class template:

```c
template<typename T> struct Box {
    T v;
    Box(T x) { v = x; }
    T get() { return v; }
}

template<template<typename> class C> struct Holder {
    C<int64> b;
    Holder(C<int64> x) { b = x; }
    int64 get() { return b.get(); }
}

int64 main() {
    Box<int64> b = Box<int64>(42);
    Holder<Box> h = Holder<Box>(b);
    return h.get();   // 42
}
```

The bound argument is a class-template **name**; uses `C<args>` in the body rewrite to `<bound><args>` at instantiation. The inner template prefix on the parameter (`<typename>`) is the conventional shape; both `class T` and `typename T` forms accepted.

#### Generic addon types + constraints (SDK-side)

SDK can constrain a generic param with `.requires_iface(param, iface)`; script binding is rejected if the bound type doesn't `.implements(iface)`. Script-level templates don't support constraints.

***

### 16. Delegates

Typed function references.

```c
delegate int32 Transform(int32 x);

int32 double_it(int32 x) { return x * 2; }
Transform t = double_it;
t(5);               // 10
```

Any function matching the signature is assignable.

***

### 17. Namespaces

```c
namespace math {
    int32 square(int32 x) { return x * x; }
    int32 cube(int32 x)   { return x * x * x; }
}

int32 a = math::square(5);
using namespace math;
int32 b = cube(5);
```

Namespaces nest, can be reopened, and contain everything: free fns, structs / classes, enums (incl. `enum class`), globals, methods.

```c
namespace col { enum class Color { Red = 1, Green = 2, Blue = 4 } }
namespace cfg { int64 max_iter = 1000; }    // global init runs at module load
namespace shapes {
    class Shape { int64 size; Shape(int64 s){ size = s; } virtual int64 area(){ return 0; } }
    class Square : Shape { Square(int64 s) : Shape(s) {}            // bare base name OK
                            virtual int64 area() override { return size * size; } }
}
namespace base { class A { int64 v; A(int64 x){ v = x; } } }
namespace derived { class B : base::A { B(int64 x) : base::A(x + 50) {} } }   // cross-ns base

int64 main() {
    int64 m = cfg::max_iter;                   // qualified read
    cfg::max_iter = 42;                        // qualified write
    int64 r = cast<int64>(col::Color::Red);    // 3-deep enum value
    shapes::Square s = shapes::Square(5);
    return s.area() + r + m;
}
```

Methods on a namespaced struct can return / accept other types in the same namespace using bare names — the compiler walks the enclosing namespace chain to qualify them. Same for ctor init lists: write `Shape(s)` even though the layout key is `shapes::Shape`. `constexpr` variables and functions declared in a namespace are visible by their bare name to other declarations in the same namespace, and by `ns::name` from outside.

***

### 18. Coroutines

Functions that suspend with `yield` and resume.

```c
coroutine int32 counter(int32 start) {
    int32 i = start;
    while (true) {
        yield i;
        i = i + 1;
    }
}

coroutine_t c = counter(0);
while (c.next() == 1) {
    println(c.value());
    if (c.value() >= 4) break;
}
```

`c.next()` advances to the next `yield`; returns `1` if a value was yielded, `0` if the coroutine finished. `c.value()` retrieves the last yielded value.

***

### 19. Exceptions

```c
try {
    if (x < 0) throw -1;
    process(x);
} catch (int32 e) {
    println(e);
}
```

#### Typed exceptions

```c
struct NetErr { int32 code; string msg; NetErr(int32 c, string m) { code = c; msg = m; } }

try { throw NetErr(503, "timeout"); }
catch (NetErr e) { println(e.code); println(e.msg); }
```

* Destructors run during unwind.
* `defer` blocks run during unwind.
* `throw T(args)` copies the struct into a thread-local exception buffer, no heap alloc.
* `throw new T(args)` heap-allocates; usable when the struct is too large for the buffer.

`catch` always takes a typed parameter. There's no parameterless `catch { ... }` form.

***

### 20. Heap Allocation (`new` / `delete`)

See `Pointers` above for full semantics.

```c
T* p = new T(args);
delete p;

T* ps = new T[N];
delete[] ps;

T* ys = new T[N](ctor_args);
delete[] ys;
```

***

### 21. Arrays (growable `T[]`)

Two array flavors:

```c
int32[] arr = {1, 2, 3, 4, 5};    // growable, scope-drop, .push/.pop/.length
arr.push(6);
int64 n = arr.length();

int32[] arr2 = new int32[256];    // same growable form, explicit size

// Contiguous heap-array (raw):
int32* raw = new int32[100];      // no length tracking, manual delete[]
raw[0] = 5;
delete[] raw;
```

#### Fixed-size arrays (`T name[N]`)

C++ declarator syntax: the size follows the name. (The old `T[N] name` form is a compile error.) Primitive elements are true stack storage; struct/class elements are default-constructed on entry and destroyed at scope exit.

```c
int64 buf[4];                     // 4 stack slots
buf[0] = 1; buf[2] = 3;

struct P { int64 x; P() { x = 0; } }
P pts[3];                         // P() runs for each; ~P() at scope exit
pts[1].x = 7;
```

A fixed array **decays to a pointer**: pass it (or any element's address) to a `T*` parameter, and range-for over it.

```c
int64 total(int64* p, int64 n) { int64 s = 0; for (int64 i = 0; i < n; i = i + 1) s = s + p[i]; return s; }
total(&buf[0], 4);
for (int64 v : buf) { /* ... */ }
```

**2D** fixed arrays (locals): `int64 m[N][M]` and `P grid[N][M]`. Both dimensions are sizes after the name; element access is `m[i][j]`.

```c
int64 m[2][3];   m[1][2] = 9;
P grid[2][2];    grid[0][0].x = 100;
```

**Brace initialization** is allowed for arrays of POD structs (no ctor/dtor); each element is filled from the list. Non-POD elements are default-constructed instead (brace init rejected).

```c
struct Pod { int64 a; int64 b; }
Pod cfg[2] = { Pod{1, 2}, Pod{3, 4} };
```

Fixed arrays also work as **class/struct fields and globals** (1D, primitive or struct elements). 2D arrays are supported as **locals only**.

#### Nested arrays

Stack `[]` for arrays of arrays. Each level is an 8-byte handle to the inner array. `push`/`set`/`insert` clone the inner so the container owns its own buffer (the source local can drop safely).

```c
int64[][] grid;                  // array of int64[]
int64[][][] cube;                // 3D

int64[] row;
row.push(1); row.push(2);
grid.push(row);                  // row is cloned into grid

int64[] r0 = grid.get(0);        // pull inner back out
int64 v   = grid.get(0).get(1);  // chained .get works
v        = grid[0][1];           // subscript chain works
int64[][] make_grid(int32 r, int32 c) { ... return grid; }  // return type OK
```

Returning a heap-managed local (array, string, ...) from a function transfers ownership to the caller — the local's destructor is suppressed on the return path so the caller sees a live handle.

***

### 22. decltype

Infer a type from an expression at compile time.

```c
int64 x = 42;
decltype(x) y = x + 1;            // y is int64

int32 a = 10;
decltype(a + a) sum = 100;        // sum is int32

int64 double_it(int64 v) { return v * 2; }
decltype(double_it(0)) r = 99;    // r is int64
```

Works in var-decl, param types, return types.

***

### 23. Designated Initializers

```c
struct Point { int32 x; int32 y; }
struct Triple { int32 a; int32 b; int32 c; }

Point p = {3, 4};                    // positional
Point q = {.x = 10, .y = 20};        // designated
Point r = {.y = 5, .x = 1};          // any order
Triple t = {.b = 42};                // a = 0, c = 0

Point bad = {.x = 1, .z = 99};       // compile error: no field z

// Type-prefixed brace form also accepts designated init:
Point pp = Point{.x = 3, .y = 4};
Triple tt = Triple{.c = 9, .a = 1};
```

Aggregate init form, does not call constructors. For types needing a ctor, use `Point(3, 4)`.

***

### 24. User-defined Literals

Suffix a numeric literal with `_name` to rewrite to `_name(value)`.

```c
int64   _km(int64 v)   { return v * 1000; }
float64 _deg(float64 v) { return v * 3.14159265 / 180.0; }

int64   d    = 42_km;           // _km(42) → 42000
float64 rad  = 180.0_deg;       // _deg(180.0)
```

Works on integer, float, and hex literals.

***

### 25. Inline Assembly Intrinsics

Fixed whitelist. JIT emits literal opcode bytes, no call boundary.

```c
int64 tsc = __asm_rdtsc();     // rdtsc, composed rdx:rax
__asm_pause();                 // spin hint
__asm_mfence();                // full memory barrier
__asm_nop();                   // nop
```

No user-provided bytes. No arbitrary memory access.

***

### 26. Annotations (`[[...]]`)

Applied to functions, structs, or fields.

| Annotation         | Effect                                                                            |
| ------------------ | --------------------------------------------------------------------------------- |
| `[[inline]]`       | Hint to inline                                                                    |
| `[[noinline]]`     | Block inlining                                                                    |
| `[[noopt]]`        | Skip optimizer passes (for debugging)                                             |
| `[[noescape]]`     | Allocation may not escape; compile error on escape                                |
| `[[packed]]`       | Struct: no padding between fields                                                 |
| `[[align(N)]]`     | Struct or field: custom alignment (per-field bumps total struct alignment too)    |
| `[[offset(N)]]`    | Field: exact byte offset (decimal or hex). Compile error on overlap.              |
| `[[reflect]]`      | Include in reflection / reachable from host reflection API                        |
| `[[serialize]]`    | Include in serialization                                                          |
| `[[export]]`       | Visible across `link()`                                                           |
| `[[dll("lib")]]`   | FFI declaration; resolved at load via `dlopen`/`LoadLibrary` (requires PERM\_FFI) |
| Custom annotations | Any `[[name(arg1, arg2)]]`, queryable via SDK `get_annotations()`                 |

```c
[[inline]] int32 hot(int32 x) { return x * 2; }
[[packed]] struct H { uint8 kind; uint32 size; }

[[my_category("combat")]]
int32 attack() { return 10; }
```

The host can enumerate annotated functions: `get_annotated_functions(mod, "my_category", out)`.

***

### 27. Nullable Types (`nullable T`)

Distinct type that can hold null. Plain `T` cannot.

```c
nullable int32 n = null;
if (n == null) { } else { println(n); }
n = 42;
```

Internally a `{value, has_flag}` pair.

***

### 28. Modules

#### import

```c
import "math_utils.em";
import "engine/renderer.em" as rend;

int32 main() {
    int32 a = square(5);         // from math_utils
    rend::draw_sprite(0, 0);
    return 0;
}
```

#### Precompiled `.emb`

The SDK can serialize a compiled module to a binary file via `enma::serialize()` and reload it later with `deserialize()`, avoiding the parse/compile cost on startup. Script-level `import` resolves `.em` sources.

#### Multi-module linking

The host joins multiple compiled modules via `link()`. Exported functions are visible across modules.

***

### 29. Preprocessor

```c
#define VER 42
#define SQUARE(x) ((x) * (x))

#ifdef DEBUG
    #define LOG(m) println(m)
#else
    #define LOG(m)
#endif

#if VER > 40
    int32 v = VER;
#endif

#include "helpers.em"

#pragma once
```

Supports `#define` / `#undef`, `#ifdef` / `#ifndef` / `#if` / `#elif` / `#else` / `#endif`, `#include`, `#pragma`, function-like macros.

***

### 30. FFI (`[[dll(...)]]`)

Call native shared libraries. Requires `PERM_FFI`.

```c
[[dll("libc.so.6")]]
extern int64 getpid();

[[dll("ws2_32.dll", "connect")]]
extern int32 ws_connect(int64 sock, int64 addr, int32 len);
```

Resolved at load time via `dlopen`/`dlsym` (Linux) or `LoadLibrary`/`GetProcAddress` (Windows).

***

### 31. Static Assert and Compile-Time Evaluation

`static_assert(expr [, message])` runs at compile time. Expression must fold via the constexpr engine. Message is optional and printed verbatim on failure. Works at module scope and inside function bodies.

```c
static_assert(sizeof(int32) == 4, "int32 must be 4 bytes");
static_assert(offsetof(Point, y) == 4);
```

`constexpr` on a variable forces compile-time folding of the initializer. On a function, makes the function callable from constexpr contexts.

```c
constexpr int32 fact(int32 n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);
}
constexpr int32 FACT10 = fact(10);
static_assert(FACT10 == 3628800);
```

Folder supports: integer/float arithmetic, bitwise/shift, comparison, logical, ternary, `cast<T>(...)`, `sizeof`/`offsetof`, hex literals, recursion + mutual recursion, `if`/`for`/`while`/local vars, calls to other constexpr fns, `string.length()` and `string.char_at(int)` on string params or literals, **string concat (`"a" + "b"`) and equality (`"a" == "b"`)**, **struct construction (`Point(3, 4)`, `Point{3, 4}`, `{1, 2}`) + field access (`p.x`)**, \*\*array literals (`{10, 20, 30}`)

* subscript (`arr[0]`)\*\*, **nested struct + array (`Pair(Point(1, 2), Point(3, 4))`, `int64[][] grid = {{1,2},{3,4}}`)**, **constexpr fns taking struct params and accessing fields**. The constexpr-folded result is also accessible at runtime: `int64 main() { return p.x; }` or `manhattan(p)` resolves to a literal at the call site when both the fn and all args fold. Loop budget: 100,000 iterations per top-level call.

Doesn't fold: pointer ops, calls to non-constexpr fns. Hoist into a helper that returns a scalar.

Compile-time hashing pattern (FNV-1a 64):

```c
constexpr int64 fnv1a(string s) {
    int64 h = 0xcbf29ce484222325;
    for (int32 i = 0; i < s.length(); i = i + 1) {
        h = h ^ s.char_at(i);
        h = h * 0x100000001b3;
    }
    return h;
}
constexpr int64 H_PLAYER = fnv1a("player");
static_assert(fnv1a("hello") == 0xa430d84680aabd0b);
```

`H_PLAYER` collapses to an immediate in the IR — no runtime cost.

Failure modes:

* `static_assert` false → compiler reports the user message verbatim
* expression non-foldable → "static\_assert expression must be a compile-time constant"
* `constexpr` initializer non-foldable → "constexpr `X`: initializer is not a compile-time constant"
* loop budget exceeded → same constexpr-init error (treats it as non-foldable)

***

### 32. String Interpolation

Prefix literal with `f`:

```c
int32 x = 5;
string s = f"value is {x}";      // "value is 5"
string t = f"sum = {x + x * 2}";
```

Non-string args convert via registered `convert` handlers.

**String escapes:** `\n` `\t` `\r` `\\` `\0`, plus `\xHH` (1-2 hex digits → one byte; useful for raw UTF-8 sequences). Unknown `\<c>` drops the backslash. Adjacent string literals do NOT auto-concatenate — use `+`.

***

### 33. Runtime Traps vs Compile Errors

#### Rejected at **compile time** (never reach runtime)

* Raw int → pointer assignment
* Pointer arithmetic
* `cast<int64>(ptr)` or `cast<int64>` on any pointer type
* Returning `&local`
* Storing `&local` in a global / field
* Escaping closure captures a stack struct
* Calling a non-`const` method on a `const` receiver
* Assigning through a `const` parameter
* Wrong-type arg at a native call site
* Wrong struct identity at a native call site
* Wrong enum identity (raw int or cross-enum)
* Wrong container element type
* `new` on a non-addon, non-struct, non-class type
* `delete` on a non-pointer
* `T x = new T()` (must pick stack or heap)
* `[[noescape]]` violation
* Missing overload / ambiguous overload
* Calling a permission-gated native without the permission

#### Caught at **runtime**

* Null deref on pointer, array, struct
* Out-of-bounds on `T[]` subscript (positive or negative)
* Use-after-free where freed-marker is still readable
* Division by zero
* Stack overflow
* Double `delete[]` on heap arrays

**Process-stability guarantee.** Every JIT-thrown fault from the list above is caught by the runtime fault handler; `execute()` returns `false`, the engine remains usable for the next call, and dtors registered for any value-struct locals on the faulting frame run via the cleanup-stack unwind. The host process does NOT die. Pattern: call `execute()`, check the bool, log via `last_error()` or `__enma_jit_get_last_fault()`, and decide to retry / abort just that engine.

Inside a native function: **not** trapped. Validate inputs on the native side before deref. Use `heap_is_tracked(ptr)` if the pointer came from Enma's heap.

#### Features that simply don't exist

* Overloaded function templates (two templates of the same name selected by arity) — so recursive variadic with a 1-arg *template* base isn't available, though recursive variadic with a *non-template* base, variadic CLASS templates, zero-element packs, and all variadic FUNCTION template features DO work (see §15). Runtime varargs: `...` with `__va_count`/`__va_arg`.
* RTTI / `typeid`: use SDK `find_type_reg` instead for reflection
* Script-level reflection. SDK-side only
* Async / await, use coroutines + threads
* Pattern matching `match T { }` on types
* Custom allocators per scope
* Attributes beyond the built-in set plus custom annotations queryable from host
* Arbitrary inline asm, only the four whitelisted intrinsics

***

### 34. Permissions

Two flags gate dangerous features. Granted per-engine by the host.

| Flag        | Value  | Gates                              |
| ----------- | ------ | ---------------------------------- |
| `PERM_FFI`  | `0x01` | `[[dll(...)]]` extern declarations |
| `PERM_FILE` | `0x02` | All file-addon calls               |

Scripts compile-fail if they call a gated feature without the permission.

***

### 35. Thread Safety Model

* Engines are independent. Multiple threads → multiple engines.
* Multiple contexts off the same module can execute concurrently.
* Per-thread TLS heap.
* Use the `thread` addon for in-script synchronization.
* The MT test suite covers 18 scenarios across all addons.

***

## Shipped Addons

19 addons register via `register_all_addons(engine)` or individually. Each documented below with the exact types + methods.

***

### Core built-ins (always available, no addon)

These ship with the engine regardless of addon registration:

```c
int64 time_ms();                             // wall-clock ms (engine built-in)
int64 assert(int64 cond, string msg);         // throws if cond == 0

int64 heap_collect();                        // no-op in deterministic model
int64 heap_count();                          // live allocation count

int64 set_budget(int64 instructions);         // cap loop-header instruction count
int64 set_memory_budget(int64 bytes);         // cap live heap bytes

int64 register_event(int64 event_id, int64 callback);  // callback is a fn ref
int64 fire_event(int64 event_id, int64 arg);
int64 clear_events();

// Built-in type used for coroutines:
coroutine_t cr = my_coro();  cr.next();  cr.value();  cr.done();
```

### Core addon (`register_addon_core`)

```c
void print(string s);        // any convertible arg auto-cast via string.convert
void println(string s);      // trailing newline
```

Non-string args (`int`, `float`, `bool`, `char`) auto-convert when the string addon is also registered.

***

### Strings (`register_addon_string`)

`string` is a primitive but methods are registered by this addon. Addon also exposes free functions.

#### Free functions

```c
string to_string(int64 v);             // works for any integral, float, bool
string to_string(float64 v);
string to_string(bool v);
string char_to_str(char c);            // "A" — not "65" like to_string(char)
string format(string fmt, ...);        // brace `{d}` or printf `%d` placeholders

// Char / encoding helpers
int64  ord(char c);                    // char code
string chr(int64 code);                // 1-char string
string from_chars(int64[] codes);      // build string from char codes

string hex_encode(int64 v);            // lowercase hex; overloaded on string for byte→hex
string hex_decode(string s);           // pairwise nibbles → bytes
int64  hex_to_int(string s);           // parse hex digits as int64

string base64_encode(string data);
string base64_decode(string text);

string url_encode(string data);        // RFC 3986 percent-encoding
string url_decode(string text);        // also decodes '+' as ' '
```

#### Methods on `string`

```c
int64   s.length();
bool    s.is_empty();
string  s.substr(int64 start, int64 len);
int64   s.find(string needle);
int64   s.last_index_of(string needle);
bool    s.contains(string sub);
bool    s.starts_with(string p);
bool    s.ends_with(string p);
bool    s.starts_with_i(string p);     // case-insensitive
bool    s.ends_with_i(string p);
int64   s.count(string needle);
int64   s.char_at(int64 i);
int64   s.to_int();
float64 s.to_float();
string  s.to_upper();
string  s.to_lower();
string  s.trim();
string  s.trim_left();
string  s.trim_right();
string  s.reverse();
string  s.replace(string from, string to);
string  s.replace_first(string from, string to);
string  s.repeat(int64 n);
string  s.pad_left(int64 width, char pad);
string  s.pad_right(int64 width, char pad);
string  s.insert(int64 i, string other);
string  s.remove_range(int64 start, int64 end);  // removes chars in [start, end)
array   s.split(string sep);
array   s.chars();                                // int64[] of char codes
```

***

### Arrays (`register_addon_array`)

The growable array type `T[]`. Also registered: iteration via `for (v : arr)`.

#### Methods

```c
int64   a.length();
int64   a.capacity();
int64   a.stride();                      // element size in bytes
void    a.push(T v);
T       a.pop();
T       a.get(int64 i);
void    a.set(int64 i, T v);
void    a.clear();
void    a.resize(int64 n);
T       a.remove(int64 i);
void    a.insert(int64 i, T v);
void    a.free();                        // manual free (scope-drop does this too)
array   a.slice(int64 start, int64 end);     // sub-array [start, end)
int64   a.contains(T v);                 // 1 or 0
int64   a.index_of(T v);                 // -1 if missing
void    a.reverse();
void    a.sort();                        // dispatches by element type (int / float / string)
string  a.join(string sep);

void    a.print_int();   void a.println_int();
void    a.print_float(); void a.println_float();
void    a.print_str();   void a.println_str();
```

#### Subscript

```c
int64[] a = {1, 2, 3};
int64 x = a[1];
a[0] = 99;
```

#### Construction

```c
int32[] a = {1, 2, 3};          // init list
int32[] b = new int32[100];      // explicit size
int32[] c;                        // empty, push-on-demand
```

***

### Maps (`register_addon_map`)

`map<K, V>` where K is **`string`** (string-keyed only), V is any int64-sized type. For **int64 keys** use `imap<V>` (the int-keyed map — same `set`/`get`/`has`/`size` API). `map<int64, V>` is a compile error. (Note: `sorted_map<K, V>` *does* accept a scalar K — both `sorted_map<string, V>` and `sorted_map<int64, V>` work.)

#### Methods

```c
map<string, int64> m;
m.set("a", 1);
int64 v = m.get("a");
int64 v2 = m.get_or_default("missing", -1);
int64 has = m.contains("a");           // 1/0
int64 has_v = m.has_value(1);
m.remove("a");
m.clear();
int64 n = m.length();
array keys = m.keys();
array vals = m.values();
m.merge(other);
m.free();
```

#### Subscript + iteration

```c
m["key"] = 42;
int64 v = m["key"];

for (int64 v : m)         { /* values */ }
for (string k, int64 v : m) { /* keys + values */ }
```

***

### Math (`register_addon_math`)

```c
// Trig (radians)
float64 sin(float64);   cos(float64);   tan(float64);
float64 asin(float64);  acos(float64);  atan(float64);
float64 atan2(float64 y, float64 x);

// Power / log
float64 sqrt(float64);  pow(float64, float64);
float64 log(float64);   log2(float64);   log10(float64);  exp(float64);

// Rounding
float64 floor(float64); ceil(float64); round(float64);

// Float
float64 fabs(float64);
float64 fmod(float64, float64);
float64 fmin(float64, float64);  fmax(float64, float64);
float64 fclamp(float64 v, float64 lo, float64 hi);

// Integer
int64 iabs(int64);
int64 imin(int64, int64); imax(int64, int64);
int64 iclamp(int64, int64, int64);

// Interpolation and mixing
float64 lerp(float64 a, float64 b, float64 t);
float64 inverse_lerp(float64 a, float64 b, float64 v);
float64 remap(float64 v, float64 in_lo, float64 in_hi, float64 out_lo, float64 out_hi);
float64 smoothstep(float64 edge0, float64 edge1, float64 x);
float64 step(float64 edge, float64 x);          // 0 if x<edge else 1
float64 saturate(float64 v);                    // clamp to [0, 1]
float64 sign(float64 v);                        // -1 / 0 / +1
float64 fract(float64 v);                       // v - floor(v)
float64 wrap(float64 v, float64 lo, float64 hi); // wrap into [lo, hi)

// Classification
bool is_nan(float64);
bool is_inf(float64);

// Aliases
float64 round_up(float64);    // == ceil
float64 round_down(float64);  // == floor

// Constants
float64 pi();
float64 euler();

// Random (per-context, seeded)
float64 rand();                          // [0, 1)
int64   rand_int(int64 lo, int64 hi);     // [lo, hi)
void    seed(int64);
bool    random_bool();                    // coin flip
float64 random_gaussian(float64 mu, float64 sigma);

// Bit-cast helpers
uint32  f32_to_u32(float32);
float32 u32_to_f32(uint32);
uint64  f64_to_u64(float64);
float64 u64_to_f64(uint64);

// Hyperbolic + extras
float64 cbrt(float64);     float64 hypot(float64, float64);     float64 log_base(float64, float64);
float64 sinh(float64);     float64 cosh(float64);               float64 tanh(float64);
float64 asinh(float64);    float64 acosh(float64);              float64 atanh(float64);
float64 copysign(float64, float64);    float64 nextafter(float64, float64);
bool    is_finite(float64);
```

***

### SIMD (`register_addon_simd`)

SSE2 vector ops. Element-wise ops are `(a, b, dst)`: inputs first, destination last. Reductions return scalar. Operands must share a compatible stride.

```c
// Float64 element-wise
int64 simd_add_f64(array a, array b, array dst);
int64 simd_sub_f64(array a, array b, array dst);
int64 simd_mul_f64(array a, array b, array dst);
int64 simd_div_f64(array a, array b, array dst);
int64 simd_min_f64(array a, array b, array dst);
int64 simd_max_f64(array a, array b, array dst);
int64 simd_abs_f64(array a, array dst);
int64 simd_sqrt_f64(array a, array dst);
int64 simd_fma_f64(array a, array b, array c, array dst);    // a*b + c
int64 simd_scale_f64(array a, float64 s, array dst);

// Float64 reductions
float64 simd_dot_f64(array a, array b);
float64 simd_sum_f64(array a);
float64 simd_min_reduce_f64(array a);
float64 simd_max_reduce_f64(array a);

// Float64 comparisons (result is a 0/1 mask array)
int64 simd_cmp_eq_f64(array a, array b, array dst);
int64 simd_cmp_lt_f64(array a, array b, array dst);

// Float32 element-wise (a, b, dst) / (a, dst)
int64 simd_add_f32(array, array, array);
int64 simd_sub_f32(array, array, array);
int64 simd_mul_f32(array, array, array);
int64 simd_div_f32(array, array, array);
int64 simd_sqrt_f32(array, array);
int64 simd_abs_f32(array, array);
int64 simd_min_f32(array, array, array);
int64 simd_max_f32(array, array, array);

// Float32 reductions (return float64 for precision)
float64 simd_dot_f32(array a, array b);
float64 simd_sum_f32(array a);

// Int64
int64 simd_add_i64(array, array, array);
int64 simd_sub_i64(array, array, array);
int64 simd_mul_i64(array, array, array);
int64 simd_sum_i64(array);

// Int32
int64 simd_add_i32(array, array, array);
int64 simd_sub_i32(array, array, array);
int64 simd_mul_i32(array, array, array);

// Int16
int64 simd_add_i16(array, array, array);
int64 simd_sub_i16(array, array, array);
int64 simd_mul_i16(array, array, array);

// Int8 (useful for bytes/masks)
int64 simd_add_i8(array, array, array);
int64 simd_sub_i8(array, array, array);
int64 simd_cmp_eq_i8(array, array, array);
int64 simd_movemask_i8(array);
int64 simd_shuffle_i8(array a, array ctl, array dst);

// Bitwise on stride-1 arrays
int64 simd_and(array a, array b, array dst);
int64 simd_or(array a, array b, array dst);
int64 simd_xor(array a, array b, array dst);

// Memory
int64 simd_memset(array dst, int64 value);
int64 simd_memcpy(array dst, array src);
```

***

### Variant (`register_addon_variant`)

Open tagged union. A variant can hold any registered type, carrying both the value and a type tag.

```c
variant v = 42;              // int
variant v2 = 3.14;           // float
variant v3 = "hi";           // string
variant v4 = true;           // bool
variant empty;               // null

if (v.is_int()) println(v.as_int());
v.set_str("new");
int64 tid = v.type();
string name = v.type_name();
```

Factory-style free functions for explicit construction:

```c
int64 variant_null();
int64 variant_int(int64);
int64 variant_float(float64);
int64 variant_bool(bool);
int64 variant_str(string);
int64 variant_array(array);
int64 variant_map(map);

// Wrap a foreign handle + its registered type_id:
variant variant_box(int64 value, int64 tid);
variant variant_box_owned(int64 value, int64 tid);   // owns it: dtor runs on drop
```

#### Methods

```c
int64   v.type();           // the tag (type_id)
string  v.type_name();      // registered type name

bool v.is_null();  v.is_int();  v.is_float();  v.is_bool();
bool v.is_str();   v.is_array();  v.is_map();
bool v.is_of_type(int64 tid);

int64   v.as_int();
float64 v.as_float();
bool    v.as_bool();
string  v.as_str();
array   v.as_array();
map     v.as_map();

void v.set_int(int64);
void v.set_float(float64);
void v.set_bool(bool);
void v.set_str(string);
void v.set_null();

int64 v.raw_storage();      // the int64 backing value
```

***

### Atomic (`register_addon_atomic`)

`atomic_int32` and `atomic_int64` types. The `aint8`/`aint16`/`aint32`/`aint64` primitives are separate value-sized atomics built into the language.

```c
atomic_int32 a = atomic_int32(0);
int32 x    = cast<int32>(a.load());
a.store(10);
int32 old  = cast<int32>(a.exchange(20));
bool  ok   = a.compare_exchange(20, 30);    // true if swap happened
a.add(5);
a.sub(1);
a.bit_and(0xFF);
a.bit_or(0x100);
a.bit_xor(0x7);
a.inc();
a.dec();
```

`atomic_int64` has the same method set.

Memory barriers:

```c
void memory_barrier();     // full barrier
void read_barrier();        // load barrier
void write_barrier();       // store barrier
```

***

### Bits (`register_addon_bits`)

```c
int64 popcount(int64);          int64 popcount_i32(int64);
int64 clz(int64);               int64 clz_i32(int64);
int64 ctz(int64);               int64 ctz_i32(int64);
int64 rotl(int64, int64);       int64 rotl_i32(int64, int64);
int64 rotr(int64, int64);       int64 rotr_i32(int64, int64);
int64 bswap(int64);             int64 bswap_i32(int64);
int64 parity(int64);
int64 bit_reverse(int64);       int64 bit_reverse_i32(int64);

// Single-bit ops
int64 set_bit(int64 v, int64 i);
int64 clear_bit(int64 v, int64 i);
int64 toggle_bit(int64 v, int64 i);
int64 test_bit(int64 v, int64 i);

// Field extract / insert (lo / hi inclusive)
int64 extract_bits(int64 v, int64 lo, int64 hi);
int64 insert_bits(int64 v, int64 val, int64 lo, int64 hi);

// Powers of two
int64 is_pow2(int64 v);
int64 next_pow2(int64 v);
int64 prev_pow2(int64 v);

// Alignment helpers
int64 align_up(int64 v, int64 n);
int64 align_down(int64 v, int64 n);
```

Every `*_i32` variant takes an `int64` and masks to the low 32 bits before operating. `clz(0) == 64`, `ctz(0) == 64`, `clz_i32(0) == 32`, `ctz_i32(0) == 32`.

***

### Time (`register_addon_time`)

Note: `time_ms()` is already a core built-in. The time addon adds the rest.

```c
// Clocks
int64 now_us();                 // microseconds since epoch
int64 now_ms();                 // milliseconds since epoch
int64 now_ns();                 // nanoseconds since epoch
int64 unix_seconds();            // seconds since epoch
int64 mono_us();                 // monotonic microseconds (not wall clock)

void  sleep_ms(int64 ms);

// Timestamp construction
int64 from_ymd(int64 y, int64 m, int64 d);
int64 from_ymdhms(int64 y, int64 mo, int64 d, int64 h, int64 mi, int64 s);

// Unpack a timestamp
int64 year(int64 ts);
int64 month(int64 ts);
int64 day(int64 ts);
int64 hour(int64 ts);
int64 minute(int64 ts);
int64 second(int64 ts);
int64 day_of_week(int64 ts);    // 0 = Sunday
int64 day_of_year(int64 ts);

// Calendar helpers
bool  is_leap(int64 year);
int64 days_in_month(int64 year, int64 month);

// ISO 8601
string iso_format(int64 ts);
int64  iso_parse(string s);

// Arithmetic
int64 add_seconds(int64 ts, int64 n);
int64 add_days(int64 ts, int64 n);
int64 diff_us(int64 a, int64 b);
int64 diff_ms(int64 a, int64 b);
int64 diff_s(int64 a, int64 b);
```

***

### Regex (`register_addon_regex`)

```c
regex re = regex("[a-z]+");           // compile; bad pattern gives a null handle

bool m = re.matches("abc");                 // entire-string match
bool h = re.has_match("x abc y");           // substring match
string first = re.first("x 12 y");          // first match (or "" if none)
array all    = re.find_all("a12 b345");     // array<string>
string rep   = re.replace("a12b34", "#");   // "a#b#"
array parts  = re.split("a,b,c");
array grps   = re.groups("age=42");         // [full, group1, group2, ...]
```

Null handles are safe: methods return false / "" / empty arrays.

***

### File (`register_addon_file`) *(requires PERM\_FILE)*

#### Free functions

```c
file_t f = file_open(string path, string mode);   // "r" / "w" / "a" / "rb" / etc.

// File-level
bool   file_exists(string path);
bool   file_remove(string path);
bool   file_rename(string from, string to);
bool   file_copy(string src, string dst);                 // overwrites dst
int64  file_size(string path);                            // -1 on error
int64  file_mtime(string path);                           // unix seconds, -1 on error
string file_read(string path);
bool   file_write(string path, string content);
array  file_read_bytes(string path);                      // uint8 stride-1 array
bool   file_write_bytes(string path, array bytes);

// Dir-level
bool   dir_exists(string path);
bool   dir_create(string path);
array  dir_list(string path);                             // immediate children, names only
array  dir_walk(string path);                             // recursive, full paths
```

#### `file_t` methods

```c
void   f.close();
bool   f.is_open();
bool   f.is_eof();
string f.read_all();
string f.read_line();
int64  f.write(string s);
void   f.flush();
int64  f.size();
int64  f.tell();
void   f.seek(int64 pos);
```

***

### Thread (`register_addon_thread`)

`mutex` is backed by `std::shared_mutex` — the same handle supports both exclusive and shared (reader/writer) locks.

```c
// Mutex (exclusive)
mutex m;
m.lock();
m.unlock();
bool got = m.try_lock();

// Reader-writer (shared) variants on the same mutex
m.lock_shared();             // multiple shared holders allowed concurrently
m.unlock_shared();
bool got_s = m.try_lock_shared();

// RAII lock_guard takes the EXCLUSIVE lock; drops at scope exit
lock_guard g = lock_guard(m);

// Condition variable
cond_var cv;
cv.wait(m);            // wait and re-acquire (caller must hold the exclusive lock)
cv.notify_one();
cv.notify_all();

// Free functions
void  sleep_us(int64 us);     // microsecond sleep
void  yield_cpu();             // hint to scheduler
int64 hardware_threads();     // logical CPU count
```

The host spawns threads from native code and shares `mutex` handles by passing the int64 value across threads. The mutex lock/unlock natives are callable from any thread; they don't touch Enma's TLS heap.

***

### Vectors, Quaternions, Matrices (`register_addon_math`)

All math types — `vec2`, `vec3`, `vec4`, `quat`, `mat4` — are value-type structs registered alongside the scalar math natives by `register_addon_math`. Components are plain struct fields; there is no parenthesised getter form (`v.x`, not `v.x()`).

```c
vec3 a = vec3(1.0, 2.0, 3.0);
vec3 b = vec3(4.0, 5.0, 6.0);

// Fields
float64 x = a.x;
a.x = 5.0;

// Operators (vec2 / vec3 / vec4)
vec3 sum = a + b;
vec3 dif = a - b;
vec3 scl = a * 0.5;        // scalar multiply
vec3 neg = -a;
bool eq  = (a == b);
a += b;
a -= b;

// Common methods
vec3    sum2 = a.add(b);
vec3    dif2 = a.sub(b);
vec3    s    = b.scale(0.5);
vec3    n2   = a.neg();             // alias: a.negate()
float64 dp   = a.dot(b);
float64 L    = a.length();
float64 Lsq  = a.length_sq();
float64 dst  = a.distance(b);
vec3    nrm  = a.normalize();
vec3    l    = a.lerp(b, 0.25);

// vec2-only
vec2 rv = vec2(1.0, 0.0).rotate(rad);  // rotate CCW around origin

// vec3-only
vec3    cp  = a.cross(b);
vec3    r   = a.reflect(n);
vec3    pr  = a.project(onto);
float64 ang = a.angle(b);
vec3    rt  = a.rotate_around(axis, rad);   // Rodrigues
```

#### Quaternion (`quat`)

```c
quat q1 = quat(0.0, 0.0, 0.0, 1.0);
quat q2 = quat_identity();
quat q3 = quat_from_euler(yaw, pitch, roll);                            // Tait-Bryan ZYX, radians
quat q4 = quat_from_axis_angle(vec3(0.0, 0.0, 1.0), deg_to_rad(90.0));

// xyzw are plain fields
float64 x = q.x; q.x = 1.0;

float64 L    = q.length();
float64 Lsq  = q.length_sq();
float64 dp   = q.dot(other);
quat    n    = q.normalize();
quat    c    = q.conjugate();
quat    i    = q.inverse();
quat    g    = q.neg();             // alias: q.negate()
quat    p    = a.mul(b);             // Hamilton product. a*b = "rotate by b, then a".
quat    s    = a.add(b);
vec3    v    = q.rotate(vec3 v);     // rotate a vec3 (assumes unit quat)
vec3    e    = q.to_euler();         // (yaw, pitch, roll), inverse of from_euler
quat    mid  = a.slerp(b, t);        // shorter-arc spherical interpolation

// Operators: a * b (mul), a + b, a - b, -q, a == b, +=, -=
```

#### 4×4 matrix (`mat4`)

Row-major. Default constructor produces a zero matrix — use `mat4_identity()` for the identity. Cells exposed as fields `m00` … `m33`.

```c
mat4 zero;                                              // typed default: all 0
mat4 i  = mat4_identity();
mat4 t  = mat4_translation(vec3(x, y, z));
mat4 s  = mat4_scale(vec3(sx, sy, sz));
mat4 rx = mat4_rotation_x(rad);
mat4 ry = mat4_rotation_y(rad);
mat4 rz = mat4_rotation_z(rad);
mat4 ra = mat4_rotation_axis(vec3 axis, rad);
mat4 fq = mat4_from_quat(q);
mat4 p  = mat4_perspective(fov_rad, aspect, near_z, far_z);  // RH, GL-style depth
mat4 o  = mat4_orthographic(left, right, bottom, top, near_z, far_z);
mat4 v  = mat4_look_at(vec3 eye, vec3 target, vec3 up);

// Cell access
m.m00 = 1.0;
float64 c = m.get(row, col);          // row, col in 0..3
m.set(row, col, value);

mat4    t  = m.transpose();
mat4    i  = m.inverse();              // identity if singular
float64 d  = m.determinant();
mat4    c  = a.mul(b);                 // a*b
mat4    g  = m.scale(2.0);
vec3    p  = m.transform_point(v);     // perspective-divides if w != 1
vec3    d  = m.transform_vec3(v);      // ignores translation
vec4    q  = m.transform_vec4(v);

// Operators: a * b, a + b, a - b, -m, a == b, +=, -=, *=
```

#### Scalar helpers (same addon)

```c
float64 deg_to_rad(float64);
float64 rad_to_deg(float64);
float64 lerp_angle(float64 a, float64 b, float64 t);
float64 move_toward(float64 current, float64 target, float64 max_delta);
float64 ease_in(float64 t);
float64 ease_out(float64 t);
float64 ease_in_out(float64 t);
bool    approx_eq(float64 a, float64 b, float64 eps);
```

***

### Hash Set (`register_addon_hash_set`)

`hash_set<T>` for scalar T (int64, int32, etc.).

```c
hash_set<int64> s;
s.add(1); s.add(2); s.add(2);     // dedup
int64 n     = s.size();            // 2
bool  has   = s.contains(1);
bool  gone  = s.remove(2);
array snap  = s.to_array();        // snapshot copy
s.clear();

for (int64 v : s) { println(v); }
```

***

### Sorted Map (`register_addon_sorted_map`)

Ordered map `sorted_map<K, V>` for scalar K and V.

```c
sorted_map<int64, int64> m;
m.set(3, 300);
m.set(1, 100);
m.set(2, 200);

int64 v      = m.get(1);        // 100
int64 miss   = m.get(999);      // 0 if missing
int64 n      = m.size();        // 3
bool  had    = m.contains(2);
bool  gone   = m.remove(2);
array ks     = m.keys();        // keys in ascending order
array vs     = m.values();
int64 first  = m.first_key();
int64 last   = m.last_key();
m.clear();

for (int64 k, int64 v : m) { /* ordered by k */ }
```

***

### List (`register_addon_list`)

Generic double-ended container `list<T>` backed by `std::deque<int64_t>`. **O(1) push/pop both ends, O(1) random access.** Use for queues, deques, entity lists; `array<T>` is cheaper for strict LIFO / growable buffer.

```c
list<int64> lst;

// Add
lst.push_back(1);                  // alias: push
lst.push_front(0);
lst.insert(1, 99);                 // at idx (clamps to end if oob)

// Remove
int64 last  = lst.pop_back();      // alias: pop
int64 first = lst.pop_front();
int64 mid   = lst.remove(1);       // by idx; returns 0 if oob

// Access
int64 v     = lst.get(0);          // alias: at; returns 0 if oob
lst[0]      = 7;                   // subscript read + write
int64 f     = lst.first();
int64 l     = lst.last();

// Search
bool has    = lst.contains(99);    // alias: has
int64 idx   = lst.index_of(7);     // -1 if missing

// Size
int64 n     = lst.size();          // alias: length
bool empty  = lst.empty();

// Modify
lst.clear();
lst.reverse();                     // in-place

// Combine
list<int64> b; b.push_back(1); b.push_back(2);
lst.extend(b);                     // append b's elements to lst
list<int64> cp = lst.copy();       // independent shallow copy
array<int64> arr = lst.to_array(); // snapshot to array<T>

// Foreach (kv-iterable: index + value)
for (int64 i, int64 v : lst) { /* ... */ }

// Class T storage — list owns the heap, retrieved values alias
class Entity { int64 id; Entity(int64 i) { id = i; } }
list<Entity> ents;
ents.push_back(new Entity(1));      // ALWAYS new T(...) inline
Entity e = ents.first();             // reference handle
e.id = 42;                           // mutates the stored Entity
```

`list<T*>` is rejected at compile (typed-pointer V is Phase 2B). Use `list<T>` for class storage with reference semantics, or `list<int64>` for opaque handles.

***

### JSON (`register_addon_json`)

```c
json_value root = json_parse("{\"name\":\"alice\",\"age\":30}");

bool ok = root.is_valid();            // false if parse failed
int64 k = root.kind();                 // 0=null 1=bool 2=num 3=str 4=array 5=obj
bool b  = root.is_obj();
int64 n = root.size();                 // field count or array length

array keys = root.keys();              // [] if not an object
bool  has  = root.has_key("name");
json_value name = root.get_key("name");
json_value first = root.get_at(0);     // array subscript

// Type checks
bool n0 = v.is_null();
bool b0 = v.is_bool();
bool nb = v.is_num();
bool s0 = v.is_str();
bool a0 = v.is_array();
bool o0 = v.is_obj();

// Converters
bool    bv = v.as_bool();
float64 fv = v.as_num();
int64   iv = v.as_int();
string  sv = v.as_str();

// Building / mutating
json_value obj = json_object();
json_value arr = json_array();
obj.set_key("n", json_parse("42"));
obj.remove_key("n");
arr.push_value(json_parse("\"hi\""));   // all mutators deep-copy

// Output
string compact = root.stringify();
string pretty  = root.pretty();        // indented with newlines
```

***

### 35b. `std::*` source library (pure `.em` ports)

C++-parity stdlib types live **in script** — no engine code, no addon — built over the language's own template / pointer / RAII / tracked-`malloc` surface. Drop them inline (`#define VEC "namespace std { ... }"` etc.) or paste the template into your source. Heap accounting and leak detection cover them exactly like user code.

**A7 (2026-05-26):** lowercase `std::*` names ALSO work as aliases to the built-in addon types. `std::array<T>`, `std::vector<T>`, `std::map<K,V>`, `std::string`, `std::wstring`, `std::set<T>`, `std::list<T>` etc. all resolve via type-alias and use the built-in implementations — no breaking change to existing scripts using `array<T>`/`map<K,V>` directly. The pure-`.em` ports below (`std::Array`, `std::vector`, `std::Map`, etc. defined as user structs) take precedence when declared — the alias is skipped if the user has a struct/template by that name. Use whichever suits the codebase.

```cpp
namespace std {
    // — std::vector<T> — growable, malloc/realloc/free backing
    template<typename T>
    struct vector {
        public T* _data; public int64 _size; public int64 _cap;
        public vector();                  // initial cap 4
        public ~vector();                 // frees backing buffer
        public int64 size();              public bool empty();
        public int64 capacity();          public void reserve(int64 n);
        public void push_back(T v);       public void pop_back();
        public T front();                 public T back();
        public T at(int64 i);             // throws on OOB
        public T operator[](int64 i);
        public void operator[]=(int64 i, T v);
        public void clear();
        // — drop-in compat aliases for the addon T[] API —
        public void push(T v); public int64 length();
        public T get(int64 i); public void set(int64 i, T v);
        public T first(); public T last(); public void pop();
    }

    // — std::Array<T, N> — fixed-size, NTTP, no heap (over T data[N])
    template<typename T, int64 N>
    struct Array {
        public T data[N];
        public int64 size();   public bool empty();
        public T front();      public T back();
        public T at(int64 i);  // throws on OOB
        public T operator[](int64 i);
        public void operator[]=(int64 i, T v);
        public void fill(T v);
    }

    // — std::list<T> — doubly-linked, new/delete nodes
    template<typename T> struct ListNode { public T value;
                                            public ListNode<T>* prev;
                                            public ListNode<T>* next; }
    template<typename T>
    struct list {
        public ListNode<T>* _head; public ListNode<T>* _tail; public int64 _size;
        public list();        public ~list();              // clear()
        public int64 size();  public bool empty();
        public T front();     public T back();
        public void push_back(T v);   public void pop_back();
        public void push_front(T v);  public void pop_front();
        public void clear();
    }

    // — std::stack<T> / std::queue<T> — LIFO / FIFO over heap T*+size+cap
    template<typename T> struct stack {
        public T* _data; public int64 _size; public int64 _cap;
        public stack(); public ~stack();
        public int64 size(); public bool empty();
        public void push(T v); public void pop(); public T top();
    }
    template<typename T> struct queue {
        public T* _data; public int64 _size; public int64 _cap; public int64 _head;
        public queue(); public ~queue();
        public int64 size(); public bool empty();
        public void push(T v); public T front(); public T back(); public void pop();
    }

    // — std::span<T> — non-owning view of T* + size
    template<typename T> struct span {
        public T* _data; public int64 _size;
        public span(); public span(T* p, int64 n);
        public int64 size(); public bool empty();
        public T front(); public T back();
        public T operator[](int64 i);
    }

    // — std::Set<T> — linear-scan unique-element vector (O(n))
    template<typename T> struct Set {
        public T* _data; public int64 _size; public int64 _cap;
        public Set(); public ~Set();
        public int64 size(); public bool empty();
        public bool contains(T v);
        public bool insert(T v);   // false if already present
        public bool erase(T v);
        public void clear();
    }

    // — std::Map<K,V> — vector-of-pairs (O(n))
    template<typename K, typename V> struct Map {
        public K* _keys; public V* _vals;
        public int64 _size; public int64 _cap;
        public Map(); public ~Map();
        public int64 size(); public bool empty();
        public bool contains(K k);
        public V at(K k);                  // throws on missing
        public void insert(K k, V v);      // updates if key exists
        public bool erase(K k);
        public void clear();
    }

    // — Earlier types still available —
    // std::Optional<T>, std::Pair<A,B>, std::tmin/tmax/clamp/swap,
    // std::Tuple3, std::Result<T>, std::unique_ptr<T>,
    // std::shared_ptr<T>, std::weak_ptr<T>.
}
```

Sample usage:

```cpp
std::vector<int64> v;
for (int64 i = 0; i < 5; i = i + 1) v.push_back(i * 10);
int64 sum = 0;
for (int64 i = 0; i < v.size(); i = i + 1) sum = sum + v[i];   // 100

std::Array<int64, 8> grid;
grid.fill(0);
grid[3] = 42;

std::list<string> log;
log.push_back("ok"); log.push_back("err");

std::Map<int64, string> table;
table.insert(1, "one"); table.insert(2, "two");
string two = table.at(2);                                       // "two"
```

Hash-based variants (`std::unordered_set`, `std::unordered_map`) are not shipped yet — they need a hash function and the transitive-template-field gap (composing one template's instance as another template's field) closes first. `std::string` waits on Phase 6 char sub-8-byte packing.

***

### 36. Ship Cycle (for authors of the language)

```cpp
powershell -ExecutionPolicy Bypass -File ship.ps1             # builds /MT and /MD libs (addons bundled in)
powershell -ExecutionPolicy Bypass -File run_all_tests.ps1    # full test suite (uses the /MT lib)
powershell -ExecutionPolicy Bypass -File build_exe.ps1        # enma-lang.exe
cd ..\testing; powershell -ExecutionPolicy Bypass -File benchmark.ps1 -Runs 11
```

`ship.ps1` produces `enma_x64static_mt.lib` and `enma_x64static_md.lib` in `shipped/windows/`. Pick the one that matches your project's `/MT` or `/MD` flag - mixing the two yields a `RuntimeLibrary` linker error. Both libs include all 19 addons.

***

### 37. Full Hello-World Demo (every major feature touched)

```c
// Types
const int32 VER = 1;
constexpr int32 MAX = 100;

// Struct
struct Point {
    int32 x; int32 y;
    Point(int32 ix, int32 iy) { x = ix; y = iy; }
    int32 dist_sq(Point o) { int32 dx = x - o.x; int32 dy = y - o.y; return dx*dx + dy*dy; }
}

// Class + inheritance + override
class Entity {
    int32 hp;
    Entity(int32 h) { hp = h; }
    int32 get_hp() { return hp; }
    ~Entity() {}
}
class Player : Entity {
    int32 xp;
    Player(int32 h, int32 x) { hp = h; xp = x; }   // set base fields directly
    int32 get_hp() override { return hp + xp * 10; }
}

// Enum, typedef
enum Kind { None = 0, Hero = 1, Boss = 2 }
using Score = int32;

// Template
template<typename T>
struct Box { T v; Box(T x) { v = x; } T get() { return v; } }

// Delegate + function ref
delegate int32 Transform(int32 x);
int32 dbl(int32 v) { return v * 2; }

// Variadic
int64 sum(...) {
    int64 s = 0;  int64 i = 0;
    while (i < __va_count) { s = s + __va_arg(i); i = i + 1; }
    return s;
}

int32 main() {
    // Basics
    Point p = Point(3, 4);
    Point q = {.x = 6, .y = 8};
    int32 d = p.dist_sq(q);        // 25

    // Class
    Player hero = Player(100, 5);
    int32 hp = hero.get_hp();       // 150

    // Template
    Box<int32> bi = Box<int32>(42);
    int32 bv = bi.get();

    // Delegate
    Transform t = dbl;
    int32 r = t(5);                 // 10

    // Arrow lambda (typed as int64 function handle)
    int64 tripler = (int32 x) => x * 3;

    // Array + map
    int32[] nums = {1, 2, 3, 4};
    nums.push(5);
    int32 total = 0;
    for (int32 v : nums) total = total + v;

    map<string, int64> scores;
    scores.set("alice", 90);
    int64 a = scores.get("alice");

    // Exception
    try { if (hp < 0) throw -1; } catch (int32 e) { println(e); }

    // Defer
    defer { println("scope ending"); }

    // Heap
    Point* hp2 = new Point(1, 2);
    int32 hx = hp2->x;
    delete hp2;

    // Variadic call
    int64 s = sum(1, 2, 3, 4, 5);   // 15

    // Variant
    variant v = 42;
    if (v.is_int()) { println(v.as_int()); }

    return cast<int32>(total + s);
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/llms-language.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
