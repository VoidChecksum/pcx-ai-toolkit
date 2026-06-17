> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/compilation.md).

# Compilation

## Compile from Source

```cpp
const char* src = "int32 main() { return 42; }";
module_t* mod = compile(e, src, strlen(src), "script.em");
```

The filename is used for error messages and source maps; it doesn't need to be a real file.

## Compile from File

```cpp
module_t* mod = compile_file(e, "scripts/game.em");
```

Include and module paths are resolved relative to the engine's configured paths.

## Module Cleanup

```cpp
module_destroy(mod);
```

Destroy all contexts created from this module before destroying the module.

## Checking for Errors

Compilation errors surface via the engine's error state:

```cpp
module_t* mod = compile(e, src, len, "script.em");
error_info err = last_error(e);
if (err.code != 0) {
    printf("[%s:%d:%d] %s\n",
        err.file.c_str(), err.line, err.column, err.message.c_str());
}
```

## What Compilation Produces

`compile()` runs: lexer → preprocessor → parser → type checker → IR builder → optimizer passes → register allocator → x64 codegen. The module holds native machine code ready to execute.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/compilation.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
