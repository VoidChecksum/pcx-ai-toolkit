> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/proc-api.md).

# Proc API

All proc natives are auto-registered into every loaded script.

`proc_t` is a value-type handle. Construct it via `ref_process(...)`; the host ref is released automatically when the variable goes out of scope.

Some natives are gated by permission flags toggled host-side. Gated calls log and return 0 / false when blocked. See [Permissions](#permissions).

**Address type:** all addresses are `uint64`. Pick `uint64` for any locals that hold an address — `uint64 base = p.base_address();` — and the rest of the chain stays cast-free. Mixing `int64` addresses requires `cast<uint64>(...)`.

## `proc_t`

```cpp
proc_t ref_process(uint32 pid);
proc_t ref_process(string name);
```

Returns an alive handle on success, a null one on failure. Verify with `.alive()`.

## Identity

```cpp
uint64 proc.base_address();
uint64 proc.peb();
uint32 proc.pid();
bool   proc.alive();
bool   proc.is_valid_address(uint64 addr);
uint64 proc.get_eprocess();   // gated: kernel_rw_access — see below
```

`get_eprocess` returns the target's EPROCESS kernel address. Gated behind the `kernel_rw_access` permission — returns `0` and logs when the script doesn't hold it. Use cases: passing the EPROCESS to a custom kernel routine, walking kernel structures the proc API doesn't already expose, etc.

## Read primitives

```cpp
uint8/16/32/64 proc.ru8/ru16/ru32/ru64(uint64 addr);
int8/16/32/64  proc.r8/r16/r32/r64  (uint64 addr);
float32 proc.rf32(uint64 addr);
float64 proc.rf64(uint64 addr);

string proc.rs (uint64 addr, int32 max_chars);   // null-terminated UTF-8, cap 8192
string proc.rws(uint64 addr, int32 max_chars);   // UTF-16, returns UTF-8, cap 8192
```

All return 0 / empty on failure or out-of-range address. By default, addresses must be usermode. When the script holds `kernel_rw_access`, *safe* kernel addresses are also accepted — see [Permissions](#permissions).

## Write primitives (gated: `write_memory`)

```cpp
bool proc.wu8/wu16/wu32/wu64(uint64 addr, uintN v);
bool proc.w8/w16/w32/w64    (uint64 addr, intN  v);
bool proc.wf32(uint64 addr, float32 v);
bool proc.wf64(uint64 addr, float64 v);
bool proc.ws (uint64 addr, string text);    // UTF-8 bytes
bool proc.wws(uint64 addr, string text);    // converts UTF-8 to UTF-16
```

## Bulk read/write

```cpp
array<uint8> proc.rvm(uint64 addr, uint64 size);             // length = bytes actually read
bool         proc.wvm(uint64 addr, array<uint8> bytes);      // gated: write_memory
```

## Typed reads / writes (vec / quat / mat)

Read a `vec2`/`vec3`/`vec4`/`quat`/`mat4` directly from process memory. `_fl32` reads source bytes as float32 (promoted to float64 in the result); `_fl64` reads source bytes as float64. `mat4` is a row-major 4x4. `quat` is `x, y, z, w` packed.

```cpp
vec2 proc.read_vec2_fl32(uint64 addr);
vec2 proc.read_vec2_fl64(uint64 addr);
vec3 proc.read_vec3_fl32(uint64 addr);
vec3 proc.read_vec3_fl64(uint64 addr);
vec4 proc.read_vec4_fl32(uint64 addr);
vec4 proc.read_vec4_fl64(uint64 addr);
quat proc.read_quat_fl32(uint64 addr);
quat proc.read_quat_fl64(uint64 addr);
mat4 proc.read_mat4_fl32(uint64 addr);
mat4 proc.read_mat4_fl64(uint64 addr);
```

Writes mirror the reads (gated: `write_memory`):

```cpp
bool proc.write_vec2_fl32(uint64 addr, vec2 v);
bool proc.write_vec2_fl64(uint64 addr, vec2 v);
bool proc.write_vec3_fl32(uint64 addr, vec3 v);
bool proc.write_vec3_fl64(uint64 addr, vec3 v);
bool proc.write_vec4_fl32(uint64 addr, vec4 v);
bool proc.write_vec4_fl64(uint64 addr, vec4 v);
bool proc.write_quat_fl32(uint64 addr, quat q);
bool proc.write_quat_fl64(uint64 addr, quat q);
bool proc.write_mat4_fl32(uint64 addr, mat4 m);
bool proc.write_mat4_fl64(uint64 addr, mat4 m);
```

Reads return the value directly:

```cpp
proc_t p = ref_process("game.exe");
vec3 cam_pos = p.read_vec3_fl32(p.base_address() + 0x10A4830);
println("camera at " + cast<string>(cam_pos.x) + "," + cast<string>(cam_pos.y));
```

Failed reads (bad address, kernel-RW gate denial, dead proc handle) return a zero-initialized value of the right type — chained `.x` / `.m[i]` stays safe instead of AVing through null. Writes return `false` on the same failure cases.

Same kernel-RW gate semantics as the rest of the proc API — see [Permissions](#permissions).

## SIMD-width reads/writes

```cpp
array<uint8> proc.r128(uint64 addr);    // 16 bytes
array<uint8> proc.r256(uint64 addr);    // 32 bytes
array<uint8> proc.r512(uint64 addr);    // 64 bytes

bool proc.w128(uint64 addr, array<uint8> bytes);   // gated: write_memory
bool proc.w256(uint64 addr, array<uint8> bytes);   // gated: write_memory
bool proc.w512(uint64 addr, array<uint8> bytes);   // gated: write_memory
```

## Modules and exports

```cpp
uint64                proc.get_module_base(string name);     // 0 if missing
uint64                proc.get_module_size(string name);     // 0 if missing
array<module_info_t>  proc.get_module_list();                // every loaded module
uint64                proc.get_proc_address(uint64 module_base, string export_name);
uint64                proc.get_import_rdata_address(uint64 module_base, string import_name);
```

`module_info_t` methods:

```cpp
string m.name();    // base DLL filename, e.g. "kernel32.dll"
uint64 m.base();    // DllBase
uint64 m.size();    // SizeOfImage
```

Example — list every module loaded in the target:

```cpp
array<module_info_t> mods = p.get_module_list();
for (module_info_t m : mods) {
    println(format("{s}  base=0x{x}  size=0x{x}", m.name(), m.base(), m.size()));
}
```

## Pattern scanning

```cpp
uint64        proc.find_code_pattern    (uint64 search_start, uint64 search_size, string sig);
array<uint64> proc.find_all_code_patterns(uint64 search_start, uint64 search_size, string sig);
```

Sig syntax: hex bytes separated by spaces, `??` is a wildcard. Example: `"48 8B ?? ?? 48 89"`.

## Threads

```cpp
array<uint64> proc.get_all_tebs();
```

## Pointer arrays

```cpp
array<uint64> proc.read_pointer_array(uint64 base, int64 count, int64 offset_delta);
```

Reads `count` consecutive `uint64`s starting at `base`. `offset_delta` is added to each value before storing (useful when the target stores relative offsets).

## VAD / virtual\_query

Both calls **exclude PE-image regions** (modules, exes). Use `get_module_base/size` for those.

```cpp
vad_region_t        proc.virtual_query(uint64 address);
array<vad_region_t> proc.get_vad_snapshot(bool heap_likely_only);
```

`virtual_query` returns a `vad_region_t` handle on hit, `0` on miss.

### `vad_region_t`

```cpp
uint64 region.start();
uint64 region.size();
uint64 region.protection();   // host page-protection bits (PAGE_READWRITE, PAGE_EXECUTE, etc.)
bool   region.heap_likely();  // host's heuristic for heap allocations
```

```cpp
array<vad_region_t> snap = p.get_vad_snapshot(false);
for (int64 i = 0; i < snap.length(); i = i + 1) {
    vad_region_t r = snap.get(i);
    uint64 start = r.start();
    uint64 size  = r.size();
    uint64 prot  = r.protection();
    bool   heap  = r.heap_likely();
}
```

## Memory scans

All scans walk the VAD snapshot (so module memory is excluded — same caveat as above). `heap_only=true` restricts to heap-likely regions.

```cpp
array<uint64> proc.scan_string (string text,    bool heap_only);
array<uint64> proc.scan_wstring(string text,    bool heap_only);   // text is UTF-8, converted to UTF-16
array<uint64> proc.scan_pointer(uint64 target,  bool heap_only);
array<uint64> proc.scan_u64    (uint64 value,   bool heap_only);
array<uint64> proc.scan_u32    (uint32 value,   bool heap_only);
array<uint64> proc.scan_float  (float32 value,  bool heap_only);
array<uint64> proc.scan_double (float64 value,  bool heap_only);
```

## VM alloc / free (gated: `virtual_memory_operations`)

```cpp
uint64 proc.alloc_vm(uint64 size);   // 0 on failure
bool   proc.free_vm (uint64 address);
```

Allocation itself is safe. To execute code from the returned page, the target must have Control Flow Guard (CFG) disabled — CFG kills the process on indirect calls/jumps to non-bitmap addresses. Reads + writes are unaffected.

## Permissions

Three flags gate sensitive operations. All default to off; the user grants them per script via the host UI.

| Flag                        | Gates                                                                                 |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `write_memory`              | `wu*`, `w*`, `wf*`, `ws`, `wws`, `wvm`, `w128/256/512`                                |
| `virtual_memory_operations` | `alloc_vm`, `free_vm`                                                                 |
| `kernel_rw_access`          | `get_eprocess`; expands every other read/write to also accept *safe* kernel addresses |

When a gated call runs without permission it logs `[ENMA] ... blocked: '<flag>' permission not granted` and returns 0 / false.

### `kernel_rw_access` semantics

Without it, every read/write address must pass `is_usermode_address` — i.e. canonical user-range, non-null, non-tiny. This is the default and matches the original behavior.

With it, addresses are accepted when **either**:

* The address is a valid usermode address (same check as before), **or**
* The address is a *safe kernel address* — canonical kernel range AND not in any host-protected critical region (the host's own EPROCESS / ETHREAD / kernel state used for privilege escalation).

The "safe kernel" denylist is enforced by `is_safe_kernel_address` in the host. Scripts can't bypass it: a kernel write to a denied address returns `false` and logs, just like any other refused op.

Use this flag when a script genuinely needs to inspect or modify kernel structures of the target process (Win32 thread state, KPCR fields, driver-side game state, etc.). Don't grant it casually — kernel writes to the wrong address bugcheck the box.

## Lifetime and cleanup

`proc_t` releases its host ref via the destructor when the variable goes out of scope. If a script forgets (e.g. leaks a `proc_t*` heap-allocation), the host sweeps remaining refs at script unload — no permanent leak.

```cpp
int64 main() {
    proc_t p = ref_process("notepad.exe");
    if (!p.alive()) return 0;

    uint64 base = p.base_address();
    println(cast<string>(p.r32(base + 0x3C)));    // e_lfanew

    return 0;
    // p drops here; host ref released
}
```

## Conventions

* **Addresses are `uint64`.** Use `uint64` for any local that holds an address — hex literals like `0x7FF000000000` work directly. Mixing in an `int64` requires `cast<uint64>(...)`.
* **Failed reads return 0**, not an exception. Check `is_valid_address` first if you need certainty.
* **Strings returned by `rs`/`rws`** are heap strings — drop normally at scope exit.
* **Array returns are length-correct.** `arr.length()` is the actual element count, not a max.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/proc-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
