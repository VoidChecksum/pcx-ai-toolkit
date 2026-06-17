> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/quick-access.md).

# Quick Access

[**Basics**](/enma/language-guide/basics.md) - Types, variables, constants, operators, control flow

[**Functions**](/enma/language-guide/functions.md)- Parameters, defaults, ref/out, variadic, lambdas, closures

[**Pointers**](/enma/language-guide/pointers.md) - Heap pointers, address-of, `.`/`->`, refs, null, escape rules

[**Structs & Classes**](/enma/language-guide/structs-and-classes.md) - Value types, reference types, inheritance, interfaces, operator overloading

[**Templates**](/enma/language-guide/templates.md) - Generic structs and functions, monomorphization

[**Advanced**](/enma/language-guide/advanced.md) - Delegates, namespaces, coroutines, exceptions, heap ops, FFI, static\_assert, constexpr / compile-time evaluation

[**Annotations**](/enma/language-guide/annotations.md) - noescape, packed, align, reflect, serialize, export, noopt, dll, custom

[**Modules** ](/enma/language-guide/modules.md)- import, .emb precompiled binaries, linking

[**Preprocessor** ](/enma/language-guide/pre-processor.md)- #define, #ifdef, #include

### SDK Guide

[**Quick Start**](/enma/sdk-guide/quick-start.md) - Minimal embed example

[**Engine Lifecycle**](/enma/sdk-guide/engine-lifecycle.md) - create, configure, destroy

[**Compilation** ](/enma/sdk-guide/compilation.md)- Compile from source or file

[**Execution**](/enma/sdk-guide/execution.md) - Contexts, execute, return values

[**Calling Functions**](/enma/sdk-guide/calling-functions.md) - Pass arguments, strings, floats

[**Globals**](/enma/sdk-guide/globals.md) - Set, get, list, direct pointer access

[**Type Registration**](/enma/sdk-guide/type-registration.md) - Full type\_builder API with fields, methods, operators, subscript, iteration

[**Native Functions**](/enma/sdk-guide/native-functions.md) - Register host functions callable from scripts

[**Hot Reload** ](/enma/sdk-guide/hot-reload.md)- Replace script code at runtime

[**Serialization & Linking**](/enma/sdk-guide/serialization-and-linking.md) - .emb binaries, multi-module linking

[**Introspection**](/enma/sdk-guide/introspection.md) - List functions, query annotations, IR dump

[**Lifecycle & RAII**](/enma/sdk-guide/lifecycle.md) - Memory model, scope-drop, destructors, escape rules

[**Debug & Heap**](/enma/sdk-guide/debug-and-gc.md) - Debug hooks, execution budget, heap stats

[**Error Handling**](/enma/sdk-guide/error-handling.md) - Compile and runtime error reporting

[**Safety**](/enma/sdk-guide/safety.md) - Fault trapping, sandboxing, permissions, threading

[**Custom Addons** ](/enma/sdk-guide/custom-addons.md)- Build your own addon from scratch

[**API Reference**](/enma/sdk-guide/api-reference.md) - Every SDK function in one page

### Pre-built Addons

[**Core**](/enma/addons/core.md) - Output (print functions for ints, floats, strings, bools, chars)

[**Strings** ](/enma/addons/strings.md)- String methods and standalone string functions

[**Arrays** ](/enma/addons/arrays.md)- Array methods for manipulation, search, sorting, iteration

[**Maps** ](/enma/addons/maps.md)- Map creation, access, iteration methods

[**Math** ](/enma/addons/math.md)- Trigonometry, power, rounding, float/int utilities, constants, random

[**SIMD** ](/enma/addons/simd.md)- SSE2 vector arithmetic + packed ops on stride-1/2/4 arrays (int8/16/32, float32), bitwise

[**Variant** ](/enma/addons/variant.md)- Open tagged union keyed by type\_id; holds any registered type

[**Atomic** ](/enma/addons/atomic.md)- `atomic_int32` / `atomic_int64` + memory barriers

[**Bits** ](/enma/addons/bits.md)- popcount, clz, ctz, rotl, rotr, bswap, parity, bit\_reverse

[**Time** ](/enma/addons/time.md)- µs-since-epoch, calendar, ISO 8601, sleep, arithmetic

[**Regex** ](/enma/addons/regex.md)- matches, find, first, find\_all, replace, split, groups

[**File** ](/enma/addons/file.md)- `file_t` + free fns (gated by `PERM_FILE`)

[**Thread** ](/enma/addons/thread.md)- mutex, lock\_guard, cond\_var

[**Vectors** ](/enma/addons/vec.md)- vec2 / vec3 / vec4 with operators + scalar helpers

[**hash\_set\<T>** ](/enma/addons/hash_set.md)- generic hashed set for scalar T

[**sorted\_map\<K,V>** ](/enma/addons/sorted_map.md)- generic ordered map for scalar K/V

[**list\<T>** ](/enma/addons/list.md)- generic double-ended container; O(1) push/pop both ends, random access

[**JSON** ](/enma/addons/json.md)- parse, stringify, navigable `json_value` tree


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/quick-access.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
