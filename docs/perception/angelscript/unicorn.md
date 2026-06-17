> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/unicorn.md).

# Unicorn

The Unicorn API exposes a lightweight CPU + memory emulation layer to AngelScript.\
It supports two modes:

* **Local emulation** (`uc_create`) — fully sandboxed memory you map/write yourself.
* **Process-backed emulation** (`uc_create_process`) — unmapped reads/fetches can be paged-in from a `proc_t` target, enabling “emulate code that reads target memory”.

***

#### Notes (Important)

* **Always** call `uc_close(handle)` when done.
* You should use **`uc_setup_stack`** for setting up stack.
* If you modify code bytes at the same address and re-run, call **`uc_flush_code(handle)`** (TB cache flush) or run the updated code at a different address.
* **Null pointer access, invalid instructions, and interrupts** are caught automatically — emulation stops and sets exception state. Check with `uc_get_last_exception(handle)` after `uc_start` returns.
* Memory addresses are Unicorn virtual addresses:
  * Low “sandbox” memory (e.g. `0x1000` / `0x2000`) is local/emulator-owned.
  * Real target VAs (user-mode addresses) are process-backed when running in process mode.

***

#### Constants

**Memory Protection Flags**

Copy

```cpp
const uint32 UC_PROT_READ
const uint32 UC_PROT_WRITE
const uint32 UC_PROT_EXEC
const uint32 UC_PROT_ALL
```

Use these with `uc_mem_map`.

***

**Register IDs (x86\_64)**

Register IDs are exposed as global `const int` values, for example:

Copy

```cpp
// General purpose registers
const int UC_X86_REG_RAX;
const int UC_X86_REG_RBX;
const int UC_X86_REG_RCX;
const int UC_X86_REG_RDX;
const int UC_X86_REG_RSI;
const int UC_X86_REG_RDI;
const int UC_X86_REG_RBP;
const int UC_X86_REG_RSP;

const int UC_X86_REG_R8;
const int UC_X86_REG_R9;
const int UC_X86_REG_R10;
const int UC_X86_REG_R11;
const int UC_X86_REG_R12;
const int UC_X86_REG_R13;
const int UC_X86_REG_R14;
const int UC_X86_REG_R15;

// Instruction pointer & flags
const int UC_X86_REG_RIP;
const int UC_X86_REG_EFLAGS;

// Segment registers
const int UC_X86_REG_CS;
const int UC_X86_REG_DS;
const int UC_X86_REG_ES;
const int UC_X86_REG_FS;
const int UC_X86_REG_GS;
const int UC_X86_REG_SS;

// Segment bases
const int UC_X86_REG_FS_BASE;
const int UC_X86_REG_GS_BASE;

// SIMD control
const int UC_X86_REG_MXCSR;

// XMM registers
const int UC_X86_REG_XMM0;
const int UC_X86_REG_XMM1;
const int UC_X86_REG_XMM2;
const int UC_X86_REG_XMM3;
const int UC_X86_REG_XMM4;
const int UC_X86_REG_XMM5;
const int UC_X86_REG_XMM6;
const int UC_X86_REG_XMM7;
const int UC_X86_REG_XMM8;
const int UC_X86_REG_XMM9;
const int UC_X86_REG_XMM10;
const int UC_X86_REG_XMM11;
const int UC_X86_REG_XMM12;
const int UC_X86_REG_XMM13;
const int UC_X86_REG_XMM14;
const int UC_X86_REG_XMM15;

// YMM registers
const int UC_X86_REG_YMM0;
const int UC_X86_REG_YMM1;
const int UC_X86_REG_YMM2;
const int UC_X86_REG_YMM3;
const int UC_X86_REG_YMM4;
const int UC_X86_REG_YMM5;
const int UC_X86_REG_YMM6;
const int UC_X86_REG_YMM7;
const int UC_X86_REG_YMM8;
const int UC_X86_REG_YMM9;
const int UC_X86_REG_YMM10;
const int UC_X86_REG_YMM11;
const int UC_X86_REG_YMM12;
const int UC_X86_REG_YMM13;
const int UC_X86_REG_YMM14;
const int UC_X86_REG_YMM15;

```

***

**Hook Types**

```cpp
const int UC_HOOK_CODE
const int UC_HOOK_MEM_UNMAPPED
```

* `UC_HOOK_CODE` — Hook every instruction executed.
* `UC_HOOK_MEM_UNMAPPED` — Hook unmapped memory access (read/write/fetch).

***

#### Engine Handles

**Create (Local)**

Copy

```cpp
uint64 uc_create()
```

Creates a new Unicorn context (local emulation). Returns a handle, or `0` on failure.

***

**Create (Process-backed)**

Copy

```cpp
uint64 uc_create_process(proc_t proc, bool allow_writes = true)
```

Creates a Unicorn context that can page-in unmapped reads/fetches from `proc`.\
Use `allow_writes=false` for safe read-only emulation.

A synthetic `TEB` is created with the real `PEB` address written at offset **0x60**. For correct and stable emulation, you should override the **FS** and **GS** base registers to point to a real TEB instance.

Returns a handle, or `0` on failure.

***

**Close**

Copy

```cpp
void uc_close(uint64 handle)
```

Destroys the Unicorn context and releases all internal resources.

***

#### Memory

**Map Memory**

Copy

```cpp
bool uc_mem_map(uint64 handle, uint64 addr, uint64 size, uint32 perms)
```

Maps a memory region in the emulator.

* `addr` must be page-aligned.
* `size` must be page-aligned (or a multiple of page size).

Returns `true` on success.

***

**Write Memory**

Copy

```cpp
bool uc_mem_write(uint64 handle, uint64 addr, const array<uint8> &in data)
```

Writes bytes into emulator memory at `addr`.

***

**Read Memory**

Copy

```cpp
bool uc_mem_read(uint64 handle, uint64 addr, uint32 size, array<uint8> &out data)
```

Reads bytes from emulator memory at `addr` into `data`.

In process-backed mode, this may succeed if the page was already paged-in (or if your integration supports paging-in for external reads).

***

#### Registers

**Write 64-bit Register**

Copy

```cpp
bool uc_reg_write64(uint64 handle, int reg, uint64 value)
```

***

**Read 64-bit Register**

Copy

```cpp
uint64 uc_reg_read64(uint64 handle, int reg)
```

***

**Write 128-bit Register (XMM)**

Copy

```cpp
bool uc_reg_write128(uint64 handle, int reg, const array<uint8> &in data)
```

`data` must be exactly 16 bytes.

***

**Read 128-bit Register (XMM)**

Copy

```cpp
bool uc_reg_read128(uint64 handle, int reg, array<uint8> &out data)
```

Returns exactly 16 bytes in `data`.

***

**Write 256-bit Register (YMM)**

Copy

```cpp
bool uc_reg_write256(uint64 handle, int reg, const array<uint8> &in data)
```

`data` must be exactly 32 bytes.

***

**Read 256-bit Register (YMM)**

Copy

```cpp
bool uc_reg_read256(uint64 handle, int reg, array<uint8> &out data)
```

Returns exactly 32 bytes in `data`.

***

#### Execution

**Setup Stack (Recommended)**

Copy

```cpp
bool uc_setup_stack(uint64 handle, uint64 stack_base, uint64 stack_size, uint64 stop_addr)
```

Maps a stack region, sets `RSP`, pushes a return address, and maps a STOP page.

Use this before running any code that can execute `ret`.

Returns `true` on success.

If `uc_setup_stack` is not used in process mode, the emulator may attempt to read stack memory from the remote process instead of the emulated address space.

***

**Start Emulation**

Copy

```cpp
int uc_start(uint64 handle, uint64 begin, uint64 end, uint64 timeout = 0, uint64 count = 0)
```

Starts emulation at `begin`.

* `end` — stop address (use a STOP page if your code returns)
* `timeout` — microseconds (0 = unlimited)
* `count` — instruction limit (0 = unlimited)

Returns `UC_ERR_OK` on success. [Error Codes](https://github.com/unicorn-engine/unicorn/blob/c24c9ebe773ce6fbecb0e39f68ffb23b7326b17f/include/unicorn/unicorn.h#L164)

***

**Flush Translated Code Cache**

Copy

```cpp
bool uc_flush_code(uint64 handle)
```

Flushes Unicorn’s internal translation cache (TB cache).\
Call this after modifying code bytes at an address you will execute again.

Returns `true` on success.

***

**Callback Signature**

```cpp
funcdef bool UcHookFn(uint64 uc, uint64 addr)
```

Hook callbacks receive:

* `uc` — Unicorn handle (same value as the `handle` you created)
* `addr` — address of the instruction or faulting memory access

Return value:

* `true` — continue emulation
* `false` — stop emulation (recommended to also call `uc_emu_stop`)

**Add Hook**

```cpp
bool uc_hook_add(uint64 handle, int type, UcHookFn@ cb)
```

Registers a hook callback on the Unicorn context.

* `handle` — Unicorn context handle
* `type` — hook type constant (`UC_HOOK_CODE`, `UC_HOOK_MEM_UNMAPPED`)
* `cb` — callback function handle

Returns `true` on success, `false` on failure.

**Stop Emulation (from hook)**

```cpp
void uc_emu_stop(uint64 handle)
```

Stops emulation immediately. Intended for use **inside hook callbacks** to halt execution cleanly.

***

#### Exception Handling

In process-backed mode, emulated code may branch to null pointers, execute invalid instructions, or trigger software interrupts. These are caught automatically and stop emulation cleanly instead of crashing or returning a cryptic error.

**What gets caught:**

* **Null pointer access** — any read, write, or fetch to an address below `0x10000` (the null page). Common when emulated code follows a branch like `if (!ptr) return;` but the pointer is actually null in the target process.
* **Invalid instructions** — bad opcodes that the CPU can't decode.
* **Software interrupts** — `INT3` breakpoints, `INT 0x2E` syscalls, and other INT instructions.

All three set the exception state and stop emulation. Your script can then check what happened.

**Get Last Exception Code**

```cpp
int uc_get_last_exception(uint64 handle)
```

Returns the NTSTATUS-style exception code from the last `uc_start` run:

| Code           | Meaning                                                  |
| -------------- | -------------------------------------------------------- |
| `0`            | Clean exit (no exception)                                |
| `0xC0000005`   | Access violation (null pointer or unmapped non-usermode) |
| `0xC000001D`   | Illegal instruction                                      |
| `0xC0000005+N` | Software interrupt N                                     |

The exception state is cleared at the start of each `uc_start` call.

**Get Exception Address**

```cpp
uint64 uc_get_exception_address(uint64 handle)
```

Returns the `RIP` (instruction pointer) where the exception occurred. Returns `0` if the last run completed cleanly.

***

**Notes (Hooks)**

* Hooks run during `uc_start(...)` execution.
* Keep hook callbacks lightweight (they can fire very frequently, especially `UC_HOOK_CODE`).
* If you stop execution from a hook, prefer:
  * `uc_emu_stop(handle)` and return `false` from the hook.

***

#### Examples

**Example 1 — Read Notepad ImageBaseAddress via PEB (GS:\[0x60])**

This example:

* References `notepad.exe`
* Creates a process-backed Unicorn context
* Reads `PEB->ImageBaseAddress` via:
  * `mov rax, gs:[0x60]` (PEB)
  * `mov rax, [rax+0x10]` (ImageBaseAddress)
  * `ret` (lands on STOP)

Copy

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (!p.alive()) { log_error("notepad not found"); return -1; }

    uint64 uc = uc_create_process(p, false);
    if (uc == 0) { log_error("uc_create_process failed"); p.deref(); return -1; }

    array<uint8> code = {
        0x65,0x48,0x8B,0x04,0x25,0x60,0x00,0x00,0x00, // mov rax, gs:[0x60]
        0x48,0x8B,0x40,0x10,                         // mov rax, [rax+0x10]
        0xC3                                          // ret
    };

    uint64 CODE  = 0x1000;
    uint64 STACK = 0x2000;
    uint64 STOP  = 0x4000;

    uc_mem_map(uc, CODE, 0x1000, UC_PROT_ALL);
    uc_mem_write(uc, CODE, code);

    uc_reg_write64(uc, UC_X86_REG_RIP, CODE);

    if (!uc_setup_stack(uc, STACK, 0x2000, STOP)) {
        log_error("uc_setup_stack failed");
        uc_close(uc); p.deref();
        return -1;
    }

    if (!uc_start(uc, CODE, STOP, 0, 0)) {
        log_error("uc_start failed");
        uc_close(uc); p.deref();
        return -1;
    }

    uint64 imageBase = uc_reg_read64(uc, UC_X86_REG_RAX);
    log("PEB->ImageBaseAddress: 0x" + formatInt(imageBase, "h"));

    uc_close(uc);
    p.deref();
    return 1;
}
```

***

**Example 2 — Patch Code In-Place + Flush Cache**

This example shows why `uc_flush_code` exists.\
We run two different code blobs at the same address:

* Run 1: `mov rax, gs:[0x60]; ret` (returns PEB)
* Patch code in place
* Flush translation cache
* Run 2: `mov rax, [abs64]; ret` (returns ImageBase)

Copy

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (!p.alive()) { log_error("notepad not found"); return -1; }

    uint64 uc = uc_create_process(p, false);
    if (uc == 0) { log_error("uc_create_process failed"); p.deref(); return -1; }

    uint64 CODE  = 0x1000;
    uint64 STACK = 0x2000;
    uint64 STOP  = 0x4000;

    uc_mem_map(uc, CODE, 0x1000, UC_PROT_ALL);

    // Run 1: get PEB in RAX
    array<uint8> get_peb = {
        0x65,0x48,0x8B,0x04,0x25,0x60,0x00,0x00,0x00, // mov rax, gs:[0x60]
        0xC3
    };

    uc_mem_write(uc, CODE, get_peb);
    uc_flush_code(uc);

    uc_reg_write64(uc, UC_X86_REG_RIP, CODE);
    uc_setup_stack(uc, STACK, 0x2000, STOP);

    if (!uc_start(uc, CODE, STOP, 0, 0)) {
        log_error("uc_start(get_peb) failed");
        uc_close(uc); p.deref();
        return -1;
    }

    uint64 peb = uc_reg_read64(uc, UC_X86_REG_RAX);
    log("PEB ptr = 0x" + formatInt(peb, "h"));

    // Read expected ImageBase from process-backed memory (optional)
    array<uint8> q;
    uc_mem_read(uc, peb + 0x10, 8, q);

    uint64 expected = 0;
    for (int i = 0; i < 8; i++)
        expected |= (uint64(q[i]) << (i * 8));

    // Run 2: mov rax, [abs (peb+0x10)]
    array<uint8> read_abs = {
        0x48,0xA1,
        0,0,0,0,0,0,0,0,
        0xC3
    };

    uint64 addr = peb + 0x10;
    for (int i = 0; i < 8; i++)
        read_abs[2 + i] = uint8((addr >> (i * 8)) & 0xFF);

    uc_mem_write(uc, CODE, read_abs);
    uc_flush_code(uc);

    uc_reg_write64(uc, UC_X86_REG_RIP, CODE);
    uc_setup_stack(uc, STACK, 0x2000, STOP);

    if (!uc_start(uc, CODE, STOP, 0, 0)) {
        log_error("uc_start(read_abs) failed");
        uc_close(uc); p.deref();
        return -1;
    }

    uint64 imageBase = uc_reg_read64(uc, UC_X86_REG_RAX);
    log("ImageBase = 0x" + formatInt(imageBase, "h"));
    log("Expected  = 0x" + formatInt(expected, "h"));

    uc_close(uc);
    p.deref();
    return 1;
}
```

***

**Example 3 — Local Sandbox Emulation (No Process)**

This runs a tiny code snippet in a fully local emulator memory map.

Copy

```cpp
int main()
{
    uint64 uc = uc_create();
    if (uc == 0) { log_error("uc_create failed"); return -1; }

    uint64 CODE  = 0x1000;
    uint64 STACK = 0x2000;
    uint64 STOP  = 0x4000;

    // mov rax, 0x12345678; ret
    array<uint8> code = {
        0x48,0xC7,0xC0,0x78,0x56,0x34,0x12,
        0xC3
    };

    uc_mem_map(uc, CODE, 0x1000, UC_PROT_ALL);
    uc_mem_write(uc, CODE, code);
    uc_reg_write64(uc, UC_X86_REG_RIP, CODE);

    if (!uc_setup_stack(uc, STACK, 0x2000, STOP)) {
        log_error("uc_setup_stack failed");
        uc_close(uc);
        return -1;
    }

    if (!uc_start(uc, CODE, STOP, 0, 0)) {
        log_error("uc_start failed");
        uc_close(uc);
        return -1;
    }

    uint64 rax = uc_reg_read64(uc, UC_X86_REG_RAX);
    log("RAX = 0x" + formatInt(rax, "h"));

    uc_close(uc);
    return 1;
}
```

***

**Example 4 — Handling Null Pointer Exceptions**

This example emulates a function that dereferences a null pointer. Instead of crashing, the emulator catches it and your script can handle it gracefully.

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (!p.alive()) { log_error("notepad not found"); return -1; }

    uint64 uc = uc_create_process(p, false);
    if (uc == 0) { log_error("uc_create_process failed"); p.deref(); return -1; }

    // mov rax, 0; mov rbx, [rax] — null pointer dereference
    array<uint8> code = {
        0x48,0x31,0xC0,             // xor rax, rax
        0x48,0x8B,0x18,             // mov rbx, [rax]  <-- null deref
        0xC3                        // ret (never reached)
    };

    uint64 CODE  = 0x1000;
    uint64 STACK = 0x2000;
    uint64 STOP  = 0x4000;

    uc_mem_map(uc, CODE, 0x1000, UC_PROT_ALL);
    uc_mem_write(uc, CODE, code);
    uc_setup_stack(uc, STACK, 0x2000, STOP);

    uc_start(uc, CODE, STOP, 0, 0);

    int exc = uc_get_last_exception(uc);
    if (exc != 0) {
        uint64 addr = uc_get_exception_address(uc);
        log_error("Exception 0x" + formatInt(exc, "h") + " at RIP 0x" + formatInt(addr, "h"));
    } else {
        uint64 rbx = uc_reg_read64(uc, UC_X86_REG_RBX);
        log("RBX = 0x" + formatInt(rbx, "h"));
    }

    uc_close(uc);
    p.deref();
    return 1;
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/unicorn.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
