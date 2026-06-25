> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/templates.md).

# Templates

Compile-time monomorphization: each unique type combination produces a separate concrete implementation.

## Template Structs

```cpp
template<typename T>
struct Pair {
    T first;
    T second;
    Pair(T a, T b) { first = a; second = b; }
    T sum() { return first + second; }
}

Pair<int32> p = Pair<int32>(10, 20);
println(p.sum());  // 30

Pair<float64> fp = Pair<float64>(1.5, 2.5);
println(fp.sum());  // 4.0
```

## Template Functions

```cpp
template<typename T>
T max_val(T a, T b) {
    if (a > b) return a;
    return b;
}

int32 m = max_val<int32>(10, 20);  // 20
```

## Template with Reference Parameters

```cpp
template<typename T>
void swap_vals(T& a, T& b) {
    T temp = a;
    a = b;
    b = temp;
}

int32 x = 10;
int32 y = 20;
swap_vals<int32>(x, y);  // x=20, y=10
```

## Nested Templates

Template functions can take template-typed args:

```cpp
template<typename T>
struct Box {
    T val;
    Box(T v) { val = v; }
    T get() { return val; }
}

template<typename T>
T unwrap(Box<T> b) {
    return b.get();
}

Box<int32> b = Box<int32>(42);
int32 v = unwrap<int32>(b);  // 42
```

Type args themselves can be template instantiations — `Pair<Pair<int64>>`, `Box<Box<Box<int64>>>`, etc. The closing `>>` parses without spacing in both type position and ctor-call position.

## No script-level constraints

Script templates accept unconstrained `typename` parameters. SDK-side generic parameters can be constrained by host registration helpers such as `.requires_iface(...)`, but that constraint syntax is not available in script templates.

```cpp
template<typename T>
struct Box {
    T value;
}
```

Not supported today:

```cpp
// Invalid: script-level constraints do not exist.
template<typename T: Hashable>
struct SetLike { }
```

Use concrete helper functions or document the methods a template expects. Type errors surface when the compiler monomorphizes the template for a concrete `T`.

## Templated Base Classes

A class can inherit from a template instantiation:

```cpp
template<typename T> class Box {
    T value;
    Box(T v) { value = v; }
    T get() { return value; }
}

class IntBox : Box<int64> {
    IntBox(int64 v) : Box<int64>(v) {}
}

int64 main() {
    IntBox* b = new IntBox(42);
    int64 r = b->get();    // inherited from Box<int64>
    delete b;
    return r;
}
```

The init-list syntax `: Box<int64>(v)` invokes the instantiated base ctor. Override syntax in the derived class works as usual:

```cpp
class Special : Box<int64> {
    Special(int64 v) : Box<int64>(v) {}
    int64 get() override { return value * 100; }
}
```

## Nested-Array Init Lists

For typed arrays of arrays (or arrays of structs), brace-init lists nest naturally:

```cpp
int64[][] grid = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
int64 v = grid.get(1).get(0);   // 4

int64[][][] cube = {{{1, 2}, {3, 4}}, {{5, 6}, {7, 8}}};
int64 c = cube.get(1).get(0).get(1);   // 6

struct Point { int64 x; int64 y; }
Point[] pts = {Point(1, 2), Point(3, 4), Point(5, 6)};
Point p = pts.get(2);  // Point(5, 6)
```

## `std::*` Source-Library Containers (Pure-`.em` Ports)

C++-parity containers are written entirely in `.em` over the language's template / pointer / RAII / tracked-`malloc` surface — no engine support code. Drop the `namespace std { ... }` block into your source and use:

| Type                                                                          | Backing                                    | Notes                                                                                                                                               |
| ----------------------------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `std::vector<T>`                                                              | `T*` + size + cap                          | Growable. Has both C++ API (push\_back/size/...) and addon-T\[]-compat aliases (push/length/get/set).                                               |
| `std::Array<T, N>`                                                            | `T data[N]` C-array                        | Fixed size via NTTP. No heap. Capitalized while `array` lexer keyword stays.                                                                        |
| `std::list<T>`                                                                | doubly-linked `Node<T>*`                   | new/delete per node. Front + back ops O(1).                                                                                                         |
| `std::stack<T>` / `std::queue<T>`                                             | inline `T*` + size + cap (+head for queue) | Self-contained — no `vector` field (the transitive-template-instantiation gap means an outer template's vector-typed field can't auto-instantiate). |
| `std::span<T>`                                                                | borrowed `T*` + size                       | Non-owning view; doesn't free on drop.                                                                                                              |
| `std::Set<T>` / `std::Map<K,V>`                                               | linear-scan parallel arrays                | O(n) ops — fine for small N. Hash variants pending a hash function.                                                                                 |
| `std::Optional<T>` / `std::Pair<A,B>` / `std::Tuple3<...>` / `std::Result<T>` | inline fields                              | Earlier ports, see LLMS-Language.md §35b.                                                                                                           |
| `std::unique_ptr<T>` / `std::shared_ptr<T>` / `std::weak_ptr<T>`              | tracked heap + (atomic) refcount           | Smart pointers (Phase 16).                                                                                                                          |

```cpp
std::vector<int64> v;
for (int64 i = 0; i < 5; i = i + 1) v.push_back(i * 10);
int64 s = 0;
for (int64 i = 0; i < v.size(); i = i + 1) s = s + v[i];   // 100

std::Array<int64, 4> a;
a.fill(7);
a[1] = 42;

std::Map<int64, string> labels;
labels.insert(1, "one"); labels.insert(2, "two");
string two = labels.at(2);
```

The full type definitions are in `LLMS-Language.md` §35b. Pin them inline in your modules or share via `#include`. Heap accounting and leak detection treat them like any user code — `heap_count()` reflects their allocations.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/templates.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
