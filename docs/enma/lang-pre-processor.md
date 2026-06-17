> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/pre-processor.md).

# Pre Processor

C-style preprocessor running before parsing: macros, conditional compilation, file inclusion.

## Defines

```cpp
#define MAX_HP 100
#define SQUARE(x) ((x) * (x))

int32 hp = MAX_HP;
int32 area = SQUARE(5);  // 25
```

## Conditional Compilation

Directives: `#ifdef`, `#ifndef`, `#else`, `#elif`, `#endif`, `#undef`, `#pragma`.

```cpp
#ifdef DEBUG
    println("debug mode");
#else
    // release mode
#endif
```

Define preprocessor symbols from the SDK:

```cpp
define(engine, "DEBUG", "1");
define(engine, "PLATFORM", "windows");
```

Then use in scripts:

```cpp
#ifdef PLATFORM
    println("platform defined");
#endif
```

## Include

Include another source file. The contents are inserted at the include point.

```cpp
#include "common.em"
#include "types.em"
```

Include paths are configured from the SDK:

```cpp
add_include_path(engine, "includes/");
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/pre-processor.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
