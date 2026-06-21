# Enma Context Pack

> Single-file context pack for AI tools writing Enma scripts. Bundles the language docs, platform APIs, behavioral skills, and quick-reference knowledge most relevant when working in Enma.

> **Generated** by `tools/build-llms-index.py` — do not edit manually. Re-generate by running the tool from the repo root. CI verifies the committed bundle matches the current source.

**Source files included: 82**

---

## Source: `docs/enma/UPSTREAM-SUGGESTIONS.md`

# Upstream Suggestions for the Enma Language & SDK

> Moved here from the repo root (`SuggestionsEnma.txt`). These are wishlist items for
> the **Enma language team** (upstream, https://enma-1.gitbook.io/enma), not toolkit
> content. They are kept here as reference for toolkit contributors who hit the same
> gaps while writing PCX scripts. If you have access to the upstream, file these as
> GitBook discussions or issues against Enma itself.

The following recommendations are compiled based on the development of the
Perception.cx (PCX) AI scripting toolkit, focusing on reverse engineering
ergonomics, template parity, and tooling enhancement.

## 1. Nesting & Nested Template Fields (Unordered Maps/Sets)

* Issue: Enma currently lacks std::unordered_map and std::unordered_set because
  composing one template's instance as a field within another template is
  not yet supported.
* PCX Impact: Scripts must frequently track entities, cache bones, and map
  game states. The lack of scalar-keyed hash maps restricts developers to
  string-keyed maps or int-keyed imaps (e.g., map<int64, V> is a compile error).
* Recommendation: Resolve the nesting limitation for template fields to enable
  native std::unordered_map<K, V> and std::unordered_set<T> supporting
  arbitrary scalar and struct keys.

## 2. Byte-Wise Pointer Arithmetic (byte* / void*)

* Issue: Pointer arithmetic in Enma is strictly typed (p + n scales by the
  sizeof(T)). Assigning raw integers to pointers is rejected at compile time
  to enforce safety, requiring verbose reinterpret_cast chains to traverse
  game structures.
* PCX Impact: When walking structures (like pBase + offset), reverse engineers
  operate directly in raw byte offsets. Scaling by type size is counter-intuitive
  when dealing with dynamic struct padding or arbitrary memory regions.
* Recommendation: Introduce a native byte* (or void* with byte-wise arithmetic) type
  that permits direct offset additions without scaling, or expose a compiler
  intrinsic for direct offset dereferencing (e.g., read_mem<T>(base, offset)).

## 3. Overloaded Function Templates

* Issue: Overloaded function templates (selected by call arity) are not supported.
  This prevents compiling recursive variadic templates with a 1-argument
  template base.
* PCX Impact: Developers writing generic serialization routines, net packet
  decoders, or multi-level pointer resolvers must duplicate code rather than
  relying on recursive templates.
* Recommendation: Implement template argument matching for overloaded function
  templates to bring closer parity with C++ template metaprogramming.

## 4. Character Packing & std::string Support

* Issue: The implementation of std::string in the standard library is currently
  blocked waiting for Phase 6 character sub-8-byte packing.
* PCX Impact: Game hooks and memory reads frequently read or write narrow
  character arrays (char[N]). The absence of a packed std::string makes
  mapping native C++ struct definitions into Enma scripts error-prone.
* Recommendation: Finalize char-packing to support std::string and allow
  script-level structs to mirror native C++ character arrays layout-wise.

## 5. LSP Type Inference for Template Instantiation

* Issue: Type diagnostics are resolved during the compiler's monomorphization
  phase, which means template errors are only reported at compilation time.
* PCX Impact: Developers using enma-lsp do not receive real-time feedback on
  missing methods on generic types, constraint violations, or syntax errors
  within template definitions.
* Recommendation: Enhance enma-lsp to parse template instantiations on-the-fly
  and provide inline diagnostics/autocomplete within specialized template scopes.

---

## Source: `docs/enma/addon-arrays.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/arrays.md).

# Arrays

Registered with `register_addon_array(engine)`.

## Methods

Called on array values:

```cpp
a.push(42)           // append element
a.pop()              // remove and return last element
a.insert(0, 99)      // insert at index
a.remove(0)          // remove at index
a.get(0)             // read element
a.set(0, 10)         // write element
a.length()           // element count
a.capacity()         // allocated capacity
a.stride()           // bytes per element (sign encodes signedness)
a.resize(100)        // resize to N elements
a.contains(42)       // true if value exists
a.index_of(42)       // index of first match, -1 if not found
a.sort()             // sort ascending
a.reverse()          // reverse in place
a.join(", ")         // join elements into string
a.clear()            // remove all elements
a.free()             // release memory
a.slice(1, 4)        // sub-array from start to end index
```

### Front / back / swap / fill

```cpp
a.first()            // a[0]
a.last()             // a[length - 1]
a.pop_front()        // remove and return a[0]
a.push_front(x)      // prepend
a.swap(i, j)         // swap two indices in place
a.fill(x)            // overwrite every element with x
```

### Aggregates

```cpp
a.count(x)           // how many elements equal x
a.unique()           // new array with duplicates removed (preserves first occurrence)
a.sum()              // sum of all elements
a.min()              // smallest element
a.max()              // largest element
a.min_idx()          // index of the smallest element
a.max_idx()          // index of the largest element
a.chunk(n)           // split into array of arrays of size n
a.flat()             // one-level flatten (array of arrays → flat array)
```

### Higher-order (callbacks)

Pass a function as `int64`. The script-side callback shapes are below.

```cpp
int64 doubler(int64 x) { return x * 2; }
int64 is_even(int64 x) { return (x % 2) == 0 ? 1 : 0; }
int64 add(int64 acc, int64 x) { return acc + x; }

array m = a.map(doubler)               // map: T(T)
array f = a.filter(is_even)            // filter: bool/int(T)
int64 t = a.reduce(add, 0)             // reduce: T(T acc, T x)
bool  any = a.any(is_even)             // any-match
bool  all = a.all(is_even)             // all-match
int64 i   = a.find(is_even)            // index of first match, -1 if none
```

Array has type-specific print helpers as methods (these interpret the raw int64 slots as the named type): `a.print_int()`, `a.println_int()`, `a.print_float()`, `a.println_float()`, `a.print_str()`, `a.println_str()`.

## Packed storage (stride)

Typed arrays store their elements packed at natural width:

| Element type                                      | Bytes/element |
| ------------------------------------------------- | ------------- |
| `int8` / `uint8` / `char` / `bool`                | 1             |
| `int16` / `uint16` / `wchar`                      | 2             |
| `int32` / `uint32` / `float32`                    | 4             |
| `int64` / `uint64` / `float64` / pointer / handle | 8             |

So `uint8[] a = new uint8[1_000_000]` uses \~1 MB, not \~8 MB. The array header tracks stride; signed vs unsigned is encoded via stride sign (e.g. `int32[]` stride = -4, `uint32[]` stride = +4) so reads sign- or zero-extend correctly into the ABI int64 slot.

Out-of-bounds subscripts (`arr[i]`, `arr.get(i)`) throw a catchable runtime exception. See the SIMD doc for packed-stride SIMD ops that operate on these element-width vectors directly.

For raw stride control there's also a global:

```cpp
array buf = array_create_strided(capacity, stride)   // stride in bytes (sign = signedness)
```

## Heap-managed elements

The array destructor walks elements before freeing the buffer, so `string[]` and arrays of any heap-typed handle (`list<T>`, `map<K,V>`, user classes, etc.) drop their inner allocations at scope exit. No manual cleanup needed for owned data; only `T*[]` arrays-of-pointers require explicit `delete` of each element (the array owns slots, not the pointed-to objects).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/arrays.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-atomic.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/atomic.md).

# Atomic

Script-exposed atomic integers and memory barriers backed by `std::atomic<>`. Use these when multiple threads touch the same value. Plain `aint32` / `aint64` keywords exist as Enma types but the codegen doesn't currently emit LOCK-prefixed ops for assignments on them, so reach for the atomic types instead.

## Types

* `atomic_int32(init) -> atomic_int32`
* `atomic_int64(init) -> atomic_int64`

Both heap-allocated, scope-dropped. Factory takes the initial value.

## Methods (identical on both widths)

```cpp
int64 load();
void  store(int64 v);
int64 exchange(int64 v);              // returns old value
bool  compare_exchange(int64 exp, int64 des);  // swaps if current == exp; returns true on success

int64 add(int64 v);                    // returns old
int64 sub(int64 v);
int64 bit_and(int64 v);
int64 bit_or(int64 v);
int64 bit_xor(int64 v);

int64 inc();                           // returns NEW value
int64 dec();                           // returns NEW value
```

All ops use `std::memory_order_seq_cst`. Relaxed / acquire / release variants aren't exposed yet.

## Barriers (free functions)

```cpp
memory_barrier();   // seq_cst
read_barrier();     // acquire
write_barrier();    // release
```

Equivalent to `std::atomic_thread_fence` at the matching order.

## Example: counter

```cpp
atomic_int64 counter = atomic_int64(0);

void worker() {
    int32 i = 0;
    while (i < 100000) {
        counter.add(1);
        i = i + 1;
    }
}

// Spawn N threads, each calling worker()...
int64 final = counter.load();
```

## Example: CAS loop

```cpp
atomic_int64 x = atomic_int64(0);

int32 try_double() {
    int32 retries = 0;
    while (true) {
        int64 cur = x.load();
        if (x.compare_exchange(cur, cur * 2)) return retries;
        retries = retries + 1;
    }
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/atomic.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-bits.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/bits.md).

# Bits

Registered with `register_addon_bits(engine)`.

All operations treat the input as an unsigned bit pattern. 64-bit variants operate on the full `int64`. `_i32` variants mask to the low 32 bits first (useful when you want strict 32-bit semantics: rotates wrap at 32, clz/ctz return 32 for zero, etc.).

## Population count

```cpp
int64 n1 = popcount(0xFF)        // 8
int64 n2 = popcount(-1)          // 64 (all bits set)
int64 n3 = popcount_i32(-1)      // 32 (masked to low 32)
```

## Leading / trailing zeros

`clz` returns the number of leading (high) zero bits. `ctz` returns the number of trailing (low) zero bits. Both return the bit width of the type (64 or 32) when the input is zero (not undefined like C's intrinsics).

```cpp
int64 a = clz(1)                  // 63
int64 b = clz(0)                  // 64
int64 c = ctz(256)                // 8   (bit 8 is the first set bit)
int64 d = ctz_i32(cast<int64>(0x00001000)) // 12
```

## Rotates

Rotate by `n & (width - 1)`; wraps cleanly at the boundary.

```cpp
int64 a = rotl(0x12345678, 4)
int64 b = rotr(a, 4)              // b == 0x12345678
int64 c = rotl_i32(0x12345678, 8) // 0x34567812
```

## Byte swap

```cpp
int64 a = bswap(0x0102030405060708)  // 0x0807060504030201
int64 b = bswap_i32(0x12345678)      // 0x78563412
```

## Parity

Returns 1 if the number of set bits is odd, else 0.

```cpp
int64 p1 = parity(7)     // 1 (three ones)
int64 p2 = parity(3)     // 0 (two ones)
```

## Bit reverse

Reverses the full bit pattern. `bit_reverse(1)` puts a single bit at position 63 (MSB); the `_i32` variant reverses within the low 32 bits.

```cpp
int64 r = bit_reverse(1)            // 0x8000000000000000
int64 s = bit_reverse_i32(1)        // 0x80000000
```

## Single-bit ops

```cpp
int64 a = set_bit(0, 3)             // 8       (set bit 3)
int64 b = clear_bit(15, 1)          // 13      (clear bit 1)
int64 c = toggle_bit(5, 1)          // 7       (flip bit 1)
int64 t = test_bit(4, 2)            // 1       (bit 2 is set in 4)
```

## Bit-range extract / insert

`extract_bits(v, lo, hi)` pulls bits in **inclusive** `[lo, hi]`. `insert_bits(v, val, lo, hi)` returns `v` with the same range overwritten by `val`.

```cpp
int64 a = extract_bits(0xDEAD, 0, 7)          // 0xAD  (bits 0..7)
int64 b = extract_bits(0xDEAD, 8, 15)         // 0xDE  (bits 8..15)
int64 c = insert_bits(0xFF00, 0xAB, 0, 7)     // 0xFFAB
```

## Power-of-two helpers

```cpp
bool  p = is_pow2(16)               // true
int64 n = next_pow2(5)              // 8       (smallest pow2 >= v; 1 if v <= 1)
int64 q = prev_pow2(17)             // 16      (largest pow2 <= v; 0 if v == 0)
```

## Alignment

Round to a multiple of `n` (typically a power of two).

```cpp
int64 a = align_up(13, 8)           // 16
int64 b = align_down(13, 8)         // 8
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/bits.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-core.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/core.md).

# Core

Registered with `register_addon_core(engine)`.

> Runtime functions (heap, budget, events, coroutines, counters, assert, time\_ms) are auto-registered by the engine, no addon needed.

## Output

```c
print("hello")            // no newline
println("hello")           // with newline
println("x = " + x)        // concat
print(42)                  // int → string via .convert()
print(3.14)                // float → string
print(true)                // "true"/"false"
print('A')                 // char → single-char string
println(format("x={d} y={f}", x, y))   // format helper
```

Non-string args auto-convert via the `string` type's `.convert(...)` table.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/core.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-file.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/file.md).

# File

Registered with `register_addon_file(engine)`.

All file-touching operations require the `PERM_FILE` permission flag to be granted on the engine. Scripts without the permission will fail to compile any call that touches the filesystem:

```cpp
set_permissions(engine, enma::PERM_FILE);
```

## Stream API

`file_t` wraps an OS file handle. Open with `file_open(path, mode)`; the destructor closes the file at scope exit.

```cpp
file_t f = file_open("data.txt", "r");
if (f.is_open()) {
    while (!f.is_eof()) {
        string line = f.read_line();
        // ... process line ...
    }
}

file_t w = file_open("out.txt", "w");
w.write("hello");
w.flush();

file_t bin = file_open("img.dat", "rb");
int64 sz = bin.size();
bin.seek(1024);
int64 pos = bin.tell();
```

### Modes

Standard C fopen modes. `"r"`, `"w"`, `"a"`, `"rb"`, `"wb"`, `"ab"`, `"r+"`, `"w+"`.

### Methods

```cpp
bool   o = f.is_open()           // false if open failed
bool   e = f.is_eof()
string s = f.read_all()          // read from current pos to end
string l = f.read_line()         // line without trailing \n/\r\n
int64  n = f.write(string)       // bytes written
int64  sz = f.size()
int64  p  = f.tell()
f.seek(pos)
f.flush()
f.close()                         // dtor also closes
```

## Whole-file convenience

Path-based shortcuts for one-shot reads/writes. Strings:

```cpp
string content = file_read("config.json")
bool   ok      = file_write("log.txt", "line1\nline2\n")
```

Bytes (uint8 stride-1 array):

```cpp
array bytes = file_read_bytes("img.png")
bool  ok    = file_write_bytes("out.bin", bytes)
```

## Filesystem operations

File-level:

```cpp
bool  exists = file_exists(path)
bool  ok     = file_remove(path)
bool  ok     = file_rename(from, to)
bool  ok     = file_copy(src, dst)         // overwrites dst
int64 sz     = file_size(path)             // -1 on error
int64 mt     = file_mtime(path)            // Unix seconds, -1 on error
```

Directory-level:

```cpp
bool  d     = dir_exists(path)
bool  ok    = dir_create(path)             // succeeds if already exists
array names = dir_list(path)               // filenames (not full paths)
array all   = dir_walk(path)               // recursive; full paths
```

## Permissions

The permission gate is enforced at compile time: calling any gated native without `PERM_FILE` granted fails the module compile with a permission error. This lets hosts sandbox untrusted scripts by default.

```cpp
// Host code:
auto* e = enma::create();
enma::register_all_addons(e);
// no set_permissions call -> file ops unavailable to all scripts

// vs. privileged script path:
enma::set_permissions(e, enma::PERM_FILE);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/file.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-hash_set.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/hash_set.md).

# Hash Set

Registered with `register_addon_hash_set(engine)`.

Generic hashed set. `T` is bound at declaration time.

```cpp
hash_set<int64> s;
s.add(1);
s.add(2);
s.add(1);           // dedup
s.size()            // 2
s.contains(1)       // true
s.remove(1)         // true
```

## Methods

```cpp
void      s.add(T v)
bool      s.contains(T v)
bool      s.remove(T v)               // true if v was present
int64     s.size()
void      s.clear()
array     s.to_array()                // copy contents into a new array (order not guaranteed)
hash_set  s.copy()                    // independent deep copy
```

## Set operations (mutate `s` in place)

```cpp
s.union_with(other)         // add every element of `other` to s
s.intersect_with(other)     // keep only elements present in both
s.diff_with(other)          // remove every element of `other` from s
bool sub = s.is_subset_of(other)
bool eq  = s.equals(other)
```

## Supported element types

`T` must fit in 64 bits and compare by **raw bits**. This works correctly for:

* `int8`/`int16`/`int32`/`int64`/`uint*` - integer values
* `bool` - 0 or 1
* `float32`/`float64` - compared as IEEE bit patterns (so `NaN != NaN`, be aware)
* Pointer types - compared as pointers

**Strings work** as hashed-equal because hash\_set internally hashes the string content (not the pointer). So `hash_set<string>` deduplicates by string value. Heap cleanup walks elements at scope-end so strings in the set get freed cleanly.

```c
hash_set<string> tags;
tags.add("alpha");
tags.add("beta");
tags.add("alpha");   // dedup; size still 2
println(cast<string>(tags.size()));   // 2
```

**Class types** as element T are not supported (class equality would require user-defined `==`); use `int64` IDs and a side lookup. Pointer V (`hash_set<T*>`) compares by raw pointer value.

## Type check

The compiler enforces `T` at every method call:

```cpp
hash_set<int64> s;
s.add("oops");      // compile error: expected int64, got string
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/hash_set.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-json.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/json.md).

# JSON

Registered with `register_addon_json(engine)`.

Hand-rolled JSON parser + stringifier. Supports the RFC 7159 core: null, bool, number, string, array, object, with all standard escapes and `\uXXXX` (BMP code points to UTF-8).

## Parsing

```cpp
json_value j = json_parse("{\"name\":\"Alice\",\"age\":30}");
bool ok = j.is_valid();        // false if the input was malformed
```

Invalid JSON returns a `json_value` where `is_valid()` is `false`; all other methods are safe on an invalid value (they return empty / 0 / false).

## Type predicates

```cpp
j.is_null()  j.is_bool()  j.is_num()  j.is_str()  j.is_array()  j.is_obj()
int64 k = j.kind()
// kind(): 0=null 1=bool 2=num 3=str 4=arr 5=obj 6=invalid
```

## Primitive extraction

```cpp
bool    b = j.as_bool()     // false if not a bool
float64 n = j.as_num()      // 0.0 if not a number
int64   i = j.as_int()      // truncated from the stored double
string  s = j.as_str()      // "" if not a string
```

## Container introspection

```cpp
int64 n = j.size()              // array/object length; 0 for primitives
bool  h = j.has_key(string)     // true for objects that have the key
array ks = j.keys()             // array<string> of object keys (insertion order)
```

## Navigation

`get_key` and `get_at` return a new `json_value` holding a **deep copy** of the subtree. No shared ownership, no view-vs-owner ambiguity - every sub-value can outlive its parent.

```cpp
json_value j = json_parse("{\"users\":[{\"id\":1},{\"id\":2}]}");
json_value users = j.get_key("users");
int64 n = users.size();              // 2
json_value first = users.get_at(0);
int64 id = first.get_key("id").as_int();   // 1
```

## Building / mutating

Empty-builder factories let you construct JSON from scratch. Mutators take any `json_value` and deep-copy it in:

```cpp
json_value obj = json_object();
json_value arr = json_array();

obj.set_key("name", json_parse("\"Alice\""));
obj.set_key("age",  json_parse("30"));
obj.remove_key("age");

arr.push_value(json_parse("1"));
arr.push_value(json_parse("\"two\""));
```

`set_key` returns true if the key was inserted/updated, `remove_key` returns true if a key was removed, `push_value` returns true on success. All deep-copy the value, so the source can be dropped independently.

## Stringifying

```cpp
string compact = j.stringify()   // {"a":1,"b":2}
string indent  = j.pretty()      // multi-line with 2-space indent
```

* Numbers round-trip as integers when they fit exactly in `[-1e15, 1e15]`, else as `%.17g` floats.
* Strings re-escape control characters, quotes, backslashes, and non-ASCII < 0x20.
* Object keys emit in **insertion order** (the parse also preserves order).

## Limitations

* No streaming API, the whole document is parsed up front.
* `\uXXXX` escapes support BMP only (no surrogate pair reconstruction).
* No schema validation.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/json.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-list.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/list.md).

# List

Registered with `register_addon_list(engine)`.

`list<T>` is a generic double-ended container. **O(1) push/pop\_back, O(1) random access, O(n) push\_front/pop\_front.** Use it for queues / deques / entity lists; for a strict LIFO stack or growable buffer, `array<T>` is cheaper (single contiguous block).

```cpp
list<Entity> ents;
ents.push_back(new Entity(1));
ents.push_back(new Entity(2));
ents.push_front(new Entity(0));
println(cast<string>(ents.size()));   // 3
```

## Construction

```cpp
list<int64> a;             // empty list
list<Point> ents;          // class T — class storage works (reference-aliased)
```

`list<T*>` is supported — V is a user-managed pointer, `get` / subscript return a typed `T*`. The list does not auto-free pointer elements; you `delete` them.

## Add / remove

```cpp
lst.push_back(x)         // append (alias: push)
lst.push_front(x)        // prepend
lst.pop_back()           // remove + return last (alias: pop)
lst.pop_front()          // remove + return first
lst.insert(idx, x)       // insert at idx (clamps oob → end)
lst.remove(idx)          // remove + return element at idx (returns 0 if oob)
```

`pop_*` on an empty list returns `0` (not a crash). `remove(idx)` does the same for out-of-bounds.

## Access

```cpp
lst.get(idx)             // bounds-checked; returns 0 if oob (alias: at)
lst.set(idx, x)          // bounds-checked; no-op if oob
lst[idx]                 // subscript (read + write)
lst.first()              // front element (0 if empty)
lst.last()               // back element (0 if empty)
```

## Search

```cpp
lst.contains(x)          // true if any element equals x (alias: has)
lst.index_of(x)          // index of first match, or -1
```

## Size

```cpp
lst.size()               // alias: length
lst.empty()              // == size() == 0
```

## Modify

```cpp
lst.clear()              // empty the list
lst.reverse()            // in-place reverse
```

## Conversion / combine / copy

```cpp
array<T> arr = lst.to_array();    // snapshot to array<T>, preserves order
list<T>  cp  = lst.copy();        // independent shallow copy
src.extend(other);                // append every element of `other` to `src`
```

`copy()` and `extend()` copy *handles* — for class T, both lists end up holding handles to the same heap instances. To deep-copy a class T element, use `*pt` deref or define a `clone()` method on your class.

## Iteration

`list<T>` supports the kv-iterable foreach form. Index is the "key", element is the value:

```cpp
list<int64> nums;
nums.push_back(10); nums.push_back(20); nums.push_back(30);

// Index + value
for (int64 i, int64 v : nums) {
    println(cast<string>(i) + " -> " + cast<string>(v));
}

// Value only — discard the index
for (int64 i, int64 v : nums) {
    println(cast<string>(v));
}
```

## Class storage

`list<T>` for class T stores reference handles. Insert via `new T(...)` inline; the list takes ownership (heap-tracked). Retrieved values are *aliased* — mutations flow back into the list:

```cpp
class Entity { int64 id; int64 hp; Entity(int64 i, int64 h) { id = i; hp = h; } }

list<Entity> ents;
ents.push_back(new Entity(1, 100));

Entity e = ents.first();    // alias — same heap object
e.hp = 50;                   // mutates the stored Entity

Entity e2 = ents.first();
println(cast<string>(e2.hp)); // 50
```

For an independent copy, use `*p` (deref) on a `T*` pointer if you have one — or define a `clone()` method on the class.

## Class field with list — auto-cleanup

A class with a `list<T>` field cleans up automatically on `delete`. The runtime walks the list field, frees each heap-tracked element, then runs the list's own dtor. Works one level deep — for nested class containers the inner level may need explicit cleanup (see Known limitations).

```cpp
class Squad {
    list<Entity> members;
    string name;
    Squad(string n) { name = n; }
}

Squad* sq = new Squad("alpha");
sq->members.push_back(new Entity(1, 100));
sq->members.push_back(new Entity(2, 100));
delete sq;   // members + each Entity inside freed
```

## Class storage in maps + cross-container sharing

The same heap class instance can live in multiple containers — `list`, `imap`, `map<string, T>` — and mutation in any one is visible in all. When the containers drop, `heap_is_tracked` guards prevent double-free.

```cpp
class Player { int64 id; int64 hp; Player(int64 i, int64 h) { id = i; hp = h; } }

list<Player>             active;
imap<Player>             by_id;
map<string, Player>      by_name;

Player* p = new Player(1, 100);
active.push_back(p);
by_id.set(1, p);
by_name.set("alpha", p);

// Mutate via one — visible everywhere
Player a = by_id.get(1);
a.hp = 50;
println(cast<string>(by_name.get("alpha").hp));   // 50
println(cast<string>(active.first().hp));         // 50
```

## list vs array vs map — which to pick

| Need                            | Use                                                              |
| ------------------------------- | ---------------------------------------------------------------- |
| LIFO stack, growable buffer     | `array<T>` (cheaper — single contiguous block, no front-end ops) |
| FIFO queue, deque, both ends    | `list<T>`                                                        |
| String → V lookup               | `map<string, V>`                                                 |
| int → V lookup                  | `imap<V>`                                                        |
| Ordered key map (range queries) | `sorted_map<K, V>`                                               |
| Unique-element set              | `hash_set<T>`                                                    |

## Notes

* `pop_*()` on empty returns 0; if you store 0 as a real value, use `empty()` to disambiguate.
* `push_front` / `pop_front` are O(n) on the current storage — fine for occasional use, avoid in tight hot loops.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/list.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-maps.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/maps.md).

# Maps (string + imap int-keyed)

Registered with `register_addon_map(engine)`.

## Creation

```c
map<string, int64> m;                     // typed declaration; default-constructs
map<string, int64> typed;                 // K/V tracked for native sig checks
```

## Methods

```c
m.get("key")                    // read value
m.get_or_default("key", 0)      // read value or fallback
m.set("key", 42)                // write value
m.contains("key")               // true if key exists
m.has_value(42)                 // true if any entry's value == 42
m.size()                        // number of entries
m.remove("key")                 // delete entry
m.clear()                       // remove all entries
m.free()                        // release memory
m.keys()                        // → string[]
m.values()                      // → element[]
m.merge(other)                  // copy all entries from other into m
```

Subscript access:

```c
m["key"] = 42
int64 v = m["key"]
```

Iteration:

```c
for (string k, int64 v : m) { ... }
```

## imap — int64-keyed hash map

Companion to `map<K, V>` for int64 keys. Same hash-based O(1) ops, but the key is an int64 directly. Headline use case: pair with constexpr FNV-1a to avoid string compares in hot loops.

```c
imap<int64> tbl;                         // typed declaration; default-constructs
```

Methods mirror `map`:

```c
tbl.set(42, 100)
tbl.get(42)
tbl.get_or_default(42, 0)
tbl.has(42)        // alias of contains
tbl.contains(42)
tbl.remove(42)
tbl.length()       // alias of size
tbl.size()
tbl.clear()
tbl.keys()         // → int64[]
tbl.values()       // → element[]
```

Subscript + iteration also supported:

```c
tbl[42] = 100
int64 v = tbl[42]
for (int64 k, int64 v : tbl) { ... }
```

Compile-time hashed lookup:

```c
constexpr int64 fnv1a(string s) {
    int64 h = -3750763034362895579;
    int32 i = 0;
    while (i < cast<int32>(s.length())) {
        h = h ^ s.char_at(i);
        h = h * 1099511628211;
        i = i + 1;
    }
    return h;
}
constexpr int64 H_PLAYER = fnv1a("player");
constexpr int64 H_ENEMY  = fnv1a("enemy");

imap<int64> handlers
handlers.set(H_PLAYER, 100)
handlers.set(H_ENEMY,  50)

// Hot loop — no string allocation, no strcmp; H_PLAYER is folded to an
// int64 immediate at compile time.
for (int64 k : keys) {
    if (handlers.has(k)) total = total + handlers.get(k)
}
```

`imap` fields auto-initialize in classes with a user ctor — same as a no-ctor class.

```c
class W {
    imap<int64> m;       // auto-init runs before W()'s body
    W() {}
}
```

Same for `map<K,V>`, `sorted_map<K,V>`, and other addon-registered container types: typed declarations on classes with or without user ctors default-construct.

## Class / struct as V

`map<K, T>` and `imap<T>` accept user-defined class or struct types as V. Class instances are heap-allocated reference handles — mutating an instance fetched via `get` flows back into the map (alias semantics, like C++ references). To clone, use `*pt` (deref).

```c
class Player {
    int64 id; string name; int64 hp;
    Player() {}
    Player(int64 i, string n, int64 h) { id = i; name = n; hp = h; }
}

// String-keyed lookup by name
map<string, Player> by_name;
by_name.set("alice", new Player(1, "alice", 100));
by_name.set("bob",   new Player(2, "bob",    85));

// Reference semantics — mutation flows back into the map
Player p = by_name.get("alice");
p.hp = 50;
println(cast<string>(by_name.get("alice").hp));   // 50

// Int-keyed lookup by id
imap<Player> by_id;
by_id.set(1, new Player(1, "alice", 100));
by_id.set(2, new Player(2, "bob",    85));

// Iterate
for (string k, Player v : by_name) {
    println(k + " -> " + cast<string>(v.hp));
}
```

`map<K, T*>` / `imap<T*>` supports pointer-typed V — `get` / subscript return a typed `T*`. The container does NOT auto-free pointer elements at scope-drop; you own the `delete` calls for each entry.

## Pattern: ECS-style entity registry

Several maps over the same heap instances — common in entity / scripting contexts. Each `Player*` is shared between `active`, `by_id`, and `by_name`.

```c
class Player {
    int64 id; string name; int64 hp;
    Player(int64 i, string n, int64 h) { id = i; name = n; hp = h; }
}

list<Player>             active;
imap<Player>             by_id;
map<string, Player>      by_name;

void spawn(int64 id, string name, int64 hp) {
    Player* p = new Player(id, name, hp);
    active.push_back(p);
    by_id.set(id, p);
    by_name.set(name, p);
}
```

When `active` (or any container holding the Player) drops, the heap class instances inside are automatically freed. Aliased entries in the other containers don't double-free — the runtime guards against it via `heap_is_tracked`.

## Heap cleanup on container drop

When a `map<string, V>` / `imap<V>` / `list<V>` etc. with class or string V goes out of scope, the IR-level scope-drop walks the elements and frees each one. This applies to:

* Local containers at function scope-end
* Container fields when the owning class is `delete`'d
* Containers held in `try` blocks unwound by `throw`

Global containers don't free at `main` return (so routines / callbacks that fire after `main` keep working). The engine's heap teardown reclaims any leftover memory when the engine is destroyed.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/maps.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-math.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/math.md).

# Math

Registered with `register_addon_math(engine)`. This addon also defines the [vec2/vec3/vec4](addon-vec.md) and [quat / mat4](addon-math3d.md) types — all math types live under the same addon registration.

## Trigonometry

```cpp
sin(x)    cos(x)    tan(x)
asin(x)   acos(x)   atan(x)   atan2(y, x)
```

## Hyperbolic

```cpp
sinh(x)    cosh(x)    tanh(x)
asinh(x)   acosh(x)   atanh(x)
```

## Power & Logarithm

```cpp
sqrt(x)    cbrt(x)    pow(x, y)    hypot(a, b)
log(x)     log2(x)    log10(x)    log_base(x, base)    exp(x)
```

## Rounding

```cpp
floor(x)   ceil(x)    round(x)
round_up(x)            // == ceil(x)
round_down(x)          // == floor(x)
```

## Float utilities

```cpp
fabs(x)                  // absolute value
fmod(x, y)               // float modulo
fmin(a, b)               // minimum
fmax(a, b)               // maximum
fclamp(x, lo, hi)        // clamp to range
```

## Integer utilities

```cpp
iabs(x)                  // absolute value
imin(a, b)               // minimum
imax(a, b)               // maximum
iclamp(x, lo, hi)        // clamp to range
```

## Overloaded `abs` / `min` / `max` / `clamp`

These names dispatch on argument type — works for both `int64` and `float64`.

```cpp
abs(x)         min(a, b)     max(a, b)     clamp(x, lo, hi)
```

## Constants

```cpp
float64 p = pi();        // 3.14159265358979...
float64 e = euler();     // 2.71828182845904...
```

## Random

```cpp
seed(42);                       // seed the RNG
float64 f = rand();             // random float [0, 1)
int64 n = rand_int(0, 100);     // random integer in [lo, hi)
bool b = random_bool();         // 50/50 coin flip
float64 g = random_gaussian(mu, sigma);   // normal distribution
```

## Interpolation

```cpp
lerp(a, b, t);                  // a + (b-a)*t
inverse_lerp(a, b, v);          // (v-a)/(b-a); 0 if a==b
```

## Classification

```cpp
bool n = is_nan(v);
bool i = is_inf(v);
bool f = is_finite(v);
```

## Sign / fractional / wrap

```cpp
sign(v)        // -1.0 / 0.0 / +1.0
fract(v)       // v - floor(v) (positive for negatives)
wrap(v, lo, hi)// wrap v into [lo, hi)
```

## Float bit ops

```cpp
copysign(mag, sgn);             // |mag| with sign of sgn
nextafter(from, toward);         // next representable float toward `toward`
```

## Bit-cast helpers

```cpp
uint32 bits = f32_to_u32(x);     // float32 -> its IEEE-754 bits
float32 f   = u32_to_f32(bits);  // bits -> float32
uint64 b    = f64_to_u64(x);     // float64 -> bits
float64 d   = u64_to_f64(b);     // bits -> float64
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/math.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-math3d.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/math3d.md).

# 3D Math (quat + mat4)

`quat` and `mat4` are value-type structs in the `math` addon (same registration as [Vectors](addon-vec.md) and [Math](addon-math.md)). Register with `register_addon_math(engine)` on the host side and `import "math";` in your script if needed.

* `quat` — unit quaternion, 32 bytes, four `float64` fields (`x`, `y`, `z`, `w`). `w` is the scalar.
* `mat4` — 4×4 row-major matrix, 128 bytes, 16 `float64` fields named `m00` … `m33`.

Both default-construct to all zeros. Use `quat_identity()` / `mat4_identity()` for the canonical "do nothing" values.

## Quaternion (`quat`)

### Construction

```cpp
quat q;                                    // typed default: (0, 0, 0, 0)
quat q4 = quat(1.0, 0.0, 0.0, 0.0);        // explicit components

quat id = quat_identity();                  // (0, 0, 0, 1) — no rotation
quat e  = quat_from_euler(yaw, pitch, roll); // Tait-Bryan ZYX, radians
quat a  = quat_from_axis_angle(vec3(0.0, 0.0, 1.0), deg_to_rad(90.0));
```

### Accessors

`x` / `y` / `z` / `w` are plain struct fields — read and write directly, no parenthesised getter form.

```cpp
// Read
float64 x = q.x;
float64 w = q.w;

// Write
q.x = 0.0;
q.w = 1.0;
```

Direct component writes do **not** re-normalize. Call `q.normalize()` afterwards if you need a unit quaternion.

### Operations

```cpp
quat n = q.normalize();
quat c = q.conjugate();         // xyz negated, w preserved
quat i = q.inverse();           // == conjugate when q is unit-length

quat r = a.mul(b);              // Hamilton product; same as a * b
quat s = a.add(b);              // component-wise; same as a + b
quat g = q.negate();            // alias: q.neg(); same as -q

float64 d   = a.dot(b);         // 4-component dot product
float64 L   = q.length();
float64 Lsq = q.length_sq();

vec3 rotated = q.rotate(vec3(0.0, 0.0, 1.0));  // assumes unit quat
vec3 euler   = q.to_euler();                    // (yaw, pitch, roll) in vec3 x/y/z

quat midway  = a.slerp(b, t);                   // shorter great-circle arc
```

### Operators

```cpp
quat r = a * b;            // Hamilton product (non-commutative)
quat s = a + b;            // component-wise add
quat n = -q;               // unary negate
bool eq = (a == b);        // exact-component equality
a += b;
a -= b;
```

## 4×4 Matrix (`mat4`)

Row-major. Default constructor produces a zero matrix — use `mat4_identity()` for the identity.

### Construction

```cpp
mat4 zero;                                  // typed default: all 0
mat4 i = mat4_identity();
mat4 t = mat4_translation(vec3(x, y, z));
mat4 s = mat4_scale(vec3(sx, sy, sz));
mat4 rx = mat4_rotation_x(rad);
mat4 ry = mat4_rotation_y(rad);
mat4 rz = mat4_rotation_z(rad);
mat4 ra = mat4_rotation_axis(vec3 axis, rad);  // Rodrigues; axis normalized internally
mat4 fq = mat4_from_quat(q);
mat4 p  = mat4_perspective(fov_rad, aspect, near_z, far_z);     // RH, GL-style depth
mat4 o  = mat4_orthographic(left, right, bottom, top, near_z, far_z);
mat4 v  = mat4_look_at(vec3 eye, vec3 target, vec3 up);          // RH view matrix
```

### Element access

You can read/write individual cells through the named fields (`m00`, `m01`, ..., `m33`) or use the `get`/`set` methods which take row/col.

```cpp
m.m00 = 1.0;
float64 c = m.m12;

float64 v = m.get(row, col);            // row, col in 0..3
m.set(row, col, value);
```

`mat4_get(m, row, col)` and `mat4_set(m, row, col, v)` are free-function aliases for the methods.

### Operations

```cpp
mat4 t = m.transpose();
mat4 i = m.inverse();              // returns identity if singular
float64 d = m.determinant();
mat4 c = a.mul(b);                  // row-major a*b; same as a * b
mat4 g = m.scale(2.0);              // scalar multiply
mat4 n = m.neg();                   // unary negate

vec3 p = m.transform_point(v);      // applies translation; perspective-divides if w != 1
vec3 d = m.transform_vec3(v);       // ignores translation (use for directions)
vec4 q = m.transform_vec4(v);       // full 4-component transform
```

### Operators

```cpp
mat4 c = a * b;
mat4 s = a + b;
mat4 d = a - b;
mat4 n = -m;
bool eq = (a == b);
a += b;
a -= b;
a *= b;
```

## Common patterns

```cpp
// Build a TRS world matrix.
mat4 world = mat4_translation(pos) * mat4_from_quat(rot) * mat4_scale(scl);
vec3 world_pos = world.transform_point(local_pos);

// Compose a view-projection matrix.
mat4 view = mat4_look_at(camera_pos, target, vec3(0.0, 1.0, 0.0));
mat4 proj = mat4_perspective(deg_to_rad(60.0), 16.0/9.0, 0.1, 1000.0);
mat4 vp = proj * view;
vec3 ndc = vp.transform_point(world_pos);    // perspective-divides via w

// Slerp between two orientations.
quat a = quat_identity();
quat b = quat_from_axis_angle(vec3(0.0, 1.0, 0.0), deg_to_rad(90.0));
quat current = a.slerp(b, t);    // t in [0, 1]
vec3 facing = current.rotate(vec3(0.0, 0.0, 1.0));
```

## Notes

* All angles are radians. Use `deg_to_rad` / `rad_to_deg` from [Vectors](addon-vec.md#scalar-helpers) to convert.
* `mat4_perspective` uses right-handed coordinates and OpenGL-style depth (`z` clipped to `[-1, 1]` after perspective divide). Direct3D conventions need the depth row tweaked.
* `mat4.inverse()` returns the identity when the matrix is singular (zero determinant). Check `m.determinant() != 0.0` if your code can produce non-invertible matrices.
* Quaternion multiplication is non-commutative: `a * b != b * a` in general. `a * b` means "rotate by `b` first, then by `a`".
* `quat_from_euler` and `q.to_euler()` both use Tait-Bryan ZYX (yaw, pitch, roll). Round-tripping isn't exact at gimbal-lock orientations (`pitch = ±π/2`).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/math3d.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-regex.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/regex.md).

# Regex

Registered with `register_addon_regex(engine)`.

ECMAScript regex syntax. The compiled `regex` type is an addon type with a destructor that runs at scope exit.

## Construction

```cpp
regex re("[0-9]+");                       // ctor-form var-decl
regex re2 = regex("\\w+");                // assignment form
regex empty("[");                          // bad pattern → null handle
```

If the pattern fails to compile, the returned handle is 0 (null). Methods on a null handle are safe — they return false / empty.

## Methods

```cpp
bool   f = re.matches("12345")             // entire string matches pattern
bool   h = re.has_match("abc 123")         // any substring matches
string m = re.first("abc 123 def")         // first match text, or ""
array  all = re.find_all("a12 b345 c6")    // array<string> of all matches
string r = re.replace("a12b34", "#")       // "a#b#" (all matches replaced)
array  parts = re.split("a,b,c,d")         // split on matches
array  g = re.groups("name=42")            // [full, group1, group2, ...]
```

**Note:** `match` is a reserved keyword in Enma (used for pattern-matching expressions), so the single-match accessor is named `first`.

## Capture groups

`groups` returns an array where `[0]` is the full match and `[1..n]` are the capture groups in order:

```cpp
regex re = regex("([a-z]+)=([0-9]+)");
array g = re.groups("age=30");
// g[0] == "age=30", g[1] == "age", g[2] == "30"
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/regex.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-simd.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/simd.md).

# SIMD

Registered with `register_addon_simd(engine)`. Uses SSE2 intrinsics; ops fall back to scalar for the trailing element when array length is odd.

Argument convention: `(a, b, dst)` — inputs first, output last. Output arrays must be pre-sized; the natives don't grow them.

## Elementwise float64

```c
simd_add_f64(a, b, dst)         // dst[i] = a[i] + b[i]
simd_sub_f64(a, b, dst)
simd_mul_f64(a, b, dst)
simd_div_f64(a, b, dst)
simd_min_f64(a, b, dst)
simd_max_f64(a, b, dst)
simd_abs_f64(src, dst)          // dst[i] = |src[i]|
simd_sqrt_f64(src, dst)
simd_fma_f64(a, b, c, dst)      // dst[i] = a[i] * b[i] + c[i]
simd_scale_f64(src, k, dst)     // dst[i] = src[i] * k
```

## Reductions

```c
float64 d = simd_dot_f64(a, b)         // a · b
float64 s = simd_sum_f64(a)
float64 m = simd_min_reduce_f64(a)
float64 m = simd_max_reduce_f64(a)
```

## Compare (1.0 / 0.0 per lane)

```c
simd_cmp_eq_f64(a, b, dst)
simd_cmp_lt_f64(a, b, dst)
```

## Elementwise int64

```c
simd_add_i64(a, b, dst)
simd_sub_i64(a, b, dst)
simd_mul_i64(a, b, dst)          // scalar fallback (no SSE2 packed 64-bit mul)
int64 s = simd_sum_i64(a)
```

## Memory

```c
simd_memset(arr, val)            // fill entire array with int64 val
simd_memcpy(src, dst)
```

## Packed SIMD on stride-1/2/4 arrays

`uint8[]`/`int8[]`/`int16[]`/`int32[]`/`float32[]` are packed buffers (1/2/4 bytes per element), so dedicated packed ops operate 16/8/4 lanes at a time. Each op validates the operand's `|stride|` and raises `runtime_error` on mismatch — passing an `int64[]` to `simd_add_i8` fails fast.

### int8 / uint8 (16 lanes)

```c
simd_add_i8(a, b, dst)           // wrap
simd_sub_i8(a, b, dst)
simd_cmp_eq_i8(a, b, dst)        // dst[i] = 0xFF if eq else 0x00
int64 mask = simd_movemask_i8(a) // bit i = sign bit of a[i], up to 64 bytes
simd_shuffle_i8(src, mask, dst)  // pshufb semantics per 16-byte block
```

### int16 / uint16 (8 lanes)

```c
simd_add_i16(a, b, dst)
simd_sub_i16(a, b, dst)
simd_mul_i16(a, b, dst)
```

### int32 / uint32 (4 lanes)

```c
simd_add_i32(a, b, dst)
simd_sub_i32(a, b, dst)
simd_mul_i32(a, b, dst)
```

### float32 (4 lanes; sse\_\*\_ps parity)

```c
simd_add_f32(a, b, dst)
simd_sub_f32(a, b, dst)
simd_mul_f32(a, b, dst)
simd_div_f32(a, b, dst)
simd_sqrt_f32(src, dst)
simd_min_f32(a, b, dst)
simd_max_f32(a, b, dst)
simd_abs_f32(src, dst)

float64 d = simd_dot_f32(a, b)   // returns float64 for precision
float64 s = simd_sum_f32(a)
```

### Bitwise on any stride-1 array

```c
simd_and(a, b, dst)
simd_or(a, b, dst)
simd_xor(a, b, dst)
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/simd.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-sorted_map.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/sorted_map.md).

# Sorted Map

Registered with `register_addon_sorted_map(engine)`.

Ordered map. Keys iterate in sorted order; `O(log n)` put/get/contains/remove.

```cpp
sorted_map<int64, int64> m;
m.set(3, 300);
m.set(1, 100);
m.set(2, 200);
int64 v = m.get(2)              // 200
array ks = m.keys()             // sorted: [1, 2, 3]
array vs = m.values()           // in key order: [100, 200, 300]
int64 first = m.first_key()     // 1
int64 last  = m.last_key()      // 3
```

## Methods

```cpp
void    m.set(K k, V v)          // insert or overwrite
V       m.get(K k)               // 0 if missing
bool    m.contains(K k)
bool    m.remove(K k)            // true if k was present
int64   m.size()
void    m.clear()
array   m.keys()                 // sorted
array   m.values()               // values in key order
K       m.first_key()            // smallest; 0 if empty
K       m.last_key()             // largest; 0 if empty
```

## Bound / range queries

```cpp
K  lo  = m.lower_bound(k)         // smallest key >= k; 0 if none
K  up  = m.upper_bound(k)         // smallest key > k; 0 if none
K  fl  = m.floor_key(k)           // largest key <= k; 0 if none
K  cl  = m.ceiling_key(k)         // alias of lower_bound
array rk = m.range_keys(lo, hi)   // keys in [lo, hi)
array rv = m.range_values(lo, hi) // values for those keys
```

The sentinel for "no key" is `0`. Call `contains()` first if `0` is a valid key in your map.

## Supported key/value types

Same scalar-only caveat as [hash\_set](addon-hash_set.md): `K` and `V` each must fit in 64 bits and order/equate by raw bits. Works for integer, bool, float-bits, pointer. Not suitable for string keys.

## Type-check

Both `K` and `V` are enforced at the call site:

```cpp
sorted_map<int64, int64> m;
m.set("str", 1);        // compile error: K is int64
m.set(1, "oops");       // compile error: V is int64
```

## When to pick which container

* `sorted_map<int64, int64>` — range queries / sorted iteration over scalars.
* `imap<T>` — int-keyed map with class V, unordered.
* `map<string, T>` — string-keyed map with class V.

Class V is not auto-cloned on `set()` here — if you need owned class storage in a sorted\_map, alloc with `new T()` so the heap instance lives independently of any source local.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/sorted_map.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-strings.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/strings.md).

# Strings

Registered with `register_addon_string(engine)`.

## Methods

```c
s.length()                      // character count
s.is_empty()                    // true if length == 0
s.substr(0, 3)                  // substring (index, length)
s.find("needle")                // index of first match, -1 if absent
s.last_index_of("needle")       // index of last match, -1 if absent
s.count("needle")               // number of non-overlapping matches
s.contains("text")              // true if substring exists
s.starts_with("pre")            // prefix check
s.ends_with("suf")              // suffix check
s.char_at(0)                    // character code at index
s.to_int()                      // parse integer
s.to_float()                    // parse float
s.to_upper()                    // uppercase copy
s.to_lower()                    // lowercase copy
s.trim()                        // strip leading/trailing whitespace
s.reverse()                     // reversed copy
s.replace("old", "new")         // replace all occurrences
s.replace_first("old", "new")   // replace first occurrence only
s.repeat(3)                     // concatenate N copies
s.pad_left(10, ' ')             // left-pad to width using char
s.pad_right(10, '.')            // right-pad to width using char
s.insert(3, "abc")              // insert at index
s.remove_range(2, 5)            // remove chars in [start, end)
s.split(",")                    // → string[]
s.chars()                       // → array of int (char codes)
s.starts_with_i("pre")          // case-insensitive prefix
s.ends_with_i("suf")            // case-insensitive suffix
s.trim_left()                   // strip leading whitespace only
s.trim_right()                  // strip trailing whitespace only
```

Operators:

```c
string c = a + b;          // concat via bin_add
bool eq = a == b;          // equality via bin_eq
for (int32 ch : s) { }     // iterate chars (int32 code per char)
```

## Converters

```c
to_string(42)              // "42"     — int / uint / char (any integral)
to_string(3.14)            // "3.14"   — float32 / float64
to_string(true)            // "true"   — bool
```

`to_string(x)` works for the integral family, floats, and bool. For chars used as characters (rather than code points), use `char_to_str('A')` → `"A"` — the `to_string` overload prints `'A'` as `"65"` since char is `int8` underneath.

`cast<string>(x)` is the universal coercion path; fires automatically whenever the compiler needs a `string` (native arg, `s + x` concat).

## Char / encoding helpers

```c
int64  c = ord('A')              // 65 - char code
string s = chr(65)               // "A"
string r = from_chars(s.chars()) // build a string from a char-code array

string h  = hex_encode(255)      // "ff"  (also overloaded on string → hex-encoded bytes)
string h2 = to_hex(255)          // "ff"  (alias for hex_encode(int64))
string b  = hex_decode("616263") // "abc" (byte-string round-trips hex_encode)
int64  v  = hex_to_int("ff")     // 255

string e = base64_encode("hello")     // "aGVsbG8="
string d = base64_decode("aGVsbG8=")  // "hello"

string u = url_encode("hello world & foo=bar")  // "hello%20world%20%26%20foo%3Dbar"
string p = url_decode("hello%20world")          // "hello world" (also '+' -> ' ')
```

## `format(fmt, ...)`

Variadic formatter. Accepts BOTH brace placeholders (`{spec}`) and printf-style placeholders (`%conv`). Use whichever feels natural — they're interchangeable and can mix in the same format string.

```c
// Brace syntax
string s1 = format("x = {d}, y = {f}", 10, 3.14);        // "x = 10, y = 3.14"
string s2 = format("name = {s}, on = {b}", "ada", true); // "name = ada, on = true"
string s3 = format("hex = {x}", 255);                    // "hex = ff"
println(format("char = {c}", 'A'));                      // "char = A"

// printf-style — same conversion letters
string p1 = format("x = %d, y = %f", 10, 3.14);          // "x = 10, y = 3.14"
string p2 = format("name = %s, on = %b", "ada", true);   // "name = ada, on = true"
string p3 = format("100%% done");                        // "100% done" (escaped %)
```

| Spec                               | Interprets arg as             |
| ---------------------------------- | ----------------------------- |
| `{d}` / `{i}` / `{}` / `%d` / `%i` | signed int64                  |
| `{u}` / `%u`                       | unsigned int64                |
| `{f}` / `%f`                       | float64 (bit-cast from int64) |
| `{s}` / `%s`                       | string pointer                |
| `{b}` / `%b`                       | bool → "true"/"false"         |
| `{x}` / `%x`                       | hex int64                     |
| `{c}` / `%c`                       | char code → single char       |

`%%` produces a literal `%`. Unknown `%` sequences pass through unchanged so non-format `%` characters in user text are safe.

## `wstring`

UTF-16 wide string. Heap-allocated null-terminated `uint16_t*` buffer. Length is counted in code units (matches Win32 `wcslen`), not code points — surrogate pairs count as 2.

```c
wstring w = cast<wstring>("Hello");      // UTF-8 → UTF-16
string  s = cast<string>(w);             // UTF-16 → UTF-8 (round-trips)

w.length()                    // code units
w.is_empty()
w.char_at(0)                  // UTF-16 code unit
w.substr(0, 3)                // wstring
w.find(other)                 // index, -1 if missing
w.contains(other)
w.starts_with(prefix)
w.ends_with(suffix)
w.to_upper()                  // ASCII case fold only
w.to_lower()
w.to_string()                 // UTF-16 → UTF-8 string

wstring full = w + cast<wstring>(", world");   // operator+
bool eq = (w == cast<wstring>("Hello"));        // operator==
bool ord = (w < cast<wstring>("zzz"));          // <, >, <=, >=
```

String arguments to wstring methods auto-wrap, so `w.contains("foo")` works without explicit `cast<wstring>(...)`. The wrap is one-way at the method-arg boundary — assignments still require an explicit cast or one of the free-fn factories.

### Free functions

```c
wstring wstring_from_str(string s)         // UTF-8 → UTF-16
string  wstring_to_str(wstring w)          // UTF-16 → UTF-8
wstring wstring_from_wchar_ptr(int64 p)    // const wchar_t* → wstring (copies)
wstring wstring_from_utf8_ptr(int64 p)     // const char*    → wstring (transcodes)
```

`wstring_from_wchar_ptr` / `wstring_from_utf8_ptr` are the entry points hosts use when handing Enma a raw C buffer from a native API (Win32 strings, third-party SDK return values, etc.). Both copy into Enma-owned storage so the caller's buffer lifetime is decoupled.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/strings.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-thread.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/thread.md).

# Thread

Registered with `register_addon_thread(engine)`.

Three addon types for thread synchronization: `mutex`, `lock_guard` (RAII over a mutex), and `cond_var`. `mutex` is backed by `std::shared_mutex`, so the same handle supports both exclusive (writer) and shared (reader) locks. `cond_var` is a thin wrapper around `std::condition_variable_any`.

## mutex

```cpp
mutex m;
m.lock();
// critical section (exclusive)
m.unlock();

bool got = m.try_lock();          // non-blocking exclusive
if (got) m.unlock();

// Reader-writer usage:
m.lock_shared();                  // multiple shared holders allowed
// read-only critical section
m.unlock_shared();
```

### Methods

```cpp
void m.lock()             // exclusive (writer)
void m.unlock()
bool m.try_lock()

void m.lock_shared()      // shared (reader); concurrent shared holders allowed
void m.unlock_shared()
bool m.try_lock_shared()
```

Use `lock` / `unlock` for plain mutual exclusion; the shared variants when multiple readers can safely run together but writers need to be alone (`std::shared_mutex` semantics).

## lock\_guard

RAII wrapper: constructor locks, destructor unlocks. Copies are rejected at runtime because two guards can't both own the same lock.

```cpp
mutex m;
{
    lock_guard g = lock_guard(m);
    // m is held here
}   // scope exit -> dtor -> m is released
```

Attempting to copy raises a runtime error:

```cpp
lock_guard a = lock_guard(m);
lock_guard b = a;       // runtime: "lock_guard is non-copyable"
```

## cond\_var

`cond_var` is `std::condition_variable_any`, which waits on any mutex. The mutex must already be held by the caller when `wait` is invoked; it's released during the wait and reacquired before returning.

```cpp
mutex m;
cond_var cv;

// Consumer:
m.lock();
while (!queue_has_items()) {
    cv.wait(cast<int64>(/* mutex handle */));
}
// drain queue...
m.unlock();

// Producer:
m.lock();
queue_push(x);
cv.notify_one();    // or notify_all()
m.unlock();
```

### Methods

```cpp
void cv.wait(int64 mutex_handle)
void cv.notify_one()
void cv.notify_all()
```

## Free helpers

```cpp
sleep_us(1000)              // sleep for N microseconds
yield_cpu()                 // hint scheduler to yield this quantum
int64 n = hardware_threads() // platform's reported core count
```

## Cross-thread usage

For a real multi-thread scenario, the host spawns threads from native code and shares the mutex handle across threads. Mutex/cond\_var handles can be passed across threads safely.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/thread.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-time.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/time.md).

# Time

Registered with `register_addon_time(engine)`.

All timestamps are `int64` microseconds since the Unix epoch (1970-01-01 00:00:00 UTC). Calendar accessors interpret in UTC.

## Current time

```cpp
int64 us = now_us()              // microseconds since epoch
int64 ms = now_ms()              // milliseconds since epoch
int64 ns = now_ns()              // nanoseconds since epoch
int64 s  = unix_seconds()        // seconds since epoch
int64 m  = mono_us()             // monotonic (for deltas; not an epoch)
```

## Calendar accessors

Given a timestamp, extract UTC calendar fields:

```cpp
int64 t = from_ymdhms(2024, 6, 15, 12, 30, 45);
int64 y = year(t)                // 2024
int64 mo = month(t)              // 1..12
int64 d = day(t)                 // 1..31
int64 h = hour(t)                // 0..23
int64 mi = minute(t)             // 0..59
int64 sec = second(t)            // 0..59
int64 dow = day_of_week(t)       // 0=Sun..6=Sat
int64 doy = day_of_year(t)       // 1..366
```

## Leap years / days per month

```cpp
bool  lp = is_leap(2024)                  // true
int64 n  = days_in_month(2024, 2)         // 29 (leap feb)
int64 x  = days_in_month(2024, 13)        // 0 (invalid month)
```

## Construction

```cpp
int64 t1 = from_ymd(2024, 1, 15)                     // midnight UTC
int64 t2 = from_ymdhms(2024, 1, 15, 10, 30, 45)      // full
```

## ISO 8601

Format produces `YYYY-MM-DDTHH:MM:SS.ffffffZ`. Parse accepts the full form, or date-only `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM:SS`, optionally with `.ffffff` fractional seconds and trailing `Z`.

```cpp
string iso = iso_format(t)               // "2024-06-15T12:30:45.000000Z"
int64 t2 = iso_parse("2024-06-15")       // midnight UTC of that day
int64 t3 = iso_parse(iso)                // round-trips
```

## Arithmetic

```cpp
int64 later   = add_seconds(t, 60)       // +60s
int64 tomorrow = add_days(t, 1)          // +1 day

int64 du = diff_us(t_later, t_earlier)   // microseconds
int64 dm = diff_ms(t_later, t_earlier)   // milliseconds
int64 ds = diff_s(t_later, t_earlier)    // seconds
```

## Sleep

```cpp
sleep_ms(100)                             // suspend 100ms
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/time.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-variant.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/variant.md).

# Variant

`variant` is Enma's open tagged union, it holds a value of any registered type along with that type's id. Used for JSON-like trees, polymorphic dicts (`map<string, variant>` or `imap<variant>` for int64 keys), RPC payloads, and anywhere the static type isn't knowable at compile time.

## Quick start

```cpp
variant v = 42;               // int
variant s = "hello";          // string (variant owns a copy)
variant f = 3.25;             // float
variant b = true;              // bool
variant n;                     // null (0-arg default)

if (v.is_int()) {
    int64 x = v.as_int();
}
if (s.type_name() == "string") {
    string p = s.as_str();
}
```

## Constructors

| Form                                                                              | Result                                                    |
| --------------------------------------------------------------------------------- | --------------------------------------------------------- |
| `variant()` / `variant v;`                                                        | null variant                                              |
| `variant v = 42;`                                                                 | int variant (via `.convert(t_int64)`)                     |
| `variant v = "x";`                                                                | string variant (copies source)                            |
| `variant v = 3.14;`                                                               | float variant                                             |
| `variant v = true;`                                                               | bool variant                                              |
| `variant_int(x)` / `_float(x)` / `_bool(x)` / `_str(x)` / `_array(x)` / `_map(x)` | explicit factories                                        |
| `variant_box(value, type_id)`                                                     | box any registered type (non-owning)                      |
| `variant_box_owned(value, type_id)`                                               | box any registered type (dtor drops inner via reflection) |
| `variant_null()`                                                                  | explicit null                                             |

## Type predicates

```cpp
v.is_null()    v.is_int()    v.is_float()   v.is_bool()
v.is_str()     v.is_array()  v.is_map()
v.is_of_type(TYPE_ID)    // generic check against any type_id
```

## Accessors

```cpp
int64 i = v.as_int();          // int/bool (0/1)/float (trunc)
float64 f = v.as_float();      // float/int/bool
bool b = v.as_bool();          // truthy on non-zero/non-empty
string s = v.as_str();         // only for string variants
array a = v.as_array();
map m = v.as_map();
int64 tid = v.type();          // raw type_id
string tn = v.type_name();     // registered name
int64 raw = v.raw_storage();   // bypass accessors, for custom types
```

## Mutation

```cpp
v.set_int(100);
v.set_float(2.5);
v.set_bool(false);
v.set_str("new");      // frees old string if variant held one
v.set_null();
```

## Equality

`variant == variant` compares: (a) same type\_id, (b) for strings does `strcmp`, (c) for everything else compares the storage. Different-type variants are not equal.

## Holding a custom type

Any type registered via `type_builder` can be boxed:

```cpp
// assume `date` was registered by the date addon:
//   type_builder(e, "date", t_int64)
//     .factory(...).destructor(...);

// DATE_TID is set by the host via set_global()
int64 DATE_TID = ...;

int64 dh = mk_date(2026, 4, 22);
variant v = variant_box_owned(dh, DATE_TID);

if (v.is_of_type(DATE_TID)) {
    // v now owns dh, dtor will free via the date's registered dtor
}
```

`variant_box_owned` makes the variant the owner. When the variant is dropped, it dispatches through reflection (`find_type_reg(type_id) → reg->dtor_fn(storage)`) to clean up the wrapped value. Use `variant_box` (non-owning) if the wrapped value's lifetime is managed elsewhere.

## Ownership semantics

| Factory                     | Owns storage?                 | Dtor behavior                               |
| --------------------------- | ----------------------------- | ------------------------------------------- |
| `variant_int/float/bool`    | inline (storage is the value) | free variant node only                      |
| `variant_str`               | yes, variant owns a copy      | free string + variant node                  |
| `variant_array/map`         | no, shares the handle         | free variant node only                      |
| `variant_box(v, tid)`       | no                            | free variant node only                      |
| `variant_box_owned(v, tid)` | yes                           | call wrapped type's dtor, free variant node |

## Notes

* The `tag` (type\_id) field is 32-bit; custom IDs start at 128.
* `v.type_name()` allocates a string; caller manages via normal string semantics.
* Bare `variant v;` invokes the 0-arg factory.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/variant.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/addon-vec.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/vec.md).

# Vectors

`vec2`, `vec3`, and `vec4` are value-type structs (16 / 24 / 32 bytes, 2 / 3 / 4 `float64` components). They are part of the `math` addon — register with `register_addon_math(engine)` on the host side and (if your host hasn't already registered it for you) `import "math";` on the script side.

```enma
import "math";

int64 main() {
    vec3 a = vec3(1.0, 2.0, 3.0);
    vec3 b = vec3(4.0, 5.0, 6.0);
    vec3 c = a + b;
    return cast<int64>(c.x);
}
```

Stored inline as fields (no heap indirection). `vec3[]` lays out N × 24-byte vec3s back-to-back; `xs.push(vec3(...))` memcpys the value.

## Construction

```cpp
vec2 p = vec2(1.0, 2.0);
vec3 v = vec3(1.0, 2.0, 3.0);
vec4 q = vec4(1.0, 2.0, 3.0, 4.0);

// Default constructor zeros all components.
vec3 zero;
```

## Component access

Components are plain struct fields — there is no `.x()` / `.y()` parenthesised getter form.

```cpp
// Read
float64 x = v.x;
float64 y = v.y;
float64 z = v.z;
float64 w = q.w;       // vec4 only

// Write
v.x = 5.0;
v.z = 3.0;
q.w = 1.0;
```

Field access compiles to a direct memory read/write — no native call, no allocation.

## Operators

```cpp
vec3 s = a + b;            // vec2 / vec3 / vec4
vec3 d = a - b;
vec3 k = v * 2.5;          // scalar multiply (float64 RHS)
vec3 n = -a;               // unary negate
bool eq = (a == b);        // component-wise equality
bool truthy = !!a;         // false if all components are 0

a += b;
a -= b;
```

## Methods

Common to **vec2 / vec3 / vec4**:

```cpp
vec3 r = a.add(b);            // same as a + b
vec3 r = a.sub(b);
vec3 r = a.scale(2.0);
vec3 r = a.neg();             // alias: a.negate()
float64 d = a.dot(b);
float64 L = v.length();
float64 Lsq = v.length_sq();   // squared (no sqrt)
float64 d = a.distance(b);
vec3 n = v.normalize();        // unit vector; zero-length stays zero
vec3 l = a.lerp(b, t);         // component-wise
```

**vec2** also has:

```cpp
vec2 r = v.rotate(rad);        // rotate CCW by `rad` radians
```

**vec3** also has:

```cpp
vec3 c = a.cross(b);
vec3 r = v.reflect(n);                 // reflect across normal `n`
vec3 p = v.project(onto);              // projection of v onto `onto`
float64 a = u.angle(v);                // angle between u and v (radians)
vec3 r = v.rotate_around(axis, rad);   // Rodrigues; axis is normalized internally
```

## Scalar helpers

Free functions in the same addon:

```cpp
float64 r = deg_to_rad(180.0);           // ~π
float64 d = rad_to_deg(3.14159);         // ~180

float64 a = lerp_angle(a0, a1, t);       // shortest-path angular lerp (radians)
float64 p = move_toward(cur, tgt, step); // step without overshooting target

float64 e1 = ease_in(t);                 // t² (t in [0,1])
float64 e2 = ease_out(t);                // 1-(1-t)²
float64 e3 = ease_in_out(t);             // quadratic in-out

bool ok = approx_eq(a, b, eps);          // |a-b| <= eps
```

For quaternions and 4×4 matrices see [3D Math](addon-math3d.md). For scalar math (`sin`, `cos`, `sqrt`, `pow`, ...) see [Math](addon-math.md).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/vec.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/lang-advanced.md`

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

See [Pointers](lang-pointers.md) for the full pointer reference.

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

`T[] arr` is a growable, subscript-safe array with scope-drop cleanup. `T* p = new T[N]` is a raw contiguous block with per-element ctor/dtor and manual `delete[]`. Args after the size (`new T[N](args)`) are passed to each element's ctor; args are evaluated once, not N times. See [Structs & Classes](lang-structs-and-classes.md#contiguous-heap-arrays).

Use `p->field` for pointers, `p.field` for value structs. See [Lifecycle & RAII](sdk-lifecycle.md).

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

---

## Source: `docs/enma/lang-annotations.md`

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

---

## Source: `docs/enma/lang-basics.md`

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

`const` prevents reassignment. `constexpr` evaluates at compile time and folds into the IR as a literal — see [Compile-Time Evaluation](lang-advanced.md#compile-time-evaluation) for what's foldable and how to write `constexpr` functions and `static_assert`s. `nullable` allows a variable to hold `null`. `auto` infers the type from the right-hand side.

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

f-string interpolation (see [Advanced](lang-advanced.md)) follows the same escape rules.

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

Float literals use `f` / `F` suffix for `float32`; bare `3.14` is `float64`. Integer literals default to `int32` in contexts that accept any integer but adapt when assigned to a wider type. Underscore digit separators (`1_000_000`) work in all numeric forms — they're stripped at lex time so `std::stoll`-style parsers see clean digits. User-defined literal suffixes (`_km`, `_m`, etc.) parse as calls to a same-named function - see [user-defined literals](lang-advanced.md) for details. The lexer distinguishes the two by what follows the underscore: digit → separator, alpha → UDL.

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

---

## Source: `docs/enma/lang-functions.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/functions.md).

# Functions

## Basic Functions

```c
int32 add(int32 a, int32 b) {
    return a + b;
}

void greet() {
    println("hello");
}
```

## Default Parameters

Defaulted params must come after all required params.

```c
int32 connect(int32 port, int32 timeout = 5000) {
    return port + timeout;
}

connect(8080);        // timeout = 5000
connect(8080, 1000);  // timeout = 1000
```

## Reference Parameters

Pass by reference with `&`. Changes to the parameter modify the caller's variable.

```c
void swap(int32& a, int32& b) {
    int32 t = a;
    a = b;
    b = t;
}

int32 x = 10;
int32 y = 20;
swap(x, y);  // x=20, y=10
```

## Out Parameters

`out` is an alternative syntax for reference parameters. Identical semantics to `&`.

```c
void compute(int32 input, out int32 result, out int32 remainder) {
    result = input / 10;
    remainder = input % 10;
}

int32 r = 0;
int32 rem = 0;
compute(42, r, rem);  // r=4, rem=2
```

## Variadic Functions

Use `...` at the end of the parameter list. Inside the body, `__va_count` is the number of variadic args and `__va_arg(i)` reads the i-th:

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

int32 main() { return cast<int32>(sum(1, 2, 3, 4, 5)); }   // 15
```

Fixed params before `...` are read normally:

```c
void log(int32 level, ...) {
    int64 i = 0;
    while (i < __va_count) {
        println(__va_arg(i));
        i = i + 1;
    }
}
log(1, 10, 20, 30);
```

Args are passed through as `int64`-sized slots; the callee is responsible for interpreting each one.

## Shadowing Native Functions

A script function with the **same signature** as a native (addon-registered) function wins at every call site. Different signatures don't shadow — the resolver picks whichever overload matches the call's argument types, so a script `wrap(string)` and a native `wrap(float, float, float)` coexist and dispatch by arity/type. To force the script version for a given site, give it a unique name.

```c
// Same signature as math addon's wrap → script version wins.
float64 wrap(float64 x, float64 lo, float64 hi) { return 999.0; }
```

## Forward Declarations

Declare a function signature before its implementation. Useful for mutual recursion.

```c
int32 is_even(int32 n);

int32 is_odd(int32 n) {
    if (n == 0) return 0;
    return is_even(n - 1);
}

int32 is_even(int32 n) {
    if (n == 0) return 1;
    return is_odd(n - 1);
}
```

## Extern Functions

Declare a function implemented in another module or native code.

```c
extern int32 lib_func(int32 x);
```

## Function References

Prefix a function name with `@` to take its address:

```c
int64 fn_ptr = @add;
```

For a typed reference, assign to a matching delegate.

## Lambdas

### Bracket Style

```c
delegate int32 Transform(int32 x);
Transform fn = [](int32 x) -> int32 { return x * 2; };
int32 r = fn(21);  // 42
```

### Arrow Lambdas

Expression body (result returned implicitly):

```c
delegate int32 Transform(int32 x);
Transform fn = (int32 x) => x * 2;
int32 r = fn(21);  // 42
```

Block body:

```c
int64 fn = (int32 a, int32 b) => {
    int32 sum = a + b;
    return sum * 2;
};
```

Zero parameters:

```c
int64 fn = () => 42;
```

### Closures

Lambdas automatically capture variables from the enclosing scope:

```c
delegate int32 Transform(int32 x);
int32 base = 100;
Transform adder = [](int32 x) -> int32 { return base + x; };
int32 r = adder(5);  // 105
```

Explicit capture lists:

```c
int32 a = 10;
int32 b = 20;
int64 fn = [a, b](int32 x) -> int32 { return a + b + x; };
```

Arrow lambdas capture implicitly as well:

```c
int32 scale = 3;
int64 fn = (int32 x) => x * scale;
```

### Capture by reference

Prefix a capture name with `&` to bind the outer slot by reference. Writes inside the lambda land in the outer scope's local; reads see live changes. Without `&` (bare `[x]`), the capture is a snapshot taken at closure-construction time and outer changes don't propagate.

```c
int64 main() {
    int64 counter = 0;
    auto inc = [&counter]() { counter = counter + 1; };
    inc(); inc(); inc();
    return counter;                   // 3
}
```

`&` works for primitives, value-structs (member writes land in the outer struct), strings, arrays, maps, and any treg-typed local. It also composes: nested lambdas can each take `[&x]` of the same outer variable and they all share one address.

```c
int64 main() {
    int64 outer = 0;
    auto bump = [&outer]() {
        auto inner = [&outer]() { outer = outer + 1; };
        inner(); inner();
    };
    bump(); bump();
    return outer;                     // 4
}
```

Bare `[x]` mixed with `[&y]` is allowed and the value/reference semantics apply independently per capture. Lifetime: the outer scope must outlive the closure — once the outer frame drops, dereferencing the captured address is undefined behaviour. Returning a closure that ref-captures a local of the returning function is the classic foot-gun.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/functions.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/lang-modules.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/modules.md).

# Modules

## Importing Modules

The `import` statement loads another Enma module. Imported symbols are namespaced.

```cpp
import scanner

int32 main() {
    scanner::init();
    scanner::run();
    return 0;
}
```

### Aliased Imports

```cpp
import scanner as sc

sc::init();
```

### Path Imports

Import from an explicit file path:

```cpp
import "libs/math_utils.em"
```

## Module Resolution

When you write `import scanner`, the compiler searches for:

1. `scanner.emb` (precompiled binary) in module paths
2. `scanner.em` (source file) in module paths and include paths

`.emb` files are tried first, then `.em` source as fallback.

Configure search paths from the SDK:

```cpp
add_module_path(engine, "modules/");
add_include_path(engine, "includes/");
```

## Precompiled Modules (.emb)

Enma modules can be compiled to a binary format (`.emb`) for distribution without source code. The SDK provides `serialize()` and `deserialize()` for this.

Precompiled modules expose their public functions as `extern` declarations in the importer's namespace. Functions starting with `_` are considered internal and hidden.

Use `[[export]]` to explicitly control which functions are visible:

```cpp
[[export]]
int32 public_fn() { return 42; }

int32 private_fn() { return 1; }
// private_fn is hidden when compiled to .emb
```

## Linking Multiple Modules

The SDK's `link()` function combines multiple compiled modules into a single unit, resolving cross-module references:

```cpp
import math_lib
import string_lib

int32 main() {
    float64 r = math_lib::sqrt(2.0);
    string s = string_lib::format(r);
    return 0;
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/modules.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/lang-pointers.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/pointers.md).

# Pointers

Pointers are typed handles to heap objects. Allocate with `new`, free with `delete`. Access fields and methods with `->`. Use `.` on values and `->` on pointers as a style convention — the parser accepts either form for both, but mixing makes code harder to read and auto-formatting may rewrite to the canonical form.

Storing the address of a local somewhere it could outlive the local is a compile error — the escape analyzer rejects anything that could dangle. Pointer arithmetic on typed pointers is supported (see below).

Pointer ↔ `int64` / `uint64` is implicit (both 8-byte slots, lossless on x64). Useful for handing handles to native APIs and for taking script-side function references via `&fn` (a `pointer` value that converts to `int64` without a cast). The implicit conversion is not a workaround for the escape analyzer - allocation and lifetime rules still apply.

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

Currently restricted to a simple variable name — `move(arr[i])` and `move(s.field)` error out at compile time.

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

---

## Source: `docs/enma/lang-pre-processor.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/pre-processor.md).

# Pre Processor

C-style preprocessor running before parsing: macros, conditional compilation, file inclusion.

## Defines

```cpp
#define MAX_HP 100
#define SQUARE(x) ((x) * (x))

int32 hp = MAX_HP;
int32 area = SQUARE(5);  // 25
```

## Conditional Compilation

Directives: `#ifdef`, `#ifndef`, `#else`, `#elif`, `#endif`, `#undef`, `#pragma`.

```cpp
#ifdef DEBUG
    println("debug mode");
#else
    // release mode
#endif
```

Define preprocessor symbols from the SDK:

```cpp
define(engine, "DEBUG", "1");
define(engine, "PLATFORM", "windows");
```

Then use in scripts:

```cpp
#ifdef PLATFORM
    println("platform defined");
#endif
```

## Include

Include another source file. The contents are inserted at the include point.

```cpp
#include "common.em"
#include "types.em"
```

Include paths are configured from the SDK:

```cpp
add_include_path(engine, "includes/");
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/pre-processor.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/lang-semantics-and-limits.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/semantics-and-limits.md).

# Semantics & Limits

Single-page answer to "can I do X?" grouped by area, with the verdict and where the rule lives.

## Pointers

Enma supports pointers as typed handles to heap objects. Pointer **arithmetic and manipulation are not in the language**. Pointers only participate in creation, member access, and deletion.

| Operation                                     | Allowed | Notes                                                              |
| --------------------------------------------- | :-----: | ------------------------------------------------------------------ |
| `T* p = new T(args);`                         |    ✓    | Heap allocation with ctor                                          |
| `p->field` (pointer access)                   |    ✓    | Use `->` on pointers, `.` on values (style); parser accepts either |
| `delete p;`                                   |    ✓    | Manual free; no-op on null                                         |
| `T* q = p;` (pointer copy)                    |    ✓    | Two pointers to the same object                                    |
| `T* q = null;`                                |    ✓    | Null literal assignable to any pointer type                        |
| `int64 i = 0x1000; T* p = i;`                 |    ✓    | int64/uint64 ↔ pointer is implicit (8-byte slot, lossless on x64)  |
| `int64 addr = cast<int64>(p);`                |    ✓    | Pointer → int64 is implicit; the explicit cast also works          |
| `int64 fn = my_function;` (or `&my_function`) |    ✓    | function → int64/pointer is implicit (closure handle)              |
| `T* p = &s + 8;` (pointer arithmetic)         |    ✗    | Compile error                                                      |
| `T* p = &local;` (address-of must feed ptr)   |  ✗ / ✓  | Must assign to pointer type; storing to non-pointer is an error    |
| `T x = new T();`                              |    ✗    | Pick stack (`T x;`) or heap (`T* x = new T();`)                    |
| `delete` on non-pointer                       |    ✗    | Compile error                                                      |
| Double delete / delete null                   |    -    | No-op                                                              |
| Storing pointer-to-local in a global/field    |    ✗    | Compile error (would dangle)                                       |
| Returning pointer to local                    |    ✗    | Compile error (would dangle)                                       |

The escape analyzer is conservative, if it can't prove the pointer is safe, it rejects. Moving to `new T()` is the escape hatch.

## Memory model

| Feature                                    | Status                                                                       |
| ------------------------------------------ | ---------------------------------------------------------------------------- |
| Stack-allocated structs (`T x;`)           | Default for value-type structs                                               |
| Heap-allocated structs (`T* x = new T();`) | Explicit via `new` / `delete`                                                |
| RAII / scope-drop                          | Built-in for all addon types with a registered dtor                          |
| Tracing garbage collector                  | **None**. Cleanup is deterministic (compile-time scope / explicit `delete`). |
| Manual `free`                              | Use `delete p` for `new`-allocated pointers                                  |
| Double-free                                | Runtime error (for array types); no-op for `delete null`                     |
| Use-after-free                             | Trapped where possible; `execute()` returns `false`                          |
| Budget (instruction / memory)              | Opt-in per module                                                            |

## Integer semantics

| Behavior                           | Rule                                                                                                      |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Overflow                           | Silent wrap at int64 width, script-level arithmetic evaluates at 64 bits regardless of declared int width |
| Division by zero                   | Runtime trap                                                                                              |
| Shift by >= bit-width              | Implementation-defined (x64: modulo the width)                                                            |
| Signed ↔ unsigned (any width)      | **Compile error** without `cast<T>(x)`. Integer/float literals are exempt - `uint32 a = 5;` is fine.      |
| `int32 → int64` (same-sign widen)  | Implicit                                                                                                  |
| `int64 → int32` (same-sign narrow) | Implicit (runtime is 64-bit-slot regardless; narrowing is purely a declared-type thing)                   |

## Float semantics

| Behavior                     | Rule                                                                                                                                                                                   |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| NaN propagation              | Standard IEEE-754 (`NaN != NaN`, arithmetic propagates NaN)                                                                                                                            |
| `float32` ABI                | Native boundary narrows to 32-bit; script keeps 64-bit view (round-trip bits preserved for `cast<float32>(x)` literals)                                                                |
| `float32 → float64` (widen)  | Implicit                                                                                                                                                                               |
| `float64 → float32` (narrow) | **Compile error** without `cast<float32>(x)`. Float literals are exempt - `float32 a = 1.5;` is fine.                                                                                  |
| Float literal `float32` form | `1.5f` / `1.5F` - the suffix narrows the literal to `float32` at parse time. Bare `1.5` is `float64`. The suffix is literal-only; runtime narrowing still needs `cast<float32>(expr)`. |
| `int → float`                | Implicit                                                                                                                                                                               |
| `float → int`                | **Compile error** without `cast<int>(x)`. Truncation is too easy to miss silently.                                                                                                     |
| Infinity                     | Standard IEEE, operations follow IEEE rules                                                                                                                                            |

## Type system

| Feature                                    | Supported                                                                                                                                                               |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Structs (value type, stack-default)        | ✓                                                                                                                                                                       |
| Classes (reference type with vtable)       | ✓                                                                                                                                                                       |
| Single inheritance + virtual methods       | ✓ (classes; structs don't vtable unless marked)                                                                                                                         |
| Multiple inheritance (C++-style)           | ✓ (`class C : A, B { ... }`. Diamond rejected, ctor/dtor chain in declaration / reverse order, this-adjusted dispatch, vtable thunks for override-via-non-primary-base) |
| Templates (`template<typename T>`)         | ✓ (duck-typed at instantiation)                                                                                                                                         |
| Concepts / requires clauses (script-level) | ✗ (generic addon types support `.requires_iface(param, iface)` constraints SDK-side)                                                                                    |
| Variadic templates (`Ts...`)               | ✗ (but functions accept `...` with `__va_count` / `__va_arg(i)` for runtime varargs)                                                                                    |
| `decltype(expr)`                           | ✓                                                                                                                                                                       |
| Designated initializers (`{.x=1, .y=2}`)   | ✓                                                                                                                                                                       |
| User-defined literals (`42_km`)            | ✓ (rewritten to `_km(42)` at parse)                                                                                                                                     |
| RTTI (`typeid`)                            | ✗ (but addon-type reflection via `find_type_reg`)                                                                                                                       |
| rvalue references / move semantics         | partial — `move(x)` intrinsic transfers + nulls source; no `&&` rvalue-reference type                                                                                   |
| Reflection at script level                 | ✗ (SDK-side only, via `find_type_reg`)                                                                                                                                  |
| Modules (`import` / `#include`)            | ✓                                                                                                                                                                       |
| Namespaces / `using`                       | ✓                                                                                                                                                                       |
| Operator overloading                       | ✓ on script structs (`operator+` etc.) and addon types (via `bin_*` / `unary_*`)                                                                                        |
| Exceptions (`try` / `catch` / `throw`)     | ✓ (throw any int / string / struct; multiple typed `catch` clauses dispatched on thrown type)                                                                           |
| Match expression (`match (x) { ... }`)     | ✓ (returns a value; arms use `=> expr,` or `_` wildcard)                                                                                                                |
| Ternary (`cond ? a : b`)                   | ✓                                                                                                                                                                       |
| Coroutines (`coroutine` / `yield`)         | ✓                                                                                                                                                                       |
| Delegates                                  | ✓                                                                                                                                                                       |
| Lambdas / closures                         | ✓ (closure escape rules enforced)                                                                                                                                       |
| Mixins / properties                        | ✓                                                                                                                                                                       |
| Nullable types (`nullable T`)              | ✓                                                                                                                                                                       |
| Fixed-size arrays (`int32[2] buf`)         | ✗ (use `int32[] buf = new int32[N]` or brace init `{...}`)                                                                                                              |

## Unsafe operations (rejected at compile time)

These produce a compile error, not a runtime fault:

* Raw int → pointer assignment
* Pointer arithmetic (`&s + 8`, `p + 1`)
* `cast<int64>(ptr)` - pointer to int
* Escaping a stack local (into a global, a field, or out of a return)
* Calling a non-`const` method on a `const` receiver
* Assigning through a `const` parameter
* Native call with wrong-typed arg (integer where string expected, etc.)
* Native call with wrong enum identity (raw int or cross-enum)
* Template method call with wrong element/key/value type
* `new` on a non-addon-registered, non-struct, non-class type
* `delete` on a non-pointer
* `T x = new T();` (must pick stack or heap)
* `[[noescape]]` violation (allocation that escapes)
* Function lacking a matching signature / ambiguous overload
* Calling a native that requires a permission the module doesn't have

## Runtime traps

These are caught at runtime and reported via `execute()` returning `false`:

* Null deref on array or struct pointer (script-catchable via `try`/`catch (string e)` when using `->`; see [Catching null-pointer dereferences](lang-advanced.md#catching-null-pointer-dereferences))
* Out-of-bounds array subscript (positive or negative index)
* Access to a freed array
* Division by zero
* Stack overflow
* Double-free on arrays (reported as a runtime error)
* Use-after-free where the freed-marker is still readable

Inside a native function: **not trapped.** Validate your inputs before dereferencing; use `heap_is_tracked(ptr)` for heap-allocated values.

## Permissions

Two bits today. A script cannot call any permission-gated native unless the permission was granted via `set_permissions(engine, flags)` on the engine:

| Flag        | Value  | Gates                       |
| ----------- | ------ | --------------------------- |
| `PERM_FFI`  | `0x01` | `[[dll(...)]]` extern decls |
| `PERM_FILE` | `0x02` | All file-addon operations   |

Scripts without the right permission fail to compile any call that requires it, the check happens at module compile, not at runtime.

## Thread safety

* Each engine is independent, no shared mutable state across engines
* Multiple contexts off the same module run concurrently
* Per-thread TLS heap (cleaned up when the thread exits)
* The `thread` addon gives you mutex / cond\_var / lock\_guard for cross-thread coordination. Native functions that touch Enma's heap must be called on a thread that has an active context; raw mutex operations don't need one.
* Tested under ASAN and TSAN with 32+ concurrent threads

## Things that simply don't exist

* **Module system beyond `import`** - no separately-compiled binary modules at the language level (the SDK's `link()` function lets host code join modules)
* **Async / await / futures** - use coroutines + the thread addon
* **Networking addon** - not shipped; host can write one as a standalone addon
* **Custom allocators per scope** - one heap per thread, not pluggable
* **Built-in annotations**: `[[inline]]`, `[[noinline]]`, `[[noopt]]`, `[[dll]]`, `[[packed]]`, `[[align]]`, `[[serialize]]`, `[[reflect]]`, `[[export]]`, `[[noescape]]`. Custom names parse and are queryable from the host but carry no compiler semantics.
* **RTTI / `typeid`** - use `find_type_reg` on the SDK side instead
* **Script-level reflection** - SDK-only
* **Inline assembly** - fixed whitelist of intrinsics only: `__asm_rdtsc`, `__asm_pause`, `__asm_mfence`, `__asm_nop`. Arbitrary user-provided asm is not supported.
* **Fold expressions** (`(args + ...)`) - not supported. Use `__va_arg(i)` + a loop for runtime fold.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/semantics-and-limits.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/lang-structs-and-classes.md`

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

---

## Source: `docs/enma/lang-templates.md`

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

---

## Source: `docs/enma/llms-language.md`

<!-- AUTO-GENERATED: This file is a single-page concatenation of the Enma language docs,
     scraped from https://enma-1.gitbook.io/enma/llms-language.md for LLM context windows.
     Do NOT edit manually — changes belong in the individual lang-*.md / addon-*.md files.
     To regenerate, re-scrape the GitBook source. -->

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

---

## Source: `docs/enma/llms-sdk.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/llms-sdk.md).

# LLMS - SDK

Enma is a full-module AOT and JIT-compiled scripting language you embed in a native host. The SDK is one header plus a static library. Everything lives in namespace `enma`.

## Ship Layout

```cpp
shipped/
├── include/sdk.h
├── enma.h                          (umbrella header)
├── windows/enma_x64static_mt.lib   (/MT static CRT - match your project's CRT flag)
├── windows/enma_x64static_md.lib   (/MD dynamic CRT)
├── linux/libenma.a                 (Linux)
└── addons/em_addon_*.cpp           (source; reference / customization only)
```

Build: link the lib that matches your project's `/MT` or `/MD` flag - mixing them produces a `RuntimeLibrary` mismatch at link. All 17 built-in addons are bundled into both `.lib` variants, so a single link is enough. The standalone `addons/em_addon_*.cpp` files still ship if you want to read, modify, or build a custom subset.

## Minimal Embed

```cpp
#include "sdk.h"
using namespace enma;

int main() {
    engine_t* e = create();
    register_all_addons(e);
    set_optimize(e, true);

    const char* src = R"(
        int32 main() {
            println("hi");
            return 42;
        }
    )";
    module_t* mod = compile(e, src, std::strlen(src), "hi.em");
    if (!mod) {
        auto err = last_error(e);
        fprintf(stderr, "compile: %s at %s:%d\n", err.message.c_str(), err.file.c_str(), err.line);
        destroy(e);
        return 1;
    }

    context_t* ctx = create_context(mod);
    if (!execute(ctx, "main")) {
        auto err = last_error(e);
        fprintf(stderr, "run: %s\n", err.message.c_str());
    }
    int64_t r = return_value(ctx);

    destroy_context(mod, ctx);
    module_destroy(mod);
    destroy(e);
    return (int)r;
}
```

Lifetime order: engine → module → context. Destroy in reverse.

## Engine Lifecycle

```cpp
engine_t* create();
void      destroy(engine_t* e);

void set_optimize(engine_t* e, bool enabled);    // IR opts + JIT optimization
void set_debug(engine_t* e, bool enabled);       // enables source maps, stack traces
void define(engine_t* e, const char* name, const char* value);  // preprocessor
void add_include_path(engine_t* e, const char* path);   // for #include
void add_module_path(engine_t* e, const char* path);    // for import
void set_permissions(engine_t* e, uint32_t flags);      // PERM_FFI | PERM_FILE
uint32_t get_permissions(engine_t* e);

// Optional: override how #include / import resolve paths
using resolve_fn = bool(*)(const char* path, char** out_data, size_t* out_len, void* userdata);
void set_include_resolver(engine_t* e, resolve_fn fn, void* userdata);
void set_import_resolver(engine_t* e, resolve_fn fn, void* userdata);
```

Permissions:

```cpp
inline constexpr uint32_t PERM_FFI  = 0x01;   // gates [[dll(...)]]
inline constexpr uint32_t PERM_FILE = 0x02;   // gates file addon
```

## Compilation

```cpp
module_t* compile(engine_t* e, const char* src, size_t len, const char* filename);
module_t* compile_file(engine_t* e, const char* path);
void      module_destroy(module_t* m);

// Hot replace source without tearing down contexts:
bool      reload(module_t* m, const char* src, size_t len, const char* filename);

// Binary serialization. keep_debug=false strips source_map + debug_functions
// (drops uploader's source paths from the .emb for marketplace publishing);
// body is XOR-obfuscated with per-file salt regardless.
bool      serialize(module_t* m, std::vector<uint8_t>& out, bool keep_debug = true);
module_t* deserialize(engine_t* e, const uint8_t* data, size_t len);

// Multi-module linking:
module_t* link(engine_t* e, const char** names, module_t** modules, uint32_t count);
```

Compile errors surface via `last_error(e)`.

## Execution

```cpp
context_t* create_context(module_t* m);
void       destroy_context(module_t* m, context_t* ctx);

bool execute(context_t* ctx, const char* fn_name);                                     // no args
bool call(context_t* ctx, const char* fn_name, const int64_t* args, uint32_t count);   // with args

int64_t     return_value(context_t* ctx);   // integer result
const char* return_string(context_t* ctx);  // string result
double      return_float(context_t* ctx);   // float result (bit-cast from int64 slot)

int64_t alloc_string(context_t* ctx, const char* str);  // alloc scripts-visible string
void*   fn_address(module_t* m, const char* name);       // raw JIT fn ptr (for direct call)
```

All args are `int64_t`. Floats bit-cast:

```cpp
double d = 3.14;
int64_t a;
std::memcpy(&a, &d, 8);
call(ctx, "set_value", &a, 1);
```

Return types are read via `return_value` / `return_string` / `return_float` based on the declared script return type.

`execute()` / `call()` return `false` on any JIT-thrown hardware fault (null deref, divide-by-zero, OOB array access, stack overflow, double-delete). The engine remains usable — call `last_error(engine)` for the message + file:line, or `__enma_jit_get_last_fault(&code, &rip, &address, &access_type)` for the raw OS exception data. dtors registered for value-struct locals on the faulting frame run via the cleanup-stack unwind, so heap resources don't leak. Process stays alive; the host can retry, log, or abort just that engine.

## Context Userdata (16 slots)

Slot 0 is shared between the single-slot and multi-slot accessors.

```cpp
void  set_userdata(context_t* ctx, void* data);                        // slot 0
void* get_userdata(context_t* ctx);                                     // slot 0
void  set_userdata_at(context_t* ctx, uint32_t slot, void* data);       // slots 0-15
void* get_userdata_at(context_t* ctx, uint32_t slot);
```

Out-of-range slots: no-op on set, `nullptr` on get. Multiple addons coexist by picking distinct slots.

## Globals

```cpp
bool     set_global(module_t* m, const char* name, int64_t value);
int64_t  get_global(module_t* m, const char* name);
bool     has_global(module_t* m, const char* name);
int64_t* get_global_ptr(module_t* m, const char* name);   // direct pointer to the slot
void     list_globals(module_t* m, std::vector<std::string>& names, std::vector<int64_t>& values);
```

## Native Function Registration (three forms)

**Typed (recommended, arity 0-6):**

```cpp
int32_t add(int32_t a, int32_t b) { return a + b; }
register_typed<&add>(e, "int32 add(int32, int32)");
```

The trampoline is generated at compile time. Supports int8/16/32/64, uint\*, float/double, bool, char, pointer, enum.

**Sig-string form:**

```cpp
int64_t my_fn(int64_t a, int64_t b) { return a + b; }
register_native(e, "int64 my_fn(int64, int64)", (void*)my_fn);
```

**Full descriptor form:**

```cpp
native_param params[] = {
    { "a", type_id::t_int32 },
    { "b", type_id::t_int32 },
};
register_native(e, "add", (void*)my_fn, type_id::t_int32, params, 2);
```

**Permissions:** `register_typed<&fn>(e, sig, PERM_FFI)` - script fails to compile the call without matching permission.

**Compile-time sig check:**

```cpp
register_native(e, ENMA_SIG("int64 foo(int64, int64)"), (void*)foo);
// Malformed sigs fail as static_asserts at native compile time.
```

**Sig syntax cheatsheet:**

| Pattern                              | Meaning                                                     |
| ------------------------------------ | ----------------------------------------------------------- |
| `int64 name(int64, float64)`         | Basic                                                       |
| `int64 name(int64 a, int64 b)`       | With param names (shows in error messages)                  |
| `int64 name(int64 a = 10)`           | Default argument                                            |
| `int64 name(...)`                    | Variadic - native takes `(int64 argc, int64* argv)`         |
| `int64 name(string fmt, ...)`        | Required + variadic                                         |
| `array name()` / `array<int> name()` | Typed array return                                          |
| `map<string,int64> name()`           | Typed map return                                            |
| `void name(const proc_t p)`          | Read-only param                                             |
| `void name(const vec3& v)`           | Pass-by-reference                                           |
| `void name(out vec3 v)`              | Write-only reference                                        |
| `struct_t name()`                    | Struct return — hidden first arg is the return-slot pointer |

## Overloading

Same name, different arities or types:

```cpp
register_native(e, "int64 pair(int64, int64)",      (void*)pair_ii);
register_native(e, "int64 pair(float64, float64)",  (void*)pair_ff);
register_native(e, "int64 pair(string, string)",    (void*)pair_ss);
```

Overload resolution picks at script call site by arg types. Ambiguous calls = compile error.

## Type Registration (`type_builder`)

Full fluent API for exposing a native type to scripts.

```cpp
type_builder(e, "vec3_t", type_id::t_struct)
    .field("x", offsetof(vec3_t, x), type_id::t_float64)
    .field("y", offsetof(vec3_t, y), type_id::t_float64)
    .field("z", offsetof(vec3_t, z), type_id::t_float64)

    .factory_typed<&vec3_create>(3)
    .destructor_typed<&vec3_destroy>()

    .method_typed<&vec3_length_sq>("float64 length_sq()")
    .method_typed<&vec3_scale>("vec3_t scale(float64)")

    .property_typed<&get_magnitude>("magnitude", type_id::t_float64)       // read-only
    .property_typed<&get_x, &set_x>("xp", type_id::t_float64)              // read/write

    .subscript_typed<&bag_get, &bag_set>()                                  // [idx] access

    .bin_add_typed<&vec3_add>()
    .bin_sub_typed<&vec3_sub>()
    .bin_mul_typed<&vec3_mul>()
    .bin_eq_typed<&vec3_eq>()
    .compare_typed<&vec3_compare>()

    .copy_typed<&vec3_copy>()
    .hash_typed<&vec3_hash>()

    .iterable((void*)vec3_len, (void*)vec3_at)
    .convert(type_id::t_int64, (void*)vec3_from_int)

    .pure_methods()      // methods don't retain receiver (container hint)
    .pure_args()         // methods don't retain args (value-type hint)
    .permission(PERM_FILE);
// `.finish()` is implicit when the builder goes out of scope; call explicitly
// if you need to chain `type_reg_t*` lookups right after.
```

### Value-type opt-in (vec3, color, quat, etc.)

Three hooks turn a typereg into a value type — non-escaping locals stack-allocate, `T[]` stores values inline, property reads compile to direct loads:

```cpp
type_builder(e, "vec3_t", type_id::t_int64)
    .value_type(sizeof(vec3_t))                       // inline storage size
    .factory_in_place((void*)&vec3_construct)         // int64_t fn(int64_t dst, args...)
    .inline_property("x", (void*)&vec3_get_x, (void*)&vec3_set_x,
                     type_id::t_float64, offsetof(vec3_t, x));
```

`factory_in_place` writes directly into the buffer (`dst` is stack or heap depending on escape analysis). `inline_property` swaps the `call_native` getter/setter for `op_load_field` / `op_store_field` at the given offset — use only when the native impl is a trivial field read.

vec2/vec3/vec4/quat in the shipped addons all opt in.

### Hook Reference

| Hook                                                                         | Typed form                                            | Signature (native)                            | Script usage                                                                                                                                                           |
| ---------------------------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.field(n, off, t)`                                                          | -                                                     | -                                             | `x.field`                                                                                                                                                              |
| `.method(sig, fn)`                                                           | `.method_typed<&Fn>(sig)`                             | `R(U*, args...)`                              | `x.method(args)`                                                                                                                                                       |
| `.property(n, g, s, t)`                                                      | `.property_typed<&Get, &Set>(n, t)`                   | `T(U*)` / `void(U*, T)`                       | `x.prop`, `x.prop = v`                                                                                                                                                 |
| `.subscript(g, s, er?)`                                                      | `.subscript_typed<&Get, &Set>(er?)`                   | `T(U*, int64)` / `void(U*, int64, T)`         | `x[i]`, `x[i] = v`                                                                                                                                                     |
| `.iterable(len, get)`                                                        | -                                                     | `int64(U*)` / `T(U*, int64)`                  | `for (v : x) { }`                                                                                                                                                      |
| `.kv_iterable(len, k, v)`                                                    | -                                                     | `int64(U*)` / `K(U*, int64)` / `V(U*, int64)` | `for (k, v : x) { }`                                                                                                                                                   |
| `.factory(fn, N)`                                                            | `.factory_typed<&Fn>(N)`                              | `U*(args...)`                                 | `T x = T(args)`                                                                                                                                                        |
| `.destructor(fn)`                                                            | `.destructor_typed<&Fn>()`                            | `void(U*)`                                    | scope-drop                                                                                                                                                             |
| `.init_push(fn)`                                                             | -                                                     | `void(U*, val)`                               | brace-init                                                                                                                                                             |
| `.bin_add(fn)` ... `_mod`                                                    | `.bin_*_typed<&Fn>()`                                 | `U*(U*, U*)`                                  | `x + y`, etc.                                                                                                                                                          |
| `.bin_eq/lt/gt/le/ge`                                                        | `.bin_*_typed<&Fn>()`                                 | `bool(U*, U*)`                                | `x == y`, etc.                                                                                                                                                         |
| `.compare(fn)`                                                               | `.compare_typed<&Fn>()`                               | `int64(U*, U*)` (-1/0/+1)                     | three-way, comparison fallback                                                                                                                                         |
| `.bin_*_assign(fn)` (arith)                                                  | `.bin_*_assign_typed<&Fn>()`                          | `U*(U*, U*)`                                  | `x += y`, etc. Falls back to `bin_*` if unset                                                                                                                          |
| `.bit_and_assign / bit_or_assign / bit_xor_assign / shl_assign / shr_assign` | -                                                     | `U*(U*, U*)`                                  | `x &= y`, `x \|= y`, `x ^= y`, `x <<= y`, `x >>= y`. Falls back to the matching `bit_*` / `shl` / `shr` if unset                                                       |
| `.increment / decrement`                                                     | `.increment_typed<&Fn>()` / `.decrement_typed<&Fn>()` | `U*(U*)`                                      | `++x` (prefix) / `--x`. Also handles postfix when no separate `post_*` is registered                                                                                   |
| `.post_increment / post_decrement`                                           | -                                                     | `U*(U*)`                                      | `x++` / `x--`. C++ int-dummy-param convention; declare for distinct postfix semantics                                                                                  |
| `.unary_neg / unary_bit_not`                                                 | `.unary_*_typed<&Fn>()`                               | `U*(U*)`                                      | `-x`, `~x`                                                                                                                                                             |
| `.unary_log_not(fn)`                                                         | -                                                     | `bool(U*)`                                    | `!x`                                                                                                                                                                   |
| `.unary_deref(fn)`                                                           | -                                                     | `T(U*)` (T = whatever you return)             | `*x` smart-pointer-style. Pointer deref of `T*` keeps memberwise-copy semantics                                                                                        |
| `.bit_and / or / xor / shl / shr`                                            | `.bit_*_typed<&Fn>()` / `.shl_typed<&Fn>()`           | `U*(U*, U*)`                                  | `&`, `\|`, `^`, `<<`, `>>`                                                                                                                                             |
| `.call(fn)`                                                                  | -                                                     | variadic                                      | `obj(args...)` — function-call. Pull args via the standard native ABI. Useful for `m(i, j)` matrix element access                                                      |
| `.arrow(fn)`                                                                 | -                                                     | `void*(U*)`                                   | `obj->member` — smart-pointer arrow. Returns a pointer the IR resolves the following `member` against                                                                  |
| `.copy_assign(fn)`                                                           | -                                                     | `void(U*, U*)`                                | `b = a;` for already-constructed `b`. Lets the type release b's old resources before adopting a's                                                                      |
| `.compare(fn)`                                                               | `.compare_typed<&Fn>()`                               | `int64(U*, U*)` (-1/0/+1)                     | Three-way `<=>`. Single registration auto-derives all six comparison ops                                                                                               |
| `.copy(fn)`                                                                  | `.copy_typed<&Fn>()`                                  | `U*(U*)`                                      | called on `T b = a;` (copy ctor)                                                                                                                                       |
| `.hash(fn)`                                                                  | `.hash_typed<&Fn>()`                                  | `int64(U*)`                                   | map keys, hash\_set                                                                                                                                                    |
| `.serialize(fn)`                                                             | -                                                     | `int64(U*) -> char*`                          | reflection-driven                                                                                                                                                      |
| `.deserialize(fn)`                                                           | -                                                     | `U*(int64 str_ptr)`                           | reflection-driven                                                                                                                                                      |
| `.convert(from_t, fn)`                                                       | -                                                     | `U*(from_T)`                                  | implicit conversion *INTO* this type from `from_T`                                                                                                                     |
| `.cast_to(target_t, fn)`                                                     | -                                                     | `T(U*)`                                       | implicit conversion *FROM* this type to `target_t`. Mirror of `.convert()`. Fires on `cast<T>(obj)` and at variable init when target is a primitive or registered type |
| `.implements(name)`                                                          | -                                                     | -                                             | marks iface compliance                                                                                                                                                 |
| `.as_interface()`                                                            | -                                                     | -                                             | marks type as interface                                                                                                                                                |
| `.generic_param(name)`                                                       | -                                                     | -                                             | template param `T`                                                                                                                                                     |
| `.requires_iface(p, i)`                                                      | -                                                     | -                                             | constraint on `p`                                                                                                                                                      |
| `.pure_methods()`                                                            | -                                                     | -                                             | retention hint (container)                                                                                                                                             |
| `.pure_args()`                                                               | -                                                     | -                                             | retention hint (value-type)                                                                                                                                            |
| `.captures_arg(idx)`                                                         | -                                                     | -                                             | arg `idx` outlives call                                                                                                                                                |
| `.permission(flags)`                                                         | -                                                     | -                                             | `PERM_FFI` / `PERM_FILE`                                                                                                                                               |

### `type_builder` vs `struct_builder`

`struct_builder` is the lightweight form for data-only types (no ctor, no methods):

```cpp
struct_builder(e, "point_t")
    .field("x", type_id::t_int64)
    .field("y", type_id::t_int64)
    .packed()                 // optional; sets packed layout
    .finish();
```

`enum_builder` for enums:

```cpp
enum_builder(e, "log_level")
    .value("DEBUG", 0)
    .value("INFO",  1)
    .value("WARN",  2)
    .value("ERROR", 3)
    .finish();
```

## Interfaces

Native:

```cpp
type_builder(e, "Stream", type_id::t_int64).as_interface();

type_builder(e, "file_stream", type_id::t_int64)
    .factory_typed<&file_create>(1)
    .destructor_typed<&file_destroy>()
    .method_typed<&file_write>("int64 write(string)")
    .implements("Stream")
    .finish();
```

A native with a `Stream` parameter accepts any implementer. The compiler auto-injects the concrete `type_id` before the value at the ABI, so the native signature is `(int64 concrete_tid, int64 value, ...)`.

Resolve a method pointer at runtime:

```cpp
void* fn = enma::interface_method_fn(active_engine(), (type_id)tid, "write");
```

**Script-level iface dispatch:**

```c
Stream s = file_stream("a.txt");   // concrete -> iface
int64 n = s.write("hi");           // dispatches to file_stream.write
s = mem_stream();
int64 m = s.write("hi");           // dispatches to mem_stream.write
```

Each iface-typed local carries a hidden companion int64 holding the concrete tid, updated on every assignment. Runtime resolves fn\_ptr per call.

## Generics + Constraints

```cpp
type_builder(e, "hash_set", type_id::t_int64)
    .generic_param("T")
    .requires_iface("T", "Hashable")    // optional constraint
    .factory_typed<&hset_create>(0)
    .destructor_typed<&hset_destroy>()
    .method("void add(T)", (void*)hset_add)
    .method("bool contains(T)", (void*)hset_contains)
    .finish();
```

Script binds at var-decl:

```c
hash_set<int64> s;   // T = int64
s.add(42);           // checked against T
```

Violations rejected at compile time (wrong type, or T doesn't implement the constrained interface).

## Reflection (`type_reg_t`)

```cpp
const type_reg_t* find_type_reg(engine_t* e, type_id id);
const type_reg_t* find_type_reg_by_name(engine_t* e, const char* name);

const char* type_reg_name(const type_reg_t*);
type_id     type_reg_id(const type_reg_t*);
void*       type_reg_factory(const type_reg_t*);
uint32_t    type_reg_factory_param_count(const type_reg_t*);
void*       type_reg_dtor(const type_reg_t*);
void*       type_reg_copy(const type_reg_t*);
void*       type_reg_hash(const type_reg_t*);
void*       type_reg_compare(const type_reg_t*);
void*       type_reg_op_eq(const type_reg_t*);
void*       type_reg_serialize(const type_reg_t*);
void*       type_reg_deserialize(const type_reg_t*);
void*       type_reg_convert_from(const type_reg_t*, type_id from);
void*       type_reg_method(const type_reg_t*, const char* name);
uint32_t    type_reg_method_count(const type_reg_t*);
const char* type_reg_method_name_at(const type_reg_t*, uint32_t idx);

bool        type_reg_implements(const type_reg_t*, const char* iface);
uint32_t    type_reg_implements_count(const type_reg_t*);
const char* type_reg_implements_at(const type_reg_t*, uint32_t idx);
bool        type_reg_is_interface(const type_reg_t*);

uint32_t    type_reg_generic_param_count(const type_reg_t*);
const char* type_reg_generic_param_at(const type_reg_t*, uint32_t idx);
uint32_t    type_reg_generic_constraint_count(const type_reg_t*);
const char* type_reg_generic_constraint_param_at(const type_reg_t*, uint32_t idx);
const char* type_reg_generic_constraint_iface_at(const type_reg_t*, uint32_t idx);

void*       interface_method_fn(engine_t*, type_id concrete, const char* method);

bool     has_type(engine_t*, const char* name);
uint32_t list_types(engine_t*, std::vector<std::string>& out);
bool     has_struct(engine_t*, const char* name);
uint32_t list_structs(engine_t*, std::vector<std::string>& out);
```

All accessors are null-safe. `nullptr` returns `0` / `""` / `false`.

## Introspection

```cpp
bool     has_function(module_t*, const char* name);
uint32_t function_param_count(module_t*, const char* name);
uint32_t function_count(module_t*);
void     list_functions(module_t*, std::vector<std::string>& out);

char*    tokenize_dump(engine_t*, const char* src, size_t len, const char* file);
char*    ir_dump(engine_t*, const char* src, size_t len, const char* file);
void     free_string(char* str);   // free result of above

// Annotations [[...]] in source:
uint32_t get_annotated_functions(module_t*, const char* annotation, std::vector<std::string>& out);
uint32_t get_annotations(module_t*, const char* fn, std::vector<annotation_info>& out);
```

`annotation_info { const char* name; const char** args; uint32_t arg_count; }`.

## Per-Context Helpers (for addon authors)

Called from a native executing inside `execute()`/`call()`:

```cpp
engine_t*  active_engine();    // engine driving this execute; nullptr outside
context_t* active_context();   // context driving this execute; nullptr outside

uint64_t random_u64();
double   random_double();
int64_t  random_int_range(int64_t lo, int64_t hi);
void     random_seed(uint64_t seed);
```

All read per-thread TLS set by `execute()`, so they're thread-safe across concurrent engines.

## Heap + Weak References

```cpp
void*    heap_alloc(size_t size);
void*    heap_realloc(void* ptr, size_t new_size);
void     heap_free(void* ptr);
bool     heap_is_tracked(void* ptr);
void     heap_collect(module_t* m);                 // no-op, deterministic model
heap_stats heap_get_stats(module_t* m);
void     heap_set_memory_budget(module_t* m, size_t bytes);

// Weak-reference primitive: shared uint64 token tied to the allocation.
// Non-zero while alive, 0 after heap_free. Same pointer for repeat calls.
// Tokens are never freed (weak-ref wrappers may outlive the target).
uint64_t* alive_token(void* ptr);
```

`heap_stats { alloc_count, total_bytes, freed_count, freed_bytes }` - all `uint64_t`.

## Event API (context-scoped, int64 IDs → int64 fn refs)

```cpp
void register_event(context_t*, int64_t event_id, int64_t callback);
void fire_event(context_t*, int64_t event_id);
void clear_events(context_t*);
```

## Exceptions

```cpp
bool    exception_pending(module_t* m);
int64_t exception_value(module_t* m);
int64_t exception_type(module_t* m);      // type hash of the thrown value
void    exception_clear(module_t* m);
```

Raise from native:

```cpp
void runtime_error(const char* msg);       // maps to execute()→false
void runtime_exception(const char* msg);   // throws, catchable by script try/catch
```

## Debug + Budget

```cpp
void set_budget(module_t* m, int64_t instructions);   // 0 = disabled
void set_debug_hook(module_t* m, void(*hook)(const char* file, uint32_t line, int64_t* frame));

struct stack_frame { const char* function; const char* file; uint32_t line; };
uint32_t get_stack_trace(context_t* ctx, stack_frame* out, uint32_t max);

int64_t get_last_executed_line(module_t* m);   // crash diagnostic
```

`set_debug(e, true)` is required for meaningful stack traces and line mapping. Must be called BEFORE compile so `op_debug_line` instructions are emitted.

## IDE debugger SDK

For IDEs that need breakpoints, stepping, and local-variable inspection. All opt-in via `set_debug(true)`. When off, none of these code paths fire (zero cost).

For full debugger fidelity (locals visible in their declared frame slots) you should ALSO disable optimization: `set_optimize(e, false)`. Otherwise the optimizer promotes locals to registers and they never land in their declared slots.

```cpp
// Source map / function lookup
struct em_debug_fn_t;   // opaque
const em_debug_fn_t* find_fn_at(module_t*, const char* file, uint32_t line);
const char* debug_fn_name        (const em_debug_fn_t*);
uint32_t    debug_fn_local_count (const em_debug_fn_t*);
uint32_t    debug_fn_param_count (const em_debug_fn_t*);

void find_code_offsets(module_t*, const char* file, uint32_t line,
                       size_t* out_offsets, uint32_t* out_count, uint32_t max);

// Local readback. frame is the rbp the hook receives.
struct em_local_info { const char* name; type_id type; uint32_t slot; };
uint32_t enumerate_locals(const em_debug_fn_t*, em_local_info* out, uint32_t max);

int64_t     read_local_int    (int64_t* frame, uint32_t slot);
double      read_local_float  (int64_t* frame, uint32_t slot);
const char* read_local_string (int64_t* frame, uint32_t slot);
void*       read_local_pointer(int64_t* frame, uint32_t slot);

// Breakpoints (per module).
int32_t set_breakpoint    (module_t*, const char* file, uint32_t line);
void    clear_breakpoint  (module_t*, int32_t bp_id);
void    enable_breakpoint (module_t*, int32_t bp_id, bool enabled);
bool    is_breakpoint_at  (module_t*, const char* file, uint32_t line);

struct em_breakpoint_info { int32_t id; const char* file; uint32_t line; bool enabled; };
uint32_t list_breakpoints(module_t*, em_breakpoint_info* out, uint32_t max);

// Stepping (per context). Multi-thread routines get independent state.
enum class step_mode : int32_t { step_none, step_over, step_in, step_out };
void      set_step_mode           (context_t*, step_mode);
step_mode get_step_mode           (context_t*);
void      set_step_baseline_depth (context_t*, int32_t depth);
int32_t   get_step_baseline_depth (context_t*);
int32_t   get_call_depth          (int64_t* frame, module_t*);

// Pause / resume (per context).
void request_pause       (context_t*);
void resume              (context_t*);
bool is_pause_requested  (context_t*);

// Convenience: combines breakpoint + pause + step logic. Returns true if
// the host hook should pause execution at this line.
bool should_pause_at(context_t*, module_t*, int64_t* frame,
                      const char* file, uint32_t line);
```

Typical IDE pattern inside the debug hook:

```cpp
void on_line(const char* file, uint32_t line, int64_t* frame) {
    context_t* ctx = active_context();
    module_t* mod = ...;
    if (should_pause_at(ctx, mod, frame, file, line)) {
        // 1. Notify IDE: paused at file:line
        // 2. Inspect locals
        auto* fn = find_fn_at(mod, file, line);
        em_local_info infos[64];
        uint32_t n = enumerate_locals(fn, infos, 64);
        for (uint32_t i = 0; i < n; ++i) {
            switch (infos[i].type) {
                case type_id::t_int64: read_local_int(frame, infos[i].slot); break;
                case type_id::t_string: read_local_string(frame, infos[i].slot); break;
                /* ... */
            }
        }
        // 3. Wait for IDE command (continue / step / etc.)
        // 4. Before returning to script:
        //    set_step_baseline_depth(ctx, get_call_depth(frame, mod));
        //    set_step_mode(ctx, step_mode::step_over);
        //    resume(ctx);   // clears pause_requested
    }
}
```

## Error Handling

```cpp
struct error_info {
    int         code;
    std::string message;
    std::string file;
    uint32_t    line;
    uint32_t    column;
};

error_info  last_error(engine_t*);
const char* last_error_message(engine_t*);
```

Error codes are set on `compile()` / `execute()` failure. Codes: `0` = ok; non-zero = fail. `message` + `file:line:column` pinpoint the problem.

## Built-in Addons (registration)

```cpp
void register_all_addons(engine_t*);   // registers everything below

void register_addon_core(engine_t*);        // print / println
void register_addon_string(engine_t*);      // string methods
void register_addon_array(engine_t*);       // array methods
void register_addon_map(engine_t*);         // map methods
void register_addon_math(engine_t*);        // scalar math + vec2/3/4 + quat + mat4
void register_addon_simd(engine_t*);        // SSE2 memops, packed ops (stride 1/2/4/8)
void register_addon_variant(engine_t*);     // open tagged union
void register_addon_atomic(engine_t*);      // atomic_int32/64
void register_addon_bits(engine_t*);        // popcount/clz/ctz/rotl/rotr/bswap
void register_addon_time(engine_t*);        // time_ms, calendar
void register_addon_regex(engine_t*);       // regex type
void register_addon_file(engine_t*);        // needs PERM_FILE
void register_addon_hash_set(engine_t*);    // hash_set<T>
void register_addon_sorted_map(engine_t*);  // sorted_map<K,V>
void register_addon_thread(engine_t*);      // mutex, cond_var, lock_guard
void register_addon_json(engine_t*);        // json_parse, json_value
void register_addon_list(engine_t*);        // list<T>
```

## Building a Custom Addon

### Stateless functions

```cpp
int32_t square(int32_t x) { return x * x; }

void register_addon_mymath(engine_t* e) {
    register_typed<&square>(e, "int32 square(int32)");
}
```

### A new custom type

```cpp
struct color_t { uint8_t r, g, b, a; };

color_t* color_create(int32_t r, int32_t g, int32_t b, int32_t a) {
    auto* c = static_cast<color_t*>(heap_alloc(sizeof(color_t)));
    c->r = (uint8_t)r; c->g = (uint8_t)g; c->b = (uint8_t)b; c->a = (uint8_t)a;
    return c;
}
void     color_destroy(color_t* c) { heap_free(c); }
int64_t  color_to_hex(color_t* c)  { return (c->r << 24) | (c->g << 16) | (c->b << 8) | c->a; }
color_t* color_blend(color_t* a, color_t* b) {
    return color_create((a->r + b->r) / 2, (a->g + b->g) / 2,
                        (a->b + b->b) / 2, (a->a + b->a) / 2);
}
bool     color_eq(color_t* a, color_t* b) {
    return a->r == b->r && a->g == b->g && a->b == b->b && a->a == b->a;
}
color_t* color_add(color_t* a, color_t* b) {
    return color_create(std::min(255, a->r + b->r), std::min(255, a->g + b->g),
                        std::min(255, a->b + b->b), std::min(255, a->a + b->a));
}

void register_addon_color(engine_t* e) {
    type_builder(e, "color_t", type_id::t_int64)
        .factory_typed<&color_create>(4)
        .destructor_typed<&color_destroy>()
        .method_typed<&color_to_hex>("int64 to_hex()")
        .method_typed<&color_blend>("color_t blend(color_t)")
        .bin_eq_typed<&color_eq>()
        .bin_add_typed<&color_add>()
        .finish();
}
```

Use from script:

```c
color_t c = color_t(255, 128, 0, 255);
int64 h  = c.to_hex();
color_t d = c + color_t(0, 128, 128, 0);
```

### Weak references in an addon

```cpp
struct weak_ref { uint64_t* tok; void* ptr; };

int64_t weak_make(int64_t target) {
    auto* w = static_cast<weak_ref*>(heap_alloc(sizeof(weak_ref)));
    w->ptr = reinterpret_cast<void*>(target);
    w->tok = alive_token(w->ptr);        // lazy token per allocation
    return reinterpret_cast<int64_t>(w);
}
bool weak_alive(weak_ref* w) { return w && w->tok && *w->tok != 0; }
int64_t weak_get(weak_ref* w) {
    if (!weak_alive(w)) return 0;
    return reinterpret_cast<int64_t>(w->ptr);
}
```

## Thread Safety

* Engines are independent, no shared mutable state. Separate threads → separate engines.
* Multiple contexts off the same module can execute concurrently.
* Per-thread TLS heap. `execute()` sets TLS before running and restores on exit.
* All `active_*` / `random_*` / `alive_token` helpers are thread-safe.
* Tested under ASAN/TSAN with 32+ threads.

## Safety Layers

* **Fault trapping**: JIT null-deref, out-of-bounds, use-after-free caught by the runtime fault handler. `execute()` returns `false`, host process stays alive.
* **Execution budget**: `set_budget(mod, N)` halts after N loop iterations.
* **Memory budget**: `heap_set_memory_budget(mod, bytes)` caps live heap.
* **Permissions**: `PERM_FFI` / `PERM_FILE` - scripts fail to compile calls without the permission.
* **Sandboxing**: scripts see only what you register. Default addons minimal; skip `register_addon_file`, don't grant `PERM_FFI`, register only your native functions.
* **Type verification**: every native call-site checks arg types, struct identity, enum identity, typed-container element types at compile.

## Scripts Ship As

* `.em` source: compile at startup with `compile`.
* `.emb` binary: `serialize()` after compile, `deserialize()` on next run. Faster startup; binary may become incompatible with SDK upgrades that change IR.

## Cheat Sheet

```cpp
// minimum
engine_t* e = create(); register_all_addons(e);
module_t* m = compile(e, src, len, "x.em");
context_t* c = create_context(m);
execute(c, "main");
int64_t r = return_value(c);
destroy_context(m, c); module_destroy(m); destroy(e);

// args
int64_t a[] = { 1, 2 };
call(c, "add", a, 2);

// userdata
set_userdata_at(c, 3, &my_state);
// inside native:
auto* s = static_cast<MyState*>(get_userdata_at(active_context(), 3));

// native fn
register_typed<&my_fn>(e, "int64 my_fn(int64, int64)");

// custom type
type_builder(e, "my_t", type_id::t_int64)
    .factory_typed<&my_create>(1)
    .destructor_typed<&my_destroy>()
    .method_typed<&my_method>("int64 method()")
    .finish();

// globals
set_global(m, "config_level", 5);

// serialization
std::vector<uint8_t> bin; serialize(m, bin);
module_t* m2 = deserialize(e, bin.data(), bin.size());

// errors
if (!compile(e, src, len, "f.em")) {
    auto err = last_error(e);
    fprintf(stderr, "%s at %s:%d:%d\n", err.message.c_str(), err.file.c_str(), err.line, err.column);
}
```

## Pitfalls

* `register_typed<&Fn>` only handles arity ≤ 6. More args → manual `register_native` with int64 ABI.
* Floats passed via `call(ctx, ...)` must be bit-cast to int64. Same for return (`return_float` bit-casts back).
* Pointer/handle args must be valid at call time, the SDK does not track ownership across the boundary. Prefer heap-owned values when crossing repeatedly.
* `destroy_context` requires the module pointer. Don't destroy the module before its contexts.
* `register_all_addons` grants nothing special. `PERM_FILE` is separate from registration. File addon calls fail to compile without the permission.
* Calling a script function before compile succeeded = undefined behavior. Always check `compile` return.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/llms-sdk.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/quick-access.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/quick-access.md).

# Quick Access

[**Basics**](lang-basics.md) - Types, variables, constants, operators, control flow

[**Functions**](lang-functions.md)- Parameters, defaults, ref/out, variadic, lambdas, closures

[**Pointers**](lang-pointers.md) - Heap pointers, address-of, `.`/`->`, refs, null, escape rules

[**Structs & Classes**](lang-structs-and-classes.md) - Value types, reference types, inheritance, interfaces, operator overloading

[**Templates**](lang-templates.md) - Generic structs and functions, monomorphization

[**Advanced**](lang-advanced.md) - Delegates, namespaces, coroutines, exceptions, heap ops, FFI, static\_assert, constexpr / compile-time evaluation

[**Annotations**](lang-annotations.md) - noescape, packed, align, reflect, serialize, export, noopt, dll, custom

[**Modules** ](lang-modules.md)- import, .emb precompiled binaries, linking

[**Preprocessor** ](lang-pre-processor.md)- #define, #ifdef, #include

### SDK Guide

[**Quick Start**](sdk-quick-start.md) - Minimal embed example

[**Engine Lifecycle**](sdk-engine-lifecycle.md) - create, configure, destroy

[**Compilation** ](sdk-compilation.md)- Compile from source or file

[**Execution**](sdk-execution.md) - Contexts, execute, return values

[**Calling Functions**](sdk-calling-functions.md) - Pass arguments, strings, floats

[**Globals**](sdk-globals.md) - Set, get, list, direct pointer access

[**Type Registration**](sdk-type-registration.md) - Full type\_builder API with fields, methods, operators, subscript, iteration

[**Native Functions**](sdk-native-functions.md) - Register host functions callable from scripts

[**Hot Reload** ](sdk-hot-reload.md)- Replace script code at runtime

[**Serialization & Linking**](sdk-serialization-and-linking.md) - .emb binaries, multi-module linking

[**Introspection**](sdk-introspection.md) - List functions, query annotations, IR dump

[**Lifecycle & RAII**](sdk-lifecycle.md) - Memory model, scope-drop, destructors, escape rules

[**Debug & Heap**](sdk-debug-and-gc.md) - Debug hooks, execution budget, heap stats

[**Error Handling**](sdk-error-handling.md) - Compile and runtime error reporting

[**Safety**](sdk-safety.md) - Fault trapping, sandboxing, permissions, threading

[**Custom Addons** ](sdk-custom-addons.md)- Build your own addon from scratch

[**API Reference**](sdk-api-reference.md) - Every SDK function in one page

### Pre-built Addons

[**Core**](addon-core.md) - Output (print functions for ints, floats, strings, bools, chars)

[**Strings** ](addon-strings.md)- String methods and standalone string functions

[**Arrays** ](addon-arrays.md)- Array methods for manipulation, search, sorting, iteration

[**Maps** ](addon-maps.md)- Map creation, access, iteration methods

[**Math** ](addon-math.md)- Trigonometry, power, rounding, float/int utilities, constants, random

[**SIMD** ](addon-simd.md)- SSE2 vector arithmetic + packed ops on stride-1/2/4 arrays (int8/16/32, float32), bitwise

[**Variant** ](addon-variant.md)- Open tagged union keyed by type\_id; holds any registered type

[**Atomic** ](addon-atomic.md)- `atomic_int32` / `atomic_int64` + memory barriers

[**Bits** ](addon-bits.md)- popcount, clz, ctz, rotl, rotr, bswap, parity, bit\_reverse

[**Time** ](addon-time.md)- µs-since-epoch, calendar, ISO 8601, sleep, arithmetic

[**Regex** ](addon-regex.md)- matches, find, first, find\_all, replace, split, groups

[**File** ](addon-file.md)- `file_t` + free fns (gated by `PERM_FILE`)

[**Thread** ](addon-thread.md)- mutex, lock\_guard, cond\_var

[**Vectors** ](addon-vec.md)- vec2 / vec3 / vec4 with operators + scalar helpers

[**hash\_set\<T>** ](addon-hash_set.md)- generic hashed set for scalar T

[**sorted\_map\<K,V>** ](addon-sorted_map.md)- generic ordered map for scalar K/V

[**list\<T>** ](addon-list.md)- generic double-ended container; O(1) push/pop both ends, random access

[**JSON** ](addon-json.md)- parse, stringify, navigable `json_value` tree


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/quick-access.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/readme.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/readme.md).

# Introduction - Enma

Enma is a full-module AOT and JIT-compiled scripting language targeting x64. Compiles to native machine code through an optimizing pipeline. Designed to embed in native applications.

```cpp
int32 fib(int32 n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}

int32 main() {
    println(fib(30));
    return 0;
}
```

### Features

**Primitives:** `bool`, `char`, `wchar`, `int8`/16/32/64, `uint8`/16/32/64, `aint8`/16/32/64 (atomic), `float32`, `float64`, `string`, `wstring`, `void`, `null`, `auto`

**Variables:** `const`, `constexpr`, `nullable`, `auto` inference

**Operators:** arithmetic, comparison, logical, bitwise, compound assign (`+=` etc.), `++`/`--`, ternary, `cast<T>()`, `sizeof`, `offsetof`

**Control flow:** `if`/`else`, `while`, `do-while`, `for`, `for-each`, `switch`, `match`, `break`, `continue`, `goto`, `defer`

**Functions:** default args, reference (`&`), out (`out`), variadic (`...` + `__va_count` / `__va_arg`), `extern`, `const` methods, function references

**Lambdas:** `[caps](p) -> T { }` and arrow `(p) => expr`

**Arrays:** dynamic with `push`/`pop`/`insert`/`remove`/`sort`/`reverse`/`contains`/`index_of`/`slice`/`join`/iteration; brace init; typed `T[]`

**Maps:** key-value with `get`/`set`/`contains`/`remove`/`length`/iteration; typed `map<K,V>`

**Strings:** interpolation `f"v={x}"`, concat with `+`, methods: `length`, `substr`, `find`, `contains`, `starts_with`, `ends_with`, `char_at`, `to_int`, `to_float`, `to_upper`, `to_lower`, `trim`, `replace`, `split`, `repeat`

**Structs:** value types, fields, ctor, dtor, methods, operator overloading, bitfields, packed/aligned

**Classes:** reference types, multi-inheritance (no virtual / no diamonds), implicit virtual dispatch with vtable thunks for non-primary base overrides, `override`, RAII

**Interfaces:** abstract method contracts

**Mixins:** add methods externally

**Properties:** getter/setter syntax

**Templates:** generic structs and functions, monomorphization, reference params, nesting

**Enums:** `Enum::Value` access with preserved identity

**Typedefs:** `using Alias = Type` or `typedef Type Alias`

**Delegates:** typed function references

**Namespaces:** `namespace`, `using namespace`, `::`

**Coroutines:** `coroutine` + `yield`, driven via `coroutine_t.next()` / `value()`

**Exceptions:** `try`/`catch`/`throw` with stack unwinding, dtors and `defer` run during unwind

**Heap allocation:** `new T(args)`, `new T[N]`, `new T[N](ctor_args)`, `delete`, `delete[]`

**Inline asm intrinsics:** `__asm_rdtsc`, `__asm_pause`, `__asm_mfence`, `__asm_nop`

**Annotations:** `[[packed]]`, `[[align(N)]]`, `[[reflect]]`, `[[serialize]]`, `[[export]]`, `[[noopt]]`, `[[noinline]]`, `[[inline]]`, `[[dll(...)]]` (FFI), custom annotations queryable from host

**Modules:** `import` with aliasing, precompiled `.emb`, source fallback, multi-module linking

**Preprocessor:** `#define`/`#undef`, `#ifdef`/`#ifndef`/`#elif`/`#else`/`#endif`, `#include`, `#pragma`

**FFI:** `[[dll("lib.so")]]` gated by `PERM_FFI`

**Static assert:** `static_assert(expr, "message")`

**SDK:** C++ embedding API. Type registration with fields, methods, properties, subscript, iteration, factory, destructor, full operator set (arithmetic, comparison, three-way `compare()`, compound assign, ++/--, bitwise), implicit conversion, hash, copy. Typed `_typed<&Fn>` wrappers for every hook. Interfaces with auto-injected `type_id`. Generic type parameters with interface constraints (`.requires_iface`). Native function binding with sig strings supporting `array<T>`, `map<K,V>`, `const T&`, default args, variadic, overloading by arity / types / element type. Hot reload, serialization, introspection, debug hooks, sandboxing, permission gating.

### Current Benchmark

Median of 11 runs, Windows x64. Six workloads: `fib(35)`, `sum 100M`, `nested 2K²`, `sieve 1M`, `collatz 100K`, `bubble 3K`. Pure execution time (script-internal `time_ms()`).

| Benchmark    | Rust -O | C++ -O2 | **Enma** | Node V8 | LuaJIT | Lua 5.4 | AngelScript |
| ------------ | ------- | ------- | -------- | ------- | ------ | ------- | ----------- |
| fib(35)      | 14.9    | 11.3    | **26**   | 44.9    | 50     | 316     | 444.8       |
| sum 100M     | 21.5    | 9.1     | **20**   | 52.9    | 51     | 208     | 537.8       |
| nested 2K²   | 0.8     | 9.9     | **1**    | 2.5     | 2      | 8       | 19.1        |
| sieve 1M     | 0.6     | 10.9    | **6**    | 4.5     | 6      | 30      | 30.4        |
| collatz 100K | 6.5     | 10.2    | **25**   | 13.3    | 31     | 147     | 156.7       |
| bubble 3K    | 1.7     | 9.6     | **11**   | 5.0     | 2      | 55      | 159.8       |
| **Total**    | 46.0    | 61.0    | **89**   | 123.1   | 142    | 764     | 1348.6      |

Matches or beats LuaJIT on 5/6 workloads (only bubble trails).

### Safety

**Fault trapping:** Null deref, invalid memory access caught via SIGSEGV/SEH and mapped to source. Host doesn't crash.

**Execution budget:** Per-loop instruction count via `set_budget()`. Prevents infinite loops.

**Memory budget:** Cap total allocations with `set_memory_budget()`.

**Permission gating:** `PERM_FFI` controls `[[dll(...)]]` access; `PERM_FILE` controls file-addon calls; per-method permissions on registered types.

**Sandboxing:** Scripts only see functions explicitly registered by the host.

**Type verification:** Native sig types checked at script call sites: wrong arg type, wrong struct identity, wrong enum, or wrong container element type are all rejected at compile time. Const correctness for parameters and methods. Implicit conversion via registered `convert_from` functions.

**Memory model:** Deterministic. Structs stack-allocated by default; `new T(...)` for explicit heap. Destructors run at scope exit (normal flow, exception unwind, JIT fault unwind). No tracing GC. Escape patterns (return pointer to stack struct, store to struct-typed global, closure capturing a stack struct) are compile errors.

**Thread safety:** Per-thread TLS, independent engines, concurrent contexts from same module. Tested under ASAN/TSAN with 32+ threads.

### Getting Started

Writing scripts: [basics](lang-basics.md)

Embedding: [SDK Quick Start](sdk-quick-start.md)


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/readme.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-api-reference.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/api-reference.md).

# API Reference

All functions are in the `enma` namespace.

### Engine

| Function                | Signature                                                          | Description                                                                                                                                                                       |
| ----------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `create`                | `engine_t* create()`                                               | Create a new engine instance                                                                                                                                                      |
| `destroy`               | `void destroy(engine_t*)`                                          | Destroy engine and free resources                                                                                                                                                 |
| `shutdown`              | `void shutdown()`                                                  | One-shot process-global teardown - removes the runtime fault handler before a DLL hosting enma unloads. Call once from `DllMain` `DLL_PROCESS_DETACH`. Safe with no live engines. |
| `set_optimize`          | `void set_optimize(engine_t*, bool)`                               | Enable/disable optimizer (default: on, set by `create()`)                                                                                                                         |
| `set_debug`             | `void set_debug(engine_t*, bool)`                                  | Enable/disable debug info                                                                                                                                                         |
| `define`                | `void define(engine_t*, const char* name, const char* value)`      | Set preprocessor define                                                                                                                                                           |
| `add_include_path`      | `void add_include_path(engine_t*, const char*)`                    | Add `#include` search path                                                                                                                                                        |
| `add_module_path`       | `void add_module_path(engine_t*, const char*)`                     | Add `import` search path                                                                                                                                                          |
| `set_permissions`       | `void set_permissions(engine_t*, uint32_t)`                        | Set permission flags                                                                                                                                                              |
| `get_permissions`       | `uint32_t get_permissions(engine_t*)`                              | Get current permission flags                                                                                                                                                      |
| `set_include_resolver`  | `void set_include_resolver(engine_t*, resolve_fn, void* userdata)` | Override `#include` file resolution                                                                                                                                               |
| `set_import_resolver`   | `void set_import_resolver(engine_t*, resolve_fn, void* userdata)`  | Override `import` module resolution                                                                                                                                               |
| `set_global_allocators` | `void set_global_allocators(allocators)`                           | Override module/runtime allocator pair (set before `create()`)                                                                                                                    |
| `get_global_allocators` | `allocators get_global_allocators()`                               | Read current global allocator pair                                                                                                                                                |
| `set_stack_allocators`  | `void set_stack_allocators(allocators)`                            | Override per-context JIT stack allocator pair (set before `create_context` with non-zero stack\_size)                                                                             |
| `get_stack_allocators`  | `allocators get_stack_allocators()`                                | Read current stack allocator pair                                                                                                                                                 |

### Compilation

| Function         | Signature                                                                         | Description                       |
| ---------------- | --------------------------------------------------------------------------------- | --------------------------------- |
| `compile`        | `module_t* compile(engine_t*, const char* src, size_t len, const char* filename)` | Compile source to module          |
| `compile_file`   | `module_t* compile_file(engine_t*, const char* path)`                             | Compile file to module            |
| `module_destroy` | `void module_destroy(module_t*)`                                                  | Destroy compiled module           |
| `reload`         | `bool reload(module_t*, const char* src, size_t len, const char* filename)`       | Hot-reload module with new source |

### Execution

| Function          | Signature                                                                         | Description                                                                                                                                                                                                                                |
| ----------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `create_context`  | `context_t* create_context(module_t*, size_t stack_size = 0)`                     | Create execution context. `stack_size > 0` allocates a separate JIT stack via the stack allocator (caveat: breaks C++ EH unwinding across the JIT boundary). Default 0 uses the OS thread stack.                                           |
| `destroy_context` | `void destroy_context(module_t*, context_t*)`                                     | Destroy execution context                                                                                                                                                                                                                  |
| `execute`         | `bool execute(context_t*, const char* fn_name)`                                   | Execute a function by name                                                                                                                                                                                                                 |
| `call`            | `bool call(context_t*, const char* fn_name, const int64_t* args, uint32_t count)` | Call function with arguments                                                                                                                                                                                                               |
| `return_value`    | `int64_t return_value(context_t*)`                                                | Get integer return value                                                                                                                                                                                                                   |
| `return_string`   | `const char* return_string(context_t*)`                                           | Get string return value                                                                                                                                                                                                                    |
| `return_float`    | `double return_float(context_t*)`                                                 | Get float return value                                                                                                                                                                                                                     |
| `alloc_string`    | `int64_t alloc_string(context_t*, const char*)`                                   | Allocate heap string for passing to scripts                                                                                                                                                                                                |
| `set_userdata`    | `void set_userdata(context_t*, void*)`                                            | Attach userdata (slot 0)                                                                                                                                                                                                                   |
| `get_userdata`    | `void* get_userdata(context_t*)`                                                  | Retrieve slot 0 userdata                                                                                                                                                                                                                   |
| `set_userdata_at` | `void set_userdata_at(context_t*, uint32_t slot, void*)`                          | Attach userdata to slot (0-15)                                                                                                                                                                                                             |
| `get_userdata_at` | `void* get_userdata_at(context_t*, uint32_t slot)`                                | Retrieve slot userdata                                                                                                                                                                                                                     |
| `fn_address`      | `void* fn_address(module_t*, const char* name)`                                   | Get raw JIT function pointer for direct calls                                                                                                                                                                                              |
| `execution_scope` | `execution_scope scope(context_t*);` (RAII)                                       | Set up per-thread TLS (heap, runtime\_state, engine, events, rng, JIT range, active context) for the lifetime of the scope. Required around any closure invocation from a thread that isn't already inside `execute()`/`call()`. Nestable. |

### Globals

| Function         | Signature                                                         | Description                          |
| ---------------- | ----------------------------------------------------------------- | ------------------------------------ |
| `set_global`     | `bool set_global(module_t*, const char* name, int64_t value)`     | Set global variable                  |
| `get_global`     | `int64_t get_global(module_t*, const char* name)`                 | Get global variable                  |
| `has_global`     | `bool has_global(module_t*, const char* name)`                    | Check if global exists               |
| `get_global_ptr` | `int64_t* get_global_ptr(module_t*, const char* name)`            | Get direct pointer to global storage |
| `list_globals`   | `void list_globals(module_t*, vector<string>&, vector<int64_t>&)` | List all globals                     |

### Native Registration

| Function                     | Signature                                                                                                                                                                    | Description                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `register_native`            | `void register_native(engine_t*, const char* signature, void* fn, uint32_t perm = 0, const char* description = nullptr)`                                                     | Signature string form with inline name (preferred), e.g. `"float64 pow(float64, float64)"`. Optional description surfaces via `extract_documentation`.                                                                                                                                                                                                                                                                                    |
| `register_native`            | `void register_native(engine_t*, const char* name, const char* signature, void* fn, uint32_t perm = 0, const char* description = nullptr)`                                   | Signature string form, name separate                                                                                                                                                                                                                                                                                                                                                                                                      |
| `register_native`            | `void register_native(engine_t*, const char* name, void* fn, type_id ret, const native_param* params, uint32_t count, uint32_t perm = 0, const char* description = nullptr)` | `native_param` array form                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `register_typed<&fn>`        | `void register_typed<&fn>(engine_t*, const char* signature, uint32_t perm = 0)`                                                                                              | Thin template wrapper around `register_native(engine, sig, (void*)Fn)`. The native is called directly via Win64 ABI; no trampoline, no int64 bit-casting. Any arity, any type mix.                                                                                                                                                                                                                                                        |
| `register_natives`           | `void register_natives(engine_t*, const native_desc* descs, uint32_t count)`                                                                                                 | Batch-register via descriptor array                                                                                                                                                                                                                                                                                                                                                                                                       |
| `register_module`            | `void register_module(engine_t*, const char* name, const char* source)`                                                                                                      | Register a built-in Enma module so scripts can `import "<name>";`. NO COPY — the engine stores a view into `source`, which MUST outlive the engine (typically a `static const char* k_foo_src = R"(...)";` literal). Resolution order at import: built-in modules → host `import_resolve` callback → `module_paths` filesystem search. See [Custom Addons → Source-level modules](sdk-custom-addons.md#source-level-modules). |
| `mark_native_returns_borrow` | `void mark_native_returns_borrow(engine_t*, const char* name)`                                                                                                               | Mark a native fn as returning a borrowed (non-owning) handle. The compiler skips scope-end dtor for `T x = fn();`. Required when the native returns a handle owned by the engine/host.                                                                                                                                                                                                                                                    |
| `ENMA_SIG(s)`                | `consteval` macro wrapping a sig literal                                                                                                                                     | Compile-time syntax validator; invalid sigs fail via `static_assert`                                                                                                                                                                                                                                                                                                                                                                      |

Signature strings support:

* **Arity + type overloading**: register multiple natives with the same name; call site picks best match. Includes element-type dispatch for typed containers.
* **Variadic**: end with `...` to pass `(int64_t argc, int64_t* argv)` to the native.
* **Default args**. `"int64 f(int64 a, int64 b = 10)"`.
* **Struct args by value / ref / ptr**. `T`, `T&`, `T*`.
* **Const params**. `const T`, `const T&` rejects assignment-through-const in callee.
* **Typed containers**. `array<T>`, `map<K, V>` checked at script call sites and var-decl assignments.
* **Enum-typed args**: compile error on raw int or cross-enum.
* **Delegate names**: script-declared delegates resolved lazily.
* **Custom struct / type\_builder names**: compile error on mismatched name.

### Type Builder

| Method                                                                                                          | Description                                                                                                                                                                                                                                |
| --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `type_builder(engine_t*, const char* name, type_id id)`                                                         | Start building a type                                                                                                                                                                                                                      |
| `type_builder(engine_t*, const char* name, type_id id, const char* description)`                                | Start building a type with a docs description                                                                                                                                                                                              |
| `.field(name, offset, type)` / `.field(name, offset, type, description)`                                        | Add a field, optionally with a description                                                                                                                                                                                                 |
| `.method_typed<&Fn>(signature)`                                                                                 | **Typed wrapper** - write the method with real types. Forwards to `.method(sig, (void*)Fn)`; the native is called directly via Win64 ABI. Any arity, any type mix.                                                                         |
| `.method(signature, fn)` / `.method(signature, fn, description)`                                                | Signature string + raw `int64_t`-ABI fn, optionally with a description                                                                                                                                                                     |
| `.method(name, signature, fn)`                                                                                  | Signature string, name separate                                                                                                                                                                                                            |
| `.method(name, fn, ret, {arg_types...}, elem_ret?)`                                                             | Typed arg list form                                                                                                                                                                                                                        |
| `.method(name, fn, ret, param_count, elem_ret?)`                                                                | Count-based form (no per-arg type check)                                                                                                                                                                                                   |
| `.property(name, getter, setter, type)` / `.property(name, getter, setter, type, description)`                  | Add a property, optionally with a description                                                                                                                                                                                              |
| `.property_typed<&Get, &Set>(name, type)`                                                                       | **Typed wrapper** - property with real types; default `Set = nullptr` = read-only                                                                                                                                                          |
| `.inline_property(name, getter, setter, type, byte_offset)`                                                     | Fast-path property — compiler emits `op_load_field` / `op_store_field` at the given offset instead of `call_native`. Use for trivial field accessors. Native fns stay registered as fallbacks.                                             |
| `.value_type(byte_size)`                                                                                        | Opt this typereg into value-type semantics. Non-escaping locals stack-allocate; `T[]` stores values inline (`byte_size` per slot). Requires the C struct to be POD-shaped. Pair with `.factory_in_place(...)` and `.inline_property(...)`. |
| `.factory_in_place(fn)`                                                                                         | Write-into-buffer ctor: `int64_t fn(int64_t dst, args...)`. Used when the typereg is `.value_type`-marked; skips the per-instance `heap_alloc`. Regular `.factory(...)` still fires for explicit `new T(...)`.                             |
| `.subscript_typed<&Get, &Set>(elem_ret?)`                                                                       | **Typed wrapper** - subscript with real types; default `Set = nullptr` = read-only                                                                                                                                                         |
| `.factory_typed<&Fn>(param_count)`                                                                              | **Typed wrapper** - factory with real arg types                                                                                                                                                                                            |
| `.factory(fn, param_count)`                                                                                     | Set constructor (raw `int64_t` ABI)                                                                                                                                                                                                        |
| `.factory(fn, {arg_types...})` / `.factory(fn, {arg_types...}, description)`                                    | Typed arg list form, optionally with a description                                                                                                                                                                                         |
| `.destructor_typed<&Fn>()`                                                                                      | **Typed wrapper** - destructor takes typed pointer                                                                                                                                                                                         |
| `.destructor(fn)` / `.destructor(fn, description)`                                                              | Set scope-drop destructor (raw), optionally with a description                                                                                                                                                                             |
| `.pure_methods()`                                                                                               | Methods don't retain receiver (container types)                                                                                                                                                                                            |
| `.pure_args()`                                                                                                  | Methods don't retain any argument (value types)                                                                                                                                                                                            |
| `.subscript(get_fn, set_fn)`                                                                                    | Enable `[]` access                                                                                                                                                                                                                         |
| `.iterable(len_fn, get_fn)`                                                                                     | Enable `for (v : obj)`                                                                                                                                                                                                                     |
| `.kv_iterable(len_fn, key_fn, val_fn)`                                                                          | Enable `for (k, v : obj)`                                                                                                                                                                                                                  |
| `.init_push(fn)`                                                                                                | Enable brace initialization                                                                                                                                                                                                                |
| `.bin_add(fn)` ... `.bin_mod(fn)`                                                                               | `+ - * / %` operators                                                                                                                                                                                                                      |
| `.bin_eq(fn)` `.bin_lt(fn)` `.bin_gt(fn)` `.bin_le(fn)` `.bin_ge(fn)`                                           | Comparison operators                                                                                                                                                                                                                       |
| `.compare(fn)`                                                                                                  | Three-way `opCmp` returning `-1`/`0`/`+1` (fallback for any unset comparison)                                                                                                                                                              |
| `.bin_add_assign(fn)` ... `.bin_mod_assign(fn)`                                                                 | Compound assignment `+= -= *= /= %=` (fallback to `bin_*` if unset)                                                                                                                                                                        |
| `.increment(fn)` `.decrement(fn)`                                                                               | Pre/post `++` and `--`                                                                                                                                                                                                                     |
| `.unary_neg(fn)` `.unary_bit_not(fn)`                                                                           | Unary `-` and `~`                                                                                                                                                                                                                          |
| `.bit_and(fn)` `.bit_or(fn)` `.bit_xor(fn)` `.shl(fn)` `.shr(fn)`                                               | Bitwise operators                                                                                                                                                                                                                          |
| `.bin_*_typed<&Fn>()`, `.unary_*_typed<&Fn>()`, `.bit_*_typed<&Fn>()`, `.shl_typed<&Fn>()`, `.shr_typed<&Fn>()` | Typed wrappers for every operator hook, write with real types                                                                                                                                                                              |
| `.compare_typed<&Fn>()`, `.increment_typed<&Fn>()`, `.decrement_typed<&Fn>()`                                   | Typed wrappers for opCmp / `++` / `--`                                                                                                                                                                                                     |
| `.hash(fn)` / `.hash_typed<&Fn>()`                                                                              | Hash function for map keys                                                                                                                                                                                                                 |
| `.copy(fn)` / `.copy_typed<&Fn>()`                                                                              | Copy hook - called on `T b = a;` copy-init. `fn(int64 src) -> int64`                                                                                                                                                                       |
| `.serialize(fn)`                                                                                                | Serialize hook. `fn(int64 value) -> int64 char_ptr`                                                                                                                                                                                        |
| `.deserialize(fn)`                                                                                              | Deserialize hook. `fn(int64 str_ptr) -> int64 value`                                                                                                                                                                                       |
| `.implements(name)`                                                                                             | Declare that this type implements an interface                                                                                                                                                                                             |
| `.as_interface()`                                                                                               | Mark this type as an interface (no instances; used as a parameter type)                                                                                                                                                                    |
| `.generic_param(name)`                                                                                          | Declare a type parameter (e.g. `"T"`, `"K"`, `"V"`); bound at var-decl site                                                                                                                                                                |
| `.requires_iface(param, iface)`                                                                                 | Constrain a generic param - its bound type must `.implements(iface)`                                                                                                                                                                       |
| `.convert(from_type, fn)`                                                                                       | Implicit conversion (fires at binary ops, native call args, var-decl)                                                                                                                                                                      |
| `.captures_arg(arg_idx)`                                                                                        | Last-registered method captures arg `i` past the call (rejects stack-local)                                                                                                                                                                |
| `.permission(flags)`                                                                                            | Permission gate on last-registered method                                                                                                                                                                                                  |
| `.finish()`                                                                                                     | Finalize registration                                                                                                                                                                                                                      |

Use `type_id::t_element` in arg types as a placeholder for the receiver's element type (arrays). Falls back to `t_auto` (match anything) when element type can't be determined.

### Struct Builder

| Method                                        | Description                                                |
| --------------------------------------------- | ---------------------------------------------------------- |
| `struct_builder(engine_t*, const char* name)` | Start building a struct layout                             |
| `.field(name, type, type_name?)`              | Add a field with type and optional struct type name        |
| `.packed()`                                   | C-compatible packed layout (no per-field 8-byte padding)   |
| `.finish()`                                   | Finalize registration (also auto-registers on destruction) |

```cpp
enma::struct_builder(engine, "Vec3")
    .field("x", enma::type_id::t_float64)
    .field("y", enma::type_id::t_float64)
    .field("z", enma::type_id::t_float64);
```

### Enum Builder

| Method                                      | Description                                                |
| ------------------------------------------- | ---------------------------------------------------------- |
| `enum_builder(engine_t*, const char* name)` | Start building an enum                                     |
| `.value(name, int64_t val)`                 | Add a named constant (accessed as `EnumName::ValueName`)   |
| `.finish()`                                 | Finalize registration (also auto-registers on destruction) |

```cpp
enma::enum_builder(engine, "Direction")
    .value("North", 0)
    .value("East",  1)
    .value("South", 2)
    .value("West",  3);
```

### Serialization & Linking

| Function      | Signature                                                                        | Description                                                                                                      |
| ------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `serialize`   | `bool serialize(module_t*, vector<uint8_t>&, bool keep_debug = true)`            | Serialize module to bytes; pass `keep_debug=false` to strip source paths + debug tables (marketplace publishing) |
| `deserialize` | `module_t* deserialize(engine_t*, const uint8_t*, size_t)`                       | Deserialize module from bytes                                                                                    |
| `link`        | `module_t* link(engine_t*, const char** names, module_t** mods, uint32_t count)` | Link multiple modules                                                                                            |

### Introspection

| Function                  | Signature                                                                       | Description                                                                                                                    |
| ------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `has_function`            | `bool has_function(module_t*, const char*)`                                     | Check if function exists                                                                                                       |
| `function_count`          | `uint32_t function_count(module_t*)`                                            | Total function count                                                                                                           |
| `function_param_count`    | `uint32_t function_param_count(module_t*, const char*)`                         | Parameter count for function                                                                                                   |
| `list_functions`          | `void list_functions(module_t*, vector<string>&)`                               | List all function names                                                                                                        |
| `get_annotated_functions` | `uint32_t get_annotated_functions(module_t*, const char* ann, vector<string>&)` | Find functions with annotation                                                                                                 |
| `get_annotations`         | `uint32_t get_annotations(module_t*, const char* fn, vector<annotation_info>&)` | Get annotations on function                                                                                                    |
| `has_type`                | `bool has_type(engine_t*, const char*)`                                         | Check if a type is registered                                                                                                  |
| `list_types`              | `uint32_t list_types(engine_t*, vector<string>&)`                               | List all registered type names                                                                                                 |
| `has_struct`              | `bool has_struct(engine_t*, const char*)`                                       | Check if a struct layout is registered                                                                                         |
| `list_structs`            | `uint32_t list_structs(engine_t*, vector<string>&)`                             | List all registered struct names                                                                                               |
| `tokenize_dump`           | `char* tokenize_dump(engine_t*, const char*, size_t, const char*)`              | Dump token stream                                                                                                              |
| `ir_dump`                 | `char* ir_dump(engine_t*, const char*, size_t, const char*)`                    | Dump IR                                                                                                                        |
| `free_string`             | `void free_string(char*)`                                                       | Free dump string                                                                                                               |
| `extract_documentation`   | `std::string extract_documentation(engine_t*)`                                  | Dump every registered native + type as a C++-ish pseudo-header with descriptions                                               |
| `extract_intellisense`    | `std::vector<doc_entry_t> extract_intellisense(engine_t*)`                      | Same data as a structured vector (kind, name, parent\_type, return\_type, params, signature, description) for IDE autocomplete |

### Debug & Heap

| Function                 | Signature                                                                  | Description                                                                                                                                             |
| ------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `set_debug_hook`         | `void set_debug_hook(module_t*, void(*)(const char*, uint32_t, int64_t*))` | Set per-line debug callback                                                                                                                             |
| `set_budget`             | `void set_budget(module_t*, int64_t)`                                      | Set instruction budget                                                                                                                                  |
| `heap_collect`           | `void heap_collect(module_t*)`                                             | No-op. Cleanup is deterministic, see [Lifecycle](sdk-lifecycle.md)                                                                          |
| `heap_get_stats`         | `heap_stats heap_get_stats(module_t*)`                                     | Get heap statistics (alloc\_count, total\_bytes, freed\_count, freed\_bytes)                                                                            |
| `heap_set_memory_budget` | `void heap_set_memory_budget(module_t*, size_t)`                           | Set heap memory limit in bytes (0 = unlimited)                                                                                                          |
| `get_stack_trace`        | `uint32_t get_stack_trace(context_t*, stack_frame*, uint32_t max)`         | Best-effort iteration of `debug_functions` - visible functions, NOT actual call frames                                                                  |
| `get_last_executed_line` | `int64_t get_last_executed_line(module_t*)`                                | Last source line the JIT was on (written by `op_debug_line`). Survives a JIT fault. Returns `-1` if no line yet, `0` if `set_debug` was off at compile. |

### IDE Debugger SDK

Opt-in via `set_debug(true)` BEFORE compile. Pair with `set_optimize(false)` for full local-variable visibility. See [Debug & Heap](sdk-debug-and-gc.md#ide-debugger-sdk) for usage.

| Function                                              | Signature                                                                                                            | Description                                                           |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `find_fn_at`                                          | `const em_debug_fn_t* find_fn_at(module_t*, const char* file, uint32_t line)`                                        | Containing fn for a source line                                       |
| `debug_fn_name`                                       | `const char* debug_fn_name(const em_debug_fn_t*)`                                                                    | Fn name                                                               |
| `debug_fn_local_count`                                | `uint32_t debug_fn_local_count(const em_debug_fn_t*)`                                                                | Count of locals                                                       |
| `debug_fn_param_count`                                | `uint32_t debug_fn_param_count(const em_debug_fn_t*)`                                                                | Count of params                                                       |
| `find_code_offsets`                                   | `void find_code_offsets(module_t*, const char* file, uint32_t line, size_t* out, uint32_t* out_count, uint32_t max)` | Reverse source map. `out_count` reports the total even when truncated |
| `enumerate_locals`                                    | `uint32_t enumerate_locals(const em_debug_fn_t*, em_local_info* out, uint32_t max)`                                  | Per-fn locals (name, type, slot)                                      |
| `read_local_int`                                      | `int64_t read_local_int(int64_t* frame, uint32_t slot)`                                                              | `frame` is the rbp the hook receives                                  |
| `read_local_float`                                    | `double read_local_float(int64_t* frame, uint32_t slot)`                                                             |                                                                       |
| `read_local_string`                                   | `const char* read_local_string(int64_t* frame, uint32_t slot)`                                                       |                                                                       |
| `read_local_pointer`                                  | `void* read_local_pointer(int64_t* frame, uint32_t slot)`                                                            |                                                                       |
| `set_breakpoint`                                      | `int32_t set_breakpoint(module_t*, const char* file, uint32_t line)`                                                 | Returns id                                                            |
| `clear_breakpoint`                                    | `void clear_breakpoint(module_t*, int32_t bp_id)`                                                                    |                                                                       |
| `enable_breakpoint`                                   | `void enable_breakpoint(module_t*, int32_t bp_id, bool enabled)`                                                     |                                                                       |
| `is_breakpoint_at`                                    | `bool is_breakpoint_at(module_t*, const char* file, uint32_t line)`                                                  | Hot-path check for hooks                                              |
| `list_breakpoints`                                    | `uint32_t list_breakpoints(module_t*, em_breakpoint_info* out, uint32_t max)`                                        |                                                                       |
| `set_step_mode` / `get_step_mode`                     | `void/step_mode (context_t*, step_mode)`                                                                             | `step_none`/`over`/`in`/`out`                                         |
| `set_step_baseline_depth` / `get_step_baseline_depth` | `void/int32_t (context_t*, ...)`                                                                                     | Baseline for step over/out                                            |
| `get_call_depth`                                      | `int32_t get_call_depth(int64_t* frame, module_t*)`                                                                  | rbp-walk frame counter                                                |
| `request_pause` / `resume` / `is_pause_requested`     | `void/void/bool (context_t*)`                                                                                        | One-shot pause flag; `should_pause_at` clears it on observation       |
| `should_pause_at`                                     | `bool should_pause_at(context_t*, module_t*, int64_t* frame, const char* file, uint32_t line)`                       | Combines breakpoint + pause + step-mode                               |

### Exceptions

| Function            | Signature                            | Description                      |
| ------------------- | ------------------------------------ | -------------------------------- |
| `exception_pending` | `bool exception_pending(module_t*)`  | Check if an exception is pending |
| `exception_value`   | `int64_t exception_value(module_t*)` | Get the thrown exception value   |
| `exception_type`    | `int64_t exception_type(module_t*)`  | Get the exception type hash      |
| `exception_clear`   | `void exception_clear(module_t*)`    | Clear pending exception state    |

### Events

| Function         | Signature                                                       | Description                    |
| ---------------- | --------------------------------------------------------------- | ------------------------------ |
| `register_event` | `void register_event(context_t*, int64_t id, int64_t callback)` | Register event callback        |
| `fire_event`     | `void fire_event(context_t*, int64_t id)`                       | Fire all callbacks for event   |
| `clear_events`   | `void clear_events(context_t*)`                                 | Remove all event registrations |

### Heap Allocation (for addon authors)

Enma has no tracing collector. These are a thin malloc/free wrapper with a magic-marker validity check and alloc/free stats.

| Function          | Signature                                    | Description                                                                                               |
| ----------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `heap_alloc`      | `void* heap_alloc(size_t size)`              | malloc-backed alloc with tracking header                                                                  |
| `heap_realloc`    | `void* heap_realloc(void* ptr, size_t size)` | Resize a tracked allocation                                                                               |
| `heap_free`       | `void heap_free(void* ptr)`                  | Free a tracked allocation                                                                                 |
| `heap_is_tracked` | `bool heap_is_tracked(void* ptr)`            | Check magic marker, safe to call `heap_free` if true                                                      |
| `alive_token`     | `uint64_t* alive_token(void* ptr)`           | Shared liveness flag - non-zero while alive, flipped to 0 on `heap_free`. Foundation for weak references. |

### Per-Context Helpers (for addon authors)

Read the engine, context, and per-thread RNG driving the current `execute()`/`call()`. Thread-safe across concurrent engines.

| Function           | Signature                                          | Description                                               |
| ------------------ | -------------------------------------------------- | --------------------------------------------------------- |
| `active_engine`    | `engine_t* active_engine()`                        | Engine currently driving execute/call; `nullptr` outside  |
| `active_context`   | `context_t* active_context()`                      | Context currently driving execute/call; `nullptr` outside |
| `random_u64`       | `uint64_t random_u64()`                            | Raw 64-bit draw from the per-context mt19937              |
| `random_double`    | `double random_double()`                           | Uniform `[0, 1)` draw                                     |
| `random_int_range` | `int64_t random_int_range(int64_t lo, int64_t hi)` | Uniform `[lo, hi)` draw                                   |
| `random_seed`      | `void random_seed(uint64_t seed)`                  | Seed the per-context rng                                  |

### Error Handling

| Function             | Signature                                   | Description                                   |
| -------------------- | ------------------------------------------- | --------------------------------------------- |
| `last_error`         | `error_info last_error(engine_t*)`          | Get last error details                        |
| `last_error_message` | `const char* last_error_message(engine_t*)` | Get last error message                        |
| `runtime_error`      | `void runtime_error(const char* msg)`       | Addon: raise a runtime error from native code |
| `runtime_exception`  | `void runtime_exception(const char* msg)`   | Addon: raise an exception from native code    |

### Addon Registration

| Function                               | Description                                                                                        |
| -------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `register_all_addons(engine_t*)`       | Register all standard addons                                                                       |
| `register_addon_core(engine_t*)`       | `print(string)` / `println(string)` - non-string args auto-convert via string addon's `.convert()` |
| `register_addon_string(engine_t*)`     | String methods                                                                                     |
| `register_addon_array(engine_t*)`      | Array methods                                                                                      |
| `register_addon_map(engine_t*)`        | Map methods                                                                                        |
| `register_addon_math(engine_t*)`       | Scalar math, vec2/vec3/vec4, quat, mat4                                                            |
| `register_addon_simd(engine_t*)`       | SIMD operations                                                                                    |
| `register_addon_variant(engine_t*)`    | Open variant type                                                                                  |
| `register_addon_atomic(engine_t*)`     | Atomic int32 / int64 types and barriers                                                            |
| `register_addon_bits(engine_t*)`       | Bit intrinsics (popcount/clz/ctz/rotl/rotr/bswap/parity/bit\_reverse)                              |
| `register_addon_time(engine_t*)`       | Timestamps, calendar, ISO 8601, sleep                                                              |
| `register_addon_regex(engine_t*)`      | Regex addon type                                                                                   |
| `register_addon_file(engine_t*)`       | File I/O, gated by `PERM_FILE`                                                                     |
| `register_addon_thread(engine_t*)`     | mutex, lock\_guard, cond\_var                                                                      |
| `register_addon_list(engine_t*)`       | Generic list                                                                                       |
| `register_addon_hash_set(engine_t*)`   | Generic hash\_set                                                                                  |
| `register_addon_sorted_map(engine_t*)` | Generic sorted\_map\<K,V>                                                                          |
| `register_addon_json(engine_t*)`       | JSON parse/stringify + json\_value type                                                            |

### Reflection

| Function                               | Signature                                                                           | Description                                                             |
| -------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `find_type_reg`                        | `const type_reg_t* find_type_reg(engine_t*, type_id)`                               | Lookup type registration by id                                          |
| `find_type_reg_by_name`                | `const type_reg_t* find_type_reg_by_name(engine_t*, const char*)`                   | Lookup type registration by name                                        |
| `type_reg_name`                        | `const char* type_reg_name(const type_reg_t*)`                                      | Name of type                                                            |
| `type_reg_id`                          | `type_id type_reg_id(const type_reg_t*)`                                            | Type ID                                                                 |
| `type_reg_factory`                     | `void* type_reg_factory(const type_reg_t*)`                                         | Factory fn pointer (nullable)                                           |
| `type_reg_factory_param_count`         | `uint32_t type_reg_factory_param_count(const type_reg_t*)`                          | Factory arity                                                           |
| `type_reg_dtor`                        | `void* type_reg_dtor(const type_reg_t*)`                                            | Destructor fn pointer (nullable)                                        |
| `type_reg_copy`                        | `void* type_reg_copy(const type_reg_t*)`                                            | Copy hook fn pointer (nullable)                                         |
| `type_reg_hash`                        | `void* type_reg_hash(const type_reg_t*)`                                            | Hash fn pointer (nullable)                                              |
| `type_reg_compare`                     | `void* type_reg_compare(const type_reg_t*)`                                         | Three-way compare fn pointer (nullable)                                 |
| `type_reg_op_eq`                       | `void* type_reg_op_eq(const type_reg_t*)`                                           | Equality fn pointer (nullable)                                          |
| `type_reg_serialize`                   | `void* type_reg_serialize(const type_reg_t*)`                                       | Serialize hook fn pointer (nullable)                                    |
| `type_reg_deserialize`                 | `void* type_reg_deserialize(const type_reg_t*)`                                     | Deserialize hook fn pointer (nullable)                                  |
| `type_reg_convert_from`                | `void* type_reg_convert_from(const type_reg_t*, type_id from)`                      | Conversion fn for a given source type (nullable)                        |
| `type_reg_method`                      | `void* type_reg_method(const type_reg_t*, const char* name)`                        | Method fn pointer by name (nullable)                                    |
| `type_reg_method_count`                | `uint32_t type_reg_method_count(const type_reg_t*)`                                 | Number of registered methods                                            |
| `type_reg_method_name_at`              | `const char* type_reg_method_name_at(const type_reg_t*, uint32_t idx)`              | Method name by index                                                    |
| `type_reg_implements`                  | `bool type_reg_implements(const type_reg_t*, const char* iface)`                    | Type implements a named interface                                       |
| `type_reg_implements_count`            | `uint32_t type_reg_implements_count(const type_reg_t*)`                             | Number of declared interfaces                                           |
| `type_reg_implements_at`               | `const char* type_reg_implements_at(const type_reg_t*, uint32_t idx)`               | Interface name by index                                                 |
| `type_reg_is_interface`                | `bool type_reg_is_interface(const type_reg_t*)`                                     | True if this type is itself an interface                                |
| `type_reg_generic_param_count`         | `uint32_t type_reg_generic_param_count(const type_reg_t*)`                          | Number of declared generic parameters                                   |
| `type_reg_generic_param_at`            | `const char* type_reg_generic_param_at(const type_reg_t*, uint32_t idx)`            | Generic parameter name by index                                         |
| `type_reg_generic_constraint_count`    | `uint32_t type_reg_generic_constraint_count(const type_reg_t*)`                     | Number of declared (param, iface) constraints                           |
| `type_reg_generic_constraint_param_at` | `const char* type_reg_generic_constraint_param_at(const type_reg_t*, uint32_t idx)` | Constrained parameter name by index                                     |
| `type_reg_generic_constraint_iface_at` | `const char* type_reg_generic_constraint_iface_at(const type_reg_t*, uint32_t idx)` | Required interface name by index                                        |
| `interface_method_fn`                  | `void* interface_method_fn(engine_t*, type_id concrete, const char* method)`        | Resolve concrete type's method fn - used inside interface-typed natives |

All reflection accessors are null-safe (pass `nullptr` → return empty/0/nullptr as appropriate).

### Type IDs

| Name            | Value | Description                                 |
| --------------- | ----- | ------------------------------------------- |
| `t_void`        | 0     | Void                                        |
| `t_bool`        | 1     | Boolean                                     |
| `t_char`        | 2     | 8-bit character                             |
| `t_wchar`       | 3     | 16-bit character                            |
| `t_int32`       | 4     | 32-bit signed int                           |
| `t_int64`       | 5     | 64-bit signed int                           |
| `t_uint8`       | 6     | 8-bit unsigned int                          |
| `t_uint16`      | 7     | 16-bit unsigned int                         |
| `t_uint32`      | 8     | 32-bit unsigned int                         |
| `t_uint64`      | 9     | 64-bit unsigned int                         |
| `t_aint8`       | 10    | Atomic int8                                 |
| `t_aint16`      | 11    | Atomic int16                                |
| `t_aint32`      | 12    | Atomic int32                                |
| `t_aint64`      | 13    | Atomic int64                                |
| `t_float32`     | 14    | 32-bit float                                |
| `t_float64`     | 15    | 64-bit float                                |
| `t_string`      | 16    | String                                      |
| `t_wstring`     | 17    | Wide string                                 |
| `t_array`       | 18    | Array                                       |
| `t_map`         | 19    | Map                                         |
| `t_class`       | 20    | Class                                       |
| `t_struct`      | 21    | Struct                                      |
| `t_enum`        | 22    | Enum                                        |
| `t_function`    | 23    | Function pointer                            |
| `t_lambda`      | 24    | Lambda/closure                              |
| `t_pointer`     | 25    | Raw pointer                                 |
| `t_auto`        | 26    | Auto-inferred                               |
| `t_null`        | 27    | Null literal                                |
| `t_element`     | 28    | Receiver's element type (container methods) |
| `t_custom_base` | 128   | Base for custom types                       |

### Constants

| Name        | Value  | Description                                   |
| ----------- | ------ | --------------------------------------------- |
| `PERM_FFI`  | `0x01` | Permission flag for `[[dll(...)]]` FFI access |
| `PERM_FILE` | `0x02` | Permission flag for the file addon            |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/api-reference.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-calling-functions.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/calling-functions.md).

# Calling Functions

## Call with Arguments

```cpp
int64_t args[] = { 10, 20 };
call(ctx, "add", args, 2);
int64_t result = return_value(ctx);  // 30
```

Arguments pass as `int64_t`. Floats must be bit-cast:

```cpp
double val = 3.14;
int64_t bits;
memcpy(&bits, &val, 8);

int64_t args[] = { bits };
call(ctx, "process_float", args, 1);

double result;
int64_t rbits = return_value(ctx);
memcpy(&result, &rbits, 8);
```

## Passing Strings

Allocate via Enma's heap:

```cpp
int64_t str = alloc_string(ctx, "hello world");
int64_t args[] = { str };
call(ctx, "process_text", args, 1);
```

Runtime manages the string's lifetime, don't free it manually.

## Reading String Returns

```cpp
execute(ctx, "get_name");
const char* name = return_string(ctx);
printf("name: %s\n", name);
```

The returned pointer is valid until the next call.

## Checking Function Existence

```cpp
if (has_function(mod, "on_tick")) {
    execute(ctx, "on_tick");
}
```

## Getting Parameter Count

```cpp
uint32_t params = function_param_count(mod, "add");  // 2
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/calling-functions.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-compilation.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/compilation.md).

# Compilation

## Compile from Source

```cpp
const char* src = "int32 main() { return 42; }";
module_t* mod = compile(e, src, strlen(src), "script.em");
```

The filename is used for error messages and source maps; it doesn't need to be a real file.

## Compile from File

```cpp
module_t* mod = compile_file(e, "scripts/game.em");
```

Include and module paths are resolved relative to the engine's configured paths.

## Module Cleanup

```cpp
module_destroy(mod);
```

Destroy all contexts created from this module before destroying the module.

## Checking for Errors

Compilation errors surface via the engine's error state:

```cpp
module_t* mod = compile(e, src, len, "script.em");
error_info err = last_error(e);
if (err.code != 0) {
    printf("[%s:%d:%d] %s\n",
        err.file.c_str(), err.line, err.column, err.message.c_str());
}
```

## What Compilation Produces

`compile()` runs: lexer → preprocessor → parser → type checker → IR builder → optimizer passes → register allocator → x64 codegen. The module holds native machine code ready to execute.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/compilation.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-custom-addons.md`

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

---

## Source: `docs/enma/sdk-debug-and-gc.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/debug-and-gc.md).

# Debug & Heap

## Debug Hooks

Callback fires at every source line:

```cpp
void my_debug_hook(const char* file, uint32_t line, int64_t* frame) {
    printf("[%s:%d]\n", file, line);
}

set_debug_hook(mod, my_debug_hook);
```

`frame` indexes into the current function's locals by slot number. Enable debug mode for source maps:

```cpp
set_debug(e, true);
```

## Execution Budget

```cpp
set_budget(mod, 1000000);  // max 1 million instructions; 0 = disabled
```

When exhausted, `execute()` returns `false`.

## Memory Model

Deterministic. No tracing collector. See [Lifecycle & RAII](sdk-lifecycle.md) for the full model.

`heap_*` SDK entry points exist for stats and budget control only:

```cpp
heap_collect(mod);                 // no-op; cleanup is deterministic
heap_set_memory_budget(mod, ...);  // hard limit on live heap bytes
heap_stats stats = heap_get_stats(mod);
```

### Stats

```cpp
heap_stats stats = heap_get_stats(mod);
printf("live allocs: %llu\n", stats.alloc_count);   // currently-alive heap objects
printf("live bytes:  %llu\n", stats.total_bytes);
printf("total freed: %llu\n", stats.freed_count);
printf("freed bytes: %llu\n", stats.freed_bytes);
```

| Field         | Description                         |
| ------------- | ----------------------------------- |
| `alloc_count` | Currently-live heap allocations     |
| `total_bytes` | Currently-live heap bytes           |
| `freed_count` | Cumulative frees since engine start |
| `freed_bytes` | Cumulative bytes freed              |

Unbounded `alloc_count` growth indicates a leak, typically a `new` whose handle isn't stored in a scope-tracked local or a pointer global that isn't reset.

### Memory Budget

Set a hard limit on total live heap bytes. `alloc()` returns null when exceeded.

```cpp
heap_set_memory_budget(mod, 1024 * 1024 * 64);  // 64 MB cap
heap_set_memory_budget(mod, 0);                  // unlimited (default)
```

## Stack Traces

Requires `set_debug(e, true)`.

```cpp
stack_frame frames[32];
uint32_t count = get_stack_trace(ctx, frames, 32);
for (uint32_t i = 0; i < count; ++i) {
    printf("  %s (%s:%d)\n", frames[i].function, frames[i].file, frames[i].line);
}
```

`stack_frame` fields: `function` (`const char*`), `file` (`const char*`), `line` (`uint32_t`).

`get_stack_trace` is best-effort. The JIT doesn't push fixed frame metadata, so the implementation iterates the module's `debug_functions` table. Treat it as a "what functions are visible in this module" snapshot rather than a true call-frame walk - it does not reflect real recursion depth or invocation order.

## Last-Executed Line

For pinpointing exactly where a JIT fault hit, use `get_last_executed_line(mod)`:

```cpp
set_debug(e, true);              // must be set BEFORE compile so op_debug_line is emitted
module_t* mod = compile_file(e, "script.em");
context_t* ctx = create_context(mod);

if (!execute(ctx, "main")) {
    int64_t line = get_last_executed_line(mod);
    printf("crashed at line %lld\n", line);
}
```

The JIT records the source line before each statement runs, so the value persists across a fault — pointing at the exact source line the JIT was on. Returns `-1` when no line has executed yet, `0` when debug wasn't enabled at compile time. More reliable than `get_stack_trace` for crash diagnostics.

## IDE Debugger SDK

A debugger SDK on top of the per-line hook foundation. All opt-in via `set_debug(e, true)` BEFORE compile.

For full local-variable visibility you should ALSO call `set_optimize(e, false)`. Otherwise the optimizer promotes locals to registers and they never land in their declared frame slots, so `read_local_*` returns garbage.

```cpp
// Source map + function lookup
struct em_debug_fn_t;   // opaque
const em_debug_fn_t* find_fn_at(module_t*, const char* file, uint32_t line);
const char* debug_fn_name        (const em_debug_fn_t*);
uint32_t    debug_fn_local_count (const em_debug_fn_t*);
uint32_t    debug_fn_param_count (const em_debug_fn_t*);

void find_code_offsets(module_t*, const char* file, uint32_t line,
                       size_t* out_offsets, uint32_t* out_count, uint32_t max);

// Local readback (frame is the rbp the hook receives)
struct em_local_info { const char* name; type_id type; uint32_t slot; };
uint32_t enumerate_locals(const em_debug_fn_t*, em_local_info* out, uint32_t max);
int64_t     read_local_int    (int64_t* frame, uint32_t slot);
double      read_local_float  (int64_t* frame, uint32_t slot);
const char* read_local_string (int64_t* frame, uint32_t slot);
void*       read_local_pointer(int64_t* frame, uint32_t slot);

// Breakpoints (per module)
int32_t set_breakpoint    (module_t*, const char* file, uint32_t line);
void    clear_breakpoint  (module_t*, int32_t bp_id);
void    enable_breakpoint (module_t*, int32_t bp_id, bool enabled);
bool    is_breakpoint_at  (module_t*, const char* file, uint32_t line);

struct em_breakpoint_info { int32_t id; const char* file; uint32_t line; bool enabled; };
uint32_t list_breakpoints(module_t*, em_breakpoint_info* out, uint32_t max);

// Stepping (per context)
enum class step_mode : int32_t { step_none, step_over, step_in, step_out };
void      set_step_mode           (context_t*, step_mode);
step_mode get_step_mode           (context_t*);
void      set_step_baseline_depth (context_t*, int32_t depth);
int32_t   get_step_baseline_depth (context_t*);
int32_t   get_call_depth          (int64_t* frame, module_t*);

// Pause/resume (per context)
void request_pause      (context_t*);
void resume             (context_t*);   // also clears step_mode
bool is_pause_requested (context_t*);

// Convenience: combines breakpoint hit, pause, and step-mode logic.
bool should_pause_at(context_t*, module_t*, int64_t* frame,
                      const char* file, uint32_t line);
```

State is per-context, so multi-thread routines each get independent step/pause state. The IDE host implements its DAP / VS Code adapter on top of these primitives.

Typical hook:

```cpp
void on_line(const char* file, uint32_t line, int64_t* frame) {
    context_t* ctx = active_context();
    module_t* mod = my_module;
    if (!should_pause_at(ctx, mod, frame, file, line)) return;

    auto* fn = find_fn_at(mod, file, line);
    em_local_info infos[64];
    uint32_t n = enumerate_locals(fn, infos, 64);
    for (uint32_t i = 0; i < n; ++i) {
        switch (infos[i].type) {
            case type_id::t_int64:   inspect(read_local_int   (frame, infos[i].slot)); break;
            case type_id::t_float64: inspect(read_local_float (frame, infos[i].slot)); break;
            case type_id::t_string:  inspect(read_local_string(frame, infos[i].slot)); break;
            default:                 inspect(read_local_pointer(frame, infos[i].slot));
        }
    }
    // ... wait for IDE command, then either:
    set_step_baseline_depth(ctx, get_call_depth(frame, mod));
    set_step_mode(ctx, step_mode::step_over);   // or step_in / step_out / step_none
    resume(ctx);   // clears pause_requested
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/debug-and-gc.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-engine-lifecycle.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/engine-lifecycle.md).

# Engine Lifecycle

### Creating an Engine

```cpp
engine_t* e = create();
```

Holds compiler state, type registrations, native function bindings, and configuration. Typically one engine per application.

`create()` auto-registers built-in script-level natives: `heap_collect`, `heap_count`, `set_budget`, `set_memory_budget`, `register_event`/`fire_event`/`clear_events`, `assert`, `time_ms`, `co_create` + type `coroutine_t`, type `counter_t`. The `throw` keyword and try/catch are wired in via the exception runtime.

### Configuration

Configure the engine before compiling any scripts.

#### Addons

```cpp
register_all_addons(e);
// or selectively:
register_addon_core(e);
register_addon_string(e);
register_addon_array(e);
register_addon_map(e);
register_addon_math(e);
register_addon_simd(e);
```

#### Optimization

```cpp
set_optimize(e, true);   // enable optimizer (default: on, set by create())
set_debug(e, false);     // enable debug info (default: off)
```

#### Preprocessor Defines

```cpp
define(e, "DEBUG", "1");
define(e, "VERSION", "2");
define(e, "PLATFORM", "windows");
```

These are available in scripts via `#ifdef`:

```cpp
#ifdef DEBUG
    println("debug build");
#endif
```

#### Include & Module Paths

```cpp
add_include_path(e, "includes/");  // for #include
add_module_path(e, "modules/");    // for import
```

#### Resolve Callbacks

Override how `#include` and `import` find files. Return `true` to provide the buffer, `false` to fall back to filesystem resolution.

```cpp
bool my_include_resolver(const char* path, char** out_data, size_t* out_len, void* userdata) {
    auto* vfs = static_cast<VirtualFS*>(userdata);
    std::string content;
    if (!vfs->read(path, content)) return false;
    *out_data = static_cast<char*>(malloc(content.size()));
    memcpy(*out_data, content.data(), content.size());
    *out_len = content.size();
    return true;
}

set_include_resolver(e, my_include_resolver, &my_vfs);
set_import_resolver(e, my_import_resolver, &my_vfs);
```

Import resolver tries `.emb` (binary) first, then `.em` (source), then the bare name. The engine frees the returned buffer after use.

#### Permissions

```cpp
set_permissions(e, PERM_FFI);            // allow [[dll(...)]] FFI calls
set_permissions(e, PERM_FFI | PERM_FILE); // also allow the file addon
```

Two flags today:

* `PERM_FFI` (`0x01`) gates `[[dll(...)]]`.
* `PERM_FILE` (`0x02`) gates the file addon.

Scripts fail to compile any call to a gated feature when the matching flag isn't set.

```cpp
uint32_t flags = get_permissions(e);
```

### Destroying an Engine

```cpp
destroy(e);
```

Destroy all modules and contexts first, the engine does not track child objects.

### DLL Shutdown

If you load enma inside a DLL/plugin that may be unloaded while the host process keeps running, call `shutdown()` once from your `DllMain` `DLL_PROCESS_DETACH` handler before the DLL unloads:

```cpp
BOOL APIENTRY DllMain(HMODULE, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_DETACH) {
        enma::shutdown();
    }
    return TRUE;
}
```

This removes enma's process-global fault handler, which holds a function pointer into the DLL's text segment. If you skip this and the DLL unloads, the next unrelated exception anywhere in the process walks into freed memory and crashes — usually delayed, looking like a spontaneous crash much later. Safe to call when no engines exist. Don't execute any enma script code after `shutdown()` — without the fault handler, JIT faults take down the host. Static-linked exes and long-lived hosts that never unload don't need this.

### Typical Lifecycle

```cpp
engine_t* e = create();

// configure
register_all_addons(e);
set_optimize(e, true);
add_module_path(e, "scripts/");

// register custom types and functions
register_typed<&get_hp_fn>(e, "int32 get_hp(int32 player_id)");

// compile and run scripts (possibly many times)
module_t* mod = compile_file(e, "game.em");
context_t* ctx = create_context(mod);
execute(ctx, "main");
destroy_context(mod, ctx);
module_destroy(mod);

// shutdown
destroy(e);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/engine-lifecycle.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-error-handling.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/error-handling.md).

# Error Handling

## Error Info

Check the engine's error state after any operation:

```cpp
error_info err = last_error(e);
if (err.code != 0) {
    printf("[%s:%d:%d] %s\n",
        err.file.c_str(), err.line, err.column,
        err.message.c_str());
}
```

## Message-Only Check

```cpp
const char* msg = last_error_message(e);
if (msg && msg[0] != '\0') {
    printf("error: %s\n", msg);
}
```

## Error Codes

The `error_info.code` field indicates the error category:

* `0` = no error
* Parser errors = syntax problems in source code
* Type errors = type mismatches, undefined symbols
* Runtime errors = segfaults in JIT code, budget exhaustion

## Compile-Time Errors

```cpp
module_t* mod = compile(e, src, len, "script.em");
error_info err = last_error(e);
if (err.code != 0) {
    // compilation failed
    printf("compile error: %s\n", err.message.c_str());
    printf("  at %s:%d:%d\n", err.file.c_str(), err.line, err.column);
}
```

### Diagnostic shape

Compile errors include a one-line summary followed by a `hint:` line where applicable. Examples:

```cpp
cannot implicitly convert int32 to uint64 (signed/unsigned mismatch)
  hint: use cast<uint64>(...) to make the conversion explicit

return type mismatch: cannot implicitly convert float64 to int32 (would truncate float)
  hint: use cast<int32>(...) to make the conversion explicit

file_open() requires PERM_FILE, but engine has only PERM_NONE
  hint: call set_permissions(engine, PERM_FILE) before compile()
```

Permission errors name the missing flag (`PERM_FILE`, `PERM_FFI`) and the current grant.

## Runtime Errors

Runtime errors (segfaults, null dereferences) are caught by the JIT fault handler and mapped to source locations via the source map:

```cpp
bool ok = execute(ctx, "main");
if (!ok) {
    error_info err = last_error(e);
    printf("runtime error: %s\n", err.message.c_str());
}
```

## Exception Access

```cpp
if (exception_pending(mod)) {
    int64_t val  = exception_value(mod);   // the thrown value
    int64_t tid  = exception_type(mod);    // type hash of the thrown value
    printf("exception: value=%lld type=%llu\n", val, tid);
    exception_clear(mod);
}
```

The runtime fault handler clears exception state before returning control to the host. For uncaught throws after execution, check `last_error()`:

```cpp
bool ok = execute(ctx, "main");
if (!ok) {
    error_info err = last_error(e);
    // err contains the uncaught exception info
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/error-handling.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-execution.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/execution.md).

# Execution

## Creating a Context

Holds execution state (stack, locals, TLS). Each context is independent.

```cpp
context_t* ctx = create_context(mod);
```

You can create multiple contexts from the same module for concurrent execution.

The full signature is `create_context(module_t* mod, size_t stack_size = 0)`. Default `stack_size = 0` runs JIT'd code on the OS thread stack, which is what you want for almost every host - it keeps OS guard pages and full C++ EH unwinding through native boundaries. Pass a non-zero `stack_size` to allocate a separate JIT stack via `set_stack_allocators`. Caveat: a switched stack breaks C++ exception unwinding across the JIT boundary because the OS dispatcher validates frames against the thread's TEB stack range. Only use it if every native call your scripts hit catches its own C++ exceptions before returning.

## Running a Function

```cpp
bool ok = execute(ctx, "main");
```

`true` on success; `false` on runtime fault, budget exceeded, or missing function.

## Reading Return Values

```cpp
int64_t  i = return_value(ctx);   // integer return
const char* s = return_string(ctx); // string return
double   f = return_float(ctx);    // float return
```

Use the function that matches the return type of the called function.

## Context Userdata

Attach application state to a context. It's accessible from native functions; 16 slots available so multiple addons can coexist without stomping each other.

```cpp
struct game_state { int32_t level; int32_t score; };
game_state state = { 5, 1000 };

set_userdata(ctx, &state);                 // slot 0 (aliased)
set_userdata_at(ctx, 1, &some_other_ptr);  // slot 1

// inside a native function:
auto* gs = static_cast<game_state*>(get_userdata(ctx));           // slot 0
auto* p  = get_userdata_at(ctx, 1);                                // slot 1

// or via active_context(), no need to thread ctx through:
auto* gs2 = static_cast<game_state*>(get_userdata(active_context()));
```

Slots are 0-15; out-of-range is a no-op / `nullptr`. Slot 0 is the same storage as `set_userdata`/`get_userdata`.

## Context Cleanup

```cpp
destroy_context(mod, ctx);
```

## Calling Script Code from Background Threads

`execute()` and `call()` set up enma's per-thread TLS automatically. If you need to invoke a script-side closure from a thread that *isn't* already inside one of those, wrap the invocation in an `execution_scope` first - see [Custom Addons / Invoking Script Closures from Background Threads](sdk-custom-addons.md#invoking-script-closures-from-background-threads). Without it, the first native that touches TLS (heap\_alloc, string concat, etc.) dereferences nullptr.

## Example

```cpp
module_t* mod = compile(e, src, len, "game.em");

context_t* ctx = create_context(mod);
execute(ctx, "init");

// game loop
while (running) {
    execute(ctx, "update");
    execute(ctx, "render");
}

execute(ctx, "shutdown");
destroy_context(mod, ctx);
module_destroy(mod);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/execution.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-globals.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/globals.md).

# Globals

## Setting Globals

Inject values into the script's global scope:

```cpp
set_global(mod, "max_hp", 100);
set_global(mod, "player_id", 42);
```

The script can read these as regular global variables:

```cpp
int32 main() {
    println(max_hp);  // 100
    return 0;
}
```

## Reading Globals

```cpp
int64_t score = get_global(mod, "score");
```

## Checking Existence

```cpp
if (has_global(mod, "score")) {
    int64_t score = get_global(mod, "score");
}
```

## Direct Pointer Access

Direct pointer to global storage (skips the call overhead):

```cpp
int64_t* hp_ptr = get_global_ptr(mod, "player_hp");
*hp_ptr = 100;          // write
int64_t hp = *hp_ptr;   // read, no function call overhead
```

The pointer is valid for the lifetime of the module.

## Listing All Globals

```cpp
std::vector<std::string> names;
std::vector<int64_t> values;
list_globals(mod, names, values);

for (size_t i = 0; i < names.size(); ++i) {
    printf("%s = %lld\n", names[i].c_str(), values[i]);
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/globals.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-hot-reload.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/hot-reload.md).

# Hot Reload

Replace a module's code at runtime without destroying the engine or losing registered types.

## Basic Reload

```cpp
const char* new_src = R"(
    int32 main() {
        println("updated version!");
        return 2;
    }
)";
bool ok = reload(mod, new_src, strlen(new_src), "script.em");
```

## Running the New Code

Existing contexts pick up the new code on the next `execute()` call, no need to recreate them:

```cpp
execute(ctx, "main");                        // runs v1
reload(mod, new_src, len, "script.em");
execute(ctx, "main");                        // runs v2 on the same ctx
```

## Typical Hot Reload Loop

```cpp
module_t* mod = compile_file(e, "game.em");
context_t* ctx = create_context(mod);

while (running) {
    if (file_changed("game.em")) {
        std::string src = read_file("game.em");
        reload(mod, src.c_str(), src.size(), "game.em");
    }
    execute(ctx, "update");
}
```

Globals, registered types, and native functions persist; only the script code is replaced.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/hot-reload.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-introspection.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/introspection.md).

# Introspection

## Listing Functions

```cpp
std::vector<std::string> fns;
list_functions(mod, fns);
for (auto& name : fns) {
    printf("  %s\n", name.c_str());
}
```

## Function Count

```cpp
uint32_t count = function_count(mod);
```

## Checking Function Existence

```cpp
if (has_function(mod, "on_damage")) {
    execute(ctx, "on_damage");
}
```

## Parameter Count

```cpp
uint32_t params = function_param_count(mod, "add");
```

## Querying Annotations

Find all functions with a specific annotation:

```cpp
std::vector<std::string> tagged;
get_annotated_functions(mod, "priority", tagged);
for (auto& fn : tagged) {
    printf("  %s has [[priority]]\n", fn.c_str());
}
```

Get all annotations on a specific function:

```cpp
std::vector<annotation_info> anns;
get_annotations(mod, "attack", anns);
for (auto& ann : anns) {
    printf("  [[%s", ann.name);
    if (ann.arg_count > 0) {
        printf("(");
        for (uint32_t i = 0; i < ann.arg_count; ++i) {
            if (i > 0) printf(", ");
            printf("%s", ann.args[i]);
        }
        printf(")");
    }
    printf("]]\n");
}
```

For a script with:

```cpp
[[priority(5)]]
[[category("combat")]]
void attack(int32 target) { }
```

This prints:

```cpp
  [[priority(5)]]
  [[category(combat)]]
```

## Debug Dumps

Dump the token stream:

```cpp
char* tokens = tokenize_dump(e, src, len, "script.em");
printf("%s\n", tokens);
free_string(tokens);
```

Dump the IR (intermediate representation):

```cpp
char* ir = ir_dump(e, src, len, "script.em");
printf("%s\n", ir);
free_string(ir);
```

Always free dump strings with `free_string()`.

## Type and Struct Queries

Check for registered types and structs, or list all of them:

```cpp
if (has_type(e, "vec3_t")) {
    printf("vec3_t is registered\n");
}

if (has_struct(e, "point_t")) {
    printf("point_t is registered\n");
}
```

```cpp
std::vector<std::string> types;
list_types(e, types);
for (auto& t : types) {
    printf("  type: %s\n", t.c_str());
}

std::vector<std::string> structs;
list_structs(e, structs);
for (auto& s : structs) {
    printf("  struct: %s\n", s.c_str());
}
```

## JIT Function Pointer

Get the raw function pointer for a compiled function. Bypasses the context layer.

```cpp
void* addr = fn_address(mod, "compute");
auto fn = reinterpret_cast<int64_t(*)()>(addr);
int64_t result = fn();
```

For functions with parameters:

```cpp
void* addr = fn_address(mod, "add");
auto fn = reinterpret_cast<int64_t(*)(int64_t, int64_t)>(addr);
int64_t result = fn(10, 20);  // 30
```

The returned pointer is valid for the lifetime of the module. If `fn_address` cannot find the function, it returns `nullptr`.

## Type Registry Reflection

Addons can query any registered type's hooks without a compile-time dependency on the concrete type. All accessors are null-safe.

### Lookup

```cpp
const type_reg_t* reg = find_type_reg(engine, some_type_id);
// or by name:
reg = find_type_reg_by_name(engine, "date");
```

Both return `nullptr` if the type isn't registered.

### Accessors

```cpp
const char* name            = type_reg_name(reg);
type_id     id              = type_reg_id(reg);
void*       factory_fn      = type_reg_factory(reg);
uint32_t    factory_args    = type_reg_factory_param_count(reg);
void*       dtor_fn         = type_reg_dtor(reg);
void*       copy_fn         = type_reg_copy(reg);
void*       hash_fn         = type_reg_hash(reg);
void*       compare_fn      = type_reg_compare(reg);
void*       op_eq_fn        = type_reg_op_eq(reg);
void*       serialize_fn    = type_reg_serialize(reg);
void*       deserialize_fn  = type_reg_deserialize(reg);
void*       convert_from_fn = type_reg_convert_from(reg, source_type_id);

void*       method_fn       = type_reg_method(reg, "methodName");
uint32_t    method_count    = type_reg_method_count(reg);
const char* method_name     = type_reg_method_name_at(reg, 0);

bool        is_iface        = type_reg_is_interface(reg);
bool        implements      = type_reg_implements(reg, "Stream");
uint32_t    iface_count     = type_reg_implements_count(reg);
const char* iface_name      = type_reg_implements_at(reg, 0);

uint32_t    param_count     = type_reg_generic_param_count(reg);
const char* param_name      = type_reg_generic_param_at(reg, 0);
uint32_t    con_count       = type_reg_generic_constraint_count(reg);
const char* con_param       = type_reg_generic_constraint_param_at(reg, 0);
const char* con_iface       = type_reg_generic_constraint_iface_at(reg, 0);
```

### Typical pattern: dispatch through reflection

```cpp
// Pretty-printer that handles any type with a serialize hook:
std::string pretty(engine_t* e, type_id t, int64_t value) {
    const type_reg_t* reg = find_type_reg(e, t);
    if (!reg) return "<unregistered>";
    auto* ser = type_reg_serialize(reg);
    if (!ser) return std::string("<") + type_reg_name(reg) + ">";
    int64_t str = ((int64_t(*)(int64_t))ser)(value);
    std::string out(reinterpret_cast<const char*>(str));
    std::free(reinterpret_cast<void*>(str));
    return out;
}
```

### Listing generic constraints

```cpp
const type_reg_t* reg = find_type_reg_by_name(e, "hset");
for (uint32_t i = 0; i < type_reg_generic_constraint_count(reg); ++i) {
    printf("%s must implement %s\n",
        type_reg_generic_constraint_param_at(reg, i),
        type_reg_generic_constraint_iface_at(reg, i));
}
```

No hardcoding of type lists; any addon that registers a `.serialize(fn)` hook participates automatically.

## Documentation Extraction

Two SDK functions dump the full registered API surface - every global native, every registered type and its methods/fields/properties/factory/destructor - in two forms.

### `extract_documentation(engine)`

Returns a C++-ish pseudo-header as a `std::string`. Drop it into a file or render it as a code block in generated docs. Descriptions (attached via the `description` parameter on `register_native`, `.method`, `.factory`, `.destructor`, `.property`, `.field`, and the `type_builder` constructor) appear as `// ...` comments above each entry.

```cpp
std::string doc = enma::extract_documentation(engine);
std::ofstream("enma_api.h") << doc;
```

Example output:

```cpp
// RGBA color, 8 bits per channel
struct color {
    // construct color(r, g, b, a) with each channel in 0..255
    color(uint8, uint8, uint8, uint8);
    // red channel
    uint8 r();
    // green channel
    uint8 g();
    // blue channel
    uint8 b();
    // alpha channel
    uint8 a();
    // free color memory
    ~color();
}

// print a message to the host's stdout
int64 log(string msg);
```

### `extract_intellisense(engine)`

Returns a `std::vector<doc_entry_t>` with one entry per registered item. Use this to populate an IDE's autocomplete database, generate tooltips, or diff API shapes across versions.

```cpp
struct doc_param_t {
    std::string type;
    std::string name;
};

enum class doc_entry_kind : uint8_t {
    global_function, type, factory, destructor,
    method, field, property, operator_hook,
};

struct doc_entry_t {
    doc_entry_kind   kind;
    std::string      name;
    std::string      parent_type;   // "" for globals/types themselves
    std::string      return_type;
    std::vector<doc_param_t> params;
    std::string      signature;     // full sig string as registered
    std::string      description;
};
```

Example - filter to methods on the `color` type:

```cpp
auto entries = enma::extract_intellisense(engine);
for (auto& e : entries) {
    if (e.kind == doc_entry_kind::method && e.parent_type == "color") {
        printf("color.%s %s\n", e.name.c_str(), e.description.c_str());
    }
}
```

Both functions are safe to call at any point after the relevant addons, natives, and types have been registered. They don't touch engine state.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/introspection.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-lifecycle.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/lifecycle.md).

# Lifecycle & RAII

Deterministic memory model. No tracing GC. Every allocation's lifetime is bound to a lexical scope or an explicit `delete`.

| Situation                                 | Where it lives                             | When it's freed                                            |
| ----------------------------------------- | ------------------------------------------ | ---------------------------------------------------------- |
| `T x;` or `T x = T(args)`                 | Stack (default) or heap (when it escapes)  | At scope exit. Destructor runs, memory reclaimed           |
| `T x = f()` (struct-returning fn)         | Caller-supplied stack buffer (return slot) | At scope exit, dtor + free                                 |
| `T x = a + b` (operator returning struct) | Same as above                              | At scope exit                                              |
| `T* x = new T(...)`                       | Heap                                       | Manual: `delete x;` (no auto-drop for `T*`)                |
| `T* xs = new T[N]`                        | Heap (struct or primitive)                 | Manual: `delete[] xs;` (per-element ctor/dtor for structs) |
| Array / string / map                      | Heap (via addon `.factory`)                | `.destructor` runs at scope exit                           |

Heap allocator is a `malloc`/`free` wrapper with a 16-byte header (magic marker, size, type tag). `heap_collect()` is a no-op, nothing reclaims memory in the background.

## Stack structs by default

Non-escaping struct locals are stack-allocated as contiguous fields. No heap trip:

```cpp
struct Point { int32 x; int32 y; }

int32 compute() {
    Point p;             // lives on the stack, no heap alloc
    p.x = 10;
    p.y = 20;
    return p.x + p.y;
}
```

Confirm with `heap_get_stats()`:

```cpp
auto before = heap_get_stats(mod);
execute(ctx, "compute");
auto after = heap_get_stats(mod);
// after.alloc_count == before.alloc_count
```

## Struct return via return-slot

Struct returns write directly into the caller's return slot: the caller pre-allocates the stack buffer, passes its address, and the callee field-copies in. No heap trip, no intermediate temp.

```cpp
struct Box { int32 v; }

Box make_box(int32 v) {
    Box b;
    b.v = v;
    return b;               // fields copied into caller's buffer
}

int32 main() {
    Box r = make_box(42);   // r is the buffer
    return r.v;
}                            // r's destructor runs here
```

The returned local in the callee is marked as moved; its destructor does **not** run in the callee (the bytes now belong to the caller).

## Destructors run at scope exit

The user `::~T()` destructor runs at scope exit for every struct local. Normal flow, exception, or JIT fault.

```cpp
struct Counter {
    int32 id;
    ~Counter() { g_dtor_count = g_dtor_count + 1; }
}

Counter make_counter(int32 v) {
    Counter c;
    c.id = v;
    return c;
}

int32 main() {
    {
        Counter a = make_counter(1);
        Counter b = make_counter(2);
    }                        // a's dtor fires, then b's dtor fires
    return g_dtor_count;     // 2
}
```

## Exceptions don't heap

`throw T(args)` copies the value into a per-thread exception buffer. No heap allocation per throw. The catch handler reads from the same buffer.

```cpp
struct Error { int32 code; }

int32 main() {
    try {
        throw Error(42);       // bytes copied into exception buffer
    } catch (Error e) {
        return e.code;         // e reads from the same buffer
    }
}
```

Struct exceptions larger than the buffer are a compile error: *"thrown struct 'X' exceeds exception buffer size"*. Primitive throws (`throw 99`) use a direct-store path. `throw new T(args)` heap-allocates; prefer `throw T(args)`.

## Scope-drop through exceptions

When a script throws, destructors for all live scope-drop objects run before the exception reaches the catch block:

```cpp
int32 main() {
    int32 caught = 0;
    try {
        int32[] a = new int32[100];
        a.push(1);
        throw 42;           // a is dropped here, then control jumps to catch
    } catch (int32 e) {
        caught = e;
    }
    return caught;
}
```

## JIT fault unwind

Null deref, OOB array access, div-by-zero, all go through the same unwind path. The runtime fault handler walks the cleanup stack back to the `execute()` call, running every registered destructor.

```cpp
int32 main() {
    int32[] a = new int32[100];
    a.push(1);
    int32 divisor = 0;
    int32 x = 100 / divisor;   // fault
    return x;
}
```

After `execute()` returns `false`, `a` has been freed.

## Escape is a compile error

Three patterns are rejected at compile time:

```cpp
struct Point { int32 x; int32 y; }
Point g_p;

int32 escape_via_global() {
    Point p;
    p.x = 1;
    g_p = p;                 // error: stack struct escapes its scope
    return 0;
}
```

```cpp
struct Thing { int32 v; }

Thing* return_stack_ptr() {
    Thing t;
    return &t;               // error: address-of a local crossing the return
}
```

```cpp
delegate int32 Getter();
struct Point { int32 x; int32 y; }

Getter escaping_closure() {
    Point p;
    p.x = 7;
    return () => p.x;        // error: escaping closure captures stack struct
}
```

Fix by making the struct heap-allocated with `new T(...)`, or by copying values (not the struct pointer) into the escape target.

## Move semantics on return

The compiler skips the destructor on a named local that's returned through the return slot:

```cpp
Box b;
b.v = 42;
return b;                // b's dtor does NOT run here
                         // (move, the caller now owns the bytes)
```

If the return expression is a temporary (`return T(args);` or `return new T();`), the temporary's destructor is also elided.

## Annotations

### `[[noescape]]`

Enforces no allocation in the function escapes. Most escape patterns are already compile errors without it. See [Annotations](lang-annotations.md).

## For addon authors

1. Register `.destructor()` - runs at every scope exit of a local of your type.
2. Mark `.pure_methods()` for container-like types (methods don't retain receiver).
3. Mark `.pure_args()` for value/math types (methods don't retain any arg).

See [Type Registration](sdk-type-registration.md) and [Custom Addons](sdk-custom-addons.md).

## Measured impact

Heavy-loop stress (1000 arrays in a loop): 2000 alloc, 2000 freed, 0 live. See [README](readme.md) for bench numbers.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/lifecycle.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-native-functions.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/native-functions.md).

# Native Functions

Expose host functions to scripts. The sig string drives compile-time type checking at every call site and per-arg ABI routing at the native boundary.

## Registering a Function

Declare the native with real types. `register_native` passes the function through directly - the Win64 ABI placement follows the signature (int-like args in `rcx`/`rdx`/`r8`/`r9`, floats in `xmm0-3`, args 5+ on stack, narrow-int returns sign/zero-extended).

```cpp
int32_t add(int32_t a, int32_t b) { return a + b; }
register_native(e, "int32 add(int32, int32)", (void*)&add);
```

## Attaching a Description

Every `register_native` overload takes an optional trailing `description` string, surfaced via `extract_documentation` and `extract_intellisense` (see [Introspection](sdk-introspection.md)). Use it for natives whose behavior isn't obvious from the signature alone.

```cpp
register_native(e, "int64 log(string msg)", (void*)&log,
    0 /* no permissions */,
    "print a message to the host's stdout");
```

Descriptions are optional. If omitted, the entry still appears in doc output without a comment.

```cpp
double lerp(double a, double b, double t) { return a + (b - a) * t; }
register_native(e, "float64 lerp(float64, float64, float64)", (void*)&lerp);
```

Script usage:

```cpp
int32 r = add(10, 20);              // 30
float64 m = lerp(0.0, 100.0, 0.5);  // 50.0
```

Any arity, any type mix (ints / bools / chars / floats / doubles / pointers / enums / registered structs / `string` / `array` / `map`) works. The native is called directly - no int64 bit-casting, no trampolines.

There's also a template form `register_typed<&fn>(e, sig)` - equivalent to `register_native(e, sig, (void*)&fn)` but captures the function as a template parameter so the binding is one token. Pick whichever reads better.

## Supported Types

Keywords resolve to the built-in type IDs:

| Category    | Keywords                                                                                 |
| ----------- | ---------------------------------------------------------------------------------------- |
| Integers    | `int8`, `int16`, `int32`, `int64`, `uint8`, `uint16`, `uint32`, `uint64`, `char`, `bool` |
| Floats      | `float32`, `float`, `float64`, `double`                                                  |
| Strings     | `string`, `wstring`                                                                      |
| Containers  | `array`, `map`                                                                           |
| Generic     | `struct`, `class`, `pointer`, `lambda`, `function`, `void`                               |
| Placeholder | `element` (in container-method signatures)                                               |

Structs, enums, and types registered via `struct_builder`, `type_builder`, or `enum_builder` are also recognized by name - see the [Custom Types in Signatures](#custom-types-in-signatures) section below.

## Floats

Declare your C function with `float` or `double`. The JIT routes those args through xmm regs per Win64 ABI, and reads float returns from xmm0:

```cpp
double my_sqrt(double x) { return std::sqrt(x); }
register_native(e, "float64 my_sqrt(float64)", (void*)&my_sqrt);
```

```cpp
float mix(float a, float b, float t) { return a + (b - a) * t; }
register_native(e, "float32 mix(float32, float32, float32)", (void*)&mix);
```

Mix int and float args freely - placement is per-position:

```cpp
void draw(int32_t id, double x, double y, int32_t color) { ... }
register_native(e, "void draw(int32, float64, float64, int32)", (void*)&draw);
//                            ^rcx    ^xmm1    ^xmm2     ^r9
```

## Strings

String arguments pass as `const char*`:

```cpp
void greet(const char* s) {
    printf("Hello, %s!\n", s);
}
register_native(e, "void greet(string)", (void*)&greet);
```

## No-Parameter Functions

```cpp
int64_t get_time() {
    return static_cast<int64_t>(time(nullptr));
}
register_native(e, "int64 get_time()", (void*)&get_time);
```

## Custom Types in Signatures

After registering a struct, enum, or `type_builder` type, you can reference it by name in subsequent registration calls. Pass struct args as typed pointers:

```cpp
struct_builder(e, "proc_t")
    .field("pid",      type_id::t_int64)
    .field("priority", type_id::t_int64);

struct proc_t { int64_t pid; int64_t priority; };

int64_t inspect_proc(proc_t* p) {
    return p->pid;
}

register_native(e, "int64 inspect_proc(proc_t)", (void*)&inspect_proc);
```

Script usage:

```cpp
proc_t p;
p.pid = 42;
int64 x = inspect_proc(p);  // 42
```

Passing a different struct is a compile error:

```cpp
item_t i;
inspect_proc(i);   // error: inspect_proc() parameter 'arg0' expects proc_t, got item_t
```

The sig accepts `T`, `T&`, `T*` with optional parameter name. The native always receives a pointer:

| Signature | Semantics    | Native sees                              |
| --------- | ------------ | ---------------------------------------- |
| `T`       | by-value     | pointer to a copy of the caller's struct |
| `T&`      | by-reference | pointer to the caller's struct           |
| `T*`      | by-pointer   | pointer to the caller's struct           |

Mutations through `T&` or `T*` are visible to the caller; mutations through bare `T` are not.

```cpp
int64_t mutate_proc(proc_t* p) {
    p->pid += 100;
    return p->pid;
}
```

```c
// sig "int64 mutate_proc(proc_t)" by-value: p.pid stays 5
// sig "int64 mutate_proc(proc_t&)" by-ref: p.pid becomes 105
proc_t p;  p.pid = 5;
int64 r = mutate_proc(p);
```

By-value copies the struct fields at the call site (one load/store per 8 bytes).

Enums resolve to `int64` at the ABI level, but the compiler enforces enum identity at call sites:

```cpp
enum_builder(e, "Priority")
    .value("Low",    1)
    .value("Medium", 5)
    .value("High",  10);
enum_builder(e, "Color")
    .value("Red", 0).value("Green", 1).value("Blue", 2);

register_native(e, "int64 enum_double(Priority)", (void*)&enum_double_fn);
```

```cpp
int64 x  = enum_double(Priority::High);   // OK → 20
int64 y  = enum_double(42);               // compile error: expects Priority, got int32
int64 z  = enum_double(Color::Red);       // compile error: expects Priority, got Color

Priority p = Priority::Medium;
int64 w  = enum_double(p);                // OK, local is typed Priority
```

Raw ints and values from a *different* enum are rejected at compile time. Declaring a local with the enum type (`Priority p = ...;`) preserves the enum identity through the rest of the scope.

Script-side enums work too:

```cpp
enum State { Idle = 0, Running = 1, Done = 2 }
```

```cpp
register_native(e, "int64 on_state(State)", (void*)&on_state);
```

The same call-site checks fire whether the enum was registered via `enum_builder` or declared in the script.

## Delegate-Typed Parameters

Script-declared delegates work directly in native signatures:

```cpp
delegate int64 Handler(int64 x);
```

```cpp
int64_t take_handler(void* fn_ptr) {
    return fn_ptr != nullptr ? 1 : 0;
}

register_native(e, "int64 take_handler(Handler)", (void*)&take_handler);
```

```cpp
int64 doubler(int64 x) { return x * 2; }
int32 main() {
    Handler h = doubler;
    return take_handler(h);   // 1
}
```

Delegate names resolve at IR-build time (after the script is parsed), so registrations that reference delegates declared *later* in the script still work. The compiler will reject mismatched arg types at the call site (`take_handler("hello")` → compile error).

## Overloading

Register two natives with the same name but different **arities** or different **argument types** and they coexist:

```cpp
register_native(e, "int64 combine(int64)",                       (void*)&combine_1);
register_native(e, "int64 combine(int64, int64)",                (void*)&combine_2);
register_native(e, "int64 combine(int64, int64, int64)",         (void*)&combine_3);

register_native(e, "int64 pairsum(int64, int64)",                (void*)&int_sum);
register_native(e, "float64 pairsum(float64, float64)",          (void*)&float_sum);
```

```cpp
combine(5);            // → combine_1
combine(3, 4);         // → combine_2
combine(1, 2, 3);      // → combine_3
combine(1, 2, 3, 4);   // compile error: no overload for 4 arg(s)

pairsum(3, 4);         // → int_sum (int args → int overload)
pairsum(1.5, 2.5);     // → float_sum (float args → float overload)
pairsum("a", "b");     // compile error: no overload matches string
```

Resolution rules:

1. **Exact-type mangle**: first try `name$<arity>$<t1>$<t2>...`; if it exists, use it.
2. **Scored compatible match**: otherwise iterate overloads with matching arity; pick the one with the lowest conversion score. Same-category conversions (int→int64, float→float64) score 1 per arg; cross-category (int→float) scores 4.
3. **Ambiguous tie**: if two overloads have the same score, emit *"call is ambiguous across overloads"* and fail to compile.
4. **No compat match**: emit *"has no overload matching N argument(s) with given types"*.

Same arity + same types = the second registration clobbers the first.

## Typed Containers (`array<T>` and `map<K, V>`)

Specify element types in container args and returns:

```cpp
register_native(e, "int64 sum_ints(array<int64>)",           (void*)&sum_ints);
register_native(e, "int64 lookup(map<string, int64>)",       (void*)&lookup);
register_native(e, "array<int64> make_ints()",               (void*)&make_ints);
```

Script-side mismatches reject at compile:

```cpp
int64[] xs;     sum_ints(xs);    // OK
string[] ys;    sum_ints(ys);    // error: expects array<int64>, got array<string>
map<string, int64> m;  lookup(m);   // OK
map<int64, int64> n;   lookup(n);   // error: expects map<string, int64>, got map<int64, int64>

string[] bad = make_ints();      // error: returns array<int64>, cannot assign to array<string>
int64[] good = make_ints();      // OK
```

Bare `array` / `map` (no `<...>`) accepts any element type, useful for generic helpers. Overload resolution: `process(array<int>)` and `process(array<string>)` coexist and dispatch by caller's element type.

The native receives an `int64` handle. Use the addon array helpers declared in `sdk/addons/array.h` (length, get, set, push, etc.) to read or mutate.

## `const` Parameters

Mark a param as read-only:

```cpp
register_native(e, "int64 read_pid(const proc_t)", (void*)&read_pid);
```

Script-side: assigning to a field of a `const` arg inside that fn rejects at compile (`cannot assign through const ...`). Combine with `const T&` for non-mutating reference args.

## Variadic Natives

End the arg list with `...` to accept any number of additional args:

```cpp
int64_t vsum(int64_t argc, int64_t* argv) {
    int64_t s = 0;
    for (int64_t i = 0; i < argc; ++i) s += argv[i];
    return s;
}

register_native(e, "int64 vsum(...)", (void*)&vsum);
```

```cpp
vsum(1, 2, 3, 4, 5);   // 15
vsum();                // 0, no args
```

The native function takes `(int64_t argc, int64_t* argv)`. `argv` is a heap buffer of raw int64 values for every passed arg (including formal-arg prefix). Freed after the call.

Formal args may precede `...`:

```cpp
register_native(e, "int64 vlog(string fmt, ...)", (void*)&vlog);
```

```cpp
vlog("hello");              // argc=1, argv[0]=string_ptr("hello")
vlog("%d + %d", 3, 4);      // argc=3, argv=[fmt_ptr, 3, 4]
vlog();                     // compile error: expects at least 1 arg
```

The formal args are still type-checked. The variadic portion accepts any value and is always int64-boxed - use `memcpy(&d, &argv[i], 8)` to recover float args as doubles from the raw buffer.

## Default Arguments

Give natives default values via `= literal` in the sig:

```cpp
register_native(e, "int64 sum3(int64 a, int64 b = 10, int64 c = 100)", (void*)&sum3);
```

```c
sum3(1);         // b = 10, c = 100  → 111
sum3(1, 2);      // c = 100          → 103
sum3(1, 2, 3);   // all explicit     → 6
sum3();          // error: expects 1-3 argument(s), got 0
```

Int and float literals are supported (e.g. `int64 n = 42`, `float64 f = 3.14`). All defaulted args must come after all required args.

## Returning a Struct by Value

Struct returns write into a caller-supplied return slot: the native takes a hidden first arg pointing at the caller's buffer:

```cpp
struct proc_t { int64_t pid; int64_t priority; };

void make_proc(proc_t* out) {
    out->pid = 42;
    out->priority = 7;
}

register_native(e, "proc_t make_proc()", (void*)&make_proc);
```

```c
proc_t p = make_proc();   // Enma allocates the buffer, native fills it
int64  x = p.pid;         // 42
```

The first native arg is the return-slot pointer (matches the standard ABI for structs larger than a register).

## Permission-Gated Functions

Restrict a function to scripts that have specific permissions:

```cpp
register_native(e, "int64 read_memory(int64, int64, int64)", (void*)&rpm_fn, PERM_FFI);
```

On a `type_builder` method, chain `.permission(...)`:

```cpp
type_builder(e, "socket_t", ...)
    .method("int64 send_raw(int64)", (void*)&send_raw_fn).permission(PERM_FFI)
    .finish();
```

Calling a permission-gated function from a script without the matching bit in `set_permissions(engine, ...)` is a compile error.

## Registration-Time Validation

If the sig string references a type that hasn't been registered (typo like `proc_T` for `proc_t`), Enma prints a warning to stderr at registration time:

```cpp
[enma] warning: arg 0 'proc_T' in sig 'int64 inspect(proc_T)' - unresolved type; it will accept any value
```

Catches type-name typos at engine setup rather than at script call time.

## Compile-Time Syntax Validation. `ENMA_SIG(...)`

For structural errors in the sig string (missing paren, empty arg slot, illegal characters), wrap the literal in `ENMA_SIG(...)` to fail at **host compile time** via a `consteval` check:

```cpp
register_native(e, ENMA_SIG("int64 add(int64, int64)"), (void*)&add_fn);  // compiles
register_native(e, ENMA_SIG("int64 bad(,)"),            (void*)&bad_fn);  // static_assert fires
register_native(e, ENMA_SIG("int64 no_close("),         (void*)&fn);      // static_assert fires
```

The checker catches:

* Missing `(` or `)`, or trailing junk after `)`.
* Empty function name (`"() foo"`).
* Empty arg segments: `"bad(,)"`, `"bad(int,,int)"`.
* Non-identifier characters (anything outside `[A-Za-z0-9_&*=.+-]`).

`...` is accepted as a variadic arg. Type-name typos (`"int64 f(int6q)"`) aren't caught here - that's the registration-time stderr warning above. Use `ENMA_SIG` for the syntax-only layer.

## Invoking Script Closures from Background Threads

Native code that wants to call a script-side closure from a thread that isn't driving `execute()` / `call()` needs to set up per-thread state first. Use `execution_scope`:

```cpp
#include "sdk.h"
using namespace enma;

void worker_tick(context_t* ctx, int64_t fn_handle, int64_t user_data) {
    execution_scope scope(ctx);   // sets up tls heap/state/engine/... for this thread
    // ...invoke the closure via inline-asm trampoline or SDK helper...
}
```

See the [Invoking Script Closures from Background Threads](sdk-custom-addons.md#invoking-script-closures-from-background-threads) section in the custom-addons guide for the full trampoline pattern.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/native-functions.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-quick-start.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/quick-start.md).

# Quick Start

Minimal code to embed Enma in your application.

## Files You Need

* `enma.h` (umbrella) or `include/sdk.h` (just the SDK)
* One Windows lib - pick the one matching your project's CRT flag:
  * `windows/enma_x64static_mt.lib` for `/MT` (static CRT)
  * `windows/enma_x64static_md.lib` for `/MD` (dynamic CRT)
  * Mixing them produces a `RuntimeLibrary` mismatch at link time.
* Linux: `libenma.a`

All 19 shipped addons are pre-compiled into both `.lib` variants, so linking the lib is enough. Standalone `addons/em_addon_*.cpp` files still ship for reference and customization.

## Minimal Example

```cpp
#include "sdk.h"
using namespace enma;

int main() {
    // 1. Create engine
    engine_t* e = create();
    register_all_addons(e);
    set_optimize(e, true);

    // 2. Compile a script
    const char* src = R"(
        int32 main() {
            println("Hello from Enma!");
            return 42;
        }
    )";
    module_t* mod = compile(e, src, strlen(src), "hello.em");

    // 3. Execute
    context_t* ctx = create_context(mod);
    execute(ctx, "main");
    int64_t result = return_value(ctx);
    printf("result: %lld\n", result);  // 42

    // 4. Cleanup
    destroy_context(mod, ctx);
    module_destroy(mod);
    destroy(e);
    return 0;
}
```

## Compile & Link

Just link the lib - addons are bundled into it.

```bash
# Windows (clang-cl, /MT)
clang-cl /I. /MT app.cpp windows/enma_x64static_mt.lib /Fe:app.exe

# Windows (clang-cl, /MD)
clang-cl /I. /MD app.cpp windows/enma_x64static_md.lib /Fe:app.exe

# Windows (MSVC)
cl /std:c++latest /O2 /MD main.cpp windows/enma_x64static_md.lib

# Linux
g++ -std=c++23 -O2 main.cpp -lenma -o app
```

If you want a smaller binary with only specific addons, you can instead compile the `addons/em_addon_*.cpp` files you need yourself - they're standalone TUs depending only on `sdk.h`.

## What Just Happened

1. `create()` initializes the Enma JIT engine.
2. `register_all_addons()` loads all 19 shipped addons (core, string, array, map, math, simd, variant, atomic, bits, time, regex, file, hash\_set, sorted\_map, list, thread, json, vec, math3d). You can register selectively instead.
3. `compile()` takes source and produces a module of native x64 machine code.
4. `create_context()` creates an execution context (stack, locals, TLS).
5. `execute()` runs a named function.
6. `return_value()` retrieves the int64 return (use `return_string()` / `return_float()` for other types).
7. Cleanup in reverse order: context, module, engine.

## Selective Addon Registration

If you don't need all addons:

```cpp
engine_t* e = create();
register_addon_core(e);     // print functions
register_addon_string(e);   // string methods
register_addon_math(e);     // math functions
// skip array, map, simd
```

## Error Handling

If compilation fails, `compile()` returns `nullptr`. Check for errors:

```cpp
module_t* mod = compile(e, src, len, "script.em");
error_info err = last_error(e);
if (err.code != 0) {
    printf("error: %s at %s:%d:%d\n",
        err.message.c_str(), err.file.c_str(), err.line, err.column);
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/quick-start.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-safety.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/safety.md).

# Safety

Safety mechanisms at every layer.

## JIT Fault Trapping

Script faults (null deref, invalid memory access) are caught by a signal/SEH handler and mapped to source via the source map. The host receives a clean error; the application doesn't crash.

```cpp
bool ok = execute(ctx, "main");
if (!ok) {
    // fault was caught, error info has the source location
    error_info err = last_error(e);
    printf("fault at %s:%d\n", err.file.c_str(), err.line);
}
```

## Execution Budget

Prevent infinite loops and runaway scripts:

```cpp
set_budget(mod, 1000000);
```

The compiler inserts `check_budget` instructions in loop headers. When the budget reaches zero, execution halts cleanly.

## Permission System

Two flags. `PERM_FFI` (`0x01`) gates `[[dll(...)]]` calls. `PERM_FILE` (`0x02`) gates the file addon. Without the matching flag, the script can't call any function gated on it - rejected at compile.

```cpp
// user scripts: no FFI, no file I/O
set_permissions(e, 0);

// trusted addons: FFI only
set_permissions(e, PERM_FFI);

// host with file access too
set_permissions(e, PERM_FFI | PERM_FILE);
```

Custom natives can opt into the same gating via the trailing `permission` arg of `register_native` or `.permission(flags)` on a `type_builder` method.

## Memory Safety

Deterministic model. Structs stack-allocated by default. Escape patterns that would produce dangling stack pointers (return-pointer-to-local, store-to-global, escaping-closure-capture) are **compile errors**, not runtime bugs. Heap allocations have deterministic dtor + free. See [Lifecycle & RAII](sdk-lifecycle.md).

## Type Verification

The native sig string drives compile-time type checking at every call site:

* Wrong arg type, rejected.
* Wrong struct/class identity, rejected.
* Wrong enum identity (raw int or cross-enum): rejected.
* Wrong typed-container element (`array<T>` / `map<K, V>`): rejected, including return-side var-decl.
* Calling a non-`const` method on a `const` receiver, rejected.
* Assigning through a `const` parameter, rejected.

Implicit conversion via `.convert()` registered functions fires automatically at native arg, var-decl, and binary-op sites when the source/dest types differ.

## Thread Safety

* Each engine is independent, no shared mutable state between engines.
* Multiple contexts from the same module can execute concurrently.
* Per-thread TLS prevents cross-thread state corruption.
* Tested under ASAN and TSAN with 32+ concurrent threads.

## Sandboxing

For untrusted scripts, combine these techniques:

```cpp
engine_t* e = create();
register_addon_core(e);    // print only
// skip string, array, map, math, simd
set_permissions(e, 0);     // no FFI
set_budget(mod, 100000);

register_typed<&get_score_fn>(e, "int32 get_score()");
```

The script only sees what you register. No file I/O, no network, no native library access.

## Raw Pointer Safety

All values are 64-bit integers at the ABI. Pointers (strings, arrays, structs) are raw addresses. Scripts can pass arbitrary integer values to natives. Validate pointer args before dereferencing:

```cpp
int64_t my_native_fn(MyType* obj) {
    if (!obj) return 0;
    if (!heap_is_tracked(obj)) return 0;   // only for heap-tracked allocs
    // safe to use obj
}
```

Invalid pointer deref inside JIT code is caught by the runtime fault handler; `execute()` returns `false`, host stays alive. Invalid pointer deref inside a native function is **not** caught, validate on the native side.

Scripts can't call arbitrary addresses as functions. Delegates resolve at compile time to known function indices. No `invoke_fn` equivalent exists.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/safety.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-serialization-and-linking.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/serialization-and-linking.md).

# Serialization & Linking

## Precompiled Binaries (.emb)

Compile once, distribute the binary; no source required at runtime.

### Serialize

```cpp
module_t* mod = compile_file(e, "library.em");

std::vector<uint8_t> data;
serialize(mod, data);  // keep_debug=true by default

// write to file
FILE* f = fopen("library.emb", "wb");
fwrite(data.data(), 1, data.size(), f);
fclose(f);
```

#### keep\_debug — strip source paths for distribution

`serialize(module_t*, vector<uint8_t>&, bool keep_debug = true)`

When `keep_debug=false`, the serializer drops the `source_map` (per-IR file/line/column) and `debug_functions` (per-fn locals with names) tables. Use this for marketplace publishing so an uploader's absolute source path isn't baked into every record. Trade: deserialized modules have `get_last_executed_line` returning 0 and empty stack traces at runtime.

```cpp
serialize(mod, data, /*keep_debug*/ false);
```

The body of the `.emb` is also XOR-obfuscated with a per-file 32-byte salt stored in the header (k\_emb\_version 4). Defeats casual `strings <file>` inspection of fixup keys, native names, struct field names. Decryption happens transparently inside `deserialize` — no caller-side change.

### Deserialize

```cpp
// read from file
std::vector<uint8_t> data = read_binary_file("library.emb");

module_t* mod = deserialize(e, data.data(), data.size());
context_t* ctx = create_context(mod);
execute(ctx, "main");
```

## Linking Multiple Modules

Combine separately compiled modules, resolving cross-module calls.

```cpp
module_t* math_mod = compile_file(e, "math.em");
module_t* game_mod = compile_file(e, "game.em");

const char* names[] = { "math", "game" };
module_t*   mods[]  = { math_mod, game_mod };
module_t*   linked  = link(e, names, mods, 2);

context_t* ctx = create_context(linked);
execute(ctx, "main");
```

In the script, linked modules are accessed by their name prefix:

```cpp
// game.em can call:
int32 r = math::sqrt_int(16);
```

## Module Cleanup

```cpp
module_destroy(math_mod);
module_destroy(game_mod);
module_destroy(linked);
```

Destroy each module separately. The linked module does not own its inputs.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/serialization-and-linking.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/enma/sdk-type-registration.md`

> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/type-registration.md).

# Type Registration

`type_builder` exposes native types to scripts: fields, methods, properties, operators (full set including `opCmp`, compound assign, `++`/`--`), subscript, iteration, conversion, factory, destructor.

## Descriptions

Every hook that takes a signature or name also takes an optional trailing `const char* description`. These surface via [`extract_documentation`](sdk-introspection.md) and `extract_intellisense` for IDE tooling and auto-generated docs.

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

---

## Source: `docs/perception/analyzer.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/perception-analyzer.md).

# Perception Analyzer

The Perception Analyzer is an integrated binary analysis tool built into the Perception.cx platform. It provides IDA-style disassembly, a full F5 decompiler, source reconstruction, hex viewing, memory scanning, and structure editing — all operating directly on live processes through Perception's memory access layer.

The Analyzer is designed from the ground up for speed. Analysis that takes minutes in traditional tools completes in seconds. Function detection, cross-reference building, string scanning, and decompilation all run in parallel across multiple threads, keeping the UI fully responsive throughout.

I am also actively working on the **Reconstruct Source** feature shown in the screenshots below. This feature is still experimental and not yet fully mature, but it is being continuously developed with the goal of becoming a truly state-of-the-art reconstruction system.

If this feature interests you and you would like to help improve it, please feel free to share suggestions and bug reports.

— **Timefall / Admin**

<div data-with-frame="true"><figure><img src="/files/FZZ90AC37miYmZdG7Xkb" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/DMNE7GLLFImh6p02hgkb" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/2rC0qAp57uTxmqTCz9ym" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/Taw90mKYeYLQoZzWkxkP" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/sjHvNmCl2y4E8mBFc2ne" alt=""><figcaption></figcaption></figure></div>

F5 Decompiler (Advance Decompiler - Generates Pseudo C) - This feature is still under development with ongoing tests and improvements.&#x20;

<div data-with-frame="true"><figure><img src="/files/IbCwMY3qnzViLJxa5mEz" alt=""><figcaption></figcaption></figure></div>

<div align="center"><figure><img src="/files/dV6BHzb2Gv5D1Wc990Cs" alt=""><figcaption></figcaption></figure></div>

The experimental **Reconstruct Source** feature generates a full project-style source reconstruction from a binary with a single click.

The output includes:

* **Header files** — types, structs, enums, globals, imports, vtables, string constants, and static data references
* **Source files** — decompiled functions grouped into named modules (e.g., `module_render`, `module_network`, `module_audio`)
* **Common helpers** — frequently used utility functions extracted into `common.cpp`
* **Hostile / unresolved functions** — obfuscated or failed functions emit `__asm {}` blocks with the raw disassembly
* **Analysis metadata** — cross-references and module assignments exported as JSON

The project structure and files shown below are generated automatically using the **Reconstruct Source** button.

<div data-with-frame="true"><figure><img src="/files/24iiTjKioUQI4O0NNCmX" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/7SdoNUWpj7CDYk6e9U9d" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/X7Zs63fV4KgDdutN4cMI" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/PJCb9CIkhrwfELmO87Hp" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/PqTklI8yNA79mAmL4Fzi" alt=""><figcaption></figcaption></figure></div>

***

### Getting Started

#### Attaching to a Process

<div align="left" data-with-frame="true"><figure><img src="/files/iKnctDv3lTMF4jZsnFID" alt=""><figcaption></figcaption></figure></div>

When the Analyzer opens, you are presented with a process selection screen. All active processes detected by Perception are listed. You can filter the list by typing in the search field at the top.

Click a process to select it, then click **Attach** to begin analysis.

#### Module Loading Modes

<div align="left" data-full-width="false" data-with-frame="true"><figure><img src="/files/LV0wC6heTp5rWgInem85" alt=""><figcaption></figcaption></figure></div>

Before attaching, you can choose how modules are loaded using the **Module Loading** pills at the bottom of the process selection card:

| Mode         | Behavior                                                                                                                                              |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Disabled** | No modules are analyzed.                                                                                                                              |
| **Primary**  | Only the main executable is fully analyzed. Other modules receive header-only loading (exports + sections visible, disassembly via on-demand decode). |
| **Selected** | After attaching, a checkbox list lets you choose which modules to fully analyze. The main executable and critical system DLLs are always included.    |
| **All**      | Every loaded module is fully analyzed. This can take significantly longer for large processes.                                                        |

> **Header-only modules** are still browsable — you can view exports, navigate sections, and disassemble code on the fly. Full analysis adds function detection, cross-references, and string identification.

**Module Switching**

Once attached, the module badge in the toolbar (e.g., `smss.exe`) acts as a dropdown. Click it to switch between loaded modules. A filter field at the top of the dropdown lets you search by module name.

***

#### Views

The Analyzer has five main views, accessible from the tab bar at the top of the workspace:

**Disasm (Disassembly)**

The primary view. Displays a linear disassembly of the current module with:

* **Address column** — Virtual addresses or symbol labels (e.g., `str_7FF7D1C92778:` for strings)
* **Bytes column** — Raw instruction bytes (toggle in Settings)
* **Mnemonic column** — Instruction mnemonic with syntax coloring (calls, jumps, returns, NOPs)
* **Operands column** — Instruction operands with resolved targets
* **Comment column** — Auto-generated cross-reference hints and string previews

**Function headers** appear as highlighted bars showing the function name, size, and xref count. **Labels** (`loc_xxxx:`, `sub_xxxx:`) mark branch targets and function entries. **String references** display IDA-style with the symbol name in the address column and the quoted string value at the mnemonic position.

**Navigation**

| Action                      | Effect                                                                    |
| --------------------------- | ------------------------------------------------------------------------- |
| Click a branch target       | Navigate to that address                                                  |
| `Ctrl+G`                    | Go to address (supports hex, decimal, and expressions like `base+0x1000`) |
| `Alt+Left` / `Alt+Right`    | Navigate back / forward                                                   |
| `M4` / `M5` (mouse buttons) | Navigate back / forward                                                   |
| `Ctrl+F`                    | Open search popup                                                         |
| `Page Up` / `Page Down`     | Scroll by screen                                                          |
| `Shift+Scroll`              | Horizontal scroll                                                         |
| `Home`                      | Reset horizontal scroll                                                   |

**Search**

Click the **Search** button or press `Ctrl+F` to open the search popup. Toggle between **Hex** and **String** mode using the pills:

* **Hex mode** — Pattern search with wildcards: `48 8B ?? 4C 89 ...` (`??` matches any byte)
* **String mode** — Case-insensitive text search

Results are navigated with the **Prev** / **Next** buttons. The status bar shows the current match index and total count.

> Searches scan PE sections only — headers, padding, and zero-filled regions are excluded.

**Symbols and Comments**

| Key | Action                                       |
| --- | -------------------------------------------- |
| `N` | Rename the symbol at the current address     |
| `;` | Add or edit a comment at the current address |

Renames and comments are saved with the session and persist across restarts.

***

**Hex**

A traditional hex editor view of the module's raw image. Displays bytes in configurable columns with an ASCII sidebar. Useful for inspecting data regions, padding, and raw binary content.

***

**Types (Structure Editor)**

A ReClass-style structure editor for defining and inspecting memory layouts.

**Creating Structures**

1. Click **New** in the left panel to create a new struct.
2. Set the **Name** and **Base Address** fields at the top.
3. Click any type button in the toolbar to add a field:

| Category | Types                                                        |
| -------- | ------------------------------------------------------------ |
| Integer  | `Hex8`, `U8`, `U16`, `U32`, `U64`, `I8`, `I16`, `I32`, `I64` |
| Float    | `Float`, `Double`                                            |
| Other    | `Bool`, `Ptr`, `UTF8`, `UTF16`, `Pad`                        |
| Vector   | `Vec2`, `Vec3`, `Vec4`, `Vec2D`, `Vec3D`, `Vec4D`            |
| Matrix   | `M3x4`, `M4x4`, `M3x4D`, `M4x4D`                             |

Fields are displayed with their offset, type, name, and live value read from the target process.

**Editing Fields**

| Key             | Action                                              |
| --------------- | --------------------------------------------------- |
| `T` / `Shift+T` | Retype the selected node (cycle forward / backward) |
| `R`             | Rename the selected node                            |
| `Delete`        | Delete the selected node                            |

**Import / Export**

* **Import** — Paste a C-style struct definition to auto-generate fields.
* **Export: C++** / **Export: AS** / **Export: Lua** — Export the struct as code in the selected language.

> Structures are saved automatically and persist across sessions.

***

**Scan (Memory Scanner)**

A live memory scanner for finding values in the target process's address space.

**First Scan**

1. Select the **Type** (UInt8 through Double, String, or WString).
2. Select the **Compare** mode:

| Compare       | Description                                  |
| ------------- | -------------------------------------------- |
| Exact         | Value equals the input exactly               |
| Greater Than  | Value is greater than the input              |
| Less Than     | Value is less than the input                 |
| Unknown Value | Capture all addresses (for later refinement) |

3. Enter a **Value** (not needed for Unknown Value).
4. Click **First Scan**.

**Next Scan**

After the first scan, refine results with additional compare modes:

| Compare   | Description                   |
| --------- | ----------------------------- |
| Changed   | Value changed since last scan |
| Unchanged | Value stayed the same         |
| Increased | Value increased               |
| Decreased | Value decreased               |

Click **Next Scan** to filter. Click **Clear** to reset and start over.

**Options**

* **Aligned Only** — Only scan addresses aligned to the data type size (faster, may miss unaligned values).
* **Heap Only** — Restrict scanning to heap memory regions.

> String and WString scans compare the full byte pattern. WString automatically converts the input to UTF-16 (little-endian) before scanning.

***

**Settings**

Configure Analyzer behavior:

| Setting                       | Description                                                           |
| ----------------------------- | --------------------------------------------------------------------- |
| **Scroll Speed**              | Adjusts scroll sensitivity across all views (slider, 0.01–2.0)        |
| **Hex Refresh Interval**      | How often live values refresh in the Hex and Types views (50–5000 ms) |
| **Show bytes in disassembly** | Toggle the raw bytes column in the Disasm view                        |
| **Show inspector panel**      | Toggle the right-side inspector panel                                 |

All settings are saved automatically and persist across restarts.

***

#### Inspector Panel

The right-side panel displays context-sensitive information about the currently selected address:

**Location**

Shows the virtual address (VA), relative virtual address (RVA), section name, containing function, and symbol name.

**Xrefs To**

All cross-references pointing **to** the current address — calls, jumps, conditional jumps, and data references. Each entry shows the xref type and the source function name. Click to navigate.

**Xrefs From**

All cross-references going **from** the current address to other locations.

**Bytes**

A hex dump of the bytes at the current address.

**Callers**

Functions that call the current function (derived from call-type xrefs to the function's entry point).

**Callees**

Functions called by the current function (unique call targets within the function body).

> All inspector sections have a fixed height with independent scrolling and scrollbar indicators.

***

#### Sidebar

The left panel provides filtered, searchable lists:

| Tab           | Contents                                                                                                                  |
| ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Functions** | All detected functions with xref counts. Click to navigate.                                                               |
| **Imports**   | Imported functions grouped by DLL. Click to navigate to the IAT entry.                                                    |
| **Exports**   | Exported functions. The entry point is listed as `DllMain` or `WinMain`.                                                  |
| **Strings**   | Detected strings with their section and value. Click to navigate.                                                         |
| **Sections**  | PE sections with flags (XRW), virtual address, size, and entropy. Process information (PID, module count) is shown below. |

All tabs support text filtering. Type in the filter field to narrow results.

***

#### Toolbar

The toolbar provides quick access to common actions:

| Button          | Action                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Search**      | Opens the hex/string search popup                                                                                                    |
| **Detach**      | Saves the session and returns to the process selection screen                                                                        |
| **Dump**        | Opens the dump popup for saving the module image to disk                                                                             |
| **Reconstruct** | Opens the source reconstruction popup — decompiles all functions and exports a full project with headers, source files, and metadata |
| **Re-resolve**  | Re-reads zero-filled pages from the target process and rebuilds data cross-references                                                |

**Dump**

The dump popup lets you save the current module's memory image to disk:

* **Output Path** — The file path for the dump. Defaults to `[module_name]_dump.exe` or `[module_name]_dump.dll` in the scripting directory.
* **Wait for VEH** — Enable this for processes with page encryption (e.g., games using VEH-based decryption). The dumper will repeatedly read zero-filled / invalid pages within the timeout, waiting for the VEH handler to decrypt them.
* **Timeout** — How long to wait for VEH decryption (1–60 seconds).

After dumping, the status bar reports how many pages were recovered via VEH.

***

#### Sessions

The Analyzer automatically saves and loads session data per module:

* **Cursor position** — Restored on next attach
* **Custom renames** — Symbol names you've assigned with `N`
* **Comments** — Annotations you've added with `;`
* **Bookmarks** — Saved address bookmarks

Sessions are stored as encrypted `.pak` files in the scripting directory and are keyed by module name.

***

#### Context Menu

Right-click in the disassembly or sidebar function list to access context actions:

| Action                 | Description                                                                                                                                                                                   |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Make Function**      | Define a new function starting at the selected address                                                                                                                                        |
| **Copy Address**       | Copy the virtual address to the clipboard                                                                                                                                                     |
| **Copy Function ASM**  | Copy the full disassembly of the containing function                                                                                                                                          |
| **Dump Function Info** | Copy a complete analysis dump: the function's assembly, its F5 decompiled output, and the assembly of all called/referenced functions. Useful for sharing context with AI tools or teammates. |
| **Make Signature**     | Generate a byte pattern signature with wildcards for the instruction at the current address                                                                                                   |

***

#### Keyboard Shortcuts

| Shortcut        | Action                         |
| --------------- | ------------------------------ |
| `Ctrl+G`        | Go to address                  |
| `Ctrl+F`        | Search (hex pattern or string) |
| `Alt+Left`      | Navigate back                  |
| `Alt+Right`     | Navigate forward               |
| `M4` / `M5`     | Navigate back / forward        |
| `Ctrl+S`        | Save session                   |
| `Ctrl+M`        | Switch module                  |
| `T` / `Shift+T` | Retype struct node             |
| `R`             | Rename struct node             |
| `Delete`        | Delete struct node             |
| `N`             | Rename symbol (disasm)         |
| `;`             | Add comment (disasm)           |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/perception-analyzer.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/changelogs.md`

# Perception.cx Changelogs (2026)

Complete changelog archive from the Perception.cx forums, covering Universal API and CS2 API updates.

---

## April 6, 2026 — Universal API

### Analyzer
- Significantly reduced overall memory usage
- Fixed access violation exceptions caused by the reconstruction system
- Fixed freezes and deadlocks in the reconstruction pipeline during function decompilation and optimizer state handling
- Significantly improved the decompiler, with better calibration for obfuscated routines and added switch statement resolution

---

## April 1, 2026 — Universal API

### IDE + Tooling Updates
- Fixed the tool call system and state cleanup when resending, starting a new chat, or clearing chat
- Added scroll-to-top and scroll-to-bottom actions in the assistant dropdown
- Ctrl+C no longer cancels streaming — only copies text as expected
- **run_in_terminal** — fixed multiline output capture; description now warns against blocking commands
- **wait_for_user** — pauses the AI until the user clicks Continue
- **ask_mcq** — added inline multiple choice UI with checkbox/radio selection
- **update_notes** — added append mode for incremental note-taking

### IDE
- Added support for **.tsx**, **.jsx**, **.vue**, **.go**, and **.cs**
- Expanded IntelliSense keywords and snippets across 11 languages

### Analyzer — Stronger Decompiler
- Fixed 32-bit register width handling where x64 zero-extension was being lost
- Noreturn detection now works for indirect jump-through-IAT patterns (e.g. NtTerminateProcess)
- Added semantic variable naming for API results (status, buffer, isSpace, etc.)
- Merged declaration + initialization output where possible
- Simple bodies now emit single-line `if` statements when appropriate
- Hex literals enabled by default (toggle in settings)
- Removed fake saved-register arguments from function signatures
- Struct field generation more conservative — prevents phantom `field_0xNN` members
- Added opaque predicate stripping, empty-if removal, argument alias elimination

### Assembly Output
- Added checkbox to make `.asm` generation optional

### Reconstruction System
- Reworked the reconstruction system (still maturing — may freeze in decompiler-heavy cases)

---

## March 31, 2026 (b) — Universal API

### Perceptproof Overlay Protection
New dropdown under overlay protection settings with three protection levels:

| Mode | Description |
|------|-------------|
| **Disabled** | Zero protection — overlay visible to recording software (Discord, OBS, etc.) |
| **Default** | Standard protection for Discord, clips, most games (CS2, COD, etc.) |
| **Perceptproof** | Maximum protection for aggressive screenshot-based anti-cheat systems |

Perceptproof handles visuals in a way that keeps them fully hidden from aggressive screenshot systems. Uses more GPU resources while active.

For normal games, Default mode is sufficient. Perceptproof is proactive protection against AI/kernel screenshot-based detection trends in modern anti-cheats.

---

## March 31, 2026 (a) — Universal API

### Analyzer
- Reconstruction fixes and proper progress display
- Fixed several out-of-memory issues, memory leaks, and excessive memory usage
- Decompiler structural improvements

### IDE Chatbot
- Fixed hallucination issues caused by context trimming during context saving
- Improved context handling to save more tokens; updated the notes system

---

## March 30, 2026 (b) — Universal API

### Major Update

- **Fully redesigned IDE**
- **Copilot + GitHub Models integration** — connect your GitHub Copilot account and use your Copilot tokens
- **Expanded RE Utilities into full Analysis Tool** — faster module analysis + experimental binary-to-source extraction and decompiler
  - Full analysis of 100MB+ binaries in ~12 seconds (multithreaded, 1M+ targets)
  - Compared to IDA Pro which can take over an hour for the same task

### GUI
- New taskbar (top-middle) — minimize, maximize, or force Perception GUI / Analyzer / Editor / Console Logger to stay on top

### IDE Changes (UI + Copilot)
- Entire IDE UI reworked
- Summarise and Continue refined for smoother experience
- Added GitHub Models and Copilot Auth
- IDE chatbot not limited to Perception scripting — assists with website creation, general development, VS/VS Code projects

### Overlay
- Screenshot proofing hardened (stream proof cannot be disabled due to this addition)

---

## March 30, 2026 (a) — Universal API

- Re-added option to enable/disable Stream Proof / Anti Screenshot
- Improved overall stability of the Stream Proof / Anti Screenshot system

---

## March 20, 2026 — Universal API

### Perception Engine
- **Fullscreen mode** — universal support for all games, enabled by engine and overlay improvements

### Overlay
- Backend redone — PCX client now "refreshes" Windows Explorer (expected behavior)
- Message queue optimizations
- Fixed memory-related BSODs under low RAM conditions
- Overlay no longer crashes on Alt+F4

### Allocation API
- Updated virtual memory allocation — no longer causes BSODs or instability
- **NOTE:** Must disable Control Flow Guard (CFG) to execute allocated memory + enable Insecure API in menu

### IDE
- **Enter key indent fix** — only `{` triggers indentation (not `if()`/`for()`/`while()`)
- **Symbol occurrence highlighting** — double-click a variable/function name to highlight all matching occurrences (VS Code-style)
- **Scrollbar marks** — find matches and highlighted occurrences shown in scrollbar

---

## March 18, 2026 — Universal API

### Security
- All configuration files and data now encrypted as `.pak` files for file-system heuristic protection
- **Clear Documents/My Games folder entirely before loading this update**

### AngelScript API — Unicorn Emulator
- Null pointer access now caught gracefully — emulation stops instead of crashing
- Added `UC_HOOK_INSN_INVALID` — invalid instructions stop emulation with a logged message
- Added `UC_HOOK_INTR` — software interrupts (INT3, syscalls) stop emulation cleanly
- Added `uc_get_last_exception(handle)` — returns NTSTATUS exception code (e.g. `0xC0000005` for access violation)
- Added `uc_get_exception_address(handle)` — returns RIP where the exception occurred

### GUI
- Config files encrypted into `.pak` files
- UI state encrypted
- Added **force render key** — RE Tools rendered while UI hidden using configured keybind

### IDE
- Timeline backups, chat history, editor state all saved as encrypted `.pak` files
- Backups now saved in platform data directory instead of project root

### RE Tools
- Saved state and structures encrypted (`re_state.pak`, `re_structs.pak`)
- Added **Ctrl+C** in scanner — copies all scan results to clipboard as tab-separated text

---

## March 17, 2026 (b) — Universal API

### AngelScript API
- Fixed `get_gui_pos` position issue
- Added optional `bool render_on_top = false` argument to `register_callback` — renders callback content on top of everything else

### IDE — Tandem AI
- **Tandem AI** — two models cooperate via `switch_model` tool. Planning/Reasoning model handles analysis; Implementation/Coder model handles code and validation. Optional separate endpoint + API key for coder model. Leave coder field empty for single-model mode
- Automatic context trimming — tool results and write arguments compressed to compact summaries after each turn
- Added `manage_context` tool — AI can drop unneeded tool categories or trim old history
- Improved Summarize & Continue — larger limits, structured summaries preserving goal/changes/pending work
- Send validation — error message if URL or model is missing
- Fixed auto-scroll on single click near editor edges
- Fixed crash on editor close when background AI threads were mid-request

---

## March 17, 2026 (a) — Universal API

### 🔺 Custom Draw API — Major 3D, Compute & Rendering Expansion

Indexed rendering, depth testing, rasterizer state, viewports, multi-texture binding, compute shaders, structured buffers, mesh loading, dynamic textures, backbuffer capture.

**New in this update:**
- **Indexed Drawing** — shared vertices reused via 16-bit and 32-bit index buffers
- **Depth Testing** — depth buffer creation, clearing, binding, configurable depth-stencil state
- **Rasterizer State** — culling and fill mode control (wireframe, solid, no-cull)
- **Custom Viewports** — split-screen or picture-in-picture rendering
- **Multi-Texture Binding** — bind multiple textures to a shader simultaneously
- **Compute Shaders** — GPU compute from AngelScript with structured buffers
- **OBJ Mesh Loading** — load `.obj` files, returns vertex + index buffer handles
- **Dynamic Textures** — create and update textures at runtime
- **Multi-Constant-Buffer Binding** — bind multiple constant buffers to different slots
- **Depth-Enabled Render Targets** — render targets with attached depth buffers
- **Backbuffer Capture** — capture current frame as a texture for post-processing

---

## March 16, 2026 — Universal API

### 🔺 Custom Draw API — Direct GPU Access from AngelScript

Full custom shader pipeline. Direct D3D11 GPU access — HLSL shaders, vertex buffers, textures, render targets, any primitive topology.

Custom draw commands respect draw order with all existing render functions.

**New Features:**
- **Shaders** — write HLSL vertex and pixel shaders, compiled at runtime. Layout defined with format string
- **GPU Resources** — vertex buffers, constant buffers, blend states, samplers, textures, render targets
- **All Primitive Topologies** — triangle list/strip, line list/strip, point list
- **Render Targets** — offscreen rendering for multi-pass effects
- **Textures & Samplers** — create textures from raw RGBA data, point/linear/anisotropic filtering

All resources encrypted, automatically cleaned up on script unload.

---

## March 16, 2026 — Counter-Strike 2

Custom Draw API (same as Universal API update) pushed to CS2 product.

---

## March 14, 2026 — Universal API

### Sound API (new)
- Full audio engine with waveOut double-buffered mixer, 44100Hz stereo, up to 64 simultaneous instances
- `load_sound` / `free_sound` / `play_sound` / `stop_sound` / `stop_all_sounds`
- Real-time `set_sound_volume` (0–1) and `set_sound_pan` (-1 to +1)
- Looping via `play_sound(..., loop=true)`
- WAV (PCM 8/16-bit) parsed directly, MP3/AAC/WMA/FLAC decoded via Media Foundation
- All audio decoded to PCM at load time — `play_sound` is zero-cost
- Auto-cleanup: leaked sound handles freed on script unload

### VAD / Memory Scan API Fixes
- Fixed `get_vad_snapshot` returning all-zero fields
- Scan functions return `array<uint64>@` (not void with `&out` params)
- Removed nonexistent functions from docs: `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64`
- Added missing functions: `scan_float`, `scan_double`, `scan_string`, `scan_wstring`, `scan_pointer`

### Extensions
- Extension system — `.as` files in `extensions/` auto-detected, ON/OFF toggle, reload, error display
- Full lifecycle hooks: activate, deactivate, tick, file/tab events
- AI pipeline hooks: intercept prompts, inject system context, register custom tools
- Custom IntelliSense: completions and hover tooltips for any file type
- Widget API for settings: checkboxes, sliders, buttons, inputs, text areas, progress bars, dropdowns, color pickers, keybinds
- Platform API access: rendering, input, CPU intrinsics, WinAPI, JSON, Zydis
- Editor API: insert/replace text, set selection, open/save files, goto line
- File I/O, clipboard, synchronization

---

## March 12, 2026 — Universal API

### IDE AI Chatbot Fixes
- Fixed auto-compaction breaking chat after compacting tool call sequences
- Fixed `read_file` overwriting wrong buffer when only one file open
- Fixed workspace path confusion across workspaces
- Fixed `create_file` failing when parent directories don't exist
- Fixed assistant text Copy button not working when overlapping Thinking block
- Fixed AI freezing on certain tool calls involving large files

### New Features
- **OpenRouter Web Search** — `web_search` tool works automatically on OpenRouter endpoints
- **Text selection** in chat — click and drag to select, Ctrl+C to copy
- **Markdown rendering** for links, blockquotes, lists, task checkboxes (during streaming)
- Explorer shows actual directory name instead of hardcoded "Root"
- AI checks file size before reading unknown files

---

## March 11, 2026 — Universal API

### IDE Update — Major Quality Improvement

**AI:**
- Full absolute paths for all file operations
- Context lists all workspace roots with full paths and labeled file trees
- `list_files` shows all workspace roots at once
- Perception API IntelliSense injects both AngelScript and Lua API references when enabled

**Workspace:**
- Multi-root workspace folders — add additional project folders alongside main root
- Manage extra workspace folders from Settings → Project

**Explorer:**
- Right-click context menu: Cut, Copy, Paste, Copy Path
- Recursive folder copy with rename-on-conflict

**Compaction:**
- Fixed auto-compaction triggering too early

---

## March 8, 2026 — Universal API

- **Heavy CPU optimizations** — average scene CPU usage reduced from ~10% down to ~1% (0.8–2% typical)
- **Added professional IDE** with built-in AI assistant (separate GUI)
- **Added reverse engineering tools** (separate GUI)
- Removed legacy RE tools and old chatbot system
- **Added 32-bit games support**

---

## February 17, 2026 — Universal API

### GUI
- Added list widget functions: `list:get`, `list:remove`, `list:highlight`, `list:remove_highlight`, `list:hide`, `list:show`
- Clear button removed for console (use third button)

### Console Logger
- Completely redone, now resizable

---

## February 12, 2026 — Universal API

### Input System
- Mouse delta now returns proper movement delta instead of screen-space delta
- Controller keybinds supported via XINPUT

### RE Tools
- Executable-section-only pattern searches
- Fixed single-hit pattern searches

### Render System
- Script render order reversed — newly created callbacks render first

### AI Chatbot
- Added support for GLM-5

### AngelScript
- Added: `get_gui_position(float &out x, float &out y)`
- Added: `get_gui_size(float &out w, float &out h)`

---

## February 3, 2026 (b) — Universal API

### Render Engine
- Optimized backend performance
- Font loading now instant

### AngelScript & Lua
- Optional `glyph_ranges` argument added to `create_font` and `create_font_mem`
- Matrix4x4 double-precision functions:
  - `readas_float` / `writeas_float` — float precision
  - `readas_double` / `writeas_double` — double precision
- Replaced `source2_world_to_screen` with:
  - `world_to_screen_rowmajor(...)` ⚠️ migration required
  - `world_to_screen_transposed(...)` (new)

### AngelScript
- Thread priority: `set_thread_to_highest_priority()`, `set_thread_to_lowest_priority()`, `set_thread_to_normal_priority()`
- **Atomic API** — `atomic_int32`, `atomic_int64` for lock-free thread-safe shared state

### Deprecated
- `source2_world_to_screen` → migrate to `world_to_screen_rowmajor` or `world_to_screen_transposed`
- Default matrix4x4 read/write → use precision-specific variants

---

## February 3, 2026 (a) — Universal API

### GUI
- Fixed list widget selected index becoming incorrect on add/remove

### RE Tools
- Fixed process selection becoming unselected
- Fixed pattern scan log output
- Fixed "Selected address" and "offset" not populating from scan results
- Disassembly output now includes section name (e.g. `winlogon.exe+0x2000 (.text)`)

### AngelScript
- Added optional viewport parameter to Source 2 W2S:
  ```
  bool source2_world_to_screen(const vector3 &in, const matrix4x4 &in, vector2 &out, const vector2 &in viewport = vector2(0, 0))
  ```

---

## February 1, 2026 — Universal API

### AngelScript & Lua
- Added `get_all_hwnds()` — returns all window handles

### AngelScript
- Fixed `hash_map` reference issue when initializing as global

---

## Enma Open Beta — Phase 2 (May 2026)

### Enma Language
- Perception's proprietary programming language, built from scratch
- **Pure Full-Module AOT and JIT** — no interpreter, no VM, compiles to native machine code
- **C/Rust-tier performance** — real benchmarks (600+ FPS in Rust, single-threaded)
- **C++-flavored syntax** — mostly familiar, cleaner and easier to pick up
- Battle-tested in private beta

**Documentation:**
- [enma-1.gitbook.io/enma](https://enma-1.gitbook.io/enma)
- [docs.perception.cx/perception/enma](https://docs.perception.cx/perception/enma)

### New Modular UI System
- Fully modular — independent, reusable UI components
- Rich new APIs from community most-requested list

### Perception MCP (60-70+ tools)
- Direct AI integration (Claude Opus, etc.)
- Script execution & validation
- Logging & error analysis
- Memory analysis tooling

### IDE & Analyzer Discontinued
- IDE and Analyzer being retired — replaced by Perception MCP
- Maintaining them solo was no longer sustainable

### New Script Market (Coming Summer 2026)
- Brand new website, built from ground up
- Single payment systems (OxaPay, crypto)
- Better moderation and quality control
- Collaborative features
- Direct Perception integration

### Subscription Tiers
| Tier | Price | Includes |
|------|-------|----------|
| **Universal API** | $54.99/month | Full access: all APIs, IDE, AI, Analyzer |
| **CS2 API** | $7.99/30 days | CS2-only framework, script execution + API access |

Universal API capped at 450 users maximum.

---

## Source: `docs/perception/cpu-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/cpu-api.md).

# CPU API

All CPU natives are auto-registered into every loaded script.

Stuff that doesn't fit cleanly into other host APIs and isn't already in Enma's preshipped addons. For wall-clock time, ISO formatting, and `unix_seconds()` see the preshipped [Time](https://enma-1.gitbook.io/enma/addons/time) addon. For `popcount`/`clz`/`bswap` etc., the preshipped [Bits](https://enma-1.gitbook.io/enma/addons/bits) addon.

## CPU identification

```cpp
string cpu_vendor();   // CPUID leaf 0, e.g. "GenuineIntel"
string cpu_brand();    // CPUID leaves 0x80000002..4, e.g. "Intel(R) Core(TM) i9-..."
```

## Timing

```cpp
int64 rdtsc();              // raw cycle counter; not stable across cores or sleep
int64 perf_time();          // QueryPerformanceCounter
int64 perf_frequency();     // counter ticks per second
int64 get_tickcount64();    // ms since system boot (monotonic, 64-bit safe)
```

`perf_time / perf_frequency` together give sub-microsecond timestamps:

```cpp
int64 t0 = perf_time();
do_work();
float64 secs = cast<float64>(perf_time() - t0) / cast<float64>(perf_frequency());
```

## Datetime helpers

Companions to the preshipped `time` addon's `year`/`month`/`day`/`hour`/`day_of_week`/etc. decoders. The `time` addon takes a unix timestamp; these convert intermediate fields:

```cpp
int64  now_millisecond();          // 0..999, current local time
string day_name(int64 dow);        // 0..6 -> "Sunday".."Saturday"; "Unknown" out of range
string month_name(int64 month);    // 1..12 -> "January".."December"; "Unknown" out of range
int64  hour12(int64 hour24);       // 0..23 -> 1..12 (12-hour wall format)
string ampm(int64 hour24);         // 0..23 -> "AM" / "PM"
```

## Bitcasts (float ↔ int)

Use the language built-in `reinterpret_cast<T>(val)`. Reinterprets the bit pattern; not a value conversion. Source and target must be the same byte size; emits a compile error otherwise.

```cpp
uint32  u    = reinterpret_cast<uint32>(1.5f);            // 0x3FC00000
float32 f    = reinterpret_cast<float32>(0x3FC00000u);    // 1.5
uint64  bits = reinterpret_cast<uint64>(3.14);            // IEEE 64-bit pattern
uint32  sign = reinterpret_cast<uint32>(-3.14f) >> 31;    // 1
```

Compiles to at most 2 mov instructions (`narrow_f32` + `cast` at the f32 boundary, plain `cast` elsewhere) — zero call overhead. Generalizes to any same-size pair: pointers ↔ `int64`, mixed signed/unsigned narrow ints, etc.

For narrow-int → wider-int (no float involved), `cast<uint32>(some_int8)` etc. works directly — Enma keeps narrow ints zero/sign-extended in 64-bit slots, so the cast is a free rename.

## Thread priority

Affects whatever thread invokes the call. Routine callbacks run each tick on their own ticker thread, so calling from a routine adjusts that ticker thread (NOT the script's main thread).

```cpp
bool set_thread_priority(thread_priority p);
```

`thread_priority` enum values: `lowest`, `below_normal`, `normal`, `above_normal`, `highest`.

```cpp
set_thread_priority(thread_priority::highest);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/cpu-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/custom-draw-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/custom-draw-api.md).

# Custom Draw API

The Custom Draw API gives scripts direct access to the **D3D11 GPU pipeline**. Write HLSL vertex, pixel, and compute shaders, create vertex/index/constant/structured buffers, textures, render targets, and depth buffers, then submit geometry with any primitive topology — all from script.

Custom draw commands respect draw order with every other render function. If you call `draw_rect_filled`, then `custom_draw`, then `draw_text`, they render in exactly that submission order.

These natives are part of the Render API and are auto-registered into every loaded script. Handles (`int64`) are encrypted pointers — pass them back into other calls, never dereference or do arithmetic on them. Every `create_*` / `load_*` handle is freed automatically on script unload.

## Constants

`topology` selects the primitive assembly mode:

| Constant | Value | Meaning |
| --- | --- | --- |
| `TOPO_TRIANGLE_LIST` | 0 | Default. 3 vertices per triangle. |
| `TOPO_TRIANGLE_STRIP` | 1 | Shared edges. N vertices = N-2 triangles. |
| `TOPO_LINE_LIST` | 2 | 2 vertices per line segment. |
| `TOPO_LINE_STRIP` | 3 | Connected line segments. |
| `TOPO_POINT_LIST` | 4 | Individual points. |

`compare_func` (depth-stencil), `int32`:

| Constant | Value | Constant | Value |
| --- | --- | --- | --- |
| `CMP_NEVER` | 0 | `CMP_GREATER` | 4 |
| `CMP_LESS` | 1 | `CMP_NOT_EQUAL` | 5 |
| `CMP_EQUAL` | 2 | `CMP_GREATER_EQUAL` | 6 |
| `CMP_LESS_EQUAL` | 3 | `CMP_ALWAYS` | 7 |

`fill_mode` and `cull_mode` (rasterizer), `int32`:

* `fill_mode`: `FILL_SOLID` (default), `FILL_WIREFRAME`.
* `cull_mode`: `CULL_BACK` (default), `CULL_FRONT`, `CULL_NONE` (render both sides).

`blend_factor` / `blend_op` / `filter` / `address` are shared with the rest of the Render API:

* `blend_factor`: 0=ZERO, 1=ONE, 2=SRC\_ALPHA, 3=INV\_SRC\_ALPHA, 4=DEST\_ALPHA, 5=INV\_DEST\_ALPHA, 6=SRC\_COLOR, 7=INV\_SRC\_COLOR, 8=DEST\_COLOR, 9=INV\_DEST\_COLOR.
* `blend_op`: 0=ADD, 1=SUBTRACT, 2=REV\_SUBTRACT, 3=MIN, 4=MAX.
* `filter`: 0=POINT, 1=LINEAR, 2=ANISOTROPIC.
* `address`: 0=WRAP, 1=CLAMP, 2=MIRROR, 3=BORDER.

`stage` selects the shader stage for binding calls: 0=VS, 1=PS, 2=CS (matches D3D11 shader stages).

## Layout string format

`create_shader` takes a vertex input layout as a comma-separated string of `SEMANTIC:INDEX:TYPE` entries:

```
"POSITION:0:FLOAT2, COLOR:0:FLOAT4"
"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2"
"POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2"
```

| Type | Bytes | Notes |
| --- | --- | --- |
| `FLOAT1` | 4 | single float |
| `FLOAT2` | 8 | |
| `FLOAT3` | 12 | |
| `FLOAT4` | 16 | |
| `BYTE4` | 4 | normalized 0–1 (unorm) |
| `UINT1` | 4 | |

The sum of all element sizes is the vertex **stride** — it must match the `stride` you pass to `create_vertex_buffer` and the byte layout you pack into `vertex_data`.

## Resource creation

All creation calls return an `int64` handle, or `0` on failure (shader compilation failure, allocation failure, etc). Always check for `0` before using a handle.

```cpp
int64 create_shader(string vs_source, string ps_source, string layout);
int64 create_compute_shader(string cs_source);
int64 create_vertex_buffer(uint32 stride, uint32 max_vertices, bool dynamic);
int64 create_index_buffer(uint32 max_indices, bool use_32bit, bool dynamic);
int64 create_constant_buffer(uint32 size);
int64 create_structured_buffer(uint32 element_size, uint32 element_count, bool cpu_write, bool gpu_write);
int64 create_blend_state(int32 src, int32 dst, int32 op, int32 src_alpha, int32 dst_alpha, int32 op_alpha);
int64 create_sampler(int32 filter, int32 address_u, int32 address_v);
int64 create_texture(uint32 width, uint32 height, array rgba_data);
int64 create_render_target(uint32 width, uint32 height);
int64 create_depth_buffer(uint32 width, uint32 height);
int64 create_depth_stencil_state(bool depth_enable, bool depth_write, int32 compare_func);
int64 create_rasterizer_state(int32 cull_mode, int32 fill_mode, bool scissor_enable);
```

* `create_shader` — Compiles `vs_5_0` + `ps_5_0` from HLSL source. Both entry points must be named `main`. `layout` describes the vertex input (see above).
* `create_compute_shader` — Compiles a `cs_5_0` compute shader. Entry point must be `main`.
* `create_vertex_buffer` — `stride` is bytes per vertex (must match shader layout). `dynamic` = `true` for per-frame updates (typical), `false` for static geometry.
* `create_index_buffer` — `use_32bit` = `true` for 32-bit indices (needed past 65535 vertices), `false` for 16-bit.
* `create_constant_buffer` — `size` is automatically aligned up to 16 bytes.
* `create_structured_buffer` — `element_size` is bytes per element (16 for `float4`). `cpu_write` creates an SRV updatable from script; `gpu_write` creates a UAV writable from compute shaders.
* `create_blend_state` — Standard alpha: `(SRC_ALPHA, INV_SRC_ALPHA, ADD, ONE, INV_SRC_ALPHA, ADD)`. Premultiplied (recommended for overlays): `(ONE, INV_SRC_ALPHA, ADD, ONE, INV_SRC_ALPHA, ADD)`.
* `create_sampler` — `LINEAR` for smooth scaling, `POINT` for pixel-perfect.
* `create_texture` — `rgba_data` must be exactly `width * height * 4` bytes.
* `create_render_target` — Offscreen color target for multi-pass rendering. Pass `0, 0` to match the viewport size.
* `create_depth_buffer` — D24S8 depth/stencil buffer. Pass `0, 0` to match the viewport size.
* `create_depth_stencil_state` — `depth_write` controls writes on pass. For solid 3D use `(true, true, CMP_LESS)`.
* `create_rasterizer_state` — `scissor_enable` should usually be `true` so clipping works.

## Drawing

```cpp
int64 custom_draw(int64 shader, int64 vb, array vertex_data, uint32 vertex_count, int32 topology,
                  int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                  int64 cb, array cb_data, int32 cb_slot);

int64 custom_draw_indexed(int64 shader, int64 vb, array vertex_data, uint32 vertex_count,
                          int64 ib, array index_data, uint32 index_count, int32 topology,
                          int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                          int64 cb, array cb_data, int32 cb_slot);
```

* `vertex_data` — Raw vertex bytes packed to match the shader layout stride.
* `vertex_count` — Number of vertices.
* `index_data` / `index_count` (indexed only) — Index bytes (16- or 32-bit per the index buffer) and count.
* `topology` — One of the `TOPO_*` constants.
* `blend` / `sampler` / `texture` / `cb` — Optional; pass `0` to skip binding any of them.
* `tex_slot` — Texture/sampler register slot (usually `0`).
* `cb_data` — Raw constant bytes, or an empty array if `cb` is `0`.
* `cb_slot` — Constant buffer register slot (usually `0`).

`custom_draw_indexed` reuses shared vertices through an index buffer — use it for cubes, grids, and any geometry with shared edges.

## Render target operations

```cpp
int64 custom_set_render_target(int64 rt);
int64 custom_set_render_target_ext(int64 rt, int64 depth_buffer);
int64 custom_reset_render_target();
int64 custom_bind_rt_as_texture(int64 rt, int32 slot);
int64 custom_clear_render_target(int64 rt, float64 r, float64 g, float64 b, float64 a);
int64 custom_clear_depth_buffer(int64 db);
int64 custom_restore_state();
```

* `custom_set_render_target` — Redirects subsequent `custom_draw` calls to an offscreen render target.
* `custom_set_render_target_ext` — Binds a render target with a depth buffer for proper 3D occlusion. Auto-clears both and sets the viewport/scissor to the RT dimensions. Pass `0` for the depth buffer for color-only.
* `custom_reset_render_target` — Switches back to the main backbuffer.
* `custom_bind_rt_as_texture` — Binds a render target's contents as a sampleable texture at `slot` — the way to blit an offscreen pass back to the screen.
* `custom_clear_render_target` — Clears an RT to an explicit color without re-binding it.
* `custom_clear_depth_buffer` — Clears depth to 1.0 and stencil to 0.
* `custom_restore_state` — Resets the D3D11 pipeline state. **Call after any custom-pipeline sequence** before returning control to the 2D layer.

## State management

```cpp
int64 custom_set_depth_stencil_state(int64 ds);
int64 custom_set_rasterizer_state(int64 rs);
int64 custom_set_viewport(float64 x, float64 y, float64 w, float64 h);
int64 custom_reset_viewport();
int64 custom_bind_texture(int64 texture, int64 sampler, int32 slot);
int64 custom_bind_constant_buffer(int64 cb, array data, int32 slot, int32 stage);
```

* `custom_set_depth_stencil_state` — Applies a depth-stencil state. Pass `0` to reset to default (no depth testing).
* `custom_set_rasterizer_state` — Applies a rasterizer state. Pass `0` to reset to default.
* `custom_set_viewport` — Restricts rendering to a sub-region — split-screen, picture-in-picture, or confining a 3D scene to a panel.
* `custom_reset_viewport` — Restores the full viewport.
* `custom_bind_texture` — Binds a texture + sampler to `slot`, persisting across subsequent draws. Pass `0` for the texture to bind the most recent backbuffer capture.
* `custom_bind_constant_buffer` — Binds a constant buffer to a specific `slot` and `stage` independently of draw calls, persisting until changed. Enables multi-buffer setups (camera on `b0`, material on `b1`, lighting on `b2`). When binding the MVP this way, pass `0` for the `cb` parameter of the draw call so it doesn't overwrite your manual bindings.

## Mesh & texture loading

```cpp
int64   create_mesh_raw(array vertex_data, uint32 vertex_count, uint32 stride,
                        array index_data, uint32 index_count, bool use_32bit);
int64   load_mesh(string path);
int64   load_mesh_mem(array data);
int64   get_mesh_vert_count(int64 mesh);
int64   get_mesh_index_count(int64 mesh);
float64 get_mesh_stride(int64 mesh);
float64 get_mesh_bounds_min_x(int64 mesh);  // ...min_y, min_z, max_x, max_y, max_z

int64   create_texture_from_file(string path);  // alias of load_texture
int64   load_texture(string path);
int64   load_texture_mem(array data);
int64   create_dynamic_texture(uint32 width, uint32 height);
int64   custom_update_texture(int64 tex, uint32 x, uint32 y, uint32 w, uint32 h, array rgba_data);
float64 get_texture_width(int64 tex);
float64 get_texture_height(int64 tex);

int64 draw_mesh(int64 mesh, int64 shader, int32 topology,
                int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                int64 cb, array cb_data, int32 cb_slot);
```

* `create_mesh_raw` — Builds a mesh from raw vertex + index bytes with any layout. The shader must match the stride. Use for procedural terrain, generated geometry, or particle quads.
* `load_mesh` / `load_mesh_mem` — Parses Wavefront OBJ (positions, normals, texcoords, 3+ vertex faces auto-triangulated, negative indices). Loaded meshes use a fixed layout `POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2` (32 bytes/vertex); shaders must match it. `load_mesh` tries the script directory first.
* `get_mesh_*` — Vertex/index counts, stride, and the axis-aligned bounding box.
* `load_texture` / `load_texture_mem` — Decodes PNG, JPG, BMP, TGA, or GIF. `load_texture` tries the script directory first, then the absolute path. `create_texture_from_file` is an alias of `load_texture`.
* `create_dynamic_texture` — Allocates an updatable texture; feed it per-frame with `custom_update_texture`.
* `custom_update_texture` — Partial update of an existing texture; `rgba_data` must be exactly `w * h * 4` bytes. Use for sprite sheets, minimaps, or procedural atlases.
* `draw_mesh` — Convenience draw for loaded/procedural meshes: binds the mesh's internal vertex/index buffers and issues `DrawIndexed` in one call. Pass `0` for optional handles. The shader layout must match the mesh's vertex format.

## Compute shaders & structured buffers

```cpp
int64 create_compute_shader(string cs_source);
int64 dispatch_compute(int64 cs, uint32 x, uint32 y, uint32 z);
int64 create_structured_buffer(uint32 element_size, uint32 element_count, bool cpu_write, bool gpu_write);
int64 update_structured_buffer(int64 sb, array data);
int64 bind_structured_buffer(int64 sb, int32 slot, int32 stage);
array read_structured_buffer(int64 sb);
```

* `dispatch_compute` — Dispatches a compute shader with thread group counts `(x, y, z)`. Dispatched as a state-only command — no geometry is drawn. Use structured buffers for input/output.
* `create_structured_buffer` — `cpu_write` makes it script-updatable (SRV); `gpu_write` makes it compute-writable (UAV). A buffer can be both.
* `update_structured_buffer` — Uploads new element bytes from script (requires `cpu_write`).
* `bind_structured_buffer` — Binds to a `slot` on `stage`. The CS stage with `gpu_write` binds as a UAV; otherwise as an SRV.
* `read_structured_buffer` — Reads element bytes back to script (GPU → CPU).

## Backbuffer capture

```cpp
int64 capture_backbuffer(int32 slot);
```

Captures the current backbuffer to a staging texture and binds it as a shader resource at `slot`. Combine with a custom pixel shader for post-processing — bloom, blur, color grading, screen-space effects:

```cpp
capture_backbuffer(0);
custom_bind_texture(0, sampler, 0);  // texture=0 uses the captured backbuffer
custom_draw(post_fx_shader, vb, fullscreen_quad, 6, TOPO_TRIANGLE_LIST,
            blend, sampler, 0, 0, cb, fx_cb, 0);
```

## Examples

### Basic colored triangle

```cpp
int64 g_shader;
int64 g_vb;

int64 main() {
    string vs = "struct VSIn { float2 pos : POSITION; float4 color : COLOR; };\n"
                "struct VSOut { float4 pos : SV_Position; float4 color : COLOR; };\n"
                "VSOut main(VSIn i) { VSOut o; o.pos = float4(i.pos, 0.0, 1.0); o.color = i.color; return o; }\n";
    string ps = "struct VSOut { float4 pos : SV_Position; float4 color : COLOR; };\n"
                "float4 main(VSOut i) : SV_Target { return i.color; }\n";

    g_shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    g_vb = create_vertex_buffer(24, 3, true);  // 2*4 + 4*4 = 24 bytes per vertex
    register_routine(cast<int64>(my_draw), 0);
    return 1;
}

void my_draw(int64 data) {
    float32[] verts;
    verts.push(-0.5f); verts.push(-0.5f);  verts.push(1); verts.push(0); verts.push(0); verts.push(1);
    verts.push( 0.5f); verts.push(-0.5f);  verts.push(0); verts.push(1); verts.push(0); verts.push(1);
    verts.push( 0.0f); verts.push( 0.5f);  verts.push(0); verts.push(0); verts.push(1); verts.push(1);

    float32[] no_cb;
    custom_draw(g_shader, g_vb, verts, 3, TOPO_TRIANGLE_LIST, 0, 0, 0, 0, 0, no_cb, 0);
}
```

### Depth-tested 3D scene

Render two meshes into an offscreen target with real depth occlusion, then blit the result to the screen:

```cpp
int64 rt = create_render_target(400, 300);
int64 db = create_depth_buffer(400, 300);
int64 ds = create_depth_stencil_state(true, true, CMP_LESS);
int64 rs = create_rasterizer_state(CULL_NONE, FILL_SOLID, true);

// Render pass
custom_set_render_target_ext(rt, db);
custom_clear_render_target(rt, 0, 0, 0, 1);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs);
draw_mesh(mesh1, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb, mvp1_data, 0);
draw_mesh(mesh2, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb, mvp2_data, 0);
custom_reset_render_target();
custom_set_rasterizer_state(0);
custom_set_depth_stencil_state(0);

// Blit result to screen
custom_bind_rt_as_texture(rt, 0);
custom_draw(blit_shader, vb, quad, 6, TOPO_TRIANGLE_LIST, blend, sampler, 0, 0, cb, screen_cb, 0);
custom_restore_state();
```

### Compute shader with structured buffer

```cpp
string cs = "RWStructuredBuffer<float4> particles : register(u0);\n"
            "[numthreads(64, 1, 1)]\n"
            "void main(uint3 id : SV_DispatchThreadID) {\n"
            "    particles[id.x].xy += particles[id.x].zw;  // advance by velocity\n"
            "}\n";

int64 compute = create_compute_shader(cs);
int64 sb = create_structured_buffer(16, 1024, false, true);  // float4 x 1024, GPU-writable

// Simulate on the GPU
bind_structured_buffer(sb, 0, 2 /* STAGE_CS */);
dispatch_compute(compute, 16, 1, 1);  // 16 groups * 64 threads = 1024 particles

// Read positions back (or bind to STAGE_PS to render directly)
bind_structured_buffer(sb, 0, 1 /* STAGE_PS */);
```

### Post-processing (full-screen blur of the current frame)

```cpp
void on_frame(int64 data) {
    capture_backbuffer(0);               // current frame -> texture slot 0
    custom_bind_texture(0, g_sampler, 0);
    custom_draw(g_blur_shader, g_vb, g_fullscreen_quad, 6, TOPO_TRIANGLE_LIST,
                g_blend, g_sampler, 0, 0, g_cb, g_fx_cb, 0);
    custom_restore_state();
}
```

## Cleanup

On script unload, every handle returned by a `create_*` / `load_*` call is destroyed automatically. Explicit destruction is optional and only needed to free a resource mid-script:

```cpp
int64 destroy_shader(int64 shader);
int64 destroy_compute_shader(int64 cs);
int64 destroy_vertex_buffer(int64 vb);
int64 destroy_index_buffer(int64 ib);
int64 destroy_constant_buffer(int64 cb);
int64 destroy_structured_buffer(int64 sb);
int64 destroy_blend_state(int64 bs);
int64 destroy_sampler(int64 s);
int64 destroy_texture(int64 tex);
int64 destroy_render_target(int64 rt);
int64 destroy_depth_buffer(int64 db);
int64 destroy_depth_stencil_state(int64 ds);
int64 destroy_rasterizer_state(int64 rs);
int64 destroy_mesh(int64 mesh);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/custom-draw-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/extensions-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/perception-ide/extensions-api.md).

# Extensions API

> **Some of the Perception.cx AngelScript APIs are available in extensions.** This includes: logging, rendering, input, CPU intrinsics, WinAPI, JSON, utilities, and Zydis encoding. **Not available:** process memory (`proc_t`/`ref_process`), mutexes, PCX script GUI API (`subtab_t`/`panel_t`/`checkbox_t`/`slider_double_t`/`button_t`/etc.), Unicorn emulation, extended math, engine-specific API, atomic API, and `register_callback`/`unregister_callback`. Extensions additionally get editor-specific APIs documented below.

**Available platform functions:** `log`, `log_error`, `log_console`, `log_console_error`, `get_username`, all `draw_*` / `clip_*` / `create_font*` / `create_bitmap` / `get_font*` / `get_text_size` rendering functions, all `key_*` / `get_mouse_*` / `get_scroll_delta` / `is_hovered` input functions, CPU intrinsics, WinAPI, JSON (`json_parse`/`json_stringify`), Zydis encoder, and utility functions.

> **Extensions also have:** file I/O (`read_file`/`write_file`/`file_exists`/`list_directory`), clipboard access, synchronous HTTP requests (`http_get`/`http_post`), and editor manipulation APIs documented below.

> **AngelScript string note:** Extensions use the standard AngelScript `string` type. Use `.isEmpty()` (not `.empty()`), `.length()` (not `.size()`), and `.findFirst()` / `.findLast()` for search.

***

**Structure**

One `.as` file per extension. Drop it in `<scripting_main_path>/extensions/`. Three optional metadata constants:

```cpp
const string EXT_NAME = "My Extension";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Short description";
```

All hook functions are optional — implement only what you need.

***

**Rules & Constraints**

* **No `main()` or `on_unload()`** — use `on_activate()` and `on_deactivate()` instead
* **`on_tick()` locals reset every call** — use global variables for persistent state across frames
* **No lambdas** — buttons return `bool`, use `if (create_button("X")) { ... }` instead of callbacks
* **Only `create_slider`** — no `create_slider_double` or `create_slider_int` variants
* **`on_settings_render` uses widget API only** — do NOT use `draw_*` render calls inside it. The widget functions handle all rendering and layout automatically
* **RGBA values are 0–255** — not 0.0–1.0
* **Keybinds and color pickers** must be created immediately after their parent checkbox

**Validation**

Extension scripts can be validated using `check_script` / `validate_script` or the **Verify** toolbar button. The editor automatically detects files in `extensions/` and uses a dedicated compile-only validator with the extension API surface registered.

* `validate_script` with `run=true` is **not supported** for extensions — they are event-driven with no `main()`
* `execute_script` **cannot** be used with extension code — extensions use a different API surface
* After validation returns PASS, the extension is correct and will be auto-loaded by the editor

***

**Hooks**

**Lifecycle**

```cpp
void on_activate()    // loaded & enabled
void on_deactivate()  // about to unload/disable
void on_tick()        // every frame (main thread)
```

**Editor Events**

```cpp
void on_file_opened(const string &in path)
void on_file_saved(const string &in path)
void on_buffer_changed(const string &in path, int line)
void on_tab_changed(const string &in path)
```

**AI Pipeline**

```cpp
bool on_ai_before_send(const string &in prompt, const string &in system_prompt)
// return false to cancel. call override_prompt() to change the prompt.

void on_ai_after_response(const string &in response)

string on_ai_tool_call(const string &in name, const string &in args)
// only fires for tools YOU registered. return result JSON.

void on_ai_after_tool(const string &in name, const string &in args, const string &in result)
// observation hook, fires for ALL tool calls

string on_ai_system_inject()
// return text appended to system prompt every request
```

**IntelliSense**

Extensions can provide completions and hover tooltips for **any file type** — not just AngelScript or Lua. The extension receives the file path, line text, and cursor column, and decides what to offer based on the file being edited. This means you can build HTML, CSS, Python, or any custom language IntelliSense via extensions.

```cpp
void on_completion(const string &in file, const string &in line_text, int col,
    array<string>@ labels, array<string>@ inserts, array<string>@ details)

void on_hover(const string &in file, const string &in word, int line, string &out tooltip)
```

**Settings UI**

```cpp
void on_settings_render(float x, float y, float w)
// render widgets in the Extensions panel sidebar
```

***

**Editor API**

```cpp
string get_active_file()
string get_active_file_content()
string get_active_language()
int    get_cursor_line()
int    get_cursor_col()
void   set_cursor_pos(int line, int col)
string get_selection_text()
int    get_line_count()
string get_line_text(int line)
string get_root_path()
void   get_open_files(array<string> &out files)
int    get_tab_count()
string get_tab_file(int index)
int    get_active_tab()
void   show_notification(const string &in msg)
void   set_status(const string &in msg)
void   send_chat_message(const string &in msg)
void   override_prompt(const string &in new_prompt) // only in on_ai_before_send
void   insert_text(const string &in text)           // insert at cursor position
void   replace_selection(const string &in text)     // replace current selection (or delete if empty)
void   set_selection(int start_line, int start_col, int end_line, int end_col)  // 0-based
bool   open_file(const string &in path)             // open file in new tab
bool   save_active_file()                           // save current buffer
void   goto_line(int line)                          // jump to line and scroll into view
```

**File I/O API**

Read and write files from extension code. Paths are resolved relative to the project root, or can be absolute.

```cpp
string read_file(const string &in path)                  // returns file contents (empty on failure)
bool   write_file(const string &in path, const string &in content)  // overwrites file
bool   file_exists(const string &in path)                // check if file exists
void   list_directory(const string &in path, array<string> &out entries)  // list directory contents
```

**Clipboard API**

```cpp
string get_clipboard()                          // read system clipboard text
void   set_clipboard(const string &in text)     // set system clipboard text
```

**Network API**

Synchronous HTTP requests via WinHTTP with a 10-second timeout. **Do not call these in `on_tick()`** — they block the main thread.

```cpp
string http_get(const string &in url, const string &in headers = "")   // returns response body
string http_post(const string &in url, const string &in body, const string &in headers = "")
int    http_get_status(const string &in url, const string &in headers = "")  // returns HTTP status code
```

Headers are passed as `"Key: Value\nKey2: Value2"` (newline-separated).

**Utility API**

```cpp
uint64 get_tick_count()                // system tick count (milliseconds)
string get_active_model()              // current AI model name
int    get_chat_message_count()        // number of messages in current chat
void   get_chat_message(int index, string &out role, string &out content)  // read chat message
```

**Settings API**

Persisted per-extension as JSON in the `extensions/` folder (e.g. `extensions/my_extension.json`). Settings survive editor restarts, extension reloads, and ON/OFF toggles. The enabled/disabled state of each extension is also persisted in the editor's workspace state.

```cpp
string setting_get(const string &in key)
void   setting_set(const string &in key, const string &in value)
bool   setting_get_bool(const string &in key)
void   setting_set_bool(const string &in key, bool value)
double setting_get_number(const string &in key)
void   setting_set_number(const string &in key, double value)
```

**Widget API**

Used inside `on_settings_render` to draw interactive UI.

```cpp
void   create_label(const string &in text)
void   create_label_colored(const string &in text, int r, int g, int b)
void   create_separator()
void   create_spacing(double px)
bool   create_checkbox(const string &in label, const string &in key)   // returns value
bool   create_button(const string &in label)                           // returns true on click
double create_slider(const string &in label, const string &in key,
                     double min, double max, double step = 0)          // returns value
string create_input_text(const string &in label, const string &in key) // single-line
string create_text_area(const string &in label, const string &in key,
                        int visible_lines = 4)                         // multi-line
void   create_progress_bar(const string &in label, double value, double max)
int    create_dropdown(const string &in label, const string &in key,
                       array<string>@ options)                         // cycle-on-click, returns selected index
int    create_color_picker(const string &in label, const string &in key) // RGBA swatch, returns packed RGBA int
int    create_keybind(const string &in label, const string &in key)    // click to capture VK code, Escape cancels
```

> **Widget rules:** Keybinds and color pickers must be created immediately after their parent checkbox. The `create_dropdown` cycles through options on each click and persists the selected index. The `create_color_picker` stores individual R/G/B/A channels as `key_r`, `key_g`, `key_b`, `key_a` in settings. The `create_keybind` widget shows a red border during capture mode and returns the Windows virtual key code.

**Tool Registration API**

Register custom AI tools. Only your extension can handle calls to tools it registered.

```cpp
void register_tool(const string &in name, const string &in desc, const string &in params_json = "")
void register_tool_param(const string &in tool, const string &in param,
                         const string &in type, const string &in desc, bool required = true)
void unregister_tool(const string &in name)
```

***

**Examples**

**Custom AI Tool**

```cpp
const string EXT_NAME = "Doc Lookup";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Gives the AI a documentation search tool";

void on_activate() {
    register_tool("search_docs", "Search project documentation for a query");
    register_tool_param("search_docs", "query", "string", "Search terms", true);
    register_tool_param("search_docs", "max_results", "integer", "Max results to return", false);
    log("Doc Lookup extension loaded");
}

string on_ai_tool_call(const string &in name, const string &in args) {
    if (name == "search_docs") {
        // parse args JSON, search your docs, return results
        return "{\"results\": [\"Found: memory_read documentation\", \"Found: pattern_scan guide\"]}";
    }
    return "{\"error\": \"unknown tool\"}";
}

void on_deactivate() {
    unregister_tool("search_docs");
}
```

**Widget Settings Panel**

```cpp
const string EXT_NAME = "Config Panel";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Extension with custom settings UI";

void on_settings_render(float x, float y, float w) {
    create_label("--- Configuration ---");
    create_separator();

    bool enabled = create_checkbox("Enable feature", "feat_enabled");
    if (enabled) {
        double speed = create_slider("Speed", "speed_val", 0, 100, 1);
        string name = create_input_text("Name", "user_name");
        create_label("Current: " + name + " @ " + formatInt(int(speed)));
    }

    create_separator();
    if (create_button("Reset Defaults")) {
        setting_set_bool("feat_enabled", false);
        setting_set_number("speed_val", 50);
        setting_set("user_name", "");
        show_notification("Settings reset");
    }
}
```

**IntelliSense Provider**

```cpp
const string EXT_NAME = "Custom Completions";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Adds project-specific completions";

void on_completion(const string &in file, const string &in line_text, int col,
    array<string>@ labels, array<string>@ inserts, array<string>@ details)
{
    // add completions when user types "myapi."
    if (line_text.findFirst("myapi.") >= 0) {
        labels.insertLast("myapi.init");
        inserts.insertLast("myapi.init()");
        details.insertLast("Initialize the API");

        labels.insertLast("myapi.shutdown");
        inserts.insertLast("myapi.shutdown()");
        details.insertLast("Shut down the API");
    }
}

void on_hover(const string &in file, const string &in word, int line, string &out tooltip) {
    if (word == "myapi")
        tooltip = "Project API namespace\nSee docs/api.md for reference";
}
```

**AI System Prompt Injection**

```cpp
const string EXT_NAME = "Context Injector";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Adds project context to every AI request";

string on_ai_system_inject() {
    string file = get_active_file();
    string lang = get_active_language();
    return "The user is editing: " + file + " (language: " + lang + ")\n"
         + "Project root: " + get_root_path() + "\n"
         + "Open tabs: " + formatInt(get_tab_count());
}

bool on_ai_before_send(const string &in prompt, const string &in system_prompt) {
    log("[AI] Sending: " + prompt.substr(0, 100));
    return true; // allow send
}

void on_ai_after_response(const string &in response) {
    log("[AI] Response length: " + formatInt(response.length()));
}
```

**Periodic Background Worker**

```cpp
const string EXT_NAME = "Auto-Saver";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Logs a reminder every ~60 seconds";

int tick_count = 0;

void on_tick() {
    tick_count++;
    // ~60fps, so 3600 ticks ≈ 60 seconds
    if (tick_count % 3600 == 0) {
        log_console("Reminder: save your work!");
    }
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/perception-ide/extensions-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/filesystem-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/filesystem-api.md).

# Filesystem API

Sandboxed filesystem access for enma scripts. Every call is gated by the `file_system_access` permission. Without it, calls return a failure value (`false` / `0` / empty array) and never throw.

## Sandbox

Paths are interpreted relative to the script's per-user data directory. Scripts cannot reach outside that root.

Rejected at the path-validation step (returns failure without touching disk):

* absolute paths — `C:\config`, `/etc/hosts`
* UNC paths — `\\server\share`
* parent traversals — `..\..\elsewhere`
* leading slashes — `/foo`, `\foo`
* embedded `:`, `\n`, `\r`, `\0`

Forward and backslashes are both accepted internally; pick one and stay consistent.

## Quick reference

| Operation                      | Native                                                                     |
| ------------------------------ | -------------------------------------------------------------------------- |
| Create / overwrite a text file | `fs_create_file(path, data)`                                               |
| Create a directory             | `fs_create_directory(path)`                                                |
| Test existence                 | `fs_file_exists(path)` / `fs_dir_exists(path)`                             |
| Delete                         | `fs_delete_file(path)` / `fs_delete_directory(path)`                       |
| File size                      | `fs_file_size(path)`                                                       |
| Read text                      | `fs_read_file(path)`                                                       |
| Write / append text            | `fs_write_file(path, data)` / `fs_append_file(path, data)`                 |
| Read binary                    | `fs_read_file_binary(path)`                                                |
| Write / append binary          | `fs_write_file_binary(path, bytes)` / `fs_append_file_binary(path, bytes)` |
| List entries                   | `fs_list_files(path)` / `fs_list_dirs(path)` / `fs_list_all(path)`         |

## File operations

```cpp
bool   fs_create_file(string path, string data);
bool   fs_create_directory(string path);
bool   fs_file_exists(string path);
bool   fs_dir_exists(string path);
bool   fs_delete_file(string path);
bool   fs_delete_directory(string path);
int64  fs_file_size(string path);
```

* `fs_create_file` writes `data` as the file's complete contents (UTF-8). Overwrites if the file already exists. Empty `data` creates a zero-byte file.
* `fs_create_directory` creates the directory and any missing parents.
* `fs_delete_directory` succeeds only when the target directory is empty.
* `fs_file_size` returns `0` for missing files (indistinguishable from a real zero-byte file — use `fs_file_exists` first if you need to disambiguate).

```cpp
if (!fs_dir_exists("configs"))
    fs_create_directory("configs");
if (!fs_create_file("configs/active.json", "{\"version\":1}"))
    println("[fs] write failed (permission?)");
```

## Text I/O

```cpp
string fs_read_file(string path);
bool   fs_write_file(string path, string data);
bool   fs_append_file(string path, string data);
```

* `fs_read_file` returns the file's bytes interpreted as UTF-8. Returns an **empty string** on missing file / read failure / permission denied — distinguish from a real empty file via `fs_file_exists` if it matters.
* `fs_write_file` overwrites; `fs_append_file` appends. Both return `true` on success, `false` on failure.

```cpp
fs_write_file("state/last_target.txt", "weapon_t1_assault");

string saved = fs_read_file("state/last_target.txt");
if (saved.length() > 0)
    set_target(saved);
```

## Binary I/O

```cpp
array<uint8> fs_read_file_binary(string path);
bool         fs_write_file_binary(string path, array<uint8> bytes);
bool         fs_append_file_binary(string path, array<uint8> bytes);
```

Use these for opaque blobs (saved offsets, screenshots, packet captures). A missing or unreadable file yields an empty array. Empty-input writes succeed and produce a zero-byte file; empty-input appends are a no-op (still return `true`).

```cpp
array<uint8> header;
header.push(0x4D); header.push(0x5A);    // "MZ"
fs_write_file_binary("dumps/probe.bin", header);

array<uint8> back = fs_read_file_binary("dumps/probe.bin");
print("read " + cast<string>(back.length()) + " bytes");
```

## Directory listing

```cpp
array<string> fs_list_files(string path);
array<string> fs_list_dirs(string path);
array<string> fs_list_all(string path);
```

Returns the **basenames** of entries (no path prefixes) in the requested directory. No recursion — descend manually by calling again with the joined relative path. A missing directory or permission denial yields an empty array. Entry order is filesystem-dependent.

```cpp
array<string> configs = fs_list_files("configs");
for (string name : configs)
{
    string body = fs_read_file("configs/" + name);
    // ...
}
```

## Failure modes

Every native handles every failure the same way: returns a falsy value (`false` / `0` / empty). The script never sees an exception from the FS layer.

| Cause                                                     | Return                                                                                                             |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `file_system_access` permission off                       | `false` / `0` / empty                                                                                              |
| Path validation fails (absolute, UNC, `..`, control char) | `false` / `0` / empty                                                                                              |
| Target file/directory missing                             | `false` / `0` / empty (writes that need a parent will fail if the parent is missing — `fs_create_directory` first) |
| Underlying I/O error (disk full, locked file, etc.)       | `false` / `0` / empty                                                                                              |

## Sandbox tests

Every escape attempt below returns `false` / empty without touching disk:

```cpp
fs_create_file("C:\\evil.txt", "x");          // false: absolute path
fs_create_file("/etc/passwd", "x");           // false: absolute /
fs_create_file("\\\\server\\f", "x");         // false: UNC
fs_create_file("../escape.txt", "x");         // false: parent traversal
fs_create_file("ok/../escape.txt", "x");      // false: nested traversal
```

## Permissions

Enabled via the script's `permissions` block. The flag is `file_system_access`. With it off, every call short-circuits before touching disk — reads return empty, writes silently no-op. Check with `fs_file_exists` after a write if your logic depends on the operation having succeeded.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/filesystem-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/gui-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/gui-api.md).

# GUI API

All GUI natives are auto-registered into every loaded script.

The API is in two parts:

* **Part 1 — sidebar sections + widgets.** A `sidebar_section_t` is a select-button in the host sidebar plus a content panel auto-attached to the main frame. The panel renders only when the section's button is selected. Widgets are created on the section directly.
* **Part 2 — frames, layers, custom widgets, menus, file pickers.** Lower-level primitives for floating windows and custom drawing.

All GUI handles are `int64`-backed. The script doesn't own the underlying resources — calling a destructor on a handle is a noop. At script unload, every handle the script created gets cleaned up automatically.

## Sidebar sections

```cpp
sidebar_section_t create_sidebar_section(string name, string icon);
void              create_sidebar_separator();
```

`name` renders as the sidebar label. `icon` accepts a codicon string (e.g. `"\xEE\xAC\xA3"` for file-code U+EB23) or `""` for no icon.

Each section is a radio-style sidebar entry: clicking one auto-deselects siblings and shows that section's panel.

```cpp
void section.set_active(bool active);   // toggle selection programmatically
```

### Widget builders on `sidebar_section_t`

Every widget builder returns a typed handle. Each is also `int64`-backed; pass to other natives via the typed name.

```cpp
label_t              section.create_label(string text, ui_align align);
void                 section.create_separator();
button_t             section.create_button(string label, ui_align align);
checkbox_t           section.create_checkbox(string label, bool initial);
slider_t             section.create_slider(string label, float64 initial, float64 minv, float64 maxv, float64 step);
slider_icon_t        section.create_slider_icon(string icon, float64 initial, float64 minv, float64 maxv, float64 step);
value_input_t        section.create_value_input(string label, float64 initial, float64 minv, float64 maxv, float64 step);
options_t            section.create_options(string label, array<string> items, int64 selected);
multi_options_t      section.create_multi_options(string label, array<string> items, int64 selected_mask);
dropdown_t           section.create_dropdown(string label, array<string> items, int64 selected);
multi_dropdown_t     section.create_multi_dropdown(string label, array<string> items, int64 selected_mask);
list_t               section.create_list(string label, array<string> info1, array<string> info2,
                                          bool selectable, int64 selected,
                                          int64 visible_rows, bool filterable);
inline_button_t      section.create_inline_button(string label, float64 width, string icon);
inline_text_input_t  section.create_inline_text_input(string initial, float64 width, string placeholder);
tabs_t               section.create_tabs(array<string> items, int64 selected);
keybind_t            section.create_keybind(string label);
progress_bar_t       section.create_progress_bar(string label, float64 initial, float64 minv, float64 maxv, bool show_pct);
spinner_t            section.create_spinner(string label);
range_slider_t       section.create_range_slider(string label, float64 minv, float64 maxv,
                                                  float64 lo, float64 hi, float64 step);
table_t              section.create_table(string label, array<string> col_names,
                                           array<float64> col_widths, int64 visible_rows);
text_input_t         section.create_text_input(string label, string initial, int64 max_lines);
text_editor_t        section.create_text_editor(string label, string initial, int64 visible_lines, string lexer);
colorpicker_t        section.create_colorpicker(string label, color initial);
```

## Common widget operations

Every widget type (except `text_editor_t`, which has no `set_active`) supports:

```cpp
void widget.set_active(bool active);
void widget.set_tooltip(string s);
void widget.on_change(int64 fn_handle);   // closure: void cb(int64 widget_handle)
```

`on_change` fires on `CALLBACK_VALUE_CHANGED` — which means click for buttons, value mutation for sliders / checkboxes / dropdowns / etc. Pass the closure via `cast<int64>(my_callback)`.

## Per-widget typed get / set

```cpp
// label
void label.set_text(string s);

// button
void button.attach_to(button_t other);   // group buttons into one row

// checkbox
bool checkbox.get();
void checkbox.set(bool v);

// slider, slider_icon, value_input
float64 X.get();
void    X.set(float64 v);

// options, dropdown, tabs
int64 X.get();
void  X.set(int64 i);

// multi_options, multi_dropdown
int64 X.get_mask();
void  X.set_mask(int64 m);

// list
int64 list.get_selected();
void  list.set_selected(int64 i);
void  list.set_items(array<string> info1, array<string> info2);
int64 list.size();

// inline_text_input, text_input, text_editor
string X.get();
void   X.set(string s);

// keybind
void  keybind.bind(int64 vk, bool ctrl, bool shift, bool alt, keybind_mode mode);
bool  keybind.is_active();      // true when any binding is currently active per its mode; poll to react to activation
int64 keybind.binding_count();  // number of bindings on this row

// progress_bar
void progress_bar.set(float64 v);

// range_slider — split lo/hi getters since there's no natural pair type
float64 range_slider.get_lo();
float64 range_slider.get_hi();
void    range_slider.set(float64 lo, float64 hi);

// table
void  table.add_row(array<string> cells);
void  table.clear();
int64 table.size();

// colorpicker — uses the registered `color` type
void  colorpicker.attach_to(colorpicker_t other);
color colorpicker.get();
void  colorpicker.set(color c);
```

## Frames (Part 2)

`frame_t` wraps any of four host frame kinds — distinguished by which factory you call:

```cpp
frame_t create_frame(string name, vec2 pos, vec2 size, layer_t layer);
//   raw frame, no chrome. Pass 0 for layer to use the default layer.
frame_t create_default_frame(string name, vec2 pos, vec2 size, layer_t layer);
//   frame with title bar / logo / drag chrome.
frame_t create_draggable_frame(string name, vec2 pos, vec2 size, layer_t layer);
frame_t create_popup(string name, vec2 pos, vec2 size, layer_t layer);
```

```cpp
void    frame.set_pos(vec2 pos);
void    frame.set_size(vec2 size);
vec2    frame.get_pos();
vec2    frame.get_size();
void    frame.set_visible(bool v);
bool    frame.is_visible();
void    frame.set_anchors(int64 mask);   // ui_anchor::* OR'd
void    frame.attach(frame_t parent);
void    frame.set_float(int64 hash, float64 v);   // widget_attr::* keys
void    frame.install_hook(int64 hook_id, int64 fn_handle);
void    frame.remove_hook(int64 hook_id);
void    frame.set_focused();
frame_t get_focused_frame();
bool    ui_is_focused();
```

## Layers

A layer is a z-stacked frame group; frames in higher layers paint over lower ones.

```cpp
layer_t create_layer(string name, bool input_passthrough, bool force_topmost);
layer_t get_default_layer();
int64   layer_count();

void  layer.promote_to_top();
void  layer.set_visible(bool v);
int64 layer.frame_count();
```

## Custom widgets on a script-owned frame

Drop a `widget_t` into one of your `frame_t`s for a custom render callback that fires every tick during the frame's render pass:

```cpp
widget_t create_widget(frame_t parent, string name, int64 execute_cb_handle, bool consume_input);
//   execute_cb shape: void cb(int64 widget_handle) — called every tick.

void widget.set_pos(vec2 pos);
void widget.set_size(vec2 size);
void widget.set_active(bool v);
void widget.set_tooltip(string s);
void widget.set_float(int64 hash, float64 v);
void widget.set_anchors(int64 mask);
void widget.install_hook(int64 hook_id, int64 fn_handle);
void widget.remove_hook(int64 hook_id);
```

## Menus

A `menu_t` is a context menu — a popup list of items. Attach it to any widget to make right-click on that widget open it.

```cpp
menu_t create_menu();
void   menu.add_item(string label, int64 on_click_cb, string shortcut, string icon);
//   shortcut: visible label only (e.g. "Ctrl+C"); not bound by add_item itself.
//   icon: codicon string or "" for none.
//   on_click_cb shape: void cb(int64 menu_user_data).
void   menu.add_separator();
```

`menu_t.attach_to_widget` is split per widget type because enma's overloading is by arity, not by parameter type. Use the variant matching the widget you're attaching to:

```cpp
void menu.attach_to_widget(widget_t target);
void menu.attach_to_button(button_t target);
void menu.attach_to_label(label_t target);
void menu.attach_to_checkbox(checkbox_t target);
void menu.attach_to_slider(slider_t target);
void menu.attach_to_slider_icon(slider_icon_t target);
void menu.attach_to_value_input(value_input_t target);
void menu.attach_to_options(options_t target);
void menu.attach_to_multi_options(multi_options_t target);
void menu.attach_to_dropdown(dropdown_t target);
void menu.attach_to_multi_dropdown(multi_dropdown_t target);
void menu.attach_to_list(list_t target);
void menu.attach_to_inline_button(inline_button_t target);
void menu.attach_to_inline_text_input(inline_text_input_t target);
void menu.attach_to_tabs(tabs_t target);
void menu.attach_to_keybind(keybind_t target);
void menu.attach_to_progress_bar(progress_bar_t target);
void menu.attach_to_spinner(spinner_t target);
void menu.attach_to_range_slider(range_slider_t target);
void menu.attach_to_table(table_t target);
void menu.attach_to_text_input(text_input_t target);
void menu.attach_to_text_editor(text_editor_t target);
void menu.attach_to_colorpicker(colorpicker_t target);
```

## File picker

```cpp
file_picker_t create_file_picker(string title, string start_path,
                                  string filter_extension, bool folder_mode);
void   picker.open();
void   picker.close();
string picker.get_selected();
```

## Theme

```cpp
bool  is_dark_theme();
void  set_dark_theme(bool dark);
color get_theme_color(int64 color_hash);
void  set_theme_color(int64 color_hash, color c);
```

`color_hash` is a value from the `ui_color` enum.

## Toasts and queries

```cpp
void show_toast(toast_kind kind, string title, string msg);
bool gui_active();
```

## Enums

All exposed without needing a header import:

| Enum           | Values                                                                                                                     |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `ui_anchor`    | `none`, `left`, `right`, `top`, `bottom`, `all`                                                                            |
| `ui_edge`      | `left`, `top`, `right`, `bottom`                                                                                           |
| `ui_align`     | `left`, `center`, `right`                                                                                                  |
| `ui_layout`    | `none`, `vertical`, `horizontal`                                                                                           |
| `ui_hook`      | 33 hook IDs incl. `pre_execute`, `post_execute`, `clicked`, `right_clicked`, `should_render`, `editor_*`, `widget_execute` |
| `ui_callback`  | `value_changed`, `item_activated`                                                                                          |
| `widget_attr`  | well-known position / size / scroll / rounding hashes                                                                      |
| `ui_color`     | 35 color hashes (`bg`, `text`, `accent`, `frame_bg`, `sidebar_bg`, `element_button_bg`, etc.)                              |
| `keybind_mode` | `off`, `on`, `single`, `toggle`, `always_on`                                                                               |
| `toast_kind`   | `info`, `success`, `warning`, `error`                                                                                      |

## Lifecycle and cleanup

GUI resources you create (sections, frames, layers, custom widgets, menus, file pickers) are tracked per-script and torn down automatically at script unload. You don't need to destroy them manually — the destructor on each handle is a noop.

Caveats:

* **Sidebar slots persist.** Sections you create occupy a sidebar slot for the lifetime of the host. Hot-reloading scripts that create many sections will leave stale slots in the sidebar.
* **Separators** stay visible after unload (no remove path).

Hook callbacks fire on the UI thread. Heavy work inside a `pre_execute` or `on_change` (running every tick on every widget) shows up in profile — keep them lightweight.

## Example

A comprehensive script exercising most of the widget builders, `on_change` plumbing through typed handles, an attached-button row, an attached colorpicker chain, a context menu, a tabs widget with per-tab content, and a routine polling `keybind.is_active()`.

```cpp
sidebar_section_t g_sec;
menu_t            g_menu;

keybind_t g_kb_aim;
keybind_t g_kb_esp;
bool g_aim_was_active = false;
bool g_esp_was_active = false;
int64 g_kb_routine = 0;

tabs_t       g_tabs;
label_t      g_t0_label; slider_t  g_t0_slider;
label_t      g_t1_label; checkbox_t g_t1_check;

void on_apply(int64 _)  { print_console("[demo] Apply clicked"); }
void on_cancel(int64 _) { print_console("[demo] Cancel clicked"); }

void on_volume(int64 self) {
    slider_t s = cast<slider_t>(self);
    print_console("Volume -> " + cast<string>(s.get()));
}

void on_features(int64 self) {
    multi_options_t mo = cast<multi_options_t>(self);
    print_console("features mask -> " + cast<string>(mo.get_mask()));
}

void on_accent(int64 self) {
    colorpicker_t cp = cast<colorpicker_t>(self);
    color c = cp.get();
    print_console("accent -> " +
        cast<string>(c.r()) + "," + cast<string>(c.g()) + "," +
        cast<string>(c.b()) + "," + cast<string>(c.a()));
}

void on_view_tabs(int64 self) {
    tabs_t t = cast<tabs_t>(self);
    int64 sel = t.get();
    // selected tab's widgets active, others inactive
    g_t0_label.set_active(sel == 0);
    g_t0_slider.set_active(sel == 0);
    g_t1_label.set_active(sel == 1);
    g_t1_check.set_active(sel == 1);
}

void on_kb_aim_changed(int64 self) {
    keybind_t kb = cast<keybind_t>(self);
    print_console("aim bindings -> " + cast<string>(kb.binding_count()));
}

// keybinds don't fire a callback on hardware-key activation —
// poll keybind.is_active() to react.
void kb_poll_routine(int64 _data) {
    bool now = g_kb_aim.is_active();
    if (now != g_aim_was_active) {
        print_console(now ? "Aim ACTIVE" : "Aim inactive");
        g_aim_was_active = now;
    }
    bool esp = g_kb_esp.is_active();
    if (esp != g_esp_was_active) {
        print_console(esp ? "ESP ACTIVE" : "ESP inactive");
        g_esp_was_active = esp;
    }
}

int32 main() {
    g_sec = create_sidebar_section("demo", "");

    g_sec.create_label("Settings panel demo.", ui_align::left);
    g_sec.create_separator();

    // Attached button row — children share the primary's row.
    button_t apply  = g_sec.create_button("Apply",  ui_align::right);
    button_t cancel = g_sec.create_button("Cancel", ui_align::right);
    cancel.attach_to(apply);
    apply.on_change(cast<int64>(on_apply));
    cancel.on_change(cast<int64>(on_cancel));

    g_sec.create_separator();
    g_sec.create_checkbox("Notifications", true);

    slider_t vol = g_sec.create_slider("Volume", 0.6, 0.0, 1.0, 0.0);
    vol.on_change(cast<int64>(on_volume));
    g_sec.create_value_input("Port", 8080.0, 1.0, 65535.0, 1.0);

    // Codicon UTF-8 byte sequence — `\xHH` lexer escape required.
    g_sec.create_slider_icon("\xEE\xA9\xB0", 0.75, 0.0, 1.0, 0.0);

    g_sec.create_separator();
    array<string> features;
    features.push("Autosave"); features.push("Spell check");
    features.push("Auto-complete"); features.push("Line numbers");
    multi_options_t mo = g_sec.create_multi_options("Editor features", features, 13);
    mo.on_change(cast<int64>(on_features));

    g_sec.create_separator();
    array<string> tab_items;
    tab_items.push("Overview"); tab_items.push("Logs");
    g_tabs = g_sec.create_tabs(tab_items, 0);
    g_tabs.on_change(cast<int64>(on_view_tabs));

    g_t0_label  = g_sec.create_label("Overview content.", ui_align::left);
    g_t0_slider = g_sec.create_slider("FOV", 90.0, 60.0, 120.0, 1.0);
    g_t1_label  = g_sec.create_label("Logs content.", ui_align::left);
    g_t1_check  = g_sec.create_checkbox("Verbose logging", false);
    g_t1_label.set_active(false);
    g_t1_check.set_active(false);

    g_sec.create_separator();
    g_kb_aim = g_sec.create_keybind("Aimbot");
    g_kb_aim.bind(0x01, false, false, false, keybind_mode::on);    // VK_LBUTTON
    g_kb_aim.on_change(cast<int64>(on_kb_aim_changed));

    g_kb_esp = g_sec.create_keybind("ESP toggle");
    g_kb_esp.bind(0x45, false, false, false, keybind_mode::toggle); // 'E'

    g_sec.create_separator();
    colorpicker_t accent = g_sec.create_colorpicker("Accent", color(180, 180, 180, 255));
    accent.on_change(cast<int64>(on_accent));

    // Attached colorpicker chain — children render as swatches in the parent's popup.
    colorpicker_t theme_cp  = g_sec.create_colorpicker("Theme",     color(120, 120, 120, 255));
    colorpicker_t primary   = g_sec.create_colorpicker("Primary",   color( 80,  80,  80, 255));
    colorpicker_t secondary = g_sec.create_colorpicker("Secondary", color(200, 200, 200, 255));
    primary.attach_to(theme_cp);
    secondary.attach_to(theme_cp);

    // Context menu attached to a button — opens on the host's right-click path.
    button_t actions = g_sec.create_button("Actions", ui_align::center);
    g_menu = create_menu();
    g_menu.add_item("Reset",     cast<int64>(on_apply),  "Ctrl+R", "");
    g_menu.add_separator();
    g_menu.add_item("About...",  cast<int64>(on_cancel), "",       "");
    g_menu.attach_to_button(actions);

    g_kb_routine = register_routine(cast<int64>(kb_poll_routine), 0);
    return 1;   // keep loaded so the section stays interactive
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/gui-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/ide.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/perception-ide.md).

# Perception IDE

Perception.cx ships with a fully integrated code editor and AI assistant. It's a native overlay panel — no Electron, no browser runtime. Write, test, and iterate on scripts without ever leaving the platform.

AI chat connects to OpenAI-compatible endpoints, GitHub Models, and GitHub Copilot via OAuth — so your existing Copilot subscription works out of the box.

***

<figure><img src="/files/IhVOyNPkf1v5KeVdtFxu" alt=""><figcaption></figcaption></figure>

<figure><img src="/files/K0kNtz2C80twuKuP74pe" alt=""><figcaption></figcaption></figure>

<figure><img src="/files/gQiJrSah7s9NQJFCrAix" alt=""><figcaption></figcaption></figure>

<figure><img src="/files/G5S15XY6gXRyqE4TrnjT" alt=""><figcaption></figcaption></figure>

<figure><img src="/files/9YhgGmCIq9f9RAPGc6RY" alt=""><figcaption></figcaption></figure>

**Editor**

**Multi-Tab Editing**

Open as many files as you want. Drag tabs to reorder, middle-click or click the × to close. Each tab tracks its own undo history, cursor position, and unsaved state.

**Syntax Highlighting**

17 languages are supported: AngelScript, Lua, C/C++, Rust, JavaScript, Python, PHP, HTML, XML, CSS, JSON, Shell, PowerShell, Batch, INI, Markdown, tsx, jsx, vue, go, cs, and log files.

**IntelliSense**

Full autocompletion for the Perception.cx API surface in both AngelScript and Lua. Includes function signatures, parameter hints, type info, and namespace-aware resolution (e.g. `sdk::player_t` resolves correctly). Trigger manually with **Ctrl+Space** or let it appear automatically as you type.

**Find & Replace**

Open with **Ctrl+F** (find) or **Ctrl+H** (find & replace). Supports regex, case sensitivity, and whole-word matching. Navigate matches with Enter/Shift+Enter or the arrow buttons.

**Line Operations**

* **Ctrl+D** — Duplicate line or selection
* **Ctrl+/** — Toggle line comment
* **Tab / Shift+Tab** — Indent / unindent selection
* **Ctrl+A** — Select all
* Standard clipboard: **Ctrl+C**, **Ctrl+X**, **Ctrl+V**

Undo (**Ctrl+Z**) and Redo (**Ctrl+Y**) use coalesced history — fast typing gets grouped into single undo steps.

**Font Scaling**

**Ctrl+Scroll** to zoom the editor font in or out.

***

**Sidebar**

The left sidebar has six tabs accessible via the activity bar icons:

* **Explorer** — project file tree
* **Chat** — AI chat panel
* **Settings** — editor configuration
* **Timeline** — file backup history and diff viewer
* **Extensions** — manage loaded extensions

***

**File Explorer**

The left sidebar shows your project's file tree with expand/collapse for folders. Right-click any item to access the context menu:

* **New File** — create a file in the selected directory
* **New Folder** — create a subdirectory
* **Rename** — rename the selected file or folder
* **Delete** — remove the selected item
* **AI Root** — set or remove the selected folder as an AI Root (see **AI Root** below)

**Workspace Folders**

You can add additional folders to your workspace from **Settings → Project → Workspace Folders**. These appear alongside the root directory in the Explorer and are included in cross-project operations like `find_references`. Click **Add Folder** to browse, and **×** to remove. Workspace folders persist across sessions.

***

**Script Toolbar**

The toolbar across the top of the editor provides one-click access to the script lifecycle:

| Button      | Action                                                             |
| ----------- | ------------------------------------------------------------------ |
| **Execute** | Compile and run the current script immediately                     |
| **Reload**  | Hot-reload a running script without restarting                     |
| **Unload**  | Stop and unload the script cleanly                                 |
| **Verify**  | Compile-check only (no execution) — shows errors with line numbers |
| **Bundle**  | Resolve all `#include` directives into a single merged output file |

The **Bundle** button uses the built-in `#include` resolver by default. You can replace it with a custom build command using **Custom Commands**.

***

**Integrated Terminal**

A built-in `cmd.exe` terminal lives at the bottom of the editor. Toggle it with **Ctrl+\`**.

**Terminal Tabs**

The terminal supports up to **8 independent tabs**, each running its own `cmd.exe` process with a separate output buffer, scroll position, and command history.

* Click **+** to open a new tab
* Click a tab to switch to it
* Click **×** on a tab to close it (at least one tab is always kept)
* Each tab shows a colored status dot: green = alive, red = process exited

**Terminal Shortcuts**

| Key           | Action                           |
| ------------- | -------------------------------- |
| **Ctrl+\`**   | Expand / collapse terminal       |
| **Ctrl+L**    | Clear terminal output            |
| **Up / Down** | Navigate command history         |
| **Ctrl+C**    | Send interrupt signal to process |
| **Esc**       | Return keyboard focus to editor  |

> **AI integration:** When the AI runs shell commands, they always execute in the **active terminal tab**. You can dedicate one tab for AI operations and keep another for manual commands.

***

**AI Chat**

The editor includes a full AI chat panel with built-in support for three API providers, plus any custom OpenAI-compatible endpoint.

**Providers**

The **Settings → Chatbot → Provider** section lets you choose between three provider modes. Each provider has completely independent settings — switching providers never overwrites another provider's configuration.

* **Default** — connect to any OpenAI-compatible API endpoint. Enter a URL, API key, and model name manually. Works with OpenRouter, LM Studio, Ollama, Together, Groq, or any cloud/local provider that speaks the standard chat completions format
* **GitHub Models** — connect to GitHub's inference API at `models.github.ai`. Enter a GitHub Personal Access Token (PAT) with `models:read` scope, then click **Fetch Models** to populate the model list from the catalog. Free tier has strict rate limits (50 req/day, 4K input tokens on most models) — enable paid billing in GitHub settings for production-grade limits
* **Copilot** — connect to the GitHub Copilot API at `api.githubcopilot.com` using your existing Copilot subscription (Pro, Pro+, Business, or Enterprise). Click **Sign in with GitHub** to authenticate via OAuth device flow — the editor opens your browser, you enter the code shown, and the token is saved automatically. Then click **Fetch Models** to get available models. Uses your Copilot subscription's rate limits and premium request allowance — no separate billing needed

**Getting Started**

1. Open the **Settings** sidebar (gear icon)
2. Under **Chatbot**, choose a **Provider** (Default, GitHub, or Copilot)
3. **Default**: enter your endpoint **URL**, **API Key**, and add a model to the **Planning / Reasoning** list
4. **GitHub**: paste your PAT in the **GitHub Token** field, click **Fetch Models**, then select a model from the dropdown
5. **Copilot**: click **Sign in with GitHub**, complete the OAuth flow in your browser, then click **Fetch Models** and select a model
6. Optionally configure an **Implementation / Coder** model for tandem mode (see **Tandem AI**)
7. Open the **Chat** sidebar tab and start typing

You can configure multiple endpoints and switch between them from the dropdown at the top of the chat panel.

**Model Selection**

Each provider maintains its own model lists for planning and coder roles. Models can be managed in two ways:

* **Manual entry** (Default provider) — click **+ Add Model** in the settings model list, enter a display name and model ID
* **Catalog fetch** (GitHub / Copilot) — click **Fetch Models** to pull all available models from the API. The model list populates automatically

Select your active model from the **filterable dropdown** at the bottom of the chat panel. Type to search, scroll with the mouse wheel, and click to select. Both planner and coder dropdowns support filtering and scrolling.

**Chat Features**

* **Streaming responses** with real-time token usage display in the header bar
* **Live generation stats** — while streaming, an animated spinner shows alongside the current speed (`~35 tok/s · 1.3s`). After completion, final stats persist below each assistant message (`456 tokens · 99.1 tok/s · 4.6s`) using the accurate token count from the API's usage response
* **Auto-continue** — if the model hits its max output token limit mid-response, the editor automatically sends a "Continue" message and resumes streaming. This repeats up to 5 times per user turn, so long analysis sessions (e.g. multi-step reverse engineering) don't require manual intervention
* **Full markdown rendering** — headings, bold/italic, inline code, fenced code blocks with syntax highlighting, tables with word-wrapped cells and per-cell clipping, horizontal rules, lists, and blockquotes
* **Thinking / reasoning** — models that output reasoning tokens get collapsible "Thinking" blocks. When collapsed, an auto-generated summary appears (e.g. "Read 3 files, edited 2 files"). Non-thinking models work normally without the thinking block
* **Conversation management** — the dropdown menu offers:
  * **New Chat** — start a fresh conversation
  * **History** — browse and load previous chat sessions (tool call badges and results are fully preserved across save/load)
  * **Clear** — wipe the current conversation
  * **Summarize & Continue** — compress older messages to free up context space. Uses structured summaries that preserve goal, changes made, validation results, pending work, and key technical details
* **Automatic context optimization** — when the assistant fully completes a response (all tool loops finished, no pending follow-ups), older tool results and tool call arguments are automatically trimmed. Large file reads become one-line summaries (e.g. `[Previously read 45 lines from foo.cpp]`), write\_file arguments are replaced with compact stubs, and RE tool outputs are condensed. Context is never trimmed mid-loop — the AI keeps full unmodified context for its entire working session
* **Tandem AI** — optionally use two models cooperatively. A planning model handles reasoning and architecture, a coder model handles implementation. See **Tandem AI** below
* **Extra system prompt** — add your own persistent instructions in the multiline text area at the bottom of the AI Chat settings section. These are injected into every API request
* **Panel positioning** — pin the chat panel on the left or right side of the editor via the **AI Chat on Right Side** checkbox

**Stopping a Response**

Click **Stop** or press **Ctrl+C** while the AI is streaming or running tools to cancel immediately. The Stop button appears in red during both streaming and tool execution (including long-running memory scans). You can then edit your message or send a new one without any issues.

**Text Selection in Chat**

You can select and copy text from any message in the chat:

* **Click and drag** on any user or assistant message text to select a range
* **Thinking blocks** (when expanded) support independent text selection
* **Ctrl+C** copies the selected text, or the full hovered message if no selection exists
* The **Copy** button on assistant messages copies the full message content

**Web Search**

The AI can search the web for current information using the `web_search` tool. Two backends are supported:

* **OpenRouter** — if your active endpoint is on OpenRouter, web search works automatically with no additional configuration. It uses OpenRouter's web plugin which is powered by native search (for OpenAI, Anthropic, Perplexity, xAI models) or Exa for other models. OpenRouter charges $4 per 1000 results ($0.02 per request at default 5 results). For example, `openai/gpt-5.2:online` works well as a search-capable model
* **Brave Search** — for non-OpenRouter endpoints, enter a Brave Search API key in Settings → **Brave Search Key**. Get a key at [brave.com/search/api](https://brave.com/search/api/)

Enable the **Web Search** toggle in Settings → Tools to make the tool available to the AI.

***

**AI Code Fill**

Separate from the chat, the editor supports inline AI code completions — similar to Copilot but running on your own model.

* Triggers automatically after a configurable delay while typing
* **Ghost text** appears inline in grey — press **Tab** to accept, **Esc** to dismiss
* Supports **FIM (Fill-in-the-Middle)** tokens for models like Qwen Coder
* Uses a **separate endpoint, model, and API key** from the chat — run a small fast model for completions and a larger model for chat
* Configurable **context window** (number of surrounding lines sent to the model)
* Platform API context is injected automatically so the model knows the Perception.cx API

**Code Fill Settings**

| Setting                      | Description                                   |
| ---------------------------- | --------------------------------------------- |
| Enable Code Fills            | Master toggle                                 |
| URL / Model / API Key        | Endpoint for completions (separate from chat) |
| Max Tokens                   | Maximum completion length                     |
| Trigger Delay (ms)           | Idle time before requesting a completion      |
| Context Lines                | Number of surrounding code lines to include   |
| Use FIM Tokens               | Enable Fill-in-the-Middle token wrapping      |
| FIM Prefix / Suffix / Middle | Custom FIM token strings for your model       |

***

**Tandem AI**

Tandem AI lets two models cooperate on tasks — a **Planning / Reasoning** model handles analysis, architecture, and review while an **Implementation / Coder** model handles code writing, edits, and validation loops.

**How It Works**

The planner model starts every conversation. When it has a detailed plan ready, it calls the `switch_model` tool to hand off to the coder. The coder implements the plan, validates the code, then switches back to the planner for review. The models self-route — no heuristic decides for them.

Both models see the full conversation history, so handoff is seamless. The `switch_model` tool call itself documents the transition in the message history.

**Setting Up**

1. In **Settings → Chatbot**, add your planning model to the **Planning / Reasoning** model list (e.g. `anthropic/claude-sonnet-4`)
2. Add your coding model to the **Implementation / Coder** model list (e.g. `google/gemini-2.5-flash`)
3. Select the desired model from each dropdown at the bottom of the chat panel
4. For the **Default** provider, you can optionally set a separate **Coder URL** and **Coder API Key** if the coder model runs on a different endpoint (e.g. planner on OpenRouter, coder on local Ollama). Leave these empty to use the planner's endpoint for both models

Select "No Coder" in the coder dropdown to disable tandem and use a single model. If both dropdowns point to the same model name, tandem is also disabled automatically.

**Separate Endpoints (Default Provider Only)**

By default, the coder uses the same URL and API key as the planner — just with a different model name in the request. If you want the coder to hit a completely different server:

* **Coder URL** — set a different API endpoint for the coder model
* **Coder API Key** — set a different API key for the coder model

Leave these empty to use the planner's endpoint. These fields are only available on the Default provider — GitHub and Copilot providers use a single endpoint for all models.

**Tips**

* The planner sets the quality ceiling. A thorough plan with exact files, functions, and changes lets even a cheap coder model execute precisely
* Use a strong model for planning (Claude, GPT-4, etc.) and a fast/cheap model for coding (Gemini Flash, Qwen Coder, etc.) to balance quality and cost
* The planner is instructed to read code before planning, produce detailed plans with exact changes, and include edge cases and validation steps
* The coder is instructed to work autonomously through the full implementation and only switch back when done, when hitting an unplanned design decision, or after 5+ validation failures

***

**AI Tool Use**

The AI doesn't just chat — it can take actions. When **Enable Tool Calls** is checked in settings, the AI has access to **65+ tools** and loops automatically until the task is done (up to the configurable **Tool Loop Limit**). Heavy reverse engineering tools run asynchronously on a background thread, keeping the UI responsive during multi-second scans. The AI keeps full context during its working session — trimming only happens after the assistant fully completes.

**File & Code Tools**

| Tool                             | Description                                                                                                                                                                |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `read_file`                      | Read a file's contents (truncated at 16KB for large files — use `read_lines` for targeted access)                                                                          |
| `read_lines`                     | Read a specific line range                                                                                                                                                 |
| `write_file`                     | Write full file contents (shows diff for review)                                                                                                                           |
| `edit_file`                      | Search/replace edit — old text must match exactly                                                                                                                          |
| `batch_edit`                     | Apply multiple search/replace edits atomically                                                                                                                             |
| `replace_all`                    | Find and replace ALL occurrences in a file                                                                                                                                 |
| `create_file`                    | Create a new file (fails if it already exists)                                                                                                                             |
| `create_directory`               | Create a directory and all parent directories                                                                                                                              |
| `insert_lines`                   | Insert text before a specific line                                                                                                                                         |
| `delete_lines`                   | Delete a range of lines                                                                                                                                                    |
| `replace_lines`                  | Replace a line range with new text. More efficient than `edit_file` when line numbers are known — no content duplication                                                   |
| `replace_selection`              | Replace the current editor selection                                                                                                                                       |
| `search_text`                    | Search across open files                                                                                                                                                   |
| `find_references`                | Search across ALL project files on disk (all workspace roots)                                                                                                              |
| `get_file_info`                  | Get file info: path, language, lines, size in bytes. Accepts optional path (defaults to active file). Use to check size before reading unknown files                       |
| `get_open_files`                 | List all open buffers with line counts and modified status                                                                                                                 |
| `list_files`                     | List directory contents (lists all workspace roots when given `.`)                                                                                                         |
| `get_symbols`                    | List function/struct/class/enum definitions in a file                                                                                                                      |
| `open_file`                      | Open a file in a new editor tab                                                                                                                                            |
| `save_file`                      | Save a file to disk                                                                                                                                                        |
| `goto_line`                      | Move cursor to a line number                                                                                                                                               |
| `get_clipboard`                  | Read system clipboard text                                                                                                                                                 |
| `get_recent_changes`             | Get last 20 undo history entries                                                                                                                                           |
| `add_bookmark` / `get_bookmarks` | Manage named bookmarks                                                                                                                                                     |
| `check_script`                   | Compile-check a script for errors without executing. Automatically uses the extension API surface for files in `extensions/`                                               |
| `validate_script`                | Compile and optionally run a script. Extensions are compile-only (no `run=true` — they have no `main()`)                                                                   |
| `get_script_api`                 | Load the Perception.cx scripting API reference for a language (`angelscript`, `lua`, or `extension`). **Mandatory** — the AI must call this before writing any script code |

**Shell & Automation Tools**

| Tool                 | Description                                                                                                                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exec_shell_command` | Run a command in the active terminal tab (30s timeout)                                                                                                                             |
| `run_custom_command` | Run a user-defined custom command by name                                                                                                                                          |
| `execute_script`     | Write and run an AngelScript/Lua script on the fly                                                                                                                                 |
| `ask_user`           | Pause and ask you a question, then resume after you respond                                                                                                                        |
| `ask_mcq`            | Pause and ask you multiple questions in one tool call, then result after you respond                                                                                               |
| `web_search`         | Search the web via Brave Search API or OpenRouter web plugin                                                                                                                       |
| `manage_context`     | AI self-optimizes its context window: `drop_tools` removes unneeded tool categories (saves tokens), `trim_history` trims old turns                                                 |
| `update_notes`       | Persistent working notes (2KB) that survive context trimming. The AI uses this to preserve key discoveries from RE sessions — addresses, offsets, struct layouts, decrypted values |
| `switch_model`       | Switch between planning and coder models during tandem AI. Only available when an Implementation / Coder model is configured                                                       |

**Diff Review Tools**

| Tool                   | Description                               |
| ---------------------- | ----------------------------------------- |
| `get_diff`             | Get current pending diff state            |
| `wait_for_diff_review` | Pause until you resolve all pending diffs |

**Reverse Engineering Tools**

| Tool                 | Description                                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `list_processes`     | List processes with PID, name, base address, EPROCESS                                                                |
| `get_process_info`   | Detailed process info: modules, threads, PEB, DTB                                                                    |
| `read_memory`        | Read bytes as hex dump + ASCII (max 4096 bytes)                                                                      |
| `read_typed_value`   | Read typed values: uint8–64, float, double, pointer arrays                                                           |
| `find_pattern`       | IDA-style byte pattern scanning with `?` wildcards                                                                   |
| `read_pointer_chain` | Follow pointer chain with offsets at each dereference                                                                |
| `read_string`        | Read ASCII or Unicode string from memory                                                                             |
| `get_module_exports` | List exported functions from a module's PE export table                                                              |
| `get_module_imports` | List imported functions from a module's PE import table (DLL names, function names, IAT addresses, resolved targets) |

**Advanced Tools**

These are gated behind the **Allow Advanced Writing Tools** checkbox in settings:

| Tool                           | Description                                                                                                                                                                                     |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `memory_write`                 | Write bytes to process memory (works on any section including `.text` — no protection changes needed)                                                                                           |
| `scan_string` / `scan_wstring` | Scan ALL committed process memory for ASCII/Unicode strings. Full VAD scan — no range limit                                                                                                     |
| `disassemble`                  | Disassemble x86-64 instructions at an address (Zydis)                                                                                                                                           |
| `delete_file`                  | Permanently delete a file                                                                                                                                                                       |
| `scan_pointer_to`              | Reverse pointer scan — find all memory locations containing a pointer to a target address. Full VAD scan                                                                                        |
| `scan_value`                   | Scan ALL process memory for typed values (uint16–64, int32/64, float, double) with optional tolerance                                                                                           |
| `scan_changed`                 | Cheat Engine-style iterative scanning: first scan → filter by changed/increased/decreased/unchanged/exact                                                                                       |
| `diff_memory`                  | Snapshot a memory region, wait, snapshot again, report all changed bytes with hex + float interpretations                                                                                       |
| `struct_dump`                  | Read memory and heuristically classify each 8-byte field: pointers, vtables, floats, doubles, ints, nulls                                                                                       |
| `find_xrefs`                   | Find all code cross-references to an address. Scans entire module in 4MB chunks — no size cap, works on 400MB+ modules                                                                          |
| `find_string_refs`             | Find code that references a string. Combines `scan_string` + `find_xrefs` in one call — scans all memory for the string, then sweeps entire module code for LEA/MOV instructions pointing to it |
| `find_function_bounds`         | Given any address inside a function, detect prologue/epilogue to find function start and end                                                                                                    |
| `analyze_function`             | Annotated disassembly with basic block labels, CALL targets, stack frame size, and control flow markers                                                                                         |
| `trace_register`               | Static backward trace: find where a register gets its value, resolve RIP-relative globals                                                                                                       |
| `analyze_vtable`               | Read vtable slots and verify each is a valid function pointer by decoding prologue bytes                                                                                                        |
| `read_rtti`                    | Read MSVC RTTI from an object pointer or vtable address. Returns class name, base classes, and inheritance hierarchy                                                                            |
| `generate_signature`           | Auto-generate IDA-style byte signatures with automatic wildcarding of RIP-relative displacements                                                                                                |
| `build_call_graph`             | Build recursive call graph from a function showing call relationships, instruction counts, and depth                                                                                            |
| `get_module_imports`           | List imported functions from a module's PE import directory                                                                                                                                     |

> **Physical memory:** All process memory operations use physical memory page table translation. This means you can read and write any memory including executable `.text` sections without changing page protection — no `VirtualProtect` needed.

***

**Diff Review**

When the AI edits a file, it doesn't overwrite your code directly. Every change goes through a diff review:

* Changes are displayed as individual **hunks** with green (added) / red (removed) highlighting
* Navigate between hunks with **Up / Down** arrow keys
* **Enter** — accept the focused hunk
* **Delete** — reject the focused hunk
* **Ctrl+Shift+A** — accept all hunks at once
* **Esc** — reject all remaining hunks

The AI can call `wait_for_diff_review` to pause until you've resolved all pending diffs before it continues. Alternatively, enable **Auto-accept AI edits** in settings to skip review entirely.

***

**AI Root**

AI Root lets you scope where the AI operates within your project. When set, the AI will only read, write, and browse files within the designated folder(s).

**Setting an AI Root**

1. In the **File Explorer** sidebar, right-click any folder
2. Click **AI Root** to toggle it on or off
3. Folders marked as AI Root show a visual indicator in the tree

You can set multiple AI Roots. When at least one is set, the AI's file operations are restricted to those directories. When no AI Roots are set, the AI can access the entire project.

AI Roots persist across sessions and are saved with your editor state.

***

**Custom Commands**

Custom Commands let you define named shell commands that integrate into the editor and AI workflow. Define them in **Settings → Custom Commands**.

**Creating a Command**

1. Click **+ Add Command**
2. Enter a **Name** (e.g. "Build", "Test", "Deploy")
3. Enter a **Command** (e.g. `build.bat`, `python test.py`, `npm run build`)
4. Optionally check **Use as Bundler** to replace the toolbar's Bundle button with this command

**Bundler Override**

When a custom command has **Use as Bundler** enabled, clicking the **Bundle** button in the script toolbar will run your custom command in the terminal instead of the built-in `#include` resolver. Only one command can be the active bundler at a time.

This is useful for custom build pipelines — C-preprocessor macro expansion, hash baking, minification, or any project-specific processing the built-in bundler doesn't cover.

**AI Integration**

Custom commands are automatically exposed to the AI as the `run_custom_command` tool. The AI can invoke any of your defined commands by name during agentic workflows. For example, after editing files the AI could run your custom build command to verify compilation.

***

**Extensions**

The editor supports AngelScript-based extensions that hook into the editor lifecycle, AI chat pipeline, and provide custom UI widgets. Extensions have full access to the Perception.cx platform API — the same surface available to regular scripts.

**Installing Extensions**

Place `.as` files in the `extensions/` folder inside your scripting main directory. The editor scans this directory every 3 seconds and automatically picks up new files or removes deleted ones.

**Managing Extensions**

Click the 🧩 puzzle icon in the activity bar to open the **Extensions** panel. Each extension shows a card with its name, version, description, ON/OFF toggle, Reload button, and any compile errors. Extension state persists across sessions.

**What Extensions Can Do**

* **Editor events** — react to files being opened, saved, edited, or tabs switching
* **AI pipeline** — intercept prompts before sending, inject system prompt text, observe or handle tool calls, register custom AI tools
* **IntelliSense** — provide custom completions and hover tooltips for any file type (not limited to AngelScript/Lua)
* **Custom UI** — render checkboxes, sliders, buttons, text inputs, progress bars, dropdowns, color pickers, and keybind capture widgets in the sidebar
* **Editor manipulation** — insert text, replace selection, set selection range, open files, save files, and jump to lines programmatically
* **File I/O** — read files, write files, check existence, and list directories from extension code
* **Clipboard** — get and set system clipboard text
* **Network** — synchronous HTTP GET/POST requests with custom headers (10s timeout)
* **Platform access** — use a selection of Perception.cx APIs including rendering, input, CPU intrinsics, WinAPI, JSON, Zydis, and utilities. Process memory, mutexes, and extended math are not available in extensions

**Validation**

Extension scripts can be validated using the same `check_script` and `validate_script` tools (or the Verify toolbar button). The editor automatically detects that the file is in `extensions/` and uses a dedicated validator with the extension API surface. Note that `validate_script` with `run=true` is not supported for extensions — they are event-driven and have no `main()` entry point. The `execute_script` tool also cannot be used with extension code.

For the full extension API reference, examples, and hook documentation, see the **Extension Development** page.

***

**File Backups & Timeline**

Every save creates a timestamped backup. The **Timeline** sidebar tab lets you browse and compare backups:

* All backups for the current file are listed, sorted by date
* Click any backup to open a **side-by-side diff view** comparing it against the current version
* Line-level add/remove/change highlighting
* Configurable **max backup count** and **backup directory** in settings
* Deleted file recovery — the most recent backup of removed files is preserved

***

**Settings**

All configuration lives in the **Settings** sidebar tab (gear icon). Everything persists to disk automatically.

**Project**

* **Root Directory** — your project folder. Set via the text field and click Apply
* **Workspace Folders** — additional folders to include alongside the root directory. Click **Add Folder** to browse, **×** to remove
* **AI Root** — managed via right-click in the file explorer (see **AI Root**)

**Editor**

* **Scroll Speed** — mouse wheel scroll multiplier
* **Autoscroll Speed** — speed when auto-scrolling during selection drag

**Bundler**

* **Strip comments from output** — remove comments when bundling `#include` files

**Chatbot**

| Setting                        | Description                                                                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| AI Chat on Right Side          | Pin the chat panel to the right side of the editor                                                                           |
| Auto-accept AI edits           | Skip diff review and apply AI changes immediately                                                                            |
| Allow Advanced Writing Tools   | Enable dangerous tools: memory write, disassemble, delete file, string scan, and advanced RE analysis tools                  |
| Enable Tool Calls              | Allow the AI to use tools (file ops, RE tools, shell, etc.)                                                                  |
| Provider                       | Choose **Default**, **GitHub**, or **Copilot**. Each provider has independent settings that don't affect the others          |
| URL *(Default only)*           | API endpoint URL (OpenAI-compatible)                                                                                         |
| API Key *(Default only)*       | Bearer token for authentication                                                                                              |
| GitHub Token *(GitHub only)*   | Personal Access Token with `models:read` scope                                                                               |
| Sign in *(Copilot only)*       | OAuth device flow — click to authenticate with your GitHub Copilot subscription                                              |
| Planning / Reasoning           | Model list for the planning model. Add models manually (Default) or fetch from catalog (GitHub/Copilot)                      |
| Implementation / Coder         | Model list for the coder model. Select "No Coder" to disable tandem mode                                                     |
| Coder URL *(Default only)*     | Separate API endpoint for the coder model. Leave empty to use the planner's endpoint                                         |
| Coder API Key *(Default only)* | Separate API key for the coder model. Leave empty to use the planner's key                                                   |
| Tool Loop Limit                | Maximum number of consecutive tool call rounds                                                                               |
| Temperature                    | Sampling temperature (0.0–2.0). Not sent for GitHub/Copilot providers — models use their own defaults                        |
| Top P                          | Nucleus sampling threshold. Not sent for GitHub/Copilot providers                                                            |
| Brave Search Key               | API key for Brave web search (not required if using OpenRouter — web search works automatically via OpenRouter's web plugin) |
| Extra System Prompt            | Your own persistent instructions appended to every request                                                                   |

**Code Fill**

See **AI Code Fill** for details on each setting.

**Backups**

| Setting          | Description                        |
| ---------------- | ---------------------------------- |
| Max Backups      | Maximum number of backups per file |
| Backup Directory | Where backup files are stored      |

**Custom Commands**

See **Custom Commands** for details.

***

**Keyboard Shortcuts**

**Editor**

| Key         | Action                             |
| ----------- | ---------------------------------- |
| Ctrl+S      | Save file                          |
| Ctrl+W      | Close tab                          |
| Ctrl+F      | Find                               |
| Ctrl+H      | Find & Replace                     |
| Ctrl+Z      | Undo                               |
| Ctrl+Y      | Redo                               |
| Ctrl+D      | Duplicate line / selection         |
| Ctrl+/      | Toggle comment                     |
| Ctrl+Space  | Trigger code fill manually         |
| Ctrl+Scroll | Zoom font size                     |
| Tab         | Accept AI suggestion / Indent      |
| Esc         | Dismiss AI suggestion / Close find |

**Diff Review**

| Key          | Action                 |
| ------------ | ---------------------- |
| Enter        | Accept hunk            |
| Delete       | Reject hunk            |
| Up / Down    | Navigate between hunks |
| Ctrl+Shift+A | Accept all hunks       |
| Esc          | Reject all hunks       |

**Chat**

| Key         | Action                                                                     |
| ----------- | -------------------------------------------------------------------------- |
| Enter       | Send message                                                               |
| Shift+Enter | New line in message                                                        |
| Ctrl+C      | Cancel AI stream (while streaming) / Copy selected text or hovered message |

**Terminal**

| Key       | Action                     |
| --------- | -------------------------- |
| Ctrl+\`   | Expand / collapse terminal |
| Ctrl+L    | Clear terminal output      |
| Up / Down | Command history            |
| Ctrl+C    | Send interrupt to process  |
| Esc       | Return focus to editor     |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/perception-ide.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/input-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/input-api.md).

# Input API

All input natives are auto-registered into every loaded script.

Read-only complement to [Win API](win-api.md) — Win API **sends** input, this **reads** state. Pollable per-frame from `my_draw` or routine callbacks.

Virtual-key codes follow Win32 VK\_\* convention. The `vk` enum bundles the common ones so no `#include` is needed.

## Mouse

```cpp
vec2 get_mouse_pos();             // render-window pixels
vec2 get_mouse_pos_desktop();     // desktop pixels (full screen)
vec2 get_mouse_delta();           // raw movement this frame
vec2 get_mouse_delta_desktop();   // desktop-space delta this frame

bool    mouse_movement_received();          // any movement this frame
bool    is_hovered(vec2 pos, vec2 size);    // mouse inside rect at pos with given size
float64 get_scroll_delta();                 // wheel ticks; positive = up
```

## Keyboard — single-flag queries

| Flag          | Meaning                                      |
| ------------- | -------------------------------------------- |
| `down`        | currently pressed (host-debounced)           |
| `raw_down`    | OS-level pressed state                       |
| `fired`       | up→down transition this frame                |
| `toggle`      | caps-lock-style toggle (flips on each press) |
| `singlepress` | fired but suppressed when modifiers are held |
| `prev_down`   | down state from previous frame               |

```cpp
bool key_down       (int64 vk);
bool key_raw_down   (int64 vk);
bool key_fired      (int64 vk);
bool key_toggle     (int64 vk);
bool key_singlepress(int64 vk);
bool key_prev_down  (int64 vk);
```

## Bulk / ergonomic queries

```cpp
key_state_t  get_key_state(int64 vk);    // atomic snapshot of all 6 flags
array<int32> get_keys_down();            // virtual-key codes currently pressed
string       get_recent_key_input();     // buffered text input (UTF-8) since last poll
string       get_key_name(int64 vk);     // localized key name (e.g. "F1", "Left Arrow"); empty on invalid
```

### `key_state_t`

```cpp
bool ks.raw_down();      // OS-level pressed state
bool ks.down();          // host-debounced pressed state
bool ks.fired();         // up->down this frame (one-shot)
bool ks.toggle();        // caps-lock-style toggle (flips on each press)
bool ks.singlepress();   // fired but suppressed if modifiers held
bool ks.prev_down();     // down state from previous frame
```

Use `get_key_state(vk)` when you need consistency across multiple flag reads in the same frame — the per-flag fns above each take a separate lock and can race.

## `vk` enum — common Win32 virtual keys

```cpp
vk::backspace  vk::tab       vk::enter     vk::shift     vk::ctrl     vk::alt
vk::pause      vk::caps_lock vk::escape    vk::space
vk::page_up    vk::page_down vk::end       vk::home
vk::left       vk::up        vk::right     vk::down
vk::insert     vk::delete

vk::k0 .. vk::k9          // top-row digits
vk::a  .. vk::z           // letters

vk::lwin       vk::rwin
vk::numpad0 .. vk::numpad9
vk::multiply   vk::add     vk::subtract  vk::decimal  vk::divide

vk::f1 .. vk::f12

vk::num_lock   vk::scroll_lock
vk::lshift     vk::rshift
vk::lctrl      vk::rctrl
vk::lalt       vk::ralt

// Mouse buttons (Win32 puts these in the same VK space):
vk::lbutton  vk::rbutton  vk::mbutton  vk::xbutton1  vk::xbutton2
```

## Example: trigger an action on F1 press

```cpp
void my_tick(int64 data) {
    if (key_fired(vk::f1)) {
        println("F1 pressed");
    }
}

int64 main() {
    register_routine(cast<int64>(my_tick), 0);
    return 1;
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/input-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lifecycle-and-routines.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/lifecycle-and-routines.md).

# Lifecycle and Routines

## Entry point

Every script needs a `main()` function. It runs once when the script is loaded.

```cpp
int64 main() {
    // setup state, load resources, register routines
    return 1;
}
```

`main()`'s return value decides what happens next:

| Return | Behavior                                           |
| ------ | -------------------------------------------------- |
| `> 0`  | Script stays loaded.                               |
| `<= 0` | Script unloads immediately after `main()` returns. |

Use `return 1;` for any normal long-lived script. Return `0` for one-shot scripts that just wanted to do work in `main()` and exit.

## Routines

A routine is a script function that runs continuously after `main()` returns. Routines are how your script keeps doing work over time.

```cpp
int64 register_routine(int64 fn_handle, int64 data);
bool  unregister_routine(int64 routine_handle);
```

### Callback shape

The function you register takes one `int64` parameter:

```cpp
void my_callback(int64 data) {
    // data: the value you passed as the second arg to register_routine
}
```

Pass the function as a closure handle via `cast<int64>(fn_name)`:

```cpp
int64 main() {
    int64 r = register_routine(cast<int64>(my_callback), 42);
    return 1;
}
```

`register_routine` returns a handle. Keep it if you intend to unregister later, or discard.

### Multiple routines

Register as many as you need.

```cpp
void on_render(int64 data) { /* draw */ }
void on_tick(int64 data)   { /* update logic */ }

int64 main() {
    register_routine(cast<int64>(on_render), 0);
    register_routine(cast<int64>(on_tick), 0);
    return 1;
}
```

### Unregistering

```cpp
unregister_routine(my_handle);
```

A routine can also unregister itself from inside its own callback:

```cpp
int64 g_handle;

void my_callback(int64 data) {
    if (should_stop()) {
        unregister_routine(g_handle);
        return;
    }
    // normal work
}

int64 main() {
    g_handle = register_routine(cast<int64>(my_callback), 0);
    return 1;
}
```

## Unload

A script unloads when `main()` returns `<= 0`, when the user unloads it from the UI, or when the host shuts down. On unload all routines stop and any GPU resources you created via the render API are destroyed automatically.

## Exceptions

Routines automatically catch uncaught throws and faults. The error is logged to `<my_games>\exceptions\enma.log` with a timestamp, the routine id, the thrown value, and the source line where it happened. The script keeps running.

## Diagnostic helpers

Quick tracing without touching the renderer:

```cpp
void heartbeat();                          // log "heartbeat called"
void take_int(int64 x);                    // log an int value
void take_ptr(int64 p);                    // log a pointer in hex
void test_3arg(int64 a, int64 b, int64 c); // log three ints
```

Useful for confirming a code path is reached or sanity-checking a value.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/lifecycle-and-routines.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/mcp-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/mcp-api.md).

# MCP API

Perception's MCP server exposes the proc-API surface as JSON-RPC tools that any [Model Context Protocol](https://modelcontextprotocol.io/) client (Claude Code, Cline, Continue, ...) can call.

Writing an Enma script? Use [Proc](proc-api.md) / [CPU](cpu-api.md) / [Zydis](zydis-api.md) directly. Driving perception from an AI agent? Enable MCP.

## Enable

In perception, **Settings → Perception MCP**:

1. Type a **Bind port** (1024..65535), or leave blank for OS-pick.
2. Toggle **Enable MCP server** on.
3. Copy the **Bound URL** that appears.

The server is loopback-only.

### Other toggles in the same panel

* **Auto-start on perception load** — persisted; on next launch the server starts automatically using the saved port (config loads before the autostart fires, so the saved port is reused rather than regenerated).
* **Heap-only scans by default** — controls the default of the `heap_only` flag on `scan_value` / `scan_string` / `scan_pointer_to` / `find_string_refs` when an MCP caller omits it. **On by default.** Flipping it off makes those tools walk the entire user-space when callers don't supply `heap_only`, which can OOM or hang on targets with multi-GiB heaps (Forza-class).

## Connect

**Claude Code:**

```
claude mcp add --transport http perception http://127.0.0.1:<port>/mcp
```

Add `--scope user` for global registration. Other clients (Cline, Continue, ...) accept the same URL via their Streamable HTTP transport.

## Transport

The server auto-detects two framings on the same port:

| First bytes                           | Framing                 | Used by                              |
| ------------------------------------- | ----------------------- | ------------------------------------ |
| `POST` / `GET` / `OPTIONS` / `DELETE` | HTTP/1.1 streamable     | MCP clients                          |
| anything else                         | Line-delimited JSON-RPC | The cpp example below, raw debugging |

Both carry JSON-RPC 2.0. Real MCP clients use the 5 protocol methods (`initialize` / `notifications/initialized` / `tools/list` / `tools/call` / `ping`); raw clients can call tool methods directly (`"method": "process/list"`).

## Handles

Most tools need a `handle` from `process/reference_by_pid` / `_by_name`. Handles are **per-connection**:

* Other connections can't use yours.
* Disconnecting releases everything automatically.
* Manual release: `process/dereference` (one) or `process/cleanup_references` (all).

## Permissions

Shared with [enma](proc-api.md#permissions). Toggle in **Scripting → API permissions**:

| Flag                        | Gates                                                                                                                                                                                                                |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `kernel_rw_access`          | Kernel-mode addresses in any read / write / disasm / `query_memory_region` / `find_pattern*` call; the `eprocess` field in `process/list` + `info_by_*`; the `ethread` field in `get_threads`; `system/list_drivers` |
| `write_memory`              | Every tool that writes target memory: `write_virtual_memory`, `write_typed_value`, `write_string`, `copy_memory`, `fill_memory`                                                                                      |
| `virtual_memory_operations` | `allocate_memory`, `free_memory`                                                                                                                                                                                     |

Blocked calls return `-32001` with the missing permission named.

## Error codes

| Code     | Meaning                         |
| -------- | ------------------------------- |
| `-32700` | Parse error                     |
| `-32600` | Invalid request                 |
| `-32601` | Method not found                |
| `-32602` | Invalid params                  |
| `-32603` | Internal                        |
| `-32001` | Permission denied               |
| `-32002` | Stale / cross-connection handle |
| `-32003` | Target not found                |
| `-32004` | Operation failed                |

## Tools

59 tools. Addresses + handles are **hex strings** (`"0x7ff7..."`) — JSON numbers lose precision past 2^53. Required params are listed plain, optional params get `?`.

Every "take a handle" tool below has `handle` as its first param — omitted from the params column to keep things readable. The tools that don't take a handle are called out per-section.

### Discovery + reference lifecycle

Params shown literally (no implicit `handle` — `process/dereference` explicitly takes the handle it's about to release).

| Tool                         | Params   |                                                   |
| ---------------------------- | -------- | ------------------------------------------------- |
| `process/list`               | —        | Snapshot of every active process.                 |
| `process/info_by_pid`        | `pid`    | One process by PID.                               |
| `process/info_by_name`       | `name`   | One process by image name.                        |
| `process/reference_by_pid`   | `pid`    | Take a per-connection handle. Returns hex string. |
| `process/reference_by_name`  | `name`   | Same, by image name.                              |
| `process/dereference`        | `handle` | Release one handle.                               |
| `process/cleanup_references` | —        | Release every handle this connection holds.       |
| `process/list_references`    | —        | What this connection currently holds.             |

### Memory I/O

| Tool                           | Params                                            |                                                                                   |
| ------------------------------ | ------------------------------------------------- | --------------------------------------------------------------------------------- |
| `process/read_virtual_memory`  | `address`, `size`                                 | Raw bytes as hex. Max 16 MiB.                                                     |
| `process/write_virtual_memory` | `address`, `data`                                 | Gated `write_memory`. `data` is hex.                                              |
| `process/is_valid_address`     | `address`                                         | Does the address resolve?                                                         |
| `process/read_typed_value`     | `address`, `type`                                 | `type` ∈ `u8..u64 / i8..i64 / f32 / f64 / ptr / bool`.                            |
| `process/write_typed_value`    | `address`, `type`, `value`                        | Gated `write_memory`. Use hex string for `value` when type is u64/i64/ptr.        |
| `process/read_string`          | `address`, `max_len?`, `encoding?`                | `max_len` 1024 default. `encoding` ∈ `auto / ascii / utf16` (default auto-sniff). |
| `process/write_string`         | `address`, `text`, `encoding?`, `null_terminate?` | Gated `write_memory`. `encoding` ∈ `ascii / utf16`.                               |
| `process/copy_memory`          | `src_address`, `dst_address`, `size`              | In-target memcpy. Gated `write_memory`. Max 64 MiB, 1 MiB chunks.                 |
| `process/fill_memory`          | `address`, `size`, `byte`                         | Memset. `byte` 0..255 (0x90 = NOP, 0xCC = int3). Gated `write_memory`.            |
| `process/read_pointer_chain`   | `base_address`, `offsets`                         | `offsets` is an int array, max 64.                                                |
| `process/disassemble`          | `address`, `max_bytes?`, `max_instructions?`      | Zydis. Defaults 256 / 32.                                                         |

### Modules / threads / PE

| Tool                          | Params                                    |                                                                                                                                                                                                                            |
| ----------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `process/get_modules`         | —                                         | All loaded modules.                                                                                                                                                                                                        |
| `process/get_threads`         | —                                         | All threads.                                                                                                                                                                                                               |
| `process/get_module_by_name`  | `name`                                    | One module by name.                                                                                                                                                                                                        |
| `process/get_export_address`  | `module_base`, `export_name`              | Single resolve.                                                                                                                                                                                                            |
| `process/get_import_address`  | `module_base`, `import_name`              | Resolve IAT slot VA.                                                                                                                                                                                                       |
| `process/get_module_imports`  | `module_base`                             | Full IAT walk.                                                                                                                                                                                                             |
| `process/list_module_exports` | `module_base`                             | Full EAT walk.                                                                                                                                                                                                             |
| `process/get_module_sections` | `module_base`                             | PE sections.                                                                                                                                                                                                               |
| `process/get_pe_header`       | `module_base`                             | NT/optional header summary.                                                                                                                                                                                                |
| `process/get_module_strings`  | `module_base`, `min_length?`, `encoding?` | `min_length` default 4. `encoding` ∈ `ascii / utf16 / both` (default both).                                                                                                                                                |
| `process/get_exception_table` | `module_base`, `max_entries?`             | x64 RUNTIME\_FUNCTION entries from `.pdata`. Precise function bounds.                                                                                                                                                      |
| `process/get_data_directory`  | `module_base`, `directory`                | One PE data-dir entry. `directory` ∈ `export / import / resource / exception / security / basereloc / debug / architecture / globalptr / tls / load_config / bound_import / iat / delay_import / com_descriptor` or 0..15. |

### Memory regions + allocation

| Tool                               | Params       |                                                                                                                                                                                                   |
| ---------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `process/query_memory_region`      | `address`    | VirtualQuery-style.                                                                                                                                                                               |
| `process/enumerate_memory_regions` | `heap_only?` | All committed regions. `heap_only` default false.                                                                                                                                                 |
| `process/allocate_memory`          | `size`       | Gated `virtual_memory_operations`. Max 256 MiB. Allocation itself is safe. To execute code from the returned VA the target must have Control Flow Guard (CFG) off; reads + writes are unaffected. |
| `process/free_memory`              | `address`    | Same gate.                                                                                                                                                                                        |

### Pattern + scanner + xrefs + signature

| Tool                         | Params                                                             |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ---------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `process/find_pattern`       | `start`, `size`, `signature`                                       | IDA-style `"AB CD ?? EF"`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `process/find_all_patterns`  | `start`, `size`, `signature`                                       | Same, all hits (cap 1024).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `process/scan_value`         | `type`, `value`, `aligned?`, `heap_only?`                          | `type` ∈ `u8..u64 / i8..i64 / f32 / f64`. Use hex string for `value` when u64/i64. Defaults: aligned true. `heap_only` defaults to the MCP UI's "Heap-only by default" toggle (on by default — skips code/module regions); pass `heap_only=false` to walk full user-space.                                                                                                                                                                                                                                                                                                             |
| `process/scan_next`          | `compare`, `value?`, `min?`, `max?`                                | `compare` ∈ `exact / range / unchanged / changed / increased / decreased`. `value` for `exact`, `min`+`max` for `range`.                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `process/scan_string`        | `text`, `encoding?`, `heap_only?`                                  | `encoding` ∈ `ascii / utf16`, default ascii. `heap_only` default = UI toggle (see `scan_value`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `process/scan_pointer_to`    | `target_address`, `heap_only?`                                     | Aligned QWORDs pointing at `target_address`. `heap_only` default = UI toggle.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `process/find_xrefs`         | `module_base`, `target_address`                                    | Decode `.text`, return refs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `process/find_string_refs`   | `module_base`, `text`, `encoding?`, `heap_only?`, `string_module?` | Combo: scan for the string, then decode `module_base`'s `.text` for code refs to each hit. Phase 1 (string search) defaults to a heap-only VAD walk (`heap_only` follows the UI toggle) and is **pre-capped at 1 GiB** so the listener never crashes on huge targets — if the cap fires the call returns an error asking you to pass `heap_only=true` or set `string_module` (hex VA of the module that owns the string, usually the same as `module_base`) for a fast bounded scan of just that module's image. Phase 2 caps code hits at 4096; response includes a `truncated` flag. |
| `process/generate_signature` | `address`, `max_length?`                                           | Default 32. `is_unique=false` if length exhausted.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `process/diff_memory`        | `addr_a`, `addr_b`, `size`                                         | Cap 1 MiB.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

### Code analysis

| Tool                                 | Params                                   |                                                                             |
| ------------------------------------ | ---------------------------------------- | --------------------------------------------------------------------------- |
| `process/find_function_bounds`       | `address`, `scan_back?`, `scan_forward?` | Defaults 4096 / 65536. Heuristic — use `get_exception_table` for precision. |
| `process/find_function_by_signature` | `module_base`, `signature`               | AOB-scan a module's `.text` + run bounds walk on each hit.                  |
| `process/analyze_vtable`             | `vtable_address`, `max_entries?`         | Default 64. Classifies entries as code/data per loaded modules.             |
| `process/read_rtti`                  | `vtable_address`                         | Win64 RTTI: class name + base classes.                                      |

### Symbol / function lookup

| Tool                            | Params                                       |                                                                                          |
| ------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `process/lookup_symbol`         | `address`                                    | VA → `{module_base, module_name, module_offset, section, nearest_export}`.               |
| `process/find_function_by_name` | `pattern`, `case_sensitive?`, `max_results?` | Substring match across all modules' export tables. Default case-insensitive, 64 results. |

### Handles

| Tool                   | Params         |                                                                            |
| ---------------------- | -------------- | -------------------------------------------------------------------------- |
| `process/enum_handles` | `max_entries?` | Default 8192. `NtQuerySystemInformation(SystemExtendedHandleInformation)`. |

### System / environment

| Tool                       | Params         |                                                                                                              |
| -------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------ |
| `system/info`              | —              | Build number, page size, processor count + arch. `is_24h2_or_later` flag for build-keyed offsets. No handle. |
| `system/list_drivers`      | `max_entries?` | Kernel modules via `NtQuerySystemInformation(SystemModuleInformation)`. Gated `kernel_rw_access`. No handle. |
| `process/get_command_line` | —              | Reads `PEB.ProcessParameters.CommandLine`. x64 only.                                                         |
| `process/list_environment` | `max_bytes?`   | Reads `PEB.ProcessParameters.Environment`. Returns `[{key, value}]`.                                         |

### Enma scripting bridge

None of these takes a `handle` — they run a script (or return reference text) with its own permissions, independent of any referenced process.

| Tool                 | Params   |                                                                                                                                                                                                                                                                                                                                    |
| -------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `script/get_context` | —        | Returns the full enma language + Perception API reference as a single `context` string. **Call this once per session before generating any script** — enma is proprietary and its addon surface can't be inferred from training data. Covers language grammar, all 17 pre-shipped enma addons, and all 12 Perception API surfaces. |
| `script/validate`    | `source` | Compile-only. **All** addons registered (render / proc / cpu / zydis / sound / win / unicorn / net / input / **gui** / **thread** / filesystem). Returns `{ ok, errors:[] }`.                                                                                                                                                      |
| `script/execute`     | `source` | Compile + run `main()` once. **GUI and thread addons are NOT registered** — those resources would outlive a one-shot script and leak. For long-lived scripts use the in-app script editor. Returns `{ ok, logs:[] }`.                                                                                                              |

## Example — minimal C++ client

Build with the VS Developer Command Prompt:

```
cl /EHsc /std:c++17 minimal_mcp.cpp /link Ws2_32.lib
```

```cpp
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>
#pragma comment(lib, "Ws2_32.lib")

int main(int argc, char** argv) {
    if (argc < 2) { printf("usage: %s <port>\n", argv[0]); return 1; }
    WSADATA wd; WSAStartup(MAKEWORD(2, 2), &wd);

    SOCKET s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    sockaddr_in a{};
    a.sin_family = AF_INET;
    a.sin_port   = htons((u_short)atoi(argv[1]));
    inet_pton(AF_INET, "127.0.0.1", &a.sin_addr);
    if (connect(s, (sockaddr*)&a, sizeof(a)) != 0) { printf("connect failed\n"); return 1; }

    auto call = [&](const char* line) {
        send(s, line, (int)strlen(line), 0);
        char buf[8192];
        int n = recv(s, buf, sizeof(buf) - 1, 0);
        if (n > 0) { buf[n] = 0; printf("%s", buf); }
    };

    // 1. List processes.
    call("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"process/list\",\"params\":{}}\n");

    // 2. Reference notepad.exe.
    call("{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"process/reference_by_name\","
         "\"params\":{\"name\":\"notepad.exe\"}}\n");

    // 3. Run a one-shot enma script.
    call("{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"script/execute\","
         "\"params\":{\"source\":\"fn main() { println(\\\"hello from mcp\\\"); }\"}}\n");

    closesocket(s);
    WSACleanup();
    return 0;
}
```

Plain line-delimited JSON-RPC — the server's auto-detect routes us to that framing because we don't open with `POST` / `GET`. For the HTTP path, wrap each request in `POST /mcp HTTP/1.1\r\nContent-Length: N\r\n\r\n<body>` — that's what Claude Code does for you.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/mcp-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/net-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/net-api.md).

# Net API

All net natives are auto-registered into every loaded script.

All network calls are gated by the `network_access` permission. Without it, calls return a transport-failure value (`status=0` / null handle / empty array).

## HTTP — sync, with timeout

```cpp
http_response_t http_get (string url, int64 timeout_ms);
http_response_t http_get (string url, map<string, string> headers, int64 timeout_ms);

http_response_t http_post(string url, string content_type, string body, int64 timeout_ms);
http_response_t http_post(string url, string content_type, string body,
                          map<string, string> headers, int64 timeout_ms);
```

Both always return a non-null `http_response_t`. Read via methods:

```cpp
int64  response.status();    // 0 on transport failure / permission denied
string response.body();
bool   response.ok();        // true if status is 200..299
```

`content_type` may be empty for `http_post`. The 3-arg `http_get` / 5-arg `http_post` overloads take a `map<string, string>` of extra request headers — useful for `Authorization: Bearer ...`, `X-API-Key`, `Accept`, custom protocol headers, etc. Pass `null` or an empty map to skip.

### Headers example

```cpp
map<string, string> headers;
headers.set("Authorization", "Bearer " + g_token);
headers.set("Accept", "application/json");

http_response_t r = http_get("https://api.example.com/me", headers, 5000);
if (r.ok()) println(r.body());
```

```cpp
map<string, string> headers;
headers.set("X-API-Key", "abc123");

http_response_t r = http_post(
    "https://api.example.com/events",
    "application/json",
    "{\"event\":\"login\"}",
    headers,
    5000);
```

## WebSocket

```cpp
ws_t ws_connect(string url, int64 timeout_ms);
```

Connects to `ws://`, `wss://` (also `http://` / `https://` accepted). Spawns a background recv thread. Returns a null handle on failure or permission denied.

### `ws_t` methods

```cpp
bool         ws.is_open();
bool         ws.send_text  (string msg);
bool         ws.send_binary(array<uint8> data);

ws_message_t ws.recv();      // blocks until a message arrives or the connection closes
ws_message_t ws.poll();      // non-blocking

void         ws.close(int64 code);    // standard WS close codes (1000 = normal)
```

### `ws_message_t` methods

```cpp
bool   msg.ok();          // true if a message was returned
bool   msg.is_text();     // payload framing
bool   msg.is_closed();   // peer / local close has fired
string msg.payload();
```

## UDP — raw datagrams

```cpp
udp_t udp_create();
```

Creates a fresh UDP socket. Returns a null handle on failure / permission denied. Send-only sockets can skip `bind()`; sockets that receive must `bind()` to a local port first.

### `udp_t` methods

```cpp
bool         udp.bind(string addr, int64 port);                      // "0.0.0.0" / port — port 0 = OS-picked
bool         udp.send_to(array<uint8> data, string addr, int64 port);
array<uint8> udp.recv(int64 timeout_ms);                             // blocking with timeout; empty on timeout/error

string       udp.last_sender_addr();    // IP of the most recent successful recv()
int64        udp.last_sender_port();    // port of the most recent successful recv()

void         udp.close();
```

`recv` returns up to one full UDP datagram (max 65535 bytes). Timeout is in milliseconds — `timeout_ms = 0` means block indefinitely. After a successful `recv`, `last_sender_addr()` / `last_sender_port()` give you the peer to reply to.

### UDP example — Source Query Protocol (A2S\_INFO)

```cpp
udp_t s = udp_create();
if (cast<int64>(s) == 0) return 0;

// A2S_INFO request: FF FF FF FF 54 "Source Engine Query" 00
array<uint8> q;
q.push(0xFF); q.push(0xFF); q.push(0xFF); q.push(0xFF); q.push(0x54);
string banner = "Source Engine Query";
for (int32 ch : banner) q.push(cast<uint8>(ch));
q.push(0x00);

if (!s.send_to(q, "1.2.3.4", 27015)) {
    println("send failed");
    return 0;
}

array<uint8> reply = s.recv(2000);  // 2-second timeout
if (reply.length() == 0) {
    println("no reply (timeout)");
} else {
    println(format("got {d} bytes from {s}:{d}",
        reply.length(), s.last_sender_addr(), s.last_sender_port()));
}
```

### UDP example — listener

```cpp
udp_t s = udp_create();
s.bind("0.0.0.0", 9999);

for (int32 i = 0; i < 10; i = i + 1) {
    array<uint8> pkt = s.recv(1000);
    if (pkt.length() == 0) continue;
    println(format("from {s}:{d} ({d} bytes)",
        s.last_sender_addr(), s.last_sender_port(), pkt.length()));
}
```

## HTTP example

```cpp
http_response_t r = http_get("https://api.example.com/status", 5000);
if (r.ok()) {
    println("got: " + r.body());
} else if (r.status() == 0) {
    println("transport failed or permission denied");
} else {
    println("server returned " + cast<string>(r.status()));
}
```

## WebSocket example

```cpp
ws_t ws = ws_connect("wss://echo.example.com/", 5000);
if (cast<int64>(ws) == 0) return 0;

ws.send_text("hello");
ws_message_t m = ws.recv();
if (m.ok()) {
    println("got: " + m.payload());
}
ws.close(1000);
```

## Permission

`network_access` gates every native in this file (HTTP, WebSocket, UDP). When off, every call returns a transport-failure value.

## Lifetime

`ws_t` and `udp_t` close + free via the destructor at scope exit. If the script forgets, the host sweeps remaining sockets at unload — connections closed, threads joined, no permanent leak. UDP packets in flight are not buffered host-side; once you close, anything still on the wire is dropped by the OS.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/net-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/proc-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/proc-api.md).

# Proc API

All proc natives are auto-registered into every loaded script.

`proc_t` is a value-type handle. Construct it via `ref_process(...)`; the host ref is released automatically when the variable goes out of scope.

Some natives are gated by permission flags toggled host-side. Gated calls log and return 0 / false when blocked. See [Permissions](#permissions).

**Address type:** all addresses are `uint64`. Pick `uint64` for any locals that hold an address — `uint64 base = p.base_address();` — and the rest of the chain stays cast-free. Mixing `int64` addresses requires `cast<uint64>(...)`.

## `proc_t`

```cpp
proc_t ref_process(uint32 pid);
proc_t ref_process(string name);
```

Returns an alive handle on success, a null one on failure. Verify with `.alive()`.

## Identity

```cpp
uint64 proc.base_address();
uint64 proc.peb();
uint32 proc.pid();
bool   proc.alive();
bool   proc.is_valid_address(uint64 addr);
uint64 proc.get_eprocess();   // gated: kernel_rw_access — see below
```

`get_eprocess` returns the target's EPROCESS kernel address. Gated behind the `kernel_rw_access` permission — returns `0` and logs when the script doesn't hold it. Use cases: passing the EPROCESS to a custom kernel routine, walking kernel structures the proc API doesn't already expose, etc.

## Read primitives

```cpp
uint8/16/32/64 proc.ru8/ru16/ru32/ru64(uint64 addr);
int8/16/32/64  proc.r8/r16/r32/r64  (uint64 addr);
float32 proc.rf32(uint64 addr);
float64 proc.rf64(uint64 addr);

string proc.rs (uint64 addr, int32 max_chars);   // null-terminated UTF-8, cap 8192
string proc.rws(uint64 addr, int32 max_chars);   // UTF-16, returns UTF-8, cap 8192
```

All return 0 / empty on failure or out-of-range address. By default, addresses must be usermode. When the script holds `kernel_rw_access`, *safe* kernel addresses are also accepted — see [Permissions](#permissions).

## Write primitives (gated: `write_memory`)

```cpp
bool proc.wu8/wu16/wu32/wu64(uint64 addr, uintN v);
bool proc.w8/w16/w32/w64    (uint64 addr, intN  v);
bool proc.wf32(uint64 addr, float32 v);
bool proc.wf64(uint64 addr, float64 v);
bool proc.ws (uint64 addr, string text);    // UTF-8 bytes
bool proc.wws(uint64 addr, string text);    // converts UTF-8 to UTF-16
```

## Bulk read/write

```cpp
array<uint8> proc.rvm(uint64 addr, uint64 size);             // length = bytes actually read
bool         proc.wvm(uint64 addr, array<uint8> bytes);      // gated: write_memory
```

## Typed reads / writes (vec / quat / mat)

Read a `vec2`/`vec3`/`vec4`/`quat`/`mat4` directly from process memory. `_fl32` reads source bytes as float32 (promoted to float64 in the result); `_fl64` reads source bytes as float64. `mat4` is a row-major 4x4. `quat` is `x, y, z, w` packed.

```cpp
vec2 proc.read_vec2_fl32(uint64 addr);
vec2 proc.read_vec2_fl64(uint64 addr);
vec3 proc.read_vec3_fl32(uint64 addr);
vec3 proc.read_vec3_fl64(uint64 addr);
vec4 proc.read_vec4_fl32(uint64 addr);
vec4 proc.read_vec4_fl64(uint64 addr);
quat proc.read_quat_fl32(uint64 addr);
quat proc.read_quat_fl64(uint64 addr);
mat4 proc.read_mat4_fl32(uint64 addr);
mat4 proc.read_mat4_fl64(uint64 addr);
```

Writes mirror the reads (gated: `write_memory`):

```cpp
bool proc.write_vec2_fl32(uint64 addr, vec2 v);
bool proc.write_vec2_fl64(uint64 addr, vec2 v);
bool proc.write_vec3_fl32(uint64 addr, vec3 v);
bool proc.write_vec3_fl64(uint64 addr, vec3 v);
bool proc.write_vec4_fl32(uint64 addr, vec4 v);
bool proc.write_vec4_fl64(uint64 addr, vec4 v);
bool proc.write_quat_fl32(uint64 addr, quat q);
bool proc.write_quat_fl64(uint64 addr, quat q);
bool proc.write_mat4_fl32(uint64 addr, mat4 m);
bool proc.write_mat4_fl64(uint64 addr, mat4 m);
```

Reads return the value directly:

```cpp
proc_t p = ref_process("game.exe");
vec3 cam_pos = p.read_vec3_fl32(p.base_address() + 0x10A4830);
println("camera at " + cast<string>(cam_pos.x) + "," + cast<string>(cam_pos.y));
```

Failed reads (bad address, kernel-RW gate denial, dead proc handle) return a zero-initialized value of the right type — chained `.x` / `.m[i]` stays safe instead of AVing through null. Writes return `false` on the same failure cases.

Same kernel-RW gate semantics as the rest of the proc API — see [Permissions](#permissions).

## SIMD-width reads/writes

```cpp
array<uint8> proc.r128(uint64 addr);    // 16 bytes
array<uint8> proc.r256(uint64 addr);    // 32 bytes
array<uint8> proc.r512(uint64 addr);    // 64 bytes

bool proc.w128(uint64 addr, array<uint8> bytes);   // gated: write_memory
bool proc.w256(uint64 addr, array<uint8> bytes);   // gated: write_memory
bool proc.w512(uint64 addr, array<uint8> bytes);   // gated: write_memory
```

## Modules and exports

```cpp
uint64                proc.get_module_base(string name);     // 0 if missing
uint64                proc.get_module_size(string name);     // 0 if missing
array<module_info_t>  proc.get_module_list();                // every loaded module
uint64                proc.get_proc_address(uint64 module_base, string export_name);
uint64                proc.get_import_rdata_address(uint64 module_base, string import_name);
```

`module_info_t` methods:

```cpp
string m.name();    // base DLL filename, e.g. "kernel32.dll"
uint64 m.base();    // DllBase
uint64 m.size();    // SizeOfImage
```

Example — list every module loaded in the target:

```cpp
array<module_info_t> mods = p.get_module_list();
for (module_info_t m : mods) {
    println(format("{s}  base=0x{x}  size=0x{x}", m.name(), m.base(), m.size()));
}
```

## Pattern scanning

```cpp
uint64        proc.find_code_pattern    (uint64 search_start, uint64 search_size, string sig);
array<uint64> proc.find_all_code_patterns(uint64 search_start, uint64 search_size, string sig);
```

Sig syntax: hex bytes separated by spaces, `??` is a wildcard. Example: `"48 8B ?? ?? 48 89"`.

## Threads

```cpp
array<uint64> proc.get_all_tebs();
```

## Pointer arrays

```cpp
array<uint64> proc.read_pointer_array(uint64 base, int64 count, int64 offset_delta);
```

Reads `count` consecutive `uint64`s starting at `base`. `offset_delta` is added to each value before storing (useful when the target stores relative offsets).

## VAD / virtual\_query

Both calls **exclude PE-image regions** (modules, exes). Use `get_module_base/size` for those.

```cpp
vad_region_t        proc.virtual_query(uint64 address);
array<vad_region_t> proc.get_vad_snapshot(bool heap_likely_only);
```

`virtual_query` returns a `vad_region_t` handle on hit, `0` on miss.

### `vad_region_t`

```cpp
uint64 region.start();
uint64 region.size();
uint64 region.protection();   // host page-protection bits (PAGE_READWRITE, PAGE_EXECUTE, etc.)
bool   region.heap_likely();  // host's heuristic for heap allocations
```

```cpp
array<vad_region_t> snap = p.get_vad_snapshot(false);
for (int64 i = 0; i < snap.length(); i = i + 1) {
    vad_region_t r = snap.get(i);
    uint64 start = r.start();
    uint64 size  = r.size();
    uint64 prot  = r.protection();
    bool   heap  = r.heap_likely();
}
```

## Memory scans

All scans walk the VAD snapshot (so module memory is excluded — same caveat as above). `heap_only=true` restricts to heap-likely regions.

```cpp
array<uint64> proc.scan_string (string text,    bool heap_only);
array<uint64> proc.scan_wstring(string text,    bool heap_only);   // text is UTF-8, converted to UTF-16
array<uint64> proc.scan_pointer(uint64 target,  bool heap_only);
array<uint64> proc.scan_u64    (uint64 value,   bool heap_only);
array<uint64> proc.scan_u32    (uint32 value,   bool heap_only);
array<uint64> proc.scan_float  (float32 value,  bool heap_only);
array<uint64> proc.scan_double (float64 value,  bool heap_only);
```

## VM alloc / free (gated: `virtual_memory_operations`)

```cpp
uint64 proc.alloc_vm(uint64 size);   // 0 on failure
bool   proc.free_vm (uint64 address);
```

Allocation itself is safe. To execute code from the returned page, the target must have Control Flow Guard (CFG) disabled — CFG kills the process on indirect calls/jumps to non-bitmap addresses. Reads + writes are unaffected.

## Permissions

Three flags gate sensitive operations. All default to off; the user grants them per script via the host UI.

| Flag                        | Gates                                                                                 |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `write_memory`              | `wu*`, `w*`, `wf*`, `ws`, `wws`, `wvm`, `w128/256/512`                                |
| `virtual_memory_operations` | `alloc_vm`, `free_vm`                                                                 |
| `kernel_rw_access`          | `get_eprocess`; expands every other read/write to also accept *safe* kernel addresses |

When a gated call runs without permission it logs `[ENMA] ... blocked: '<flag>' permission not granted` and returns 0 / false.

### `kernel_rw_access` semantics

Without it, every read/write address must pass `is_usermode_address` — i.e. canonical user-range, non-null, non-tiny. This is the default and matches the original behavior.

With it, addresses are accepted when **either**:

* The address is a valid usermode address (same check as before), **or**
* The address is a *safe kernel address* — canonical kernel range AND not in any host-protected critical region (the host's own EPROCESS / ETHREAD / kernel state used for privilege escalation).

The "safe kernel" denylist is enforced by `is_safe_kernel_address` in the host. Scripts can't bypass it: a kernel write to a denied address returns `false` and logs, just like any other refused op.

Use this flag when a script genuinely needs to inspect or modify kernel structures of the target process (Win32 thread state, KPCR fields, driver-side game state, etc.). Don't grant it casually — kernel writes to the wrong address bugcheck the box.

## Lifetime and cleanup

`proc_t` releases its host ref via the destructor when the variable goes out of scope. If a script forgets (e.g. leaks a `proc_t*` heap-allocation), the host sweeps remaining refs at script unload — no permanent leak.

```cpp
int64 main() {
    proc_t p = ref_process("notepad.exe");
    if (!p.alive()) return 0;

    uint64 base = p.base_address();
    println(cast<string>(p.r32(base + 0x3C)));    // e_lfanew

    return 0;
    // p drops here; host ref released
}
```

## Conventions

* **Addresses are `uint64`.** Use `uint64` for any local that holds an address — hex literals like `0x7FF000000000` work directly. Mixing in an `int64` requires `cast<uint64>(...)`.
* **Failed reads return 0**, not an exception. Check `is_valid_address` first if you need certainty.
* **Strings returned by `rs`/`rws`** are heap strings — drop normally at scope exit.
* **Array returns are length-correct.** `arr.length()` is the actual element count, not a max.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/proc-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/readme.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/readme.md).

# Enma - Overview

Enma is perception's proprietary full-module AOT and JIT-compiled scripting language. This site covers the APIs perception registers on top of Enma. For the language itself see [enma docs](https://enma-1.gitbook.io/enma).

## What's registered

#### Enma Pre-Shipped

* [Core](https://enma-1.gitbook.io/enma/addons/core)
* [String](https://enma-1.gitbook.io/enma/addons/strings)
* [Arrays](https://enma-1.gitbook.io/enma/addons/arrays)
* [Maps](https://enma-1.gitbook.io/enma/addons/maps)
* [Math](https://enma-1.gitbook.io/enma/addons/math)
* [3D Math (quat + mat4)](https://enma-1.gitbook.io/enma/addons/math3d)
* [SIMD](https://enma-1.gitbook.io/enma/addons/simd)
* [Variant](https://enma-1.gitbook.io/enma/addons/variant)
* [Atomic](https://enma-1.gitbook.io/enma/addons/atomic)
* [Bits](https://enma-1.gitbook.io/enma/addons/bits)
* [Time](https://enma-1.gitbook.io/enma/addons/time)
* [Regex](https://enma-1.gitbook.io/enma/addons/regex)
* [Thread](https://enma-1.gitbook.io/enma/addons/thread)
* [Vectors](https://enma-1.gitbook.io/enma/addons/vec)
* [Hash Set](https://enma-1.gitbook.io/enma/addons/hash_set)
* [Sorted Map](https://enma-1.gitbook.io/enma/addons/sorted_map)
* [List](https://enma-1.gitbook.io/enma/addons/list)
* [JSON](https://enma-1.gitbook.io/enma/addons/json)

#### **Perception API**

* [Lifecycle and Routines](lifecycle-and-routines.md)
* [Render](render-api.md)
* [Proc](proc-api.md)
* [CPU](cpu-api.md)
* [Filesystem](filesystem-api.md)
* [Sound](sound-api.md)
* [Zydis](zydis-api.md)
* [Win](win-api.md)
* [Input](input-api.md)
* [Unicorn](unicorn-api.md)
* [Net](net-api.md)
* [GUI](gui-api.md)

#### AI agent surface

* [MCP](mcp-api.md) — JSON-RPC over local TCP / HTTP for Claude Code, Cline, etc.

## Minimal example

```cpp
int64 g_tick;

void my_draw(int64 data) {
    g_tick = g_tick + 1;
    color white = color(255, 255, 255, 255);
    color noeffect = color(0, 0, 0, 0);

    string text = "tick=" + cast<string>(g_tick);
    draw_text(text, vec2(40.0, 40.0), white, get_font20(), 0, noeffect, 0.0);
}

int64 main() {
    g_tick = 0;
    register_routine(cast<int64>(my_draw), 0);
    return 1;
}
```

See [Lifecycle and Routines](lifecycle-and-routines.md) for the entry point, return-value semantics, and how routines tick.

## Conventions

* **Colors and positions**: always wrap. `color(255, 255, 255, 255)`, `vec2(10.0, 20.0)`. Freshly constructed each frame is fine; Enma drops the temporaries at scope exit.
* **Float32 literals**: `0.2f`, not `cast<float32>(0.2)`. Required for vertex buffers.
* **Handles**: all `create_*` / `load_*` natives return an encrypted `int64`. Pass it back into draw / bind / destroy. Don't inspect.

## SDK

Perception's Enma SDK is not public yet.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/readme.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/render-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/render-api.md).

# Render API

All render natives are auto-registered into every loaded script.

Handles (`int64`) are encrypted pointers. Pass them back into other render calls. Don't dereference or arithmetic them.

## `color` type

`color` is a source-level module. Opt in with `import "color";`:

```enma
import "vec";
import "color";

int64 main() {
    color red = color(255, 0, 0, 255);
    draw_rect_filled(vec2(10.0, 10.0), vec2(100.0, 50.0), red, 4.0, 15);
    return 0;
}
```

`color` is a `[[packed]]` 4-byte struct with `r` / `g` / `b` / `a` fields plus `with_alpha(uint8 _a)` to copy with a different alpha. Non-escaping locals are stack-allocated; the byte layout matches the native `pixelcolor4` so every `draw_*` call reads them directly.

Read fields directly: `c.r`, `c.g`, `c.b`, `c.a` (each returns `uint8`).

## 2D primitives

```cpp
int64 draw_rect(vec2 pos, vec2 size, color c, float64 thickness, float64 rounding, uint8 rounding_flags);
int64 draw_rect_filled(vec2 pos, vec2 size, color c, float64 rounding, uint8 rounding_flags);
int64 draw_line(vec2 a, vec2 b, color c, float64 thickness);
int64 draw_circle(vec2 center, float64 radius, color c, float64 thickness, bool filled);
int64 draw_arc(vec2 center, vec2 radii, float64 start_deg, float64 sweep_deg, color c, float64 thickness, bool filled);
int64 draw_triangle(vec2 a, vec2 b, vec2 c, color col, float64 thickness, bool filled);
int64 draw_four_corner_gradient(vec2 pos, vec2 size, color tl, color tr, color bl, color br, float64 rounding);
int64 draw_polygon(array xy_pairs, uint32 count_pairs, color c, float64 thickness, bool filled);
int64 draw_bitmap(int64 bmp, vec2 pos, vec2 size, color tint, bool rounded);
int64 draw_text(string text, vec2 pos, color c, int64 font, int32 effect, color effect_color, float64 effect_amount);
```

`effect`: 0=none, 1=shadow, 2=outline. `rounding_flags`: bitmask of which corners to round (ImGui-style, `15` = all corners).

## Text and fonts

```cpp
float64 get_text_width(int64 font, string text, int32 maxw, int32 maxh);
float64 get_text_height(int64 font, string text, int32 maxw, int32 maxh);
int32   get_char_advance(int64 font, uint32 wchar32);

int64 create_font(string path, float64 size, bool antialias, bool load_color, array glyph_ranges);
int64 create_font_mem(string label, float64 size, array buf, bool antialias, bool load_color, array glyph_ranges);
int64 create_bitmap(array data);

int64 get_font18();
int64 get_font20();
int64 get_font24();
int64 get_font28();
```

`create_font` first tries the path as-is, then retries under perception's main dir. `glyph_ranges` may be an empty array.

## Clipping

```cpp
int64 clip_push(vec2 pos, vec2 size);
int64 clip_pop();
```

## Viewport

```cpp
float64 get_view_width();
float64 get_view_height();
float64 get_view_scale();
float64 get_fps();
```

## Shaders

```cpp
int64 create_shader(string vs_source, string ps_source, string layout);
int64 destroy_shader(int64 shader);
int64 create_compute_shader(string cs_source);
int64 destroy_compute_shader(int64 cs);
```

Layout format: `"SEMANTIC:INDEX:TYPE, ..."`. Example: `"POSITION:0:FLOAT2, COLOR:0:FLOAT4"`. Types: `FLOAT1`, `FLOAT2`, `FLOAT3`, `FLOAT4`, `BYTE4` (unorm), `UINT1`.

## Buffers

```cpp
int64 create_vertex_buffer(uint32 stride, uint32 max_vertices, bool dynamic);
int64 destroy_vertex_buffer(int64 vb);
int64 create_index_buffer(uint32 max_indices, bool use_32bit, bool dynamic);
int64 destroy_index_buffer(int64 ib);
int64 create_constant_buffer(uint32 size);
int64 destroy_constant_buffer(int64 cb);
int64 create_structured_buffer(uint32 element_size, uint32 element_count, bool cpu_write, bool gpu_write);
int64 destroy_structured_buffer(int64 sb);
```

## Pipeline state

```cpp
int64 create_blend_state(int32 src, int32 dst, int32 op, int32 src_alpha, int32 dst_alpha, int32 op_alpha);
int64 destroy_blend_state(int64 bs);
int64 create_sampler(int32 filter, int32 address_u, int32 address_v);
int64 destroy_sampler(int64 s);
int64 create_depth_stencil_state(bool depth_enable, bool depth_write, int32 compare_func);
int64 destroy_depth_stencil_state(int64 ds);
int64 create_rasterizer_state(int32 cull_mode, int32 fill_mode, bool scissor_enable);
int64 destroy_rasterizer_state(int64 rs);
```

Enum values (all `int32`):

* `blend_factor`: 0=ZERO, 1=ONE, 2=SRC\_ALPHA, 3=INV\_SRC\_ALPHA, 4=DEST\_ALPHA, 5=INV\_DEST\_ALPHA, 6=SRC\_COLOR, 7=INV\_SRC\_COLOR, 8=DEST\_COLOR, 9=INV\_DEST\_COLOR.
* `blend_op`: 0=ADD, 1=SUBTRACT, 2=REV\_SUBTRACT, 3=MIN, 4=MAX.
* `filter`: 0=POINT, 1=LINEAR, 2=ANISOTROPIC.
* `address`: 0=WRAP, 1=CLAMP, 2=MIRROR, 3=BORDER.
* `compare_func`: 0=NEVER, 1=LESS, 2=EQUAL, 3=LESS\_EQUAL, 4=GREATER, 5=NOT\_EQUAL, 6=GREATER\_EQUAL, 7=ALWAYS.

## Render targets and textures

```cpp
int64 create_render_target(uint32 width, uint32 height);
int64 destroy_render_target(int64 rt);
int64 create_depth_buffer(uint32 width, uint32 height);
int64 destroy_depth_buffer(int64 db);
int64 create_texture(uint32 width, uint32 height, array rgba_data);
int64 destroy_texture(int64 tex);
int64 load_texture(string path);
int64 load_texture_mem(array data);
float64 get_texture_width(int64 tex);
float64 get_texture_height(int64 tex);
```

`create_texture` wants `width * height * 4` bytes of RGBA.

## Meshes

```cpp
int64 create_mesh_raw(array vertex_data, uint32 vertex_count, uint32 stride, array index_data, uint32 index_count, bool use_32bit);
int64 load_mesh(string path);
int64 load_mesh_mem(array data);
int64 destroy_mesh(int64 mesh);
int64 get_mesh_vert_count(int64 mesh);
int64 get_mesh_index_count(int64 mesh);
float64 get_mesh_stride(int64 mesh);
float64 get_mesh_bounds_min_x(int64 mesh);
float64 get_mesh_bounds_min_y(int64 mesh);
float64 get_mesh_bounds_min_z(int64 mesh);
float64 get_mesh_bounds_max_x(int64 mesh);
float64 get_mesh_bounds_max_y(int64 mesh);
float64 get_mesh_bounds_max_z(int64 mesh);
```

## Custom draw

```cpp
int64 custom_draw(int64 shader, int64 vb, array vertex_data, uint32 vertex_count, int32 topology,
                  int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                  int64 cb, array cb_data, int32 cb_slot);

int64 custom_draw_indexed(int64 shader, int64 vb, array vertex_data, uint32 vertex_count,
                          int64 ib, array index_data, uint32 index_count, int32 topology,
                          int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                          int64 cb, array cb_data, int32 cb_slot);

int64 draw_mesh(int64 mesh, int64 shader, int32 topology,
                int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                int64 cb, array cb_data, int32 cb_slot);

int64 dispatch_compute(int64 cs, uint32 x, uint32 y, uint32 z);
```

`topology`: 0=TRIANGLE\_LIST, 1=TRIANGLE\_STRIP, 2=LINE\_LIST, 3=LINE\_STRIP, 4=POINT\_LIST.

Any of `blend` / `sampler` / `texture` / `cb` can be `0` to skip binding. `cb_data` may be an empty array.

## Binding and state

```cpp
int64 custom_set_render_target(int64 rt);
int64 custom_set_render_target_ext(int64 rt, int64 depth_buffer);
int64 custom_reset_render_target();
int64 custom_bind_rt_as_texture(int64 rt, int32 slot);
int64 custom_restore_state();
int64 custom_set_depth_stencil_state(int64 ds);
int64 custom_set_rasterizer_state(int64 rs);
int64 custom_set_viewport(float64 x, float64 y, float64 w, float64 h);
int64 custom_reset_viewport();
int64 custom_bind_texture(int64 texture, int64 sampler, int32 slot);
int64 custom_bind_constant_buffer(int64 cb, array data, int32 slot, int32 stage);
int64 custom_update_texture(int64 tex, uint32 x, uint32 y, uint32 w, uint32 h, array rgba_data);
int64 custom_clear_render_target(int64 rt, float64 r, float64 g, float64 b, float64 a);
int64 custom_clear_depth_buffer(int64 db);
int64 bind_structured_buffer(int64 sb, int32 slot, int32 stage);
int64 update_structured_buffer(int64 sb, array data);
int64 capture_backbuffer(int32 slot);
```

`stage`: 0=VS, 1=PS, 2=CS (matches D3D11 shader stages).

Call `custom_restore_state()` after any custom-pipeline sequence before returning control to the 2D layer.

## Minimal triangle

```cpp
int64 g_shader;
int64 g_vb;

int64 main() {
    string vs = "struct VSIn { float2 pos : POSITION; float4 color : COLOR; };\nstruct VSOut { float4 pos : SV_Position; float4 color : COLOR; };\nVSOut main(VSIn i) { VSOut o; o.pos = float4(i.pos, 0.0, 1.0); o.color = i.color; return o; }\n";
    string ps = "struct VSOut { float4 pos : SV_Position; float4 color : COLOR; };\nfloat4 main(VSOut i) : SV_Target { return i.color; }\n";

    g_shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    g_vb = create_vertex_buffer(24, 3, true);  // 2*4 + 4*4 = 24 bytes per vertex
    register_routine(cast<int64>(my_draw), 0);
    return 1;
}

void my_draw(int64 data) {
    float32[] verts;
    // vertex 0: pos(-0.5, -0.5) color(1, 0, 0, 1)
    verts.push(-0.5f); verts.push(-0.5f);
    verts.push(1.0f);  verts.push(0.0f); verts.push(0.0f); verts.push(1.0f);
    // vertex 1: pos(0.5, -0.5) color(0, 1, 0, 1)
    verts.push(0.5f);  verts.push(-0.5f);
    verts.push(0.0f);  verts.push(1.0f); verts.push(0.0f); verts.push(1.0f);
    // vertex 2: pos(0, 0.5) color(0, 0, 1, 1)
    verts.push(0.0f);  verts.push(0.5f);
    verts.push(0.0f);  verts.push(0.0f); verts.push(1.0f); verts.push(1.0f);

    float32[] no_cb;
    custom_draw(g_shader, g_vb, verts, 3, 0, 0, 0, 0, 0, 0, no_cb, 0);
}
```

## Cleanup

On script unload, every handle returned by `create_*` / `load_*` is destroyed automatically. Explicit `destroy_*` is optional and only needed if you want to free a resource mid-script.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/render-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/sound-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/sound-api.md).

# Sound API

All sound natives are auto-registered into every loaded script.

Two handle types:

* `sound_t` — a loaded resource. Multiple instances can play from one resource concurrently.
* `sound_inst_t` — a live playback instance. Returned by `sound.play(...)`.

Both are `int64`-backed handles with auto-cleanup destructors. Resources are tracked per-script; an unload sweep frees anything the user forgot to drop.

## Load / unload

```cpp
sound_t load_sound(string relative_path);
```

Loads `<my_games>/<relative_path>`. Path is validated:

* No `..` segments.
* No `:` (drive letters), `\n`, `\r`.
* Cannot start with `/` or `\` (must be relative).

Returns a null handle on validation failure or read failure. The destructor frees the resource.

## Playback

```cpp
sound_inst_t sound.play(float64 volume, float64 pan, bool loop);
```

* `volume`: 0.0 .. 1.0 (clamped)
* `pan`: -1.0 (full left) .. 1.0 (full right) (clamped)
* `loop`: repeat forever until stopped

## Instance control

```cpp
bool sound_inst.is_playing();
void sound_inst.stop();
void sound_inst.set_volume(float64 v);    // 0..1
void sound_inst.set_pan(float64 p);       // -1..1
```

## Globals

```cpp
void stop_all_sounds();    // halts every instance globally
```

## Example

```cpp
int64 main() {
    sound_t snd = load_sound("sounds/notification.wav");
    if (cast<int64>(snd) == 0) return 0;

    sound_inst_t inst = snd.play(0.5, 0.0, false);
    while (inst.is_playing()) sleep_ms(50);

    return 1;
    // snd / inst drop here; resource + instance freed
}
```

## Lifetime

`sound_t` and `sound_inst_t` both release at scope exit. If the script forgets, the host sweeps remaining handles at unload. No permanent leak.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/sound-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/unicorn-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/unicorn-api.md).

# Unicorn API

All unicorn natives are auto-registered into every loaded script.

`cpu_t` is the emulator handle. RAII destructor closes the engine + frees user hooks. Standalone or process-bound (process-bound: unmapped reads pull from `proc.rvm`, writes go to `proc.wvm`).

## Constants — exposed as enums (no header import needed)

```cpp
uc_reg::rax / rbx / rcx / rdx / rsi / rdi / rbp / rsp
uc_reg::r8 .. r15
uc_reg::rip / eflags
uc_reg::cs / ds / es / fs / gs / ss
uc_reg::fs_base / gs_base / mxcsr
uc_reg::xmm0 .. xmm15
uc_reg::ymm0 .. ymm15

uc_prot::none / read / write / exec / rw / rx / rwx / all

uc_hook::code            // fires per instruction
uc_hook::mem_unmapped    // fires on read/write/fetch to unmapped page
```

## Construction

```cpp
cpu_t cpu_create();
cpu_t cpu_create_process(proc_t proc, bool allow_writes);
```

* `cpu_create` — standalone emulator, no process backing.
* `cpu_create_process` — unmapped reads pull pages from `proc.rvm`; writes go to `proc.wvm` if `allow_writes=true`. Auto-installs read/write/fetch/unmapped hooks plus invalid-instruction + interrupt handlers.

The destructor closes the engine and frees any user hooks.

## Memory

```cpp
bool         cpu.mem_map  (int64 addr, int64 size, uc_prot perms);
bool         cpu.mem_write(int64 addr, array<uint8> bytes);
array<uint8> cpu.mem_read (int64 addr, int64 size);                  // empty array on read failure
```

`addr` and `size` should be page-aligned. `mem_map` returns true on success or already-mapped. `perms` accepts `uc_prot::*` values OR'd together.

## Registers

```cpp
bool  cpu.reg_write64(uc_reg reg, int64 value);
int64 cpu.reg_read64 (uc_reg reg);

bool         cpu.reg_write128(uc_reg reg, array<uint8> bytes);    // XMM, must be exactly 16 bytes
array<uint8> cpu.reg_read128 (uc_reg reg);

bool         cpu.reg_write256(uc_reg reg, array<uint8> bytes);    // YMM, must be exactly 32 bytes
array<uint8> cpu.reg_read256 (uc_reg reg);
```

## Execution

```cpp
int64 cpu.start(int64 begin, int64 end, int64 timeout, int64 count);
```

Emulates from `begin` to `end`. `timeout=0` and `count=0` are unbounded. Returns a `uc_err` code (0 = OK).

```cpp
void cpu.emu_stop();         // halt emulation from inside a hook
bool cpu.flush_code();       // drop translation cache (after self-modifying writes)
bool cpu.setup_stack(int64 base, int64 size, int64 stop_addr);
```

`setup_stack` maps stack pages, plants a NOP page at `stop_addr` (so a `RET` out lands somewhere mapped), and sets `RSP`.

## Hooks (script callbacks)

```cpp
bool cpu.hook_add(uc_hook hook_kind, int64 fn_handle);
```

* `fn_handle` = `cast<int64>(my_callback)` closure handle.
* Callback shape: `int64 cb(int64 addr)`. **Return 0 to stop emulation; non-zero to continue.**

The currently-emulating CPU is available as `cpu_active()` from inside the callback — useful for reading/writing state without capturing the handle.

```cpp
cpu_t cpu_active();    // null outside a hook
```

## Exception inspection

```cpp
int64 cpu.get_last_exception();      // NTSTATUS-shaped: 0 = none, 0xC000001D = invalid insn, 0xC0000005 = AV
int64 cpu.get_exception_address();   // RIP at the faulting instruction
```

Set when emulation stops due to invalid instruction, AV-style unmapped access, or interrupt.

## Example: emulate `mov rax, 0x42; hlt`

```cpp
cpu_t cpu = cpu_create();
cpu.mem_map(0x10000, 0x1000, uc_prot::rwx);
cpu.mem_map(0x20000, 0x1000, uc_prot::rw);

// Build code: mov rax, 0x42 + hlt (0xF4)
zydis_req_t r;
r.set_mnemonic(zydis_mnemonic_from_string("mov"));
r.set_operand_count(2);
r.set_operand_reg(0, zydis_register_from_string("rax"));
r.set_operand_imm(1, 0x42);
array<uint8> code = zydis_encode(r);
code.push(cast<uint8>(0xF4));

cpu.mem_write(0x10000, code);
cpu.reg_write64(uc_reg::rsp, 0x21000 - 8);

cpu.start(0x10000, 0x10000 + code.length(), 1000000, 0);
println(cast<string>(cpu.reg_read64(uc_reg::rax)));    // "66"  (= 0x42)
```

## Lifetime

`cpu_t` releases its host resources via the destructor at scope exit. If a script forgets, the host sweeps remaining cpus at unload — engine closed, hooks freed, no permanent leak.

## Notes

* Hook callbacks fire on the emulating thread (whichever thread called `cpu.start`). Enma's TLS is already set up in that context — heap-alloc, string concat etc. all work.
* `cpu_create_process` automatically maps a fake TEB at `0x101000` and a fake / real PEB so guest code reading FS/GS doesn't fault. `gs_base` and `fs_base` are set to the fake TEB.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/unicorn-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/win-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/win-api.md).

# Win API

All win natives are auto-registered into every loaded script.

This API **sends** input and reads window state. For state polling (mouse position, key down/up etc.), see [Input API](input-api.md).

`HWND` is exposed as raw `int64`. OS-owned; if the window disappears, subsequent calls reject via `IsWindow()`.

## `window_info_t`

Snapshot of a window at enumeration time. Heap-allocated; fields read via methods.

```cpp
int64  info.hwnd();
int64  info.pid();
int64  info.tid();
string info.process_name();    // exe basename
string info.title();           // window title at snapshot time
string info.class_name();
```

## Enumerate / find

```cpp
array<window_info_t> get_all_hwnds();
int64 find_window(string title);
int64 find_window(string title, string class_name);
```

`find_window` returns 0 when no match.

## Window queries

Geometry is split per axis (no array tuples). Combine pos + size for a rect.

```cpp
int64  get_window_width(int64 hwnd);                    // 0 on invalid hwnd
int64  get_window_height(int64 hwnd);                   // 0 on invalid hwnd
vec2   get_window_pos(int64 hwnd);                      // screen coords; (0,0) on invalid
vec2   get_window_size(int64 hwnd);                     // (width, height) as vec2
bool   is_foreground_window(int64 hwnd);
bool   is_window_active(int64 hwnd);                    // visible AND not minimized
string get_window_title(int64 hwnd);
string get_window_class(int64 hwnd);
bool   set_foreground_window(int64 hwnd);
int64  get_window_thread_id(int64 hwnd);                // 0 on invalid hwnd
int64  get_window_process_id(int64 hwnd);               // 0 on invalid hwnd
bool   post_message(int64 hwnd, int64 msg, int64 wparam, int64 lparam);
```

## Clipboard

```cpp
bool   copy_to_clipboard(string text);
string copy_from_clipboard();    // empty string when nothing or wrong format
```

`copy_to_clipboard` is gated by perception's restricted-string filter (returns false + logs when blocked).

## Keyboard SEND

Synthesized via `SendInput`. Restricted virtual keys (set host-side) are blocked + logged.

```cpp
void win_key_down (int64 vk);
void win_key_up   (int64 vk);
void win_key_press(int64 vk, int64 delay_ms);    // down + sleep + up; delay capped at 1000ms

bool send_char(int64 hwnd, string text);          // PostMessageW(WM_CHAR), first wide char only
bool send_key (int64 hwnd, int64 vk);             // PostMessageW(WM_KEYDOWN+WM_KEYUP) targeted at hwnd
```

## Mouse SEND

```cpp
void mouse_move         (int64 x, int64 y);          // absolute screen coords
void mouse_move_relative(int64 dx, int64 dy);
void mouse_left_click   ();                          // down + 10ms + up
void mouse_right_click  ();
void mouse_middle_click ();
void mouse_scroll       (int64 amount);              // multiples of WHEEL_DELTA
void send_mouse_input   (int64 dx, int64 dy, int64 flags, int64 mouse_data);   // raw SendInput
```

## Example: focus a window and click in it

```cpp
int64 hwnd = find_window("Notepad");
if (hwnd == 0) return 0;

set_foreground_window(hwnd);
sleep_ms(50);

vec2 pos = get_window_pos(hwnd);
vec2 sz  = get_window_size(hwnd);
mouse_move(pos.x() + sz.x() / 2.0, pos.y() + sz.y() / 2.0);
mouse_left_click();
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/win-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/zydis-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/zydis-api.md).

# Zydis API

All Zydis natives are auto-registered into every loaded script.

Two handle types:

* `zydis_req_t` — single-instruction encoder request (mnemonic + operands).
* `zydis_builder_t` — sequence of requests + raw byte chunks; encodes to a flat byte buffer with absolute addressing.

Constants are exposed as enums (`zydis_machine_mode::long_64` etc.) so no header import is needed.

## `zydis_req_t`

```cpp
zydis_req_t r;                                          // factory: defaults to MODE_LONG_64
r.set_mnemonic(int64 mnemonic);                         // ZydisMnemonic value (use zydis_mnemonic_from_string)
r.set_machine_mode(zydis_machine_mode mode);
r.set_operand_count(int64 count);                       // 0..4
r.set_branch_type (zydis_branch_type type);
r.set_branch_width(zydis_branch_width width);

r.set_operand_reg(int64 idx, int64 reg);                                              // ZydisRegister value
r.set_operand_imm(int64 idx, int64 imm);
r.set_operand_mem(int64 idx, int64 base, int64 idx_reg, int64 scale, int64 disp, int64 size);
r.set_operand_ptr(int64 idx, int64 segment, int64 offset);

int64              r.get_mnemonic();
zydis_machine_mode r.get_machine_mode();
int64              r.get_operand_count();
```

## Encoding

```cpp
array<uint8> zydis_encode         (zydis_req_t req);                       // empty array on failure
array<uint8> zydis_encode_absolute(zydis_req_t req, int64 runtime_rip);    // bakes RIP-relative immediates
array<uint8> zydis_nop_fill       (int64 length);                          // minimal NOP padding
zydis_req_t  zydis_decoded_to_request(array<uint8> bytes, int64 runtime_rip);
```

`zydis_decoded_to_request` decodes the bytes and returns a fresh request you can mutate and re-encode (useful for instruction patching).

## Mnemonic / register name lookup

```cpp
int64  zydis_mnemonic_from_string(string name);    // case-insensitive; 0 (INVALID) if no match
string zydis_mnemonic_to_string  (int64 mnemonic);

int64  zydis_register_from_string(string name);    // case-insensitive; 0 (NONE) if no match
string zydis_register_to_string  (int64 reg);
```

## Disassembly (textual)

```cpp
array<string> zydis_disasm(array<uint8> bytes, int64 runtime_rip);
```

One element per decoded instruction, formatted as Zydis's intel syntax (e.g. `"mov rax, 0x1234"`). Decoding stops at the first invalid byte.

For per-operand structure, decode + convert to a `zydis_req_t` via `zydis_decoded_to_request` and read the request fields.

## `zydis_builder_t`

Builds a sequence of instructions (and raw bytes) into one flat output buffer. Tracks a base address so RIP-relative encoding produces correct offsets.

```cpp
zydis_builder_t b;
b.set_machine_mode(zydis_machine_mode mode);
b.set_base_address(int64 addr);
b.clear();

b.push        (zydis_req_t req);
b.push_bytes  (array<uint8> bytes);
b.push_byte   (uint8 b);
b.push_u16    (uint16 v);    // little-endian
b.push_u32    (uint32 v);    // little-endian
b.push_u64    (uint64 v);    // little-endian
b.push_nop    (int64 count);
b.push_int3   ();
b.push_ret    ();

array<uint8> b.build();      // encode every entry in order
int64 b.get_count();         // number of entries
```

## Enums (no header needed)

```cpp
zydis_machine_mode::long_64 / long_compat_32 / long_compat_16 / legacy_32 / legacy_16 / real_16
zydis_branch_type::none / short / near / far
zydis_branch_width::none / w8 / w16 / w32 / w64
```

## Example: encode `mov rax, 0x42`, then disasm

```cpp
int64 mov_id = zydis_mnemonic_from_string("mov");
int64 rax_id = zydis_register_from_string("rax");

zydis_req_t r;
r.set_mnemonic(mov_id);
r.set_operand_count(2);
r.set_operand_reg(0, rax_id);
r.set_operand_imm(1, 0x42);

array<uint8> bytes  = zydis_encode(r);
array<string> texts = zydis_disasm(bytes, 0);

println(texts.get(0));    // "mov rax, 0x42"
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/zydis-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `.claude/skills/game-cheat-guidelines/SKILL.md`

---
name: game-cheat-guidelines
description: >
  Mandatory behavioral rules and practical patterns for writing Perception.cx
  game-cheat scripts in Enma, AngelScript, and C++. Always active — these
  rules apply every time you write or edit game-cheat code, including ESP,
  aimbot, triggerbot, radar, pattern scanning, and overlay rendering.
  Authorized use only — analyze software you own or are permitted to test.
license: MIT
---

# Perception.cx Game-Cheat Script Development Guidelines

Behavioral rules and practical patterns for writing game-cheat scripts with Perception.cx in Enma, AngelScript, and C++. Derived from the Karpathy principles and rewritten for the domain: ESP, aimbot, triggerbot, radar, pattern scanning, world-to-screen math, memory reads/writes, and overlay rendering. These rules apply to authorized reverse engineering, security research, and game-cheat development — analyze only software you own or are authorized to test.

**Always active.** These rules apply every time you write or edit a game-cheat script. They are not suggestions.

**Prerequisites:** Load the `game-cheat-script-master` skill first. It defines the mandatory co-skills, read-first docs, and the canonical project layout. Then keep `game-hacking-pcx` loaded for the full API doc index. **Read the relevant doc before writing any API call** — see `skill://game-hacking-pcx` for the complete file-by-file index.

**Templates:** Use `templates/cheat-skeleton-em/` and `templates/cheat-skeleton-as/` as the starting scaffold for every new cheat. See `knowledge/cheat-script-cookbook.md` for reusable recipes (W2S, ESP, aimbot smoothing, triggerbot, radar, config save/load).

---

## 1. Know the Target Before You Touch Memory

**Never read or write a single byte until you know what you're reading.**

Before implementing any feature:
- State the game, engine, and binary you're targeting. Name the module.
- Identify whether offsets come from a sig scan, a hardcoded offset table, or the r5sdk/community SDK. Say which.
- If an offset is hardcoded, flag it: hardcoded offsets break on game updates. Prefer pattern scans.
- If the struct layout comes from a reversed SDK, cite the header file. If you guessed it, say "UNVERIFIED" and mark the offset.
- If you don't know the field size, read it as `ru64` and inspect — never assume `int32` vs `float32` without evidence.

```
Before: "Read player health at base+0x43E0"
After:  "r5sdk/src/game/server/player.h defines m_iHealth at 0x43E0 (int32).
         Sig for entity list: 48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 81
         Last verified: Season 21 patch 1.98"
```

**Why:** A wrong offset doesn't crash your script — it reads garbage silently. You'll spend an hour debugging ESP that draws at (0, 0) because the position field moved 8 bytes. Ground every offset.

---

## 2. Addresses Are `uint64`, Always

**One type for addresses. No exceptions. No `int64` addresses.**

- Every variable holding a memory address is `uint64`. Period.
- `proc.base_address()` returns `uint64`. Module bases are `uint64`. Pointer chain intermediates are `uint64`.
- If you must pass an address to a function taking `int64`, use `cast<int64>(addr)` at the call site, not at storage.
- Pattern scan results are `uint64`. Entity list pointers are `uint64`. VTable slots are `uint64`.

```cpp
// WRONG
int64 base = p.base_address();
int64 entity = p.r64(base + 0x1234);  // sign-extends high addresses, subtle corruption

// RIGHT
uint64 base = p.base_address();
uint64 entity = p.ru64(base + 0x1234);
```

**Why:** `int64` and `uint64` are implicitly convertible in Enma but sign-extend differently in pointer arithmetic. Kernel addresses and high-usermode addresses (Windows `0x7FF...`) turn negative in `int64`, breaking comparisons and offset math. One type, zero bugs.

---

## 3. Validate Before You Chain

**Every pointer in a chain can be null. Check it or crash.**

- After every `ru64` that produces a pointer, check for 0 before dereferencing.
- After `ref_process()`, check `.alive()` immediately.
- After `find_code_pattern()`, check for 0 — a missed sig means the offset table is stale.
- After `get_module_base()`, check for 0 — the module might not be loaded yet.
- `is_valid_address()` exists. Use it when chasing unknown pointer chains.

```cpp
// WRONG — entity_list could be 0 after a patch
uint64 entity_list = p.ru64(base + ENTITY_LIST_OFFSET);
uint64 entity = p.ru64(entity_list + i * 0x8);  // reads from address 0x0 + i*8 = garbage

// RIGHT
uint64 entity_list = p.ru64(base + ENTITY_LIST_OFFSET);
if (entity_list == 0) return;
uint64 entity = p.ru64(entity_list + i * 0x8);
if (entity == 0) continue;
```

**Why:** Failed reads return 0 silently in Perception. A null pointer in a chain doesn't crash — it reads from address `0 + offset`, which returns more zeros or garbage. Your ESP draws nothing or draws at (0,0) and you don't know why. Validate every link.

---

## 4. Separate Scan from Render

**Pattern scans and heavy reads happen once or on interval. Rendering happens every frame.**

Structure every script as:
1. **`main()`** — setup: process attach, pattern scans, resolve base addresses. Run once.
2. **Update routine** — read entity data, build display list. Runs on interval or every frame, but does NO drawing.
3. **Render routine** — draws from the cached display list. Runs every frame. Does NO memory reads.

```cpp
// Global state
proc_t g_proc;
uint64 g_entity_list;
vec3[] g_positions;

void on_update(int64 data) {
    // Read game state — separated from render
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 0x8);
        if (ent == 0) continue;
        g_positions[i] = g_proc.read_vec3_fl32(ent + POS_OFFSET);
    }
}

void on_render(int64 data) {
    // Draw from cache — no proc reads here
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        draw_circle(world_to_screen(g_positions[i]), 5.0, g_color_enemy, 1.0, true);
    }
}
```

**Why:** Mixing reads and draws makes every frame dependent on read latency. If the target process lags or a page is swapped out, your overlay stutters. Separating them means the render path is pure compute — smooth even when reads are slow. It also makes the code testable: you can verify reads independently from draw correctness.

---

## 5. Pattern Scans Over Hardcoded Offsets

**Sigs survive patches. Hardcoded offsets don't.**

- For any address that isn't a direct struct field offset from a known base, use `find_code_pattern`.
- The sig should be wide enough to be unique but not so wide it spans an instruction that changes per-build.
- Wildcard (`??`) the bytes that contain relocatable values: RIP-relative displacements, jump targets, immediate addresses.
- Store the sig as a named constant, not inline. Document what it finds.

```cpp
// Sig for CEntityList global pointer — LEA RCX, [rip+????]
// Wildcards on the 4-byte RIP displacement
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";

uint64 resolve_entity_list(proc_t& p, uint64 base, uint64 size) {
    uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0) return 0;
    // Resolve RIP-relative: read 4-byte displacement at hit+3, add to hit+7
    int32 disp = p.r32(hit + 3);
    return hit + 7 + cast<uint64>(disp);
}
```

**Why:** Every game update shuffles code and data. A hardcoded offset `0x25AB3F0` is dead on the next patch. A sig for the instruction that loads that pointer survives unless the compiler changes the instruction pattern — which is rare. Name your sigs, document what instruction they match, and resolve RIP-relative displacements correctly (4 bytes, signed, added to the *end* of the instruction).

---

## 6. One Feature, One File

**Each feature lives in its own file. No god scripts.**

- ESP in `esp.em`. Aimbot in `aim.em`. Radar in `radar.em`. Config/GUI in `menu.em`.
- Shared state (process handle, entity cache, config values) goes in a `globals.em` module and is imported.
- If two features need the same data, extract it into a shared update routine — don't duplicate reads.

```
project/
├── globals.em      # proc_t, entity cache, config state
├── offsets.em      # all sigs and resolved addresses
├── esp.em          # render routine for boxes/names/health
├── aim.em          # aimbot logic + smoothing
├── menu.em         # GUI sidebar widgets
└── main.em         # main() — setup, register routines
```

**Why:** A 2000-line monolith means every edit risks breaking unrelated features. Separate files let you reload one feature without touching others (Perception supports hot reload). It also makes it trivial to disable a feature: just don't register its routine.

---

## 7. Construct Every Frame, Cache Nothing Graphical

**Colors, vec2 positions, and font handles from `get_font*()` are cheap. Construct them fresh.**

- `color(r, g, b, a)` is a 4-byte stack struct. Creating it costs nothing.
- `vec2(x, y)` is two floats. Creating it costs nothing.
- `get_font20()` returns a cached handle — calling it every frame is fine.
- Never cache a `color` or `vec2` in a global to "avoid allocation" — there is no allocation. Enma drops them at scope exit.

```cpp
// WRONG — premature "optimization" that adds global state for nothing
color g_white;
color g_red;
int64 g_font;

int64 main() {
    g_white = color(255, 255, 255, 255);
    g_red = color(255, 0, 0, 255);
    g_font = get_font20();
    // ...
}

// RIGHT — construct in the render function, zero overhead
void on_render(int64 data) {
    color white = color(255, 255, 255, 255);
    color red = color(255, 0, 0, 255);
    draw_text("ESP", vec2(10.0, 10.0), white, get_font20(), 0, color(0,0,0,0), 0.0);
}
```

**Why:** Enma's `[[packed]]` structs are stack-allocated value types. A `color` is 4 bytes on the stack — cheaper than a global load. Caching render primitives adds mutable global state that makes reasoning about the render path harder, for literally zero performance gain.

---

## 8. Float Literals Need the `f` Suffix

**`0.2` is `float64`. `0.2f` is `float32`. The GPU and the game don't agree on which you meant.**

- All `vec2`/`vec3`/`vec4` constructors that feed vertex buffers need `float32` — use `f` suffix.
- Screen coordinates from `get_view_width()`/`get_view_height()` return `float64` — that's fine for draw calls.
- `read_vec3_fl32` returns `float64` fields (promoted) — arithmetic is `float64`, no suffix needed.
- When writing back to game memory with `wf32()`, the value is narrowed — make sure your math didn't accumulate `float64` precision you'll silently lose.

```cpp
// Custom vertex buffer data — must be float32
float32 x = 10.0f;
float32 y = 20.0f;

// Draw calls accept float64 — no suffix needed
draw_line(vec2(10.0, 20.0), vec2(100.0, 200.0), white, 1.0);
```

---

## 9. Prefer Reads Over Writes

**Reads are non-invasive. Writes alter the target's state and are inherently riskier.**

- Analysis, visualization, entity inspection, distance display — all read-only. Prefer these.
- If you must write (patching for research on a target you own or are authorized to test, modifying your own single-player session), write the minimum bytes needed and know exactly why.
- Never `wvm` a large buffer when `wu32` or `wf32` on a single field suffices.
- After a research write, verify it took effect with a read-back; some targets revert unexpected patches.
- Gate all writes behind `write_memory` permission checks — Perception enforces this; respect it in your design too.

```cpp
// WRONG — nop-patching 16 bytes when you only need one field
array<uint8> nops = {0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90};
p.wvm(recoil_addr, nops);

// RIGHT — write the single float you actually mean to change, minimal footprint
p.wf32(recoil_spread_addr, 0.0f);
```

**Why:** Every memory write mutates the target's state — a read is observation, a write is intervention. For analysis and overlay work you almost never need to write, and when you do, a minimal, deliberate write is easier to reason about and roll back than a large patch. Treat writes as a last resort, not a default.

---

## 10. World-to-Screen Is Math, Not Magic

**Implement W2S correctly once. Never approximate it.**

The formula depends on the engine's view matrix layout. For Source Engine (Apex, CS2, TF2):

```cpp
// Source Engine uses a 4x3 view matrix (3 rows of 4 floats = 48 bytes)
// Row 0: right.x, right.y, right.z, right.w
// Row 1: up.x,    up.y,    up.z,    up.w
// Row 2: fwd.x,   fwd.y,   fwd.z,   fwd.w

bool world_to_screen(vec3 world, out vec2 screen, float64 matrix_addr) {
    // Read 12 floats from the view matrix
    float64 w = m[3]*world.x + m[7]*world.y + m[11]*world.z + m[15]; // not present in 4x3 — check engine
    if (w < 0.001) return false;  // behind camera

    float64 inv_w = 1.0 / w;
    float64 nx = (m[0]*world.x + m[4]*world.y + m[8]*world.z + m[12]) * inv_w;
    float64 ny = (m[1]*world.x + m[5]*world.y + m[9]*world.z + m[13]) * inv_w;

    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2(
        (vw * 0.5) + (nx * vw * 0.5),
        (vh * 0.5) - (ny * vh * 0.5)
    );
    return true;
}
```

**Rules:**
- Always check `w > 0` (or a small epsilon) — behind-camera points produce mirrored coordinates.
- Read the matrix from the game's actual view matrix address, not a reconstructed one.
- Match the matrix layout to the engine. Source uses column-major 4x4, Unreal uses row-major, Unity uses column-major with flipped Z.
- Implement it once in a shared module. Every feature imports it.

---

## 11. GUI State Is Config, Not Code

**Every tunable goes through the GUI API. No magic constants buried in logic.**

- Bind every threshold, color, toggle, and hotkey to a GUI widget in a sidebar section.
- Use `section_checkbox` for feature toggles, `section_slider_float` for distances/smoothing, `section_keybind` for hotkeys.
- Read widget state at the top of each routine, then branch on it. Don't mix widget reads deep inside nested loops.
- Persist config to a file via the filesystem API. Load it in `main()`.

```cpp
bool g_esp_enabled;
float64 g_esp_distance;
color g_esp_color;

void setup_gui() {
    int64 sec = create_section("ESP");
    section_checkbox(sec, "Enable ESP", g_esp_enabled);
    section_slider_float(sec, "Max Distance", g_esp_distance, 0.0, 5000.0);
    // color picker, keybind, etc.
}
```

**Why:** Hardcoded thresholds mean recompiling to tweak. The overlay is your debugger — every value you might change during a session should be adjustable live. This also means someone else can use your script without reading the source.

---

## 12. Verify With the Binary, Not With Your Memory

**The IDB, the sig, and the live read must agree. If they don't, trust the live read.**

When something doesn't work:
1. Check the sig still hits in the current binary: `find_code_pattern` returns 0? Offset table is stale.
2. `struct_dump` the entity at the base you have — verify the field layout visually.
3. Cross-reference against the r5sdk headers or IDA's type info, but remember the SDK may be from an older season.
4. If the live read shows a valid-looking float where you expected an int, the struct changed. Update your types.
5. Never assume your cached offset table is correct after a game update. Re-scan everything.

```
Debugging checklist:
1. Is the process alive?           → p.alive()
2. Is the module loaded?           → get_module_base() != 0
3. Does the sig still hit?         → find_code_pattern() != 0
4. Is the pointer chain valid?     → check every link for 0
5. Does the field contain what     → struct_dump() or read + print
   you expect?
```

---

## Summary

| # | Rule | One-liner |
|---|------|-----------|
| 1 | Know the target | Ground every offset in evidence |
| 2 | `uint64` addresses | One type, zero sign bugs |
| 3 | Validate chains | Every pointer can be null |
| 4 | Separate scan/render | Reads and draws don't mix |
| 5 | Sigs over hardcodes | Survive patches |
| 6 | One feature, one file | No god scripts |
| 7 | Construct every frame | Colors and vecs are free |
| 8 | `f` suffix for float32 | The GPU cares |
| 9 | Prefer reads over writes | Reads are non-invasive |
| 10 | W2S once, correctly | Math, not magic |
| 11 | GUI for all tunables | No magic constants |
| 12 | Verify with the binary | Trust live reads over memory |

---

## Source: `.claude/skills/game-hacking-pcx/SKILL.md`

---
name: game-hacking-pcx
description: >
  Mandatory doc router for all PCX scripting sessions. Triggers on any game
  hacking, game cheat, ESP, aimbot, triggerbot, radar, Enma, AngelScript, or
  Perception.cx work. Provides the full doc index (43,000+ lines across 139
  files) and enforces reading the relevant documentation before writing any
  API call. Load alongside game-cheat-script-master and game-cheat-guidelines
  on every PCX game-cheat session.
license: MIT
---

# Game Hacking & Scripting — Perception.cx / Enma / AngelScript / C++

## Trigger
Game hacking, game cheats, cheat scripts, ESP, aimbot, triggerbot, radar, memory reading/writing,
pattern scanning, vtable hooking, process manipulation, Enma scripting, AngelScript scripting,
Perception.cx, PCX, render overlays, any `.em` or `.as` game script work, or any mention of the
Perception platform.

## MANDATORY: Read Before Writing Code

**You MUST read the relevant docs from `docs/` before writing ANY Enma, AngelScript,
or PCX API code.** Do not write from memory. The docs are the source of truth.

### When writing Enma (.em) code — read these:

**Language (always read `llms-language.md` first — it's the complete single-page reference):**
| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Complete language ref** | `docs/enma/llms-language.md` | 2861 | Every type, operator, control flow, struct, class, template, coroutine, exception, heap, FFI, annotation, module, addon |
| Complete SDK ref | `docs/enma/llms-sdk.md` | 832 | Embedding API, type registration, native functions, hot reload |

**Language guide (granular pages if you need detail beyond the single-page ref):**
| Doc | Path | Lines |
|-----|------|-------|
| Basics (types, vars, operators, control flow) | `docs/enma/lang-basics.md` | 267 |
| Functions (params, defaults, refs, out, variadic, lambdas) | `docs/enma/lang-functions.md` | 247 |
| Pointers (heap, address-of, member access, null) | `docs/enma/lang-pointers.md` | 357 |
| Structs & Classes (value/ref types, inheritance, vtable, interfaces, mixins) | `docs/enma/lang-structs-and-classes.md` | 912 |
| Templates (generics, monomorphization) | `docs/enma/lang-templates.md` | 173 |
| Advanced (delegates, namespaces, coroutines, exceptions, smart ptrs, FFI) | `docs/enma/lang-advanced.md` | 562 |
| Annotations (packed, align, reflect, serialize, export, dll, custom) | `docs/enma/lang-annotations.md` | 209 |
| Modules (import, .emb, multi-module linking) | `docs/enma/lang-modules.md` | 100 |
| Preprocessor (#define, #ifdef, #include, #pragma) | `docs/enma/lang-pre-processor.md` | 77 |
| Semantics & Limits (guarantees, compile-time rejects, what doesn't exist) | `docs/enma/lang-semantics-and-limits.md` | 181 |

**Addons (standard library — read the addon doc before using its types):**
| Addon | Path | Lines | Key types/functions |
|-------|------|-------|---------------------|
| Core | `docs/enma/addon-core.md` | 42 | `println`, `print` |
| Strings | `docs/enma/addon-strings.md` | 165 | `format`, `to_int`, `split`, `replace`, `substr` |
| Arrays | `docs/enma/addon-arrays.md` | 119 | `push`, `pop`, `sort`, `contains`, `slice`, `for-each` |
| Maps | `docs/enma/addon-maps.md` | 200 | `map<K,V>`, `get`, `set`, `contains`, `imap<V>` |
| Math | `docs/enma/addon-math.md` | 137 | `sin`, `cos`, `atan2`, `sqrt`, `clamp`, `lerp`, `random` |
| SIMD | `docs/enma/addon-simd.md` | 128 | SSE2 `f32x4`, `i32x4` vector ops |
| Vectors | `docs/enma/addon-vec.md` | 135 | `vec2`, `vec3`, `vec4` math types |
| 3D Math | `docs/enma/addon-math3d.md` | 182 | `quat`, `mat4` rotation/transform |
| Variant | `docs/enma/addon-variant.md` | 130 | Type-erased value container |
| Atomic | `docs/enma/addon-atomic.md` | 94 | `aint32`, `aint64` atomic ops |
| Bits | `docs/enma/addon-bits.md` | 117 | `popcount`, `clz`, `ctz`, `bswap`, `rotl` |
| Time | `docs/enma/addon-time.md` | 95 | `time_ms()`, `time_us()`, ISO 8601, `sleep` |
| Regex | `docs/enma/addon-regex.md` | 61 | `match`, `find`, `replace`, `split`, capture groups |
| File | `docs/enma/addon-file.md` | 125 | Sandboxed file I/O (permission-gated) |
| Thread | `docs/enma/addon-thread.md` | 120 | `mutex`, `lock_guard`, `condition_variable` |
| Hash Set | `docs/enma/addon-hash_set.md` | 89 | `hash_set<T>` |
| Sorted Map | `docs/enma/addon-sorted_map.md` | 89 | `sorted_map<K,V>` ordered iteration |
| List | `docs/enma/addon-list.md` | 192 | Double-ended O(1) push/pop |
| JSON | `docs/enma/addon-json.md` | 108 | `json_parse`, `json_stringify`, `json_value` navigation |

**SDK (C++ embedding — read when building host-side or custom addons):**
| Doc | Path | Lines |
|-----|------|-------|
| Quick Start | `docs/enma/sdk-quick-start.md` | 126 |
| Engine Lifecycle | `docs/enma/sdk-engine-lifecycle.md` | 166 |
| Compilation | `docs/enma/sdk-compilation.md` | 65 |
| Execution | `docs/enma/sdk-execution.md` | 103 |
| Calling Functions | `docs/enma/sdk-calling-functions.md` | 82 |
| Globals | `docs/enma/sdk-globals.md` | 79 |
| Type Registration | `docs/enma/sdk-type-registration.md` | 862 |
| Native Functions | `docs/enma/sdk-native-functions.md` | 446 |
| Hot Reload | `docs/enma/sdk-hot-reload.md` | 64 |
| Serialization & Linking | `docs/enma/sdk-serialization-and-linking.md` | 97 |
| Introspection | `docs/enma/sdk-introspection.md` | 317 |
| Lifecycle & RAII | `docs/enma/sdk-lifecycle.md` | 227 |
| Debug & Heap | `docs/enma/sdk-debug-and-gc.md` | 202 |
| Error Handling | `docs/enma/sdk-error-handling.md` | 116 |
| Safety | `docs/enma/sdk-safety.md` | 121 |
| Custom Addons | `docs/enma/sdk-custom-addons.md` | 576 |
| API Reference | `docs/enma/sdk-api-reference.md` | 411 |

### When writing PCX Enma API code — read the relevant API doc:

| API | Path | Lines | Use for |
|-----|------|-------|---------|
| **Proc API** | `docs/perception/proc-api.md` | 294 | Memory read/write, modules, pattern scan, VAD, pointer arrays, vec/quat/mat reads |
| **Render API** | `docs/perception/render-api.md` | 264 | 2D drawing (text, lines, circles, rects), fonts, shaders, vertex/index buffers, compute |
| **GUI API** | `docs/perception/gui-api.md` | 455 | Sidebar sections, checkboxes, sliders, buttons, text inputs, color pickers, keybinds |
| **Input API** | `docs/perception/input-api.md` | 126 | Mouse + keyboard state polling |
| **CPU API** | `docs/perception/cpu-api.md` | 92 | CPU ID, timing, datetime, bitcasts, thread priority |
| **Zydis API** | `docs/perception/zydis-api.md` | 133 | x86-64 assembler/disassembler |
| **Unicorn API** | `docs/perception/unicorn-api.md` | 151 | x86-64 CPU emulation |
| **Net API** | `docs/perception/net-api.md` | 200 | HTTP, WebSocket, raw UDP |
| **Win API** | `docs/perception/win-api.md` | 120 | Window enum, clipboard, keyboard/mouse send |
| **Filesystem API** | `docs/perception/filesystem-api.md` | 162 | Sandboxed file I/O |
| **Sound API** | `docs/perception/sound-api.md` | 90 | WAV/OGG playback |
| **Lifecycle** | `docs/perception/lifecycle-and-routines.md` | 134 | main(), routines, unload, exceptions |
| **MCP API** | `docs/perception/mcp-api.md` | 268 | AI agent JSON-RPC surface |

### When writing core AngelScript (.as) code — read the language manual:

| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Language Index** | `docs/angelscript-lang/INDEX.md` | - | Overview of the core language, data types, statements, etc. |
| Datatypes | `docs/angelscript-lang/datatypes.md` | 17 | Landing page for primitives, objects, and handles |
| Handles | `docs/angelscript-lang/handles.md` | - | Core AngelScript `@` object handles and memory management |
| Script Classes | `docs/angelscript-lang/script-class.md` | - | User-defined classes, members, and methods |
| Expressions | `docs/angelscript-lang/expressions.md` | - | Math, logic, assignments, and operator precedence |
| Statements | `docs/angelscript-lang/statements.md` | - | If, switch, loops, try/catch |

### When writing PCX AngelScript (.as) code — read these:

| API | Path | Lines |
|-----|------|-------|
| Overview | `docs/perception/angelscript/overview.md` | 68 |
| Life Cycle | `docs/perception/angelscript/life-cycle.md` | 128 |
| Engine | `docs/perception/angelscript/engine.md` | 178 |
| Atomic Types | `docs/perception/angelscript/atomic-types.md` | 185 |
| Proc API | `docs/perception/angelscript/proc-api.md` | 1156 |
| Render API | `docs/perception/angelscript/render-api.md` | 1829 |
| GUI API | `docs/perception/angelscript/gui-api.md` | 718 |
| Input API | `docs/perception/angelscript/input-api.md` | 226 |
| System/CPU/Disasm | `docs/perception/angelscript/system-api-cpu-and-disassembly.md` | 304 |
| Net API | `docs/perception/angelscript/net-api.md` | 379 |
| File System | `docs/perception/angelscript/file-system.md` | 298 |
| Extended Math | `docs/perception/angelscript/extended-math-api.md` | 580 |
| Win API | `docs/perception/angelscript/win-api.md` | 594 |
| JSON API | `docs/perception/angelscript/json-api.md` | 479 |
| Unicorn | `docs/perception/angelscript/unicorn.md` | 702 |
| Zydis Encoder | `docs/perception/angelscript/zydis-encoder.md` | 703 |
| Intrinsics | `docs/perception/angelscript/intrinsics.md` | 661 |
| Mutex API | `docs/perception/angelscript/mutex-api.md` | 248 |
| Utilities | `docs/perception/angelscript/utilities.md` | 607 |
| Sound API | `docs/perception/angelscript/sound-api.md` | 250 |
| Bit Reinterpret | `docs/perception/angelscript/bit-reinterpret-helpers.md` | 167 |
| Engine Specific | `docs/perception/angelscript/engine-specific-api.md` | 195 |
| CS2 Extended | `docs/perception/angelscript/cs2-extended-api.md` | 165 |

### PCX IDE & Extensions:

| Doc | Path | Lines |
|-----|------|-------|
| Perception IDE | `docs/perception/ide.md` | 585 |
| Extensions API | `docs/perception/extensions-api.md` | 371 |
| Analyzer | `docs/perception/analyzer.md` | 370 |

### When writing core Lua (.lua) code — read the language manual:

| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Reference Manual** | `docs/lua-lang/manual-5.4.md` | 6056 | Full, authoritative Lua 5.4 reference manual |
| Welcome & Readme | `docs/lua-lang/readme-5.4.md` | 150 | Lua 5.4 readme and changes |

### PCX Lua (.lua) scripting:

| API | Path | Lines |
|-----|------|-------|
| Overview | `docs/perception/lua/overview.md` | 59 |
| All APIs | `docs/perception/lua/*.md` | 5779 total |

## How To Use These Docs

1. **Before starting a game-cheat script**: load `skill://game-cheat-script-master` and read `knowledge/cheat-script-cookbook.md`
2. **Before writing Enma code**: `read docs/enma/llms-language.md` (the single-page complete ref)
3. **Before calling a PCX API**: `read docs/perception/<api-name>.md`
4. **Before writing AngelScript**: `read docs/perception/angelscript/<api-name>.md`
5. **If unsure about a type, function, or parameter**: read the doc, don't guess
6. **If the doc says a function is "gated"**: it requires a permission flag — mention this to the user
7. **For a starting project scaffold**: use `templates/cheat-skeleton-em/` or `templates/cheat-skeleton-as/`

## Cheat-Script Scaffolds

- **Enma skeleton**: `templates/cheat-skeleton-em/` — globals, offsets, utils, ESP, aim, triggerbot, radar, menu, main
- **AngelScript skeleton**: `templates/cheat-skeleton-as/` — same layout in AngelScript
- **Cookbook recipes**: `knowledge/cheat-script-cookbook.md` — pattern scan, pointer chain, W2S, ESP, aim smoothing, FOV, triggerbot, radar, config, unload cleanup

## Critical Enma Rules (from the docs)

- **Addresses are `uint64`**, never `int64` — sign-extension breaks high addresses
- **`float32` literals need `f` suffix**: `0.2f` not `0.2`
- **Implicit conversion: `int→float` OK, `float→int` COMPILE ERROR** — use `cast<int32>(f)`
- **`signed↔unsigned` is COMPILE ERROR** — use `cast<uint64>(signed_val)`
- **`color` and `vec2` are value types** — 4-byte and 8-byte stack structs, construct every frame
- **Handles from `create_*`/`load_*` are encrypted `int64`** — pass back, don't inspect
- **`main()` returns `> 0` to stay loaded, `<= 0` to unload**
- **Routines registered via `register_routine(cast<int64>(fn), data)`**
- **`proc_t` released on scope exit** (RAII) — no leak if you use stack variables
- **Failed reads return 0**, not exceptions — validate pointers
- **Pattern sigs**: hex bytes, `??` wildcard, e.g. `"48 8B 05 ?? ?? ?? ?? 48 85 C0"`
- **`import "vec"; import "color";`** — modules must be imported to use their types
- **`string` interpolation**: `f"value={x}"` — use `format()` for hex: `format("0x{x}", addr)`
- **No garbage collector** — deterministic RAII, destructors run at scope exit

## LSP Servers (built, ready to use)

- **Enma LSP**: `lsp/enma-lsp/server/dist/server.js`
- **AngelScript+PCX LSP**: `lsp/angel-lsp-pcx/server/out/server.js`

## RE Tools & Knowledge

- **Plugins & FLIRT sigs**: `knowledge/re-plugins-and-tools.md` — 6 IDA plugins, 4 Ghidra extensions, 51 FLIRT sigs, diffing, ret-sync
- **Anti-cheat architecture**: `knowledge/anti-cheat-architecture.md` — EAC/BE/Vanguard/GG detection matrix
- **Kernel RE tools**: `knowledge/kernel-re-tools.md` — WinDbg, HyperDbg, Volatility, PCILeech, IRPMon
- **AC driver patterns**: `signatures/anti-cheat/common-ac-patterns.md` — driver ID, callback sigs, integrity check patterns
- **Deobfuscation**: `skill://deobfuscation` — VM/CFF/packer reversal methodology (Themida, VMProtect, OLLVM)
- **Obfuscation taxonomy**: `knowledge/obfuscation-taxonomy.md` — protector architecture and weaknesses
- **Deobfuscation tools**: `knowledge/deobfuscation-tools.md` — NoVmp, Triton, Miasm, D-810, ScyllaHide, FLOSS
- **Protector patterns**: `signatures/obfuscation/protector-patterns.md` — VMP/Themida/OLLVM section names, dispatcher patterns, anti-debug
- r5sdk: `sdks/r5sdk/` (2438 reversed headers for Apex Legends)
- IDA IDB: `idb/r5apex_dx12_dump.i64` (28936 functions, FLIRT+types)
- Ghidra: `ghidra-projects/r5apex/`
- radare2, Ghidra, semgrep MCP servers all available

---

## Source: `.claude/skills/pcx-coding-discipline/SKILL.md`

---
name: pcx-coding-discipline
description: >
  Workflow discipline for developing Enma (.em) and AngelScript (.as) scripts
  on Perception.cx. Derived from Karpathy principles — think before coding,
  simplicity first, surgical changes, goal-driven execution — rewritten for
  cheat development realities: stale offsets, silent failed reads, detection
  surface. Always active when writing or editing PCX scripts.
license: MIT
---

# PCX Coding Discipline — How to Write Scripts, Not What They Look Like

Workflow discipline for developing Enma (`.em`) and AngelScript (`.as`) scripts on Perception.cx. Derived from the four Karpathy principles — *think before coding, simplicity first, surgical changes, goal-driven execution* — and rewritten for the realities of cheat development: stale offsets, silent failed reads, detection surface, and overlays you debug by looking at them.

**Always active when writing or editing PCX scripts.** This is the *process* layer. The `game-cheat-guidelines` skill is the *code-shape* layer (uint64 addresses, null guards, render separation). Load both: this one tells you how to work, that one tells you what the code must look like.

**Prerequisite:** Read the relevant doc before writing any API call — see `skill://game-hacking-pcx` for the file-by-file index.

## Trigger
Writing or editing any `.em` / `.as` script, adding a cheat feature, refactoring a script, fixing a broken overlay, deciding how much to build, or judging whether a script is "done."

---

## 1. Think Before You Touch the Editor

**Name the target, the source of every offset, and the tradeoff you're making — out loud — before you write a line.**

The single most expensive habit in cheat development is writing code against assumptions. A wrong offset doesn't throw; it reads garbage and your ESP draws at (0, 0). Before implementing:

- **State the target.** Game, engine, module. "Apex / Source (r5) / `r5apex.exe`."
- **State where each offset comes from.** Sig scan, SDK header, or hardcode — and say which. If you're guessing a struct field, write `// UNVERIFIED` next to it.
- **Surface the tradeoff the user didn't ask about.** Read-only ESP is invisible; a memory write for aimbot is a detection surface. Per-frame reads are simple but couple render to read latency. Say which you're choosing and why.
- **If the doc is ambiguous or the API is permission-gated, stop and read it.** Do not invent `draw_esp()` or assume `draw_circle` takes a fill flag. Open `docs/perception/render-api.md`.

```
Before: "I'll write an ESP overlay."
        *invents function names, assumes int32 offsets, no W2S behind-camera check*

After:  "Target: Apex / Source (r5). Entity list via sig (UNVERIFIED layout, r5sdk season 21).
         Read-only ESP, per-frame W2S — accepting read/render coupling for v1 simplicity.
         Reading render-api.md + lifecycle-and-routines.md before writing."
```

**Why:** Confusion hidden behind plausible code costs hours. Confusion stated up front costs one sentence and gets corrected before it compiles into a silent bug.

---

## 2. The Simplest Cheat That Works

**Build the minimum feature that satisfies the ask. Nothing speculative.**

Cheat scripts rot into 2000-line monoliths because every feature arrives with prediction, smoothing, themes, and a config framework nobody requested. Climb down the ladder:

- **"Highlight enemies" is a box, not a skeleton-ESP-with-bones-and-LOD.** Ship the box. Add bones when asked.
- **An aimbot the user described as "snap to head" doesn't need velocity prediction.** Don't add it.
- **No config system for a value that never changes.** A fixed enemy color is `color(255,0,0,255)`, not a JSON-loaded theme engine.
- **No abstraction over the proc API.** `p.ru64(...)` is the interface. Wrapping it in a `MemoryManager` class buys nothing.
- **No "feature manager" framework for three features.** Three registered routines is the framework.

```cpp
// WRONG — entity-component scaffolding for "draw boxes on enemies"
class IFeature { void update(); void render(); }
class FeatureRegistry { array<IFeature@> features; ... }
class EspFeature : IFeature { /* 200 lines */ }

// RIGHT — two routines, done
void on_update(int64 data) { /* read positions into g_positions */ }
void on_render(int64 data) { /* draw boxes from g_positions */ }
```

**Why:** Every speculative line is a line someone debugs at 3am after a patch. The lazy version ships today and is trivially extended when a real second requirement shows up — which is the only honest signal that the abstraction was needed.

---

## 3. Surgical Edits — One Feature, One Diff

**When changing a script, touch only the feature you're changing. Clean up only the mess your change makes.**

Perception scripts are built for hot reload precisely so you can change one file without disturbing the rest. Honor that:

- **Editing ESP color? Edit `esp.em`.** Do not reformat `menu.em`, rename globals in `globals.em`, or "tidy" `main.em` while you're in there.
- **Match the module's existing style** — naming, the per-feature file split, the order of routine registration. A second convention beside the first is worse than the style you'd have picked.
- **If your change orphans a global or import, remove it.** If you spot pre-existing dead code unrelated to your change, mention it — don't delete it.
- **Don't churn working offsets.** A sig that still hits and resolves to valid data is not your problem today.

```
Task: "the enemy boxes are the wrong color"

WRONG diff:  esp.em (color)  +  globals.em (renamed g_col → g_enemyColor)
             +  menu.em (reordered widgets)  +  main.em (reformatted)

RIGHT diff:  esp.em (color)
```

**Why:** Every file you touch is a file that can break and a file the next reader has to diff. A four-file diff to change one color hides the actual change and risks the three features you didn't mean to touch.

---

## 4. Done Means It Works on the Target

**Define success as something you can *see* on the live game, then loop until you see it. Compiling is not done.**

A script that compiles has proven nothing about whether the offsets are right, the W2S matches the engine, or the overlay aligns. Set a concrete bar and verify against it:

- **Write the success criteria before coding**, as observable facts: "boxes track enemies at any distance, nothing draws behind the camera, count matches the scoreboard."
- **The overlay is your debugger.** When something's off, draw the raw W2S coordinates and `print` the entity count — don't guess.
- **Loop:** compile → load → look at the screen → compare to the criteria → fix → reload. Repeat until every criterion holds.
- **When the IDB, the SDK, and the live read disagree, trust the live read** (see `game-cheat-guidelines` #12). The SDK may be from an older season.

```
Success criteria for "enemy ESP":
[ ] A box appears on every enemy entity (count == live enemy count)
[ ] Boxes track movement smoothly, no stutter
[ ] No box renders when the entity is behind the camera (W2S w > 0)
[ ] No box at (0,0) — that means a null read slipped a guard
[ ] Boxes scale with distance (far enemies = smaller boxes)
```

**Why:** "It compiles" and "it works" are different claims, and only the second one is the deliverable. A success checklist turns a vague "make ESP" into a loop you can run yourself without asking the user whether it's right.

---

## 5. Deletion Before Addition

**Try removing code before writing new code. The shortest script that works is the one with the fewest lines to break after a patch.**

When a feature request arrives, check what already exists first:

- **Can you delete a workaround instead of adding a second one?** Two workarounds for the same stale offset is a sign one should die.
- **Can you inline a wrapper?** A `ReadEntity()` function that calls `p.ru64()` once with no validation adds a name, not value. Inline it.
- **Can you merge two features into one routine?** If `on_update_esp` and `on_update_radar` both walk the same entity list, one walk and two draw calls in `on_render` is fewer lines and fewer reads.
- **Before adding a class, count its callers.** One caller = inline. Two = maybe. Three = extract, not before.

```cpp
// WRONG — utility wrapper around a one-liner
uint64 ReadEntityBase(proc_t@ p, uint64 list, int idx) {
    return p.ru64(list + idx * 0x20);
}
// ... called exactly once

// RIGHT — inline it, the proc_t API is already the interface
uint64 ent = p.ru64(entity_list + i * 0x20);
```

**Why:** Every line in a cheat script is a line you re-validate after a game patch. 80 lines is 80 potential breakpoints. 40 lines is half the post-patch work.

---

## 6. Question the Requirement

**Ship the minimum, then challenge the rest — in the same response, not a separate conversation.**

When the ask is vague or ambitious ("make a full ESP with health bars, distance, snaplines, team colors, and a config panel"):

1. **Build the core** — boxes on enemies, W2S, null guards.
2. **Ship it working.**
3. **In the same response:** "Done: box ESP with W2S + null guards. Health bars and snaplines are 10 lines each when you want them. Team colors need a second read per entity — add when the base ESP is confirmed working. Config panel is overhead for 3 settings — `bool` globals + a sidebar checkbox cover it."

Never stall on an answer you can default. Never build five features to avoid the conversation about whether three of them matter.

```
Pattern:  [working code] → skipped: [X]. add when [Y].
```

---

## 7. Mark Deliberate Shortcuts

**Every deliberate simplification gets a `// defer:` comment naming its ceiling and the trigger to revisit.**

`// UNVERIFIED` marks offset confidence. `// defer:` marks *design* shortcuts — places where you chose the simple path and know the ceiling.

```cpp
// defer: single entity array walk, separate walks per feature if >200 entities tank FPS
void on_update(int64 data) { ... }

// defer: hardcoded team color, config panel if user asks for customization
color enemy_col = color(255, 0, 0, 255);

// defer: global proc_t handle, per-feature handles if multi-process support needed
proc_t@ g_proc;
```

Format: `// defer: <what was simplified>, <when to revisit>`

A `// defer:` with no trigger is a shortcut that rots silently. Always name the trigger.

**Not deferred:** pointer validation, `w > 0` checks, `uint64` for addresses, `f` suffix on floats. Those are the floor, not shortcuts.

---

## 8. One Self-Check Per Non-Trivial Feature

**You can't unit test against a live game, but non-trivial logic leaves one sanity print behind.**

Cheat scripts run against a live target — no mock framework, no test harness. But logic bugs (wrong struct offset math, bad matrix indexing, off-by-one in entity iteration) can be caught with a visible sanity check:

- **Entity count print:** `print("entities: " + g_positions.length());` in `on_update`. If it reads 0 or 9999, something's wrong before you even look at the overlay.
- **Address range check:** `if (addr < 0x10000 || addr > 0x7FFFFFFFFFFF) print("suspect addr: " + addr);` — catches sign-extension and null-deref-adjacent reads.
- **W2S validation:** draw the raw screen coords as text before drawing boxes. If they cluster at (0,0), a null read slipped.
- **One `print()` per feature, gated behind a debug flag.** Not a logging framework — one line.

```cpp
// Self-check: remove or gate behind g_debug when stable
if (g_debug) print("[esp] ents=" + ents.length() + " visible=" + drawn);
```

**Why:** The laziest debugger that catches real bugs. One print per feature is near-zero overhead. A logging framework for three features is debt you don't need.

---

## Summary

| # | Principle | In PCX terms |
|---|-----------|--------------|
| 1 | Think Before Coding | Name target, offset source, and tradeoff before the first line |
| 2 | Simplicity First | Ship the box, not the framework — no speculative features |
| 3 | Surgical Changes | One feature, one diff; clean only your own orphans |
| 4 | Goal-Driven Execution | Done = visible success criteria met on the live target, not "compiles" |
| 5 | Deletion Before Addition | Try removing/inlining before writing new code |
| 6 | Question the Requirement | Ship the minimum, challenge the rest in the same response |
| 7 | Mark Deliberate Shortcuts | `// defer: <ceiling>, <trigger>` for design shortcuts |
| 8 | One Self-Check Per Feature | One `print()` per non-trivial feature, gated behind `g_debug` |

---

## Source: `.claude/skills/pcx-re-discipline/SKILL.md`

---
name: pcx-re-discipline
description: >
  Workflow discipline for reverse engineering and offset maintenance: locating
  structs, generating signatures, resolving RIP-relative addresses, and
  keeping an offset table alive across patches. Derived from Karpathy
  principles, rewritten for RE where the failure mode is a confident wrong
  answer. Always active when doing RE or offset work.
license: MIT
---

# PCX Reverse-Engineering Discipline — Finding Offsets Without Fooling Yourself

Workflow discipline for reverse engineering and offset maintenance: locating structs, generating signatures, resolving RIP-relative addresses, and keeping an offset table alive across game patches. Derived from the four Karpathy principles — *think before coding, simplicity first, surgical changes, goal-driven execution* — rewritten for RE work, where the failure mode isn't a crash but a confident wrong answer.

**Always active when doing RE or offset work.** This complements `game-cheat-guidelines` #1 (ground every offset) and #12 (verify with the binary), and the `knowledge/offset-methodology.md` mechanics. Those cover *how* to scan; this covers *how to work* so you don't ship a guess.

## Trigger
Disassembling a function, mapping a struct layout, generating a byte signature, resolving an offset, updating an offset table after a patch, or cross-referencing an SDK against a live binary. Tools: IDA, Ghidra, radare2, and the Perception RE tools (`struct_dump`, `find_xrefs`, `analyze_vtable`, `read_rtti`, `generate_signature`, `find_code_pattern`, `build_call_graph`).

---

## 1. Hypothesize Before You Disassemble

**Form a claim about what a function or field *is*, then look for evidence — don't reverse aimlessly and rationalize whatever you find.**

A float at `entity+0x43E0` that reads `100.0` might be health. It might be armor, a timer, or a shield that happens to start at 100. Guessing wrong here is silent and expensive.

- **State the hypothesis first.** "This sig should land on the LEA that loads `CEntityList`. Expected: `48 8D 0D` followed by a RIP displacement."
- **Use the cheapest evidence before manual disasm.** RTTI names (`read_rtti`) and string xrefs (`find_xrefs`) identify a class faster than reading instructions. Reach for them first.
- **Mark unverified findings `UNVERIFIED` and cite the source** — r5sdk header path, RTTI string, IDA xref address. An offset without a citation is a rumor.
- **One value is not proof.** Confirm a field by watching it change as you'd expect in-game, or by matching the SDK layout — not by a single plausible read.

```
Before: "0x43E0 is health, it reads 100."

After:  "Hypothesis: 0x43E0 = m_iHealth (int32).
         Evidence: r5sdk/player.h offset matches; read_rtti confirms class CPlayer;
         value drops to 73 after taking damage in-game. CONFIRMED."
```

**Why:** RE has no compiler to catch you. The only thing standing between a wrong offset and an hour of debugging ESP-at-(0,0) is the evidence you demanded before believing your own hypothesis.

---

## 2. The Simplest Signature That's Unique

**The shortest byte pattern that hits exactly one location. Not longer, not vaguer.**

A sig is a tradeoff: too specific and it breaks on the next compiler tweak; too loose and it matches three places and resolves to garbage.

- **Wildcard only the relocatable bytes** — RIP-relative displacements, absolute immediates, jump targets. Keep the opcodes. `48 8D 0D ?? ?? ?? ??` wildcards the displacement, keeps the `LEA RCX` opcode.
- **Stop at the first length that's unique.** Verify it with `find_code_pattern` over the module — one hit means stop. Don't bolt on ten more bytes "to be safe"; that's the brittleness you'll pay for next patch.
- **Don't reverse a whole class to read one field.** `struct_dump` the instance and xref the accessor function. Map the entire vtable only when you actually need the entire vtable.
- **Don't build a full offset dumper for three offsets.** Three sigs in `offsets.em` is the right size for three offsets.

```cpp
// WRONG — 24 bytes, spans an immediate that changes per build → dead next patch
"48 8D 0D 30 AF 25 02 E8 1A 4C 00 00 48 8B D8 48 85 DB 74 12 8B 05 ..."

// RIGHT — shortest unique hit, displacement wildcarded
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";
// verify: find_code_pattern(base, size, SIG_ENTITY_LIST) returns exactly one hit
```

**Why:** Every non-wildcarded byte is a bet that the compiler emits it identically next build. The minimal unique sig makes the fewest bets, so it survives the most patches — which is the entire point of using sigs over hardcodes.

---

## 3. After a Patch, Re-verify Only What Broke

**Run the whole table, fix the misses, leave the hits alone. Don't regenerate offsets that still work.**

The temptation after a game update is to rebuild the offset table from scratch. That's churn: it risks the offsets that were fine and buries the one real change in noise.

- **Run every sig.** `find_code_pattern` returning 0 is a miss — that sig needs a new pattern. A hit that resolves to valid data is fine; leave it untouched.
- **Verify the survivors didn't silently shift.** A sig can still hit while the *struct field* behind it moved. Spot-check resolved pointers with `struct_dump`.
- **Touch only the broken entries.** Re-sig the misses, update their resolved addresses, bump the version stamp, and log exactly what changed in a changelog. The diff should be the patch's actual damage, nothing more.

```
Post-patch checklist:
[ ] Ran all N sigs                          → 3 misses, N-3 hits
[ ] Hits resolve to valid data              → struct_dump spot-check OK
[ ] Re-sigged ONLY the 3 misses             → no churn on working entries
[ ] Bumped version stamp + changelog        → "Season 22: re-sigged entity_list,
                                               view_matrix, local_player"
```

**Why:** A surgical post-patch diff is reviewable and reversible — you can see precisely what the update moved. A full-table rewrite hides the signal, re-introduces transcription bugs into offsets that were already correct, and turns a 20-minute fix into a re-audit.

---

## 4. Trust Live Memory, Loop Until It Agrees

**Success is a sig that resolves to an address whose *live contents* match the expected layout. Loop until the three sources agree, and when they don't, the running process wins.**

The IDB, the SDK headers, and live memory are three views that drift apart. The IDB is a snapshot; the SDK may be an old season; only live memory is the truth right now.

- **Define done concretely:** "sig hits once, RIP resolves to an address, the bytes there `struct_dump` to the layout I expect."
- **Loop:** sig hit → resolve RIP-relative (4-byte signed displacement added to the *end* of the instruction) → read at the target → `struct_dump` / `print` → does it match the hypothesis? → if not, fix the sig or the resolution math and repeat.
- **Resolve RIP correctly or everything downstream is wrong:** `target = hit + instr_len + read_i32(hit + disp_offset)`. Off-by-one on the instruction length points you at the wrong global.
- **When the SDK says one offset and the live read says another, trust the live read** and update your notes. The header was written for a build that no longer exists.

```cpp
// The verify loop, made explicit
uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
if (hit == 0) { println("MISS — sig is stale, re-RE the load instruction"); return; }
int32 disp   = p.r32(hit + 3);          // displacement at LEA+3
uint64 target = hit + 7 + cast<uint64>(disp);  // end of 7-byte LEA + signed disp
uint64 list  = p.ru64(target);
println(format("entity_list global @ 0x{x} -> 0x{x}", target, list));
// struct_dump `list` and confirm it looks like a CEntityList before trusting it
```

**Why:** A sig that compiles into your script proves nothing. A sig that resolves to live memory matching your expected struct is the only evidence that the offset is real — and demanding that evidence is what separates a maintained offset table from a pile of hopeful constants.

---

## Summary

| # | Principle (Karpathy) | In RE terms |
|---|----------------------|-------------|
| 1 | Think Before Coding | Hypothesize + cite evidence before believing a field's meaning |
| 2 | Simplicity First | Shortest unique sig; wildcard only relocatable bytes |
| 3 | Surgical Changes | Post-patch: fix only the misses, never churn working offsets |
| 4 | Goal-Driven Execution | Done = sig resolves to live memory matching the expected layout |

---

## Source: `.claude/skills/pcx-perf-budget/SKILL.md`

---
name: pcx-perf-budget
description: >
  Turns the update/render separation rule into enforceable numeric budgets
  using mono_us() measurements. Covers per-frame targets at common refresh
  rates, per-call cost rules of thumb, a drop-in profiler recipe, and
  read-coalescing patterns. Always active when writing or reviewing
  performance-sensitive render or update routines.
license: MIT
---

# Performance Budget — Frame-Time Targets for PCX Scripts

Turns `game-cheat-guidelines` rule #4 (separate update from render) into enforceable numeric budgets, so the question "is my script too slow?" gets answered with `mono_us()` measurements instead of vibes. Covers per-frame targets at common refresh rates, per-call cost rules of thumb, the drop-in `profile_begin/end` recipe, and the read-coalescing patterns that produce the biggest wins.

**Always active when writing or reviewing performance-sensitive paths** (render routines, update routines, entity loops, pattern scans inside hot paths).

**Prerequisite:** `docs/enma/addon-time.md` for the timing primitives (`mono_us`, `now_us`, `sleep_ms`); `skill://game-cheat-guidelines` rules #4 (update/render separation) and #7 (per-frame construction).

---

## Trigger

Render stutter, FPS drop on overlay enable, "my script feels slow," profiling questions, write-up of per-feature performance, decisions about whether to cache or recompute, multi-routine scripts where update + render share a frame budget.

---

## 1. Know the Frame Budget at Your Target Refresh Rate

**The frame budget is the entire wall-clock window between two consecutive render calls. Everything — your update, your render, the game's own rendering, the GPU present — must fit inside it.**

Total frame budgets:

| Refresh | Budget per frame | PCX render budget (target) | PCX update budget (target) |
|---|---|---|---|
| 60 Hz | 16.67 ms | ≤ 2.0 ms | ≤ 4.0 ms |
| 120 Hz | 8.33 ms | ≤ 1.5 ms | ≤ 3.0 ms |
| 144 Hz | 6.94 ms | ≤ 1.5 ms | ≤ 2.5 ms |
| 240 Hz | 4.17 ms | ≤ 1.0 ms | ≤ 1.5 ms |
| 360 Hz | 2.78 ms | ≤ 0.7 ms | ≤ 1.0 ms |

The render budget is small because the game's own renderer + the GPU present + your overlay all share the frame. If your render path takes 5 ms at 144 Hz, you've eaten 72% of the frame by yourself, leaving 1.94 ms for the game's render — which causes the game to drop frames even though it would have hit 144 Hz without your overlay.

The update budget is more generous because, if you separate update from render properly (rule #4), update runs less frequently and on its own clock — it competes with the game less directly. But "less directly" is not "for free": a 10 ms update routine running at 60 Hz costs the same total CPU as a 2 ms render routine running at 144 Hz × 2.

**Heuristic:** measure once, then forget. If your script runs at the target FPS with no stutter on the lowest-spec machine you ship to, the budgets are met. If it stutters, instrument first (Step 3) before optimizing.

**Why:** Hard numeric targets prevent the "feels slow, must be fast" loop where you over-cache things that don't matter and miss the one routine that does. The render budget being tight is non-negotiable; the update budget is the negotiable lever — push work into update, off the render path, and most stutter disappears.

---

## 2. Per-Call Cost Rules of Thumb

**Order-of-magnitude costs for the operations you'll write most. Measure on your target; these are guides for *which order* of magnitude to expect, not contracts.**

| Operation | Cold (page-fault) | Warm (cached) | Notes |
|---|---|---|---|
| `proc.ru8/16/32/64` | 10-100 µs | 1-5 µs | Cold = first read of a page; warm = same page already touched this frame |
| `proc.rf32/rf64` | 10-100 µs | 1-5 µs | Same as integer reads — cost is the cross-process read, not the type |
| `proc.read_vec3_fl32` | 30-300 µs | 5-15 µs | One read of 12 bytes vs three separate reads |
| `proc.read_memory(N)` bulk | 30-500 µs depending on N | 10-100 µs | A single struct-dump is almost always cheaper than N scalar reads |
| `proc.find_code_pattern` | 5-200 ms first scan | N/A | Cold path only — never in update/render. Run in `main()` and cache. |
| `is_key_pressed` / `is_key_down` | < 1 µs | < 1 µs | Cheap; fine in hot paths |
| `draw_rect` / `draw_line` / `draw_circle` | 1-10 µs | 1-10 µs | Cost dominated by GPU command submission, not CPU |
| `draw_text` | 5-50 µs | 5-50 µs | Per-glyph atlas lookup + GPU submission; longer strings cost more |
| `world_to_screen` (pure math) | 1-5 µs | 1-5 µs | When matrix is cached; if you re-read the matrix per call, add a `read_memory` cost |
| GUI widget query (`section_*` reads) | < 1 µs | < 1 µs | Reading widget state is a local memory access |
| `now_us` / `mono_us` | < 0.5 µs | < 0.5 µs | Cheap; safe to call multiple times per frame for profiling |

**The implication:** a render path that does 50 entity boxes with one `read_vec3_fl32` per entity inside the render routine costs `50 × 5-15 µs = 0.25-0.75 ms` *if* the entity pages are warm. Cold-cache, it could be `50 × 30-300 µs = 1.5-15 ms` — already over the render budget at 144 Hz on the high end. Solution: move the reads to update (cache the cold-page cost there), draw from the cache.

**Why:** The single most important number to internalize is that cross-process memory reads are *very expensive* relative to draws and math. A NOP loop running 1000 iterations costs nothing; 1000 `ru32` calls can be 30 ms. Every performance problem in a PCX script is either too many reads or reads on the wrong thread.

---

## 3. The `profile_begin/end` Drop-In Recipe

**A minimal inline profiler with no new modules, no allocation, no rebuilds. Drop into any script, get per-routine breakdowns in console or on screen.**

The pattern uses `mono_us()` (monotonic; safe for deltas) and a small fixed-size accumulator. No `map` needed — name your buckets explicitly.

```cpp
import "vec";
import "color";

// ── Profile state — tiny fixed accumulator ──
const int32 NUM_BUCKETS = 8;
string  g_bucket_name[8];        // initialized once
int64   g_bucket_total_us[8];    // accumulated microseconds
int64   g_bucket_count[8];       // number of samples
int64   g_bucket_max_us[8];      // worst single sample
int64   g_profile_last_dump = 0;
int64   g_profile_dump_interval_us = 1000000;  // dump every second

// Push/pop pattern — name maps to bucket index 0..NUM_BUCKETS-1
int64 g_bucket_start_us[8];

void profile_begin(int32 bucket) {
    g_bucket_start_us[bucket] = mono_us();
}

void profile_end(int32 bucket) {
    int64 dur = mono_us() - g_bucket_start_us[bucket];
    g_bucket_total_us[bucket] += dur;
    g_bucket_count[bucket]    += 1;
    if (dur > g_bucket_max_us[bucket]) {
        g_bucket_max_us[bucket] = dur;
    }
}

// Call once per frame from render — prints once per second
void profile_dump_if_due() {
    int64 now = mono_us();
    if (now - g_profile_last_dump < g_profile_dump_interval_us) return;
    g_profile_last_dump = now;

    println("── PROFILE ──");
    for (int32 i = 0; i < NUM_BUCKETS; i++) {
        if (g_bucket_count[i] == 0) continue;
        int64 avg = g_bucket_total_us[i] / g_bucket_count[i];
        println(format("  {s}: avg {d}us  max {d}us  ({d} samples)",
                       g_bucket_name[i], avg, g_bucket_max_us[i], g_bucket_count[i]));
        // Reset for next window
        g_bucket_total_us[i] = 0;
        g_bucket_count[i]    = 0;
        g_bucket_max_us[i]   = 0;
    }
}

// Bucket assignments (give them stable indices)
const int32 BKT_UPDATE_ENTITIES = 0;
const int32 BKT_RESOLVE_OFFSETS = 1;
const int32 BKT_RENDER_ESP      = 2;
const int32 BKT_RENDER_HUD      = 3;

int64 main() {
    g_bucket_name[BKT_UPDATE_ENTITIES] = "update_entities";
    g_bucket_name[BKT_RESOLVE_OFFSETS] = "resolve_offsets";
    g_bucket_name[BKT_RENDER_ESP]      = "render_esp";
    g_bucket_name[BKT_RENDER_HUD]      = "render_hud";
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

void on_update(int64 data) {
    profile_begin(BKT_UPDATE_ENTITIES);
    // ... entity read loop ...
    profile_end(BKT_UPDATE_ENTITIES);
}

void on_render(int64 data) {
    profile_begin(BKT_RENDER_ESP);
    // ... ESP draws ...
    profile_end(BKT_RENDER_ESP);

    profile_begin(BKT_RENDER_HUD);
    // ... HUD draws ...
    profile_end(BKT_RENDER_HUD);

    profile_dump_if_due();
}
```

Sample output after one second:

```
── PROFILE ──
  update_entities: avg 1840us  max 4200us  (12 samples)
  render_esp:      avg 320us   max 510us   (144 samples)
  render_hud:      avg 45us    max 80us    (144 samples)
```

Interpretation:
- `update_entities` averages 1.84 ms — fine, well under the 2.5 ms update budget at 144 Hz
- But `max 4200us` is the spike to watch — a single 4.2 ms update *will* be visible if it lands on a render frame; this is the cold-page cost
- `render_esp` at 0.32 ms is healthy; `render_hud` at 45 µs is excellent

**Why:** Real numbers replace arguments. Without a profiler, every conversation about "is this fast enough" devolves into hand-wave. With one, you point at the bucket and either fix it or move on. The `max` column is more useful than the average — averages hide spikes that cause user-visible stutter.

---

## 4. Read Coalescing — The Single Biggest Win

**Cross-process memory reads dominate cost. Bundling 8 scalar reads from the same struct into one `read_memory` call is typically 5-10× faster.**

The entity loop is the canonical offender. Eight reads per entity, fifty entities = 400 cross-process reads per update. With page-warm reads at 3 µs each, that's 1.2 ms; cold, it's tens of ms.

```cpp
// SLOW — 8 reads per entity, each a separate kernel transition
void on_update(int64 data) {
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;
        g_cache[i].health    = g_proc.r32(ent + OFFSET_HEALTH);
        g_cache[i].team      = g_proc.r32(ent + OFFSET_TEAM);
        g_cache[i].position  = g_proc.read_vec3_fl32(ent + OFFSET_POSITION);
        g_cache[i].velocity  = g_proc.read_vec3_fl32(ent + OFFSET_VELOCITY);
        g_cache[i].view_yaw  = g_proc.rf32(ent + OFFSET_VIEW_YAW);
        g_cache[i].view_pit  = g_proc.rf32(ent + OFFSET_VIEW_PITCH);
    }
}

// FAST — one read per entity into a fixed buffer, parse in-script
struct entity_struct_layout {
    // Layout reflects the bytes at the entity base — adjust for your target.
    // Use [[packed]] if you depend on no padding.
} [[packed]];

void on_update(int64 data) {
    array<uint8> buf;
    buf.resize(0x200);                               // sized to span all fields you read

    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;

        // ONE read covering the whole entity record — single kernel transition
        if (!g_proc.read_memory(ent, buf, 0x200)) continue;

        // Parse from the local buffer — pure memory math, ~10x cheaper
        g_cache[i].health   = buf_read_i32(buf, OFFSET_HEALTH);
        g_cache[i].team     = buf_read_i32(buf, OFFSET_TEAM);
        g_cache[i].position = buf_read_vec3(buf, OFFSET_POSITION);
        g_cache[i].velocity = buf_read_vec3(buf, OFFSET_VELOCITY);
        g_cache[i].view_yaw = buf_read_f32(buf, OFFSET_VIEW_YAW);
        g_cache[i].view_pit = buf_read_f32(buf, OFFSET_VIEW_PITCH);
    }
}
```

Order of optimization (high impact to low):

1. **Coalesce per-entity scalar reads into struct-dumps.** Biggest single win for entity loops.
2. **Cache the view matrix once per update, share across entities.** Currently common to re-read per W2S call.
3. **Skip cold entities.** Read just the alive/team field first; if dead or friendly, skip the rest of the read.
4. **Bound entity counts.** A `MAX_ENTITIES = 64` cap on a list that's structurally bounded at 128 saves half the reads if many slots are empty.

**Why:** Cross-process reads are the dominant cost in any non-trivial script. A read-coalescing pass typically halves total CPU time of an entity-heavy script. The cost of structuring the read is a one-time `resize` and a handful of byte-offset getters — trivial relative to the win.

---

## 5. Cache What's Expensive to Get, Recompute What's Cheap

**Pattern scans, module bases, view matrix (across many entities) — cache. Colors, vec2s, format strings, font handles — recompute. Caching cheap things adds state without measurable savings.**

| Cache | Recompute |
|---|---|
| Pattern scan results (in `main()`, never again) | `color(r,g,b,a)` (4 bytes, stack-allocated, zero cost) |
| Module base / module size (until process re-attach) | `vec2(x, y)` (8 bytes, stack-allocated) |
| Resolved RIP addresses (until reload) | `get_font20()` (returns a cached handle internally) |
| View matrix once per update (shared across all W2S in this frame) | `format("{d}", n)` for short HUD text |
| Entity data in `g_cache` (the whole point of update/render separation) | World-to-screen result (it's just float math; do it where you need it) |
| Local player position once per frame (read in update, used by N features) | `is_key_down(VK_F)` (a cheap intrinsic; safe per-frame) |

Anti-cache (don't):

```cpp
// WRONG — caching a color "for performance"
color g_white;  // global state for zero gain
int64 main() {
    g_white = color(255, 255, 255, 255);
    return 1;
}

// RIGHT — construct fresh, no globals
void on_render(int64 data) {
    draw_text("HUD", vec2(10.0, 10.0), color(255, 255, 255, 255),
              get_font20(), 1, color(0, 0, 0, 180), 1.0);
}
```

Pro-cache:

```cpp
// View matrix — read once per update, reuse across N entities per render
float64 g_matrix[16];

void on_update(int64 data) {
    // 16 floats = 64 bytes in one read
    g_proc.read_memory(g_view_matrix_addr, g_matrix_buf, 64);
    // ... parse into g_matrix[16] ...
}

void on_render(int64 data) {
    for (int32 i = 0; i < g_entity_count; i++) {
        vec2 screen;
        if (world_to_screen(g_cache[i].position, g_matrix, screen)) {
            draw_circle(screen, 4.0, color(255, 0, 0, 255), 1.0, true);
        }
    }
}
```

**Why:** Caching cheap things makes the script harder to reason about (mutable globals, lifetime questions) for zero performance benefit. Caching expensive things (or things on cold paths) is the explicit purpose of rule #4 (update/render separation) — the whole point of "do it in update" is that the result lives until next update. Use that mechanism for what it's for; don't extend it to things that don't need it.

---

## 6. When to Break the Rule

**The budgets are steady-state targets. Bursts are fine. Don't split a one-frame initialization across ten frames to "meet budget" — the user-visible cost is the same and the code is worse.**

Legitimate bursts:

- **Initial process attach and sig resolution** in `main()` — can take 10-50 ms total, runs once, before the user starts using the overlay. Don't split.
- **First-frame entity cache fill** after a level load — a one-frame 5 ms spike that lets every subsequent frame run at 0.5 ms. Worth it.
- **Patch-day re-resolution** if you detect base address changed mid-session — let it stutter once.
- **Config save** on `on_unload` — file I/O takes ms; doesn't matter, the script is exiting.

Illegitimate bursts (these you DO need to fix):

- A pattern scan in a *callback* that fires periodically (should be in `main`)
- A `find_string_refs` or `struct_dump` call on the render thread (cold paths only)
- Allocating a 4 KB array inside `on_render` every frame (move to global, reuse the buffer)
- Calling `is_valid_address` on every pointer in a chain on every frame (validate at update time, cache the bool)

The test: if the user could feel the cost as a one-frame stutter, is it acceptable? A 50 ms stutter at script load is invisible (the overlay just appears 50 ms later). A 50 ms stutter mid-game is felt as a hitch.

**Why:** Performance work that makes the code uglier without changing the user-visible behavior is bad performance work. The framing of "everything must fit in 6.94 ms" applies to steady-state operation; setup, teardown, and event-driven one-shots get a pass. Save the optimization energy for the actual hot path.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | Know your budget | 16/8/7/4 ms at 60/120/144/240 Hz; render ≤ 1.5-2 ms, update ≤ 2.5-4 ms |
| 2 | Internalize per-call costs | Cross-process reads = expensive; draws and math = cheap |
| 3 | Profile with `mono_us` | Drop-in `profile_begin/end` with fixed buckets — measure before optimizing |
| 4 | Coalesce reads | One `read_memory` struct-dump replaces 8 scalar reads; biggest single win |
| 5 | Cache expensive, recompute cheap | Sigs, bases, matrix — yes; colors, vecs, fonts — no |
| 6 | Bursts are fine | Don't split one-shot setup across frames to "meet budget" |

**Cross-references:** `skill://game-cheat-guidelines` rules #4 and #7; `knowledge/common-patterns.md` for read-coalesced entity loops; `docs/enma/addon-time.md` for `mono_us` / `now_us`; `skill://pcx-patch-day-playbook` Step 5 (post-patch re-resolution that legitimately spends a frame budget).

---

## Source: `.claude/skills/pcx-patch-day-playbook/SKILL.md`

---
name: pcx-patch-day-playbook
description: >
  Ordered triage workflow for recovering a PCX script after a game update.
  Triggers when sigs return 0, reads return garbage after a patch, or the
  user says "broken", "updated", "patch day", "hotfix", "season drop", or
  "DLC dropped". Keeps diagnosis short and fixes targeted.
license: MIT
---

# Patch Day Playbook — Recovering After a Game Update

The ordered triage workflow for when a game update lands and your Perception.cx script stops working. This is the single most painful recurring scenario in scripting work; the cost is dominated by *not knowing what changed*, not by the re-RE itself. This playbook keeps the diagnosis short and the fix targeted.

**Trigger when:** the target game updated, sigs return 0, the script throws on first run after a patch, `ref_process().alive()` is fine but reads return garbage, or the user says any of: "broken", "updated", "patch day", "hotfix", "season drop", "DLC dropped".

**Prerequisite:** `knowledge/offset-methodology.md` for sig resolution mechanics, `tools/offset-diff.py` for batch sig diffing between binary versions, `tools/sig-uniqueness-checker.py` for re-sig validation. Also requires that you saved the previous-version binary and the working `offsets.em` *before* the update landed (see Step 1).

---

## Trigger

`.em` script suddenly throws on launch after a game update, overlay draws at (0,0), ESP renders no entities, sigs return 0, RIP-resolved addresses point outside the module, the user updates the game and runs the script and nothing works.

---

## 1. Snapshot the Broken State Before You Touch Anything

**Patch day is destructive. Save the old binary and old offsets before you do anything else. Diffing is impossible if you've already overwritten history.**

The single most common amateur mistake is "let me just update the offsets and see." Two hours later you can't remember what worked yesterday because everything is overwritten and the game's auto-updater wiped the old binary.

```
# Before any debugging — make a snapshot directory:
mkdir patch-2026-06-17

# 1. Copy the new game binary out (it's already on disk after the patch)
cp "C:/Games/MyGame/MyGame.exe" patch-2026-06-17/MyGame-new.exe

# 2. The OLD binary should already be in your previous snapshot dir.
#    If you don't have one, the lesson is: make one TODAY before the next patch.
#    The toolkit's `tools/offset-diff.py` needs both binaries to diff.

# 3. Save the last-known-good offsets:
cp scripts/offsets.em patch-2026-06-17/offsets-old.em

# 4. Save the broken script output for reference:
#    (in the IDE, copy the error trace; or run `check_script` and capture output)
```

**Why:** Without a snapshot, you're guessing what changed. With one, `offset-diff.py` and `radiff2` will tell you exactly which sigs moved, which are still valid, and which are gone. The 30 seconds of snapshotting saves the 2 hours of guesswork.

---

## 2. Run `tools/offset-diff.py` Before Editing Anything

**Most sigs survive a patch. You want to find the few that didn't — not re-do every one.**

The natural reflex is to open IDA on the new binary and start re-deriving offsets from scratch. Don't. The diff tool tells you in 30 seconds which sigs are intact, which moved (delta only — still resolvable), and which are gone (need re-sig).

```bash
# Build a JSON of named sigs once (reuse forever):
cat > sigs.json <<EOF
[
  {"name": "entity_list", "pattern": "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8", "kind": "rip", "rip_offset": 3, "insn_len": 7},
  {"name": "local_player", "pattern": "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 81", "kind": "rip", "rip_offset": 3, "insn_len": 7},
  {"name": "view_matrix",  "pattern": "48 8D 15 ?? ?? ?? ?? 48 8D 4C 24 ?? E8", "kind": "rip", "rip_offset": 3, "insn_len": 7}
]
EOF

# Diff:
python3 tools/offset-diff.py --old patch-old/MyGame.exe \
                              --new patch-new/MyGame.exe \
                              --sigs sigs.json
```

Read the output table top to bottom:

| Status | What it means | What to do |
|---|---|---|
| `UNCHANGED` | sig hits same address in both binaries | Nothing. Keep the offset. |
| `MOVED` | sig hits, but the resolved address differs (recompile shifted code) | Update the resolved address; sig itself is still good. |
| `LOST_IN_NEW` | sig hit old, doesn't hit new | Re-sig needed; instruction sequence changed. Go to Step 4. |
| `NEW_IN_NEW` | sig hit new but not old | Probably a typo in the old sig; ignore unless suspicious. |
| `MULTIPLE_HITS_OLD` / `MULTIPLE_HITS_NEW` | sig is ambiguous | Sig is too broad; tighten before trusting either result. Go to Step 4. |

**Why:** Triage before surgery. A patch typically moves 5-15% of sigs and breaks 1-3% outright. The diff tells you which 1-3% to spend the next hour on, instead of re-checking the 95% that survived.

---

## 3. Bisect the Cascade: Find the Earliest Failure, Not the Loudest

**A broken script after a patch shows ten errors. Nine of them are downstream of one bad pointer. Find the first one.**

Failure cascades trick you into chasing the wrong fix. The script log says "no entities drawn"; the actual cause is `g_entity_list = 0` because the *base address resolution* failed because the module name in the script changed (rare, but happens with engine version bumps). Fixing the entity-list sig won't help.

Bisect in dependency order:

```
1. Process attach   → ref_process("game.exe").alive() == true?
                      If false: process name changed? Anti-cheat blocking attach?
2. Base resolve     → get_module_base("game.exe") returns non-zero?
                      If 0: module renamed (e.g. CSGO → CS2 binary swap).
3. Module size      → get_module_size("game.exe") plausible (hundreds of MB)?
                      If wildly different: you're looking at the wrong binary.
4. First sig hit    → find_code_pattern returns non-zero for the FIRST sig you try?
                      If 0: the .text section may have moved (rare) or the binary
                      is encrypted/packed at runtime (e.g. Denuvo VM re-emergence).
5. RIP resolve      → resolved_addr is in [base, base+size]?
                      If outside: RIP math is wrong (Step 5).
6. Field reads      → ru64() on the resolved address returns non-zero?
                      If 0: pointer chain broken, struct layout changed.
```

Stop at the first failing step. Fix that. Re-run. Most of the cascade evaporates.

```cpp
// Tiny diagnostic harness — drop into main() temporarily:
int64 main() {
    proc_t p = ref_process("game.exe");
    if (!p.alive())                  { println("STEP 1 FAIL: process not attached"); return 0; }
    uint64 base = p.base_address();
    if (base == 0)                   { println("STEP 2 FAIL: no module base"); return 0; }
    uint64 size = p.get_module_size("game.exe");
    println(format("base={x} size={x}", base, size));

    uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0)                    { println("STEP 4 FAIL: entity_list sig stale"); return 0; }
    uint64 entity_list = resolve_rip(p, hit, 3, 7);
    if (entity_list < base || entity_list > base + size) {
        println(format("STEP 5 FAIL: rip resolve out of range: {x}", entity_list));
        return 0;
    }
    uint64 first = p.ru64(entity_list);
    println(format("first entity={x}", first));
    return 1;
}
```

**Why:** Without bisection you fix symptoms. You'll spend 30 minutes re-deriving an entity-list sig that was fine the whole time because the *real* failure was the module name. Bisection points the spotlight.

---

## 4. Re-Sig the Broken Ones with the Near-Miss Checker

**A sig that was unique yesterday may collide today, or vice versa. Don't trust your old sigs after a patch — validate.**

`tools/sig-uniqueness-checker.py` gives a verdict per sig: `UNIQUE`, `AMBIGUOUS`, `STALE`, `BRITTLE`. The `--near-misses N` flag is the killer feature on patch day — it scans for sigs whose first N bytes survive but trailing bytes drift, telling you exactly how to extend or narrow the wildcards.

```bash
# Verdict on every sig in your list:
python3 tools/sig-uniqueness-checker.py patch-new/MyGame.exe \
        --sig-file sigs.txt --near-misses 2

# Suppose this prints:
#   entity_list      UNIQUE      margin=5
#   local_player     STALE       near-miss: 48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 89
#                                           (last byte was 0x81, now 0x89 — struct offset shift)
#   view_matrix      AMBIGUOUS   3 hits — sig too broad; need 2-4 more bytes of context
```

For each broken sig:

1. **STALE with near-miss** → the instruction is still there but a register/offset byte changed. Update the sig (often a single byte) and retest.
2. **STALE with no near-miss** → the whole code path was rewritten. Go to the *xref* — find the function this sig was inside, find the new version in the patched binary by string xrefs or call patterns, derive a new sig from there.
3. **AMBIGUOUS** → tighten with 2-4 more bytes of leading or trailing context. Aim for `margin` between 2 and 6 — `margin=0` is brittle (one-byte change kills it), `margin>10` is overspecified (more likely to drift on the *next* patch).
4. **BRITTLE** (`margin=0`) → widen the sig until margin ≥ 2 even if the diff said it's fine — you got lucky this patch, you won't next time.

**Why:** Treating sigs as "either works or doesn't" misses the gradient. Most patch breakage is one-byte drift, which the near-miss check finds in seconds. Re-sigging from xrefs is the fallback when drift exceeds the threshold.

---

## 5. Re-Verify RIP-Relative Resolution After Every Sig Change

**Half of patch-day breakage is correct sig hits with wrong RIP math because the instruction length changed.**

A sig matching `48 8D 0D ?? ?? ?? ??` (7-byte `LEA rcx, [rip+disp]`) becomes `48 8B 0D ?? ?? ?? ??` (7-byte `MOV rcx, [rip+disp]`) — same length, same RIP math, fine. But a recompile can also turn a 7-byte `LEA r64, [rip+disp32]` into a 4-byte `LEA r64, [rip+disp8]` (small displacement form) — different length, different RIP math, your resolved address is now 3 bytes off. The script "works" but reads from the wrong location.

The check:

```cpp
// Always verify the resolved address lies inside the expected section.
// .text is executable code; data globals resolve to .data or .rdata.
uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
if (hit == 0) return 0;

int32 disp = p.r32(hit + 3);                  // displacement is 4 signed bytes
uint64 resolved = hit + 7 + cast<uint64>(disp); // 7 = total LEA instruction length

// Validation gate — if the resolved address points back into executable code,
// you almost certainly got the math wrong (most globals live in .data/.rdata):
if (resolved >= base && resolved < base + size) {
    // looks plausible; verify with a ru64 read and check the value shape
    uint64 first_field = p.ru64(resolved);
    println(format("resolved={x} first_field={x}", resolved, first_field));
} else {
    println(format("RIP resolve out of module: hit={x} disp={x} resolved={x}", hit, disp, resolved));
}
```

Patterns that change instruction length:

| From | To | Length delta | Common trigger |
|---|---|---|---|
| `LEA r64, [rip+disp32]` (7B) | `LEA r64, [rip+disp8]` (4B) | -3 | small-data global moved closer to code |
| `MOV r64, [rip+disp32]` (7B) | `MOV r64, mem` direct (10B) | +3 | global moved out of .rdata range |
| Standalone instruction | Instruction fused with prologue/epilogue change | varies | inliner heuristic changed in compiler |

**Why:** A wrong RIP math produces a perfectly plausible-looking address that's wrong by a small offset. Your reads return garbage that doesn't crash. You'll spend an hour blaming the struct layout for what's actually a 3-byte miscalculation in your resolver.

---

## 6. Validate End-to-End on the Live Target, Not Just "No Crash"

**Compile-clean is not the bar. Visible-correct on the live target is the bar.**

A script that doesn't crash and an overlay that draws *something* tells you almost nothing — every previous bug shipped the same way. Concrete validation:

```
End-to-end checklist after a patch fix:

[ ] Run the script on the live target (not a paused process)
[ ] Move the camera 90° — overlay tracks correctly?
[ ] Walk forward 10 meters — distance text updates plausibly?
[ ] Find a known entity (a teammate, a stationary object) — ESP box positioned over them?
[ ] Open the menu — every widget responds, no GUI freezes?
[ ] Run for 60 seconds without an exception — no late-binding errors?
[ ] Open the in-game scoreboard — entity count matches expected?
```

If you can't tick all seven, you're not done — keep bisecting.

**Why:** "It compiled" lulls you into the false sense of completion that costs you the next hour when a teammate reports the ESP is 50 pixels off. Five minutes of live verification on patch day is cheaper than any post-merge debugging.

---

## 7. Commit the Diff with a Changelog Note

**Every patch is data for the next patch. Record what moved, where it moved, and how you found it.**

A two-line note per patch turns into the most valuable file in your project after the third patch. It tells you which sigs are stable across patches (keep them), which drift every patch (rewrite from xrefs each time, don't bother updating in place), and which are version-tied (deprecate them entirely).

```
# patch-log.md
## 2026-06-17 — Game v1.42.3

### Moved
- view_matrix: +0x1C0 (recompile shift, sig still valid)
- local_player: +0x0 (no movement, listed for completeness)

### Re-sigged
- entity_list: old sig `48 8D 0D ?? ?? ?? ?? E8` matched at 3 places (ambiguous)
  new sig:     `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8` (margin=5)

### Lost — deprecated
- ammo_count: function inlined into shoot routine; not recoverable as a global,
              folded into per-weapon offset table

### Notes
- ETW Threat Intel callbacks (per anti-cheat-architecture.md) saw activity for
  the first time on this build — driver may have updated. Flag for review.
```

**Why:** Future-you needs this. The third patch when a sig regresses is when you'll discover that it's been brittle since v1.40 and you should rewrite it from xrefs once and for all instead of patching it again.

---

## Decision: When to Patch vs When to Re-RE from Scratch

Not every patch is a patch — sometimes the game shipped a real engine change and the old offsets are gone, not moved. Heuristics for when the playbook above doesn't apply and you need to start from `knowledge/offset-methodology.md` again:

| Signal | Likely cause | Action |
|---|---|---|
| Module name changed | Engine swap or major rebrand (CSGO → CS2) | Full re-RE; old offsets are reference-only |
| Module size changed >30% | Major engine update or large content drop with code refactor | Bisect aggressively; expect 30-50% sig loss |
| Most sigs `STALE` with no near-miss | Compiler upgrade (Clang version, LTO change) | Re-derive from xrefs; sigs based on RIP-relative globals usually survive better than register-allocation-sensitive ones |
| `IL2CPP` rebuild signal (Unity titles) | metadata.dat changed → entire struct layout rotated | Re-dump with IL2CPPDumper; use `tools/dumper-to-enma.py` to regenerate `offsets.em` |
| Schema system reset (Source 2 titles) | Schema registration order changed at runtime | Offsets are runtime-resolved; sigs for the schema getter are usually stable; revalidate the resolver, not the offsets |
| New anti-cheat driver loaded | AC vendor pushed an update | See `skill://anti-cheat-re` — driver behavior may have changed, not just code layout |

**The general rule:** if Steps 2-5 are fixing 70%+ of sigs with one-byte tweaks, you're in patch territory — keep going. If they're failing to find any near-misses for the broken sigs, you're in re-RE territory — close the playbook, open IDA, start over from the methodology.

---

## Summary

| # | Step | One-liner |
|---|---|---|
| 1 | Snapshot first | Save old binary, old offsets, error log before touching anything |
| 2 | Diff before editing | `offset-diff.py` triages which sigs survived, moved, lost |
| 3 | Bisect the cascade | Find the *first* failure, not the loudest |
| 4 | Re-sig with near-miss check | One-byte drift is the common case — find it in seconds |
| 5 | Re-verify RIP math | Instruction-length changes silently break resolved addresses |
| 6 | Live validation | Seven concrete in-game checks before declaring done |
| 7 | Patch log entry | Two lines per patch; the third patch will thank you |

**Decision:** if Steps 2-5 aren't recovering 70%+ of broken sigs, stop patching and re-RE from scratch via `knowledge/offset-methodology.md`.

**Cross-references:** `skill://pcx-re-discipline` (the rules of RE work), `knowledge/offset-methodology.md` (sig mechanics), `tools/offset-diff.py`, `tools/sig-uniqueness-checker.py`, `tools/dumper-to-enma.py` (for engines with structured dumpers).

---

## Source: `.claude/skills/re-evidence-log/SKILL.md`

---
name: re-evidence-log
description: >
  Discipline for recording why each offset and sig is trusted — the proof
  behind the offset table. Every offset added, every sig derived, every
  struct layout committed comes with a citable evidence entry. Always active
  during RE work; pairs with pcx-re-discipline and pcx-patch-day-playbook.
license: MIT
---

# RE Evidence Log — Every Claim Cites Its Proof

The discipline of recording *why* you trust each offset and sig in your project. The offset table is data; the evidence log is the proof behind it. Without the log, every patch day starts from zero on the same offsets you derived three months ago — you remember roughly what you did, not the citations that let you confirm it. This skill is the artifact half of `pcx-re-discipline` (which is the discipline itself) and the input to `pcx-patch-day-playbook` Step 7 (which writes a per-patch entry into the log).

**Always active when doing RE work.** Every offset you add, every sig you derive, every struct layout you commit to the project comes with an evidence entry. The cost is one paragraph per claim; the payoff is being able to answer "why do we trust this?" three months later without re-reversing.

**Prerequisite:** `skill://pcx-re-discipline` for the underlying discipline rules; `knowledge/offset-methodology.md` for the sig-derivation mechanics the log entries reference; `tools/sig-uniqueness-checker.py` for the verdict you record alongside each sig.

---

## Trigger

Starting RE work on a new binary, adding an offset to `offsets.em`, committing a struct layout to a feature, recovering from a patch (the patch-day skill produces a log entry), onboarding a teammate to existing offsets, code-review of RE claims, suspicious behavior in a script you wrote weeks ago and can't remember why a field is at +0x40.

---

## 1. One File per Binary, One Entry per Claim

**The canonical layout: `evidence/<binary-hash-prefix>.md`, one file per binary you reverse, one numbered entry per claim.** Filed by content hash, not by game name or version — the same game across patches produces different binaries with different hashes; each gets its own file.

```
project/
├── globals.em
├── offsets.em
├── ...
└── evidence/
    ├── README.md                          ← what's in here, naming convention
    ├── 7a3f4d1c-game-v1.42.3.md           ← per-binary log
    ├── 7a3f4d1c-game-v1.42.3.sha256       ← cached hash for trivial verification
    ├── 9b2e8a07-game-v1.42.4.md           ← next patch = new file
    └── archive/                           ← old entries kept for diffing
        └── 7a3f4d1c-game-v1.42.3.md
```

Inside one file, each claim is its own section:

```markdown
# Evidence Log — game.exe v1.42.3
SHA-256: 7a3f4d1c8e2b5a019f3d4c7e2b1a8f6d...
Module size: 158,720,000 bytes (.text 0x00400000–0x00C12000)
First verified: 2026-06-15
Last verified: 2026-06-17

## E-001 — entity_list global pointer
## E-002 — local_player slot
## E-003 — view matrix (4x4 row-major)
## E-004 — CEntity::m_iHealth field offset
## E-005 — CEntity::m_vecOrigin field offset
...
```

Entry IDs (`E-001` … `E-NNN`) are stable across patches — `offsets.em` references them in comments (`// E-003`), so when you rewrite the offset for the next version, you keep the same ID and update the per-version file. The ID is the cross-reference; the file is the version-specific evidence.

**Why:** Without a per-binary file, you can't diff what changed between patches. Without numbered entries, you can't reference a claim from your code or a teammate's review. The file naming by hash means the system survives renames, re-downloads, and side-by-side comparison.

---

## 2. Every Claim Cites: Binary, Address, Xref Source, Last-Verified Date

**The minimum citation per entry. Anything shorter is a vague memory dressed up as a fact.**

The required fields per entry:

| Field | Why |
|---|---|
| `id` | Stable cross-reference for `offsets.em` and patch logs |
| `name` | Human-readable label (matches the constant in `offsets.em`) |
| `binary_hash` | The binary this claim is verified against |
| `rva` (or `sig`) | Where the thing is |
| `xref_source` | Function symbol, sig pattern, or string xref that found it |
| `derived_via` | How: pattern scan? SDK header lookup? Struct dump? |
| `last_verified` | Date of the most recent successful run on this binary |
| `verified_against` | The in-game observation that confirmed it works |

```markdown
## E-001 — entity_list global pointer

| Field             | Value |
|---|---|
| name              | `OFF_ENTITY_LIST` |
| kind              | RIP-relative pointer (loaded by LEA) |
| rva               | 0x04A2B100  (resolved from sig hit at 0x00872F40) |
| sig               | `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8` |
| sig_uniqueness    | UNIQUE (margin=5, per `tools/sig-uniqueness-checker.py`) |
| xref_source       | Called by `CGameWorld::Update`, identified via string xref "entity_list_full" |
| derived_via       | Pattern scan + RIP resolve (disp@+3, insn_len=7) |
| last_verified     | 2026-06-17 |
| verified_against  | ESP showed 12 entities in a match; entity count matched scoreboard |
```

WRONG — the kind of "evidence" that's actually nothing:

```markdown
## entity_list
Found in some function, +0x18 or +0x20, I think? Worked last time I checked.
```

This will cost you an hour the next time you touch it.

RIGHT — every field present, every claim verifiable:

```markdown
## E-001 — entity_list
hash 7a3f4d1c..., rva 0x04A2B100, sig "48 8D 0D ?? ...", from CGameWorld::Update,
verified 2026-06-17 against the scoreboard entity count.
```

The detail level is up to you — a table per entry or a single dense line — but the *fields* are mandatory.

**Why:** Three months from now, you will not remember which function you found this in. The patch-day playbook Step 4 (re-sig with near-miss) needs the original `derived_via` to know what the sig was trying to match. A teammate reviewing your offsets needs `xref_source` to know where to look themselves. The `last_verified` date is the brittleness signal (rule #5).

---

## 3. Sigs Cite the Disassembly They Were Derived From

**A sig alone is a number. A sig with its disassembly context is a hypothesis you can re-derive.** When the sig breaks, the disassembly tells you what the instruction *was*, so you can find what it *became* in the patched binary.

Format: the sig as a literal, then a small fenced block of the instructions it covers, then a one-line explanation of which bytes are wildcarded and why.

```markdown
## E-001 — entity_list (sig derivation)

sig: `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8`

Derived from (game.exe v1.42.3, at .text+0x00872F40):
    48 8D 0D 5B 80 1B 04       LEA  rcx, [rip+0x041B805B]   ; -> &g_entity_list
    E8 2A 4F 12 00             CALL CGameWorld::Lookup       ; ret in rax
    48 8B D8                   MOV  rbx, rax                 ; save list ptr

Wildcards:
  - bytes 3..6   (4-byte RIP disp32 in the LEA — relocatable)
  - bytes 8..11  (4-byte CALL target relative disp — relocatable)
Total signature length: 15 bytes.
Unique-match verdict at derivation time: UNIQUE (margin=5).
```

When this sig later returns 0 after a patch, you have *exactly* what to look for in the new binary: a `LEA rcx, [rip+disp]` immediately followed by a `CALL` and `MOV rbx, rax`, near the same string xref ("entity_list_full") that originally led you here.

**Why:** A bare hex string strips out everything you knew when you wrote it. The disassembly preserves the *intent*: this is the LEA that loads the entity-list pointer into RCX, called immediately. If the compiler changed `MOV` to `LEA` in the patch (different opcode, different sig), you still know what to look for.

---

## 4. Struct Layouts Cite SDK Header AND In-Memory Verification

**Most struct layouts are partially known: some fields come from a community SDK header, others from your own struct dumping, others from guessing. Flag which are which.**

When a struct layout is wrong, the bug is silent — your script reads garbage that doesn't crash. The cost of being wrong is high; the cost of citing your source per field is two lines.

```markdown
## E-004 — CEntity struct layout (partial)

source: `r5sdk/include/game/server/entity.h` (commit 8a4c2e7, fetched 2026-06-10)
in-memory verification: 2026-06-17, walked g_entity_list[0..3] in a live match

| offset  | size | field         | source              | confidence |
|---------|------|---------------|---------------------|------------|
| 0x0000  | 8    | vtable_ptr    | SDK header          | HIGH       |
| 0x0008  | 4    | netvar_id     | SDK header          | HIGH       |
| 0x0040  | 4    | m_iHealth     | SDK header          | HIGH       |
| 0x0044  | 4    | m_iMaxHealth  | SDK header          | HIGH       |
| 0x00F0  | 4    | m_iTeamNum    | SDK header          | HIGH       |
| 0x0170  | 12   | m_vecOrigin   | SDK header          | HIGH       |
| 0x017C  | 12   | m_vecVelocity | OBSERVED (struct dump, three entities, values match expected ranges) | MEDIUM |
| 0x0188  | 4    | m_flAimYaw    | GUESS (correlated with on-screen view direction) | LOW |
| 0x1234  | 8    | m_pPlayerCtl  | GUESS (looks like a pointer; value is within module range) | LOW |
```

Three confidence tiers, three response policies:

- `HIGH` — SDK-cited or directly observed. Use without ceremony.
- `MEDIUM` — observed but not SDK-confirmed. Flag in `offsets.em` with a one-line comment.
- `LOW` — guess. Mark `UNVERIFIED` per `game-cheat-guidelines` rule #1. Treat reads as suspect; cross-validate (e.g. compare the supposed `m_flAimYaw` against the on-screen view direction over 100 frames before trusting it).

When code-reviewing, the question "where did you get this field?" is answered by looking at the table.

**Why:** Partial-layout bugs are the worst class of RE error. The script "works" — it draws ESP, it reads health, it pulls coords — but one field is wrong and the feature using that field silently produces garbage. Marking confidence per field makes the wrong-field call inspectable instead of invisible.

---

## 5. Update the Verified-On Date After Every Successful Run

**The age of the last verification is the brittleness signal. A sig last verified six months ago is more suspect than one verified yesterday, even if both are technically "in the log."**

The discipline: at the end of any session where the script ran correctly against the live target, walk through the log and bump `last_verified` for every claim that was actually exercised. Five seconds of editing per session.

```markdown
## E-001 — entity_list
last_verified: 2026-06-17  ← yesterday, fresh
last_verified: 2026-04-02  ← two months old, recheck before trusting
last_verified: 2025-12-15  ← six months — assume stale; revalidate or re-derive
```

At code-review time or before a release, sort entries by age:

```bash
# rough one-liner — adapt to your log format
grep -E '^last_verified:' evidence/*.md | sort -k2 | head -10
```

The oldest entries are the next ones to verify (or retire if they're no longer used by any feature).

A second related discipline: when you add a NEW claim, also list which claims it *depends on*. If E-006 is "`CEntity::m_pPlayer` reads `CPlayer` at the pointed address" and `CPlayer`'s layout is E-007, then E-006's evidence cites "depends on E-007." When E-007 becomes stale, the dependent claim is suspect too.

**Why:** Without freshness tracking, every entry has the same epistemic weight, which is wrong. A six-month-old "I verified this once" is closer to a guess than to fresh evidence. Dating gives you a triage signal for free, the cost of which is one date edit per session.

---

## 6. Cite Negative Results Too

**"Tried sig X, returned 0; tried sig Y, returned 3 hits; settled on sig Z" is data. Future-you debugging a regression needs to know what's *already been ruled out*.**

Most evidence logs record only the *successful* derivation. The next time the sig breaks and you reach for one of the *other* candidates you ruled out months ago, you'll re-rule it out again — costing the same hour.

Format: under each entry, a brief "Considered and rejected" subsection.

```markdown
## E-001 — entity_list

[main entry as above]

### Considered and rejected
- Sig `48 8B 0D ?? ?? ?? ??` (just the MOV form): too short, matched 47 places in .text.
- Hardcoded offset 0x04A2B100: that's the resolved address from THIS binary; will not
  survive a patch. Kept as the resolved value but the sig is the canonical source.
- Walking from `CGameWorld::Init` (xref candidate): the init function is in .data
  and gets re-inlined per build; brittle xref starting point.
- Reading PEB.LdrData to find a "game module" data segment: technically possible
  but adds a per-frame cost we don't want.
```

The same pattern applies to struct layout dead-ends ("field at +0x180 looked like a vec3 origin but the values were screen-space coords, not world; it's actually the last frame's m_vecOldPosition") and to struct-walking dead-ends ("the second pointer in this list is null in solo play; only populated in team modes — don't use as a liveness check").

**Why:** Negative results are the second-most-valuable thing in the log after positive ones. A teammate looking at this log can immediately see "ah, the obvious short sig is ambiguous — that's why we have a long one." The cost of recording is one line; the cost of not recording is rediscovery.

---

## Template

Drop-in skeleton for `evidence/<hash>.md` — copy, fill in:

```markdown
# Evidence Log — <binary_name> <version>

SHA-256: <full hash>
Module size: <bytes>  (.text <start>–<end>)
First verified: <YYYY-MM-DD>
Last verified: <YYYY-MM-DD>

Cross-reference: this file lists entries E-001..E-NNN; each entry's ID is
stable across patches and is referenced from `offsets.em` and `patch-log.md`.

---

## E-001 — <short name matching offsets.em constant>

| Field             | Value |
|---|---|
| name              | `OFF_X` |
| kind              | <RIP-relative pointer / direct address / field offset / sig> |
| rva               | <0x...> (resolved from sig hit at <0x...>) |
| sig               | `<bytes>` |
| sig_uniqueness    | <UNIQUE margin=N / AMBIGUOUS / etc per sig-uniqueness-checker.py> |
| xref_source       | <function, string xref, or other anchor> |
| derived_via       | <pattern scan + RIP resolve / SDK header / struct dump / xref walk> |
| last_verified     | <YYYY-MM-DD> |
| verified_against  | <in-game observation that confirmed it works> |
| depends_on        | <E-NNN, E-NNN — or "none"> |

Disassembly context (for sigs):
    <4-6 lines of asm covering the matched bytes; wildcards explained below>

Wildcards:
  - bytes A..B  (<what relocatable thing they cover>)

### Considered and rejected
- <alternative sig / approach / source>: <why it didn't pan out>

---

## E-002 — ...
```

A second template for struct entries:

```markdown
## E-NNN — <StructName> layout (<partial|complete>)

source: <SDK header path or "self-derived">
in-memory verification: <date>, <how many instances walked>

| offset | size | field | source | confidence |
|--------|------|-------|--------|------------|
| 0x0000 | 8    | vtable_ptr | SDK / observed | HIGH |
| ...    |      |       |        |            |

### Considered and rejected
- <field-shape alternative>: <why rejected>
```

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | One file per binary, one entry per claim | Stable IDs (E-NNN) cross-reference `offsets.em` and patch logs |
| 2 | Cite binary + address + xref + date | Six fields mandatory per entry; vague memory is not evidence |
| 3 | Sigs cite their disassembly | The intent of the sig is the hypothesis you re-derive from |
| 4 | Structs cite source + verification per field | HIGH / MEDIUM / LOW confidence tiers; LOW = `UNVERIFIED` in code |
| 5 | Update `last_verified` per successful run | Age is the brittleness signal — six months old is suspect |
| 6 | Cite negative results too | "Tried and rejected" prevents the next person re-deriving the same dead end |

**Cross-references:** `skill://pcx-re-discipline` (the discipline rules), `skill://pcx-patch-day-playbook` (Step 7 writes a per-patch log entry), `knowledge/offset-methodology.md` (the mechanics being cited), `tools/sig-uniqueness-checker.py` (produces the `sig_uniqueness` field value), `tools/offset-diff.py` (per-patch diff feeds the negative-results section).

---

## Source: `knowledge/pcx-api-cheatsheet.md`

# Perception.cx Enma API Quick Reference

All natives are auto-registered. No import needed (except `import "vec"; import "color";` for those types).

## Proc API — Process Memory

```cpp
proc_t p = ref_process("game.exe");       // by name
proc_t p = ref_process(1234);              // by PID
bool alive = p.alive();
uint64 base = p.base_address();
uint64 peb  = p.peb();
uint32 pid  = p.pid();
bool valid  = p.is_valid_address(addr);
```

### Read Primitives
```cpp
uint8/16/32/64  p.ru8/ru16/ru32/ru64(uint64 addr);
int8/16/32/64   p.r8/r16/r32/r64(uint64 addr);
float32         p.rf32(uint64 addr);
float64         p.rf64(uint64 addr);
string          p.rs(uint64 addr, int32 max_chars);    // ASCII
string          p.rws(uint64 addr, int32 max_chars);   // UTF-16→UTF-8
array<uint8>    p.rvm(uint64 addr, uint64 size);       // bulk
```

### Write Primitives (gated: `write_memory`)
```cpp
bool p.wu8/wu16/wu32/wu64(uint64 addr, uintN v);
bool p.w8/w16/w32/w64(uint64 addr, intN v);
bool p.wf32(uint64 addr, float32 v);
bool p.wf64(uint64 addr, float64 v);
bool p.wvm(uint64 addr, array<uint8> bytes);
```

### Typed Reads (vec/quat/mat)
```cpp
vec2 p.read_vec2_fl32(uint64 addr);     // also: _fl64 variant
vec3 p.read_vec3_fl32(uint64 addr);
vec4 p.read_vec4_fl32(uint64 addr);
quat p.read_quat_fl32(uint64 addr);
mat4 p.read_mat4_fl32(uint64 addr);
// write variants: p.write_vec3_fl32(addr, v), etc. (gated)
```

### Modules
```cpp
uint64                base = p.get_module_base("module.dll");
uint64                size = p.get_module_size("module.dll");
array<module_info_t>  mods = p.get_module_list();
uint64                exp  = p.get_proc_address(base, "ExportName");
uint64                imp  = p.get_import_rdata_address(base, "ImportName");
// module_info_t: .name(), .base(), .size()
```

### Pattern Scanning
```cpp
uint64 hit = p.find_code_pattern(start, size, "48 8B 05 ?? ?? ?? ?? 48 85 C0");
array<uint64> hits = p.find_all_code_patterns(start, size, sig);
```

### Memory Scanning
```cpp
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
array<uint64> p.scan_u64(value, heap_only);
array<uint64> p.scan_u32(value, heap_only);
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
```

### VAD / Virtual Query
```cpp
vad_region_t r = p.virtual_query(addr);       // .start(), .size(), .protection()
array<vad_region_t> snap = p.get_vad_snapshot(heap_only);
```

### VM Alloc/Free (gated: `virtual_memory_operations`)
```cpp
uint64 page = p.alloc_vm(4096);
bool ok = p.free_vm(page);
```

## Render API — 2D Drawing

```cpp
import "vec";
import "color";

// Primitives
draw_line(vec2 a, vec2 b, color c, float64 thickness);
draw_rect(vec2 pos, vec2 size, color c, float64 thickness, float64 rounding, uint8 flags);
draw_rect_filled(vec2 pos, vec2 size, color c, float64 rounding, uint8 flags);
draw_circle(vec2 center, float64 radius, color c, float64 thickness, bool filled);
draw_arc(vec2 center, vec2 radii, float64 start, float64 sweep, color c, float64 thick, bool filled);
draw_triangle(vec2 a, vec2 b, vec2 c, color col, float64 thickness, bool filled);
draw_text(string text, vec2 pos, color c, int64 font, int32 effect, color effect_c, float64 effect_amt);
draw_bitmap(int64 bmp, vec2 pos, vec2 size, color tint, bool rounded);

// effect: 0=none, 1=shadow, 2=outline
// rounding_flags: bitmask, 15=all corners

// Fonts
int64 get_font18(); int64 get_font20(); int64 get_font24(); int64 get_font28();
int64 create_font(string path, float64 size, bool aa, bool color, array ranges);
float64 get_text_width(int64 font, string text, int32 maxw, int32 maxh);
float64 get_text_height(int64 font, string text, int32 maxw, int32 maxh);

// Viewport
float64 get_view_width();  float64 get_view_height();
float64 get_view_scale();  float64 get_fps();

// Clipping
clip_push(vec2 pos, vec2 size); clip_pop();

// Shaders (layout: "POSITION:0:FLOAT2, COLOR:0:FLOAT4")
int64 create_shader(string vs, string ps, string layout);
int64 create_compute_shader(string cs);

// Buffers
int64 create_vertex_buffer(uint32 stride, uint32 max, bool dynamic);
int64 create_index_buffer(uint32 max, bool use32, bool dynamic);
int64 create_constant_buffer(uint32 size);
```

## GUI API — Sidebar Widgets

```cpp
int64 sec = create_section("Section Name");
section_checkbox(sec, "Label", bool_ref);
section_slider_float(sec, "Label", float_ref, min, max);
section_slider_int(sec, "Label", int_ref, min, max);
section_button(sec, "Label", callback_fn);
section_text_input(sec, "Label", string_ref);
section_keybind(sec, "Label", key_ref);
section_color_picker(sec, "Label", color_ref);
section_dropdown(sec, "Label", index_ref, items_array);
section_label(sec, "Text");
section_separator(sec);
```

## Input API

```cpp
bool key_down       (int64 vk);      // host-debounced down state
bool key_raw_down   (int64 vk);      // OS-level pressed state
bool key_fired      (int64 vk);      // up->down this frame (one-shot)
bool key_toggle     (int64 vk);      // caps-lock-style toggle
bool key_singlepress(int64 vk);      // fired but suppressed if modifiers held
bool key_prev_down  (int64 vk);      // down state from previous frame

key_state_t  get_key_state(int64 vk); // atomic snapshot of all 6 flags
array<int32> get_keys_down();         // virtual-key codes currently pressed
string       get_recent_key_input();  // buffered text input (UTF-8)
string       get_key_name(int64 vk);  // localized key name (e.g. "F1")

vec2 get_mouse_pos();                 // render-window pixels
vec2 get_mouse_pos_desktop();         // desktop pixels (full screen)
vec2 get_mouse_delta();               // raw movement this frame
vec2 get_mouse_delta_desktop();       // desktop-space delta this frame
bool mouse_movement_received();       // any movement this frame
bool is_hovered(vec2 pos, vec2 size); // mouse inside rect
float64 get_scroll_delta();           // wheel ticks; positive = up
```

## CPU API

```cpp
string get_cpu_vendor();
float64 time_ms();     // monotonic milliseconds
float64 time_us();     // monotonic microseconds
int32 get_datetime_year/month/day/hour/minute/second();
```

## Zydis API — x86-64 Disassembler/Assembler

```cpp
zydis_insn_t insn = zydis_decode(bytes_array, addr);
// insn.mnemonic, insn.length, insn.operands[]
array<uint8> encoded = zydis_encode(mnemonic, operands);
```

## Unicorn API — x86-64 Emulation

```cpp
int64 uc = uc_create();
uc_mem_map(uc, addr, size, perms);
uc_mem_write(uc, addr, bytes);
uc_reg_write(uc, reg_id, value);
uc_emu_start(uc, begin, until, timeout, count);
uint64 val = uc_reg_read(uc, reg_id);
array<uint8> data = uc_mem_read(uc, addr, size);
uc_destroy(uc);
```

## Net API

```cpp
string body = http_get(url, headers_map);
string body = http_post(url, post_body, headers_map);
int64 ws = ws_connect(url); ws_send(ws, msg); string r = ws_recv(ws);
int64 sock = udp_create(); udp_send(sock, host, port, data); udp_recv(sock, buf, timeout);
```

## Win API

```cpp
array<window_t> wins = enum_windows();
// window_t: .hwnd(), .title(), .class_name(), .pid(), .rect()
send_key(int32 vk, bool down);
send_mouse(int32 button, bool down, int32 x, int32 y);
string clip = get_clipboard(); set_clipboard(text);
```

## Filesystem API

```cpp
string content = read_file(path);
bool ok = write_file(path, content);
bool exists = file_exists(path);
array<string> entries = list_dir(path);
bool ok = create_dir(path);
bool ok = delete_file(path);
```

## Sound API

```cpp
int64 snd = load_sound(path);   // .wav or .ogg
play_sound(snd);
```

## Lifecycle

```cpp
int64 main() {
    // return > 0 to stay loaded, <= 0 to unload
    register_routine(cast<int64>(my_fn), user_data);
    return 1;
}
void my_fn(int64 data) { /* called every frame */ }
unregister_routine(handle);
```

---

# New API Additions (Feb–June 2026 Changelogs)

## Custom Draw API — Direct GPU Access (D3D11)

Full custom shader pipeline on the Universal API. Write HLSL, create vertex
buffers, textures, render targets, depth buffers, and draw any primitive
topology directly from AngelScript/Enma. Custom draw commands respect draw
order with every existing render function. All resources are tracked
per-script and auto-cleaned on unload.

### Resource Creation (all return `uint64` handle, `0` on failure)
```cpp
uint64 create_shader(string vs_source, string ps_source, string layout);
uint64 create_vertex_buffer(uint32 stride, uint32 max_vertices, bool dynamic);
uint64 create_index_buffer(uint32 max_indices, bool is_32bit, bool dynamic);
uint64 create_constant_buffer(uint32 size);
uint64 create_blend_state(src, dst, op, src_alpha, dst_alpha, op_alpha);
uint64 create_sampler(filter, address_u, address_v);
uint64 create_texture(uint32 width, uint32 height, array<uint8> rgba_data);
uint64 create_render_target(uint32 width, uint32 height);
uint64 create_depth_buffer(uint32 width, uint32 height);
uint64 create_depth_stencil_state(bool depth_enable, bool depth_write, int compare_func);
uint64 create_rasterizer_state(int fill_mode, int cull_mode);
```

### Drawing
```cpp
custom_draw(shader, vb, data, vertex_count, topology,
            blend, sampler, texture, rt, cb, cb_data, cb_slot);
custom_draw_indexed(shader, vb, vert_data, vert_stride,
                    ib, index_data, index_count, topology,
                    blend, sampler, texture, rt, cb, cb_data, cb_slot);
```

### Render Target Operations
```cpp
custom_set_render_target(rt);
custom_set_render_target_ext(rt, depth_buffer);
custom_clear_render_target(rt, r, g, b, a);
custom_clear_depth_buffer(db);
custom_resolve_render_target(rt);     // copy RT -> backbuffer
```

### State Management
```cpp
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs);
custom_set_viewport(x, y, w, h);                          // split-screen / PiP
custom_bind_textures(shader, slot0_tex, slot1_tex, ...);  // multi-texture
custom_bind_constant_buffers(shader, slot, cb, cb_data, cb_size);
```

### Mesh & Texture Loading
```cpp
load_obj_mesh(path);                  // returns vb + ib handles
create_texture_from_file(path);
create_dynamic_texture(width, height);
update_dynamic_texture(tex, rgba_data);
```

### Compute Shaders
```cpp
uint64 cs  = create_compute_shader(cs_source);
uint64 buf = create_structured_buffer(element_size, element_count, data);
dispatch_compute(cs, groups_x, groups_y, groups_z);
read_structured_buffer(buf);
```

### Backbuffer Capture
```cpp
uint64 tex = capture_backbuffer();    // texture handle of current frame
```

### Constants
```cpp
// Topology
TOPO_POINT_LIST, TOPO_LINE_LIST, TOPO_LINE_STRIP,
TOPO_TRIANGLE_LIST, TOPO_TRIANGLE_STRIP

// Compare funcs (depth stencil)
CMP_NEVER, CMP_LESS, CMP_EQUAL, CMP_LESS_EQUAL,
CMP_GREATER, CMP_NOT_EQUAL, CMP_GREATER_EQUAL, CMP_ALWAYS

// Fill modes
FILL_WIREFRAME, FILL_SOLID

// Cull modes
CULL_NONE, CULL_FRONT, CULL_BACK
```

### Layout String Format
Comma-separated `SEMANTIC:slot:TYPE` entries, e.g.
`"POSITION:0:FLOAT2, COLOR:0:FLOAT4"`.

### Key Features
- Indexed rendering with 16-bit and 32-bit index formats
- True 3D depth testing with configurable depth-stencil state
- Rasterizer state control (culling, wireframe)
- Custom viewports for split-screen / picture-in-picture
- Multi-texture and multi-constant-buffer binding
- Compute shaders with structured buffers
- OBJ mesh loading + dynamic texture updates
- Depth-enabled render targets, backbuffer capture for post-processing

### Example: Basic Colored Triangle
```angelscript
string vs = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj);
    o.col = i.col;
    return o;
}
""";

string ps = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

uint64 shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
uint64 vb = create_vertex_buffer(24, 3, true);
uint64 blend = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
```

### Example: Depth-Tested 3D Scene
```angelscript
uint64 db = create_depth_buffer(400, 300);
uint64 ds = create_depth_stencil_state(true, true, CMP_LESS);

custom_set_render_target_ext(rt, db);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
```

## World-to-Screen (updated Feb 2026)

```cpp
bool world_to_screen_rowmajor(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
bool world_to_screen_transposed(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
```
- Use `world_to_screen_rowmajor` for row-major view matrices.
- Use `world_to_screen_transposed` for transposed (column-major) matrices.
- ⚠️ **DEPRECATED:** `source2_world_to_screen` — replace with the variants above.

## Matrix4x4 Double Precision (Feb 2026)

```cpp
mat4 m.readas_float(uint64 addr);      // float-precision read
mat4 m.readas_double(uint64 addr);     // double-precision read
bool m.writeas_float(uint64 addr, mat4 v);
bool m.writeas_double(uint64 addr, mat4 v);
```
- ⚠️ **DEPRECATED:** default `matrix4x4` read/write — use a precision-specific variant.

## Thread Priority Helpers (Feb 2026)

```cpp
set_thread_to_highest_priority();
set_thread_to_lowest_priority();
set_thread_to_normal_priority();
```

## Atomics (Feb 2026)

```cpp
atomic_int32 a;    // lock-free thread-safe 32-bit integer
atomic_int64 b;    // lock-free thread-safe 64-bit integer
```

## GUI Additions (Feb–Mar 2026)

```cpp
get_gui_position(float &out x, float &out y);   // GUI window position
get_gui_size(float &out w, float &out h);       // GUI window size

// List widget ops
list:get(...);              list:remove(...);
list:highlight(...);        list:remove_highlight(...);
list:hide(...);             list:show(...);
```

## Callbacks (Mar 2026)

```cpp
register_callback(string name, func, bool render_on_top = false);
// render_on_top=true renders on top of everything else
```

## Window Additions (Feb 2026)

```cpp
array<uint64> hwnds = get_all_hwnds();   // all window handles
```

## Fonts (Feb 2026)

```cpp
int64 create_font(string name, float64 size, array glyph_ranges);       // glyph_ranges optional
int64 create_font_mem(array<uint8> data, float64 size, array glyph_ranges); // glyph_ranges optional
```

## Input Additions (Feb 2026)

- Controller keybinds via **XINPUT** now supported.
- `get_mouse_delta()` now returns proper movement delta (fixed).

## Unicorn Emulator Updates (Mar 2026)

```cpp
// New hook types
UC_HOOK_INSN_INVALID    // invalid instructions
UC_HOOK_INTR            // software interrupts (INT3, syscalls)

uint64 status = uc_get_last_exception(uc);     // NTSTATUS, e.g. 0xC0000005
uint64 rip    = uc_get_exception_address(uc);  // RIP where exception occurred
```
- Null pointer access is now caught gracefully instead of crashing.

## Sound API — Full Audio Engine (Mar 2026)

44100Hz stereo, up to 64 simultaneous instances. WAV (PCM 8/16-bit) parsed
directly; MP3/AAC/WMA/FLAC decoded via Media Foundation. Auto-cleanup on
script unload.

```cpp
int64 snd = load_sound(path);
free_sound(snd);
play_sound(snd, bool loop);
stop_sound(snd);
stop_all_sounds();
set_sound_volume(snd, float vol);   // 0.0 – 1.0
set_sound_pan(snd, float pan);      // -1.0 (L) – +1.0 (R)
```

## Scan API Updates (Mar 2026)

Scan functions now return `array<uint64>@` directly (no `&out` params).
The `get_vad_snapshot` regression is fixed and returns proper values.

```cpp
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
```
- ⚠️ **REMOVED (never existed):** `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64`.

## Deprecated Functions Summary

| Deprecated | Replacement |
|---|---|
| `source2_world_to_screen` | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| default `matrix4x4` read/write | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` |
| `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64` | removed — use `scan_float` / `scan_double` / `scan_string` / `scan_wstring` / `scan_pointer` |

---

## Source: `knowledge/enma-cheatsheet.md`

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

---

## Source: `knowledge/common-patterns.md`

# Common Enma Scripting Patterns for Perception.cx

## Pattern: Process Attach and Module Resolve

```cpp
proc_t g_proc;
uint64 g_base;
uint64 g_size;

bool init_process() {
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) return false;
    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    return g_base != 0;
}
```

## Pattern: Signature Scanning with RIP-Relative Resolution

```cpp
// Resolve a RIP-relative LEA/MOV: instruction at `hit` has a 4-byte displacement at `hit+disp_offset`
// Final address = hit + instruction_length + signed_displacement
uint64 resolve_rip(proc_t& p, uint64 hit, int32 disp_offset, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = p.r32(hit + cast<uint64>(disp_offset));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}

// Example: LEA RCX, [rip+????] = 48 8D 0D ?? ?? ?? ??
// disp_offset=3 (skip 48 8D 0D), insn_len=7
uint64 find_global(proc_t& p, uint64 base, uint64 size, string sig) {
    uint64 hit = p.find_code_pattern(base, size, sig);
    return resolve_rip(p, hit, 3, 7);
}
```

## Pattern: Entity List Iteration with Null Guards

```cpp
void iterate_entities(proc_t& p, uint64 entity_list, int32 max_count) {
    for (int32 i = 0; i < max_count; i++) {
        uint64 ent = p.ru64(entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;

        // Read position (Source Engine typically stores as float32 vec3)
        vec3 pos = p.read_vec3_fl32(ent + OFFSET_POSITION);
        int32 health = p.r32(ent + OFFSET_HEALTH);
        int32 team = p.r32(ent + OFFSET_TEAM);

        if (health <= 0) continue;       // skip dead
        if (team == local_team) continue; // skip friendly

        // ... process entity
    }
}
```

## Pattern: World-to-Screen Projection (Source Engine 4x4 Matrix)

```cpp
// Source Engine stores the view-projection matrix as 16 floats (4x4, row-major)
bool world_to_screen(proc_t& p, uint64 matrix_addr, vec3 world, out vec2 screen) {
    // Read the 4 rows (w-component row is row 3)
    float64 w = p.rf32(matrix_addr + 12) * world.x
              + p.rf32(matrix_addr + 28) * world.y
              + p.rf32(matrix_addr + 44) * world.z
              + p.rf32(matrix_addr + 60);

    if (w < 0.001) return false; // behind camera

    float64 inv_w = 1.0 / w;

    float64 nx = (p.rf32(matrix_addr + 0)  * world.x
                + p.rf32(matrix_addr + 16) * world.y
                + p.rf32(matrix_addr + 32) * world.z
                + p.rf32(matrix_addr + 48)) * inv_w;

    float64 ny = (p.rf32(matrix_addr + 4)  * world.x
                + p.rf32(matrix_addr + 20) * world.y
                + p.rf32(matrix_addr + 36) * world.z
                + p.rf32(matrix_addr + 52)) * inv_w;

    float64 vw = get_view_width();
    float64 vh = get_view_height();

    screen = vec2(
        (vw * 0.5) + (nx * vw * 0.5),
        (vh * 0.5) - (ny * vh * 0.5)
    );
    return true;
}
```

## Pattern: 2D Box Overlay with Health Bar

```cpp
import "vec";
import "color";

void draw_entity_box(vec2 head_screen, vec2 feet_screen, float64 health_pct, string name) {
    color c_box = color(255, 50, 50, 200);
    color c_hp  = color(50, 255, 50, 200);
    color c_text = color(255, 255, 255, 255);
    color c_shadow = color(0, 0, 0, 180);

    float64 height = feet_screen.y - head_screen.y;
    float64 width = height * 0.4;
    float64 x = head_screen.x - width * 0.5;
    float64 y = head_screen.y;

    // Box
    draw_rect(vec2(x, y), vec2(width, height), c_box, 1.0, 0.0, 0);

    // Health bar (left side)
    float64 bar_h = height * health_pct;
    float64 bar_y = y + height - bar_h;
    draw_rect_filled(vec2(x - 4.0, bar_y), vec2(2.0, bar_h), c_hp, 0.0, 0);

    // Name text above box
    draw_text(name, vec2(head_screen.x, y - 14.0), c_text, get_font18(), 2, c_shadow, 1.0);
}
```

## Pattern: Snapline Drawing

```cpp
void draw_snapline(vec2 entity_screen) {
    float64 screen_w = get_view_width();
    float64 screen_h = get_view_height();
    vec2 bottom_center = vec2(screen_w * 0.5, screen_h);
    color c = color(255, 255, 255, 120);
    draw_line(bottom_center, entity_screen, c, 1.0);
}
```

## Pattern: Distance Calculation and Display

```cpp
float64 distance_3d(vec3 a, vec3 b) {
    float64 dx = a.x - b.x;
    float64 dy = a.y - b.y;
    float64 dz = a.z - b.z;
    return sqrt(dx*dx + dy*dy + dz*dz);
}

void draw_distance(vec2 screen_pos, float64 dist) {
    string text = format("{d}m", cast<int32>(dist / 39.37)); // units to meters
    color white = color(255, 255, 255, 200);
    draw_text(text, vec2(screen_pos.x, screen_pos.y + 12.0), white, get_font18(), 0, color(0,0,0,0), 0.0);
}
```

## Pattern: Angle Calculation (Atan2-Based)

```cpp
vec2 calc_angle(vec3 src, vec3 dst) {
    vec3 delta;
    delta.x = dst.x - src.x;
    delta.y = dst.y - src.y;
    delta.z = dst.z - src.z;
    float64 dist_xy = sqrt(delta.x * delta.x + delta.y * delta.y);
    float64 pitch = atan2(-delta.z, dist_xy) * (180.0 / 3.14159265);
    float64 yaw   = atan2(delta.y, delta.x) * (180.0 / 3.14159265);
    return vec2(pitch, yaw);
}

float64 angle_fov(vec2 current, vec2 target) {
    float64 dp = current.x - target.x;
    float64 dy = current.y - target.y;
    // Normalize yaw delta to [-180, 180]
    while (dy > 180.0)  dy = dy - 360.0;
    while (dy < -180.0) dy = dy + 360.0;
    return sqrt(dp*dp + dy*dy);
}
```

## Pattern: Smooth Angle Interpolation

```cpp
vec2 smooth_angle(vec2 current, vec2 target, float64 smooth_factor) {
    float64 dx = target.x - current.x;
    float64 dy = target.y - current.y;
    while (dy > 180.0)  dy = dy - 360.0;
    while (dy < -180.0) dy = dy + 360.0;
    return vec2(
        current.x + dx / smooth_factor,
        current.y + dy / smooth_factor
    );
}
```

## Pattern: GUI Menu with Config

```cpp
bool g_enabled = true;
float64 g_max_dist = 3000.0;
float64 g_smooth = 5.0;
int32 g_hotkey = 0x06; // VK_XBUTTON2
color g_color = color(255, 50, 50, 255);

void setup_menu() {
    int64 sec = create_section("Settings");
    section_checkbox(sec, "Enable", g_enabled);
    section_slider_float(sec, "Max Distance", g_max_dist, 100.0, 10000.0);
    section_slider_float(sec, "Smooth Factor", g_smooth, 1.0, 30.0);
    section_keybind(sec, "Hotkey", g_hotkey);
    section_color_picker(sec, "Overlay Color", g_color);
    section_separator(sec);
    section_label(sec, "v1.0");
}
```

## Pattern: Config Save/Load

```cpp
void save_config() {
    string cfg = "";
    cfg = cfg + "enabled=" + cast<string>(g_enabled) + "\n";
    cfg = cfg + "max_dist=" + cast<string>(g_max_dist) + "\n";
    cfg = cfg + "smooth=" + cast<string>(g_smooth) + "\n";
    write_file("config.txt", cfg);
}

void load_config() {
    if (!file_exists("config.txt")) return;
    string cfg = read_file("config.txt");
    // Parse key=value pairs
    array<string> lines = cfg.split("\n");
    for (string line : lines) {
        array<string> kv = line.split("=");
        if (kv.length() < 2) continue;
        string key = kv[0];
        string val = kv[1];
        if (key == "enabled")  g_enabled = val == "true" || val == "1";
        if (key == "max_dist") g_max_dist = val.to_float();
        if (key == "smooth")   g_smooth = val.to_float();
    }
}
```

## Pattern: Minimap / Radar

```cpp
void draw_radar(vec3 local_pos, float64 local_yaw, vec3[] positions, float64 radar_range) {
    color c_bg    = color(0, 0, 0, 150);
    color c_dot   = color(255, 50, 50, 255);
    color c_self  = color(50, 255, 50, 255);
    float64 radar_size = 150.0;
    float64 cx = 90.0;
    float64 cy = 90.0;

    // Background
    draw_rect_filled(vec2(cx - radar_size*0.5, cy - radar_size*0.5),
                     vec2(radar_size, radar_size), c_bg, 4.0, 15);

    // Self dot at center
    draw_circle(vec2(cx, cy), 3.0, c_self, 1.0, true);

    float64 yaw_rad = local_yaw * (3.14159265 / 180.0);

    for (int32 i = 0; i < positions.length(); i++) {
        float64 dx = positions[i].x - local_pos.x;
        float64 dy = positions[i].y - local_pos.y;

        // Rotate by -yaw so "up" on radar = forward
        float64 rx = dx * cos(-yaw_rad) - dy * sin(-yaw_rad);
        float64 ry = dx * sin(-yaw_rad) + dy * cos(-yaw_rad);

        // Scale to radar
        float64 scale = (radar_size * 0.5) / radar_range;
        float64 px = cx + rx * scale;
        float64 py = cy - ry * scale;

        // Clamp to radar bounds
        float64 half = radar_size * 0.5 - 4.0;
        if (px < cx - half) px = cx - half;
        if (px > cx + half) px = cx + half;
        if (py < cy - half) py = cy - half;
        if (py > cy + half) py = cy + half;

        draw_circle(vec2(px, py), 2.5, c_dot, 1.0, true);
    }
}
```

## Pattern: Complete Script Skeleton

```cpp
import "vec";
import "color";

// Globals
proc_t g_proc;
uint64 g_base;
uint64 g_size;
bool   g_running = false;

// Config (bound to GUI)
bool    g_enabled = true;
float64 g_max_distance = 3000.0;

void on_update(int64 data) {
    if (!g_enabled) return;
    if (!g_proc.alive()) return;
    // ... read game state into cache
}

void on_render(int64 data) {
    if (!g_enabled) return;
    // ... draw from cached state (no proc reads here)
}

int64 main() {
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) {
        println("Process not found");
        return 0;
    }
    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    if (g_base == 0) return 0;

    // Resolve offsets via pattern scans here
    // ...

    // Setup GUI
    int64 sec = create_section("My Script");
    section_checkbox(sec, "Enable", g_enabled);
    section_slider_float(sec, "Max Distance", g_max_distance, 0.0, 10000.0);

    // Register routines
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);

    g_running = true;
    return 1; // stay loaded
}
```

---

## Source: `knowledge/aimbot-math.md`

# Aimbot Math Reference

> **Scope:** Educational math reference for PCX cheat development. Authorized targets only.

This is the math companion to [`common-patterns.md`](common-patterns.md). That file
covers the *render* half — world-to-screen, boxes, snaplines, radar — plus a single
`calc_angle` / `smooth_angle` teaser. The README promises "angle calc, smooth interp"
for the aim half; this file is where that math actually lives. Everything below builds
on the Enma idioms already established in `common-patterns.md`: `uint64` addresses,
`proc_t` reads, `vec3` field access (`.x` / `.y` / `.z`, no getter parens), and the
`(180.0 / PI)` degree conversion used by `calc_angle`.

Code blocks honor the 12 [`game-cheat-guidelines`](../.claude/skills/game-cheat-guidelines/SKILL.md):
`uint64` addresses, caller null-guards every read, scan stays out of render, and the one
feature that writes memory (no-recoil, angle writeback) writes the minimum bytes. Offsets
appear as bare symbolic identifiers (`OFF_VELOCITY`, resolved in `offsets.em`) exactly as
`common-patterns.md` does — never a version-specific hex literal.

```cpp
// Shared throughout this reference. Matches common-patterns.md calc_angle.
const float64 PI = 3.14159265358979;
const float64 RAD2DEG = 180.0 / PI;
const float64 DEG2RAD = PI / 180.0;
```

## Angles: yaw and pitch from two world points

The aimbot's core question — "what view angles point my camera at that target?" — answers with
two `atan2` calls. This is `calc_angle` from `common-patterns.md`, restated with the convention
spelled out:

```cpp
// Returns (pitch, yaw) in degrees. Source-engine convention (z = up).
vec2 calc_angle(vec3 src, vec3 dst) {
    vec3 delta = dst.sub(src);                          // dst - src
    float64 dist_xy = sqrt(delta.x * delta.x + delta.y * delta.y);
    float64 pitch = atan2(-delta.z, dist_xy) * RAD2DEG; // up = negative pitch
    float64 yaw   = atan2(delta.y, delta.x) * RAD2DEG;
    return vec2(pitch, yaw);                             // vec2.x = pitch, vec2.y = yaw
}
```

**Output range.** `atan2` returns `(-PI, PI]`, so pitch and yaw come out in `(-180, 180]` — the
range Source-family games store. If your engine stores yaw in `[0, 360)`, normalize *on
writeback*, not here; the delta math below wraps either input correctly.

**Pitch sign is engine-specific and trips everyone.** `atan2(-delta.z, dist_xy)` produces
a *negative* pitch when the target is above you (`delta.z > 0`). That matches Source, where
looking up is negative pitch. Other engines flip this:

| Engine          | Angle storage           | Up is...        | Yaw zero axis | Handedness |
| --------------- | ----------------------- | --------------- | ------------- | ---------- |
| Source / Source2| `QAngle{pitch,yaw,roll}`, degrees | negative pitch | +X | left, z-up |
| Unreal (UE4/5)  | `FRotator{Pitch,Yaw,Roll}`, degrees | positive pitch | +X | left, z-up |
| Unity           | Euler degrees / quaternion | positive pitch | +Z | left, y-up |

For Unreal, drop the negation: `pitch = atan2(delta.z, dist_xy) * RAD2DEG`. For Unity the "up"
axis is `y`, so `dist_xy` is the XZ-plane distance and pitch keys off `delta.y`.

## Angle deltas — the wrap-around trap

You never write absolute angles into a smoothing loop; you work with the *delta* from your
current view to the target. Subtracting two angles naively breaks at the seam where the
range wraps.

Suppose your current yaw is `350°` and the target is at `10°`. The shortest turn is `+20°`
(swing right through `360°/0°`). But `target - current = 10 - 350 = -340°` tells the
aimbot to spin almost all the way around the other direction. Symmetrically, current `10°`
to target `350°` should be `-20°`, not `+340°`.

The fix maps any delta into `[-180, 180)`:

```cpp
// Normalize an angle delta (degrees) to the shortest signed path in [-180, 180).
float64 normalize_delta(float64 delta) {
    return fmod(delta + 540.0, 360.0) - 180.0;
}
```

**Why `+540`, not `+180`?** `540 = 360 + 180`. Enma's `fmod` follows C semantics: the
result takes the sign of the dividend, so `fmod(-340.0, 360.0)` is a *negative* `-340`, not
`20`. Offsetting by `540` guarantees the argument is positive for any delta in `[-360, 360]`
(`delta + 540` lands in `[180, 900]`), so `fmod` stays positive, and the trailing `- 180`
re-centers it. Verify:

```
normalize_delta(-340) = fmod(200, 360) - 180 = 200 - 180 = +20   // 350 -> 10, correct
normalize_delta(+340) = fmod(880, 360) - 180 = 160 - 180 = -20   // 10 -> 350, correct
normalize_delta(+10)  = fmod(550, 360) - 180 = 190 - 180 = +10   // no wrap, unchanged
```

Apply it to yaw on every frame. Pitch does **not** wrap (it is clamped to roughly
`[-89, 89]`), so clamp pitch instead of wrapping it:

```cpp
vec2 angle_delta(vec2 current, vec2 target) {
    float64 dp = fclamp(target.x - current.x, -89.0, 89.0);  // pitch: clamp, no wrap
    float64 dy = normalize_delta(target.y - current.y);      // yaw: wrap
    return vec2(dp, dy);
}
```

## FOV cone check — "is the target in screen FOV"

Two formulations. They answer slightly different questions; pick by what you already have.

**3D angle cone (dot product).** Use this when you have view angles and world positions and
have *not* run world-to-screen yet (cheaper — no matrix multiply). Build the view-forward
unit vector from your angles, build the unit direction to the target, and compare their dot
product against `cos(fov)`:

```cpp
// Forward unit vector from Source-convention view angles (degrees).
vec3 angles_to_forward(float64 pitch_deg, float64 yaw_deg) {
    float64 p = pitch_deg * DEG2RAD;
    float64 y = yaw_deg * DEG2RAD;
    float64 cp = cos(p);
    return vec3(cp * cos(y), cp * sin(y), -sin(p));  // -sin(p): up = negative pitch
}

// True if target sits within `fov_deg` half-angle of where the camera looks.
bool in_fov_cone(vec3 eye, vec2 view_angles, vec3 target, float64 fov_deg) {
    vec3 fwd = angles_to_forward(view_angles.x, view_angles.y);  // already unit length
    vec3 dir = target.sub(eye).normalize();
    float64 cos_limit = cos(fov_deg * DEG2RAD);
    return fwd.dot(dir) >= cos_limit;   // larger dot = smaller angle = inside cone
}
```

The dot of two unit vectors is `cos(angle_between)`. A wider FOV means a *smaller*
`cos_limit`, so the `>=` test loosens as `fov_deg` grows — exactly what you want.

**2D screen-space (pixel radius).** Use this when you already projected the target with
`world_to_screen` (from `common-patterns.md`). FOV becomes a pixel circle around the
crosshair (screen center):

```cpp
// True if the projected target is within `radius_px` of the crosshair.
bool in_fov_screen(vec2 target_screen, float64 radius_px) {
    float64 cx = get_view_width()  * 0.5;
    float64 cy = get_view_height() * 0.5;
    float64 dx = target_screen.x - cx;
    float64 dy = target_screen.y - cy;
    return (dx * dx + dy * dy) <= (radius_px * radius_px);  // squared: no sqrt needed
}
```

**Which to use.** The screen form is intuitive (a circle the user tunes in pixels) and honors
the game's real FOV/zoom for free since the projection already did. The 3D cone needs no
projection and works for off-screen targets, so it is the better gate for a closest-target
search over the full entity list. Many aimbots use the cone to *select* and the circle to
*display* the FOV ring.

## Closest target selection

Once the FOV gate passes, rank the survivors and pick one. Four metrics, increasing cost
and increasing "feel":

**By screen distance (2D).** Pixels from crosshair. Cheapest after projection; matches what
the player sees. This is what most "FOV aimbots" use:

```cpp
float64 score_screen(vec2 target_screen) {
    float64 dx = target_screen.x - get_view_width()  * 0.5;
    float64 dy = target_screen.y - get_view_height() * 0.5;
    return dx * dx + dy * dy;   // squared px; smaller = closer to crosshair
}
```

**By angular distance (3D).** The turn the aimbot must make, in degrees. Independent of FOV
zoom and screen resolution. Reuse `angle_delta`:

```cpp
float64 score_angular(vec2 view_angles, vec2 target_angles) {
    vec2 d = angle_delta(view_angles, target_angles);
    return sqrt(d.x * d.x + d.y * d.y);   // degrees of correction needed
}
```

**By world distance.** Closest in meters (`distance_3d` from `common-patterns.md`). Useful for
melee/shotgun logic, but a distant target dead-center beats a close one at the screen edge, so
world distance alone aims poorly.

**Hybrid weighted.** Prefer targets both near the crosshair *and* close. Normalize each term to
`[0, 1]` against its max, then weight:

```cpp
// Lower score wins. ang_w + dist_w should sum to 1.0.
float64 score_hybrid(float64 ang_deg, float64 max_ang,
                     float64 world_dist, float64 max_dist,
                     float64 ang_w, float64 dist_w) {
    float64 ang_n  = fclamp(ang_deg    / max_ang,  0.0, 1.0);
    float64 dist_n = fclamp(world_dist / max_dist, 0.0, 1.0);
    return ang_w * ang_n + dist_w * dist_n;
}
```

Worked example (`ang_w=0.7`, `dist_w=0.3`, `max_ang=30°`, `max_dist=3000`): target A (`5°` at
`2500`) → `0.7*(5/30)+0.3*(2500/3000)=0.367`; target B (`15°` at `400`) → `0.390`. A wins, the
smaller turn dominates. Bias toward angle for twitchy aim, toward distance to lock the nearest.

Selection loop picks the minimum score over the validated, in-FOV set:

```cpp
int32 best = -1;
float64 best_score = 1.0e30;
for (int32 i = 0; i < g_candidates.length(); i++) {
    float64 s = score_hybrid(g_ang[i], 30.0, g_dist[i], 3000.0, 0.7, 0.3);
    if (s < best_score) { best_score = s; best = i; }
}
```

## Target validation gate

Selecting a target is worthless if it is dead, friendly, or behind a wall. Run an **ordered**
checklist — cheap field reads first, the expensive line-of-sight trace last — and bail at the
first failure so you never trace a target you already rejected. (Separate scan from render:
this runs in `on_update`, not `on_render`.)

```cpp
bool is_valid_target(proc_t& p, uint64 ent, vec3 eye, vec3 target_pos,
                     int32 local_team, float64 max_dist) {
    // 1. Alive (one int read — cheapest).
    if (p.r32(ent + OFF_HEALTH) <= 0) return false;

    // 2. Enemy team (one int read).
    if (p.r32(ent + OFF_TEAM) == local_team) return false;

    // 3. In range (no read; pure math on cached positions).
    if (target_pos.distance(eye) > max_dist) return false;

    // 4. Not smoked / flag-gated (one read; engine-specific flags).
    if ((p.ru32(ent + OFF_FLAGS) & FLAG_BLOCKED) != 0) return false;

    // 5. Visible — line of sight. The expensive check goes LAST.
    //    Prefer the engine's per-bone visible flag when it exists (one read);
    //    fall back to a ray trace only when it doesn't.
    if (p.r32(ent + OFF_VISIBLE) == 0) return false;

    return true;
}
```

**Ordering rationale.** Checks 1-4 are single integer reads or cached-position math —
nanoseconds. A visibility *trace* (casting a ray through the game's collision world, or
calling its `TraceLine`) is orders of magnitude more expensive and may require a write to set
up trace parameters. Gate it behind everything cheaper. If the engine exposes a
`m_bSpotted` / visible-bone bitmask (a plain read), prefer that over a trace entirely — it is
both cheaper and quieter. Offsets shown (`OFF_HEALTH`, `OFF_TEAM`, `OFF_FLAGS`, `OFF_VISIBLE`)
resolve in `offsets.em`; mark any you guessed `// UNVERIFIED` per guideline 12.

## Prediction — basic linear

Bullets are not hitscan in most games; they take time to arrive, and the target keeps moving.
Linear prediction extrapolates the target along its velocity by the bullet's travel time:

```
predicted = target_pos + target_vel * t,   where t = distance / bullet_speed
```

The catch: `distance` depends on where you aim, which depends on `t`, which depends on
`distance`. Solve it with a couple of fixed-point iterations — each pass refines `t` using
the previous pass's aim point. Two or three iterations converge for any reasonable speed:

```cpp
vec3 predict_linear(proc_t& p, uint64 ent, vec3 eye, vec3 target_pos, float64 bullet_speed) {
    vec3 vel = p.read_vec3_fl32(ent + OFF_VELOCITY);   // units/sec; read once
    vec3 aim = target_pos;
    for (int32 i = 0; i < 3; i++) {
        float64 t = aim.distance(eye) / bullet_speed;  // bullet flight time
        aim = target_pos.add(vel.scale(t));            // target_pos + vel*t
    }
    return aim;
}
```

**Getting bullet speed is game-dependent.** It is not a universal constant — it is per-weapon
muzzle velocity, often stored on the active weapon entity or a weapon-data table:

- **Source / Source2:** weapon script `CSWeaponData` / `WeaponInfo` exposes a projectile or
  muzzle speed; some weapons are hitscan (treat `t = 0`). Read the active weapon, then its
  data pointer.
- **Unreal:** the projectile class's `InitialSpeed` on `ProjectileMovementComponent`.
- **Generic:** if you cannot find a field, measure it — fire once at a wall a known distance
  away and time the impact, then hardcode per-weapon (and re-measure after patches).

Velocity itself comes from the target's movement field (`OFF_VELOCITY`, frequently
`m_vecVelocity`). If the game only stores positions, derive velocity as
`(pos_this_frame - pos_last_frame) / frametime` in `on_update`.

## Prediction — gravity-aware

When the projectile arcs (grenades, arrows, tank shells, Apex sniper drop), linear prediction
under-aims: you must both *lead* the moving target and *raise* the aim to fight gravity.

**Step 1 — intercept time against a moving target.** Treat the projectile as traveling at
constant speed `s` (handle the arc as a separate vertical correction). Let `pRel =
target_pos - shooter_pos` and `vt = target_vel`. The projectile reaches the target when the
straight-line distance it has flown equals the moving target's distance:

```
|pRel + vt*t| = s*t
```

Square both sides and group by powers of `t`:

```
(vt·vt - s²) t² + 2(pRel·vt) t + (pRel·pRel) = 0
       a              b               c
```

A standard quadratic. Take the **smallest positive** root (earliest interception):

```cpp
// Returns intercept time t > 0, or -1.0 if no real solution (target outruns projectile).
float64 intercept_time(vec3 p_rel, vec3 vt, float64 s) {
    float64 a = vt.dot(vt) - s * s;
    float64 b = 2.0 * p_rel.dot(vt);
    float64 c = p_rel.dot(p_rel);

    if (fabs(a) < 0.0001) {                 // target speed == projectile speed: linear
        if (fabs(b) < 0.0001) return -1.0;
        float64 t = -c / b;
        return t > 0.0 ? t : -1.0;
    }

    float64 disc = b * b - 4.0 * a * c;
    if (disc < 0.0) return -1.0;            // unreachable
    float64 sq = sqrt(disc);
    float64 t1 = (-b - sq) / (2.0 * a);
    float64 t2 = (-b + sq) / (2.0 * a);

    // Smallest strictly-positive root.
    float64 best = -1.0;
    if (t1 > 0.0) best = t1;
    if (t2 > 0.0 && (best < 0.0 || t2 < best)) best = t2;
    return best;
}
```

**Step 2 — gravity drop.** With the intercept time known, the lead point is
`target_pos + vt*t`. Gravity pulls the projectile down by `0.5 * g * t²` over that flight, so
aim that much *higher* (z is up in Source). `g` is the game's projectile gravity (often the
world gravity scaled by a per-projectile multiplier — read it, don't assume `9.8`):

```cpp
// Full gravity-aware aim point. Returns target_pos if unreachable.
vec3 predict_gravity(vec3 shooter, vec3 target_pos, vec3 target_vel,
                     float64 proj_speed, float64 gravity) {
    vec3 p_rel = target_pos.sub(shooter);
    float64 t = intercept_time(p_rel, target_vel, proj_speed);
    if (t < 0.0) return target_pos;                 // no firing solution; caller skips shot

    vec3 lead = target_pos.add(target_vel.scale(t)); // lead the motion
    lead.z = lead.z + 0.5 * gravity * t * t;         // raise to fight the drop
    return lead;
}
```

Feed `lead` into `calc_angle(eye, lead)` to get the firing angles. The drop term assumes z-up;
for a y-up engine (Unity) adjust `lead.y` instead. If `intercept_time` returns `-1`, there is
no firing solution — the target is faster than the projectile or out of range — so withhold
the shot rather than aiming at a garbage point.

## Recoil compensation (no-recoil)

A recoil pattern is a per-shot kick table: each consecutive round adds a known offset to the
view angles (a "spray pattern"). The game tracks how many rounds you have fired and the
accumulated punch, then offsets your aim by it. No-recoil cancels that offset.

Two approaches, cheapest first:

**Read and subtract the punch (read-mostly).** Most engines expose the accumulated aim punch
as a vector (`m_aimPunchAngle` in Source) and a shot counter (`m_iShotsFired`). Read the punch
and subtract it from your view angles when you write them back. This is the quiet path — you
only ever write the view-angle field you were going to write anyway for aim:

```cpp
// Returns view angles with the current recoil punch removed.
// OFF_PUNCH / OFF_VIEW_ANGLES resolve in offsets.em; UNVERIFIED until checked against binary.
vec2 compensate_recoil(proc_t& p, uint64 local, vec2 desired_angles) {
    vec3 punch = p.read_vec3_fl32(local + OFF_PUNCH);  // (pitch, yaw, roll) punch in degrees
    // Source scales stored punch by 2.0 for the actual view offset; verify per engine.
    return vec2(desired_angles.x - punch.x * 2.0,
                desired_angles.y - punch.y * 2.0);
}
```

**Patch the punch source (write, heavier footprint).** Some scripts zero the recoil-spread
float in game memory so the gun never kicks. Per guideline 9, write the single float, never a
NOP sled over the recoil code:

```cpp
// WRONG — nop-patching the recoil routine (16 bytes in .text, integrity-checked).
// RIGHT — zero the spread float that the routine reads.
if (g_norecoil) p.wf32(local + OFF_RECOIL_SPREAD, 0.0f);
```

Prefer the read-and-subtract path: it leaves zero write footprint on the recoil system and
folds cleanly into the angle you already plan to write. Reading the shot index (`m_iShotsFired`)
lets you ramp compensation in only while a spray is active, so single taps stay untouched.

## Smoothing — why and how

Snapping the view instantly onto a target is the loudest aim-detection signal: human aim has a
measurable acceleration curve and overshoot, a teleport does not, and behavioral anti-cheats
flag the zero-frame angle jump directly. Smoothing spreads the correction over several frames.
Always smooth the *delta* (wrapped via `normalize_delta`), never raw absolute angles, or the
yaw seam will make the view spin.

**Linear (divide).** Move a fixed fraction of the remaining delta each frame. This is
`smooth_angle` from `common-patterns.md`. Simple, but the speed decays as you close in, giving
a soft ease-out:

```cpp
vec2 smooth_linear(vec2 view, vec2 target, float64 smooth_factor) {
    vec2 d = angle_delta(view, target);                 // wrapped pitch+yaw delta
    return vec2(view.x + d.x / smooth_factor,           // larger factor = slower
                view.y + d.y / smooth_factor);
}
```

**Exponential (frame-rate independent).** The divide form above is tied to frame rate —
faster FPS means more steps means snappier aim. Decouple it from frame rate by deriving the
blend factor from elapsed time:

```cpp
vec2 smooth_exp(vec2 view, vec2 target, float64 rate, float64 dt) {
    float64 a = 1.0 - exp(-rate * dt);   // dt = 1.0 / get_fps(); a in (0,1)
    vec2 d = angle_delta(view, target);
    return vec2(view.x + d.x * a, view.y + d.y * a);
}
```

**Spring-damped (SmoothDamp).** Tracks angular velocity so the view *accelerates* into the turn
and eases out without overshoot — the most human-looking profile. `smooth_time` is the
approximate seconds to converge. It returns the new angle *and* the new velocity packed in a
`vec2`; persist `.y` per axis and feed it back next frame:

```cpp
// Critically-damped smoothing for one axis. Returns vec2(new_angle, new_velocity).
vec2 smooth_damp(float64 cur, float64 target, float64 vel, float64 smooth_time, float64 dt) {
    float64 omega = 2.0 / smooth_time;
    float64 x = omega * dt;
    float64 decay = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x);
    float64 change = cur - target;
    float64 temp = (vel + omega * change) * dt;
    float64 new_vel = (vel - omega * temp) * decay;
    return vec2(target + (change + temp) * decay, new_vel);
}
```

| Method        | Feel               | State | Frame-rate safe | Cost |
| ------------- | ------------------ | ----- | --------------- | ---- |
| Linear divide | ease-out only      | none  | no              | tiny |
| Exponential   | ease-out, smooth   | none  | yes (uses `dt`) | tiny |
| Spring-damped | ease-in + ease-out | per-axis velocity | yes | small |

**Sample-rate considerations.** Any tuning constant that is not time-based drifts with frame
rate — feed `dt = 1.0 / get_fps()` into the exponential and spring forms. The linear divide
form has no `dt`, so its effective speed differs between 60 and 240 FPS; document the slider as
frame-rate dependent or convert it to the exponential form.

## Mouse input writeback paths

Computed angles have to *become* aim somehow. Two routes, with very different detection
surfaces.

**Synthetic mouse input (`SendInput`).** Convert the angle delta to mouse counts and feed it
through the OS input stack via the Win API. The game sees ordinary mouse movement and applies
its own sensitivity, so the conversion needs the game's yaw/pitch-per-count factor:

```cpp
// Convert a view-angle delta (degrees) to relative mouse counts and send it.
// `counts_per_deg` is game sensitivity dependent — derive or measure it; UNVERIFIED.
void writeback_sendinput(vec2 angle_delta_deg, float64 counts_per_deg) {
    int64 dx = cast<int64>(angle_delta_deg.y * counts_per_deg);   // yaw  -> horizontal
    int64 dy = cast<int64>(angle_delta_deg.x * counts_per_deg);   // pitch -> vertical
    mouse_move_relative(dx, dy);   // or send_mouse_input(dx, dy, MOUSEEVENTF_MOVE, 0)
}
```

- *Pros:* no game-memory write at all — the cleanest footprint against memory-integrity
  checks; the movement rides the input path the game already trusts.
- *Cons:* synthetic input is itself detectable (injected-input flags, delta-timing analysis)
  and needs the sensitivity conversion, which shifts with the player's sens and zoom.

**Direct view-angle write.** Write the computed angles straight into the game's view-angle
field:

```cpp
void writeback_angles(proc_t& p, uint64 local, vec2 angles) {
    // OFF_VIEW_ANGLES resolves in offsets.em. One vec write per active frame, no more.
    p.write_vec3_fl32(local + OFF_VIEW_ANGLES, vec3(angles.x, angles.y, 0.0));
}
```

- *Pros:* exact — no sensitivity math, the view lands precisely where you computed.
- *Cons:* it is a memory write to a contested gameplay field; anti-cheat can monitor the
  field for writes that did not originate from the input path, and on a contested field the
  game may revert it (read back to confirm, per guideline 9).

**Respect guideline 9 either way.** Whichever path, write only while the aim key is held and
only the minimum needed — one relative move or one `write_vec3_fl32` per active frame, gated
on a GUI keybind. Never write every frame unconditionally:

```cpp
void on_update(int64 data) {
    if (!g_aim_enabled) return;
    if (!key_down(vk::xbutton2)) return;   // hold-to-aim; no key, no write
    // ... select + validate + predict + smooth, then a single writeback ...
}
```

## Common pitfalls

**Radians vs degrees — the silent 57× bug.** `atan2` and all Enma trig work in radians; most
view-angle fields store degrees, some store radians. The classic failure: read a radian-stored
angle, treat it as degrees, then write your degree result back into a radian field — everything
is off by `180/PI ≈ 57.3×` and the aim flicks to nonsense. Convert at *every* boundary
(`* RAD2DEG` after a trig call, `* DEG2RAD` before one) and confirm the field's unit by reading
it while looking at a known angle in-game.

**Pitch sign convention.** Source uses up = *negative* pitch; Unreal and Unity use up =
*positive* pitch. Backwards, and the aimbot pulls *down* onto targets above you and the spray
compensation fights the recoil instead of canceling it. Verify by reading the field while
aiming straight up.

**Left- vs right-handed coordinates.** Source/Unreal are left-handed z-up; Unity left-handed
y-up; many math libraries and custom W2S assume right-handed. A mismatch flips a yaw or
cross-product sign, so left-side targets read as right-side. If lead prediction consistently
aims to the wrong side, suspect a flipped axis before the velocity read.

**Wrong "up" axis in pitch math.** `calc_angle` uses `dist_xy` (XY-plane) because Source is
z-up. On a y-up engine the planar distance is over XZ and pitch keys off `delta.y`. Reusing the
z-up form on Unity makes pitch track horizontal distance — aim drifts vertically as the target
strafes.

## See also

- [`common-patterns.md`](common-patterns.md) — the render half (W2S, boxes, radar) and the
  `calc_angle` / `smooth_angle` this file extends.
- [`offset-methodology.md`](offset-methodology.md) — resolving `OFF_VELOCITY`, `OFF_VIEW_ANGLES`,
  `OFF_PUNCH` with sigs instead of hardcodes.
- [`anti-cheat-architecture.md`](anti-cheat-architecture.md) — why instant snaps and memory
  writes are detection surfaces; informs the smoothing and writeback choices above.
- [`pcx-api-cheatsheet.md`](pcx-api-cheatsheet.md) — quick reference for the natives used here.
- [`game-cheat-guidelines`](../.claude/skills/game-cheat-guidelines/SKILL.md) — the 12 rules;
  9 (minimize writes) and 10 (W2S) govern this file directly.
- Perception API: [`proc-api`](../docs/perception/proc-api.md),
  [`render-api`](../docs/perception/render-api.md),
  [`input-api`](../docs/perception/input-api.md),
  [`win-api`](../docs/perception/win-api.md); Enma math:
  [`addon-vec`](../docs/enma/addon-vec.md), [`addon-math`](../docs/enma/addon-math.md).

---

## Source: `knowledge/offset-methodology.md`

# Offset Finding and Maintenance Methodology

## When to Pattern Scan vs Hardcode

**Pattern scan** (preferred): any global pointer, vtable address, or function address that the compiler may relocate between builds. The instruction sequence referencing it is stable; the address it points to is not.

**Hardcode** (acceptable): struct field offsets within a known type. `m_iHealth` at `+0x43E0` inside `CPlayer` changes only when Respawn reorders the class — which happens less often than code relocations. Still document the source.

## Signature Construction

1. Open the function in IDA/Ghidra. Find the instruction that loads/references the value you need.
2. Copy the raw bytes of that instruction and 1-2 neighboring instructions for uniqueness.
3. Replace **RIP-relative displacements** (4 bytes after the opcode) with `??` wildcards — these change every build.
4. Replace **immediate addresses** and **jump targets** with `??` — also unstable.
5. Keep **opcode bytes** and **register encodings** — these are stable unless the compiler changes register allocation.

```
Example instruction:  48 8B 05 [A0 B3 2A 01]  ← MOV RAX, [rip+0x12AB3A0]
                      ^^^^^^^^ ^^^^^^^^^^^^^^
                      opcode   RIP displacement (changes every build)

Signature:           "48 8B 05 ?? ?? ?? ??"
```

Verify uniqueness: `find_all_code_patterns` should return exactly 1 hit. If multiple, extend the sig with more surrounding bytes.

## RIP-Relative Address Resolution

Most x64 instructions use RIP-relative addressing. The displacement is a **signed 32-bit integer** relative to the **end** of the instruction (i.e., the address of the next instruction).

```
hit        = address where the sig matched
disp_off   = offset from hit to the displacement bytes (e.g., 3 for LEA reg,[rip+??])
insn_len   = total instruction length (e.g., 7 for a 7-byte LEA)
displacement = read_int32(hit + disp_off)      ← signed!
resolved   = hit + insn_len + displacement
```

Common instruction shapes:

| Pattern | Instruction | disp_off | insn_len |
|---------|-------------|----------|----------|
| `48 8B 05 ?? ?? ?? ??` | MOV RAX, [rip+disp] | 3 | 7 |
| `48 8D 0D ?? ?? ?? ??` | LEA RCX, [rip+disp] | 3 | 7 |
| `48 8B 0D ?? ?? ?? ??` | MOV RCX, [rip+disp] | 3 | 7 |
| `E8 ?? ?? ?? ??` | CALL rel32 | 1 | 5 |
| `E9 ?? ?? ?? ??` | JMP rel32 | 1 | 5 |

## Pointer Chain Walking

Game data is often behind multiple levels of indirection:

```
base_address → entity_list_ptr → entity_ptr → field
```

Strategy:
1. Find the first pointer via sig scan + RIP resolution.
2. Dereference each level with `ru64`, checking for 0 at every step.
3. Document the full chain: `base + 0x... → deref → + 0x... → deref → + 0x...`
4. The final offset into the struct is typically a hardcoded field offset.

```cpp
uint64 entity_list = resolve_sig(p, base, size, SIG_ENTITY_LIST);  // sig scan
if (entity_list == 0) return;                                       // stale sig
uint64 list_ptr = p.ru64(entity_list);                              // deref level 1
if (list_ptr == 0) return;                                          // null
uint64 entity = p.ru64(list_ptr + cast<uint64>(index) * 0x8);      // deref level 2
if (entity == 0) return;                                            // null entry
int32 health = p.r32(entity + 0x43E0);                             // struct field
```

## Using struct_dump for Discovery

When you don't know a struct layout, read raw memory and classify fields:

```cpp
// In Perception IDE, the AI can use struct_dump tool:
// struct_dump(addr, size=0x100)
// Returns: offset, raw hex, heuristic type (pointer/vtable/float/int/null)
```

Look for:
- **Pointers**: values in the `0x7FF...` range (usermode x64)
- **VTable ptrs**: first 8 bytes of an object, pointing into .rdata
- **Floats**: values like `100.0`, `0.0`, `-1.0` that make sense as game state
- **Ints**: small values (health, ammo, team ID)

## Cross-Referencing with IDA/Ghidra

1. Find the ConVar or string that names the feature (e.g., `"cl_interp"`, `"m_iHealth"`).
2. Xref the string → find the registration function → find the global variable or struct field.
3. Verify the offset in the reversed SDK headers if available (e.g., `r5sdk/src/game/server/player.h`).
4. Remember: SDK headers may be from an older game version. Always verify with a live read.

## Offset Table Format

Maintain a structured offset file:

```cpp
// offsets.em — auto-resolved via pattern scans
// Last verified: 2025-06-15, game version 1.98

const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";
// LEA RCX, [rip+????] — loads CEntityList global
// Source: sub_1400ABCDE in IDA, xref from "cl_entitylist"

const string SIG_VIEW_MATRIX = "48 8D 05 ?? ?? ?? ?? 48 89 44 24 ?? F3 0F";
// LEA RAX, [rip+????] — loads view-projection matrix (16 floats)

const string SIG_LOCAL_PLAYER = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? 48 8B 48";
// MOV RAX, [rip+????] — loads local player pointer

// Struct field offsets (hardcoded, verified against SDK)
const uint64 OFF_HEALTH   = 0x43E0;   // CPlayer::m_iHealth (int32)
const uint64 OFF_TEAM     = 0x0448;   // CBaseEntity::m_iTeamNum (int32)
const uint64 OFF_POSITION = 0x014C;   // CBaseEntity::m_vecAbsOrigin (vec3 float32)
const uint64 OFF_NAME     = 0x0589;   // CBaseEntity::m_iName (string ptr)
```

## What Breaks on Game Updates

| What | Stability | Why |
|------|-----------|-----|
| Pattern signatures | **High** | Instruction sequences rarely change unless the function is rewritten |
| RIP-relative resolved addresses | **None** | Absolute addresses change every build |
| Struct field offsets | **Medium** | Change when devs add/remove/reorder fields |
| VTable indices | **Medium** | Change when virtual functions are added/removed |
| Function addresses | **None** | Change every build — always use sigs |
| String literals | **High** | Rarely change — good anchor points for xrefs |
