> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/json-api.md).

# Json API

The AngelScript JSON API provides robust parsing and encoding of JSON directly into native AngelScript structures.\
JSON objects map to **dictionary** objects, using standard AngelScript types.

This API mirrors the Lua JSON API and is designed to behave identically where possible.

***

### Overview

Available functions:

| Function                             | Description                               |
| ------------------------------------ | ----------------------------------------- |
| `json_parse(text, result, error)`    | Parse JSON text into a `dictionary`       |
| `json_decode(text, result, error)`   | Alias of `json_parse`                     |
| `json_stringify(value, json, error)` | Convert a `dictionary` into a JSON string |
| `json_encode(value, json, error)`    | Alias of `json_stringify`                 |

All functions return **true on success** and **false on failure**, with detailed error messages.

***

### JSON → Dictionary

#### `bool json_parse(const string &in text, dictionary &out result, string &out error)`

#### `bool json_decode(const string &in text, dictionary &out result, string &out error)`

Parses a JSON string and converts it into a nested AngelScript `dictionary`.

#### Parameters

| Name     | Type         | Description                                 |
| -------- | ------------ | ------------------------------------------- |
| `text`   | `string`     | JSON text to parse                          |
| `result` | `dictionary` | Output dictionary filled with parsed values |
| `error`  | `string`     | Error message if the function fails         |

#### JSON → AngelScript Type Mapping

| JSON                 | AngelScript                       |
| -------------------- | --------------------------------- |
| Object `{}`          | `dictionary` (recursively nested) |
| String `"text"`      | `string`                          |
| Number `123`, `4.5`  | `double`                          |
| Boolean `true/false` | `double` (`1.0`/`0.0`)            |
| null                 | *field omitted*                   |
| Array `[...]`        | *(currently skipped)*             |

#### Example

```cpp
dictionary d;
string err;

bool ok = json_parse("{\"a\":1, \"b\":\"hello\"}", d, err);
if (!ok)
{
    log_error("JSON parse failed: " + err);
    return;
}

double a;
string b;

d.get("a", a);    // 1.0
d.get("b", b);    // "hello"
```

***

### Dictionary → JSON

#### `bool json_stringify(const dictionary &in value, string &out json, string &out error)`

#### `bool json_encode(const dictionary &in value, string &out json, string &out error)`

Converts a dictionary (and any nested dictionaries) into valid JSON text.

#### Parameters

| Name    | Type         | Description                         |
| ------- | ------------ | ----------------------------------- |
| `value` | `dictionary` | The object to convert into JSON     |
| `json`  | `string`     | Output JSON text                    |
| `error` | `string`     | Error message if the function fails |

#### AngelScript → JSON Type Mapping

| AngelScript        | JSON        |
| ------------------ | ----------- |
| `double`           | number      |
| `string`           | string      |
| `bool`             | boolean     |
| `dictionary@`      | JSON object |
| `null dictionary@` | `null`      |
| *(any other type)* | error       |

#### Example

```cpp
dictionary d;
d.set("name", "Player1");
d.set("score", 120.0);
d.set("alive", true);

string json;
string err;

if (!json_stringify(d, json, err))
{
    log_error("Stringify failed: " + err);
}
else
{
    log("JSON: " + json);
}
```

Output:

```cpp
{"name":"Player1","score":120,"alive":true}
```

***

### Nesting Example

JSON objects automatically map to nested dictionaries:

```cpp
string text = """
{
    "player": {
        "name": "Alice",
        "pos": { "x": 10, "y": 20 }
    }
}
""";

dictionary root;
string err;

json_parse(text, root, err);

dictionary@ player;
root.get("player", @player);

string name;
dictionary@ pos;
double px, py;

player.get("name", name);
player.get("pos", @pos);
pos.get("x", px);
pos.get("y", py);
```

***

### Null Behavior

JSON `null` becomes **nonexistent key**:

```cpp
{"a":1,"b":null,"c":2}
```

Becomes:

```cpp
d.exists("a") == true
d.exists("b") == false
d.exists("c") == true
```

***

### Unsupported Types

The AngelScript dictionary can technically store any type, but the JSON stringifier only supports:

* `double`
* `string`
* `bool`
* `dictionary@`

Anything else causes:

```cpp
json_stringify: unsupported value type in dictionary
```

***

### Arrays

JSON arrays (`[ ... ]`) are **currently skipped**.\
If you need them, support can be added using `array<T>` or `CScriptArray`.

***

### Full Roundtrip Example

```cpp
dictionary d;
d.set("value", 123.0);
d.set("name", "Test");
d.set("ok", true);

dictionary inner;
inner.set("x", 10.0);
inner.set("y", 20.0);
d.set("pos", @inner);

string json, err;
json_stringify(d, json, err);

// parse it back
dictionary back;
json_parse(json, back, err);
```

***

### Full API Test

```cpp
void DumpDict(const string &in label, dictionary &in d)
{
    log(label);
    
    array<string>@ keys = d.getKeys();
    for (uint i = 0; i < keys.length(); i++)
    {
        string k = keys[i];
        // Try double first
        double dv;
        string sv;
        bool gotDouble = d.get(k, dv);
        bool gotString = d.get(k, sv);
        
        string vStr;
        if (gotDouble)
        vStr = "double " + k + " = " + dv;
        else if (gotString)
        vStr = "string " + k + " = \"" + sv + "\"";
        else
        vStr = "key " + k + " (unsupported type in dump)";
        
        log("  " + vStr);
    }
}

void TestBasicParse()
{
    log("[1] Basic json_parse / json_decode");
    
    const string jsonText = """
    {
        "number": 123,
        "float":  3.14,
        "bool_true": true,
        "bool_false": false,
        "text": "hello",
        "object": { "x": 10, "y": 20 }
    }
    """;
    
    dictionary d;
    string err;
    
    if (!json_parse(jsonText, d, err))
    {
        log_error("  [FAIL] json_parse failed: " + err);
        return;
    }
    log("  [ OK ] json_parse succeeded");
    DumpDict("  Dump of parsed dictionary:", d);
    
    // Basic checks
    double num = 0;
    double flt = 0;
    string txt;
    
    if (d.get("number", num) && num == 123)
    log("  [ OK ] number == 123");
    else
    log_error("  [FAIL] number != 123");
    
    if (d.get("float", flt) && flt > 3.13 && flt < 3.15)
    log("  [ OK ] float ~= 3.14");
    else
    log_error("  [FAIL] float ~= 3.14");
    
    if (d.get("text", txt) && txt == "hello")
    log("  [ OK ] text == \"hello\"");
    else
    log_error("  [FAIL] text != \"hello\"");
    
    // bools are stored as doubles (1.0 / 0.0)
    double bt = 0, bf = 1;
    d.get("bool_true", bt);
    d.get("bool_false", bf);
    if (bt == 1.0 && bf == 0.0)
    log("  [ OK ] bool_true/false mapped to 1.0/0.0");
    else
    log_error("  [FAIL] bool mapping incorrect");
    
    // Test alias json_decode
    dictionary d2;
    string err2;
    if (json_decode("{\"a\":1,\"b\":2}", d2, err2))
    log("  [ OK ] json_decode succeeded");
    else
    log_error("  [FAIL] json_decode failed: " + err2);
}

void TestInvalidParse()
{
    log("\n[2] Invalid JSON parse test");
    
    dictionary d;
    string err;
    
    const string badJson = "{ invalid json !!! }";
    bool ok = json_parse(badJson, d, err);
    if (!ok)
    {
        log("  [ OK ] json_parse returned false for invalid JSON");
        log("        error: " + err);
    }
    else
    {
        log_error("  [FAIL] json_parse unexpectedly succeeded on invalid JSON");
    }
}

void TestStringifyRoundtrip()
{
    log("\n[3] json_stringify / json_encode roundtrip");
    
    dictionary d;
    d.set("hello", "world");
    d.set("num", 42.0);          // numbers are stored as double
    d.set("float", 1.5);
    d.set("flag_bool", true);    // bool (script side)
    d.set("flag_num", 1.0);      // numeric boolean
    
    // nested object
    dictionary nested;
    nested.set("x", 10.0);
    nested.set("y", 20.0);
    d.set("nested", @nested);
    
    DumpDict("  Original dictionary:", d);
    
    string json;
    string err;
    
    if (!json_stringify(d, json, err))
    {
        log_error("  [FAIL] json_stringify failed: " + err);
        return;
    }
    
    log("  [ OK ] json_stringify succeeded");
    log("  JSON: " + json);
    
    // Roundtrip: parse back
    dictionary back;
    string err2;
    if (!json_parse(json, back, err2))
    {
        log_error("  [FAIL] parse(stringify(...)) failed: " + err2);
        return;
    }
    
    log("  [ OK ] parse(stringify(...)) succeeded");
    DumpDict("  Decoded dictionary:", back);
    
    // Test alias json_encode
    string json2, err3;
    if (json_encode(d, json2, err3))
    log("  [ OK ] json_encode succeeded: " + json2);
    else
    log_error("  [FAIL] json_encode failed: " + err3);
}

void TestNullAndArrays()
{
    log("\n[4] Null and array handling note");
    
    const string txt = """
    {
        "a": 1,
        "b": null,
        "c": [1,2,3]
    }
    """;
    
    dictionary d;
    string err;
    
    if (!json_parse(txt, d, err))
    {
        log_error("  [FAIL] parse failed: " + err);
        return;
    }
    
    DumpDict("  Parsed dictionary:", d);
    
    // "b" is null -> omitted
    double a = 0;
    bool hasB = d.exists("b");
    d.get("a", a);
    
    if (a == 1.0 && !hasB)
    log("  [ OK ] null field skipped, 'a' present");
    else
    log_error("  [FAIL] null or 'a' handling incorrect");
    
    // "c" is an array -> currently skipped
    if (!d.exists("c"))
    log("  [ OK ] array key 'c' skipped as expected");
    else
    log_error("  [FAIL] array key 'c' unexpectedly present");
}

int main()
{
    log("=== JSON API Test Begin (AngelScript) ===");
    
    TestBasicParse();
    TestInvalidParse();
    TestStringifyRoundtrip();
    TestNullAndArrays();
    
    log("=== JSON API Test End ===");
    return 0;
}

```

***

### Summary of Functions

| Function                             | Description                |
| ------------------------------------ | -------------------------- |
| `json_parse(text, result, error)`    | Parse JSON into dictionary |
| `json_decode(text, result, error)`   | Alias of parse             |
| `json_stringify(value, json, error)` | Convert dictionary to JSON |
| `json_encode(value, json, error)`    | Alias of stringify         |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/json-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
