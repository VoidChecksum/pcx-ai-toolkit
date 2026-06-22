# PCX Cross-Language API Reference

Side-by-side mapping of common Perception.cx APIs across Enma (`.em`), AngelScript (`.as`), and Lua (`.lua`).
Use this when porting code between languages or when an AI assistant needs to stay locked to one language surface.

---

## Lifecycle & Registration

| Operation | Enma (`.em`) | AngelScript (`.as`) | Lua (`.lua`) |
|---|---|---|---|
| Entry point | `int64 main()` | `int main()` | `function main()` — returns number |
| Frame/update hook | `void on_render(int64 data)` via `register_routine` | `void on_tick(int id, int data_index)` via `register_callback` | `function on_frame()` — global, no registration |
| Cleanup hook | **None** — RAII handles cleanup | `void on_unload()` | `function on_unload()` |
| Register recurring | `register_routine(cast<int64>(fn), data)` | `register_callback(@fn, every_ms, data_index)` | *Not applicable* |
| Unregister | *Not needed* — tied to script lifecycle | `unregister_callback(cb_id)` | *Not applicable* |

### Examples

**Enma**
```cpp
int64 main() {
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
void on_render(int64 data) { }
```

**AngelScript**
```cpp
int main() {
    register_callback(@on_tick, 16, 0);
    return 1;
}
void on_tick(int id, int data_index) { }
void on_unload() { unregister_callback(g_cb); }
```

**Lua**
```lua
function main()
    return 1  -- >0 AND on_frame defined => persistent
end
function on_frame() end
function on_unload() deref_process(g_proc) end
```

---

## Process Attachment

| Operation | Enma (`.em`) | AngelScript (`.as`) | Lua (`.lua`) |
|---|---|---|---|
| Open process | `proc_t p = ref_process("game.exe");` | `proc_t@ p = ref_process("game.exe");` | `p = ref_process("game.exe")` |
| Null check | `if (!p.alive())` | `if (p is null || !p.alive())` | `if not p then ... end` |
| Module base/size | `p.get_module_size(name)` returns `uint64` | `p.get_module(name, base, size)` returns `bool` | `base, size = p:get_module(name)` |
| Process base | `p.base_address()` | `p.base_address()` | `p:base_address()` |
| Is alive | `p.alive()` | `p.alive()` | `p:alive()` |
| Release | *Automatic (RAII)* | `p.deref()` — **mandatory** | `deref_process(p)` — **mandatory** |

### Examples

**Enma**
```cpp
proc_t p = ref_process("game.exe");
if (!p.alive()) return 0;
uint64 base = p.base_address();
uint64 size = p.get_module_size("game.exe");
```

**AngelScript**
```cpp
proc_t@ p = ref_process("game.exe");
if (p is null || !p.alive()) return 0;
uint64 base = p.base_address();
uint64 size = 0;
if (!p.get_module("game.exe", base, size)) return 0;
p.deref();
```

**Lua**
```lua
p = ref_process("game.exe")
if not p then return 0 end
local base = p:base_address()
local ok, size = p:get_module("game.exe")
if not ok then return 0 end
-- later: deref_process(p)
```

---

## Memory Reads

| Operation | Enma (`.em`) | AngelScript (`.as`) | Lua (`.lua`) |
|---|---|---|---|
| 8-bit signed | `p.r8(addr)` | `p.r8(addr)` | `p:r8(addr)` |
| 8-bit unsigned | `p.ru8(addr)` | `p.ru8(addr)` | `p:ru8(addr)` |
| 16-bit signed | `p.r16(addr)` | `p.r16(addr)` | `p:r16(addr)` |
| 16-bit unsigned | `p.ru16(addr)` | `p.ru16(addr)` | `p:ru16(addr)` |
| 32-bit signed | `p.r32(addr)` | `p.r32(addr)` | `p:r32(addr)` |
| 32-bit unsigned | `p.ru32(addr)` | `p.ru32(addr)` | `p:ru32(addr)` |
| 64-bit signed | `p.r64(addr)` | `p.r64(addr)` | `p:r64(addr)` |
| 64-bit unsigned | `p.ru64(addr)` | `p.ru64(addr)` | `p:ru64(addr)` |
| 32-bit float | `p.rf32(addr)` | `p.rf32(addr)` | `p:rf32(addr)` |
| 64-bit float | `p.rf64(addr)` | `p.rf64(addr)` | `p:rf64(addr)` |
| Pattern scan | `p.find_code_pattern(base, size, sig)` | `p.find_code_pattern(base, size, sig)` | `p:find_code_pattern(base, size, sig)` |
| Find all patterns | `p.find_all_code_patterns(base, size, sig, results)` | `p.find_all_code_patterns(base, size, sig, results)` | `p:find_all_code_patterns(base, size, sig)` |

**Note:** Lua reads return numbers; AS/Enma return typed scalars. In Lua, `find_code_pattern` returns `0` on failure (truthy!), so you MUST use `== 0` checks.

---

## Drawing / Render API

| Primitive | Enma (`.em`) | AngelScript (`.as`) | Lua (`.lua`) |
|---|---|---|---|
| Viewport | `get_view_width()` / `get_view_height()` | `get_view(vw, vh)` — out-params | `vw, vh = get_view()` — multi-return |
| Filled rect | `draw_rect_filled(vec2 pos, vec2 size, color c, float64 rounding, uint8 flags)` | `draw_rect_filled(float x, float y, float w, float h, uint8 r, uint8 g, uint8 b, uint8 a, float rounding, uint8 flags)` | `draw_rect_filled(x, y, w, h, r, g, b, a, rounding, rounding_flags)` |
| Outlined rect | `draw_rect(vec2 pos, vec2 size, color c, float64 thickness, float64 rounding, uint8 flags)` | `draw_rect(float x, float y, float w, float h, uint8 r, uint8 g, uint8 b, uint8 a, float thickness, float rounding, uint8 flags)` | `draw_rect(x, y, w, h, r, g, b, a, thickness, rounding, rounding_flags)` |
| Line | `draw_line(vec2 a, vec2 b, color c, float64 thickness)` | `draw_line(float x1, float y1, float x2, float y2, uint8 r, uint8 g, uint8 b, uint8 a, float thickness)` | `draw_line(x1, y1, x2, y2, r, g, b, a, thickness)` |
| Circle | `draw_circle(vec2 center, float64 radius, color c, float64 thickness, bool filled)` | `draw_circle(float cx, float cy, float radius, uint8 r, uint8 g, uint8 b, uint8 a, float thickness, bool filled)` | `draw_circle(cx, cy, radius, r, g, b, a, thickness, filled)` |
| Text | `draw_text(string text, vec2 pos, color c, int64 font, int32 effect, color effect_c, float64 effect_amt)` | `draw_text(const string &in text, float x, float y, uint8 r, uint8 g, uint8 b, uint8 a, uint64 font, int effect, uint8 er, uint8 eg, uint8 eb, uint8 ea, float effect_amount)` | `draw_text(text, x, y, r, g, b, a, font, effect, er, eg, eb, ea, effect_amount)` |
| Font handle | `get_font20()` | `get_font20()` | `get_font20()` |
| Mouse pos | `get_mouse_pos()` | `get_mouse_pos()` | `get_mouse_pos()` |

**Key difference:** Enma bundles position/size/color into structs; AS and Lua pass raw positional integers/floats. Never mix the styles.

---

## Types & Containers

| Concept | Enma (`.em`) | AngelScript (`.as`) | Lua (`.lua`) |
|---|---|---|---|
| Array | `T[]` with `.push()`, `.pop()`, `.length` (property) | `array<T>` with `.insertLast()`, `.removeLast()`, `.length()` | `{}` table with `table.insert()`, `#t`, `ipairs()` |
| Map | `map<K,V>` with `.set()`, `.get()`, `.contains()` | `dictionary` with string keys only; `.get(key, out_value)` | Plain `{}` table; both array and map faces |
| Vec2 | `vec2(x, y)` — value type | `vec2(x, y)` — value type | No native vec2; use `{x=..., y=...}` or two locals |
| Vec3 | `vec3(x, y, z)` — value type | `vec3(x, y, z)` — value type | No native vec3; use `{x=..., y=..., z=...}` or three locals |
| Color | `color(r, g, b, a)` — value type | No `color` struct in standard API; pass raw rgba ints | No `color` struct; pass raw rgba ints |
| String | `string` with `+` concatenation | `string` with `+` concatenation | Immutable strings; avoid `..` in hot paths |
| Float default | `float64` (default) | `double` / `float` (32-bit) | One number type with integer/float subtypes |
| Address type | `uint64` | `uint64` | Integer subtype of `number` |

---

## Input

| Operation | Enma (`.em`) | AngelScript (`.as`) | Lua (`.lua`) |
|---|---|---|---|
| Key down | `is_key_down(VK_LSHIFT)` | `is_key_down(VK_LSHIFT)` | `is_key_down(VK_LSHIFT)` |
| Mouse press | `press_mouse_left()` | `press_mouse_left()` | `press_mouse_left()` |
| Mouse pos | `get_mouse_pos()` | `get_mouse_pos()` | `get_mouse_pos()` |

---

## Time & Math

| Operation | Enma (`.em`) | AngelScript (`.as`) | Lua (`.lua`) |
|---|---|---|---|
| Milliseconds | `time_ms()` | `time_ms()` | `time_ms()` |
| FPS | `get_fps()` | `get_fps()` | `get_fps()` |
| Format int hex | `formatInt(val, "h")` | `formatInt(val, "h")` | `string.format("0x%X", val)` |
| Sine / cosine | `sin(x)`, `cos(x)` | `sin(x)`, `cos(x)` | `math.sin(x)`, `math.cos(x)` |
| Square root | `sqrt(x)` | `sqrt(x)` | `math.sqrt(x)` |
| Arctan2 | `atan2(y, x)` | `atan2(y, x)` | `math.atan(y, x)` |
| Clamp | `clamp(val, min, max)` | `clamp(val, min, max)` | `math.max(min, math.min(max, val))` |
| Fmod | `fmod(a, b)` | `fmod(a, b)` | `a % b` |

---

## Logging

| Language | Function |
|---|---|
| Enma | `println(...)` |
| AngelScript | `log(...)` |
| Lua | `log(...)` |

---

## Language-Lock Rules for AI Assistants

When a user asks for code in a specific PCX language, apply these constraints:

1. **Enma (`.em`):**
   - Use `register_routine(cast<int64>(fn), data)`
   - Use `int64 main()`
   - Use `println(...)` for logging
   - Use `vec2`, `vec3`, `color` value types in draw calls
   - Use `T[]` arrays and `map<K,V>`
   - No `@` handles, no `deref()`, no `is null`
   - Cleanup via RAII, not `on_unload`

2. **AngelScript (`.as`):**
   - Use `register_callback(@fn, every_ms, data_index)`
   - Use `int main()`
   - Use `log(...)` for logging
   - Use raw positional args in draw calls (no `color` struct in standard API)
   - Use `array<T>` and `dictionary`
   - Use `proc_t@` handles, `@=` rebinding, `is null` checks, `deref()`
   - Provide `on_unload()` with `unregister_callback` and `deref()`

3. **Lua (`.lua`):**
   - Use global `function on_frame()` / `function on_unload()` — no registration
   - Use `function main()` returning `1` for persistence
   - Use `log(...)` for logging
   - Use raw positional args in draw calls
   - Use `{}` tables; never `setmetatable` on PCX userdata
   - `0` is truthy — always zero-check addresses with `== 0`
   - Use `pcall` for genuinely-throwing calls (e.g. `world_to_screen`)
   - Use `deref_process(proc)` in `on_unload`

**Golden rule:** If you cannot find an API in the target language's docs, do not invent it. Prefer asking the user to clarify over hallucinating a cross-language borrow.
