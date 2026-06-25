> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/pointers.md).

# Pointers

Pointers are typed handles to heap objects. Allocate with `new`, free with `delete`. Access fields and methods with `->`. Use `.` on values and `->` on pointers as a style convention — the parser accepts either form for both, but mixing makes code harder to read and auto-formatting may rewrite to the canonical form.

Storing the address of a local somewhere it could outlive the local is a compile error — the escape analyzer rejects anything that could dangle. Pointer arithmetic on typed pointers is supported (see below).

Pointer ↔ `int64` / `uint64` is implicit (both 8-byte slots, lossless on x64). Useful for handing handles to native APIs and for taking script-side function references via `&fn` (a `pointer` value that converts to `int64` without a cast). The implicit conversion is not a workaround for the escape analyzer - allocation and lifetime rules still apply.

## Process memory is not Enma heap memory

Typed Enma pointers are for Enma heap objects allocated with `new`. Do not model arbitrary target-process addresses as `T*` unless the memory is actually an Enma object. For reverse-engineering byte offsets, keep addresses as `uint64` and use Perception Proc/CPU APIs.

Preferred:

```c
uint64 entity = base + offsets[i];
int32 hp = proc.r32(entity + 0x120);
string name = proc.rs(entity + 0x180, 32);
```

Do not use typed casts for raw target memory:

```c
// Invalid / unsafe model for target-process memory.
Player* p = cast<Player*>(base + offset);
```

Typed pointer arithmetic scales by `sizeof(T)`: `p + 1` means "next T", not "next byte". Integer-to-pointer assignment is not a byte-offset traversal primitive.


## Allocation & Deletion

```c
struct Node {
    int32 val;
    Node(int32 v) { val = v; }
    int32 get() { return val; }
}

Node* p = new Node(42);
println(p->val);     // 42
println(p->get());   // 42; idiomatic for pointers

delete p;            // manual free
```

`delete null` and double-delete are no-ops. `delete` on a non-pointer is a compile error.

## Null

```c
Node* p = null;
if (p == null) { /* ... */ }
p = new Node(1);
if (p != null) { delete p; }
```

`null` is assignable to any pointer type.

## Aliasing

Two pointers can refer to the same object. `delete` on a non-null pointer fires the dtor, frees the heap memory, and zeroes the source slot — so a subsequent `delete p;` is a no-op via the same null guard. Aliased pointers in OTHER slots still hold the freed address; accessing them is undefined behaviour.

```c
Node* a = new Node(1);
Node* b = a;          // same object
b->val = 99;
println(a->val);      // 99
delete a;             // b is now dangling, don't touch
```

## Copy via `*pt`

Dereferencing a pointer gives you a fresh independent copy of the pointee. Field-by-field memberwise copy (matching C++ default copy ctor semantics): primitive fields copy by value, inline struct fields recurse into their layout, pointer-typed fields stay shallow (alias).

```c
class Pt { int32 x; int32 y; Pt() { x = 0; y = 0; } Pt(int32 a, int32 b) { x = a; y = b; } }

Pt* a = new Pt(1, 2);
Pt b = *a;           // independent copy
b.x = 99;
println(a->x);       // still 1, unaffected by b.x = 99
```

For class types (reference types), `*pt` allocates a new heap instance — `b` is a heap object distinct from `*a`. For value-type structs you'd typically copy by assignment from a struct local rather than dereferencing a pointer; `*pt` is most useful for breaking aliasing on class types.

For deep copy of heap-managed sub-objects (string fields, array fields, nested class held by reference), define an explicit `clone()` method on the class — `*pt` is intentionally shallow to match C++ defaults.

## Move via `move(x)`

Transfer ownership of a heap object from one variable to another. The source slot is nulled out; subsequent access null-faults at runtime.

```c
Pt* a = new Pt(1, 2);
Pt* b = move(a);     // b inherits the handle, a becomes null
println(b->x);       // 1
println(a->x);       // null deref - traps
```

`move(x)` returns the value at `x` AND writes 0 (null) to `x`'s slot in one step. Distinct from `*pt` which makes an independent copy and leaves the source intact. Useful for explicit ownership transfer without a copy.

Currently restricted to a simple variable name — `move(arr[i])` and `move(s.field)` error out at compile time. Move through a temporary and clear the original slot yourself:

```c
Foo* tmp = arr[i];
Foo* owned = move(tmp);
arr[i] = null;
```

## Pointer Fields & Globals

Heap pointers can escape, they can be stored in globals, fields, or returned from functions. Stack structs cannot.

```c
struct Bag { Node* head; }

Node* g_root = null;

void install() {
    g_root = new Node(7);   // OK (heap)
}

Bag make_bag() {
    Bag b;
    b.head = new Node(1);   // OK (heap) pointer in a struct
    return b;
}
```

## Heap Arrays

Raw contiguous blocks. Separate from `T[]` growable arrays.

```c
struct Point { int32 x; int32 y; Point() { x = 0; y = 0; } }

Point* ps = new Point[10];          // default-ctor each
ps[0].x = 1;                        // element access: ps[i] is the Point value
ps[9].y = 2;
delete[] ps;                        // dtor each, then free

Point* ys = new Point[4](3, 5);     // every element constructed with (3, 5)
delete[] ys;
```

Args after `[N]` are evaluated once and forwarded to each element's ctor. Wrong arity is a compile error.

`int64[] xs = new int64[256]` is the other form, a growable array with `push`/`pop`/`length`, scope-drop cleanup, no `delete[]` needed. See [Arrays](addon-arrays.md).

## Fixed-Size Arrays

C++ declarator syntax — the size follows the name: `T name[N]`. `N` is an integer literal or a `constexpr`. The array lives for its scope and is released automatically; there is no `delete`.

```c
int32 buf[3];                 // primitive: lives in the stack frame, zero heap
buf[0] = 4; buf[1] = 5; buf[2] = 6;
int32 sum = 0;
for (int32 i = 0; i < 3; i++) sum = sum + buf[i];   // 15

int32 vals[2] = { 10, 20 };   // brace init (primitive elements)
```

A fixed array decays to `T*`: pass it to a function, take `&buf[0]` (or `&buf[i]`), and index/write through the pointer.

```c
int64 sum_n(int64* p, int64 n) {
    int64 s = 0;
    for (int64 i = 0; i < n; i++) s = s + p[i];
    return s;
}

int64 b[3];
b[0] = 10; b[1] = 20; b[2] = 30;
println(sum_n(b, 3));     // 60 — decays to &b[0]

int64 total = 0;
for (int64 e : b) total = total + e;   // range-for
```

Struct/class elements work the same way. Each element is default-constructed at the declaration; `name[i].field` accesses it. At scope exit every element's destructor runs and the storage is freed — no `delete[]`.

```c
struct Pt { int64 x; int64 y; }

Pt pts[2];
pts[0].x = 3; pts[1].y = 4;
println(pts[0].x + pts[1].y);   // 7

class Node { int64 v; string tag; Node() { v = 0; tag = ""; } }
Node ns[4];                     // ctor runs for each; dtors + frees at scope end
```

The type-prefix spelling `T[N] name` is a compile error — write `T name[N]`. Struct-element arrays are default-constructed only; a brace initializer on them is rejected. For a heap array you manage yourself, use `new T[N]` / `delete[]` (above).

A struct or class can hold a fixed array of structs as a **member** (`struct Bag { Pt items[2]; }`) or declare one at **global** scope (`Pt gps[3];`): each element is default-constructed up front, so `bag.items[i].field` / `gps[i].field` always indexes a live element. Members are destroyed with their containing object; globals live for the program.

## Pointer Arithmetic

Typed pointers support arithmetic, scaled by the element. `p + n` / `p - n` advance by n elements, `++p` / `--p` step one, `p - q` gives the element distance, and `p[i]` is `*(p + i)`.

```c
int64* p = new int64[4];
p[0] = 10; p[1] = 20; p[2] = 30;

int64* q = p + 1;      // points at p[1]
int64 v = *q;          // 20
q++;                   // now p[2]
int64 d = q - p;       // 2 (element distance)
delete[] p;
```

Works on any typed pointer — a `new T[N]` block, a pointer field, or a pointer returned from a function. `void*` has no element type; cast it to a typed pointer before arithmetic or deref. Multi-level pointers (`T**`) and `alignof(T)` are also supported.

## Reference Parameters

`T& param` passes by reference. The callee mutates the caller's variable. Not a pointer; no `&` at the call site.

```c
void swap(int32& a, int32& b) {
    int32 t = a; a = b; b = t;
}

int32 x = 1;
int32 y = 2;
swap(x, y);      // x=2, y=1, no & needed
```

Struct references avoid copying:

```c
void add_in_place(vec3& dst, vec3 other) {
    dst.x = dst.x + other.x;
    dst.y = dst.y + other.y;
    dst.z = dst.z + other.z;
}
```

`out T` is the same ABI but signals the param is write-only and skips reading its initial value.

## Local References

`T& r = x;` binds `r` as an alias of `x` — reads and writes go straight to `x`. The referent must be a variable, field, or another reference (an initializer is required; an expression or temporary is rejected).

```c
int64 x = 5;
int64& r = x;
r = 9;            // x is now 9

const int64& cr = x;   // read-only alias
```

## Return by Reference

`T& f()` returns a reference to a variable, field, or member the caller can read or assign through.

```c
class Counter {
    int64 v;
    int64& slot() { return v; }   // hand out a reference to the field
}

Counter c;
c.slot() = 42;            // writes c.v
int64 n = c.slot();       // reads c.v (auto-dereferenced)
int64& r = c.slot();      // bind it
```

## Pointer-to-Member Functions

A pointer-to-member-function holds a method address; the receiver is supplied at the call. Take one with `@Cls::method` or `&Cls::method`; invoke with `(obj.*pmf)(args)` or `(ptr->*pmf)(args)`, which pass `obj`/`ptr` as the implicit receiver.

```c
class Foo {
    int64 v;
    int64 dbl(int64 a) { return a * 2; }
}

typedef int64 (Foo::*Fn)(int64);

Foo f;
Fn pmf = &Foo::dbl;
int64 r = (f.*pmf)(21);          // 42 — f is the receiver

Foo* p = new Foo();
int64 s = (p->*pmf)(21);         // 42
delete p;
```

The value is a plain method address — store it in a `Fn` typedef or an `int64`, keep it in a struct field, or pass it to pick a method at runtime. Dispatch is non-virtual (the named method, not a derived override).

## Escape Errors

Stack structs can't escape. The compiler rejects anything that would dangle:

```c
struct Point { int32 x; int32 y; }
Point g_p;
Point* g_ptr = null;

int32 bad_return() {
    Point p;
    return &p.x;           // compile error: pointer to local
}

int32 bad_store() {
    Point p;
    g_ptr = &p;            // compile error: stack pointer stored globally
    return 0;
}

int32 ok_copy() {
    Point p;
    g_p.x = p.x;           // OK (value copy)
    return 0;
}

int32 ok_heap() {
    Point* p = new Point();
    g_ptr = p;              // OK (heap) pointer
    return 0;
}
```

## What's Rejected

| Operation                              | Result                             |
| -------------------------------------- | ---------------------------------- |
| `T* p = &local;` stored to global      | Compile error (escape)             |
| `return &local;`                       | Compile error (escape)             |
| `T x = new T();`                       | Compile error (pick stack or heap) |
| `delete x;` where `x` is value         | Compile error                      |
| Escaping closure captures stack struct | Compile error                      |

## Runtime Traps

These are caught by the runtime fault handler and surface as `execute()` returning `false`:

* Null deref through a pointer
* Out-of-bounds on `T[]` arrays (positive or negative)
* Use-after-free when the freed-marker is still readable
* Double `delete[]` on heap arrays

Inside a native C++ function, dereferences are not trapped. Validate inputs on the native side. Use `heap_is_tracked(ptr)` if the pointer came from Enma's heap.

## Quick Reference

| Pattern                                | Meaning                                          |
| -------------------------------------- | ------------------------------------------------ |
| `T* p = new T(args);`                  | Heap allocate with ctor                          |
| `T* p = new T[N];`                     | Heap array, default-ctor each element            |
| `T* p = new T[N](ctor_args);`          | Heap array, every element ctor'd with ctor\_args |
| `delete p;`                            | Free single-object heap allocation               |
| `delete[] p;`                          | Free heap array (runs per-element dtor)          |
| `p->field`                             | Field access on a pointer                        |
| `p->method()`                          | Method call on a pointer                         |
| `T* q = p;`                            | Alias                                            |
| `T* p = null;` / `p == null`           | Null                                             |
| `void fn(T& x)`                        | Reference parameter (not a pointer)              |
| `void fn(out T x)`                     | Write-only reference parameter                   |
| `T& r = x;`                            | Local reference alias                            |
| `T& f()`                               | Return by reference                              |
| `@Cls::m` / `&Cls::m`                  | Pointer-to-member-function                       |
| `(obj.*pmf)(args)` / `(p->*pmf)(args)` | Call through a pointer-to-member-function        |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/pointers.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
