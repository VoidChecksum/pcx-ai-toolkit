> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/annotations.md).

# Annotations

Metadata on declarations via `[[name]]` or `[[name(args)]]`. Built-in ones drive compiler behavior; custom ones are stored for host querying.

## Compiler Annotations

### `[[noopt]]`

Disable all optimization passes for this function.

```cpp
[[noopt]]
int32 debug_func(int32 x) {
    return x + 1;
}
```

### `[[noinline]]`

Prevent the optimizer from inlining this function into callers.

```cpp
[[noinline]]
int32 always_call(int32 x) { return x * 2; }
```

### `[[inline]]`

Hint that this function should be inlined where possible.

```cpp
[[inline]]
int32 fast_add(int32 a, int32 b) { return a + b; }
```

### `[[noescape]]`

Compile error if any allocation in the function escapes its scope (store to global, return, captured by escaping closure, etc.).

```cpp
Point g_sink;

[[noescape]]
int32 bad() {
    Point p;
    g_sink = p;             // compile error: p escapes via global store
    return p.x;
}
```

### `[[packed]]`

Remove alignment padding from struct fields. Fields use their natural size instead of being padded to 8 bytes.

```cpp
[[packed]]
struct Packet {
    uint8 type;     // offset 0, size 1
    uint8 flags;    // offset 1, size 1
    int32 payload;  // offset 2, size 4
}
// sizeof(Packet) == 6
```

Without `[[packed]]`, each field would be padded to 8 bytes, giving `sizeof == 24`.

### `[[align(N)]]`

Set custom alignment for a struct. `N` is the alignment in bytes. Composable with `[[packed]]`.

```cpp
[[align(16)]]
struct AlignedData {
    int32 x;
    int32 y;
}
// sizeof(AlignedData) == 16
```

Also works on individual fields — forces that field's offset to N-byte alignment AND bumps the struct's overall alignment to at least N:

```cpp
struct Lane {
    int64 hdr;
    [[align(16)]] vec3 pos;     // pos at offset 16, not 8
    int64 ftr;                  // immediately after pos
}
```

### `[[offset(N)]]`

Per-field annotation. Forces the field to land at exactly byte offset `N`. Accepts decimal or hex (`[[offset(0x10)]]`). Compile error if the requested offset would overlap a prior field.

Useful for matching reverse-engineered game-struct layouts where field offsets are known from a memory dump:

```cpp
struct GameEntity {
    [[offset(0x10)]] int64 health;
    [[offset(0x40)]] vec3  position;
    [[offset(0x80)]] int64 team_id;
}
// Field positions match the dumped layout regardless of declaration order
```

Combined for SIMD-aligned types (Unreal-style FVector — 3 float32 fields, 16-byte aligned):

```cpp
[[packed]] [[align(16)]] struct FVector {
    float32 x;
    float32 y;
    float32 z;
}
// size = 16; offsets x=0, y=4, z=8 (matches Unreal MS_ALIGN(16))
```

### `[[reflect]]`

Generate runtime introspection functions for a struct. Creates four callable functions:

```cpp
[[reflect]]
struct Vec3 {
    float64 x;
    float64 y;
    float64 z;
}

int32 count = Vec3::__reflect_count();     // 3
string name = Vec3::__reflect_name(0);     // "x"
int32 type  = Vec3::__reflect_type(0);     // type id for float64
int32 off   = Vec3::__reflect_offset(1);   // 8
```

### `[[serialize]]`

Auto-generate serialization methods for a struct. Creates `to_bytes` and `from_bytes` functions.

```cpp
[[serialize]]
class Config {
    int32 width;
    int32 height;
    int32 flags;
    Config(int32 w, int32 h, int32 f) { width = w; height = h; flags = f; }
}

Config c = Config(1920, 1080, 7);
int64 buf = Config::to_bytes(c);

Config c2 = Config(0, 0, 0);
Config::from_bytes(c2, buf);
// c2.width == 1920, c2.height == 1080, c2.flags == 7
```

### `[[export]]`

Mark a function for module export. When a module is compiled to `.emb` and imported, only functions with `[[export]]` are visible to the importer. If no functions have `[[export]]`, all non-internal functions are visible (default behavior).

```cpp
[[export]]
int32 public_api(int32 x) { return x * 2; }

int32 internal_helper(int32 x) { return x + 1; }
// internal_helper is NOT visible when this module is imported
```

### `[[dll(...)]]`

Bind to a native shared library function. Requires `PERM_FFI` permission.

```cpp
[[dll("libc.so.6")]]
extern int64 getpid();

[[dll("mylib.dll", "my_export")]]
extern int32 custom_fn(int32 a, int32 b);
```

## Custom Annotations

Unknown annotations are parsed, stored on the AST node, and queryable from the host via `get_annotated_functions()` / `get_annotations()`.

```cpp
[[priority(5)]]
[[category("combat")]]
void attack(int32 target) { }
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/annotations.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
