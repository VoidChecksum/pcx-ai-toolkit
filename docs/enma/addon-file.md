> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/file.md).

# File

Registered with `register_addon_file(engine)`.

All file-touching operations require the `PERM_FILE` permission flag to be granted on the engine. Scripts without the permission will fail to compile any call that touches the filesystem:

```cpp
set_permissions(engine, enma::PERM_FILE);
```

## Stream API

`file_t` wraps an OS file handle. Open with `file_open(path, mode)`; the destructor closes the file at scope exit.

```cpp
file_t f = file_open("data.txt", "r");
if (f.is_open()) {
    while (!f.is_eof()) {
        string line = f.read_line();
        // ... process line ...
    }
}

file_t w = file_open("out.txt", "w");
w.write("hello");
w.flush();

file_t bin = file_open("img.dat", "rb");
int64 sz = bin.size();
bin.seek(1024);
int64 pos = bin.tell();
```

### Modes

Standard C fopen modes. `"r"`, `"w"`, `"a"`, `"rb"`, `"wb"`, `"ab"`, `"r+"`, `"w+"`.

### Methods

```cpp
bool   o = f.is_open()           // false if open failed
bool   e = f.is_eof()
string s = f.read_all()          // read from current pos to end
string l = f.read_line()         // line without trailing \n/\r\n
int64  n = f.write(string)       // bytes written
int64  sz = f.size()
int64  p  = f.tell()
f.seek(pos)
f.flush()
f.close()                         // dtor also closes
```

## Whole-file convenience

Path-based shortcuts for one-shot reads/writes. Strings:

```cpp
string content = file_read("config.json")
bool   ok      = file_write("log.txt", "line1\nline2\n")
```

Bytes (uint8 stride-1 array):

```cpp
array bytes = file_read_bytes("img.png")
bool  ok    = file_write_bytes("out.bin", bytes)
```

## Filesystem operations

File-level:

```cpp
bool  exists = file_exists(path)
bool  ok     = file_remove(path)
bool  ok     = file_rename(from, to)
bool  ok     = file_copy(src, dst)         // overwrites dst
int64 sz     = file_size(path)             // -1 on error
int64 mt     = file_mtime(path)            // Unix seconds, -1 on error
```

Directory-level:

```cpp
bool  d     = dir_exists(path)
bool  ok    = dir_create(path)             // succeeds if already exists
array names = dir_list(path)               // filenames (not full paths)
array all   = dir_walk(path)               // recursive; full paths
```

## Permissions

The permission gate is enforced at compile time: calling any gated native without `PERM_FILE` granted fails the module compile with a permission error. This lets hosts sandbox untrusted scripts by default.

```cpp
// Host code:
auto* e = enma::create();
enma::register_all_addons(e);
// no set_permissions call -> file ops unavailable to all scripts

// vs. privileged script path:
enma::set_permissions(e, enma::PERM_FILE);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/file.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
