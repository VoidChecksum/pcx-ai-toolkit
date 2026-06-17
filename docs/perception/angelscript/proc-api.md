> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/proc-api.md).

# Proc API

The Proc API lets AngelScript access and edit memory of external processes using a lightweight handle type `proc_t`.

***

#### 🔑 Process Handles

***

**Referencing Processes**

```cpp
proc_t ref_process(uint pid)
proc_t ref_process(const string &in name)
```

* `pid` – Windows process ID.
* `name` – Executable name (`"notepad.exe"`, `"cs2.exe"`, etc).

Returns a `proc_t` handle, or `0` if the process could not be opened.

***

**Releasing Handles**

```cpp
void proc_t::deref()
```

Decrements the internal reference and clears the handle.\
After calling `deref()`, the handle becomes invalid (further calls are no-ops).

You must also call `deref()` if `proc_t::alive()` returns `false`.

***

#### 🧬 Process Info

```cpp
uint64 proc_t::base_address() const
uint64 proc_t::peb()          const
uint   proc_t::pid()          const
bool   proc_t::alive()        const
```

* `base_address()` – Image base (module base) of the process.
* `peb()` – Address of the process' PEB.
* `pid()` – Process ID.
* `alive()` – Determines whether the process is currently alive and running.

***

#### Address Validity

```cpp
bool   proc_t::is_valid_address(uint64 address)     const
```

Check if an address is mapped inside target process.

***

#### 📖 Scalar Reads

All addresses are **virtual addresses** in the target process.

**Unsigned Integers**

```cpp
uint8  proc_t::ru8 (uint64 addr) const
uint16 proc_t::ru16(uint64 addr) const
uint32 proc_t::ru32(uint64 addr) const
uint64 proc_t::ru64(uint64 addr) const
```

Reads unsigned integer values at `addr`.

***

**Signed Integers**

```cpp
int8  proc_t::r8 (uint64 addr) const
int16 proc_t::r16(uint64 addr) const
int32 proc_t::r32(uint64 addr) const
int64 proc_t::r64(uint64 addr) const
```

Reads signed integer values at `addr`.

***

**Floating-Point**

```cpp
float  proc_t::rf32(uint64 addr) const
double proc_t::rf64(uint64 addr) const
```

Reads `float` / `double` from `addr`.

***

#### ✏️ Scalar Writes

**Unsigned Integers**

```cpp
bool proc_t::wu8 (uint64 addr, uint8  v)
bool proc_t::wu16(uint64 addr, uint16 v)
bool proc_t::wu32(uint64 addr, uint32 v)
bool proc_t::wu64(uint64 addr, uint64 v)
```

Writes unsigned integer values.\
Returns `true` on success.

***

**Signed Integers**

```cpp
bool proc_t::w8 (uint64 addr, int8  v)
bool proc_t::w16(uint64 addr, int16 v)
bool proc_t::w32(uint64 addr, int32 v)
bool proc_t::w64(uint64 addr, int64 v)
```

Writes signed integer values.

***

**Floating-Point**

```cpp
bool proc_t::wf32(uint64 addr, float  v)
bool proc_t::wf64(uint64 addr, double v)
```

Writes `float` / `double`.

***

#### 🔤 Strings

All string helpers assume **null-terminated** memory on the remote side (for reads) and write a terminating null when writing.

**Reading Strings**

```cpp
string proc_t::rs (uint64 addr, int max_chars) const
string proc_t::rws(uint64 addr, int max_chars) const
```

* `rs` – Reads an ANSI/UTF-8 style string from `addr`.
* `rws` – Reads a UTF-16 wide string, converts to UTF-8 `string`.

`max_chars` is a hard cap to avoid walking off invalid memory.

***

**Writing Strings**

```cpp
bool proc_t::ws (uint64 addr, const string &in text)
bool proc_t::wws(uint64 addr, const string &in text)
```

* `ws` – Writes `text` as ANSI/UTF-8 bytes plus trailing `\0`.
* `wws` – Converts `text` to UTF-16 and writes wide string plus trailing `L'\0'`.

Returns `true` on success.

***

#### 📦 Raw Memory (byte arrays)

Uses `array<uint8>` for bulk reads/writes.

```cpp
void proc_t::rvm(uint64 addr, uint size, array<uint8> &out out_buf)
bool proc_t::wvm(uint64 addr, const array<uint8> &in in_buf)
```

* `rvm` – Reads `size` bytes starting at `addr` into `out_buf`.\
  `out_buf` is resized to `size`.
* `wvm` – Writes bytes from `in_buf` to `addr`.\
  Returns `true` if all bytes were written.

***

#### 🧮 SIMD Helpers

Convenience wrappers around 16/32/64-byte vectors (`__m128/__m256/__m512`).\
All data is exposed as raw bytes.

```cpp
void proc_t::r128(uint64 addr, array<uint8> &out out16) const
void proc_t::r256(uint64 addr, array<uint8> &out out32) const
void proc_t::r512(uint64 addr, array<uint8> &out out64) const

bool proc_t::w128(uint64 addr, const array<uint8> &in in16)
bool proc_t::w256(uint64 addr, const array<uint8> &in in32)
bool proc_t::w512(uint64 addr, const array<uint8> &in in64)
```

* `r128`/`r256`/`r512` – Read 16/32/64 bytes into the output array (array is resized).
* `w128`/`w256`/`w512` – Write 16/32/64 bytes from the input array.\
  Returns `false` if the array is too small or the write fails.

***

#### Thread Environment Blocks (TEB)

**`array<uint64>@ proc_t::get_all_tebs() const`**

Returns a list of **TEB (Thread Environment Block) addresses** for all threads currently discovered in the target process.

**Signature**

```
array<uint64>@ proc_t::get_all_tebs() const
```

**Returns**

* `array<uint64>` — `{ teb1, teb2, ... }`
  * Each entry is a **virtual address** of a TEB in the target process.
  * Returns null if no threads are found or enumeration fails.

***

#### 📦 Modules & Pattern Scans

**Module Lookup**

```cpp
bool proc_t::get_module(
    const string &in name,
    uint64 &out module_base,
    uint64 &out module_size
)
```

Looks up a module by name (e.g. `"notepad.exe"`, `"client.dll"`):

* On success:
  * `module_base` – Base address of the module.
  * `module_size` – Size in bytes.
  * Returns `true`.
* Returns `false` if the module is not found.

***

**Code Pattern Search**

```cpp
uint64 proc_t::find_code_pattern(
    uint64 search_start,
    uint64 search_size,
    const string &in signature
)

void proc_t::find_all_code_patterns(
    uint64 search_start,
    uint64 search_size,
    const string &in signature,
    array<uint64> &out result
)
```

Scans `[search_start, search_start + search_size)` for a textual pattern:

* `signature` – Pattern string, e.g. `"48 8B ?? ?? ?? 89"`\
  (exact format is the same as used internally by your pattern scanner).
* `find_code_pattern` returns the **address of the first match**, or `0` if not found.
* `find_all_code_patterns` populates `result` with **all** matching addresses.

***

#### 🔍 Example: Scanning Notepad

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (p.pid() == 0)
    {
        log("Failed to reference notepad.exe");
        return 0;
    }

    uint64 base = p.base_address();
    log("PID  = " + p.pid());
    log("Base = 0x" + formatUInt(base, "0H", 16));

    // Read the first two bytes ("MZ")
    uint8 b0 = p.ru8(base);
    uint8 b1 = p.ru8(base + 1);
    log("Header Bytes: "
        + formatUInt(b0, "0H", 2) + " "
        + formatUInt(b1, "0H", 2));

    // Dump first 16 bytes
    array<uint8> bytes;
    p.rvm(base, 16, bytes);

    string dump;
    for (uint i = 0; i < bytes.length(); i++)
    {
        if (i > 0) dump += " ";
        dump += formatUInt(bytes[i], "0H", 2);
    }
    log("DOS Header (16 bytes): " + dump);

    // Find module + pattern "4D 5A" (MZ signature)
    uint64 modBase, modSize;
    if (p.get_module("notepad.exe", modBase, modSize))
    {
        log("Module Base = 0x" + formatUInt(modBase, "0H", 16));
        log("Module Size = 0x" + formatUInt(modSize, "0H", 16));

        uint64 addr = p.find_code_pattern(modBase, modSize, "4D 5A");
        log("Pattern '4D 5A' found at 0x" + formatUInt(addr, "0H", 16));
    }
    else
    {
        log("Module not found");
    }

    p.deref();
    return 0;
}
```

***

### Process Struct Helpers

These helpers let you describe a C-style structure in a `dictionary` and read it.

***

#### 📦 Struct Descriptor (common concept)

A **struct descriptor** is a `dictionary` where each entry:

* Key = field name (string)
* Value = another `dictionary` with:
  * `"offset"` – byte offset from struct base (int64)
  * `"type"` – field type string (`"u16"`, `"i32"`, `"f32"`, etc.)
  * *(optional)* `"max_chars"` for string fields

Example:

```cpp
dictionary PLAYER_DESC;

void init_player_desc()
{
    dictionary@ health = { {"offset", int64(0x10)}, {"type", "i32"} };
    dictionary@ armor  = { {"offset", int64(0x14)}, {"type", "i32"} };
    dictionary@ pos_x  = { {"offset", int64(0x30)}, {"type", "f32"} };
    dictionary@ pos_y  = { {"offset", int64(0x34)}, {"type", "f32"} };
    dictionary@ pos_z  = { {"offset", int64(0x38)}, {"type", "f32"} };

    PLAYER_DESC.set("health", @health);
    PLAYER_DESC.set("armor",  @armor);
    PLAYER_DESC.set("pos_x",  @pos_x);
    PLAYER_DESC.set("pos_y",  @pos_y);
    PLAYER_DESC.set("pos_z",  @pos_z);
}
```

**Supported field types**

| Type        | Size | Meaning                  |
| ----------- | ---- | ------------------------ |
| `"u8"`      | 1    | unsigned 8-bit           |
| `"u16"`     | 2    | unsigned 16-bit          |
| `"u32"`     | 4    | unsigned 32-bit          |
| `"u64"`     | 8    | unsigned 64-bit          |
| `"i8"`      | 1    | signed 8-bit             |
| `"i16"`     | 2    | signed 16-bit            |
| `"i32"`     | 4    | signed 32-bit            |
| `"i64"`     | 8    | signed 64-bit            |
| `"f32"`     | 4    | 32-bit float             |
| `"f64"`     | 8    | 64-bit double            |
| `"string"`  | var  | UTF-8 C-string in target |
| `"wstring"` | var  | UTF-16 string → UTF-8    |

For `"string"` / `"wstring"`, you can add `"max_chars"` to limit how many characters are read (default \~256, clamped to 1..8192).

***

#### 📘 `bool proc_t::read_struct(uint64 addr, dictionary &out result, const dictionary &in desc)`

Reads **one** structure instance from the target process into an existing `dictionary`.

**Signature**

```cpp
bool read_struct(uint64 addr,
                 dictionary &out result,
                 const dictionary &in desc) const
```

**Parameters**

* `addr`\
  Absolute address of the struct in the remote process.
* `result`\
  Dictionary that will be **filled** with the decoded fields.\
  (Existing contents are cleared before filling.)
* `desc`\
  Struct descriptor `dictionary` described above.

**Return**

* `true` on success
* `false` on failure (invalid process handle, invalid descriptor, etc.)

**Stored value types**

To keep things simple (and consistent with your JSON API):

* All integer fields are stored as **`int64`**
* All float fields are stored as **`double`**
* String fields are stored as script **`string`**

So you can safely read with:

```cpp
int64  i;   result.get("field", i);
double d;   result.get("field", d);
string s;   result.get("field", s);
```

You can also read into `uint64` etc. – the dictionary will convert as needed.

***

**Example – Read one player struct**

```cpp
void example_read_player()
{
    init_player_desc();

    proc_t p = ref_process("somegame.exe");

    uint64 base, size;
    p.get_module("somegame.exe", base, size);

    dictionary player;
    if (!p.read_struct(base + 0x123456, player, PLAYER_DESC))
    {
        log("read_struct failed");
        return;
    }

    int64 health;
    player.get("health", health);

    log("Health = " + health);
}
```

***

#### 📘 `bool proc_t::read_struct_array(uint64 base, uint count, uint size, array<dictionary>@ &out result, const dictionary &in desc)`

Reads an **array** of structures into an `array<dictionary>`.

**Signature**

```cpp
bool read_struct_array(uint64 base,
                       uint count,
                       uint size,
                       array<dictionary>@ &out result,
                       const dictionary &in desc) const
```

**Parameters**

* `base`\
  Address of the **first** element.
* `count`\
  Number of elements to read.
* `size`\
  Size in bytes of each element in the array (`sizeof(struct)`).
* `result`\
  `array<dictionary>` that will be resized to `count`.\
  Each element will be filled with that struct's data. If an element is `null` internally, it is created.
* `desc`\
  Same struct descriptor as for `read_struct`.

**Return**

* `true` on success
* `false` if the process is invalid, `count`/`size` is 0, etc.

**Example – Player list**

```cpp
void example_read_players()
{
    init_player_desc();

    proc_t p = ref_process("somegame.exe");

    uint64 base = 0x20000000;
    uint   count = 32;
    uint   structSize = 0x140;

    array<dictionary> players;
    if (!p.read_struct_array(base, count, structSize, players, PLAYER_DESC))
    {
        log("read_struct_array failed");
        return;
    }

    for (uint i = 0; i < players.length(); i++)
    {
        dictionary@ pl = players[i];

        int64  hp   = 0;
        double px   = 0.0;
        pl.get("health", hp);
        pl.get("pos_x", px);

        log("Player " + i + " hp=" + hp + " pos_x=" + px);
    }
}
```

***

### 🧪 Full Example Script – Read `IMAGE_DOS_HEADER` from notepad.exe

This is a complete AngelScript file you can drop into your environment.\
It:

1. Builds a DOS header descriptor
2. Uses `proc_t.read_struct` to read it from `notepad.exe`
3. Prints all key fields and the computed NT header address

```cpp
dictionary DOS_HEADER;

string to_hex16(uint v)
{
    const string HEX = "0123456789ABCDEF";
    string hex16 = "0000";
    for (int i = 0; i < 4; i++)
    {
        uint nibble = (v >> ((3 - i) * 4)) & 0xF;
        hex16[i] = HEX[nibble];
    }
    return hex16;
}

string to_hex32(uint v)
{
    const string HEX = "0123456789ABCDEF";
    string hex32 = "00000000";
    for (int i = 0; i < 8; i++)
    {
        uint nibble = (v >> ((7 - i) * 4)) & 0xF;
        hex32[i] = HEX[nibble];
    }
    return hex32;
}

void init_dos_descriptor()
{
    dictionary@ e_magic    = { {"offset", int64(0x00)}, {"type", "u16"} };
    dictionary@ e_cblp     = { {"offset", int64(0x02)}, {"type", "u16"} };
    dictionary@ e_cp       = { {"offset", int64(0x04)}, {"type", "u16"} };
    dictionary@ e_crlc     = { {"offset", int64(0x06)}, {"type", "u16"} };
    dictionary@ e_cparhdr  = { {"offset", int64(0x08)}, {"type", "u16"} };
    dictionary@ e_minalloc = { {"offset", int64(0x0A)}, {"type", "u16"} };
    dictionary@ e_maxalloc = { {"offset", int64(0x0C)}, {"type", "u16"} };
    dictionary@ e_ss       = { {"offset", int64(0x0E)}, {"type", "u16"} };
    dictionary@ e_sp       = { {"offset", int64(0x10)}, {"type", "u16"} };
    dictionary@ e_csum     = { {"offset", int64(0x12)}, {"type", "u16"} };
    dictionary@ e_ip       = { {"offset", int64(0x14)}, {"type", "u16"} };
    dictionary@ e_cs       = { {"offset", int64(0x16)}, {"type", "u16"} };
    dictionary@ e_lfarlc   = { {"offset", int64(0x18)}, {"type", "u16"} };
    dictionary@ e_ovno     = { {"offset", int64(0x1A)}, {"type", "u16"} };

    dictionary@ e_lfanew   = { {"offset", int64(0x3C)}, {"type", "u32"} };

    DOS_HEADER.set("e_magic",    @e_magic);
    DOS_HEADER.set("e_cblp",     @e_cblp);
    DOS_HEADER.set("e_cp",       @e_cp);
    DOS_HEADER.set("e_crlc",     @e_crlc);
    DOS_HEADER.set("e_cparhdr",  @e_cparhdr);
    DOS_HEADER.set("e_minalloc", @e_minalloc);
    DOS_HEADER.set("e_maxalloc", @e_maxalloc);
    DOS_HEADER.set("e_ss",       @e_ss);
    DOS_HEADER.set("e_sp",       @e_sp);
    DOS_HEADER.set("e_csum",     @e_csum);
    DOS_HEADER.set("e_ip",       @e_ip);
    DOS_HEADER.set("e_cs",       @e_cs);
    DOS_HEADER.set("e_lfarlc",   @e_lfarlc);
    DOS_HEADER.set("e_ovno",     @e_ovno);
    DOS_HEADER.set("e_lfanew",   @e_lfanew);
}

void dump_dos_header(dictionary@ dos, uint64 base)
{
    uint64 e_magic64    = 0;
    uint64 e_cblp64     = 0;
    uint64 e_cp64       = 0;
    uint64 e_crlc64     = 0;
    uint64 e_cparhdr64  = 0;
    uint64 e_minalloc64 = 0;
    uint64 e_maxalloc64 = 0;
    uint64 e_ss64       = 0;
    uint64 e_sp64       = 0;
    uint64 e_csum64     = 0;
    uint64 e_ip64       = 0;
    uint64 e_cs64       = 0;
    uint64 e_lfarlc64   = 0;
    uint64 e_ovno64     = 0;
    uint64 e_lfanew64   = 0;

    dos.get("e_magic",    e_magic64);
    dos.get("e_cblp",     e_cblp64);
    dos.get("e_cp",       e_cp64);
    dos.get("e_crlc",     e_crlc64);
    dos.get("e_cparhdr",  e_cparhdr64);
    dos.get("e_minalloc", e_minalloc64);
    dos.get("e_maxalloc", e_maxalloc64);
    dos.get("e_ss",       e_ss64);
    dos.get("e_sp",       e_sp64);
    dos.get("e_csum",     e_csum64);
    dos.get("e_ip",       e_ip64);
    dos.get("e_cs",       e_cs64);
    dos.get("e_lfarlc",   e_lfarlc64);
    dos.get("e_ovno",     e_ovno64);
    dos.get("e_lfanew",   e_lfanew64);

    log("[AS] ==== IMAGE_DOS_HEADER dump ====");
    log("[AS] base      = 0x" + to_hex32(uint(base & 0xFFFFFFFF)));
    log("[AS] e_magic   = 0x" + to_hex16(uint(e_magic64   & 0xFFFF)));
    log("[AS] e_cblp    = 0x" + to_hex16(uint(e_cblp64    & 0xFFFF)));
    log("[AS] e_cp      = 0x" + to_hex16(uint(e_cp64      & 0xFFFF)));
    log("[AS] e_crlc    = 0x" + to_hex16(uint(e_crlc64    & 0xFFFF)));
    log("[AS] e_cparhdr = 0x" + to_hex16(uint(e_cparhdr64 & 0xFFFF)));
    log("[AS] e_minalloc= 0x" + to_hex16(uint(e_minalloc64& 0xFFFF)));
    log("[AS] e_maxalloc= 0x" + to_hex16(uint(e_maxalloc64& 0xFFFF)));
    log("[AS] e_ss      = 0x" + to_hex16(uint(e_ss64      & 0xFFFF)));
    log("[AS] e_sp      = 0x" + to_hex16(uint(e_sp64      & 0xFFFF)));
    log("[AS] e_csum    = 0x" + to_hex16(uint(e_csum64    & 0xFFFF)));
    log("[AS] e_ip      = 0x" + to_hex16(uint(e_ip64      & 0xFFFF)));
    log("[AS] e_cs      = 0x" + to_hex16(uint(e_cs64      & 0xFFFF)));
    log("[AS] e_lfarlc  = 0x" + to_hex16(uint(e_lfarlc64  & 0xFFFF)));
    log("[AS] e_ovno    = 0x" + to_hex16(uint(e_ovno64    & 0xFFFF)));
    log("[AS] e_lfanew  = 0x" + to_hex32(uint(e_lfanew64  & 0xFFFFFFFF)));

    if ((e_magic64 & 0xFFFF) == 0x5A4D)
    log("[AS] DOS magic OK ('MZ')");
    else
    log("[AS] DOS magic INVALID (expected 0x5A4D)");

    uint64 nt_addr = base + (e_lfanew64 & 0xFFFFFFFF);
    log("[AS] NT header at: 0x" + to_hex32(uint(nt_addr & 0xFFFFFFFF)));
}

void test_dos_header()
{
    init_dos_descriptor();

    proc_t p = ref_process("notepad.exe");
    if (!p.alive())
    {
        log("[AS] notepad.exe not found");
        return;
    }

    uint64 base = p.base_address();

    dictionary dos;
    if (!p.read_struct(base, dos, DOS_HEADER))
    {
        log("[AS] read_struct failed");
        return;
    }

    dump_dos_header(@dos, base);
}

int main()
{
    test_dos_header();
    return 1;
}
```

***

#### Virtual Memory Allocation

These functions let you allocate and manage RWX memory inside the target process.\
They are intended for advanced use; you are fully responsible for tracking and freeing any allocations you create.

**:red\_circle: Important Memory Management Notes (MUST READ!)**

These points are critical for using `alloc_vm` safely:

* **Control Flow Guard**\
  If the target process has Control Flow Guard (CFG) enabled and you intend to execute code from this region, CFG may block all jumps and calls into the allocated memory.\
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
  If you repeatedly allocate memory without freeing it, these leaks will accumulate and can eventually **consume all available physical RAM**, potentially degrading system performance or causing instability. If you are writing an injector make sure your inject frees the memory.
* **If you are writing an injector, you must free allocated memory.**\
  Any injector, loader, or external tool that allocates memory through `alloc_vm` is responsible for freeing it once the memory is no longer needed.\
  Failing to do so will leave permanent physical memory leaks until the target process exits.

**Functions**

```cpp
uint64 proc_t::alloc_vm(uint size)
bool   proc_t::free_vm(uint64 address)
```

**`uint64 proc_t::alloc_vm(uint size)`**

Allocates a block of **read–write–execute (RWX)** memory in the target process and returns its base address.

* **Parameters**
  * `size` — Size of the allocation in bytes.
* **Returns**
  * Base address of the allocated region on success.
  * `0` on failure.

**Notes**

* The allocated region is **not associated with any module** and is **not discoverable** through higher-level helpers (e.g. module lookup, pattern scan helpers, etc.).\
  You must store and manage the returned address yourself.
* The memory is RWX. If the target process uses **Control Flow Guard (CFG)** and you intend to execute from this region, CFG may block jumps/calls into it unless the target process allows it.

***

**`bool proc_t::free_vm(uint64 address)`**

Frees a region previously allocated with `alloc_vm`.

* **Parameters**
  * `address` — Base address previously returned by `alloc_vm`.
* **Returns**
  * `true` if the region was successfully freed.
  * `false` if the address is invalid or the free fails.

***

**🔗 Export Lookup – `get_proc_address`**

```cpp
uint64 proc_t::get_proc_address(
    uint64        module_base,
    const string &in export_name
)
```

Resolves the address of an **exported symbol** inside a module in the target process.

* `module_base`\
  Base address of the module **inside the target process**.\
  Typically obtained from:
  * `proc_t::base_address()`, or
  * `proc_t::get_module("module_name.dll", base, size)`.
* `export_name`\
  Name of the exported function or symbol, e.g. `"Sleep"`, `"CreateFileW"`.

**Returns**

* Absolute **virtual address** of the exported symbol in the target process.
* `0` if the export is not found or the arguments are invalid.

**Notes**

* This walks the module's **export table** only – it does *not* search imports or runtime-resolved addresses.
* The address is directly usable for:
  * Call stubs / shellcode in the remote process.
  * Manual thunking (e.g. "jmp \[resolved\_addr]" from your injected code).
* You are responsible for ensuring the returned address is valid / executable before calling into it.

**Example**

```cpp
proc_t p = ref_process("notepad.exe");

uint64 kbase, ksize;
if (p.get_module("KERNEL32.DLL", kbase, ksize))
{
    uint64 addrSleep = p.get_proc_address(kbase, "Sleep");
    log("Sleep @ 0x" + formatUInt(addrSleep, "0H", 16));
}
```

***

**🧷 Import Table (IAT) Slot Lookup – `get_import_rdata_address`**

```cpp
uint64 proc_t::get_import_rdata_address(
    uint64        module_base,
    const string &in import_name
)
```

Resolves the **address of the import table entry** (IAT slot) for a given imported function inside a module.

This does **not** return the function's address directly – it returns the address of the **pointer stored in `.rdata` / IAT**. That pointer can then be read or patched (for IAT hooks, trampolines, etc.).

* `module_base`\
  Base address of the module whose **imports you want to inspect/patch** (usually the main EXE or a specific DLL), obtained from `base_address()` or `get_module(...)`.
* `import_name`\
  Name of the imported function as it appears in the import table, e.g. `"Sleep"`, `"MessageBoxW"`.

**Returns**

* Address of the **IAT entry** (pointer-sized slot) for the requested import.
* `0` if the import cannot be found or the arguments are invalid.

**How to use**

* Read current target of the import:

  ```cpp
  uint64 slot_addr = p.get_import_rdata_address(modBase, "Sleep");
  uint64 current_fn = p.ru64(slot_addr); // current function pointer
  ```
* Install a basic IAT hook (patch the pointer):

  ```cpp
  uint64 slot_addr = p.get_import_rdata_address(modBase, "Sleep");
  if (slot_addr != 0)
  {
      // 'stub_remote' is an RWX address you allocated in the target
      p.wu64(slot_addr, stub_remote);
  }
  ```

**Notes**

* This only sees imports that are present in the module's **static import table**.
* Imports resolved manually at runtime (e.g. via `GetProcAddress` into custom memory) will **not** show up here.
* Ideal for:
  * Classic **IAT hooks** (redirecting calls to your own stub).
  * Finding the call site used by a module to invoke a given API, so your shellcode can jump through the same IAT entry.

***

**Pointer Array Helpers**

**`array<uint64>@ proc_t::read_pointer_array(uint64 base, uint count, int offset_delta) const`**

Reads an array of 64-bit pointers from the target process.

This is a convenience helper for common layouts like:

* pointer lists (`T**`, vtable arrays, entity pointer arrays)
* "pointer + fixed offset" patterns

**Parameters**

* `base` — Address of the first pointer (each element is `uint64`, so step = 8 bytes).
* `count` — Number of pointers to read.
* `offset_delta` — Value added to **each** pointer after reading (can be negative).

**Return**

* Returns `array<uint64>@` containing `count` elements.
* Returns `null` if `base` is invalid, `count` is 0, or the process handle is invalid.

**Example**

```cpp
proc_t p = ref_process("cs2.exe");
if (!p.alive())
{
    log_error("process not found");
    return 0;
}

uint64 list_base = 0x12345678; // address of first uint64 pointer
uint count = 64;

// Example: read pointer array and add +0x10 to each pointer
array<uint64>@ ptrs = p.read_pointer_array(list_base, count, 0x10);
if (ptrs is null)
{
    log_error("read_pointer_array failed");
    return 0;
}

for (uint i = 0; i < ptrs.length(); ++i)
{
    uint64 addr = ptrs[i];
    if (addr == 0) continue;

    // ... use addr ...
}
```

***

### Virtual Memory Analysis

These APIs allow querying and iterating virtual memory regions.

***

#### `bool proc_t::virtual_query(uint64 address, uint64 &out region_start, uint64 &out region_size, uint &out protection, bool &out heap_likely) const`

Queries the memory region that contains `address`.

**Parameters**

* `address` — Any virtual address inside the target region.
* `region_start` — Region start address (output).
* `region_size` — Region size in bytes (output).
* `protection` — Region protection flags (output).
* `heap_likely` — True if the region is likely heap/alloc-like (output).

**Returns**

* `true` on success
* `false` if the address is not mapped or cannot be queried

***

#### `array<dictionary@>@ proc_t::get_vad_snapshot(bool heap_likely_only = false) const`

Builds a snapshot of virtual memory regions and **returns** it as an array of dictionary handles.

* When `heap_likely_only == true`, only heap-like regions are returned.
* When `heap_likely_only == false`, all regions are returned.

**Returns**

* `array<dictionary@>@` — array of dictionaries, one per region. Returns `null` on failure.

**Dictionary field types**

Each dictionary entry stores fields as `int64` (matching the same convention as `read_struct`). You must use `int64` in your `.get()` calls:

| Key             | Stored Type | Description                               |
| --------------- | ----------- | ----------------------------------------- |
| `"start"`       | `int64`     | Region start address                      |
| `"size"`        | `int64`     | Region size in bytes                      |
| `"end"`         | `int64`     | Region end address                        |
| `"protection"`  | `int64`     | Protection flags                          |
| `"heap_likely"` | `int64`     | `1` if region is heap-like, `0` otherwise |

**Example**

```cpp
void enumerate_regions(proc_t p, bool heap_only)
{
    array<dictionary@>@ vad = p.get_vad_snapshot(heap_only);
    if (vad is null)
    {
        log("get_vad_snapshot failed");
        return;
    }

    log("Regions: " + vad.length());

    for (uint i = 0; i < vad.length(); i++)
    {
        dictionary@ d = vad[i];

        int64 rStart = 0;
        int64 rSize  = 0;
        int64 rEnd   = 0;
        int64 prot   = 0;
        int64 heap   = 0;

        d.get("start",       rStart);
        d.get("size",        rSize);
        d.get("end",         rEnd);
        d.get("protection",  prot);
        d.get("heap_likely", heap);

        log("Region[" + i + "] start=0x" + formatUInt(uint64(rStart), "0H", 16)
            + " size=0x" + formatUInt(uint64(rSize), "0H", 16)
            + " heap=" + (heap != 0));
    }
}
```

***

### Memory Scan Helpers

All scan functions **return** `array<uint64>@` containing matching addresses. Returns `null` on failure (invalid process handle, etc.).

All scan functions accept a `heap_only` parameter (default `false`). When `true`, only heap-like memory regions are scanned.

***

#### `array<uint64>@ proc_t::scan_u32(uint value, bool heap_only = false) const`

Scans for a 32-bit unsigned value.

```cpp
array<uint64>@ results = p.scan_u32(12345, false);
```

***

#### `array<uint64>@ proc_t::scan_u64(uint64 value, bool heap_only = false) const`

Scans for a 64-bit unsigned value.

```cpp
array<uint64>@ results = p.scan_u64(0xDEADBEEF, false);
```

***

#### `array<uint64>@ proc_t::scan_float(float value, bool heap_only = false) const`

Scans for a 32-bit floating-point value.

```cpp
array<uint64>@ results = p.scan_float(100.0f, true);
```

***

#### `array<uint64>@ proc_t::scan_double(double value, bool heap_only = false) const`

Scans for a 64-bit floating-point value.

```cpp
array<uint64>@ results = p.scan_double(3.14159, false);
```

***

#### `array<uint64>@ proc_t::scan_string(const string &in text, bool heap_only = false) const`

Scans for a UTF-8 / ANSI byte string in memory.

```cpp
array<uint64>@ results = p.scan_string("player_name", true);
```

***

#### `array<uint64>@ proc_t::scan_wstring(const string &in text, bool heap_only = false) const`

Scans for a UTF-16 (wide) string in memory. The input is a regular `string` which is internally converted to UTF-16 before scanning.

```cpp
array<uint64>@ results = p.scan_wstring("Notepad", false);
```

***

#### `array<uint64>@ proc_t::scan_pointer(uint64 target, bool heap_only = false) const`

Scans for all locations in memory that contain a pointer to `target`.

```cpp
uint64 vtable_addr = 0x7FF612340000;
array<uint64>@ refs = p.scan_pointer(vtable_addr, false);
if (refs !is null)
{
    for (uint i = 0; i < refs.length(); i++)
        log("Reference at 0x" + formatUInt(refs[i], "0H", 16));
}
```

***

#### 🔍 Full Scan Example

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (!p.alive())
    {
        log("Process not found");
        return 0;
    }
    
    // Scan for a known health value
    array<uint64>@ hits = p.scan_u32(100, true);
    if (hits is null || hits.length() == 0)
    {
        log("No matches found");
        p.deref();
        return 0;
    }

    log("Found " + hits.length() + " matches for value 100:");
    uint n = hits.length() < 10 ? hits.length() : 10;
    for (uint i = 0; i < n; i++)
    {
        log("  [" + i + "] 0x" + formatUInt(hits[i], "0H", 16));
    }

    // Scan for a float position
    array<uint64>@ float_hits = p.scan_float(128.5f, true);
    if (float_hits !is null)
        log("Float matches: " + float_hits.length());

    // Scan for a string
    array<uint64>@ str_hits = p.scan_string("notepad", false);
    if (str_hits !is null)
        log("String matches: " + str_hits.length());

    p.deref();
    return 0;
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/proc-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
