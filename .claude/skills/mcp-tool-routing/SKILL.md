# Perception MCP Tool Routing — The Decision Guide

37 tools across memory / analysis / scanning / process / files. This skill answers "which one for this task" so the AI doesn't reach for the wrong tool. The Perception MCP server (`mcp/perception-mcp-config.json`) exposes a wide surface where several tools overlap in capability but differ wildly in cost or precision — using `read_memory` for what `read_typed_value` does costs you a parse step; using `find_pattern` for what `scan_string` does is an order of magnitude slower; using `analyze_function` for what `disassemble` does costs an unnecessary IDA-style pass. Routing matters.

**Always active when calling Perception MCP tools.** Before every MCP call, the question is: am I picking the cheapest tool that gives me the precision I need? This skill makes that decision tree explicit.

**Prerequisite:** `mcp/perception-mcp-config.json` is the authoritative tool list and signatures. `mcp/claude-code-setup.md` covers the wiring. `mcp/cursor-setup.md` covers the Cursor variant. This skill is the *routing* layer that sits above all of those.

---

## Trigger

About to call a Perception MCP tool, deciding between `read_memory` vs `read_typed_value` vs `struct_dump`, choosing between `find_pattern` vs `scan_string` vs `find_string_refs`, deciding when `analyze_function` is worth its cost over `disassemble`, deciding whether to call a tool per-frame or cache the result, composing multiple tools into a workflow.

---

## 1. "I Need to Read N Bytes at Address X"

**Decision tree, cheapest precise option first:**

```
Is it a typed scalar (one int / float / pointer)?
  └── yes → read_typed_value(addr, type)
            cheapest; parses for you; one round trip

Is it a known struct (you have a declaration)?
  └── yes → struct_dump(addr, struct_name)
            one read of the whole struct, parsed by name

Is it a pointer chain (deref → +offset → deref → ...)?
  └── yes → read_pointer_chain(start, [offsets...])
            saves N round trips; the server does the chase

Is it a null-terminated string?
  └── yes → read_string(addr, max_len, charset?)
            chooses null termination over fixed length

Otherwise — a raw byte buffer:
  └── read_memory(addr, length)
            no parsing, returns bytes
```

The cost gradient (cheapest left, most expensive right):

```
read_typed_value < read_string < struct_dump < read_pointer_chain < read_memory(large N)
```

`read_memory` for a 4-byte field where `read_typed_value` would do it costs you a manual struct-unpack on the client side and one extra parse round trip. `read_memory` for a 12-byte vec3 where `read_typed_value` for each component would also work depends — if you call `read_typed_value` three times, that's three round trips vs one `read_memory` for 12 bytes. Use `read_memory` when N ≥ 8 *and* you need the raw bytes, or use `read_typed_value` when you need one specific component cheaply.

`struct_dump` requires that the server side knows the struct. When it does, it's the right answer almost always. When it doesn't, fall back to `read_memory(addr, sizeof_struct)` + client-side parsing — but consider whether to define the struct so future calls are clean.

`read_pointer_chain` is the killer feature for entity-list walks. Instead of `read_typed_value` × 3 (deref base, deref +offset, deref +offset), one call does all three.

**Why:** Most "slow MCP" complaints reduce to picking `read_memory` when a typed variant would be faster, or picking three calls when `read_pointer_chain` would do it in one. The cost of a wrong choice is per-frame latency; the cost of the right choice is reading the doc once.

---

## 2. "I Need to Find Something in Memory"

**Different "find" tools for different inputs.** Picking the wrong one is the most common search-related mistake.

```
What are you looking for?
  ASCII / UTF-8 string?  → scan_string(needle, [section?])
  UTF-16LE string?       → scan_wstring(needle, [section?])
  Specific numeric value (4/8 bytes)?  → scan_value(value, size)
  A pointer to a known address?         → scan_pointer_to(target_addr)
  A specific instruction pattern (bytes + wildcards)?  → find_pattern(bytes, mask)
  References to a function in code?     → find_xrefs(func_addr)
  References to a known string?         → find_string_refs(string_addr OR string_literal)
  What changed since I last looked?     → scan_changed() then diff_memory(then, now)
```

The cost gradient (cheapest first):

```
scan_string ~ scan_wstring ~ scan_value < scan_pointer_to < find_pattern < find_xrefs < find_string_refs < scan_changed
```

Special-case observations:

- **`find_pattern` is for *code* sigs**, not random data — it's faster on `.text` than `.data` because the search is bounded to executable sections by default. If you're searching `.data`, a `scan_value` for the discriminating field is usually faster.
- **`scan_pointer_to` is the right tool for "find every variable that points to this object"** — pointer scans for tracing object ownership / entity-list discovery. Faster than `find_pattern` for an 8-byte address because the search knows the alignment and excludes obvious-noise patterns.
- **`find_string_refs` does the cross-reference walk for you**: pass a string literal, get back the addresses of every instruction that loads it via `LEA`/`MOV [rip+...]`. The combo `find a UI label → find_string_refs → analyze_function` is the canonical "find the function that owns this UI element" workflow.
- **`scan_changed` + `diff_memory` is the cheat-engine workflow**: snapshot the process state, do an in-game action, snapshot again, diff. The output is a list of changed addresses + before/after values. Use sparingly — it scans the whole process and is expensive.

**Why:** `find_pattern` is the tool every new user reaches for because it sounds the most general. It's actually the most *specialized* — it scans `.text` for code patterns. For data search (string, value, pointer), the dedicated scan tools are 5-10× faster because they know the type they're hunting for.

---

## 3. "I Need to Understand This Function"

**Cost-tiered: just see the asm vs full IDA-style analysis. Pick the depth you actually need.**

```
Just want the disassembly of a few instructions?
  → disassemble(addr, num_insns)
    cheap; one call; bytes → asm

Need start/end of the function containing addr?
  → find_function_bounds(addr)
    cheap; returns [start, end]

Need what the function calls + complexity hints?
  → analyze_function(addr)
    medium; recursive into prologue/epilogue, calls table

Need the full call graph rooted at addr?
  → build_call_graph(addr, depth)
    expensive; can be slow on deep / wide call graphs — cap depth

Need to know what value RCX/RDX/etc. holds at a specific instruction?
  → trace_register(addr, register, direction)
    medium; useful for "what's the first argument to this call site"
```

The standard composition:

```
find_pattern(sig)              → addr
find_function_bounds(addr)     → [start, end]
disassemble(start, end-start)  → asm
trace_register(call_addr, RCX) → what gets passed
```

This is the four-step "what does this code path do?" workflow that replaces an IDA session for most questions.

Avoid `build_call_graph` unless you actually need the graph as a graph. For "what does this function call," `analyze_function` returns the immediate call list, which is usually what you wanted.

**Why:** `analyze_function` and `build_call_graph` are the most expensive tools in the routing table. Calling them when `disassemble` would do is multi-second latency vs millisecond latency. The cost isn't visible until you wire one into a per-frame path.

---

## 4. "I Need to Understand This Class / VTable"

**Two tools, often used together:**

```
Want the vtable function-pointer layout?
  → analyze_vtable(vtable_addr)
    returns ordered list of [offset, function_addr] entries

Want the RTTI class name + parent chain?
  → read_rtti(object_addr)
    returns class name string + inheritance hierarchy
```

The combo gives you a full picture of "what is this object?" — start with `read_rtti` to know the class, then `analyze_vtable` to get the methods. Together they replace a Class Informer / Class Explorer pass in IDA.

Caveat: RTTI is only present in binaries compiled with `/GR` (MSVC) or `-frtti` (GCC/Clang). Stripped binaries return nothing useful from `read_rtti`. In that case, the vtable layout is your only handle on the class identity — name your "VTable_<addr>" yourself.

**Why:** Class identification is half the battle in any C++ game RE. `read_rtti` answers "what is this?" in one call when it works; falling back to vtable layout matching is the alternative. Routing here is binary: try RTTI first, fall back to vtable analysis.

---

## 5. "I Need a Sig for This Address"

**`generate_signature(addr, length_hint)` produces a sig from the instruction at `addr`, with sensible wildcarding of relocatable bytes (RIP-relative displacements, call targets).**

Pair immediately with `tools/sig-uniqueness-checker.py` (added in this branch) to validate:

```
1. generate_signature(addr, 16)         → "48 8D 0D ?? ?? ?? ?? E8"
2. write to a temp file, then:
3. python3 tools/sig-uniqueness-checker.py game.exe --sig "..."
4. read the verdict:
   - UNIQUE margin=5    → ship it
   - AMBIGUOUS, N hits  → regenerate with longer length
   - STALE              → the sig doesn't match at the expected address (very rare; investigate)
   - BRITTLE margin=0   → regenerate longer
```

The `length_hint` is a starting point; you can iterate with `generate_signature(addr, 24)` if the 16-byte version is ambiguous. Each generation is cheap; the validation step is also cheap. Iterate until UNIQUE with `margin ≥ 2` and add the sig to your `offsets.em` with an `// E-NNN` evidence reference (per `skill://re-evidence-log`).

**Why:** The MCP can generate sigs but cannot validate them; the local Python tool can validate sigs but cannot generate them from a live address. The combination is the workflow.

---

## 6. "I Need to Know About the Process / Modules"

**Process and module enumeration tools.** All cheap; safe to call at script start.

```
What processes are running?                → list_processes()
Info on one process (pid, threads, modules)? → get_process_info(pid OR name)
What does this module export?              → get_module_exports(module_name)
What does this module import?              → get_module_imports(module_name)
```

For deeper cross-module analysis (which other modules import a specific export from this one), pair with `tools/module-export-mapper.py --consumers <dir>` (added in this branch). The MCP gives you exports + imports per module; the Python tool joins them into "this DLL is consumed by ..." map.

`get_process_info` is the right call when attaching: it returns the module list including base addresses + sizes, which is what you need for `find_pattern` calls bounded to a specific module. Don't iterate `list_processes` + `get_module_exports` per module yourself — `get_process_info` returns the full picture in one call.

**Why:** These tools are cheap and idempotent; the routing is mostly "use them rather than guessing." The only mistake is overusing `list_processes` in a loop — it scans the system every call. Call it once; cache the result.

---

## 7. "I Need to Work with Files / Scripts"

**File and script lifecycle tools.** Mostly self-explanatory but the validate/check/execute trio is worth mapping out.

```
Read a file:        read_file(path)
Write a file:       write_file(path, contents)
Patch a file:       edit_file(path, [{search, replace}, ...])

Grep across files:  search_text(pattern, [scope?])
Find references:    find_references(symbol, [scope?])

Compile-only:       check_script(path)   ← syntax + types, no run
Semantic check:     validate_script(path) ← deeper passes (unused decls, etc.)
Run it:             execute_script(path)  ← actually loads + runs

What APIs are available? get_script_api()  ← runtime API surface for the active scripting language
```

The check/validate/execute progression:

- `check_script` first — compile-only, catches syntax + type errors. Cheap; safe to run on every save.
- `validate_script` when you're about to ship — deeper checks: unused decls, unreachable code, suspicious patterns. Slower; run before release.
- `execute_script` only when you actually want to run it — actively loads into the engine and starts callbacks. Has side effects (attaches to processes, allocates GPU resources).

`get_script_api()` is the version-introspection tool — returns the currently-available API surface, useful for runtime checks and for documenting what your script depends on. Pair with `knowledge/pcx-version-matrix.md` for the historical timeline.

**Why:** Mixing up `check_script` and `execute_script` is the new-user mistake — running the script when you only wanted to check syntax. The progression cheap → medium → side-effecting is the right ladder; climb only as far as the question demands.

---

## 8. Cost Tiers — What's Expensive, What's Cheap

**Internalize these tiers. Cheap tools are fine in tight loops; expensive ones must be cached or called outside hot paths.**

| Tier | Tools | Latency feel |
|---|---|---|
| **Cheap** (<1 ms typical) | `list_processes`, `get_process_info`, `get_module_exports`, `get_module_imports`, `read_typed_value`, `read_memory` (small), `read_string`, `disassemble` (1-2 insns), `find_function_bounds`, `read_rtti` | Safe per-call when you need them |
| **Medium** (1-100 ms) | `find_pattern`, `scan_string`, `scan_wstring`, `scan_value`, `scan_pointer_to`, `struct_dump`, `read_pointer_chain`, `read_memory` (large), `analyze_function` (small), `analyze_vtable`, `find_xrefs`, `find_string_refs`, `trace_register`, `generate_signature` | Cache results; never call per-frame |
| **Expensive** (100 ms-10 s) | `build_call_graph` (deep), `analyze_function` (with deep recursion), `scan_changed` (whole-process), `diff_memory` (large region), `search_text` (large codebase), `find_references` (large codebase), `validate_script` (large project), `web_search` | Manual workflow tools; never automated into hot paths |
| **Side-effecting** | `memory_write`, `write_file`, `edit_file`, `execute_script` | Permission-gated; ask before doing |

The pattern in PCX scripts: call medium-tier tools in `main()` (one-shot setup), cache results into globals, then in `on_update` / `on_render` only call cheap tools. The 12-rule discipline (`game-cheat-guidelines` rule #4: separate update from render; `skill://pcx-perf-budget` Step 5: cache expensive, recompute cheap) is the same principle applied to MCP calls.

**Why:** The MCP latency budget is shared with the rest of your frame. A 5 ms `find_pattern` in `on_render` at 144 Hz eats 72% of the frame. Tier awareness is what keeps the script smooth.

---

## 9. Composition Patterns — Tools That Compose Well

**The standard combos. Each is a four-to-five-call workflow that's reused across most RE sessions.**

| Goal | Composition |
|---|---|
| "Find the function that handles a UI label" | `scan_string(label)` → `find_string_refs(addr)` → `analyze_function(call_addr)` |
| "Find a global pointer behind a LEA" | `find_pattern(sig)` → `read_typed_value(hit+3, "int32")` (the disp) → resolve RIP manually → `read_typed_value(resolved, "uint64")` |
| "What are the args passed to this call?" | `disassemble(call_site, 1)` (confirm it's a CALL) → `trace_register(call_site, "rcx", "backward")` → repeat for `rdx`, `r8`, `r9` |
| "Map an entity struct" | `read_pointer_chain([entity_list_base, 0, 0])` → `read_rtti(entity_ptr)` → `analyze_vtable(vtable_ptr)` → `struct_dump(entity_ptr, "CEntity")` |
| "Snapshot, perform action, diff" | `scan_changed()` (snapshot 1) → user does in-game action → `scan_changed()` (snapshot 2) → `diff_memory()` |
| "Sig + validate" | `generate_signature(addr, 16)` → save → `python3 tools/sig-uniqueness-checker.py game.exe --sig "..."` → if margin < 2, regenerate longer |
| "Per-binary diff after patch" | `read_file(old_offsets_json)` → `python3 tools/offset-diff.py --old V1 --new V2 --sigs old_offsets_json` → for each LOST: `find_pattern` against V2 with broadened sig → record new sig |

These compose without ceremony — each call's output is the next call's input. The AI should *reach for the composition* rather than asking "should I call N more tools?" — the workflow is the unit, not the individual call.

**Why:** Naming the compositions makes them habits. Without a name, every new user re-derives the workflow from scratch and asks each tool call as a separate question. Named compositions become muscle memory after a handful of uses.

---

## Summary — Goal → Tool Map

| Goal | Right tool | Wrong tool (common mistake) |
|---|---|---|
| Read one int/float at address | `read_typed_value` | `read_memory` + manual unpack |
| Read whole struct | `struct_dump` | N × `read_typed_value` |
| Follow pointer chain | `read_pointer_chain` | N × `read_typed_value` |
| Find string in memory | `scan_string` / `scan_wstring` | `find_pattern` |
| Find numeric value | `scan_value` | `find_pattern` |
| Find pointer to X | `scan_pointer_to` | `find_pattern` |
| Find code pattern | `find_pattern` | `search_text` (search_text is for files, not memory) |
| Find xrefs to function | `find_xrefs` | `disassemble` + manual scan |
| Find xrefs to string | `find_string_refs` | `find_pattern` on the string bytes |
| See some asm | `disassemble` | `analyze_function` |
| Get function start/end | `find_function_bounds` | `disassemble` + walk |
| Get class name | `read_rtti` | `analyze_vtable` (use both — RTTI first) |
| Get vtable layout | `analyze_vtable` | `read_memory` + manual deref |
| Generate a sig | `generate_signature` + `tools/sig-uniqueness-checker.py` | hand-crafting bytes |
| Find diff after action | `scan_changed` + `diff_memory` | `find_pattern` on guesses |

**Cross-references:** `mcp/perception-mcp-config.json` (authoritative tool list), `mcp/claude-code-setup.md` / `mcp/cursor-setup.md` / `mcp/aider-setup.md` (per-IDE wiring), `tools/sig-uniqueness-checker.py` / `tools/offset-diff.py` / `tools/dumper-to-enma.py` / `tools/module-export-mapper.py` (local CLI tools that pair with MCP calls), `skill://pcx-perf-budget` (call-cost discipline that applies to MCP calls), `skill://re-evidence-log` (E-NNN cross-references record which MCP calls produced each offset).
