# RE Plugins & Tools Reference

IDA Pro plugins, Ghidra extensions, FLIRT signature databases, binary diffing tools, and debugger sync infrastructure for game binary reverse engineering. Every tool listed here is cloned, ready to build or install.

> This is the **plugin and tool** reference — what to install and how to use it. For kernel-specific tools (WinDbg, HyperDbg, Volatility), see `knowledge/kernel-re-tools.md`. For anti-cheat methodology, see `skill://anti-cheat-re`.

---

## IDA Pro Plugins

### hrtng — Deobfuscation & Decryption

**What:** 2024 Hex-Rays Plugin Contest winner from Kaspersky. Automated string decryption, control flow unflattening, vtable resolution for complex inheritance, and data structure recovery. The single most impactful IDA plugin for obfuscated binaries.

**Use for:** Anti-cheat driver deobfuscation, encrypted string recovery, flattened control flow restoration, complex C++ vtable resolution.

**Install:** Build from source (needs IDA SDK ≥ 7.3 + Hex-Rays decompiler). Copy the compiled `.so`/`.dll` to IDA's `plugins/` directory.

**Source:** [github.com/AandersonL/hrtng](https://github.com/AandersonL/hrtng) (Kaspersky fork)

---

### HexRaysCodeXplorer — C++ Virtual Call Analysis

**What:** Hex-Rays decompiler plugin for C++ reverse engineering. Auto-reconstructs types from vtable references, navigates virtual function calls, provides an Object Explorer window for browsing all vtables.

**Use for:** Any C++ game binary with RTTI — reconstructs class hierarchies, resolves virtual calls that IDA shows as indirect `call [rax+offset]`. Essential for Source Engine, Unreal Engine, Unity IL2CPP binaries.

**Key features:**
- Right-click in pseudocode → "Reconstruct Type" → generates C struct from vtable references
- Object Explorer → browse all vtables with class names
- Virtual call resolution → resolves `(**(code **)(*obj + 0x40))(obj)` to `CBaseEntity::Think()`

**Install:** Copy compiled plugin to IDA's `plugins/` directory.

**Source:** [github.com/REhints/HexRaysCodeXplorer](https://github.com/REhints/HexRaysCodeXplorer)

---

### ClassInformer — MSVC RTTI Scanner

**What:** Scans the binary for MSVC RTTI (Run-Time Type Information) structures — `vftable`, `type_info`, `_RTTICompleteObjectLocator`, `_RTTIClassHierarchyDescriptor`. Builds a browsable list of all C++ classes with vtables.

**Use for:** Any MSVC-compiled binary with RTTI not stripped (most game binaries, including Apex Legends, CS2, COD). First step after loading — gives you every class name the compiler embedded.

**Usage:** Edit → Plugins → Class Informer → scan. Results appear in an IDA window — sortable by name, vtable address, hierarchy depth.

**Source:** [github.com/nihilus/IDA_ClassInformer_PlugIn](https://github.com/nihilus/IDA_ClassInformer_PlugIn)

---

### SigMakerEx — Pattern Signature Generator

**What:** Generates IDA-style byte-pattern signatures from selected code. Supports multiple output formats: IDA, x64dbg, `find_code_pattern` PCX format, raw hex.

**Use for:** Generating sigs for `offsets.em` — select a unique instruction sequence, right-click → SigMaker → generate. Automatically wildcards relocatable bytes.

**Usage:** Right-click on code → SigMaker → "Create IDA Sig" or "Create Code Sig". Options: auto-wildcard, minimum uniqueness check, copy to clipboard.

**Key feature:** The "auto-wildcard" mode detects and masks RIP-relative displacements, absolute addresses, and other patch-volatile bytes — exactly what `game-cheat-guidelines` #5 (sigs over hardcodes) requires.

**Source:** [github.com/A200K/IDA-Pro-SigMaker](https://github.com/A200K/IDA-Pro-SigMaker)

---

### FIRST — Community Function Fingerprints

**What:** Cisco Talos Function Identification and Recovery Signature Tool. Free alternative to IDA's Lumina service. Matches unknown functions against a community database of identified functions using metadata hashing (not just bytes).

**Use for:** Auto-naming standard library functions, crypto routines, and common utility functions that FLIRT signatures miss. Particularly useful for statically-linked libraries where FLIRT sigs may not cover the exact version.

**Usage:** Edit → Plugins → FIRST → "Check All Functions". Functions with matches are renamed automatically. Review in FIRST's panel.

**Install:** Copy `first_plugin_ida/` content to `~/.idapro/plugins/`. Requires FIRST server access (public instance available).

**Source:** [github.com/ciscocsirt/FIRST-plugin-ida](https://github.com/ciscocsirt/FIRST-plugin-ida)

---

### RevEng.AI — Binary Similarity

**What:** AI-powered binary similarity analysis. Identifies library code, matches functions across builds/platforms, suggests function names based on training corpus. Cloud-based analysis.

**Use for:** Cross-version offset matching — when a game patches and functions move, RevEng.AI can match the old function to its new location by structural similarity rather than bytes.

**Source:** [github.com/RevEngAI/reai-ida](https://github.com/RevEngAI/reai-ida)

---

## Ghidra Plugins

### GhidrAssist — LLM-Powered RE Assistant

**What:** Integrates Claude, GPT, or local Ollama models directly into Ghidra. Explains decompiled functions, suggests names, bulk-renames symbols, answers questions about the code in context.

**Use for:** Rapid function triage on massive binaries — ask the LLM "what does this function do?" with the decompiled output as context. Bulk rename 1000+ functions in a session.

**Source:** [github.com/jtang613/GhidrAssist](https://github.com/jtang613/GhidrAssist)

---

### BinDiffHelper — Cross-Version Comparison

**What:** Integrates Google BinDiff into Ghidra's workflow. Export BinExport2 from Ghidra, diff two versions, import matched function names back.

**Use for:** Post-patch offset recovery — diff the pre-patch and post-patch binaries, identify which functions moved, import the matches to propagate names.

**Source:** [github.com/ubfx/BinDiffHelper](https://github.com/ubfx/BinDiffHelper)

---

### OOAnalyzer (Pharos) — Automated C++ Recovery

**What:** Carnegie Mellon SEI's OOAnalyzer framework for Ghidra. Automated C++ class, method, and vtable recovery using Prolog-based reasoning over the binary.

**Use for:** Large game binaries with complex C++ hierarchies where manual vtable reconstruction would take weeks. Runs as a Ghidra script and produces class definitions.

**Source:** [github.com/cmu-sei/pharos](https://github.com/cmu-sei/pharos)

---

### RevEng.AI for Ghidra

Same as the IDA plugin — AI binary similarity, function matching, and naming. Ghidra-native interface.

**Source:** [github.com/RevEngAI/reai-ghidra](https://github.com/RevEngAI/reai-ghidra)

---

## FLIRT Signature Databases

FLIRT (Fast Library Identification and Recognition Technology) signatures let IDA auto-name standard library functions. Critical for MSVC-compiled game binaries — without them, `memcpy`, `malloc`, `std::string::assign`, and thousands of CRT/STL functions appear as `sub_XXXXX`.

### Pre-Selected Signatures (51 sigs)

Priority order for game binaries compiled with MSVC v15 (Visual Studio 2017/2019):

| Signature File | What It Names | Priority |
|---|---|---|
| `libvcruntime_15_msvc_x64.sig` | CRT basics (SEH, stack guards, type info) | 1 |
| `libcmt_15_msvc_x64.sig` | C runtime (memcpy, malloc, printf, etc.) | 2 |
| `libcpmt_15_msvc_64.sig` | C++ runtime (std::string, std::vector, std::map) | 3 |
| `libcryptoMT_15_msvc_x64.sig` | OpenSSL crypto (AES, SHA, RSA) | 4 |
| `libsslMT_15_msvc_x64.sig` | OpenSSL SSL/TLS | 5 |
| `libcurl-vc-x64-*.sig` | libcurl HTTP client | 6 |
| `libboost_*.sig` | Boost (filesystem, thread, regex, etc.) | 7 |

**Apply in IDA:** `Shift+F5` → Apply new signature → select file. Apply in priority order — lower-priority sigs fill in what higher-priority ones missed.

### Signature Databases

| Database | Sigs | Coverage |
|---|---|---|
| **FLIRTDB** | 4000+ | Community collection covering MSVC, GCC, Clang, MinGW across many versions |
| **sig-database** | 2000+ | Additional collection with emphasis on game middleware (Steam API, EAC SDK, etc.) |

---

## Binary Diffing Tools

### Diaphora — IDA-Native Binary Diffing

**What:** Python-based binary diffing that runs inside IDA. Exports IDB analysis to SQLite, then diffs two exports. More accurate than BinDiff for heavily optimized/obfuscated code because it uses IDA's deeper analysis data.

**Use for:** Post-patch analysis — diff the pre-patch and post-patch game binary to find exactly what changed. Prioritize reviewing new/changed functions for updated offsets.

**Usage:**
```
# In IDA with pre-patch binary:
File → Script file → diaphora/diaphora.py → Export to SQLite

# In IDA with post-patch binary:
File → Script file → diaphora/diaphora.py → Export to SQLite

# Then: Diff the two SQLite exports
File → Script file → diaphora/diaphora.py → Diff
```

**Source:** [github.com/joxeankoret/diaphora](https://github.com/joxeankoret/diaphora)

---

### BinDiff — Structural CFG Comparison

**What:** Google's binary diffing tool. Compares control flow graphs structurally — insensitive to register allocation and instruction scheduling changes. Industry standard for cross-version binary matching.

**Use for:** Matching functions across game patches when Diaphora's byte-level diff is too noisy. BinDiff's CFG matching survives compiler flag changes and link-time optimization shuffles.

**Usage:**
```bash
# Export from IDA: File → Produce file → Create BinExport2 file
# Or from Ghidra: via BinDiffHelper extension
bindiff old_version.BinExport new_version.BinExport
# Opens BinDiff GUI with matched/unmatched function pairs
```

**Source:** [github.com/google/bindiff](https://github.com/google/bindiff)

---

## Debugger Sync — ret-sync

**What:** Real-time synchronization between a debugger and IDA/Ghidra/Binary Ninja. When you step in the debugger, the disassembler view jumps to the same address. When you set a breakpoint in IDA, it's set in the debugger.

**Supported debuggers:** WinDbg, x64dbg, GDB, LLDB, OllyDbg 1/2
**Supported disassemblers:** IDA, Ghidra, Binary Ninja

**Use for:** Live game analysis — attach x64dbg or WinDbg to the game process while IDA shows the decompiled view. Step through a function in the debugger and see the pseudocode update in real time.

**Install:**
- IDA: Copy `ext_ida/` to IDA plugins directory
- Ghidra: Install `ext_ghidra/` as a Ghidra extension
- x64dbg: Copy `ext_x64dbg/` DLL to x64dbg plugins directory
- WinDbg: Load `ext_windbg/` extension

**Source:** [github.com/bootleg/ret-sync](https://github.com/bootleg/ret-sync)

---

## SDK / Type Libraries

### r5sdk — Reversed Apex Legends SDK

**2,438 header files** reversed by the community (primarily Mauler125). Covers the entire Source Engine (Respawn fork) class hierarchy.

| Directory | Headers | Coverage |
|---|---|---|
| `game/server/` | 79 | Player, entity, AI, weapons, physics |
| `game/client/` | 35 | Client entities, HUD, viewrender |
| `game/shared/` | 15 | Player vars, weapon data, melee |
| `engine/` | 61 | Client/server engine, networking |
| `public/` | 178 | Interfaces, tier0/1/2, vscript, vgui |
| `rtech/` | 19 | Pak system, playlists, LiveAPI, Stryder |
| `networksystem/` | 6 | Pylon, bans, host manager |
| `thirdparty/` | ~300 | Boost, curl, protobuf, mbedtls, lz4, zstd |

**Import into IDA:** File → Load file → Parse C header file → select the `.h` files you need. Key starting headers: `player.h`, `baseentity.h`, `convar.h`.

**Import into Ghidra:** File → Parse C Source → add the header directories to the include path. Then apply types to decompiled functions.

**Source:** [github.com/AyeZee/r5sdk](https://github.com/AyeZee/r5sdk) (community fork)

---

## Recommended Workflow

### First Load (any game binary)

```
1. Load in IDA → let auto-analysis run
2. Apply FLIRT sigs (Shift+F5) → names CRT/STL/crypto/network functions
3. Run ClassInformer → scan RTTI → browse vtables
4. Run HexRaysCodeXplorer → reconstruct key types from vtables
5. Import SDK headers if available (r5sdk, UE SDK, etc.)
6. Run FIRST → community function fingerprints for remaining unknowns
```

### Post-Patch Update

```
1. Load new binary in IDA → apply same FLIRT sigs
2. Export both IDBs via Diaphora (or BinExport2 for BinDiff)
3. Diff → identify moved/changed functions
4. Import matched names into new IDB
5. Update offset table — re-verify sigs that moved
```

### Live Analysis

```
1. Attach debugger (x64dbg/WinDbg) to game process
2. Start ret-sync in both debugger and IDA/Ghidra
3. Set breakpoints on functions of interest
4. Step through execution → decompiler view follows in real time
5. Inspect register/memory state at each step
```

---

## MCP Integration

These tools complement the Perception MCP server's RE tools:

| Perception MCP Tool | Offline Equivalent | When to Use Which |
|---|---|---|
| `find_pattern` | SigMakerEx (generate) | SigMakerEx to create sigs; `find_pattern` to apply them live |
| `struct_dump` | ClassInformer + CodeXplorer | ClassInformer for RTTI discovery; `struct_dump` for live memory layout verification |
| `disassemble` | IDA/Ghidra decompiler | IDA for deep static analysis; `disassemble` for quick live checks |
| `analyze_vtable` | ClassInformer | ClassInformer for full hierarchy; `analyze_vtable` for live vtable state |
| `read_rtti` | ClassInformer | Same data source, different access — live vs. static |
| `generate_signature` | SigMakerEx | Both generate sigs; SigMakerEx has more options for wildcarding |
| `build_call_graph` | IDA xrefs | IDA xrefs are more complete; `build_call_graph` works on live memory |
