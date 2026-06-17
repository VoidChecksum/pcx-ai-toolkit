> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/utilities.md).

# Utilities

The `util` module provides fast Base64, Hex, and URL encoding/decoding helpers for Lua scripts.

All functions operate on **raw byte strings**, not UTF-8 text, so they safely support:

* Binary data
* Network packets
* Ciphertext
* Hashes
* Buffers containing `\0` bytes
* Arbitrary byte sequences

The module is registered globally as:

```lua
util = {
    base64_encode = function(str) end,
    base64_decode = function(str) end,
    hex_encode    = function(str) end,
    hex_decode    = function(str) end,
    url_encode    = function(str) end,
    url_decode    = function(str) end,
}
```

***

## Base64 Functions

### `util.base64_encode(str)`

Encodes a raw byte string into Base64 text.

#### Parameters

| Name  | Type   | Description         |
| ----- | ------ | ------------------- |
| `str` | string | Raw bytes to encode |

#### Returns

* Base64 string

#### Example

```lua
local out = util.base64_encode("hello")
print(out)   --> aGVsbG8=
```

***

### `util.base64_decode(str)`

Decodes Base64 text into raw bytes.

#### Parameters

| Name  | Type   | Description |
| ----- | ------ | ----------- |
| `str` | string | Base64 text |

#### Returns

* `string` (raw bytes) on success
* `nil, error_message` on failure

#### Example

```lua
local raw, err = util.base64_decode("aGVsbG8=")
if raw then
    print(raw)   --> hello
else
    print("Decode failed:", err)
end
```

#### Error Example

```lua
local v, err = util.base64_decode("!!!!bad!!!!")
-- v   == nil
-- err == "Invalid base64 character"
```

***

## Hex Functions

### `util.hex_encode(str)`

Encodes bytes into uppercase hexadecimal text.

#### Parameters

| Name  | Type   | Description |
| ----- | ------ | ----------- |
| `str` | string | Raw bytes   |

#### Returns

* Uppercase hex string

#### Example

```lua
local out = util.hex_encode("ABC")
print(out)   --> 414243
```

***

### `util.hex_decode(str)`

Decodes a hex string into raw bytes.

#### Parameters

| Name  | Type   | Description                      |
| ----- | ------ | -------------------------------- |
| `str` | string | Hex text (must have even length) |

#### Returns

* Raw bytes on success
* `nil, error_message` on failure

#### Example

```lua
local raw = util.hex_decode("414243")
print(raw)   --> ABC
```

#### Error Examples

```lua
util.hex_decode("ABC")
-- nil, "Hex string length must be even"

util.hex_decode("GGGG")
-- nil, "Invalid hex character"
```

***

## URL Encode / Decode

Matches standard percent-encoding:

* Safe characters stay as-is: `A–Z a–z 0–9 - _ . ~`
* Everything else becomes `%XX`

`+` is **not** treated as space.\
Binary bytes are preserved.

***

### `util.url_encode(str)`

Encodes text for safe URL usage.

#### Example

```lua
local enc = util.url_encode("hello world! 100% ok?")
print(enc)
-- "hello%20world%21%20100%25%20ok%3F"
```

***

### `util.url_decode(str)`

Decodes `%XX` sequences back into bytes.

#### Example

```lua
local dec = util.url_decode("name=John%20Doe&msg=hi%21")
print(dec)
-- "name=John Doe&msg=hi!"
```

Invalid `%` sequences are returned literally.

***

## Roundtrip Examples

#### Base64 roundtrip

```lua
local original = "hello world"
local enc = util.base64_encode(original)
local dec = util.base64_decode(enc)
assert(dec == original)
```

#### Hex roundtrip

```lua
local original = "hello world"
local hex = util.hex_encode(original)
local raw = util.hex_decode(hex)
assert(raw == original)
```

#### URL roundtrip

```lua
local original = "email=test@example.com&msg=hello!"
local enc = util.url_encode(original)
local dec = util.url_decode(enc)
assert(dec == original)
```

***

## Binary Safety

All `util.*` functions:

* correctly handle `\0` bytes
* accept arbitrary binary input
* never corrupt data
* do not assume UTF-8
* support large buffers

Tested with byte sizes from 1 → 256 without corruption.

***

## Summary

| Function                  | Description                          |
| ------------------------- | ------------------------------------ |
| `util.base64_encode(str)` | Encode bytes → Base64                |
| `util.base64_decode(str)` | Decode Base64 → bytes (or nil+error) |
| `util.hex_encode(str)`    | Encode bytes → uppercase hex         |
| `util.hex_decode(str)`    | Decode hex → bytes (or nil+error)    |
| `util.url_encode(str)`    | Percent-encode unsafe characters     |
| `util.url_decode(str)`    | Decode `%XX` → bytes                 |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/utilities.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
