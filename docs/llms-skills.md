# pcx-ai-toolkit — Skills Bundle

> Every AI skill in the pcx-ai-toolkit concatenated into one file. Drop into tools that load a single context document, or @-reference from Cursor / Aider / Continue when you want the full behavioral discipline surface available.

> **Generated** by `tools/build-llms-index.py` — do not edit manually. Re-generate by running the tool from the repo root. CI verifies the committed bundle matches the current source.

**Source files included: 16**

---

## Source: `.claude/skills/game-cheat-guidelines/SKILL.md`

---
name: game-cheat-guidelines
description: >
  Mandatory behavioral rules and practical patterns for writing Perception.cx
  game-cheat scripts in Enma, AngelScript, and C++. Always active — these
  rules apply every time you write or edit game-cheat code, including ESP,
  aimbot, triggerbot, radar, pattern scanning, and overlay rendering.
  Authorized use only — analyze software you own or are permitted to test.
license: MIT
---

# Perception.cx Game-Cheat Script Development Guidelines

Behavioral rules and practical patterns for writing game-cheat scripts with Perception.cx in Enma, AngelScript, and C++. Derived from the Karpathy principles and rewritten for the domain: ESP, aimbot, triggerbot, radar, pattern scanning, world-to-screen math, memory reads/writes, and overlay rendering. These rules apply to authorized reverse engineering, security research, and game-cheat development — analyze only software you own or are authorized to test.

**Always active.** These rules apply every time you write or edit a game-cheat script. They are not suggestions.

**Prerequisites:** Load the `game-cheat-script-master` skill first. It defines the mandatory co-skills, read-first docs, and the canonical project layout. Then keep `game-hacking-pcx` loaded for the full API doc index. **Read the relevant doc before writing any API call** — see `skill://game-hacking-pcx` for the complete file-by-file index.

**Templates:** Use `templates/cheat-skeleton-em/` and `templates/cheat-skeleton-as/` as the starting scaffold for every new cheat. See `knowledge/cheat-script-cookbook.md` for reusable recipes (W2S, ESP, aimbot smoothing, triggerbot, radar, config save/load).

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

## Source: `.claude/skills/game-cheat-script-master/SKILL.md`

---
name: game-cheat-script-master
description: >
  Master skill for Perception.cx game cheat script development. Activates on any
  request for cheats, hacks, ESP, aimbot, triggerbot, radar, overlay, memory
  reading, pattern scanning, or anti-cheat research. Loads the complete doc
  index, the 12 cheat guidelines, the AI pair-programming workflow, and the
  official cheat templates. Always use this alongside game-cheat-guidelines and
  game-hacking-pcx.
license: MIT
---

# Game Cheat Script Master — Perception.cx

This skill turns any LLM into a specialized Perception.cx cheat-script developer.
It is the single entry point for **ESP, aimbot, triggerbot, radar, overlay,
memory-reading, world-to-screen, pattern-scanning, and anti-cheat research**
requests. It tells the model exactly which docs to read, which rules to follow,
which templates to scaffold from, and how to stay safe and legal.

**Always active when the user asks for any kind of game cheat, hack, overlay,
memory script, or Perception.cx tooling related to games.**

---

## Trigger

- Any request containing: cheat, hack, esp, wallhack, aimbot, triggerbot,
  recoil, no-recoil, radar, overlay, menu, gui, memory read, pattern scan,
  signature, offset, vtable hook, anti-cheat, EAC, BattlEye, Vanguard, GameGuard,
  integrity check, bypass, streamproof, kernel driver, dump, IDA, Ghidra, r5sdk,
  source engine, Unreal Engine, Unity, Frostbite, REDengine, CryEngine, Godot.
- Any file extension: `.em`, `.as`, `.lua` in a Perception.cx context.
- Any mention of `ref_process`, `find_code_pattern`, `ru64`, `draw_rect`,
  `world_to_screen`, `register_routine`, `proc_t`, `perception`, `enma`, `angelscript`.

---

## Mandatory Co-Loaded Skills

Load these on every cheat-script session. They are prerequisites, not options.

| Skill | Why it matters |
|-------|----------------|
| `skill://game-cheat-guidelines` | The 12 hard rules: `uint64` addresses, null checks, scan/render separation, sigs over hardcodes, GUI for tunables, etc. |
| `skill://game-hacking-pcx` | The full doc router: which `docs/perception/` and `docs/enma/` files to read before writing any API call. |
| `skill://ai-pair-programming` | How to drive the AI: read docs first, plan before code, verify sigs with MCP, diff-review, unstuck questions. |
| `skill://pcx-patch-day-playbook` | What to do when the script breaks after a game update. |
| `skill://mcp-tool-routing` | Which of the 59 Perception MCP tools to use for binary discovery. |

---

## Read-First Docs

Before writing **any** cheat script code, read these in order. They are small
and prevent the most expensive mistakes.

1. **Quick API surface:** `knowledge/pcx-api-cheatsheet.md` (15 KB)
2. **The 12 guidelines:** `.claude/skills/game-cheat-guidelines/SKILL.md`
3. **Language reference:** `docs/enma/llms-language.md` (Enma) or `docs/angelscript-lang/INDEX.md` (AS)
4. **Core APIs for almost every cheat:**
   - `docs/perception/proc-api.md` — process attach, memory reads, pattern scan
   - `docs/perception/render-api.md` — 2D overlay drawing
   - `docs/perception/gui-api.md` — sidebar widgets for every tunable
   - `docs/perception/input-api.md` — keybinds and polling
5. **Math & patterns:**
   - `knowledge/aimbot-math.md` — `calc_angle`, smoothing, FOV checks, angle wrap
   - `knowledge/common-patterns.md` — world-to-screen, ESP boxes, snaplines, radar
   - `knowledge/offset-methodology.md` — how to find and maintain offsets
6. **Engine-specific notes:** `knowledge/engine-*.md` and `signatures/*/*.md`
7. **Anti-cheat research:** `knowledge/anti-cheat-architecture.md`, `signatures/anti-cheat/common-ac-patterns.md`
8. **Cheat cookbook (templates + recipes):** `knowledge/cheat-script-cookbook.md`

---

## Project Scaffolding

Use the official templates. Do **not** invent a layout.

| Template | Use when |
|----------|----------|
| `templates/cheat-skeleton-em/` | Full Enma cheat project (ESP, aim, triggerbot, radar, menu) |
| `templates/cheat-skeleton-as/` | Full AngelScript cheat project |
| `templates/full-project/` | Minimal one-feature Enma scaffold |
| `templates/full-project-as/` | Minimal one-feature AngelScript scaffold |
| `templates/aimbot-skeleton.em` | Standalone aimbot math/reference |
| `templates/overlay-basic.em` | Tiny overlay-only script |

Scaffold command pattern:

```bash
pcx new cheat-skeleton-em my-esp
```

If `pcx new` is not available, copy the template directory manually.

---

## Standard Module Layout

Every full cheat project should look like this. One feature, one file.

```
project/
├── globals.em/as/lua   # proc_t, base/size, entity cache, config state
├── offsets.em/as/lua   # all sigs + resolved addresses + RIP helpers
├── esp.em/as/lua       # entity reads + 2D/3D box / health / name
├── aim.em/as/lua       # target selection + smoothing + angle writeback
├── triggerbot.em/as/lua # trigger timing + crosshair check
├── radar.em/as/lua     # world-to-map + blips
├── menu.em/as/lua      # GUI sidebar, keybinds, config load/save
├── utils.em/as/lua     # W2S, distance, team check, visibility helper
└── main.em/as/lua      # attach, resolve, register routines, unload
```

If the target engine or game is known, name the process string and module
explicitly, but never hardcode an absolute address.

---

## Domain-Specific Rules (In Addition to the 12 Guidelines)

### Anti-Cheat & Legal Scope

- **Analyze only software you own or are authorized to test.**
- Single-player, offline, or your-own-process research is the default scope.
- Multi-player or live-service work requires explicit authorization; if unsure,
  refuse and tell the user to verify their rights.
- Do not produce code whose sole purpose is to bypass kernel anti-cheat or evade
  detection in a protected online environment.
- Defensive anti-cheat analysis (understanding how detection works, writing
  detection tools, mapping integrity checks for authorized research) is allowed.

### Memory Safety

- `uint64` for every address, pointer, module base, and VTable slot.
- Null-check after **every** `ru64`, `find_code_pattern`, `get_module_base`,
  `ref_process`, and pointer-chain step.
- Failed reads return `0`, not exceptions. Treat `0` as "I don't know yet."
- Prefer read-only analysis and visualization. Writes are a last resort,
  minimal bytes, verified with read-back, gated behind permissions.

### Pattern Scanning

- Never generate a sig from memory. Use `mcp:find_pattern` or
  `python tools/sig-uniqueness-checker.py --sig` on the actual binary.
- Keep sigs in `offsets.*`, named, with a comment describing the instruction.
- Resolve RIP-relative displacements correctly: `final = hit + insn_len + signed_disp`.
- Wildcard only the displacement bytes; don't wildcard opcodes that identify the
  instruction pattern.

### Rendering

- Update routines read + build a cache. Render routines draw only from the cache.
- Construct `color`, `vec2`, `vec3` per frame; they are stack value types.
- Always check `w > 0.001` (or engine-equivalent) before trusting world-to-screen.
- Use `get_view_width()` / `get_view_height()` for screen-space scaling.

### Aimbot

- `calc_angle` returns `(pitch, yaw)` in degrees, engine-convention specific.
- Normalize yaw delta to `[-180, 180)` with the `fmod(delta + 540.0, 360.0) - 180.0` trick.
- Clamp pitch to `[-89, 89]` or engine limits; never wrap pitch.
- Smooth with `current + delta * factor`, factor exposed in GUI as a slider.
- FOV check before aiming; prefer the closest in-FOV enemy or the one under
  crosshair, configurable in GUI.

### Triggerbot

- Read the same entity data the ESP uses; do not duplicate entity walks.
- Add a small random delay or fire only when crosshair is stable to avoid robotic
  timing; expose the delay range in the GUI.
- Respect game fire-rate by checking `can_fire()` or equivalent if available.

### Radar

- Project world positions to a 2D map coordinate using a chosen reference origin
  and scale; do not call expensive W2S per blip.
- Draw blips as colored circles with team differentiation.
- Keep the radar in its own render routine with no memory reads.

### Config / Menu

- Every tunable (distance, color, smoothing, FOV, hotkey, toggle) is bound to a
  GUI widget in `menu.*`.
- Load config from a JSON file in `main()` and save on change.
- Use `section_checkbox`, `section_slider_float`, `section_keybind`,
  `section_color_picker`, `section_combo_box` as appropriate.

---

## Decision Tree for "Which Language?"

| User wants... | Default | Alternative |
|---------------|---------|-------------|
| Modern PCX, hot reload, typed, fast | **Enma (.em)** | — |
| Host already loads AngelScript | AngelScript (.as) | — |
| Minimal embedded scripting, existing Lua host | Lua (.lua) | — |
| Cross-engine portability | Enma | Lua |
| Tight C++ interop / SDK work | C++ host + Enma | — |

See `knowledge/pcx-cross-language-bridge.md` for the full comparison.

---

## Decision Tree for "Which Doc First?"

| Task | Read first | Then read |
|------|------------|-----------|
| "Write an ESP" | `docs/perception/proc-api.md` | `docs/perception/render-api.md`, `knowledge/common-patterns.md` |
| "Write an aimbot" | `knowledge/aimbot-math.md` | `docs/perception/proc-api.md`, `docs/perception/input-api.md` |
| "Add a menu" | `docs/perception/gui-api.md` | `knowledge/common-patterns.md` |
| "Find offsets/sigs" | `knowledge/offset-methodology.md` | `signatures/<engine>/*.md`, `skill://mcp-tool-routing` |
| "Script broke after patch" | `skill://pcx-patch-day-playbook` | `knowledge/offset-methodology.md` |
| "Anti-cheat research" | `knowledge/anti-cheat-architecture.md` | `signatures/anti-cheat/common-ac-patterns.md` |

---

## Common Pitfalls to Catch in Diff Review

| Code smell | Rule | Fix |
|------------|------|-----|
| `int64` / `int32` near `addr`, `base`, `ptr`, `offset` | #2 | Change to `uint64` |
| Bare float literal in GPU/vertex data | #8 | Add `f` suffix |
| `ru64()` result used without `== 0` check | #3 | Add null guard |
| `find_code_pattern` in render/update tick | #4 | Move to `main()` / `offsets.*` |
| Hardcoded RVA without citation | #1, #12 | Replace with sig + `// E-NNN` or `// UNVERIFIED` |
| `color` / `vec2` / `vec3` at file scope | #7 | Construct per frame |
| Hotkey hardcoded, no GUI widget | #11 | Add `section_keybind` |
| Memory write not gated / too large | #9 | Minimize bytes, verify, use permissions |
| W2S without `w > 0.001` check | #10 | Add behind-camera guard |
| One giant file | #6 | Split into globals/offsets/esp/aim/menu/main |

---

Before delivering any cheat script:

1. [ ] Read the relevant docs (see "Read-First Docs" above).
2. [ ] Load the mandatory co-skills.
3. [ ] Scaffold from an official template.
4. [ ] Honor the 12 `game-cheat-guidelines` plus the domain rules here.
5. [ ] Verify sigs/offsets against a real binary, not from memory.
6. [ ] Separate update (reads) from render (draws).
7. [ ] Bind every tunable to a GUI widget.
8. [ ] Add `uint64` address checks, null checks, and `w > 0` guards.
9. [ ] Confirm the work is for authorized/single-player/educational targets.
10. [ ] Run `pcx verify <file>` and fix any `unknown_call` / `missing_import` findings.
11. [ ] Suggest `pcx lint <file>` and a diff review before running.

---

## Source: `.claude/skills/game-hacking-pcx/SKILL.md`

---
name: game-hacking-pcx
description: >
  Mandatory doc router for all PCX scripting sessions. Triggers on any game
  hacking, game cheat, ESP, aimbot, triggerbot, radar, Enma, AngelScript, or
  Perception.cx work. Provides the full doc index (43,000+ lines across 139
  files) and enforces reading the relevant documentation before writing any
  API call. Load alongside game-cheat-script-master and game-cheat-guidelines
  on every PCX game-cheat session.
license: MIT
---

# Game Hacking & Scripting — Perception.cx / Enma / AngelScript / C++

## Trigger
Game hacking, game cheats, cheat scripts, ESP, aimbot, triggerbot, radar, memory reading/writing,
pattern scanning, vtable hooking, process manipulation, Enma scripting, AngelScript scripting,
Perception.cx, PCX, render overlays, any `.em` or `.as` game script work, or any mention of the
Perception platform.

## MANDATORY: Read Before Writing Code

**The only authoritative sources for PCX API names are the two upstream docs:**

1. `https://docs.perception.cx/perception/enma/overview` — Enma API surface
2. `https://docs.perception.cx/perception/angel-script/overview` — AngelScript API surface

Use the `.md` variant of any sub-page (e.g. `https://docs.perception.cx/perception/enma/proc-api.md`,
`https://docs.perception.cx/perception/angel-script/render-api.md`) for structured markdown.
The local `docs/` tree is a drift-checked mirror of these upstream pages; when in doubt, trust
the live upstream version.

You MUST read the relevant upstream doc before writing ANY Enma, AngelScript,
or PCX API code. Do not write from memory. The docs are the source of truth.

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

### When writing core AngelScript (.as) code — read the language manual:

| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Language Index** | `docs/angelscript-lang/INDEX.md` | - | Overview of the core language, data types, statements, etc. |
| Datatypes | `docs/angelscript-lang/datatypes.md` | 17 | Landing page for primitives, objects, and handles |
| Handles | `docs/angelscript-lang/handles.md` | - | Core AngelScript `@` object handles and memory management |
| Script Classes | `docs/angelscript-lang/script-class.md` | - | User-defined classes, members, and methods |
| Expressions | `docs/angelscript-lang/expressions.md` | - | Math, logic, assignments, and operator precedence |
| Statements | `docs/angelscript-lang/statements.md` | - | If, switch, loops, try/catch |

### When writing PCX AngelScript (.as) code — read these:

| API | Path | Lines |
|-----|------|-------|
| Overview | `docs/perception/angelscript/overview.md` | 68 |
| Life Cycle | `docs/perception/angelscript/life-cycle.md` | 128 |
| Engine | `docs/perception/angelscript/engine.md` | 178 |
| Atomic Types | `docs/perception/angelscript/atomic-types.md` | 185 |
| Proc API | `docs/perception/angelscript/proc-api.md` | 1156 |
| Render API | `docs/perception/angelscript/render-api.md` | 1829 |
| GUI API | `docs/perception/angelscript/gui-api.md` | 718 |
| Input API | `docs/perception/angelscript/input-api.md` | 226 |
| System/CPU/Disasm | `docs/perception/angelscript/system-api-cpu-and-disassembly.md` | 304 |
| Net API | `docs/perception/angelscript/net-api.md` | 379 |
| File System | `docs/perception/angelscript/file-system.md` | 298 |
| Extended Math | `docs/perception/angelscript/extended-math-api.md` | 580 |
| Win API | `docs/perception/angelscript/win-api.md` | 594 |
| JSON API | `docs/perception/angelscript/json-api.md` | 479 |
| Unicorn | `docs/perception/angelscript/unicorn.md` | 702 |
| Zydis Encoder | `docs/perception/angelscript/zydis-encoder.md` | 703 |
| Intrinsics | `docs/perception/angelscript/intrinsics.md` | 661 |
| Mutex API | `docs/perception/angelscript/mutex-api.md` | 248 |
| Utilities | `docs/perception/angelscript/utilities.md` | 607 |
| Sound API | `docs/perception/angelscript/sound-api.md` | 250 |
| Bit Reinterpret | `docs/perception/angelscript/bit-reinterpret-helpers.md` | 167 |
| Engine Specific | `docs/perception/angelscript/engine-specific-api.md` | 195 |
| CS2 Extended | `docs/perception/angelscript/cs2-extended-api.md` | 165 |

### PCX IDE & Extensions:

| Doc | Path | Lines |
|-----|------|-------|
| Perception IDE | `docs/perception/ide.md` | 585 |
| Extensions API | `docs/perception/extensions-api.md` | 371 |
| Analyzer | `docs/perception/analyzer.md` | 370 |

### When writing core Lua (.lua) code — read the language manual:

| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Reference Manual** | `docs/lua-lang/manual-5.4.md` | 6056 | Full, authoritative Lua 5.4 reference manual |
| Welcome & Readme | `docs/lua-lang/readme-5.4.md` | 150 | Lua 5.4 readme and changes |

### PCX Lua (.lua) scripting:

| API | Path | Lines |
|-----|------|-------|
| Overview | `docs/perception/lua/overview.md` | 59 |
| All APIs | `docs/perception/lua/*.md` | 5779 total |
## How To Use These Docs

1. **Before starting a game-cheat script**: load `skill://game-cheat-script-master` and read `knowledge/cheat-script-cookbook.md`
2. **Before writing Enma code**: start from `https://docs.perception.cx/perception/enma/overview` and read the relevant `.md` sub-page
3. **Before writing AngelScript code**: start from `https://docs.perception.cx/perception/angel-script/overview` and read the relevant `.md` sub-page
4. **If unsure about a type, function, or parameter**: read the upstream doc, don't guess
5. **If the doc says a function is "gated"**: it requires a permission flag — mention this to the user
6. **For a starting project scaffold**: use `templates/cheat-skeleton-em/` or `templates/cheat-skeleton-as/`

## Anti-Hallucination Rule

You must NEVER invent a PCX or Enma/AngelScript/Lua API name. Every function,
method, type, and import you use must come from one of:
  - `https://docs.perception.cx/perception/enma/overview` and its sub-pages,
  - `https://docs.perception.cx/perception/angel-script/overview` and its sub-pages,
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
- **AngelScript skeleton**: `templates/cheat-skeleton-as/` — same layout in AngelScript
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
- **AngelScript+PCX LSP**: `lsp/angel-lsp-pcx/server/out/server.js`

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

## Source: `.claude/skills/mcp-tool-routing/SKILL.md`

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

Pair immediately with `tools/sig-uniqueness-checker.py` (added in this branch) to validate:

```
1. process/generate_signature(handle, addr, 16)  → "48 8D 0D ?? ?? ?? ?? E8"
2. write to a temp file, then:
3. python3 tools/sig-uniqueness-checker.py game.exe --sig "..."
4. read the verdict:
   - UNIQUE margin=5    → ship it
   - AMBIGUOUS, N hits  → regenerate with longer max_length
   - STALE              → the sig doesn't match at the expected address (very rare; investigate)
   - BRITTLE margin=0   → regenerate longer
```

`max_length` is a starting point; iterate with `process/generate_signature(handle, addr, 24)` if the 16-byte version is ambiguous. Each generation is cheap; the validation step is also cheap. Iterate until UNIQUE with `margin ≥ 2` and add the sig to your `offsets.em` with an `// E-NNN` evidence reference (per `skill://re-evidence-log`).

To *use* a sig to find a function in a module you haven't attached to by address, `process/find_function_by_signature(handle, module_base, signature)` AOB-scans `.text` and bounds-walks each hit — heavier than a plain `process/find_pattern`, but it returns function bounds, not just a hit address.

**Why:** The MCP can generate sigs but cannot validate them; the local Python tool can validate sigs but cannot generate them from a live address. The combination is the workflow.

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

For deeper cross-module analysis (which other modules import a specific export from this one), pair with `tools/module-export-mapper.py --consumers <dir>` (added in this branch). The MCP gives you exports + imports per module; the Python tool joins them into a "this DLL is consumed by ..." map.

`process/get_modules` is the right call when attaching: it returns the module list including base addresses + sizes, which is what you need for `process/find_pattern` calls bounded to a specific module. Don't iterate `process/list` + `process/list_module_exports` per module yourself — `process/get_modules` returns the full picture in one call.

**Why:** These tools are cheap and idempotent; the routing is mostly "use them rather than guessing." The only mistake is overusing `process/list` in a loop — it snapshots the system every call. Call it once; cache the result. And remember `system/info`'s `is_24h2_or_later` flag for build-keyed offsets — query it once per session, not per call.

---

## 7. Scripting Bridge (Enma)

**The Enma scripting bridge is three tools, none of which takes a `handle`.** They run a script (or return reference text) with their own permissions, independent of any referenced process. The bridge is exactly these three — there are no MCP tools for host file I/O, host text search, host reference finding, internet search, or duplicate script-lifecycle aliases. File reads/writes are NOT MCP tools; do them via the toolkit's standalone Python tools or the Perception IDE.

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
| "Sig + validate" | `process/generate_signature(addr, 16)` → save → `python3 tools/sig-uniqueness-checker.py game.exe --sig "..."` → if margin < 2, regenerate longer |
| "Sig → function in a new build" | `process/get_module_by_name(name)` → `process/find_function_by_signature(module_base, sig)` → if STALE, broaden the sig and retry |
| "Which module owns this VA?" | `process/lookup_symbol(address)` → `{module_base, module_name, module_offset, section, nearest_export}` |
| "Write a one-shot Enma script" | `script/get_context` (once) → `script/validate(source)` (compile-only, all addons) → `script/execute(source)` (run `main()` once; no GUI/thread addons) |
| "Per-binary diff after patch" | `python3 tools/offset-diff.py --old V1 --new V2 --sigs old_offsets_json` → for each LOST: `process/find_pattern` against V2 with broadened sig → record new sig |

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
| Generate a sig | `process/generate_signature` + `tools/sig-uniqueness-checker.py` | hand-crafting bytes |
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

**Cross-references:** `mcp/perception-mcp-config.json` (authoritative 59-tool list), `mcp/claude-code-setup.md` / `mcp/cursor-setup.md` / `mcp/aider-setup.md` (per-IDE wiring), `tools/sig-uniqueness-checker.py` / `tools/offset-diff.py` / `tools/dumper-to-enma.py` / `tools/module-export-mapper.py` (local CLI tools that pair with MCP calls — file I/O and cross-module joins live here, NOT on the MCP server), `skill://pcx-perf-budget` (call-cost discipline that applies to MCP calls), `skill://re-evidence-log` (E-NNN cross-references record which MCP calls produced each offset).

---

## Source: `.claude/skills/pcx-angelscript-discipline/SKILL.md`

---
name: pcx-angelscript-discipline
description: >
  Behavioral and syntactic rules for writing .as scripts on Perception.cx.
  Prevents Enma-reflex errors in the AngelScript API surface — method names,
  parameter shapes, and constants differ between the two languages. Always
  active when editing .as files.
license: MIT
---

# AngelScript Discipline for Perception.cx

Behavioral and syntactic rules for writing `.as` scripts on Perception.cx. The companion skill to `game-cheat-guidelines` (which is Enma-flavored): same domain, different language, different gotchas. AngelScript on PCX has its own type system, lifecycle conventions, and API surface; the AI defaults to Enma idioms when editing `.as` files and produces code that does not compile.

**Always active when editing `.as` files.** These rules apply every time you write or edit a Perception.cx AngelScript script.

**Prerequisite:** `game-hacking-pcx` skill for the full doc index. **Read the relevant `docs/perception/angelscript/<file>.md` before writing any API call** — the AngelScript surface is not the Enma surface, and method names, parameter shapes, and constants differ.

---

## Trigger

`.as` file open, AngelScript syntax visible (`&in` references, `@` handles, `register_callback`, `on_tick`), user mentions AngelScript / `proc_t` / PCX scripting in AS context, any code referencing `docs/perception/angelscript/`.

---

## 1. AngelScript Is Not Enma — Don't Paste Enma APIs

**The PCX AngelScript API has different function names, different parameter shapes, and different idioms than the Enma API. They look similar; they are not interchangeable.**

The most common bug in AI-written `.as` scripts is pasting Enma API calls verbatim. The script doesn't compile, or worse, compiles to something that looks right and behaves wrong because AngelScript happens to have a same-named function with a different signature.

| Enma | AngelScript |
|---|---|
| `register_routine(cast<int64>(on_render), 0)` | `register_callback(on_tick, 16, 0)` |
| `int64 main()` | `int main()` |
| `void on_render(int64 data)` | `void on_tick(int id, int data_index)` |
| `println(...)` | `log(...)` |
| `color(r,g,b,a)` then `draw_rect(pos, size, color, ...)` | `draw_rect_filled(x, y, w, h, r, g, b, a, rounding, corner_flags)` |
| `get_view_width()` / `get_view_height()` | `get_view(vw, vh)` — out-param into two floats |
| `create_section("X")` returning `int64` | `create_section("X")` — same name, but check the AS gui-api doc for return type |

```cpp
// WRONG — Enma idioms in an .as file
int64 main() {
    color c = color(255, 0, 0, 255);
    draw_rect(vec2(10, 10), vec2(100, 100), c, 1.0, 4.0, 15);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

// RIGHT — AngelScript syntax, AS API, AS lifecycle
int main() {
    register_callback(on_tick, 16, 0);
    return 1;
}

void on_tick(int id, int data_index) {
    draw_rect_filled(10.0f, 10.0f, 100.0f, 100.0f,
                     255, 0, 0, 255, 4.0f, RR_ALL);
}
```

**Why:** AngelScript is a separately registered host language with its own bindings. The Enma and AS APIs cover overlapping domains but the function signatures, type registrations, and constants are independent. Always confirm the call in `docs/perception/angelscript/<area>-api.md` before writing it.

---

## 2. Handles vs Values — Know Which You're Holding

**AngelScript distinguishes reference handles (`Type@`) from value types. PCX types use both, and the rule for each is in the doc.**

A handle is `Type@` — a reference-counted pointer. Assignment with `=` copies the handle; assignment with `@=` rebinds it. Method calls on a null handle throw. Value types use `=` for deep copy; you cannot have a "null" value.

```cpp
// Handle syntax — explicit @, null-checkable, ref-counted
proc_t@ p = ref_process("game.exe");      // ref_process returns a handle
if (p is null) { log("process not found"); return 0; }
if (!p.alive()) { p.deref(); return 0; }   // also deref when alive returns false

// Value syntax — vec3, color tuples, math types are typically values
Vector3 pos(1.0f, 2.0f, 3.0f);             // direct construction, no @
Vector3 copy = pos;                         // deep copy
```

The PCX docs are explicit about which types are handle-only, value-only, or both — *check the API page for each type you instantiate*. `proc_t` is documented as a handle; never declare it without `@` and never skip `is null` after `ref_process`.

```cpp
// WRONG — proc_t without handle syntax; may compile depending on registration
//         but ref_process returns a handle, and you lose the null-check pattern
proc_t p = ref_process("game.exe");
uint64 base = p.base_address();   // throws if process didn't open

// RIGHT
proc_t@ p = ref_process("game.exe");
if (p is null || !p.alive()) { return 0; }
uint64 base = p.base_address();
```

**Why:** A null handle dereference is a runtime exception that kills your script. Value-vs-handle confusion is the #1 source of `.as` crashes on PCX. The doc for each type tells you which one it is; check it once, write the right syntax forever.

---

## 3. Always `deref()` When You're Done — Even on Failure

**`proc_t` is reference-counted. You MUST call `deref()` to release it. The docs are explicit: even if `alive()` returns false, deref the handle.**

This is unique to AngelScript on PCX. The Enma equivalent (`ref_process` returning a `proc_t` value) is RAII-managed; the AngelScript version is not. A script that leaks `proc_t` handles will accumulate them across reloads.

```cpp
// WRONG — early return without deref leaks the handle
int main() {
    proc_t@ p = ref_process("game.exe");
    if (p is null) return 0;
    if (!p.alive()) return 0;            // LEAK — never derefed
    // ... do work ...
    p.deref();
    return 0;
}

// RIGHT — single exit path, or deref on every exit
int main() {
    proc_t@ p = ref_process("game.exe");
    if (p is null) return 0;
    if (!p.alive()) { p.deref(); return 0; }
    // ... do work ...
    p.deref();
    return 0;
}

// BETTER — for persistent scripts, store the handle globally and deref in on_unload
proc_t@ g_proc = null;

int main() {
    @g_proc = ref_process("game.exe");
    if (g_proc is null || !g_proc.alive()) { return 0; }
    register_callback(on_tick, 16, 0);
    return 1;
}

void on_unload() {
    if (g_proc !is null) {
        g_proc.deref();
        @g_proc = null;
    }
}
```

Note the `@=` operator for rebinding handle assignments (`@g_proc = ...`); plain `=` between handles invokes the value-copy path on most PCX types and will not compile.

**Why:** Leaked handles keep the underlying process reference alive past script unload. Across many script reloads in an editing session, this accumulates resource pressure and can prevent re-attach to the target. The deref pattern is cheap; making it a habit costs you nothing and saves a class of bug.

---

## 4. `float` Is `float32` — Use `f` Suffixes; `double` Promotes Silently

**AngelScript uses `float` for 32-bit and `double` for 64-bit. Literal `1.5` is `double`. Render APIs and vertex math expect `float`. Use `1.5f` literals.**

This mirrors C/C++. The AS compiler will silently promote `float` to `double` when mixed in arithmetic, then narrow the result back at the call boundary — a path that can lose precision in tight render loops. Be explicit.

```cpp
// WRONG — double literals everywhere
float vw, vh; get_view(vw, vh);
float cx = vw * 0.5;                      // promotes vw to double, narrows result
draw_rect_filled(cx - 100, cy - 50, 200, 100,
                 40, 40, 40, 255, 8.0, RR_ALL);  // 8.0 is double → 8.0f conversion

// RIGHT — f suffix on every float literal that feeds a float API
float vw, vh; get_view(vw, vh);
float cx = vw * 0.5f;
draw_rect_filled(cx - 100.0f, cy - 50.0f, 200.0f, 100.0f,
                 40, 40, 40, 255, 8.0f, RR_ALL);
```

Color components are integers (0-255) in the PCX AS draw API — no `f` suffix on those. Rounding, dimensions, positions are floats — `f` suffix.

**Why:** AS's implicit promotion does the right thing for correctness but pays in a constant stream of `cvtss2sd` / `cvtsd2ss` around every literal. In a render path hit at 144 Hz, that's measurable. The `f` suffix is also a clarity signal — when you read the code later, you can tell what's a pixel coordinate (`100.0f`) and what's a count or flag (`100`).

---

## 5. Out Parameters Use `&out` — Not `out`, Not Pointers

**AngelScript out parameters are reference parameters declared `&out` (write-only) or `&inout` (read-write). `&in` is read-only by reference. These are *part of the declaration*, not call-site syntax.**

```cpp
// Declaring an out-param function
void get_view(float &out width, float &out height);
bool world_to_screen(const Vector3 &in world, Vector2 &out screen);

// Calling it — just pass the variables, no `&` at call site
float vw, vh;
get_view(vw, vh);                          // AS handles the reference

Vector2 screen;
if (world_to_screen(player_pos, screen)) {
    draw_circle_filled(screen.x, screen.y, 4.0f, 255, 0, 0, 255);
}
```

Three common mistakes:

- Declaring `out` without `&` — compile error, AS requires the reference qualifier
- Trying to write to `&in` — read-only, compile error
- Using `&inout` when you only write — silently legal but confusing; prefer `&out` when you mean "I will write this"

```cpp
// WRONG — bare `out` is C# syntax, not AS
void get_view(out float width, out float height);

// WRONG — & at call site is C++ syntax
get_view(&vw, &vh);

// RIGHT — & at declaration, plain variable at call
void get_view(float &out width, float &out height);
get_view(vw, vh);
```

**Why:** AS's reference syntax is its own — neither C++ nor C#. Mixing them gives confusing errors. Pin the rule once: `&in` / `&out` / `&inout` go on the parameter declaration; the call site is plain.

---

## 6. `array<T>` Is the Container, Not `T[]`

**AngelScript's standard array is `array<T>`, registered as part of the array add-on (per `docs/perception/angelscript/overview.md`). Do not use `T[]` — that is Enma syntax.**

```cpp
// WRONG — Enma syntax
uint64[] entities;
entities.push(0x12345);

// RIGHT — AngelScript syntax
array<uint64> entities;
entities.insertLast(0x12345);              // not push — check array docs for full API
uint count = entities.length();             // length() returns uint
for (uint i = 0; i < count; i++) {
    log("ent " + i + " = 0x" + formatInt(entities[i], "X", 16));
}
```

The AS array methods are `insertLast`, `removeLast`, `insertAt`, `removeAt`, `length`, `resize`, `sortAsc`, `sortDesc`, `find` — not the Enma `push`/`pop`/`contains`/`slice` set. The signatures and return types come from the AS standard library and are documented in the AngelScript reference (search "array" in the AS docs); read it once when you need a method you haven't used.

**Why:** `T[]` is a compile error in PCX AS. Even if you remember `array<T>`, defaulting to Enma method names (`push`, `pop`) will fail. The script-helper exception messages are clear, but the time wasted on a 30-second lookup adds up across an editing session.

---

## 7. Use `dictionary` for Maps, Not `map<K,V>`

**`dictionary` is AS's string-keyed map. There is no generic `map<K,V>` in the registered surface (per `docs/perception/angelscript/overview.md`).**

```cpp
// WRONG — Enma map syntax
map<string, int32> counts;
counts.set("a", 1);
int32 v = counts.get("a");

// RIGHT — AS dictionary
dictionary counts;
counts["a"] = 1;
int v;
if (counts.get("a", v)) {                  // get returns bool; out-param the value
    log("a = " + v);
}
```

Dictionary keys are always `string`. Values are `any`-typed (stored as `?` boxed values); reading them requires the typed `get(key, out_value)` form to unbox correctly. If you need a non-string key, encode it as a string (`formatInt(addr, "X")` for addresses) or use parallel arrays.

**Why:** AS's type system doesn't carry through generic K/V parameters in the same way Enma's does. The boxed-`any` pattern via `dictionary` is the idiomatic substitute. Mis-typing the `get` form is the common error — always use the two-arg form with a typed output variable.

---

## 8. Render API Takes Raw RGBA Ints, Not `color` Structs

**The PCX AS render API is positional-args-style: pass red, green, blue, alpha as separate `uint8`-range integers (0-255). There is no `color` value type to wrap them in the way Enma does.**

```cpp
// WRONG — Enma-style color struct
color c(255, 100, 50, 200);
draw_rect_filled(10, 10, 100, 100, c, 4.0f, RR_ALL);

// RIGHT — raw rgba ints inline
draw_rect_filled(10.0f, 10.0f, 100.0f, 100.0f,
                 255, 100, 50, 200, 4.0f, RR_ALL);

// For text — same pattern with optional shadow color
uint64 font = get_font20();
draw_text("HUD", 10.0f, 10.0f,
          255, 255, 255, 255,                // fg rgba
          font, TE_SHADOW,
          0, 0, 0, 180,                       // shadow rgba
          1.0f, true);                        // shadow dist, centered
```

This means colors don't carry through assignments cleanly. If you need named colors, define them as four constants each:

```cpp
const uint8 FG_R = 255, FG_G = 200, FG_B = 50, FG_A = 255;
const uint8 BG_R =   0, BG_G =   0, BG_B =  0, BG_A = 180;

void on_tick(int id, int data_index) {
    draw_rect_filled(10.0f, 10.0f, 200.0f, 50.0f, BG_R, BG_G, BG_B, BG_A, 4.0f, RR_ALL);
    draw_text("HUD", 20.0f, 25.0f, FG_R, FG_G, FG_B, FG_A,
              get_font20(), TE_NONE, 0,0,0,0, 0.0f, false);
}
```

**Why:** The AS render API is wide-call-shaped intentionally — the marshaling cost to host C++ for a `color` struct would dominate the call. Accepting integers directly maps to a single C function call with stack arguments. Embrace the verbosity; it pays in performance and clarity.

---

## 9. `register_callback` — Two-Argument Callback Signature, Interval in Milliseconds

**Callbacks registered with `register_callback(fn, interval_ms, data_index)` are invoked with `void on_X(int id, int data_index)`. The id is the callback id from `register_callback`; data_index is the third arg you passed at registration, so one function can serve many registrations.**

```cpp
// Two callbacks, same function, different data_index — common pattern for
// running the same logic against multiple targets
int g_cb_fast = 0;
int g_cb_slow = 0;

int main() {
    g_cb_fast = register_callback(on_tick, 8,   0);  // ~120 Hz, data 0
    g_cb_slow = register_callback(on_tick, 100, 1);  // 10 Hz,   data 1
    return 1;
}

void on_tick(int id, int data_index) {
    if (data_index == 0) {
        // hot path — runs every 8 ms
        render_overlay();
    } else if (data_index == 1) {
        // cold path — runs every 100 ms
        refresh_entity_cache();
    }
}

void on_unload() {
    unregister_callback(g_cb_fast);
    unregister_callback(g_cb_slow);
}
```

The interval is in milliseconds and is a *minimum gap*, not a deadline — if your callback runs 12 ms and you asked for 8 ms, the next call is in 12 ms, not -4 ms backed up. Use `100`–`200` for cold-path entity refresh, `8`–`16` for render-frequency updates.

**Why:** Mis-binding the callback signature is a silent failure — the engine looks up the function by name+arity, and if your signature is wrong it either fails to register or registers a different function. `unregister_callback` in `on_unload` is mandatory for clean reloads; an un-unregistered callback survives the script unload and fires against a freed context, which crashes.

---

## 10. Hot Reload Boundaries — Globals Reset, Game State Doesn't

**AS scripts on PCX reload by tearing down the whole script context — globals reset, callbacks are released, the dictionary heap is rebuilt. The game process is untouched. Design your data flow around this.**

What survives a reload:
- The game process and its memory (you re-attach via `ref_process`)
- File-system state (if you persisted config to disk)
- The PCX engine and its GUI state

What does NOT survive a reload:
- Global variables (reset to declaration default)
- Registered callbacks (cleared; you must `register_callback` again in `main`)
- Cached pattern-scan results (re-resolve in `main` or first callback)
- Dictionary entries holding values (rebuilt from disk if you persist them)
- GUI section state (per-section configuration; the GUI API will re-create sections, but their widget states are reinitialized to your defaults)

```cpp
// Typical hot-reload-safe persistent script structure:
proc_t@ g_proc = null;
uint64  g_entity_list = 0;
int     g_cb = 0;

int main() {
    // Re-attach on every load
    @g_proc = ref_process("game.exe");
    if (g_proc is null || !g_proc.alive()) { return 0; }

    // Re-resolve sigs on every load (cheap relative to runtime cost of running)
    uint64 base = g_proc.base_address();
    uint64 size = g_proc.module_size("game.exe");
    uint64 hit  = g_proc.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0) { g_proc.deref(); return 0; }
    g_entity_list = resolve_rip(g_proc, hit, 3, 7);

    // Load config from disk if you persist it
    load_config();

    g_cb = register_callback(on_tick, 16, 0);
    return 1;
}

void on_unload() {
    unregister_callback(g_cb);
    save_config();
    if (g_proc !is null) { g_proc.deref(); @g_proc = null; }
}
```

**Why:** A script that assumes globals survive a reload will read stale or zero data on its first callback after reload — your overlay draws nothing, or worse, against a freed process handle. Treat `main()` as the authoritative initializer that runs from scratch every time.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | AS is not Enma | Look up every API in `docs/perception/angelscript/` before pasting |
| 2 | Handles vs values | `proc_t@` not `proc_t`; null-check with `is null` |
| 3 | Always deref | Even when alive() is false; in `on_unload` for persistent scripts |
| 4 | `float` literals get `f` | `8.0f` not `8.0` — render APIs are float-typed |
| 5 | `&out` at declaration | Call site is plain variable, no `&` |
| 6 | `array<T>` not `T[]` | Methods are `insertLast` / `removeLast` / `length` |
| 7 | `dictionary` for maps | String keys only; `get(key, out_var)` two-arg form |
| 8 | Raw RGBA ints | No `color` struct; pass `r, g, b, a` separately |
| 9 | `register_callback` | Signature `void on_X(int id, int data_index)`; deregister in `on_unload` |
| 10 | Hot-reload safety | Re-attach, re-resolve, re-register every `main()` |

**The 12 game-cheat-guidelines rules still apply** — this skill is the *AngelScript-flavored* version of those discipline rules. Address types are `uint64`, null-check every read, separate update from render, sigs over hardcodes, one feature per file, minimize writes, validate against the live binary. Read `skill://game-cheat-guidelines` for the full discipline.

**Cross-references:** `skill://game-cheat-guidelines` (the 12 rules; Enma-flavored examples but principles apply), `skill://game-hacking-pcx` (doc router), `docs/perception/angelscript/overview.md` (registered modules and addons), `docs/perception/angelscript/proc-api.md`, `docs/perception/angelscript/render-api.md`, `docs/perception/angelscript/life-cycle.md`, `docs/perception/angelscript/gui-api.md`.

---

## Source: `.claude/skills/pcx-bloat-audit/SKILL.md`

---
name: pcx-bloat-audit
description: >
  Whole-project audit for over-engineering in PCX scripts. Scans every .em and
  .as file for wrappers, dead abstractions, duplicate entity walks, unused
  offsets, and config systems that outweigh their settings. Ranked by lines
  recoverable. Use when the user says "audit for bloat", "what can I delete",
  "find over-engineering", "slim this project", or invokes /pcx-bloat-audit.
  One-shot report, does not apply fixes.
license: MIT
---

pcx-bloat-review, project-wide. Scan every `.em` and `.as` file. Rank
findings by lines recoverable, biggest first.

## Tags

Same as pcx-bloat-review:

- `delete:` dead code, unused feature path, speculative abstraction.
- `pcx-api:` hand-rolled thing the PCX API ships. Name the function + doc.
- `inline:` wrapper/class/helper with one caller.
- `yagni:` abstraction with one implementation, config for nothing.
- `shrink:` same logic, fewer lines.
- `merge:` two routines/walks that should be one.

## Hunt List

Scan for these in priority order:

1. **Dead offsets** — sig constants or hardcodes nothing reads. Post-patch debris.
2. **Single-caller wrappers** — functions that wrap one `p.ru64()` / `p.wu64()` call.
3. **Class hierarchies for one feature** — `IFeature`, `BaseEntity`, `AbstractRenderer` with one concrete child.
4. **Config systems vs setting count** — if the config loader is longer than the settings it loads, flag it.
5. **Duplicate entity walks** — two routines independently iterating the same list.
6. **Files exporting one symbol** — `utils.em` with one function, `types.em` with one typedef.
7. **Unused imports** — `import` statements for modules nothing in the file calls.
8. **Commented-out code blocks** — not `// defer:` or `// UNVERIFIED`, just dead code behind `//`.

## Output

One line per finding, ranked by lines recoverable:

```
<tag> <what to cut>. <replacement or "nothing">. [<file>:<lines>] (-<N> lines)
```

End with:

```
net: -<N> lines, -<M> files possible across <P> findings.
```

Nothing to cut: `Lean already. Ship.`

## Boundaries

Complexity only. Does not flag correctness, security, or performance issues.
Does not touch `// defer:` or `// UNVERIFIED` markers — those are
deliberate/tracked. Does not apply fixes.

---

## Source: `.claude/skills/pcx-bloat-review/SKILL.md`

---
name: pcx-bloat-review
description: >
  Code review focused on over-engineering in PCX scripts. Finds what to delete:
  proc_t wrappers, entity managers for three entities, config systems for two
  settings, class hierarchies for one feature. One line per finding. Use when
  the user says "review for bloat", "is this over-engineered", "what can I
  delete", or invokes /pcx-bloat-review. Complements correctness review — this
  one only hunts unnecessary complexity in Enma/AngelScript scripts.
license: MIT
---

Review PCX script diffs for unnecessary complexity. One line per finding.
The diff's best outcome is getting shorter.

## Format

`L<line>: <tag> <what>. <replacement>.`, or `<file>:L<line>: ...` for
multi-file diffs.

## Tags

- `delete:` dead code, unused feature path, speculative abstraction. Replacement: nothing.
- `pcx-api:` hand-rolled thing the PCX API already ships. Name the function + doc page.
- `inline:` wrapper/class/helper with one caller. Inline it.
- `yagni:` abstraction with one implementation, config nobody sets, manager for one thing.
- `shrink:` same logic, fewer lines. Show the shorter form.
- `merge:` two routines/walks that should be one. Name the merge.

## PCX-Specific Hunts

- **proc_t wrappers** — `ReadMemory()` / `ReadEntity()` functions that just call `p.ru64()` with no added validation. The proc API *is* the interface.
- **Entity managers / registries** — `EntityManager`, `FeatureRegistry`, `IFeature` interface for ≤3 features. Three routines registered in `main()` is the framework.
- **Config systems for few settings** — JSON/file config loader for 2-5 `bool` toggles. A `bool g_esp = true;` + sidebar checkbox is the config system.
- **Color/theme abstractions** — `ThemeManager`, `ColorScheme` classes when `color(r,g,b,a)` constructed per-frame costs nothing.
- **Over-split files** — `utils.em` exporting one function, `types.em` defining one typedef. Inline into the caller.
- **Duplicate entity walks** — two `on_update` routines walking the same entity list independently. One walk, two consumers.
- **Dead offset blocks** — sig constants or hardcoded offsets that nothing reads anymore. Post-patch leftover.

## Examples

✅ `esp.em:L12-38: inline: ReadEntity() wraps p.ru64() once with no guard. Inline the call, save 26 lines.`

✅ `main.em:L5-44: yagni: FeatureRegistry class for 2 features. register_routine() twice in main(), done.`

✅ `menu.em:L80-130: yagni: JSON config loader for 3 bools. bool globals + sidebar checkbox, 6 lines.`

✅ `globals.em:L22: delete: g_old_entity_list — nothing reads it since the sig update.`

✅ `esp.em:L60, radar.em:L40: merge: both walk entity_list independently. One walk in on_update, both draw in on_render.`

✅ `utils.em:L1-8: inline: exports only clamp(). Move to the one file that calls it, delete utils.em.`

## Scoring

End with: `net: -<N> lines, -<M> files possible.`

Nothing to cut: `Lean already. Ship.`

## Boundaries

Complexity only. Correctness bugs (wrong offsets, missing null guards, sign
extension), security (detection surface), and performance (read frequency)
belong to a normal review pass.

Does not touch `// defer:` comments — those are tracked deliberately.
Does not apply fixes, only lists them.

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

## Source: `.claude/skills/pcx-debug-overlay/SKILL.md`

---
name: pcx-debug-overlay
description: >
  Pattern for shipping diagnostic and profiler output as a separate, gated
  overlay rather than mixing it into the production rendering. Triggers when
  debugging a script, building a support-mode panel, profiling a slow path,
  or creating a diagnostic vs release build of the same code.
license: MIT
---

# Debug Overlay — Diagnostic Surfaces Separate from the Production Overlay

The pattern for shipping diagnostic / profiler / address-dump information as a separate, gated overlay rather than mixed into the production rendering. Companion to `pcx-perf-budget` (which gives the timing primitives) and `gui-design-patterns` (which says "no debug section by default"). This skill names the structure that lets you ship a script that's diagnosable when you need it and clean when you don't.

**Trigger when:** the user is debugging a script that "isn't working," wants to ship a script with a built-in support-mode panel, profiling a feature to find a slow path, building a diagnostic build vs a release build of the same code, debugging "the AI says it resolved the sig but the script does nothing."

**Prerequisite:** `skill://pcx-perf-budget` for the `mono_us()`-based profiler recipe this skill consumes; `knowledge/gui-design-patterns.md` section "Don't ship a debug panel by default" for the layout discipline this skill extends.

---

## Trigger

Debugging a non-working script, building a support-mode panel for end users, profiling a script's per-routine costs, tracing why an offset resolution succeeded but a read returns 0, designing a script that needs to be diagnosable in the field without the user having to grep logs.

---

## 1. Two Overlays: Production and Diagnostic — Always Separate

**Production overlay shows what the user wants to see (ESP boxes, HUD, target indicators). Diagnostic overlay shows what the script knows about itself (sigs resolved, addresses, profiler timings, error counts). Never mix.**

When you mix them, the user permanently sees diagnostic noise during normal play, and you can't ship a diagnostic-rich build to a tester without also shipping the noise to everyone else. The separation is the only way to have both.

```cpp
// WRONG — diagnostic info in the production render path
void on_render(int64 data) {
    // ... ESP drawing ...

    // Inline diagnostic — every user sees this, every match
    draw_text(format("entity_list=0x{x} count={d}", g_entity_list, g_ent_count),
              vec2(10.0, 10.0), color(255, 255, 0, 255),
              get_font20(), 1, color(0, 0, 0, 200), 1.0);
}

// RIGHT — diagnostic overlay is its own routine, its own render path
void on_render(int64 data) {
    // ... ESP drawing only ...
}

void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    // ... diagnostic drawing, separately registered, separately controlled ...
}

int64 main() {
    // Both registered; the diagnostic one no-ops when g_diag_enabled is false
    register_routine(cast<int64>(on_render),            0);
    register_routine(cast<int64>(on_render_diagnostic), 0);
    return 1;
}
```

The separation is also a CPU-budget thing: when `g_diag_enabled` is false, the diagnostic routine no-ops on the first line and costs nothing. When it's true, it draws every frame. Letting users (or you, in development) toggle that with a single global is the discipline.

**Why:** Mixed render paths are impossible to ship to two audiences. Separated render paths let you ship one binary that's clean by default and rich-on-demand. Cost is one extra global, one extra routine registration; benefit is permanent.

---

## 2. The Diagnostic Overlay Has Five Standard Sections

**Diagnostic overlays converge on the same shape across projects. Pin it once; reuse it.**

The five sections, in display order:

1. **Process & module status** — `g_proc.alive()` result, base address, module size, whether base resolution succeeded.
2. **Sig resolution status** — per-named-sig: hit address (or 0), resolved address (after RIP), uniqueness margin (if you ran the checker at build time).
3. **Runtime data sanity** — first few entity-list entries, local-player address, view-matrix sample value, whether the values look plausible (in range, non-zero, etc.).
4. **Profiler readouts** — per-routine `avg / max / count` from the `pcx-perf-budget` profiler recipe.
5. **Error counters** — counts of failed reads, null pointer cases caught, sig-resolution fallbacks, exception catches. (Use atomic counters per `addon-atomic` if features can write to them concurrently.)

```cpp
void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;

    float64 x = 10.0;
    float64 y = 200.0;
    float64 line_h = 16.0;
    uint64 font = get_font20();
    color fg = color(220, 220, 220, 255);
    color hdr = color(255, 200, 80, 255);
    color shadow = color(0, 0, 0, 180);

    // Section 1: Process & module
    draw_text("[ Process ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  alive: {s}  base: 0x{x}  size: 0x{x}",
                     g_proc.alive() ? "yes" : "no", g_module_base, g_module_size),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h + 4.0;

    // Section 2: Sig resolution
    draw_text("[ Sigs ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  entity_list: hit=0x{x} resolved=0x{x}",
                     g_sig_entity_list_hit, g_off_entity_list),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  view_matrix: hit=0x{x} resolved=0x{x}",
                     g_sig_view_matrix_hit, g_off_view_matrix),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h + 4.0;

    // Section 3: Runtime sanity
    draw_text("[ Runtime ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  ent count: {d}  first ent: 0x{x}",
                     g_ent_count, g_first_ent_ptr),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h + 4.0;

    // Section 4: Profiler (read from pcx-perf-budget bucket accumulators)
    draw_text("[ Profile ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    for (int32 i = 0; i < NUM_BUCKETS; i++) {
        if (g_bucket_count[i] == 0) continue;
        int64 avg = g_bucket_total_us[i] / g_bucket_count[i];
        draw_text(format("  {s}: avg {d}us  max {d}us",
                         g_bucket_name[i], avg, g_bucket_max_us[i]),
                  vec2(x, y), fg, font, 1, shadow, 1.0);
        y += line_h;
    }
    y += 4.0;

    // Section 5: Error counters
    draw_text("[ Errors ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  null reads: {d}  sig fallbacks: {d}",
                     g_err_null_reads, g_err_sig_fallbacks),
              vec2(x, y), fg, font, 1, shadow, 1.0);
}
```

The five-section structure is enough to diagnose ~90% of script issues without further instrumentation. When a user reports "the script isn't working," the screenshot of this panel answers the question.

**Why:** Ad-hoc diagnostics in different scripts use different shapes; you waste mental energy each time figuring out which info is shown where. The five-section structure is a contract — once your team agrees on it, every script's diagnostic surface is interchangeable.

---

## 3. Gate the Toggle Behind a Hotkey, Not a GUI Widget Default

**The diagnostic overlay should default to OFF and be toggleable via a hotkey. A GUI checkbox is fine *as well*, but the hotkey is the primary control.**

End users won't navigate to a GUI section just to enable diagnostics — they'll Discord-message the author asking "why doesn't this work?" A hotkey they can hit gives them (and you, helping them) a 1-second path to the diagnostic info.

```cpp
bool   g_diag_enabled = false;
int32  g_diag_hotkey  = 0x77;   // VK_F8 by default

int64 main() {
    // ... process attach ...

    int64 sec = create_section("Debug");
    section_checkbox(sec, "Show diagnostic overlay", g_diag_enabled);
    section_keybind(sec, "Toggle diagnostic hotkey", g_diag_hotkey);
    section_separator(sec);
    section_label(sec, "Hotkey toggles section 1-5 readout.");

    register_routine(cast<int64>(on_update),            0);
    register_routine(cast<int64>(on_render),            0);
    register_routine(cast<int64>(on_render_diagnostic), 0);
    return 1;
}

void on_update(int64 data) {
    if (is_key_pressed(g_diag_hotkey)) {
        g_diag_enabled = !g_diag_enabled;
    }
    // ... feature update logic ...
}
```

When the user reports a problem, the support cycle is:

```
You:    "Hit F8 in-game, screenshot the panel, paste it to me."
User:   [screenshot]
You:    "entity_list resolved=0 — your binary doesn't match the supported version.
        See README requirements."
```

The diagnostic panel + hotkey reduces a 20-message back-and-forth to a 2-message exchange.

**Why:** Hotkeys are the universal "I need diagnostic info now" gesture. GUI checkboxes are good for opt-in features the user explicitly knows they want; diagnostic toggles need to be reachable when the user is *confused*, which is when they're not navigating GUI panels.

---

## 4. Diagnostic Routines Are Read-Only — Never Modify Game State

**The diagnostic overlay reads everything it shows. It never writes, never patches, never calls into game functions, never modifies the script's own behavior.**

This is the rule that lets you leave the diagnostic surface enabled in production builds for support purposes — it cannot break anything by being on. If the diagnostic does any of these:

- Calls `memory_write` to patch a value
- Calls a game function via a hook
- Modifies any other feature's globals (e.g. forcing `g_aim_target_id = X` "to test")
- Reads in a way that has side effects (rare, but some MMIO regions do)

...then the diagnostic itself is now a feature, with its own correctness concerns. It needs its own evidence entries (`skill://re-evidence-log`), its own validation, its own bug surface. Conflating "diagnostic" and "active feature" produces neither well.

The cost of pure-read diagnostics: occasionally you want to verify a write path. Don't put that in the diagnostic overlay; put it in a *separate* "lab" feature in `Misc` with its own master toggle, its own warnings, its own GUI gating. The lab feature is opt-in destructive; the diagnostic overlay is opt-in observational.

```cpp
// RIGHT — pure read diagnostic
void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    // reads only — g_proc.ru64, g_proc.read_memory, accumulator dereferences
}

// WRONG — diagnostic that also writes
void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    if (is_key_pressed(VK_F9)) {
        g_proc.write_u32(g_off_health, 100);   // "just testing health write"
    }
    // ... drawing ...
}

// RIGHT — separate lab feature, GUI-gated, distinct toggle
bool g_lab_enabled = false;
void on_update_lab(int64 data) {
    if (!g_lab_enabled) return;
    if (is_key_pressed(VK_F9)) {
        g_proc.write_u32(g_off_health, 100);   // intentional, opted-in
    }
}
```

**Why:** A read-only diagnostic can stay enabled during gameplay without consequence; an active diagnostic can't. The discipline preserves the diagnostic overlay's "safe to leave on" property, which is what makes it useful for support.

---

## 5. Atomic Counters for Cross-Routine State

**When multiple routines (update + render + features) increment error counters or sample profile buckets, use atomic types (`addon-atomic`) — not plain integers.**

PCX scripts can have multiple routines firing on different scheduler cadences; if both `on_update` and `on_render` write to `g_err_null_reads`, the increments can interleave and lose counts on plain integers. `aint32` / `aint64` (per `docs/enma/addon-atomic.md`) handle this correctly without locks.

```cpp
import "atomic";

aint32 g_err_null_reads;
aint32 g_err_sig_fallbacks;
aint64 g_total_reads;

void on_update(int64 data) {
    uint64 entity = g_proc.ru64(g_off_entity_list);
    g_total_reads.add(1);                  // atomic increment
    if (entity == 0) {
        g_err_null_reads.add(1);
        return;
    }
    // ...
}

void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    // load() reads the current atomic value
    int32 nulls = g_err_null_reads.load();
    int64 total = g_total_reads.load();
    draw_text(format("  null reads: {d} / {d} total", nulls, total),
              vec2(x, y), fg, font, 1, shadow, 1.0);
}
```

For single-writer counters (only `on_update` increments, only `on_render_diagnostic` reads), plain integers are fine — atomic is overkill. The atomic discipline applies when multiple writers exist.

**Why:** Lost counts in error counters silently hide bugs (you report "10 null reads" when the actual was 47 because 37 increments interleaved and overwrote each other). Atomics are cheap; the bug they prevent is invisible.

---

## 6. Ship a Diagnostic-Only Build for Power Users

**Some users want the diagnostic build by default — the streamer doing tech-content, the long-tail debugger, the script's contributor. Ship two `.emb` artifacts: production (`script.emb`) and diagnostic (`script-debug.emb`).**

The split:

| Build | `g_diag_enabled` default | `g_diag_hotkey` works | Extra debug features |
|---|---|---|---|
| `script.emb` (production) | `false` | yes | none |
| `script-debug.emb` (diagnostic) | `true` | yes | profiler dumps to file, extra logging |

The implementation: a single `#define` (per `docs/enma/lang-pre-processor.md`) controls the build flavor:

```cpp
// At the top of main.em
#define BUILD_FLAVOR_DEBUG     // comment out for production

#ifdef BUILD_FLAVOR_DEBUG
    bool g_diag_enabled_default = true;
#else
    bool g_diag_enabled_default = false;
#endif

bool g_diag_enabled = g_diag_enabled_default;

#ifdef BUILD_FLAVOR_DEBUG
    // Extra debug-only routines
    void on_update_log_to_file(int64 data) {
        // periodic snapshot of profiler buckets to disk for offline analysis
    }
#endif

int64 main() {
    // ... process attach ...
    register_routine(cast<int64>(on_render),            0);
    register_routine(cast<int64>(on_render_diagnostic), 0);
    #ifdef BUILD_FLAVOR_DEBUG
        register_routine(cast<int64>(on_update_log_to_file), 0);
    #endif
    return 1;
}
```

Build both flavors as part of your release process (see `skill://script-bundler`). Ship the production one as the headline download; ship the debug one as a "for support / contributors" link in the README.

**Why:** Two builds from one source is cheap (one `#define` swap, two compilations); the value to users who need diagnostics-by-default (streamers, contributors, support) is real. The alternative is shipping one build and asking users to enable diagnostics manually each time — fine for most, friction for the power users you want engaged.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | Two overlays, always separate | Production renders user-visible features; diagnostic renders script-internal state |
| 2 | Five standard sections | Process / Sigs / Runtime / Profile / Errors — covers ~90% of "script isn't working" reports |
| 3 | Hotkey-gated, off by default | Default off, F8 toggles on — reachable when the user is confused, invisible otherwise |
| 4 | Read-only diagnostics | No writes, no hooks; lab/test features are separate, opt-in destructive features |
| 5 | Atomic counters for cross-routine state | `aint32` / `aint64` for multi-writer counters; plain ints for single-writer |
| 6 | Two builds: production + diagnostic | `#define BUILD_FLAVOR_DEBUG` switch; both shipped, production headline |

**Cross-references:** `skill://pcx-perf-budget` (the `mono_us()` profiler recipe section 4 consumes); `knowledge/gui-design-patterns.md` (the "no debug panel by default" rule this skill extends); `skill://script-bundler` (the two-build process); `skill://re-evidence-log` (the lab features' citation discipline); `docs/enma/addon-atomic.md` (the atomic types section 5 uses); `docs/enma/lang-pre-processor.md` (the `#ifdef` mechanism section 6 uses).

---

## Source: `.claude/skills/pcx-defer-ledger/SKILL.md`

---
name: pcx-defer-ledger
description: >
  Harvest every `// defer:` comment in the PCX project into a debt ledger.
  Tracks deliberate shortcuts (global handles, hardcoded colors, single-walk
  assumptions) so deferrals don't rot into permanent hacks. Use when the user
  says "defer ledger", "what did we defer", "list shortcuts", "show debt", or
  invokes /pcx-defer-ledger. One-shot report, changes nothing.
license: MIT
---

Every deliberate shortcut is marked `// defer: <ceiling>, <trigger>`. This
collects them into one ledger so a deferral can't quietly become permanent.

## Scan

Search `.em` and `.as` files for `// defer:` markers, skipping build output:

```
grep -rnE '// ?defer:' --include='*.em' --include='*.as' .
```

Also scan for `// UNVERIFIED` — those are offset-confidence markers, tracked
separately but surfaced in the same report.

## Output

### Defer markers

One row per marker, grouped by file:

```
<file>:<line> — <what was simplified>. ceiling: <limit>. trigger: <when to revisit>.
```

Pull ceiling and trigger from the comment. The convention is
`// defer: <ceiling>, <trigger>`.

### Rot risk

Flag `no-trigger` on any `// defer:` that names no upgrade condition — those
rot silently.

### Unverified offsets

Separate section:

```
<file>:<line> — <offset/field>. source: UNVERIFIED.
```

These aren't shortcuts, they're confidence gaps. Surface them so they can be
resolved against the live target.

### Summary

```
<N> defer markers (<M> with no trigger)
<P> UNVERIFIED offsets
```

Nothing found: `No deferred debt. Clean ledger.`

## Boundaries

Reads and reports only, changes nothing. To persist: ask, and it writes the
ledger to `DEFER-LEDGER.md` at the project root. One-shot.

---

## Source: `.claude/skills/pcx-enma-discipline/SKILL.md`

---
name: pcx-enma-discipline
description: >
  Behavioral and syntactic rules for writing .em (Enma) scripts on Perception.cx.
  Prevents AngelScript/Lua-reflex errors in the Enma API surface — method names,
  parameter shapes, type system, and lifecycle differ from AS and Lua. Always
  active when editing .em files.
license: MIT
---

# Enma Discipline for Perception.cx

Behavioral and syntactic rules for writing `.em` scripts on Perception.cx. Enma is the **primary** scripting language on PCX and has a distinct C++-like type system, RAII semantics, and value-type APIs that differ from AngelScript (handles, `register_callback`, `array<T>`) and Lua (tables, `on_frame`, `require`). The AI defaults to AS or Lua idioms when editing `.em` files and produces code that does not compile.

**Always active when editing `.em` files.** These rules apply every time you write or edit a Perception.cx Enma script.

**Prerequisite:** `game-cheat-guidelines` skill for the full doc index. **Read the relevant `docs/perception/enma/<file>.md` before writing any API call** — the Enma surface is not the AS surface, and method names, parameter shapes, and constants differ.

---

## Trigger

`.em` file open, Enma syntax visible (`import`, `#pragma once`, `register_routine`, `println`, `color`/`vec2` value types, `cast<T>`), user mentions Enma / `proc_t` value semantics / PCX scripting in Enma context, any code referencing `docs/perception/enma/`.

---

## 1. Enma Is Not AngelScript or Lua — Don't Paste AS/Lua APIs

**The PCX Enma API has different function names, different parameter shapes, and different idioms than AS and Lua. They look similar; they are not interchangeable.**

The most common bug in AI-written `.em` scripts is pasting AS or Lua API calls verbatim. The script doesn't compile because Enma is a statically typed C++-like language with value semantics, not a garbage-collected handle system (AS) or a dynamic table language (Lua).

| Enma | AngelScript | Lua |
|---|---|---|
| `register_routine(cast<int64>(on_render), 0)` | `register_callback(on_tick, 16, 0)` | `function on_frame()` — no registration |
| `int64 main()` | `int main()` | `function main()` — returns number |
| `void on_render(int64 data)` | `void on_tick(int id, int data_index)` | `function on_frame()` — no args |
| `println(...)` | `log(...)` | `log(...)` |
| `color(r,g,b,a)` then `draw_rect(vec2(pos), vec2(size), color, ...)` | `draw_rect_filled(x, y, w, h, r, g, b, a, rounding, flags)` | `draw_rect_filled(x, y, w, h, r, g, b, a, rounding, flags)` |
| `get_view_width()` / `get_view_height()` | `get_view(vw, vh)` — out-param | `vw, vh = get_view()` — multi-return |
| `proc_t g_proc;` (value, RAII) | `proc_t@ g_proc;` (handle, ref-counted) | `g_proc = ref_process(...)` — userdata |
| `T[]` arrays with `.push()`, `.pop()` | `array<T>` with `.insertLast()`, `.removeLast()` | `{}` tables with `table.insert()` |
| `map<K,V>` with `.set()`, `.get()` | `dictionary` with string keys only | `table` as map |
| `cast<T>(x)` | `T(x)` or `float(x)` — C-style cast | `tonumber(x)` — no generic cast |
| `#pragma once` + `import "module"` | `#pragma once` + `#include "module"` | No header guards; `require()` |

```cpp
// WRONG — AS idioms in an .em file
int main() {
    proc_t@ p = ref_process("game.exe");      // AS handle syntax
    if (p is null) return 0;                  // AS null-check
    register_callback(on_tick, 16, 0);        // AS registration
    log("loaded");                            // AS log function
    return 1;
}

// WRONG — Lua idioms in an .em file
function main()
    g_proc = ref_process("game.exe")          -- Lua assignment
    if not g_proc then return 0 end           -- Lua nil-check
    return 1
end
function on_frame() end                       -- Lua lifecycle

// RIGHT — Enma syntax, Enma API, Enma lifecycle
int64 main() {
    proc_t p = ref_process("game.exe");       // value type, RAII
    if (!p.alive()) { println("not found"); return 0; }
    register_routine(cast<int64>(on_render), 0);
    println("[main] loaded");
    return 1;
}

void on_render(int64 data) {
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    draw_rect_filled(vec2(10, 10), vec2(100, 50),
                     color(255, 100, 50, 200), 4.0, 15);
}
```

**Why:** Enma is a separately compiled host language with its own type system and standard library. The AS and Lua bindings cover overlapping domains but the function signatures, type registrations, and constants are independent. Always confirm the call in `docs/perception/enma/<area>-api.md` before writing it.

---

## 2. Value Semantics — No Handles, No `@`, No `deref()`

**Enma uses value semantics and RAII for `proc_t` and most PCX types. There are no reference handles (`@`), no `@=` rebinding, and no `deref()` call. The process reference is managed automatically.**

```cpp
// WRONG — AS handle syntax in Enma
proc_t@ p = ref_process("game.exe");
if (p is null) return 0;
p.deref();

// RIGHT — Enma value semantics
proc_t p = ref_process("game.exe");
if (!p.alive()) { println("not found"); return 0; }
// p is cleaned up automatically when it leaves scope
```

`proc_t` in Enma is a value type that wraps an internal handle. Copying it (`proc_t copy = p;`) copies the internal reference, but RAII means destruction at end of scope — you do not call `deref()`. For global persistence, store the value directly; it will be destroyed when the script unloads.

```cpp
// Global state — no handle, no null, just a default-constructed proc_t
proc_t g_proc;
uint64 g_base = 0;

int64 main() {
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) return 0;
    g_base = g_proc.base_address();
    return 1;
}
```

**Why:** The AS handle system (ref-counted, manual `deref()`, `@` syntax) does not exist in Enma. Mixing the two produces compile errors on `@` or runtime leaks if you somehow port `deref()` as a no-op. Enma's RAII is simpler: acquire, use, let it die at scope end.

---

## 3. `float64` Is the Default Float; `float32` Is Explicit

**Enma uses `float64` (double-precision) as its default floating-point type. `float32` is explicit. Literal `1.5` is `float64`. Render APIs and math use `float64` unless otherwise documented.**

Unlike AngelScript where `float` means `float32` and `double` means `float64`, Enma's native float is `float64`. The `f` suffix does not exist in Enma — `1.5` is already `float64`.

```cpp
// Enma — float64 by default
float64 smooth = 0.15;        // 0.15 is float64
float32 fov = 30.0f;          // explicit f suffix for float32 ONLY if needed

float64 cx = get_view_width() * 0.5;   // no promotion issues; 0.5 is float64

// WRONG — AS-style float/double confusion
double cx = get_view_width() * 0.5f;   // Enma has no 'double' keyword; use 'float64'
float cx  = get_view_width() * 0.5;    // Enma has no 'float' keyword; use 'float32'
```

**Why:** Enma is closer to C++ than AS. `float64` / `float32` map directly to C++ `double` / `float`. Using `double` or `float` in Enma is a compile error — those keywords don't exist. The default `float64` eliminates the silent promotion issues that plague AS.

---

## 4. Arrays Use `T[]` Syntax — Not `array<T>`, Not Lua Tables

**Enma's standard array is `T[]` with `.push()`, `.pop()`, `.insert()`, `.remove()`, `.length`, and `.contains()`. Do not use `array<T>` — that is AngelScript syntax.**

```cpp
// WRONG — AS syntax
array<uint64> entities;
entities.insertLast(0x12345);

// WRONG — Lua syntax
local entities = {}
table.insert(entities, 0x12345)

// RIGHT — Enma syntax
uint64[] entities;
entities.push(0x12345);
uint64 count = entities.length;       // no () — property, not method
for (uint64 i = 0; i < count; i++) {
    println("ent " + i + " = " + formatInt(entities[i], "h"));
}
```

Enma array methods: `push(v)`, `pop()`, `insert(idx, v)`, `remove(idx)`, `clear()`, `length` (property), `contains(v)`, `slice(start, end)`, `sort()`, `reverse()`. Methods match Enma's C++-like standard library, not AS's.

**Why:** `array<T>` is a compile error in Enma. Even if you remember `T[]`, defaulting to AS method names (`insertLast`, `removeLast`) will fail. The property-vs-method distinction (`length` vs `length()`) also matters.

---

## 5. Maps Use `map<K,V>` — Not `dictionary`, Not Plain Lua Tables

**Enma has a generic `map<K,V>` type with `.set(key, val)`, `.get(key)`, `.remove(key)`, `.contains(key)`, `.keys()`, `.values()`, and `.length`. There is no `dictionary` type (that's AS-only).**

```cpp
// WRONG — AS dictionary
map<string, int32> counts;       // compile error: 'map' is not a type in AS
// Actually AS uses 'dictionary'...

// WRONG — AS dictionary pattern in Enma
dictionary counts;               // compile error: no 'dictionary' in Enma

// RIGHT — Enma map
map<string, int64> offsets;
offsets.set("local_player", 0x12345678);
if (offsets.contains("local_player")) {
    int64 off = offsets.get("local_player");
    println("local_player = " + formatInt(off, "h"));
}
```

Note: Enma's `map<K,V>` requires `K` to support `operator<` (ordered map) or hashing (unordered map). The exact constraints depend on the PCX Enma registration — verify in `docs/perception/enma/overview.md`.

**Why:** AS's `dictionary` is a string-keyed boxed-value map. Enma's `map<K,V>` is closer to C++ `std::map` or `std::unordered_map` with typed keys and values. Using the wrong map type produces compile errors or runtime misbehavior.

---

## 6. Render API Takes `vec2`, `color`, and Other Value Types

**The PCX Enma render API is struct-typed: pass `vec2` for positions/sizes, `color` for RGBA, and `float64` for scalars. Do not pass raw positional args the way AS and Lua do.**

```cpp
// WRONG — AS/Lua raw-positional style in Enma
draw_rect_filled(10.0, 10.0, 100.0, 100.0,
                 255, 100, 50, 200, 4.0, 15);

// RIGHT — Enma value-type style
color bg(30, 30, 40, 230);
draw_rect_filled(vec2(10, 10), vec2(100, 50), bg, 4.0, 15);

// Text — same pattern
draw_text("HUD", vec2(20, 25),
          color(255, 255, 255, 255), get_font20(),
          TE_NONE, color(0, 0, 0, 0), 0.0);
```

Enma value types (`vec2`, `vec3`, `color`) are lightweight stack structs — copying them is cheap. You can construct them inline or cache them:

```cpp
// Named colors are fine in Enma
color BG(30, 30, 40, 230);
color FG(255, 200, 50, 255);

void on_render(int64 data) {
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    draw_rect_filled(vec2(10, 10), vec2(200, 50), BG, 4.0, 15);
    draw_text("HUD", vec2(20, 25), FG, get_font20(), TE_NONE, color(0,0,0,0), 0.0);
}
```

**Why:** The Enma render API was designed around C++-style value semantics. Passing four separate integers for color and four separate floats for rectangle bounds is the AS/Lua binding choice to avoid marshaling structs across the language boundary. In Enma, the structs live on the native side and are passed by value efficiently.

---

## 7. `register_routine` — One-Argument Callback Signature, Data Payload Is `int64`

**Callbacks registered with `register_routine(cast<int64>(fn), data)` are invoked with `void on_render(int64 data)`. The `data` parameter is the second arg you passed at registration.**

```cpp
// Two routines, same function, different data — common pattern
int64 g_routine_update = 0;
int64 g_routine_render = 0;

int64 main() {
    g_routine_update = register_routine(cast<int64>(on_tick), 0);   // data = 0
    g_routine_render = register_routine(cast<int64>(on_tick), 1); // data = 1
    return 1;
}

void on_tick(int64 data) {
    if (data == 0) {
        // update path — runs every frame
        refresh_entity_cache();
    } else if (data == 1) {
        // render path — runs every frame
        render_overlay();
    }
}
```

There is no explicit unregister in Enma — routines are tied to the script lifecycle and are cleaned up on unload. There is no `on_unload` hook in Enma (unlike AS and Lua); cleanup happens via RAII destructors.

**Why:** Enma's `register_routine` takes a function pointer cast to `int64` (the underlying function address) plus an arbitrary `int64` payload. The engine calls the function with that payload. The cast is mandatory because Enma lacks implicit function-to-int conversion. Forgetting `cast<int64>` produces a type mismatch compile error.

---

## 8. Structs Can Have Default Member Initializers

**Enma structs support default member initializers (`bool valid = false;`). Use them to avoid uninitialized garbage. AS does not support this; Lua doesn't have structs at all.**

```cpp
// Enma struct with defaults
struct EntityInfo {
    bool    valid   = false;
    uint64  ptr     = 0;
    int32   health  = 0;
    int32   team    = 0;
    vec3    pos     = vec3(0, 0, 0);
    vec3    head    = vec3(0, 0, 0);
};

// Fixed-size array of structs — also Enma-specific
const int32 MAX_ENTITIES = 64;
EntityInfo g_entities[MAX_ENTITIES];

void reset_entities() {
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        g_entities[i].valid = false;
        g_entities[i].ptr = 0;
    }
}
```

**Why:** Enma's C++ heritage gives it default member initializers and fixed-size arrays. AS requires manual initialization in constructors (which may not even be registered for all types), and Lua uses tables. Leveraging Enma's features makes code cleaner and less error-prone.

---

## 9. Import System: `#pragma once` + `import "module"`

**Enma uses `#pragma once` for header guards and `import "module"` for module imports. Do not use `#include` (C/C++) or `require()` (Lua).**

```cpp
// globals.em — shared header
#pragma once

import "proc";
import "vec";
import "math";
import "color";

const int32 MAX_ENTITIES = 64;

struct EntityInfo {
    bool    valid   = false;
    uint64  ptr     = 0;
    int32   health  = 0;
    int32   team    = 0;
    vec3    pos     = vec3(0, 0, 0);
    vec3    head    = vec3(0, 0, 0);
};

// Fixed-size array declaration
EntityInfo g_entities[MAX_ENTITIES];

// Global state
proc_t g_proc;
uint64 g_base = 0;
uint64 g_size = 0;
```

```cpp
// main.em — entry point
import "globals";
import "offsets";
import "utils";
import "esp";

const string TARGET_PROCESS = "game.exe";

int64 main() {
    g_proc = ref_process(TARGET_PROCESS);
    if (!g_proc.alive()) {
        println("[main] target not found: " + TARGET_PROCESS);
        return 0;
    }

    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size(TARGET_PROCESS);
    if (g_base == 0 || g_size == 0) {
        println("[main] module not ready");
        return 0;
    }

    if (!resolve_all()) {
        println("[main] signature resolution failed");
        return 0;
    }

    // Register update and render routines
    register_routine(cast<int64>(esp_update), 0);
    register_routine(cast<int64>(esp_render), 1);

    println("[main] cheat skeleton loaded");
    return 1;
}
```

**Why:** Enma's module system is import-based with `#pragma once` guards. Each imported module is compiled once and shared. There is no preprocessor `#include` text inclusion — `import` resolves symbols through the module system. Using `#include` will either fail or produce multiple-definition errors.

---

## 10. Hot Reload — Globals Reset, No `on_unload` Hook

**Enma scripts on PCX reload by tearing down the whole script context — globals reset, routines are released. The game process is untouched. There is no `on_unload` lifecycle hook in Enma; cleanup happens through RAII destructors.**

What survives a reload:
- The game process and its memory (re-attach via `ref_process`)
- File-system state (if you persisted config to disk)
- The PCX engine and its GUI state

What does NOT survive a reload:
- Global variables (reset to declaration default / struct initializers)
- Registered routines (cleared; you must `register_routine` again in `main()`)
- Cached pattern-scan results (re-resolve in `main()` or first routine)
- GUI section state (reinitialized to defaults)

```cpp
// Typical hot-reload-safe persistent Enma script structure:
proc_t  g_proc;
uint64  g_entity_list = 0;

int64 main() {
    // Re-attach on every load
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) { return 0; }

    // Re-resolve sigs on every load
    uint64 base = g_proc.base_address();
    uint64 size = g_proc.get_module_size("game.exe");
    uint64 hit  = g_proc.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0) { return 0; }
    g_entity_list = resolve_rip(hit, 3, 7);

    // Register routines
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

void on_render(int64 data) {
    // Draw from cache — no proc reads here
    if (g_entity_list == 0) return;
    // ... render logic ...
}
```

**Why:** Enma lacks `on_unload` because its RAII model means destructors run automatically. A script that assumes globals survive a reload will read stale or zero data on its first routine after reload. Treat `main()` as the authoritative initializer that runs from scratch every time.

---

## 11. Type Casting: Use `cast<T>(x)`, Not C-style or AS-Specific Syntax

**Enma uses `cast<T>(expression)` for explicit type casting. Do not use C-style `(T)expr` or AngelScript's constructor-style `T(expr)` for cross-type casts.**

```cpp
// WRONG — C-style cast (may not be supported in all Enma versions)
uint64 addr = (uint64)disp;

// WRONG — AS constructor-style cast
uint64 addr = uint64(disp);

// RIGHT — Enma cast syntax
uint64 addr = cast<uint64>(disp);
int64 signed = cast<int64>(disp);
float64 f = cast<float64>(i);
```

**Why:** Enma's type system is stricter than C. `cast<T>` is the idiomatic and guaranteed-safe way to convert between unrelated scalar types. Constructor-style casts work for some cases in Enma but `cast<T>` is the documented and preferred form.

---

## 12. Pointer Arithmetic Is Type-Scaled — Not Byte-Wise

**Enma pointer arithmetic scales by the `sizeof(T)`, like C++. There is no `byte*` or `void*` with byte-wise arithmetic in Enma. Use `uint64` for raw byte offsets and cast at read time.**

```cpp
// WRONG — attempting byte-wise pointer arithmetic
int32* p = cast<int32*>(base);
int32 val = p[0x10];   // reads at base + sizeof(int32)*0x10, not base + 0x10!

// RIGHT — uint64 base + offset, read via proc_t
uint64 base = g_proc.base_address();
int32 val = g_proc.r32(base + 0x10);   // exact byte offset

// For struct traversal, keep offsets as uint64
uint64 player = g_proc.ru64(g_entity_list + OFF_LOCAL);
if (player == 0) return;
int32 hp = g_proc.r32(player + OFF_HEALTH);
```

**Why:** Enma's type safety means `T* + n` advances by `n * sizeof(T)` bytes. When reverse-engineering, you operate in raw byte offsets. Keep addresses as `uint64`, add offsets as plain integers, and use `proc_t`'s typed read methods (`r32`, `r64`, `ru64`, `read_vec3`) to reinterpret bytes at the target location.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | Enma is not AS/Lua | Look up every API in `docs/perception/enma/` before pasting |
| 2 | Value semantics | `proc_t` is a value; no `@`, no `deref()`, no `is null` |
| 3 | `float64` default | No `float`/`double` keywords; use `float64` / `float32` |
| 4 | `T[]` arrays | `.push()`, `.pop()`; `length` is a property |
| 5 | `map<K,V>` | Typed keys/values; `.set()`, `.get()`, `.contains()` |
| 6 | Value-type render API | `vec2`, `color` structs; not raw positional args |
| 7 | `register_routine` | `cast<int64>(fn)` + data payload; no unregister needed |
| 8 | Struct defaults | `bool valid = false;` — use default initializers |
| 9 | `import "module"` | `#pragma once` guards; no `#include`, no `require()` |
| 10 | Hot-reload safety | Re-attach, re-resolve, re-register every `main()`; no `on_unload` |
| 11 | `cast<T>(x)` | Explicit cast syntax; no C-style or AS-style |
| 12 | Type-scaled pointers | Use `uint64` offsets + `proc_t` reads; never raw pointer arithmetic |

**The 12 game-cheat-guidelines rules still apply** — this skill is the *Enma-flavored* version of those discipline rules. Address types are `uint64`, null-check every read, separate update from render, sigs over hardcodes, one feature per file, minimize writes, validate against the live binary. Read `skill://game-cheat-guidelines` for the full discipline.

**Cross-references:** `skill://game-cheat-guidelines` (the 12 rules), `skill://game-hacking-pcx` (doc router), `skill://pcx-angelscript-discipline` (AS-specific gotchas, useful when porting), `skill://pcx-lua-discipline` (Lua-specific gotchas, useful when porting), `docs/perception/enma/overview.md` (registered modules and addons), `docs/perception/enma/proc-api.md`, `docs/perception/enma/render-api.md`, `docs/perception/enma/life-cycle.md`, `docs/perception/enma/gui-api.md`.

---

## Source: `.claude/skills/pcx-knowledge-index/SKILL.md`

---
name: pcx-knowledge-index
description: >
  Guide to the three surfaces (llms.txt static index, bundle files, MCP
  server) through which AI tools reach the toolkit corpus, and which to pick
  under which integration model. Always active when working with the
  pcx-ai-toolkit knowledge base from any AI tool (Claude Code, Cursor, Cline,
  Aider, Copilot, Continue, Zed).
license: MIT
---

# PCX Knowledge Index — The Three Ways AI Tools Reach the Toolkit's Corpus

The toolkit publishes its docs / skills / knowledge / templates / tools via three complementary surfaces, each optimized for a different AI-tool integration model. This skill names which surface to reach for under which circumstances, so a session doesn't waste tokens preloading a 4 MB bundle when MCP search would do, and doesn't fail mid-task because the tool only supports `@`-file references and you reached for a search call instead.

**Always active when working with the pcx-ai-toolkit corpus from an AI tool.** Applies to Claude Code, Claude Desktop, Cursor, Cline, Aider, Copilot, Continue, Zed, and any other AI tool that consumes external knowledge.

**Prerequisite:** `tools/build-llms-index.py` (the generator for the static surface), `mcp/pcx-knowledge-mcp/` (the dynamic surface), the per-IDE drop-ins (`rules/CLAUDE.md`, `rules/CURSOR.md`, etc.) for how each tool wires in its preferred surface.

---

## Trigger

About to load the toolkit's docs into AI context, the user asked which doc to use, the AI is preloading too much / too little context, deciding whether to ship the toolkit content as bundles vs MCP server vs both, debugging "the AI doesn't know about the PCX X API," configuring a new AI tool to consume the toolkit.

---

## The Three Surfaces

### 1. `llms.txt` — the Auto-Fetch Convention

Located at `docs/llms.txt` (also `docs/llms-full.txt` for the full bundle).

**What it is.** A structured plain-text index of the entire toolkit, following the Anthropic / Mintlify `llms.txt` convention. ~45 KB; lists every doc, skill, knowledge file, IDE drop-in, template, signature guide, and tool with its title, URL, and one-line description grouped by category.

**Who uses it.** Tools that auto-fetch this convention from a project's root:
- Claude (when given a repo URL, often auto-fetches `<repo>/llms.txt`)
- Cursor (configurable)
- Cline (via project context)
- Several others, growing

**When to reach for it.** First-touch with a new tool, or any time you want the tool to discover the toolkit's surface area without manually `@`-referencing every file.

**Cost.** ~45 KB of context (the index, not the full content). Tiny relative to the value.

### 2. Concatenated Context Packs — the Bundle Surface

Located at `docs/llms-full.txt`, `docs/llms-perception-{enma,angelscript,lua}.md`, `docs/llms-skills.md`, `docs/llms-knowledge.md`.

**What it is.** Per-language and per-category single-file concatenations of the relevant subset of the toolkit. Each file carries every member document inline with stable separators and the original source path preserved.

| Bundle | Scope | Size |
|---|---|---:|
| `llms-full.txt` | Everything (docs / skills / knowledge / rules / templates / signatures) | ~2 MB |
| `llms-perception-enma.md` | Enma language + APIs + Enma-discipline skills + cheatsheet | ~950 KB |
| `llms-perception-angelscript.md` | AngelScript APIs + AS discipline + cheatsheet | ~400 KB |
| `llms-perception-lua.md` | Lua APIs + Lua discipline + cheatsheet | ~215 KB |
| `llms-skills.md` | All 17 skills concatenated | ~300 KB |
| `llms-knowledge.md` | All 20 knowledge references concatenated | ~350 KB |

**Who uses it.** Any tool that accepts a single file as context:
- Aider (`/read docs/llms-perception-enma.md`)
- Copilot (paste-into custom instructions, or `@file` reference)
- Cursor (`@docs/llms-perception-enma.md`)
- Continue (`@files`)
- Any AI editor that has a "load file as context" surface

**When to reach for it.** Tools without MCP support, sessions where you know upfront which language you'll work in (load the matching pack), or anywhere the AI client is stateless across calls and you want a known-fixed context surface.

**Cost.** The chosen bundle's full byte cost loaded into context. The per-language bundles are much smaller than `llms-full.txt`; default to the per-language pack unless you're working across all three.

### 3. The Knowledge MCP Server — the Dynamic Surface

Located at `mcp/pcx-knowledge-mcp/` (Python package).

**What it is.** An MCP server exposing four tools (`search`, `get_file`, `list_files`, `overview`) and every file as a `file://<repo-path>` resource. Search is keyword-based with light TF-IDF scoring, runs in-process, no embeddings model, no external service. Returns ranked `{path, score, snippet}` results.

**Who uses it.** Any MCP-aware tool:
- Claude Desktop
- Cline
- Cursor (MCP support varies by version)
- Continue
- Zed
- Custom MCP clients

**When to reach for it.** Long sessions where you'll touch many files unpredictably, sessions where you don't know upfront which docs you need, or any time you want lazy loading instead of preload-everything. The AI calls `search("entity list walk")` first, then `get_file(top_hit)` — only the relevant slice ends up in context.

**Cost.** One running Python process. Per-query latency <50ms cold, <5ms warm. Memory: ~5-10 MB resident.

---

## The Decision Tree

```
Which surface should I use right now?

  ┌─ Is the AI tool MCP-aware AND will the session span many files?
  │
  ├── YES → MCP server (mcp/pcx-knowledge-mcp/)
  │        Configure once per client; the AI searches lazily.
  │        Examples: Claude Desktop, Cline, Continue.
  │
  └── NO  → continue
            │
            ├─ Will the session work primarily in ONE language (Enma / AS / Lua)?
            │
            ├── YES → the matching per-language bundle (docs/llms-perception-<lang>.md)
            │        Smallest preload that covers the typical session.
            │        Examples: Aider /read, Cursor @file, Continue @files.
            │
            └── NO  → continue
                      │
                      ├─ Does the tool auto-fetch llms.txt conventions?
                      │
                      ├── YES → let it; no manual setup needed.
                      │        Examples: Claude when given the repo URL.
                      │
                      └── NO  → load docs/llms-full.txt (~2 MB) or
                                a category-specific bundle (llms-skills.md / llms-knowledge.md).
```

The choices are not exclusive — combining the MCP server with a small upfront bundle (e.g. `llms-perception-enma.md` for "you work in Enma" baseline + MCP for "and you can search the rest") is the recommended setup for long, complex sessions.

---

## Recipe per AI Tool

### Claude Code (this tool)

- Primary: skills auto-load; this skill IS one of them.
- For specific docs: `@`-reference by path, or use the perception MCP (the runtime one in `mcp/perception-mcp-config.json` — not the knowledge one). The knowledge MCP is more useful for Claude Desktop than Claude Code.

### Claude Desktop

- **Wire the knowledge MCP** (see `mcp/pcx-knowledge-mcp/README.md` for the JSON config).
- Optionally also drop `docs/llms-perception-enma.md` content into Claude Desktop's "Files" feature for persistent context.

### Cursor

- **First choice**: `@docs/llms-perception-<lang>.md` per session, scoped to the language.
- **For wider exploration**: configure the knowledge MCP via `.cursor/mcp.json`.
- The `.cursorrules` file (`rules/CURSOR.md`) handles project-rule baseline.

### Cline

- **Wire the knowledge MCP** via `cline_mcp_settings.json` (see `rules/CLINE.md`).
- Use Plan mode + the MCP's `search` tool to explore before any edits.
- Auto-approve read-only MCP tools (search, get_file, list_files, overview) — they're safe.

### Aider

- **Per-session**: `/read docs/llms-perception-enma.md` (or matching language pack).
- For broader work: `/read docs/llms-full.txt` (large; only when you'll truly use the breadth).
- Pair with `CONVENTIONS.md` carrying `rules/CLAUDE.md` content.
- The knowledge MCP works but Aider's MCP support is newer/less mature than Continue's or Cline's.

### Copilot

- **Wire `.github/copilot-instructions.md`** with `rules/COPILOT.md` content.
- For session context: paste `docs/llms-perception-<lang>.md` excerpts into the chat (Copilot Chat) when working on a specific area.
- Copilot doesn't speak MCP, so the static bundles are the only surface.

### Continue

- **Wire the knowledge MCP** via `.continue/config.yaml` `mcpServers` block.
- Pin `knowledge/pcx-api-cheatsheet.md` as always-loaded context via Continue's per-project config.

### Zed

- **Wire the knowledge MCP** via `~/.config/zed/settings.json` `context_servers`.
- For agent panel: `@`-reference docs as needed; the MCP search handles the discovery half.

---

## When the Bundles Drift

The static bundles (`docs/llms*.{txt,md}`) are generated by `tools/build-llms-index.py`. If you commit changes to docs / skills / knowledge / etc. *without* regenerating the bundles, they go stale. The fix:

```bash
python3 tools/build-llms-index.py          # regenerate
git add docs/llms*
git commit
```

CI runs `python3 tools/build-llms-index.py --check`; the build fails on drift. This is the same discipline as committing a generated lockfile or compiled-protobuf — if you change the source, regenerate the artifact.

---

## When You Don't Need the Index at All

For one-off lookups of a specific known doc, just read the file directly. The whole indexing apparatus is for the case where the AI doesn't know what's there to read; if you (the human) know the path, just `read docs/perception/render-api.md` and skip the index entirely.

The index also doesn't help with content the toolkit doesn't have — if you're working on a different PCX runtime version with different APIs, the toolkit's docs are the wrong source regardless of which surface you reach them through. See `knowledge/pcx-version-matrix.md` for the version dimension.

---

## Summary

| # | Surface | When to use | Cost |
|---|---|---|---|
| 1 | `docs/llms.txt` | First-touch with a new tool; auto-fetch convention | ~45 KB context |
| 2 | `docs/llms-perception-<lang>.md` | One-language session in a non-MCP tool | ~215-950 KB context |
| 3 | `docs/llms-full.txt` | All-language session in a non-MCP tool | ~2 MB context |
| 4 | `docs/llms-skills.md` / `llms-knowledge.md` | Skills- or knowledge-focused session | ~300-350 KB context |
| 5 | `mcp/pcx-knowledge-mcp/` server | MCP-aware tool, long session, lazy loading | One running process |

**Combine #2 + #5** for the best of both: small upfront context for your primary language + searchable depth for everything else. Recommended for long sessions.

**Cross-references:** `tools/build-llms-index.py` (generates the static bundles), `mcp/pcx-knowledge-mcp/` (the server + install guide), `.claude/skills/mcp-tool-routing/SKILL.md` (which Perception runtime MCP tool for which task — different MCP, different purpose), `.claude/skills/ai-pair-programming/SKILL.md` (the meta-workflow this skill slots into at the "load context" step).

---

## Source: `.claude/skills/pcx-lua-discipline/SKILL.md`

---
name: pcx-lua-discipline
description: >
  Lua-specific rules for writing Perception.cx scripts in Lua 5.4.6.
  Prevents Enma-reflex errors (typed addresses, C truthiness, struct value
  types, register_routine) in the Lua scripting surface. Always active when
  editing .lua PCX scripts — applies on top of game-cheat-guidelines.
license: MIT
---

# PCX Lua Discipline — Lua Idioms for Perception.cx Scripts

Lua-specific rules for writing Perception.cx scripts in **Lua 5.4.6** (confirmed in `docs/perception/lua/render-api.md`). PCX exposes a third scripting surface alongside Enma and AngelScript; the host APIs are nearly identical in shape but the *language* underneath is Lua, and the failure modes are different. Default to Lua semantics here, not Enma idioms — Enma reflexes (typed addresses, C truthiness, struct value types, `register_routine`) produce code that silently misreads memory or never runs.

**Always active when writing or editing `.lua` PCX scripts.** These rules apply on top of `game-cheat-guidelines`, not instead of it.

**Prerequisite:** `game-cheat-guidelines` MUST be loaded alongside this skill — its 12 rules (ground offsets, validate chains, separate scan from render, sigs over hardcodes, minimize writes) still govern *what* you do to memory. This skill governs *how Lua expresses it*. **Read the relevant page in `docs/perception/lua/` before writing any host API call.**

## Trigger

Activate when: the script file is `.lua`; the user asks for a Lua overlay/ESP/aimbot/dumper; you are porting an Enma or AngelScript script to Lua; you see `ref_process`, `on_frame`, `ui.create_subtab`, `proc:ru64`, or `string.format("0x%016X", ...)`; or you catch yourself writing `uint64 x =`, `register_routine`, `cast<>`, or `color(...)` in a file that is supposed to be Lua.

---

## 1. Addresses Are 64-bit Integers — Keep Them Integer-Typed

**Lua 5.4 has one number value with two subtypes: integer and float. Addresses are integers. The moment a float touches address math, anything past 2^53 is silently wrong.**

PCX is built on Lua 5.4.6, which has a true 64-bit integer subtype — so `proc:base_address()` returns a full-width integer, not a lossy double (`docs/perception/lua/proc-api.md` documents every read as `--> number (uint64)`, and `engine-specific-api.md` calls returned pointers "integer addresses"). This is *unlike* LuaJIT/5.1, where every number is a double and high addresses are already broken. The danger in 5.4 is the silent promotion: `/`, `^`, and mixing a float literal into the expression turn an exact integer into a float, and `0x7FF6_1234_5678` cannot be represented exactly as a double.

```lua
-- WRONG — float division and a float literal poison the address
local base = proc:base_address()
local slot = base + (i / 2)          -- '/' always yields a float in 5.4
local ent  = base + index * 8.0      -- 8.0 is a float; whole expr promotes
-- ent is now a float; past 2^53 it rounds to the wrong byte, read returns garbage

-- RIGHT — stay in integer land
local base = proc:base_address()
local slot = base + (i // 2)         -- floor division keeps the integer subtype
local ent  = base + index * 8        -- integer literal, integer result
```

**Why:** A float-contaminated address does not error — `proc:ru64` happily reads from the rounded address and returns more plausible-looking garbage. You get ESP at (0,0) and no stack trace. Use `//` (floor division) not `/`, use integer literals (`8` not `8.0`), and when you must check, `math.type(addr) == "integer"` tells you the subtype. Format with `%X`/`%d`, never `%f`.

---

## 2. `0` Is Truthy in Lua — Nil-Check and Zero-Check Are Different Tests

**`if x then` is true for `0`. PCX host functions split into two failure conventions, and using the wrong test lets failures through.**

This is the single biggest Enma-to-Lua porting bug. In C/Enma, `0` is false; in Lua, only `nil` and `false` are falsy — `0`, `0.0`, and `""` are all truthy. PCX host functions fail in two different ways (`docs/perception/lua/proc-api.md`):

- Return **`nil`** on failure: `ref_process`, `proc:get_module` → `if not x then` is correct.
- Return **`0`** on failure: `proc:find_code_pattern`, `proc:get_proc_address`, and every scalar read → you MUST compare `== 0` explicitly, because `if addr then` is **true** when `addr == 0`.

```lua
-- WRONG — a missed sig returns 0, and 0 is truthy, so this branch runs anyway
local hit = proc:find_code_pattern(base, size, SIG_ENTITY_LIST)
if hit then                          -- TRUE even when hit == 0
    local list = proc:ru64(hit + 3)  -- reads from 0x3, returns garbage
end

-- RIGHT — match the test to the convention
local proc = ref_process("game.exe")
if not proc then return 0 end                 -- nil convention
local base, size = proc:get_module("game.exe")
if not base then return 0 end                 -- nil convention

local hit = proc:find_code_pattern(base, size, SIG_ENTITY_LIST)
if hit == 0 then return 0 end                 -- ZERO convention — explicit
local list = proc:ru64(base + ENTITY_LIST_OFF)
if list == 0 then return 0 end                -- reads fail to 0, check it
```

**Why:** `if addr then` reads as a null check to anyone with a C background, but in Lua it only catches `nil`. A stale sig returns `0`, the truthy check passes, and you dereference address `0`. Memorize the split: handles are `nil`-checked, addresses and reads are `== 0`-checked.

---

## 3. A Table Is an Array or a Map — Never Both in One Variable

**Pick one shape per table. Mixing 1-based integer keys with string keys breaks `#`, `ipairs`, and every reader after you.**

Lua has one container type. PCX leans on both faces of it: `proc:read_struct_array` returns a **1-based array** (`docs/perception/lua/proc-api.md`), while struct descriptors and the view tables from `unreal_engine.read_minimal_view_info` are **string-keyed maps** (`docs/perception/lua/engine-specific-api.md`). The `#` operator and `ipairs` only work on a *sequence* (contiguous integer keys `1..n`); the instant you stash a string key on an array, `#t` becomes unreliable and `ipairs` stops early.

```lua
-- WRONG — array with a bolted-on string field
local ents = {}
ents[1] = ptr_a
ents[2] = ptr_b
ents.count = 2                       -- now #ents and ipairs are unreliable
for i = 1, #ents do ... end          -- may or may not see everything

-- RIGHT — array stays a pure sequence; metadata lives elsewhere
local ents = proc:read_struct_array(list_base, MAX_ENTS, ENT_SIZE, ENT_DESC)
for i, e in ipairs(ents) do          -- ipairs for sequences
    if e.health > 0 then draw_enemy(e) end
end

-- RIGHT — a descriptor is a map; iterate with pairs, never #
local ENT_DESC = {
    health = { offset = HEALTH_OFF, type = "i32" },
    pos_x  = { offset = POS_OFF,    type = "f32" },
}
for name, field in pairs(ENT_DESC) do ... end
```

**Why:** `#t` on a mixed table returns *any* border, not the count you meant — a documented Lua quirk, not a bug you can patch around. Use `ipairs`/`#` for sequences you built contiguously, `pairs` for maps, and keep the two roles in separate variables.

---

## 4. PCX Userdata Carries a Host Metatable — Don't Replace It

**`process`, `ui_*`, and `net_ws` handles are userdata with host-owned metatables. `setmetatable` on them breaks method dispatch. Wrap, don't reparent.**

Every PCX handle is userdata whose methods (`proc:ru64`, `cb:get`, `ws:send_text`) resolve through a metatable the host installed — `docs/perception/lua/net-api.md` names the WebSocket metatable `"net_ws"` outright. If you `setmetatable` one of these to add a helper, you detach `__index` and the built-in methods vanish. The Lua-correct move when you want helpers is to wrap the handle in a *plain table* you own and forward to it.

```lua
-- WRONG — clobbers the host metatable; proc:ru64 now errors
setmetatable(proc, { __index = { read_ptr = function(self, a) ... end } })

-- RIGHT — your own wrapper table delegates to the real handle
local Mem = {}
Mem.__index = Mem
function Mem.new(proc) return setmetatable({ p = proc }, Mem) end
function Mem:chain(base, ...)        -- helper that null-checks each hop
    local addr = base
    for _, off in ipairs({...}) do
        addr = self.p:ru64(addr + off)
        if addr == 0 then return 0 end
    end
    return addr
end

local mem = Mem.new(proc)
local weapon = mem:chain(base, OFF_LOCAL, OFF_WEAPON)
```

**Why:** Host userdata is opaque on purpose. Replacing its metatable is how you get `attempt to call a nil value (method 'ru64')` three frames later. Extend behavior by composition — a table that holds the handle and adds methods — and leave the host's metatable untouched.

---

## 5. Pass Function *Values* to Callbacks; Lifecycle Hooks Are Looked Up by Global Name

**There is no `register_routine` in Lua. Button callbacks take a function value. Lifecycle hooks must exist as global functions with exact names.**

PCX Lua wires logic two ways (`docs/perception/lua/life-cycle.md`, `gui-api.md`):

- **Lifecycle** — the engine calls the *globals* `main`, `on_frame`, and `on_unload` by name. They must be global (`function main()`, not `local function main()`) and spelled exactly. There is no registration call.
- **GUI callbacks** — `panel:add_button(name, fn)` takes a **function value** (a closure or a reference), not a string name.

```lua
-- WRONG — Enma reflexes: there is no register_routine, and a name string is not a callback
register_routine(on_frame, 0)                 -- nil global -> error
pnl:add_button("Reload", "do_reload")         -- string is not callable

-- WRONG — lifecycle hook hidden behind a local; engine never finds it
local function on_frame() ... end             -- not global -> never runs

-- RIGHT — globals for lifecycle, a function value for the callback
function main()
    local st  = ui.create_subtab(0, "ESP")
    local pnl = st:add_panel("Main", false)
    pnl:add_button("Reload Offsets", function() resolve_offsets() end)
    return 1                                   -- >0 AND on_frame defined => persistent
end

function on_frame() ... end                    -- engine calls this by name every frame
function on_unload() deref_process(g_proc) end -- cleanup hook
```

**Why:** `main()` returning `> 0` only keeps the script alive *if `on_frame` exists* (`life-cycle.md`); a `local function on_frame` is invisible to the engine and your overlay silently unloads. And a callback passed as `"do_reload"` is just a string — the button does nothing. Globals for hooks, function values for callbacks.

---

## 6. Closures Capture Upvalues by Reference — The Bite Is Shared Mutable State, Not the Loop Variable

**Lua's numeric `for` gives each iteration a fresh variable, so closing over the loop counter is safe. What bites is a closure or coroutine that captures an outer mutable local and runs *later*.**

The JS `var`-in-loop trap does not exist here: in Lua 5.4 the `for i = ...` control variable is a fresh local per iteration, so buttons created in a loop capture distinct `i` values correctly. The real PCX bug is deferred execution over a *shared upvalue* — a callback or `on_frame`-resumed coroutine that reads a variable mutated after the closure was created.

```lua
-- SAFE — each iteration's `i` is a fresh local; every button prints its own index
for i = 1, 3 do
    pnl:add_button("Slot " .. i, function() print("slot", i) end)
end

-- WRONG — all closures share the single upvalue `cur`, read at click time
local cur
for _, ent in ipairs(entities) do
    cur = ent                                  -- mutated every iteration
    pnl:add_button("Lock " .. ent.name, function() lock(cur) end)
end                                            -- every button locks the LAST entity

-- RIGHT — capture a fresh per-iteration local
for _, ent in ipairs(entities) do
    local target = ent                         -- new local each iteration
    pnl:add_button("Lock " .. ent.name, function() lock(target) end)
end
```

**Why:** Closures grab the *variable*, not its value-at-creation. A loop-local declared inside the body is fresh each pass and captures cleanly; a single local declared outside the loop is one shared box that every closure sees mutate. This matters most for GUI callbacks and coroutines (rule 9) that fire long after the loop finished.

---

## 7. Wrap Genuinely-Throwing Calls in `pcall` — One Bad Pointer Must Not Kill the Frame

**Scalar reads fail soft (return `0`/`""`), so don't `pcall` them. A handful of helpers raise Lua errors — those you wrap, or an uncaught error aborts `on_frame`.**

PCX reads are designed to fail quietly: `proc:ru64` on a bad address returns `0`, `proc:rs` returns `""` (`docs/perception/lua/proc-api.md`). Wrapping those in `pcall` is noise. But some helpers *raise*: `unreal_engine.world_to_screen` "raises a Lua error" on invalid input (`docs/perception/lua/engine-specific-api.md`), and JSON/net parsing can throw. An uncaught error propagates out of `on_frame`, and returning nothing (or erroring) unloads the script mid-session.

```lua
-- WRONG — reads already fail soft; this pcall is pure overhead
local ok, hp = pcall(function() return proc:r32(ent + HEALTH_OFF) end)

-- WRONG — w2s can raise; an uncaught error here kills the whole overlay this frame
function on_frame()
    for _, e in ipairs(g_ents) do
        local s = unreal_engine.world_to_screen(e.pos, g_view)  -- may error
        draw_box(s.x, s.y)
    end
end

-- RIGHT — pcall only the call that actually throws; degrade one entity, not the frame
function on_frame()
    for _, e in ipairs(g_ents) do
        local ok, s = pcall(unreal_engine.world_to_screen, e.pos, g_view)
        if ok and s and s.visible then         -- w2s also returns nil behind camera
            draw_box(s.x, s.y)
        end
    end
end
```

**Why:** Reads returning `0` are handled by rule 2's zero-checks, not by `pcall` — wrapping them buys nothing and hides the real check. Reserve `pcall` for the documented throwers, and scope it to the smallest call so a single malformed entity skips a draw instead of blanking the overlay and unloading the script.

---

## 8. Build Hot-Path Strings with `table.concat`, Never `..` in `on_frame`

**Lua strings are immutable. Each `..` allocates and interns a new string; chaining them in a per-frame loop is O(n²) garbage churn. Format once, cache, or use `table.concat`.**

Every `..` produces a fresh immutable string (the engine's own example uses `table.concat` for exactly this reason — `docs/perception/lua/proc-api.md` line ~279). In `on_frame`, which runs every frame, repeated concatenation allocates per frame and thrashes the GC, dropping FPS. Best is to not build strings in render at all: compute display text in the update pass and cache it; `draw_text` takes the cached string directly.

```lua
-- WRONG — N concatenations per entity, every frame
function on_frame()
    for _, e in ipairs(g_ents) do
        local label = "[" .. e.name .. "] " .. e.hp .. "hp " .. e.dist .. "m"
        draw_text(label, e.sx, e.sy, 255,255,255,255, g_font, TE_SHADOW, 0,0,0,180, 1.0)
    end
end

-- RIGHT — format in the update pass, cache the string, draw the cache
function update_labels()                       -- runs on interval, not every frame
    for _, e in ipairs(g_ents) do
        e.label = string.format("[%s] %dhp %dm", e.name, e.hp, e.dist)
    end
end

function on_frame()
    for _, e in ipairs(g_ents) do
        draw_text(e.label, e.sx, e.sy, 255,255,255,255, g_font, TE_SHADOW, 0,0,0,180, 1.0)
    end
end

-- When you must assemble many pieces, collect and join once
local parts = {}
for i, e in ipairs(g_ents) do parts[i] = e.name end
local csv = table.concat(parts, ", ")          -- one allocation
```

**Why:** `a .. b .. c` builds two intermediate strings and a final one, all interned; do that for 64 entities at 240 FPS and the allocator is your bottleneck. `string.format` in a cached field (rule from `game-cheat-guidelines` #4: separate scan from render) keeps the render path allocation-free, and `table.concat` collapses a join to a single allocation.

---

## 9. Use Coroutines to Spread Heavy Work Across Frames

**The `coroutine` add-on is enabled. A scan that stalls one frame should `yield` periodically and be resumed a slice at a time from `on_frame` — never loop until done inside a single frame.**

`docs/perception/lua/overview.md` lists `coroutine` as a registered add-on, and `life-cycle.md` is explicit: "No infinite loops — frame updates are handled by the engine." A full-module pattern scan or a deep entity walk done synchronously in one `on_frame` freezes the overlay. Model it as a coroutine that does a bounded chunk, `coroutine.yield`s, and is resumed each frame until `coroutine.status` is `"dead"`.

```lua
-- WRONG — scans the whole module in one frame; overlay hitches
function on_frame()
    g_list = proc:find_code_pattern(base, size, SIG)   -- blocks the frame if huge
end

-- RIGHT — a coroutine that scans in slices, resumed once per frame
local scanner
function main()
    g_proc = ref_process("game.exe")
    if not g_proc then return 0 end
    scanner = coroutine.create(function()
        local base, size = g_proc:get_module("game.exe")
        if not base then return end
        local CHUNK = 0x100000                          -- 1 MiB per frame
        local off = 0
        while off < size do
            local hit = g_proc:find_code_pattern(base + off, math.min(CHUNK, size - off), SIG)
            if hit ~= 0 then g_entity_list = hit; return end
            off = off + CHUNK
            coroutine.yield()                           -- give the frame back
        end
    end)
    return 1
end

function on_frame()
    if scanner and coroutine.status(scanner) ~= "dead" then
        local ok = coroutine.resume(scanner)            -- resume returns ok, err
        if not ok then scanner = nil end                -- coroutine errored; stop
    end
    -- render from whatever state is ready
end
```

**Why:** A coroutine turns a one-frame freeze into a smooth multi-frame task without threads or callbacks. `coroutine.resume` returns `false` plus the error message if the body throws — check it (same spirit as rule 7) so a failed scan stops cleanly instead of resuming a dead coroutine. `ponytail:` only reach for coroutines when the work genuinely overruns a frame; a fast scan in `main()` needs none of this.

---

## 10. `require` for File-Per-Feature Modules — Return a Table, Don't Leak Globals

**The `package` add-on gives you `require()`. Keep one feature per file, share state through a returned module table, and reserve globals for the lifecycle hooks the engine calls by name.**

`docs/perception/lua/overview.md` registers `package` with "`require()` and module loading", so the standard Lua module pattern applies and `game-cheat-guidelines` rule #6 (one feature, one file) carries over directly. `require` runs a module once and caches the result — return a table of that feature's API instead of scattering globals. The exception is the lifecycle trio (`main`/`on_frame`/`on_unload`, rule 5): those must be globals in the entry script.

```lua
-- offsets.lua — resolves and exposes addresses
local M = {}
function M.resolve(proc)
    local base, size = proc:get_module("game.exe")
    if not base then return false end
    M.entity_list = proc:find_code_pattern(base, size, SIG_ENTITY_LIST)
    if M.entity_list == 0 then return false end          -- rule 2: zero-check
    return true
end
return M

-- esp.lua — pure render, imports shared state
local offsets = require("offsets")
local M = {}
function M.draw(proc) ... end
return M

-- main.lua — entry script; globals only for lifecycle
local offsets = require("offsets")
local esp     = require("esp")
g_proc = nil

function main()
    g_proc = ref_process("game.exe")
    if not g_proc then return 0 end
    if not offsets.resolve(g_proc) then return 0 end
    return 1
end

function on_frame() esp.draw(g_proc) end
function on_unload() deref_process(g_proc) end           -- always release the handle
```

**Why:** `require` caching means a module's top-level code runs exactly once — perfect for resolving offsets, wrong for per-frame work. Returning a table keeps each feature's surface explicit and reloadable; dumping everything into globals reintroduces the god-script you split the files to avoid. And every `ref_process` needs its matching `deref_process` in `on_unload` (`docs/perception/lua/proc-api.md`) — a leaked handle outlives the script.

---

## Summary

| # | Rule | One-liner |
|---|------|-----------|
| 1 | Integer addresses | `//` not `/`; no float literals in address math (2^53 cliff) |
| 2 | `0` is truthy | `nil`-handles use `not x`; `0`-returns need `== 0` |
| 3 | One table shape | Array or map per variable; `ipairs`/`#` vs `pairs` |
| 4 | Don't reparent userdata | Wrap host handles, never `setmetatable` them |
| 5 | Values & global hooks | Callbacks take functions; lifecycle hooks are named globals |
| 6 | Capture loop-locals | Fresh local per iteration; shared upvalues bite later |
| 7 | `pcall` only throwers | Reads fail soft; wrap w2s/json so one error ≠ dead frame |
| 8 | `table.concat` in hot paths | `..` per frame is O(n²) garbage; cache formatted strings |
| 9 | Coroutines for big work | Yield slices across frames; no in-frame loops |
| 10 | `require` per feature | Return a module table; globals only for lifecycle |

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

## Source: `.claude/skills/pcx-streamproof/SKILL.md`

---
name: pcx-streamproof
description: >
  Explains when PCX overlay output appears in screen captures per capture
  method (OBS, Discord, ShadowPlay, NVIDIA Highlights, capture cards,
  PrintScreen). Triggers on streaming, OBS, Discord screenshare, "my overlay
  shows on stream," "my friend can see my menu," and related capture or
  recording questions.
license: MIT
---

# Streamproof Overlay — Capture Compatibility for PCX Renders

When PCX overlay output shows up in screen captures and when it doesn't, mapped per capture method (OBS, Discord, GeForce ShadowPlay, NVIDIA Highlights, PrintScreen, Steam screenshot, capture cards). The user-recurring questions "why does my friend on Discord see my menu" and "I want my overlay invisible on stream" both reduce to which capture path each viewer is using and which PCX render surface they're seeing — this skill makes that mapping explicit.

**Trigger when:** the user mentions OBS, Twitch, streaming, capture card, Discord screenshare, GeForce Experience, ShadowPlay, NVIDIA Highlights, Steam screenshot, PrintScreen, NVENC, Elgato, replay buffer, instant replay, "my overlay shows on stream," "my friend can see my menu," or related capture / recording questions.

**Prerequisite:** `docs/perception/render-api.md` for the actual render surface taxonomy on your PCX build; `knowledge/anti-cheat-architecture.md` for context on screenshot-based scans by anti-cheats.

---

## Trigger

Streaming, recording, screen-share, capture-card, screenshot, replay-buffer, NVIDIA/AMD overlay coexistence questions; reports of friends seeing things on Discord, viewers seeing menus on Twitch, an overlay artifact appearing in a saved screenshot.

---

## 1. Capture Taxonomy — How Each Capture Method Sees the Screen

**The single fact that explains every "why can my friend see this" question: different capture methods see different layers of the rendering stack. They are not interchangeable.**

| Capture Method | What It Captures | Common Software |
|---|---|---|
| **Game Capture / Window Capture (hook)** | Hooks the game process's D3D/Vulkan/OGL swap chain; captures the frame *before* it composites with other overlays | OBS "Game Capture", Streamlabs, Twitch Studio |
| **Display Capture (DXGI Desktop Duplication)** | Captures the final composited desktop image as DWM composes it | OBS "Display Capture", Discord screenshare, Windows screenshot, Snipping Tool |
| **GPU-driver capture** | Driver-level hook of the game's render output, before window composition | NVIDIA ShadowPlay, NVIDIA Highlights, AMD ReLive |
| **Print-window GDI** | Bitblts a specific window's GDI surface | Legacy screen-capture tools, `PrintScreen` on some configurations |
| **Capture card (HDMI)** | Captures the GPU output signal at the cable; sees exactly what the monitor sees | Elgato, AverMedia, dedicated streaming PC setups |
| **Mirror driver** | Inserts a virtual display device that mirrors what would have rendered | Some VPN/remote-access tools, older streaming setups |

Three categories matter:

1. **Process-internal capture** (Game Capture, ShadowPlay) — sees only what the game process renders into its own swap chain
2. **Desktop-composited capture** (Display Capture, Discord screenshare, screenshot tools) — sees the final image after DWM merges everything
3. **Signal-level capture** (HDMI capture card) — sees the final pixels on the wire to the monitor

A PCX overlay can be visible to any subset of these depending on how it's rendered. The default question to ask any user with a capture problem is: "which of these three categories is the viewer using?"

**Why:** Most "but my friend can see it" reports are actually "my friend uses Discord screenshare (desktop-composited), and you tested with OBS Game Capture (process-internal) — different layers, different results." Pin the capture method before debugging anything else.

---

## 2. PCX Render Surface Behavior

**PCX provides multiple ways to put pixels on screen. Each one lands in a different layer of the rendering stack, and that determines which capture methods see it. The exact surface names and modes are in `docs/perception/render-api.md` — read it for your PCX version.**

The general mapping (verify against your build's docs):

| PCX Render Path | Lands In | Visible to Game Capture? | Visible to Display Capture? | Visible to ShadowPlay? | Visible to HDMI Capture? |
|---|---|---|---|---|---|
| **Direct game-process render** (overlay drawn into the game's own swap chain via PCX's swap-chain hook) | The game's swap chain, before window composition | Yes | Yes (via the composited desktop) | Yes | Yes |
| **External overlay window** (PCX renders to a separate top-most layered window) | A separate window, composited by DWM into the desktop | No (Game Capture only sees the game window) | Yes | No (driver capture is per-game) | Yes |
| **DWM composition layer hook** (where supported) | Inserted into the DWM composition pipeline | Varies by platform; treat as Display Capture in practice | Yes | No | Yes |
| **GPU compute shader visualization** (custom shader output) | Depends on how PCX exposes the shader output — typically composited similar to one of the above | Same as the surface it composites into | Same | Same | Same |

The pattern: anything that ends up *inside the game process's render output* is visible to everything. Anything that's a *separate window or DWM layer* is invisible to in-game-process captures (Game Capture, ShadowPlay) but visible to anything that captures the composited desktop.

**Why:** Capture-card and desktop-capture methods see "what the user sees" — so anything visible to the user is visible to them, period. The only capture paths that distinguish overlays from the game's own rendering are the process-internal ones, and they distinguish based on which process's swap chain the overlay landed in.

---

## 3. The Pre-Stream Checklist

**Before going live, validate against the capture method you actually use. A test against OBS Game Capture tells you nothing about what shows up on Discord screenshare.**

```
For each capture method the user cares about (typically Twitch + Discord):

[ ] Open the capture in preview (OBS preview pane, Discord call with self-view, etc.)
[ ] Walk through every PCX render path you have enabled:
    - Main overlay
    - Menu / GUI sections
    - Notification popups
    - Any custom shader output
[ ] For each: is it visible in the preview?
[ ] If visible-but-wanted-hidden: switch to a render path that doesn't land in this capture's layer
[ ] If wanted-visible-but-hidden: switch to one that does land in this capture's layer
[ ] Confirm by recording a 10-second clip and rewatching; previews are sometimes lossy
```

The matrix to fill before going live:

| Capture target | What I want visible | What I want hidden | Render path to use |
|---|---|---|---|
| Twitch stream (OBS Game Capture) | Game | PCX overlay | External overlay window |
| Twitch stream (OBS Display Capture) | Game + overlay | Nothing | Either render path; both visible |
| Discord screenshare | Same as Display Capture | Hard to hide; see Step 4 | External window won't help here |
| ShadowPlay highlight clip | Game | PCX overlay | External overlay window |
| Steam screenshot | Game | PCX overlay | External overlay window |
| HDMI capture card | Both | Nothing hideable | All renders land here |

**Why:** Going live without checking is how the "my menu just showed up on stream during a clutch" story happens. Five minutes of preview-and-record is cheaper than a clip going around.

---

## 4. Capture Cards and HDMI Are Pixel-Accurate — No Software Solution

**An HDMI capture card sees the monitor signal. If the user sees it, the capture card sees it. There is no software-rendered overlay that avoids being captured by a downstream signal-level capture.**

The only options when a capture card is in play:

- **Dual-monitor setup with the overlay on the non-captured display** (e.g. menus on monitor 2 which is not piped to the capture card). Requires PCX to render to a specific display, which depends on the render-surface options in your build.
- **Use the in-game render path and accept it's visible** — then make the overlay aesthetically discreet (low alpha, small footprint, off-screen during gameplay) so it's not eye-catching even when visible.
- **Use a streaming PC topology** where the gaming PC's HDMI goes to a capture card on a *second* PC, and the second PC composites the streamer's webcam/scenes; the overlay still shows on the captured feed but you have more control over what's composited around it.

There is no clever DWM trick that defeats the HDMI signal — pixels are pixels by the time they reach the cable.

**Why:** Newcomers ask "how do I make my overlay invisible to my capture card" expecting a software answer. There isn't one; pin this fact early and shift the conversation to the topology / aesthetic options that actually work.

---

## 5. Screenshot-Based Detection by Anti-Cheats

**Some anti-cheats capture screenshots of the game window or full desktop and analyze them for known overlay artifacts. This is a separate concern from "streamproof for viewers" but uses the same capture-path taxonomy.**

The standard mechanisms (see `knowledge/anti-cheat-architecture.md` for per-AC details):

- **In-process screenshot** — AC code running inside the game process grabs the game's swap-chain backbuffer. Sees anything that landed in the game's render output. External overlay windows do not appear in this capture.
- **Desktop screenshot** — AC service captures the full desktop via DXGI. Sees everything the user sees. External overlay windows DO appear here.
- **Game-window PrintWindow** — AC calls `PrintWindow(hwnd, ...)` on the game window. Sees only what's GDI-rendered into that window (often misses D3D-composited overlays entirely).

Historical examples (from publicly documented behavior of the named systems — see `knowledge/anti-cheat-architecture.md`):

- BattlEye's `BEClient.dll` has been observed taking screenshots via in-process capture and uploading them for analysis.
- EAC includes screenshot capability invoked by backend rule pushes.
- Vanguard does in-process capture as part of its memory-integrity scanning.

The general principle: a render path that's invisible to a given capture *for viewers* is also invisible to a screenshot taken via the same mechanism. An overlay invisible to OBS Game Capture is also invisible to in-process AC screenshots. This is coincidental alignment with anti-evasion goals — the underlying mechanism is the same render-pipeline layering.

**Note:** the appropriate response to AC screenshot detection is platform terms-of-service compliance and `skill://anti-cheat-re` for understanding the detection surface. This skill maps the *what's visible to what* fact; it does not advise on evasion of legitimate platform enforcement.

**Why:** Users conflate "streamproof" with "AC-invisible" — they aren't the same goal, but they share a technical foundation (which render surface is in which capture layer). Splitting the goals clarifies which question you're answering and prevents over-claiming "this is invisible to AC" when you've only verified one capture path.

---

## 6. Differential Diagnosis: "Friend on Discord Can See My Menu"

**The most-reported confusion. The user tests their overlay against OBS Game Capture (sees nothing — good), then a friend on Discord screenshare sees the menu. This is not a bug; it's the capture-path mismatch from Step 1.**

Standard diagnosis sequence:

1. Ask: how is the friend viewing? Discord screenshare, Discord camera passthrough, watching a Twitch stream, looking at a screenshot, watching a recorded clip?
2. Map their viewing method to a capture category from Step 1 (Discord screenshare → Display Capture; Twitch via OBS Game Capture → process-internal; etc.).
3. Confirm: the PCX render path the user is using lands in *that* capture's layer. (Refer to the Step 2 matrix.)
4. Options:
   - Switch the offending render path to one that doesn't land in the friend's capture layer
   - If unavoidable (Display Capture catches all visible overlays): change the workflow (different capture target, hide-toggle hotkey, render only off-screen)
   - If the friend uses a HDMI capture card: see Step 4 — no software fix

```
Concrete walkthrough:

User: "My friend on Discord can see my ESP."
You:  "Discord screenshare uses Display Capture (composited desktop). Your
       PCX overlay landing in either the game's swap chain OR a separate
       desktop window will both show up there.
       To hide it from Discord screenshare specifically, you'd need to
       hide the rendering itself — there's no render path that's visible
       to you-the-user but invisible to Display Capture, because both you
       and Display Capture see the same composited desktop."

User: "But I tested with OBS and it didn't show up!"
You:  "OBS Game Capture only hooks the game's swap chain. If your overlay
       renders to a separate window, OBS Game Capture misses it — but
       Discord screenshare (Display Capture) doesn't. Different layers,
       different visibility."
```

The honest answer to many "how do I hide this from Discord" questions is "you can't, because Discord screenshare sees the same desktop you do." Steer toward workflow changes (bind a hide hotkey, share game audio only, share a specific application window that excludes the overlay).

**Why:** The technical answer (capture-path layering) once explained becomes obvious in retrospect. The hours of "but why" questions disappear when the user understands the three-category model from Step 1.

---

## Summary

| # | Topic | One-liner |
|---|---|---|
| 1 | Capture taxonomy | Process-internal vs desktop-composited vs signal-level — three layers, different visibility |
| 2 | PCX render paths | Game-swap-chain hook vs external window vs DWM layer — each lands in a different capture layer |
| 3 | Pre-stream checklist | Validate against the specific capture method, not "a screen capture" generically |
| 4 | HDMI capture cards | Pixel-accurate; no software solution; topology and aesthetics only |
| 5 | AC screenshot detection | Uses the same capture taxonomy; alignment with streamproofing is coincidental, not by design |
| 6 | Differential diagnosis | "Friend on Discord sees X" almost always = capture-path mismatch, not a script bug |

**Cross-references:** `docs/perception/render-api.md` (authoritative surface list for your PCX version), `knowledge/anti-cheat-architecture.md` (per-AC screenshot mechanisms), `skill://anti-cheat-re` (detection-surface methodology), `skill://pcx-perf-budget` (overlay render cost considerations for streamers running on a single-PC topology).
