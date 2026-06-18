# PCX Cross-Language Bridge — Enma vs AngelScript vs Lua

Perception.cx supports three scripting languages: Enma (the native one), AngelScript, and Lua. Each has a different API surface, different performance characteristics, and different ergonomic strengths. The AI keeps defaulting to whichever language the user opened the editor in — missing the cases where another language is materially better for the feature. This file is the comparison and decision guide, plus the patterns for cross-language coordination when one project genuinely needs multiple.

> **Read this before** starting a new feature, picking a language for a new project, or wondering whether a slow / awkward feature would be better in a different language.

---

## At-a-Glance Comparison

| Property | Enma | AngelScript | Lua |
|---|---|---|---|
| **Language family** | C++-like with extensions (FFI, coroutines, annotations) | C++-like, AngelScript registration model | Dynamic, table-centric |
| **Typing** | Static, optionally inferred | Static | Dynamic, with optional type hints in 5.4 |
| **Memory model** | Manual + RAII (deterministic destructors, no GC) | Refcounted handles for objects; value types for math primitives | Garbage-collected |
| **Performance tier** | Fastest (JIT / bytecode, no GC) | Fast (interpreted with type-erased dispatch) | Slower (interpreted, GC pauses possible) |
| **Startup cost** | Low (precompiled `.emb` deserializes fast) | Medium (compile from source on load) | Low (LuaJIT-class speed if exposed; otherwise interpreted) |
| **Hot-reload semantics** | Yes (script code replaced; globals + types persist host-side) | Yes (callbacks released on unload; `proc_t` must `deref()`) | Yes (globals reset; package cache may persist) |
| **Concurrency / threading** | First-class via `addon-thread` (mutex, condvar) and atomics | Mutex / Atomic types per registered addon | Coroutines (idiomatic Lua); no native threads |
| **FFI / native function registration** | Direct via SDK; many built-ins | Via the AngelScript registration model (host-side `RegisterObjectMethod`, etc.) | Via Lua C API (host-side `lua_register`) |
| **Error handling** | Exceptions (`try`/`catch`); rich error types | Exceptions; AS-specific exception types | `pcall` / `xpcall` returning ok-flag + value |
| **Compile-time checking** | Strong (type-checks on compile) | Strong (type-checks on compile) | Weak (most errors are runtime) |
| **Has `vec2`/`vec3`/`vec4`/`quat`/`mat4`** | Yes (math addon) | Yes (vector / matrix types per the engine-specific-api docs) | Yes via the extended-math API (`vector3`, `quaternion`, `matrix4x4`, `mat4` namespace) |
| **Has SIMD intrinsics** | Yes (`addon-simd`: `f32x4`, `i32x4`) | Not as a first-class addon at last check | Not as a first-class addon at last check |
| **Has atomic types** | Yes (`addon-atomic`: `aint32`, `aint64`) | Yes (per AS docs) | No |
| **JSON support** | Yes (`addon-json`) | Yes (per AS docs) | Yes (via `package` addon) |
| **Regex support** | Yes (`addon-regex`) | Available per AS surface | Standard Lua `string.match` patterns |
| **Coroutines** | Yes (per `lang-advanced.md`) | Variable per build — check `docs/perception/angelscript/overview.md` | Native and idiomatic |
| **AS Intrinsics namespace** | n/a | Yes — PCX-specific AS extension (per the README's AngelScript section) | n/a |
| **Debugger tooling at dev time** | Strong (LSP via `lsp/enma-lsp`, full SDK debug hooks) | Strong (LSP via `lsp/angel-lsp-pcx`) | Variable per host integration |

The single most important row is **performance tier**. For hot-path code (render routines at 144 Hz, entity loops over 256 entities, per-frame math), Enma is materially faster than AngelScript, which is materially faster than Lua. The differences below render-rate are usually negligible; at render-rate, they're felt.

Verify each row against the per-language docs for your PCX version — `docs/enma/`, `docs/perception/angelscript/`, `docs/perception/lua/`. The table is a guide; the docs are authoritative.

---

## Per-Use-Case Routing

The decision-tree, ordered by frequency:

### High-frequency render-path code → **Enma**

Render routines running at 144-240 Hz are budget-tight (see `skill://pcx-perf-budget`). Static typing avoids per-call dispatch overhead; no GC eliminates pause variance; the precompiled `.emb` format means no compile cost at script load. For ESP, radar, HUD, anything called from `on_render`: Enma is the default.

### Complex stateful UI logic with rich object lifecycle → **AngelScript**

Features with many in-flight objects with non-trivial lifetimes (target tracker that maintains per-entity state across frames, queue-of-attempts state machine, menu system with nested panels) lean on AngelScript's refcounted handles. The `Type@` syntax + automatic `deref()` (when scoped correctly) handles ownership without manual bookkeeping. See `skill://pcx-angelscript-discipline` rules 2-3 for the discipline.

### Quick prototyping / config DSL / one-off scripts → **Lua**

Dynamic typing is the fastest iteration loop. A table-based config file ("here are my hotkey assignments, my color preferences, my distance thresholds") in Lua is one screen; in Enma it's three. For exploratory work where the shape of the data isn't known yet, Lua's tables-as-everything pattern wins.

### CPU-bound math (matrix transforms, pathfinding, simulation) → **Enma**

The `addon-math3d` (`quat`, `mat4`) and `addon-simd` (`f32x4`, `i32x4`) addons give Enma the native math primitives modern game-math work needs. AngelScript has matrix types but no SIMD addon. Lua's math library is general-purpose, not game-shaped. For pathfinding / physics-y simulation / matrix-heavy work: Enma.

### Network protocol handling / file I/O → **any (use the project's primary language)**

`addon-net` (Enma) and equivalents in AS / Lua all cover sockets, HTTP, websockets. File I/O similarly (`addon-file`, `fs_*` in Lua, AS file APIs). Pick based on what the rest of the script uses; the per-call cost of network I/O dwarfs the per-call cost of the language dispatch overhead.

### Cross-binary compatibility shims → **Enma**

The `.emb` precompiled format (per `docs/enma/sdk-serialization-and-linking.md`) is portable across compatible runtime versions and ships without the script source. AngelScript scripts ship as source by default; Lua scripts ship as source or LuaJIT bytecode. For a library you'll distribute to other users running varying PCX versions, Enma's `.emb` is the most portable artifact.

### Coroutine-heavy state machines → **Enma or Lua**

Enma's coroutines are first-class (per `docs/enma/lang-advanced.md`); Lua's are idiomatic and well-documented. AngelScript's support varies per build. For a stateful "send command → await response → handle result → loop" pattern: pick by what your rest-of-the-project uses.

---

## Cross-Language Coordination

When one feature genuinely spans languages (a render-rate ESP in Enma that consumes data from a config file maintained in Lua, or an AngelScript menu wrapping an Enma compute kernel), three patterns:

### 1. Shared state via files

```
language A writes  ───>  config.json on disk  ───>  language B reads
```

- Cheap; asynchronous; no language-level coupling
- Latency = filesystem-write + filesystem-read; fine for config, slow for per-frame data
- Robust against crashes (file persists)
- Use for: config, persisted state, occasional cross-script communication

### 2. Shared state via the host process

If PCX exposes a host-side state bridge (check `docs/perception/` for cross-language data sharing — the surface is host-specific), one script can write a global the host exposes; another reads it.

- Latency low (in-process)
- Coupling: high (both scripts must agree on the global's shape)
- Use only when the latency of pattern #1 is genuinely too high (per-frame coordination)

### 3. Don't

In most cases, picking one language per feature is cheaper than coordinating across two. If you find yourself reaching for cross-language plumbing, ask: would rewriting the smaller side in the larger side's language eliminate the bridge? Usually yes. Usually it's cheaper.

The rule of thumb: cross-language coordination is for cases where the languages have genuinely different strengths the feature needs. Lua for a config DSL + Enma for the render-rate consumer is a fair split. Two features in two languages "because we have a multi-language codebase" usually means you've imported maintenance overhead for no gain.

---

## Performance Notes

Measured-style guidance (the actual numbers vary per binary, build, and platform — verify on your target):

### Equivalent across languages

These dominate the cost of any non-trivial script regardless of language choice:

- Cross-process memory reads (`ru64`, `read_memory`, etc.) — kernel transition cost dominates, language overhead invisible
- Render API calls (`draw_*`) — GPU command submission dominates
- File I/O — disk latency dominates
- Network calls — network latency dominates

If your script is dominated by these, the language choice barely matters.

### Materially different across languages

These are where the choice shows up:

- **Per-script-call native function overhead** — Enma's dispatch is the tightest; AS adds a type-check pass; Lua's varies by integration. In a tight loop of 1000 native calls per frame, the difference can be 100s of µs.
- **Garbage collection pauses** — Lua has GC; pauses are usually sub-ms but can spike. Enma has none. AS uses refcounting (deterministic, no pauses, but cycles need manual handling).
- **Hot-path arithmetic** — Enma + the SIMD addon outperforms AS + scalar math, which outperforms Lua's general-purpose number type.
- **Allocation overhead** — Lua's table allocations on the hot path show up; Enma's stack-allocated value types don't allocate; AS's refcounted handles allocate but predictably.

The implication: a render-rate routine in Lua + a render-rate routine in Enma differ by 10-50% in CPU time *not* counting the cross-process reads. With cross-process reads dominating, the user-visible difference is smaller, but on a tight script the choice matters.

---

## Migration Notes

When you start a feature in one language and realize another would be better:

### Enma ↔ AngelScript

- Type names mostly align (`uint64`, `float`, `string`, etc.).
- The proc API surface is parallel but the spellings differ — see `skill://pcx-angelscript-discipline` rule 1 for the mapping table (e.g. Enma's `register_routine(cast<int64>(on_render), 0)` becomes AS's `register_callback(on_tick, 16, 0)` with a different callback signature).
- Handle vs value: AS uses `Type@` for refs; Enma uses references / pointers. Conversion is mechanical but per-variable.
- Render APIs differ in shape: Enma takes `color` / `vec2` structs; AS takes raw RGBA ints and separate x/y floats. See `skill://pcx-angelscript-discipline` rule 8.

### Enma ↔ Lua

- Bigger jump. Lua's dynamic typing means every Enma type annotation gets discarded; in return, every Enma type-check happens at runtime.
- Numbers are subtle: Lua 5.4 has a 64-bit integer subtype, so addresses survive; pre-5.4 Lua loses precision past 2^53. See `skill://pcx-lua-discipline` rule 1.
- Lifecycle: Enma's `on_update` / `on_render` map to Lua's `register_routine` (or equivalent — check `docs/perception/lua/life-cycle.md`).
- Tables replace structs; field access syntax is `.` either way; iteration syntax differs.

### AngelScript ↔ Lua

- Largest jump. AS is C++-with-handles; Lua is dynamic + tables. Plan to rewrite, not translate.
- Reuse the architecture (what feature does what, how data flows), not the code.

For all three: the underlying *engine* knowledge (sigs, offsets, struct layouts) is language-agnostic. Port the language-specific parts; keep the offset table.

---

## Recommended Default by Project Size

| Project size | Recommendation |
|---|---|
| 1-3 file script | Pick whichever you know best; the differences don't matter at this scale. |
| 5-15 file project | **Enma is the default** unless a specific feature wants AS or Lua per the routing above. |
| 20+ file production project | **Enma** with selective AS / Lua per feature; **consistency** in the bulk of the codebase matters more than the marginal per-language wins. |
| Library you'll distribute | **Enma** — `.emb` is the most portable artifact. |
| Quick personal experiment | **Lua** — fastest iteration. |
| Performance-critical feature pulled out of a larger project | **Enma** — even if the project is in another language. |

The recommendation against mixing languages in mid-size projects isn't arbitrary: every cross-language boundary is a coupling point, a maintenance overhead, and a context switch for the next maintainer. Use the boundary when the benefit is concrete; default to one language when it's not.

---

## Cross-References

- `docs/enma/` — Enma language + SDK (50 files; start at `enma/readme.md`)
- `docs/perception/angelscript/` — AngelScript APIs (23 files; start at `overview.md`)
- `docs/perception/lua/` — Lua APIs (17 files; start at `overview.md`)
- `skill://pcx-angelscript-discipline` — 10 AS-specific rules (handles, `&out`, `array<T>`, `register_callback` shape)
- `skill://pcx-lua-discipline` — 10 Lua-specific rules (int subtype for addresses, `pcall`, hot-reload boundaries)
- `skill://pcx-perf-budget` — the perf budgets the language choice affects
- `skill://script-bundler` — `.emb` packaging that makes Enma especially portable
- `knowledge/script-organization-patterns.md` — multi-file organization patterns (largely language-agnostic, with notes per language)
- `knowledge/pcx-api-cheatsheet.md` — cross-API surface at a glance
