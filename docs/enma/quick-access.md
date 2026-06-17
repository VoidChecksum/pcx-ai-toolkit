> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/quick-access.md).

# Quick Access

[**Basics**](lang-basics.md) - Types, variables, constants, operators, control flow

[**Functions**](lang-functions.md)- Parameters, defaults, ref/out, variadic, lambdas, closures

[**Pointers**](lang-pointers.md) - Heap pointers, address-of, `.`/`->`, refs, null, escape rules

[**Structs & Classes**](lang-structs-and-classes.md) - Value types, reference types, inheritance, interfaces, operator overloading

[**Templates**](lang-templates.md) - Generic structs and functions, monomorphization

[**Advanced**](lang-advanced.md) - Delegates, namespaces, coroutines, exceptions, heap ops, FFI, static\_assert, constexpr / compile-time evaluation

[**Annotations**](lang-annotations.md) - noescape, packed, align, reflect, serialize, export, noopt, dll, custom

[**Modules** ](lang-modules.md)- import, .emb precompiled binaries, linking

[**Preprocessor** ](lang-pre-processor.md)- #define, #ifdef, #include

### SDK Guide

[**Quick Start**](sdk-quick-start.md) - Minimal embed example

[**Engine Lifecycle**](sdk-engine-lifecycle.md) - create, configure, destroy

[**Compilation** ](sdk-compilation.md)- Compile from source or file

[**Execution**](sdk-execution.md) - Contexts, execute, return values

[**Calling Functions**](sdk-calling-functions.md) - Pass arguments, strings, floats

[**Globals**](sdk-globals.md) - Set, get, list, direct pointer access

[**Type Registration**](sdk-type-registration.md) - Full type\_builder API with fields, methods, operators, subscript, iteration

[**Native Functions**](sdk-native-functions.md) - Register host functions callable from scripts

[**Hot Reload** ](sdk-hot-reload.md)- Replace script code at runtime

[**Serialization & Linking**](sdk-serialization-and-linking.md) - .emb binaries, multi-module linking

[**Introspection**](sdk-introspection.md) - List functions, query annotations, IR dump

[**Lifecycle & RAII**](sdk-lifecycle.md) - Memory model, scope-drop, destructors, escape rules

[**Debug & Heap**](sdk-debug-and-gc.md) - Debug hooks, execution budget, heap stats

[**Error Handling**](sdk-error-handling.md) - Compile and runtime error reporting

[**Safety**](sdk-safety.md) - Fault trapping, sandboxing, permissions, threading

[**Custom Addons** ](sdk-custom-addons.md)- Build your own addon from scratch

[**API Reference**](sdk-api-reference.md) - Every SDK function in one page

### Pre-built Addons

[**Core**](addon-core.md) - Output (print functions for ints, floats, strings, bools, chars)

[**Strings** ](addon-strings.md)- String methods and standalone string functions

[**Arrays** ](addon-arrays.md)- Array methods for manipulation, search, sorting, iteration

[**Maps** ](addon-maps.md)- Map creation, access, iteration methods

[**Math** ](addon-math.md)- Trigonometry, power, rounding, float/int utilities, constants, random

[**SIMD** ](addon-simd.md)- SSE2 vector arithmetic + packed ops on stride-1/2/4 arrays (int8/16/32, float32), bitwise

[**Variant** ](addon-variant.md)- Open tagged union keyed by type\_id; holds any registered type

[**Atomic** ](addon-atomic.md)- `atomic_int32` / `atomic_int64` + memory barriers

[**Bits** ](addon-bits.md)- popcount, clz, ctz, rotl, rotr, bswap, parity, bit\_reverse

[**Time** ](addon-time.md)- µs-since-epoch, calendar, ISO 8601, sleep, arithmetic

[**Regex** ](addon-regex.md)- matches, find, first, find\_all, replace, split, groups

[**File** ](addon-file.md)- `file_t` + free fns (gated by `PERM_FILE`)

[**Thread** ](addon-thread.md)- mutex, lock\_guard, cond\_var

[**Vectors** ](addon-vec.md)- vec2 / vec3 / vec4 with operators + scalar helpers

[**hash\_set\<T>** ](addon-hash_set.md)- generic hashed set for scalar T

[**sorted\_map\<K,V>** ](addon-sorted_map.md)- generic ordered map for scalar K/V

[**list\<T>** ](addon-list.md)- generic double-ended container; O(1) push/pop both ends, random access

[**JSON** ](addon-json.md)- parse, stringify, navigable `json_value` tree


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
