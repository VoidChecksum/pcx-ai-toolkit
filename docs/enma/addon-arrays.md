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
