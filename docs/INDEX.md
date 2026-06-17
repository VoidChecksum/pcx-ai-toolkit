# Documentation Index

## Enma Language

### Single-Page References (start here)

| File | Lines | Description |
|------|-------|-------------|
| [`enma/llms-language.md`](enma/llms-language.md) | 2,861 | **Complete language reference** — every feature, every addon, one file |
| [`enma/llms-sdk.md`](enma/llms-sdk.md) | 832 | **Complete SDK reference** — embedding, type registration, native functions |

### Language Guide (detailed breakdown)

| File | Lines | Topic |
|------|-------|-------|
| [`enma/lang-basics.md`](enma/lang-basics.md) | 267 | Types, variables, constants, operators, control flow |
| [`enma/lang-functions.md`](enma/lang-functions.md) | 247 | Parameters, defaults, references, out params, variadic, lambdas, closures |
| [`enma/lang-pointers.md`](enma/lang-pointers.md) | 357 | Heap pointers, address-of, member access, references, null |
| [`enma/lang-structs-and-classes.md`](enma/lang-structs-and-classes.md) | 912 | Value types, reference types, inheritance, virtual dispatch, interfaces, mixins, operator overloading |
| [`enma/lang-templates.md`](enma/lang-templates.md) | 173 | Generic structs and functions, monomorphization |
| [`enma/lang-advanced.md`](enma/lang-advanced.md) | 562 | Delegates, namespaces, coroutines, exceptions, heap allocation, smart pointers, FFI, nullable |
| [`enma/lang-annotations.md`](enma/lang-annotations.md) | 209 | packed, align, reflect, serialize, export, noopt, noinline, inline, dll, custom |
| [`enma/lang-modules.md`](enma/lang-modules.md) | 100 | Import system, aliased imports, precompiled .emb, multi-module linking |
| [`enma/lang-pre-processor.md`](enma/lang-pre-processor.md) | 77 | #define, #undef, #ifdef, #ifndef, #elif, #else, #endif, #include, #pragma |
| [`enma/lang-semantics-and-limits.md`](enma/lang-semantics-and-limits.md) | 181 | Guarantees, compile-time rejects, what doesn't exist |

### Standard Library Addons

| File | Lines | Types/Functions |
|------|-------|-----------------|
| [`enma/addon-core.md`](enma/addon-core.md) | 42 | `print`, `println` |
| [`enma/addon-strings.md`](enma/addon-strings.md) | 165 | `format`, `to_int`, `split`, `replace`, `substr`, interpolation |
| [`enma/addon-arrays.md`](enma/addon-arrays.md) | 119 | `T[]`, `push`, `pop`, `sort`, `contains`, `slice`, `for-each` |
| [`enma/addon-maps.md`](enma/addon-maps.md) | 200 | `map<K,V>`, `imap<V>`, `get`, `set`, `contains`, iteration |
| [`enma/addon-math.md`](enma/addon-math.md) | 137 | `sin`, `cos`, `atan2`, `sqrt`, `clamp`, `lerp`, `random`, constants |
| [`enma/addon-simd.md`](enma/addon-simd.md) | 128 | SSE2: `f32x4`, `i32x4` vector arithmetic |
| [`enma/addon-vec.md`](enma/addon-vec.md) | 135 | `vec2`, `vec3`, `vec4` math types |
| [`enma/addon-math3d.md`](enma/addon-math3d.md) | 182 | `quat`, `mat4` rotation and transform |
| [`enma/addon-variant.md`](enma/addon-variant.md) | 130 | Type-erased value container |
| [`enma/addon-atomic.md`](enma/addon-atomic.md) | 94 | `aint32`, `aint64` atomic operations |
| [`enma/addon-bits.md`](enma/addon-bits.md) | 117 | `popcount`, `clz`, `ctz`, `bswap`, `rotl`, `rotr`, `parity` |
| [`enma/addon-time.md`](enma/addon-time.md) | 95 | `time_ms`, `time_us`, ISO 8601, `sleep` |
| [`enma/addon-regex.md`](enma/addon-regex.md) | 61 | `match`, `find`, `replace`, `split`, capture groups |
| [`enma/addon-file.md`](enma/addon-file.md) | 125 | Sandboxed file I/O (permission-gated) |
| [`enma/addon-thread.md`](enma/addon-thread.md) | 120 | `mutex`, `lock_guard`, `condition_variable` |
| [`enma/addon-hash_set.md`](enma/addon-hash_set.md) | 89 | `hash_set<T>` unordered set |
| [`enma/addon-sorted_map.md`](enma/addon-sorted_map.md) | 89 | `sorted_map<K,V>` ordered key-value |
| [`enma/addon-list.md`](enma/addon-list.md) | 192 | Double-ended O(1) push/pop container |
| [`enma/addon-json.md`](enma/addon-json.md) | 108 | `json_parse`, `json_stringify`, `json_value` |

### SDK Guide (C++ embedding)

| File | Lines | Topic |
|------|-------|-------|
| [`enma/sdk-quick-start.md`](enma/sdk-quick-start.md) | 126 | Minimal embedding example |
| [`enma/sdk-engine-lifecycle.md`](enma/sdk-engine-lifecycle.md) | 166 | Create, configure, destroy |
| [`enma/sdk-compilation.md`](enma/sdk-compilation.md) | 65 | Compile from source strings/files |
| [`enma/sdk-execution.md`](enma/sdk-execution.md) | 103 | Create contexts, execute, read returns |
| [`enma/sdk-calling-functions.md`](enma/sdk-calling-functions.md) | 82 | Pass arguments from host |
| [`enma/sdk-globals.md`](enma/sdk-globals.md) | 79 | Read/write script globals |
| [`enma/sdk-type-registration.md`](enma/sdk-type-registration.md) | 862 | Expose native types via type_builder |
| [`enma/sdk-native-functions.md`](enma/sdk-native-functions.md) | 446 | Register host functions |
| [`enma/sdk-hot-reload.md`](enma/sdk-hot-reload.md) | 64 | Replace script code at runtime |
| [`enma/sdk-serialization-and-linking.md`](enma/sdk-serialization-and-linking.md) | 97 | .emb binaries, multi-module linking |
| [`enma/sdk-introspection.md`](enma/sdk-introspection.md) | 317 | List functions, query annotations, dump IR |
| [`enma/sdk-lifecycle.md`](enma/sdk-lifecycle.md) | 227 | Deterministic RAII, stack-first structs, no GC |
| [`enma/sdk-debug-and-gc.md`](enma/sdk-debug-and-gc.md) | 202 | Debug hooks, budgets, heap stats, stack traces |
| [`enma/sdk-error-handling.md`](enma/sdk-error-handling.md) | 116 | Compile-time and runtime errors |
| [`enma/sdk-safety.md`](enma/sdk-safety.md) | 121 | Fault trapping, sandboxing, permissions, threads |
| [`enma/sdk-custom-addons.md`](enma/sdk-custom-addons.md) | 576 | Build your own addon |
| [`enma/sdk-api-reference.md`](enma/sdk-api-reference.md) | 411 | Complete function listing |

## Perception.cx Platform APIs — Enma

| File | Lines | API |
|------|-------|-----|
| [`perception/proc-api.md`](perception/proc-api.md) | 294 | Process handle, memory read/write, modules, pattern scan, VAD, typed reads |
| [`perception/render-api.md`](perception/render-api.md) | 264 | 2D drawing, fonts, shaders, vertex/index/constant buffers, compute |
| [`perception/gui-api.md`](perception/gui-api.md) | 455 | Sidebar sections, all widget types |
| [`perception/input-api.md`](perception/input-api.md) | 126 | Mouse + keyboard state polling |
| [`perception/cpu-api.md`](perception/cpu-api.md) | 92 | CPU ID, timing, datetime, bitcasts |
| [`perception/zydis-api.md`](perception/zydis-api.md) | 133 | x86-64 assembler/disassembler |
| [`perception/unicorn-api.md`](perception/unicorn-api.md) | 151 | x86-64 CPU emulation |
| [`perception/net-api.md`](perception/net-api.md) | 200 | HTTP, WebSocket, raw UDP |
| [`perception/win-api.md`](perception/win-api.md) | 120 | Window enum, clipboard, key/mouse send |
| [`perception/filesystem-api.md`](perception/filesystem-api.md) | 162 | Sandboxed file I/O |
| [`perception/sound-api.md`](perception/sound-api.md) | 90 | WAV/OGG playback |
| [`perception/lifecycle-and-routines.md`](perception/lifecycle-and-routines.md) | 134 | main(), routines, unload, exceptions |
| [`perception/mcp-api.md`](perception/mcp-api.md) | 268 | AI agent JSON-RPC surface |
| [`perception/ide.md`](perception/ide.md) | 585 | Perception IDE: editor, AI chat, tools, extensions |
| [`perception/extensions-api.md`](perception/extensions-api.md) | 371 | Extension development API |
| [`perception/analyzer.md`](perception/analyzer.md) | 370 | Perception Analyzer |
| [`perception/custom-draw-api.md`](perception/custom-draw-api.md) | ~500 | D3D11 GPU pipeline: shaders, buffers, textures, compute, depth testing |
| [`perception/changelogs.md`](perception/changelogs.md) | ~500 | Complete changelog archive (Feb–June 2026) |

## Perception.cx Platform APIs — AngelScript

24 files, 11,000+ lines total. Located in [`perception/angelscript/`](perception/angelscript/).

Covers: Overview, Life Cycle, Engine, Atomic Types, Proc API, Render API, **Custom Draw API**, GUI API, Input API, System/CPU/Disassembly, Net API, File System, Extended Math, Win API, JSON API, Unicorn, Zydis Encoder, Intrinsics, Mutex, Utilities, Sound, Bit Reinterpret, Engine Specific, CS2 Extended.

## Perception.cx Platform APIs — Lua

17 files, 5,779 lines total. Located in [`perception/lua/`](perception/lua/).

Covers: Overview, Life Cycle, Engine, Proc API, Render API, GUI API, Input API, System/CPU/Disassembly, Net API, File System, Extended Math, Win API, JSON API, Utilities, Sound, Engine Specific, CS2 Extended.

## Knowledge Base

| File | Description |
|------|-------------|
| [`../knowledge/enma-cheatsheet.md`](../knowledge/enma-cheatsheet.md) | Enma language quick reference |
| [`../knowledge/pcx-api-cheatsheet.md`](../knowledge/pcx-api-cheatsheet.md) | Perception API quick reference (updated with 2026 additions) |
| [`../knowledge/common-patterns.md`](../knowledge/common-patterns.md) | 13 working code patterns |
| [`../knowledge/custom-draw-patterns.md`](../knowledge/custom-draw-patterns.md) | 8 Custom Draw API GPU rendering patterns |
| [`../knowledge/offset-methodology.md`](../knowledge/offset-methodology.md) | Signature construction and pointer chain walking |
| [`../knowledge/community-tools.md`](../knowledge/community-tools.md) | Community MCP servers, VS Code extensions, and utilities |
| [`../knowledge/game-targets.md`](../knowledge/game-targets.md) | Complete game support reference (25+ games) |

## Signatures & Reversal Guides

| File | Description |
|------|-------------|
| [`../signatures/source-engine/common-sigs.md`](../signatures/source-engine/common-sigs.md) | Source Engine example patterns (entity list, local player, view matrix) |
| [`../signatures/unreal-engine/ue-reversal-guide.md`](../signatures/unreal-engine/ue-reversal-guide.md) | Unreal Engine reversal (GWorld/GObjects/GNames, Dumper-7, key structures) |
