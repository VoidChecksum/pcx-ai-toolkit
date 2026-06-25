> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/filesystem-api.md).

# Filesystem API

Sandboxed filesystem access for enma scripts. Every call is gated by the `file_system_access` permission. Without it, calls return a failure value (`false` / `0` / empty array) and never throw.

## Sandbox

Paths are interpreted relative to the script's per-user data directory. Scripts cannot reach outside that root.

Rejected at the path-validation step (returns failure without touching disk):

* absolute paths — `C:\config`, `/etc/hosts`
* UNC paths — `\\server\share`
* parent traversals — `..\..\elsewhere`
* leading slashes — `/foo`, `\foo`
* embedded `:`, `\n`, `\r`, `\0`

Forward and backslashes are both accepted internally; pick one and stay consistent.

## Quick reference

| Operation                      | Native                                                                     |
| ------------------------------ | -------------------------------------------------------------------------- |
| Create / overwrite a text file | `fs_create_file(path, data)`                                               |
| Create a directory             | `fs_create_directory(path)`                                                |
| Test existence                 | `fs_file_exists(path)` / `fs_dir_exists(path)`                             |
| Delete                         | `fs_delete_file(path)` / `fs_delete_directory(path)`                       |
| File size                      | `fs_file_size(path)`                                                       |
| Read text                      | `fs_read_file(path)`                                                       |
| Write / append text            | `fs_write_file(path, data)` / `fs_append_file(path, data)`                 |
| Read binary                    | `fs_read_file_binary(path)`                                                |
| Write / append binary          | `fs_write_file_binary(path, bytes)` / `fs_append_file_binary(path, bytes)` |
| List entries                   | `fs_list_files(path)` / `fs_list_dirs(path)` / `fs_list_all(path)`         |

## File operations

```cpp
bool   fs_create_file(string path, string data);
bool   fs_create_directory(string path);
bool   fs_file_exists(string path);
bool   fs_dir_exists(string path);
bool   fs_delete_file(string path);
bool   fs_delete_directory(string path);
int64  fs_file_size(string path);
```

* `fs_create_file` writes `data` as the file's complete contents (UTF-8). Overwrites if the file already exists. Empty `data` creates a zero-byte file.
* `fs_create_directory` creates the directory and any missing parents.
* `fs_delete_directory` succeeds only when the target directory is empty.
* `fs_file_size` returns `0` for missing files (indistinguishable from a real zero-byte file — use `fs_file_exists` first if you need to disambiguate).

```cpp
if (!fs_dir_exists("configs"))
    fs_create_directory("configs");
if (!fs_create_file("configs/active.json", "{\"version\":1}"))
    println("[fs] write failed (permission?)");
```

## Text I/O

```cpp
string fs_read_file(string path);
bool   fs_write_file(string path, string data);
bool   fs_append_file(string path, string data);
```

* `fs_read_file` returns the file's bytes interpreted as UTF-8. Returns an **empty string** on missing file / read failure / permission denied — distinguish from a real empty file via `fs_file_exists` if it matters.
* `fs_write_file` overwrites; `fs_append_file` appends. Both return `true` on success, `false` on failure.

```cpp
fs_write_file("state/last_target.txt", "weapon_t1_assault");

string saved = fs_read_file("state/last_target.txt");
if (saved.length() > 0)
    set_target(saved);
```

## Binary I/O

```cpp
array<uint8> fs_read_file_binary(string path);
bool         fs_write_file_binary(string path, array<uint8> bytes);
bool         fs_append_file_binary(string path, array<uint8> bytes);
```

Use these for opaque blobs (saved offsets, screenshots, packet captures). A missing or unreadable file yields an empty array. Empty-input writes succeed and produce a zero-byte file; empty-input appends are a no-op (still return `true`).

```cpp
array<uint8> header;
header.push(0x4D); header.push(0x5A);    // "MZ"
fs_write_file_binary("dumps/probe.bin", header);

array<uint8> back = fs_read_file_binary("dumps/probe.bin");
print("read " + cast<string>(back.length()) + " bytes");
```

## Directory listing

```cpp
array<string> fs_list_files(string path);
array<string> fs_list_dirs(string path);
array<string> fs_list_all(string path);
```

Returns the **basenames** of entries (no path prefixes) in the requested directory. No recursion — descend manually by calling again with the joined relative path. A missing directory or permission denial yields an empty array. Entry order is filesystem-dependent.

```cpp
array<string> configs = fs_list_files("configs");
for (string name : configs)
{
    string body = fs_read_file("configs/" + name);
    // ...
}
```

## Pitfalls and correct failure handling

Filesystem natives collapse failures into falsy values and never throw. Check existence before reading when empty data is valid.

```cpp
string path = "configs/active.json";
if (!fs_file_exists(path)) {
    println("[fs] missing file");
} else {
    string data = fs_read_file(path);
    // data may legitimately be empty here.
}
```

For sizes, `0` means either a zero-byte file or failure:

```cpp
if (fs_file_exists(path)) {
    int64 size = fs_file_size(path);
    println("size=" + cast<string>(size));
}
```

Directory listing is non-recursive and returns basenames only. Empty array means either no entries, missing directory, permission denial, or I/O failure, so check `fs_dir_exists(path)` first when it matters.

## Failure modes

Every native handles every failure the same way: returns a falsy value (`false` / `0` / empty). The script never sees an exception from the FS layer.

| Cause                                                     | Return                                                                                                             |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `file_system_access` permission off                       | `false` / `0` / empty                                                                                              |
| Path validation fails (absolute, UNC, `..`, control char) | `false` / `0` / empty                                                                                              |
| Target file/directory missing                             | `false` / `0` / empty (writes that need a parent will fail if the parent is missing — `fs_create_directory` first) |
| Underlying I/O error (disk full, locked file, etc.)       | `false` / `0` / empty                                                                                              |

## Sandbox tests

Every escape attempt below returns `false` / empty without touching disk:

```cpp
fs_create_file("C:\\evil.txt", "x");          // false: absolute path
fs_create_file("/etc/passwd", "x");           // false: absolute /
fs_create_file("\\\\server\\f", "x");         // false: UNC
fs_create_file("../escape.txt", "x");         // false: parent traversal
fs_create_file("ok/../escape.txt", "x");      // false: nested traversal
```

## Permissions

Enabled via the script's `permissions` block. The flag is `file_system_access`. With it off, every call short-circuits before touching disk — reads return empty, writes silently no-op. Check with `fs_file_exists` after a write if your logic depends on the operation having succeeded.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/filesystem-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
