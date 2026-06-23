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

**Prerequisite:** `game-cheat-guidelines` skill for the full doc index. **Read the relevant `docs/perception/<file>.md` before writing any API call** — the Enma surface is not the AS surface, and method names, parameter shapes, and constants differ.

---

## Trigger

`.em` file open, Enma syntax visible (`import`, `#pragma once`, `register_routine`, `println`, `color`/`vec2` value types, `cast<T>`), user mentions Enma / `proc_t` value semantics / PCX scripting in Enma context, any code referencing `docs/perception/`.

---

## 1. Enma Is Not AngelScript — Don't Paste AS APIs

**The PCX Enma API has different function names, different parameter shapes, and different idioms than AngelScript. They look similar; they are not interchangeable.**

The most common bug in AI-written `.em` scripts is pasting AngelScript API calls verbatim. The script doesn't compile because Enma is a statically typed C++-like language with value semantics, not AngelScript's handle system.

| Enma | AngelScript |
|---|---|
| `register_routine(cast<int64>(on_render), 0)` | `register_callback(on_tick, 16, 0)` |
| `int64 main()` | `int main()` |
| `void on_render(int64 data)` | `void on_tick(int id, int data_index)` |
| `println(...)` | `log(...)` |
| `color(r,g,b,a)` then `draw_rect(vec2(pos), vec2(size), color, ...)` | `draw_rect_filled(x, y, w, h, r, g, b, a, rounding, flags)` |
| `get_view_width()` / `get_view_height()` | `get_view(vw, vh)` — out-param |
| `proc_t g_proc;` (value, RAII) | `proc_t@ g_proc;` (handle, ref-counted) |
| `T[]` arrays with `.push()`, `.pop()` | `array<T>` with `.insertLast()`, `.removeLast()` |
| `map<K,V>` with `.set()`, `.get()` | `dictionary` with string keys only |
| `cast<T>(x)` | `T(x)` or `float(x)` — C-style cast |
| `#pragma once` + `import "module"` | `#pragma once` + `#include "module"` |

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

**Why:** Enma is a separately compiled host language with its own type system and standard library. The AS and Lua bindings cover overlapping domains but the function signatures, type registrations, and constants are independent. Always confirm the call in `docs/perception/<area>-api.md` before writing it.

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

## 3. `float64` Is the Default Float; `float32` Uses the `f` Suffix

**Enma uses `float64` (double-precision) as its default floating-point type. A bare literal `1.5` is `float64`. `float32` is explicit: write `float32` literals with the `f` suffix (`0.2f`, `1.5f`) — not `cast<float32>(0.2)`. Render APIs and math use `float64` unless otherwise documented.**

This is the official Enma overview convention — *"Float32 literals: `0.2f`, not `cast<float32>(0.2)`. Required for vertex buffers."* It is also guideline #8 (`f` suffix on float32) and `script-linter.py` rule 8: a `float32` target assigned a bare `float64` literal is flagged. `cast<float32>(x)` is for converting a `float64` *value* (variable/expression), not a literal.

```cpp
// Enma — float64 by default, float32 via the f suffix
float64 smooth = 0.15;          // 0.15 is float64
float32 fov    = 30.0f;         // f suffix -> float32
float32 uv     = 0.2f;          // 0.2f, NOT cast<float32>(0.2) — vertex buffers need float32

float64 cx = get_view_width() * 0.5;   // 0.5 is float64; no promotion issue

// Convert a float64 VALUE (not a literal) with cast<float32>:
int64  ticks    = 40;
float64 measured = cast<float64>(ticks);    // a float64 value from an int64
float32 m32      = cast<float32>(measured); // cast the value, not a literal

// WRONG — bare float64 literal into a float32 (linter rule 8 fires)
float32 bad = 0.2;              // 0.2 is float64; write 0.2f

// WRONG — AS-style float/double keywords
double cx = get_view_width() * 0.5f;   // Enma has no 'double' keyword; use 'float64'
float cx  = get_view_width() * 0.5;    // Enma has no 'float' keyword; use 'float32'
```

**Why:** Enma is closer to C++ than AS. `float64` / `float32` map directly to C++ `double` / `float`; `double` and `float` are not keywords. A silent `float64`→`float32` literal truncation corrupts GPU vertex-buffer layout — which is why the overview mandates the `f` suffix and the linter warns on bare `float64` literals assigned to `float32`. The default `float64` eliminates the promotion issues that plague AS.

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

Note: Enma's `map<K,V>` requires `K` to support `operator<` (ordered map) or hashing (unordered map). The exact constraints depend on the PCX Enma registration — verify in `docs/perception/readme.md`.

**Why:** AS's `dictionary` is a string-keyed boxed-value map. Enma's `map<K,V>` is closer to C++ `std::map` or `std::unordered_map` with typed keys and values. Using the wrong map type produces compile errors or runtime misbehavior.

---

## 6. Render API Takes `vec2`, `color`, and Other Value Types

**The PCX Enma render API is struct-typed: pass `vec2` for positions/sizes, `color` for RGBA, and `float64` for scalars. Do not pass raw positional args the way AngelScript does.**

```cpp
// WRONG — AngelScript raw-positional style in Enma
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

Enma value types (`vec2`, `vec3`, `color`) are lightweight stack structs — copying them is cheap. You can construct them inline or cache them. Per the official Enma overview convention, **colors and positions should always be wrapped** (`color(255, 255, 255, 255)`, `vec2(10.0, 20.0)`) — and **constructing them fresh each frame is fine; Enma drops the temporaries at scope exit.** You don't need to hoist them into globals to avoid per-frame cost (guideline #7's "construct per frame" is about not binding magic constants to cached globals, not about avoiding inline construction).

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

**Why:** The Enma render API was designed around C++-style value semantics. Passing four separate integers for color and four separate floats for rectangle bounds is the AngelScript binding choice to avoid marshaling structs across the language boundary. In Enma, the structs live on the native side and are passed by value efficiently.

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

## 13. Encrypted `int64` Handles — Pass Back, Never Inspect

**Every `create_*` and `load_*` native returns an encrypted `int64` handle. Store it, pass it straight back into the matching `draw_*` / `bind_*` / `destroy_*` call, and never inspect, print, do arithmetic on, or compare it against a raw integer.**

This is an official Enma overview convention — *"Handles: all `create_*` / `load_*` natives return an encrypted `int64`. Pass it back into draw / bind / destroy. Don't inspect."* The handle is an opaque encrypted token the host uses to locate the resource internally; its bits are not a pointer or an index.

```cpp
// RIGHT — store the encrypted int64, round-trip it opaquely
int64 g_tex  = /* return value of a create_* / load_* native */;
int64 g_font = /* return value of a create_* / load_* native */;

void on_render(int64 data) {
    // Hand g_tex / g_font straight back to their matching
    // bind_* / draw_* / destroy_* natives as-is — never inspect the value.
}
// on unload: pass each handle to its matching destroy_* native
```

```cpp
// WRONG — treating the encrypted handle as a meaningful integer
int64 tex = /* create_* / load_* return value */;
if (tex == 0) { ... }                     // don't compare to a raw int
println("handle = " + cast<string>(tex)); // don't print or inspect it
int64 leaked = tex + 0x1000;              // don't do arithmetic on it
```

**Why:** Inspecting or mutating the encrypted handle yields garbage and breaks the resource binding — the host can no longer match the token to its internal resource. Keep it in an `int64`, pass it back unchanged, and let the matching `destroy_*` native release it. This is distinct from rule #2's `proc_t` value semantics: `proc_t` is a value type with methods (`.alive()`, `.base_address()`); `create_*`/`load_*` handles are raw encrypted `int64` tokens with no methods.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | Enma is not AS | Look up every API in `docs/perception/` before pasting |
| 2 | Value semantics | `proc_t` is a value; no `@`, no `deref()`, no `is null` |
| 3 | `float64` default, `float32` `f` suffix | `0.2f` is `float32`; bare `0.2` is `float64`; no `float`/`double` keywords |
| 4 | `T[]` arrays | `.push()`, `.pop()`; `length` is a property |
| 5 | `map<K,V>` | Typed keys/values; `.set()`, `.get()`, `.contains()` |
| 6 | Value-type render API | `vec2`, `color` structs; not raw positional args |
| 7 | `register_routine` | `cast<int64>(fn)` + data payload; no unregister needed |
| 8 | Struct defaults | `bool valid = false;` — use default initializers |
| 9 | `import "module"` | `#pragma once` guards; no `#include`, no `require()` |
| 10 | Hot-reload safety | Re-attach, re-resolve, re-register every `main()`; no `on_unload` |
| 11 | `cast<T>(x)` | Explicit cast syntax; no C-style or AS-style |
| 12 | Type-scaled pointers | Use `uint64` offsets + `proc_t` reads; never raw pointer arithmetic |
| 13 | Encrypted `int64` handles | `create_*`/`load_*` return encrypted `int64`; pass back to `draw_*`/`bind_*`/`destroy_*`; never inspect |

**The 12 game-cheat-guidelines rules still apply** — this skill is the *Enma-flavored* version of those discipline rules. Address types are `uint64`, null-check every read, separate update from render, sigs over hardcodes, one feature per file, minimize writes, validate against the live binary. Read `skill://game-cheat-guidelines` for the full discipline.

**Cross-references:** `skill://game-cheat-guidelines` (the 12 rules), `skill://game-hacking-pcx` (doc router), `skill://pcx-angelscript-discipline` (AS-specific gotchas, useful when porting), `docs/perception/readme.md` (registered modules and addons), `docs/perception/proc-api.md`, `docs/perception/render-api.md`, `docs/perception/lifecycle-and-routines.md`, `docs/perception/gui-api.md`.
