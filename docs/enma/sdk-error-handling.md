> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/error-handling.md).

# Error Handling

## Error Info

Check the engine's error state after any operation:

```cpp
error_info err = last_error(e);
if (err.code != 0) {
    printf("[%s:%d:%d] %s\n",
        err.file.c_str(), err.line, err.column,
        err.message.c_str());
}
```

## Message-Only Check

```cpp
const char* msg = last_error_message(e);
if (msg && msg[0] != '\0') {
    printf("error: %s\n", msg);
}
```

## Error Codes

The `error_info.code` field indicates the error category:

* `0` = no error
* Parser errors = syntax problems in source code
* Type errors = type mismatches, undefined symbols
* Runtime errors = segfaults in JIT code, budget exhaustion

## Compile-Time Errors

```cpp
module_t* mod = compile(e, src, len, "script.em");
error_info err = last_error(e);
if (err.code != 0) {
    // compilation failed
    printf("compile error: %s\n", err.message.c_str());
    printf("  at %s:%d:%d\n", err.file.c_str(), err.line, err.column);
}
```

### Diagnostic shape

Compile errors include a one-line summary followed by a `hint:` line where applicable. Examples:

```cpp
cannot implicitly convert int32 to uint64 (signed/unsigned mismatch)
  hint: use cast<uint64>(...) to make the conversion explicit

return type mismatch: cannot implicitly convert float64 to int32 (would truncate float)
  hint: use cast<int32>(...) to make the conversion explicit

file_open() requires PERM_FILE, but engine has only PERM_NONE
  hint: call set_permissions(engine, PERM_FILE) before compile()
```

Permission errors name the missing flag (`PERM_FILE`, `PERM_FFI`) and the current grant.

## Runtime Errors

Runtime errors (segfaults, null dereferences) are caught by the JIT fault handler and mapped to source locations via the source map:

```cpp
bool ok = execute(ctx, "main");
if (!ok) {
    error_info err = last_error(e);
    printf("runtime error: %s\n", err.message.c_str());
}
```

## Exception Access

```cpp
if (exception_pending(mod)) {
    int64_t val  = exception_value(mod);   // the thrown value
    int64_t tid  = exception_type(mod);    // type hash of the thrown value
    printf("exception: value=%lld type=%llu\n", val, tid);
    exception_clear(mod);
}
```

The runtime fault handler clears exception state before returning control to the host. For uncaught throws after execution, check `last_error()`:

```cpp
bool ok = execute(ctx, "main");
if (!ok) {
    error_info err = last_error(e);
    // err contains the uncaught exception info
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/error-handling.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
