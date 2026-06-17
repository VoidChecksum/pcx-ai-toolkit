> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/structs-and-classes.md).

# Structs & Classes

## Structs

Structs are value types, stack-allocated by default. Only explicit `new T(...)` goes to the heap, and heap pointers are manually managed with `delete`.

| Syntax                                     | Storage                             | Cleanup                     |
| ------------------------------------------ | ----------------------------------- | --------------------------- |
| `T x;`                                     | stack                               | auto `::~T()` at scope exit |
| `T x = T(args);`                           | stack                               | auto `::~T()` at scope exit |
| `T x = f();` (struct-returning call)       | caller's stack buffer (return slot) | auto `::~T()` at scope exit |
| `T x = a + b;` (operator returning struct) | stack                               | auto `::~T()` at scope exit |
| `T* p = new T(args);`                      | heap                                | **manual**. `delete p;`     |
| `T[] arr = new T[N];`                      | heap (Enma dynamic array)           | `arr.free()` or scope-drop  |
| `T* p = new T[N];`                         | heap (contiguous C-style array)     | **manual**. `delete[] p;`   |

`T x = new T();` is a compile error, pick stack (`T x;`) or heap (`T* p = new T();`). `delete` on a non-pointer is also a compile error. `delete null;` is a no-op. Mixing `delete` and `delete[]` is undefined behavior (match the form you allocated with).

### Contiguous heap arrays

`T* p = new T[N];` allocates N contiguous elements. `p[i]` accesses by offset; `delete[] p;` frees the block.

```c
struct Cell {
    int32 v;
    Cell() { this->v = 0; }
    ~Cell() { /* cleanup */ }
    void inc() { this->v = this->v + 1; }
}

int32 main() {
    Cell* cs = new Cell[4];   // ctor fires 4 times; all cs[i].v = 0
    cs[0].inc();
    cs[0].inc();
    int32 sum = cs[0].v + cs[1].v + cs[2].v + cs[3].v;   // 2
    delete[] cs;              // dtor fires 4 times, then frees the block
    return sum;
}
```

N may be a literal or any int expression. Element count stored as an 8-byte prefix inside the allocation so `delete[]` can loop the dtor correctly. If T has a no-arg ctor, it runs on every element at alloc time; if T has a dtor, it runs on every element at delete time. If T has neither, bytes are zero-initialized and freed.

**Ctor args**: pass args after the size to forward them to every element's ctor:

```c
struct Point {
    int32 x; int32 y;
    Point(int32 ix, int32 iy) { this->x = ix; this->y = iy; }
}
Point* ps = new Point[10](3, 4);   // Point(3, 4) called 10 times
delete[] ps;
```

Args are evaluated once before the loop; each element sees the same values. Wrong arity is a compile error.

**Primitive T also supported**. `int32* p = new int32[N]`, `float64* p = new float64[N]`, etc. Primitive elements use 8-byte slots (Enma's internal convention) and are zero-initialized.

`delete[]` must match `new T[N]` (use `delete` without brackets for `new T()`).

### Escape via container methods

Some container methods capture their argument past the call. Passing a stack struct to such a method is a compile error:

```c
Point[] arr = new Point[4];
Point p;
p.x = 10;
arr.push(p);        // error: cannot pass local struct `p` to `push()` ...
```

Fix by constructing on the heap inline, or by using a `T*` pointer:

```c
arr.push(new Point(10, 20));   // OK (heap) alloc captured by the array

Point* q = new Point();
q->x = 10;
arr.push(q);                   // OK, you own q via delete
```

Capturing methods: `array.push`, `array.set`, `array.insert`, `map.set` (value arg). Driven by `.captures_arg(i)` on the addon side; custom types can opt in.

### Basic Struct

```c
struct Vec2 {
    float64 x;
    float64 y;
}

Vec2 v;
v.x = 1.0;
v.y = 2.0;
```

### Constructors & Methods

```c
struct Vec2 {
    float64 x;
    float64 y;
    Vec2(float64 a, float64 b) { x = a; y = b; }
    float64 length_sq() { return x*x + y*y; }
}

Vec2 v = Vec2(3.0, 4.0);        // stack
float64 lsq = v.length_sq();    // 25.0
```

### Implicit Initialization

Without an explicit constructor, positional args map to fields in declaration order:

```c
struct Color {
    int32 r;
    int32 g;
    int32 b;
    int32 sum() { return r + g + b; }
}

Color c = Color(255, 128, 0);  // r=255, g=128, b=0
```

### Destructors

```c
struct Resource {
    int64 handle;
    Resource(int64 h) { handle = h; }
    ~Resource() { close(handle); }
}
```

Destructors run deterministically at scope exit: normal control flow, exception unwind, and JIT fault unwind (div-by-zero, OOB, null deref). The `}` is the trigger.

### Chained construction & destruction

Member fields with constructors auto-fire when their parent constructs, in **declaration order**. Destructors fire in **reverse declaration order** between the user dtor body and the base-class dtor chain. Mirrors C++ exactly.

```c
struct Inner {
    int64 v;
    Inner() { v = 42; }              // fires automatically
    ~Inner() { /* fires automatically too */ }
}

struct Outer {
    Inner a;
    Inner b;
    Outer() { /* a.ctor + b.ctor have already fired */ }
    ~Outer() {
        // 1. user dtor body runs first
        // 2. b's ~Inner fires (reverse declaration order)
        // 3. a's ~Inner fires
        // 4. base class dtor chain (if Outer has bases)
    }
}

{ Outer o; }
// Output: a.ctor → b.ctor → Outer.ctor → ~Outer body → b.~Inner → a.~Inner
```

Container fields (`string`, `list<T>`, `map<K,V>`, `hash_set<T>`, `sorted_map<K,V>`, `imap<V>`, `vec3`, `T[]`) auto-init to empty on parent construction and clean up on destruction. Class-V elements have their `~T()` called per element before the container's heap is freed:

```c
class Player {
    string name;
    ~Player() { /* fires automatically per element */ }
}

class Roster {
    list<Player> active;
    map<string, Player> by_name;
    Roster() {
        active.push_back(new Player());
        by_name.set("p1", new Player());
    }
}

{ Roster r; }
// Each Player gets its ~Player called as the container is walked,
// then the container itself is freed, then ~Roster body runs.
```

Constructor init lists (`Outer() : a(arg) {}`) override the default no-arg auto-init for that specific field — the explicit `Inner(arg)` runs instead, no double-construction, no leak.

**Init order follows declaration order, not init-list source order.** Just like C++. Given

```c
struct A { A() { mark(1); } }
struct B { B(int64 x) { mark(2); } }
struct C { C() { mark(3); } }

struct Owner {
    A a;
    B b;
    C c;
    Owner() : c(), b(0) { mark(4); }   // init-list mentions c first, then b
}
```

the init order is `A` → `B(0)` → `C` → body → final log = `1234`. The init-list source order (`c(), b(0)`) controls *what* runs for each field but not *when* — declaration order wins. Fields not mentioned in the init list get their default no-arg ctor at their slot in the order. Destructors fire in reverse declaration order.

### Escape is a compile error

Stack structs can't escape their scope:

```c
struct Point { int32 x; int32 y; }
Point g_last;

int32 main() {
    Point p;
    p.x = 1;
    g_last = p;          // error: stack struct escapes its scope; use `new Point(...)`
    return 0;
}
```

Fix by heap-allocating:

```c
Point* g_last;

int32 main() {
    Point* p = new Point();
    p->x = 1;
    g_last = p;          // OK, g_last holds a heap pointer
    return 0;
}
```

Or by copying field values:

```c
g_last.x = p.x;
g_last.y = p.y;           // OK (value copy), not a pointer
```

### Passing & Copying

Struct and class values follow C++ value semantics: pass-by-value is a copy, assignment is a copy, return is a copy. Mutating a parameter's fields inside the callee does NOT touch the caller.

```c
struct Box { int64 v; Box(int64 x) { v = x; } }

void mutate(Box b) {
    b.v = 999;             // local to b; caller's Box stays at 7
}

int64 main() {
    Box a = Box(7);
    mutate(a);
    return a.v;            // 7
}
```

```c
Box a = Box(7);
Box c = a;                 // independent copy
c.v = 99;                  // a.v still 7
```

When you want reference semantics, use a pointer:

```c
void mutate_ref(Box* b) {
    b->v = 999;            // dereference modifies the caller's Box
}

Box a = Box(7);
mutate_ref(&a);
// a.v is now 999
```

Same rules inside operator overloads. `operator+(T other)` receives a copy of `other`; reading or modifying its fields has no side effect on the caller.

For deep-copying with non-trivial fields, you can write an explicit `clone()`:

```c
struct Vec3 {
    float64 x; float64 y; float64 z;
    Vec3(float64 a, float64 b, float64 c) { x = a; y = b; z = c; }
    Vec3 clone() { return Vec3(x, y, z); }   // returns by-value (copy)
}
```

### Const Methods

Trailing `const` marks a method as non-mutating. Inside a const method, `this` is read-only.

```c
struct Counter {
    int32 n;
    int32 inc() { this->n = this->n + 1; return this->n; }
    int32 get() const { return this->n; }
}

int32 observe(const Counter c) {
    int32 v = c.get();      // OK
    c.inc();                // compile error: non-const method on const receiver
    return v;
}
```

A `const T` parameter rejects field assignment through it. Non-const methods can't be called on const receivers.

### Operator Overloading

```c
struct Vec2 {
    float64 x;
    float64 y;
    Vec2(float64 a, float64 b) { x = a; y = b; }
    Vec2 operator+(Vec2 o) { return Vec2(x + o.x, y + o.y); }
    Vec2 operator-(Vec2 o) { return Vec2(x - o.x, y - o.y); }
    Vec2 operator*(float64 s) { return Vec2(x * s, y * s); }
    bool operator==(Vec2 o) { return x == o.x && y == o.y; }
}

Vec2 a = Vec2(1.0, 2.0);
Vec2 b = Vec2(3.0, 4.0);
Vec2 c = a + b;  // Vec2(4.0, 6.0)
```

**Supported operators**

| Form                  | Operators                                                     | Example signature                                                                                                                                                                                                                                                                                                                                                                 |
| --------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Binary arithmetic     | `+`, `-`, `*`, `/`, `%`                                       | `T operator+(T other)`                                                                                                                                                                                                                                                                                                                                                            |
| Comparison            | `==`, `!=`, `<`, `>`, `<=`, `>=`                              | `bool operator==(T other)`                                                                                                                                                                                                                                                                                                                                                        |
| Three-way comparison  | `<=>`                                                         | `int64 operator<=>(T other)` — define one, all six comparison ops auto-derive: `a < b` becomes `(a <=> b) < 0`. Negative = less, 0 = equal, positive = greater. Derived classes inherit `operator<=>` from any base in the chain — `Derived a, b; a < b;` works as long as some base defines it.                                                                                  |
| Bitwise / shift       | `&`, `\|`, `^`, `<<`, `>>`                                    | `T operator^(T other)`                                                                                                                                                                                                                                                                                                                                                            |
| Compound assignment   | `+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `\|=`, `^=`, `<<=`, `>>=` | `void operator+=(T other)` (mutates `*this`)                                                                                                                                                                                                                                                                                                                                      |
| Copy assignment       | `=`                                                           | `void operator=(const T& other)` — fires on `b = a;` for already-constructed `b`. Lets the type release `b`'s old resources before assigning `a`'s. (Distinct from copy ctor `T(const T&)`, which fires on `T b = a;` while constructing `b`.)                                                                                                                                    |
| Move assignment       | `=`                                                           | `void operator=(T&& other)` — selected when the RHS is an rvalue: `b = move(a)`, or a fresh temporary (`b = T(args)`, or `b = make()` where `make` returns `T` by value). An lvalue RHS (`b = a`, a borrowed element `b = arr.get(0)`, or a reference-returning call `b = ref_fn()`) stays on copy-assignment. Falls back to copy-assignment when no move-assignment is declared. |
| Increment / decrement | `++`, `--`                                                    | `T operator++()` (prefix) / `T operator++(int)` (postfix). C++'s int-dummy-param convention; if only one is declared, both prefix and postfix dispatch through it.                                                                                                                                                                                                                |
| Unary                 | `-`, `~`, `!`, `*`                                            | `T operator-()` / `bool operator!()` / `U operator*()` (smart-pointer-style deref — when the operand is a value struct, `*obj` calls this; pointer deref `*pt` for `T*` keeps regular memberwise-copy semantics).                                                                                                                                                                 |
| Subscript             | `[]`, `[]=`                                                   | `T operator[](int64 i)` / `void operator[]=(int64 i, T v)`                                                                                                                                                                                                                                                                                                                        |
| Function call         | `()`                                                          | `T operator()(args...)` — makes the type callable: `obj(a, b)`                                                                                                                                                                                                                                                                                                                    |
| Type conversion       | `operator T()`                                                | Called by `cast<T>(obj)` AND implicitly at variable initialization, function-argument binding, return statements, and arithmetic operands. T can be a primitive (int64, bool, ...) OR another struct.                                                                                                                                                                             |
| Smart-pointer arrow   | `->`                                                          | `U* operator->()` — `obj->member` reads `member` on the returned pointer; `obj->method(...)` calls a method on it                                                                                                                                                                                                                                                                 |

`!=` automatically negates `==` if you don't define it explicitly. `[]=` is the assigning form (`obj[i] = v`) — declare it separately from the read form `[]`. Compound assignment auto-falls-back to the matching binary op if you don't define it explicitly: `a += b` resolves to `a = a + b` when `operator+=` is missing but `operator+` is defined. The three-way `<=>` operator works the same way for the six comparisons — `<` `>` `<=` `>=` `==` `!=` all derive from a single `<=>` if defined. Explicit specific operators take priority over `<=>` when both are present.

**Inheritance and operator overloads.** When a derived type doesn't define its own operator, the dispatcher walks the base chain looking for one — `class D : B {}` with `B::operator+(const B&)` lets `D d1, d2; d1 + d2` compile and run against the inherited `B::operator+`. The rhs is implicitly upcast from `D` to `B`. Override the operator on `D` to specialise the behavior.

**Operators on globals and ns-qualified globals.** Operator overloads dispatch correctly whether the operands are locals, globals, namespace-qualified globals (`ns::g_a + ns::g_b`), or struct-field receivers (`g_pair.a + g_pair.b`). The compiler routes ref-param ABIs through a temp-spill so the `const T&` indirection matches whatever the source's storage shape is.

**Free-function operators + ADL.** Operators can also be defined as free functions outside the struct:

```cpp
struct P { int64 v; }
bool operator==(P a, P b) { return a.v == b.v; }
P    operator+ (P a, P b) { P r; r.v = a.v + b.v; return r; }
```

When the free operator lives inside a `namespace`, Enma finds it via **Argument-Dependent Lookup (ADL)** — `ns::P x, y; if (x == y)` resolves `ns::operator==(P, P)` even though the call site is unqualified and outside the namespace. The compiler walks the operand type's enclosing namespace chain looking for matching free operators:

```cpp
namespace ns {
    struct P { int64 v; }
    bool operator==(P a, P b) { return a.v == b.v; }
    P    operator+ (P a, P b) { P r; r.v = a.v + b.v; return r; }
}

int64 main() {
    ns::P x; x.v = 42;
    ns::P y; y.v = 42;
    if (x == y) {         // finds ns::operator== via ADL
        ns::P z = x + y;  // finds ns::operator+ via ADL, returns ns::P by value
        return z.v;
    }
    return 0;
}
```

Free operators returning a value-struct go through the same NRVO/SRET path as struct-method operators — the result is constructed directly into the destination slot. The return type of an ADL-resolved operator is also visible to `return x + y;` and `auto z = x + y;` so type-checking and inference work without a temp local.

**ADL coverage details:**

* **All operator categories** — arithmetic (`+`, `-`, `*`, `/`, `%`), bitwise (`&`, `|`, `^`, `<<`, `>>`), comparison (`==`, `!=`, `<`, `>`, `<=`, `>=`), unary (`-`, `~`, `!`, `++`, `--`), spaceship (`<=>`), and compound assignment (`+=`, `-=`, etc.).
* **All param ABI shapes** — by-value `P`, by-ref `P&`, const-ref `const P&`, mixed. The compiler spills + leas references automatically.
* **Inheritance** — if `class D : ns::B`, then `D` instances can dispatch through `ns::operator==(B, B)` via ADL. The compiler walks the operand type's base chain when resolving free operators.
* **Member operators take priority over free operators** — if both exist, the member version is selected.
* **`operator<=>` synthesis** — a free `int64 operator<=>(P, P)` declared in a namespace synthesizes all six comparison ops (`<`, `>`, `<=`, `>=`, `==`, `!=`) via ADL just like member spaceship.
* **Compound assign fallback** — `a += b` finds member `T::operator+=` first; if absent, falls back to member `T::operator+` then to free `ns::operator+` via ADL, synthesizing `a = a + b`.

```cpp
namespace math {
    struct V3 { float64 x; float64 y; float64 z; }

    V3   operator+(const V3& a, const V3& b) { V3 r; r.x = a.x + b.x; r.y = a.y + b.y; r.z = a.z + b.z; return r; }
    V3   operator-(const V3& a)              { V3 r; r.x = -a.x; r.y = -a.y; r.z = -a.z; return r; }
    bool operator==(const V3& a, const V3& b){ return a.x == b.x && a.y == b.y && a.z == b.z; }
}

int64 main() {
    math::V3 u; u.x = 1.0; u.y = 2.0; u.z = 3.0;
    math::V3 v; v.x = 1.0; v.y = 2.0; v.z = 3.0;
    math::V3 sum = u + v;     // ADL + const-ref + SRET
    math::V3 neg = -u;        // ADL unary
    u += v;                   // ADL compound (falls back to operator+)
    if (u == v) return 0;
    return 1;
}
```

**Return-by-value (NRVO).** A function returning a value-struct constructs the result directly into the caller's return slot — no intermediate temp, no copy ctor. This matches C++17 mandatory copy elision. Constructors / dtors fire exactly once per object, balanced. `make()` discarded inline still runs `~T()` at end-of-statement.

```c
struct Bits {
    uint64 v;
    Bits(uint64 x) { v = x; }
    Bits operator&(Bits o) { return Bits(v & o.v); }
    Bits operator|(Bits o) { return Bits(v | o.v); }
    Bits operator^(Bits o) { return Bits(v ^ o.v); }
    Bits operator~()       { return Bits(~v); }
    bool operator!()       { return v == 0; }
    bool operator==(Bits o){ return v == o.v; }
}

struct Adder {
    int64 base;
    Adder(int64 b) { base = b; }
    int64 operator()(int64 x) { return base + x; }
}

Adder a = Adder(100);
int64 r = a(5);   // 105

struct Inner {
    int64 v;
    Inner(int64 x) { v = x; }
    int64 doubled() { return v * 2; }
}
struct Holder {
    Inner* p;
    Holder(int64 v) { p = new Inner(v); }
    Inner* operator->() { return this->p; }   // smart-pointer style
}

Holder h = Holder(42);
int64 v = h->v;            // 42 — operator->() then read .v on returned ptr
int64 d = h->doubled();    // 84 — operator->() then call .doubled() on returned ptr
delete h.p;

struct Box {
    int64 v;
    Box(int64 x) { v = x; }
    operator int64() { return v * 2; }
    operator bool()  { return v != 0; }
}

Box b = Box(21);
int64 i = cast<int64>(b);   // 42 — calls operator int64()
int64 j = b;                // 42 — same call, fired implicitly at variable init
bool  z = cast<bool>(b);    // true — calls operator bool()
bool  w = b;                // true — implicit at variable init

// Cross-struct conversion — T can be another struct, not just a primitive.
struct Celsius   { float64 deg; Celsius(float64 d)   { deg = d; } }
struct Fahrenheit {
    float64 deg;
    Fahrenheit(float64 d) { deg = d; }
    operator Celsius() { return Celsius((deg - 32.0) * 5.0 / 9.0); }
}

Fahrenheit f = Fahrenheit(212.0);
Celsius    c = f;                   // implicit — calls operator Celsius()
Celsius    e = cast<Celsius>(f);    // explicit — same call
```

### User-defined copy and move constructors

`T(const T& other)` overrides the default field-by-field copy. `T(T&& other)` is the move ctor — fires on `T c = move(a);`.

```c
struct Counter {
    int64 v;
    Counter(int64 x)             { v = x; }
    Counter(const Counter& other) { v = other.v; }            // copy
    Counter(Counter&& other)      { v = other.v; }            // move (a is nulled after)
}

Counter a = Counter(7);
Counter b = a;          // copy ctor — a stays valid
Counter c = move(a);    // move ctor — a is nulled (subsequent a.v traps)
```

If only a copy ctor is declared, `move(a)` falls back to it (same call shape, source still nulled). If neither is declared, `T c = a;` does default memberwise copy (matches C++'s implicit copy ctor). Move and copy ctors coexist with regular 1-arg ctors like `T(int)` — they resolve as distinct overloads so there's no conflict.

### Explicit constructors and conversions

`explicit` on a constructor or conversion operator blocks implicit conversion through it — only direct construction (`T(x)`) and `cast<T>(x)` invoke it.

```c
struct Meters {
    float64 v;
    explicit Meters(float64 m) { v = m; }
    explicit operator float64() { return v; }
}

Meters d = Meters(5.0);          // OK — direct construction
Meters e = 5.0;                  // error — implicit conversion through explicit ctor
float64 f = cast<float64>(d);    // OK — explicit cast
float64 g = d;                   // error — implicit conversion through explicit operator
```

The same applies to by-value arguments and return values: an implicit conversion through an `explicit` member is a compile error. Without `explicit`, all of these conversions fire implicitly (see the conversion-operator row above).

**Not overloadable:** `&&`, `\|\|` (short-circuit; can't preserve evaluation order), `,` (footgun).

### Bitfields

```c
struct Flags {
    int32 active : 1;
    int32 priority : 4;
    int32 state : 3;
}
```

Multiple values packed into a single 64-bit word.

### Layout control — `[[packed]]`, `[[align(N)]]`, `[[offset(N)]]`

Struct-level annotations control the overall layout:

```c
[[packed]] struct NetHeader {       // no padding, 1+4+1+1 = 7 bytes
    int8  version;
    int32 length;
    int8  flags;
    int8  reserved;
}

[[align(16)]] struct AlignedPair {  // total size rounded to 16-byte boundary
    int64 lo;
    int64 hi;
}
```

Per-field annotations target individual fields — useful when matching exact byte layouts of game structs from a memory dump or external API:

```c
// [[align(N)]] forces this field's offset to N-byte alignment
struct SimdLane {
    int64 hdr;
    [[align(16)]] vec3 pos;     // pos at offset 16, not 8
    int64 ftr;                  // immediately after pos
}

// [[offset(N)]] forces an exact byte offset (decimal or hex)
struct GameEntity {
    [[offset(0x10)]] int64 health;
    [[offset(0x40)]] vec3  position;
    [[offset(0x80)]] int64 team_id;
}
// → exact match to the dumped layout, regardless of field declaration order
```

Combined for SIMD-aligned types (Unreal-style FVector — 3 float32 fields, 16-byte aligned):

```c
[[packed]] [[align(16)]] struct FVector {
    float32 x;
    float32 y;
    float32 z;
}
// size = 16; offsets x=0, y=4, z=8
```

Without `[[packed]]`, primitive field sizes are bumped to 8 bytes (handle compatibility). Apply `[[packed]]` to get exact C/C++ widths per field.

## Classes

Reference types with single or multiple inheritance and virtual dispatch.

```c
class Entity {
    int32 hp;
    Entity(int32 h) { hp = h; }
    int32 get_hp() { return hp; }
    void damage(int32 d) { hp = hp - d; }
}
```

### Inheritance

```c
class Player : Entity {
    int32 armor;
    Player(int32 h, int32 a) { hp = h; armor = a; }
    override int32 get_hp() { return hp + armor; }
}
```

`override` can appear before the return type or after the parameter list:

```c
override int32 get_hp() { return hp + armor; }
int32 get_hp() override { return hp + armor; }
```

### Multiple inheritance

Enma supports C++-style multi-class inheritance for both `class` and `struct`. Each base is laid out as its own subobject in declaration order, and derived classes inherit fields and methods from every base.

```c
class Health {
    int32 hp;
    Health() { hp = 100; }
    void take_damage(int32 d) { hp = hp - d; }
}

class Mana {
    int32 mp;
    Mana() { mp = 50; }
    void spend(int32 cost) { mp = mp - cost; }
}

class Player : Health, Mana {
    int32 xp;
    Player() { xp = 0; }
}

Player* p = new Player();
p->take_damage(30);  // Health.hp = 70
p->spend(15);        // Mana.mp = 35  (this auto-adjusted to point at Mana subobject)
delete p;
```

**Constructor chaining.** When `new Player()` runs, each base's no-arg constructor fires in **declaration order** before the derived body executes (Health, then Mana, then Player). Destructors fire in **reverse order** at `delete` (Player, then Mana, then Health).

```c
class A { A() { /* fires first */ } ~A() { /* fires last  */ } }
class B { B() { /* fires second */ } ~B() { /* fires second-to-last */ } }
class C : A, B { C() { /* fires last */ } ~C() { /* fires first */ } }
```

**Diamond inheritance is rejected.** If two bases share a common ancestor, the compiler errors instead of silently giving you two copies. Restructure with composition or pull common functionality into the derived class.

```c
class Base { int32 v; }
class L : Base { }
class R : Base { }
class D : L, R { }   // compile error: diamond. `Base` reachable via L and R
```

**Field name conflicts across bases are rejected.** If two bases declare a field with the same name, derived can't have both. Rename one of them.

**Bases past the first need a `this`-adjusted pointer.** When you call a method from a non-first base (`p->spend(...)` above is from `Mana`, not the primary `Health`), enma compiles in a pointer adjustment so the method body sees its expected subobject layout. This happens automatically.

**Method name conflicts.** If two bases declare a method with the same name, the derived class must override it to disambiguate (or the compiler errors).

```c
class A { int32 sig() { return 10; } }
class B { int32 sig() { return 20; } }   // same name as A::sig

class C : A, B {
    // override int32 sig() { return 999; }  // <-- required to compile
}
// Without the override above: compile error
//   "method 'sig' is declared by both 'A' and 'B'. Override it in the derived class to disambiguate."
```

**Upcast** to a base pointer is implicit in all four conversion contexts: variable declaration, function argument, assignment, and return value. The compiler shifts the pointer to the base subobject as needed:

```c
Mana* m = p;          // var_decl upcast: m = p + offset_of_Mana_in_Player

void take(Mana* m) { ... }
take(p);              // fn-arg upcast

m = make_other_player();   // assignment upcast

Mana* find_player_mana(Player* p) {
    return p;         // return upcast
}
```

**Override through any base pointer.** Virtual dispatch through any base pointer (primary or non-primary) finds derived overrides. The compiler synthesizes `this`-adjusting thunks for non-primary base subobjects automatically:

```c
class A { int32 sig() { return 10; } }
class B { int32 sig() { return 20; } }   // also need override in C to disambiguate
class C : A, B {
    override int32 sig() { return 999; }
}

C* c = new C();
A* a = c;
B* b = c;
c->sig();  // 999 (direct)
a->sig();  // 999 (primary base)
b->sig();  // 999 (non-primary base, dispatched via thunk)
```

**Explicit base init lists.** When a base needs ctor args, use the C++-style `: Base(args)` syntax:

```c
class Player : Health, Mana {
    int32 xp;
    Player(int32 h, int32 m) : Health(h), Mana(m) { xp = 0; }
}
```

Bases without an entry in the init list use their no-arg ctor (or default-init if no ctor is declared).

If you need behavior from multiple sources without the inheritance ceremony, **composition** is also available:

```c
class Z : Health {
    Mana inner;
    Z() { }
    void spend(int32 c) { inner.spend(c); }   // forward
}
```

### Virtual Dispatch

Method calls through a base-type pointer dispatch to the derived implementation via the class's vtable slot:

```c
Player* p = new Player(100, 50);
Entity* e = p;          // base-type pointer to derived instance
int32 hp = e->get_hp(); // calls Player::get_hp → 150
delete p;
```

## Interfaces

Method-signature contracts that structs must implement.

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

For SDK-registered interfaces (`.as_interface()` + `.implements(...)`), an interface-typed local dispatches method calls at runtime, including across reassignment:

```c
Stream s = file_stream(path);   // concrete impl assigned to iface var
int64 n = s.write("hello");     // dispatches to file_stream.write
s = mem_stream(...);
int64 m = s.write("...");       // dispatches to mem_stream.write
```

## Mixins

Add methods to an existing struct from outside its definition:

```c
struct Rect {
    int32 x;
    int32 y;
    int32 w;
    int32 h;
}

mixin int32 Rect::area() { return w * h; }
mixin int32 Rect::perimeter() { return 2 * (w + h); }
```

## Properties

Getter/setter syntax for computed values. Both blocks are optional; supply `get`, `set`, or both.

```c
struct Rect {
    int32 w;
    int32 h;
    property int32 area {
        get { return w * h; }
    }
    property int32 width {
        get { return w; }
        set { w = value; }
    }
}

Rect r = Rect(10, 5);
int32 a = r.area;     // 50, calls getter
r.width = 20;         // calls setter; `value` holds the rhs
```

## Enums

```c
enum Color { Red = 0, Green = 1, Blue = 2 }

int32 c = Color::Red;
```

## Typedefs

```c
using ID = int32;
using Point = Vec2;

ID player_id = 42;
Point pos = Vec2(1.0, 2.0);
```

`typedef int32 ID;` (C-style) also works.

## Structs / classes inside namespaces

Everything works the same — fields, methods, ctors, dtors, operator overloads, inheritance, virtual / override, ctor init lists. Access from outside is `ns::Type(args)` or, after `using namespace ns;`, just `Type(args)`. Namespaces nest and can be reopened.

```c
namespace shapes {
    class Shape {
        int64 size;
        Shape(int64 s) { size = s; }
        virtual int64 area() { return 0; }
    }

    // Bare base name `Shape` works for same-namespace inheritance.
    class Square : Shape {
        Square(int64 s) : Shape(s) {}
        virtual int64 area() override { return size * size; }
    }
}

namespace base   { class A { int64 v; A(int64 x){ v = x; } } }
namespace derived {
    // Cross-namespace base — qualify the base name.
    class B : base::A {
        B(int64 x) : base::A(x + 50) {}
    }
}

int64 main() {
    shapes::Square s = shapes::Square(5);
    derived::B b = derived::B(7);
    return s.area() + b.v;       // 25 + 57 = 82
}
```

A method on a namespaced class can refer to other types in the same namespace using bare names — the compiler walks the enclosing namespace chain to qualify return types, parameter types, base names, and ctor-init-list base names. So inside `namespace n { struct Maker { Wrap make(int64 x) { ... } } }`, the unqualified `Wrap` resolves to `n::Wrap`.

Arrays of namespaced structs work the same as unqualified ones:

```c
namespace n { struct V { int64 v; V(int64 x){ v = x; } } }

int64 sum() {
    n::V[] arr;
    arr.push(n::V(1));
    arr.push(n::V(2));
    arr.push(n::V(3));
    return arr.get(0).v + arr.get(1).v + arr.get(2).v;   // 6
}
```

## Constructor initializer lists

Initialize base classes and value-struct fields before the body runs.

```c
struct Inner { int64 v; Inner(int64 x){ v = x; } }

struct Outer {
    Inner i;             // value-struct field with a ctor
    int64 outer_v;
    Outer(int64 x, int64 y) : i(x) {   // calls Inner::Inner$1 on this->i
        outer_v = y;
    }
}

int64 main() {
    Outer o = Outer(10, 32);
    return o.i.v + o.outer_v;   // 10 + 32 = 42
}
```

The init-list runs before the body. For a `class D : Base` with `D(int x) : Base(x + 50) { }`, the base-class ctor is called first; for a `Inner i;` field with `: i(arg)`, the field's inner ctor runs and the result is stored into the field. Fields not mentioned in the init list get default initialization (or whatever the body writes first).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/structs-and-classes.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
