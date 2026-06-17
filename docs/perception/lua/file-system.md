> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/file-system.md).

# File System

**API Folder Location** : C:\Users\\"UserName"\Documents\My Games\\

Filesystem API that allows scripts to read, write, and manage files **only inside the main scripting directory**.

Scripts **cannot** access, modify, create, or query files **outside** this directory.\
All paths must be **relative** and are automatically sandboxed for safety.

***

## **Overview**

The filesystem API provides the following capabilities:

* Create files
* Create directories
* Read files
* Check if a file exists
* List files or directories
* Delete files
* Delete directories

All functions operate only on paths **relative to the script directory**.

***

## **Path Rules**

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

## **Global Functions**

All filesystem functions are available as **global Lua functions**.

***

### `create_file(path, [data]) → boolean`

Creates or overwrites a file.

#### Example:

```lua
create_file("data/info.txt", "Hello World!")
```

***

### `create_directory(path) → boolean`

Creates a directory (non-recursive).

#### Example:

```lua
create_directory("data/logs")
```

***

### `read_file(path) → boolean, string`

Reads a file and returns `(success, contents)`.

#### Example:

```lua
local ok, text = read_file("data/info.txt")
if ok then
    print(text)
end
```

***

### `does_file_exist(path) → boolean`

Checks if a file exists.

#### Example:

```lua
if does_file_exist("data/info.txt") then
    print("found")
end
```

***

### `query_directory(path, include_dirs?, include_files?, extensions_table?) → boolean, table`

Lists the contents of a directory.

#### Parameters:

| Name               | Type    | Default  | Description                             |
| ------------------ | ------- | -------- | --------------------------------------- |
| `path`             | string  | required | Directory to list                       |
| `include_dirs`     | boolean | `true`   | Include subdirectories                  |
| `include_files`    | boolean | `true`   | Include files                           |
| `extensions_table` | table   | `nil`    | Filter by extensions, e.g. `{ ".txt" }` |

#### Example:

```lua
local ok, items = query_directory("data", true, true)
if ok then
    for i, name in ipairs(items) do
        print(name)
    end
end
```

#### Filter example:

```lua
local ok, jsons = query_directory("data", false, true, { ".json" })
```

***

### `delete_file(path) → boolean`

Deletes a file.

#### Example:

```lua
delete_file("data/old.txt")
```

***

### `delete_directory(path) → boolean`

Deletes a directory (may require the directory to be empty).

#### Example:

```lua
delete_directory("data/temp")
```

***

## **Example Test Script**

A simple script to confirm everything is working:

```lua
function main()
    print("=== FS TEST START ===")

    create_directory("fs_tests")
    create_file("fs_tests/test.txt", "hello test")

    local ok, data = read_file("fs_tests/test.txt")
    print("read ok:", ok, "data:", data)

    local ok_q, items = query_directory("fs_tests")
    if ok_q then
        for _, name in ipairs(items) do
            print(" -", name)
        end
    end

    delete_file("fs_tests/test.txt")
    delete_directory("fs_tests")

    print("=== FS TEST END ===")
    return 0;
end
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/file-system.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
