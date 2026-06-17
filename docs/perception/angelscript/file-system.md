> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/file-system.md).

# File System

**API Folder Location** : C:\Users\\"UserName"\Documents\My Games\\

Filesystem API that allows scripts to read, write, and manage files **only inside the main scripting directory**.

Scripts **cannot** access, modify, create, or query files **outside** this directory.\
All paths must be **relative** and are automatically sandboxed for safety.

***

### Overview

The filesystem API provides the following capabilities:

* Create files
* Create directories
* Read files
* Check if a file exists
* List files or directories
* Delete files
* Delete directories

All functions are available as **global AngelScript functions**.

***

### Path Rules

To ensure safety and consistency:

#### ✔ Paths must be relative

Absolute paths such as:

```
/folder/file.txt
C:\temp\log.txt
```

are not allowed.

#### ✔ Parent-directory traversal is not allowed

Paths cannot contain:

```
..
```

#### ✔ Scripts cannot escape the main scripting directory

Every operation is automatically constrained to the script directory.

***

### Global Functions

#### `bool create_file(const string &in path, const string &in data = "")`

Creates or overwrites a file at the given relative path.

* **path** — relative file path under the main scripting directory
* **data** — optional file contents (defaults to empty)

```cpp
bool ok = create_file("data/info.txt", "Hello World!");
```

***

#### `bool create_directory(const string &in path)`

Creates a directory (non-recursive).

```cpp
bool ok = create_directory("data/logs");
```

***

#### `bool read_file(const string &in path, string &out data)`

Reads a file and returns its contents through an output parameter.

* Returns `true` on success, `false` if the file does not exist or could not be read.

```cpp
string text;
bool ok = read_file("data/info.txt", text);
if (ok)
{
    log("File contents: " + text);
}
```

***

#### `bool does_file_exist(const string &in path)`

Checks if a file exists.

```cpp
if (does_file_exist("data/info.txt"))
{
    log("File exists");
}
```

***

#### \`bool query\_directory(const string \&in path,

bool include\_dirs,\
bool include\_files,\
const array\<string> \&in extensions,\
array\<string> \&out entries)\`

Lists the contents of a directory.

**Parameters**

* `path` — relative directory path under the main scripting directory
* `include_dirs` — if `true`, include subdirectories in the results
* `include_files` — if `true`, include files in the results
* `extensions` — list of file extensions to include; pass an empty array for no filter
* `entries` — output array that will be filled with names (no directory prefix)

**Example**

```cpp
array<string> entries;
array<string> noFilter; // empty

bool ok = query_directory("data", true, true, noFilter, entries);
if (ok)
{
    for (uint i = 0; i < entries.length(); ++i)
    {
        log("Entry: " + entries[i]);
    }
}
```

**Filtered example**

```cpp
array<string> exts = { ".json" };
array<string> jsonFiles;

bool ok = query_directory("data", false, true, exts, jsonFiles);
if (ok)
{
    for (uint i = 0; i < jsonFiles.length(); ++i)
    {
        log("JSON: " + jsonFiles[i]);
    }
}
```

***

#### `bool delete_file(const string &in path)`

Deletes a file.

```cpp
bool ok = delete_file("data/old.txt");
```

***

#### `bool delete_directory(const string &in path)`

Deletes a directory.\
Depending on configuration, the directory may need to be empty.

```cpp
bool ok = delete_directory("data/temp");
```

***

#### `bool write_file_binary(const string &in path, const array<uint8> &in data)`

Writes raw bytes to a file (creates or overwrites).

* `path` — relative file path under the main scripting directory
* `data` — raw bytes to write

Returns `true` on success, `false` on failure.

***

#### `bool read_file_binary(const string &in path, array<uint8> &out data)`

Reads a file as raw bytes.

* `path` — relative file path under the main scripting directory
* `data` (out) — filled with file bytes on success

Returns `true` on success, `false` if the file does not exist or could not be read.

***

#### `bool append_file_binary(const string &in path, const array<uint8> &in data)`

Appends raw bytes to the end of a file.

* `path` — relative file path under the main scripting directory
* `data` — raw bytes to append

Returns `true` on success, `false` on failure.

***

#### `uint64 get_file_size(const string &in path)`

Returns the file size in bytes.

* `path` — relative file path under the main scripting directory

Returns the size in bytes. (If you want to document a failure value, pick one consistent rule like “returns 0 on missing file” and note it here.)

***

### Example Test Script

A simple AngelScript example that exercises all functions:

```cpp
int main()
{
    log("=== AS FS TEST START ===");

    // 1) Create a directory
    bool ok = create_directory("fs_tests");
    log("create_directory: " + string(ok ? "true" : "false"));

    // 2) Create a file
    ok = create_file("fs_tests/test.txt", "Hello from AngelScript FS API!\n");
    log("create_file: " + string(ok ? "true" : "false"));

    // 3) Read it back
    string data;
    ok = read_file("fs_tests/test.txt", data);
    log("read_file: " + string(ok ? "true" : "false"));
    if (ok)
        log("data = " + data);

    // 4) Check existence
    bool exists = does_file_exist("fs_tests/test.txt");
    log("does_file_exist: " + string(exists ? "true" : "false"));

    // 5) Query directory
    array<string> entries;
    array<string> noFilter;
    ok = query_directory("fs_tests", true, true, noFilter, entries);
    log("query_directory: " + string(ok ? "true" : "false"));
    if (ok)
    {
        for (uint i = 0; i < entries.length(); ++i)
            log("entry: " + entries[i]);
    }

    // 6) Delete file + directory
    ok = delete_file("fs_tests/test.txt");
    log("delete_file: " + string(ok ? "true" : "false"));

    ok = delete_directory("fs_tests");
    log("delete_directory: " + string(ok ? "true" : "false"));

    log("=== AS FS TEST END ===");
    return 1; // keep script loaded
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/file-system.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
