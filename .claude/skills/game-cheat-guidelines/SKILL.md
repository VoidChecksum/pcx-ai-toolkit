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
