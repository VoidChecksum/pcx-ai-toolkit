# Enma Language Quick Reference

## Primitives

| Type | Size | Notes |
|------|------|-------|
| `bool` | 1B | `true` / `false` |
| `char` / `wchar` | 1B / 2B | ASCII / wide |
| `int8/16/32/64` | 1-8B | Signed |
| `uint8/16/32/64` | 1-8B | Unsigned |
| `aint8/16/32/64` | 1-8B | Atomic |
| `float32` / `float64` | 4B / 8B | IEEE single/double |
| `string` / `wstring` | ptr | UTF-8 / UTF-16 heap |
| `void` / `null` / `auto` | - | No value / null literal / inferred |

## Conversion Rules (COMPILE-TIME ENFORCED)

- `signed ↔ unsigned` → **COMPILE ERROR** — use `cast<uint64>(x)`
- `float → int` → **COMPILE ERROR** — use `cast<int32>(f)`
- `int → float` → implicit OK
- `float32 → float64` → implicit OK
- `float64 → float32` → **COMPILE ERROR** — use `cast<float32>(d)`
- `pointer ↔ int64/uint64` → implicit (both 8-byte)

## Variables

```cpp
int32 x = 42;
const float64 PI = 3.14;           // runtime-initialized, not reassignable
constexpr int32 MAX = 100;          // compile-time only
auto y = x + 1;                     // inferred
nullable int32 n = null;            // can hold null
```

## Operators

Arithmetic: `+ - * / %`  |  Comparison: `== != < > <= >=`  |  Logical: `&& || !`
Bitwise: `& | ^ ~ << >>`  |  Compound: `+= -= *= /= %= &= |= ^= <<= >>=`
Inc/Dec: `++ --`  |  Ternary: `cond ? a : b`  |  Cast: `cast<T>(x)`
Size: `sizeof(T)` `offsetof(Struct, field)`  |  Heap: `new T(args)` `delete`

## Control Flow

```cpp
if (x > 0) { } else if (x == 0) { } else { }
while (x > 0) x--;
do { x++; } while (x < 10);
for (int32 i = 0; i < 10; i++) { }
for (int32 v : arr) { }                          // for-each
for (string k, int64 v : m) { }                  // map for-each
switch (x) { case 1: break; default: break; }
int32 r = match (x) { 1 => 10, 2 => 20, _ => 0 };
defer { cleanup(); }                              // runs at scope exit
goto label; label: /* ... */
```

## Functions

```cpp
int32 add(int32 a, int32 b = 10) { return a + b; }   // default param
void swap(int32& a, int32& b) { /* pass by ref */ }   // reference
bool parse(string s, out int32 v) { /* write-only out */ }
void log(string fmt, ...) { /* variadic */ }
auto fn = (int32 x) => x * 2;                         // lambda
auto fn2 = [&cap](int32 x) -> int32 { return cap + x; }; // closure
```

## Structs (value types) vs Classes (reference types)

```cpp
struct Vec2 { float64 x; float64 y; }   // stack-allocated, copied on assign
class Player {                            // heap-allocated via new, virtual dispatch
    int32 health;
    Player(int32 h) { health = h; }
    virtual void update() { }
}
interface IDrawable { void draw(); }
mixin Logging for Player { void log() { println("hp=" + cast<string>(health)); } }
```

## Templates

```cpp
template<typename T>
T max(T a, T b) { return a > b ? a : b; }
template<typename T>
struct Stack { T[] items; void push(T v) { items.push(v); } }
```

## Arrays & Maps

```cpp
int32[] arr = {1, 2, 3};
arr.push(4); arr.pop(); arr.sort(); arr.reverse();
arr.contains(2); arr.index_of(3); arr.slice(0, 2);
arr.length(); arr.remove(0); arr.insert(1, 99);

map<string, int64> m;
m["key"] = 42; m.get("key"); m.contains("key");
m.remove("key"); m.length();
```

## Strings

```cpp
string s = f"value={x}";                         // interpolation
string h = format("addr=0x{x} name={s}", addr, name);  // format
s.length(); s.substr(0, 5); s.find("abc");
s.contains("x"); s.starts_with("pre"); s.ends_with("suf");
s.to_upper(); s.to_lower(); s.trim(); s.replace("a","b");
s.split(","); s.to_int(); s.to_float();
```

## Pointers

```cpp
int32* p = new int32(42);    // heap alloc
int32 v = *p;                // dereference (shallow copy)
delete p;                     // free
int32 x = 5; int32* px = &x; // address-of
Player* pl = new Player(100);
pl->update();                 // member access via pointer
```

## Coroutines

```cpp
coroutine int32 counter() { int32 i = 0; while (true) { yield i; i++; } }
coroutine_t c = counter();
c.next(); int32 v = c.value();
```

## Exceptions

```cpp
try { throw "error"; }
catch (string e) { println(e); }
// dtors and defer blocks run during stack unwinding
```

## Modules & Preprocessor

```cpp
import "math";                    // import module
import "utils" as u;              // aliased
using namespace MyLib;            // bring names into scope

#define DEBUG
#ifdef DEBUG
  println("debug mode");
#endif
#include "shared.em"
```

## Annotations

```cpp
[[packed]] struct Data { uint8 a; uint32 b; }     // no padding
[[align(16)]] struct Aligned { float32 v[4]; }
[[reflect]] struct Config { int32 x; }             // queryable from host
[[dll("user32.dll")]] extern int32 MessageBoxA(/*...*/);  // FFI
[[noopt]] void sensitive() { }                      // skip optimization
[[export]] void api_func() { }                      // visible to host
```
