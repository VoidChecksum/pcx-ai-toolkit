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
