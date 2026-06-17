> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/proc-api.md).

# Proc API

This API lets scripts inspect and modify the memory of external processes via a `process` userdata.\
Handles are created with `ref_process(...)` and released with `deref_process(process)`.

***

### 🔑 Process Handles

#### Userdata Type

All functions operate on a `process` userdata created by `ref_process`.

```lua
-- Get a process handle by PID
local proc = ref_process(1234)

-- Get a process handle by name
local proc = ref_process("notepad.exe")
```

If the process is not found, `ref_process` returns `nil`.

***

#### Referencing / Releasing

```lua
process = ref_process(pid_or_name)   -- global
deref_process(process)               -- global
```

* `ref_process(pid)` – `pid` is a number (Windows PID).
* `ref_process("name.exe")` – search by executable name.
* `deref_process(process)` – releases the reference; the userdata becomes invalid.
* You must also call `deref_process` if `process:alive()` returns `false`.

> Each Lua script keeps its own list of referenced processes internally.\
> Always call `deref_process(proc)` when you’re done.

***

### 🧬 Process Info

```lua
process:base_address()  --> number (uint64)
process:peb()           --> number (uint64)
process:pid()           --> number (uint)
process:alive()         --> bool
```

* `base_address()` – Image base address of the process.
* `peb()` – Address of the process’ PEB.
* `pid()` – Process ID.
* `alive()` -  Determines whether the process is currently alive and running.

***

#### Address Validity

```cpp
process:is_valid_address(address)   --> bool
```

Check if an address is mapped inside target process.

***

### 📖 Scalar Reads

All addresses are **virtual addresses** in the target process.

#### Unsigned Integers

```lua
process:ru8(addr)   --> uint8
process:ru16(addr)  --> uint16
process:ru32(addr)  --> uint32
process:ru64(addr)  --> uint64
```

Reads unsigned integers from `addr`.

***

#### Signed Integers

```lua
process:r8(addr)   --> int8
process:r16(addr)  --> int16
process:r32(addr)  --> int32
process:r64(addr)  --> int64
```

Reads signed integers from `addr`.

***

#### Floating Point

```lua
process:rf32(addr) --> float
process:rf64(addr) --> double
```

Reads floating point values from `addr`.

***

### ✏️ Scalar Writes

#### Unsigned Integers

```lua
process:wu8(addr,  value) --> bool
process:wu16(addr, value) --> bool
process:wu32(addr, value) --> bool
process:wu64(addr, value) --> bool
```

Writes an unsigned integer at `addr`.\
Returns `true` on success.

***

#### Signed Integers

```lua
process:w8(addr,  value) --> bool
process:w16(addr, value) --> bool
process:w32(addr, value) --> bool
process:w64(addr, value) --> bool
```

Writes a signed integer at `addr`.

***

#### Floating Point

```lua
process:wf32(addr, value) --> bool
process:wf64(addr, value) --> bool
```

Writes `float` / `double`.

***

### 🔤 Strings

Read and write null-terminated strings from the remote process.

#### Read Strings

```lua
process:rs(addr,  max_chars) --> string    -- ANSI / UTF-8 style
process:rws(addr, max_chars) --> string    -- UTF-16 wide -> Lua string
```

* `rs` – Reads up to `max_chars` characters from `addr`.
* `rws` – Reads a wide string and converts it to a Lua UTF-8 string.
* If nothing valid is read, an empty string is returned.

***

#### Write Strings

```lua
process:ws(addr,  text) --> bool   -- ANSI / UTF-8
process:wws(addr, text) --> bool   -- UTF-16 wide
```

* `ws` – Writes `text` bytes plus a terminating `\0`.
* `wws` – Converts `text` to UTF-16 and writes plus wide `\0`.

Returns `true` on success.

***

### 📦 Raw Memory (byte tables)

Use Lua tables of bytes (`1..N`, values `0–255`) for bulk reads / writes.

```lua
process:rvm(addr, size)          --> { byte1, byte2, ... }
process:wvm(addr, byte_table)    --> bool
```

* `rvm` – Returns a new table of length `size` filled with bytes from `addr`.
* `wvm` – Writes all bytes in `byte_table` to `addr`.\
  Returns `true` if all bytes are written.

***

### 🧮 SIMD Helpers

Convenience helpers for 16/32/64-byte SIMD vectors (raw bytes).

```lua
process:r128(addr)        --> { b1..b16 }
process:r256(addr)        --> { b1..b32 }
process:r512(addr)        --> { b1..b64 }

process:w128(addr, t16)   --> bool  -- t16 length >= 16
process:w256(addr, t32)   --> bool  -- t32 length >= 32
process:w512(addr, t64)   --> bool  -- t64 length >= 64
```

All values are plain bytes (`0–255`).\
`wXXX` returns `false` if the table is too short or the write fails.

***

### 📦 Modules & Pattern Scanning

#### Module Lookup

```lua
local base, size = process:get_module(name)
```

* `name` – Module name, e.g. `"notepad.exe"`, `"client.dll"`.
* Returns `base, size` on success.
* Returns `nil` if the module is not found.

***

#### Code Pattern Scan

```lua
local addr = process:find_code_pattern(search_start, search_size, signature)
```

* `search_start` – Starting address.
* `search_size` – Number of bytes to scan.
* `signature` – Pattern string, e.g. `"48 8B ?? ?? ?? 89"`\
  (same format as your internal pattern scanner).

Returns:

* `addr` – Address of the first match, or `0` if not found.

***

### 🔍 Example: Scanning Notepad (Lua)

```lua
function main()
    log("==== LUA PROC API TEST START ====")

    local proc = ref_process("notepad.exe")
    if not proc then
        log("[-] Failed to ref notepad.exe")
        return
    end

    local pid   = proc:pid()
    local base  = proc:base_address()
    local peb   = proc:peb()

    log(string.format("[+] Referenced Notepad: pid=%d", pid))
    log(string.format("    Base Address = 0x%016X", base))
    log(string.format("    PEB          = 0x%016X", peb))

    -- DOS header
    local b0 = proc:ru8(base)
    local b1 = proc:ru8(base + 1)
    log(string.format("Header bytes: %02X %02X", b0, b1))

    -- First 16 bytes as hex
    local raw = proc:rvm(base, 16)
    local hex = {}
    for i = 1, #raw do
        hex[#hex+1] = string.format("%02X", raw[i])
    end
    log("DOS header (16 bytes): " .. table.concat(hex, " "))

    -- Module + pattern scan
    local mod_base, mod_size = proc:get_module("notepad.exe")
    if mod_base then
        log(string.format("Module Base = 0x%016X", mod_base))
        log(string.format("Module Size = 0x%X",    mod_size))

        local addr = proc:find_code_pattern(mod_base, mod_size, "4D 5A")
        log(string.format("Pattern '4D 5A' found at 0x%016X", addr))
    else
        log("[-] get_module('notepad.exe') failed")
    end

    -- SIMD round-trip (128-bit)
    local v128 = proc:r128(base)
    local ok = proc:w128(base, v128)
    log("w128 ok? " .. tostring(ok))

    deref_process(proc)
    log("==== LUA PROC API TEST END ====")
end
```

***

## `proc:read_struct`

Reads a **single C-style structure** from the target process using a descriptor table.

***

### **Signature**

```lua
table proc:read_struct(uint64 base_address, table descriptor)
```

***

### **Parameters**

#### **`base_address`**

Absolute address of the struct in the remote process.

#### **`descriptor`**

A Lua table describing each struct field:

```lua
field_name = {
    offset = <byte offset>,
    type   = "<field type>"
}
```

***

### **Supported Types**

| Type  | Size | Notes           |
| ----- | ---- | --------------- |
| `u8`  | 1    | unsigned 8-bit  |
| `u16` | 2    | unsigned 16-bit |
| `u32` | 4    | unsigned 32-bit |
| `u64` | 8    | unsigned 64-bit |
| `i8`  | 1    | signed 8-bit    |
| `i16` | 2    | signed 16-bit   |
| `i32` | 4    | signed 32-bit   |
| `i64` | 8    | signed 64-bit   |
| `f32` | 4    | float           |
| `f64` | 8    | double          |

***

### **Returns**

A **Lua table** containing the decoded fields:

```lua
local t = proc:read_struct(addr, DESC)

print(t.health)
print(t.pos_x)
```

***

### **Example – Reading IMAGE\_DOS\_HEADER**

```lua
local DOS_HEADER = {
    e_magic  = { offset = 0x00, type = "u16" },
    e_lfanew = { offset = 0x3C, type = "u32" },
}

local proc = ref_process("notepad.exe")
local base = proc:get_module("notepad.exe")

local dos = proc:read_struct(base, DOS_HEADER)

log_console(string.format("e_magic  = 0x%04X", dos.e_magic))
log_console(string.format("e_lfanew = 0x%08X", dos.e_lfanew))
```

***

## 📘 `proc:read_struct_array`

Reads an **array of structures** from the target process.

***

### **Signature**

```lua
table proc:read_struct_array(
    uint64 base_address,
    integer count,
    integer struct_size,
    table descriptor
)
```

***

### **Parameters**

#### **`base_address`**

Address of the **first** element in the array.

#### **`count`**

Number of array elements to read.

#### **`struct_size`**

Size in bytes of each array element.

#### **`descriptor`**

Same descriptor table used with `read_struct`.

***

### **Returns**

A **1-based Lua array**, where each element is a struct table:

```lua
local arr = proc:read_struct_array(addr, 10, 0x140, DESC)
print(arr[1].health)
```

***

### **Example – Reading a Player Array**

```lua
local PLAYER = {
    health = { offset = 0x10, type = "i32" },
    armor  = { offset = 0x14, type = "i32" },
    pos_x  = { offset = 0x30, type = "f32" },
}

local base = 0x12345678
local size = 0x140
local count = 5

local players = proc:read_struct_array(base, count, size, PLAYER)

for i, p in ipairs(players) do
    log_console(string.format(
        "Player %d: hp=%d armor=%d x=%.1f",
        i, p.health, p.armor, p.pos_x
    ))
end
```

***

### `proc:get_all_tebs()`

Returns a Lua table of **TEB addresses (uint64)** for threads in the target process.

**Syntax**

```lua
local tebs = proc:get_all_tebs()
```

**Returns**

* `{ teb1, teb2, ... }` where each `teb` is a **virtual address** in the remote process
* `{}` if none found / enumeration fails

***

### Virtual Memory Allocation

These functions let you allocate and manage RWX memory inside the target process.\
They are intended for advanced use; you are fully responsible for tracking and freeing any allocations you create.

#### :red\_circle: Important Memory Management Notes (MUST READ!)

These points are critical for using `alloc_vm` safely:

* **Control Flow Guard**                                                                                                                                                          If the target process has Control Flow Guard (CFG) enabled and you intend to execute code from this region, CFG may block all jumps and calls into the allocated memory.\
  To avoid this, CFG must be fully disabled for the target process.\
  Be aware that disabling CFG reduces the security of the device.
* **Allocations are not automatically freed.**\
  Every allocation you create must be manually released using `free_vm()`. If you lose track of an allocation, the memory will remain reserved until the target process exits.
* **Allocations persist for the lifetime of the target process.**\
  Memory created with `alloc_vm` is automatically released only when the **target process** itself closes.
* **Closing the Perception overlay will clear all allocations.**\
  When the overlay is closed, Perception will clean up every RWX allocation for *all* processes currently referenced.\
  If you need an allocation to stay alive, **do not close the overlay** while that memory is being used.
* **Repeated unfreed allocations can exhaust physical memory.**\
  If you repeatedly allocate memory without freeing it, these leaks will accumulate and can eventually **consume all available physical RAM**, potentially degrading system performance or causing instability. If you are writing an injector make sure your inject frees the memory&#x20;
* **If you are writing an injector, you must free allocated memory.**\
  Any injector, loader, or external tool that allocates memory through `alloc_vm` is responsible for freeing it once the memory is no longer needed.\
  Failing to do so will leave permanent physical memory leaks until the target process exits.

***

### Functions

```lua
uint64 proc:alloc_vm(uint size)
bool   proc:free_vm(uint64 address)
```

### `uint64 proc:alloc_vm(size)`

Allocates a block of **read–write–execute (RWX)** memory inside the target process and returns its base address.

#### Parameters

* **size** — Size of the allocation in bytes.

#### Returns

* Base address of the allocation on success.
* `0` on failure.

#### Notes

* Allocated memory is **not tied to any module** and is **not discoverable** through helpers like module queries or pattern scans.\
  You must store and manage the returned address yourself.
* The memory is RWX.\
  If the target process uses **Control Flow Guard (CFG)** and you intend to execute code from this region, CFG may block jumps/calls unless the target allows it.

***

### `bool proc:free_vm(address)`

Frees a region previously allocated with `proc:alloc_vm()`.

#### Parameters

* **address** — The exact base address returned by `alloc_vm`.

#### Returns

* `true` if the region was successfully freed.
* `false` if the address is invalid or the free fails.

***

#### 🔗 Export Lookup – `process:get_proc_address`

```lua
addr = process:get_proc_address(module_base, export_name)
```

Resolves the address of an **exported function or symbol** inside a module in the target process.

* `module_base`\
  Base address of the module **inside the target process**.\
  Typically obtained from:
  * `process:base_address()`, or
  * `local base, size = process:get_module("module_name.dll")`.
* `export_name`\
  Name of the exported function/symbol, e.g. `"Sleep"`, `"CreateFileW"`, `"DllMain"`.

**Returns**

* Absolute **virtual address** of the exported symbol in the target process (as a Lua integer).
* `0` if the export is not found or the arguments are invalid.

**Notes**

* This walks the module’s **export table only** – it does *not* look at imports or IAT.
* The returned address is suitable for:
  * Remote call stubs / shellcode.
  * Manual thunks that jump directly to an API inside the target module.

**Example**

```lua
local proc = ref_process("notepad.exe")
if not proc then return end

local kbase, ksize = proc:get_module("KERNEL32.DLL")
if kbase then
    local addr_sleep = proc:get_proc_address(kbase, "Sleep")
    log(string.format("Sleep @ 0x%016X", addr_sleep))
end

deref_process(proc)
```

***

#### 🧷 Import Table (IAT) Slot Lookup – `process:get_import_rdata_address`

```lua
slot_addr = process:get_import_rdata_address(module_base, import_name)
```

Resolves the **address of the import table entry** (IAT slot) for a given imported function inside a module.

This does **not** return the function’s address itself – it returns the address of the **pointer stored in `.rdata` / IAT**. You can then read or patch that pointer for IAT hooks.

* `module_base`\
  Base address of the module whose imports you want to inspect/patch\
  (usually the main EXE or a specific DLL), e.g. from `process:get_module(...)`.
* `import_name`\
  Name of the imported function (as it appears in the import table), e.g. `"Sleep"`, `"MessageBoxW"`.

**Returns**

* Address of the **IAT entry** (pointer-sized slot) as a Lua integer.
* `0` if the import cannot be found or arguments are invalid.

**Typical usage**

* Read the current imported function pointer:

  ```lua
  local slot = proc:get_import_rdata_address(mod_base, "Sleep")
  if slot ~= 0 then
      local current = proc:ru64(slot)   -- current function pointer
      log(string.format("IAT[Sleep] = 0x%016X", current))
  end
  ```
* Install a simple IAT hook (patch the slot to point to your stub):

  ```lua
  local slot = proc:get_import_rdata_address(mod_base, "Sleep")
  if slot ~= 0 then
      -- 'stub_addr' is an RWX address you allocated with proc:alloc_vm(...)
      local ok = proc:wu64(slot, stub_addr)
      log("IAT hook applied? " .. tostring(ok))
  end
  ```

**Notes**

* Only sees functions present in the module’s **static import table**.
* Manually resolved APIs (e.g. `GetProcAddress` into some custom region) will **not** show up here.
* Designed for **IAT hooks** and for shellcode that wants to call through the same import slot as the module.

***

### Virtual Memory Analysis

#### `proc:virtual_query(address) -> (start:uint64, size:uint64, protection:int, heap_likely:bool)|nil`

Queries the virtual memory region containing the given `address`.

**Parameters:**

* `address` — a `uint64` virtual address.

**Returns:**

* `start` — region base address (`uint64`)
* `size` — region size in bytes (`uint64`)
* `protection` — region protection flags (`int`)
* `heap_likely` — `true` if the region is heuristically likely to be heap/alloc-like (`bool`)
* `nil` if the address is not mapped or cannot be queried.

***

#### `proc:get_vad_snapshot(heap_likely_only:bool) -> table`

Builds a snapshot of virtual memory regions.

**Parameters:**

* `heap_likely_only` — when `true`, only heap-like regions are returned; when `false`, all regions are returned.

**Returns:**

A 1-based Lua array of region tables:

```lua
{
   { start=<uint64>, size=<uint64>, ["end"]=<uint64>, protection=<int>, heap_likely=<bool> },
   ...
}
```

Each region table contains:

* `start` (`uint64`)
* `size` (`uint64`)
* `end` (`uint64`)
* `protection` (`int`)
* `heap_likely` (`bool`)

***

#### **Memory Scanning Helpers**

These helpers scan the target process memory by iterating over the snapshot of virtual memory regions. All scanning functions return a **1-based Lua table** of matching virtual addresses:

```lua
{ addr1, addr2, ... }
```

***

#### `proc:scan_string(text:string, heap_only:bool|nil) -> table`

Scan for occurrences of an ASCII/multibyte constant string in memory.

* `text` — the pattern to search for.
* `heap_only` — optional `bool` filter restricting scan to heap-like regions (`false` if nil).

***

#### `proc:scan_wstring(text:string, heap_only:bool|nil) -> table`

Scan for occurrences of a UTF-16 (wide) string.

* `text` — the wide string to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_pointer(target:uint64, heap_only:bool|nil) -> table`

Find all references to a pointer value.

* `target` — the pointer value to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_u64(value:uint64, heap_only:bool|nil) -> table`

Scan for a 64-bit unsigned integer value in memory.

* `value` — the uint64 value to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_u32(value:int, heap_only:bool|nil) -> table`

Scan for a 32-bit unsigned integer value in memory.

* `value` — the uint32 value to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_float(value:float, heap_only:bool|nil) -> table`

Scan for a 32-bit float value in memory.

* `value` — float pattern to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_double(value:float, heap_only:bool|nil) -> table`

Scan for a 64-bit double value in memory.

* `value` — double pattern to search for.
* `heap_only` — optional `bool` filter.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/proc-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
