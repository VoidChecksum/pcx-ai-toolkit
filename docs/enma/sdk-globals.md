> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/globals.md).

# Globals

## Setting Globals

Inject values into the script's global scope:

```cpp
set_global(mod, "max_hp", 100);
set_global(mod, "player_id", 42);
```

The script can read these as regular global variables:

```cpp
int32 main() {
    println(max_hp);  // 100
    return 0;
}
```

## Reading Globals

```cpp
int64_t score = get_global(mod, "score");
```

## Checking Existence

```cpp
if (has_global(mod, "score")) {
    int64_t score = get_global(mod, "score");
}
```

## Direct Pointer Access

Direct pointer to global storage (skips the call overhead):

```cpp
int64_t* hp_ptr = get_global_ptr(mod, "player_hp");
*hp_ptr = 100;          // write
int64_t hp = *hp_ptr;   // read, no function call overhead
```

The pointer is valid for the lifetime of the module.

## Listing All Globals

```cpp
std::vector<std::string> names;
std::vector<int64_t> values;
list_globals(mod, names, values);

for (size_t i = 0; i < names.size(); ++i) {
    printf("%s = %lld\n", names[i].c_str(), values[i]);
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/globals.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
