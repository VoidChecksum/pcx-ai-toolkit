---
name: mcp-tool-routing
description: >
  Routing guide for the 59 Perception MCP tools — which to pick for memory
  reads, scans, disassembly, PE/module walks, and the Enma scripting bridge
  to avoid slower or redundant calls. Always active when calling Perception
  MCP tools. Answers "which tool for this task" so the AI picks the cheapest
  tool with the required precision.
license: MIT
---

# Perception MCP Tool Routing — The Decision Guide

59 tools across memory I/O, modules/threads/PE, memory regions, pattern/scanner/xrefs/signature, code analysis, symbol/function lookup, handles, system/environment, and the Enma scripting bridge. This skill answers "which one for this task" so the AI doesn't reach for the wrong tool. The Perception MCP server (`mcp/perception-mcp-config.json`, kept in sync with `docs/perception/mcp-api.md` by CI) exposes a wide surface where several tools overlap in capability but differ wildly in cost or precision — using `process/read_virtual_memory` for what `process/read_typed_value` does costs you a parse step; using `process/find_pattern` for what `process/scan_string` does is an order of magnitude slower; using `process/find_function_by_signature` for what `process/find_function_bounds` does costs an unnecessary AOB rescan. Routing matters.

**Always active when calling Perception MCP tools.** Before every MCP call, the question is: am I picking the cheapest tool that gives me the precision I need? This skill makes that decision tree explicit.

**Prerequisite:** `mcp/perception-mcp-config.json` is the authoritative 59-tool list and signatures. `mcp/claude-code-setup.md` covers the wiring. `mcp/cursor-setup.md` covers the Cursor variant. This skill is the *routing* layer that sits above all of those.

**Three load-bearing facts that shape every routing decision below:**

1. **Addresses + handles are HEX STRINGS** (`"0x7ff7..."`), not JSON numbers — JSON numbers lose precision past 2^53. Every `address`/`module_base`/`target_address`/`handle` param is a hex string.
2. **Handles are per-connection.** Most `process/*` tools take a `handle` as their first param (omitted from the param columns below for readability). You obtain it with `process/reference_by_pid` or `process/reference_by_name`; other connections can't use it; disconnecting releases everything; `process/dereference` releases one, `process/cleanup_references` releases all, `process/list_references` shows what you hold. A stale/cross-connection handle returns `-32002`. **Acquire a handle before any process-scoped call.**
3. **Permissions gate whole tool classes.** Toggle in Perception's *Scripting → API permissions*:
   - `kernel_rw_access` → kernel addresses in any read/write/disasm/`query_memory_region`/`find_pattern*` call, the `eprocess` field in `process/list` + `info_by_*`, the `ethread` field in `process/get_threads`, and `system/list_drivers`.
   - `write_memory` → every write tool: `process/write_virtual_memory`, `process/write_typed_value`, `process/write_string`, `process/copy_memory`, `process/fill_memory`.
   - `virtual_memory_operations` → `process/allocate_memory`, `process/free_memory`.

   A blocked call returns `-32001` naming the missing permission. Surface this in the routing advice where relevant.

---

## Trigger

About to call a Perception MCP tool: deciding between `process/read_virtual_memory` vs `process/read_typed_value` vs `process/read_pointer_chain`, choosing between `process/find_pattern` vs `process/scan_string` vs `process/find_string_refs`, deciding when `process/disassemble` is enough vs an iterative bounds+disasm walk, deciding whether to call a tool per-frame or cache the result, composing multiple tools into a workflow, or deciding which `script/*` call answers a scripting question.

---

## 0. Attach to the Target (handles — a prerequisite)

**Before any `process/*` call that takes a handle, you must hold one.** This is the first routing decision of every session.

```
Know the PID?            → process/reference_by_pid(pid)          → handle (hex string)
Know the image name?     → process/reference_by_name(name)        → handle (hex string)
Just want to browse?     → process/list()                          → [{pid, name, ...}]
Confirm one process?     → process/info_by_pid(pid) / info_by_name(name)
What handles do I hold?  → process/list_references()                → per-connection table
Done with one target?    → process/dereference(handle)              → releases that one
Session ending / reset?  → process/cleanup_references()             → releases all
```

`process/list` and `process/info_by_*` do **not** require a handle — they enumerate. Everything scoped to a live target (memory I/O, modules, scans, disasm) does. `system/info`, `system/list_drivers`, `script/*`, and the handle-lifecycle tools themselves take no handle.

**Why:** Skipping the reference step is the #1 first-call failure. `-32002` (stale/cross-connection handle) almost always means "I forgot to acquire one this session" or "I'm reusing a handle from a connection that disconnected."

---

## 1. "I Need to Read N Bytes at Address X"

**Decision tree, cheapest precise option first.** Every call below takes a `handle` plus the params shown.

```
Is it a typed scalar (one int / float / pointer / bool)?
  └── yes → process/read_typed_value(handle, address, type)
            type ∈ u8..u64 / i8..i64 / f32 / f64 / ptr / bool
            cheapest; one round trip; parsed for you

Is it a null-terminated / length-capped string?
  └── yes → process/read_string(handle, address, max_len?, encoding?)
            max_len default 1024; encoding ∈ auto/ascii/utf16 (auto-sniffs)
            chooses null termination over fixed length

Is it a pointer chain (deref → +offset → deref → ...)?
  └── yes → process/read_pointer_chain(handle, base_address, offsets[])
            offsets is an int array, max 64; saves N round trips

Need to know the address resolves at all before reading?
  └── yes → process/is_valid_address(handle, address)   (cheap guard)

Otherwise — a raw byte buffer (struct, blob, opcode bytes):
  └── process/read_virtual_memory(handle, address, size)
            returns bytes as hex; max 16 MiB; no parsing
```

The cost gradient (cheapest left, most expensive right):

```
process/is_valid_address < process/read_typed_value < process/read_string < process/read_pointer_chain < process/read_virtual_memory(large N)
```

**There is no server-side struct dumper.** Reading a whole struct means `process/read_virtual_memory(addr, sizeof_struct)` + client-side parse, or one `process/read_typed_value` per field. Pick by shape: a 12-byte vec3 is one `process/read_virtual_memory` (12 bytes, one trip) vs three `process/read_typed_value` calls (three trips) — take the single read when you need all the bytes; take the typed read when you need one field cheaply. If you'll re-read the same struct shape often, define it in your Enma script instead of wishing for a dumper the server doesn't provide.

`process/read_pointer_chain` is the killer feature for entity-list walks. Instead of `process/read_typed_value` × 3 (deref base, deref +offset, deref +offset), one call does all three — but the chain is capped at 64 offsets.

**Why:** Most "slow MCP" complaints reduce to picking `process/read_virtual_memory` when a typed variant would be faster, or picking three calls when `process/read_pointer_chain` would do it in one. The cost of a wrong choice is per-frame latency; the cost of the right choice is reading the doc once.

---

## 2. "I Need to Find Something in Memory"

**Different "find" tools for different inputs.** Picking the wrong one is the most common search-related mistake. All take a `handle`.

```
What are you looking for?
  ASCII string?                          → process/scan_string(text, encoding:"ascii", heap_only?)
  UTF-16LE string?                       → process/scan_string(text, encoding:"utf16", heap_only?)
                                          (no separate wide-string scanner — the encoding param picks it)
  Specific numeric value (1..8 bytes)?   → process/scan_value(type, value, aligned?, heap_only?)
                                          type ∈ u8..u64 / i8..i64 / f32 / f64; value is hex for u64/i64
  A pointer to a known address?          → process/scan_pointer_to(target_address, heap_only?)
  A code pattern (bytes + wildcards)?    → process/find_pattern(start, size, signature)        (first hit)
                                          or process/find_all_patterns(start, size, signature)   (cap 1024 hits)
  References to a function in code?      → process/find_xrefs(module_base, target_address)       (decodes .text)
  References to a known string?          → process/find_string_refs(module_base, text, encoding?, heap_only?, string_module?)
  What changed since a snapshot?         → process/scan_next(compare, value?, min?, max?)
                                          compare ∈ exact/range/unchanged/changed/increased/decreased
                                          then process/diff_memory(addr_a, addr_b, size) for byte-level diffs
  What module owns this VA?              → process/lookup_symbol(address)  (VA → module+offset+nearest export)
```

The cost gradient (cheapest first):

```
process/scan_string ~ process/scan_value < process/scan_pointer_to < process/find_pattern < process/find_xrefs < process/find_string_refs < process/scan_next(iterative) < process/diff_memory
```

Special-case observations:

- **`process/scan_string` is the one string scanner** — pass `encoding:"utf16"` for wide strings; there is no separate wide-string tool. `heap_only` defaults to the MCP UI's "Heap-only by default" toggle (on by default); pass `heap_only=false` only if you need to walk the full image.
- **`process/scan_value` with `aligned` (default true)** is the right tool for a discriminating data field — alignment narrows the hit set by 4–8×. For u64/i64, `value` is a hex string.
- **`process/scan_pointer_to` is the right tool for "find every variable that points to this object"** — aligned-QWORD scan, faster than `process/find_pattern` for an 8-byte address because alignment is known and obvious-noise patterns are excluded.
- **`process/find_pattern` takes `start` + `size` + an IDA-style signature** (`"AB CD ?? EF"`). It is for *code* sigs on a bounded region — usually a module's `.text`. For data search (string/value/pointer), the dedicated scan tools are 5–10× faster because they know the type they're hunting. Use `process/find_all_patterns` when you need every hit (cap 1024).
- **`process/find_string_refs` does the cross-reference walk for you**: pass a string literal, get back every instruction that loads it via `LEA`/`MOV [rip+...]`. Phase 1 (string search) is **pre-capped at 1 GiB** — if the cap fires, the call errors and asks you to pass `heap_only=true` or set `string_module` (hex VA of the module that owns the string, usually the same as `module_base`) for a fast bounded scan. Phase 2 caps code hits at 4096 and sets a `truncated` flag. The combo `scan the label → find_string_refs → disassemble the call site` is the canonical "find the function that owns this UI element" workflow.
- **The cheat-engine workflow is `process/scan_next` + `process/diff_memory`, not a whole-process snapshot.** There is no tool that snapshots the entire process. `process/scan_next(compare:"changed")` narrows the value-type hits you've accumulated across scans; `process/diff_memory(addr_a, addr_b, size)` gives byte-level before/after on a region you choose (cap 1 MiB). Decide the region up front — there is no global diff.

**Why:** `process/find_pattern` is the tool every new user reaches for because it sounds the most general. It's actually the most *specialized* — it scans a bounded region for a byte pattern. For data search (string, value, pointer), the dedicated scan tools are faster because they know the type they're hunting for. And the "what changed" workflow is `scan_next` (typed narrowing) + `diff_memory` (region diff), not a magic snapshot tool.

---

## 3. "I Need to Understand This Function"

**Cost-tiered: just see the asm vs walk bounds vs AOB-rescan. Pick the depth you actually need.** All take a `handle`.

```
Just want the disassembly of a few instructions?
  → process/disassemble(handle, address, max_bytes?, max_instructions?)
    Zydis; defaults 256 bytes / 32 insns; cheap; bytes → asm

Need start/end of the function containing addr?
  → process/find_function_bounds(handle, address, scan_back?, scan_forward?)
    heuristic; defaults 4096 back / 65536 forward; returns [start, end]
    for precision, use process/get_exception_table(module_base) — .pdata RUNTIME_FUNCTION entries are exact

Need to find a function by an AOB sig across a module?
  → process/find_function_by_signature(handle, module_base, signature)
    AOB-scans .text + runs bounds walk on each hit; more expensive than a single bounds call

Want to know what function lives at a VA / which module owns it?
  → process/lookup_symbol(handle, address)
    VA → {module_base, module_name, module_offset, section, nearest_export}
  → process/find_function_by_name(handle, pattern, case_sensitive?, max_results?)
    substring match across all modules' export tables; default case-insensitive, 64 results
```

There is **no function-analyzer tool** and **no call-graph builder**. For "what does this function call," `process/disassemble` the body and read the `CALL`/`JMP` targets yourself (iterate `process/find_xrefs` if you need incoming callers). For "what value is in RCX at this instruction," there is **no register-tracer** — `process/disassemble` the surrounding instructions and reason about the register set (a `MOV RCX, [rip+x]` tells you the source; a `LEA RCX, [...]` likewise). State the limitation honestly: the MCP gives you bytes and disassembly; register-dataflow analysis is the client's job.

The standard composition:

```
process/find_pattern(start, size, sig)        → addr
process/find_function_bounds(handle, addr)    → [start, end]
process/disassemble(handle, start, end-start) → asm
process/lookup_symbol(handle, call_target)    → which export each CALL hits
```

This is the four-step "what does this code path do?" workflow that replaces an IDA session for most questions. For precise bounds (stripped binaries, no heuristics), swap `process/find_function_bounds` for `process/get_exception_table(module_base)` and look up the RUNTIME_FUNCTION covering `addr`.

**Why:** `process/find_function_by_signature` is the expensive one here — it AOB-scans a whole module's `.text` and bounds-walks every hit. Calling it when `process/disassemble` of a known address would do is multi-second latency vs millisecond latency. The cost isn't visible until you wire one into a per-frame path.

---

## 4. "I Need to Understand This Class / VTable"

**Two tools, often used together.** Both take a `handle`.

```
Want the vtable function-pointer layout?
  → process/analyze_vtable(handle, vtable_address, max_entries?)
    default 64 entries; classifies each as code/data per loaded modules

Want the RTTI class name + parent chain?
  → process/read_rtti(handle, vtable_address)
    Win64 RTTI: class name string + base-class hierarchy
```

The combo gives you a full picture of "what is this object?" — start with `process/read_rtti` to know the class, then `process/analyze_vtable` to get the methods. Together they replace a Class Informer / Class Explorer pass in IDA. Note both take the **vtable address**, not the object address — deref the object to its vtable first (`process/read_typed_value(obj, "ptr")`).

Caveat: RTTI is only present in binaries compiled with `/GR` (MSVC) or `-frtti` (GCC/Clang). Stripped binaries return nothing useful from `process/read_rtti`. In that case, the vtable layout is your only handle on the class identity — name your `VTable_<addr>` yourself. For deeper PE truth (sections, exports, data dirs), see section 6.

**Why:** Class identification is half the battle in any C++ game RE. `process/read_rtti` answers "what is this?" in one call when it works; falling back to vtable layout matching is the alternative. Routing here is binary: try RTTI first, fall back to vtable analysis.

---

## 5. "I Need a Sig for This Address"

**`process/generate_signature(handle, address, max_length?)`** produces an IDA-style sig from the instruction at `addr`, wildcarding relocatable bytes (RIP-relative displacements, call targets). `max_length` defaults 32; the response carries `is_unique=false` if the length is exhausted without uniqueness.

Pair immediately with `tools/bin/sig-uniqueness-checker` (added in this branch) to validate:

```
1. process/generate_signature(handle, addr, 16)  → "48 8D 0D ?? ?? ?? ?? E8"
2. write to a temp file, then:
3. tools/bin/sig-uniqueness-checker game.exe --sig "..."
4. read the verdict:
   - UNIQUE margin=5    → ship it
   - AMBIGUOUS, N hits  → regenerate with longer max_length
   - STALE              → the sig doesn't match at the expected address (very rare; investigate)
   - BRITTLE margin=0   → regenerate longer
```

`max_length` is a starting point; iterate with `process/generate_signature(handle, addr, 24)` if the 16-byte version is ambiguous. Each generation is cheap; the validation step is also cheap. Iterate until UNIQUE with `margin ≥ 2` and add the sig to your `offsets.em` with an `// E-NNN` evidence reference (per `skill://re-evidence-log`).

To *use* a sig to find a function in a module you haven't attached to by address, `process/find_function_by_signature(handle, module_base, signature)` AOB-scans `.text` and bounds-walks each hit — heavier than a plain `process/find_pattern`, but it returns function bounds, not just a hit address.

**Why:** The MCP can generate sigs but cannot validate them; the local Rust tool can validate sigs but cannot generate them from a live address. The combination is the workflow.

---

## 6. "I Need to Know About the Process / Modules"

**Process, module, thread, and PE enumeration tools.** All cheap and safe to call at session start. The handle-less ones (`process/list`, `process/info_by_*`) come first; the rest take a `handle`.

```
What processes are running?                   → process/list()                                 (no handle)
One process by PID / by image name?           → process/info_by_pid(pid) / info_by_name(name)  (no handle)
All loaded modules in the target?             → process/get_modules(handle)
All threads?                                  → process/get_threads(handle)                   (ethread gated kernel_rw_access)
One module by name?                           → process/get_module_by_name(handle, name)
PE sections of a module?                      → process/get_module_sections(handle, module_base)
NT/optional header summary?                   → process/get_pe_header(handle, module_base)
One PE data directory?                        → process/get_data_directory(handle, module_base, directory)
                                              directory ∈ export/import/resource/exception/.../com_descriptor or 0..15
Full EAT walk?                                → process/list_module_exports(handle, module_base)
Single export resolve?                        → process/get_export_address(handle, module_base, export_name)
Full IAT walk?                                → process/get_module_imports(handle, module_base)
Single IAT slot VA?                           → process/get_import_address(handle, module_base, import_name)
All strings in a module image?                → process/get_module_strings(handle, module_base, min_length?, encoding?)
                                              min_length default 4; encoding ∈ ascii/utf16/both
Precise function bounds from .pdata?          → process/get_exception_table(handle, module_base, max_entries?)
Target's command line (PEB)?                 → process/get_command_line(handle)               (x64 only)
Target's environment block (PEB)?             → process/list_environment(handle, max_bytes?)  → [{key, value}]
System-wide handle table?                    → process/enum_handles(max_entries?)            (no handle; default 8192)
Build / page size / arch for keyed offsets?  → system/info()                                  (no handle; is_24h2_or_later flag)
Kernel modules?                              → system/list_drivers(max_entries?)             (no handle; gated kernel_rw_access)
```

`process/enum_handles`, `system/info`, and `system/list_drivers` take **no handle** — they query the system, not a referenced process.

For deeper cross-module analysis (which other modules import a specific export from this one), pair with `tools/bin/module-export-mapper --consumers <dir>` (added in this branch). The MCP gives you exports + imports per module; the Rust tool joins them into a "this DLL is consumed by ..." map.

`process/get_modules` is the right call when attaching: it returns the module list including base addresses + sizes, which is what you need for `process/find_pattern` calls bounded to a specific module. Don't iterate `process/list` + `process/list_module_exports` per module yourself — `process/get_modules` returns the full picture in one call.

**Why:** These tools are cheap and idempotent; the routing is mostly "use them rather than guessing." The only mistake is overusing `process/list` in a loop — it snapshots the system every call. Call it once; cache the result. And remember `system/info`'s `is_24h2_or_later` flag for build-keyed offsets — query it once per session, not per call.

---

## 7. Scripting Bridge (Enma)

**The Enma scripting bridge is three tools, none of which takes a `handle`.** They run a script (or return reference text) with their own permissions, independent of any referenced process. The bridge is exactly these three — there are no MCP tools for host file I/O, host text search, host reference finding, internet search, or duplicate script-lifecycle aliases. File reads/writes are NOT MCP tools; do them via the toolkit's standalone Rust tools or the Perception IDE.

```
Need the Enma language + Perception API reference?
  → script/get_context()
    Returns the full reference as one context string. CALL ONCE PER SESSION
    before generating any script — enma is proprietary and its addon surface
    can't be inferred from training data. Covers language grammar, all 17
    pre-shipped enma addons, and all 12 Perception API surfaces.

Syntax + type check only (no run)?
  → script/validate(source)
    Compile-only. ALL addons registered (render/proc/cpu/zydis/sound/win/
    unicorn/net/input/gui/thread/filesystem). Returns { ok, errors:[] }.
    Cheap; safe to run on every save.

Actually run the script?
  → script/execute(source)
    Compile + run main() once. Returns { ok, logs:[] }.
    GUI and thread addons are NOT registered here — those resources would
    outlive a one-shot script and leak. For long-lived scripts with GUI/
    threads, use the in-app script editor, not script/execute.
```

The validate→execute ladder:

- `script/get_context` first, once per session — load the reference so you emit valid enma.
- `script/validate` on every edit — compile-only, all addons registered, catches syntax + type errors. This is the only compile-check; there is no second script-lifecycle alias.
- `script/execute` only when you actually want to run it — has side effects, and **cannot** register GUI/thread addons.

**Why:** Mixing up `script/validate` and `script/execute` is the new-user mistake — running the script when you only wanted to check syntax. And assuming `script/execute` can spawn a GUI is the second mistake — it can't, by design. The progression reference → validate → execute is the right ladder; climb only as far as the question demands.

---

## 8. Cost Tiers — What's Expensive, What's Cheap

**Internalize these tiers. Cheap tools are fine in tight loops; expensive ones must be cached or called outside hot paths.** Latency feel is qualitative; the hard limits are the numbers that bite.

| Tier | Tools | Hard limits / notes | Latency feel |
|---|---|---|---|
| **Cheap** (sub-ms to few ms) | `process/list`, `process/info_by_pid`, `process/info_by_name`, `process/get_modules`, `process/get_module_by_name`, `process/get_threads`, `process/get_module_sections`, `process/get_pe_header`, `process/get_data_directory`, `process/get_export_address`, `process/get_import_address`, `process/is_valid_address`, `process/read_typed_value`, `process/read_string`, `process/read_pointer_chain` (≤64 offsets), `process/disassemble` (1–2 insns, default 256 B / 32 insns), `process/find_function_bounds`, `process/read_rtti`, `process/lookup_symbol`, `process/find_function_by_name` (default 64 results), `process/query_memory_region`, `process/get_command_line`, `process/list_environment`, `system/info`, `process/enum_handles` (default 8192) | First three + `system/info` + `enum_handles` take no handle. | Safe per-call when you need them |
| **Medium** (1–100 ms) | `process/scan_string`, `process/scan_value`, `process/scan_pointer_to`, `process/scan_next`, `process/find_pattern`, `process/find_all_patterns` (cap 1024 hits), `process/analyze_vtable` (default 64 entries), `process/find_xrefs`, `process/generate_signature`, `process/read_virtual_memory` (≤16 MiB), `process/copy_memory` (≤64 MiB in 1 MiB chunks), `process/list_module_exports`, `process/get_module_imports`, `process/get_module_strings`, `process/get_exception_table` | `heap_only` defaults to the UI toggle (on) for the scanners — flipping it off walks full user-space and can OOM on multi-GiB heaps. | Cache results; never call per-frame |
| **Expensive** (100 ms–10 s) | `process/find_string_refs` (phase 1 pre-capped 1 GiB; phase 2 caps code hits 4096), `process/find_function_by_signature` (module-wide AOB + bounds walk per hit), `process/diff_memory` (cap 1 MiB), `process/allocate_memory` (≤256 MiB), `process/enumerate_memory_regions` (full VAD walk), `system/list_drivers` (gated `kernel_rw_access`), `script/get_context` (returns the whole reference) | `find_string_refs` errors if the 1 GiB cap fires — pass `heap_only=true` or set `string_module`. | Manual workflow tools; never automated into hot paths |
| **Side-effecting** (permission-gated) | `process/write_virtual_memory`, `process/write_typed_value`, `process/write_string`, `process/copy_memory`, `process/fill_memory` (all gated `write_memory`); `process/allocate_memory`, `process/free_memory` (gated `virtual_memory_operations`); `process/dereference`, `process/cleanup_references` (release handles); `script/execute` (runs `main()`, no GUI/thread addons) | Blocked calls return `-32001` naming the missing permission. | Ask before doing; never in a render loop |

The pattern in PCX scripts: call medium-tier tools in `main()` (one-shot setup), cache results into globals, then in `on_update` / `on_render` only call cheap tools. The 12-rule discipline (`game-cheat-guidelines` rule #4: separate update from render; `skill://pcx-perf-budget` Step 5: cache expensive, recompute cheap) is the same principle applied to MCP calls.

**Why:** The MCP latency budget is shared with the rest of your frame. A 5 ms `process/find_pattern` in `on_render` at 144 Hz eats 72% of the frame. Tier awareness is what keeps the script smooth.

---

## 9. Composition Patterns — Tools That Compose Well

**The standard combos. Each is a multi-call workflow reused across most RE sessions.** Every `process/*` call here implicitly takes a `handle` acquired in section 0.

| Goal | Composition |
|---|---|
| "Attach to the target" | `process/list` → `process/reference_by_name(name)` → `process/get_modules` (cache bases+sizes) → `process/cleanup_references` on shutdown |
| "Find the function that handles a UI label" | `process/scan_string(text, encoding:"utf16")` → `process/find_string_refs(module_base, text)` → `process/disassemble(call_addr)` → `process/lookup_symbol(call_target)` |
| "Find a global pointer behind a LEA" | `process/find_pattern(start, size, sig)` → `process/disassemble(hit, max_instructions:1)` (confirm `LEA reg, [rip+x]`) → `process/read_typed_value(resolved, "ptr")` |
| "What are the args passed to this call?" | `process/disassemble(call_site, max_instructions:8)` (read the `MOV RCX/RDX/R8/R9` and `LEA` insns before the `CALL`) → reason about the register set client-side. No register-tracer exists. |
| "Map an entity struct" | `process/read_pointer_chain(base, [0, 0])` → `process/read_rtti(vtable_addr)` → `process/analyze_vtable(vtable_addr)` → `process/read_virtual_memory(entity, sizeof)` + client parse (no server-side struct dumper) |
| "Precise function bounds (stripped binary)" | `process/get_module_by_name(name)` → `process/get_exception_table(module_base)` → look up the RUNTIME_FUNCTION covering `addr` (fallback to `process/find_function_bounds` if no .pdata) |
| "Snapshot, perform action, diff" | `process/scan_value(type, value)` (baseline hits) → user does in-game action → `process/scan_next(compare:"changed")` (narrow) → `process/diff_memory(addr_a, addr_b, size)` for byte-level before/after on a chosen region (cap 1 MiB). No whole-process snapshot tool. |
| "Sig + validate" | `process/generate_signature(addr, 16)` → save → `tools/bin/sig-uniqueness-checker game.exe --sig "..."` → if margin < 2, regenerate longer |
| "Sig → function in a new build" | `process/get_module_by_name(name)` → `process/find_function_by_signature(module_base, sig)` → if STALE, broaden the sig and retry |
| "Which module owns this VA?" | `process/lookup_symbol(address)` → `{module_base, module_name, module_offset, section, nearest_export}` |
| "Write a one-shot Enma script" | `script/get_context` (once) → `script/validate(source)` (compile-only, all addons) → `script/execute(source)` (run `main()` once; no GUI/thread addons) |
| "Per-binary diff after patch" | `tools/bin/offset-diff --old V1 --new V2 --sigs old_offsets_json` → for each LOST: `process/find_pattern` against V2 with broadened sig → record new sig |

These compose without ceremony — each call's output is the next call's input. The AI should *reach for the composition* rather than asking "should I call N more tools?" — the workflow is the unit, not the individual call.

**Why:** Naming the compositions makes them habits. Without a name, every new user re-derives the workflow from scratch and asks each tool call as a separate question. Named compositions become muscle memory after a handful of uses.

---

## Summary — Goal → Tool Map

| Goal | Right tool | Wrong tool (common mistake) |
|---|---|---|
| Attach to a process | `process/reference_by_pid` / `process/reference_by_name` | calling process/* tools with no handle (`-32002`) |
| Read one int/float/ptr at address | `process/read_typed_value` | `process/read_virtual_memory` + manual unpack |
| Read a null-terminated string | `process/read_string` | `process/read_virtual_memory` + manual scan for `\0` |
| Follow a pointer chain (≤64 hops) | `process/read_pointer_chain` | N × `process/read_typed_value` |
| Read a whole struct | `process/read_virtual_memory(addr, sizeof)` + client parse (no server-side struct dumper) | N × `process/read_typed_value` |
| Guard a read against bad addr | `process/is_valid_address` | catching `-32004` from the read |
| Find ASCII/UTF-16 string | `process/scan_string(text, encoding)` (encoding param covers UTF-16) | `process/find_pattern` on the bytes |
| Find numeric value | `process/scan_value` | `process/find_pattern` |
| Find pointer to X | `process/scan_pointer_to` | `process/find_pattern` on 8 bytes |
| Find code pattern (first/all) | `process/find_pattern` / `process/find_all_patterns` | `process/scan_value` |
| Find xrefs to a function | `process/find_xrefs(module_base, target_address)` | `process/disassemble` + manual scan |
| Find xrefs to a string | `process/find_string_refs(module_base, text)` | `process/find_pattern` on the string bytes |
| What changed (typed narrowing) | `process/scan_next(compare:"changed")` | guessing addresses |
| Byte-level before/after diff | `process/diff_memory(addr_a, addr_b, size)` (cap 1 MiB) | whole-process snapshot (none exists) |
| Which module owns a VA | `process/lookup_symbol(address)` | guessing from `process/get_modules` |
| See some asm | `process/disassemble` | (nothing cheaper) |
| Get function start/end (heuristic) | `process/find_function_bounds` | `process/disassemble` + walk |
| Get function bounds (precise) | `process/get_exception_table(module_base)` (.pdata) | heuristic when .pdata exists |
| Find a function by sig in a module | `process/find_function_by_signature` | manual `find_pattern` + bounds loop |
| Find a function by export name | `process/find_function_by_name(pattern)` | `process/list_module_exports` + client filter |
| Get class name + parents | `process/read_rtti(vtable_addr)` | `process/analyze_vtable` (use both — RTTI first) |
| Get vtable layout | `process/analyze_vtable` | `process/read_virtual_memory` + manual deref |
| Generate a sig | `process/generate_signature` + `tools/bin/sig-uniqueness-checker` | hand-crafting bytes |
| List processes | `process/list` (no handle) | — |
| One process's info | `process/info_by_pid` / `process/info_by_name` (no handle) | — |
| All modules + bases | `process/get_modules` | `process/info_by_name` + re-walk |
| Module exports (all) | `process/list_module_exports(module_base)` | — |
| One export resolve | `process/get_export_address(module_base, name)` | full EAT walk for one name |
| Module imports (all) | `process/get_module_imports(module_base)` | — |
| One IAT slot | `process/get_import_address(module_base, name)` | full IAT walk for one name |
| PE sections / header | `process/get_module_sections` / `process/get_pe_header` | — |
| One data directory | `process/get_data_directory(module_base, directory)` | full header + parse |
| Strings in a module | `process/get_module_strings` | `process/scan_string` across the image |
| Inspect a memory region | `process/query_memory_region(address)` | `process/read_virtual_memory` (different question) |
| Enumerate committed regions | `process/enumerate_memory_regions(heap_only?)` | — |
| Allocate / free target memory | `process/allocate_memory` / `process/free_memory` (gated `virtual_memory_operations`) | — |
| Target command line / env | `process/get_command_line` / `process/list_environment` | — |
| System handle table | `process/enum_handles` (no handle) | — |
| Build / page size / 24H2 flag | `system/info` (no handle) | hardcoding build offsets |
| Kernel modules | `system/list_drivers` (no handle; gated `kernel_rw_access`) | — |
| Load Enma reference | `script/get_context` (once per session) | inferring enma from training data |
| Compile-check a script | `script/validate` (all addons) | `script/execute` (runs it) |
| Run a one-shot script | `script/execute` (no GUI/thread addons) | — |
| Write target memory | `process/write_virtual_memory` / `write_typed_value` / `write_string` / `copy_memory` / `fill_memory` (all gated `write_memory`) | — |

**Cross-references:** `mcp/perception-mcp-config.json` (authoritative 59-tool list), `mcp/claude-code-setup.md` / `mcp/cursor-setup.md` / `mcp/aider-setup.md` (per-IDE wiring), `tools/bin/sig-uniqueness-checker` / `tools/bin/offset-diff` / `removed dumper-to-enma converter` / `tools/bin/module-export-mapper` (local CLI tools that pair with MCP calls — file I/O and cross-module joins live here, NOT on the MCP server), `skill://pcx-perf-budget` (call-cost discipline that applies to MCP calls), `skill://re-evidence-log` (E-NNN cross-references record which MCP calls produced each offset).