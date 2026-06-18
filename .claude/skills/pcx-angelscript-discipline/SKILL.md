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
