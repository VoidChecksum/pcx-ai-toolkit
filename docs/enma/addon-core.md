> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/core.md).

# Core

Registered with `register_addon_core(engine)`.

> Runtime functions (heap, budget, events, coroutines, counters, assert, time\_ms) are auto-registered by the engine, no addon needed.

## Output

```c
print("hello")            // no newline
println("hello")           // with newline
println("x = " + x)        // concat
print(42)                  // int → string via .convert()
print(3.14)                // float → string
print(true)                // "true"/"false"
print('A')                 // char → single-char string
println(format("x={d} y={f}", x, y))   // format helper
```

Non-string args auto-convert via the `string` type's `.convert(...)` table.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/core.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
