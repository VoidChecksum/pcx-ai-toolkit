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

Same scalar-only caveat as [hash\_set](/enma/addons/hash_set.md): `K` and `V` each must fit in 64 bits and order/equate by raw bits. Works for integer, bool, float-bits, pointer. Not suitable for string keys.

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
