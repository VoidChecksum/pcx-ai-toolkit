> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/utilities.md).

# Utilities

Low-level helpers for encoding/decoding binary data and text.

All functions treat `string` as a raw byte container, so they work fine with binary data (including `\0` bytes and non-UTF8).

#### Functions

```cpp
string util_base64_encode(const string &in data)
bool   util_base64_decode(const string &in text, string &out data, string &out error)

string util_hex_encode(const string &in data)
bool   util_hex_decode(const string &in text, string &out data, string &out error)

string util_url_encode(const string &in data)
string util_url_decode(const string &in data)
```

***

### Base64 helpers

#### `string util_base64_encode(const string &in data)`

Encodes arbitrary data as Base64 text.

* **Parameters**
  * `data` — Input bytes to encode (any string, including binary).
* **Returns**
  * Base64-encoded text using the standard alphabet `A–Z a–z 0–9 + /` with `=` padding.

**Example**

```cpp
string original = "hello";
string enc = util_base64_encode(original);
log("Base64 = " + enc);   // "aGVsbG8="
```

***

#### `bool util_base64_decode(const string &in text, string &out data, string &out error)`

Decodes a Base64 string back into raw bytes.

* **Parameters**
  * `text` — Base64 text to decode.
  * `data` (out) — Output decoded bytes on success.
  * `error` (out) — Error message when returning `false`.
* **Returns**
  * `true` on success, `false` on error.

**On success**

* `data` contains decoded bytes.
* `error` is empty.

**On failure**

* `data` is empty.
* `error` contains a human-readable message (e.g. `"Invalid base64 character"`).

**Example**

```cpp
string src = "aGVsbG8=";
string raw, err;

if (util_base64_decode(src, raw, err))
{
    log("decoded = " + raw);   // "hello"
}
else
{
    log_error("base64 decode failed: " + err);
}
```

**Error example**

```cpp
string bad = "aGVsbG8$";       // invalid char
string data, err;
bool ok = util_base64_decode(bad, data, err);
// ok  == false
// err == "Invalid base64 character"
```

***

### Hex helpers

#### `string util_hex_encode(const string &in data)`

Encodes binary data as uppercase hexadecimal text.

* **Parameters**
  * `data` — Raw bytes to encode.
* **Returns**
  * Hex string using `0–9 A–F`. Each byte becomes 2 characters.

**Example**

```cpp
string original = "hello";
string hex = util_hex_encode(original);
log("hex = " + hex);      // "68656C6C6F"
```

***

#### `bool util_hex_decode(const string &in text, string &out data, string &out error)`

Decodes a hex string back into raw bytes.

* **Parameters**

| Name  | Type           | Description                          |
| ----- | -------------- | ------------------------------------ |
| text  | `string`       | Hex text (must have even length)     |
| data  | `string` (out) | Output decoded bytes on success      |
| error | `string` (out) | Error message when returning `false` |

* **Returns**
  * `true` on success, `false` on error.

**On success**

* `data` contains decoded bytes.
* `error` is empty.

**On failure**

* `data` is empty.
* `error` contains a message.

**Example**

```cpp
string hex = "68656C6C6F";
string raw, err;

if (util_hex_decode(hex, raw, err))
{
    log("raw = " + raw);   // "hello"
}
else
{
    log_error("hex decode failed: " + err);
}
```

**Error examples**

```cpp
// 1) Odd length
string bad1  = "ABC";
string data1, err1;
bool ok1 = util_hex_decode(bad1, data1, err1);
// ok1  == false
// err1 == "Hex string length must be even"

// 2) Invalid characters
string bad2  = "GGGG";
string data2, err2;
bool ok2 = util_hex_decode(bad2, data2, err2);
// ok2  == false
// err2 == "Invalid hex character"
```

***

### URL helpers

These functions use standard URL percent-encoding:

* Unreserved characters stay as-is: `A–Z a–z 0–9 - _ . ~`
* Everything else becomes `%XX` (hex byte).

> **Note:** `util_url_decode` does **not** convert `+` to space. `+` is treated as a normal character.

#### `string util_url_encode(const string &in data)`

Percent-encodes a string for safe use in URLs (query params, etc).

* **Parameters**
  * `data` — Input string (can be binary, but typically text).
* **Returns**
  * URL-encoded string.

**Example**

```cpp
string original = "hello world! 100% ok?";
string enc = util_url_encode(original);
// Example: "hello%20world%21%20100%25%20ok%3F"

log("url encoded = " + enc);
```

***

#### `string util_url_decode(const string &in data)`

Decodes `%XX` sequences back into raw bytes.

* **Parameters**
  * `data` — URL-encoded string (e.g. `"hello%20world"`).
* **Returns**
  * Decoded string with `%XX` sequences converted to bytes.
  * Invalid `%` sequences are left as literal characters.

**Example**

```cpp
string url = "name=John%20Doe&msg=hello%21";
string decoded = util_url_decode(url);
// "name=John Doe&msg=hello!"

log("url decoded = " + decoded);
```

***

### Roundtrip examples

#### Base64 roundtrip

```cpp
string original = "The quick brown fox.";
string enc = util_base64_encode(original);
string dec, err;

if (util_base64_decode(enc, dec, err) && dec == original)
{
    log("Base64 roundtrip OK");
}
else
{
    log_error("Base64 roundtrip failed: " + err);
}
```

#### Hex roundtrip

```cpp
string original = "hello world!";
string hex = util_hex_encode(original);
string raw, err;

if (util_hex_decode(hex, raw, err) && raw == original)
{
    log("Hex roundtrip OK");
}
else
{
    log_error("Hex roundtrip failed: " + err);
}
```

#### URL roundtrip

```cpp
string original = "email=test@example.com&msg=hi there!";
string enc = util_url_encode(original);
string dec = util_url_decode(enc);

if (dec == original)
{
    log("URL roundtrip OK");
}
else
{
    log_error("URL roundtrip failed");
}
```

***

### Binary safety

All `util_*` functions operate on `string` as byte containers:

* You can safely encode/decode **binary** data.
* Data with `\0` bytes is preserved.
* Non-UTF8 content is preserved.

Useful for:

* Network packets
* Encryption keys
* Hash outputs
* Serialized structs / blobs

***

### hash\_set&#x20;

`hash_set` is a lightweight `unordered_set<uint64>` wrapper for fast membership tests (O(1) average).

#### Type

`hash_set`

#### Methods

**Core**

* `bool hash_set::contains(uint64 v) const`\
  Returns true if `v` exists in the set.
* `bool hash_set::insert(uint64 v)`\
  Inserts `v`. Returns true if it was newly inserted, false if it already existed.
* `bool hash_set::erase(uint64 v)`\
  Removes `v`. Returns true if an element was removed, false if it wasn’t present.
* `void hash_set::clear()`\
  Removes all elements.
* `uint hash_set::size() const`\
  Returns the number of elements.
* `bool hash_set::empty() const`\
  Returns true if the set is empty.

***

**Convenience**

* `void hash_set::set(uint64 v)`\
  Inserts `v` without returning a status.
* `bool hash_set::get(uint64 v, uint64 &out value)`\
  Checks if `v` exists and outputs the stored value.

***

**Iteration**

* `void hash_set::iter_begin()`\
  Resets the internal iterator to the start.
* `bool hash_set::iter_next(uint64 &out value)`\
  Retrieves the next value in the set.\
  Returns false when iteration is finished.

***

### hash\_map&#x20;

`hash_map` is a lightweight unordered map that associates `uint64` keys with any AngelScript type\
(primitives, strings, objects, and handles).

All operations run in O(1) average time.

#### Type

`hash_map`

#### Methods

**Construction**

* `hash_map@ hash_map()`\
  Factory constructor.

***

**Core**

* `void hash_map::set(uint64 key, ?&in value)`\
  Stores a value for the given key.
* `bool hash_map::get(uint64 key, ?&out value)`\
  Retrieves the value associated with `key`.\
  Returns true if found.
* `bool hash_map::contains(uint64 key)`\
  Returns true if the key exists.
* `bool hash_map::erase(uint64 key)`\
  Removes the entry for `key`.\
  Returns true if removed.
* `void hash_map::clear()`\
  Removes all entries.
* `uint hash_map::size()`\
  Returns the number of stored entries.
* `bool hash_map::empty()`\
  Returns true if the map is empty.

***

**Iteration**

* `void hash_map::iter_begin()`\
  Resets the internal iterator to the start.
* `bool hash_map::iter_next_key(uint64 &out key)`\
  Iterates over keys only.
* `bool hash_map::iter_next(uint64 &out key, ?&out value)`\
  Iterates over key-value pairs.

### Example (hash\_set & hash\_map)

```cpp
int main()
{
    log("hash_set + hash_map test: start");
    
    // ============================
    // hash_set tests
    // ============================
    
    hash_set s;
    
    // empty / size
    if (!s.empty()) { log_error("hash_set: expected empty() == true"); return 0; }
    if (s.size() != 0) { log_error("hash_set: expected size() == 0"); return 0; }
    
    // insert / set / contains
    if (!s.insert(0x100)) { log_error("hash_set: insert(0x100) should return true"); return 0; }
    s.set(0x200);
    
    if (!s.contains(0x100)) { log_error("hash_set: contains(0x100) failed"); return 0; }
    if (!s.contains(0x200)) { log_error("hash_set: contains(0x200) failed"); return 0; }
    if (s.contains(0x999)) { log_error("hash_set: contains(0x999) should be false"); return 0; }
    
    if (s.size() != 2) { log_error("hash_set: expected size() == 2"); return 0; }
    
    // get
    uint64 out_v = 0;
    if (!s.get(0x100, out_v) || out_v != 0x100)
    {
        log_error("hash_set: get(0x100) failed");
        return 0;
    }
    
    // erase
    if (!s.erase(0x100)) { log_error("hash_set: erase(0x100) should return true"); return 0; }
    if (s.erase(0x100))  { log_error("hash_set: erase(0x100) should return false"); return 0; }
    
    if (s.contains(0x100)) { log_error("hash_set: value still exists after erase"); return 0; }
    if (s.size() != 1) { log_error("hash_set: expected size() == 1 after erase"); return 0; }
    
    // iteration
    uint iter_count = 0;
    s.iter_begin();
    while (true)
    {
        uint64 v = 0;
        if (!s.iter_next(v))
        break;
        
        if (v != 0x200)
        {
            log_error("hash_set: unexpected value in iteration");
            return 0;
        }
        
        iter_count++;
    }
    
    if (iter_count != 1)
    {
        log_error("hash_set: iteration count mismatch");
        return 0;
    }
    
    // clear
    s.clear();
    if (!s.empty() || s.size() != 0)
    {
        log_error("hash_set: clear() failed");
        return 0;
    }
    
    // ============================
    // hash_map tests
    // ============================
    
    hash_map@ m = hash_map();
    if (m is null) { log_error("hash_map: factory returned null"); return 0; }
    
    // empty / size
    if (!m.empty()) { log_error("hash_map: expected empty() == true"); return 0; }
    if (m.size() != 0) { log_error("hash_map: expected size() == 0"); return 0; }
    
    int    vi = 42;
    double vd = 2.5;
    string vs = "test";
    
    // set
    m.set(1, vi);
    m.set(2, vd);
    m.set(3, vs);
    
    if (m.size() != 3) { log_error("hash_map: expected size() == 3"); return 0; }
    
    // contains
    if (!m.contains(1) || !m.contains(2) || !m.contains(3))
    {
        log_error("hash_map: contains failed");
        return 0;
    }
    
    if (m.contains(999))
    {
        log_error("hash_map: contains(999) should be false");
        return 0;
    }
    
    // get with correct types
    int out_i = 0;
    if (!m.get(1, out_i) || out_i != 42)
    {
        log_error("hash_map: get int failed");
        return 0;
    }
    
    double out_d = 0.0;
    if (!m.get(2, out_d) || out_d != 2.5)
    {
        log_error("hash_map: get double failed");
        return 0;
    }
    
    string out_s;
    if (!m.get(3, out_s) || out_s != "test")
    {
        log_error("hash_map: get string failed");
        return 0;
    }
    
    // type mismatch should fail
    string wrong;
    if (m.get(1, wrong))
    {
        log_error("hash_map: expected type mismatch to return false");
        return 0;
    }
    
    // iteration (keys only)
    uint key_count = 0;
    m.iter_begin();
    while (true)
    {
        uint64 k = 0;
        if (!m.iter_next_key(k))
        break;
        
        if (!m.contains(k))
        {
            log_error("hash_map: iter_next_key returned invalid key");
            return 0;
        }
        
        key_count++;
    }
    
    if (key_count != m.size())
    {
        log_error("hash_map: key iteration count mismatch");
        return 0;
    }
    
    // erase
    if (!m.erase(2)) { log_error("hash_map: erase(2) should return true"); return 0; }
    if (m.erase(2))  { log_error("hash_map: erase(2) should return false"); return 0; }
    
    if (m.contains(2))
    {
        log_error("hash_map: value still exists after erase");
        return 0;
    }
    
    if (m.size() != 2)
    {
        log_error("hash_map: expected size() == 2 after erase");
        return 0;
    }
    
    // clear
    m.clear();
    if (!m.empty() || m.size() != 0)
    {
        log_error("hash_map: clear() failed");
        return 0;
    }
    
    log("hash_set + hash_map test: OK");
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
GET https://docs.perception.cx/perception/angel-script/utilities.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
