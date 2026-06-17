> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/advanced.md).

# Advanced

## Delegates

Typed function references. Hold any function matching the signature.

```c
delegate int32 Transform(int32 x);

int32 double_it(int32 x) { return x * 2; }
int32 triple_it(int32 x) { return x * 3; }

Transform t = double_it;
println(t(5));    // 10
t = triple_it;
println(t(5));    // 15
```

## Namespaces

```c
namespace math {
    int32 square(int32 x) { return x * x; }
    int32 cube(int32 x) { return x * x * x; }
}

int32 r = math::square(5);  // 25
```

Pull names with `using namespace`:

```c
using namespace math;
int32 r = square(5);
```

Namespaces nest, can be reopened, and contain everything the language has — free fns, structs / classes (incl. inheritance + ctor init lists), enums (incl. `enum class`), globals, methods.

```c
namespace cfg { int64 max_iter = 1000; }                      // global with initializer
namespace col { enum class Color { Red = 1, Green = 2, Blue = 4 } }
namespace shapes {
    class Shape { int64 size; Shape(int64 s){ size = s; } virtual int64 area(){ return 0; } }
    class Square : Shape {                                     // bare base in same ns
        Square(int64 s) : Shape(s) {}
        virtual int64 area() override { return size * size; }
    }
}
namespace base    { class A { int64 v; A(int64 x){ v = x; } } }
namespace derived { class B : base::A { B(int64 x) : base::A(x + 50) {} } }   // cross-ns

int64 main() {
    int64 r1 = cfg::max_iter;                       // qualified read
    cfg::max_iter = 42;                             // qualified write
    int64 r2 = cast<int64>(col::Color::Blue);       // 3-deep enum-class value (= 4)
    shapes::Square s = shapes::Square(5);
    return s.area() + r1 + r2;
}
```

Inside a namespaced class, you can refer to other types in the same namespace using bare names — the compiler walks the enclosing chain to qualify return types, parameter types, base names, and ctor-init-list base names. So `Wrap make()` inside `namespace n { struct Maker { ... } }` finds `n::Wrap`.

Arrays of namespaced structs, ctor calls in expression context, operator overloads on ns types — all work as you'd expect:

```c
namespace n {
    struct V {
        int64 v;
        V(int64 x){ v = x; }
        V operator+(V o){ V r = V(0); r.v = v + o.v; return r; }
    }
}

int64 main() {
    n::V[] arr;
    arr.push(n::V(1));
    arr.push(n::V(2));
    n::V c = n::V(10) + n::V(32);
    return arr.get(0).v + arr.get(1).v + c.v;   // 1 + 2 + 42 = 45
}
```

## Coroutines

Functions that suspend execution with `yield` and resume later.

```c
coroutine int32 counter(int32 start) {
    int32 i = start;
    while (true) {
        yield i;
        i = i + 1;
    }
}
```

Drive via `coroutine_t`:

```c
coroutine_t c = counter(0);
while (c.next() == 1) {
    println(c.value());
    if (c.value() >= 4) break;
}
// prints: 0, 1, 2, 3, 4
```

`c.next()` returns `1` if the coroutine yielded a value, `0` if it finished. `c.value()` retrieves the last yielded value.

## Exceptions

Destructors and `defer` blocks run during stack unwinding.

```c
try {
    if (x < 0) throw -1;
    process(x);
} catch (int32 e) {
    println("error code:");
    println(e);
}
```

### Typed exceptions

`catch (T t)` fires only when the thrown value's type matches. A `try` block may chain multiple typed `catch` clauses; the first one whose declared type matches the thrown value runs.

```c
struct NetErr {
    int32 code;
    string msg;
    NetErr(int32 c, string m) { this->code = c; this->msg = m; }
}

try {
    throw NetErr(503, "timeout");
} catch (NetErr e) {
    println(e.code);       // 503
    println(e.msg);         // "timeout"
} catch (string e) {
    println(e);
} catch (int64 e) {
    println(e);
}
```

`throw T(args)` copies the struct value into a thread-local exception buffer — no heap allocation per throw, as long as the struct fits. `throw new T(args)` is also accepted and heap-allocates (use it when the struct is too large for the buffer). `defer` blocks and destructors run on exception unwind, not just on normal scope exit.

### Catching null-pointer dereferences

Dereferencing a null pointer with `->` inside a `try` block raises a catchable `string` exception with the message `"null pointer dereference"` instead of trapping the process. The check is emitted inline before each arrow-deref `load_field` (anchor + any intermediate ptr-deref in a chain), so deep chains like `a->b->c` catch the failure at the first null link.

```c
class N { int64 v; }

int32 main() {
    N* p = null;
    try {
        int64 x = p->v;          // throws "null pointer dereference"
        return 1;
    } catch (string e) {
        println(e);               // "null pointer dereference"
        return 0;
    }
}
```

Outside a `try` block, null deref still traps at runtime and returns control to the host with `execute()` reporting failure — the inline null check is only emitted inside `try` blocks, so the zero-cost path is preserved for code that doesn't opt into catching.

## Heap Allocation

`new` opts in to heap. Heap pointers are manually managed - call `delete` when done. No auto-free for `T*`.

```c
class Node {
    int32 val;
    Node(int32 v) { val = v; }
}

Node* n = new Node(42);
println(n->val);
delete n;
```

`T x = new T();` is a compile error, pick stack (`T x;`) or heap (`T* x = new T();`). `delete` on a non-pointer is a compile error. `delete null;` and double-delete are no-ops.

See [Pointers](/enma/language-guide/pointers.md) for the full pointer reference.

Two flavours of heap array:

```c
int64[] arr = new int64[256];       // dynamic array: push/pop/length/scope-drop

struct Cell { int32 v; Cell() { this->v = 0; } }
Cell* cs = new Cell[N];             // contiguous C-style: ctor per element
delete[] cs;                        // dtor per element, then free

struct Point {
    int32 x; int32 y;
    Point(int32 ix, int32 iy) { this->x = ix; this->y = iy; }
}
Point* ps = new Point[10](3, 4);    // every element constructed with (3, 4)
delete[] ps;
```

`T[] arr` is a growable, subscript-safe array with scope-drop cleanup. `T* p = new T[N]` is a raw contiguous block with per-element ctor/dtor and manual `delete[]`. Args after the size (`new T[N](args)`) are passed to each element's ctor; args are evaluated once, not N times. See [Structs & Classes](/enma/language-guide/structs-and-classes.md#contiguous-heap-arrays).

Use `p->field` for pointers, `p.field` for value structs. See [Lifecycle & RAII](/enma/sdk-guide/lifecycle.md).

### Nested arrays

Stack any number of `[]` for arrays of arrays. Each level stores an 8-byte handle to the inner array.

```c
int64[][] grid;                  // array of int64[]
int64[][][] cube;                // array of int64[][]

int64[] row;
row.push(1); row.push(2); row.push(3);
grid.push(row);                  // inner is cloned on push so the
                                 // container owns its own buffer
                                 // (the source local can drop safely)

int64[] r0 = grid.get(0);        // pull the inner array back out
int64 v   = grid.get(0).get(1);  // chain through directly
v        = grid[0][1];           // subscript chain works too
int64 n   = grid.length();       // outer length
```

`push`/`set`/`insert` clone-on-write at each level, so a freshly built inner array can be pushed and then go out of scope without dangling. Mutating the inner array via the cloned handle (`grid.get(0).set(...)`) mutates the container's copy.

### Escape errors

Stack structs can't escape their scope. Pick one of:

```c
struct Point { int32 x; int32 y; }
Point g_p;

int32 bad() {
    Point p;
    g_p = p;            // error: stack struct escapes its scope
    return 0;
}

Point* g_p_ptr;

int32 good() {
    Point* p = new Point();   // heap, OK to escape
    g_p_ptr = p;
    return 0;
}

int32 also_good() {
    Point p;
    g_p.x = p.x;              // OK (value copy), not pointer
    g_p.y = p.y;
    return 0;
}
```

Capturing a stack struct in an **escaping** closure is also an error:

```c
delegate int32 Getter();

Getter bad() {
    Point p;
    return () => p.x;   // error: escaping closure captures stack struct
}

Getter good() {
    Point* p = new Point();
    return () => p->x;  // OK, closure captures a heap pointer
}
```

## RAII Smart Pointers

Templates, move semantics, and deterministic destructors compose into C++-style smart pointers, written in script over the tracked heap. A move-only owning pointer:

```c
template<typename T>
struct unique_ptr {
    T* p;
    unique_ptr(T* raw) { p = raw; }
    unique_ptr(const unique_ptr<T>&) = delete;                    // non-copyable
    unique_ptr(unique_ptr<T>&& o) { p = o.p; o.p = cast<T*>(0); } // movable
    ~unique_ptr() { if (cast<int64>(p) != 0) { delete p; } }
    T* get() { return p; }
}

unique_ptr<Node> a = unique_ptr<Node>(new Node(7));
unique_ptr<Node> b = move(a);     // ownership transfers; a is emptied
int64 v = b.get()->val;           // 7
// b's `delete` runs at scope exit — no leak, no double-free
```

A reference-counted `shared_ptr<T>` follows the same shape with a shared count the copy ctor increments and the dtor decrements, freeing the object at zero.

## Static Assert

Compile-time assertion. Fails compilation if the condition is false. The expression must fold to a constant — anything `eval_constexpr` accepts works (see [Compile-Time Evaluation](#compile-time-evaluation) below).

```c
static_assert(sizeof(int32) == 4, "int32 must be 4 bytes");
static_assert(sizeof(float64) == 8, "float64 must be 8 bytes");
static_assert(sizeof(MyStruct) == 16, "layout drift");
```

The message is optional:

```c
static_assert(1 + 1 == 2);
```

When the assertion fails, the compiler reports the user message verbatim (or `static assertion failed` if none was supplied). When the expression isn't a compile-time constant, the compiler reports `static_assert expression must be a compile-time constant` and the line that tripped it.

`static_assert` works at module scope and inside function bodies.

```c
static_assert(MAX_PLAYERS <= 64);  // module scope

int32 main() {
    static_assert(sizeof(Packet) == 32, "packet abi");  // function scope
    return 0;
}
```

You can call any `constexpr` function from a `static_assert`, which makes it a powerful invariant checker. See the FNV-1a hashing example below.

## Compile-Time Evaluation

Mark a function or variable `constexpr` to evaluate it at compile time. References to the result fold into the IR as a literal, so there's no runtime cost.

### `constexpr` variables

```c
constexpr int32 MAX = 100;
constexpr int64 MASK = (0xff << 8) | 0xf;
constexpr float64 HALF = 1.0 / 2.0;
```

Initializers may use any expression `eval_constexpr` can fold — literals, integer/float arithmetic, bitwise ops, ternary, casts, `sizeof`/`offsetof`, enum values, other `constexpr` identifiers, and calls to `constexpr` functions.

If the initializer can't be folded the compiler reports `constexpr \`X\`: initializer is not a compile-time constant\` and the line.

`constexpr` variables (and functions) declared inside a namespace are visible to other declarations in the same namespace by their **bare** name, and to outside callers by their **qualified** name:

```c
namespace cfg {
    constexpr int64 value = 42;
    int64 get() { return value; }   // bare name — works inside `cfg`
}

int64 main() {
    return cfg::value + cfg::get();  // qualified access from outside
}
```

### `constexpr` functions

```c
constexpr int32 fact(int32 n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);
}

constexpr int32 FACT_10 = fact(10);
static_assert(FACT_10 == 3628800);
```

`constexpr` functions can use:

* arithmetic, bitwise, shift, comparison, logical ops
* ternary `cond ? a : b`
* `cast<T>(...)`
* local variables and assignments (including `+=`, `++`, etc.)
* `if`/`else`
* `for` and `while` loops
* recursion and mutual recursion
* calls to other `constexpr` functions
* `string.length()` and `string.char_at(int)` on string parameters or string literals

A loop budget caps total compile-time iterations at **100,000** per top-level call, so an accidentally infinite loop trips a clear error instead of hanging the compiler.

### Compile-time hashing (FNV-1a)

A canonical use case: hash a string at compile time so identifier lookups become constant integer comparisons.

```c
constexpr int64 fnv1a(string s) {
    int64 hash = 0xcbf29ce484222325;
    for (int32 i = 0; i < s.length(); i = i + 1) {
        hash = hash ^ s.char_at(i);
        hash = hash * 0x100000001b3;
    }
    return hash;
}

constexpr int64 H_PLAYER = fnv1a("player");
constexpr int64 H_ENEMY  = fnv1a("enemy");

static_assert(fnv1a("hello") == 0xa430d84680aabd0b, "fnv reference");
static_assert(H_PLAYER != H_ENEMY);

int32 dispatch(int64 h) {
    if (h == H_PLAYER) return 1;
    if (h == H_ENEMY)  return 2;
    return 0;
}
```

Both `H_PLAYER` and `H_ENEMY` collapse to immediates in the emitted IR. The `static_assert` tests run at compile time — they cost nothing at runtime.

### Things `constexpr` doesn't fold

These return `false` from `eval_constexpr` today and either cause an error (if used as a `constexpr` initializer or `static_assert` expression) or fall back to runtime evaluation (anywhere else):

* struct construction or field access
* array indexing and method calls beyond `string.length()` / `string.char_at(int)`
* pointer operations (`new`, `delete`, `&`, `*`)
* string concatenation
* calls to non-`constexpr` functions

If you hit one of these, hoist the work into a helper that returns the final scalar.

## Nullable Types

Allow a variable to hold `null`:

```c
nullable int32 n = null;
if (n == null) {
    println("is null");
}
n = 42;
```

## FFI

Call native shared libraries via `[[dll(...)]]`. Requires `PERM_FFI`.

```c
[[dll("libc.so.6")]]
extern int64 getpid();

[[dll("ws2_32.dll", "connect")]]
extern int32 ws_connect(int64 sock, int64 addr, int32 len);
```

Resolved at load time via `dlopen`/`dlsym` (Linux) or `LoadLibrary`/`GetProcAddress` (Windows).

## decltype

`decltype(expr)` is a type specifier that infers the type from an expression at compile time. Useful in generic code where you want to declare a variable whose type follows an existing one.

```c
int64 x = 42;
decltype(x) y = x + 1;           // y is int64

int32 a = 10;
decltype(a + a) sum = 100;       // sum is int32 (type of a + a)

int64 double_it(int64 v) { return v * 2; }
decltype(double_it(0)) r = 99;   // r is int64 (the return type)
```

Works anywhere a type specifier is accepted: var-decls, function parameters, return types.

## User-defined literals

Suffix a numeric literal with `_name` to rewrite it to a call `_name(value)`. Define the suffix function as a normal Enma function:

```c
int64   _km(int64 v)   { return v * 1000; }
int64   _ms(int64 v)   { return v; }
float64 _deg(float64 v) { return v * 3.14159265358979 / 180.0; }

int64   d    = 42_km;         // _km(42) = 42000
float64 rad  = 180.0_deg;     // ~3.14159 (pi)
int64   wait = 500_ms;
```

Works on integer, float, and hex literals. Calling an unknown suffix is a normal undefined-function compile error.

## Designated initializers

Struct literals support both positional and designated forms. Unlisted fields are zero-initialized.

```c
struct Point { int32 x; int32 y; }
struct Triple { int32 a; int32 b; int32 c; }

Point p = {3, 4};                    // positional: p.x=3, p.y=4
Point q = {.x = 10, .y = 20};        // designated
Point r = {.y = 5, .x = 1};          // order doesn't matter

Triple t = {.b = 42};                // a=0, b=42, c=0

Point bad = {.x = 1, .z = 99};       // compile error: no field z
```

Designated init is the aggregate-initialization form, it doesn't call a constructor. For types that need a ctor, use the function-call form: `Point p = Point(3, 4);`.

## Variadic Script Functions

Declare a script function with `...` to accept any number of trailing args. Access them with the `__va_count` intrinsic and `__va_arg(i)`:

```c
int64 sum(...) {
    int64 s = 0;
    int64 i = 0;
    while (i < __va_count) {
        s = s + __va_arg(i);
        i = i + 1;
    }
    return s;
}

int32 main() {
    int64 r = sum(1, 2, 3, 4, 5);   // 15
    return cast<int32>(r);
}
```

All args must fit in an `int64` slot, primitives, pointers, or heap handles. Mixed types are accepted at the call site; the function receives the raw bit pattern and is responsible for interpreting each `__va_arg(i)`.

## Inline Asm Intrinsics

Four preapproved x64 intrinsics that the JIT emits as their literal opcode bytes, no native-call overhead. No user-provided bytes, no arbitrary memory access.

```c
int64 tsc  = __asm_rdtsc();   // rdtsc, composed rdx:rax → int64
__asm_pause();                // F3 90 - spin-loop hint
__asm_mfence();               // 0F AE F0 - full memory barrier
__asm_nop();                  // 90
```

Use for tight perf timing (`__asm_rdtsc`), spin-wait loops (`__asm_pause`), and cross-thread memory ordering (`__asm_mfence`) without paying the call-boundary cost.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/advanced.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
