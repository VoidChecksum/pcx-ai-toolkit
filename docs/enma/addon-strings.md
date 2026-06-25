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

## String / char memory layout

Strings are script-managed values, not a layout-compatible view of target-process memory. Treat string contents as text/byte data exposed through string APIs, not as a `char[N]` field you can embed in an Enma struct to mirror a native C/C++ structure.

Current rules for native layout work:

* `char` is `int8` underneath for scalar values and formatting helpers.
* Script `string` storage is implementation-owned; do not depend on its in-memory layout.
* `struct { char name[32]; }`-style native layout mirroring is not a supported replacement for reading a target process C string.
* For process memory, read bytes through the Perception Proc/CPU APIs, stop at NUL yourself, then convert or print the resulting bytes as needed.

Pattern:

```c
// Prefer explicit process-memory reads for native C strings.
uint64 name_addr = entity + 0x120;
string name = proc.rs(name_addr, 32);      // UTF-8, stops at NUL, empty on failure

array<uint8> raw = proc.rvm(name_addr, 32); // use bytes when layout matters
```

Packed `std::string` / exact native `char[N]` struct parity is tracked as an upstream language/runtime gap.

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
