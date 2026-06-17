> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/hot-reload.md).

# Hot Reload

Replace a module's code at runtime without destroying the engine or losing registered types.

## Basic Reload

```cpp
const char* new_src = R"(
    int32 main() {
        println("updated version!");
        return 2;
    }
)";
bool ok = reload(mod, new_src, strlen(new_src), "script.em");
```

## Running the New Code

Existing contexts pick up the new code on the next `execute()` call, no need to recreate them:

```cpp
execute(ctx, "main");                        // runs v1
reload(mod, new_src, len, "script.em");
execute(ctx, "main");                        // runs v2 on the same ctx
```

## Typical Hot Reload Loop

```cpp
module_t* mod = compile_file(e, "game.em");
context_t* ctx = create_context(mod);

while (running) {
    if (file_changed("game.em")) {
        std::string src = read_file("game.em");
        reload(mod, src.c_str(), src.size(), "game.em");
    }
    execute(ctx, "update");
}
```

Globals, registered types, and native functions persist; only the script code is replaced.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/hot-reload.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
