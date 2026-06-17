> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/modules.md).

# Modules

## Importing Modules

The `import` statement loads another Enma module. Imported symbols are namespaced.

```cpp
import scanner

int32 main() {
    scanner::init();
    scanner::run();
    return 0;
}
```

### Aliased Imports

```cpp
import scanner as sc

sc::init();
```

### Path Imports

Import from an explicit file path:

```cpp
import "libs/math_utils.em"
```

## Module Resolution

When you write `import scanner`, the compiler searches for:

1. `scanner.emb` (precompiled binary) in module paths
2. `scanner.em` (source file) in module paths and include paths

`.emb` files are tried first, then `.em` source as fallback.

Configure search paths from the SDK:

```cpp
add_module_path(engine, "modules/");
add_include_path(engine, "includes/");
```

## Precompiled Modules (.emb)

Enma modules can be compiled to a binary format (`.emb`) for distribution without source code. The SDK provides `serialize()` and `deserialize()` for this.

Precompiled modules expose their public functions as `extern` declarations in the importer's namespace. Functions starting with `_` are considered internal and hidden.

Use `[[export]]` to explicitly control which functions are visible:

```cpp
[[export]]
int32 public_fn() { return 42; }

int32 private_fn() { return 1; }
// private_fn is hidden when compiled to .emb
```

## Linking Multiple Modules

The SDK's `link()` function combines multiple compiled modules into a single unit, resolving cross-module references:

```cpp
import math_lib
import string_lib

int32 main() {
    float64 r = math_lib::sqrt(2.0);
    string s = string_lib::format(r);
    return 0;
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/modules.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
