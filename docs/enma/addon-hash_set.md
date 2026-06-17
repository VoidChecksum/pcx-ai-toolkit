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
