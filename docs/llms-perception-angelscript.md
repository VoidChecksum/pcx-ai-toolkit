# AngelScript Context Pack

> Single-file context pack for AI tools writing current Perception AngelScript `.as` scripts while Enma AOT is unreleased.

> **Generated** by `tools/build-llms-index.py` — do not edit manually. Re-generate by running the tool from the repo root. CI verifies the committed bundle matches the current source.

**Source files included: 12**

---

## Source: `docs/perception/llm-routing.md`

# Perception-First LLM Routing

Use this page before writing any Perception.cx script in this toolkit. The repo
supports **AngelScript (`.as`) and Lua (`.lua`) as current production targets**
and **Enma (`.em`) as the future AOT transition target**. Never mix syntax or
APIs between modes.

## Load Order

For AngelScript work:

1. Read `docs/llms-perception-angelscript.md` or the official AngelScript page
   matching the API surface under `https://docs.perception.cx/perception/angel-script/`.
2. Read `docs/angelscript/quickstart.md` before writing `main()`, callbacks,
   render code, or proc code.
3. Verify every host API and add-on symbol with `pcx api <symbol> --lang
   angelscript` or MCP `api_lookup(symbol, "angelscript")`.
4. Validate final `.as` code with `pcx symbol-check <file.as>`, `pcx verify
   <file.as>`, or MCP `validate_code(code, "angelscript")`.

For Lua work:

1. Read `docs/llms-perception-lua.md` or the official Lua page matching the API
   surface under `https://docs.perception.cx/perception/lua-script/`.
2. Read `docs/lua/quickstart.md` before writing `main()`, callbacks, render
   code, or proc code.
3. Verify every host API and add-on symbol with `pcx api <symbol> --lang lua`
   or MCP `api_lookup(symbol, "lua")`.
4. Validate final `.lua` code with `pcx symbol-check <file.lua>`, `pcx verify
   <file.lua>`, or MCP `validate_code(code, "lua")`.

For Enma migration/AOT work:

1. Read `docs/perception/readme.md` for the registered Enma surface and official
   conventions.
2. Read `docs/perception/lifecycle-and-routines.md` before writing `main()` or
   routines.
3. Read the relevant Enma API page under `docs/perception/*.md` before using any
   host function.
4. Read `knowledge/enma-cheatsheet.md` and
   `.claude/skills/pcx-enma-discipline/SKILL.md` for language gotchas.

## Language Contracts

| Concern | AngelScript `.as` | Lua `.lua` | Enma `.em` |
|---|---|---|---|
| Status | Current production surface | Current production surface | Future AOT transition |
| Entry point | `int main()` | `function main()` | `int64 main()` |
| Repeating work | `register_callback(fn, interval_ms, data_index)` | `register_callback(fn, interval_ms, data_index)` or `on_frame()` | `register_routine(cast<int64>(fn), data)` |
| Callback shape | `void fn(int id, int data_index)` | `function fn(id, data_index)` | `void fn(int64 data)` |
| Logging | `log(...)` | `log(...)` | `println(...)` |
| Process ref | `proc_t` handle; call `deref()` | `process` userdata; call `deref_process(proc)` | `proc_t` value, RAII |
| Arrays | `array<T>` | tables | `T[]`, `.push()`, `.pop()` |
| Maps | `dictionary` | tables | `map<K,V>` / `imap<V>` |
| Render positions | scalar `x, y` arguments unless the AS page says otherwise | scalar `x, y` arguments unless the Lua page says otherwise | `vec2(...)` values |
| Render colors | scalar RGBA arguments unless the AS page says otherwise | scalar RGBA arguments unless the Lua page says otherwise | `color(r,g,b,a)` values |

If generated code mixes AngelScript/Lua lifecycle, containers, or render calls
into Enma, or Enma `vec2`/`color` wrappers into AngelScript/Lua, treat it as wrong.

## Perception Enma Facts From Upstream

The official Perception Enma overview states:

- Enma is Perception's proprietary full-module AOT and JIT-compiled scripting
  language.
- Perception's public Enma docs cover the APIs registered on top of Enma; the
  language itself is documented separately in the upstream Enma docs.
- Colors and positions should be wrapped: `color(255, 255, 255, 255)` and
  `vec2(10.0, 20.0)`.
- Fresh color/vector temporaries each frame are fine because Enma drops them at
  scope exit.
- `float32` literals use the `f` suffix, for example `0.2f`; do not write
  `cast<float32>(0.2)` for a literal.
- `create_*` and `load_*` natives return encrypted `int64` handles. Pass them
  back unchanged into draw, bind, or destroy calls. Do not inspect them.
- The Perception Enma SDK is not public yet.

## Answering Rules For Any LLM

Before producing code:

1. Infer the target language from the user, filename, or explicit `--language`.
   Default to AngelScript for current Perception production scripts; use Lua
   when requested or when the source file is `.lua`; use Enma only when the task
   explicitly asks for Enma or migration prep.
2. Load the matching context pack:
   - AngelScript: `docs/llms-perception-angelscript.md`
   - Lua: `docs/llms-perception-lua.md`
   - Enma: `docs/llms-perception-enma.md`
3. Verify every PCX function name and parameter shape against the matching API
   page, `pcx api <symbol> --lang <language>`, or MCP
   `api_lookup(symbol, "<language>")`.
4. Prefer symbolic offsets and placeholders over version-specific magic values
   unless the user supplied verified offsets.
5. Keep update/scanning work out of render callbacks.
6. Before presenting final code, run `pcx symbol-check <file.as|file.lua|file.em>`
   or MCP `validate_code(code, "<language>")` when available.
7. Before copying a generated Markdown answer into a project, run
   `pcx check-answer <answer.md>` to validate fenced code.

When uncertain, answer with the exact docs that must be checked instead of
inventing a plausible API.

---

## Source: `docs/angelscript/quickstart.md`

# Perception AngelScript Quickstart

Source: https://docs.perception.cx/perception/angel-script/overview.md

AngelScript (`.as`) is the current production scripting surface while Enma AOT is unreleased. Use this mode for UI, rendering, memory analysis, process interaction, and PCX add-ons documented under `https://docs.perception.cx/perception/angel-script/`.

## Lifecycle

Source: https://docs.perception.cx/perception/angel-script/life-cycle.md

```cpp
int main()
```

Return `> 0` to keep the script loaded. Return `<= 0` to unload after `main()` completes. Use `void on_unload()` for cleanup. Do not run infinite loops inside `main()`; register callbacks instead.

```cpp
void on_tick(int id, int data_index)
{
    float w, h;
    get_view(w, h);
    draw_text("Hello", 20, 20, 255,255,255,255, get_font20(), TE_SHADOW, 0,0,0,180, 1.0f);
}

int main()
{
    register_callback(on_tick, 16, 0);
    return 1;
}
```

## Core types and add-ons

AngelScript has `string`, `array<T>`, `dictionary`, `any`, and PCX host add-ons including Render, Input, Proc, Mutex, GUI, System, Net, File System, Extended Math, Engine Specific, Json, Zydis Encoder, Intrinsics, Sound, Bit Reinterpret Helpers, and Unicorn.

## Proc discipline

Source: https://docs.perception.cx/perception/angel-script/proc-api.md

Use `proc_t` handles and `uint64` virtual addresses. Release acquired process handles with `deref()` when done or on unload.

```cpp
proc_t p = ref_process("game.exe");
if (p.pid() == 0)
{
    log("process not found");
    return 0;
}
uint64 base = p.base_address();
p.deref();
```

## Render discipline

Source: https://docs.perception.cx/perception/angel-script/render-api.md

AngelScript Render API uses scalar coordinates and RGBA arguments. Do not use Enma `vec2(...)` or `color(...)` wrappers in `.as` code.

---

## Source: `.claude/skills/game-cheat-guidelines/SKILL.md`

---
name: game-cheat-guidelines
description: >
  Mandatory behavioral rules and practical patterns for writing Perception.cx
  game-cheat scripts in Enma. Always active — these
  rules apply every time you write or edit game-cheat code, including ESP,
  aimbot, triggerbot, radar, pattern scanning, and overlay rendering.
  Authorized use only — analyze software you own or are permitted to test.
license: MIT
---

# Perception.cx Game-Cheat Script Development Guidelines

Behavioral rules and practical patterns for writing game-cheat scripts with Perception.cx in Enma. Derived from the Karpathy principles and rewritten for the domain: ESP, aimbot, triggerbot, radar, pattern scanning, world-to-screen math, memory reads/writes, and overlay rendering. These rules apply to authorized reverse engineering, security research, and game-cheat development — analyze only software you own or are authorized to test.

**Always active.** These rules apply every time you write or edit a game-cheat script. They are not suggestions.

**Prerequisites:** Load the `game-cheat-script-master` skill first. It defines the mandatory co-skills, read-first docs, and the canonical project layout. Then keep `game-hacking-pcx` loaded for the full API doc index. **Read the relevant doc before writing any API call** — see `skill://game-hacking-pcx` for the complete file-by-file index.

**Templates:** Use `templates/cheat-skeleton-em/` as the starting scaffold for every new cheat. See `knowledge/cheat-script-cookbook.md` for reusable recipes (W2S, ESP, aimbot smoothing, triggerbot, radar, config save/load).

## Source-Grounding Gate

Before writing or accepting code, load `docs/perception/llm-routing.md`, verify
host API names with `pcx api <symbol> --lang enma` or MCP
`api_lookup`, then run `pcx symbol-check`, `pcx check-answer`, MCP
`validate_code`, or MCP `validate_answer`. If the target language docs do not
prove a symbol exists, do not invent it.

---

## 1. Know the Target Before You Touch Memory

**Never read or write a single byte until you know what you're reading.**

Before implementing any feature:
- State the game, engine, and binary you're targeting. Name the module.
- Identify whether offsets come from a sig scan, a hardcoded offset table, or the r5sdk/community SDK. Say which.
- If an offset is hardcoded, flag it: hardcoded offsets break on game updates. Prefer pattern scans.
- If the struct layout comes from a reversed SDK, cite the header file. If you guessed it, say "UNVERIFIED" and mark the offset.
- If you don't know the field size, read it as `ru64` and inspect — never assume `int32` vs `float32` without evidence.

```
Before: "Read player health at base+0x43E0"
After:  "r5sdk/src/game/server/player.h defines m_iHealth at 0x43E0 (int32).
         Sig for entity list: 48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 81
         Last verified: Season 21 patch 1.98"
```

**Why:** A wrong offset doesn't crash your script — it reads garbage silently. You'll spend an hour debugging ESP that draws at (0, 0) because the position field moved 8 bytes. Ground every offset.

---

## 2. Addresses Are `uint64`, Always

**One type for addresses. No exceptions. No `int64` addresses.**

- Every variable holding a memory address is `uint64`. Period.
- `proc.base_address()` returns `uint64`. Module bases are `uint64`. Pointer chain intermediates are `uint64`.
- If you must pass an address to a function taking `int64`, use `cast<int64>(addr)` at the call site, not at storage.
- Pattern scan results are `uint64`. Entity list pointers are `uint64`. VTable slots are `uint64`.

```cpp
// WRONG
int64 base = p.base_address();
int64 entity = p.r64(base + 0x1234);  // sign-extends high addresses, subtle corruption

// RIGHT
uint64 base = p.base_address();
uint64 entity = p.ru64(base + 0x1234);
```

**Why:** `int64` and `uint64` are implicitly convertible in Enma but sign-extend differently in pointer arithmetic. Kernel addresses and high-usermode addresses (Windows `0x7FF...`) turn negative in `int64`, breaking comparisons and offset math. One type, zero bugs.

---

## 3. Validate Before You Chain

**Every pointer in a chain can be null. Check it or crash.**

- After every `ru64` that produces a pointer, check for 0 before dereferencing.
- After `ref_process()`, check `.alive()` immediately.
- After `find_code_pattern()`, check for 0 — a missed sig means the offset table is stale.
- After `get_module_base()`, check for 0 — the module might not be loaded yet.
- `is_valid_address()` exists. Use it when chasing unknown pointer chains.

```cpp
// WRONG — entity_list could be 0 after a patch
uint64 entity_list = p.ru64(base + ENTITY_LIST_OFFSET);
uint64 entity = p.ru64(entity_list + i * 0x8);  // reads from address 0x0 + i*8 = garbage

// RIGHT
uint64 entity_list = p.ru64(base + ENTITY_LIST_OFFSET);
if (entity_list == 0) return;
uint64 entity = p.ru64(entity_list + i * 0x8);
if (entity == 0) continue;
```

**Why:** Failed reads return 0 silently in Perception. A null pointer in a chain doesn't crash — it reads from address `0 + offset`, which returns more zeros or garbage. Your ESP draws nothing or draws at (0,0) and you don't know why. Validate every link.

---

## 4. Separate Scan from Render

**Pattern scans and heavy reads happen once or on interval. Rendering happens every frame.**

Structure every script as:
1. **`main()`** — setup: process attach, pattern scans, resolve base addresses. Run once.
2. **Update routine** — read entity data, build display list. Runs on interval or every frame, but does NO drawing.
3. **Render routine** — draws from the cached display list. Runs every frame. Does NO memory reads.

```cpp
// Global state
proc_t g_proc;
uint64 g_entity_list;
vec3[] g_positions;

void on_update(int64 data) {
    // Read game state — separated from render
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 0x8);
        if (ent == 0) continue;
        g_positions[i] = g_proc.read_vec3_fl32(ent + POS_OFFSET);
    }
}

void on_render(int64 data) {
    // Draw from cache — no proc reads here
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        draw_circle(world_to_screen(g_positions[i]), 5.0, g_color_enemy, 1.0, true);
    }
}
```

**Why:** Mixing reads and draws makes every frame dependent on read latency. If the target process lags or a page is swapped out, your overlay stutters. Separating them means the render path is pure compute — smooth even when reads are slow. It also makes the code testable: you can verify reads independently from draw correctness.

---

## 5. Pattern Scans Over Hardcoded Offsets

**Sigs survive patches. Hardcoded offsets don't.**

- For any address that isn't a direct struct field offset from a known base, use `find_code_pattern`.
- The sig should be wide enough to be unique but not so wide it spans an instruction that changes per-build.
- Wildcard (`??`) the bytes that contain relocatable values: RIP-relative displacements, jump targets, immediate addresses.
- Store the sig as a named constant, not inline. Document what it finds.

```cpp
// Sig for CEntityList global pointer — LEA RCX, [rip+????]
// Wildcards on the 4-byte RIP displacement
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";

uint64 resolve_entity_list(proc_t& p, uint64 base, uint64 size) {
    uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0) return 0;
    // Resolve RIP-relative: read 4-byte displacement at hit+3, add to hit+7
    int32 disp = p.r32(hit + 3);
    return hit + 7 + cast<uint64>(disp);
}
```

**Why:** Every game update shuffles code and data. A hardcoded offset `0x25AB3F0` is dead on the next patch. A sig for the instruction that loads that pointer survives unless the compiler changes the instruction pattern — which is rare. Name your sigs, document what instruction they match, and resolve RIP-relative displacements correctly (4 bytes, signed, added to the *end* of the instruction).

---

## 6. One Feature, One File

**Each feature lives in its own file. No god scripts.**

- ESP in `esp.em`. Aimbot in `aim.em`. Radar in `radar.em`. Config/GUI in `menu.em`.
- Shared state (process handle, entity cache, config values) goes in a `globals.em` module and is imported.
- If two features need the same data, extract it into a shared update routine — don't duplicate reads.

```
project/
├── globals.em      # proc_t, entity cache, config state
├── offsets.em      # all sigs and resolved addresses
├── esp.em          # render routine for boxes/names/health
├── aim.em          # aimbot logic + smoothing
├── menu.em         # GUI sidebar widgets
└── main.em         # main() — setup, register routines
```

**Why:** A 2000-line monolith means every edit risks breaking unrelated features. Separate files let you reload one feature without touching others (Perception supports hot reload). It also makes it trivial to disable a feature: just don't register its routine.

---

## 7. Construct Every Frame, Cache Nothing Graphical

**Colors, vec2 positions, and font handles from `get_font*()` are cheap. Construct them fresh.**

- `color(r, g, b, a)` is a 4-byte stack struct. Creating it costs nothing.
- `vec2(x, y)` is two floats. Creating it costs nothing.
- `get_font20()` returns a cached handle — calling it every frame is fine.
- Never cache a `color` or `vec2` in a global to "avoid allocation" — there is no allocation. Enma drops them at scope exit.

```cpp
// WRONG — premature "optimization" that adds global state for nothing
color g_white;
color g_red;
int64 g_font;

int64 main() {
    g_white = color(255, 255, 255, 255);
    g_red = color(255, 0, 0, 255);
    g_font = get_font20();
    // ...
}

// RIGHT — construct in the render function, zero overhead
void on_render(int64 data) {
    color white = color(255, 255, 255, 255);
    color red = color(255, 0, 0, 255);
    draw_text("ESP", vec2(10.0, 10.0), white, get_font20(), 0, color(0,0,0,0), 0.0);
}
```

**Why:** Enma's `[[packed]]` structs are stack-allocated value types. A `color` is 4 bytes on the stack — cheaper than a global load. Caching render primitives adds mutable global state that makes reasoning about the render path harder, for literally zero performance gain.

---

## 8. Float Literals Need the `f` Suffix

**`0.2` is `float64`. `0.2f` is `float32`. The GPU and the game don't agree on which you meant.**

- All `vec2`/`vec3`/`vec4` constructors that feed vertex buffers need `float32` — use `f` suffix.
- Screen coordinates from `get_view_width()`/`get_view_height()` return `float64` — that's fine for draw calls.
- `read_vec3_fl32` returns `float64` fields (promoted) — arithmetic is `float64`, no suffix needed.
- When writing back to game memory with `wf32()`, the value is narrowed — make sure your math didn't accumulate `float64` precision you'll silently lose.

```cpp
// Custom vertex buffer data — must be float32
float32 x = 10.0f;
float32 y = 20.0f;

// Draw calls accept float64 — no suffix needed
draw_line(vec2(10.0, 20.0), vec2(100.0, 200.0), white, 1.0);
```

---

## 9. Prefer Reads Over Writes

**Reads are non-invasive. Writes alter the target's state and are inherently riskier.**

- Analysis, visualization, entity inspection, distance display — all read-only. Prefer these.
- If you must write (patching for research on a target you own or are authorized to test, modifying your own single-player session), write the minimum bytes needed and know exactly why.
- Never `wvm` a large buffer when `wu32` or `wf32` on a single field suffices.
- After a research write, verify it took effect with a read-back; some targets revert unexpected patches.
- Gate all writes behind `write_memory` permission checks — Perception enforces this; respect it in your design too.

```cpp
// WRONG — nop-patching 16 bytes when you only need one field
array<uint8> nops = {0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90};
p.wvm(recoil_addr, nops);

// RIGHT — write the single float you actually mean to change, minimal footprint
p.wf32(recoil_spread_addr, 0.0f);
```

**Why:** Every memory write mutates the target's state — a read is observation, a write is intervention. For analysis and overlay work you almost never need to write, and when you do, a minimal, deliberate write is easier to reason about and roll back than a large patch. Treat writes as a last resort, not a default.

---

## 10. World-to-Screen Is Math, Not Magic

**Implement W2S correctly once. Never approximate it.**

The formula depends on the engine's view matrix layout. For Source Engine (Apex, CS2, TF2):

```cpp
// Source Engine uses a 4x3 view matrix (3 rows of 4 floats = 48 bytes)
// Row 0: right.x, right.y, right.z, right.w
// Row 1: up.x,    up.y,    up.z,    up.w
// Row 2: fwd.x,   fwd.y,   fwd.z,   fwd.w

bool world_to_screen(vec3 world, out vec2 screen, float64 matrix_addr) {
    // Read 12 floats from the view matrix
    float64 w = m[3]*world.x + m[7]*world.y + m[11]*world.z + m[15]; // not present in 4x3 — check engine
    if (w < 0.001) return false;  // behind camera

    float64 inv_w = 1.0 / w;
    float64 nx = (m[0]*world.x + m[4]*world.y + m[8]*world.z + m[12]) * inv_w;
    float64 ny = (m[1]*world.x + m[5]*world.y + m[9]*world.z + m[13]) * inv_w;

    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2(
        (vw * 0.5) + (nx * vw * 0.5),
        (vh * 0.5) - (ny * vh * 0.5)
    );
    return true;
}
```

**Rules:**
- Always check `w > 0` (or a small epsilon) — behind-camera points produce mirrored coordinates.
- Read the matrix from the game's actual view matrix address, not a reconstructed one.
- Match the matrix layout to the engine. Source uses column-major 4x4, Unreal uses row-major, Unity uses column-major with flipped Z.
- Implement it once in a shared module. Every feature imports it.

---

## 11. GUI State Is Config, Not Code

**Every tunable goes through the GUI API. No magic constants buried in logic.**

- Bind every threshold, color, toggle, and hotkey to a GUI widget in a sidebar section.
- Use `section_checkbox` for feature toggles, `section_slider_float` for distances/smoothing, `section_keybind` for hotkeys.
- Read widget state at the top of each routine, then branch on it. Don't mix widget reads deep inside nested loops.
- Persist config to a file via the filesystem API. Load it in `main()`.

```cpp
bool g_esp_enabled;
float64 g_esp_distance;
color g_esp_color;

void setup_gui() {
    int64 sec = create_section("ESP");
    section_checkbox(sec, "Enable ESP", g_esp_enabled);
    section_slider_float(sec, "Max Distance", g_esp_distance, 0.0, 5000.0);
    // color picker, keybind, etc.
}
```

**Why:** Hardcoded thresholds mean recompiling to tweak. The overlay is your debugger — every value you might change during a session should be adjustable live. This also means someone else can use your script without reading the source.

---

## 12. Verify With the Binary, Not With Your Memory

**The IDB, the sig, and the live read must agree. If they don't, trust the live read.**

When something doesn't work:
1. Check the sig still hits in the current binary: `find_code_pattern` returns 0? Offset table is stale.
2. `struct_dump` the entity at the base you have — verify the field layout visually.
3. Cross-reference against the r5sdk headers or IDA's type info, but remember the SDK may be from an older season.
4. If the live read shows a valid-looking float where you expected an int, the struct changed. Update your types.
5. Never assume your cached offset table is correct after a game update. Re-scan everything.

```
Debugging checklist:
1. Is the process alive?           → p.alive()
2. Is the module loaded?           → get_module_base() != 0
3. Does the sig still hit?         → find_code_pattern() != 0
4. Is the pointer chain valid?     → check every link for 0
5. Does the field contain what     → struct_dump() or read + print
   you expect?
```

---

## Summary

| # | Rule | One-liner |
|---|------|-----------|
| 1 | Know the target | Ground every offset in evidence |
| 2 | `uint64` addresses | One type, zero sign bugs |
| 3 | Validate chains | Every pointer can be null |
| 4 | Separate scan/render | Reads and draws don't mix |
| 5 | Sigs over hardcodes | Survive patches |
| 6 | One feature, one file | No god scripts |
| 7 | Construct every frame | Colors and vecs are free |
| 8 | `f` suffix for float32 | The GPU cares |
| 9 | Prefer reads over writes | Reads are non-invasive |
| 10 | W2S once, correctly | Math, not magic |
| 11 | GUI for all tunables | No magic constants |
| 12 | Verify with the binary | Trust live reads over memory |

---

## Source: `.claude/skills/game-hacking-pcx/SKILL.md`

---
name: game-hacking-pcx
description: >
  Mandatory doc router for all PCX scripting sessions. Triggers on any game
  hacking, game cheat, ESP, aimbot, triggerbot, radar, Enma, AngelScript, or
  Perception.cx work. Provides the full supported doc index (32,000+ lines
  across 123 docs) and enforces reading the relevant documentation before writing any
  API call. Load alongside game-cheat-script-master and game-cheat-guidelines
  on every PCX game-cheat session.
license: MIT
---

# Game Hacking & Scripting — Perception.cx / Enma / AngelScript

## Trigger
Game hacking, game cheats, cheat scripts, ESP, aimbot, triggerbot, radar, memory reading/writing,
pattern scanning, vtable hooking, process manipulation, Enma scripting, AngelScript scripting,
Perception.cx, PCX, render overlays, any `.em` or `.as` game script work, or any mention of the
Perception platform.

## MANDATORY: Read Before Writing Code

**The only authoritative sources for PCX API names are the two upstream docs:**

1. `https://docs.perception.cx/perception/enma/readme.md` — Enma API surface
2. `https://docs.perception.cx/perception/angelscript/overview.md` — AngelScript API surface

Use the `.md` variant of any sub-page (e.g. `https://docs.perception.cx/perception/enma/proc-api.md`,
`https://docs.perception.cx/perception/angelscript/render-api.md`) for structured markdown.
The local `docs/` tree is a drift-checked mirror of these upstream pages; when in doubt, trust
the live upstream version.

You MUST read the relevant upstream doc before writing ANY Enma, AngelScript,
or PCX API code. Do not write from memory. The docs are the source of truth.

## Source-Grounding Gate

For MCP-aware clients, call `recommend_context(task, language)` first, then load
the returned skills/docs. Verify host symbols with `api_lookup(symbol, language)`
and validate generated code with `validate_code` or `validate_answer`. For CLI
workflows, use `pcx api`, `pcx symbol-check`, and `pcx check-answer`.

### When writing Enma (.em) code — read these:

**Language (always read `docs/enma/llms-language.md` first — it's the complete single-page reference):**

| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Complete language ref** | `docs/enma/llms-language.md` | 2861 | Every type, operator, control flow, struct, class, template, coroutine, exception, heap, FFI, annotation, module, addon |
| Complete SDK ref | `docs/enma/llms-sdk.md` | 832 | Embedding API, type registration, native functions, hot reload |

**Language guide (granular pages if you need detail beyond the single-page ref):**
| Doc | Path | Lines |
|-----|------|-------|
| Basics (types, vars, operators, control flow) | `docs/enma/lang-basics.md` | 267 |
| Functions (params, defaults, refs, out, variadic, lambdas) | `docs/enma/lang-functions.md` | 247 |
| Pointers (heap, address-of, member access, null) | `docs/enma/lang-pointers.md` | 357 |
| Structs & Classes (value/ref types, inheritance, vtable, interfaces, mixins) | `docs/enma/lang-structs-and-classes.md` | 912 |
| Templates (generics, monomorphization) | `docs/enma/lang-templates.md` | 173 |
| Advanced (delegates, namespaces, coroutines, exceptions, smart ptrs, FFI) | `docs/enma/lang-advanced.md` | 562 |
| Annotations (packed, align, reflect, serialize, export, dll, custom) | `docs/enma/lang-annotations.md` | 209 |
| Modules (import, .emb, multi-module linking) | `docs/enma/lang-modules.md` | 100 |
| Preprocessor (#define, #ifdef, #include, #pragma) | `docs/enma/lang-pre-processor.md` | 77 |
| Semantics & Limits (guarantees, compile-time rejects, what doesn't exist) | `docs/enma/lang-semantics-and-limits.md` | 181 |

**Addons (standard library — read the addon doc before using its types):**
| Addon | Path | Lines | Key types/functions |
|-------|------|-------|---------------------|
| Core | `docs/enma/addon-core.md` | 42 | `println`, `print` |
| Strings | `docs/enma/addon-strings.md` | 165 | `format`, `to_int`, `split`, `replace`, `substr` |
| Arrays | `docs/enma/addon-arrays.md` | 119 | `push`, `pop`, `sort`, `contains`, `slice`, `for-each` |
| Maps | `docs/enma/addon-maps.md` | 200 | `map<K,V>`, `get`, `set`, `contains`, `imap<V>` |
| Math | `docs/enma/addon-math.md` | 137 | `sin`, `cos`, `atan2`, `sqrt`, `clamp`, `lerp`, `random` |
| SIMD | `docs/enma/addon-simd.md` | 128 | SSE2 `f32x4`, `i32x4` vector ops |
| Vectors | `docs/enma/addon-vec.md` | 135 | `vec2`, `vec3`, `vec4` math types |
| 3D Math | `docs/enma/addon-math3d.md` | 182 | `quat`, `mat4` rotation/transform |
| Variant | `docs/enma/addon-variant.md` | 130 | Type-erased value container |
| Atomic | `docs/enma/addon-atomic.md` | 94 | `aint32`, `aint64` atomic ops |
| Bits | `docs/enma/addon-bits.md` | 117 | `popcount`, `clz`, `ctz`, `bswap`, `rotl` |
| Time | `docs/enma/addon-time.md` | 95 | `time_ms()`, `time_us()`, ISO 8601, `sleep` |
| Regex | `docs/enma/addon-regex.md` | 61 | `match`, `find`, `replace`, `split`, capture groups |
| File | `docs/enma/addon-file.md` | 125 | Sandboxed file I/O (permission-gated) |
| Thread | `docs/enma/addon-thread.md` | 120 | `mutex`, `lock_guard`, `condition_variable` |
| Hash Set | `docs/enma/addon-hash_set.md` | 89 | `hash_set<T>` |
| Sorted Map | `docs/enma/addon-sorted_map.md` | 89 | `sorted_map<K,V>` ordered iteration |
| List | `docs/enma/addon-list.md` | 192 | Double-ended O(1) push/pop |
| JSON | `docs/enma/addon-json.md` | 108 | `json_parse`, `json_stringify`, `json_value` navigation |

**SDK (C++ embedding — read when building host-side or custom addons):**
| Doc | Path | Lines |
|-----|------|-------|
| Quick Start | `docs/enma/sdk-quick-start.md` | 126 |
| Engine Lifecycle | `docs/enma/sdk-engine-lifecycle.md` | 166 |
| Compilation | `docs/enma/sdk-compilation.md` | 65 |
| Execution | `docs/enma/sdk-execution.md` | 103 |
| Calling Functions | `docs/enma/sdk-calling-functions.md` | 82 |
| Globals | `docs/enma/sdk-globals.md` | 79 |
| Type Registration | `docs/enma/sdk-type-registration.md` | 862 |
| Native Functions | `docs/enma/sdk-native-functions.md` | 446 |
| Hot Reload | `docs/enma/sdk-hot-reload.md` | 64 |
| Serialization & Linking | `docs/enma/sdk-serialization-and-linking.md` | 97 |
| Introspection | `docs/enma/sdk-introspection.md` | 317 |
| Lifecycle & RAII | `docs/enma/sdk-lifecycle.md` | 227 |
| Debug & Heap | `docs/enma/sdk-debug-and-gc.md` | 202 |
| Error Handling | `docs/enma/sdk-error-handling.md` | 116 |
| Safety | `docs/enma/sdk-safety.md` | 121 |
| Custom Addons | `docs/enma/sdk-custom-addons.md` | 576 |
| API Reference | `docs/enma/sdk-api-reference.md` | 411 |

### When writing PCX Enma API code — read the relevant API doc:

| API | Path | Lines | Use for |
|-----|------|-------|---------|
| **Proc API** | `docs/perception/proc-api.md` | 294 | Memory read/write, modules, pattern scan, VAD, pointer arrays, vec/quat/mat reads |
| **Render API** | `docs/perception/render-api.md` | 264 | 2D drawing (text, lines, circles, rects), fonts, shaders, vertex/index buffers, compute |
| **GUI API** | `docs/perception/gui-api.md` | 455 | Sidebar sections, checkboxes, sliders, buttons, text inputs, color pickers, keybinds |
| **Input API** | `docs/perception/input-api.md` | 126 | Mouse + keyboard state polling |
| **CPU API** | `docs/perception/cpu-api.md` | 92 | CPU ID, timing, datetime, bitcasts, thread priority |
| **Zydis API** | `docs/perception/zydis-api.md` | 133 | x86-64 assembler/disassembler |
| **Unicorn API** | `docs/perception/unicorn-api.md` | 151 | x86-64 CPU emulation |
| **Net API** | `docs/perception/net-api.md` | 200 | HTTP, WebSocket, raw UDP |
| **Win API** | `docs/perception/win-api.md` | 120 | Window enum, clipboard, keyboard/mouse send |
| **Filesystem API** | `docs/perception/filesystem-api.md` | 162 | Sandboxed file I/O |
| **Sound API** | `docs/perception/sound-api.md` | 90 | WAV/OGG playback |
| **Lifecycle** | `docs/perception/lifecycle-and-routines.md` | 134 | main(), routines, unload, exceptions |
| **MCP API** | `docs/perception/mcp-api.md` | 268 | AI agent JSON-RPC surface |

### PCX IDE & Extensions:

| Doc | Path | Lines |
|-----|------|-------|
| Perception IDE | `docs/perception/ide.md` | 585 |
| Extensions API | `docs/perception/extensions-api.md` | 371 |
| Analyzer | `docs/perception/analyzer.md` | 370 |

## How To Use These Docs

1. **Before starting a game-cheat script**: load `skill://game-cheat-script-master` and read `knowledge/cheat-script-cookbook.md`
2. **Before writing AngelScript code**: start from `https://docs.perception.cx/perception/angel-script/overview.md` and read the relevant `.md` sub-page
3. **Before writing Enma code**: use Enma only for explicit `.em` or migration/AOT work, then start from `https://docs.perception.cx/perception/enma/readme.md`
4. **If unsure about a type, function, or parameter**: read the upstream doc, don't guess
5. **If the doc says a function is "gated"**: it requires a permission flag — mention this to the user
6. **For a starting AngelScript project scaffold**: use `templates/angelscript-overlay.as` or `pcx create --language angelscript --kind overlay`

## Anti-Hallucination Rule

You must NEVER invent a PCX or Enma API name. Every function,
method, type, and import you use must come from one of:
  - `https://docs.perception.cx/perception/enma/readme.md` and its sub-pages,
  - `knowledge/pcx-api-index.json` (via `pcx symbol-check` or the
    `mcp:pcx-knowledge` `validate_code` tool),
  - a user-defined function declared in the same script.

Before delivering code, run `pcx verify <file>` (or `pcx symbol-check
<file>` if `verify` is unavailable). If it reports an `unknown_call`,
`unknown_type`, or `missing_import`, fix it by reading the correct upstream
doc and using the real symbol. Do not silence the checker by renaming things.

See `knowledge/pcx-doc-roots.md` for the full sourcing policy.

## Cheat-Script Scaffolds

- **Enma skeleton**: `templates/cheat-skeleton-em/` — globals, offsets, utils, ESP, aim, triggerbot, radar, menu, main
- **Cookbook recipes**: `knowledge/cheat-script-cookbook.md` — pattern scan, pointer chain, W2S, ESP, aim smoothing, FOV, triggerbot, radar, config, unload cleanup

## Critical Enma Rules (from the docs)

- **Addresses are `uint64`**, never `int64` — sign-extension breaks high addresses
- **`float32` literals need `f` suffix**: `0.2f` not `0.2`
- **Implicit conversion: `int→float` OK, `float→int` COMPILE ERROR** — use `cast<int32>(f)`
- **`signed↔unsigned` is COMPILE ERROR** — use `cast<uint64>(signed_val)`
- **`color` and `vec2` are value types** — 4-byte and 8-byte stack structs, construct every frame
- **Handles from `create_*`/`load_*` are encrypted `int64`** — pass back, don't inspect
- **`main()` returns `> 0` to stay loaded, `<= 0` to unload**
- **Routines registered via `register_routine(cast<int64>(fn), data)`**
- **`proc_t` released on scope exit** (RAII) — no leak if you use stack variables
- **Failed reads return 0**, not exceptions — validate pointers
- **Pattern sigs**: hex bytes, `??` wildcard, e.g. `"48 8B 05 ?? ?? ?? ?? 48 85 C0"`
- **`import "vec"; import "color";`** — modules must be imported to use their types
- **`string` interpolation**: `f"value={x}"` — use `format()` for hex: `format("0x{x}", addr)`
- **No garbage collector** — deterministic RAII, destructors run at scope exit

## LSP Servers (built, ready to use)

- **Enma LSP**: `lsp/enma-lsp/server/dist/server.js`

## RE Tools & Knowledge

- **Plugins & FLIRT sigs**: `knowledge/re-plugins-and-tools.md` — 6 IDA plugins, 4 Ghidra extensions, 51 FLIRT sigs, diffing, ret-sync
- **Anti-cheat architecture**: `knowledge/anti-cheat-architecture.md` — EAC/BE/Vanguard/GG detection matrix
- **Kernel RE tools**: `knowledge/kernel-re-tools.md` — WinDbg, HyperDbg, Volatility, PCILeech, IRPMon
- **AC driver patterns**: `signatures/anti-cheat/common-ac-patterns.md` — driver ID, callback sigs, integrity check patterns
- **Deobfuscation**: `skill://deobfuscation` — VM/CFF/packer reversal methodology (Themida, VMProtect, OLLVM)
- **Obfuscation taxonomy**: `knowledge/obfuscation-taxonomy.md` — protector architecture and weaknesses
- **Deobfuscation tools**: `knowledge/deobfuscation-tools.md` — NoVmp, Triton, Miasm, D-810, ScyllaHide, FLOSS
- **Protector patterns**: `signatures/obfuscation/protector-patterns.md` — VMP/Themida/OLLVM section names, dispatcher patterns, anti-debug
- r5sdk: `sdks/r5sdk/` (2438 reversed headers for Apex Legends)
- IDA IDB: `idb/r5apex_dx12_dump.i64` (28936 functions, FLIRT+types)
- Ghidra: `ghidra-projects/r5apex/`
- radare2, Ghidra, semgrep MCP servers all available

---

## Source: `.claude/skills/pcx-coding-discipline/SKILL.md`

---
name: pcx-coding-discipline
description: >
  Workflow discipline for developing Enma (.em) and AngelScript (.as) scripts
  on Perception.cx. Derived from Karpathy principles — think before coding,
  simplicity first, surgical changes, goal-driven execution — rewritten for
  cheat development realities: stale offsets, silent failed reads, detection
  surface. Always active when writing or editing PCX scripts.
license: MIT
---

# PCX Coding Discipline — How to Write Scripts, Not What They Look Like

Workflow discipline for developing Enma (`.em`) and AngelScript (`.as`) scripts on Perception.cx. Derived from the four Karpathy principles — *think before coding, simplicity first, surgical changes, goal-driven execution* — and rewritten for the realities of cheat development: stale offsets, silent failed reads, detection surface, and overlays you debug by looking at them.

**Always active when writing or editing PCX scripts.** This is the *process* layer. The `game-cheat-guidelines` skill is the *code-shape* layer (uint64 addresses, null guards, render separation). Load both: this one tells you how to work, that one tells you what the code must look like.

**Prerequisite:** Read the relevant doc before writing any API call — see `skill://game-hacking-pcx` for the file-by-file index.

## Trigger
Writing or editing any `.em` / `.as` script, adding a cheat feature, refactoring a script, fixing a broken overlay, deciding how much to build, or judging whether a script is "done."

---

## 1. Think Before You Touch the Editor

**Name the target, the source of every offset, and the tradeoff you're making — out loud — before you write a line.**

The single most expensive habit in cheat development is writing code against assumptions. A wrong offset doesn't throw; it reads garbage and your ESP draws at (0, 0). Before implementing:

- **State the target.** Game, engine, module. "Apex / Source (r5) / `r5apex.exe`."
- **State where each offset comes from.** Sig scan, SDK header, or hardcode — and say which. If you're guessing a struct field, write `// UNVERIFIED` next to it.
- **Surface the tradeoff the user didn't ask about.** Read-only ESP is invisible; a memory write for aimbot is a detection surface. Per-frame reads are simple but couple render to read latency. Say which you're choosing and why.
- **If the doc is ambiguous or the API is permission-gated, stop and read it.** Do not invent `draw_esp()` or assume `draw_circle` takes a fill flag. Open `docs/perception/render-api.md`.

```
Before: "I'll write an ESP overlay."
        *invents function names, assumes int32 offsets, no W2S behind-camera check*

After:  "Target: Apex / Source (r5). Entity list via sig (UNVERIFIED layout, r5sdk season 21).
         Read-only ESP, per-frame W2S — accepting read/render coupling for v1 simplicity.
         Reading render-api.md + lifecycle-and-routines.md before writing."
```

**Why:** Confusion hidden behind plausible code costs hours. Confusion stated up front costs one sentence and gets corrected before it compiles into a silent bug.

---

## 2. The Simplest Cheat That Works

**Build the minimum feature that satisfies the ask. Nothing speculative.**

Cheat scripts rot into 2000-line monoliths because every feature arrives with prediction, smoothing, themes, and a config framework nobody requested. Climb down the ladder:

- **"Highlight enemies" is a box, not a skeleton-ESP-with-bones-and-LOD.** Ship the box. Add bones when asked.
- **An aimbot the user described as "snap to head" doesn't need velocity prediction.** Don't add it.
- **No config system for a value that never changes.** A fixed enemy color is `color(255,0,0,255)`, not a JSON-loaded theme engine.
- **No abstraction over the proc API.** `p.ru64(...)` is the interface. Wrapping it in a `MemoryManager` class buys nothing.
- **No "feature manager" framework for three features.** Three registered routines is the framework.

```cpp
// WRONG — entity-component scaffolding for "draw boxes on enemies"
class IFeature { void update(); void render(); }
class FeatureRegistry { array<IFeature@> features; ... }
class EspFeature : IFeature { /* 200 lines */ }

// RIGHT — two routines, done
void on_update(int64 data) { /* read positions into g_positions */ }
void on_render(int64 data) { /* draw boxes from g_positions */ }
```

**Why:** Every speculative line is a line someone debugs at 3am after a patch. The lazy version ships today and is trivially extended when a real second requirement shows up — which is the only honest signal that the abstraction was needed.

---

## 3. Surgical Edits — One Feature, One Diff

**When changing a script, touch only the feature you're changing. Clean up only the mess your change makes.**

Perception scripts are built for hot reload precisely so you can change one file without disturbing the rest. Honor that:

- **Editing ESP color? Edit `esp.em`.** Do not reformat `menu.em`, rename globals in `globals.em`, or "tidy" `main.em` while you're in there.
- **Match the module's existing style** — naming, the per-feature file split, the order of routine registration. A second convention beside the first is worse than the style you'd have picked.
- **If your change orphans a global or import, remove it.** If you spot pre-existing dead code unrelated to your change, mention it — don't delete it.
- **Don't churn working offsets.** A sig that still hits and resolves to valid data is not your problem today.

```
Task: "the enemy boxes are the wrong color"

WRONG diff:  esp.em (color)  +  globals.em (renamed g_col → g_enemyColor)
             +  menu.em (reordered widgets)  +  main.em (reformatted)

RIGHT diff:  esp.em (color)
```

**Why:** Every file you touch is a file that can break and a file the next reader has to diff. A four-file diff to change one color hides the actual change and risks the three features you didn't mean to touch.

---

## 4. Done Means It Works on the Target

**Define success as something you can *see* on the live game, then loop until you see it. Compiling is not done.**

A script that compiles has proven nothing about whether the offsets are right, the W2S matches the engine, or the overlay aligns. Set a concrete bar and verify against it:

- **Write the success criteria before coding**, as observable facts: "boxes track enemies at any distance, nothing draws behind the camera, count matches the scoreboard."
- **The overlay is your debugger.** When something's off, draw the raw W2S coordinates and `print` the entity count — don't guess.
- **Loop:** compile → load → look at the screen → compare to the criteria → fix → reload. Repeat until every criterion holds.
- **When the IDB, the SDK, and the live read disagree, trust the live read** (see `game-cheat-guidelines` #12). The SDK may be from an older season.

```
Success criteria for "enemy ESP":
[ ] A box appears on every enemy entity (count == live enemy count)
[ ] Boxes track movement smoothly, no stutter
[ ] No box renders when the entity is behind the camera (W2S w > 0)
[ ] No box at (0,0) — that means a null read slipped a guard
[ ] Boxes scale with distance (far enemies = smaller boxes)
```

**Why:** "It compiles" and "it works" are different claims, and only the second one is the deliverable. A success checklist turns a vague "make ESP" into a loop you can run yourself without asking the user whether it's right.

---

## 5. Deletion Before Addition

**Try removing code before writing new code. The shortest script that works is the one with the fewest lines to break after a patch.**

When a feature request arrives, check what already exists first:

- **Can you delete a workaround instead of adding a second one?** Two workarounds for the same stale offset is a sign one should die.
- **Can you inline a wrapper?** A `ReadEntity()` function that calls `p.ru64()` once with no validation adds a name, not value. Inline it.
- **Can you merge two features into one routine?** If `on_update_esp` and `on_update_radar` both walk the same entity list, one walk and two draw calls in `on_render` is fewer lines and fewer reads.
- **Before adding a class, count its callers.** One caller = inline. Two = maybe. Three = extract, not before.

```cpp
// WRONG — utility wrapper around a one-liner
uint64 ReadEntityBase(proc_t@ p, uint64 list, int idx) {
    return p.ru64(list + idx * 0x20);
}
// ... called exactly once

// RIGHT — inline it, the proc_t API is already the interface
uint64 ent = p.ru64(entity_list + i * 0x20);
```

**Why:** Every line in a cheat script is a line you re-validate after a game patch. 80 lines is 80 potential breakpoints. 40 lines is half the post-patch work.

---

## 6. Question the Requirement

**Ship the minimum, then challenge the rest — in the same response, not a separate conversation.**

When the ask is vague or ambitious ("make a full ESP with health bars, distance, snaplines, team colors, and a config panel"):

1. **Build the core** — boxes on enemies, W2S, null guards.
2. **Ship it working.**
3. **In the same response:** "Done: box ESP with W2S + null guards. Health bars and snaplines are 10 lines each when you want them. Team colors need a second read per entity — add when the base ESP is confirmed working. Config panel is overhead for 3 settings — `bool` globals + a sidebar checkbox cover it."

Never stall on an answer you can default. Never build five features to avoid the conversation about whether three of them matter.

```
Pattern:  [working code] → skipped: [X]. add when [Y].
```

---

## 7. Mark Deliberate Shortcuts

**Every deliberate simplification gets a `// defer:` comment naming its ceiling and the trigger to revisit.**

`// UNVERIFIED` marks offset confidence. `// defer:` marks *design* shortcuts — places where you chose the simple path and know the ceiling.

```cpp
// defer: single entity array walk, separate walks per feature if >200 entities tank FPS
void on_update(int64 data) { ... }

// defer: hardcoded team color, config panel if user asks for customization
color enemy_col = color(255, 0, 0, 255);

// defer: global proc_t handle, per-feature handles if multi-process support needed
proc_t@ g_proc;
```

Format: `// defer: <what was simplified>, <when to revisit>`

A `// defer:` with no trigger is a shortcut that rots silently. Always name the trigger.

**Not deferred:** pointer validation, `w > 0` checks, `uint64` for addresses, `f` suffix on floats. Those are the floor, not shortcuts.

---

## 8. One Self-Check Per Non-Trivial Feature

**You can't unit test against a live game, but non-trivial logic leaves one sanity print behind.**

Cheat scripts run against a live target — no mock framework, no test harness. But logic bugs (wrong struct offset math, bad matrix indexing, off-by-one in entity iteration) can be caught with a visible sanity check:

- **Entity count print:** `print("entities: " + g_positions.length());` in `on_update`. If it reads 0 or 9999, something's wrong before you even look at the overlay.
- **Address range check:** `if (addr < 0x10000 || addr > 0x7FFFFFFFFFFF) print("suspect addr: " + addr);` — catches sign-extension and null-deref-adjacent reads.
- **W2S validation:** draw the raw screen coords as text before drawing boxes. If they cluster at (0,0), a null read slipped.
- **One `print()` per feature, gated behind a debug flag.** Not a logging framework — one line.

```cpp
// Self-check: remove or gate behind g_debug when stable
if (g_debug) print("[esp] ents=" + ents.length() + " visible=" + drawn);
```

**Why:** The laziest debugger that catches real bugs. One print per feature is near-zero overhead. A logging framework for three features is debt you don't need.

---

## Summary

| # | Principle | In PCX terms |
|---|-----------|--------------|
| 1 | Think Before Coding | Name target, offset source, and tradeoff before the first line |
| 2 | Simplicity First | Ship the box, not the framework — no speculative features |
| 3 | Surgical Changes | One feature, one diff; clean only your own orphans |
| 4 | Goal-Driven Execution | Done = visible success criteria met on the live target, not "compiles" |
| 5 | Deletion Before Addition | Try removing/inlining before writing new code |
| 6 | Question the Requirement | Ship the minimum, challenge the rest in the same response |
| 7 | Mark Deliberate Shortcuts | `// defer: <ceiling>, <trigger>` for design shortcuts |
| 8 | One Self-Check Per Feature | One `print()` per non-trivial feature, gated behind `g_debug` |

---

## Source: `.claude/skills/pcx-re-discipline/SKILL.md`

---
name: pcx-re-discipline
description: >
  Workflow discipline for reverse engineering and offset maintenance: locating
  structs, generating signatures, resolving RIP-relative addresses, and
  keeping an offset table alive across patches. Derived from Karpathy
  principles, rewritten for RE where the failure mode is a confident wrong
  answer. Always active when doing RE or offset work.
license: MIT
---

# PCX Reverse-Engineering Discipline — Finding Offsets Without Fooling Yourself

Workflow discipline for reverse engineering and offset maintenance: locating structs, generating signatures, resolving RIP-relative addresses, and keeping an offset table alive across game patches. Derived from the four Karpathy principles — *think before coding, simplicity first, surgical changes, goal-driven execution* — rewritten for RE work, where the failure mode isn't a crash but a confident wrong answer.

**Always active when doing RE or offset work.** This complements `game-cheat-guidelines` #1 (ground every offset) and #12 (verify with the binary), and the `knowledge/offset-methodology.md` mechanics. Those cover *how* to scan; this covers *how to work* so you don't ship a guess.

## Trigger
Disassembling a function, mapping a struct layout, generating a byte signature, resolving an offset, updating an offset table after a patch, or cross-referencing an SDK against a live binary. Tools: IDA, Ghidra, radare2, and the Perception RE tools (`struct_dump`, `find_xrefs`, `analyze_vtable`, `read_rtti`, `generate_signature`, `find_code_pattern`, `build_call_graph`).

---

## 1. Hypothesize Before You Disassemble

**Form a claim about what a function or field *is*, then look for evidence — don't reverse aimlessly and rationalize whatever you find.**

A float at `entity+0x43E0` that reads `100.0` might be health. It might be armor, a timer, or a shield that happens to start at 100. Guessing wrong here is silent and expensive.

- **State the hypothesis first.** "This sig should land on the LEA that loads `CEntityList`. Expected: `48 8D 0D` followed by a RIP displacement."
- **Use the cheapest evidence before manual disasm.** RTTI names (`read_rtti`) and string xrefs (`find_xrefs`) identify a class faster than reading instructions. Reach for them first.
- **Mark unverified findings `UNVERIFIED` and cite the source** — r5sdk header path, RTTI string, IDA xref address. An offset without a citation is a rumor.
- **One value is not proof.** Confirm a field by watching it change as you'd expect in-game, or by matching the SDK layout — not by a single plausible read.

```
Before: "0x43E0 is health, it reads 100."

After:  "Hypothesis: 0x43E0 = m_iHealth (int32).
         Evidence: r5sdk/player.h offset matches; read_rtti confirms class CPlayer;
         value drops to 73 after taking damage in-game. CONFIRMED."
```

**Why:** RE has no compiler to catch you. The only thing standing between a wrong offset and an hour of debugging ESP-at-(0,0) is the evidence you demanded before believing your own hypothesis.

---

## 2. The Simplest Signature That's Unique

**The shortest byte pattern that hits exactly one location. Not longer, not vaguer.**

A sig is a tradeoff: too specific and it breaks on the next compiler tweak; too loose and it matches three places and resolves to garbage.

- **Wildcard only the relocatable bytes** — RIP-relative displacements, absolute immediates, jump targets. Keep the opcodes. `48 8D 0D ?? ?? ?? ??` wildcards the displacement, keeps the `LEA RCX` opcode.
- **Stop at the first length that's unique.** Verify it with `find_code_pattern` over the module — one hit means stop. Don't bolt on ten more bytes "to be safe"; that's the brittleness you'll pay for next patch.
- **Don't reverse a whole class to read one field.** `struct_dump` the instance and xref the accessor function. Map the entire vtable only when you actually need the entire vtable.
- **Don't build a full offset dumper for three offsets.** Three sigs in `offsets.em` is the right size for three offsets.

```cpp
// WRONG — 24 bytes, spans an immediate that changes per build → dead next patch
"48 8D 0D 30 AF 25 02 E8 1A 4C 00 00 48 8B D8 48 85 DB 74 12 8B 05 ..."

// RIGHT — shortest unique hit, displacement wildcarded
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";
// verify: find_code_pattern(base, size, SIG_ENTITY_LIST) returns exactly one hit
```

**Why:** Every non-wildcarded byte is a bet that the compiler emits it identically next build. The minimal unique sig makes the fewest bets, so it survives the most patches — which is the entire point of using sigs over hardcodes.

---

## 3. After a Patch, Re-verify Only What Broke

**Run the whole table, fix the misses, leave the hits alone. Don't regenerate offsets that still work.**

The temptation after a game update is to rebuild the offset table from scratch. That's churn: it risks the offsets that were fine and buries the one real change in noise.

- **Run every sig.** `find_code_pattern` returning 0 is a miss — that sig needs a new pattern. A hit that resolves to valid data is fine; leave it untouched.
- **Verify the survivors didn't silently shift.** A sig can still hit while the *struct field* behind it moved. Spot-check resolved pointers with `struct_dump`.
- **Touch only the broken entries.** Re-sig the misses, update their resolved addresses, bump the version stamp, and log exactly what changed in a changelog. The diff should be the patch's actual damage, nothing more.

```
Post-patch checklist:
[ ] Ran all N sigs                          → 3 misses, N-3 hits
[ ] Hits resolve to valid data              → struct_dump spot-check OK
[ ] Re-sigged ONLY the 3 misses             → no churn on working entries
[ ] Bumped version stamp + changelog        → "Season 22: re-sigged entity_list,
                                               view_matrix, local_player"
```

**Why:** A surgical post-patch diff is reviewable and reversible — you can see precisely what the update moved. A full-table rewrite hides the signal, re-introduces transcription bugs into offsets that were already correct, and turns a 20-minute fix into a re-audit.

---

## 4. Trust Live Memory, Loop Until It Agrees

**Success is a sig that resolves to an address whose *live contents* match the expected layout. Loop until the three sources agree, and when they don't, the running process wins.**

The IDB, the SDK headers, and live memory are three views that drift apart. The IDB is a snapshot; the SDK may be an old season; only live memory is the truth right now.

- **Define done concretely:** "sig hits once, RIP resolves to an address, the bytes there `struct_dump` to the layout I expect."
- **Loop:** sig hit → resolve RIP-relative (4-byte signed displacement added to the *end* of the instruction) → read at the target → `struct_dump` / `print` → does it match the hypothesis? → if not, fix the sig or the resolution math and repeat.
- **Resolve RIP correctly or everything downstream is wrong:** `target = hit + instr_len + read_i32(hit + disp_offset)`. Off-by-one on the instruction length points you at the wrong global.
- **When the SDK says one offset and the live read says another, trust the live read** and update your notes. The header was written for a build that no longer exists.

```cpp
// The verify loop, made explicit
uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
if (hit == 0) { println("MISS — sig is stale, re-RE the load instruction"); return; }
int32 disp   = p.r32(hit + 3);          // displacement at LEA+3
uint64 target = hit + 7 + cast<uint64>(disp);  // end of 7-byte LEA + signed disp
uint64 list  = p.ru64(target);
println(format("entity_list global @ 0x{x} -> 0x{x}", target, list));
// struct_dump `list` and confirm it looks like a CEntityList before trusting it
```

**Why:** A sig that compiles into your script proves nothing. A sig that resolves to live memory matching your expected struct is the only evidence that the offset is real — and demanding that evidence is what separates a maintained offset table from a pile of hopeful constants.

---

## Summary

| # | Principle (Karpathy) | In RE terms |
|---|----------------------|-------------|
| 1 | Think Before Coding | Hypothesize + cite evidence before believing a field's meaning |
| 2 | Simplicity First | Shortest unique sig; wildcard only relocatable bytes |
| 3 | Surgical Changes | Post-patch: fix only the misses, never churn working offsets |
| 4 | Goal-Driven Execution | Done = sig resolves to live memory matching the expected layout |

---

## Source: `.claude/skills/pcx-perf-budget/SKILL.md`

---
name: pcx-perf-budget
description: >
  Turns the update/render separation rule into enforceable numeric budgets
  using mono_us() measurements. Covers per-frame targets at common refresh
  rates, per-call cost rules of thumb, a drop-in profiler recipe, and
  read-coalescing patterns. Always active when writing or reviewing
  performance-sensitive render or update routines.
license: MIT
---

# Performance Budget — Frame-Time Targets for PCX Scripts

Turns `game-cheat-guidelines` rule #4 (separate update from render) into enforceable numeric budgets, so the question "is my script too slow?" gets answered with `mono_us()` measurements instead of vibes. Covers per-frame targets at common refresh rates, per-call cost rules of thumb, the drop-in `profile_begin/end` recipe, and the read-coalescing patterns that produce the biggest wins.

**Always active when writing or reviewing performance-sensitive paths** (render routines, update routines, entity loops, pattern scans inside hot paths).

**Prerequisite:** `docs/enma/addon-time.md` for the timing primitives (`mono_us`, `now_us`, `sleep_ms`); `skill://game-cheat-guidelines` rules #4 (update/render separation) and #7 (per-frame construction).

---

## Trigger

Render stutter, FPS drop on overlay enable, "my script feels slow," profiling questions, write-up of per-feature performance, decisions about whether to cache or recompute, multi-routine scripts where update + render share a frame budget.

---

## 1. Know the Frame Budget at Your Target Refresh Rate

**The frame budget is the entire wall-clock window between two consecutive render calls. Everything — your update, your render, the game's own rendering, the GPU present — must fit inside it.**

Total frame budgets:

| Refresh | Budget per frame | PCX render budget (target) | PCX update budget (target) |
|---|---|---|---|
| 60 Hz | 16.67 ms | ≤ 2.0 ms | ≤ 4.0 ms |
| 120 Hz | 8.33 ms | ≤ 1.5 ms | ≤ 3.0 ms |
| 144 Hz | 6.94 ms | ≤ 1.5 ms | ≤ 2.5 ms |
| 240 Hz | 4.17 ms | ≤ 1.0 ms | ≤ 1.5 ms |
| 360 Hz | 2.78 ms | ≤ 0.7 ms | ≤ 1.0 ms |

The render budget is small because the game's own renderer + the GPU present + your overlay all share the frame. If your render path takes 5 ms at 144 Hz, you've eaten 72% of the frame by yourself, leaving 1.94 ms for the game's render — which causes the game to drop frames even though it would have hit 144 Hz without your overlay.

The update budget is more generous because, if you separate update from render properly (rule #4), update runs less frequently and on its own clock — it competes with the game less directly. But "less directly" is not "for free": a 10 ms update routine running at 60 Hz costs the same total CPU as a 2 ms render routine running at 144 Hz × 2.

**Heuristic:** measure once, then forget. If your script runs at the target FPS with no stutter on the lowest-spec machine you ship to, the budgets are met. If it stutters, instrument first (Step 3) before optimizing.

**Why:** Hard numeric targets prevent the "feels slow, must be fast" loop where you over-cache things that don't matter and miss the one routine that does. The render budget being tight is non-negotiable; the update budget is the negotiable lever — push work into update, off the render path, and most stutter disappears.

---

## 2. Per-Call Cost Rules of Thumb

**Order-of-magnitude costs for the operations you'll write most. Measure on your target; these are guides for *which order* of magnitude to expect, not contracts.**

| Operation | Cold (page-fault) | Warm (cached) | Notes |
|---|---|---|---|
| `proc.ru8/16/32/64` | 10-100 µs | 1-5 µs | Cold = first read of a page; warm = same page already touched this frame |
| `proc.rf32/rf64` | 10-100 µs | 1-5 µs | Same as integer reads — cost is the cross-process read, not the type |
| `proc.read_vec3_fl32` | 30-300 µs | 5-15 µs | One read of 12 bytes vs three separate reads |
| `proc.read_memory(N)` bulk | 30-500 µs depending on N | 10-100 µs | A single struct-dump is almost always cheaper than N scalar reads |
| `proc.find_code_pattern` | 5-200 ms first scan | N/A | Cold path only — never in update/render. Run in `main()` and cache. |
| `is_key_pressed` / `is_key_down` | < 1 µs | < 1 µs | Cheap; fine in hot paths |
| `draw_rect` / `draw_line` / `draw_circle` | 1-10 µs | 1-10 µs | Cost dominated by GPU command submission, not CPU |
| `draw_text` | 5-50 µs | 5-50 µs | Per-glyph atlas lookup + GPU submission; longer strings cost more |
| `world_to_screen` (pure math) | 1-5 µs | 1-5 µs | When matrix is cached; if you re-read the matrix per call, add a `read_memory` cost |
| GUI widget query (`section_*` reads) | < 1 µs | < 1 µs | Reading widget state is a local memory access |
| `now_us` / `mono_us` | < 0.5 µs | < 0.5 µs | Cheap; safe to call multiple times per frame for profiling |

**The implication:** a render path that does 50 entity boxes with one `read_vec3_fl32` per entity inside the render routine costs `50 × 5-15 µs = 0.25-0.75 ms` *if* the entity pages are warm. Cold-cache, it could be `50 × 30-300 µs = 1.5-15 ms` — already over the render budget at 144 Hz on the high end. Solution: move the reads to update (cache the cold-page cost there), draw from the cache.

**Why:** The single most important number to internalize is that cross-process memory reads are *very expensive* relative to draws and math. A NOP loop running 1000 iterations costs nothing; 1000 `ru32` calls can be 30 ms. Every performance problem in a PCX script is either too many reads or reads on the wrong thread.

---

## 3. The `profile_begin/end` Drop-In Recipe

**A minimal inline profiler with no new modules, no allocation, no rebuilds. Drop into any script, get per-routine breakdowns in console or on screen.**

The pattern uses `mono_us()` (monotonic; safe for deltas) and a small fixed-size accumulator. No `map` needed — name your buckets explicitly.

```cpp
import "vec";
import "color";

// ── Profile state — tiny fixed accumulator ──
const int32 NUM_BUCKETS = 8;
string  g_bucket_name[8];        // initialized once
int64   g_bucket_total_us[8];    // accumulated microseconds
int64   g_bucket_count[8];       // number of samples
int64   g_bucket_max_us[8];      // worst single sample
int64   g_profile_last_dump = 0;
int64   g_profile_dump_interval_us = 1000000;  // dump every second

// Push/pop pattern — name maps to bucket index 0..NUM_BUCKETS-1
int64 g_bucket_start_us[8];

void profile_begin(int32 bucket) {
    g_bucket_start_us[bucket] = mono_us();
}

void profile_end(int32 bucket) {
    int64 dur = mono_us() - g_bucket_start_us[bucket];
    g_bucket_total_us[bucket] += dur;
    g_bucket_count[bucket]    += 1;
    if (dur > g_bucket_max_us[bucket]) {
        g_bucket_max_us[bucket] = dur;
    }
}

// Call once per frame from render — prints once per second
void profile_dump_if_due() {
    int64 now = mono_us();
    if (now - g_profile_last_dump < g_profile_dump_interval_us) return;
    g_profile_last_dump = now;

    println("── PROFILE ──");
    for (int32 i = 0; i < NUM_BUCKETS; i++) {
        if (g_bucket_count[i] == 0) continue;
        int64 avg = g_bucket_total_us[i] / g_bucket_count[i];
        println(format("  {s}: avg {d}us  max {d}us  ({d} samples)",
                       g_bucket_name[i], avg, g_bucket_max_us[i], g_bucket_count[i]));
        // Reset for next window
        g_bucket_total_us[i] = 0;
        g_bucket_count[i]    = 0;
        g_bucket_max_us[i]   = 0;
    }
}

// Bucket assignments (give them stable indices)
const int32 BKT_UPDATE_ENTITIES = 0;
const int32 BKT_RESOLVE_OFFSETS = 1;
const int32 BKT_RENDER_ESP      = 2;
const int32 BKT_RENDER_HUD      = 3;

int64 main() {
    g_bucket_name[BKT_UPDATE_ENTITIES] = "update_entities";
    g_bucket_name[BKT_RESOLVE_OFFSETS] = "resolve_offsets";
    g_bucket_name[BKT_RENDER_ESP]      = "render_esp";
    g_bucket_name[BKT_RENDER_HUD]      = "render_hud";
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

void on_update(int64 data) {
    profile_begin(BKT_UPDATE_ENTITIES);
    // ... entity read loop ...
    profile_end(BKT_UPDATE_ENTITIES);
}

void on_render(int64 data) {
    profile_begin(BKT_RENDER_ESP);
    // ... ESP draws ...
    profile_end(BKT_RENDER_ESP);

    profile_begin(BKT_RENDER_HUD);
    // ... HUD draws ...
    profile_end(BKT_RENDER_HUD);

    profile_dump_if_due();
}
```

Sample output after one second:

```
── PROFILE ──
  update_entities: avg 1840us  max 4200us  (12 samples)
  render_esp:      avg 320us   max 510us   (144 samples)
  render_hud:      avg 45us    max 80us    (144 samples)
```

Interpretation:
- `update_entities` averages 1.84 ms — fine, well under the 2.5 ms update budget at 144 Hz
- But `max 4200us` is the spike to watch — a single 4.2 ms update *will* be visible if it lands on a render frame; this is the cold-page cost
- `render_esp` at 0.32 ms is healthy; `render_hud` at 45 µs is excellent

**Why:** Real numbers replace arguments. Without a profiler, every conversation about "is this fast enough" devolves into hand-wave. With one, you point at the bucket and either fix it or move on. The `max` column is more useful than the average — averages hide spikes that cause user-visible stutter.

---

## 4. Read Coalescing — The Single Biggest Win

**Cross-process memory reads dominate cost. Bundling 8 scalar reads from the same struct into one `read_memory` call is typically 5-10× faster.**

The entity loop is the canonical offender. Eight reads per entity, fifty entities = 400 cross-process reads per update. With page-warm reads at 3 µs each, that's 1.2 ms; cold, it's tens of ms.

```cpp
// SLOW — 8 reads per entity, each a separate kernel transition
void on_update(int64 data) {
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;
        g_cache[i].health    = g_proc.r32(ent + OFFSET_HEALTH);
        g_cache[i].team      = g_proc.r32(ent + OFFSET_TEAM);
        g_cache[i].position  = g_proc.read_vec3_fl32(ent + OFFSET_POSITION);
        g_cache[i].velocity  = g_proc.read_vec3_fl32(ent + OFFSET_VELOCITY);
        g_cache[i].view_yaw  = g_proc.rf32(ent + OFFSET_VIEW_YAW);
        g_cache[i].view_pit  = g_proc.rf32(ent + OFFSET_VIEW_PITCH);
    }
}

// FAST — one read per entity into a fixed buffer, parse in-script
struct entity_struct_layout {
    // Layout reflects the bytes at the entity base — adjust for your target.
    // Use [[packed]] if you depend on no padding.
} [[packed]];

void on_update(int64 data) {
    array<uint8> buf;
    buf.resize(0x200);                               // sized to span all fields you read

    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;

        // ONE read covering the whole entity record — single kernel transition
        if (!g_proc.read_memory(ent, buf, 0x200)) continue;

        // Parse from the local buffer — pure memory math, ~10x cheaper
        g_cache[i].health   = buf_read_i32(buf, OFFSET_HEALTH);
        g_cache[i].team     = buf_read_i32(buf, OFFSET_TEAM);
        g_cache[i].position = buf_read_vec3(buf, OFFSET_POSITION);
        g_cache[i].velocity = buf_read_vec3(buf, OFFSET_VELOCITY);
        g_cache[i].view_yaw = buf_read_f32(buf, OFFSET_VIEW_YAW);
        g_cache[i].view_pit = buf_read_f32(buf, OFFSET_VIEW_PITCH);
    }
}
```

Order of optimization (high impact to low):

1. **Coalesce per-entity scalar reads into struct-dumps.** Biggest single win for entity loops.
2. **Cache the view matrix once per update, share across entities.** Currently common to re-read per W2S call.
3. **Skip cold entities.** Read just the alive/team field first; if dead or friendly, skip the rest of the read.
4. **Bound entity counts.** A `MAX_ENTITIES = 64` cap on a list that's structurally bounded at 128 saves half the reads if many slots are empty.

**Why:** Cross-process reads are the dominant cost in any non-trivial script. A read-coalescing pass typically halves total CPU time of an entity-heavy script. The cost of structuring the read is a one-time `resize` and a handful of byte-offset getters — trivial relative to the win.

---

## 5. Cache What's Expensive to Get, Recompute What's Cheap

**Pattern scans, module bases, view matrix (across many entities) — cache. Colors, vec2s, format strings, font handles — recompute. Caching cheap things adds state without measurable savings.**

| Cache | Recompute |
|---|---|
| Pattern scan results (in `main()`, never again) | `color(r,g,b,a)` (4 bytes, stack-allocated, zero cost) |
| Module base / module size (until process re-attach) | `vec2(x, y)` (8 bytes, stack-allocated) |
| Resolved RIP addresses (until reload) | `get_font20()` (returns a cached handle internally) |
| View matrix once per update (shared across all W2S in this frame) | `format("{d}", n)` for short HUD text |
| Entity data in `g_cache` (the whole point of update/render separation) | World-to-screen result (it's just float math; do it where you need it) |
| Local player position once per frame (read in update, used by N features) | `is_key_down(VK_F)` (a cheap intrinsic; safe per-frame) |

Anti-cache (don't):

```cpp
// WRONG — caching a color "for performance"
color g_white;  // global state for zero gain
int64 main() {
    g_white = color(255, 255, 255, 255);
    return 1;
}

// RIGHT — construct fresh, no globals
void on_render(int64 data) {
    draw_text("HUD", vec2(10.0, 10.0), color(255, 255, 255, 255),
              get_font20(), 1, color(0, 0, 0, 180), 1.0);
}
```

Pro-cache:

```cpp
// View matrix — read once per update, reuse across N entities per render
float64 g_matrix[16];

void on_update(int64 data) {
    // 16 floats = 64 bytes in one read
    g_proc.read_memory(g_view_matrix_addr, g_matrix_buf, 64);
    // ... parse into g_matrix[16] ...
}

void on_render(int64 data) {
    for (int32 i = 0; i < g_entity_count; i++) {
        vec2 screen;
        if (world_to_screen(g_cache[i].position, g_matrix, screen)) {
            draw_circle(screen, 4.0, color(255, 0, 0, 255), 1.0, true);
        }
    }
}
```

**Why:** Caching cheap things makes the script harder to reason about (mutable globals, lifetime questions) for zero performance benefit. Caching expensive things (or things on cold paths) is the explicit purpose of rule #4 (update/render separation) — the whole point of "do it in update" is that the result lives until next update. Use that mechanism for what it's for; don't extend it to things that don't need it.

---

## 6. When to Break the Rule

**The budgets are steady-state targets. Bursts are fine. Don't split a one-frame initialization across ten frames to "meet budget" — the user-visible cost is the same and the code is worse.**

Legitimate bursts:

- **Initial process attach and sig resolution** in `main()` — can take 10-50 ms total, runs once, before the user starts using the overlay. Don't split.
- **First-frame entity cache fill** after a level load — a one-frame 5 ms spike that lets every subsequent frame run at 0.5 ms. Worth it.
- **Patch-day re-resolution** if you detect base address changed mid-session — let it stutter once.
- **Config save** on `on_unload` — file I/O takes ms; doesn't matter, the script is exiting.

Illegitimate bursts (these you DO need to fix):

- A pattern scan in a *callback* that fires periodically (should be in `main`)
- A `find_string_refs` or `struct_dump` call on the render thread (cold paths only)
- Allocating a 4 KB array inside `on_render` every frame (move to global, reuse the buffer)
- Calling `is_valid_address` on every pointer in a chain on every frame (validate at update time, cache the bool)

The test: if the user could feel the cost as a one-frame stutter, is it acceptable? A 50 ms stutter at script load is invisible (the overlay just appears 50 ms later). A 50 ms stutter mid-game is felt as a hitch.

**Why:** Performance work that makes the code uglier without changing the user-visible behavior is bad performance work. The framing of "everything must fit in 6.94 ms" applies to steady-state operation; setup, teardown, and event-driven one-shots get a pass. Save the optimization energy for the actual hot path.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | Know your budget | 16/8/7/4 ms at 60/120/144/240 Hz; render ≤ 1.5-2 ms, update ≤ 2.5-4 ms |
| 2 | Internalize per-call costs | Cross-process reads = expensive; draws and math = cheap |
| 3 | Profile with `mono_us` | Drop-in `profile_begin/end` with fixed buckets — measure before optimizing |
| 4 | Coalesce reads | One `read_memory` struct-dump replaces 8 scalar reads; biggest single win |
| 5 | Cache expensive, recompute cheap | Sigs, bases, matrix — yes; colors, vecs, fonts — no |
| 6 | Bursts are fine | Don't split one-shot setup across frames to "meet budget" |

**Cross-references:** `skill://game-cheat-guidelines` rules #4 and #7; `knowledge/common-patterns.md` for read-coalesced entity loops; `docs/enma/addon-time.md` for `mono_us` / `now_us`; `skill://pcx-patch-day-playbook` Step 5 (post-patch re-resolution that legitimately spends a frame budget).

---

## Source: `.claude/skills/pcx-patch-day-playbook/SKILL.md`

---
name: pcx-patch-day-playbook
description: >
  Ordered triage workflow for recovering a PCX script after a game update.
  Triggers when sigs return 0, reads return garbage after a patch, or the
  user says "broken", "updated", "patch day", "hotfix", "season drop", or
  "DLC dropped". Keeps diagnosis short and fixes targeted.
license: MIT
---

# Patch Day Playbook — Recovering After a Game Update

The ordered triage workflow for when a game update lands and your Perception.cx script stops working. This is the single most painful recurring scenario in scripting work; the cost is dominated by *not knowing what changed*, not by the re-RE itself. This playbook keeps the diagnosis short and the fix targeted.

**Trigger when:** the target game updated, sigs return 0, the script throws on first run after a patch, `ref_process().alive()` is fine but reads return garbage, or the user says any of: "broken", "updated", "patch day", "hotfix", "season drop", "DLC dropped".

**Prerequisite:** `knowledge/offset-methodology.md` for sig resolution mechanics, `tools/offset-diff.py` for batch sig diffing between binary versions, `tools/sig-uniqueness-checker.py` for re-sig validation. Also requires that you saved the previous-version binary and the working `offsets.em` *before* the update landed (see Step 1).

---

## Trigger

`.em` script suddenly throws on launch after a game update, overlay draws at (0,0), ESP renders no entities, sigs return 0, RIP-resolved addresses point outside the module, the user updates the game and runs the script and nothing works.

---

## 1. Snapshot the Broken State Before You Touch Anything

**Patch day is destructive. Save the old binary and old offsets before you do anything else. Diffing is impossible if you've already overwritten history.**

The single most common amateur mistake is "let me just update the offsets and see." Two hours later you can't remember what worked yesterday because everything is overwritten and the game's auto-updater wiped the old binary.

```
# Before any debugging — make a snapshot directory:
mkdir patch-2026-06-17

# 1. Copy the new game binary out (it's already on disk after the patch)
cp "C:/Games/MyGame/MyGame.exe" patch-2026-06-17/MyGame-new.exe

# 2. The OLD binary should already be in your previous snapshot dir.
#    If you don't have one, the lesson is: make one TODAY before the next patch.
#    The toolkit's `tools/offset-diff.py` needs both binaries to diff.

# 3. Save the last-known-good offsets:
cp scripts/offsets.em patch-2026-06-17/offsets-old.em

# 4. Save the broken script output for reference:
#    (in the IDE, copy the error trace; or run `check_script` and capture output)
```

**Why:** Without a snapshot, you're guessing what changed. With one, `offset-diff.py` and `radiff2` will tell you exactly which sigs moved, which are still valid, and which are gone. The 30 seconds of snapshotting saves the 2 hours of guesswork.

---

## 2. Run `tools/offset-diff.py` Before Editing Anything

**Most sigs survive a patch. You want to find the few that didn't — not re-do every one.**

The natural reflex is to open IDA on the new binary and start re-deriving offsets from scratch. Don't. The diff tool tells you in 30 seconds which sigs are intact, which moved (delta only — still resolvable), and which are gone (need re-sig).

```bash
# Build a JSON of named sigs once (reuse forever):
cat > sigs.json <<EOF
[
  {"name": "entity_list", "pattern": "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8", "kind": "rip", "rip_offset": 3, "insn_len": 7},
  {"name": "local_player", "pattern": "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 81", "kind": "rip", "rip_offset": 3, "insn_len": 7},
  {"name": "view_matrix",  "pattern": "48 8D 15 ?? ?? ?? ?? 48 8D 4C 24 ?? E8", "kind": "rip", "rip_offset": 3, "insn_len": 7}
]
EOF

# Diff:
python3 tools/offset-diff.py --old patch-old/MyGame.exe \
                              --new patch-new/MyGame.exe \
                              --sigs sigs.json
```

Read the output table top to bottom:

| Status | What it means | What to do |
|---|---|---|
| `UNCHANGED` | sig hits same address in both binaries | Nothing. Keep the offset. |
| `MOVED` | sig hits, but the resolved address differs (recompile shifted code) | Update the resolved address; sig itself is still good. |
| `LOST_IN_NEW` | sig hit old, doesn't hit new | Re-sig needed; instruction sequence changed. Go to Step 4. |
| `NEW_IN_NEW` | sig hit new but not old | Probably a typo in the old sig; ignore unless suspicious. |
| `MULTIPLE_HITS_OLD` / `MULTIPLE_HITS_NEW` | sig is ambiguous | Sig is too broad; tighten before trusting either result. Go to Step 4. |

**Why:** Triage before surgery. A patch typically moves 5-15% of sigs and breaks 1-3% outright. The diff tells you which 1-3% to spend the next hour on, instead of re-checking the 95% that survived.

---

## 3. Bisect the Cascade: Find the Earliest Failure, Not the Loudest

**A broken script after a patch shows ten errors. Nine of them are downstream of one bad pointer. Find the first one.**

Failure cascades trick you into chasing the wrong fix. The script log says "no entities drawn"; the actual cause is `g_entity_list = 0` because the *base address resolution* failed because the module name in the script changed (rare, but happens with engine version bumps). Fixing the entity-list sig won't help.

Bisect in dependency order:

```
1. Process attach   → ref_process("game.exe").alive() == true?
                      If false: process name changed? Anti-cheat blocking attach?
2. Base resolve     → get_module_base("game.exe") returns non-zero?
                      If 0: module renamed (e.g. CSGO → CS2 binary swap).
3. Module size      → get_module_size("game.exe") plausible (hundreds of MB)?
                      If wildly different: you're looking at the wrong binary.
4. First sig hit    → find_code_pattern returns non-zero for the FIRST sig you try?
                      If 0: the .text section may have moved (rare) or the binary
                      is encrypted/packed at runtime (e.g. Denuvo VM re-emergence).
5. RIP resolve      → resolved_addr is in [base, base+size]?
                      If outside: RIP math is wrong (Step 5).
6. Field reads      → ru64() on the resolved address returns non-zero?
                      If 0: pointer chain broken, struct layout changed.
```

Stop at the first failing step. Fix that. Re-run. Most of the cascade evaporates.

```cpp
// Tiny diagnostic harness — drop into main() temporarily:
int64 main() {
    proc_t p = ref_process("game.exe");
    if (!p.alive())                  { println("STEP 1 FAIL: process not attached"); return 0; }
    uint64 base = p.base_address();
    if (base == 0)                   { println("STEP 2 FAIL: no module base"); return 0; }
    uint64 size = p.get_module_size("game.exe");
    println(format("base={x} size={x}", base, size));

    uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0)                    { println("STEP 4 FAIL: entity_list sig stale"); return 0; }
    uint64 entity_list = resolve_rip(p, hit, 3, 7);
    if (entity_list < base || entity_list > base + size) {
        println(format("STEP 5 FAIL: rip resolve out of range: {x}", entity_list));
        return 0;
    }
    uint64 first = p.ru64(entity_list);
    println(format("first entity={x}", first));
    return 1;
}
```

**Why:** Without bisection you fix symptoms. You'll spend 30 minutes re-deriving an entity-list sig that was fine the whole time because the *real* failure was the module name. Bisection points the spotlight.

---

## 4. Re-Sig the Broken Ones with the Near-Miss Checker

**A sig that was unique yesterday may collide today, or vice versa. Don't trust your old sigs after a patch — validate.**

`tools/sig-uniqueness-checker.py` gives a verdict per sig: `UNIQUE`, `AMBIGUOUS`, `STALE`, `BRITTLE`. The `--near-misses N` flag is the killer feature on patch day — it scans for sigs whose first N bytes survive but trailing bytes drift, telling you exactly how to extend or narrow the wildcards.

```bash
# Verdict on every sig in your list:
python3 tools/sig-uniqueness-checker.py patch-new/MyGame.exe \
        --sig-file sigs.txt --near-misses 2

# Suppose this prints:
#   entity_list      UNIQUE      margin=5
#   local_player     STALE       near-miss: 48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 89
#                                           (last byte was 0x81, now 0x89 — struct offset shift)
#   view_matrix      AMBIGUOUS   3 hits — sig too broad; need 2-4 more bytes of context
```

For each broken sig:

1. **STALE with near-miss** → the instruction is still there but a register/offset byte changed. Update the sig (often a single byte) and retest.
2. **STALE with no near-miss** → the whole code path was rewritten. Go to the *xref* — find the function this sig was inside, find the new version in the patched binary by string xrefs or call patterns, derive a new sig from there.
3. **AMBIGUOUS** → tighten with 2-4 more bytes of leading or trailing context. Aim for `margin` between 2 and 6 — `margin=0` is brittle (one-byte change kills it), `margin>10` is overspecified (more likely to drift on the *next* patch).
4. **BRITTLE** (`margin=0`) → widen the sig until margin ≥ 2 even if the diff said it's fine — you got lucky this patch, you won't next time.

**Why:** Treating sigs as "either works or doesn't" misses the gradient. Most patch breakage is one-byte drift, which the near-miss check finds in seconds. Re-sigging from xrefs is the fallback when drift exceeds the threshold.

---

## 5. Re-Verify RIP-Relative Resolution After Every Sig Change

**Half of patch-day breakage is correct sig hits with wrong RIP math because the instruction length changed.**

A sig matching `48 8D 0D ?? ?? ?? ??` (7-byte `LEA rcx, [rip+disp]`) becomes `48 8B 0D ?? ?? ?? ??` (7-byte `MOV rcx, [rip+disp]`) — same length, same RIP math, fine. But a recompile can also turn a 7-byte `LEA r64, [rip+disp32]` into a 4-byte `LEA r64, [rip+disp8]` (small displacement form) — different length, different RIP math, your resolved address is now 3 bytes off. The script "works" but reads from the wrong location.

The check:

```cpp
// Always verify the resolved address lies inside the expected section.
// .text is executable code; data globals resolve to .data or .rdata.
uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
if (hit == 0) return 0;

int32 disp = p.r32(hit + 3);                  // displacement is 4 signed bytes
uint64 resolved = hit + 7 + cast<uint64>(disp); // 7 = total LEA instruction length

// Validation gate — if the resolved address points back into executable code,
// you almost certainly got the math wrong (most globals live in .data/.rdata):
if (resolved >= base && resolved < base + size) {
    // looks plausible; verify with a ru64 read and check the value shape
    uint64 first_field = p.ru64(resolved);
    println(format("resolved={x} first_field={x}", resolved, first_field));
} else {
    println(format("RIP resolve out of module: hit={x} disp={x} resolved={x}", hit, disp, resolved));
}
```

Patterns that change instruction length:

| From | To | Length delta | Common trigger |
|---|---|---|---|
| `LEA r64, [rip+disp32]` (7B) | `LEA r64, [rip+disp8]` (4B) | -3 | small-data global moved closer to code |
| `MOV r64, [rip+disp32]` (7B) | `MOV r64, mem` direct (10B) | +3 | global moved out of .rdata range |
| Standalone instruction | Instruction fused with prologue/epilogue change | varies | inliner heuristic changed in compiler |

**Why:** A wrong RIP math produces a perfectly plausible-looking address that's wrong by a small offset. Your reads return garbage that doesn't crash. You'll spend an hour blaming the struct layout for what's actually a 3-byte miscalculation in your resolver.

---

## 6. Validate End-to-End on the Live Target, Not Just "No Crash"

**Compile-clean is not the bar. Visible-correct on the live target is the bar.**

A script that doesn't crash and an overlay that draws *something* tells you almost nothing — every previous bug shipped the same way. Concrete validation:

```
End-to-end checklist after a patch fix:

[ ] Run the script on the live target (not a paused process)
[ ] Move the camera 90° — overlay tracks correctly?
[ ] Walk forward 10 meters — distance text updates plausibly?
[ ] Find a known entity (a teammate, a stationary object) — ESP box positioned over them?
[ ] Open the menu — every widget responds, no GUI freezes?
[ ] Run for 60 seconds without an exception — no late-binding errors?
[ ] Open the in-game scoreboard — entity count matches expected?
```

If you can't tick all seven, you're not done — keep bisecting.

**Why:** "It compiled" lulls you into the false sense of completion that costs you the next hour when a teammate reports the ESP is 50 pixels off. Five minutes of live verification on patch day is cheaper than any post-merge debugging.

---

## 7. Commit the Diff with a Changelog Note

**Every patch is data for the next patch. Record what moved, where it moved, and how you found it.**

A two-line note per patch turns into the most valuable file in your project after the third patch. It tells you which sigs are stable across patches (keep them), which drift every patch (rewrite from xrefs each time, don't bother updating in place), and which are version-tied (deprecate them entirely).

```
# patch-log.md
## 2026-06-17 — Game v1.42.3

### Moved
- view_matrix: +0x1C0 (recompile shift, sig still valid)
- local_player: +0x0 (no movement, listed for completeness)

### Re-sigged
- entity_list: old sig `48 8D 0D ?? ?? ?? ?? E8` matched at 3 places (ambiguous)
  new sig:     `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8` (margin=5)

### Lost — deprecated
- ammo_count: function inlined into shoot routine; not recoverable as a global,
              folded into per-weapon offset table

### Notes
- ETW Threat Intel callbacks (per anti-cheat-architecture.md) saw activity for
  the first time on this build — driver may have updated. Flag for review.
```

**Why:** Future-you needs this. The third patch when a sig regresses is when you'll discover that it's been brittle since v1.40 and you should rewrite it from xrefs once and for all instead of patching it again.

---

## Decision: When to Patch vs When to Re-RE from Scratch

Not every patch is a patch — sometimes the game shipped a real engine change and the old offsets are gone, not moved. Heuristics for when the playbook above doesn't apply and you need to start from `knowledge/offset-methodology.md` again:

| Signal | Likely cause | Action |
|---|---|---|
| Module name changed | Engine swap or major rebrand (CSGO → CS2) | Full re-RE; old offsets are reference-only |
| Module size changed >30% | Major engine update or large content drop with code refactor | Bisect aggressively; expect 30-50% sig loss |
| Most sigs `STALE` with no near-miss | Compiler upgrade (Clang version, LTO change) | Re-derive from xrefs; sigs based on RIP-relative globals usually survive better than register-allocation-sensitive ones |
| `IL2CPP` rebuild signal (Unity titles) | metadata.dat changed → entire struct layout rotated | Re-dump with IL2CPPDumper; use `tools/dumper-to-enma.py` to regenerate `offsets.em` |
| Schema system reset (Source 2 titles) | Schema registration order changed at runtime | Offsets are runtime-resolved; sigs for the schema getter are usually stable; revalidate the resolver, not the offsets |
| New anti-cheat driver loaded | AC vendor pushed an update | See `skill://anti-cheat-re` — driver behavior may have changed, not just code layout |

**The general rule:** if Steps 2-5 are fixing 70%+ of sigs with one-byte tweaks, you're in patch territory — keep going. If they're failing to find any near-misses for the broken sigs, you're in re-RE territory — close the playbook, open IDA, start over from the methodology.

---

## Summary

| # | Step | One-liner |
|---|---|---|
| 1 | Snapshot first | Save old binary, old offsets, error log before touching anything |
| 2 | Diff before editing | `offset-diff.py` triages which sigs survived, moved, lost |
| 3 | Bisect the cascade | Find the *first* failure, not the loudest |
| 4 | Re-sig with near-miss check | One-byte drift is the common case — find it in seconds |
| 5 | Re-verify RIP math | Instruction-length changes silently break resolved addresses |
| 6 | Live validation | Seven concrete in-game checks before declaring done |
| 7 | Patch log entry | Two lines per patch; the third patch will thank you |

**Decision:** if Steps 2-5 aren't recovering 70%+ of broken sigs, stop patching and re-RE from scratch via `knowledge/offset-methodology.md`.

**Cross-references:** `skill://pcx-re-discipline` (the rules of RE work), `knowledge/offset-methodology.md` (sig mechanics), `tools/offset-diff.py`, `tools/sig-uniqueness-checker.py`, `tools/dumper-to-enma.py` (for engines with structured dumpers).

---

## Source: `.claude/skills/re-evidence-log/SKILL.md`

---
name: re-evidence-log
description: >
  Discipline for recording why each offset and sig is trusted — the proof
  behind the offset table. Every offset added, every sig derived, every
  struct layout committed comes with a citable evidence entry. Always active
  during RE work; pairs with pcx-re-discipline and pcx-patch-day-playbook.
license: MIT
---

# RE Evidence Log — Every Claim Cites Its Proof

The discipline of recording *why* you trust each offset and sig in your project. The offset table is data; the evidence log is the proof behind it. Without the log, every patch day starts from zero on the same offsets you derived three months ago — you remember roughly what you did, not the citations that let you confirm it. This skill is the artifact half of `pcx-re-discipline` (which is the discipline itself) and the input to `pcx-patch-day-playbook` Step 7 (which writes a per-patch entry into the log).

**Always active when doing RE work.** Every offset you add, every sig you derive, every struct layout you commit to the project comes with an evidence entry. The cost is one paragraph per claim; the payoff is being able to answer "why do we trust this?" three months later without re-reversing.

**Prerequisite:** `skill://pcx-re-discipline` for the underlying discipline rules; `knowledge/offset-methodology.md` for the sig-derivation mechanics the log entries reference; `tools/sig-uniqueness-checker.py` for the verdict you record alongside each sig.

---

## Trigger

Starting RE work on a new binary, adding an offset to `offsets.em`, committing a struct layout to a feature, recovering from a patch (the patch-day skill produces a log entry), onboarding a teammate to existing offsets, code-review of RE claims, suspicious behavior in a script you wrote weeks ago and can't remember why a field is at +0x40.

---

## 1. One File per Binary, One Entry per Claim

**The canonical layout: `evidence/<binary-hash-prefix>.md`, one file per binary you reverse, one numbered entry per claim.** Filed by content hash, not by game name or version — the same game across patches produces different binaries with different hashes; each gets its own file.

```
project/
├── globals.em
├── offsets.em
├── ...
└── evidence/
    ├── README.md                          ← what's in here, naming convention
    ├── 7a3f4d1c-game-v1.42.3.md           ← per-binary log
    ├── 7a3f4d1c-game-v1.42.3.sha256       ← cached hash for trivial verification
    ├── 9b2e8a07-game-v1.42.4.md           ← next patch = new file
    └── archive/                           ← old entries kept for diffing
        └── 7a3f4d1c-game-v1.42.3.md
```

Inside one file, each claim is its own section:

```markdown
# Evidence Log — game.exe v1.42.3
SHA-256: 7a3f4d1c8e2b5a019f3d4c7e2b1a8f6d...
Module size: 158,720,000 bytes (.text 0x00400000–0x00C12000)
First verified: 2026-06-15
Last verified: 2026-06-17

## E-001 — entity_list global pointer
## E-002 — local_player slot
## E-003 — view matrix (4x4 row-major)
## E-004 — CEntity::m_iHealth field offset
## E-005 — CEntity::m_vecOrigin field offset
...
```

Entry IDs (`E-001` … `E-NNN`) are stable across patches — `offsets.em` references them in comments (`// E-003`), so when you rewrite the offset for the next version, you keep the same ID and update the per-version file. The ID is the cross-reference; the file is the version-specific evidence.

**Why:** Without a per-binary file, you can't diff what changed between patches. Without numbered entries, you can't reference a claim from your code or a teammate's review. The file naming by hash means the system survives renames, re-downloads, and side-by-side comparison.

---

## 2. Every Claim Cites: Binary, Address, Xref Source, Last-Verified Date

**The minimum citation per entry. Anything shorter is a vague memory dressed up as a fact.**

The required fields per entry:

| Field | Why |
|---|---|
| `id` | Stable cross-reference for `offsets.em` and patch logs |
| `name` | Human-readable label (matches the constant in `offsets.em`) |
| `binary_hash` | The binary this claim is verified against |
| `rva` (or `sig`) | Where the thing is |
| `xref_source` | Function symbol, sig pattern, or string xref that found it |
| `derived_via` | How: pattern scan? SDK header lookup? Struct dump? |
| `last_verified` | Date of the most recent successful run on this binary |
| `verified_against` | The in-game observation that confirmed it works |

```markdown
## E-001 — entity_list global pointer

| Field             | Value |
|---|---|
| name              | `OFF_ENTITY_LIST` |
| kind              | RIP-relative pointer (loaded by LEA) |
| rva               | 0x04A2B100  (resolved from sig hit at 0x00872F40) |
| sig               | `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8` |
| sig_uniqueness    | UNIQUE (margin=5, per `tools/sig-uniqueness-checker.py`) |
| xref_source       | Called by `CGameWorld::Update`, identified via string xref "entity_list_full" |
| derived_via       | Pattern scan + RIP resolve (disp@+3, insn_len=7) |
| last_verified     | 2026-06-17 |
| verified_against  | ESP showed 12 entities in a match; entity count matched scoreboard |
```

WRONG — the kind of "evidence" that's actually nothing:

```markdown
## entity_list
Found in some function, +0x18 or +0x20, I think? Worked last time I checked.
```

This will cost you an hour the next time you touch it.

RIGHT — every field present, every claim verifiable:

```markdown
## E-001 — entity_list
hash 7a3f4d1c..., rva 0x04A2B100, sig "48 8D 0D ?? ...", from CGameWorld::Update,
verified 2026-06-17 against the scoreboard entity count.
```

The detail level is up to you — a table per entry or a single dense line — but the *fields* are mandatory.

**Why:** Three months from now, you will not remember which function you found this in. The patch-day playbook Step 4 (re-sig with near-miss) needs the original `derived_via` to know what the sig was trying to match. A teammate reviewing your offsets needs `xref_source` to know where to look themselves. The `last_verified` date is the brittleness signal (rule #5).

---

## 3. Sigs Cite the Disassembly They Were Derived From

**A sig alone is a number. A sig with its disassembly context is a hypothesis you can re-derive.** When the sig breaks, the disassembly tells you what the instruction *was*, so you can find what it *became* in the patched binary.

Format: the sig as a literal, then a small fenced block of the instructions it covers, then a one-line explanation of which bytes are wildcarded and why.

```markdown
## E-001 — entity_list (sig derivation)

sig: `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8`

Derived from (game.exe v1.42.3, at .text+0x00872F40):
    48 8D 0D 5B 80 1B 04       LEA  rcx, [rip+0x041B805B]   ; -> &g_entity_list
    E8 2A 4F 12 00             CALL CGameWorld::Lookup       ; ret in rax
    48 8B D8                   MOV  rbx, rax                 ; save list ptr

Wildcards:
  - bytes 3..6   (4-byte RIP disp32 in the LEA — relocatable)
  - bytes 8..11  (4-byte CALL target relative disp — relocatable)
Total signature length: 15 bytes.
Unique-match verdict at derivation time: UNIQUE (margin=5).
```

When this sig later returns 0 after a patch, you have *exactly* what to look for in the new binary: a `LEA rcx, [rip+disp]` immediately followed by a `CALL` and `MOV rbx, rax`, near the same string xref ("entity_list_full") that originally led you here.

**Why:** A bare hex string strips out everything you knew when you wrote it. The disassembly preserves the *intent*: this is the LEA that loads the entity-list pointer into RCX, called immediately. If the compiler changed `MOV` to `LEA` in the patch (different opcode, different sig), you still know what to look for.

---

## 4. Struct Layouts Cite SDK Header AND In-Memory Verification

**Most struct layouts are partially known: some fields come from a community SDK header, others from your own struct dumping, others from guessing. Flag which are which.**

When a struct layout is wrong, the bug is silent — your script reads garbage that doesn't crash. The cost of being wrong is high; the cost of citing your source per field is two lines.

```markdown
## E-004 — CEntity struct layout (partial)

source: `r5sdk/include/game/server/entity.h` (commit 8a4c2e7, fetched 2026-06-10)
in-memory verification: 2026-06-17, walked g_entity_list[0..3] in a live match

| offset  | size | field         | source              | confidence |
|---------|------|---------------|---------------------|------------|
| 0x0000  | 8    | vtable_ptr    | SDK header          | HIGH       |
| 0x0008  | 4    | netvar_id     | SDK header          | HIGH       |
| 0x0040  | 4    | m_iHealth     | SDK header          | HIGH       |
| 0x0044  | 4    | m_iMaxHealth  | SDK header          | HIGH       |
| 0x00F0  | 4    | m_iTeamNum    | SDK header          | HIGH       |
| 0x0170  | 12   | m_vecOrigin   | SDK header          | HIGH       |
| 0x017C  | 12   | m_vecVelocity | OBSERVED (struct dump, three entities, values match expected ranges) | MEDIUM |
| 0x0188  | 4    | m_flAimYaw    | GUESS (correlated with on-screen view direction) | LOW |
| 0x1234  | 8    | m_pPlayerCtl  | GUESS (looks like a pointer; value is within module range) | LOW |
```

Three confidence tiers, three response policies:

- `HIGH` — SDK-cited or directly observed. Use without ceremony.
- `MEDIUM` — observed but not SDK-confirmed. Flag in `offsets.em` with a one-line comment.
- `LOW` — guess. Mark `UNVERIFIED` per `game-cheat-guidelines` rule #1. Treat reads as suspect; cross-validate (e.g. compare the supposed `m_flAimYaw` against the on-screen view direction over 100 frames before trusting it).

When code-reviewing, the question "where did you get this field?" is answered by looking at the table.

**Why:** Partial-layout bugs are the worst class of RE error. The script "works" — it draws ESP, it reads health, it pulls coords — but one field is wrong and the feature using that field silently produces garbage. Marking confidence per field makes the wrong-field call inspectable instead of invisible.

---

## 5. Update the Verified-On Date After Every Successful Run

**The age of the last verification is the brittleness signal. A sig last verified six months ago is more suspect than one verified yesterday, even if both are technically "in the log."**

The discipline: at the end of any session where the script ran correctly against the live target, walk through the log and bump `last_verified` for every claim that was actually exercised. Five seconds of editing per session.

```markdown
## E-001 — entity_list
last_verified: 2026-06-17  ← yesterday, fresh
last_verified: 2026-04-02  ← two months old, recheck before trusting
last_verified: 2025-12-15  ← six months — assume stale; revalidate or re-derive
```

At code-review time or before a release, sort entries by age:

```bash
# rough one-liner — adapt to your log format
grep -E '^last_verified:' evidence/*.md | sort -k2 | head -10
```

The oldest entries are the next ones to verify (or retire if they're no longer used by any feature).

A second related discipline: when you add a NEW claim, also list which claims it *depends on*. If E-006 is "`CEntity::m_pPlayer` reads `CPlayer` at the pointed address" and `CPlayer`'s layout is E-007, then E-006's evidence cites "depends on E-007." When E-007 becomes stale, the dependent claim is suspect too.

**Why:** Without freshness tracking, every entry has the same epistemic weight, which is wrong. A six-month-old "I verified this once" is closer to a guess than to fresh evidence. Dating gives you a triage signal for free, the cost of which is one date edit per session.

---

## 6. Cite Negative Results Too

**"Tried sig X, returned 0; tried sig Y, returned 3 hits; settled on sig Z" is data. Future-you debugging a regression needs to know what's *already been ruled out*.**

Most evidence logs record only the *successful* derivation. The next time the sig breaks and you reach for one of the *other* candidates you ruled out months ago, you'll re-rule it out again — costing the same hour.

Format: under each entry, a brief "Considered and rejected" subsection.

```markdown
## E-001 — entity_list

[main entry as above]

### Considered and rejected
- Sig `48 8B 0D ?? ?? ?? ??` (just the MOV form): too short, matched 47 places in .text.
- Hardcoded offset 0x04A2B100: that's the resolved address from THIS binary; will not
  survive a patch. Kept as the resolved value but the sig is the canonical source.
- Walking from `CGameWorld::Init` (xref candidate): the init function is in .data
  and gets re-inlined per build; brittle xref starting point.
- Reading PEB.LdrData to find a "game module" data segment: technically possible
  but adds a per-frame cost we don't want.
```

The same pattern applies to struct layout dead-ends ("field at +0x180 looked like a vec3 origin but the values were screen-space coords, not world; it's actually the last frame's m_vecOldPosition") and to struct-walking dead-ends ("the second pointer in this list is null in solo play; only populated in team modes — don't use as a liveness check").

**Why:** Negative results are the second-most-valuable thing in the log after positive ones. A teammate looking at this log can immediately see "ah, the obvious short sig is ambiguous — that's why we have a long one." The cost of recording is one line; the cost of not recording is rediscovery.

---

## Template

Drop-in skeleton for `evidence/<hash>.md` — copy, fill in:

```markdown
# Evidence Log — <binary_name> <version>

SHA-256: <full hash>
Module size: <bytes>  (.text <start>–<end>)
First verified: <YYYY-MM-DD>
Last verified: <YYYY-MM-DD>

Cross-reference: this file lists entries E-001..E-NNN; each entry's ID is
stable across patches and is referenced from `offsets.em` and `patch-log.md`.

---

## E-001 — <short name matching offsets.em constant>

| Field             | Value |
|---|---|
| name              | `OFF_X` |
| kind              | <RIP-relative pointer / direct address / field offset / sig> |
| rva               | <0x...> (resolved from sig hit at <0x...>) |
| sig               | `<bytes>` |
| sig_uniqueness    | <UNIQUE margin=N / AMBIGUOUS / etc per sig-uniqueness-checker.py> |
| xref_source       | <function, string xref, or other anchor> |
| derived_via       | <pattern scan + RIP resolve / SDK header / struct dump / xref walk> |
| last_verified     | <YYYY-MM-DD> |
| verified_against  | <in-game observation that confirmed it works> |
| depends_on        | <E-NNN, E-NNN — or "none"> |

Disassembly context (for sigs):
    <4-6 lines of asm covering the matched bytes; wildcards explained below>

Wildcards:
  - bytes A..B  (<what relocatable thing they cover>)

### Considered and rejected
- <alternative sig / approach / source>: <why it didn't pan out>

---

## E-002 — ...
```

A second template for struct entries:

```markdown
## E-NNN — <StructName> layout (<partial|complete>)

source: <SDK header path or "self-derived">
in-memory verification: <date>, <how many instances walked>

| offset | size | field | source | confidence |
|--------|------|-------|--------|------------|
| 0x0000 | 8    | vtable_ptr | SDK / observed | HIGH |
| ...    |      |       |        |            |

### Considered and rejected
- <field-shape alternative>: <why rejected>
```

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | One file per binary, one entry per claim | Stable IDs (E-NNN) cross-reference `offsets.em` and patch logs |
| 2 | Cite binary + address + xref + date | Six fields mandatory per entry; vague memory is not evidence |
| 3 | Sigs cite their disassembly | The intent of the sig is the hypothesis you re-derive from |
| 4 | Structs cite source + verification per field | HIGH / MEDIUM / LOW confidence tiers; LOW = `UNVERIFIED` in code |
| 5 | Update `last_verified` per successful run | Age is the brittleness signal — six months old is suspect |
| 6 | Cite negative results too | "Tried and rejected" prevents the next person re-deriving the same dead end |

**Cross-references:** `skill://pcx-re-discipline` (the discipline rules), `skill://pcx-patch-day-playbook` (Step 7 writes a per-patch log entry), `knowledge/offset-methodology.md` (the mechanics being cited), `tools/sig-uniqueness-checker.py` (produces the `sig_uniqueness` field value), `tools/offset-diff.py` (per-patch diff feeds the negative-results section).

---

## Source: `knowledge/angelscript-cheatsheet.md`

# Perception AngelScript Cheat Sheet

Use this for current production `.as` scripts. Verify every symbol with `pcx api <symbol> --lang angelscript` or MCP `api_lookup(symbol, "angelscript")` before final code.

## Official source set

The Perception AngelScript docs are the source of truth:

- Overview: `https://docs.perception.cx/perception/angel-script/overview.md`
- Life Cycle: `https://docs.perception.cx/perception/angel-script/life-cycle.md`
- Engine: `https://docs.perception.cx/perception/angel-script/engine.md`
- Atomic Types: `https://docs.perception.cx/perception/angel-script/atomic-types.md`
- Unicorn: `https://docs.perception.cx/perception/angel-script/unicorn.md`
- Render API: `https://docs.perception.cx/perception/angel-script/render-api.md`
- Input API: `https://docs.perception.cx/perception/angel-script/input-api.md`
- Proc API: `https://docs.perception.cx/perception/angel-script/proc-api.md`
- Mutex API: `https://docs.perception.cx/perception/angel-script/mutex-api.md`
- GUI API: `https://docs.perception.cx/perception/angel-script/gui-api.md`
- System API: `https://docs.perception.cx/perception/angel-script/system-api-cpu-and-disassembly.md`
- Net API: `https://docs.perception.cx/perception/angel-script/net-api.md`
- File System: `https://docs.perception.cx/perception/angel-script/file-system.md`
- Extended Math API: `https://docs.perception.cx/perception/angel-script/extended-math-api.md`
- Win API: `https://docs.perception.cx/perception/angel-script/win-api.md`
- Engine Specific API: `https://docs.perception.cx/perception/angel-script/engine-specific-api.md`
- Json API: `https://docs.perception.cx/perception/angel-script/json-api.md`
- Utilities: `https://docs.perception.cx/perception/angel-script/utilities.md`
- Zydis Encoder: `https://docs.perception.cx/perception/angel-script/zydis-encoder.md`
- Intrinsics: `https://docs.perception.cx/perception/angel-script/intrinsics.md`
- Sound API: `https://docs.perception.cx/perception/angel-script/sound-api.md`
- Bit Reinterpret Helpers: `https://docs.perception.cx/perception/angel-script/bit-reinterpret-helpers.md`

## Lifecycle

```cpp
int main()
```

Return `> 0` to stay loaded. Return `<= 0` to unload. Register recurring work instead of looping forever in `main()`.

```cpp
void on_tick(int id, int data_index)
{
    // work here
}

int main()
{
    register_callback(on_tick, 16, 0);
    return 1;
}

void on_unload()
{
    // cleanup here
}
```

## Language rules

- Use AngelScript containers: `array<T>`, `dictionary`, `any`.
- Use `string` for text unless an API page documents another type.
- Do not use Enma-only `vec2(...)`, `color(...)`, `T[]`, `map<K,V>`, `imap<V>`, `cast<int64>(fn)`, or `register_routine(...)` in `.as` code.
- Do not use Lua syntax or JavaScript async helpers.

## Render rules

AngelScript Render API calls use the exact scalar/value shapes documented on the AngelScript Render API page. Common Enma wrappers such as `vec2(x, y)` and `color(r, g, b, a)` are wrong in `.as` unless an AngelScript page explicitly documents that value type.

Example text draw shape:

```cpp
draw_text("PCX", 20, 20, 255, 255, 255, 255, get_font20(), TE_SHADOW, 0, 0, 0, 180, 1.0f);
```

## Proc rules

Use `proc_t` and `uint64` addresses. Always release acquired process handles with `deref()` when done or inside `on_unload()`.

```cpp
proc_t p = ref_process("game.exe");
if (p.pid() == 0)
{
    log("process not found");
    return 0;
}
uint64 base = p.base_address();
p.deref();
```

## Verification commands

```bash
pcx api draw_text --lang angelscript
pcx symbol-check script.as
pcx verify script.as
```

---

## Source: `knowledge/aimbot-math.md`

# Aimbot Math Reference

> **Scope:** Educational math reference for PCX cheat development. Authorized targets only.

This is the math companion to [`common-patterns.md`](common-patterns.md). That file
covers the *render* half — world-to-screen, boxes, snaplines, radar — plus a single
`calc_angle` / `smooth_angle` teaser. The README promises "angle calc, smooth interp"
for the aim half; this file is where that math actually lives. Everything below builds
on the Enma idioms already established in `common-patterns.md`: `uint64` addresses,
`proc_t` reads, `vec3` field access (`.x` / `.y` / `.z`, no getter parens), and the
`(180.0 / PI)` degree conversion used by `calc_angle`.

Code blocks honor the 12 [`game-cheat-guidelines`](../.claude/skills/game-cheat-guidelines/SKILL.md):
`uint64` addresses, caller null-guards every read, scan stays out of render, and the one
feature that writes memory (no-recoil, angle writeback) writes the minimum bytes. Offsets
appear as bare symbolic identifiers (`OFF_VELOCITY`, resolved in `offsets.em`) exactly as
`common-patterns.md` does — never a version-specific hex literal.

```cpp
// Shared throughout this reference. Matches common-patterns.md calc_angle.
const float64 PI = 3.14159265358979;
const float64 RAD2DEG = 180.0 / PI;
const float64 DEG2RAD = PI / 180.0;
```

## Angles: yaw and pitch from two world points

The aimbot's core question — "what view angles point my camera at that target?" — answers with
two `atan2` calls. This is `calc_angle` from `common-patterns.md`, restated with the convention
spelled out:

```cpp
// Returns (pitch, yaw) in degrees. Source-engine convention (z = up).
vec2 calc_angle(vec3 src, vec3 dst) {
    vec3 delta = dst.sub(src);                          // dst - src
    float64 dist_xy = sqrt(delta.x * delta.x + delta.y * delta.y);
    float64 pitch = atan2(-delta.z, dist_xy) * RAD2DEG; // up = negative pitch
    float64 yaw   = atan2(delta.y, delta.x) * RAD2DEG;
    return vec2(pitch, yaw);                             // vec2.x = pitch, vec2.y = yaw
}
```

**Output range.** `atan2` returns `(-PI, PI]`, so pitch and yaw come out in `(-180, 180]` — the
range Source-family games store. If your engine stores yaw in `[0, 360)`, normalize *on
writeback*, not here; the delta math below wraps either input correctly.

**Pitch sign is engine-specific and trips everyone.** `atan2(-delta.z, dist_xy)` produces
a *negative* pitch when the target is above you (`delta.z > 0`). That matches Source, where
looking up is negative pitch. Other engines flip this:

| Engine          | Angle storage           | Up is...        | Yaw zero axis | Handedness |
| --------------- | ----------------------- | --------------- | ------------- | ---------- |
| Source / Source2| `QAngle{pitch,yaw,roll}`, degrees | negative pitch | +X | left, z-up |
| Unreal (UE4/5)  | `FRotator{Pitch,Yaw,Roll}`, degrees | positive pitch | +X | left, z-up |
| Unity           | Euler degrees / quaternion | positive pitch | +Z | left, y-up |

For Unreal, drop the negation: `pitch = atan2(delta.z, dist_xy) * RAD2DEG`. For Unity the "up"
axis is `y`, so `dist_xy` is the XZ-plane distance and pitch keys off `delta.y`.

## Angle deltas — the wrap-around trap

You never write absolute angles into a smoothing loop; you work with the *delta* from your
current view to the target. Subtracting two angles naively breaks at the seam where the
range wraps.

Suppose your current yaw is `350°` and the target is at `10°`. The shortest turn is `+20°`
(swing right through `360°/0°`). But `target - current = 10 - 350 = -340°` tells the
aimbot to spin almost all the way around the other direction. Symmetrically, current `10°`
to target `350°` should be `-20°`, not `+340°`.

The fix maps any delta into `[-180, 180)`:

```cpp
// Normalize an angle delta (degrees) to the shortest signed path in [-180, 180).
float64 normalize_delta(float64 delta) {
    return fmod(delta + 540.0, 360.0) - 180.0;
}
```

**Why `+540`, not `+180`?** `540 = 360 + 180`. Enma's `fmod` follows C semantics: the
result takes the sign of the dividend, so `fmod(-340.0, 360.0)` is a *negative* `-340`, not
`20`. Offsetting by `540` guarantees the argument is positive for any delta in `[-360, 360]`
(`delta + 540` lands in `[180, 900]`), so `fmod` stays positive, and the trailing `- 180`
re-centers it. Verify:

```
normalize_delta(-340) = fmod(200, 360) - 180 = 200 - 180 = +20   // 350 -> 10, correct
normalize_delta(+340) = fmod(880, 360) - 180 = 160 - 180 = -20   // 10 -> 350, correct
normalize_delta(+10)  = fmod(550, 360) - 180 = 190 - 180 = +10   // no wrap, unchanged
```

Apply it to yaw on every frame. Pitch does **not** wrap (it is clamped to roughly
`[-89, 89]`), so clamp pitch instead of wrapping it:

```cpp
vec2 angle_delta(vec2 current, vec2 target) {
    float64 dp = fclamp(target.x - current.x, -89.0, 89.0);  // pitch: clamp, no wrap
    float64 dy = normalize_delta(target.y - current.y);      // yaw: wrap
    return vec2(dp, dy);
}
```

## FOV cone check — "is the target in screen FOV"

Two formulations. They answer slightly different questions; pick by what you already have.

**3D angle cone (dot product).** Use this when you have view angles and world positions and
have *not* run world-to-screen yet (cheaper — no matrix multiply). Build the view-forward
unit vector from your angles, build the unit direction to the target, and compare their dot
product against `cos(fov)`:

```cpp
// Forward unit vector from Source-convention view angles (degrees).
vec3 angles_to_forward(float64 pitch_deg, float64 yaw_deg) {
    float64 p = pitch_deg * DEG2RAD;
    float64 y = yaw_deg * DEG2RAD;
    float64 cp = cos(p);
    return vec3(cp * cos(y), cp * sin(y), -sin(p));  // -sin(p): up = negative pitch
}

// True if target sits within `fov_deg` half-angle of where the camera looks.
bool in_fov_cone(vec3 eye, vec2 view_angles, vec3 target, float64 fov_deg) {
    vec3 fwd = angles_to_forward(view_angles.x, view_angles.y);  // already unit length
    vec3 dir = target.sub(eye).normalize();
    float64 cos_limit = cos(fov_deg * DEG2RAD);
    return fwd.dot(dir) >= cos_limit;   // larger dot = smaller angle = inside cone
}
```

The dot of two unit vectors is `cos(angle_between)`. A wider FOV means a *smaller*
`cos_limit`, so the `>=` test loosens as `fov_deg` grows — exactly what you want.

**2D screen-space (pixel radius).** Use this when you already projected the target with
`world_to_screen` (from `common-patterns.md`). FOV becomes a pixel circle around the
crosshair (screen center):

```cpp
// True if the projected target is within `radius_px` of the crosshair.
bool in_fov_screen(vec2 target_screen, float64 radius_px) {
    float64 cx = get_view_width()  * 0.5;
    float64 cy = get_view_height() * 0.5;
    float64 dx = target_screen.x - cx;
    float64 dy = target_screen.y - cy;
    return (dx * dx + dy * dy) <= (radius_px * radius_px);  // squared: no sqrt needed
}
```

**Which to use.** The screen form is intuitive (a circle the user tunes in pixels) and honors
the game's real FOV/zoom for free since the projection already did. The 3D cone needs no
projection and works for off-screen targets, so it is the better gate for a closest-target
search over the full entity list. Many aimbots use the cone to *select* and the circle to
*display* the FOV ring.

## Closest target selection

Once the FOV gate passes, rank the survivors and pick one. Four metrics, increasing cost
and increasing "feel":

**By screen distance (2D).** Pixels from crosshair. Cheapest after projection; matches what
the player sees. This is what most "FOV aimbots" use:

```cpp
float64 score_screen(vec2 target_screen) {
    float64 dx = target_screen.x - get_view_width()  * 0.5;
    float64 dy = target_screen.y - get_view_height() * 0.5;
    return dx * dx + dy * dy;   // squared px; smaller = closer to crosshair
}
```

**By angular distance (3D).** The turn the aimbot must make, in degrees. Independent of FOV
zoom and screen resolution. Reuse `angle_delta`:

```cpp
float64 score_angular(vec2 view_angles, vec2 target_angles) {
    vec2 d = angle_delta(view_angles, target_angles);
    return sqrt(d.x * d.x + d.y * d.y);   // degrees of correction needed
}
```

**By world distance.** Closest in meters (`distance_3d` from `common-patterns.md`). Useful for
melee/shotgun logic, but a distant target dead-center beats a close one at the screen edge, so
world distance alone aims poorly.

**Hybrid weighted.** Prefer targets both near the crosshair *and* close. Normalize each term to
`[0, 1]` against its max, then weight:

```cpp
// Lower score wins. ang_w + dist_w should sum to 1.0.
float64 score_hybrid(float64 ang_deg, float64 max_ang,
                     float64 world_dist, float64 max_dist,
                     float64 ang_w, float64 dist_w) {
    float64 ang_n  = fclamp(ang_deg    / max_ang,  0.0, 1.0);
    float64 dist_n = fclamp(world_dist / max_dist, 0.0, 1.0);
    return ang_w * ang_n + dist_w * dist_n;
}
```

Worked example (`ang_w=0.7`, `dist_w=0.3`, `max_ang=30°`, `max_dist=3000`): target A (`5°` at
`2500`) → `0.7*(5/30)+0.3*(2500/3000)=0.367`; target B (`15°` at `400`) → `0.390`. A wins, the
smaller turn dominates. Bias toward angle for twitchy aim, toward distance to lock the nearest.

Selection loop picks the minimum score over the validated, in-FOV set:

```cpp
int32 best = -1;
float64 best_score = 1.0e30;
for (int32 i = 0; i < g_candidates.length(); i++) {
    float64 s = score_hybrid(g_ang[i], 30.0, g_dist[i], 3000.0, 0.7, 0.3);
    if (s < best_score) { best_score = s; best = i; }
}
```

## Target validation gate

Selecting a target is worthless if it is dead, friendly, or behind a wall. Run an **ordered**
checklist — cheap field reads first, the expensive line-of-sight trace last — and bail at the
first failure so you never trace a target you already rejected. (Separate scan from render:
this runs in `on_update`, not `on_render`.)

```cpp
bool is_valid_target(proc_t& p, uint64 ent, vec3 eye, vec3 target_pos,
                     int32 local_team, float64 max_dist) {
    // 1. Alive (one int read — cheapest).
    if (p.r32(ent + OFF_HEALTH) <= 0) return false;

    // 2. Enemy team (one int read).
    if (p.r32(ent + OFF_TEAM) == local_team) return false;

    // 3. In range (no read; pure math on cached positions).
    if (target_pos.distance(eye) > max_dist) return false;

    // 4. Not smoked / flag-gated (one read; engine-specific flags).
    if ((p.ru32(ent + OFF_FLAGS) & FLAG_BLOCKED) != 0) return false;

    // 5. Visible — line of sight. The expensive check goes LAST.
    //    Prefer the engine's per-bone visible flag when it exists (one read);
    //    fall back to a ray trace only when it doesn't.
    if (p.r32(ent + OFF_VISIBLE) == 0) return false;

    return true;
}
```

**Ordering rationale.** Checks 1-4 are single integer reads or cached-position math —
nanoseconds. A visibility *trace* (casting a ray through the game's collision world, or
calling its `TraceLine`) is orders of magnitude more expensive and may require a write to set
up trace parameters. Gate it behind everything cheaper. If the engine exposes a
`m_bSpotted` / visible-bone bitmask (a plain read), prefer that over a trace entirely — it is
both cheaper and quieter. Offsets shown (`OFF_HEALTH`, `OFF_TEAM`, `OFF_FLAGS`, `OFF_VISIBLE`)
resolve in `offsets.em`; mark any you guessed `// UNVERIFIED` per guideline 12.

## Prediction — basic linear

Bullets are not hitscan in most games; they take time to arrive, and the target keeps moving.
Linear prediction extrapolates the target along its velocity by the bullet's travel time:

```
predicted = target_pos + target_vel * t,   where t = distance / bullet_speed
```

The catch: `distance` depends on where you aim, which depends on `t`, which depends on
`distance`. Solve it with a couple of fixed-point iterations — each pass refines `t` using
the previous pass's aim point. Two or three iterations converge for any reasonable speed:

```cpp
vec3 predict_linear(proc_t& p, uint64 ent, vec3 eye, vec3 target_pos, float64 bullet_speed) {
    vec3 vel = p.read_vec3_fl32(ent + OFF_VELOCITY);   // units/sec; read once
    vec3 aim = target_pos;
    for (int32 i = 0; i < 3; i++) {
        float64 t = aim.distance(eye) / bullet_speed;  // bullet flight time
        aim = target_pos.add(vel.scale(t));            // target_pos + vel*t
    }
    return aim;
}
```

**Getting bullet speed is game-dependent.** It is not a universal constant — it is per-weapon
muzzle velocity, often stored on the active weapon entity or a weapon-data table:

- **Source / Source2:** weapon script `CSWeaponData` / `WeaponInfo` exposes a projectile or
  muzzle speed; some weapons are hitscan (treat `t = 0`). Read the active weapon, then its
  data pointer.
- **Unreal:** the projectile class's `InitialSpeed` on `ProjectileMovementComponent`.
- **Generic:** if you cannot find a field, measure it — fire once at a wall a known distance
  away and time the impact, then hardcode per-weapon (and re-measure after patches).

Velocity itself comes from the target's movement field (`OFF_VELOCITY`, frequently
`m_vecVelocity`). If the game only stores positions, derive velocity as
`(pos_this_frame - pos_last_frame) / frametime` in `on_update`.

## Prediction — gravity-aware

When the projectile arcs (grenades, arrows, tank shells, Apex sniper drop), linear prediction
under-aims: you must both *lead* the moving target and *raise* the aim to fight gravity.

**Step 1 — intercept time against a moving target.** Treat the projectile as traveling at
constant speed `s` (handle the arc as a separate vertical correction). Let `pRel =
target_pos - shooter_pos` and `vt = target_vel`. The projectile reaches the target when the
straight-line distance it has flown equals the moving target's distance:

```
|pRel + vt*t| = s*t
```

Square both sides and group by powers of `t`:

```
(vt·vt - s²) t² + 2(pRel·vt) t + (pRel·pRel) = 0
       a              b               c
```

A standard quadratic. Take the **smallest positive** root (earliest interception):

```cpp
// Returns intercept time t > 0, or -1.0 if no real solution (target outruns projectile).
float64 intercept_time(vec3 p_rel, vec3 vt, float64 s) {
    float64 a = vt.dot(vt) - s * s;
    float64 b = 2.0 * p_rel.dot(vt);
    float64 c = p_rel.dot(p_rel);

    if (fabs(a) < 0.0001) {                 // target speed == projectile speed: linear
        if (fabs(b) < 0.0001) return -1.0;
        float64 t = -c / b;
        return t > 0.0 ? t : -1.0;
    }

    float64 disc = b * b - 4.0 * a * c;
    if (disc < 0.0) return -1.0;            // unreachable
    float64 sq = sqrt(disc);
    float64 t1 = (-b - sq) / (2.0 * a);
    float64 t2 = (-b + sq) / (2.0 * a);

    // Smallest strictly-positive root.
    float64 best = -1.0;
    if (t1 > 0.0) best = t1;
    if (t2 > 0.0 && (best < 0.0 || t2 < best)) best = t2;
    return best;
}
```

**Step 2 — gravity drop.** With the intercept time known, the lead point is
`target_pos + vt*t`. Gravity pulls the projectile down by `0.5 * g * t²` over that flight, so
aim that much *higher* (z is up in Source). `g` is the game's projectile gravity (often the
world gravity scaled by a per-projectile multiplier — read it, don't assume `9.8`):

```cpp
// Full gravity-aware aim point. Returns target_pos if unreachable.
vec3 predict_gravity(vec3 shooter, vec3 target_pos, vec3 target_vel,
                     float64 proj_speed, float64 gravity) {
    vec3 p_rel = target_pos.sub(shooter);
    float64 t = intercept_time(p_rel, target_vel, proj_speed);
    if (t < 0.0) return target_pos;                 // no firing solution; caller skips shot

    vec3 lead = target_pos.add(target_vel.scale(t)); // lead the motion
    lead.z = lead.z + 0.5 * gravity * t * t;         // raise to fight the drop
    return lead;
}
```

Feed `lead` into `calc_angle(eye, lead)` to get the firing angles. The drop term assumes z-up;
for a y-up engine (Unity) adjust `lead.y` instead. If `intercept_time` returns `-1`, there is
no firing solution — the target is faster than the projectile or out of range — so withhold
the shot rather than aiming at a garbage point.

## Recoil compensation (no-recoil)

A recoil pattern is a per-shot kick table: each consecutive round adds a known offset to the
view angles (a "spray pattern"). The game tracks how many rounds you have fired and the
accumulated punch, then offsets your aim by it. No-recoil cancels that offset.

Two approaches, cheapest first:

**Read and subtract the punch (read-mostly).** Most engines expose the accumulated aim punch
as a vector (`m_aimPunchAngle` in Source) and a shot counter (`m_iShotsFired`). Read the punch
and subtract it from your view angles when you write them back. This is the quiet path — you
only ever write the view-angle field you were going to write anyway for aim:

```cpp
// Returns view angles with the current recoil punch removed.
// OFF_PUNCH / OFF_VIEW_ANGLES resolve in offsets.em; UNVERIFIED until checked against binary.
vec2 compensate_recoil(proc_t& p, uint64 local, vec2 desired_angles) {
    vec3 punch = p.read_vec3_fl32(local + OFF_PUNCH);  // (pitch, yaw, roll) punch in degrees
    // Source scales stored punch by 2.0 for the actual view offset; verify per engine.
    return vec2(desired_angles.x - punch.x * 2.0,
                desired_angles.y - punch.y * 2.0);
}
```

**Patch the punch source (write, heavier footprint).** Some scripts zero the recoil-spread
float in game memory so the gun never kicks. Per guideline 9, write the single float, never a
NOP sled over the recoil code:

```cpp
// WRONG — nop-patching the recoil routine (16 bytes in .text, integrity-checked).
// RIGHT — zero the spread float that the routine reads.
if (g_norecoil) p.wf32(local + OFF_RECOIL_SPREAD, 0.0f);
```

Prefer the read-and-subtract path: it leaves zero write footprint on the recoil system and
folds cleanly into the angle you already plan to write. Reading the shot index (`m_iShotsFired`)
lets you ramp compensation in only while a spray is active, so single taps stay untouched.

## Smoothing — why and how

Snapping the view instantly onto a target is the loudest aim-detection signal: human aim has a
measurable acceleration curve and overshoot, a teleport does not, and behavioral anti-cheats
flag the zero-frame angle jump directly. Smoothing spreads the correction over several frames.
Always smooth the *delta* (wrapped via `normalize_delta`), never raw absolute angles, or the
yaw seam will make the view spin.

**Linear (divide).** Move a fixed fraction of the remaining delta each frame. This is
`smooth_angle` from `common-patterns.md`. Simple, but the speed decays as you close in, giving
a soft ease-out:

```cpp
vec2 smooth_linear(vec2 view, vec2 target, float64 smooth_factor) {
    vec2 d = angle_delta(view, target);                 // wrapped pitch+yaw delta
    return vec2(view.x + d.x / smooth_factor,           // larger factor = slower
                view.y + d.y / smooth_factor);
}
```

**Exponential (frame-rate independent).** The divide form above is tied to frame rate —
faster FPS means more steps means snappier aim. Decouple it from frame rate by deriving the
blend factor from elapsed time:

```cpp
vec2 smooth_exp(vec2 view, vec2 target, float64 rate, float64 dt) {
    float64 a = 1.0 - exp(-rate * dt);   // dt = 1.0 / get_fps(); a in (0,1)
    vec2 d = angle_delta(view, target);
    return vec2(view.x + d.x * a, view.y + d.y * a);
}
```

**Spring-damped (SmoothDamp).** Tracks angular velocity so the view *accelerates* into the turn
and eases out without overshoot — the most human-looking profile. `smooth_time` is the
approximate seconds to converge. It returns the new angle *and* the new velocity packed in a
`vec2`; persist `.y` per axis and feed it back next frame:

```cpp
// Critically-damped smoothing for one axis. Returns vec2(new_angle, new_velocity).
vec2 smooth_damp(float64 cur, float64 target, float64 vel, float64 smooth_time, float64 dt) {
    float64 omega = 2.0 / smooth_time;
    float64 x = omega * dt;
    float64 decay = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x);
    float64 change = cur - target;
    float64 temp = (vel + omega * change) * dt;
    float64 new_vel = (vel - omega * temp) * decay;
    return vec2(target + (change + temp) * decay, new_vel);
}
```

| Method        | Feel               | State | Frame-rate safe | Cost |
| ------------- | ------------------ | ----- | --------------- | ---- |
| Linear divide | ease-out only      | none  | no              | tiny |
| Exponential   | ease-out, smooth   | none  | yes (uses `dt`) | tiny |
| Spring-damped | ease-in + ease-out | per-axis velocity | yes | small |

**Sample-rate considerations.** Any tuning constant that is not time-based drifts with frame
rate — feed `dt = 1.0 / get_fps()` into the exponential and spring forms. The linear divide
form has no `dt`, so its effective speed differs between 60 and 240 FPS; document the slider as
frame-rate dependent or convert it to the exponential form.

## Mouse input writeback paths

Computed angles have to *become* aim somehow. Two routes, with very different detection
surfaces.

**Synthetic mouse input (`SendInput`).** Convert the angle delta to mouse counts and feed it
through the OS input stack via the Win API. The game sees ordinary mouse movement and applies
its own sensitivity, so the conversion needs the game's yaw/pitch-per-count factor:

```cpp
// Convert a view-angle delta (degrees) to relative mouse counts and send it.
// `counts_per_deg` is game sensitivity dependent — derive or measure it; UNVERIFIED.
void writeback_sendinput(vec2 angle_delta_deg, float64 counts_per_deg) {
    int64 dx = cast<int64>(angle_delta_deg.y * counts_per_deg);   // yaw  -> horizontal
    int64 dy = cast<int64>(angle_delta_deg.x * counts_per_deg);   // pitch -> vertical
    mouse_move_relative(dx, dy);   // or send_mouse_input(dx, dy, MOUSEEVENTF_MOVE, 0)
}
```

- *Pros:* no game-memory write at all — the cleanest footprint against memory-integrity
  checks; the movement rides the input path the game already trusts.
- *Cons:* synthetic input is itself detectable (injected-input flags, delta-timing analysis)
  and needs the sensitivity conversion, which shifts with the player's sens and zoom.

**Direct view-angle write.** Write the computed angles straight into the game's view-angle
field:

```cpp
void writeback_angles(proc_t& p, uint64 local, vec2 angles) {
    // OFF_VIEW_ANGLES resolves in offsets.em. One vec write per active frame, no more.
    p.write_vec3_fl32(local + OFF_VIEW_ANGLES, vec3(angles.x, angles.y, 0.0));
}
```

- *Pros:* exact — no sensitivity math, the view lands precisely where you computed.
- *Cons:* it is a memory write to a contested gameplay field; anti-cheat can monitor the
  field for writes that did not originate from the input path, and on a contested field the
  game may revert it (read back to confirm, per guideline 9).

**Respect guideline 9 either way.** Whichever path, write only while the aim key is held and
only the minimum needed — one relative move or one `write_vec3_fl32` per active frame, gated
on a GUI keybind. Never write every frame unconditionally:

```cpp
void on_update(int64 data) {
    if (!g_aim_enabled) return;
    if (!key_down(vk::xbutton2)) return;   // hold-to-aim; no key, no write
    // ... select + validate + predict + smooth, then a single writeback ...
}
```

## Common pitfalls

**Radians vs degrees — the silent 57× bug.** `atan2` and all Enma trig work in radians; most
view-angle fields store degrees, some store radians. The classic failure: read a radian-stored
angle, treat it as degrees, then write your degree result back into a radian field — everything
is off by `180/PI ≈ 57.3×` and the aim flicks to nonsense. Convert at *every* boundary
(`* RAD2DEG` after a trig call, `* DEG2RAD` before one) and confirm the field's unit by reading
it while looking at a known angle in-game.

**Pitch sign convention.** Source uses up = *negative* pitch; Unreal and Unity use up =
*positive* pitch. Backwards, and the aimbot pulls *down* onto targets above you and the spray
compensation fights the recoil instead of canceling it. Verify by reading the field while
aiming straight up.

**Left- vs right-handed coordinates.** Source/Unreal are left-handed z-up; Unity left-handed
y-up; many math libraries and custom W2S assume right-handed. A mismatch flips a yaw or
cross-product sign, so left-side targets read as right-side. If lead prediction consistently
aims to the wrong side, suspect a flipped axis before the velocity read.

**Wrong "up" axis in pitch math.** `calc_angle` uses `dist_xy` (XY-plane) because Source is
z-up. On a y-up engine the planar distance is over XZ and pitch keys off `delta.y`. Reusing the
z-up form on Unity makes pitch track horizontal distance — aim drifts vertically as the target
strafes.

## See also

- [`common-patterns.md`](common-patterns.md) — the render half (W2S, boxes, radar) and the
  `calc_angle` / `smooth_angle` this file extends.
- [`offset-methodology.md`](offset-methodology.md) — resolving `OFF_VELOCITY`, `OFF_VIEW_ANGLES`,
  `OFF_PUNCH` with sigs instead of hardcodes.
- [`anti-cheat-architecture.md`](anti-cheat-architecture.md) — why instant snaps and memory
  writes are detection surfaces; informs the smoothing and writeback choices above.
- [`pcx-api-cheatsheet.md`](pcx-api-cheatsheet.md) — quick reference for the natives used here.
- [`game-cheat-guidelines`](../.claude/skills/game-cheat-guidelines/SKILL.md) — the 12 rules;
  9 (minimize writes) and 10 (W2S) govern this file directly.
- Perception API: [`proc-api`](../docs/perception/proc-api.md),
  [`render-api`](../docs/perception/render-api.md),
  [`input-api`](../docs/perception/input-api.md),
  [`win-api`](../docs/perception/win-api.md); Enma math:
  [`addon-vec`](../docs/enma/addon-vec.md), [`addon-math`](../docs/enma/addon-math.md).

---

## Source: `knowledge/offset-methodology.md`

# Offset Finding and Maintenance Methodology

## When to Pattern Scan vs Hardcode

**Pattern scan** (preferred): any global pointer, vtable address, or function address that the compiler may relocate between builds. The instruction sequence referencing it is stable; the address it points to is not.

**Hardcode** (acceptable): struct field offsets within a known type. `m_iHealth` at `+0x43E0` inside `CPlayer` changes only when Respawn reorders the class — which happens less often than code relocations. Still document the source.

## Signature Construction

1. Open the function in IDA/Ghidra. Find the instruction that loads/references the value you need.
2. Copy the raw bytes of that instruction and 1-2 neighboring instructions for uniqueness.
3. Replace **RIP-relative displacements** (4 bytes after the opcode) with `??` wildcards — these change every build.
4. Replace **immediate addresses** and **jump targets** with `??` — also unstable.
5. Keep **opcode bytes** and **register encodings** — these are stable unless the compiler changes register allocation.

```
Example instruction:  48 8B 05 [A0 B3 2A 01]  ← MOV RAX, [rip+0x12AB3A0]
                      ^^^^^^^^ ^^^^^^^^^^^^^^
                      opcode   RIP displacement (changes every build)

Signature:           "48 8B 05 ?? ?? ?? ??"
```

Verify uniqueness: `find_all_code_patterns` should return exactly 1 hit. If multiple, extend the sig with more surrounding bytes.

## RIP-Relative Address Resolution

Most x64 instructions use RIP-relative addressing. The displacement is a **signed 32-bit integer** relative to the **end** of the instruction (i.e., the address of the next instruction).

```
hit        = address where the sig matched
disp_off   = offset from hit to the displacement bytes (e.g., 3 for LEA reg,[rip+??])
insn_len   = total instruction length (e.g., 7 for a 7-byte LEA)
displacement = read_int32(hit + disp_off)      ← signed!
resolved   = hit + insn_len + displacement
```

Common instruction shapes:

| Pattern | Instruction | disp_off | insn_len |
|---------|-------------|----------|----------|
| `48 8B 05 ?? ?? ?? ??` | MOV RAX, [rip+disp] | 3 | 7 |
| `48 8D 0D ?? ?? ?? ??` | LEA RCX, [rip+disp] | 3 | 7 |
| `48 8B 0D ?? ?? ?? ??` | MOV RCX, [rip+disp] | 3 | 7 |
| `E8 ?? ?? ?? ??` | CALL rel32 | 1 | 5 |
| `E9 ?? ?? ?? ??` | JMP rel32 | 1 | 5 |

## Pointer Chain Walking

Game data is often behind multiple levels of indirection:

```
base_address → entity_list_ptr → entity_ptr → field
```

Strategy:
1. Find the first pointer via sig scan + RIP resolution.
2. Dereference each level with `ru64`, checking for 0 at every step.
3. Document the full chain: `base + 0x... → deref → + 0x... → deref → + 0x...`
4. The final offset into the struct is typically a hardcoded field offset.

```cpp
uint64 entity_list = resolve_sig(p, base, size, SIG_ENTITY_LIST);  // sig scan
if (entity_list == 0) return;                                       // stale sig
uint64 list_ptr = p.ru64(entity_list);                              // deref level 1
if (list_ptr == 0) return;                                          // null
uint64 entity = p.ru64(list_ptr + cast<uint64>(index) * 0x8);      // deref level 2
if (entity == 0) return;                                            // null entry
int32 health = p.r32(entity + 0x43E0);                             // struct field
```

## Using struct_dump for Discovery

When you don't know a struct layout, read raw memory and classify fields:

```cpp
// In Perception IDE, the AI can use struct_dump tool:
// struct_dump(addr, size=0x100)
// Returns: offset, raw hex, heuristic type (pointer/vtable/float/int/null)
```

Look for:
- **Pointers**: values in the `0x7FF...` range (usermode x64)
- **VTable ptrs**: first 8 bytes of an object, pointing into .rdata
- **Floats**: values like `100.0`, `0.0`, `-1.0` that make sense as game state
- **Ints**: small values (health, ammo, team ID)

## Cross-Referencing with IDA/Ghidra

1. Find the ConVar or string that names the feature (e.g., `"cl_interp"`, `"m_iHealth"`).
2. Xref the string → find the registration function → find the global variable or struct field.
3. Verify the offset in the reversed SDK headers if available (e.g., `r5sdk/src/game/server/player.h`).
4. Remember: SDK headers may be from an older game version. Always verify with a live read.

## Offset Table Format

Maintain a structured offset file:

```cpp
// offsets.em — auto-resolved via pattern scans
// Last verified: 2025-06-15, game version 1.98

const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";
// LEA RCX, [rip+????] — loads CEntityList global
// Source: sub_1400ABCDE in IDA, xref from "cl_entitylist"

const string SIG_VIEW_MATRIX = "48 8D 05 ?? ?? ?? ?? 48 89 44 24 ?? F3 0F";
// LEA RAX, [rip+????] — loads view-projection matrix (16 floats)

const string SIG_LOCAL_PLAYER = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? 48 8B 48";
// MOV RAX, [rip+????] — loads local player pointer

// Struct field offsets (hardcoded, verified against SDK)
const uint64 OFF_HEALTH   = 0x43E0;   // CPlayer::m_iHealth (int32)
const uint64 OFF_TEAM     = 0x0448;   // CBaseEntity::m_iTeamNum (int32)
const uint64 OFF_POSITION = 0x014C;   // CBaseEntity::m_vecAbsOrigin (vec3 float32)
const uint64 OFF_NAME     = 0x0589;   // CBaseEntity::m_iName (string ptr)
```

## What Breaks on Game Updates

| What | Stability | Why |
|------|-----------|-----|
| Pattern signatures | **High** | Instruction sequences rarely change unless the function is rewritten |
| RIP-relative resolved addresses | **None** | Absolute addresses change every build |
| Struct field offsets | **Medium** | Change when devs add/remove/reorder fields |
| VTable indices | **Medium** | Change when virtual functions are added/removed |
| Function addresses | **None** | Change every build — always use sigs |
| String literals | **High** | Rarely change — good anchor points for xrefs |
