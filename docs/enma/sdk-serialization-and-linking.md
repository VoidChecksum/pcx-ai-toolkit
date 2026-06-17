> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/sdk-guide/serialization-and-linking.md).

# Serialization & Linking

## Precompiled Binaries (.emb)

Compile once, distribute the binary; no source required at runtime.

### Serialize

```cpp
module_t* mod = compile_file(e, "library.em");

std::vector<uint8_t> data;
serialize(mod, data);  // keep_debug=true by default

// write to file
FILE* f = fopen("library.emb", "wb");
fwrite(data.data(), 1, data.size(), f);
fclose(f);
```

#### keep\_debug — strip source paths for distribution

`serialize(module_t*, vector<uint8_t>&, bool keep_debug = true)`

When `keep_debug=false`, the serializer drops the `source_map` (per-IR file/line/column) and `debug_functions` (per-fn locals with names) tables. Use this for marketplace publishing so an uploader's absolute source path isn't baked into every record. Trade: deserialized modules have `get_last_executed_line` returning 0 and empty stack traces at runtime.

```cpp
serialize(mod, data, /*keep_debug*/ false);
```

The body of the `.emb` is also XOR-obfuscated with a per-file 32-byte salt stored in the header (k\_emb\_version 4). Defeats casual `strings <file>` inspection of fixup keys, native names, struct field names. Decryption happens transparently inside `deserialize` — no caller-side change.

### Deserialize

```cpp
// read from file
std::vector<uint8_t> data = read_binary_file("library.emb");

module_t* mod = deserialize(e, data.data(), data.size());
context_t* ctx = create_context(mod);
execute(ctx, "main");
```

## Linking Multiple Modules

Combine separately compiled modules, resolving cross-module calls.

```cpp
module_t* math_mod = compile_file(e, "math.em");
module_t* game_mod = compile_file(e, "game.em");

const char* names[] = { "math", "game" };
module_t*   mods[]  = { math_mod, game_mod };
module_t*   linked  = link(e, names, mods, 2);

context_t* ctx = create_context(linked);
execute(ctx, "main");
```

In the script, linked modules are accessed by their name prefix:

```cpp
// game.em can call:
int32 r = math::sqrt_int(16);
```

## Module Cleanup

```cpp
module_destroy(math_mod);
module_destroy(game_mod);
module_destroy(linked);
```

Destroy each module separately. The linked module does not own its inputs.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/sdk-guide/serialization-and-linking.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
