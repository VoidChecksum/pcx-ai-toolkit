> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/calling-functions.md).

# Calling Functions

## Call with Arguments

```cpp
int64_t args[] = { 10, 20 };
call(ctx, "add", args, 2);
int64_t result = return_value(ctx);  // 30
```

Arguments pass as `int64_t`. Floats must be bit-cast:

```cpp
double val = 3.14;
int64_t bits;
memcpy(&bits, &val, 8);

int64_t args[] = { bits };
call(ctx, "process_float", args, 1);

double result;
int64_t rbits = return_value(ctx);
memcpy(&result, &rbits, 8);
```

## Passing Strings

Allocate via Enma's heap:

```cpp
int64_t str = alloc_string(ctx, "hello world");
int64_t args[] = { str };
call(ctx, "process_text", args, 1);
```

Runtime manages the string's lifetime, don't free it manually.

## Reading String Returns

```cpp
execute(ctx, "get_name");
const char* name = return_string(ctx);
printf("name: %s\n", name);
```

The returned pointer is valid until the next call.

## Checking Function Existence

```cpp
if (has_function(mod, "on_tick")) {
    execute(ctx, "on_tick");
}
```

## Getting Parameter Count

```cpp
uint32_t params = function_param_count(mod, "add");  // 2
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/calling-functions.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
