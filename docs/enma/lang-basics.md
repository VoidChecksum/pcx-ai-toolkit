> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/basics.md).

# Basics

## Types

| Type                                     | Size | Description            |
| ---------------------------------------- | ---- | ---------------------- |
| `bool`                                   | 1B   | `true` / `false`       |
| `char`                                   | 1B   | ASCII character        |
| `wchar` / `wchar_t`                      | 2B   | Wide character         |
| `int8` / `int16` / `int32` / `int64`     | 1-8B | Signed integers        |
| `uint8` / `uint16` / `uint32` / `uint64` | 1-8B | Unsigned integers      |
| `aint8` / `aint16` / `aint32` / `aint64` | 1-8B | Atomic integers        |
| `float32`                                | 4B   | Single-precision float |
| `float64`                                | 8B   | Double-precision float |
| `string`                                 | ptr  | Heap-managed string    |
| `wstring`                                | ptr  | Wide string            |
| `void`                                   | 0    | No value               |
| `null`                                   | -    | Null literal           |
| `auto`                                   | -    | Type inference         |

**Literals.** `"text"` is a `string` and `L"text"` a `wstring`; `'c'` is a `char` and `L'c'` a `wchar`. `wchar_t` is an accepted spelling of `wchar`. (String/char escapes like `\n`, `\t`, `\xHH` apply to both narrow and wide forms.)

## Variables & Constants

```c
int32 x = 42;
const float64 PI = 3.14;
constexpr int32 MAX = 100;
auto y = x + 1;
nullable int32 n = null;
```

`const` prevents reassignment. `constexpr` evaluates at compile time and folds into the IR as a literal — see [Compile-Time Evaluation](/enma/language-guide/advanced.md#compile-time-evaluation) for what's foldable and how to write `constexpr` functions and `static_assert`s. `nullable` allows a variable to hold `null`. `auto` infers the type from the right-hand side.

### Multi-declarator syntax

You can declare multiple variables of the same type on one line, separating each declarator with a comma. Each declarator may have its own initializer or be left uninitialized:

```c
int64 i, j, k;                       // three uninitialized locals
int64 a = 10, b = 20, c = 30;        // three with initializers
int64 x = 1, y, z = 3;               // mixed: y has no initializer
float64 px, py, pz;                  // works for any type
string s1 = "a", s2 = "b", s3;       // strings too
```

The same form works at every declaration site:

```c
// Globals
uint32 g_a, g_b, g_c;

// Namespace globals
namespace cfg { int64 width, height; string title; }

// Struct / class fields
struct Vec3 { float64 x, y, z; }
class Foo {
    private: int64 a, b, c;
    public: Foo() { a = 1; b = 2; c = 3; }
}

// For-init clause
for (int64 i = 0, j = 100; i < 5; i = i + 1) { /* ... */ }
```

The type applies uniformly to every declarator. For pointers, **all declarators are pointers** — `int64* p, q;` makes both `p` and `q` of type `int64*` (deviates from C/C++, which would make only `p` a pointer). Bit-fields (`int8 x : 4`) are single-declarator only — declare each bit-field on its own line.

## String literals

Double-quoted strings produce `string` values. Adjacent literals do **not** auto-concatenate (unlike C/C++) — use `+` to join: `"hello" + " " + "world"`.

Supported escape sequences:

| Escape     | Produces                                                                                                                                 |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `\n`       | newline (LF, 0x0A)                                                                                                                       |
| `\t`       | tab (0x09)                                                                                                                               |
| `\r`       | carriage return (0x0D)                                                                                                                   |
| `\\`       | backslash                                                                                                                                |
| `\0`       | null byte                                                                                                                                |
| `\xHH`     | one byte from up to two hex digits — useful for embedding raw UTF-8 sequences (e.g. `"\xEE\xA9\xB0"` is a single 3-byte UTF-8 codepoint) |
| `\<other>` | the literal character (the backslash is dropped)                                                                                         |

```c
string newline = "line one\nline two";
string utf8    = "\xEE\xA9\xB0";    // 3-byte UTF-8 sequence, length() == 3
```

f-string interpolation (see [Advanced](/enma/language-guide/advanced.md)) follows the same escape rules.

## Number Literals

```c
int32 a = 42;            // integer literal → default int32
int64 b = 42;            // fits context
int64 c = 0xFF;          // hex
int64 d = 0b1010;        // binary
float64 e = 3.14;        // float literal → default float64
float32 f = 3.14f;       // f/F suffix → float32
float64 g = 1.5e-3;      // scientific notation

int64 big = 1_000_000;   // underscore digit separator (any numeric form)
int64 mask = 0xFF_FF_FF; // separator works inside hex too
int64 bin  = 0b1010_1100; // and binary
float64 pi = 3.141_592_6; // and floats

int64 km = 42_km;        // user-defined literal suffix (calls _km(42))
float64 m = 1.5_m;       // same for float literals
int64 mix = 1_500_km;    // separator + UDL: parses as 1500 with _km suffix
```

Float literals use `f` / `F` suffix for `float32`; bare `3.14` is `float64`. Integer literals default to `int32` in contexts that accept any integer but adapt when assigned to a wider type. Underscore digit separators (`1_000_000`) work in all numeric forms — they're stripped at lex time so `std::stoll`-style parsers see clean digits. User-defined literal suffixes (`_km`, `_m`, etc.) parse as calls to a same-named function - see [user-defined literals](/enma/language-guide/advanced.md) for details. The lexer distinguishes the two by what follows the underscore: digit → separator, alpha → UDL.

## Operators

* **Arithmetic:** `+` `-` `*` `/` `%` — modulo follows C semantics (result takes the sign of the dividend: `-7 % 2 == -1`).
* **Comparison:** `==` `!=` `<` `>` `<=` `>=`
* **Logical:** `&&` `||` `!`
* **Bitwise:** `&` `|` `^` `~` `<<` `>>`
* **Assignment:** `=` `+=` `-=` `*=` `/=` `%=` `&=` `|=` `^=` `<<=` `>>=`
* **Increment / Decrement:** `++` `--` (prefix and postfix)
* **Ternary:** `cond ? a : b`

Arithmetic on unsigned narrow integer types (`uint8`, `uint16`, `uint32`) wraps modulo the type's width on assignment — `uint8 b = 255; b = b + 1;` leaves `b == 0`. Internally Enma's arithmetic operates on 64-bit values, but stores back to narrow unsigned locals mask the result to the declared width. Signed narrow types (`int8` / `int16` / `int32`) carry through int64 arithmetic with sign-extend on read.

* **Cast:** Five C++-style variants:
  * `cast<T>(val)` — Enma's loose generic conversion (numeric truncate / promote, bool truthiness, registered converters, user `operator __cast_T()` overload).
  * `static_cast<T>(val)` — same well-defined conversions as `cast<>` (alias for now; reserved for stricter checks).
  * `reinterpret_cast<T>(val)` — bit-pattern preserving. Source and target must be the same byte size; emits compile error otherwise. Float ↔ int at the f32 boundary handles narrow/widen automatically. Replaces the `bits_f*_to_*` host natives. Example: `reinterpret_cast<uint32>(1.5f) == 0x3FC00000`.
  * `const_cast<T>(val)` — identity at the IR level; same byte size required. Used to strip const for ergonomics (e.g. copying a const local to a mutable one).
  * `dynamic_cast<T*>(ptr)` — runtime-checked downcast for polymorphic class pointers. Returns `ptr` if its actual runtime type IS-A `T` (including any class derived from `T`), or `null` on cast failure. Uses **vtable identity** rather than RTTI strings — the binary contains no struct names or type-info metadata, so the implementation cannot be reverse-engineered to recover the class hierarchy from string scans. Null source yields a null result (no AV). Common idiom: `if (D* d = dynamic_cast<D*>(b)) { ... }`.
* **Sizeof:** `sizeof(type)` returns the byte size of a type or struct.
* **Offsetof:** `offsetof(Struct, field)` returns the byte offset of a field.
* **Heap:** `new T(args)`, `new T[N]`; `delete ptr`, `delete[] ptr`.

## Control Flow

### if / else

```c
if (x > 0) {
    println("positive");
} else if (x == 0) {
    println("zero");
} else {
    println("negative");
}
```

### while / do-while

```c
while (x > 0) {
    x = x - 1;
}

do {
    x = x + 1;
} while (x < 10);
```

### for

```c
for (int32 i = 0; i < 10; i++) {
    println(i);
}
```

### for-each

```c
int32[] arr = {1, 2, 3};
for (int32 v : arr) {
    println(v);
}
```

Two-variable form iterates a map (or any indexable type whose registration provides a key getter):

```c
map<string, int64> m;
m.set("a", 1);
m.set("b", 2);
for (string k, int64 v : m) {
    println(k);
    println(v);
}
```

### switch

```c
switch (x) {
    case 1: println("one"); break;
    case 2: println("two"); break;
    default: println("other");
}
```

### match

A match expression returns a value. The `case` keyword is optional.

```c
int32 result = match (x) {
    1 => 10,
    2 => 20,
    3 => 30,
    _ => 0
};
```

Match arms can have block bodies. Blocks execute as statements (they don't yield a value), so use the expression form when you need a result.

```c
match (x) {
    case 1 => { println("one"); },
    _ => { println("other"); }
};
```

### defer

`defer` schedules a statement to run when the enclosing scope exits, including during stack unwinding from exceptions.

```c
int64 handle = open_resource();
defer { close_resource(handle); }
// handle is always closed, even if an exception is thrown
```

### goto

```c
goto done;
println("skipped");
done:
println("reached");
```

### break / continue

`break` exits the innermost loop. `continue` skips to the next iteration.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/basics.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
