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
