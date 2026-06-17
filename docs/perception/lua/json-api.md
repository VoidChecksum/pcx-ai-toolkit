> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/json-api.md).

# Json API

The JSON API provides simple, fast parsing and encoding of JSON using native Lua data types.\
All JSON features are exposed under the global `json` table.

***

### Overview

The `json` module supports:

| Operation                   | Description                         |
| --------------------------- | ----------------------------------- |
| **`json.parse(str)`**       | Parse a JSON string into Lua values |
| **`json.decode(str)`**      | Alias of `json.parse`               |
| **`json.stringify(value)`** | Convert Lua values into JSON        |
| **`json.encode(value)`**    | Alias of `json.stringify`           |

The API is intentionally minimal and strictly uses plain Lua tables, numbers, booleans, strings, and `nil`.

***

### JSON → Lua: `json.parse` / `json.decode`

```lua
value, err = json.parse(string)
value, err = json.decode(string)
```

#### Parameters

* **string** — a UTF-8 JSON text.

#### Returns

* On success:\
  **Lua value representing the JSON structure**
* On error:\
  `nil, "error message"`

#### Lua Type Mapping

| JSON             | Lua                                          |
| ---------------- | -------------------------------------------- |
| Object `{}`      | Table `{ key = value }`                      |
| Array `[]`       | Table `{ [1] = ..., [2] = ... }`             |
| `"text"`         | string                                       |
| `123`            | number                                       |
| `true` / `false` | boolean                                      |
| `null`           | **`nil`** (field disappears when iterating!) |

#### Example

```lua
local data, err = json.parse('{"a":1,"b":[10,20],"flag":true}')
print(data.a)         --> 1
print(data.b[1])      --> 10
print(data.flag)      --> true
```

#### Invalid JSON example

```lua
local v, e = json.parse("{ broken json }")
if not v then
    print("Parse failed:", e)
end
```

***

### Lua → JSON: `json.stringify` / `json.encode`

```lua
json_str, err = json.stringify(value)
json_str, err = json.encode(value)
```

#### Parameters

* **value** — any Lua value (table / string / number / boolean / nil)

#### Returns

* On success:\
  **string containing JSON**
* On failure:\
  `nil, "error message"`

#### Supported Lua Types

| Lua     | JSON                              |
| ------- | --------------------------------- |
| String  | `"text"`                          |
| Number  | `123` or `1.23`                   |
| Boolean | `true` / `false`                  |
| Table   | Object or Array *(auto-detected)* |
| nil     | `null` *(inside tables only)*     |

#### Array vs Object Detection

Lua tables are encoded as JSON arrays **only** if they contain:

* continuous integer keys
* starting from `1`
* with no gaps

Otherwise they become JSON objects.

#### Example

```lua
local obj = {
    hello = "world",
    numbers = { 1, 2, 3 }
}

local json_str = json.stringify(obj)
print(json_str)
-- {"hello":"world","numbers":[1,2,3]}
```

#### Mixed Tables

Tables with both numeric and string keys become JSON objects:

```lua
local t = { [1] = "first", [3] = "third", foo = "bar" }
print(json.stringify(t))
-- {"3":"third","1":"first","foo":"bar"}
```

***

### Round-Trip Example

```lua
local original = {
    text = "hello",
    list = { 10, 20, 30 },
    nested = { a = 1, b = { "x", "y" } }
}

local encoded = json.stringify(original)
local decoded = json.parse(encoded)

-- decoded now matches `original`
```

***

### Null Handling

JSON `null` becomes **Lua `nil`**.

This means fields may “disappear” from tables:

```lua
local obj = json.parse('{"a":1,"b":null,"c":2}')
-- obj = { a = 1, c = 2 }
```

This is correct behavior and matches typical JSON–Lua conventions.

***

### Error Handling

All functions safely return:

```lua
nil, "error message"
```

Examples of failure:

* malformed JSON
* unsupported Lua type (function, userdata, thread)

***

### Summary

#### Functions Provided

| Function              | Description                |
| --------------------- | -------------------------- |
| `json.parse(str)`     | Parse JSON into Lua values |
| `json.decode(str)`    | Alias of parse             |
| `json.stringify(val)` | Encode Lua value into JSON |
| `json.encode(val)`    | Alias of stringify         |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/json-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
