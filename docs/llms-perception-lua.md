# Lua Context Pack

> Single-file context pack for AI tools writing Lua scripts on Perception.cx. Bundles the Lua API surface, the discipline skill, and cross-references to the underlying 12 guidelines.

> **Generated** by `tools/build-llms-index.py` — do not edit manually. Re-generate by running the tool from the repo root. CI verifies the committed bundle matches the current source.

**Source files included: 26**

---

## Source: `docs/perception/lua/cs2-extended-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/cs2-extended-api.md).

# CS2 Extended API

This API is available in both the Uni API and the CS2 product.

This API is strictly allowed to be used for local and educational purposes only, any online-multiplayer usage will result in termination from the platform. Any violation of our [TOS](https://perception.cx/help/terms/) will result in termination from the platform.

In the CS2 product, all standard Proc API functions are supported **except**:

* Process referencing by PID/name
* Engine-specific helpers
* Virtual memory allocation (`alloc_vm` / `free_vm`)

On CS2 Product, `ref_process()` always returns the **CS2 process only**, so it is used like:

```lua
local cs2 = ref_process()  -- for CS2 Product only
```

There is **no memory allocation API** exposed in the CS2 product.

***

**🔗 `process:cs2_get_interface(module_base, name)`**

Resolves a **CreateInterface-style** interface exported by a CS2 module.

```lua
addr = process:cs2_get_interface(module_base, name)
```

**Parameters**

* `module_base`\
  Base address of the module that exports `CreateInterface`, e.g.:

  * `"tier0.dll"`

  Typically obtained via:

  ```lua
  local base, size = process:get_module("tier0.dll")
  ```
* `name`\
  Interface name string, e.g.:
  * `"VEngineCvar007"`

**Returns**

* Absolute pointer to the resolved interface (Lua integer).
* `0` if the interface cannot be found or the arguments are invalid.

***

**🧬 `process:cs2_get_schema_dump()`**

Dumps all Schema System fields for `client.dll` via `schemasystem.dll`.

```lua
entries = process:cs2_get_schema_dump()
```

**Return value**

A **Lua array-style table** (`1..N`) where each element is a table:

```lua
{
    name   = "ClassName::fieldName", -- string
    offset = 0x10,                   -- integer offset
}
```

**Fields**

* `name` — `"ClassName::fieldName"`, UTF-8 string\
  e.g. `"CPulse_CallInfo::m_nEditorNodeID"`, `"C_BaseEntity::m_iHealth"`
* `offset` — field offset from the base of that class.

If no schema data can be read, returns an **empty table**.

***

#### 🧪 Example – Interface Lookup + Schema Dump (Lua)

```lua
local function dump_schema(proc)
    local entries = proc:cs2_get_schema_dump()
    if not entries or #entries == 0 then
        log("[LUA] schema dump empty")
        return
    end

    log("[LUA] Dumping " .. #entries .. " schema fields...")

    for i = 1, #entries do
        local e = entries[i]
        if e then
            -- format: CPulse_CallInfo::m_nEditorNodeID @ 0x00000010
            log(string.format(
                "%s @ 0x%08X",
                e.name,
                e.offset
            ))
        end
    end

    log("[LUA] Schema dump complete.")
end

function main()
    -- Uni API build:
    local cs2 = ref_process("cs2.exe")

    -- On the CS2 Product build, just use:
    --   local cs2 = ref_process()

    if not cs2 or not cs2:alive() then
        log("[LUA] cs2.exe not found")
        return 0
    end

    local tierBase, tierSize = cs2:get_module("tier0.dll")
    if not tierBase then
        log("[LUA] tier0.dll not found")
        return 0
    end

    local iface = cs2:cs2_get_interface(tierBase, "VEngineCvar007")
    if iface == 0 then
        log("[LUA] interface not found!")
        return 0
    end

    log(string.format(
        "VEngineCvar007 interface at 0x%016X",
        iface
    ))

    dump_schema(cs2)
    return 1
end
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/cs2-extended-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/engine-specific-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/engine-specific-api.md).

# Engine Specific API

### Unreal Engine Helpers (`unreal_engine`)

The `unreal_engine` table contains helpers for working with Unreal Engine games (UE4 / UE5).

***

#### `unreal_engine.read_tarray`

```lua
unreal_engine.read_tarray(proc, tarray_address[, max_count]) -> table
```

Reads an Unreal-style dynamic array (`TArray`) and returns its contents as a Lua array of pointers.

**Parameters**

* `proc`\
  Process object used for reading game memory.
* `tarray_address`\
  Integer address of the array in game memory.
* `max_count` *(optional, default: 4096)*\
  Maximum number of elements to read. Used as a safety limit.

**Returns**

* A Lua array table indexed from `1` upward, containing integer addresses (pointers).
* If anything is invalid (bad address, null pointer, weird count), an **empty table** is returned.

**Example**

```lua
local actors = unreal_engine.read_tarray(proc, actors_array_addr, 1024)

for i, actor_ptr in ipairs(actors) do
    -- actor_ptr is an integer address inside the game
end
```

***

#### `unreal_engine.read_minimal_view_info`

```lua
unreal_engine.read_minimal_view_info(proc, view_info_address) -> table
```

Reads a camera/view structure and converts it into a normalized Lua table.

**Parameters**

* `proc`\
  Process object.
* `view_info_address`\
  Address of the camera/view information in memory.

**Returns**

A table with this structure:

```lua
{
  location = { x = number, y = number, z = number },
  rotation = { pitch = number, yaw = number, roll = number },
  fov      = number
}
```

If the address or process is invalid, an **empty table** is returned.

**Example**

```lua
local view = unreal_engine.read_minimal_view_info(proc, camera_addr)

if view.fov then
    local s = unreal_engine.world_to_screen({ x = 0, y = 0, z = 200 }, view)
    -- ...
end
```

***

#### `unreal_engine.read_minimal_view_info_f64`

```lua
unreal_engine.read_minimal_view_info_f64(proc, view_info_address) -> table
```

Same purpose as `read_minimal_view_info`, but for layouts that use **double-precision** values (common in some UE5 setups).

**Parameters**

* `proc`\
  Process object.
* `view_info_address`\
  Address of the camera/view information in memory.

**Returns**

Same shape as the float version:

```lua
{
  location = { x = number, y = number, z = number },
  rotation = { pitch = number, yaw = number, roll = number },
  fov      = number
}
```

If inputs are invalid, returns an **empty table**.

**Example**

```lua
-- Example when you know the game uses a double-precision view structure:
local view = unreal_engine.read_minimal_view_info_f64(proc, view_addr)
local screen = unreal_engine.world_to_screen({ x = 1000, y = 500, z = 150 }, view)
```

***

#### `unreal_engine.world_to_screen`

```lua
unreal_engine.world_to_screen(world_position, view_info) -> table | nil
```

Projects a point from world space to screen space using camera data.

**Parameters**

* `world_position`\
  Can be either:
  * A table: `{ x = number, y = number, z = number }`, or
  * Three numbers: `x, y, z`
* `view_info`\
  The camera table returned from:

  * `unreal_engine.read_minimal_view_info`, or
  * `unreal_engine.read_minimal_view_info_f64`

  Must contain:

  ```lua
  view_info = {
    location = { x, y, z },
    rotation = { pitch, yaw, roll },
    fov      = number
  }
  ```

**Returns**

* On success (point is in front of the camera):

  ```lua
  {
    x       = number,  -- screen X (pixels)
    y       = number,  -- screen Y (pixels)
    visible = true
  }
  ```
* If the point is behind the camera: `nil`.
* If input is invalid: a Lua error is raised.

**Example**

```lua
local view = unreal_engine.read_minimal_view_info(proc, camera_addr)

local pos = { x = enemy.x, y = enemy.y, z = enemy.z + 80 }
local screen = unreal_engine.world_to_screen(pos, view)

if screen and screen.visible then
    -- draw box, text, etc. at screen.x, screen.y
end
```

***

#### World-to-Screen Projection&#xD;

Convert 3D world coordinates to 2D screen positions using view matrices.

```lua
-- Row-major matrix layout (DirectX-style, Source engine, etc.)
world_to_screen_rowmajor(world_pos, view_matrix, viewport?) -> {x, y, visible} or nil
--   world_pos:   table {x, y, z} - 3D world position
--   view_matrix: accepts table with 16 floats (indices 1-16) or matrix4x4
--   viewport:    optional table {x, y} - screen size (defaults to overlay size)
--   returns:     table {x, y, visible} or nil if behind camera

-- Transposed/column-major layout (Unity, OpenGL-style)
world_to_screen_transposed(world_pos, view_matrix, viewport?) -> {x, y, visible} or nil
--   world_pos:   table {x, y, z} - 3D world position
--   view_matrix: accepts table with 16 floats (indices 1-16) or matrix4x4
--   viewport:    optional table {x, y} - screen size (defaults to overlay size)
--   returns:     table {x, y, visible} or nil if behind camera
```

***

### Fortnite Helper

A small helper for reading player names in Fortnite.

***

#### `fortnite_get_player_name`

```lua
fortnite_get_player_name(proc, address) -> string
```

Attempts to read and decode a player name from game memory.

**Parameters**

* `proc`\
  Process object.
* `address`\
  Address pointing to a name-related structure in Fortnite.

**Returns**

* The player name as a string on success.
* An empty string `""` if:
  * The process is invalid,
  * The memory cannot be read safely,
  * The decoded name is empty.

**Example**

```lua
local name = fortnite_get_player_name(proc, name_struct_addr)

if name ~= "" then
    print("Player name:", name)
end
```

***

### Rust Helper

A helper for getting world-space transform positions in Rust (Unity).

***

#### `rust_get_transform_position`

```lua
rust_get_transform_position(proc, address) -> x, y, z
```

Resolves the world-space position of a Unity transform hierarchy used by Rust.

**Parameters**

* `proc`\
  Process object.
* `address`\
  Address of a transform-related structure for a given entity.

**Returns**

* On success: three numbers `x, y, z` (Lua returns them as multiple values).
* On failure (invalid process, invalid address, or any internal error): `0, 0, 0`.

**Example**

```lua
local x, y, z = rust_get_transform_position(proc, transform_addr)

if x ~= 0 or y ~= 0 or z ~= 0 then
    local screen = unreal_engine.world_to_screen({ x = x, y = y, z = z }, view_info)
    if screen and screen.visible then
        -- draw marker on that entity
    end
end
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/engine-specific-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/engine.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/engine.md).

# Engine

The Engine provides three global logging helpers available in every Lua script.\
Each of them targets a different part of the UI and is intended for a different use-case.

***

### **log(message: string)**

Send a standard UI log message (top-left overlay).

#### **Syntax**

```lua
log("message")
```

#### **Description**

Adds a **styled notification log** to the engine’s **top-left UI log feed**.\
These logs appear with the same formatting as other engine notifications (fade-out timers, colors, etc.).

#### **Examples**

```lua
log("Script initialized.")
log("Speed boost activated!")
```

#### **Overlay Output**

```
[LUA] Script initialized.
[LUA] Speed boost activated!
```

***

### **log\_error(message: string)**

Send an error message to the UI log panel.

#### **Syntax**

```lua
log_error("message")
```

#### **Description**

Same as `log()`, but marked as an **error**, shown with an **error style**, prefixing the message with **`[LUA][ERR]`**.

#### **Examples**

```lua
log_error("Failed to load config!")
log_error("Invalid teleport target!")
```

#### **Overlay Output**

```
[LUA][ERR] Failed to load config!
[LUA][ERR] Invalid teleport target!
```

***

### **log\_console(message: string)**

Append text to the debug console (persistent until cleared).

#### **Syntax**

```lua
log_console("message")
```

#### **Description**

Writes text directly into the **script debugging console**, where messages accumulate continuously.\
This console is separate from the UI log panel and is intended purely for development and live debugging.

Unlike `log()` and `log_error()`, **console output does not fade or disappear** — it continues to append until the user manually clears the console.

#### **Examples**

```lua
log_console("Tick: " .. tick)
log_console("Entity pos = " .. tostring(vec))
```

#### **Console Output**

```
[LUA] Tick: 4521
[LUA] Entity pos = (1024, 88, 12)
```

***

### log\_console\_error(message: string)

Append an **error message** to the debug console (persistent until cleared).

#### Syntax

```lua
log_console_error("message")
```

#### Description

Writes an error-styled message directly into the script debugging console.\
This behaves the same as `log_console()`, but marks the message as an error and prefixes it with **`[LUA][ERR]`**.

Unlike `log()` and `log_error()`, console error output:

* Does **not** appear in the UI overlay
* Does **not** fade or disappear
* Accumulates continuously until the user clears the console

Use this for:

* Debugging failures inside loops
* Tracing error conditions without spamming the UI
* Logging internal script errors or invalid states
* Development-only error output

#### Parameters

* **message** (`string`)\
  The error message to append to the debug console.

#### Examples

```lua
log_console_error("Failed to resolve entity pointer")
log_console_error("Invalid memory read at 0x0")
```

#### Console Output

```
[LUA][ERR] Failed to resolve entity pointer
[LUA][ERR] Invalid memory read at 0x0
```

***

### get\_user\_name(): string

Returns the current PCX username.

#### **Syntax**

```lua
get_user_name()
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/engine.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/extended-math-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/extended-math-api.md).

# Extended Math API

This API provides vectors, quaternions, matrices, math constants, and helper functions found in modern game engines.

***

## 📘 Contents

* Math Constants
* Global Math Helpers
* vector2
* vector3
* quaternion
* matrix4x4
* mat4 Namespace

***

## 🔢 **Math Constants**

These are available globally:

| Name              | Value                  |
| ----------------- | ---------------------- |
| `M_PI`            | 3.141592653589793      |
| `M_TAU`           | 6.283185307179586 (2π) |
| `M_PI_2`          | π/2                    |
| `M_PI_4`          | π/4                    |
| `DEG2RAD`         | π/180                  |
| `RAD2DEG`         | 180/π                  |
| `PI_OVER_180`     | π/180                  |
| `INV_PI_OVER_180` | 180/π                  |
| `M_ZERO`          | 0                      |
| `M_ONE`           | 1                      |
| `M_EPSILON`       | 0.000001               |

Usage:

```lua
local angle = 45 * DEG2RAD
local circumference = 2 * M_PI * radius
```

***

## 🛠 **Global Math Helpers**

#### ✔ clamp(x, min, max)

Clamps a value between two bounds.

```lua
local v = clamp(5, 0, 1)  -- 1
```

#### ✔ saturate(x)

Clamps value to `[0,1]`.

```lua
local t = saturate(1.5) -- 1
```

#### ✔ sign(x)

Returns `-1`, `0`, or `1`.

#### ✔ round(x), round\_up(x), round\_down(x)

Standard rounding helpers.

#### ✔ fract(x)

Fractional part (always 0–1, even for negatives).

#### ✔ wrap(x, min, max)

Wraps a number into a cyclic range.

```lua
wrap(5, 0, 4) --> 1
```

#### ✔ lerp(a, b, t)

Linear interpolation.

#### ✔ inverse\_lerp(a, b, v)

Inverse of `lerp`.

#### ✔ remap(a1, b1, a2, b2, v)

Maps a value from one range to another.

#### ✔ smoothstep(edge0, edge1, x)

Smooth Hermite interpolation.

#### ✔ step(edge, x)

Returns 0 if x < edge, else 1.

#### ✔ is\_nan(x), is\_inf(x)

Checks numeric state.

***

## 🟦 **vector2**

A 2D double-precision vector.

#### ✔ Create

```lua
local v = vector2(x, y)
local v = vector2() -- 0,0
```

#### ✔ Fields

* `v.x`
* `v.y`

#### ✔ Operators

| Operation         | Example    |
| ----------------- | ---------- |
| add               | `v1 + v2`  |
| subtract          | `v1 - v2`  |
| multiply (scalar) | `v * 2`    |
| divide (scalar)   | `v / 2`    |
| unary minus       | `-v`       |
| equality          | `v1 == v2` |

#### ✔ Methods

```lua
v:length()
v:distance(other)
v:distance_to(other)
v:lerp(other, t)
v:min(other)
v:max(other)
```

#### ✔ Memory I/O

```lua
v:readas_float(proc, addr)
v:readas_double(proc, addr)
v:writeas_float(proc, addr)
v:writeas_double(proc, addr)
```

***

## 🟩 **vector3**

A 3D double-precision vector.

#### ✔ Create

```lua
local v = vector3(x, y, z)
local v = vector3()
```

#### ✔ Fields

`v.x`, `v.y`, `v.z`

#### ✔ Operators

Same as vector2, plus:

* `v:dot(other)`
* `v:cross_product(other)`

#### ✔ Methods

```lua
v:length()
v:length2d()
v:distance(other)
v:distance2d(other)
v:distance_to(other)
v:distance2d_to(other)
v:lerp(other, t)
v:min(other)
v:max(other)
v:dot_product(other)
v:cross_product(other)
```

#### ✔ Memory I/O

Same pattern as vector2.

***

## 🟪 **quaternion**

A 4D double-precision quaternion (x, y, z, w).

#### ✔ Create

```lua
local q = quaternion(x, y, z, w)
local q = quaternion()     -- 0,0,0,1
local q = quat_from_euler(pitch, yaw, roll)
```

#### ✔ Fields

`q.x`, `q.y`, `q.z`, `q.w`

#### ✔ Operators

| Operation           | Example    |
| ------------------- | ---------- |
| multiply quaternion | `q1 * q2`  |
| multiply scalar     | `q * 2`    |
| divide scalar       | `q / 2`    |
| add                 | `q1 + q2`  |
| subtract            | `q1 - q2`  |
| negate              | `-q`       |
| equality            | `q1 == q2` |

#### ✔ Methods

```lua
q:length()
q:normalized()
q:dot(other)
q:conjugate()
q:inverse()
q:to_euler()          -- returns pitch,yaw,roll
q:rotate(vec3)        -- rotates a vector
```

#### ✔ Memory I/O

```lua
q:readas_double(proc, addr)
q:writeas_double(proc, addr)
q:readas_float(proc, addr)
q:writeas_float(proc, addr)
```

***

## 🟥 **matrix4x4**

A 4×4 float matrix (row-major), used for transforms and 3D math.

#### ✔ Create

```lua
local m = matrix4x4()   -- zero matrix
```

#### ✔ Indexing

```lua
m[1] .. m[16]
```

#### ✔ Operators

```lua
local M = A * B
```

#### ✔ Methods (instance)

```lua
m:transform(vec3)
m:readas_float(proc, addr)
m:writeas_float(proc, addr)
m:readas_double(proc, addr)
m:writeas_double(proc, addr)
```

#### ✔ tostring()

Pretty-prints matrix for debugging.

***

## 🟧 **mat4 Namespace**

Convenient static constructors:

```lua
local I = mat4.identity()
local Z = mat4.zero()

local T = mat4.translate(tx, ty, tz)
local S = mat4.scale(sx, sy, sz)
local R = mat4.rotate_euler(pitch, yaw, roll)

local Mq = mat4.from_quaternion(q)
```

***

## 📘 **Examples**

#### TRS (Translate → Rotate → Scale)

```lua
local T = mat4.translate(10, 5, 0)
local R = mat4.rotate_euler(0, 90, 0)
local S = mat4.scale(2, 2, 2)

local M = T * R * S
local out = M:transform(vector3(1,0,0))
log(out)
```

#### Quaternion Rotation

```lua
local q = quat_from_euler(0, 0, 90)
local v = vector3(1,0,0)
local r = q:rotate(v)     -- (0,1,0)
```

#### Remapping Values

```lua
local t = inverse_lerp(0, 100, 25)   -- 0.25
local v = remap(0, 1, -1, 1, t)      -- -0.5
```

## Full API Test

```lua
log("=========== MATH HELPERS TESTS START ===========")

local function approx(a,b,eps)
    eps = eps or 0.000001
    return math.abs(a-b) <= eps
end

local function assert_eq(a,b,msg)
    if a ~= b then
        log("[ASSERT FAIL] "..msg.." | expected="..tostring(b).." got="..tostring(a))
    else
        log("[PASS] "..msg)
    end
end

local function assert_approx(a,b,msg)
    if approx(a,b) then
        log("[PASS] "..msg)
    else
        log("[ASSERT FAIL] "..msg.." | expected="..tostring(b).." got="..tostring(a))
    end
end

----------------------------------------------------------------
-- clamp(x, min, max)
----------------------------------------------------------------
assert_approx(clamp(-1, 0, 1), 0,   "clamp below")
assert_approx(clamp(0.5, 0, 1), 0.5,"clamp inside")
assert_approx(clamp(2, 0, 1), 1,    "clamp above")
-- swapped min/max should still work
assert_approx(clamp(5, 10, 0), 5,   "clamp swapped bounds")

----------------------------------------------------------------
-- saturate(x) -> [0,1]
----------------------------------------------------------------
assert_approx(saturate(-1), 0,      "saturate below")
assert_approx(saturate(0.3), 0.3,   "saturate inside")
assert_approx(saturate(5), 1,       "saturate above")

----------------------------------------------------------------
-- sign(x)
----------------------------------------------------------------
assert_eq(sign( 5),  1,  "sign positive")
assert_eq(sign(-2), -1,  "sign negative")
assert_eq(sign( 0),  0,  "sign zero")

----------------------------------------------------------------
-- round, round_up, round_down
----------------------------------------------------------------
assert_approx(round(2.3),  2,   "round 2.3")
assert_approx(round(2.5),  3,   "round 2.5")
assert_approx(round(-2.3), -2,  "round -2.3")
assert_approx(round(-2.5), -3,  "round -2.5")

assert_approx(round_up(2.1),   3, "round_up 2.1")
assert_approx(round_up(-2.1), -2, "round_up -2.1")

assert_approx(round_down(2.9),   2, "round_down 2.9")
assert_approx(round_down(-2.1), -3, "round_down -2.1")

----------------------------------------------------------------
-- fract(x)
----------------------------------------------------------------
assert_approx(fract(1.25), 0.25, "fract 1.25")
-- our implementation keeps negative fractional part in [0,1)
assert_approx(fract(-1.25), 0.75, "fract -1.25")

----------------------------------------------------------------
-- wrap(x, min, max)
----------------------------------------------------------------
assert_approx(wrap(5, 0, 4), 1,   "wrap 5 in [0,4]")
assert_approx(wrap(-1, 0, 4), 3,  "wrap -1 in [0,4]")
assert_approx(wrap(9, 2, 6), 5, "wrap 9 in [2,6]")
assert_approx(wrap(2, 2, 6), 2,   "wrap 2 (edge)")

----------------------------------------------------------------
-- lerp / inverse_lerp
----------------------------------------------------------------
assert_approx(lerp(0, 10, 0.0), 0,   "lerp t=0")
assert_approx(lerp(0, 10, 1.0), 10,  "lerp t=1")
assert_approx(lerp(0, 10, 0.25), 2.5,"lerp t=0.25")

assert_approx(inverse_lerp(0, 10, 2.5), 0.25, "inverse_lerp 2.5 in [0,10]")
assert_approx(inverse_lerp(0, 10, 0),    0.0, "inverse_lerp 0")
assert_approx(inverse_lerp(0, 10, 10),   1.0, "inverse_lerp 10")

----------------------------------------------------------------
-- remap(a1,b1,a2,b2,v)
----------------------------------------------------------------
assert_approx(remap(0, 10, 0, 100, 2.5), 25,  "remap 2.5 [0,10]->[0,100]")
assert_approx(remap(0, 1, -1, 1, 0.5),   0,   "remap 0.5 [0,1]->[-1,1]")
assert_approx(remap(-1, 1, 0, 1, 0),     0.5, "remap 0 [-1,1]->[0,1]")

----------------------------------------------------------------
-- smoothstep(edge0,edge1,x)
----------------------------------------------------------------
assert_approx(smoothstep(0,1, -0.5), 0.0,  "smoothstep below")
assert_approx(smoothstep(0,1,  0.0), 0.0,  "smoothstep 0")
assert_approx(smoothstep(0,1,  1.0), 1.0,  "smoothstep 1")
-- at x=0.5 we expect 0.5 for 3t^2-2t^3
local s05 = smoothstep(0,1,0.5)
assert_approx(s05, 0.5, "smoothstep 0.5")

----------------------------------------------------------------
-- step(edge, x)
----------------------------------------------------------------
assert_approx(step(0.5, 0.3), 0.0, "step below")
assert_approx(step(0.5, 0.5), 1.0, "step equal")
assert_approx(step(0.5, 0.9), 1.0, "step above")

----------------------------------------------------------------
-- is_nan / is_inf
----------------------------------------------------------------
local nan = 0/0
local pinf = 1/0
local ninf = -1/0

assert_eq(is_nan(nan), true,  "is_nan on NaN")
assert_eq(is_nan(0),   false, "is_nan on 0")

assert_eq(is_inf(pinf), true,  "is_inf +inf")
assert_eq(is_inf(ninf), true,  "is_inf -inf")
assert_eq(is_inf(123),  false, "is_inf 123")

log("=========== MATH HELPERS TESTS END ===========")

function main()
    return 1;
end

```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/extended-math-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/file-system.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/file-system.md).

# File System

**API Folder Location** : C:\Users\\"UserName"\Documents\My Games\\

Filesystem API that allows scripts to read, write, and manage files **only inside the main scripting directory**.

Scripts **cannot** access, modify, create, or query files **outside** this directory.\
All paths must be **relative** and are automatically sandboxed for safety.

***

## **Overview**

The filesystem API provides the following capabilities:

* Create files
* Create directories
* Read files
* Check if a file exists
* List files or directories
* Delete files
* Delete directories

All functions operate only on paths **relative to the script directory**.

***

## **Path Rules**

To ensure safety and consistency:

#### ✔ Paths must be relative

Absolute paths such as:

```
/folder/file.txt
C:\temp\log.txt
```

are not allowed.

#### ✔ Parent-directory traversal is not allowed

Paths cannot contain:

```
..
```

#### ✔ Scripts cannot escape the main scripting directory

Every operation is automatically constrained to the script directory.

***

## **Global Functions**

All filesystem functions are available as **global Lua functions**.

***

### `create_file(path, [data]) → boolean`

Creates or overwrites a file.

#### Example:

```lua
create_file("data/info.txt", "Hello World!")
```

***

### `create_directory(path) → boolean`

Creates a directory (non-recursive).

#### Example:

```lua
create_directory("data/logs")
```

***

### `read_file(path) → boolean, string`

Reads a file and returns `(success, contents)`.

#### Example:

```lua
local ok, text = read_file("data/info.txt")
if ok then
    print(text)
end
```

***

### `does_file_exist(path) → boolean`

Checks if a file exists.

#### Example:

```lua
if does_file_exist("data/info.txt") then
    print("found")
end
```

***

### `query_directory(path, include_dirs?, include_files?, extensions_table?) → boolean, table`

Lists the contents of a directory.

#### Parameters:

| Name               | Type    | Default  | Description                             |
| ------------------ | ------- | -------- | --------------------------------------- |
| `path`             | string  | required | Directory to list                       |
| `include_dirs`     | boolean | `true`   | Include subdirectories                  |
| `include_files`    | boolean | `true`   | Include files                           |
| `extensions_table` | table   | `nil`    | Filter by extensions, e.g. `{ ".txt" }` |

#### Example:

```lua
local ok, items = query_directory("data", true, true)
if ok then
    for i, name in ipairs(items) do
        print(name)
    end
end
```

#### Filter example:

```lua
local ok, jsons = query_directory("data", false, true, { ".json" })
```

***

### `delete_file(path) → boolean`

Deletes a file.

#### Example:

```lua
delete_file("data/old.txt")
```

***

### `delete_directory(path) → boolean`

Deletes a directory (may require the directory to be empty).

#### Example:

```lua
delete_directory("data/temp")
```

***

## **Example Test Script**

A simple script to confirm everything is working:

```lua
function main()
    print("=== FS TEST START ===")

    create_directory("fs_tests")
    create_file("fs_tests/test.txt", "hello test")

    local ok, data = read_file("fs_tests/test.txt")
    print("read ok:", ok, "data:", data)

    local ok_q, items = query_directory("fs_tests")
    if ok_q then
        for _, name in ipairs(items) do
            print(" -", name)
        end
    end

    delete_file("fs_tests/test.txt")
    delete_directory("fs_tests")

    print("=== FS TEST END ===")
    return 0;
end
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/file-system.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/gui-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/gui-api.md).

# GUI API

The Lua GUI API allows scripts to dynamically create UI inside the Perception.cx interface.\
UI created by a script is **owned** by that script and is automatically removed when the script unloads.

#### ✔ Supported Features

* Create subtabs inside the main UI
* Add panels inside subtabs
* Add UI elements inside panels
* Read/write element values
* Hide/show elements at runtime (`set_active`)
* Keybinds, color pickers, and buttons that belong to a parent checkbox
* List controls with highlight, insert, remove, set active index
* Script-level button callbacks

***

## **UI Hierarchy**

```
Tab (index 0–4)
 └─ Subtab
      └─ Panel (small or large)
           ├─ Checkbox
           │     ├─ Keybind (child)
           │     └─ Color Picker(s) (child, up to 2)
           │     └─ Button (child)
           ├─ Slider (double or int)
           ├─ Input Text Box
           ├─ Multi Select
           ├─ Single Select
           ├─ List
           └─ Other elements…
```

***

## **Element Creation Rules**

#### 🔥 **Important Ordering Constraint**

Some elements must be created *immediately after a checkbox*, because the UI engine uses the checkbox as their parent:

| Child Element    | Rule                                                             |
| ---------------- | ---------------------------------------------------------------- |
| **keybind**      | MUST be created right after its parent checkbox (1 or 2 allowed) |
| **color picker** | MUST be created right after its parent checkbox (1 or 2 allowed) |

If you break this rule, the element will not get created.

* **2 color pickers**, or
* **2 keybinds**, or
* **1 color picker + 1 keybind**

***

## **Global Entry**

### `ui.create_subtab(tab_index, name)`

Creates a new subtab in a given tab.

#### **Parameters**

| Name        | Type          | Description                                  |
| ----------- | ------------- | -------------------------------------------- |
| `tab_index` | integer (0–4) | Index of the main tab to place the subtab in |
| `name`      | string        | Display name of the subtab                   |

#### **Returns**

`ui_subtab` userdata.

#### **Example**

```lua
local st = ui.create_subtab(0, "ESP Settings")
```

***

## **Subtab API**

### `subtab:add_panel(name, is_small)`

Creates a panel inside the subtab.

#### **Parameters**

| Name       | Type    | Description                       |
| ---------- | ------- | --------------------------------- |
| `name`     | string  | Panel title                       |
| `is_small` | boolean | Whether panel uses compact layout |

#### **Returns**

`ui_panel` userdata.

#### **Example**

```lua
local pnl = st:add_panel("Aimbot", false)
```

#### **Common**

```lua
subtab:set_active(true/false)
```

***

## **Panel Element APIs**

All elements are created using methods on a panel.

***

## **Checkbox**

### `panel:add_checkbox(name, initial_value, [draw_title], [find_protect], [draw_just_label])`

#### **Parameters**

| Name              | Type               | Description                                                                                                                                                                   |
| ----------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`            | string             | Checkbox label                                                                                                                                                                |
| `initial_value`   | boolean            | Starting state                                                                                                                                                                |
| `draw_title`      | boolean (optional) | Show the label (default: true)                                                                                                                                                |
| `find_protect`    | boolean (optional) | Internal protection flag                                                                                                                                                      |
| `draw_just_label` | boolean (optional) | When enabled, the checkbox is non-interactive and functions purely as a label. This is useful when you only want to attach a color picker or keybind without toggle behavior. |

#### **Returns**

`ui_checkbox` userdata.

#### **Example**

```lua
local cb = pnl:add_checkbox("Enable ESP", true)
```

#### **Methods**

```lua
cb:get() → bool
cb:set(true/false)
cb:set_active(true/false)
```

***

## **Slider (Double)**

### `panel:add_slider_double(name, postfix, value, min, max, step, [draw_title], [find_protect])`

#### **Parameters**

| Name           | Type               | Description                                           |
| -------------- | ------------------ | ----------------------------------------------------- |
| `name`         | string             | Slider label                                          |
| `postfix`      | string             | Text shown after numeric value (“°”, “ms”, “x”, etc.) |
| `value`        | number             | Initial value                                         |
| `min`          | number             | Minimum                                               |
| `max`          | number             | Maximum                                               |
| `step`         | number             | Step size                                             |
| `draw_title`   | boolean (optional) | Show the name (default: true)                         |
| `find_protect` | boolean (optional) | Internal flag                                         |

#### **Returns**

`ui_slider_double` userdata.

#### **Methods**

```lua
s:get() → number
s:set(number)
s:set_active(true/false)
```

***

## **Slider (Int)**

### `panel:add_slider_int(name, postfix, value, min, max, step, [draw_title], [find_protect])`

Same parameters as the double slider, all integers.

#### **Methods**

```lua
s:get() → integer
s:set(integer)
s:set_active(true/false)
```

***

## **Input Text Box**

### `panel:add_input(name, initial_text, [draw_title], [find_protect])`

#### **Parameters**

| Name           | Type   | Description      |
| -------------- | ------ | ---------------- |
| `name`         | string | Display name     |
| `initial_text` | string | Starting content |

#### **Returns**

`ui_input` userdata.

#### **Methods**

```lua
inp:get() → string
inp:set("text")
inp:set_active(true/false)
```

***

## **Multi Select**

### `panel:add_multi_select(name, options_table, is_expandable, [draw_title], [find_protect])`

#### **`options_table` Format**

```lua
{
    {"Option 1", true},
    {"Option 2", false},
    {"Option 3", true},
}
```

#### **Methods**

```lua
ms:get() → { bool, bool, bool }
ms:set(index, bool)   -- 0-based index!
ms:set_active(true/false)
```

***

## **Single Select**

### `panel:add_single_select(name, options_table, initial_index, is_expandable, [draw_title], [find_protect])`

#### **Methods**

```lua
ss:get() → index
ss:set(index)        -- 0-based
ss:set_active(true/false)
```

***

## **Keybind (Checkbox Child Only)**

### `panel:add_keybind(name, vk_keycode, mode_string, [draw_title], [find_protect])`

⚠ **Must be created immediately after a checkbox**, or it will not attach properly.

#### **Modes**

* `"off"`
* `"on"`
* `"single"`
* `"toggle"`
* `"always_on"`

#### **Methods**

```lua
key, mode = kb:get()
kb:set(0x46, "toggle")
kb:set_active(true/false)
kb:is_pressed()
```

#### **Example**

```lua
local cb = pnl:add_checkbox("Enable Toggle", true)
local kb = pnl:add_keybind("Hotkey", 0x46, "toggle")
```

***

## **Color Picker (Checkbox Child)**

### `panel:add_color(name, {r,g,b,a}, [find_protect])`

⚠ Must be placed immediately after a checkbox.\
Supports **1–2** color pickers per checkbox.

#### **Parameters**

| Channel | Type    | Range |
| ------- | ------- | ----- |
| `r`     | integer | 0–255 |
| `g`     | integer | 0–255 |
| `b`     | integer | 0–255 |
| `a`     | integer | 0–255 |

#### **Methods**

```lua
col:get() → {r,g,b,a}
col:set({255,0,0,128})
col:set_active(true/false)
```

***

## **Button**

### `panel:add_button(name, callback_function)`

#### **Behavior**

* When clicked, the Lua function is executed

#### **Example**

```lua
local btn = pnl:add_button("Reload Script", function()
    print("Reload pressed!")
end)
```

#### **Methods**

```lua
btn:set_active(true/false)
```

***

## **List**

### `panel:add_list(name, entries_table, [draw_title], [find_protect])`

#### **`entries_table` Format**

```lua
{
    {"Name1", "Info1"},
    {"Name2", "Info2"},
}
```

#### **Methods**

**Append**

```lua
lst:append("Enemy3", "HP:50")
```

**Append After (insert)**

```lua
lst:append_after("EnemyX", "HP:99", 1)
```

Inserts after index `1` (0-based).

**Read / Manage**

```lua
lst:get() -> integer
lst:get_all() → { {name, info}, ... }
lst:get_count() → integer
lst:clear()

lst:highlight(index)
lst:remove_highlight(index)
lst:remove(index)   -- 0-based
lst:set_active_index(index)

lst:set_active(true/false)
```

***

## **Visibility (set\_active)**

All elements support:

```lua
element:set_active(true)
element:set_active(false)
```

This applies to all elements

***

## **Full Example**

```lua
local st = ui.create_subtab(0, "Demo UI")
local pnl = st:add_panel("Aimbot Settings", false)

local cb = pnl:add_checkbox("Enable Aimbot", true)

local fov = pnl:add_slider_double("FOV", "°", 90, 1, 180, 1)
local smooth = pnl:add_slider_int("Smoothness", "", 5, 1, 20, 1)

local cb_col_a = pnl:add_checkbox("Primary", true)
local colA = pnl:add_color("Primary", {255, 0, 0, 255})
local cb_col_b = pnl:add_checkbox("Secondary", true)
local colB = pnl:add_color("Secondary", {0, 0, 255, 200})

local lst = pnl:add_list("Targets", {
        {"Player1", "HP:100"},
        {"Player2", "HP:90"},
    })

local btn = pnl:add_button("Print Info", function()
    print("FOV:", fov:get())
    print("Smooth:", smooth:get())
end)

function on_frame()
    
end

function main()
    return 1;
end
```

***

## **Script Unload Behavior**

When a script unloads:

* All subtabs created by it are deleted
* All panels and elements inside them are deleted
* All button callbacks are unregistered
* No UI leftovers remain

***

## **Lookup API**

### `ui.find_element(parent_tab_index, subtab_name, panel_name, element_name, type_string)`

Looks up an existing UI element anywhere in the menu and returns the correct Lua userdata (the same type returned when you created it with `panel:add_*`).

If nothing is found → returns `nil`.

***

#### **Parameters**

| Name               | Type          | Description                           |
| ------------------ | ------------- | ------------------------------------- |
| `parent_tab_index` | integer (0–4) | Which main tab the subtab is in       |
| `subtab_name`      | string        | Name of the subtab                    |
| `panel_name`       | string        | Name of the panel                     |
| `element_name`     | string        | Exact display name of the element     |
| `type_string`      | string        | Type of the element (see table below) |

***

#### **Valid `type_string` Values**

| Type String       | Returns            |
| ----------------- | ------------------ |
| `"checkbox"`      | `ui_checkbox`      |
| `"slider_double"` | `ui_slider_double` |
| `"slider_int"`    | `ui_slider_int`    |
| `"input"`         | `ui_input`         |
| `"multi_select"`  | `ui_multi_select`  |
| `"single_select"` | `ui_single_select` |
| `"keybind"`       | `ui_keybind`       |
| `"color_picker"`  | `ui_color`         |
| `"button"`        | `ui_button`        |
| `"list"`          | `ui_list`          |

***

#### **Return Value**

| Condition     | Returns                                            |
| ------------- | -------------------------------------------------- |
| Element found | Correct UI userdata (checkbox, slider, list, etc.) |
| Not found     | `nil`                                              |

***

#### **Usage Examples**

**Toggle a checkbox**

```lua
local cb = ui.find_element(0, "ESP Settings", "Panel Name", "Enable ESP", "checkbox")
if cb then
    cb:set(not cb:get())
end
```

**Adjust a slider by name**

```lua
local fov = ui.find_element(0, "Aimbot", "Panel Name", "FOV", "slider_double")
if fov then
    fov:set(math.min(180, fov:get() + 5))
end
```

**Highlight list entry by name**

```lua
local lst = ui.find_element(0, "Radar", "Panel Name", "Entities", "list")
if lst then
    lst:highlight(0)
end
```

***

## 🧾 **Config API**

Perception.cx supports saving/loading the entire UI configuration, including all elements, values, and states.

These two APIs allow Lua scripts to trigger that behavior.

***

### `ui.construct_config() → string`

Builds a **full configuration snapshot** of all UI elements.

Returns a config string you can save to disk or use however you like.

#### Example

```lua
local cfg = ui.construct_config()
host.write_file("settings.cfg", cfg) -- using your file API
```

***

### `ui.apply_config(config_string)`

Applies a config previously generated by `ui.construct_config()`.

#### Example

```lua
local cfg = host.read_file("settings.cfg")
if cfg then
    ui.apply_config(cfg)
end
```

***

## `ui.is_active()`

Checks if the gui is currently visible or not

***

### 🏷 Name Prefixing for Elements (`##prefix_`)

The  GUI API supports **name prefixing** so that multiple UI elements can share the **same visible label** while still being uniquely identified by the configuration system.

This is important when you have repeated layouts (per-player, per-item, etc.) and want each control to save/load separately.

#### How It Works

When you pass the `name` parameter to `panel:add_*`:

* The part **after** `##prefix_` is the **visible label** shown in the UI and the rest is unique id
* The **configuration system** (`ui.construct_config` / `ui.apply_config`) uses the **full prefixed name**
* `ui.find_element(...)` **does not take prefix** and matches based on the **visible label only**

So:

```lua
pnl:add_input("##elem1_Player Name", "Alex")
pnl:add_input("##elem2_Player Name", "Bob")
```

Both controls render as:

> Player Name

…but their internal IDs and config entries are different.

***

#### Duplicate Names and Config Behavior

* **Duplicate visible names are allowed even without prefixes.**\
  The UI will render and behave normally.
* However, **without prefixes**, the internal configuration system **cannot uniquely differentiate** those elements:
  * Their saved values can overwrite each other
  * Loading a config may apply the wrong value to the wrong element
* With `##prefix_`, each element has a distinct internal ID, so:
  * `ui.construct_config()` stores them separately
  * `ui.apply_config()` restores each one correctly

***

#### `ui.find_element` and Prefixes

```lua
ui.find_element(parent_tab_index, subtab_name, panel_name, element_name, type_string)
```

* `element_name` is matched against the **visible name only** (the part after `##`).
* If multiple elements share the same visible label:
  * `ui.find_element` will return the **first matching element** of that type in that panel.

Example:

```lua
local pnl = st:add_panel("Players", false)

pnl:add_input("##p1_Name", "Alice")
pnl:add_input("##p2_Name", "Bob")

-- Both show "Name" in the UI

local inp = ui.find_element(0, "Players Tab", "Players", "Name", "input")
if inp then
    -- This will refer to the *first* "Name" input (##p1_Name)
    print(inp:get())
end
```

***

#### When to Use Prefixing

Use the `##prefix_` pattern whenever:

* You have **multiple elements with the same visible label** in the same panel/subtab.
* You care that each element’s value is **saved and loaded distinctly** via the config system.

Example pattern:

```lua
for i, player in ipairs(players) do
    local label = string.format("##p%d_Player Name", i)
    pnl:add_input(label, player.name)
end
```

All rows show **“Player Name”**, but each has its own internal ID and config entry.

***

## 🔒 **Reference Tracking (Internal Behavior)**

Whenever you call:

```
ui.find_element(...)
```

The element is automatically tracked by the script.\
If the element is destroyed elsewhere (e.g., its panel or subtab is removed), the script can safely unregister that reference later.

(You do **not** need to manage this manually — it is just here for understanding the lifecycle.)


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/gui-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/input-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/input-api.md).

# Input API

The Input API provides access to mouse, keyboard, and UI-hover information from Lua scripts.\
These functions are intended to be used inside `on_frame()`.

***

### 🖱 Mouse Input

#### Mouse Position

```lua
x, y = get_mouse_pos()
```

Returns the cursor position **inside the game/overlay window**.

```lua
x, y = get_mouse_pos_desktop()
```

Returns the cursor position in **desktop/screen coordinates**.

***

#### Mouse Delta

```lua
dx, dy = get_mouse_delta()
```

Movement since last frame in overlay space.

```lua
dx, dy = get_mouse_delta_desktop()
```

Movement since last frame in desktop space.

***

#### Scroll Wheel

```lua
amount = get_scroll_delta()
```

Positive for scroll up, negative for scroll down.

***

#### Movement Event

```lua
moved = mouse_movement_received()
```

Returns `true` if the mouse moved this frame.

***

#### Hover Detection

```lua
hovered = is_hovered(x, y, w, h) --overlay window
```

Returns `true` if the mouse is inside the rectangle `(x, y, w, h)`.

***

### ⌨️ Keyboard Input

#### Key Down

```lua
down = key_down(vk)
```

Returns `true` while key is held.

#### Raw Down

```lua
raw = key_raw_down(vk)
```

Reflects OS-level down state before filtering.

#### Fired

```lua
fired = key_fired(vk)
```

Behaves like text input

#### Toggle

```lua
toggle = key_toggle(vk)
```

Toggles each time the key is pressed (flip-flop behavior).

#### Single Press

```lua
single = key_singlepress(vk)
```

True only on the **first frame** the key is pressed.

#### Previous State

```lua
prev = key_prev_down(vk)
```

State from the previous frame.

***

### 🔍 Full Key State

```lua
raw_down, down, fired, toggle, single, prev =
    get_key_state(vk)
```

Returns all internal state fields for a virtual key.

***

### 🧩 Keys Down List

```lua
keys = get_keys_down()
```

Returns a Lua table of all currently pressed virtual keys.

Example:

```lua
for i, vk in ipairs(get_keys_down()) do
    log("Down: " .. get_key_name(vk))
end
```

***

### 📝 Text Input & Key Names

#### Recent Typed Characters

```lua
txt = get_recent_key_input()
```

Returns a string of recently typed characters\
(from your internal text buffer).

#### Key Name

```lua
name = get_key_name(vk)
```

Returns a readable name like `"SPACE"`, `"A"`, `"SHIFT"`.

***

## 📌 Example

```lua
local font = 0
local frame = 0
local last_keys = ""

function main()
    log("Lua Input Test Script Loaded!")
    font = get_font20()
    return 1
end

function on_frame()
    frame = frame + 1
    
    local vw, vh = get_view()
    local scale = get_view_scale()
    
    local mx, my = get_mouse_pos()
    local dx, dy = get_mouse_delta()
    local scroll = get_scroll_delta()
    
    local keys = get_keys_down()
    local recent = get_recent_key_input()
    
    -- Panel
    local w = 450 * scale
    local h = 300 * scale
    local x = 20 * scale
    local y = 20 * scale
    
    draw_rect_filled(
        x, y, w, h,
        20, 20, 25, 220,
        8 * scale,
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT
        )
    
    draw_rect(
        x, y, w, h,
        60, 120, 255, 255,
        2 * scale,
        8 * scale,
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT
        )
    
    local function text(label, value, ox, oy)
        draw_text(
            label .. value,
            x + 10 * scale, y + oy * scale,
            255, 255, 255, 255,
            font,
            TE_SHADOW,
            0,0,0,180,
            1.0,
            true
            )
    end
    
    text("Mouse Pos: ", string.format("%0.1f, %0.1f", mx, my), 10, 10)
    text("Mouse Delta: ", string.format("%0.2f, %0.2f", dx, dy), 10, 40)
    text("Scroll: ", tostring(scroll), 10, 70)
    
    -- Hover test
    local hx, hy, hw, hh = vw*0.5 - 50*scale, vh*0.5 - 50*scale, 100*scale, 100*scale
    local hovered = is_hovered(hx, hy, hw, hh)
    
    draw_rect_filled(
        hx, hy, hw, hh,
        hovered and 60 or 30,
        hovered and 200 or 60,
        hovered and 80 or 60,
        240,
        8*scale,
        RR_TOP_LEFT | RR_BOTTOM_RIGHT
        )
    
    text("Hovered (center box): ", hovered and "true" or "false", 10, 100)
    
    -- Key states
    local space_down = key_down(0x20)
    local space_name = get_key_name(0x20) or "?"
    
    text("SPACE down: ", tostring(space_down), 10, 130)
    text("SPACE name: ", space_name, 10, 190)
    
    -- Keys currently down
    local kd = ""
    for i,vk in ipairs(keys) do
        kd = kd .. get_key_name(vk) .. " "
    end  
    text("Keys down: ", kd, 10, 220)
    
    -- Recent typed characters
    if recent ~= "" then
        last_keys = recent
    end
    text("Recent typed: ", last_keys, 10, 250)
end

function on_unload()
    log("Lua Input Test Script Unloaded")
end

```

***

## 💡 Notes

* `vk` refers to Windows Virtual-Key codes (e.g., `0x41` = `'A'`, `0x20` = Space).
* The Input API is frame-based and intended to be called from inside `on_frame()`.
* `get_recent_key_input()` is ideal for text input boxes or consoles.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/input-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/json-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/json-api.md).

# Json API

The JSON API provides simple, fast parsing and encoding of JSON using native Lua data types.\
All JSON features are exposed under the global `json` table.

***

### Overview

The `json` module supports:

| Operation                   | Description                         |
| --------------------------- | ----------------------------------- |
| **`json.parse(str)`**       | Parse a JSON string into Lua values |
| **`json.decode(str)`**      | Alias of `json.parse`               |
| **`json.stringify(value)`** | Convert Lua values into JSON        |
| **`json.encode(value)`**    | Alias of `json.stringify`           |

The API is intentionally minimal and strictly uses plain Lua tables, numbers, booleans, strings, and `nil`.

***

### JSON → Lua: `json.parse` / `json.decode`

```lua
value, err = json.parse(string)
value, err = json.decode(string)
```

#### Parameters

* **string** — a UTF-8 JSON text.

#### Returns

* On success:\
  **Lua value representing the JSON structure**
* On error:\
  `nil, "error message"`

#### Lua Type Mapping

| JSON             | Lua                                          |
| ---------------- | -------------------------------------------- |
| Object `{}`      | Table `{ key = value }`                      |
| Array `[]`       | Table `{ [1] = ..., [2] = ... }`             |
| `"text"`         | string                                       |
| `123`            | number                                       |
| `true` / `false` | boolean                                      |
| `null`           | **`nil`** (field disappears when iterating!) |

#### Example

```lua
local data, err = json.parse('{"a":1,"b":[10,20],"flag":true}')
print(data.a)         --> 1
print(data.b[1])      --> 10
print(data.flag)      --> true
```

#### Invalid JSON example

```lua
local v, e = json.parse("{ broken json }")
if not v then
    print("Parse failed:", e)
end
```

***

### Lua → JSON: `json.stringify` / `json.encode`

```lua
json_str, err = json.stringify(value)
json_str, err = json.encode(value)
```

#### Parameters

* **value** — any Lua value (table / string / number / boolean / nil)

#### Returns

* On success:\
  **string containing JSON**
* On failure:\
  `nil, "error message"`

#### Supported Lua Types

| Lua     | JSON                              |
| ------- | --------------------------------- |
| String  | `"text"`                          |
| Number  | `123` or `1.23`                   |
| Boolean | `true` / `false`                  |
| Table   | Object or Array *(auto-detected)* |
| nil     | `null` *(inside tables only)*     |

#### Array vs Object Detection

Lua tables are encoded as JSON arrays **only** if they contain:

* continuous integer keys
* starting from `1`
* with no gaps

Otherwise they become JSON objects.

#### Example

```lua
local obj = {
    hello = "world",
    numbers = { 1, 2, 3 }
}

local json_str = json.stringify(obj)
print(json_str)
-- {"hello":"world","numbers":[1,2,3]}
```

#### Mixed Tables

Tables with both numeric and string keys become JSON objects:

```lua
local t = { [1] = "first", [3] = "third", foo = "bar" }
print(json.stringify(t))
-- {"3":"third","1":"first","foo":"bar"}
```

***

### Round-Trip Example

```lua
local original = {
    text = "hello",
    list = { 10, 20, 30 },
    nested = { a = 1, b = { "x", "y" } }
}

local encoded = json.stringify(original)
local decoded = json.parse(encoded)

-- decoded now matches `original`
```

***

### Null Handling

JSON `null` becomes **Lua `nil`**.

This means fields may “disappear” from tables:

```lua
local obj = json.parse('{"a":1,"b":null,"c":2}')
-- obj = { a = 1, c = 2 }
```

This is correct behavior and matches typical JSON–Lua conventions.

***

### Error Handling

All functions safely return:

```lua
nil, "error message"
```

Examples of failure:

* malformed JSON
* unsupported Lua type (function, userdata, thread)

***

### Summary

#### Functions Provided

| Function              | Description                |
| --------------------- | -------------------------- |
| `json.parse(str)`     | Parse JSON into Lua values |
| `json.decode(str)`    | Alias of parse             |
| `json.stringify(val)` | Encode Lua value into JSON |
| `json.encode(val)`    | Alias of stringify         |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/json-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/life-cycle.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/life-cycle.md).

# Life Cycle

Every Lua script **must define** an entry function:

***

#### **main()**

```lua
function main()
    ...
    return number
end
```

| Return Value | Meaning                                              |
| ------------ | ---------------------------------------------------- |
| **> 0**      | Script stays active **only if** `on_frame()` exists. |
| **≤ 0**      | Script unloads immediately after `main()` finishes.  |

***

#### **on\_frame()**

```lua
function on_frame()
    ...
end
```

| Behavior    | Meaning                                                        |
| ----------- | -------------------------------------------------------------- |
| **Missing** | Script unloads right after `main()` (even if it returned > 0). |
| **Exists**  | Runs every frame. Returning **≤ 0** unloads the script.        |

***

### on\_unload()

```lua
function on_unload()
    ...
end
```

* Called once **when the script is about to be unloaded**.
* Use this to clean up state, save data, etc.
* Cannot prevent the script from unloading

***

### ◆ Execution Flow

1. The engine runs the script’s `main()` function.
2. After `main()` returns:
   * If return value **≤ 0** → script unloads.
   * If return value **> 0**:
     * If `on_frame()` exists → script becomes persistent.
     * If `on_frame()` is missing → script unloads immediately.
3. For persistent scripts, `on_frame()` runs every frame until:
   * It returns **≤ 0**, or
   * The script is manually unloaded.
4. When the script is unloading, `on_unload()` is called once (if defined)

***

### ◆ Example #1 — Persistent Script

```lua
function main()
    log("Persistent script.")
    return 1
end

function on_frame()
    log("Tick")
end
```

***

### ◆ Example #2 — One-shot Script

```lua
function main()
    log("This runs once.")
    return 1   -- still unloads because on_frame() is missing
end
```

***

### ◆ Engine Notes

* `main()` is **required**.
* `on_frame()` is **optional**, but required for a script to stay active.
* Returning **≤ 0** from either function unloads the script.
* No infinite loops — frame updates are handled by the engine.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/life-cycle.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/net-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/net-api.md).

# Net API

The Net API provides:

* **HTTP(S)** helpers
  * `net_http_get(url, timeout_ms?)`
  * `net_http_post(url, content_type, body, timeout_ms?)`
* **WebSocket** client using WinHTTP’s WebSocket support
  * `ws_connect(url, timeout_ms?) -> websocket userdata`
  * WebSocket methods:\
    `send_text`, `send_binary`, `send_json`, `recv`, `poll`, `is_open`, `close`

Supported URL schemes:

* HTTP: `http://`, `https://`
* WebSocket: `ws://`, `wss://` (internally mapped to `http://` / `https://` for WinHTTP)
* Works with hostnames **and** IP addresses, with or without custom ports.

> ⚠ These are **low-level** primitives intended for advanced users. Higher-level helpers/wrappers can be built on top, but are not part of this page.

***

### HTTP API

#### `net_http_get`

```lua
ok, status_code, body = net_http_get(url, timeout_ms?)
```

Performs a **synchronous HTTP/HTTPS GET**.

**Parameters**

* `url : string`
  * Full URL:
    * `"https://example.com/api/test"`
    * `"http://127.0.0.1:8080/status"`
* `timeout_ms : number (optional)`
  * Total timeout (ms) applied to resolve, connect, send, receive.
  * `0` or `nil` = default WinHTTP timeouts.

**Returns**

* `ok : boolean`
  * `true` if the HTTP request succeeded at the transport level (WinHTTP OK).
  * `false` if there was a network/protocol error.
* `status_code : integer`
  * HTTP status code (200, 404, 500, ...)
  * `0` if the request failed before a response was received.
* `body : string`
  * Response body as raw bytes (Lua string).

**Example**

```lua
local ok, status, body = net_http_get("https://httpbin.org/get", 5000)

if not ok then
    log("[HTTP] GET failed, status=" .. tostring(status))
    return
end

log("[HTTP] GET status=" .. status)
log("[HTTP] GET body=" .. body)
```

***

#### `net_http_post`

```lua
ok, status_code, body = net_http_post(url, content_type, body, timeout_ms?)
```

Performs a **synchronous HTTP/HTTPS POST** with a request body.

**Parameters**

* `url : string`
  * Full URL, same as `net_http_get`.
* `content_type : string`
  * MIME type, e.g.:
    * `"application/json"`
    * `"application/x-www-form-urlencoded"`
    * `"text/plain; charset=utf-8"`
* `body : string`
  * Request body as a Lua string (raw bytes).
* `timeout_ms : number (optional)`
  * Same semantics as `net_http_get`.

**Returns**

* `ok : boolean`
* `status_code : integer`
* `body : string`\
  (Same meaning as `net_http_get`.)

**Example – POST JSON**

```lua
local payload = '{"hello":"world","value":123}'

local ok, status, resp = net_http_post(
    "https://httpbin.org/post",
    "application/json",
    payload,
    5000
)

if not ok then
    log("[HTTP] POST failed, status=" .. tostring(status))
    return
end

log("[HTTP] POST status=" .. status)
log("[HTTP] POST body=" .. resp)
```

***

### WebSocket API

The WebSocket API exposes:

* A global **constructor**: `ws_connect(url, timeout_ms?)`
* A userdata type **`net_ws`** with methods:
  * `send_text`, `send_binary`, `send_json`
  * `recv`, `poll`
  * `is_open`, `close`

Internally, the implementation uses WinHTTP:

* `ws://` → internally mapped to `http://`
* `wss://` → internally mapped to `https://`
* A background **receive thread** continuously reads frames and pushes **complete messages** into a queue.
* Lua sees messages via `ws:recv()` (blocking) or `ws:poll()` (non-blocking).

#### Global: `ws_connect`

```lua
ws, err = ws_connect(url, timeout_ms?)
```

Opens a **client WebSocket** connection.

**Parameters**

* `url : string`
  * WebSocket URL, e.g.:
    * `"wss://ws.postman-echo.com/raw"`
    * `"ws://127.0.0.1:9001/echo"`
* `timeout_ms : number (optional)`
  * WinHTTP timeouts (resolve, connect, send, receive).

**Returns**

* On success:
  * `ws : userdata` (type `net_ws`)
    * A WebSocket object with methods described below.
* On failure:
  * `nil, "error string"`

**Example**

```lua
local ws, err = ws_connect("wss://ws.postman-echo.com/raw", 5000)
if not ws then
    log("[WS] connect failed: " .. tostring(err))
    return
end

log("[WS] connected: " .. tostring(ws))  -- e.g. "websocket(open)"
```

***

### WebSocket Object (`net_ws`)

Once connected, you have a userdata with metatable `"net_ws"`, exposing these methods:

* `ws:send_text(message)`
* `ws:send_binary(data)`
* `ws:send_json(value)`
* `ws:recv()`
* `ws:poll()`
* `ws:is_open()`
* `ws:close(code?)`

And metamethods:

* `__gc` – automatic cleanup
* `__tostring` – `"websocket(open)"` or `"websocket(closed)"`

***

#### `ws:send_text`

```lua
ok = ws:send_text(message)
```

Sends a **UTF-8 text message**.

**Parameters**

* `message : string` – Lua string, treated as UTF-8.

**Returns**

* `ok : boolean` – `true` if the send call succeeded; `false` otherwise.

**Example**

```lua
local ok = ws:send_text("hello from PCX")
log("[WS] send_text ok = " .. tostring(ok))
```

***

#### `ws:send_binary`

```lua
ok = ws:send_binary(data)
```

Sends a **binary WebSocket frame**.

**Parameters**

* `data : string` – raw bytes (Lua string).

> ⚠ Some public echo servers (e.g. Postman’s) **close the connection** when they receive binary frames. That’s a server behavior, not a bug in the API.

**Returns**

* `ok : boolean`

**Example**

```lua
local bin = string.char(0,1,2,3,4,5)
local ok = ws:send_binary(bin)
log("[WS] send_binary ok = " .. tostring(ok))
```

***

#### `ws:send_json`

```lua
ok = ws:send_json(value)
```

Sends a **JSON text message**. Supports:

* `value` = **string**: sent directly as UTF-8.
* `value` = **table**: encoded via global Lua function `json_encode`.

**Parameters**

* `value : string | table`
  * `string` – assumed to already be valid JSON.
  * `table` – will call `json_encode(value)` to produce JSON.

**Requirements**

* For `table`:
  * A global function `json_encode` must exist:

    ```lua
    function json_encode(tbl) -> string
    ```
  * If `json_encode` is missing or throws, `ws:send_json` raises a Lua error.

**Returns**

* `ok : boolean`

**Example – string**

```lua
local js = '{"type":"ping","time":123.45}'
ws:send_json(js)
```

**Example – table**

```lua
-- Assuming json_encode is registered globally in this environment.

ws:send_json({
    type = "ping",
    time = perf_time(),
    source = "pcx"
})
```

***

#### `ws:recv` (blocking)

```lua
msg, is_text = ws:recv()
```

**Blocking** receive that waits for a **complete WebSocket message** to be available in the queue.

* Uses the internal message queue (filled by a background thread).
* Does **not** block WinHTTP directly; it loops until:
  * A message is dequeued, or
  * The socket is closed and the queue is empty.

**Returns**

* On message:
  * `msg : string` – message payload (text or binary).
  * `is_text : boolean`
    * `true` for text frames
    * `false` for binary frames
* On closed and empty:
  * `nil`

> ⚠ This is a **blocking loop with a small sleep** (`Sleep(1)`).\
> Best used in worker scripts or one-shot tests, not every frame in the UI thread.

**Example**

```lua
local msg, is_text = ws:recv()
if not msg then
    log("[WS] recv: connection closed or error")
else
    log("[WS] recv: kind=" .. (is_text and "text" or "binary")
        .. " len=" .. #msg)
end
```

***

#### `ws:poll` (non-blocking)

```lua
msg, is_text_or_closed = ws:poll()
```

**Non-blocking** receive from the internal message queue.

You get **three possible outcomes**:

1. **Message available**
   * `msg : string` – message payload
   * `is_text_or_closed : boolean` – `true` = text, `false` = binary
2. **No message yet, still open**
   * `msg = nil`
   * `is_text_or_closed` is **nil**
3. **Socket closed and queue empty**
   * `msg = nil`
   * `is_text_or_closed = false`

This makes it easy to integrate in per-frame loops:

* `msg != nil` → handle it
* `msg == nil and is_text_or_closed == nil` → nothing yet
* `msg == nil and is_text_or_closed == false` → closed

**Example: per-frame polling**

```lua
function on_frame()
    if not ws then return end

    local msg, flag = ws:poll()
    if msg then
        local kind = flag and "text" or "binary"
        log("[WS] poll: " .. kind .. " msg=" .. msg)
    elseif flag == false then
        log("[WS] poll: socket closed")
        ws = nil
    end
end
```

***

#### `ws:is_open`

```lua
is_open = ws:is_open()
```

Checks whether the socket is currently open.

* Reflects the internal `is_open` flag updated by the background thread and close logic.

**Returns**

* `true` if the socket is open.
* `false` if it is closed or has encountered a fatal error.

**Example**

```lua
if ws and ws:is_open() then
    ws:send_text("still here")
else
    log("[WS] socket is closed")
end
```

***

#### `ws:close`

```lua
ws:close(code?)
```

Closes the WebSocket connection.

* Signals the background receive thread to stop.
* Sends a WebSocket close frame (best effort).
* Waits for the thread to exit, then closes all WinHTTP handles.

**Parameters**

* `code : integer (optional)`
  * WebSocket close status. Defaults to `WINHTTP_WEB_SOCKET_SUCCESS_CLOSE_STATUS`.

**Example**

```lua
if ws then
    ws:close()  -- normal clean shutdown
    ws = nil
end
```

***

#### Metamethods

**`__gc`**

Called automatically when the Lua userdata is garbage collected.

* Calls `ws_close_internal`, deletes the critical section, frees `lua_ws_t`.
* You don’t call this directly; it’s tied to object lifetime.

**`__tostring`**

Used when you do:

```lua
tostring(ws)
```

* Returns `"websocket(open)"` or `"websocket(closed)"`.

Example:

```lua
log("WS object: " .. tostring(ws))
```

***

### Summary

**Global HTTP:**

```lua
ok, status, body = net_http_get(url, timeout_ms?)
ok, status, body = net_http_post(url, content_type, body, timeout_ms?)
```

**Global WebSocket:**

```lua
ws, err = ws_connect(url, timeout_ms?)
```

**WebSocket object (`net_ws`):**

```lua
ws:send_text(message)         -- bool
ws:send_binary(data)          -- bool
ws:send_json(value)           -- bool (string or table with json_encode)
ws:recv()                     -- msg, is_text | nil  (blocking)
ws:poll()                     -- msg, is_text | nil | nil,false
ws:is_open()                  -- bool
ws:close(code?)               -- nil
tostring(ws)                  -- "websocket(open)" / "websocket(closed)"
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/net-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/overview.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/overview.md).

# Overview

This environment provides a lightweight scripting layer for UI, rendering, memory analysis and interaction in Perception.cx. It uses **Lua** with core add-ons and PCX-specific APIs enabled by default.

This API is strictly allowed to be used for malware analysis and educational purposes only, any violation of our [TOS](https://perception.cx/help/terms/) will result in termination from the platform.

### Core Add-ons

The following standard AngelScript modules are registered:

* **base** — core Lua functions
* **package** — `require()` and module loading
* **coroutine** — coroutine creation & scheduling
* **table** — table helpers (`insert`, `remove`, `sort`, ...)
* **string** — pattern matching & string utilities
* **math** — numeric functions
* **utf8** — UTF-8 text helpers

***

### PCX APIs

Custom host APIs extend the scripting environment:

* **Render API** — draw shapes, text, images, and gradients
* **Input API** — mouse, keyboard, and scroll input
* **Host Utilities** — logging and script lifecycle helpers
* **Proc API** — memory inspection and manipulation
* **GUI API** — create and interact with UI elements
* **System API** — CPU info, instruction utilities, disassembly
* **Net API** — HTTP, HTTPS, and WebSocket networking
* **File System API** — read, write, and manage files/folders
* **Extended Math API** — vectors, matrices, quaternions, and math helpers
* **Engine Specific API**  — read engine specific structures easier
* **Json API**
* **Utilities** — encoding, decoding, etc
* **Sound API**&#x20;


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/overview.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/proc-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/proc-api.md).

# Proc API

This API lets scripts inspect and modify the memory of external processes via a `process` userdata.\
Handles are created with `ref_process(...)` and released with `deref_process(process)`.

***

### 🔑 Process Handles

#### Userdata Type

All functions operate on a `process` userdata created by `ref_process`.

```lua
-- Get a process handle by PID
local proc = ref_process(1234)

-- Get a process handle by name
local proc = ref_process("notepad.exe")
```

If the process is not found, `ref_process` returns `nil`.

***

#### Referencing / Releasing

```lua
process = ref_process(pid_or_name)   -- global
deref_process(process)               -- global
```

* `ref_process(pid)` – `pid` is a number (Windows PID).
* `ref_process("name.exe")` – search by executable name.
* `deref_process(process)` – releases the reference; the userdata becomes invalid.
* You must also call `deref_process` if `process:alive()` returns `false`.

> Each Lua script keeps its own list of referenced processes internally.\
> Always call `deref_process(proc)` when you’re done.

***

### 🧬 Process Info

```lua
process:base_address()  --> number (uint64)
process:peb()           --> number (uint64)
process:pid()           --> number (uint)
process:alive()         --> bool
```

* `base_address()` – Image base address of the process.
* `peb()` – Address of the process’ PEB.
* `pid()` – Process ID.
* `alive()` -  Determines whether the process is currently alive and running.

***

#### Address Validity

```cpp
process:is_valid_address(address)   --> bool
```

Check if an address is mapped inside target process.

***

### 📖 Scalar Reads

All addresses are **virtual addresses** in the target process.

#### Unsigned Integers

```lua
process:ru8(addr)   --> uint8
process:ru16(addr)  --> uint16
process:ru32(addr)  --> uint32
process:ru64(addr)  --> uint64
```

Reads unsigned integers from `addr`.

***

#### Signed Integers

```lua
process:r8(addr)   --> int8
process:r16(addr)  --> int16
process:r32(addr)  --> int32
process:r64(addr)  --> int64
```

Reads signed integers from `addr`.

***

#### Floating Point

```lua
process:rf32(addr) --> float
process:rf64(addr) --> double
```

Reads floating point values from `addr`.

***

### ✏️ Scalar Writes

#### Unsigned Integers

```lua
process:wu8(addr,  value) --> bool
process:wu16(addr, value) --> bool
process:wu32(addr, value) --> bool
process:wu64(addr, value) --> bool
```

Writes an unsigned integer at `addr`.\
Returns `true` on success.

***

#### Signed Integers

```lua
process:w8(addr,  value) --> bool
process:w16(addr, value) --> bool
process:w32(addr, value) --> bool
process:w64(addr, value) --> bool
```

Writes a signed integer at `addr`.

***

#### Floating Point

```lua
process:wf32(addr, value) --> bool
process:wf64(addr, value) --> bool
```

Writes `float` / `double`.

***

### 🔤 Strings

Read and write null-terminated strings from the remote process.

#### Read Strings

```lua
process:rs(addr,  max_chars) --> string    -- ANSI / UTF-8 style
process:rws(addr, max_chars) --> string    -- UTF-16 wide -> Lua string
```

* `rs` – Reads up to `max_chars` characters from `addr`.
* `rws` – Reads a wide string and converts it to a Lua UTF-8 string.
* If nothing valid is read, an empty string is returned.

***

#### Write Strings

```lua
process:ws(addr,  text) --> bool   -- ANSI / UTF-8
process:wws(addr, text) --> bool   -- UTF-16 wide
```

* `ws` – Writes `text` bytes plus a terminating `\0`.
* `wws` – Converts `text` to UTF-16 and writes plus wide `\0`.

Returns `true` on success.

***

### 📦 Raw Memory (byte tables)

Use Lua tables of bytes (`1..N`, values `0–255`) for bulk reads / writes.

```lua
process:rvm(addr, size)          --> { byte1, byte2, ... }
process:wvm(addr, byte_table)    --> bool
```

* `rvm` – Returns a new table of length `size` filled with bytes from `addr`.
* `wvm` – Writes all bytes in `byte_table` to `addr`.\
  Returns `true` if all bytes are written.

***

### 🧮 SIMD Helpers

Convenience helpers for 16/32/64-byte SIMD vectors (raw bytes).

```lua
process:r128(addr)        --> { b1..b16 }
process:r256(addr)        --> { b1..b32 }
process:r512(addr)        --> { b1..b64 }

process:w128(addr, t16)   --> bool  -- t16 length >= 16
process:w256(addr, t32)   --> bool  -- t32 length >= 32
process:w512(addr, t64)   --> bool  -- t64 length >= 64
```

All values are plain bytes (`0–255`).\
`wXXX` returns `false` if the table is too short or the write fails.

***

### 📦 Modules & Pattern Scanning

#### Module Lookup

```lua
local base, size = process:get_module(name)
```

* `name` – Module name, e.g. `"notepad.exe"`, `"client.dll"`.
* Returns `base, size` on success.
* Returns `nil` if the module is not found.

***

#### Code Pattern Scan

```lua
local addr = process:find_code_pattern(search_start, search_size, signature)
```

* `search_start` – Starting address.
* `search_size` – Number of bytes to scan.
* `signature` – Pattern string, e.g. `"48 8B ?? ?? ?? 89"`\
  (same format as your internal pattern scanner).

Returns:

* `addr` – Address of the first match, or `0` if not found.

***

### 🔍 Example: Scanning Notepad (Lua)

```lua
function main()
    log("==== LUA PROC API TEST START ====")

    local proc = ref_process("notepad.exe")
    if not proc then
        log("[-] Failed to ref notepad.exe")
        return
    end

    local pid   = proc:pid()
    local base  = proc:base_address()
    local peb   = proc:peb()

    log(string.format("[+] Referenced Notepad: pid=%d", pid))
    log(string.format("    Base Address = 0x%016X", base))
    log(string.format("    PEB          = 0x%016X", peb))

    -- DOS header
    local b0 = proc:ru8(base)
    local b1 = proc:ru8(base + 1)
    log(string.format("Header bytes: %02X %02X", b0, b1))

    -- First 16 bytes as hex
    local raw = proc:rvm(base, 16)
    local hex = {}
    for i = 1, #raw do
        hex[#hex+1] = string.format("%02X", raw[i])
    end
    log("DOS header (16 bytes): " .. table.concat(hex, " "))

    -- Module + pattern scan
    local mod_base, mod_size = proc:get_module("notepad.exe")
    if mod_base then
        log(string.format("Module Base = 0x%016X", mod_base))
        log(string.format("Module Size = 0x%X",    mod_size))

        local addr = proc:find_code_pattern(mod_base, mod_size, "4D 5A")
        log(string.format("Pattern '4D 5A' found at 0x%016X", addr))
    else
        log("[-] get_module('notepad.exe') failed")
    end

    -- SIMD round-trip (128-bit)
    local v128 = proc:r128(base)
    local ok = proc:w128(base, v128)
    log("w128 ok? " .. tostring(ok))

    deref_process(proc)
    log("==== LUA PROC API TEST END ====")
end
```

***

## `proc:read_struct`

Reads a **single C-style structure** from the target process using a descriptor table.

***

### **Signature**

```lua
table proc:read_struct(uint64 base_address, table descriptor)
```

***

### **Parameters**

#### **`base_address`**

Absolute address of the struct in the remote process.

#### **`descriptor`**

A Lua table describing each struct field:

```lua
field_name = {
    offset = <byte offset>,
    type   = "<field type>"
}
```

***

### **Supported Types**

| Type  | Size | Notes           |
| ----- | ---- | --------------- |
| `u8`  | 1    | unsigned 8-bit  |
| `u16` | 2    | unsigned 16-bit |
| `u32` | 4    | unsigned 32-bit |
| `u64` | 8    | unsigned 64-bit |
| `i8`  | 1    | signed 8-bit    |
| `i16` | 2    | signed 16-bit   |
| `i32` | 4    | signed 32-bit   |
| `i64` | 8    | signed 64-bit   |
| `f32` | 4    | float           |
| `f64` | 8    | double          |

***

### **Returns**

A **Lua table** containing the decoded fields:

```lua
local t = proc:read_struct(addr, DESC)

print(t.health)
print(t.pos_x)
```

***

### **Example – Reading IMAGE\_DOS\_HEADER**

```lua
local DOS_HEADER = {
    e_magic  = { offset = 0x00, type = "u16" },
    e_lfanew = { offset = 0x3C, type = "u32" },
}

local proc = ref_process("notepad.exe")
local base = proc:get_module("notepad.exe")

local dos = proc:read_struct(base, DOS_HEADER)

log_console(string.format("e_magic  = 0x%04X", dos.e_magic))
log_console(string.format("e_lfanew = 0x%08X", dos.e_lfanew))
```

***

## 📘 `proc:read_struct_array`

Reads an **array of structures** from the target process.

***

### **Signature**

```lua
table proc:read_struct_array(
    uint64 base_address,
    integer count,
    integer struct_size,
    table descriptor
)
```

***

### **Parameters**

#### **`base_address`**

Address of the **first** element in the array.

#### **`count`**

Number of array elements to read.

#### **`struct_size`**

Size in bytes of each array element.

#### **`descriptor`**

Same descriptor table used with `read_struct`.

***

### **Returns**

A **1-based Lua array**, where each element is a struct table:

```lua
local arr = proc:read_struct_array(addr, 10, 0x140, DESC)
print(arr[1].health)
```

***

### **Example – Reading a Player Array**

```lua
local PLAYER = {
    health = { offset = 0x10, type = "i32" },
    armor  = { offset = 0x14, type = "i32" },
    pos_x  = { offset = 0x30, type = "f32" },
}

local base = 0x12345678
local size = 0x140
local count = 5

local players = proc:read_struct_array(base, count, size, PLAYER)

for i, p in ipairs(players) do
    log_console(string.format(
        "Player %d: hp=%d armor=%d x=%.1f",
        i, p.health, p.armor, p.pos_x
    ))
end
```

***

### `proc:get_all_tebs()`

Returns a Lua table of **TEB addresses (uint64)** for threads in the target process.

**Syntax**

```lua
local tebs = proc:get_all_tebs()
```

**Returns**

* `{ teb1, teb2, ... }` where each `teb` is a **virtual address** in the remote process
* `{}` if none found / enumeration fails

***

### Virtual Memory Allocation

These functions let you allocate and manage RWX memory inside the target process.\
They are intended for advanced use; you are fully responsible for tracking and freeing any allocations you create.

#### :red\_circle: Important Memory Management Notes (MUST READ!)

These points are critical for using `alloc_vm` safely:

* **Control Flow Guard**                                                                                                                                                          If the target process has Control Flow Guard (CFG) enabled and you intend to execute code from this region, CFG may block all jumps and calls into the allocated memory.\
  To avoid this, CFG must be fully disabled for the target process.\
  Be aware that disabling CFG reduces the security of the device.
* **Allocations are not automatically freed.**\
  Every allocation you create must be manually released using `free_vm()`. If you lose track of an allocation, the memory will remain reserved until the target process exits.
* **Allocations persist for the lifetime of the target process.**\
  Memory created with `alloc_vm` is automatically released only when the **target process** itself closes.
* **Closing the Perception overlay will clear all allocations.**\
  When the overlay is closed, Perception will clean up every RWX allocation for *all* processes currently referenced.\
  If you need an allocation to stay alive, **do not close the overlay** while that memory is being used.
* **Repeated unfreed allocations can exhaust physical memory.**\
  If you repeatedly allocate memory without freeing it, these leaks will accumulate and can eventually **consume all available physical RAM**, potentially degrading system performance or causing instability. If you are writing an injector make sure your inject frees the memory&#x20;
* **If you are writing an injector, you must free allocated memory.**\
  Any injector, loader, or external tool that allocates memory through `alloc_vm` is responsible for freeing it once the memory is no longer needed.\
  Failing to do so will leave permanent physical memory leaks until the target process exits.

***

### Functions

```lua
uint64 proc:alloc_vm(uint size)
bool   proc:free_vm(uint64 address)
```

### `uint64 proc:alloc_vm(size)`

Allocates a block of **read–write–execute (RWX)** memory inside the target process and returns its base address.

#### Parameters

* **size** — Size of the allocation in bytes.

#### Returns

* Base address of the allocation on success.
* `0` on failure.

#### Notes

* Allocated memory is **not tied to any module** and is **not discoverable** through helpers like module queries or pattern scans.\
  You must store and manage the returned address yourself.
* The memory is RWX.\
  If the target process uses **Control Flow Guard (CFG)** and you intend to execute code from this region, CFG may block jumps/calls unless the target allows it.

***

### `bool proc:free_vm(address)`

Frees a region previously allocated with `proc:alloc_vm()`.

#### Parameters

* **address** — The exact base address returned by `alloc_vm`.

#### Returns

* `true` if the region was successfully freed.
* `false` if the address is invalid or the free fails.

***

#### 🔗 Export Lookup – `process:get_proc_address`

```lua
addr = process:get_proc_address(module_base, export_name)
```

Resolves the address of an **exported function or symbol** inside a module in the target process.

* `module_base`\
  Base address of the module **inside the target process**.\
  Typically obtained from:
  * `process:base_address()`, or
  * `local base, size = process:get_module("module_name.dll")`.
* `export_name`\
  Name of the exported function/symbol, e.g. `"Sleep"`, `"CreateFileW"`, `"DllMain"`.

**Returns**

* Absolute **virtual address** of the exported symbol in the target process (as a Lua integer).
* `0` if the export is not found or the arguments are invalid.

**Notes**

* This walks the module’s **export table only** – it does *not* look at imports or IAT.
* The returned address is suitable for:
  * Remote call stubs / shellcode.
  * Manual thunks that jump directly to an API inside the target module.

**Example**

```lua
local proc = ref_process("notepad.exe")
if not proc then return end

local kbase, ksize = proc:get_module("KERNEL32.DLL")
if kbase then
    local addr_sleep = proc:get_proc_address(kbase, "Sleep")
    log(string.format("Sleep @ 0x%016X", addr_sleep))
end

deref_process(proc)
```

***

#### 🧷 Import Table (IAT) Slot Lookup – `process:get_import_rdata_address`

```lua
slot_addr = process:get_import_rdata_address(module_base, import_name)
```

Resolves the **address of the import table entry** (IAT slot) for a given imported function inside a module.

This does **not** return the function’s address itself – it returns the address of the **pointer stored in `.rdata` / IAT**. You can then read or patch that pointer for IAT hooks.

* `module_base`\
  Base address of the module whose imports you want to inspect/patch\
  (usually the main EXE or a specific DLL), e.g. from `process:get_module(...)`.
* `import_name`\
  Name of the imported function (as it appears in the import table), e.g. `"Sleep"`, `"MessageBoxW"`.

**Returns**

* Address of the **IAT entry** (pointer-sized slot) as a Lua integer.
* `0` if the import cannot be found or arguments are invalid.

**Typical usage**

* Read the current imported function pointer:

  ```lua
  local slot = proc:get_import_rdata_address(mod_base, "Sleep")
  if slot ~= 0 then
      local current = proc:ru64(slot)   -- current function pointer
      log(string.format("IAT[Sleep] = 0x%016X", current))
  end
  ```
* Install a simple IAT hook (patch the slot to point to your stub):

  ```lua
  local slot = proc:get_import_rdata_address(mod_base, "Sleep")
  if slot ~= 0 then
      -- 'stub_addr' is an RWX address you allocated with proc:alloc_vm(...)
      local ok = proc:wu64(slot, stub_addr)
      log("IAT hook applied? " .. tostring(ok))
  end
  ```

**Notes**

* Only sees functions present in the module’s **static import table**.
* Manually resolved APIs (e.g. `GetProcAddress` into some custom region) will **not** show up here.
* Designed for **IAT hooks** and for shellcode that wants to call through the same import slot as the module.

***

### Virtual Memory Analysis

#### `proc:virtual_query(address) -> (start:uint64, size:uint64, protection:int, heap_likely:bool)|nil`

Queries the virtual memory region containing the given `address`.

**Parameters:**

* `address` — a `uint64` virtual address.

**Returns:**

* `start` — region base address (`uint64`)
* `size` — region size in bytes (`uint64`)
* `protection` — region protection flags (`int`)
* `heap_likely` — `true` if the region is heuristically likely to be heap/alloc-like (`bool`)
* `nil` if the address is not mapped or cannot be queried.

***

#### `proc:get_vad_snapshot(heap_likely_only:bool) -> table`

Builds a snapshot of virtual memory regions.

**Parameters:**

* `heap_likely_only` — when `true`, only heap-like regions are returned; when `false`, all regions are returned.

**Returns:**

A 1-based Lua array of region tables:

```lua
{
   { start=<uint64>, size=<uint64>, ["end"]=<uint64>, protection=<int>, heap_likely=<bool> },
   ...
}
```

Each region table contains:

* `start` (`uint64`)
* `size` (`uint64`)
* `end` (`uint64`)
* `protection` (`int`)
* `heap_likely` (`bool`)

***

#### **Memory Scanning Helpers**

These helpers scan the target process memory by iterating over the snapshot of virtual memory regions. All scanning functions return a **1-based Lua table** of matching virtual addresses:

```lua
{ addr1, addr2, ... }
```

***

#### `proc:scan_string(text:string, heap_only:bool|nil) -> table`

Scan for occurrences of an ASCII/multibyte constant string in memory.

* `text` — the pattern to search for.
* `heap_only` — optional `bool` filter restricting scan to heap-like regions (`false` if nil).

***

#### `proc:scan_wstring(text:string, heap_only:bool|nil) -> table`

Scan for occurrences of a UTF-16 (wide) string.

* `text` — the wide string to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_pointer(target:uint64, heap_only:bool|nil) -> table`

Find all references to a pointer value.

* `target` — the pointer value to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_u64(value:uint64, heap_only:bool|nil) -> table`

Scan for a 64-bit unsigned integer value in memory.

* `value` — the uint64 value to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_u32(value:int, heap_only:bool|nil) -> table`

Scan for a 32-bit unsigned integer value in memory.

* `value` — the uint32 value to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_float(value:float, heap_only:bool|nil) -> table`

Scan for a 32-bit float value in memory.

* `value` — float pattern to search for.
* `heap_only` — optional `bool` filter.

***

#### `proc:scan_double(value:float, heap_only:bool|nil) -> table`

Scan for a 64-bit double value in memory.

* `value` — double pattern to search for.
* `heap_only` — optional `bool` filter.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/proc-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/render-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/render-api.md).

# Render API

### Constants

```lua
RR_TOP_LEFT
RR_TOP_RIGHT
RR_BOTTOM_LEFT
RR_BOTTOM_RIGHT
```

Rectangle corner rounding flags (bitmask), used with `rounding_flags` in rect functions.

```lua
TE_NONE
TE_OUTLINE
TE_SHADOW
TE_GLOW
```

Text effects used by `draw_text`.

***

### Viewport

```lua
w, h = get_view()
scale = get_view_scale()
fps = get_fps()
```

* `get_view()` — returns the current viewport width and height in pixels.
* `get_view_scale()` — returns a reference scale factor (useful for DPI-aware sizes).
* `get_fps()`

***

### Shapes

#### Rectangle (outline)

```lua
draw_rect(x, y, w, h,
          r, g, b, a,
          thickness, rounding, rounding_flags)
```

Draws a rounded rectangle outline.

***

#### Rectangle (filled)

```lua
draw_rect_filled(x, y, w, h,
                 r, g, b, a,
                 rounding, rounding_flags)
```

Draws a filled rounded rectangle.

***

#### Line

```lua
draw_line(x1, y1, x2, y2,
          r, g, b, a,
          thickness)
```

Draws a line from `(x1, y1)` to `(x2, y2)`.

***

#### Arc

```lua
draw_arc(cx, cy, rx, ry,
         start_angle_deg, sweep_angle_deg,
         r, g, b, a,
         thickness, filled)
```

Draws an arc or pie-slice centered at `(cx, cy)`.

***

#### Circle

```lua
draw_circle(cx, cy, radius,
            r, g, b, a,
            thickness, filled)
```

Draws a circle centered at `(cx, cy)`.

* If `filled == true`, draws a filled circle.
* Otherwise draws an outlined circle.

***

#### Triangle

```lua
draw_triangle(ax, ay, bx, by, cx, cy,
              r, g, b, a,
              thickness, filled)
```

Draws a triangle using the three points `(ax, ay)`, `(bx, by)`, `(cx, cy)`.

***

#### Polygon

```lua
draw_polygon(xy_pairs, count_pairs,
             r, g, b, a,
             thickness, filled)
```

* `xy_pairs` — Lua table of floats: `{ x1, y1, x2, y2, x3, y3, ... }`.
* `count_pairs` — optional; if `nil` or `0`, uses the whole table.

Draws a polyline or filled polygon.

***

#### Four-Corner Gradient

```lua
draw_four_corner_gradient(x, y, w, h,
                          tlr, tlg, tlb, tla,
                          trr, trg, trb, tra,
                          blr, blg, blb, bla,
                          brr, brg, brb, bra,
                          rounding)
```

Draws a rectangle with independent colors per corner:

* top-left: `(tlr, tlg, tlb, tla)`
* top-right: `(trr, trg, trb, tra)`
* bottom-left: `(blr, blg, blb, bla)`
* bottom-right: `(brr, brg, brb, bra)`

***

### Bitmaps

#### Create bitmap

```lua
bmp = create_bitmap(data)
```

* `data` — Lua table of `uint8` values (byte buffer).
* Returns a handle `bmp` that can be passed to `draw_bitmap`.
* Returns `0` on failure.

***

#### Draw bitmap

```lua
draw_bitmap(bmp, x, y, w, h,
            r, g, b, a,
            rounded)
```

Draws a bitmap tinted with color `(r, g, b, a)`.

* `bmp` — handle returned by `create_bitmap`.
* `rounded` — if `true`, draws with rounded corners.

***

### Fonts & Text

#### Built-in fonts

```lua
font = get_font18()
font = get_font20()
font = get_font24()
font = get_font28()
```

Returns a handle to a default font at a given size.

***

#### Create font from file

```lua
font = create_font(path, size, anti_aliased, load_color, optional:glyph_ranges)
```

* `path` — filesystem path or font name.
* `size` — font size in pixels.
* `anti_aliased` — `true` for smooth text, `false` for pixel-style rendering (boolean).
* `load_color` — `true` to enable color glyphs (emoji / color fonts), `false` for standard monochrome glyphs (boolean).
* `glyph_ranges`  — array of custom glyph ranges
* Returns a font handle or `0` on failure.

The function searches for fonts inside the API directory (e.g. `verdana_custom.ttf`, `fonts/verdana_custom.ttf`) and may fall back to system font locations.\
If a font name matches a system font, that one may be loaded instead— use unique names to prevent conflicts.

***

#### Create font from memory

```lua
font = create_font_mem(label, size, buf , anti_aliased, load_color, optional:glyph_ranges)
```

* `label` — name/tag for the font (string).
* `size` — font size in pixels.
* `buf` — Lua table of `uint8` values (font binary data).
* `anti_aliased` — `true` for smooth text, `false` for pixel-style rendering (boolean).
* `load_color` — `true` to enable color glyphs (emoji / color fonts), `false` for standard monochrome glyphs (boolean).
* `glyph_ranges`  — array of custom glyph ranges
* Returns a font handle or `0` on failure.

***

#### Using custom glyph ranges

```lua
local ranges = {
    0x0020, 0x00FF,   -- Basic Latin + Latin-1 Supplement
    0x0400, 0x04FF,   -- Cyrillic
    0
}
local font2 = create_font("Arial", 16.0, true, false, ranges)
```

***

#### Draw text

```lua
draw_text(text, x, y,
          r, g, b, a,
          font, effect,
          er, eg, eb, ea,
          effect_amount)
```

* `text` — string to draw.
* `(r, g, b, a)` — text color.
* `font` — font handle.
* `effect` — one of `TE_NONE`, `TE_OUTLINE`, `TE_SHADOW`, `TE_GLOW`.
* `(er, eg, eb, ea)` — effect color (e.g. shadow/outline color).
* `effect_amount` — intensity scalar.

***

#### Text metrics

```lua
w, h = get_text_size(font, text,
                     maxw, maxh)

advance = get_char_advance(font, wchar32)
```

* `get_text_size` — returns width/height of the rendered `text`.
* `get_char_advance` — returns advance width for a single character (`wchar32`).

***

### Clipping

```lua
clip_push(x, y, w, h)
clip_pop()
```

* `clip_push` — pushes a rectangular clip region.
* `clip_pop` — restores the previous clip region.

All drawing while a clip is active is restricted to the specified rectangle.

***

### Example

```lua
local font = 0
local t = 0

function main()
    log("Lua render example loaded.")

    -- Use built-in default font
    font = get_font20()

    return 1 -- keep script running
end

function on_frame()
    -- Get viewport
    local vw, vh = get_view()
    local scale  = get_view_scale()

    t = t + 1

    -- Panel size
    local w  = 260 * scale
    local h  = 120 * scale
    local cx = vw * 0.5
    local cy = vh * 0.5
    local x  = cx - w * 0.5
    local y  = cy - h * 0.5

    -- Background panel
    draw_rect_filled(
        x, y, w, h,
        30, 30, 40, 230,      -- r,g,b,a
        8.0 * scale,          -- rounding
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT
    )

    -- Outline
    draw_rect(
        x, y, w, h,
        80, 140, 255, 255,    -- r,g,b,a
        2.0 * scale,          -- thickness
        8.0 * scale,          -- rounding
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT
    )

    -- Animated accent bar
    local bar_h = 4 * scale
    draw_rect_filled(
        x, y - bar_h - 2 * scale, w, bar_h,
        120 + (t % 60), 80, 220, 255,
        2.0 * scale,
        RR_TOP_LEFT | RR_TOP_RIGHT
    )

    -- Text
    local title = "Lua Render API"
    local w_text, h_text = get_text_size(font, title, 1000, 1000)

    local tx = cx - w_text * 0.5
    local ty = cy - h_text * 0.5 - 10 * scale

    draw_text(
        title,
        tx, ty,
        255, 255, 255, 255,  -- text color
        font,
        TE_SHADOW,           -- effect
        0, 0, 0, 180,        -- effect color (shadow)
        1.0,                 -- effect amount
    )

    -- Subtitle
    local subtitle = "drawing from Lua 5.4.6"
    local sw, sh = get_text_size(font, subtitle, 1000, 1000)
    local sx = cx - sw * 0.5
    local sy = ty + h_text + 8 * scale

    draw_text(
        subtitle,
        sx, sy,
        180, 200, 255, 255,
        font,
        TE_NONE,
        0, 0, 0, 0,
        0.0
    )
end

function on_unload()
    log("Lua render example unloading.")
end

```

This draws a centered rounded panel and a title text using the Lua Render API.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/render-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/sound-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/sound-api.md).

# Sound API

The Sound API lets Lua scripts load and play audio files with real-time volume and stereo panning control.

Sound files are loaded from relative paths resolved against your script directory (same as the File System API).

**Supported formats:** WAV (PCM 8/16-bit), MP3, AAC, WMA, FLAC — anything Windows Media Foundation can decode.

All audio is resampled to 44100 Hz stereo at load time. Up to 64 sounds can play simultaneously.

***

### Concepts

There are two handle types, both represented as integers:

* **Sound handle** — a loaded audio resource returned by `load_sound`. Can be played multiple times simultaneously. Must be freed with `free_sound` when no longer needed.
* **Instance handle** — a single playing occurrence returned by `play_sound`. Used to stop, query, or adjust an active playback.

Both return `0` on failure. All functions are safe to call with `0` handles (they become no-ops).

***

### Loading & Freeing

**`load_sound(path) -> handle`**

Loads a sound file from a relative path.

* `path` (string) — Relative path to the audio file (e.g. `"sounds/hit.wav"`, `"alert.mp3"`).

Returns a sound handle (integer), or `0` if the file doesn't exist or decoding fails.

***

**`free_sound(handle)`**

Frees a previously loaded sound resource. Any active instances using this sound are stopped automatically.

***

### Playback

**`play_sound(sound [, volume [, pan [, loop]]]) -> instance`**

Plays a loaded sound and returns an instance handle.

* `sound` (integer) — Sound handle from `load_sound`.
* `volume` (number) — `0.0` (silent) to `1.0` (full). Default `1.0`. Clamped.
* `pan` (number) — `-1.0` (full left) to `+1.0` (full right). Default `0.0` (center). Clamped.
* `loop` (boolean) — If `true`, the sound repeats until explicitly stopped. Default `false`.

Returns an instance handle (integer), or `0` if the sound handle is invalid or all 64 instance slots are in use.

***

**`stop_sound(instance)`**

Stops a playing instance immediately.

***

**`stop_all_sounds()`**

Stops every currently playing sound instance.

***

**`is_sound_playing(instance) -> bool`**

Returns `true` if the instance is still actively playing. Returns `false` if it finished, was stopped, or the handle is invalid.

***

### Live Adjustment

These functions modify a playing instance in real time. Changes take effect on the next mixer tick (\~20ms).

**`set_sound_volume(instance, volume)`**

Changes volume of a playing instance. `0.0` to `1.0`, clamped.

***

**`set_sound_pan(instance, pan)`**

Changes stereo panning of a playing instance. `-1.0` (left) to `+1.0` (right), clamped.

***

### Examples

#### Play a one-shot sound effect

```lua
local snd = 0

function main()
    snd = load_sound("pop.mp3")
    if snd == 0 then
        log("Failed to load sound")
        return 0
    end

    play_sound(snd, 0.8, 0.0)
    return 1
end

function on_unload()
    if snd ~= 0 then free_sound(snd) end
end
```

***

#### Looping background music

```lua
local music = 0
local music_inst = 0

function main()
    music = load_sound("ambient.ogg")
    if music ~= 0 then
        music_inst = play_sound(music, 0.5, 0.0, true)
    end
    return 1
end

function on_unload()
    if music_inst ~= 0 then stop_sound(music_inst) end
    if music ~= 0 then free_sound(music) end
end
```

***

#### Directional sound with panning

```lua
local function play_hit(snd, target_x, player_x, max_range)
    local pan = (target_x - player_x) / max_range
    if pan < -1.0 then pan = -1.0 end
    if pan >  1.0 then pan =  1.0 end

    play_sound(snd, 1.0, pan)
end
```

***

#### Fade out over time

```lua
local snd = 0
local inst = 0
local vol = 1.0

function main()
    snd = load_sound("alert.wav")
    if snd == 0 then return 0 end

    inst = play_sound(snd, 1.0, 0.0)
    return 1
end

function on_frame()
    if inst == 0 then return end

    vol = vol - 0.02
    if vol <= 0.0 then
        stop_sound(inst)
        inst = 0
        return
    end

    set_sound_volume(inst, vol)
end

function on_unload()
    if inst ~= 0 then stop_sound(inst) end
    if snd ~= 0 then free_sound(snd) end
end
```

***

#### Multiple simultaneous sounds

```lua
function main()
    local snd = load_sound("hit.wav")
    if snd == 0 then return 0 end

    play_sound(snd, 1.0,  0.0)
    play_sound(snd, 0.7, -0.5)
    play_sound(snd, 0.5,  0.8)

    return 1
end
```

***

### Notes

* Sound data is fully decoded to PCM at load time. Loading is the expensive operation — `play_sound` is cheap.
* Instance handles point into a fixed pool of 64 slots. If all slots are in use, `play_sound` returns `0`.
* Calling `free_sound` automatically stops all instances that reference that sound.
* Sounds are automatically freed when your script is unloaded (leaked handles are cleaned up). You should still free sounds explicitly when possible.
* The `path` parameter follows the same validation rules as the File System API: relative paths only, no `..` segments, no `:` characters.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/sound-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/system-api-cpu-and-disassembly.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/system-api-cpu-and-disassembly.md).

# System API (CPU & Disassembly)

The **System API** provides low-level functionality for CPU information, performance timing, and x64 instruction disassembly using **Zydis**.\
All functions listed here are available globally inside Lua scripts.

***

### 📌 **Available Functions**

#### **CPU Information**

| Function       | Returns  | Description                                             |
| -------------- | -------- | ------------------------------------------------------- |
| `cpu_vendor()` | `string` | CPU vendor (e.g. `"AuthenticAMD"` or `"GenuineIntel"`). |
| `cpu_brand()`  | `string` | Human-readable CPU model string.                        |

***

#### **Timing Functions**

| Function           | Returns  | Description                                                           |
| ------------------ | -------- | --------------------------------------------------------------------- |
| `rdtsc()`          | `uint64` | Raw timestamp counter from the CPU. Fast but CPU-frequency dependent. |
| `perf_time()`      | `int64`  | High-resolution performance counter ticks from Windows.               |
| `perf_frequency()` | `int64`  | Number of performance counter ticks per second.                       |

Useful for accurate microbenchmarking:

```
seconds = (perf_time_end - perf_time_start) / perf_frequency()
```

***

#### **Disassembly (Zydis)**

| Function                                   | Returns                         | Description                                                                    |
| ------------------------------------------ | ------------------------------- | ------------------------------------------------------------------------------ |
| `zydis_disasm(bytes_table, [runtime_rip])` | `table` (array of instructions) | Disassembles multiple x64 instructions and returns detailed structured output. |

***

## **Instruction Structure**

`zydis_disasm` returns an **array of `disasm_instruction_t`**.\
Each instruction contains:

```lua
{
    runtime_address       = 0x140000000,  -- uint64
    length                = 5,            -- bytes
    mnemonic              = "mov",        -- "push", "call", etc.
    text                  = "mov rbp, rsp",  -- full Intel syntax
    operand_count         = 3,            -- total (explicit + hidden)
    operand_count_visible = 2,            -- explicit operands only

    operands = { operand_t, operand_t, ... }
}
```

***

## **Operand Structure**

Each operand is an `operand_t` table with a consistent schema:

```lua
{
    id         = 0,
    visibility = "explicit", -- "explicit" | "implicit" | "hidden"
    type       = "reg",      -- "reg" | "mem" | "imm" | "ptr" | "unused"
    size       = 64,         -- bits

    -- Register operand
    reg = {
        name = "rbp"
    },

    -- Memory operand
    mem = {
        segment          = "ss",
        base             = "rsp",
        index            = nil,
        scale            = 1,
        has_displacement = true,
        displacement     = -0x20,
    },

    -- Immediate operand
    imm = {
        is_signed        = true,
        is_relative      = false,
        value            = 48,
        absolute_address = nil, -- if relative & resolvable
    },

    -- Pointer operand
    ptr = {
        segment = 0x1234,
        offset  = 0xABCDEF,
    }
}
```

***

## 🚀 Usage Examples

### **1. CPU Information**

```lua
function main()
    log("CPU Vendor: " .. cpu_vendor())
    log("CPU Brand : " .. cpu_brand())
end
```

***

### **2. High-Resolution Timing**

```lua
function main()
    local freq = perf_frequency()
    local t0 = perf_time()

    -- workload
    for i = 1, 1000000 do end

    local t1 = perf_time()

    local dt = (t1 - t0) / freq
    log("Elapsed seconds: " .. dt)
end
```

***

### **3. Disassemble Raw Bytes**

You can disassemble any byte array:

```lua
function main()
    local bytes = {
        0x55,                    -- push rbp
        0x48, 0x89, 0xE5,        -- mov rbp, rsp
        0x48, 0x83, 0xEC, 0x30   -- sub rsp, 0x30
    }

    local ins = zydis_disasm(bytes, 0x140000000)

    for i, inst in ipairs(ins) do
        log(string.format("0x%X: %s", inst.runtime_address, inst.text))
    end
end
```

***

### **4. Disassemble Memory From a Process**

Works perfectly with your `proc:rvm()`:

```lua
function main()
    local p = ref_process("notepad.exe")
    if not p then return end

    local base = p:base_address()
    local bytes = p:rvm(base, 32)

    local ins = zydis_disasm(bytes, base)

    for _, inst in ipairs(ins) do
        log(inst.runtime_address .. ": " .. inst.text)
    end

    deref_process(p)
end
```

***

## 🛠 Example Output

```asm
0x140000000: push rbp
  mnemonic = push, length = 1, operands = 1/3
    op1: id=0 type=reg vis=explicit size=64
      reg: rbp
    op2: id=1 type=reg vis=hidden size=64
      reg: rsp
    op3: id=2 type=mem vis=hidden size=64
      mem: seg=ss base=rsp index=nil scale=0 has_disp=false disp=nil

0x140000001: mov rbp, rsp
  mnemonic = mov, length = 3, operands = 2/2

0x140000004: sub rsp, 0x30
  mnemonic = sub, length = 4, operands = 2/3
```

***

## 📅 Date & Time API

#### **`get_datetime()`**

Returns a table describing the **local** date and time.

```lua
local dt = get_datetime()
-- dt = {
--     year        = 2025,
--     month       = 11,
--     day         = 27,
--     hour        = 14,        -- 24h clock
--     minute      = 5,
--     second      = 33,
--     msec        = 120,
--
--     day_name    = "Thursday",
--     month_name  = "November",
--
--     hour12      = 2,         -- 12h clock
--     ampm        = "PM"
-- }
```

#### **`get_timestamp()`**

Returns a **Unix timestamp** (UTC) — seconds since `1970-01-01`.

```lua
local ts = get_timestamp()
-- example: 1732734005
```

#### **Example**

```lua
function main()
    local dt = get_datetime()

    log(string.format(
        "Today is %s, %s %d, %d",
        dt.day_name, dt.month_name, dt.day, dt.year
    ))

    log(string.format(
        "Local Time: %d:%02d %s",
        dt.hour12, dt.minute, dt.ampm
    ))

    local ts = get_timestamp()
    log("Unix Timestamp: " .. ts)
end
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/system-api-cpu-and-disassembly.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/utilities.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/utilities.md).

# Utilities

The `util` module provides fast Base64, Hex, and URL encoding/decoding helpers for Lua scripts.

All functions operate on **raw byte strings**, not UTF-8 text, so they safely support:

* Binary data
* Network packets
* Ciphertext
* Hashes
* Buffers containing `\0` bytes
* Arbitrary byte sequences

The module is registered globally as:

```lua
util = {
    base64_encode = function(str) end,
    base64_decode = function(str) end,
    hex_encode    = function(str) end,
    hex_decode    = function(str) end,
    url_encode    = function(str) end,
    url_decode    = function(str) end,
}
```

***

## Base64 Functions

### `util.base64_encode(str)`

Encodes a raw byte string into Base64 text.

#### Parameters

| Name  | Type   | Description         |
| ----- | ------ | ------------------- |
| `str` | string | Raw bytes to encode |

#### Returns

* Base64 string

#### Example

```lua
local out = util.base64_encode("hello")
print(out)   --> aGVsbG8=
```

***

### `util.base64_decode(str)`

Decodes Base64 text into raw bytes.

#### Parameters

| Name  | Type   | Description |
| ----- | ------ | ----------- |
| `str` | string | Base64 text |

#### Returns

* `string` (raw bytes) on success
* `nil, error_message` on failure

#### Example

```lua
local raw, err = util.base64_decode("aGVsbG8=")
if raw then
    print(raw)   --> hello
else
    print("Decode failed:", err)
end
```

#### Error Example

```lua
local v, err = util.base64_decode("!!!!bad!!!!")
-- v   == nil
-- err == "Invalid base64 character"
```

***

## Hex Functions

### `util.hex_encode(str)`

Encodes bytes into uppercase hexadecimal text.

#### Parameters

| Name  | Type   | Description |
| ----- | ------ | ----------- |
| `str` | string | Raw bytes   |

#### Returns

* Uppercase hex string

#### Example

```lua
local out = util.hex_encode("ABC")
print(out)   --> 414243
```

***

### `util.hex_decode(str)`

Decodes a hex string into raw bytes.

#### Parameters

| Name  | Type   | Description                      |
| ----- | ------ | -------------------------------- |
| `str` | string | Hex text (must have even length) |

#### Returns

* Raw bytes on success
* `nil, error_message` on failure

#### Example

```lua
local raw = util.hex_decode("414243")
print(raw)   --> ABC
```

#### Error Examples

```lua
util.hex_decode("ABC")
-- nil, "Hex string length must be even"

util.hex_decode("GGGG")
-- nil, "Invalid hex character"
```

***

## URL Encode / Decode

Matches standard percent-encoding:

* Safe characters stay as-is: `A–Z a–z 0–9 - _ . ~`
* Everything else becomes `%XX`

`+` is **not** treated as space.\
Binary bytes are preserved.

***

### `util.url_encode(str)`

Encodes text for safe URL usage.

#### Example

```lua
local enc = util.url_encode("hello world! 100% ok?")
print(enc)
-- "hello%20world%21%20100%25%20ok%3F"
```

***

### `util.url_decode(str)`

Decodes `%XX` sequences back into bytes.

#### Example

```lua
local dec = util.url_decode("name=John%20Doe&msg=hi%21")
print(dec)
-- "name=John Doe&msg=hi!"
```

Invalid `%` sequences are returned literally.

***

## Roundtrip Examples

#### Base64 roundtrip

```lua
local original = "hello world"
local enc = util.base64_encode(original)
local dec = util.base64_decode(enc)
assert(dec == original)
```

#### Hex roundtrip

```lua
local original = "hello world"
local hex = util.hex_encode(original)
local raw = util.hex_decode(hex)
assert(raw == original)
```

#### URL roundtrip

```lua
local original = "email=test@example.com&msg=hello!"
local enc = util.url_encode(original)
local dec = util.url_decode(enc)
assert(dec == original)
```

***

## Binary Safety

All `util.*` functions:

* correctly handle `\0` bytes
* accept arbitrary binary input
* never corrupt data
* do not assume UTF-8
* support large buffers

Tested with byte sizes from 1 → 256 without corruption.

***

## Summary

| Function                  | Description                          |
| ------------------------- | ------------------------------------ |
| `util.base64_encode(str)` | Encode bytes → Base64                |
| `util.base64_decode(str)` | Decode Base64 → bytes (or nil+error) |
| `util.hex_encode(str)`    | Encode bytes → uppercase hex         |
| `util.hex_decode(str)`    | Decode hex → bytes (or nil+error)    |
| `util.url_encode(str)`    | Percent-encode unsafe characters     |
| `util.url_decode(str)`    | Decode `%XX` → bytes                 |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/utilities.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/lua/win-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/win-api.md).

# Win API

This API exposes a small subset of the Win32 window, clipboard, keyboard, mouse and messaging functions to Lua:

* Work with windows via **handles** (`hwnd` as integer).
* Inspect window rectangles and sizes.
* Check if a window is foreground or “active”.
* Read / write text to the **clipboard** (UTF-8).
* Look up the **thread & process IDs** for a window.
* Send **messages**, **keys**, and **characters** to a window.
* Send **global keyboard and mouse input** via `SendInput`.

***

### Window Lookup & Info

#### `find_window(title [, class]) -> hwnd | nil`

Search for a top-level window.

* `title` — window title to match (UTF-8 string).
* `class` — optional window class name (UTF-8 string).

If both are provided, both must match.\
Returns `hwnd` (integer) or `nil` if not found.

***

### Window Enumeration

#### `get_all_hwnds()`

Enumerates all top-level windows on the system and returns detailed information about each.

**Returns:** A 1-based Lua array of window info tables.

**Window Info Table Fields:**

| Field          | Type     | Description                             |
| -------------- | -------- | --------------------------------------- |
| `hwnd`         | `int`    | Window handle                           |
| `pid`          | `int`    | Process ID                              |
| `tid`          | `int`    | Thread ID                               |
| `process_name` | `string` | Executable name (e.g., `"notepad.exe"`) |
| `title`        | `string` | Window title text                       |
| `class_name`   | `string` | Window class name                       |

```lua
log("Found " .. #windows .. " windows")

for i, w in ipairs(windows) do
    -- Only show windows with titles
    if w.title ~= "" then
        log(string.format("[%s] %s (PID: %d)", 
            w.process_name, w.title, w.pid))
    end
end

-- Find a specific window by process name
for _, w in ipairs(windows) do
    if w.process_name == "notepad.exe" then
        log("Found Notepad! HWND: " .. w.hwnd)
        set_foreground_window(w.hwnd)
        break
    end
end

return 0
```

***

#### `get_window_size(hwnd) -> width, height | nil, nil`

Get the window’s **outer** size in pixels.

* `hwnd` — window handle (integer).

Returns:

* `width`, `height` (integers), or
* `nil, nil` if the handle is invalid or the call fails.

***

#### `get_window_rect(hwnd) -> x, y, width, height | nil, nil, nil, nil`

Get the window’s full rectangle in screen coordinates.

* `x`, `y` — top-left screen coordinates.
* `width`, `height` — size in pixels.

Returns all `nil` on failure.

***

### Window Focus & Activity

#### `is_foreground_window(hwnd) -> bool`

Checks if `hwnd` is the **current foreground window**.

***

#### `is_window_active(hwnd) -> bool`

Checks if a window is “active” in a broad sense:

* is a valid window,
* is visible,
* is **not minimized**.

Returns `true` or `false`.

***

### Window Text & Class

#### `get_window_title(hwnd) -> string | nil`

Get the window’s title as a UTF-8 string.

* Returns `""` for empty titles.
* Returns `nil` if the handle is invalid.

***

#### `get_window_class(hwnd) -> string | nil`

Get the window’s **class name**.

* Returns `""` if class name can’t be read.
* Returns `nil` if the handle is invalid.

***

#### `set_foreground_window(hwnd) -> bool`

Attempts to bring the given window to the foreground.

Returns `true` on success, `false` otherwise.

***

### Clipboard

All clipboard operations use UTF-8 strings.

#### `copy_to_clipboard(text) -> bool`

Copies a Lua string into the system clipboard.

* `text` — UTF-8 string.
* Returns `true` on success, `false` on failure.

***

#### `copy_from_clipboard() -> string`

Reads UTF-8 text from the system clipboard.

* Returns `""` (empty string) if:
  * clipboard cannot be opened,
  * the clipboard doesn’t contain text, or
  * any error occurs.

***

### Thread / Process Info

#### `get_window_thread_process_id(hwnd) -> thread_id, process_id | nil, nil`

Returns IDs associated with a given window.

* `thread_id` — thread that owns the window.
* `process_id` — process that owns the thread.

If the handle is invalid or the IDs can’t be obtained, returns `nil, nil`.

***

### Messages & Keys

#### `post_message(hwnd, msg, wparam, lparam) -> bool`

Low-level API to post a message to a window.

* `hwnd` — window handle.
* `msg` — message ID (e.g., `0x0010` for `WM_CLOSE`).
* `wparam`, `lparam` — integer parameters.

Returns `true` on success.

***

#### Global key input (`SendInput`)

These functions send **global** keyboard input (not scoped to a specific window). Use when you simply want to simulate key presses.

Virtual keys are integers (e.g. `0x41` for `A`, `0x11` for Ctrl, `0x0D` for Enter).

**`win_key_down(vk)`**

Simulate key down for virtual key `vk`.

&#x20; **`win_key_up(vk)`**

Simulate key up for virtual key `vk`.

**`win_key_press(vk [, delay_ms])`**

Press and release a key, with an optional delay.

* `vk` — virtual key code.
* `delay_ms` — optional delay in milliseconds between down and up (default \~30, clamped to `0..1000`).

***

#### Message-based character & key sending

These functions target a specific window using messages (`WM_CHAR`, `WM_KEYDOWN`, `WM_KEYUP`).

**`send_char(hwnd, text) -> bool`**

Sends a single character via `WM_CHAR`.

* `text` — Lua string; only the **first UTF-16 code unit** is used, which is fine for most BMP characters.

Returns `true` on success.

**`send_key(hwnd, vk) -> bool`**

Sends a key to a specific window using `WM_KEYDOWN` and `WM_KEYUP`.

* `vk` — virtual key code.

Returns `true` if both messages were posted successfully.

***

### Mouse Input

All mouse functions send **global** input via `SendInput`.

Coordinates are in **screen pixels** (primary monitor), unless noted otherwise.

#### `mouse_move(x, y)`

Moves the cursor to absolute screen coordinates.

* `(0,0)` is top-left of the primary display.
* Coordinates are converted to the normalized range expected by `SendInput`.

***

#### `mouse_move_relative(dx, dy)`

Moves the cursor relative to its current position.

* `dx` — horizontal delta (pixels).
* `dy` — vertical delta (pixels).

***

#### `mouse_left_click()`

Performs a left button click at the current cursor position.

#### `mouse_right_click()`

Performs a right button click.

#### `mouse_middle_click()`

Performs a middle button click.

Each click sends a down event, waits \~10 ms, then sends an up event.

***

#### `send_mouse_input(dx, dy, flags, mouse_data)`

Send input manually via raw input.

***

#### `mouse_scroll(amount)`

Scrolls the mouse wheel vertically.

* `amount` is in “notches”:
  * positive → scroll **up**
  * negative → scroll **down**

Example: `mouse_scroll(3)` scrolls up 3 notches.

***

## **Util**

`get_tickcount64()`

* GetTickCount64()

***

### Usage Examples

#### Find a window and print info

```lua
local title   = "Untitled - Notepad"
local hwnd    = find_window(title)

if not hwnd then
  print("Window not found:", title)
  return
end

print("HWND:", string.format("0x%X", hwnd))

local x, y, w, h = get_window_rect(hwnd)
print("Rect:", x, y, w, h)

local winTitle = get_window_title(hwnd) or "<nil>"
local winClass = get_window_class(hwnd) or "<nil>"
print("Title:", winTitle)
print("Class:", winClass)

local tid, pid = get_window_thread_process_id(hwnd)
print("Thread ID:", tid, "Process ID:", pid)
```

***

#### Clipboard

```lua
copy_to_clipboard("Hello from Lua! こんにちは 🌸")

local txt = copy_from_clipboard()
print("Clipboard:", txt)
```

***

#### Global keystrokes

```lua
-- Type 'HELLO'
local letters = { 0x48, 0x45, 0x4C, 0x4C, 0x4F } -- H E L L O
for _, vk in ipairs(letters) do
  win_key_press(vk, 40)
end

-- Ctrl+V
local VK_CONTROL = 0x11
local VK_V       = 0x56

win_key_down(VK_CONTROL)
win_key_press(VK_V, 30)
win_key_up(VK_CONTROL)
```

***

#### Message-based typing into a window

```lua
local hwnd = find_window("Untitled - Notepad")
if not hwnd then return end

-- make sure Notepad has focus (if you expose set_foreground_window)
set_foreground_window(hwnd)

send_char(hwnd, "H")
send_char(hwnd, "i")
send_char(hwnd, " ")
send_char(hwnd, "🌸")

local VK_RETURN = 0x0D
send_key(hwnd, VK_RETURN)
```

***

#### Mouse movement & clicks

```lua
-- Move to near top-left, left-click
mouse_move(100, 100)
mouse_left_click()

-- Move a bit to the right and right-click
mouse_move_relative(80, 0)
mouse_right_click()

-- Move down and middle-click
mouse_move_relative(0, 60)
mouse_middle_click()

-- Scroll up then down
mouse_scroll(3)
mouse_scroll(-3)
```

## Full API Test

<pre class="language-lua"><code class="lang-lua"><strong>local TARGET_TITLE = "Untitled - Notepad"  -- change to your target window
</strong>
local function has_global(name)
    return _G[name] ~= nil
end

local function get_target_hwnd()
    if not has_global("find_window") then
        log("ERROR: find_window is not available.")
        return nil
    end

    local hwnd = find_window(TARGET_TITLE)
    if not hwnd then
        log("Window not found:", TARGET_TITLE)
        return nil
    end

    log("Found hwnd:", string.format("0x%X", hwnd))

    if has_global("set_foreground_window") then
        local ok = set_foreground_window(hwnd)
        log("set_foreground_window:", ok)
    else
        log("set_foreground_window not available, skipping.")
    end

    return hwnd
end

local function test_mouse_basic()
    log("=== TEST: mouse movement &#x26; clicks ===")
    log("Move your eyes to where the cursor goes. :)")

    -- Move to approximate top-left of the primary screen
    mouse_move(100, 100)
    mouse_left_click()
    log("  mouse_move(100,100) + left click")

    -- Move a bit to the right and right-click
    mouse_move_relative(80, 0)
    mouse_right_click()
    log("  mouse_move_relative(80,0) + right click")

    -- Move a bit down and middle-click
    mouse_move_relative(0, 60)
    mouse_middle_click()
    log("  mouse_move_relative(0,60) + middle click")

    -- Scroll up then down a bit
    mouse_scroll(3)   -- up 3 notches
    mouse_scroll(-3)  -- down 3 notches
    log("  mouse_scroll(3) then mouse_scroll(-3)")
end

local function test_send_char_key(hwnd)
    if not hwnd then
        log("No hwnd, skipping send_char/send_key test.")
        return
    end

    if not has_global("send_char") or not has_global("send_key") then
        log("send_char / send_key not available, skipping.")
        return
    end

    log("=== TEST: send_char / send_key ===")
    log("Make sure the target window has a focused text field.")

    -- Send "Hi " + emoji via WM_CHAR
    send_char(hwnd, "H")
    send_char(hwnd, "i")
    send_char(hwnd, " ")
    send_char(hwnd, "🌸") -- only 

    -- Press Enter via WM_KEYDOWN/UP
    local VK_RETURN = 0x0D
    local ok = send_key(hwnd, VK_RETURN)
    log("send_key(VK_RETURN) ->", ok)
end

function main()
    log("Target window title:", TARGET_TITLE)

    local hwnd = get_target_hwnd()

    test_mouse_basic()
    test_send_char_key(hwnd)

    log("=== winapi_input_test.lua done ===")
    return 1;
end
</code></pre>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/win-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/lua-lang/INDEX.md`

<!-- Source: https://www.lua.org/manual/5.4/ (index generated from the official Lua 5.4 manual pages)
     Fetched: 2026-06-20
     License: Lua is distributed under the terms of the Lua license (an MIT-style license; see license.md).
     Reproduced under that license with attribution to Lua.org, PUC-Rio.
     This is the core Lua 5.4 reference, scraped from the official manual.
     Do not edit manually — re-fetch from the source above to update. -->

# Lua 5.4 Language Reference

This directory contains the authoritative core **Lua 5.4 language reference**, scraped from the official Lua manual at https://www.lua.org/manual/5.4/. It documents the Lua language itself — its lexical conventions, syntax, semantics, standard libraries, C API, auxiliary library, standalone interpreter, incompatibilities with the previous version, and the complete syntax in extended BNF. This is **not** the PCX Lua API bindings; the Perception.cx platform API exposed to Lua is documented separately under docs/perception/lua/. The content here is reproduced under the Lua license (an MIT-style license; see license.md), with attribution to Lua.org, PUC-Rio.

| File | Source | Topic |
| --- | --- | --- |
| manual-5.4.md | https://www.lua.org/manual/5.4/manual.html | Full Lua 5.4 reference manual — sections 1–9: Introduction, Basic Concepts, The Language, The C API, The Auxiliary Library, The Standard Libraries, Lua Standalone, Incompatibilities with the Previous Version, The Complete Syntax |
| readme-5.4.md | https://www.lua.org/manual/5.4/readme.html | Lua 5.4 release notes / readme — about, installation, changes since Lua 5.3, license |
| license.md | https://www.lua.org/license.html | The Lua license text (MIT-style) for attribution |
| INDEX.md | (this file) | Directory index and provenance |

> **Note:** This is **Lua 5.4** specifically — not 5.3 or 5.5. The PCX Lua API bindings (the Perception.cx platform API exposed to Lua scripts) live in a separate location: docs/perception/lua/. The files in this directory are verbatim reference material for the core language and should not be edited by hand; re-fetch from the source URLs above to update.

---

## Source: `docs/lua-lang/license.md`

<!-- Source: https://www.lua.org/manual/5.4/license.html
     Fetched: 2026-06-20
     License: Lua is distributed under the terms of the Lua license (an MIT-style license; see license.md).
     Reproduced under that license with attribution to Lua.org, PUC-Rio.
     This is the core Lua 5.4 reference, scraped from the official manual.
     Do not edit manually — re-fetch from the source above to update. -->

# License

Lua is free software distributed under the terms of the [MIT license](https://opensource.org/license/mit/) reproduced here. Lua may be used for any purpose, including commercial purposes, at absolutely no cost. No paperwork, no royalties, no GNU-like "copyleft" restrictions, either. Just [download](https://www.lua.org/download.html) it and use it.

Lua is certified [Open Source](https://opensource.org/osd/) software. Its license is simple and liberal and is [compatible with GPL](https://www.gnu.org/licenses/license-list.html#GPLCompatibleLicenses). Lua is not in the public domain and [PUC-Rio](https://www.puc-rio.br/) keeps its copyright.

The spirit of the Lua license is that you are free to use Lua for any purpose at no cost without having to ask us. The only requirement is that if you do use Lua, then you should give us credit by including the copyright notice somewhere in your product or its documentation. A nice, but optional, way to give us further credit is to include a [Lua logo](https://www.lua.org/images/) and a [link to our site](https://www.lua.org/) in a web page for your product.

The Lua language is entirely designed, implemented, and maintained by a [team](https://www.lua.org/authors.html) at [PUC-Rio](https://www.puc-rio.br/) in Brazil. The implementation is not derived from licensed software.

Before Lua 5.0, Lua used its own license, which was very close to the [zlib license](https://opensource.org/license/zlib/) and others, but not quite the same. Check the [source distribution](https://www.lua.org/ftp/) for the exact license text for each version before Lua 5.0. Nevertheless, if you wish to use those old versions, you may hereby assume that they have all been re-licensed under the MIT license as described above.

Copyright © 1994–2025 Lua.org, PUC-Rio.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Source: `docs/lua-lang/manual-5.4.md`

<!-- Source: https://www.lua.org/manual/5.4/manual.html
     Fetched: 2026-06-20
     License: Lua is distributed under the terms of the Lua license (an MIT-style license; see license.md).
     Reproduced under that license with attribution to Lua.org, PUC-Rio.
     This is the core Lua 5.4 reference, scraped from the official manual.
     Do not edit manually — re-fetch from the source above to update. -->

# Lua 5.4 Reference Manual

by Roberto Ierusalimschy, Luiz Henrique de Figueiredo, Waldemar Celes

Copyright © 2020–2025 Lua.org, PUC-Rio. Freely available under the terms of the [Lua license](https://www.lua.org/license.html).

# 1 – Introduction

Lua is a powerful, efficient, lightweight, embeddable scripting language. It supports procedural programming, object-oriented programming, functional programming, data-driven programming, and data description.

Lua combines simple procedural syntax with powerful data description constructs based on associative arrays and extensible semantics. Lua is dynamically typed, runs by interpreting bytecode with a register-based virtual machine, and has automatic memory management with a generational garbage collection, making it ideal for configuration, scripting, and rapid prototyping.

Lua is implemented as a library, written in *clean C*, the common subset of standard C and C++. The Lua distribution includes a host program called `lua`, which uses the Lua library to offer a complete, standalone Lua interpreter, for interactive or batch use. Lua is intended to be used both as a powerful, lightweight, embeddable scripting language for any program that needs one, and as a powerful but lightweight and efficient stand-alone language.

As an extension language, Lua has no notion of a "main" program: it works *embedded* in a host client, called the *embedding program* or simply the *host*. (Frequently, this host is the stand-alone `lua` program.) The host program can invoke functions to execute a piece of Lua code, can write and read Lua variables, and can register C functions to be called by Lua code. Through the use of C functions, Lua can be augmented to cope with a wide range of different domains, thus creating customized programming languages sharing a syntactical framework.

Lua is free software, and is provided as usual with no guarantees, as stated in its license. The implementation described in this manual is available at Lua's official web site, `www.lua.org`.

Like any other reference manual, this document is dry in places. For a discussion of the decisions behind the design of Lua, see the technical papers available at Lua's web site. For a detailed introduction to programming in Lua, see Roberto's book, *Programming in Lua*.

# 2 – Basic Concepts

This section describes the basic concepts of the language.

## 2.1 – Values and Types

Lua is a dynamically typed language. This means that variables do not have types; only values do. There are no type definitions in the language. All values carry their own type.

All values in Lua are first-class values. This means that all values can be stored in variables, passed as arguments to other functions, and returned as results.

There are eight basic types in Lua: *nil*, *boolean*, *number*, *string*, *function*, *userdata*, *thread*, and *table*. The type *nil* has one single value, **nil**, whose main property is to be different from any other value; it often represents the absence of a useful value. The type *boolean* has two values, **false** and **true**. Both **nil** and **false** make a condition false; they are collectively called *false values*. Any other value makes a condition true. Despite its name, **false** is frequently used as an alternative to **nil**, with the key difference that **false** behaves like a regular value in a table, while a **nil** in a table represents an absent key.

The type *number* represents both integer numbers and real (floating-point) numbers, using two subtypes: *integer* and *float*. Standard Lua uses 64-bit integers and double-precision (64-bit) floats, but you can also compile Lua so that it uses 32-bit integers and/or single-precision (32-bit) floats. The option with 32 bits for both integers and floats is particularly attractive for small machines and embedded systems. (See macro `LUA_32BITS` in file `luaconf.h`.)

Unless stated otherwise, any overflow when manipulating integer values *wrap around*, according to the usual rules of two-complement arithmetic. (In other words, the actual result is the unique representable integer that is equal modulo *2^n* to the mathematical result, where *n* is the number of bits of the integer type.)

Lua has explicit rules about when each subtype is used, but it also converts between them automatically as needed (see [§3.4.3](#3.4.3)). Therefore, the programmer may choose to mostly ignore the difference between integers and floats or to assume complete control over the representation of each number.

The type *string* represents immutable sequences of bytes. Lua is 8-bit clean: strings can contain any 8-bit value, including embedded zeros ('`\0`'). Lua is also encoding-agnostic; it makes no assumptions about the contents of a string. The length of any string in Lua must fit in a Lua integer.

Lua can call (and manipulate) functions written in Lua and functions written in C (see [§3.4.10](#3.4.10)). Both are represented by the type *function*.

The type *userdata* is provided to allow arbitrary C data to be stored in Lua variables. A userdata value represents a block of raw memory. There are two kinds of userdata: *full userdata*, which is an object with a block of memory managed by Lua, and *light userdata*, which is simply a C pointer value. Userdata has no predefined operations in Lua, except assignment and identity test. By using *metatables*, the programmer can define operations for full userdata values (see [§2.4](#2.4)). Userdata values cannot be created or modified in Lua, only through the C API. This guarantees the integrity of data owned by the host program and C libraries.

The type *thread* represents independent threads of execution and it is used to implement coroutines (see [§2.6](#2.6)). Lua threads are not related to operating-system threads. Lua supports coroutines on all systems, even those that do not support threads natively.

The type *table* implements associative arrays, that is, arrays that can have as indices not only numbers, but any Lua value except **nil** and NaN. (*Not a Number* is a special floating-point value used by the IEEE 754 standard to represent undefined numerical results, such as `0/0`.) Tables can be *heterogeneous*; that is, they can contain values of all types (except **nil**). Any key associated to the value **nil** is not considered part of the table. Conversely, any key that is not part of a table has an associated value **nil**.

Tables are the sole data-structuring mechanism in Lua; they can be used to represent ordinary arrays, lists, symbol tables, sets, records, graphs, trees, etc. To represent records, Lua uses the field name as an index. The language supports this representation by providing `a.name` as syntactic sugar for `a["name"]`. There are several convenient ways to create tables in Lua (see [§3.4.9](#3.4.9)).

Like indices, the values of table fields can be of any type. In particular, because functions are first-class values, table fields can contain functions. Thus tables can also carry *methods* (see [§3.4.11](#3.4.11)).

The indexing of tables follows the definition of raw equality in the language. The expressions `a[i]` and `a[j]` denote the same table element if and only if `i` and `j` are raw equal (that is, equal without metamethods). In particular, floats with integral values are equal to their respective integers (e.g., `1.0 == 1`). To avoid ambiguities, any float used as a key that is equal to an integer is converted to that integer. For instance, if you write `a[2.0] = true`, the actual key inserted into the table will be the integer `2`.

Tables, functions, threads, and (full) userdata values are *objects*: variables do not actually *contain* these values, only *references* to them. Assignment, parameter passing, and function returns always manipulate references to such values; these operations do not imply any kind of copy.

The library function [`type`](#pdf-type) returns a string describing the type of a given value (see [`type`](#pdf-type)).

## 2.2 – Environments and the Global Environment

As we will discuss further in [§3.2](#3.2) and [§3.3.3](#3.3.3), any reference to a free name (that is, a name not bound to any declaration) `var` is syntactically translated to `_ENV.var`. Moreover, every chunk is compiled in the scope of an external local variable named `_ENV` (see [§3.3.2](#3.3.2)), so `_ENV` itself is never a free name in a chunk.

Despite the existence of this external `_ENV` variable and the translation of free names, `_ENV` is a completely regular name. In particular, you can define new variables and parameters with that name. Each reference to a free name uses the `_ENV` that is visible at that point in the program, following the usual visibility rules of Lua (see [§3.5](#3.5)).

Any table used as the value of `_ENV` is called an *environment*.

Lua keeps a distinguished environment called the *global environment*. This value is kept at a special index in the C registry (see [§4.3](#4.3)). In Lua, the global variable [`_G`](#pdf-_G) is initialized with this same value. ([`_G`](#pdf-_G) is never used internally, so changing its value will affect only your own code.)

When Lua loads a chunk, the default value for its `_ENV` variable is the global environment (see [`load`](#pdf-load)). Therefore, by default, free names in Lua code refer to entries in the global environment and, therefore, they are also called *global variables*. Moreover, all standard libraries are loaded in the global environment and some functions there operate on that environment. You can use [`load`](#pdf-load) (or [`loadfile`](#pdf-loadfile)) to load a chunk with a different environment. (In C, you have to load the chunk and then change the value of its first upvalue; see [`lua_setupvalue`](#lua_setupvalue).)

## 2.3 – Error Handling

Several operations in Lua can *raise* an error. An error interrupts the normal flow of the program, which can continue by *catching* the error.

Lua code can explicitly raise an error by calling the [`error`](#pdf-error) function. (This function never returns.)

To catch errors in Lua, you can do a *protected call*, using [`pcall`](#pdf-pcall) (or [`xpcall`](#pdf-xpcall)). The function [`pcall`](#pdf-pcall) calls a given function in *protected mode*. Any error while running the function stops its execution, and control returns immediately to `pcall`, which returns a status code.

Because Lua is an embedded extension language, Lua code starts running by a call from C code in the host program. (When you use Lua standalone, the `lua` application is the host program.) Usually, this call is protected; so, when an otherwise unprotected error occurs during the compilation or execution of a Lua chunk, control returns to the host, which can take appropriate measures, such as printing an error message.

Whenever there is an error, an *error object* is propagated with information about the error. Lua itself only generates errors whose error object is a string, but programs can generate errors with any value as the error object. It is up to the Lua program or its host to handle such error objects. For historical reasons, an error object is often called an *error message*, even though it does not have to be a string.

When you use [`xpcall`](#pdf-xpcall) (or [`lua_pcall`](#lua_pcall), in C) you can give a *message handler* to be called in case of errors. This function is called with the original error object and returns a new error object. It is called before the error unwinds the stack, so that it can gather more information about the error, for instance by inspecting the stack and creating a stack traceback. This message handler is still protected by the protected call; so, an error inside the message handler will call the message handler again. If this loop goes on for too long, Lua breaks it and returns an appropriate message. The message handler is called only for regular runtime errors. It is not called for memory-allocation errors nor for errors while running finalizers or other message handlers.

Lua also offers a system of *warnings* (see [`warn`](#pdf-warn)). Unlike errors, warnings do not interfere in any way with program execution. They typically only generate a message to the user, although this behavior can be adapted from C (see [`lua_setwarnf`](#lua_setwarnf)).

## 2.4 – Metatables and Metamethods

Every value in Lua can have a *metatable*. This *metatable* is an ordinary Lua table that defines the behavior of the original value under certain events. You can change several aspects of the behavior of a value by setting specific fields in its metatable. For instance, when a non-numeric value is the operand of an addition, Lua checks for a function in the field `__add` of the value's metatable. If it finds one, Lua calls this function to perform the addition.

The key for each event in a metatable is a string with the event name prefixed by two underscores; the corresponding value is called a *metavalue*. For most events, the metavalue must be a function, which is then called a *metamethod*. In the previous example, the key is the string "`__add`" and the metamethod is the function that performs the addition. Unless stated otherwise, a metamethod can in fact be any callable value, which is either a function or a value with a `__call` metamethod.

You can query the metatable of any value using the [`getmetatable`](#pdf-getmetatable) function. Lua queries metamethods in metatables using a raw access (see [`rawget`](#pdf-rawget)).

You can replace the metatable of tables using the [`setmetatable`](#pdf-setmetatable) function. You cannot change the metatable of other types from Lua code, except by using the debug library ([§6.10](#6.10)).

Tables and full userdata have individual metatables, although multiple tables and userdata can share their metatables. Values of all other types share one single metatable per type; that is, there is one single metatable for all numbers, one for all strings, etc. By default, a value has no metatable, but the string library sets a metatable for the string type (see [§6.4](#6.4)).

A detailed list of operations controlled by metatables is given next. Each event is identified by its corresponding key. By convention, all metatable keys used by Lua are composed by two underscores followed by lowercase Latin letters.

- **`__add`: ** the addition (`+`) operation. If any operand for an addition is not a number, Lua will try to call a metamethod. It starts by checking the first operand (even if it is a number); if that operand does not define a metamethod for `__add`, then Lua will check the second operand. If Lua can find a metamethod, it calls the metamethod with the two operands as arguments, and the result of the call (adjusted to one value) is the result of the operation. Otherwise, if no metamethod is found, Lua raises an error.

- **`__sub`: ** the subtraction (`-`) operation. Behavior similar to the addition operation.

- **`__mul`: ** the multiplication (`*`) operation. Behavior similar to the addition operation.

- **`__div`: ** the division (`/`) operation. Behavior similar to the addition operation.

- **`__mod`: ** the modulo (`%`) operation. Behavior similar to the addition operation.

- **`__pow`: ** the exponentiation (`^`) operation. Behavior similar to the addition operation.

- **`__unm`: ** the negation (unary `-`) operation. Behavior similar to the addition operation.

- **`__idiv`: ** the floor division (`//`) operation. Behavior similar to the addition operation.

- **`__band`: ** the bitwise AND (`&`) operation. Behavior similar to the addition operation, except that Lua will try a metamethod if any operand is neither an integer nor a float coercible to an integer (see [§3.4.3](#3.4.3)).

- **`__bor`: ** the bitwise OR (`|`) operation. Behavior similar to the bitwise AND operation.

- **`__bxor`: ** the bitwise exclusive OR (binary `~`) operation. Behavior similar to the bitwise AND operation.

- **`__bnot`: ** the bitwise NOT (unary `~`) operation. Behavior similar to the bitwise AND operation.

- **`__shl`: ** the bitwise left shift (`<<`) operation. Behavior similar to the bitwise AND operation.

- **`__shr`: ** the bitwise right shift (`>>`) operation. Behavior similar to the bitwise AND operation.

- **`__concat`: ** the concatenation (`..`) operation. Behavior similar to the addition operation, except that Lua will try a metamethod if any operand is neither a string nor a number (which is always coercible to a string).

- **`__len`: ** the length (`#`) operation. If the object is not a string, Lua will try its metamethod. If there is a metamethod, Lua calls it with the object as argument, and the result of the call (always adjusted to one value) is the result of the operation. If there is no metamethod but the object is a table, then Lua uses the table length operation (see [§3.4.7](#3.4.7)). Otherwise, Lua raises an error.

- **`__eq`: ** the equal (`==`) operation. Behavior similar to the addition operation, except that Lua will try a metamethod only when the values being compared are either both tables or both full userdata and they are not primitively equal. The result of the call is always converted to a boolean.

- **`__lt`: ** the less than (`<`) operation. Behavior similar to the addition operation, except that Lua will try a metamethod only when the values being compared are neither both numbers nor both strings. Moreover, the result of the call is always converted to a boolean.

- **`__le`: ** the less equal (`<=`) operation. Behavior similar to the less than operation.

- **`__index`: ** The indexing access operation `table[key]`. This event happens when `table` is not a table or when `key` is not present in `table`. The metavalue is looked up in the metatable of `table`.

  The metavalue for this event can be either a function, a table, or any value with an `__index` metavalue. If it is a function, it is called with `table` and `key` as arguments, and the result of the call (adjusted to one value) is the result of the operation. Otherwise, the final result is the result of indexing this metavalue with `key`. This indexing is regular, not raw, and therefore can trigger another `__index` metavalue.

- **`__newindex`: ** The indexing assignment `table[key] = value`. Like the index event, this event happens when `table` is not a table or when `key` is not present in `table`. The metavalue is looked up in the metatable of `table`.

  Like with indexing, the metavalue for this event can be either a function, a table, or any value with an `__newindex` metavalue. If it is a function, it is called with `table`, `key`, and `value` as arguments. Otherwise, Lua repeats the indexing assignment over this metavalue with the same key and value. This assignment is regular, not raw, and therefore can trigger another `__newindex` metavalue.

  Whenever a `__newindex` metavalue is invoked, Lua does not perform the primitive assignment. If needed, the metamethod itself can call [`rawset`](#pdf-rawset) to do the assignment.

- **`__call`: ** The call operation `func(args)`. This event happens when Lua tries to call a non-function value (that is, `func` is not a function). The metamethod is looked up in `func`. If present, the metamethod is called with `func` as its first argument, followed by the arguments of the original call (`args`). All results of the call are the results of the operation. This is the only metamethod that allows multiple results.

In addition to the previous list, the interpreter also respects the following keys in metatables: `__gc` (see [§2.5.3](#2.5.3)), `__close` (see [§3.3.8](#3.3.8)), `__mode` (see [§2.5.4](#2.5.4)), and `__name`. (The entry `__name`, when it contains a string, may be used by [`tostring`](#pdf-tostring) and in error messages.)

For the unary operators (negation, length, and bitwise NOT), the metamethod is computed and called with a dummy second operand, equal to the first one. This extra operand is only to simplify Lua's internals (by making these operators behave like a binary operation) and may be removed in future versions. For most uses this extra operand is irrelevant.

Because metatables are regular tables, they can contain arbitrary fields, not only the event names defined above. Some functions in the standard library (e.g., [`tostring`](#pdf-tostring)) use other fields in metatables for their own purposes.

It is a good practice to add all needed metamethods to a table before setting it as a metatable of some object. In particular, the `__gc` metamethod works only when this order is followed (see [§2.5.3](#2.5.3)). It is also a good practice to set the metatable of an object right after its creation.

## 2.5 – Garbage Collection

Lua performs automatic memory management. This means that you do not have to worry about allocating memory for new objects or freeing it when the objects are no longer needed. Lua manages memory automatically by running a *garbage collector* to collect all *dead* objects. All memory used by Lua is subject to automatic management: strings, tables, userdata, functions, threads, internal structures, etc.

An object is considered *dead* as soon as the collector can be sure the object will not be accessed again in the normal execution of the program. ("Normal execution" here excludes finalizers, which can resurrect dead objects (see [§2.5.3](#2.5.3)), and excludes also operations using the debug library.) Note that the time when the collector can be sure that an object is dead may not coincide with the programmer's expectations. The only guarantees are that Lua will not collect an object that may still be accessed in the normal execution of the program, and it will eventually collect an object that is inaccessible from Lua. (Here, *inaccessible from Lua* means that neither a variable nor another live object refer to the object.) Because Lua has no knowledge about C code, it never collects objects accessible through the registry (see [§4.3](#4.3)), which includes the global environment (see [§2.2](#2.2)).

The garbage collector (GC) in Lua can work in two modes: incremental and generational.

The default GC mode with the default parameters are adequate for most uses. However, programs that waste a large proportion of their time allocating and freeing memory can benefit from other settings. Keep in mind that the GC behavior is non-portable both across platforms and across different Lua releases; therefore, optimal settings are also non-portable.

You can change the GC mode and parameters by calling [`lua_gc`](#lua_gc) in C or [`collectgarbage`](#pdf-collectgarbage) in Lua. You can also use these functions to control the collector directly (e.g., to stop and restart it).

### 2.5.1 – Incremental Garbage Collection

In incremental mode, each GC cycle performs a mark-and-sweep collection in small steps interleaved with the program's execution. In this mode, the collector uses three numbers to control its garbage-collection cycles: the *garbage-collector pause*, the *garbage-collector step multiplier*, and the *garbage-collector step size*.

The garbage-collector pause controls how long the collector waits before starting a new cycle. The collector starts a new cycle when the use of memory hits *n%* of the use after the previous collection. Larger values make the collector less aggressive. Values equal to or less than 100 mean the collector will not wait to start a new cycle. A value of 200 means that the collector waits for the total memory in use to double before starting a new cycle. The default value is 200; the maximum value is 1000.

The garbage-collector step multiplier controls the speed of the collector relative to memory allocation, that is, how many elements it marks or sweeps for each kilobyte of memory allocated. Larger values make the collector more aggressive but also increase the size of each incremental step. You should not use values less than 100, because they make the collector too slow and can result in the collector never finishing a cycle. The default value is 100; the maximum value is 1000.

The garbage-collector step size controls the size of each incremental step, specifically how many bytes the interpreter allocates before performing a step. This parameter is logarithmic: A value of *n* means the interpreter will allocate *2^n* bytes between steps and perform equivalent work during the step. A large value (e.g., 60) makes the collector a stop-the-world (non-incremental) collector. The default value is 13, which means steps of approximately 8 Kbytes.

### 2.5.2 – Generational Garbage Collection

In generational mode, the collector does frequent *minor* collections, which traverses only objects recently created. If after a minor collection the use of memory is still above a limit, the collector does a stop-the-world *major* collection, which traverses all objects. The generational mode uses two parameters: the *minor multiplier* and the *the major multiplier*.

The minor multiplier controls the frequency of minor collections. For a minor multiplier *x*, a new minor collection will be done when memory grows *x%* larger than the memory in use after the previous major collection. For instance, for a multiplier of 20, the collector will do a minor collection when the use of memory gets 20% larger than the use after the previous major collection. The default value is 20; the maximum value is 200.

The major multiplier controls the frequency of major collections. For a major multiplier *x*, a new major collection will be done when memory grows *x%* larger than the memory in use after the previous major collection. For instance, for a multiplier of 100, the collector will do a major collection when the use of memory gets larger than twice the use after the previous collection. The default value is 100; the maximum value is 1000.

### 2.5.3 – Garbage-Collection Metamethods

You can set garbage-collector metamethods for tables and, using the C API, for full userdata (see [§2.4](#2.4)). These metamethods, called *finalizers*, are called when the garbage collector detects that the corresponding table or userdata is dead. Finalizers allow you to coordinate Lua's garbage collection with external resource management such as closing files, network or database connections, or freeing your own memory.

For an object (table or userdata) to be finalized when collected, you must *mark* it for finalization. You mark an object for finalization when you set its metatable and the metatable has a `__gc` metamethod. Note that if you set a metatable without a `__gc` field and later create that field in the metatable, the object will not be marked for finalization.

When a marked object becomes dead, it is not collected immediately by the garbage collector. Instead, Lua puts it in a list. After the collection, Lua goes through that list. For each object in the list, it checks the object's `__gc` metamethod: If it is present, Lua calls it with the object as its single argument.

At the end of each garbage-collection cycle, the finalizers are called in the reverse order that the objects were marked for finalization, among those collected in that cycle; that is, the first finalizer to be called is the one associated with the object marked last in the program. The execution of each finalizer may occur at any point during the execution of the regular code.

Because the object being collected must still be used by the finalizer, that object (and other objects accessible only through it) must be *resurrected* by Lua. Usually, this resurrection is transient, and the object memory is freed in the next garbage-collection cycle. However, if the finalizer stores the object in some global place (e.g., a global variable), then the resurrection is permanent. Moreover, if the finalizer marks a finalizing object for finalization again, its finalizer will be called again in the next cycle where the object is dead. In any case, the object memory is freed only in a GC cycle where the object is dead and not marked for finalization.

When you close a state (see [`lua_close`](#lua_close)), Lua calls the finalizers of all objects marked for finalization, following the reverse order that they were marked. If any finalizer marks objects for collection during that phase, these marks have no effect.

Finalizers cannot yield nor run the garbage collector. Because they can run in unpredictable times, it is good practice to restrict each finalizer to the minimum necessary to properly release its associated resource.

Any error while running a finalizer generates a warning; the error is not propagated.

### 2.5.4 – Weak Tables

A *weak table* is a table whose elements are *weak references*. A weak reference is ignored by the garbage collector. In other words, if the only references to an object are weak references, then the garbage collector will collect that object.

A weak table can have weak keys, weak values, or both. A table with weak values allows the collection of its values, but prevents the collection of its keys. A table with both weak keys and weak values allows the collection of both keys and values. In any case, if either the key or the value is collected, the whole pair is removed from the table. The weakness of a table is controlled by the `__mode` field of its metatable. This metavalue, if present, must be one of the following strings: "`k`", for a table with weak keys; "`v`", for a table with weak values; or "`kv`", for a table with both weak keys and values.

A table with weak keys and strong values is also called an *ephemeron table*. In an ephemeron table, a value is considered reachable only if its key is reachable. In particular, if the only reference to a key comes through its value, the pair is removed.

Any change in the weakness of a table may take effect only at the next collect cycle. In particular, if you change the weakness to a stronger mode, Lua may still collect some items from that table before the change takes effect.

Only objects that have an explicit construction are removed from weak tables. Values, such as numbers and light C functions, are not subject to garbage collection, and therefore are not removed from weak tables (unless their associated values are collected). Although strings are subject to garbage collection, they do not have an explicit construction and their equality is by value; they behave more like values than like objects. Therefore, they are not removed from weak tables.

Resurrected objects (that is, objects being finalized and objects accessible only through objects being finalized) have a special behavior in weak tables. They are removed from weak values before running their finalizers, but are removed from weak keys only in the next collection after running their finalizers, when such objects are actually freed. This behavior allows the finalizer to access properties associated with the object through weak tables.

If a weak table is among the resurrected objects in a collection cycle, it may not be properly cleared until the next cycle.

## 2.6 – Coroutines

Lua supports coroutines, also called *collaborative multithreading*. A coroutine in Lua represents an independent thread of execution. Unlike threads in multithread systems, however, a coroutine only suspends its execution by explicitly calling a yield function.

You create a coroutine by calling [`coroutine.create`](#pdf-coroutine.create). Its sole argument is a function that is the main function of the coroutine. The `create` function only creates a new coroutine and returns a handle to it (an object of type *thread*); it does not start the coroutine.

You execute a coroutine by calling [`coroutine.resume`](#pdf-coroutine.resume). When you first call [`coroutine.resume`](#pdf-coroutine.resume), passing as its first argument a thread returned by [`coroutine.create`](#pdf-coroutine.create), the coroutine starts its execution by calling its main function. Extra arguments passed to [`coroutine.resume`](#pdf-coroutine.resume) are passed as arguments to that function. After the coroutine starts running, it runs until it terminates or *yields*.

A coroutine can terminate its execution in two ways: normally, when its main function returns (explicitly or implicitly, after the last instruction); and abnormally, if there is an unprotected error. In case of normal termination, [`coroutine.resume`](#pdf-coroutine.resume) returns **true**, plus any values returned by the coroutine main function. In case of errors, [`coroutine.resume`](#pdf-coroutine.resume) returns **false** plus the error object. In this case, the coroutine does not unwind its stack, so that it is possible to inspect it after the error with the debug API.

A coroutine yields by calling [`coroutine.yield`](#pdf-coroutine.yield). When a coroutine yields, the corresponding [`coroutine.resume`](#pdf-coroutine.resume) returns immediately, even if the yield happens inside nested function calls (that is, not in the main function, but in a function directly or indirectly called by the main function). In the case of a yield, [`coroutine.resume`](#pdf-coroutine.resume) also returns **true**, plus any values passed to [`coroutine.yield`](#pdf-coroutine.yield). The next time you resume the same coroutine, it continues its execution from the point where it yielded, with the call to [`coroutine.yield`](#pdf-coroutine.yield) returning any extra arguments passed to [`coroutine.resume`](#pdf-coroutine.resume).

Like [`coroutine.create`](#pdf-coroutine.create), the [`coroutine.wrap`](#pdf-coroutine.wrap) function also creates a coroutine, but instead of returning the coroutine itself, it returns a function that, when called, resumes the coroutine. Any arguments passed to this function go as extra arguments to [`coroutine.resume`](#pdf-coroutine.resume). [`coroutine.wrap`](#pdf-coroutine.wrap) returns all the values returned by [`coroutine.resume`](#pdf-coroutine.resume), except the first one (the boolean error code). Unlike [`coroutine.resume`](#pdf-coroutine.resume), the function created by [`coroutine.wrap`](#pdf-coroutine.wrap) propagates any error to the caller. In this case, the function also closes the coroutine (see [`coroutine.close`](#pdf-coroutine.close)).

As an example of how coroutines work, consider the following code:

```
function foo (a)
  print("foo", a)
  return coroutine.yield(2*a)
end

co = coroutine.create(function (a,b)
      print("co-body", a, b)
      local r = foo(a+1)
      print("co-body", r)
      local r, s = coroutine.yield(a+b, a-b)
      print("co-body", r, s)
      return b, "end"
end)

print("main", coroutine.resume(co, 1, 10))
print("main", coroutine.resume(co, "r"))
print("main", coroutine.resume(co, "x", "y"))
print("main", coroutine.resume(co, "x", "y"))
```

When you run it, it produces the following output:

```
co-body 1       10
foo     2
main    true    4
co-body r
main    true    11      -9
co-body x       y
main    true    10      end
main    false   cannot resume dead coroutine
```

You can also create and manipulate coroutines through the C API: see functions [`lua_newthread`](#lua_newthread), [`lua_resume`](#lua_resume), and [`lua_yield`](#lua_yield).

# 3 – The Language

This section describes the lexis, the syntax, and the semantics of Lua. In other words, this section describes which tokens are valid, how they can be combined, and what their combinations mean.

Language constructs will be explained using the usual extended BNF notation, in which {*a*} means 0 or more *a*'s, and [*a*] means an optional *a*. Non-terminals are shown like non-terminal, keywords are shown like **kword**, and other terminal symbols are shown like ‘**=**’. The complete syntax of Lua can be found in [§9](#9) at the end of this manual.

## 3.1 – Lexical Conventions

Lua is a free-form language. It ignores spaces and comments between lexical elements (tokens), except as delimiters between two tokens. In source code, Lua recognizes as spaces the standard ASCII whitespace characters space, form feed, newline, carriage return, horizontal tab, and vertical tab.

*Names* (also called *identifiers*) in Lua can be any string of Latin letters, Arabic-Indic digits, and underscores, not beginning with a digit and not being a reserved word. Identifiers are used to name variables, table fields, and labels.

The following *keywords* are reserved and cannot be used as names:

```
and       break     do        else      elseif    end
false     for       function  goto      if        in
local     nil       not       or        repeat    return
then      true      until     while
```

Lua is a case-sensitive language: `and` is a reserved word, but `And` and `AND` are two different, valid names. As a convention, programs should avoid creating names that start with an underscore followed by one or more uppercase letters (such as [`_VERSION`](#pdf-_VERSION)).

The following strings denote other tokens:

```
+     -     *     /     %     ^     #
&     ~     |     <<    >>    //
==    ~=    <=    >=    <     >     =
(     )     {     }     [     ]     ::
;     :     ,     .     ..    ...
```

A *short literal string* can be delimited by matching single or double quotes, and can contain the following C-like escape sequences: '`\a`' (bell), '`\b`' (backspace), '`\f`' (form feed), '`\n`' (newline), '`\r`' (carriage return), '`\t`' (horizontal tab), '`\v`' (vertical tab), '`\\`' (backslash), '`\"`' (quotation mark [double quote]), and '`\'`' (apostrophe [single quote]). A backslash followed by a line break results in a newline in the string. The escape sequence '`\z`' skips the following span of whitespace characters, including line breaks; it is particularly useful to break and indent a long literal string into multiple lines without adding the newlines and spaces into the string contents. A short literal string cannot contain unescaped line breaks nor escapes not forming a valid escape sequence.

We can specify any byte in a short literal string, including embedded zeros, by its numeric value. This can be done with the escape sequence `\xXX`, where *XX* is a sequence of exactly two hexadecimal digits, or with the escape sequence `\ddd`, where *ddd* is a sequence of up to three decimal digits. (Note that if a decimal escape sequence is to be followed by a digit, it must be expressed using exactly three digits.)

The UTF-8 encoding of a Unicode character can be inserted in a literal string with the escape sequence `\u{XXX}` (with mandatory enclosing braces), where *XXX* is a sequence of one or more hexadecimal digits representing the character code point. This code point can be any value less than *2^31*. (Lua uses the original UTF-8 specification here, which is not restricted to valid Unicode code points.)

Literal strings can also be defined using a long format enclosed by *long brackets*. We define an *opening long bracket of level n* as an opening square bracket followed by *n* equal signs followed by another opening square bracket. So, an opening long bracket of level 0 is written as `[[`, an opening long bracket of level 1 is written as `[=[`, and so on. A *closing long bracket* is defined similarly; for instance, a closing long bracket of level 4 is written as `]====]`. A *long literal* starts with an opening long bracket of any level and ends at the first closing long bracket of the same level. It can contain any text except a closing bracket of the same level. Literals in this bracketed form can run for several lines, do not interpret any escape sequences, and ignore long brackets of any other level. Any kind of end-of-line sequence (carriage return, newline, carriage return followed by newline, or newline followed by carriage return) is converted to a simple newline. When the opening long bracket is immediately followed by a newline, the newline is not included in the string.

As an example, in a system using ASCII (in which '`a`' is coded as 97, newline is coded as 10, and '`1`' is coded as 49), the five literal strings below denote the same string:

```
a = 'alo\n123"'
a = "alo\n123\""
a = '\97lo\10\04923"'
a = [[alo
123"]]
a = [==[
alo
123"]==]
```

Any byte in a literal string not explicitly affected by the previous rules represents itself. However, Lua opens files for parsing in text mode, and the system's file functions may have problems with some control characters. So, it is safer to represent binary data as a quoted literal with explicit escape sequences for the non-text characters.

A *numeric constant* (or *numeral*) can be written with an optional fractional part and an optional decimal exponent, marked by a letter '`e`' or '`E`'. Lua also accepts hexadecimal constants, which start with `0x` or `0X`. Hexadecimal constants also accept an optional fractional part plus an optional binary exponent, marked by a letter '`p`' or '`P`' and written in decimal. (For instance, `0x1.fp10` denotes 1984, which is *0x1f / 16* multiplied by *2^10*.)

A numeric constant with a radix point or an exponent denotes a float; otherwise, if its value fits in an integer or it is a hexadecimal constant, it denotes an integer; otherwise (that is, a decimal integer numeral that overflows), it denotes a float. Hexadecimal numerals with neither a radix point nor an exponent always denote an integer value; if the value overflows, it *wraps around* to fit into a valid integer.

Examples of valid integer constants are

```
3   345   0xff   0xBEBADA
```

Examples of valid float constants are

```
3.0     3.1416     314.16e-2     0.31416E1     34e1
0x0.1E  0xA23p-4   0X1.921FB54442D18P+1
```

A *comment* starts with a double hyphen (`--`) anywhere outside a string. If the text immediately after `--` is not an opening long bracket, the comment is a *short comment*, which runs until the end of the line. Otherwise, it is a *long comment*, which runs until the corresponding closing long bracket.

## 3.2 – Variables

Variables are places that store values. There are three kinds of variables in Lua: global variables, local variables, and table fields.

A single name can denote a global variable or a local variable (or a function's formal parameter, which is a particular kind of local variable):

```
var ::= Name
```

Name denotes identifiers (see [§3.1](#3.1)).

Any variable name is assumed to be global unless explicitly declared as a local (see [§3.3.7](#3.3.7)). Local variables are *lexically scoped*: local variables can be freely accessed by functions defined inside their scope (see [§3.5](#3.5)).

Before the first assignment to a variable, its value is **nil**.

Square brackets are used to index a table:

```
var ::= prefixexp ‘[’ exp ‘]’
```

The meaning of accesses to table fields can be changed via metatables (see [§2.4](#2.4)).

The syntax `var.Name` is just syntactic sugar for `var["Name"]`:

```
var ::= prefixexp ‘.’ Name
```

An access to a global variable `x` is equivalent to `_ENV.x`. Due to the way that chunks are compiled, the variable `_ENV` itself is never global (see [§2.2](#2.2)).

## 3.3 – Statements

Lua supports an almost conventional set of statements, similar to those in other conventional languages. This set includes blocks, assignments, control structures, function calls, and variable declarations.

### 3.3.1 – Blocks

A block is a list of statements, which are executed sequentially:

```
block ::= {stat}
```

Lua has *empty statements* that allow you to separate statements with semicolons, start a block with a semicolon or write two semicolons in sequence:

```
stat ::= ‘;’
```

Both function calls and assignments can start with an open parenthesis. This possibility leads to an ambiguity in Lua's grammar. Consider the following fragment:

```
a = b + c
(print or io.write)('done')
```

The grammar could see this fragment in two ways:

```
a = b + c(print or io.write)('done')

a = b + c; (print or io.write)('done')
```

The current parser always sees such constructions in the first way, interpreting the open parenthesis as the start of the arguments to a call. To avoid this ambiguity, it is a good practice to always precede with a semicolon statements that start with a parenthesis:

```
;(print or io.write)('done')
```

A block can be explicitly delimited to produce a single statement:

```
stat ::= do block end
```

Explicit blocks are useful to control the scope of variable declarations. Explicit blocks are also sometimes used to add a **return** statement in the middle of another block (see [§3.3.4](#3.3.4)).

### 3.3.2 – Chunks

The unit of compilation of Lua is called a *chunk*. Syntactically, a chunk is simply a block:

```
chunk ::= block
```

Lua handles a chunk as the body of an anonymous function with a variable number of arguments (see [§3.4.11](#3.4.11)). As such, chunks can define local variables, receive arguments, and return values. Moreover, such anonymous function is compiled as in the scope of an external local variable called `_ENV` (see [§2.2](#2.2)). The resulting function always has `_ENV` as its only external variable, even if it does not use that variable.

A chunk can be stored in a file or in a string inside the host program. To execute a chunk, Lua first *loads* it, precompiling the chunk's code into instructions for a virtual machine, and then Lua executes the compiled code with an interpreter for the virtual machine.

Chunks can also be precompiled into binary form; see the program `luac` and the function [`string.dump`](#pdf-string.dump) for details. Programs in source and compiled forms are interchangeable; Lua automatically detects the file type and acts accordingly (see [`load`](#pdf-load)).

### 3.3.3 – Assignment

Lua allows multiple assignments. Therefore, the syntax for assignment defines a list of variables on the left side and a list of expressions on the right side. The elements in both lists are separated by commas:

```
stat ::= varlist ‘=’ explist
varlist ::= var {‘,’ var}
explist ::= exp {‘,’ exp}
```

Expressions are discussed in [§3.4](#3.4).

Before the assignment, the list of values is *adjusted* to the length of the list of variables (see [§3.4.12](#3.4.12)).

If a variable is both assigned and read inside a multiple assignment, Lua ensures that all reads get the value of the variable before the assignment. Thus the code

```
i = 3
i, a[i] = i+1, 20
```

sets `a[3]` to 20, without affecting `a[4]` because the `i` in `a[i]` is evaluated (to 3) before it is assigned 4. Similarly, the line

```
x, y = y, x
```

exchanges the values of `x` and `y`, and

```
x, y, z = y, z, x
```

cyclically permutes the values of `x`, `y`, and `z`.

Note that this guarantee covers only accesses syntactically inside the assignment statement. If a function or a metamethod called during the assignment changes the value of a variable, Lua gives no guarantees about the order of that access.

An assignment to a global name `x = val` is equivalent to the assignment `_ENV.x = val` (see [§2.2](#2.2)).

The meaning of assignments to table fields and global variables (which are actually table fields, too) can be changed via metatables (see [§2.4](#2.4)).

### 3.3.4 – Control Structures

The control structures **if**, **while**, and **repeat** have the usual meaning and familiar syntax:

```
stat ::= while exp do block end
stat ::= repeat block until exp
stat ::= if exp then block {elseif exp then block} [else block] end
```

Lua also has a **for** statement, in two flavors (see [§3.3.5](#3.3.5)).

The condition expression of a control structure can return any value. Both **false** and **nil** test false. All values different from **nil** and **false** test true. In particular, the number 0 and the empty string also test true.

In the **repeat**–**until** loop, the inner block does not end at the **until** keyword, but only after the condition. So, the condition can refer to local variables declared inside the loop block.

The **goto** statement transfers the program control to a label. For syntactical reasons, labels in Lua are considered statements too:

```
stat ::= goto Name
stat ::= label
label ::= ‘::’ Name ‘::’
```

A label is visible in the entire block where it is defined, except inside nested functions. A goto can jump to any visible label as long as it does not enter into the scope of a local variable. A label should not be declared where a label with the same name is visible, even if this other label has been declared in an enclosing block.

The **break** statement terminates the execution of a **while**, **repeat**, or **for** loop, skipping to the next statement after the loop:

```
stat ::= break
```

A **break** ends the innermost enclosing loop.

The **return** statement is used to return values from a function or a chunk (which is handled as an anonymous function). Functions can return more than one value, so the syntax for the **return** statement is

```
stat ::= return [explist] [‘;’]
```

The **return** statement can only be written as the last statement of a block. If it is necessary to **return** in the middle of a block, then an explicit inner block can be used, as in the idiom `do return end`, because now **return** is the last statement in its (inner) block.

### 3.3.5 – For Statement

The **for** statement has two forms: one numerical and one generic.

#### The numerical **for** loop

The numerical **for** loop repeats a block of code while a control variable goes through an arithmetic progression. It has the following syntax:

```
stat ::= for Name ‘=’ exp ‘,’ exp [‘,’ exp] do block end
```

The given identifier (Name) defines the control variable, which is a new variable local to the loop body (*block*).

The loop starts by evaluating once the three control expressions. Their values are called respectively the *initial value*, the *limit*, and the *step*. If the step is absent, it defaults to 1.

If both the initial value and the step are integers, the loop is done with integers; note that the limit may not be an integer. Otherwise, the three values are converted to floats and the loop is done with floats. Beware of floating-point accuracy in this case.

After that initialization, the loop body is repeated with the value of the control variable going through an arithmetic progression, starting at the initial value, with a common difference given by the step. A negative step makes a decreasing sequence; a step equal to zero raises an error. The loop continues while the value is less than or equal to the limit (greater than or equal to for a negative step). If the initial value is already greater than the limit (or less than, if the step is negative), the body is not executed.

For integer loops, the control variable never wraps around; instead, the loop ends in case of an overflow.

You should not change the value of the control variable during the loop. If you need its value after the loop, assign it to another variable before exiting the loop.

#### The generic **for** loop

The generic **for** statement works over functions, called *iterators*. On each iteration, the iterator function is called to produce a new value, stopping when this new value is **nil**. The generic **for** loop has the following syntax:

```
stat ::= for namelist in explist do block end
namelist ::= Name {‘,’ Name}
```

A **for** statement like

```
for var_1, ···, var_n in explist do body end
```

works as follows.

The names *var_i* declare loop variables local to the loop body. The first of these variables is the *control variable*.

The loop starts by evaluating *explist* to produce four values: an *iterator function*, a *state*, an initial value for the control variable, and a *closing value*.

Then, at each iteration, Lua calls the iterator function with two arguments: the state and the control variable. The results from this call are then assigned to the loop variables, following the rules of multiple assignments (see [§3.3.3](#3.3.3)). If the control variable becomes **nil**, the loop terminates. Otherwise, the body is executed and the loop goes to the next iteration.

The closing value behaves like a to-be-closed variable (see [§3.3.8](#3.3.8)), which can be used to release resources when the loop ends. Otherwise, it does not interfere with the loop.

You should not change the value of the control variable during the loop.

### 3.3.6 – Function Calls as Statements

To allow possible side-effects, function calls can be executed as statements:

```
stat ::= functioncall
```

In this case, all returned values are thrown away. Function calls are explained in [§3.4.10](#3.4.10).

### 3.3.7 – Local Declarations

Local variables can be declared anywhere inside a block. The declaration can include an initialization:

```
stat ::= local attnamelist [‘=’ explist]
attnamelist ::=  Name attrib {‘,’ Name attrib}
```

If present, an initial assignment has the same semantics of a multiple assignment (see [§3.3.3](#3.3.3)). Otherwise, all variables are initialized with **nil**.

Each variable name may be postfixed by an attribute (a name between angle brackets):

```
attrib ::= [‘<’ Name ‘>’]
```

There are two possible attributes: `const`, which declares a constant variable, that is, a variable that cannot be assigned to after its initialization; and `close`, which declares a to-be-closed variable (see [§3.3.8](#3.3.8)). A list of variables can contain at most one to-be-closed variable.

A chunk is also a block (see [§3.3.2](#3.3.2)), and so local variables can be declared in a chunk outside any explicit block.

The visibility rules for local variables are explained in [§3.5](#3.5).

### 3.3.8 – To-be-closed Variables

A to-be-closed variable behaves like a constant local variable, except that its value is *closed* whenever the variable goes out of scope, including normal block termination, exiting its block by **break**/**goto**/**return**, or exiting by an error.

Here, to *close* a value means to call its `__close` metamethod. When calling the metamethod, the value itself is passed as the first argument and the error object that caused the exit (if any) is passed as a second argument; if there was no error, the second argument is **nil**.

The value assigned to a to-be-closed variable must have a `__close` metamethod or be a false value. (**nil** and **false** are ignored as to-be-closed values.)

If several to-be-closed variables go out of scope at the same event, they are closed in the reverse order that they were declared.

If there is any error while running a closing method, that error is handled like an error in the regular code where the variable was defined. After an error, the other pending closing methods will still be called.

If a coroutine yields and is never resumed again, some variables may never go out of scope, and therefore they will never be closed. (These variables are the ones created inside the coroutine and in scope at the point where the coroutine yielded.) Similarly, if a coroutine ends with an error, it does not unwind its stack, so it does not close any variable. In both cases, you can either use finalizers or call [`coroutine.close`](#pdf-coroutine.close) to close the variables. However, if the coroutine was created through [`coroutine.wrap`](#pdf-coroutine.wrap), then its corresponding function will close the coroutine in case of errors.

## 3.4 – Expressions

The basic expressions in Lua are the following:

```
exp ::= prefixexp
exp ::= nil | false | true
exp ::= Numeral
exp ::= LiteralString
exp ::= functiondef
exp ::= tableconstructor
exp ::= ‘...’
exp ::= exp binop exp
exp ::= unop exp
prefixexp ::= var | functioncall | ‘(’ exp ‘)’
```

Numerals and literal strings are explained in [§3.1](#3.1); variables are explained in [§3.2](#3.2); function definitions are explained in [§3.4.11](#3.4.11); function calls are explained in [§3.4.10](#3.4.10); table constructors are explained in [§3.4.9](#3.4.9). Vararg expressions, denoted by three dots ('`...`'), can only be used when directly inside a variadic function; they are explained in [§3.4.11](#3.4.11).

Binary operators comprise arithmetic operators (see [§3.4.1](#3.4.1)), bitwise operators (see [§3.4.2](#3.4.2)), relational operators (see [§3.4.4](#3.4.4)), logical operators (see [§3.4.5](#3.4.5)), and the concatenation operator (see [§3.4.6](#3.4.6)). Unary operators comprise the unary minus (see [§3.4.1](#3.4.1)), the unary bitwise NOT (see [§3.4.2](#3.4.2)), the unary logical **not** (see [§3.4.5](#3.4.5)), and the unary *length operator* (see [§3.4.7](#3.4.7)).

### 3.4.1 – Arithmetic Operators

Lua supports the following arithmetic operators:

- **`+`: **addition

- **`-`: **subtraction

- **`*`: **multiplication

- **`/`: **float division

- **`//`: **floor division

- **`%`: **modulo

- **`^`: **exponentiation

- **`-`: **unary minus

With the exception of exponentiation and float division, the arithmetic operators work as follows: If both operands are integers, the operation is performed over integers and the result is an integer. Otherwise, if both operands are numbers, then they are converted to floats, the operation is performed following the machine's rules for floating-point arithmetic (usually the IEEE 754 standard), and the result is a float. (The string library coerces strings to numbers in arithmetic operations; see [§3.4.3](#3.4.3) for details.)

Exponentiation and float division (`/`) always convert their operands to floats and the result is always a float. Exponentiation uses the ISO C function `pow`, so that it works for non-integer exponents too.

Floor division (`//`) is a division that rounds the quotient towards minus infinity, resulting in the floor of the division of its operands.

Modulo is defined as the remainder of a division that rounds the quotient towards minus infinity (floor division).

In case of overflows in integer arithmetic, all operations *wrap around*.

### 3.4.2 – Bitwise Operators

Lua supports the following bitwise operators:

- **`&`: **bitwise AND

- **`|`: **bitwise OR

- **`~`: **bitwise exclusive OR

- **`>>`: **right shift

- **`<<`: **left shift

- **`~`: **unary bitwise NOT

All bitwise operations convert its operands to integers (see [§3.4.3](#3.4.3)), operate on all bits of those integers, and result in an integer.

Both right and left shifts fill the vacant bits with zeros. Negative displacements shift to the other direction; displacements with absolute values equal to or higher than the number of bits in an integer result in zero (as all bits are shifted out).

### 3.4.3 – Coercions and Conversions

Lua provides some automatic conversions between some types and representations at run time. Bitwise operators always convert float operands to integers. Exponentiation and float division always convert integer operands to floats. All other arithmetic operations applied to mixed numbers (integers and floats) convert the integer operand to a float. The C API also converts both integers to floats and floats to integers, as needed. Moreover, string concatenation accepts numbers as arguments, besides strings.

In a conversion from integer to float, if the integer value has an exact representation as a float, that is the result. Otherwise, the conversion gets the nearest higher or the nearest lower representable value. This kind of conversion never fails.

The conversion from float to integer checks whether the float has an exact representation as an integer (that is, the float has an integral value and it is in the range of integer representation). If it does, that representation is the result. Otherwise, the conversion fails.

Several places in Lua coerce strings to numbers when necessary. In particular, the string library sets metamethods that try to coerce strings to numbers in all arithmetic operations. If the conversion fails, the library calls the metamethod of the other operand (if present) or it raises an error. Note that bitwise operators do not do this coercion.

It is always a good practice not to rely on the implicit coercions from strings to numbers, as they are not always applied; in particular, `"1"==1` is false and `"1"<1` raises an error (see [§3.4.4](#3.4.4)). These coercions exist mainly for compatibility and may be removed in future versions of the language.

A string is converted to an integer or a float following its syntax and the rules of the Lua lexer. The string may have also leading and trailing whitespaces and a sign. All conversions from strings to numbers accept both a dot and the current locale mark as the radix character. (The Lua lexer, however, accepts only a dot.) If the string is not a valid numeral, the conversion fails. If necessary, the result of this first step is then converted to a specific number subtype following the previous rules for conversions between floats and integers.

The conversion from numbers to strings uses a non-specified human-readable format. To convert numbers to strings in any specific way, use the function [`string.format`](#pdf-string.format).

### 3.4.4 – Relational Operators

Lua supports the following relational operators:

- **`==`: **equality

- **`~=`: **inequality

- **`<`: **less than

- **`>`: **greater than

- **`<=`: **less or equal

- **`>=`: **greater or equal

These operators always result in **false** or **true**.

Equality (`==`) first compares the type of its operands. If the types are different, then the result is **false**. Otherwise, the values of the operands are compared. Strings are equal if they have the same byte content. Numbers are equal if they denote the same mathematical value.

Tables, userdata, and threads are compared by reference: two objects are considered equal only if they are the same object. Every time you create a new object (a table, a userdata, or a thread), this new object is different from any previously existing object. A function is always equal to itself. Functions with any detectable difference (different behavior, different definition) are always different. Functions created at different times but with no detectable differences may be classified as equal or not (depending on internal caching details).

You can change the way that Lua compares tables and userdata by using the `__eq` metamethod (see [§2.4](#2.4)).

Equality comparisons do not convert strings to numbers or vice versa. Thus, `"0"==0` evaluates to **false**, and `t[0]` and `t["0"]` denote different entries in a table.

The operator `~=` is exactly the negation of equality (`==`).

The order operators work as follows. If both arguments are numbers, then they are compared according to their mathematical values, regardless of their subtypes. Otherwise, if both arguments are strings, then their values are compared according to the current locale. Otherwise, Lua tries to call the `__lt` or the `__le` metamethod (see [§2.4](#2.4)). A comparison `a > b` is translated to `b = b` is translated to `b <= a`.

Following the IEEE 754 standard, the special value NaN is considered neither less than, nor equal to, nor greater than any value, including itself.

### 3.4.5 – Logical Operators

The logical operators in Lua are **and**, **or**, and **not**. Like the control structures (see [§3.3.4](#3.3.4)), all logical operators consider both **false** and **nil** as false and anything else as true.

The negation operator **not** always returns **false** or **true**. The conjunction operator **and** returns its first argument if this value is **false** or **nil**; otherwise, **and** returns its second argument. The disjunction operator **or** returns its first argument if this value is different from **nil** and **false**; otherwise, **or** returns its second argument. Both **and** and **or** use short-circuit evaluation; that is, the second operand is evaluated only if necessary. Here are some examples:

```
10 or 20            --> 10
10 or error()       --> 10
nil or "a"          --> "a"
nil and 10          --> nil
false and error()   --> false
false and nil       --> false
false or nil        --> nil
10 and 20           --> 20
```

### 3.4.6 – Concatenation

The string concatenation operator in Lua is denoted by two dots ('`..`'). If both operands are strings or numbers, then the numbers are converted to strings in a non-specified format (see [§3.4.3](#3.4.3)). Otherwise, the `__concat` metamethod is called (see [§2.4](#2.4)).

### 3.4.7 – The Length Operator

The length operator is denoted by the unary prefix operator `#`.

The length of a string is its number of bytes. (That is the usual meaning of string length when each character is one byte.)

The length operator applied on a table returns a border in that table. A *border* in a table `t` is any non-negative integer that satisfies the following condition:

```
(border == 0 or t[border] ~= nil) and
(t[border + 1] == nil or border == math.maxinteger)
```

In words, a border is any positive integer index present in the table that is followed by an absent index, plus two limit cases: zero, when index 1 is absent; and the maximum value for an integer, when that index is present. Note that keys that are not positive integers do not interfere with borders.

A table with exactly one border is called a *sequence*. For instance, the table `{10, 20, 30, 40, 50}` is a sequence, as it has only one border (5). The table `{10, 20, 30, nil, 50}` has two borders (3 and 5), and therefore it is not a sequence. (The **nil** at index 4 is called a *hole*.) The table `{nil, 20, 30, nil, nil, 60, nil}` has three borders (0, 3, and 6), so it is not a sequence, too. The table `{}` is a sequence with border 0.

When `t` is a sequence, `#t` returns its only border, which corresponds to the intuitive notion of the length of the sequence. When `t` is not a sequence, `#t` can return any of its borders. (The exact one depends on details of the internal representation of the table, which in turn can depend on how the table was populated and the memory addresses of its non-numeric keys.)

The computation of the length of a table has a guaranteed worst time of *O(log n)*, where *n* is the largest integer key in the table.

A program can modify the behavior of the length operator for any value but strings through the `__len` metamethod (see [§2.4](#2.4)).

### 3.4.8 – Precedence

Operator precedence in Lua follows the table below, from lower to higher priority:

```
or
and
<     >     <=    >=    ~=    ==
|
~
&
<<    >>
..
+     -
*     /     //    %
unary operators (not   #     -     ~)
^
```

As usual, you can use parentheses to change the precedences of an expression. The concatenation ('`..`') and exponentiation ('`^`') operators are right associative. All other binary operators are left associative.

### 3.4.9 – Table Constructors

Table constructors are expressions that create tables. Every time a constructor is evaluated, a new table is created. A constructor can be used to create an empty table or to create a table and initialize some of its fields. The general syntax for constructors is

```
tableconstructor ::= ‘{’ [fieldlist] ‘}’
fieldlist ::= field {fieldsep field} [fieldsep]
field ::= ‘[’ exp ‘]’ ‘=’ exp | Name ‘=’ exp | exp
fieldsep ::= ‘,’ | ‘;’
```

Each field of the form `[exp1] = exp2` adds to the new table an entry with key `exp1` and value `exp2`. A field of the form `name = exp` is equivalent to `["name"] = exp`. Fields of the form `exp` are equivalent to `[i] = exp`, where `i` are consecutive integers starting with 1; fields in the other formats do not affect this counting. For example,

```
a = { [f(1)] = g; "x", "y"; x = 1, f(x), [30] = 23; 45 }
```

is equivalent to

```
do
  local t = {}
  t[f(1)] = g
  t[1] = "x"         -- 1st exp
  t[2] = "y"         -- 2nd exp
  t.x = 1            -- t["x"] = 1
  t[3] = f(x)        -- 3rd exp
  t[30] = 23
  t[4] = 45          -- 4th exp
  a = t
end
```

The order of the assignments in a constructor is undefined. (This order would be relevant only when there are repeated keys.)

If the last field in the list has the form `exp` and the expression is a multires expression, then all values returned by this expression enter the list consecutively (see [§3.4.12](#3.4.12)).

The field list can have an optional trailing separator, as a convenience for machine-generated code.

### 3.4.10 – Function Calls

A function call in Lua has the following syntax:

```
functioncall ::= prefixexp args
```

In a function call, first prefixexp and args are evaluated. If the value of prefixexp has type *function*, then this function is called with the given arguments. Otherwise, if present, the prefixexp `__call` metamethod is called: its first argument is the value of prefixexp, followed by the original call arguments (see [§2.4](#2.4)).

The form

```
functioncall ::= prefixexp ‘:’ Name args
```

can be used to emulate methods. A call `v:name(args)` is syntactic sugar for `v.name(v,args)`, except that `v` is evaluated only once.

Arguments have the following syntax:

```
args ::= ‘(’ [explist] ‘)’
args ::= tableconstructor
args ::= LiteralString
```

All argument expressions are evaluated before the call. A call of the form `f{fields}` is syntactic sugar for `f({fields})`; that is, the argument list is a single new table. A call of the form `f'string'` (or `f"string"` or `f[[string]]`) is syntactic sugar for `f('string')`; that is, the argument list is a single literal string.

A call of the form `return functioncall` not in the scope of a to-be-closed variable is called a *tail call*. Lua implements *proper tail calls* (or *proper tail recursion*): In a tail call, the called function reuses the stack entry of the calling function. Therefore, there is no limit on the number of nested tail calls that a program can execute. However, a tail call erases any debug information about the calling function. Note that a tail call only happens with a particular syntax, where the **return** has one single function call as argument, and it is outside the scope of any to-be-closed variable. This syntax makes the calling function return exactly the returns of the called function, without any intervening action. So, none of the following examples are tail calls:

```
return (f(x))        -- results adjusted to 1
return 2 * f(x)      -- result multiplied by 2
return x, f(x)       -- additional results
f(x); return         -- results discarded
return x or f(x)     -- results adjusted to 1
```

### 3.4.11 – Function Definitions

The syntax for function definition is

```
functiondef ::= function funcbody
funcbody ::= ‘(’ [parlist] ‘)’ block end
```

The following syntactic sugar simplifies function definitions:

```
stat ::= function funcname funcbody
stat ::= local function Name funcbody
funcname ::= Name {‘.’ Name} [‘:’ Name]
```

The statement

```
function f () body end
```

translates to

```
f = function () body end
```

The statement

```
function t.a.b.c.f () body end
```

translates to

```
t.a.b.c.f = function () body end
```

The statement

```
local function f () body end
```

translates to

```
local f; f = function () body end
```

not to

```
local f = function () body end
```

(This only makes a difference when the body of the function contains references to `f`.)

A function definition is an executable expression, whose value has type *function*. When Lua precompiles a chunk, all its function bodies are precompiled too, but they are not created yet. Then, whenever Lua executes the function definition, the function is *instantiated* (or *closed*). This function instance, or *closure*, is the final value of the expression.

Parameters act as local variables that are initialized with the argument values:

```
parlist ::= namelist [‘,’ ‘...’] | ‘...’
```

When a Lua function is called, it adjusts its list of arguments to the length of its list of parameters (see [§3.4.12](#3.4.12)), unless the function is a *variadic function*, which is indicated by three dots ('`...`') at the end of its parameter list. A variadic function does not adjust its argument list; instead, it collects all extra arguments and supplies them to the function through a *vararg expression*, which is also written as three dots. The value of this expression is a list of all actual extra arguments, similar to a function with multiple results (see [§3.4.12](#3.4.12)).

As an example, consider the following definitions:

```
function f(a, b) end
function g(a, b, ...) end
function r() return 1,2,3 end
```

Then, we have the following mapping from arguments to parameters and to the vararg expression:

```
CALL             PARAMETERS

f(3)             a=3, b=nil
f(3, 4)          a=3, b=4
f(3, 4, 5)       a=3, b=4
f(r(), 10)       a=1, b=10
f(r())           a=1, b=2

g(3)             a=3, b=nil, ... -->  (nothing)
g(3, 4)          a=3, b=4,   ... -->  (nothing)
g(3, 4, 5, 8)    a=3, b=4,   ... -->  5  8
g(5, r())        a=5, b=1,   ... -->  2  3
```

Results are returned using the **return** statement (see [§3.3.4](#3.3.4)). If control reaches the end of a function without encountering a **return** statement, then the function returns with no results.

There is a system-dependent limit on the number of values that a function may return. This limit is guaranteed to be greater than 1000.

The *colon* syntax is used to emulate *methods*, adding an implicit extra parameter `self` to the function. Thus, the statement

```
function t.a.b.c:f (params) body end
```

is syntactic sugar for

```
t.a.b.c.f = function (self, params) body end
```

### 3.4.12 – Lists of expressions, multiple results, and adjustment

Both function calls and vararg expressions can result in multiple values. These expressions are called *multires expressions*.

When a multires expression is used as the last element of a list of expressions, all results from the expression are added to the list of values produced by the list of expressions. Note that a single expression in a place that expects a list of expressions is the last expression in that (singleton) list.

These are the places where Lua expects a list of expressions:

- A **return** statement, for instance `return e1, e2, e3` (see [§3.3.4](#3.3.4)).

- A table constructor, for instance `{e1, e2, e3}` (see [§3.4.9](#3.4.9)).

- The arguments of a function call, for instance `foo(e1, e2, e3)` (see [§3.4.10](#3.4.10)).

- A multiple assignment, for instance `a , b, c = e1, e2, e3` (see [§3.3.3](#3.3.3)).

- A local declaration, for instance `local a , b, c = e1, e2, e3` (see [§3.3.7](#3.3.7)).

- The initial values in a generic **for** loop, for instance `for k in e1, e2, e3 do ... end` (see [§3.3.5](#3.3.5)).

In the last four cases, the list of values from the list of expressions must be *adjusted* to a specific length: the number of parameters in a call to a non-variadic function (see [§3.4.11](#3.4.11)), the number of variables in a multiple assignment or a local declaration, and exactly four values for a generic **for** loop. The *adjustment* follows these rules: If there are more values than needed, the extra values are thrown away; if there are fewer values than needed, the list is extended with **nil**'s. When the list of expressions ends with a multires expression, all results from that expression enter the list of values before the adjustment.

When a multires expression is used in a list of expressions without being the last element, or in a place where the syntax expects a single expression, Lua adjusts the result list of that expression to one element. As a particular case, the syntax expects a single expression inside a parenthesized expression; therefore, adding parentheses around a multires expression forces it to produce exactly one result.

We seldom need to use a vararg expression in a place where the syntax expects a single expression. (Usually it is simpler to add a regular parameter before the variadic part and use that parameter.) When there is such a need, we recommend assigning the vararg expression to a single variable and using that variable in its place.

Here are some examples of uses of mutlres expressions. In all cases, when the construction needs "the n-th result" and there is no such result, it uses a **nil**.

```
print(x, f())      -- prints x and all results from f().
print(x, (f()))    -- prints x and the first result from f().
print(f(), x)      -- prints the first result from f() and x.
print(1 + f())     -- prints 1 added to the first result from f().
local x = ...      -- x gets the first vararg argument.
x,y = ...          -- x gets the first vararg argument,
                   -- y gets the second vararg argument.
x,y,z = w, f()     -- x gets w, y gets the first result from f(),
                   -- z gets the second result from f().
x,y,z = f()        -- x gets the first result from f(),
                   -- y gets the second result from f(),
                   -- z gets the third result from f().
x,y,z = f(), g()   -- x gets the first result from f(),
                   -- y gets the first result from g(),
                   -- z gets the second result from g().
x,y,z = (f())      -- x gets the first result from f(), y and z get nil.
return f()         -- returns all results from f().
return x, ...      -- returns x and all received vararg arguments.
return x,y,f()     -- returns x, y, and all results from f().
{f()}              -- creates a list with all results from f().
{...}              -- creates a list with all vararg arguments.
{f(), 5}           -- creates a list with the first result from f() and 5.
```

## 3.5 – Visibility Rules

Lua is a lexically scoped language. The scope of a local variable begins at the first statement after its declaration and lasts until the last non-void statement of the innermost block that includes the declaration. (*Void statements* are labels and empty statements.) Consider the following example:

```
x = 10                -- global variable
do                    -- new block
  local x = x         -- new 'x', with value 10
  print(x)            --> 10
  x = x+1
  do                  -- another block
    local x = x+1     -- another 'x'
    print(x)          --> 12
  end
  print(x)            --> 11
end
print(x)              --> 10  (the global one)
```

Notice that, in a declaration like `local x = x`, the new `x` being declared is not in scope yet, and so the second `x` refers to the outside variable.

Because of the lexical scoping rules, local variables can be freely accessed by functions defined inside their scope. A local variable used by an inner function is called an *upvalue* (or *external local variable*, or simply *external variable*) inside the inner function.

Notice that each execution of a **local** statement defines new local variables. Consider the following example:

```
a = {}
local x = 20
for i = 1, 10 do
  local y = 0
  a[i] = function () y = y + 1; return x + y end
end
```

The loop creates ten closures (that is, ten instances of the anonymous function). Each of these closures uses a different `y` variable, while all of them share the same `x`.

# 4 – The Application Program Interface

This section describes the C API for Lua, that is, the set of C functions available to the host program to communicate with Lua. All API functions and related types and constants are declared in the header file `lua.h`.

Even when we use the term "function", any facility in the API may be provided as a macro instead. Except where stated otherwise, all such macros use each of their arguments exactly once (except for the first argument, which is always a Lua state), and so do not generate any hidden side-effects.

As in most C libraries, the Lua API functions do not check their arguments for validity or consistency. However, you can change this behavior by compiling Lua with the macro `LUA_USE_APICHECK` defined.

The Lua library is fully reentrant: it has no global variables. It keeps all information it needs in a dynamic structure, called the *Lua state*.

Each Lua state has one or more threads, which correspond to independent, cooperative lines of execution. The type [`lua_State`](#lua_State) (despite its name) refers to a thread. (Indirectly, through the thread, it also refers to the Lua state associated to the thread.)

A pointer to a thread must be passed as the first argument to every function in the library, except to [`lua_newstate`](#lua_newstate), which creates a Lua state from scratch and returns a pointer to the *main thread* in the new state.

## 4.1 – The Stack

Lua uses a *virtual stack* to pass values to and from C. Each element in this stack represents a Lua value (**nil**, number, string, etc.). Functions in the API can access this stack through the Lua state parameter that they receive.

Whenever Lua calls C, the called function gets a new stack, which is independent of previous stacks and of stacks of C functions that are still active. This stack initially contains any arguments to the C function and it is where the C function can store temporary Lua values and must push its results to be returned to the caller (see [`lua_CFunction`](#lua_CFunction)).

For convenience, most query operations in the API do not follow a strict stack discipline. Instead, they can refer to any element in the stack by using an *index*: A positive index represents an absolute stack position, starting at 1 as the bottom of the stack; a negative index represents an offset relative to the top of the stack. More specifically, if the stack has *n* elements, then index 1 represents the first element (that is, the element that was pushed onto the stack first) and index *n* represents the last element; index -1 also represents the last element (that is, the element at the top) and index *-n* represents the first element.

### 4.1.1 – Stack Size

When you interact with the Lua API, you are responsible for ensuring consistency. In particular, *you are responsible for controlling stack overflow*. When you call any API function, you must ensure the stack has enough room to accommodate the results.

There is one exception to the above rule: When you call a Lua function without a fixed number of results (see [`lua_call`](#lua_call)), Lua ensures that the stack has enough space for all results. However, it does not ensure any extra space. So, before pushing anything on the stack after such a call you should use [`lua_checkstack`](#lua_checkstack).

Whenever Lua calls C, it ensures that the stack has space for at least `LUA_MINSTACK` extra elements; that is, you can safely push up to `LUA_MINSTACK` values into it. `LUA_MINSTACK` is defined as 20, so that usually you do not have to worry about stack space unless your code has loops pushing elements onto the stack. Whenever necessary, you can use the function [`lua_checkstack`](#lua_checkstack) to ensure that the stack has enough space for pushing new elements.

### 4.1.2 – Valid and Acceptable Indices

Any function in the API that receives stack indices works only with *valid indices* or *acceptable indices*.

A *valid index* is an index that refers to a position that stores a modifiable Lua value. It comprises stack indices between 1 and the stack top (`1 ≤ abs(index) ≤ top`) plus *pseudo-indices*, which represent some positions that are accessible to C code but that are not in the stack. Pseudo-indices are used to access the registry (see [§4.3](#4.3)) and the upvalues of a C function (see [§4.2](#4.2)).

Functions that do not need a specific mutable position, but only a value (e.g., query functions), can be called with acceptable indices. An *acceptable index* can be any valid index, but it also can be any positive index after the stack top within the space allocated for the stack, that is, indices up to the stack size. (Note that 0 is never an acceptable index.) Indices to upvalues (see [§4.2](#4.2)) greater than the real number of upvalues in the current C function are also acceptable (but invalid). Except when noted otherwise, functions in the API work with acceptable indices.

Acceptable indices serve to avoid extra tests against the stack top when querying the stack. For instance, a C function can query its third argument without the need to check whether there is a third argument, that is, without the need to check whether 3 is a valid index.

For functions that can be called with acceptable indices, any non-valid index is treated as if it contains a value of a virtual type `LUA_TNONE`, which behaves like a nil value.

### 4.1.3 – Pointers to strings

Several functions in the API return pointers (`const char*`) to Lua strings in the stack. (See [`lua_pushfstring`](#lua_pushfstring), [`lua_pushlstring`](#lua_pushlstring), [`lua_pushstring`](#lua_pushstring), and [`lua_tolstring`](#lua_tolstring). See also [`luaL_checklstring`](#luaL_checklstring), [`luaL_checkstring`](#luaL_checkstring), and [`luaL_tolstring`](#luaL_tolstring) in the auxiliary library.)

In general, Lua's garbage collection can free or move internal memory and then invalidate pointers to internal strings. To allow a safe use of these pointers, the API guarantees that any pointer to a string in a stack index is valid while the string value at that index is not removed from the stack. (It can be moved to another index, though.) When the index is a pseudo-index (referring to an upvalue), the pointer is valid while the corresponding call is active and the corresponding upvalue is not modified.

Some functions in the debug interface also return pointers to strings, namely [`lua_getlocal`](#lua_getlocal), [`lua_getupvalue`](#lua_getupvalue), [`lua_setlocal`](#lua_setlocal), and [`lua_setupvalue`](#lua_setupvalue). For these functions, the pointer is guaranteed to be valid while the caller function is active and the given closure (if one was given) is in the stack.

Except for these guarantees, the garbage collector is free to invalidate any pointer to internal strings.

## 4.2 – C Closures

When a C function is created, it is possible to associate some values with it, thus creating a *C closure* (see [`lua_pushcclosure`](#lua_pushcclosure)); these values are called *upvalues* and are accessible to the function whenever it is called.

Whenever a C function is called, its upvalues are located at specific pseudo-indices. These pseudo-indices are produced by the macro [`lua_upvalueindex`](#lua_upvalueindex). The first upvalue associated with a function is at index `lua_upvalueindex(1)`, and so on. Any access to `lua_upvalueindex(n)`, where *n* is greater than the number of upvalues of the current function (but not greater than 256, which is one plus the maximum number of upvalues in a closure), produces an acceptable but invalid index.

A C closure can also change the values of its corresponding upvalues.

## 4.3 – Registry

Lua provides a *registry*, a predefined table that can be used by any C code to store whatever Lua values it needs to store. The registry table is always accessible at pseudo-index `LUA_REGISTRYINDEX`. Any C library can store data into this table, but it must take care to choose keys that are different from those used by other libraries, to avoid collisions. Typically, you should use as key a string containing your library name, or a light userdata with the address of a C object in your code, or any Lua object created by your code. As with variable names, string keys starting with an underscore followed by uppercase letters are reserved for Lua.

The integer keys in the registry are used by the reference mechanism (see [`luaL_ref`](#luaL_ref)) and by some predefined values. Therefore, integer keys in the registry must not be used for other purposes.

When you create a new Lua state, its registry comes with some predefined values. These predefined values are indexed with integer keys defined as constants in `lua.h`. The following constants are defined:

- **`LUA_RIDX_MAINTHREAD`: ** At this index the registry has the main thread of the state. (The main thread is the one created together with the state.)

- **`LUA_RIDX_GLOBALS`: ** At this index the registry has the global environment.

## 4.4 – Error Handling in C

Internally, Lua uses the C `longjmp` facility to handle errors. (Lua will use exceptions if you compile it as C++; search for `LUAI_THROW` in the source code for details.) When Lua faces any error, such as a memory allocation error or a type error, it *raises* an error; that is, it does a long jump. A *protected environment* uses `setjmp` to set a recovery point; any error jumps to the most recent active recovery point.

Inside a C function you can raise an error explicitly by calling [`lua_error`](#lua_error).

Most functions in the API can raise an error, for instance due to a memory allocation error. The documentation for each function indicates whether it can raise errors.

If an error happens outside any protected environment, Lua calls a *panic function* (see [`lua_atpanic`](#lua_atpanic)) and then calls `abort`, thus exiting the host application. Your panic function can avoid this exit by never returning (e.g., doing a long jump to your own recovery point outside Lua).

The panic function, as its name implies, is a mechanism of last resort. Programs should avoid it. As a general rule, when a C function is called by Lua with a Lua state, it can do whatever it wants on that Lua state, as it should be already protected. However, when C code operates on other Lua states (e.g., a Lua-state argument to the function, a Lua state stored in the registry, or the result of [`lua_newthread`](#lua_newthread)), it should use them only in API calls that cannot raise errors.

The panic function runs as if it were a message handler (see [§2.3](#2.3)); in particular, the error object is on the top of the stack. However, there is no guarantee about stack space. To push anything on the stack, the panic function must first check the available space (see [§4.1.1](#4.1.1)).

### 4.4.1 – Status Codes

Several functions that report errors in the API use the following status codes to indicate different kinds of errors or other conditions:

- **`LUA_OK` (0): ** no errors.

- **`LUA_ERRRUN`: ** a runtime error.

- **`LUA_ERRMEM`: ** memory allocation error. For such errors, Lua does not call the message handler.

- **`LUA_ERRERR`: ** error while running the message handler.

- **`LUA_ERRSYNTAX`: ** syntax error during precompilation.

- **`LUA_YIELD`: ** the thread (coroutine) yields.

- **`LUA_ERRFILE`: ** a file-related error; e.g., it cannot open or read the file.

These constants are defined in the header file `lua.h`.

## 4.5 – Handling Yields in C

Internally, Lua uses the C `longjmp` facility to yield a coroutine. Therefore, if a C function `foo` calls an API function and this API function yields (directly or indirectly by calling another function that yields), Lua cannot return to `foo` any more, because the `longjmp` removes its frame from the C stack.

To avoid this kind of problem, Lua raises an error whenever it tries to yield across an API call, except for three functions: [`lua_yieldk`](#lua_yieldk), [`lua_callk`](#lua_callk), and [`lua_pcallk`](#lua_pcallk). All those functions receive a *continuation function* (as a parameter named `k`) to continue execution after a yield.

We need to set some terminology to explain continuations. We have a C function called from Lua which we will call the *original function*. This original function then calls one of those three functions in the C API, which we will call the *callee function*, that then yields the current thread. This can happen when the callee function is [`lua_yieldk`](#lua_yieldk), or when the callee function is either [`lua_callk`](#lua_callk) or [`lua_pcallk`](#lua_pcallk) and the function called by them yields.

Suppose the running thread yields while executing the callee function. After the thread resumes, it eventually will finish running the callee function. However, the callee function cannot return to the original function, because its frame in the C stack was destroyed by the yield. Instead, Lua calls a *continuation function*, which was given as an argument to the callee function. As the name implies, the continuation function should continue the task of the original function.

As an illustration, consider the following function:

```
int original_function (lua_State *L) {
  ...     /* code 1 */
  status = lua_pcall(L, n, m, h);  /* calls Lua */
  ...     /* code 2 */
}
```

Now we want to allow the Lua code being run by [`lua_pcall`](#lua_pcall) to yield. First, we can rewrite our function like here:

```
int k (lua_State *L, int status, lua_KContext ctx) {
  ...  /* code 2 */
}

int original_function (lua_State *L) {
  ...     /* code 1 */
  return k(L, lua_pcall(L, n, m, h), ctx);
}
```

In the above code, the new function `k` is a *continuation function* (with type [`lua_KFunction`](#lua_KFunction)), which should do all the work that the original function was doing after calling [`lua_pcall`](#lua_pcall). Now, we must inform Lua that it must call `k` if the Lua code being executed by [`lua_pcall`](#lua_pcall) gets interrupted in some way (errors or yielding), so we rewrite the code as here, replacing [`lua_pcall`](#lua_pcall) by [`lua_pcallk`](#lua_pcallk):

```
int original_function (lua_State *L) {
  ...     /* code 1 */
  return k(L, lua_pcallk(L, n, m, h, ctx2, k), ctx1);
}
```

Note the external, explicit call to the continuation: Lua will call the continuation only if needed, that is, in case of errors or resuming after a yield. If the called function returns normally without ever yielding, [`lua_pcallk`](#lua_pcallk) (and [`lua_callk`](#lua_callk)) will also return normally. (Of course, instead of calling the continuation in that case, you can do the equivalent work directly inside the original function.)

Besides the Lua state, the continuation function has two other parameters: the final status of the call and the context value (`ctx`) that was passed originally to [`lua_pcallk`](#lua_pcallk). Lua does not use this context value; it only passes this value from the original function to the continuation function. For [`lua_pcallk`](#lua_pcallk), the status is the same value that would be returned by [`lua_pcallk`](#lua_pcallk), except that it is [`LUA_YIELD`](#pdf-LUA_YIELD) when being executed after a yield (instead of [`LUA_OK`](#pdf-LUA_OK)). For [`lua_yieldk`](#lua_yieldk) and [`lua_callk`](#lua_callk), the status is always [`LUA_YIELD`](#pdf-LUA_YIELD) when Lua calls the continuation. (For these two functions, Lua will not call the continuation in case of errors, because they do not handle errors.) Similarly, when using [`lua_callk`](#lua_callk), you should call the continuation function with [`LUA_OK`](#pdf-LUA_OK) as the status. (For [`lua_yieldk`](#lua_yieldk), there is not much point in calling directly the continuation function, because [`lua_yieldk`](#lua_yieldk) usually does not return.)

Lua treats the continuation function as if it were the original function. The continuation function receives the same Lua stack from the original function, in the same state it would be if the callee function had returned. (For instance, after a [`lua_callk`](#lua_callk) the function and its arguments are removed from the stack and replaced by the results from the call.) It also has the same upvalues. Whatever it returns is handled by Lua as if it were the return of the original function.

## 4.6 – Functions and Types

Here we list all functions and types from the C API in alphabetical order. Each function has an indicator like this: [-o, +p, *x*]

The first field, `o`, is how many elements the function pops from the stack. The second field, `p`, is how many elements the function pushes onto the stack. (Any function always pushes its results after popping its arguments.) A field in the form `x|y` means the function can push (or pop) `x` or `y` elements, depending on the situation; an interrogation mark '`?`' means that we cannot know how many elements the function pops/pushes by looking only at its arguments. (For instance, they may depend on what is in the stack.) The third field, `x`, tells whether the function may raise errors: '`-`' means the function never raises any error; '`m`' means the function may raise only out-of-memory errors; '`v`' means the function may raise the errors explained in the text; '`e`' means the function can run arbitrary Lua code, either directly or through metamethods, and therefore may raise any errors.

---

### `lua_absindex`

[-0, +0, –]

```
int lua_absindex (lua_State *L, int idx);
```

Converts the acceptable index `idx` into an equivalent absolute index (that is, one that does not depend on the stack size).

---

### `lua_Alloc`

```
typedef void * (*lua_Alloc) (void *ud,
                             void *ptr,
                             size_t osize,
                             size_t nsize);
```

The type of the memory-allocation function used by Lua states. The allocator function must provide a functionality similar to `realloc`, but not exactly the same. Its arguments are `ud`, an opaque pointer passed to [`lua_newstate`](#lua_newstate); `ptr`, a pointer to the block being allocated/reallocated/freed; `osize`, the original size of the block or some code about what is being allocated; and `nsize`, the new size of the block.

When `ptr` is not `NULL`, `osize` is the size of the block pointed by `ptr`, that is, the size given when it was allocated or reallocated.

When `ptr` is `NULL`, `osize` encodes the kind of object that Lua is allocating. `osize` is any of [`LUA_TSTRING`](#pdf-LUA_TSTRING), [`LUA_TTABLE`](#pdf-LUA_TTABLE), [`LUA_TFUNCTION`](#pdf-LUA_TFUNCTION), [`LUA_TUSERDATA`](#pdf-LUA_TUSERDATA), or [`LUA_TTHREAD`](#pdf-LUA_TTHREAD) when (and only when) Lua is creating a new object of that type. When `osize` is some other value, Lua is allocating memory for something else.

Lua assumes the following behavior from the allocator function:

When `nsize` is zero, the allocator must behave like `free` and then return `NULL`.

When `nsize` is not zero, the allocator must behave like `realloc`. In particular, the allocator returns `NULL` if and only if it cannot fulfill the request.

Here is a simple implementation for the allocator function. It is used in the auxiliary library by [`luaL_newstate`](#luaL_newstate).

```
static void *l_alloc (void *ud, void *ptr, size_t osize,
                                           size_t nsize) {
  (void)ud;  (void)osize;  /* not used */
  if (nsize == 0) {
    free(ptr);
    return NULL;
  }
  else
    return realloc(ptr, nsize);
}
```

Note that ISO C ensures that `free(NULL)` has no effect and that `realloc(NULL,size)` is equivalent to `malloc(size)`.

---

### `lua_arith`

[-(2|1), +1, *e*]

```
void lua_arith (lua_State *L, int op);
```

Performs an arithmetic or bitwise operation over the two values (or one, in the case of negations) at the top of the stack, with the value on the top being the second operand, pops these values, and pushes the result of the operation. The function follows the semantics of the corresponding Lua operator (that is, it may call metamethods).

The value of `op` must be one of the following constants:

- **`LUA_OPADD`: ** performs addition (`+`)

- **`LUA_OPSUB`: ** performs subtraction (`-`)

- **`LUA_OPMUL`: ** performs multiplication (`*`)

- **`LUA_OPDIV`: ** performs float division (`/`)

- **`LUA_OPIDIV`: ** performs floor division (`//`)

- **`LUA_OPMOD`: ** performs modulo (`%`)

- **`LUA_OPPOW`: ** performs exponentiation (`^`)

- **`LUA_OPUNM`: ** performs mathematical negation (unary `-`)

- **`LUA_OPBNOT`: ** performs bitwise NOT (`~`)

- **`LUA_OPBAND`: ** performs bitwise AND (`&`)

- **`LUA_OPBOR`: ** performs bitwise OR (`|`)

- **`LUA_OPBXOR`: ** performs bitwise exclusive OR (`~`)

- **`LUA_OPSHL`: ** performs left shift (`<<`)

- **`LUA_OPSHR`: ** performs right shift (`>>`)

---

### `lua_atpanic`

[-0, +0, –]

```
lua_CFunction lua_atpanic (lua_State *L, lua_CFunction panicf);
```

Sets a new panic function and returns the old one (see [§4.4](#4.4)).

---

### `lua_call`

[-(nargs+1), +nresults, *e*]

```
void lua_call (lua_State *L, int nargs, int nresults);
```

Calls a function. Like regular Lua calls, `lua_call` respects the `__call` metamethod. So, here the word "function" means any callable value.

To do a call you must use the following protocol: first, the function to be called is pushed onto the stack; then, the arguments to the call are pushed in direct order; that is, the first argument is pushed first. Finally you call [`lua_call`](#lua_call); `nargs` is the number of arguments that you pushed onto the stack. When the function returns, all arguments and the function value are popped and the call results are pushed onto the stack. The number of results is adjusted to `nresults`, unless `nresults` is `LUA_MULTRET`. In this case, all results from the function are pushed; Lua takes care that the returned values fit into the stack space, but it does not ensure any extra space in the stack. The function results are pushed onto the stack in direct order (the first result is pushed first), so that after the call the last result is on the top of the stack.

Any error while calling and running the function is propagated upwards (with a `longjmp`).

The following example shows how the host program can do the equivalent to this Lua code:

```
a = f("how", t.x, 14)
```

Here it is in C:

```
lua_getglobal(L, "f");                  /* function to be called */
lua_pushliteral(L, "how");                       /* 1st argument */
lua_getglobal(L, "t");                    /* table to be indexed */
lua_getfield(L, -1, "x");        /* push result of t.x (2nd arg) */
lua_remove(L, -2);                  /* remove 't' from the stack */
lua_pushinteger(L, 14);                          /* 3rd argument */
lua_call(L, 3, 1);     /* call 'f' with 3 arguments and 1 result */
lua_setglobal(L, "a");                         /* set global 'a' */
```

Note that the code above is *balanced*: at its end, the stack is back to its original configuration. This is considered good programming practice.

---

### `lua_callk`

[-(nargs + 1), +nresults, *e*]

```
void lua_callk (lua_State *L,
                int nargs,
                int nresults,
                lua_KContext ctx,
                lua_KFunction k);
```

This function behaves exactly like [`lua_call`](#lua_call), but allows the called function to yield (see [§4.5](#4.5)).

---

### `lua_CFunction`

```
typedef int (*lua_CFunction) (lua_State *L);
```

Type for C functions.

In order to communicate properly with Lua, a C function must use the following protocol, which defines the way parameters and results are passed: a C function receives its arguments from Lua in its stack in direct order (the first argument is pushed first). So, when the function starts, `lua_gettop(L)` returns the number of arguments received by the function. The first argument (if any) is at index 1 and its last argument is at index `lua_gettop(L)`. To return values to Lua, a C function just pushes them onto the stack, in direct order (the first result is pushed first), and returns in C the number of results. Any other value in the stack below the results will be properly discarded by Lua. Like a Lua function, a C function called by Lua can also return many results.

As an example, the following function receives a variable number of numeric arguments and returns their average and their sum:

```
static int foo (lua_State *L) {
  int n = lua_gettop(L);    /* number of arguments */
  lua_Number sum = 0.0;
  int i;
  for (i = 1; i <= n; i++) {
    if (!lua_isnumber(L, i)) {
      lua_pushliteral(L, "incorrect argument");
      lua_error(L);
    }
    sum += lua_tonumber(L, i);
  }
  lua_pushnumber(L, sum/n);        /* first result */
  lua_pushnumber(L, sum);         /* second result */
  return 2;                   /* number of results */
}
```

---

### `lua_checkstack`

[-0, +0, –]

```
int lua_checkstack (lua_State *L, int n);
```

Ensures that the stack has space for at least `n` extra elements, that is, that you can safely push up to `n` values into it. It returns false if it cannot fulfill the request, either because it would cause the stack to be greater than a fixed maximum size (typically at least several thousand elements) or because it cannot allocate memory for the extra space. This function never shrinks the stack; if the stack already has space for the extra elements, it is left unchanged.

---

### `lua_close`

[-0, +0, –]

```
void lua_close (lua_State *L);
```

Close all active to-be-closed variables in the main thread, release all objects in the given Lua state (calling the corresponding garbage-collection metamethods, if any), and frees all dynamic memory used by this state.

On several platforms, you may not need to call this function, because all resources are naturally released when the host program ends. On the other hand, long-running programs that create multiple states, such as daemons or web servers, will probably need to close states as soon as they are not needed.

---

### `lua_closeslot`

[-0, +0, *e*]

```
void lua_closeslot (lua_State *L, int index);
```

Close the to-be-closed slot at the given index and set its value to **nil**. The index must be the last index previously marked to be closed (see [`lua_toclose`](#lua_toclose)) that is still active (that is, not closed yet).

A `__close` metamethod cannot yield when called through this function.

(This function was introduced in release 5.4.3.)

---

### `lua_closethread`

[-0, +?, –]

```
int lua_closethread (lua_State *L, lua_State *from);
```

Resets a thread, cleaning its call stack and closing all pending to-be-closed variables. Returns a status code: [`LUA_OK`](#pdf-LUA_OK) for no errors in the thread (either the original error that stopped the thread or errors in closing methods), or an error status otherwise. In case of error, leaves the error object on the top of the stack.

The parameter `from` represents the coroutine that is resetting `L`. If there is no such coroutine, this parameter can be `NULL`.

(This function was introduced in release 5.4.6.)

---

### `lua_compare`

[-0, +0, *e*]

```
int lua_compare (lua_State *L, int index1, int index2, int op);
```

Compares two Lua values. Returns 1 if the value at index `index1` satisfies `op` when compared with the value at index `index2`, following the semantics of the corresponding Lua operator (that is, it may call metamethods). Otherwise returns 0. Also returns 0 if any of the indices is not valid.

The value of `op` must be one of the following constants:

- **`LUA_OPEQ`: ** compares for equality (`==`)

- **`LUA_OPLT`: ** compares for less than (`<`)

- **`LUA_OPLE`: ** compares for less or equal (`<=`)

---

### `lua_concat`

[-n, +1, *e*]

```
void lua_concat (lua_State *L, int n);
```

Concatenates the `n` values at the top of the stack, pops them, and leaves the result on the top. If `n` is 1, the result is the single value on the stack (that is, the function does nothing); if `n` is 0, the result is the empty string. Concatenation is performed following the usual semantics of Lua (see [§3.4.6](#3.4.6)).

---

### `lua_copy`

[-0, +0, –]

```
void lua_copy (lua_State *L, int fromidx, int toidx);
```

Copies the element at index `fromidx` into the valid index `toidx`, replacing the value at that position. Values at other positions are not affected.

---

### `lua_createtable`

[-0, +1, *m*]

```
void lua_createtable (lua_State *L, int narr, int nrec);
```

Creates a new empty table and pushes it onto the stack. Parameter `narr` is a hint for how many elements the table will have as a sequence; parameter `nrec` is a hint for how many other elements the table will have. Lua may use these hints to preallocate memory for the new table. This preallocation may help performance when you know in advance how many elements the table will have. Otherwise you can use the function [`lua_newtable`](#lua_newtable).

---

### `lua_dump`

[-0, +0, –]

```
int lua_dump (lua_State *L,
                        lua_Writer writer,
                        void *data,
                        int strip);
```

Dumps a function as a binary chunk. Receives a Lua function on the top of the stack and produces a binary chunk that, if loaded again, results in a function equivalent to the one dumped. As it produces parts of the chunk, [`lua_dump`](#lua_dump) calls function `writer` (see [`lua_Writer`](#lua_Writer)) with the given `data` to write them.

If `strip` is true, the binary representation may not include all debug information about the function, to save space.

The value returned is the error code returned by the last call to the writer; 0 means no errors.

This function does not pop the Lua function from the stack.

---

### `lua_error`

[-1, +0, *v*]

```
int lua_error (lua_State *L);
```

Raises a Lua error, using the value on the top of the stack as the error object. This function does a long jump, and therefore never returns (see [`luaL_error`](#luaL_error)).

---

### `lua_gc`

[-0, +0, –]

```
int lua_gc (lua_State *L, int what, ...);
```

Controls the garbage collector.

This function performs several tasks, according to the value of the parameter `what`. For options that need extra arguments, they are listed after the option.

- **`LUA_GCCOLLECT`: ** Performs a full garbage-collection cycle.

- **`LUA_GCSTOP`: ** Stops the garbage collector.

- **`LUA_GCRESTART`: ** Restarts the garbage collector.

- **`LUA_GCCOUNT`: ** Returns the current amount of memory (in Kbytes) in use by Lua.

- **`LUA_GCCOUNTB`: ** Returns the remainder of dividing the current amount of bytes of memory in use by Lua by 1024.

- **`LUA_GCSTEP` `(int stepsize)`: ** Performs an incremental step of garbage collection, corresponding to the allocation of `stepsize` Kbytes.

- **`LUA_GCISRUNNING`: ** Returns a boolean that tells whether the collector is running (i.e., not stopped).

- **`LUA_GCINC` (int pause, int stepmul, stepsize): ** Changes the collector to incremental mode with the given parameters (see [§2.5.1](#2.5.1)). Returns the previous mode (`LUA_GCGEN` or `LUA_GCINC`).

- **`LUA_GCGEN` (int minormul, int majormul): ** Changes the collector to generational mode with the given parameters (see [§2.5.2](#2.5.2)). Returns the previous mode (`LUA_GCGEN` or `LUA_GCINC`).

For more details about these options, see [`collectgarbage`](#pdf-collectgarbage).

This function should not be called by a finalizer.

---

### `lua_getallocf`

[-0, +0, –]

```
lua_Alloc lua_getallocf (lua_State *L, void **ud);
```

Returns the memory-allocation function of a given state. If `ud` is not `NULL`, Lua stores in `*ud` the opaque pointer given when the memory-allocator function was set.

---

### `lua_getfield`

[-0, +1, *e*]

```
int lua_getfield (lua_State *L, int index, const char *k);
```

Pushes onto the stack the value `t[k]`, where `t` is the value at the given index. As in Lua, this function may trigger a metamethod for the "index" event (see [§2.4](#2.4)).

Returns the type of the pushed value.

---

### `lua_getextraspace`

[-0, +0, –]

```
void *lua_getextraspace (lua_State *L);
```

Returns a pointer to a raw memory area associated with the given Lua state. The application can use this area for any purpose; Lua does not use it for anything.

Each new thread has this area initialized with a copy of the area of the main thread.

By default, this area has the size of a pointer to void, but you can recompile Lua with a different size for this area. (See `LUA_EXTRASPACE` in `luaconf.h`.)

---

### `lua_getglobal`

[-0, +1, *e*]

```
int lua_getglobal (lua_State *L, const char *name);
```

Pushes onto the stack the value of the global `name`. Returns the type of that value.

---

### `lua_geti`

[-0, +1, *e*]

```
int lua_geti (lua_State *L, int index, lua_Integer i);
```

Pushes onto the stack the value `t[i]`, where `t` is the value at the given index. As in Lua, this function may trigger a metamethod for the "index" event (see [§2.4](#2.4)).

Returns the type of the pushed value.

---

### `lua_getmetatable`

[-0, +(0|1), –]

```
int lua_getmetatable (lua_State *L, int index);
```

If the value at the given index has a metatable, the function pushes that metatable onto the stack and returns 1. Otherwise, the function returns 0 and pushes nothing on the stack.

---

### `lua_gettable`

[-1, +1, *e*]

```
int lua_gettable (lua_State *L, int index);
```

Pushes onto the stack the value `t[k]`, where `t` is the value at the given index and `k` is the value on the top of the stack.

This function pops the key from the stack, pushing the resulting value in its place. As in Lua, this function may trigger a metamethod for the "index" event (see [§2.4](#2.4)).

Returns the type of the pushed value.

---

### `lua_gettop`

[-0, +0, –]

```
int lua_gettop (lua_State *L);
```

Returns the index of the top element in the stack. Because indices start at 1, this result is equal to the number of elements in the stack; in particular, 0 means an empty stack.

---

### `lua_getiuservalue`

[-0, +1, –]

```
int lua_getiuservalue (lua_State *L, int index, int n);
```

Pushes onto the stack the `n`-th user value associated with the full userdata at the given index and returns the type of the pushed value.

If the userdata does not have that value, pushes **nil** and returns [`LUA_TNONE`](#pdf-LUA_TNONE).

---

### `lua_insert`

[-1, +1, –]

```
void lua_insert (lua_State *L, int index);
```

Moves the top element into the given valid index, shifting up the elements above this index to open space. This function cannot be called with a pseudo-index, because a pseudo-index is not an actual stack position.

---

### `lua_Integer`

```
typedef ... lua_Integer;
```

The type of integers in Lua.

By default this type is `long long`, (usually a 64-bit two-complement integer), but that can be changed to `long` or `int` (usually a 32-bit two-complement integer). (See `LUA_INT_TYPE` in `luaconf.h`.)

Lua also defines the constants `LUA_MININTEGER` and `LUA_MAXINTEGER`, with the minimum and the maximum values that fit in this type.

---

### `lua_isboolean`

[-0, +0, –]

```
int lua_isboolean (lua_State *L, int index);
```

Returns 1 if the value at the given index is a boolean, and 0 otherwise.

---

### `lua_iscfunction`

[-0, +0, –]

```
int lua_iscfunction (lua_State *L, int index);
```

Returns 1 if the value at the given index is a C function, and 0 otherwise.

---

### `lua_isfunction`

[-0, +0, –]

```
int lua_isfunction (lua_State *L, int index);
```

Returns 1 if the value at the given index is a function (either C or Lua), and 0 otherwise.

---

### `lua_isinteger`

[-0, +0, –]

```
int lua_isinteger (lua_State *L, int index);
```

Returns 1 if the value at the given index is an integer (that is, the value is a number and is represented as an integer), and 0 otherwise.

---

### `lua_islightuserdata`

[-0, +0, –]

```
int lua_islightuserdata (lua_State *L, int index);
```

Returns 1 if the value at the given index is a light userdata, and 0 otherwise.

---

### `lua_isnil`

[-0, +0, –]

```
int lua_isnil (lua_State *L, int index);
```

Returns 1 if the value at the given index is **nil**, and 0 otherwise.

---

### `lua_isnone`

[-0, +0, –]

```
int lua_isnone (lua_State *L, int index);
```

Returns 1 if the given index is not valid, and 0 otherwise.

---

### `lua_isnoneornil`

[-0, +0, –]

```
int lua_isnoneornil (lua_State *L, int index);
```

Returns 1 if the given index is not valid or if the value at this index is **nil**, and 0 otherwise.

---

### `lua_isnumber`

[-0, +0, –]

```
int lua_isnumber (lua_State *L, int index);
```

Returns 1 if the value at the given index is a number or a string convertible to a number, and 0 otherwise.

---

### `lua_isstring`

[-0, +0, –]

```
int lua_isstring (lua_State *L, int index);
```

Returns 1 if the value at the given index is a string or a number (which is always convertible to a string), and 0 otherwise.

---

### `lua_istable`

[-0, +0, –]

```
int lua_istable (lua_State *L, int index);
```

Returns 1 if the value at the given index is a table, and 0 otherwise.

---

### `lua_isthread`

[-0, +0, –]

```
int lua_isthread (lua_State *L, int index);
```

Returns 1 if the value at the given index is a thread, and 0 otherwise.

---

### `lua_isuserdata`

[-0, +0, –]

```
int lua_isuserdata (lua_State *L, int index);
```

Returns 1 if the value at the given index is a userdata (either full or light), and 0 otherwise.

---

### `lua_isyieldable`

[-0, +0, –]

```
int lua_isyieldable (lua_State *L);
```

Returns 1 if the given coroutine can yield, and 0 otherwise.

---

### `lua_KContext`

```
typedef ... lua_KContext;
```

The type for continuation-function contexts. It must be a numeric type. This type is defined as `intptr_t` when `intptr_t` is available, so that it can store pointers too. Otherwise, it is defined as `ptrdiff_t`.

---

### `lua_KFunction`

```
typedef int (*lua_KFunction) (lua_State *L, int status, lua_KContext ctx);
```

Type for continuation functions (see [§4.5](#4.5)).

---

### `lua_len`

[-0, +1, *e*]

```
void lua_len (lua_State *L, int index);
```

Returns the length of the value at the given index. It is equivalent to the '`#`' operator in Lua (see [§3.4.7](#3.4.7)) and may trigger a metamethod for the "length" event (see [§2.4](#2.4)). The result is pushed on the stack.

---

### `lua_load`

[-0, +1, –]

```
int lua_load (lua_State *L,
              lua_Reader reader,
              void *data,
              const char *chunkname,
              const char *mode);
```

Loads a Lua chunk without running it. If there are no errors, `lua_load` pushes the compiled chunk as a Lua function on top of the stack. Otherwise, it pushes an error message.

The `lua_load` function uses a user-supplied `reader` function to read the chunk (see [`lua_Reader`](#lua_Reader)). The `data` argument is an opaque value passed to the reader function.

The `chunkname` argument gives a name to the chunk, which is used for error messages and in debug information (see [§4.7](#4.7)).

`lua_load` automatically detects whether the chunk is text or binary and loads it accordingly (see program `luac`). The string `mode` works as in function [`load`](#pdf-load), with the addition that a `NULL` value is equivalent to the string "`bt`".

`lua_load` uses the stack internally, so the reader function must always leave the stack unmodified when returning.

`lua_load` can return [`LUA_OK`](#pdf-LUA_OK), [`LUA_ERRSYNTAX`](#pdf-LUA_ERRSYNTAX), or [`LUA_ERRMEM`](#pdf-LUA_ERRMEM). The function may also return other values corresponding to errors raised by the read function (see [§4.4.1](#4.4.1)).

If the resulting function has upvalues, its first upvalue is set to the value of the global environment stored at index `LUA_RIDX_GLOBALS` in the registry (see [§4.3](#4.3)). When loading main chunks, this upvalue will be the `_ENV` variable (see [§2.2](#2.2)). Other upvalues are initialized with **nil**.

---

### `lua_newstate`

[-0, +0, –]

```
lua_State *lua_newstate (lua_Alloc f, void *ud);
```

Creates a new independent state and returns its main thread. Returns `NULL` if it cannot create the state (due to lack of memory). The argument `f` is the allocator function; Lua will do all memory allocation for this state through this function (see [`lua_Alloc`](#lua_Alloc)). The second argument, `ud`, is an opaque pointer that Lua passes to the allocator in every call.

---

### `lua_newtable`

[-0, +1, *m*]

```
void lua_newtable (lua_State *L);
```

Creates a new empty table and pushes it onto the stack. It is equivalent to `lua_createtable(L, 0, 0)`.

---

### `lua_newthread`

[-0, +1, *m*]

```
lua_State *lua_newthread (lua_State *L);
```

Creates a new thread, pushes it on the stack, and returns a pointer to a [`lua_State`](#lua_State) that represents this new thread. The new thread returned by this function shares with the original thread its global environment, but has an independent execution stack.

Threads are subject to garbage collection, like any Lua object.

---

### `lua_newuserdatauv`

[-0, +1, *m*]

```
void *lua_newuserdatauv (lua_State *L, size_t size, int nuvalue);
```

This function creates and pushes on the stack a new full userdata, with `nuvalue` associated Lua values, called `user values`, plus an associated block of raw memory with `size` bytes. (The user values can be set and read with the functions [`lua_setiuservalue`](#lua_setiuservalue) and [`lua_getiuservalue`](#lua_getiuservalue).)

The function returns the address of the block of memory. Lua ensures that this address is valid as long as the corresponding userdata is alive (see [§2.5](#2.5)). Moreover, if the userdata is marked for finalization (see [§2.5.3](#2.5.3)), its address is valid at least until the call to its finalizer.

---

### `lua_next`

[-1, +(2|0), *v*]

```
int lua_next (lua_State *L, int index);
```

Pops a key from the stack, and pushes a key–value pair from the table at the given index, the "next" pair after the given key. If there are no more elements in the table, then [`lua_next`](#lua_next) returns 0 and pushes nothing.

A typical table traversal looks like this:

```
/* table is in the stack at index 't' */
lua_pushnil(L);  /* first key */
while (lua_next(L, t) != 0) {
  /* uses 'key' (at index -2) and 'value' (at index -1) */
  printf("%s - %s\n",
         lua_typename(L, lua_type(L, -2)),
         lua_typename(L, lua_type(L, -1)));
  /* removes 'value'; keeps 'key' for next iteration */
  lua_pop(L, 1);
}
```

While traversing a table, avoid calling [`lua_tolstring`](#lua_tolstring) directly on a key, unless you know that the key is actually a string. Recall that [`lua_tolstring`](#lua_tolstring) may change the value at the given index; this confuses the next call to [`lua_next`](#lua_next).

This function may raise an error if the given key is neither **nil** nor present in the table. See function [`next`](#pdf-next) for the caveats of modifying the table during its traversal.

---

### `lua_Number`

```
typedef ... lua_Number;
```

The type of floats in Lua.

By default this type is double, but that can be changed to a single float or a long double. (See `LUA_FLOAT_TYPE` in `luaconf.h`.)

---

### `lua_numbertointeger`

```
int lua_numbertointeger (lua_Number n, lua_Integer *p);
```

Tries to convert a Lua float to a Lua integer; the float `n` must have an integral value. If that value is within the range of Lua integers, it is converted to an integer and assigned to `*p`. The macro results in a boolean indicating whether the conversion was successful. (Note that this range test can be tricky to do correctly without this macro, due to rounding.)

This macro may evaluate its arguments more than once.

---

### `lua_pcall`

[-(nargs + 1), +(nresults|1), –]

```
int lua_pcall (lua_State *L, int nargs, int nresults, int msgh);
```

Calls a function (or a callable object) in protected mode.

Both `nargs` and `nresults` have the same meaning as in [`lua_call`](#lua_call). If there are no errors during the call, [`lua_pcall`](#lua_pcall) behaves exactly like [`lua_call`](#lua_call). However, if there is any error, [`lua_pcall`](#lua_pcall) catches it, pushes a single value on the stack (the error object), and returns an error code. Like [`lua_call`](#lua_call), [`lua_pcall`](#lua_pcall) always removes the function and its arguments from the stack.

If `msgh` is 0, then the error object returned on the stack is exactly the original error object. Otherwise, `msgh` is the stack index of a *message handler*. (This index cannot be a pseudo-index.) In case of runtime errors, this handler will be called with the error object and its return value will be the object returned on the stack by [`lua_pcall`](#lua_pcall).

Typically, the message handler is used to add more debug information to the error object, such as a stack traceback. Such information cannot be gathered after the return of [`lua_pcall`](#lua_pcall), since by then the stack has unwound.

The [`lua_pcall`](#lua_pcall) function returns one of the following status codes: [`LUA_OK`](#pdf-LUA_OK), [`LUA_ERRRUN`](#pdf-LUA_ERRRUN), [`LUA_ERRMEM`](#pdf-LUA_ERRMEM), or [`LUA_ERRERR`](#pdf-LUA_ERRERR).

---

### `lua_pcallk`

[-(nargs + 1), +(nresults|1), –]

```
int lua_pcallk (lua_State *L,
                int nargs,
                int nresults,
                int msgh,
                lua_KContext ctx,
                lua_KFunction k);
```

This function behaves exactly like [`lua_pcall`](#lua_pcall), except that it allows the called function to yield (see [§4.5](#4.5)).

---

### `lua_pop`

[-n, +0, *e*]

```
void lua_pop (lua_State *L, int n);
```

Pops `n` elements from the stack. It is implemented as a macro over [`lua_settop`](#lua_settop).

---

### `lua_pushboolean`

[-0, +1, –]

```
void lua_pushboolean (lua_State *L, int b);
```

Pushes a boolean value with value `b` onto the stack.

---

### `lua_pushcclosure`

[-n, +1, *m*]

```
void lua_pushcclosure (lua_State *L, lua_CFunction fn, int n);
```

Pushes a new C closure onto the stack. This function receives a pointer to a C function and pushes onto the stack a Lua value of type `function` that, when called, invokes the corresponding C function. The parameter `n` tells how many upvalues this function will have (see [§4.2](#4.2)).

Any function to be callable by Lua must follow the correct protocol to receive its parameters and return its results (see [`lua_CFunction`](#lua_CFunction)).

When a C function is created, it is possible to associate some values with it, the so called upvalues; these upvalues are then accessible to the function whenever it is called. This association is called a C closure (see [§4.2](#4.2)). To create a C closure, first the initial values for its upvalues must be pushed onto the stack. (When there are multiple upvalues, the first value is pushed first.) Then [`lua_pushcclosure`](#lua_pushcclosure) is called to create and push the C function onto the stack, with the argument `n` telling how many values will be associated with the function. [`lua_pushcclosure`](#lua_pushcclosure) also pops these values from the stack.

The maximum value for `n` is 255.

When `n` is zero, this function creates a *light C function*, which is just a pointer to the C function. In that case, it never raises a memory error.

---

### `lua_pushcfunction`

[-0, +1, –]

```
void lua_pushcfunction (lua_State *L, lua_CFunction f);
```

Pushes a C function onto the stack. This function is equivalent to [`lua_pushcclosure`](#lua_pushcclosure) with no upvalues.

---

### `lua_pushfstring`

[-0, +1, *v*]

```
const char *lua_pushfstring (lua_State *L, const char *fmt, ...);
```

Pushes onto the stack a formatted string and returns a pointer to this string (see [§4.1.3](#4.1.3)). It is similar to the ISO C function `sprintf`, but has two important differences. First, you do not have to allocate space for the result; the result is a Lua string and Lua takes care of memory allocation (and deallocation, through garbage collection). Second, the conversion specifiers are quite restricted. There are no flags, widths, or precisions. The conversion specifiers can only be '`%%`' (inserts the character '`%`'), '`%s`' (inserts a zero-terminated string, with no size restrictions), '`%f`' (inserts a [`lua_Number`](#lua_Number)), '`%I`' (inserts a [`lua_Integer`](#lua_Integer)), '`%p`' (inserts a pointer), '`%d`' (inserts an `int`), '`%c`' (inserts an `int` as a one-byte character), and '`%U`' (inserts a `long int` as a UTF-8 byte sequence).

This function may raise errors due to memory overflow or an invalid conversion specifier.

---

### `lua_pushglobaltable`

[-0, +1, –]

```
void lua_pushglobaltable (lua_State *L);
```

Pushes the global environment onto the stack.

---

### `lua_pushinteger`

[-0, +1, –]

```
void lua_pushinteger (lua_State *L, lua_Integer n);
```

Pushes an integer with value `n` onto the stack.

---

### `lua_pushlightuserdata`

[-0, +1, –]

```
void lua_pushlightuserdata (lua_State *L, void *p);
```

Pushes a light userdata onto the stack.

Userdata represent C values in Lua. A *light userdata* represents a pointer, a `void*`. It is a value (like a number): you do not create it, it has no individual metatable, and it is not collected (as it was never created). A light userdata is equal to "any" light userdata with the same C address.

---

### `lua_pushliteral`

[-0, +1, *m*]

```
const char *lua_pushliteral (lua_State *L, const char *s);
```

This macro is equivalent to [`lua_pushstring`](#lua_pushstring), but should be used only when `s` is a literal string. (Lua may optimize this case.)

---

### `lua_pushlstring`

[-0, +1, *m*]

```
const char *lua_pushlstring (lua_State *L, const char *s, size_t len);
```

Pushes the string pointed to by `s` with size `len` onto the stack. Lua will make or reuse an internal copy of the given string, so the memory at `s` can be freed or reused immediately after the function returns. The string can contain any binary data, including embedded zeros.

Returns a pointer to the internal copy of the string (see [§4.1.3](#4.1.3)).

---

### `lua_pushnil`

[-0, +1, –]

```
void lua_pushnil (lua_State *L);
```

Pushes a nil value onto the stack.

---

### `lua_pushnumber`

[-0, +1, –]

```
void lua_pushnumber (lua_State *L, lua_Number n);
```

Pushes a float with value `n` onto the stack.

---

### `lua_pushstring`

[-0, +1, *m*]

```
const char *lua_pushstring (lua_State *L, const char *s);
```

Pushes the zero-terminated string pointed to by `s` onto the stack. Lua will make or reuse an internal copy of the given string, so the memory at `s` can be freed or reused immediately after the function returns.

Returns a pointer to the internal copy of the string (see [§4.1.3](#4.1.3)).

If `s` is `NULL`, pushes **nil** and returns `NULL`.

---

### `lua_pushthread`

[-0, +1, –]

```
int lua_pushthread (lua_State *L);
```

Pushes the thread represented by `L` onto the stack. Returns 1 if this thread is the main thread of its state.

---

### `lua_pushvalue`

[-0, +1, –]

```
void lua_pushvalue (lua_State *L, int index);
```

Pushes a copy of the element at the given index onto the stack.

---

### `lua_pushvfstring`

[-0, +1, *v*]

```
const char *lua_pushvfstring (lua_State *L,
                              const char *fmt,
                              va_list argp);
```

Equivalent to [`lua_pushfstring`](#lua_pushfstring), except that it receives a `va_list` instead of a variable number of arguments.

---

### `lua_rawequal`

[-0, +0, –]

```
int lua_rawequal (lua_State *L, int index1, int index2);
```

Returns 1 if the two values in indices `index1` and `index2` are primitively equal (that is, equal without calling the `__eq` metamethod). Otherwise returns 0. Also returns 0 if any of the indices are not valid.

---

### `lua_rawget`

[-1, +1, –]

```
int lua_rawget (lua_State *L, int index);
```

Similar to [`lua_gettable`](#lua_gettable), but does a raw access (i.e., without metamethods). The value at `index` must be a table.

---

### `lua_rawgeti`

[-0, +1, –]

```
int lua_rawgeti (lua_State *L, int index, lua_Integer n);
```

Pushes onto the stack the value `t[n]`, where `t` is the table at the given index. The access is raw, that is, it does not use the `__index` metavalue.

Returns the type of the pushed value.

---

### `lua_rawgetp`

[-0, +1, –]

```
int lua_rawgetp (lua_State *L, int index, const void *p);
```

Pushes onto the stack the value `t[k]`, where `t` is the table at the given index and `k` is the pointer `p` represented as a light userdata. The access is raw; that is, it does not use the `__index` metavalue.

Returns the type of the pushed value.

---

### `lua_rawlen`

[-0, +0, –]

```
lua_Unsigned lua_rawlen (lua_State *L, int index);
```

Returns the raw "length" of the value at the given index: for strings, this is the string length; for tables, this is the result of the length operator ('`#`') with no metamethods; for userdata, this is the size of the block of memory allocated for the userdata. For other values, this call returns 0.

---

### `lua_rawset`

[-2, +0, *m*]

```
void lua_rawset (lua_State *L, int index);
```

Similar to [`lua_settable`](#lua_settable), but does a raw assignment (i.e., without metamethods). The value at `index` must be a table.

---

### `lua_rawseti`

[-1, +0, *m*]

```
void lua_rawseti (lua_State *L, int index, lua_Integer i);
```

Does the equivalent of `t[i] = v`, where `t` is the table at the given index and `v` is the value on the top of the stack.

This function pops the value from the stack. The assignment is raw, that is, it does not use the `__newindex` metavalue.

---

### `lua_rawsetp`

[-1, +0, *m*]

```
void lua_rawsetp (lua_State *L, int index, const void *p);
```

Does the equivalent of `t[p] = v`, where `t` is the table at the given index, `p` is encoded as a light userdata, and `v` is the value on the top of the stack.

This function pops the value from the stack. The assignment is raw, that is, it does not use the `__newindex` metavalue.

---

### `lua_Reader`

```
typedef const char * (*lua_Reader) (lua_State *L,
                                    void *data,
                                    size_t *size);
```

The reader function used by [`lua_load`](#lua_load). Every time [`lua_load`](#lua_load) needs another piece of the chunk, it calls the reader, passing along its `data` parameter. The reader must return a pointer to a block of memory with a new piece of the chunk and set `size` to the block size. The block must exist until the reader function is called again. To signal the end of the chunk, the reader must return `NULL` or set `size` to zero. The reader function may return pieces of any size greater than zero.

---

### `lua_register`

[-0, +0, *e*]

```
void lua_register (lua_State *L, const char *name, lua_CFunction f);
```

Sets the C function `f` as the new value of global `name`. It is defined as a macro:

```
#define lua_register(L,n,f) \
       (lua_pushcfunction(L, f), lua_setglobal(L, n))
```

---

### `lua_remove`

[-1, +0, –]

```
void lua_remove (lua_State *L, int index);
```

Removes the element at the given valid index, shifting down the elements above this index to fill the gap. This function cannot be called with a pseudo-index, because a pseudo-index is not an actual stack position.

---

### `lua_replace`

[-1, +0, –]

```
void lua_replace (lua_State *L, int index);
```

Moves the top element into the given valid index without shifting any element (therefore replacing the value at that given index), and then pops the top element.

---

### `lua_resetthread`

[-0, +?, –]

```
int lua_resetthread (lua_State *L);
```

This function is deprecated; it is equivalent to [`lua_closethread`](#lua_closethread) with `from` being `NULL`.

---

### `lua_resume`

[-?, +?, –]

```
int lua_resume (lua_State *L, lua_State *from, int nargs,
                          int *nresults);
```

Starts and resumes a coroutine in the given thread `L`.

To start a coroutine, you push the main function plus any arguments onto the empty stack of the thread. then you call [`lua_resume`](#lua_resume), with `nargs` being the number of arguments. This call returns when the coroutine suspends or finishes its execution. When it returns, `*nresults` is updated and the top of the stack contains the `*nresults` values passed to [`lua_yield`](#lua_yield) or returned by the body function. [`lua_resume`](#lua_resume) returns [`LUA_YIELD`](#pdf-LUA_YIELD) if the coroutine yields, [`LUA_OK`](#pdf-LUA_OK) if the coroutine finishes its execution without errors, or an error code in case of errors (see [§4.4.1](#4.4.1)). In case of errors, the error object is on the top of the stack.

To resume a coroutine, you remove the `*nresults` yielded values from its stack, push the values to be passed as results from `yield`, and then call [`lua_resume`](#lua_resume).

The parameter `from` represents the coroutine that is resuming `L`. If there is no such coroutine, this parameter can be `NULL`.

---

### `lua_rotate`

[-0, +0, –]

```
void lua_rotate (lua_State *L, int idx, int n);
```

Rotates the stack elements between the valid index `idx` and the top of the stack. The elements are rotated `n` positions in the direction of the top, for a positive `n`, or `-n` positions in the direction of the bottom, for a negative `n`. The absolute value of `n` must not be greater than the size of the slice being rotated. This function cannot be called with a pseudo-index, because a pseudo-index is not an actual stack position.

---

### `lua_setallocf`

[-0, +0, –]

```
void lua_setallocf (lua_State *L, lua_Alloc f, void *ud);
```

Changes the allocator function of a given state to `f` with user data `ud`.

---

### `lua_setfield`

[-1, +0, *e*]

```
void lua_setfield (lua_State *L, int index, const char *k);
```

Does the equivalent to `t[k] = v`, where `t` is the value at the given index and `v` is the value on the top of the stack.

This function pops the value from the stack. As in Lua, this function may trigger a metamethod for the "newindex" event (see [§2.4](#2.4)).

---

### `lua_setglobal`

[-1, +0, *e*]

```
void lua_setglobal (lua_State *L, const char *name);
```

Pops a value from the stack and sets it as the new value of global `name`.

---

### `lua_seti`

[-1, +0, *e*]

```
void lua_seti (lua_State *L, int index, lua_Integer n);
```

Does the equivalent to `t[n] = v`, where `t` is the value at the given index and `v` is the value on the top of the stack.

This function pops the value from the stack. As in Lua, this function may trigger a metamethod for the "newindex" event (see [§2.4](#2.4)).

---

### `lua_setiuservalue`

[-1, +0, –]

```
int lua_setiuservalue (lua_State *L, int index, int n);
```

Pops a value from the stack and sets it as the new `n`-th user value associated to the full userdata at the given index. Returns 0 if the userdata does not have that value.

---

### `lua_setmetatable`

[-1, +0, –]

```
int lua_setmetatable (lua_State *L, int index);
```

Pops a table or **nil** from the stack and sets that value as the new metatable for the value at the given index. (**nil** means no metatable.)

(For historical reasons, this function returns an `int`, which now is always 1.)

---

### `lua_settable`

[-2, +0, *e*]

```
void lua_settable (lua_State *L, int index);
```

Does the equivalent to `t[k] = v`, where `t` is the value at the given index, `v` is the value on the top of the stack, and `k` is the value just below the top.

This function pops both the key and the value from the stack. As in Lua, this function may trigger a metamethod for the "newindex" event (see [§2.4](#2.4)).

---

### `lua_settop`

[-?, +?, *e*]

```
void lua_settop (lua_State *L, int index);
```

Accepts any index, or 0, and sets the stack top to this index. If the new top is greater than the old one, then the new elements are filled with **nil**. If `index` is 0, then all stack elements are removed.

This function can run arbitrary code when removing an index marked as to-be-closed from the stack.

---

### `lua_setwarnf`

[-0, +0, –]

```
void lua_setwarnf (lua_State *L, lua_WarnFunction f, void *ud);
```

Sets the warning function to be used by Lua to emit warnings (see [`lua_WarnFunction`](#lua_WarnFunction)). The `ud` parameter sets the value `ud` passed to the warning function.

---

### `lua_State`

```
typedef struct lua_State lua_State;
```

An opaque structure that points to a thread and indirectly (through the thread) to the whole state of a Lua interpreter. The Lua library is fully reentrant: it has no global variables. All information about a state is accessible through this structure.

A pointer to this structure must be passed as the first argument to every function in the library, except to [`lua_newstate`](#lua_newstate), which creates a Lua state from scratch.

---

### `lua_status`

[-0, +0, –]

```
int lua_status (lua_State *L);
```

Returns the status of the thread `L`.

The status can be [`LUA_OK`](#pdf-LUA_OK) for a normal thread, an error code if the thread finished the execution of a [`lua_resume`](#lua_resume) with an error, or [`LUA_YIELD`](#pdf-LUA_YIELD) if the thread is suspended.

You can call functions only in threads with status [`LUA_OK`](#pdf-LUA_OK). You can resume threads with status [`LUA_OK`](#pdf-LUA_OK) (to start a new coroutine) or [`LUA_YIELD`](#pdf-LUA_YIELD) (to resume a coroutine).

---

### `lua_stringtonumber`

[-0, +1, –]

```
size_t lua_stringtonumber (lua_State *L, const char *s);
```

Converts the zero-terminated string `s` to a number, pushes that number into the stack, and returns the total size of the string, that is, its length plus one. The conversion can result in an integer or a float, according to the lexical conventions of Lua (see [§3.1](#3.1)). The string may have leading and trailing whitespaces and a sign. If the string is not a valid numeral, returns 0 and pushes nothing. (Note that the result can be used as a boolean, true if the conversion succeeds.)

---

### `lua_toboolean`

[-0, +0, –]

```
int lua_toboolean (lua_State *L, int index);
```

Converts the Lua value at the given index to a C boolean value (0 or 1). Like all tests in Lua, [`lua_toboolean`](#lua_toboolean) returns true for any Lua value different from **false** and **nil**; otherwise it returns false. (If you want to accept only actual boolean values, use [`lua_isboolean`](#lua_isboolean) to test the value's type.)

---

### `lua_tocfunction`

[-0, +0, –]

```
lua_CFunction lua_tocfunction (lua_State *L, int index);
```

Converts a value at the given index to a C function. That value must be a C function; otherwise, returns `NULL`.

---

### `lua_toclose`

[-0, +0, *v*]

```
void lua_toclose (lua_State *L, int index);
```

Marks the given index in the stack as a to-be-closed slot (see [§3.3.8](#3.3.8)). Like a to-be-closed variable in Lua, the value at that slot in the stack will be closed when it goes out of scope. Here, in the context of a C function, to go out of scope means that the running function returns to Lua, or there is an error, or the slot is removed from the stack through [`lua_settop`](#lua_settop) or [`lua_pop`](#lua_pop), or there is a call to [`lua_closeslot`](#lua_closeslot). A slot marked as to-be-closed should not be removed from the stack by any other function in the API except [`lua_settop`](#lua_settop) or [`lua_pop`](#lua_pop), unless previously deactivated by [`lua_closeslot`](#lua_closeslot).

This function raises an error if the value at the given slot neither has a `__close` metamethod nor is a false value.

This function should not be called for an index that is equal to or below an active to-be-closed slot.

Note that, both in case of errors and of a regular return, by the time the `__close` metamethod runs, the C stack was already unwound, so that any automatic C variable declared in the calling function (e.g., a buffer) will be out of scope.

---

### `lua_tointeger`

[-0, +0, –]

```
lua_Integer lua_tointeger (lua_State *L, int index);
```

Equivalent to [`lua_tointegerx`](#lua_tointegerx) with `isnum` equal to `NULL`.

---

### `lua_tointegerx`

[-0, +0, –]

```
lua_Integer lua_tointegerx (lua_State *L, int index, int *isnum);
```

Converts the Lua value at the given index to the signed integral type [`lua_Integer`](#lua_Integer). The Lua value must be an integer, or a number or string convertible to an integer (see [§3.4.3](#3.4.3)); otherwise, `lua_tointegerx` returns 0.

If `isnum` is not `NULL`, its referent is assigned a boolean value that indicates whether the operation succeeded.

---

### `lua_tolstring`

[-0, +0, *m*]

```
const char *lua_tolstring (lua_State *L, int index, size_t *len);
```

Converts the Lua value at the given index to a C string. If `len` is not `NULL`, it sets `*len` with the string length. The Lua value must be a string or a number; otherwise, the function returns `NULL`. If the value is a number, then `lua_tolstring` also *changes the actual value in the stack to a string*. (This change confuses [`lua_next`](#lua_next) when `lua_tolstring` is applied to keys during a table traversal.)

`lua_tolstring` returns a pointer to a string inside the Lua state (see [§4.1.3](#4.1.3)). This string always has a zero ('`\0`') after its last character (as in C), but can contain other zeros in its body.

This function can raise memory errors only when converting a number to a string (as then it may create a new string).

---

### `lua_tonumber`

[-0, +0, –]

```
lua_Number lua_tonumber (lua_State *L, int index);
```

Equivalent to [`lua_tonumberx`](#lua_tonumberx) with `isnum` equal to `NULL`.

---

### `lua_tonumberx`

[-0, +0, –]

```
lua_Number lua_tonumberx (lua_State *L, int index, int *isnum);
```

Converts the Lua value at the given index to the C type [`lua_Number`](#lua_Number) (see [`lua_Number`](#lua_Number)). The Lua value must be a number or a string convertible to a number (see [§3.4.3](#3.4.3)); otherwise, [`lua_tonumberx`](#lua_tonumberx) returns 0.

If `isnum` is not `NULL`, its referent is assigned a boolean value that indicates whether the operation succeeded.

---

### `lua_topointer`

[-0, +0, –]

```
const void *lua_topointer (lua_State *L, int index);
```

Converts the value at the given index to a generic C pointer (`void*`). The value can be a userdata, a table, a thread, a string, or a function; otherwise, `lua_topointer` returns `NULL`. Different objects will give different pointers. There is no way to convert the pointer back to its original value.

Typically this function is used only for hashing and debug information.

---

### `lua_tostring`

[-0, +0, *m*]

```
const char *lua_tostring (lua_State *L, int index);
```

Equivalent to [`lua_tolstring`](#lua_tolstring) with `len` equal to `NULL`.

---

### `lua_tothread`

[-0, +0, –]

```
lua_State *lua_tothread (lua_State *L, int index);
```

Converts the value at the given index to a Lua thread (represented as `lua_State*`). This value must be a thread; otherwise, the function returns `NULL`.

---

### `lua_touserdata`

[-0, +0, –]

```
void *lua_touserdata (lua_State *L, int index);
```

If the value at the given index is a full userdata, returns its memory-block address. If the value is a light userdata, returns its value (a pointer). Otherwise, returns `NULL`.

---

### `lua_type`

[-0, +0, –]

```
int lua_type (lua_State *L, int index);
```

Returns the type of the value in the given valid index, or `LUA_TNONE` for a non-valid but acceptable index. The types returned by [`lua_type`](#lua_type) are coded by the following constants defined in `lua.h`: `LUA_TNIL`, `LUA_TNUMBER`, `LUA_TBOOLEAN`, `LUA_TSTRING`, `LUA_TTABLE`, `LUA_TFUNCTION`, `LUA_TUSERDATA`, `LUA_TTHREAD`, and `LUA_TLIGHTUSERDATA`.

---

### `lua_typename`

[-0, +0, –]

```
const char *lua_typename (lua_State *L, int tp);
```

Returns the name of the type encoded by the value `tp`, which must be one the values returned by [`lua_type`](#lua_type).

---

### `lua_Unsigned`

```
typedef ... lua_Unsigned;
```

The unsigned version of [`lua_Integer`](#lua_Integer).

---

### `lua_upvalueindex`

[-0, +0, –]

```
int lua_upvalueindex (int i);
```

Returns the pseudo-index that represents the `i`-th upvalue of the running function (see [§4.2](#4.2)). `i` must be in the range *[1,256]*.

---

### `lua_version`

[-0, +0, –]

```
lua_Number lua_version (lua_State *L);
```

Returns the version number of this core.

---

### `lua_WarnFunction`

```
typedef void (*lua_WarnFunction) (void *ud, const char *msg, int tocont);
```

The type of warning functions, called by Lua to emit warnings. The first parameter is an opaque pointer set by [`lua_setwarnf`](#lua_setwarnf). The second parameter is the warning message. The third parameter is a boolean that indicates whether the message is to be continued by the message in the next call.

See [`warn`](#pdf-warn) for more details about warnings.

---

### `lua_warning`

[-0, +0, –]

```
void lua_warning (lua_State *L, const char *msg, int tocont);
```

Emits a warning with the given message. A message in a call with `tocont` true should be continued in another call to this function.

See [`warn`](#pdf-warn) for more details about warnings.

---

### `lua_Writer`

```
typedef int (*lua_Writer) (lua_State *L,
                           const void* p,
                           size_t sz,
                           void* ud);
```

The type of the writer function used by [`lua_dump`](#lua_dump). Every time [`lua_dump`](#lua_dump) produces another piece of chunk, it calls the writer, passing along the buffer to be written (`p`), its size (`sz`), and the `ud` parameter supplied to [`lua_dump`](#lua_dump).

The writer returns an error code: 0 means no errors; any other value means an error and stops [`lua_dump`](#lua_dump) from calling the writer again.

---

### `lua_xmove`

[-?, +?, –]

```
void lua_xmove (lua_State *from, lua_State *to, int n);
```

Exchange values between different threads of the same state.

This function pops `n` values from the stack `from`, and pushes them onto the stack `to`.

---

### `lua_yield`

[-?, +?, *v*]

```
int lua_yield (lua_State *L, int nresults);
```

This function is equivalent to [`lua_yieldk`](#lua_yieldk), but it has no continuation (see [§4.5](#4.5)). Therefore, when the thread resumes, it continues the function that called the function calling `lua_yield`. To avoid surprises, this function should be called only in a tail call.

---

### `lua_yieldk`

[-?, +?, *v*]

```
int lua_yieldk (lua_State *L,
                int nresults,
                lua_KContext ctx,
                lua_KFunction k);
```

Yields a coroutine (thread).

When a C function calls [`lua_yieldk`](#lua_yieldk), the running coroutine suspends its execution, and the call to [`lua_resume`](#lua_resume) that started this coroutine returns. The parameter `nresults` is the number of values from the stack that will be passed as results to [`lua_resume`](#lua_resume).

When the coroutine is resumed again, Lua calls the given continuation function `k` to continue the execution of the C function that yielded (see [§4.5](#4.5)). This continuation function receives the same stack from the previous function, with the `n` results removed and replaced by the arguments passed to [`lua_resume`](#lua_resume). Moreover, the continuation function receives the value `ctx` that was passed to [`lua_yieldk`](#lua_yieldk).

Usually, this function does not return; when the coroutine eventually resumes, it continues executing the continuation function. However, there is one special case, which is when this function is called from inside a line or a count hook (see [§4.7](#4.7)). In that case, `lua_yieldk` should be called with no continuation (probably in the form of [`lua_yield`](#lua_yield)) and no results, and the hook should return immediately after the call. Lua will yield and, when the coroutine resumes again, it will continue the normal execution of the (Lua) function that triggered the hook.

This function can raise an error if it is called from a thread with a pending C call with no continuation function (what is called a *C-call boundary*), or it is called from a thread that is not running inside a resume (typically the main thread).

## 4.7 – The Debug Interface

Lua has no built-in debugging facilities. Instead, it offers a special interface by means of functions and *hooks*. This interface allows the construction of different kinds of debuggers, profilers, and other tools that need "inside information" from the interpreter.

---

### `lua_Debug`

```
typedef struct lua_Debug {
  int event;
  const char *name;           /* (n) */
  const char *namewhat;       /* (n) */
  const char *what;           /* (S) */
  const char *source;         /* (S) */
  size_t srclen;              /* (S) */
  int currentline;            /* (l) */
  int linedefined;            /* (S) */
  int lastlinedefined;        /* (S) */
  unsigned char nups;         /* (u) number of upvalues */
  unsigned char nparams;      /* (u) number of parameters */
  char isvararg;              /* (u) */
  char istailcall;            /* (t) */
  unsigned short ftransfer;   /* (r) index of first value transferred */
  unsigned short ntransfer;   /* (r) number of transferred values */
  char short_src[LUA_IDSIZE]; /* (S) */
  /* private part */
  other fields
} lua_Debug;
```

A structure used to carry different pieces of information about a function or an activation record. [`lua_getstack`](#lua_getstack) fills only the private part of this structure, for later use. To fill the other fields of [`lua_Debug`](#lua_Debug) with useful information, you must call [`lua_getinfo`](#lua_getinfo) with an appropriate parameter. (Specifically, to get a field, you must add the letter between parentheses in the field's comment to the parameter `what` of [`lua_getinfo`](#lua_getinfo).)

The fields of [`lua_Debug`](#lua_Debug) have the following meaning:

- **`source`: ** the source of the chunk that created the function. If `source` starts with a '`@`', it means that the function was defined in a file where the file name follows the '`@`'. If `source` starts with a '`=`', the remainder of its contents describes the source in a user-dependent manner. Otherwise, the function was defined in a string where `source` is that string.

- **`srclen`: ** The length of the string `source`.

- **`short_src`: ** a "printable" version of `source`, to be used in error messages.

- **`linedefined`: ** the line number where the definition of the function starts.

- **`lastlinedefined`: ** the line number where the definition of the function ends.

- **`what`: ** the string `"Lua"` if the function is a Lua function, `"C"` if it is a C function, `"main"` if it is the main part of a chunk.

- **`currentline`: ** the current line where the given function is executing. When no line information is available, `currentline` is set to -1.

- **`name`: ** a reasonable name for the given function. Because functions in Lua are first-class values, they do not have a fixed name: some functions can be the value of multiple global variables, while others can be stored only in a table field. The `lua_getinfo` function checks how the function was called to find a suitable name. If it cannot find a name, then `name` is set to `NULL`.

- **`namewhat`: ** explains the `name` field. The value of `namewhat` can be `"global"`, `"local"`, `"method"`, `"field"`, `"upvalue"`, or `""` (the empty string), according to how the function was called. (Lua uses the empty string when no other option seems to apply.)

- **`istailcall`: ** true if this function invocation was called by a tail call. In this case, the caller of this level is not in the stack.

- **`nups`: ** the number of upvalues of the function.

- **`nparams`: ** the number of parameters of the function (always 0 for C functions).

- **`isvararg`: ** true if the function is a variadic function (always true for C functions).

- **`ftransfer`: ** the index in the stack of the first value being "transferred", that is, parameters in a call or return values in a return. (The other values are in consecutive indices.) Using this index, you can access and modify these values through [`lua_getlocal`](#lua_getlocal) and [`lua_setlocal`](#lua_setlocal). This field is only meaningful during a call hook, denoting the first parameter, or a return hook, denoting the first value being returned. (For call hooks, this value is always 1.)

- **`ntransfer`: ** The number of values being transferred (see previous item). (For calls of Lua functions, this value is always equal to `nparams`.)

---

### `lua_gethook`

[-0, +0, –]

```
lua_Hook lua_gethook (lua_State *L);
```

Returns the current hook function.

---

### `lua_gethookcount`

[-0, +0, –]

```
int lua_gethookcount (lua_State *L);
```

Returns the current hook count.

---

### `lua_gethookmask`

[-0, +0, –]

```
int lua_gethookmask (lua_State *L);
```

Returns the current hook mask.

---

### `lua_getinfo`

[-(0|1), +(0|1|2), *m*]

```
int lua_getinfo (lua_State *L, const char *what, lua_Debug *ar);
```

Gets information about a specific function or function invocation.

To get information about a function invocation, the parameter `ar` must be a valid activation record that was filled by a previous call to [`lua_getstack`](#lua_getstack) or given as argument to a hook (see [`lua_Hook`](#lua_Hook)).

To get information about a function, you push it onto the stack and start the `what` string with the character '`>`'. (In that case, `lua_getinfo` pops the function from the top of the stack.) For instance, to know in which line a function `f` was defined, you can write the following code:

```
lua_Debug ar;
lua_getglobal(L, "f");  /* get global 'f' */
lua_getinfo(L, ">S", &ar);
printf("%d\n", ar.linedefined);
```

Each character in the string `what` selects some fields of the structure `ar` to be filled or a value to be pushed on the stack. (These characters are also documented in the declaration of the structure [`lua_Debug`](#lua_Debug), between parentheses in the comments following each field.)

- **'`f`': ** pushes onto the stack the function that is running at the given level;

- **'`l`': ** fills in the field `currentline`;

- **'`n`': ** fills in the fields `name` and `namewhat`;

- **'`r`': ** fills in the fields `ftransfer` and `ntransfer`;

- **'`S`': ** fills in the fields `source`, `short_src`, `linedefined`, `lastlinedefined`, and `what`;

- **'`t`': ** fills in the field `istailcall`;

- **'`u`': ** fills in the fields `nups`, `nparams`, and `isvararg`;

- **'`L`': ** pushes onto the stack a table whose indices are the lines on the function with some associated code, that is, the lines where you can put a break point. (Lines with no code include empty lines and comments.) If this option is given together with option '`f`', its table is pushed after the function. This is the only option that can raise a memory error.

This function returns 0 to signal an invalid option in `what`; even then the valid options are handled correctly.

---

### `lua_getlocal`

[-0, +(0|1), –]

```
const char *lua_getlocal (lua_State *L, const lua_Debug *ar, int n);
```

Gets information about a local variable or a temporary value of a given activation record or a given function.

In the first case, the parameter `ar` must be a valid activation record that was filled by a previous call to [`lua_getstack`](#lua_getstack) or given as argument to a hook (see [`lua_Hook`](#lua_Hook)). The index `n` selects which local variable to inspect; see [`debug.getlocal`](#pdf-debug.getlocal) for details about variable indices and names.

[`lua_getlocal`](#lua_getlocal) pushes the variable's value onto the stack and returns its name.

In the second case, `ar` must be `NULL` and the function to be inspected must be on the top of the stack. In this case, only parameters of Lua functions are visible (as there is no information about what variables are active) and no values are pushed onto the stack.

Returns `NULL` (and pushes nothing) when the index is greater than the number of active local variables.

---

### `lua_getstack`

[-0, +0, –]

```
int lua_getstack (lua_State *L, int level, lua_Debug *ar);
```

Gets information about the interpreter runtime stack.

This function fills parts of a [`lua_Debug`](#lua_Debug) structure with an identification of the *activation record* of the function executing at a given level. Level 0 is the current running function, whereas level *n+1* is the function that has called level *n* (except for tail calls, which do not count in the stack). When called with a level greater than the stack depth, [`lua_getstack`](#lua_getstack) returns 0; otherwise it returns 1.

---

### `lua_getupvalue`

[-0, +(0|1), –]

```
const char *lua_getupvalue (lua_State *L, int funcindex, int n);
```

Gets information about the `n`-th upvalue of the closure at index `funcindex`. It pushes the upvalue's value onto the stack and returns its name. Returns `NULL` (and pushes nothing) when the index `n` is greater than the number of upvalues.

See [`debug.getupvalue`](#pdf-debug.getupvalue) for more information about upvalues.

---

### `lua_Hook`

```
typedef void (*lua_Hook) (lua_State *L, lua_Debug *ar);
```

Type for debugging hook functions.

Whenever a hook is called, its `ar` argument has its field `event` set to the specific event that triggered the hook. Lua identifies these events with the following constants: `LUA_HOOKCALL`, `LUA_HOOKRET`, `LUA_HOOKTAILCALL`, `LUA_HOOKLINE`, and `LUA_HOOKCOUNT`. Moreover, for line events, the field `currentline` is also set. To get the value of any other field in `ar`, the hook must call [`lua_getinfo`](#lua_getinfo).

For call events, `event` can be `LUA_HOOKCALL`, the normal value, or `LUA_HOOKTAILCALL`, for a tail call; in this case, there will be no corresponding return event.

While Lua is running a hook, it disables other calls to hooks. Therefore, if a hook calls back Lua to execute a function or a chunk, this execution occurs without any calls to hooks.

Hook functions cannot have continuations, that is, they cannot call [`lua_yieldk`](#lua_yieldk), [`lua_pcallk`](#lua_pcallk), or [`lua_callk`](#lua_callk) with a non-null `k`.

Hook functions can yield under the following conditions: Only count and line events can yield; to yield, a hook function must finish its execution calling [`lua_yield`](#lua_yield) with `nresults` equal to zero (that is, with no values).

---

### `lua_sethook`

[-0, +0, –]

```
void lua_sethook (lua_State *L, lua_Hook f, int mask, int count);
```

Sets the debugging hook function.

Argument `f` is the hook function. `mask` specifies on which events the hook will be called: it is formed by a bitwise OR of the constants `LUA_MASKCALL`, `LUA_MASKRET`, `LUA_MASKLINE`, and `LUA_MASKCOUNT`. The `count` argument is only meaningful when the mask includes `LUA_MASKCOUNT`. For each event, the hook is called as explained below:

- **The call hook: ** is called when the interpreter calls a function. The hook is called just after Lua enters the new function.

- **The return hook: ** is called when the interpreter returns from a function. The hook is called just before Lua leaves the function.

- **The line hook: ** is called when the interpreter is about to start the execution of a new line of code, or when it jumps back in the code (even to the same line). This event only happens while Lua is executing a Lua function.

- **The count hook: ** is called after the interpreter executes every `count` instructions. This event only happens while Lua is executing a Lua function.

Hooks are disabled by setting `mask` to zero.

---

### `lua_setlocal`

[-(0|1), +0, –]

```
const char *lua_setlocal (lua_State *L, const lua_Debug *ar, int n);
```

Sets the value of a local variable of a given activation record. It assigns the value on the top of the stack to the variable and returns its name. It also pops the value from the stack.

Returns `NULL` (and pops nothing) when the index is greater than the number of active local variables.

Parameters `ar` and `n` are as in the function [`lua_getlocal`](#lua_getlocal).

---

### `lua_setupvalue`

[-(0|1), +0, –]

```
const char *lua_setupvalue (lua_State *L, int funcindex, int n);
```

Sets the value of a closure's upvalue. It assigns the value on the top of the stack to the upvalue and returns its name. It also pops the value from the stack.

Returns `NULL` (and pops nothing) when the index `n` is greater than the number of upvalues.

Parameters `funcindex` and `n` are as in the function [`lua_getupvalue`](#lua_getupvalue).

---

### `lua_upvalueid`

[-0, +0, –]

```
void *lua_upvalueid (lua_State *L, int funcindex, int n);
```

Returns a unique identifier for the upvalue numbered `n` from the closure at index `funcindex`.

These unique identifiers allow a program to check whether different closures share upvalues. Lua closures that share an upvalue (that is, that access a same external local variable) will return identical ids for those upvalue indices.

Parameters `funcindex` and `n` are as in the function [`lua_getupvalue`](#lua_getupvalue), but `n` cannot be greater than the number of upvalues.

---

### `lua_upvaluejoin`

[-0, +0, –]

```
void lua_upvaluejoin (lua_State *L, int funcindex1, int n1,
                                    int funcindex2, int n2);
```

Make the `n1`-th upvalue of the Lua closure at index `funcindex1` refer to the `n2`-th upvalue of the Lua closure at index `funcindex2`.

# 5 – The Auxiliary Library

The *auxiliary library* provides several convenient functions to interface C with Lua. While the basic API provides the primitive functions for all interactions between C and Lua, the auxiliary library provides higher-level functions for some common tasks.

All functions and types from the auxiliary library are defined in header file `lauxlib.h` and have a prefix `luaL_`.

All functions in the auxiliary library are built on top of the basic API, and so they provide nothing that cannot be done with that API. Nevertheless, the use of the auxiliary library ensures more consistency to your code.

Several functions in the auxiliary library use internally some extra stack slots. When a function in the auxiliary library uses less than five slots, it does not check the stack size; it simply assumes that there are enough slots.

Several functions in the auxiliary library are used to check C function arguments. Because the error message is formatted for arguments (e.g., "`bad argument #1`"), you should not use these functions for other stack values.

Functions called `luaL_check*` always raise an error if the check is not satisfied.

## 5.1 – Functions and Types

Here we list all functions and types from the auxiliary library in alphabetical order.

---

### `luaL_addchar`

[-?, +?, *m*]

```
void luaL_addchar (luaL_Buffer *B, char c);
```

Adds the byte `c` to the buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)).

---

### `luaL_addgsub`

[-?, +?, *m*]

```
const void luaL_addgsub (luaL_Buffer *B, const char *s,
                         const char *p, const char *r);
```

Adds a copy of the string `s` to the buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)), replacing any occurrence of the string `p` with the string `r`.

---

### `luaL_addlstring`

[-?, +?, *m*]

```
void luaL_addlstring (luaL_Buffer *B, const char *s, size_t l);
```

Adds the string pointed to by `s` with length `l` to the buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)). The string can contain embedded zeros.

---

### `luaL_addsize`

[-?, +?, –]

```
void luaL_addsize (luaL_Buffer *B, size_t n);
```

Adds to the buffer `B` a string of length `n` previously copied to the buffer area (see [`luaL_prepbuffer`](#luaL_prepbuffer)).

---

### `luaL_addstring`

[-?, +?, *m*]

```
void luaL_addstring (luaL_Buffer *B, const char *s);
```

Adds the zero-terminated string pointed to by `s` to the buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)).

---

### `luaL_addvalue`

[-?, +?, *m*]

```
void luaL_addvalue (luaL_Buffer *B);
```

Adds the value on the top of the stack to the buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)). Pops the value.

This is the only function on string buffers that can (and must) be called with an extra element on the stack, which is the value to be added to the buffer.

---

### `luaL_argcheck`

[-0, +0, *v*]

```
void luaL_argcheck (lua_State *L,
                    int cond,
                    int arg,
                    const char *extramsg);
```

Checks whether `cond` is true. If it is not, raises an error with a standard message (see [`luaL_argerror`](#luaL_argerror)).

---

### `luaL_argerror`

[-0, +0, *v*]

```
int luaL_argerror (lua_State *L, int arg, const char *extramsg);
```

Raises an error reporting a problem with argument `arg` of the C function that called it, using a standard message that includes `extramsg` as a comment:

```
bad argument #arg to 'funcname' (extramsg)
```

This function never returns.

---

### `luaL_argexpected`

[-0, +0, *v*]

```
void luaL_argexpected (lua_State *L,
                       int cond,
                       int arg,
                       const char *tname);
```

Checks whether `cond` is true. If it is not, raises an error about the type of the argument `arg` with a standard message (see [`luaL_typeerror`](#luaL_typeerror)).

---

### `luaL_Buffer`

```
typedef struct luaL_Buffer luaL_Buffer;
```

Type for a *string buffer*.

A string buffer allows C code to build Lua strings piecemeal. Its pattern of use is as follows:

- First declare a variable `b` of type [`luaL_Buffer`](#luaL_Buffer).

- Then initialize it with a call `luaL_buffinit(L, &b)`.

- Then add string pieces to the buffer calling any of the `luaL_add*` functions.

- Finish by calling `luaL_pushresult(&b)`. This call leaves the final string on the top of the stack.

If you know beforehand the maximum size of the resulting string, you can use the buffer like this:

- First declare a variable `b` of type [`luaL_Buffer`](#luaL_Buffer).

- Then initialize it and preallocate a space of size `sz` with a call `luaL_buffinitsize(L, &b, sz)`.

- Then produce the string into that space.

- Finish by calling `luaL_pushresultsize(&b, sz)`, where `sz` is the total size of the resulting string copied into that space (which may be less than or equal to the preallocated size).

During its normal operation, a string buffer uses a variable number of stack slots. So, while using a buffer, you cannot assume that you know where the top of the stack is. You can use the stack between successive calls to buffer operations as long as that use is balanced; that is, when you call a buffer operation, the stack is at the same level it was immediately after the previous buffer operation. (The only exception to this rule is [`luaL_addvalue`](#luaL_addvalue).) After calling [`luaL_pushresult`](#luaL_pushresult), the stack is back to its level when the buffer was initialized, plus the final string on its top.

---

### `luaL_buffaddr`

[-0, +0, –]

```
char *luaL_buffaddr (luaL_Buffer *B);
```

Returns the address of the current content of buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)). Note that any addition to the buffer may invalidate this address.

---

### `luaL_buffinit`

[-0, +?, –]

```
void luaL_buffinit (lua_State *L, luaL_Buffer *B);
```

Initializes a buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)). This function does not allocate any space; the buffer must be declared as a variable.

---

### `luaL_bufflen`

[-0, +0, –]

```
size_t luaL_bufflen (luaL_Buffer *B);
```

Returns the length of the current content of buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)).

---

### `luaL_buffinitsize`

[-?, +?, *m*]

```
char *luaL_buffinitsize (lua_State *L, luaL_Buffer *B, size_t sz);
```

Equivalent to the sequence [`luaL_buffinit`](#luaL_buffinit), [`luaL_prepbuffsize`](#luaL_prepbuffsize).

---

### `luaL_buffsub`

[-?, +?, –]

```
void luaL_buffsub (luaL_Buffer *B, int n);
```

Removes `n` bytes from the buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)). The buffer must have at least that many bytes.

---

### `luaL_callmeta`

[-0, +(0|1), *e*]

```
int luaL_callmeta (lua_State *L, int obj, const char *e);
```

Calls a metamethod.

If the object at index `obj` has a metatable and this metatable has a field `e`, this function calls this field passing the object as its only argument. In this case this function returns true and pushes onto the stack the value returned by the call. If there is no metatable or no metamethod, this function returns false without pushing any value on the stack.

---

### `luaL_checkany`

[-0, +0, *v*]

```
void luaL_checkany (lua_State *L, int arg);
```

Checks whether the function has an argument of any type (including **nil**) at position `arg`.

---

### `luaL_checkinteger`

[-0, +0, *v*]

```
lua_Integer luaL_checkinteger (lua_State *L, int arg);
```

Checks whether the function argument `arg` is an integer (or can be converted to an integer) and returns this integer.

---

### `luaL_checklstring`

[-0, +0, *v*]

```
const char *luaL_checklstring (lua_State *L, int arg, size_t *l);
```

Checks whether the function argument `arg` is a string and returns this string; if `l` is not `NULL` fills its referent with the string's length.

This function uses [`lua_tolstring`](#lua_tolstring) to get its result, so all conversions and caveats of that function apply here.

---

### `luaL_checknumber`

[-0, +0, *v*]

```
lua_Number luaL_checknumber (lua_State *L, int arg);
```

Checks whether the function argument `arg` is a number and returns this number converted to a `lua_Number`.

---

### `luaL_checkoption`

[-0, +0, *v*]

```
int luaL_checkoption (lua_State *L,
                      int arg,
                      const char *def,
                      const char *const lst[]);
```

Checks whether the function argument `arg` is a string and searches for this string in the array `lst` (which must be NULL-terminated). Returns the index in the array where the string was found. Raises an error if the argument is not a string or if the string cannot be found.

If `def` is not `NULL`, the function uses `def` as a default value when there is no argument `arg` or when this argument is **nil**.

This is a useful function for mapping strings to C enums. (The usual convention in Lua libraries is to use strings instead of numbers to select options.)

---

### `luaL_checkstack`

[-0, +0, *v*]

```
void luaL_checkstack (lua_State *L, int sz, const char *msg);
```

Grows the stack size to `top + sz` elements, raising an error if the stack cannot grow to that size. `msg` is an additional text to go into the error message (or `NULL` for no additional text).

---

### `luaL_checkstring`

[-0, +0, *v*]

```
const char *luaL_checkstring (lua_State *L, int arg);
```

Checks whether the function argument `arg` is a string and returns this string.

This function uses [`lua_tolstring`](#lua_tolstring) to get its result, so all conversions and caveats of that function apply here.

---

### `luaL_checktype`

[-0, +0, *v*]

```
void luaL_checktype (lua_State *L, int arg, int t);
```

Checks whether the function argument `arg` has type `t`. See [`lua_type`](#lua_type) for the encoding of types for `t`.

---

### `luaL_checkudata`

[-0, +0, *v*]

```
void *luaL_checkudata (lua_State *L, int arg, const char *tname);
```

Checks whether the function argument `arg` is a userdata of the type `tname` (see [`luaL_newmetatable`](#luaL_newmetatable)) and returns the userdata's memory-block address (see [`lua_touserdata`](#lua_touserdata)).

---

### `luaL_checkversion`

[-0, +0, *v*]

```
void luaL_checkversion (lua_State *L);
```

Checks whether the code making the call and the Lua library being called are using the same version of Lua and the same numeric types.

---

### `luaL_dofile`

[-0, +?, *m*]

```
int luaL_dofile (lua_State *L, const char *filename);
```

Loads and runs the given file. It is defined as the following macro:

```
(luaL_loadfile(L, filename) || lua_pcall(L, 0, LUA_MULTRET, 0))
```

It returns 0 ([`LUA_OK`](#pdf-LUA_OK)) if there are no errors, or 1 in case of errors.

---

### `luaL_dostring`

[-0, +?, –]

```
int luaL_dostring (lua_State *L, const char *str);
```

Loads and runs the given string. It is defined as the following macro:

```
(luaL_loadstring(L, str) || lua_pcall(L, 0, LUA_MULTRET, 0))
```

It returns 0 ([`LUA_OK`](#pdf-LUA_OK)) if there are no errors, or 1 in case of errors.

---

### `luaL_error`

[-0, +0, *v*]

```
int luaL_error (lua_State *L, const char *fmt, ...);
```

Raises an error. The error message format is given by `fmt` plus any extra arguments, following the same rules of [`lua_pushfstring`](#lua_pushfstring). It also adds at the beginning of the message the file name and the line number where the error occurred, if this information is available.

This function never returns, but it is an idiom to use it in C functions as `return luaL_error(args)`.

---

### `luaL_execresult`

[-0, +3, *m*]

```
int luaL_execresult (lua_State *L, int stat);
```

This function produces the return values for process-related functions in the standard library ([`os.execute`](#pdf-os.execute) and [`io.close`](#pdf-io.close)).

---

### `luaL_fileresult`

[-0, +(1|3), *m*]

```
int luaL_fileresult (lua_State *L, int stat, const char *fname);
```

This function produces the return values for file-related functions in the standard library ([`io.open`](#pdf-io.open), [`os.rename`](#pdf-os.rename), [`file:seek`](#pdf-file:seek), etc.).

---

### `luaL_getmetafield`

[-0, +(0|1), *m*]

```
int luaL_getmetafield (lua_State *L, int obj, const char *e);
```

Pushes onto the stack the field `e` from the metatable of the object at index `obj` and returns the type of the pushed value. If the object does not have a metatable, or if the metatable does not have this field, pushes nothing and returns `LUA_TNIL`.

---

### `luaL_getmetatable`

[-0, +1, *m*]

```
int luaL_getmetatable (lua_State *L, const char *tname);
```

Pushes onto the stack the metatable associated with the name `tname` in the registry (see [`luaL_newmetatable`](#luaL_newmetatable)), or **nil** if there is no metatable associated with that name. Returns the type of the pushed value.

---

### `luaL_getsubtable`

[-0, +1, *e*]

```
int luaL_getsubtable (lua_State *L, int idx, const char *fname);
```

Ensures that the value `t[fname]`, where `t` is the value at index `idx`, is a table, and pushes that table onto the stack. Returns true if it finds a previous table there and false if it creates a new table.

---

### `luaL_gsub`

[-0, +1, *m*]

```
const char *luaL_gsub (lua_State *L,
                       const char *s,
                       const char *p,
                       const char *r);
```

Creates a copy of string `s`, replacing any occurrence of the string `p` with the string `r`. Pushes the resulting string on the stack and returns it.

---

### `luaL_len`

[-0, +0, *e*]

```
lua_Integer luaL_len (lua_State *L, int index);
```

Returns the "length" of the value at the given index as a number; it is equivalent to the '`#`' operator in Lua (see [§3.4.7](#3.4.7)). Raises an error if the result of the operation is not an integer. (This case can only happen through metamethods.)

---

### `luaL_loadbuffer`

[-0, +1, –]

```
int luaL_loadbuffer (lua_State *L,
                     const char *buff,
                     size_t sz,
                     const char *name);
```

Equivalent to [`luaL_loadbufferx`](#luaL_loadbufferx) with `mode` equal to `NULL`.

---

### `luaL_loadbufferx`

[-0, +1, –]

```
int luaL_loadbufferx (lua_State *L,
                      const char *buff,
                      size_t sz,
                      const char *name,
                      const char *mode);
```

Loads a buffer as a Lua chunk. This function uses [`lua_load`](#lua_load) to load the chunk in the buffer pointed to by `buff` with size `sz`.

This function returns the same results as [`lua_load`](#lua_load). `name` is the chunk name, used for debug information and error messages. The string `mode` works as in the function [`lua_load`](#lua_load).

---

### `luaL_loadfile`

[-0, +1, *m*]

```
int luaL_loadfile (lua_State *L, const char *filename);
```

Equivalent to [`luaL_loadfilex`](#luaL_loadfilex) with `mode` equal to `NULL`.

---

### `luaL_loadfilex`

[-0, +1, *m*]

```
int luaL_loadfilex (lua_State *L, const char *filename,
                                            const char *mode);
```

Loads a file as a Lua chunk. This function uses [`lua_load`](#lua_load) to load the chunk in the file named `filename`. If `filename` is `NULL`, then it loads from the standard input. The first line in the file is ignored if it starts with a `#`.

The string `mode` works as in the function [`lua_load`](#lua_load).

This function returns the same results as [`lua_load`](#lua_load) or [`LUA_ERRFILE`](#pdf-LUA_ERRFILE) for file-related errors.

As [`lua_load`](#lua_load), this function only loads the chunk; it does not run it.

---

### `luaL_loadstring`

[-0, +1, –]

```
int luaL_loadstring (lua_State *L, const char *s);
```

Loads a string as a Lua chunk. This function uses [`lua_load`](#lua_load) to load the chunk in the zero-terminated string `s`.

This function returns the same results as [`lua_load`](#lua_load).

Also as [`lua_load`](#lua_load), this function only loads the chunk; it does not run it.

---

### `luaL_newlib`

[-0, +1, *m*]

```
void luaL_newlib (lua_State *L, const luaL_Reg l[]);
```

Creates a new table and registers there the functions in the list `l`.

It is implemented as the following macro:

```
(luaL_newlibtable(L,l), luaL_setfuncs(L,l,0))
```

The array `l` must be the actual array, not a pointer to it.

---

### `luaL_newlibtable`

[-0, +1, *m*]

```
void luaL_newlibtable (lua_State *L, const luaL_Reg l[]);
```

Creates a new table with a size optimized to store all entries in the array `l` (but does not actually store them). It is intended to be used in conjunction with [`luaL_setfuncs`](#luaL_setfuncs) (see [`luaL_newlib`](#luaL_newlib)).

It is implemented as a macro. The array `l` must be the actual array, not a pointer to it.

---

### `luaL_newmetatable`

[-0, +1, *m*]

```
int luaL_newmetatable (lua_State *L, const char *tname);
```

If the registry already has the key `tname`, returns 0. Otherwise, creates a new table to be used as a metatable for userdata, adds to this new table the pair `__name = tname`, adds to the registry the pair `[tname] = new table`, and returns 1.

In both cases, the function pushes onto the stack the final value associated with `tname` in the registry.

---

### `luaL_newstate`

[-0, +0, –]

```
lua_State *luaL_newstate (void);
```

Creates a new Lua state. It calls [`lua_newstate`](#lua_newstate) with an allocator based on the ISO C allocation functions and then sets a warning function and a panic function (see [§4.4](#4.4)) that print messages to the standard error output.

Returns the new state, or `NULL` if there is a memory allocation error.

---

### `luaL_openlibs`

[-0, +0, *e*]

```
void luaL_openlibs (lua_State *L);
```

Opens all standard Lua libraries into the given state.

---

### `luaL_opt`

[-0, +0, –]

```
T luaL_opt (L, func, arg, dflt);
```

This macro is defined as follows:

```
(lua_isnoneornil(L,(arg)) ? (dflt) : func(L,(arg)))
```

In words, if the argument `arg` is nil or absent, the macro results in the default `dflt`. Otherwise, it results in the result of calling `func` with the state `L` and the argument index `arg` as arguments. Note that it evaluates the expression `dflt` only if needed.

---

### `luaL_optinteger`

[-0, +0, *v*]

```
lua_Integer luaL_optinteger (lua_State *L,
                             int arg,
                             lua_Integer d);
```

If the function argument `arg` is an integer (or it is convertible to an integer), returns this integer. If this argument is absent or is **nil**, returns `d`. Otherwise, raises an error.

---

### `luaL_optlstring`

[-0, +0, *v*]

```
const char *luaL_optlstring (lua_State *L,
                             int arg,
                             const char *d,
                             size_t *l);
```

If the function argument `arg` is a string, returns this string. If this argument is absent or is **nil**, returns `d`. Otherwise, raises an error.

If `l` is not `NULL`, fills its referent with the result's length. If the result is `NULL` (only possible when returning `d` and `d == NULL`), its length is considered zero.

This function uses [`lua_tolstring`](#lua_tolstring) to get its result, so all conversions and caveats of that function apply here.

---

### `luaL_optnumber`

[-0, +0, *v*]

```
lua_Number luaL_optnumber (lua_State *L, int arg, lua_Number d);
```

If the function argument `arg` is a number, returns this number as a `lua_Number`. If this argument is absent or is **nil**, returns `d`. Otherwise, raises an error.

---

### `luaL_optstring`

[-0, +0, *v*]

```
const char *luaL_optstring (lua_State *L,
                            int arg,
                            const char *d);
```

If the function argument `arg` is a string, returns this string. If this argument is absent or is **nil**, returns `d`. Otherwise, raises an error.

---

### `luaL_prepbuffer`

[-?, +?, *m*]

```
char *luaL_prepbuffer (luaL_Buffer *B);
```

Equivalent to [`luaL_prepbuffsize`](#luaL_prepbuffsize) with the predefined size `LUAL_BUFFERSIZE`.

---

### `luaL_prepbuffsize`

[-?, +?, *m*]

```
char *luaL_prepbuffsize (luaL_Buffer *B, size_t sz);
```

Returns an address to a space of size `sz` where you can copy a string to be added to buffer `B` (see [`luaL_Buffer`](#luaL_Buffer)). After copying the string into this space you must call [`luaL_addsize`](#luaL_addsize) with the size of the string to actually add it to the buffer.

---

### `luaL_pushfail`

[-0, +1, –]

```
void luaL_pushfail (lua_State *L);
```

Pushes the **fail** value onto the stack (see [§6](#6)).

---

### `luaL_pushresult`

[-?, +1, *m*]

```
void luaL_pushresult (luaL_Buffer *B);
```

Finishes the use of buffer `B` leaving the final string on the top of the stack.

---

### `luaL_pushresultsize`

[-?, +1, *m*]

```
void luaL_pushresultsize (luaL_Buffer *B, size_t sz);
```

Equivalent to the sequence [`luaL_addsize`](#luaL_addsize), [`luaL_pushresult`](#luaL_pushresult).

---

### `luaL_ref`

[-1, +0, *m*]

```
int luaL_ref (lua_State *L, int t);
```

Creates and returns a *reference*, in the table at index `t`, for the object on the top of the stack (and pops the object).

A reference is a unique integer key. As long as you do not manually add integer keys into the table `t`, [`luaL_ref`](#luaL_ref) ensures the uniqueness of the key it returns. You can retrieve an object referred by the reference `r` by calling `lua_rawgeti(L, t, r)`. The function [`luaL_unref`](#luaL_unref) frees a reference.

If the object on the top of the stack is **nil**, [`luaL_ref`](#luaL_ref) returns the constant `LUA_REFNIL`. The constant `LUA_NOREF` is guaranteed to be different from any reference returned by [`luaL_ref`](#luaL_ref).

---

### `luaL_Reg`

```
typedef struct luaL_Reg {
  const char *name;
  lua_CFunction func;
} luaL_Reg;
```

Type for arrays of functions to be registered by [`luaL_setfuncs`](#luaL_setfuncs). `name` is the function name and `func` is a pointer to the function. Any array of [`luaL_Reg`](#luaL_Reg) must end with a sentinel entry in which both `name` and `func` are `NULL`.

---

### `luaL_requiref`

[-0, +1, *e*]

```
void luaL_requiref (lua_State *L, const char *modname,
                    lua_CFunction openf, int glb);
```

If `package.loaded[modname]` is not true, calls the function `openf` with the string `modname` as an argument and sets the call result to `package.loaded[modname]`, as if that function has been called through [`require`](#pdf-require).

If `glb` is true, also stores the module into the global `modname`.

Leaves a copy of the module on the stack.

---

### `luaL_setfuncs`

[-nup, +0, *m*]

```
void luaL_setfuncs (lua_State *L, const luaL_Reg *l, int nup);
```

Registers all functions in the array `l` (see [`luaL_Reg`](#luaL_Reg)) into the table on the top of the stack (below optional upvalues, see next).

When `nup` is not zero, all functions are created with `nup` upvalues, initialized with copies of the `nup` values previously pushed on the stack on top of the library table. These values are popped from the stack after the registration.

A function with a `NULL` value represents a placeholder, which is filled with **false**.

---

### `luaL_setmetatable`

[-0, +0, –]

```
void luaL_setmetatable (lua_State *L, const char *tname);
```

Sets the metatable of the object on the top of the stack as the metatable associated with name `tname` in the registry (see [`luaL_newmetatable`](#luaL_newmetatable)).

---

### `luaL_Stream`

```
typedef struct luaL_Stream {
  FILE *f;
  lua_CFunction closef;
} luaL_Stream;
```

The standard representation for file handles used by the standard I/O library.

A file handle is implemented as a full userdata, with a metatable called `LUA_FILEHANDLE` (where `LUA_FILEHANDLE` is a macro with the actual metatable's name). The metatable is created by the I/O library (see [`luaL_newmetatable`](#luaL_newmetatable)).

This userdata must start with the structure `luaL_Stream`; it can contain other data after this initial structure. The field `f` points to the corresponding C stream (or it can be `NULL` to indicate an incompletely created handle). The field `closef` points to a Lua function that will be called to close the stream when the handle is closed or collected; this function receives the file handle as its sole argument and must return either a true value, in case of success, or a false value plus an error message, in case of error. Once Lua calls this field, it changes the field value to `NULL` to signal that the handle is closed.

---

### `luaL_testudata`

[-0, +0, *m*]

```
void *luaL_testudata (lua_State *L, int arg, const char *tname);
```

This function works like [`luaL_checkudata`](#luaL_checkudata), except that, when the test fails, it returns `NULL` instead of raising an error.

---

### `luaL_tolstring`

[-0, +1, *e*]

```
const char *luaL_tolstring (lua_State *L, int idx, size_t *len);
```

Converts any Lua value at the given index to a C string in a reasonable format. The resulting string is pushed onto the stack and also returned by the function (see [§4.1.3](#4.1.3)). If `len` is not `NULL`, the function also sets `*len` with the string length.

If the value has a metatable with a `__tostring` field, then `luaL_tolstring` calls the corresponding metamethod with the value as argument, and uses the result of the call as its result.

---

### `luaL_traceback`

[-0, +1, *m*]

```
void luaL_traceback (lua_State *L, lua_State *L1, const char *msg,
                     int level);
```

Creates and pushes a traceback of the stack `L1`. If `msg` is not `NULL`, it is appended at the beginning of the traceback. The `level` parameter tells at which level to start the traceback.

---

### `luaL_typeerror`

[-0, +0, *v*]

```
int luaL_typeerror (lua_State *L, int arg, const char *tname);
```

Raises a type error for the argument `arg` of the C function that called it, using a standard message; `tname` is a "name" for the expected type. This function never returns.

---

### `luaL_typename`

[-0, +0, –]

```
const char *luaL_typename (lua_State *L, int index);
```

Returns the name of the type of the value at the given index.

---

### `luaL_unref`

[-0, +0, –]

```
void luaL_unref (lua_State *L, int t, int ref);
```

Releases the reference `ref` from the table at index `t` (see [`luaL_ref`](#luaL_ref)). The entry is removed from the table, so that the referred object can be collected. The reference `ref` is also freed to be used again.

If `ref` is [`LUA_NOREF`](#pdf-LUA_NOREF) or [`LUA_REFNIL`](#pdf-LUA_REFNIL), [`luaL_unref`](#luaL_unref) does nothing.

---

### `luaL_where`

[-0, +1, *m*]

```
void luaL_where (lua_State *L, int lvl);
```

Pushes onto the stack a string identifying the current position of the control at level `lvl` in the call stack. Typically this string has the following format:

```
chunkname:currentline:
```

Level 0 is the running function, level 1 is the function that called the running function, etc.

This function is used to build a prefix for error messages.

# 6 – The Standard Libraries

The standard Lua libraries provide useful functions that are implemented in C through the C API. Some of these functions provide essential services to the language (e.g., [`type`](#pdf-type) and [`getmetatable`](#pdf-getmetatable)); others provide access to outside services (e.g., I/O); and others could be implemented in Lua itself, but that for different reasons deserve an implementation in C (e.g., [`table.sort`](#pdf-table.sort)).

All libraries are implemented through the official C API and are provided as separate C modules. Unless otherwise noted, these library functions do not adjust its number of arguments to its expected parameters. For instance, a function documented as `foo(arg)` should not be called without an argument.

The notation **fail** means a false value representing some kind of failure. (Currently, **fail** is equal to **nil**, but that may change in future versions. The recommendation is to always test the success of these functions with `(not status)`, instead of `(status == nil)`.)

Currently, Lua has the following standard libraries:

- basic library ([§6.1](#6.1));

- coroutine library ([§6.2](#6.2));

- package library ([§6.3](#6.3));

- string manipulation ([§6.4](#6.4));

- basic UTF-8 support ([§6.5](#6.5));

- table manipulation ([§6.6](#6.6));

- mathematical functions ([§6.7](#6.7)) (sin, log, etc.);

- input and output ([§6.8](#6.8));

- operating system facilities ([§6.9](#6.9));

- debug facilities ([§6.10](#6.10)).

Except for the basic and the package libraries, each library provides all its functions as fields of a global table or as methods of its objects.

To have access to these libraries, the C host program should call the [`luaL_openlibs`](#luaL_openlibs) function, which opens all standard libraries. Alternatively, the host program can open them individually by using [`luaL_requiref`](#luaL_requiref) to call `luaopen_base` (for the basic library), `luaopen_package` (for the package library), `luaopen_coroutine` (for the coroutine library), `luaopen_string` (for the string library), `luaopen_utf8` (for the UTF-8 library), `luaopen_table` (for the table library), `luaopen_math` (for the mathematical library), `luaopen_io` (for the I/O library), `luaopen_os` (for the operating system library), and `luaopen_debug` (for the debug library). These functions are declared in `lualib.h`.

## 6.1 – Basic Functions

The basic library provides core functions to Lua. If you do not include this library in your application, you should check carefully whether you need to provide implementations for some of its facilities.

---

### `assert (v [, message])`

Raises an error if the value of its argument `v` is false (i.e., **nil** or **false**); otherwise, returns all its arguments. In case of error, `message` is the error object; when absent, it defaults to "`assertion failed!`"

---

### `collectgarbage ([opt [, arg]])`

This function is a generic interface to the garbage collector. It performs different functions according to its first argument, `opt`:

- **"`collect`": ** Performs a full garbage-collection cycle. This is the default option.

- **"`stop`": ** Stops automatic execution of the garbage collector. The collector will run only when explicitly invoked, until a call to restart it.

- **"`restart`": ** Restarts automatic execution of the garbage collector.

- **"`count`": ** Returns the total memory in use by Lua in Kbytes. The value has a fractional part, so that it multiplied by 1024 gives the exact number of bytes in use by Lua.

- **"`step`": ** Performs a garbage-collection step. The step "size" is controlled by `arg`. With a zero value, the collector will perform one basic (indivisible) step. For non-zero values, the collector will perform as if that amount of memory (in Kbytes) had been allocated by Lua. Returns **true** if the step finished a collection cycle.

- **"`isrunning`": ** Returns a boolean that tells whether the collector is running (i.e., not stopped).

- **"`incremental`": ** Change the collector mode to incremental. This option can be followed by three numbers: the garbage-collector pause, the step multiplier, and the step size (see [§2.5.1](#2.5.1)). A zero means to not change that value.

- **"`generational`": ** Change the collector mode to generational. This option can be followed by two numbers: the garbage-collector minor multiplier and the major multiplier (see [§2.5.2](#2.5.2)). A zero means to not change that value.

See [§2.5](#2.5) for more details about garbage collection and some of these options.

This function should not be called by a finalizer.

---

### `dofile ([filename])`

Opens the named file and executes its content as a Lua chunk. When called without arguments, `dofile` executes the content of the standard input (`stdin`). Returns all values returned by the chunk. In case of errors, `dofile` propagates the error to its caller. (That is, `dofile` does not run in protected mode.)

---

### `error (message [, level])`

Raises an error (see [§2.3](#2.3)) with `message` as the error object. This function never returns.

Usually, `error` adds some information about the error position at the beginning of the message, if the message is a string. The `level` argument specifies how to get the error position. With level 1 (the default), the error position is where the `error` function was called. Level 2 points the error to where the function that called `error` was called; and so on. Passing a level 0 avoids the addition of error position information to the message.

---

### `_G`

A global variable (not a function) that holds the global environment (see [§2.2](#2.2)). Lua itself does not use this variable; changing its value does not affect any environment, nor vice versa.

---

### `getmetatable (object)`

If `object` does not have a metatable, returns **nil**. Otherwise, if the object's metatable has a `__metatable` field, returns the associated value. Otherwise, returns the metatable of the given object.

---

### `ipairs (t)`

Returns three values (an iterator function, the table `t`, and 0) so that the construction

```
for i,v in ipairs(t) do body end
```

will iterate over the key–value pairs (`1,t[1]`), (`2,t[2]`), ..., up to the first absent index.

---

### `load (chunk [, chunkname [, mode [, env]]])`

Loads a chunk.

If `chunk` is a string, the chunk is this string. If `chunk` is a function, `load` calls it repeatedly to get the chunk pieces. Each call to `chunk` must return a string that concatenates with previous results. A return of an empty string, **nil**, or no value signals the end of the chunk.

If there are no syntactic errors, `load` returns the compiled chunk as a function; otherwise, it returns **fail** plus the error message.

When you load a main chunk, the resulting function will always have exactly one upvalue, the `_ENV` variable (see [§2.2](#2.2)). However, when you load a binary chunk created from a function (see [`string.dump`](#pdf-string.dump)), the resulting function can have an arbitrary number of upvalues, and there is no guarantee that its first upvalue will be the `_ENV` variable. (A non-main function may not even have an `_ENV` upvalue.)

Regardless, if the resulting function has any upvalues, its first upvalue is set to the value of `env`, if that parameter is given, or to the value of the global environment. Other upvalues are initialized with **nil**. All upvalues are fresh, that is, they are not shared with any other function.

`chunkname` is used as the name of the chunk for error messages and debug information (see [§4.7](#4.7)). When absent, it defaults to `chunk`, if `chunk` is a string, or to "`=(load)`" otherwise.

The string `mode` controls whether the chunk can be text or binary (that is, a precompiled chunk). It may be the string "`b`" (only binary chunks), "`t`" (only text chunks), or "`bt`" (both binary and text). The default is "`bt`".

It is safe to load malformed binary chunks; `load` signals an appropriate error. However, Lua does not check the consistency of the code inside binary chunks; running maliciously crafted bytecode can crash the interpreter.

---

### `loadfile ([filename [, mode [, env]]])`

Similar to [`load`](#pdf-load), but gets the chunk from file `filename` or from the standard input, if no file name is given.

---

### `next (table [, index])`

Allows a program to traverse all fields of a table. Its first argument is a table and its second argument is an index in this table. A call to `next` returns the next index of the table and its associated value. When called with **nil** as its second argument, `next` returns an initial index and its associated value. When called with the last index, or with **nil** in an empty table, `next` returns **nil**. If the second argument is absent, then it is interpreted as **nil**. In particular, you can use `next(t)` to check whether a table is empty.

The order in which the indices are enumerated is not specified, *even for numeric indices*. (To traverse a table in numerical order, use a numerical **for**.)

You should not assign any value to a non-existent field in a table during its traversal. You may however modify existing fields. In particular, you may set existing fields to nil.

---

### `pairs (t)`

If `t` has a metamethod `__pairs`, calls it with `t` as argument and returns the first three results from the call.

Otherwise, returns three values: the [`next`](#pdf-next) function, the table `t`, and **nil**, so that the construction

```
for k,v in pairs(t) do body end
```

will iterate over all key–value pairs of table `t`.

See function [`next`](#pdf-next) for the caveats of modifying the table during its traversal.

---

### `pcall (f [, arg1, ···])`

Calls the function `f` with the given arguments in *protected mode*. This means that any error inside `f` is not propagated; instead, `pcall` catches the error and returns a status code. Its first result is the status code (a boolean), which is **true** if the call succeeds without errors. In such case, `pcall` also returns all results from the call, after this first result. In case of any error, `pcall` returns **false** plus the error object. Note that errors caught by `pcall` do not call a message handler.

---

### `print (···)`

Receives any number of arguments and prints their values to `stdout`, converting each argument to a string following the same rules of [`tostring`](#pdf-tostring).

The function `print` is not intended for formatted output, but only as a quick way to show a value, for instance for debugging. For complete control over the output, use [`string.format`](#pdf-string.format) and [`io.write`](#pdf-io.write).

---

### `rawequal (v1, v2)`

Checks whether `v1` is equal to `v2`, without invoking the `__eq` metamethod. Returns a boolean.

---

### `rawget (table, index)`

Gets the real value of `table[index]`, without using the `__index` metavalue. `table` must be a table; `index` may be any value.

---

### `rawlen (v)`

Returns the length of the object `v`, which must be a table or a string, without invoking the `__len` metamethod. Returns an integer.

---

### `rawset (table, index, value)`

Sets the real value of `table[index]` to `value`, without using the `__newindex` metavalue. `table` must be a table, `index` any value different from **nil** and NaN, and `value` any Lua value.

This function returns `table`.

---

### `select (index, ···)`

If `index` is a number, returns all arguments after argument number `index`; a negative number indexes from the end (-1 is the last argument). Otherwise, `index` must be the string `"#"`, and `select` returns the total number of extra arguments it received.

---

### `setmetatable (table, metatable)`

Sets the metatable for the given table. If `metatable` is **nil**, removes the metatable of the given table. If the original metatable has a `__metatable` field, raises an error.

This function returns `table`.

To change the metatable of other types from Lua code, you must use the debug library ([§6.10](#6.10)).

---

### `tonumber (e [, base])`

When called with no `base`, `tonumber` tries to convert its argument to a number. If the argument is already a number or a string convertible to a number, then `tonumber` returns this number; otherwise, it returns **fail**.

The conversion of strings can result in integers or floats, according to the lexical conventions of Lua (see [§3.1](#3.1)). The string may have leading and trailing spaces and a sign.

When called with `base`, then `e` must be a string to be interpreted as an integer numeral in that base. The base may be any integer between 2 and 36, inclusive. In bases above 10, the letter '`A`' (in either upper or lower case) represents 10, '`B`' represents 11, and so forth, with '`Z`' representing 35. If the string `e` is not a valid numeral in the given base, the function returns **fail**.

---

### `tostring (v)`

Receives a value of any type and converts it to a string in a human-readable format.

If the metatable of `v` has a `__tostring` field, then `tostring` calls the corresponding value with `v` as argument, and uses the result of the call as its result. Otherwise, if the metatable of `v` has a `__name` field with a string value, `tostring` may use that string in its final result.

For complete control of how numbers are converted, use [`string.format`](#pdf-string.format).

---

### `type (v)`

Returns the type of its only argument, coded as a string. The possible results of this function are "`nil`" (a string, not the value **nil**), "`number`", "`string`", "`boolean`", "`table`", "`function`", "`thread`", and "`userdata`".

---

### `_VERSION`

A global variable (not a function) that holds a string containing the running Lua version. The current value of this variable is "`Lua 5.4`".

---

### `warn (msg1, ···)`

Emits a warning with a message composed by the concatenation of all its arguments (which should be strings).

By convention, a one-piece message starting with '`@`' is intended to be a *control message*, which is a message to the warning system itself. In particular, the standard warning function in Lua recognizes the control messages "`@off`", to stop the emission of warnings, and "`@on`", to (re)start the emission; it ignores unknown control messages.

---

### `xpcall (f, msgh [, arg1, ···])`

This function is similar to [`pcall`](#pdf-pcall), except that it sets a new message handler `msgh`.

## 6.2 – Coroutine Manipulation

This library comprises the operations to manipulate coroutines, which come inside the table `coroutine`. See [§2.6](#2.6) for a general description of coroutines.

---

### `coroutine.close (co)`

Closes coroutine `co`, that is, closes all its pending to-be-closed variables and puts the coroutine in a dead state. The given coroutine must be dead or suspended. In case of error (either the original error that stopped the coroutine or errors in closing methods), returns **false** plus the error object; otherwise returns **true**.

---

### `coroutine.create (f)`

Creates a new coroutine, with body `f`. `f` must be a function. Returns this new coroutine, an object with type `"thread"`.

---

### `coroutine.isyieldable ([co])`

Returns **true** when the coroutine `co` can yield. The default for `co` is the running coroutine.

A coroutine is yieldable if it is not the main thread and it is not inside a non-yieldable C function.

---

### `coroutine.resume (co [, val1, ···])`

Starts or continues the execution of coroutine `co`. The first time you resume a coroutine, it starts running its body. The values `val1`, ... are passed as the arguments to the body function. If the coroutine has yielded, `resume` restarts it; the values `val1`, ... are passed as the results from the yield.

If the coroutine runs without any errors, `resume` returns **true** plus any values passed to `yield` (when the coroutine yields) or any values returned by the body function (when the coroutine terminates). If there is any error, `resume` returns **false** plus the error message.

---

### `coroutine.running ()`

Returns the running coroutine plus a boolean, **true** when the running coroutine is the main one.

---

### `coroutine.status (co)`

Returns the status of the coroutine `co`, as a string: `"running"`, if the coroutine is running (that is, it is the one that called `status`); `"suspended"`, if the coroutine is suspended in a call to `yield`, or if it has not started running yet; `"normal"` if the coroutine is active but not running (that is, it has resumed another coroutine); and `"dead"` if the coroutine has finished its body function, or if it has stopped with an error.

---

### `coroutine.wrap (f)`

Creates a new coroutine, with body `f`; `f` must be a function. Returns a function that resumes the coroutine each time it is called. Any arguments passed to this function behave as the extra arguments to `resume`. The function returns the same values returned by `resume`, except the first boolean. In case of error, the function closes the coroutine and propagates the error.

---

### `coroutine.yield (···)`

Suspends the execution of the calling coroutine. Any arguments to `yield` are passed as extra results to `resume`.

## 6.3 – Modules

The package library provides basic facilities for loading modules in Lua. It exports one function directly in the global environment: [`require`](#pdf-require). Everything else is exported in the table `package`.

---

### `require (modname)`

Loads the given module. The function starts by looking into the [`package.loaded`](#pdf-package.loaded) table to determine whether `modname` is already loaded. If it is, then `require` returns the value stored at `package.loaded[modname]`. (The absence of a second result in this case signals that this call did not have to load the module.) Otherwise, it tries to find a *loader* for the module.

To find a loader, `require` is guided by the table [`package.searchers`](#pdf-package.searchers). Each item in this table is a search function, that searches for the module in a particular way. By changing this table, we can change how `require` looks for a module. The following explanation is based on the default configuration for [`package.searchers`](#pdf-package.searchers).

First `require` queries `package.preload[modname]`. If it has a value, this value (which must be a function) is the loader. Otherwise `require` searches for a Lua loader using the path stored in [`package.path`](#pdf-package.path). If that also fails, it searches for a C loader using the path stored in [`package.cpath`](#pdf-package.cpath). If that also fails, it tries an *all-in-one* loader (see [`package.searchers`](#pdf-package.searchers)).

Once a loader is found, `require` calls the loader with two arguments: `modname` and an extra value, a *loader data*, also returned by the searcher. The loader data can be any value useful to the module; for the default searchers, it indicates where the loader was found. (For instance, if the loader came from a file, this extra value is the file path.) If the loader returns any non-nil value, `require` assigns the returned value to `package.loaded[modname]`. If the loader does not return a non-nil value and has not assigned any value to `package.loaded[modname]`, then `require` assigns **true** to this entry. In any case, `require` returns the final value of `package.loaded[modname]`. Besides that value, `require` also returns as a second result the loader data returned by the searcher, which indicates how `require` found the module.

If there is any error loading or running the module, or if it cannot find any loader for the module, then `require` raises an error.

---

### `package.config`

A string describing some compile-time configurations for packages. This string is a sequence of lines:

- The first line is the directory separator string. Default is '`\`' for Windows and '`/`' for all other systems.

- The second line is the character that separates templates in a path. Default is '`;`'.

- The third line is the string that marks the substitution points in a template. Default is '`?`'.

- The fourth line is a string that, in a path in Windows, is replaced by the executable's directory. Default is '`!`'.

- The fifth line is a mark to ignore all text after it when building the `luaopen_` function name. Default is '`-`'.

---

### `package.cpath`

A string with the path used by [`require`](#pdf-require) to search for a C loader.

Lua initializes the C path [`package.cpath`](#pdf-package.cpath) in the same way it initializes the Lua path [`package.path`](#pdf-package.path), using the environment variable `LUA_CPATH_5_4`, or the environment variable `LUA_CPATH`, or a default path defined in `luaconf.h`.

---

### `package.loaded`

A table used by [`require`](#pdf-require) to control which modules are already loaded. When you require a module `modname` and `package.loaded[modname]` is not false, [`require`](#pdf-require) simply returns the value stored there.

This variable is only a reference to the real table; assignments to this variable do not change the table used by [`require`](#pdf-require). The real table is stored in the C registry (see [§4.3](#4.3)), indexed by the key `LUA_LOADED_TABLE`, a string.

---

### `package.loadlib (libname, funcname)`

Dynamically links the host program with the C library `libname`.

If `funcname` is "`*`", then it only links with the library, making the symbols exported by the library available to other dynamically linked libraries. Otherwise, it looks for a function `funcname` inside the library and returns this function as a C function. So, `funcname` must follow the [`lua_CFunction`](#lua_CFunction) prototype (see [`lua_CFunction`](#lua_CFunction)).

This is a low-level function. It completely bypasses the package and module system. Unlike [`require`](#pdf-require), it does not perform any path searching and does not automatically adds extensions. `libname` must be the complete file name of the C library, including if necessary a path and an extension. `funcname` must be the exact name exported by the C library (which may depend on the C compiler and linker used).

This functionality is not supported by ISO C. As such, it is only available on some platforms (Windows, Linux, Mac OS X, Solaris, BSD, plus other Unix systems that support the `dlfcn` standard).

This function is inherently insecure, as it allows Lua to call any function in any readable dynamic library in the system. (Lua calls any function assuming the function has a proper prototype and respects a proper protocol (see [`lua_CFunction`](#lua_CFunction)). Therefore, calling an arbitrary function in an arbitrary dynamic library more often than not results in an access violation.)

---

### `package.path`

A string with the path used by [`require`](#pdf-require) to search for a Lua loader.

At start-up, Lua initializes this variable with the value of the environment variable `LUA_PATH_5_4` or the environment variable `LUA_PATH` or with a default path defined in `luaconf.h`, if those environment variables are not defined. A "`;;`" in the value of the environment variable is replaced by the default path.

---

### `package.preload`

A table to store loaders for specific modules (see [`require`](#pdf-require)).

This variable is only a reference to the real table; assignments to this variable do not change the table used by [`require`](#pdf-require). The real table is stored in the C registry (see [§4.3](#4.3)), indexed by the key `LUA_PRELOAD_TABLE`, a string.

---

### `package.searchers`

A table used by [`require`](#pdf-require) to control how to find modules.

Each entry in this table is a *searcher function*. When looking for a module, [`require`](#pdf-require) calls each of these searchers in ascending order, with the module name (the argument given to [`require`](#pdf-require)) as its sole argument. If the searcher finds the module, it returns another function, the module *loader*, plus an extra value, a *loader data*, that will be passed to that loader and returned as a second result by [`require`](#pdf-require). If it cannot find the module, it returns a string explaining why (or **nil** if it has nothing to say).

Lua initializes this table with four searcher functions.

The first searcher simply looks for a loader in the [`package.preload`](#pdf-package.preload) table.

The second searcher looks for a loader as a Lua library, using the path stored at [`package.path`](#pdf-package.path). The search is done as described in function [`package.searchpath`](#pdf-package.searchpath).

The third searcher looks for a loader as a C library, using the path given by the variable [`package.cpath`](#pdf-package.cpath). Again, the search is done as described in function [`package.searchpath`](#pdf-package.searchpath). For instance, if the C path is the string

```
"./?.so;./?.dll;/usr/local/?/init.so"
```

the searcher for module `foo` will try to open the files `./foo.so`, `./foo.dll`, and `/usr/local/foo/init.so`, in that order. Once it finds a C library, this searcher first uses a dynamic link facility to link the application with the library. Then it tries to find a C function inside the library to be used as the loader. The name of this C function is the string "`luaopen_`" concatenated with a copy of the module name where each dot is replaced by an underscore. Moreover, if the module name has a hyphen, its suffix after (and including) the first hyphen is removed. For instance, if the module name is `a.b.c-v2.1`, the function name will be `luaopen_a_b_c`.

The fourth searcher tries an *all-in-one loader*. It searches the C path for a library for the root name of the given module. For instance, when requiring `a.b.c`, it will search for a C library for `a`. If found, it looks into it for an open function for the submodule; in our example, that would be `luaopen_a_b_c`. With this facility, a package can pack several C submodules into one single library, with each submodule keeping its original open function.

All searchers except the first one (preload) return as the extra value the file path where the module was found, as returned by [`package.searchpath`](#pdf-package.searchpath). The first searcher always returns the string "`:preload:`".

Searchers should raise no errors and have no side effects in Lua. (They may have side effects in C, for instance by linking the application with a library.)

---

### `package.searchpath (name, path [, sep [, rep]])`

Searches for the given `name` in the given `path`.

A path is a string containing a sequence of *templates* separated by semicolons. For each template, the function replaces each interrogation mark (if any) in the template with a copy of `name` wherein all occurrences of `sep` (a dot, by default) were replaced by `rep` (the system's directory separator, by default), and then tries to open the resulting file name.

For instance, if the path is the string

```
"./?.lua;./?.lc;/usr/local/?/init.lua"
```

the search for the name `foo.a` will try to open the files `./foo/a.lua`, `./foo/a.lc`, and `/usr/local/foo/a/init.lua`, in that order.

Returns the resulting name of the first file that it can open in read mode (after closing the file), or **fail** plus an error message if none succeeds. (This error message lists all file names it tried to open.)

## 6.4 – String Manipulation

This library provides generic functions for string manipulation, such as finding and extracting substrings, and pattern matching. When indexing a string in Lua, the first character is at position 1 (not at 0, as in C). Indices are allowed to be negative and are interpreted as indexing backwards, from the end of the string. Thus, the last character is at position -1, and so on.

The string library provides all its functions inside the table `string`. It also sets a metatable for strings where the `__index` field points to the `string` table. Therefore, you can use the string functions in object-oriented style. For instance, `string.byte(s,i)` can be written as `s:byte(i)`.

The string library assumes one-byte character encodings.

---

### `string.byte (s [, i [, j]])`

Returns the internal numeric codes of the characters `s[i]`, `s[i+1]`, ..., `s[j]`. The default value for `i` is 1; the default value for `j` is `i`. These indices are corrected following the same rules of function [`string.sub`](#pdf-string.sub).

Numeric codes are not necessarily portable across platforms.

---

### `string.char (···)`

Receives zero or more integers. Returns a string with length equal to the number of arguments, in which each character has the internal numeric code equal to its corresponding argument.

Numeric codes are not necessarily portable across platforms.

---

### `string.dump (function [, strip])`

Returns a string containing a binary representation (a *binary chunk*) of the given function, so that a later [`load`](#pdf-load) on this string returns a copy of the function (but with new upvalues). If `strip` is a true value, the binary representation may not include all debug information about the function, to save space.

Functions with upvalues have only their number of upvalues saved. When (re)loaded, those upvalues receive fresh instances. (See the [`load`](#pdf-load) function for details about how these upvalues are initialized. You can use the debug library to serialize and reload the upvalues of a function in a way adequate to your needs.)

---

### `string.find (s, pattern [, init [, plain]])`

Looks for the first match of `pattern` (see [§6.4.1](#6.4.1)) in the string `s`. If it finds a match, then `find` returns the indices of `s` where this occurrence starts and ends; otherwise, it returns **fail**. A third, optional numeric argument `init` specifies where to start the search; its default value is 1 and can be negative. A **true** as a fourth, optional argument `plain` turns off the pattern matching facilities, so the function does a plain "find substring" operation, with no characters in `pattern` being considered magic.

If the pattern has captures, then in a successful match the captured values are also returned, after the two indices.

---

### `string.format (formatstring, ···)`

Returns a formatted version of its variable number of arguments following the description given in its first argument, which must be a string. The format string follows the same rules as the ISO C function `sprintf`. The only differences are that the conversion specifiers and modifiers `F`, `n`, `*`, `h`, `L`, and `l` are not supported and that there is an extra specifier, `q`. Both width and precision, when present, are limited to two digits.

The specifier `q` formats booleans, nil, numbers, and strings in a way that the result is a valid constant in Lua source code. Booleans and nil are written in the obvious way (`true`, `false`, `nil`). Floats are written in hexadecimal, to preserve full precision. A string is written between double quotes, using escape sequences when necessary to ensure that it can safely be read back by the Lua interpreter. For instance, the call

```
string.format('%q', 'a string with "quotes" and \n new line')
```

may produce the string:

```
"a string with \"quotes\" and \
 new line"
```

This specifier does not support modifiers (flags, width, precision).

The conversion specifiers `A`, `a`, `E`, `e`, `f`, `G`, and `g` all expect a number as argument. The specifiers `c`, `d`, `i`, `o`, `u`, `X`, and `x` expect an integer. When Lua is compiled with a C89 compiler, the specifiers `A` and `a` (hexadecimal floats) do not support modifiers.

The specifier `s` expects a string; if its argument is not a string, it is converted to one following the same rules of [`tostring`](#pdf-tostring). If the specifier has any modifier, the corresponding string argument should not contain embedded zeros.

The specifier `p` formats the pointer returned by [`lua_topointer`](#lua_topointer). That gives a unique string identifier for tables, userdata, threads, strings, and functions. For other values (numbers, nil, booleans), this specifier results in a string representing the pointer `NULL`.

---

### `string.gmatch (s, pattern [, init])`

Returns an iterator function that, each time it is called, returns the next captures from `pattern` (see [§6.4.1](#6.4.1)) over the string `s`. If `pattern` specifies no captures, then the whole match is produced in each call. A third, optional numeric argument `init` specifies where to start the search; its default value is 1 and can be negative.

As an example, the following loop will iterate over all the words from string `s`, printing one per line:

```
s = "hello world from Lua"
for w in string.gmatch(s, "%a+") do
  print(w)
end
```

The next example collects all pairs `key=value` from the given string into a table:

```
t = {}
s = "from=world, to=Lua"
for k, v in string.gmatch(s, "(%w+)=(%w+)") do
  t[k] = v
end
```

For this function, a caret '`^`' at the start of a pattern does not work as an anchor, as this would prevent the iteration.

---

### `string.gsub (s, pattern, repl [, n])`

Returns a copy of `s` in which all (or the first `n`, if given) occurrences of the `pattern` (see [§6.4.1](#6.4.1)) have been replaced by a replacement string specified by `repl`, which can be a string, a table, or a function. `gsub` also returns, as its second value, the total number of matches that occurred. The name `gsub` comes from *Global SUBstitution*.

If `repl` is a string, then its value is used for replacement. The character `%` works as an escape character: any sequence in `repl` of the form `%d`, with *d* between 1 and 9, stands for the value of the *d*-th captured substring; the sequence `%0` stands for the whole match; the sequence `%%` stands for a single `%`.

If `repl` is a table, then the table is queried for every match, using the first capture as the key.

If `repl` is a function, then this function is called every time a match occurs, with all captured substrings passed as arguments, in order.

In any case, if the pattern specifies no captures, then it behaves as if the whole pattern was inside a capture.

If the value returned by the table query or by the function call is a string or a number, then it is used as the replacement string; otherwise, if it is **false** or **nil**, then there is no replacement (that is, the original match is kept in the string).

Here are some examples:

```
x = string.gsub("hello world", "(%w+)", "%1 %1")
--> x="hello hello world world"

x = string.gsub("hello world", "%w+", "%0 %0", 1)
--> x="hello hello world"

x = string.gsub("hello world from Lua", "(%w+)%s*(%w+)", "%2 %1")
--> x="world hello Lua from"

x = string.gsub("home = $HOME, user = $USER", "%$(%w+)", os.getenv)
--> x="home = /home/roberto, user = roberto"

x = string.gsub("4+5 = $return 4+5$", "%$(.-)%$", function (s)
      return load(s)()
    end)
--> x="4+5 = 9"

local t = {name="lua", version="5.4"}
x = string.gsub("$name-$version.tar.gz", "%$(%w+)", t)
--> x="lua-5.4.tar.gz"
```

---

### `string.len (s)`

Receives a string and returns its length. The empty string `""` has length 0. Embedded zeros are counted, so `"a\000bc\000"` has length 5.

---

### `string.lower (s)`

Receives a string and returns a copy of this string with all uppercase letters changed to lowercase. All other characters are left unchanged. The definition of what an uppercase letter is depends on the current locale.

---

### `string.match (s, pattern [, init])`

Looks for the first *match* of the `pattern` (see [§6.4.1](#6.4.1)) in the string `s`. If it finds one, then `match` returns the captures from the pattern; otherwise it returns **fail**. If `pattern` specifies no captures, then the whole match is returned. A third, optional numeric argument `init` specifies where to start the search; its default value is 1 and can be negative.

---

### `string.pack (fmt, v1, v2, ···)`

Returns a binary string containing the values `v1`, `v2`, etc. serialized in binary form (packed) according to the format string `fmt` (see [§6.4.2](#6.4.2)).

---

### `string.packsize (fmt)`

Returns the length of a string resulting from [`string.pack`](#pdf-string.pack) with the given format. The format string cannot have the variable-length options '`s`' or '`z`' (see [§6.4.2](#6.4.2)).

---

### `string.rep (s, n [, sep])`

Returns a string that is the concatenation of `n` copies of the string `s` separated by the string `sep`. The default value for `sep` is the empty string (that is, no separator). Returns the empty string if `n` is not positive.

(Note that it is very easy to exhaust the memory of your machine with a single call to this function.)

---

### `string.reverse (s)`

Returns a string that is the string `s` reversed.

---

### `string.sub (s, i [, j])`

Returns the substring of `s` that starts at `i` and continues until `j`; `i` and `j` can be negative. If `j` is absent, then it is assumed to be equal to -1 (which is the same as the string length). In particular, the call `string.sub(s,1,j)` returns a prefix of `s` with length `j`, and `string.sub(s, -i)` (for a positive `i`) returns a suffix of `s` with length `i`.

If, after the translation of negative indices, `i` is less than 1, it is corrected to 1. If `j` is greater than the string length, it is corrected to that length. If, after these corrections, `i` is greater than `j`, the function returns the empty string.

---

### `string.unpack (fmt, s [, pos])`

Returns the values packed in string `s` (see [`string.pack`](#pdf-string.pack)) according to the format string `fmt` (see [§6.4.2](#6.4.2)). An optional `pos` marks where to start reading in `s` (default is 1). After the read values, this function also returns the index of the first unread byte in `s`.

---

### `string.upper (s)`

Receives a string and returns a copy of this string with all lowercase letters changed to uppercase. All other characters are left unchanged. The definition of what a lowercase letter is depends on the current locale.

### 6.4.1 – Patterns

Patterns in Lua are described by regular strings, which are interpreted as patterns by the pattern-matching functions [`string.find`](#pdf-string.find), [`string.gmatch`](#pdf-string.gmatch), [`string.gsub`](#pdf-string.gsub), and [`string.match`](#pdf-string.match). This section describes the syntax and the meaning (that is, what they match) of these strings.

#### Character Class:

A *character class* is used to represent a set of characters. The following combinations are allowed in describing a character class:

- ***x*: ** (where *x* is not one of the *magic characters* `^$()%.[]*+-?`) represents the character *x* itself.

- **`.`: ** (a dot) represents all characters.

- **`%a`: ** represents all letters.

- **`%c`: ** represents all control characters.

- **`%d`: ** represents all digits.

- **`%g`: ** represents all printable characters except space.

- **`%l`: ** represents all lowercase letters.

- **`%p`: ** represents all punctuation characters.

- **`%s`: ** represents all space characters.

- **`%u`: ** represents all uppercase letters.

- **`%w`: ** represents all alphanumeric characters.

- **`%x`: ** represents all hexadecimal digits.

- **`%x`: ** (where *x* is any non-alphanumeric character) represents the character *x*. This is the standard way to escape the magic characters. Any non-alphanumeric character (including all punctuation characters, even the non-magical) can be preceded by a '`%`' to represent itself in a pattern.

- **`[set]`: ** represents the class which is the union of all characters in *set*. A range of characters can be specified by separating the end characters of the range, in ascending order, with a '`-`'. All classes `%`*x* described above can also be used as components in *set*. All other characters in *set* represent themselves. For example, `[%w_]` (or `[_%w]`) represents all alphanumeric characters plus the underscore, `[0-7]` represents the octal digits, and `[0-7%l%-]` represents the octal digits plus the lowercase letters plus the '`-`' character.

  You can put a closing square bracket in a set by positioning it as the first character in the set. You can put a hyphen in a set by positioning it as the first or the last character in the set. (You can also use an escape for both cases.)

  The interaction between ranges and classes is not defined. Therefore, patterns like `[%a-z]` or `[a-%%]` have no meaning.

- **`[^set]`: ** represents the complement of *set*, where *set* is interpreted as above.

For all classes represented by single letters (`%a`, `%c`, etc.), the corresponding uppercase letter represents the complement of the class. For instance, `%S` represents all non-space characters.

The definitions of letter, space, and other character groups depend on the current locale. In particular, the class `[a-z]` may not be equivalent to `%l`.

#### Pattern Item:

A *pattern item* can be

- a single character class, which matches any single character in the class;

- a single character class followed by '`*`', which matches sequences of zero or more characters in the class. These repetition items will always match the longest possible sequence;

- a single character class followed by '`+`', which matches sequences of one or more characters in the class. These repetition items will always match the longest possible sequence;

- a single character class followed by '`-`', which also matches sequences of zero or more characters in the class. Unlike '`*`', these repetition items will always match the shortest possible sequence;

- a single character class followed by '`?`', which matches zero or one occurrence of a character in the class. It always matches one occurrence if possible;

- `%n`, for *n* between 1 and 9; such item matches a substring equal to the *n*-th captured string (see below);

- `%bxy`, where *x* and *y* are two distinct characters; such item matches strings that start with *x*, end with *y*, and where the *x* and *y* are *balanced*. This means that, if one reads the string from left to right, counting *+1* for an *x* and *-1* for a *y*, the ending *y* is the first *y* where the count reaches 0. For instance, the item `%b()` matches expressions with balanced parentheses.

- `%f[set]`, a *frontier pattern*; such item matches an empty string at any position such that the next character belongs to *set* and the previous character does not belong to *set*. The set *set* is interpreted as previously described. The beginning and the end of the subject are handled as if they were the character '`\0`'.

#### Pattern:

A *pattern* is a sequence of pattern items. A caret '`^`' at the beginning of a pattern anchors the match at the beginning of the subject string. A '`$`' at the end of a pattern anchors the match at the end of the subject string. At other positions, '`^`' and '`$`' have no special meaning and represent themselves.

#### Captures:

A pattern can contain sub-patterns enclosed in parentheses; they describe *captures*. When a match succeeds, the substrings of the subject string that match captures are stored (*captured*) for future use. Captures are numbered according to their left parentheses. For instance, in the pattern `"(a*(.)%w(%s*))"`, the part of the string matching `"a*(.)%w(%s*)"` is stored as the first capture, and therefore has number 1; the character matching "`.`" is captured with number 2, and the part matching "`%s*`" has number 3.

As a special case, the capture `()` captures the current string position (a number). For instance, if we apply the pattern `"()aa()"` on the string `"flaaap"`, there will be two captures: 3 and 5.

#### Multiple matches:

The function [`string.gsub`](#pdf-string.gsub) and the iterator [`string.gmatch`](#pdf-string.gmatch) match multiple occurrences of the given pattern in the subject. For these functions, a new match is considered valid only if it ends at least one byte after the end of the previous match. In other words, the pattern machine never accepts the empty string as a match immediately after another match. As an example, consider the results of the following code:

```
> string.gsub("abc", "()a*()", print);
--> 1   2
--> 3   3
--> 4   4
```

The second and third results come from Lua matching an empty string after '`b`' and another one after '`c`'. Lua does not match an empty string after '`a`', because it would end at the same position of the previous match.

### 6.4.2 – Format Strings for Pack and Unpack

The first argument to [`string.pack`](#pdf-string.pack), [`string.packsize`](#pdf-string.packsize), and [`string.unpack`](#pdf-string.unpack) is a format string, which describes the layout of the structure being created or read.

A format string is a sequence of conversion options. The conversion options are as follows:

- **`<`: **sets little endian

- **`>`: **sets big endian

- **`=`: **sets native endian

- **`![n]`: **sets maximum alignment to `n` (default is native alignment)

- **`b`: **a signed byte (`char`)

- **`B`: **an unsigned byte (`char`)

- **`h`: **a signed `short` (native size)

- **`H`: **an unsigned `short` (native size)

- **`l`: **a signed `long` (native size)

- **`L`: **an unsigned `long` (native size)

- **`j`: **a `lua_Integer`

- **`J`: **a `lua_Unsigned`

- **`T`: **a `size_t` (native size)

- **`i[n]`: **a signed `int` with `n` bytes (default is native size)

- **`I[n]`: **an unsigned `int` with `n` bytes (default is native size)

- **`f`: **a `float` (native size)

- **`d`: **a `double` (native size)

- **`n`: **a `lua_Number`

- **`cn`: **a fixed-sized string with `n` bytes

- **`z`: **a zero-terminated string

- **`s[n]`: **a string preceded by its length coded as an unsigned integer with `n` bytes (default is a `size_t`)

- **`x`: **one byte of padding

- **`Xop`: **an empty item that aligns according to option `op` (which is otherwise ignored)

- **'` `': **(space) ignored

(A "`[n]`" means an optional integral numeral.) Except for padding, spaces, and configurations (options "`xX !`"), each option corresponds to an argument in [`string.pack`](#pdf-string.pack) or a result in [`string.unpack`](#pdf-string.unpack).

For options "`!n`", "`sn`", "`in`", and "`In`", `n` can be any integer between 1 and 16. All integral options check overflows; [`string.pack`](#pdf-string.pack) checks whether the given value fits in the given size; [`string.unpack`](#pdf-string.unpack) checks whether the read value fits in a Lua integer. For the unsigned options, Lua integers are treated as unsigned values too.

Any format string starts as if prefixed by "`!1=`", that is, with maximum alignment of 1 (no alignment) and native endianness.

Native endianness assumes that the whole system is either big or little endian. The packing functions will not emulate correctly the behavior of mixed-endian formats.

Alignment works as follows: For each option, the format gets extra padding until the data starts at an offset that is a multiple of the minimum between the option size and the maximum alignment; this minimum must be a power of 2. Options "`c`" and "`z`" are not aligned; option "`s`" follows the alignment of its starting integer.

All padding is filled with zeros by [`string.pack`](#pdf-string.pack) and ignored by [`string.unpack`](#pdf-string.unpack).

## 6.5 – UTF-8 Support

This library provides basic support for UTF-8 encoding. It provides all its functions inside the table `utf8`. This library does not provide any support for Unicode other than the handling of the encoding. Any operation that needs the meaning of a character, such as character classification, is outside its scope.

Unless stated otherwise, all functions that expect a byte position as a parameter assume that the given position is either the start of a byte sequence or one plus the length of the subject string. As in the string library, negative indices count from the end of the string.

Functions that create byte sequences accept all values up to `0x7FFFFFFF`, as defined in the original UTF-8 specification; that implies byte sequences of up to six bytes.

Functions that interpret byte sequences only accept valid sequences (well formed and not overlong). By default, they only accept byte sequences that result in valid Unicode code points, rejecting values greater than `10FFFF` and surrogates. A boolean argument `lax`, when available, lifts these checks, so that all values up to `0x7FFFFFFF` are accepted. (Not well formed and overlong sequences are still rejected.)

---

### `utf8.char (···)`

Receives zero or more integers, converts each one to its corresponding UTF-8 byte sequence and returns a string with the concatenation of all these sequences.

---

### `utf8.charpattern`

The pattern (a string, not a function) "`[\0-\x7F\xC2-\xFD][\x80-\xBF]*`" (see [§6.4.1](#6.4.1)), which matches exactly one UTF-8 byte sequence, assuming that the subject is a valid UTF-8 string.

---

### `utf8.codes (s [, lax])`

Returns values so that the construction

```
for p, c in utf8.codes(s) do body end
```

will iterate over all UTF-8 characters in string `s`, with `p` being the position (in bytes) and `c` the code point of each character. It raises an error if it meets any invalid byte sequence.

---

### `utf8.codepoint (s [, i [, j [, lax]]])`

Returns the code points (as integers) from all characters in `s` that start between byte position `i` and `j` (both included). The default for `i` is 1 and for `j` is `i`. It raises an error if it meets any invalid byte sequence.

---

### `utf8.len (s [, i [, j [, lax]]])`

Returns the number of UTF-8 characters in string `s` that start between positions `i` and `j` (both inclusive). The default for `i` is 1 and for `j` is -1. If it finds any invalid byte sequence, returns **fail** plus the position of the first invalid byte.

---

### `utf8.offset (s, n [, i])`

Returns the position (in bytes) where the encoding of the `n`-th character of `s` (counting from position `i`) starts. A negative `n` gets characters before position `i`. The default for `i` is 1 when `n` is non-negative and `#s + 1` otherwise, so that `utf8.offset(s, -n)` gets the offset of the `n`-th character from the end of the string. If the specified character is neither in the subject nor right after its end, the function returns **fail**.

As a special case, when `n` is 0 the function returns the start of the encoding of the character that contains the `i`-th byte of `s`.

This function assumes that `s` is a valid UTF-8 string.

## 6.6 – Table Manipulation

This library provides generic functions for table manipulation. It provides all its functions inside the table `table`.

Remember that, whenever an operation needs the length of a table, all caveats about the length operator apply (see [§3.4.7](#3.4.7)). All functions ignore non-numeric keys in the tables given as arguments.

---

### `table.concat (list [, sep [, i [, j]]])`

Given a list where all elements are strings or numbers, returns the string `list[i]..sep..list[i+1] ··· sep..list[j]`. The default value for `sep` is the empty string, the default for `i` is 1, and the default for `j` is `#list`. If `i` is greater than `j`, returns the empty string.

---

### `table.insert (list, [pos,] value)`

Inserts element `value` at position `pos` in `list`, shifting up the elements `list[pos], list[pos+1], ···, list[#list]`. The default value for `pos` is `#list+1`, so that a call `table.insert(t,x)` inserts `x` at the end of the list `t`.

---

### `table.move (a1, f, e, t [,a2])`

Moves elements from the table `a1` to the table `a2`, performing the equivalent to the following multiple assignment: `a2[t],··· = a1[f],···,a1[e]`. The default for `a2` is `a1`. The destination range can overlap with the source range. The number of elements to be moved must fit in a Lua integer.

Returns the destination table `a2`.

---

### `table.pack (···)`

Returns a new table with all arguments stored into keys 1, 2, etc. and with a field "`n`" with the total number of arguments. Note that the resulting table may not be a sequence, if some arguments are **nil**.

---

### `table.remove (list [, pos])`

Removes from `list` the element at position `pos`, returning the value of the removed element. When `pos` is an integer between 1 and `#list`, it shifts down the elements `list[pos+1], list[pos+2], ···, list[#list]` and erases element `list[#list]`; The index `pos` can also be 0 when `#list` is 0, or `#list + 1`.

The default value for `pos` is `#list`, so that a call `table.remove(l)` removes the last element of the list `l`.

---

### `table.sort (list [, comp])`

Sorts the list elements in a given order, *in-place*, from `list[1]` to `list[#list]`. If `comp` is given, then it must be a function that receives two list elements and returns true when the first element must come before the second in the final order, so that, after the sort, `i <= j` implies `not comp(list[j],list[i])`. If `comp` is not given, then the standard Lua operator `<` is used instead.

The `comp` function must define a consistent order; more formally, the function must define a strict weak order. (A weak order is similar to a total order, but it can equate different elements for comparison purposes.)

The sort algorithm is not stable: Different elements considered equal by the given order may have their relative positions changed by the sort.

---

### `table.unpack (list [, i [, j]])`

Returns the elements from the given list. This function is equivalent to

```
return list[i], list[i+1], ···, list[j]
```

By default, `i` is 1 and `j` is `#list`.

## 6.7 – Mathematical Functions

This library provides basic mathematical functions. It provides all its functions and constants inside the table `math`. Functions with the annotation "`integer/float`" give integer results for integer arguments and float results for non-integer arguments. The rounding functions [`math.ceil`](#pdf-math.ceil), [`math.floor`](#pdf-math.floor), and [`math.modf`](#pdf-math.modf) return an integer when the result fits in the range of an integer, or a float otherwise.

---

### `math.abs (x)`

Returns the maximum value between `x` and `-x`. (integer/float)

---

### `math.acos (x)`

Returns the arc cosine of `x` (in radians).

---

### `math.asin (x)`

Returns the arc sine of `x` (in radians).

---

### `math.atan (y [, x])`

Returns the arc tangent of `y/x` (in radians), using the signs of both arguments to find the quadrant of the result. It also handles correctly the case of `x` being zero.

The default value for `x` is 1, so that the call `math.atan(y)` returns the arc tangent of `y`.

---

### `math.ceil (x)`

Returns the smallest integral value greater than or equal to `x`.

---

### `math.cos (x)`

Returns the cosine of `x` (assumed to be in radians).

---

### `math.deg (x)`

Converts the angle `x` from radians to degrees.

---

### `math.exp (x)`

Returns the value *e^x* (where `e` is the base of natural logarithms).

---

### `math.floor (x)`

Returns the largest integral value less than or equal to `x`.

---

### `math.fmod (x, y)`

Returns the remainder of the division of `x` by `y` that rounds the quotient towards zero. (integer/float)

---

### `math.huge`

The float value `HUGE_VAL`, a value greater than any other numeric value.

---

### `math.log (x [, base])`

Returns the logarithm of `x` in the given base. The default for `base` is *e* (so that the function returns the natural logarithm of `x`).

---

### `math.max (x, ···)`

Returns the argument with the maximum value, according to the Lua operator `<`.

---

### `math.maxinteger`

An integer with the maximum value for an integer.

---

### `math.min (x, ···)`

Returns the argument with the minimum value, according to the Lua operator `<`.

---

### `math.mininteger`

An integer with the minimum value for an integer.

---

### `math.modf (x)`

Returns the integral part of `x` and the fractional part of `x`. Its second result is always a float.

---

### `math.pi`

The value of *π*.

---

### `math.rad (x)`

Converts the angle `x` from degrees to radians.

---

### `math.random ([m [, n]])`

When called without arguments, returns a pseudo-random float with uniform distribution in the range *[0,1)*. When called with two integers `m` and `n`, `math.random` returns a pseudo-random integer with uniform distribution in the range *[m, n]*. The call `math.random(n)`, for a positive `n`, is equivalent to `math.random(1,n)`. The call `math.random(0)` produces an integer with all bits (pseudo)random.

This function uses the `xoshiro256**` algorithm to produce pseudo-random 64-bit integers, which are the results of calls with argument 0. Other results (ranges and floats) are unbiased extracted from these integers.

Lua initializes its pseudo-random generator with the equivalent of a call to [`math.randomseed`](#pdf-math.randomseed) with no arguments, so that `math.random` should generate different sequences of results each time the program runs.

---

### `math.randomseed ([x [, y]])`

When called with at least one argument, the integer parameters `x` and `y` are joined into a 128-bit *seed* that is used to reinitialize the pseudo-random generator; equal seeds produce equal sequences of numbers. The default for `y` is zero.

When called with no arguments, Lua generates a seed with a weak attempt for randomness.

This function returns the two seed components that were effectively used, so that setting them again repeats the sequence.

To ensure a required level of randomness to the initial state (or contrarily, to have a deterministic sequence, for instance when debugging a program), you should call [`math.randomseed`](#pdf-math.randomseed) with explicit arguments.

---

### `math.sin (x)`

Returns the sine of `x` (assumed to be in radians).

---

### `math.sqrt (x)`

Returns the square root of `x`. (You can also use the expression `x^0.5` to compute this value.)

---

### `math.tan (x)`

Returns the tangent of `x` (assumed to be in radians).

---

### `math.tointeger (x)`

If the value `x` is convertible to an integer, returns that integer. Otherwise, returns **fail**.

---

### `math.type (x)`

Returns "`integer`" if `x` is an integer, "`float`" if it is a float, or **fail** if `x` is not a number.

---

### `math.ult (m, n)`

Returns a boolean, **true** if and only if integer `m` is below integer `n` when they are compared as unsigned integers.

## 6.8 – Input and Output Facilities

The I/O library provides two different styles for file manipulation. The first one uses implicit file handles; that is, there are operations to set a default input file and a default output file, and all input/output operations are done over these default files. The second style uses explicit file handles.

When using implicit file handles, all operations are supplied by table `io`. When using explicit file handles, the operation [`io.open`](#pdf-io.open) returns a file handle and then all operations are supplied as methods of the file handle.

The metatable for file handles provides metamethods for `__gc` and `__close` that try to close the file when called.

The table `io` also provides three predefined file handles with their usual meanings from C: `io.stdin`, `io.stdout`, and `io.stderr`. The I/O library never closes these files.

Unless otherwise stated, all I/O functions return **fail** on failure, plus an error message as a second result and a system-dependent error code as a third result, and some non-false value on success. On non-POSIX systems, the computation of the error message and error code in case of errors may be not thread safe, because they rely on the global C variable `errno`.

---

### `io.close ([file])`

Equivalent to `file:close()`. Without a `file`, closes the default output file.

---

### `io.flush ()`

Equivalent to `io.output():flush()`.

---

### `io.input ([file])`

When called with a file name, it opens the named file (in text mode), and sets its handle as the default input file. When called with a file handle, it simply sets this file handle as the default input file. When called without arguments, it returns the current default input file.

In case of errors this function raises the error, instead of returning an error code.

---

### `io.lines ([filename, ···])`

Opens the given file name in read mode and returns an iterator function that works like `file:lines(···)` over the opened file. When the iterator function fails to read any value, it automatically closes the file. Besides the iterator function, `io.lines` returns three other values: two **nil** values as placeholders, plus the created file handle. Therefore, when used in a generic **for** loop, the file is closed also if the loop is interrupted by an error or a **break**.

The call `io.lines()` (with no file name) is equivalent to `io.input():lines("l")`; that is, it iterates over the lines of the default input file. In this case, the iterator does not close the file when the loop ends.

In case of errors opening the file, this function raises the error, instead of returning an error code.

---

### `io.open (filename [, mode])`

This function opens a file, in the mode specified in the string `mode`. In case of success, it returns a new file handle.

The `mode` string can be any of the following:

- **"`r`": ** read mode (the default);

- **"`w`": ** write mode;

- **"`a`": ** append mode;

- **"`r+`": ** update mode, all previous data is preserved;

- **"`w+`": ** update mode, all previous data is erased;

- **"`a+`": ** append update mode, previous data is preserved, writing is only allowed at the end of file.

The `mode` string can also have a '`b`' at the end, which is needed in some systems to open the file in binary mode.

---

### `io.output ([file])`

Similar to [`io.input`](#pdf-io.input), but operates over the default output file.

---

### `io.popen (prog [, mode])`

This function is system dependent and is not available on all platforms.

Starts the program `prog` in a separated process and returns a file handle that you can use to read data from this program (if `mode` is `"r"`, the default) or to write data to this program (if `mode` is `"w"`).

---

### `io.read (···)`

Equivalent to `io.input():read(···)`.

---

### `io.tmpfile ()`

In case of success, returns a handle for a temporary file. This file is opened in update mode and it is automatically removed when the program ends.

---

### `io.type (obj)`

Checks whether `obj` is a valid file handle. Returns the string `"file"` if `obj` is an open file handle, `"closed file"` if `obj` is a closed file handle, or **fail** if `obj` is not a file handle.

---

### `io.write (···)`

Equivalent to `io.output():write(···)`.

---

### `file:close ()`

Closes `file`. Note that files are automatically closed when their handles are garbage collected, but that takes an unpredictable amount of time to happen.

When closing a file handle created with [`io.popen`](#pdf-io.popen), [`file:close`](#pdf-file:close) returns the same values returned by [`os.execute`](#pdf-os.execute).

---

### `file:flush ()`

Saves any written data to `file`.

---

### `file:lines (···)`

Returns an iterator function that, each time it is called, reads the file according to the given formats. When no format is given, uses "`l`" as a default. As an example, the construction

```
for c in file:lines(1) do body end
```

will iterate over all characters of the file, starting at the current position. Unlike [`io.lines`](#pdf-io.lines), this function does not close the file when the loop ends.

---

### `file:read (···)`

Reads the file `file`, according to the given formats, which specify what to read. For each format, the function returns a string or a number with the characters read, or **fail** if it cannot read data with the specified format. (In this latter case, the function does not read subsequent formats.) When called without arguments, it uses a default format that reads the next line (see below).

The available formats are

- **"`n`": ** reads a numeral and returns it as a float or an integer, following the lexical conventions of Lua. (The numeral may have leading whitespaces and a sign.) This format always reads the longest input sequence that is a valid prefix for a numeral; if that prefix does not form a valid numeral (e.g., an empty string, "`0x`", or "`3.4e-`") or it is too long (more than 200 characters), it is discarded and the format returns **fail**.

- **"`a`": ** reads the whole file, starting at the current position. On end of file, it returns the empty string; this format never fails.

- **"`l`": ** reads the next line skipping the end of line, returning **fail** on end of file. This is the default format.

- **"`L`": ** reads the next line keeping the end-of-line character (if present), returning **fail** on end of file.

- ***number*: ** reads a string with up to this number of bytes, returning **fail** on end of file. If `number` is zero, it reads nothing and returns an empty string, or **fail** on end of file.

The formats "`l`" and "`L`" should be used only for text files.

---

### `file:seek ([whence [, offset]])`

Sets and gets the file position, measured from the beginning of the file, to the position given by `offset` plus a base specified by the string `whence`, as follows:

- **"`set`": ** base is position 0 (beginning of the file);

- **"`cur`": ** base is current position;

- **"`end`": ** base is end of file;

In case of success, `seek` returns the final file position, measured in bytes from the beginning of the file. If `seek` fails, it returns **fail**, plus a string describing the error.

The default value for `whence` is `"cur"`, and for `offset` is 0. Therefore, the call `file:seek()` returns the current file position, without changing it; the call `file:seek("set")` sets the position to the beginning of the file (and returns 0); and the call `file:seek("end")` sets the position to the end of the file, and returns its size.

---

### `file:setvbuf (mode [, size])`

Sets the buffering mode for a file. There are three available modes:

- **"`no`": ** no buffering.

- **"`full`": ** full buffering.

- **"`line`": ** line buffering.

For the last two cases, `size` is a hint for the size of the buffer, in bytes. The default is an appropriate size.

The specific behavior of each mode is non portable; check the underlying ISO C function `setvbuf` in your platform for more details.

---

### `file:write (···)`

Writes the value of each of its arguments to `file`. The arguments must be strings or numbers.

In case of success, this function returns `file`.

## 6.9 – Operating System Facilities

This library is implemented through table `os`.

---

### `os.clock ()`

Returns an approximation of the amount in seconds of CPU time used by the program, as returned by the underlying ISO C function `clock`.

---

### `os.date ([format [, time]])`

Returns a string or a table containing date and time, formatted according to the given string `format`.

If the `time` argument is present, this is the time to be formatted (see the [`os.time`](#pdf-os.time) function for a description of this value). Otherwise, `date` formats the current time.

If `format` starts with '`!`', then the date is formatted in Coordinated Universal Time. After this optional character, if `format` is the string "`*t`", then `date` returns a table with the following fields: `year`, `month` (1–12), `day` (1–31), `hour` (0–23), `min` (0–59), `sec` (0–61, due to leap seconds), `wday` (weekday, 1–7, Sunday is 1), `yday` (day of the year, 1–366), and `isdst` (daylight saving flag, a boolean). This last field may be absent if the information is not available.

If `format` is not "`*t`", then `date` returns the date as a string, formatted according to the same rules as the ISO C function `strftime`.

If `format` is absent, it defaults to "`%c`", which gives a human-readable date and time representation using the current locale.

On non-POSIX systems, this function may be not thread safe because of its reliance on C function `gmtime` and C function `localtime`.

---

### `os.difftime (t2, t1)`

Returns the difference, in seconds, from time `t1` to time `t2` (where the times are values returned by [`os.time`](#pdf-os.time)). In POSIX, Windows, and some other systems, this value is exactly `t2`*-*`t1`.

---

### `os.execute ([command])`

This function is equivalent to the ISO C function `system`. It passes `command` to be executed by an operating system shell. Its first result is **true** if the command terminated successfully, or **fail** otherwise. After this first result the function returns a string plus a number, as follows:

- **"`exit`": ** the command terminated normally; the following number is the exit status of the command.

- **"`signal`": ** the command was terminated by a signal; the following number is the signal that terminated the command.

When called without a `command`, `os.execute` returns a boolean that is true if a shell is available.

---

### `os.exit ([code [, close]])`

Calls the ISO C function `exit` to terminate the host program. If `code` is **true**, the returned status is `EXIT_SUCCESS`; if `code` is **false**, the returned status is `EXIT_FAILURE`; if `code` is a number, the returned status is this number. The default value for `code` is **true**.

If the optional second argument `close` is true, the function closes the Lua state before exiting (see [`lua_close`](#lua_close)).

---

### `os.getenv (varname)`

Returns the value of the process environment variable `varname` or **fail** if the variable is not defined.

---

### `os.remove (filename)`

Deletes the file (or empty directory, on POSIX systems) with the given name. If this function fails, it returns **fail** plus a string describing the error and the error code. Otherwise, it returns true.

---

### `os.rename (oldname, newname)`

Renames the file or directory named `oldname` to `newname`. If this function fails, it returns **fail**, plus a string describing the error and the error code. Otherwise, it returns true.

---

### `os.setlocale (locale [, category])`

Sets the current locale of the program. `locale` is a system-dependent string specifying a locale; `category` is an optional string describing which category to change: `"all"`, `"collate"`, `"ctype"`, `"monetary"`, `"numeric"`, or `"time"`; the default category is `"all"`. The function returns the name of the new locale, or **fail** if the request cannot be honored.

If `locale` is the empty string, the current locale is set to an implementation-defined native locale. If `locale` is the string "`C`", the current locale is set to the standard C locale.

When called with **nil** as the first argument, this function only returns the name of the current locale for the given category.

This function may be not thread safe because of its reliance on C function `setlocale`.

---

### `os.time ([table])`

Returns the current time when called without arguments, or a time representing the local date and time specified by the given table. This table must have fields `year`, `month`, and `day`, and may have fields `hour` (default is 12), `min` (default is 0), `sec` (default is 0), and `isdst` (default is **nil**). Other fields are ignored. For a description of these fields, see the [`os.date`](#pdf-os.date) function.

When the function is called, the values in these fields do not need to be inside their valid ranges. For instance, if `sec` is -10, it means 10 seconds before the time specified by the other fields; if `hour` is 1000, it means 1000 hours after the time specified by the other fields.

The returned value is a number, whose meaning depends on your system. In POSIX, Windows, and some other systems, this number counts the number of seconds since some given start time (the "epoch"). In other systems, the meaning is not specified, and the number returned by `time` can be used only as an argument to [`os.date`](#pdf-os.date) and [`os.difftime`](#pdf-os.difftime).

When called with a table, `os.time` also normalizes all the fields documented in the [`os.date`](#pdf-os.date) function, so that they represent the same time as before the call but with values inside their valid ranges.

---

### `os.tmpname ()`

Returns a string with a file name that can be used for a temporary file. The file must be explicitly opened before its use and explicitly removed when no longer needed.

In POSIX systems, this function also creates a file with that name, to avoid security risks. (Someone else might create the file with wrong permissions in the time between getting the name and creating the file.) You still have to open the file to use it and to remove it (even if you do not use it).

When possible, you may prefer to use [`io.tmpfile`](#pdf-io.tmpfile), which automatically removes the file when the program ends.

## 6.10 – The Debug Library

This library provides the functionality of the debug interface ([§4.7](#4.7)) to Lua programs. You should exert care when using this library. Several of its functions violate basic assumptions about Lua code (e.g., that variables local to a function cannot be accessed from outside; that userdata metatables cannot be changed by Lua code; that Lua programs do not crash) and therefore can compromise otherwise secure code. Moreover, some functions in this library may be slow.

All functions in this library are provided inside the `debug` table. All functions that operate over a thread have an optional first argument which is the thread to operate over. The default is always the current thread.

---

### `debug.debug ()`

Enters an interactive mode with the user, running each string that the user enters. Using simple commands and other debug facilities, the user can inspect global and local variables, change their values, evaluate expressions, and so on. A line containing only the word `cont` finishes this function, so that the caller continues its execution.

Note that commands for `debug.debug` are not lexically nested within any function and so have no direct access to local variables.

---

### `debug.gethook ([thread])`

Returns the current hook settings of the thread, as three values: the current hook function, the current hook mask, and the current hook count, as set by the [`debug.sethook`](#pdf-debug.sethook) function.

Returns **fail** if there is no active hook.

---

### `debug.getinfo ([thread,] f [, what])`

Returns a table with information about a function. You can give the function directly or you can give a number as the value of `f`, which means the function running at level `f` of the call stack of the given thread: level 0 is the current function (`getinfo` itself); level 1 is the function that called `getinfo` (except for tail calls, which do not count in the stack); and so on. If `f` is a number greater than the number of active functions, then `getinfo` returns **fail**.

The returned table can contain all the fields returned by [`lua_getinfo`](#lua_getinfo), with the string `what` describing which fields to fill in. The default for `what` is to get all information available, except the table of valid lines. The option '`f`' adds a field named `func` with the function itself. The option '`L`' adds a field named `activelines` with the table of valid lines, provided the function is a Lua function. If the function has no debug information, the table is empty.

For instance, the expression `debug.getinfo(1,"n").name` returns a name for the current function, if a reasonable name can be found, and the expression `debug.getinfo(print)` returns a table with all available information about the [`print`](#pdf-print) function.

---

### `debug.getlocal ([thread,] f, local)`

This function returns the name and the value of the local variable with index `local` of the function at level `f` of the stack. This function accesses not only explicit local variables, but also parameters and temporary values.

The first parameter or local variable has index 1, and so on, following the order that they are declared in the code, counting only the variables that are active in the current scope of the function. Compile-time constants may not appear in this listing, if they were optimized away by the compiler. Negative indices refer to vararg arguments; -1 is the first vararg argument. The function returns **fail** if there is no variable with the given index, and raises an error when called with a level out of range. (You can call [`debug.getinfo`](#pdf-debug.getinfo) to check whether the level is valid.)

Variable names starting with '`(`' (open parenthesis) represent variables with no known names (internal variables such as loop control variables, and variables from chunks saved without debug information).

The parameter `f` may also be a function. In that case, `getlocal` returns only the name of function parameters.

---

### `debug.getmetatable (value)`

Returns the metatable of the given `value` or **nil** if it does not have a metatable.

---

### `debug.getregistry ()`

Returns the registry table (see [§4.3](#4.3)).

---

### `debug.getupvalue (f, up)`

This function returns the name and the value of the upvalue with index `up` of the function `f`. The function returns **fail** if there is no upvalue with the given index.

(For Lua functions, upvalues are the external local variables that the function uses, and that are consequently included in its closure.)

For C functions, this function uses the empty string `""` as a name for all upvalues.

Variable name '`?`' (interrogation mark) represents variables with no known names (variables from chunks saved without debug information).

---

### `debug.getuservalue (u, n)`

Returns the `n`-th user value associated to the userdata `u` plus a boolean, **false** if the userdata does not have that value.

---

### `debug.sethook ([thread,] hook, mask [, count])`

Sets the given function as the debug hook. The string `mask` and the number `count` describe when the hook will be called. The string mask may have any combination of the following characters, with the given meaning:

- **'`c`': ** the hook is called every time Lua calls a function;

- **'`r`': ** the hook is called every time Lua returns from a function;

- **'`l`': ** the hook is called every time Lua enters a new line of code.

Moreover, with a `count` different from zero, the hook is called also after every `count` instructions.

When called without arguments, [`debug.sethook`](#pdf-debug.sethook) turns off the hook.

When the hook is called, its first parameter is a string describing the event that has triggered its call: `"call"`, `"tail call"`, `"return"`, `"line"`, and `"count"`. For line events, the hook also gets the new line number as its second parameter. Inside a hook, you can call `getinfo` with level 2 to get more information about the running function. (Level 0 is the `getinfo` function, and level 1 is the hook function.)

---

### `debug.setlocal ([thread,] level, local, value)`

This function assigns the value `value` to the local variable with index `local` of the function at level `level` of the stack. The function returns **fail** if there is no local variable with the given index, and raises an error when called with a `level` out of range. (You can call `getinfo` to check whether the level is valid.) Otherwise, it returns the name of the local variable.

See [`debug.getlocal`](#pdf-debug.getlocal) for more information about variable indices and names.

---

### `debug.setmetatable (value, table)`

Sets the metatable for the given `value` to the given `table` (which can be **nil**). Returns `value`.

---

### `debug.setupvalue (f, up, value)`

This function assigns the value `value` to the upvalue with index `up` of the function `f`. The function returns **fail** if there is no upvalue with the given index. Otherwise, it returns the name of the upvalue.

See [`debug.getupvalue`](#pdf-debug.getupvalue) for more information about upvalues.

---

### `debug.setuservalue (udata, value, n)`

Sets the given `value` as the `n`-th user value associated to the given `udata`. `udata` must be a full userdata.

Returns `udata`, or **fail** if the userdata does not have that value.

---

### `debug.traceback ([thread,] [message [, level]])`

If `message` is present but is neither a string nor **nil**, this function returns `message` without further processing. Otherwise, it returns a string with a traceback of the call stack. The optional `message` string is appended at the beginning of the traceback. An optional `level` number tells at which level to start the traceback (default is 1, the function calling `traceback`).

---

### `debug.upvalueid (f, n)`

Returns a unique identifier (as a light userdata) for the upvalue numbered `n` from the given function.

These unique identifiers allow a program to check whether different closures share upvalues. Lua closures that share an upvalue (that is, that access a same external local variable) will return identical ids for those upvalue indices.

---

### `debug.upvaluejoin (f1, n1, f2, n2)`

Make the `n1`-th upvalue of the Lua closure `f1` refer to the `n2`-th upvalue of the Lua closure `f2`.

# 7 – Lua Standalone

Although Lua has been designed as an extension language, to be embedded in a host C program, it is also frequently used as a standalone language. An interpreter for Lua as a standalone language, called simply `lua`, is provided with the standard distribution. The standalone interpreter includes all standard libraries. Its usage is:

```
lua [options] [script [args]]
```

The options are:

- **`-e stat`: ** execute string *stat*;

- **`-i`: ** enter interactive mode after running *script*;

- **`-l mod`: ** "require" *mod* and assign the result to global *mod*;

- **`-l g=mod`: ** "require" *mod* and assign the result to global *g*;

- **`-v`: ** print version information;

- **`-E`: ** ignore environment variables;

- **`-W`: ** turn warnings on;

- **`--`: ** stop handling options;

- **`-`: ** execute `stdin` as a file and stop handling options.

(The form `-l g=mod` was introduced in release 5.4.4.)

After handling its options, `lua` runs the given *script*. When called without arguments, `lua` behaves as `lua -v -i` when the standard input (`stdin`) is a terminal, and as `lua -` otherwise.

When called without the option `-E`, the interpreter checks for an environment variable `LUA_INIT_5_4` (or `LUA_INIT` if the versioned name is not defined) before running any argument. If the variable content has the format `@filename`, then `lua` executes the file. Otherwise, `lua` executes the string itself.

When called with the option `-E`, Lua does not consult any environment variables. In particular, the values of [`package.path`](#pdf-package.path) and [`package.cpath`](#pdf-package.cpath) are set with the default paths defined in `luaconf.h`. To signal to the libraries that this option is on, the stand-alone interpreter sets the field `"LUA_NOENV"` in the registry to a true value. Other libraries may consult this field for the same purpose.

The options `-e`, `-l`, and `-W` are handled in the order they appear. For instance, an invocation like

```
$ lua -e 'a=1' -llib1 script.lua
```

will first set `a` to 1, then require the library `lib1`, and finally run the file `script.lua` with no arguments. (Here `$` is the shell prompt. Your prompt may be different.)

Before running any code, `lua` collects all command-line arguments in a global table called `arg`. The script name goes to index 0, the first argument after the script name goes to index 1, and so on. Any arguments before the script name (that is, the interpreter name plus its options) go to negative indices. For instance, in the call

```
$ lua -la b.lua t1 t2
```

the table is like this:

```
arg = { [-2] = "lua", [-1] = "-la",
        [0] = "b.lua",
        [1] = "t1", [2] = "t2" }
```

If there is no script in the call, the interpreter name goes to index 0, followed by the other arguments. For instance, the call

```
$ lua -e "print(arg[1])"
```

will print "`-e`". If there is a script, the script is called with arguments `arg[1]`, ···, `arg[#arg]`. Like all chunks in Lua, the script is compiled as a variadic function.

In interactive mode, Lua repeatedly prompts and waits for a line. After reading a line, Lua first try to interpret the line as an expression. If it succeeds, it prints its value. Otherwise, it interprets the line as a statement. If you write an incomplete statement, the interpreter waits for its completion by issuing a different prompt.

If the global variable `_PROMPT` contains a string, then its value is used as the prompt. Similarly, if the global variable `_PROMPT2` contains a string, its value is used as the secondary prompt (issued during incomplete statements).

In case of unprotected errors in the script, the interpreter reports the error to the standard error stream. If the error object is not a string but has a metamethod `__tostring`, the interpreter calls this metamethod to produce the final message. Otherwise, the interpreter converts the error object to a string and adds a stack traceback to it. When warnings are on, they are simply printed in the standard error output.

When finishing normally, the interpreter closes its main Lua state (see [`lua_close`](#lua_close)). The script can avoid this step by calling [`os.exit`](#pdf-os.exit) to terminate.

To allow the use of Lua as a script interpreter in Unix systems, Lua skips the first line of a file chunk if it starts with `#`. Therefore, Lua scripts can be made into executable programs by using `chmod +x` and the `#!` form, as in

```
#!/usr/local/bin/lua
```

Of course, the location of the Lua interpreter may be different in your machine. If `lua` is in your `PATH`, then

```
#!/usr/bin/env lua
```

is a more portable solution.

# 8 – Incompatibilities with the Previous Version

Here we list the incompatibilities that you may find when moving a program from Lua 5.3 to Lua 5.4.

You can avoid some incompatibilities by compiling Lua with appropriate options (see file `luaconf.h`). However, all these compatibility options will be removed in the future. More often than not, compatibility issues arise when these compatibility options are removed. So, whenever you have the chance, you should try to test your code with a version of Lua compiled with all compatibility options turned off. That will ease transitions to newer versions of Lua.

Lua versions can always change the C API in ways that do not imply source-code changes in a program, such as the numeric values for constants or the implementation of functions as macros. Therefore, you should never assume that binaries are compatible between different Lua versions. Always recompile clients of the Lua API when using a new version.

Similarly, Lua versions can always change the internal representation of precompiled chunks; precompiled chunks are not compatible between different Lua versions.

The standard paths in the official distribution may change between versions.

## 8.1 – Incompatibilities in the Language

- The coercion of strings to numbers in arithmetic and bitwise operations has been removed from the core language. The string library does a similar job for arithmetic (but not for bitwise) operations using the string metamethods. However, unlike in previous versions, the new implementation preserves the implicit type of the numeral in the string. For instance, the result of `"1" + "2"` now is an integer, not a float.

- Literal decimal integer constants that overflow are read as floats, instead of wrapping around. You can use hexadecimal notation for such constants if you want the old behavior (reading them as integers with wrap around).

- The use of the `__lt` metamethod to emulate `__le` has been removed. When needed, this metamethod must be explicitly defined.

- The semantics of the numerical **for** loop over integers changed in some details. In particular, the control variable never wraps around.

- A label for a **goto** cannot be declared where a label with the same name is visible, even if this other label is declared in an enclosing block.

- When finalizing an object, Lua does not ignore `__gc` metamethods that are not functions. Any value will be called, if present. (Non-callable values will generate a warning, like any other error when calling a finalizer.)

## 8.2 – Incompatibilities in the Libraries

- The function [`print`](#pdf-print) does not call [`tostring`](#pdf-tostring) to format its arguments; instead, it has this functionality hardwired. You should use `__tostring` to modify how values are printed.

- The pseudo-random number generator used by the function [`math.random`](#pdf-math.random) now starts with a somewhat random seed. Moreover, it uses a different algorithm.

- By default, the decoding functions in the [`utf8`](#pdf-utf8) library do not accept surrogates as valid code points. An extra parameter in these functions makes them more permissive.

- The options "`setpause`" and "`setstepmul`" of the function [`collectgarbage`](#pdf-collectgarbage) are deprecated. You should use the new option "`incremental`" to set them.

- The function [`io.lines`](#pdf-io.lines) now returns four values, instead of just one. That can be a problem when it is used as the sole argument to another function that has optional parameters, such as in `load(io.lines(filename, "L"))`. To fix that issue, you can wrap the call into parentheses, to adjust its number of results to one.

## 8.3 – Incompatibilities in the API

- Full userdata now has an arbitrary number of associated user values. Therefore, the functions `lua_newuserdata`, `lua_setuservalue`, and `lua_getuservalue` were replaced by [`lua_newuserdatauv`](#lua_newuserdatauv), [`lua_setiuservalue`](#lua_setiuservalue), and [`lua_getiuservalue`](#lua_getiuservalue), which have an extra argument.

  For compatibility, the old names still work as macros assuming one single user value. Note, however, that userdata with zero user values are more efficient memory-wise.

- The function [`lua_resume`](#lua_resume) has an extra parameter. This out parameter returns the number of values on the top of the stack that were yielded or returned by the coroutine. (In previous versions, those values were the entire stack.)

- The function [`lua_version`](#lua_version) returns the version number, instead of an address of the version number. The Lua core should work correctly with libraries using their own static copies of the same core, so there is no need to check whether they are using the same address space.

- The constant `LUA_ERRGCMM` was removed. Errors in finalizers are never propagated; instead, they generate a warning.

- The options `LUA_GCSETPAUSE` and `LUA_GCSETSTEPMUL` of the function [`lua_gc`](#lua_gc) are deprecated. You should use the new option `LUA_GCINC` to set them.

# 9 – The Complete Syntax of Lua

Here is the complete syntax of Lua in extended BNF. As usual in extended BNF, {A} means 0 or more As, and [A] means an optional A. (For operator precedences, see [§3.4.8](#3.4.8); for a description of the terminals Name, Numeral, and LiteralString, see [§3.1](#3.1).)

```
chunk ::= block

block ::= {stat} [retstat]

stat ::=  ‘;’ |
	 varlist ‘=’ explist |
	 functioncall |
	 label |
	 break |
	 goto Name |
	 do block end |
	 while exp do block end |
	 repeat block until exp |
	 if exp then block {elseif exp then block} [else block] end |
	 for Name ‘=’ exp ‘,’ exp [‘,’ exp] do block end |
	 for namelist in explist do block end |
	 function funcname funcbody |
	 local function Name funcbody |
	 local attnamelist [‘=’ explist]

attnamelist ::=  Name attrib {‘,’ Name attrib}

attrib ::= [‘<’ Name ‘>’]

retstat ::= return [explist] [‘;’]

label ::= ‘::’ Name ‘::’

funcname ::= Name {‘.’ Name} [‘:’ Name]

varlist ::= var {‘,’ var}

var ::=  Name | prefixexp ‘[’ exp ‘]’ | prefixexp ‘.’ Name

namelist ::= Name {‘,’ Name}

explist ::= exp {‘,’ exp}

exp ::=  nil | false | true | Numeral | LiteralString | ‘...’ | functiondef |
	 prefixexp | tableconstructor | exp binop exp | unop exp

prefixexp ::= var | functioncall | ‘(’ exp ‘)’

functioncall ::=  prefixexp args | prefixexp ‘:’ Name args

args ::=  ‘(’ [explist] ‘)’ | tableconstructor | LiteralString

functiondef ::= function funcbody

funcbody ::= ‘(’ [parlist] ‘)’ block end

parlist ::= namelist [‘,’ ‘...’] | ‘...’

tableconstructor ::= ‘{’ [fieldlist] ‘}’

fieldlist ::= field {fieldsep field} [fieldsep]

field ::= ‘[’ exp ‘]’ ‘=’ exp | Name ‘=’ exp | exp

fieldsep ::= ‘,’ | ‘;’

binop ::=  ‘+’ | ‘-’ | ‘*’ | ‘/’ | ‘//’ | ‘^’ | ‘%’ |
	 ‘&’ | ‘~’ | ‘|’ | ‘>>’ | ‘<<’ | ‘..’ |
	 ‘<’ | ‘<=’ | ‘>’ | ‘>=’ | ‘==’ | ‘~=’ |
	 and | or

unop ::= ‘-’ | not | ‘#’ | ‘~’
```

---

## Source: `docs/lua-lang/readme-5.4.md`

<!-- Source: https://www.lua.org/manual/5.4/readme.html
     Fetched: 2026-06-20
     License: Lua is distributed under the terms of the Lua license (an MIT-style license; see license.md).
     Reproduced under that license with attribution to Lua.org, PUC-Rio.
     This is the core Lua 5.4 reference, scraped from the official manual.
     Do not edit manually — re-fetch from the source above to update. -->

# Welcome to Lua 5.4

[about](#about) · [installation](#install) · [changes](#changes) · [license](#license) · [reference manual](https://www.lua.org/manual/5.4/contents.html)

## About Lua

Lua is a powerful, efficient, lightweight, embeddable scripting language developed by a [team](https://www.lua.org/authors.html) at [PUC-Rio](https://www.puc-rio.br/), the Pontifical Catholic University of Rio de Janeiro in Brazil. Lua is [free software](#license) used in [many products and projects](https://www.lua.org/uses.html) around the world.

Lua's [official website](https://www.lua.org/) provides complete information about Lua, including an [executive summary](https://www.lua.org/about.html), tips on [getting started](https://www.lua.org/start.html), and updated [documentation](https://www.lua.org/docs.html), especially the [reference manual](https://www.lua.org/manual/5.4/), which may differ slightly from the [local copy](https://www.lua.org/manual/5.4/contents.html) distributed in this package.

## Installing Lua

Lua is distributed in [source](https://www.lua.org/ftp/) form. You need to build it before using it. Building Lua should be straightforward because Lua is implemented in pure ISO C and compiles unmodified in all known platforms that have an ISO C compiler. Lua also compiles unmodified as C++. The instructions given below for building Lua are for Unix-like platforms, such as Linux and macOS. See also [instructions for other systems](#other) and [customization options](#customization).

If you don't have the time or the inclination to compile Lua yourself, get a binary from [LuaBinaries](https://luabinaries.sourceforge.net).

### Building Lua

In most common Unix-like platforms, simply do "make". Here are the details.

1. Open a terminal window and move to the top-level directory, which is named `lua-5.4.8`. The `Makefile` there controls both the build process and the installation process.

2. Do "make". The `Makefile` will guess your platform and build Lua for it.

3. If the guess failed, do "make help" and see if your platform is listed. The platforms currently supported are:

  guess aix bsd c89 freebsd generic ios linux linux-readline macosx mingw posix solaris

  If your platform is listed, just do "make xxx", where xxx is your platform name.

  If your platform is not listed, try the closest one or posix, generic, c89, in this order.

4. The compilation takes only a few moments and produces three files in the `src` directory: lua (the interpreter), luac (the compiler), and liblua.a (the library).

5. To check that Lua has been built correctly, do "make test" after building Lua. This will run the interpreter and print its version.

If you're running Linux, try "make linux-readline" to build the interactive Lua interpreter with handy line-editing and history capabilities. If you get compilation errors, make sure you have installed the `readline` development package (which is probably named `libreadline-dev` or `readline-devel`). If you get link errors after that, then try "make linux-readline MYLIBS=-ltermcap".

### Installing Lua

Once you have built Lua, you may want to install it in an official place in your system. In this case, do "make install". The official place and the way to install files are defined in the `Makefile`. You'll probably need the right permissions to install files, and so may need to do "sudo make install".

To build and install Lua in one step, do "make all install", or "make xxx install", where xxx is your platform name.

To install Lua locally after building it, do "make local". This will create a directory `install` with subdirectories `bin`, `include`, `lib`, `man`, `share`, and install Lua as listed below. To install Lua locally, but in some other directory, do "make install INSTALL_TOP=xxx", where xxx is your chosen directory. The installation starts in the `src` and `doc` directories, so take care if `INSTALL_TOP` is not an absolute path.

bin:

lua luac

include:

lua.h luaconf.h lualib.h lauxlib.h lua.hpp

lib:

liblua.a

man/man1:

lua.1 luac.1

These are the only directories you need for development. If you only want to run Lua programs, you only need the files in `bin` and `man`. The files in `include` and `lib` are needed for embedding Lua in C or C++ programs.

### Customization

Three kinds of things can be customized by editing a file:

- Where and how to install Lua — edit `Makefile`.

- How to build Lua — edit `src/Makefile`.

- Lua features — edit `src/luaconf.h`.

You don't actually need to edit the Makefiles because you may set the relevant variables in the command line when invoking make. Nevertheless, it's probably best to edit and save the Makefiles to record the changes you've made.

On the other hand, if you need to customize some Lua features, edit `src/luaconf.h` before building and installing Lua. The edited file will be the one installed, and it will be used by any Lua clients that you build, to ensure consistency. Further customization is available to experts by editing the Lua sources.

### Building Lua on other systems

If you're not using the usual Unix tools, then the instructions for building Lua depend on the compiler you use. You'll need to create projects (or whatever your compiler uses) for building the library, the interpreter, and the compiler, as follows:

library:

lapi.c lcode.c lctype.c ldebug.c ldo.c ldump.c lfunc.c lgc.c llex.c lmem.c lobject.c lopcodes.c lparser.c lstate.c lstring.c ltable.c ltm.c lundump.c lvm.c lzio.c lauxlib.c lbaselib.c lcorolib.c ldblib.c liolib.c lmathlib.c loadlib.c loslib.c lstrlib.c ltablib.c lutf8lib.c linit.c

interpreter:

library, lua.c

compiler:

library, luac.c

To use Lua as a library in your own programs, you need to know how to create and use libraries with your compiler. Moreover, to dynamically load C libraries for Lua, you'll need to know how to create dynamic libraries and you'll need to make sure that the Lua API functions are accessible to those dynamic libraries — but *don't* link the Lua library into each dynamic library. For Unix, we recommend that the Lua library be linked statically into the host program and its symbols exported for dynamic linking; `src/Makefile` does this for the Lua interpreter. For Windows, we recommend that the Lua library be a DLL. In all cases, the compiler luac should be linked statically.

As mentioned above, you may edit `src/luaconf.h` to customize some features before building Lua.

## Changes since Lua 5.3

Here are the main changes introduced in Lua 5.4. The [reference manual](https://www.lua.org/manual/5.4/contents.html) lists the [incompatibilities](https://www.lua.org/manual/5.4/manual.html#8) that had to be introduced.

### Main changes

- new generational mode for garbage collection

- to-be-closed variables

- const variables

- userdata can have multiple user values

- new implementation for math.random

- warning system

- debug information about function arguments and returns

- new semantics for the integer 'for' loop

- optional 'init' argument to 'string.gmatch'

- new functions 'lua_resetthread' and 'coroutine.close'

- string-to-number coercions moved to the string library

- allocation function allowed to fail when shrinking a memory block

- new format '%p' in 'string.format'

- utf8 library accepts codepoints up to 2^31

## License

Lua is free software distributed under the terms of the [MIT license](https://opensource.org/license/mit) reproduced below; it may be used for any purpose, including commercial purposes, at absolutely no cost without having to ask us. The only requirement is that if you do use Lua, then you should give us credit by including the appropriate copyright notice somewhere in your product or its documentation. For details, see the [license page](https://www.lua.org/license.html).

Copyright © 1994–2025 Lua.org, PUC-Rio.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

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

## Source: `.claude/skills/game-cheat-guidelines/SKILL.md`

---
name: game-cheat-guidelines
description: >
  Behavioral rules for writing Perception.cx scripts in Enma, AngelScript, and
  C++ for authorized reverse engineering, analysis, overlay rendering, and
  research. Derived from Karpathy principles: memory reading, visualization,
  hooking, render pipelines, and RE workflows. Always active — these rules
  apply every time you write or edit Perception.cx script code. Authorized use
  only — analyze software you own or are permitted to test.
license: MIT
---

# Perception.cx Script Development Guidelines

Behavioral rules for writing Perception.cx scripts in Enma, AngelScript, and C++. Derived from the Karpathy principles and rewritten for the domain: memory reading, visualization, overlay rendering, hooking, and reverse-engineering workflows on the Perception.cx platform. These rules originated in game-overlay development and apply equally to authorized reverse engineering, security research, and analysis — analyze only software you own or are authorized to test.

**Always active.** These rules apply every time you write or edit Perception.cx script code. They are not suggestions.

**Prerequisite:** The `game-hacking-pcx` skill MUST be loaded alongside this one. It contains the full doc index (33,580 lines across 99 files) for Enma, AngelScript, and all Perception.cx APIs. **Read the relevant doc before writing any API call** — see `skill://game-hacking-pcx` for the complete file-by-file index.

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
  hacking, Enma, AngelScript, or Perception.cx work. Provides the full doc
  index (43,000+ lines across 139 files) and enforces reading the relevant
  documentation before writing any API call. Load alongside
  game-cheat-guidelines on every PCX session.
license: MIT
---

# Game Hacking & Scripting — Perception.cx / Enma / AngelScript / C++

## Trigger
Game hacking, game cheats, memory reading/writing, ESP, aimbot, pattern scanning, vtable hooking,
process manipulation, Enma scripting, AngelScript scripting, Perception.cx, PCX, render overlays,
any `.em` or `.as` game script work, or any mention of the Perception platform.

## MANDATORY: Read Before Writing Code

**You MUST read the relevant docs from `docs/` before writing ANY Enma, AngelScript,
or PCX API code.** Do not write from memory. The docs are the source of truth.

### When writing Enma (.em) code — read these:

**Language (always read `llms-language.md` first — it's the complete single-page reference):**
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

1. **Before writing Enma code**: `read docs/enma/llms-language.md` (the single-page complete ref)
2. **Before calling a PCX API**: `read docs/perception/<api-name>.md`
3. **Before writing AngelScript**: `read docs/perception/angelscript/<api-name>.md`
4. **If unsure about a type, function, or parameter**: read the doc, don't guess
5. **If the doc says a function is "gated"**: it requires a permission flag — mention this to the user

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

## Source: `knowledge/pcx-api-cheatsheet.md`

# Perception.cx Enma API Quick Reference

All natives are auto-registered. No import needed (except `import "vec"; import "color";` for those types).

## Proc API — Process Memory

```cpp
proc_t p = ref_process("game.exe");       // by name
proc_t p = ref_process(1234);              // by PID
bool alive = p.alive();
uint64 base = p.base_address();
uint64 peb  = p.peb();
uint32 pid  = p.pid();
bool valid  = p.is_valid_address(addr);
```

### Read Primitives
```cpp
uint8/16/32/64  p.ru8/ru16/ru32/ru64(uint64 addr);
int8/16/32/64   p.r8/r16/r32/r64(uint64 addr);
float32         p.rf32(uint64 addr);
float64         p.rf64(uint64 addr);
string          p.rs(uint64 addr, int32 max_chars);    // ASCII
string          p.rws(uint64 addr, int32 max_chars);   // UTF-16→UTF-8
array<uint8>    p.rvm(uint64 addr, uint64 size);       // bulk
```

### Write Primitives (gated: `write_memory`)
```cpp
bool p.wu8/wu16/wu32/wu64(uint64 addr, uintN v);
bool p.w8/w16/w32/w64(uint64 addr, intN v);
bool p.wf32(uint64 addr, float32 v);
bool p.wf64(uint64 addr, float64 v);
bool p.wvm(uint64 addr, array<uint8> bytes);
```

### Typed Reads (vec/quat/mat)
```cpp
vec2 p.read_vec2_fl32(uint64 addr);     // also: _fl64 variant
vec3 p.read_vec3_fl32(uint64 addr);
vec4 p.read_vec4_fl32(uint64 addr);
quat p.read_quat_fl32(uint64 addr);
mat4 p.read_mat4_fl32(uint64 addr);
// write variants: p.write_vec3_fl32(addr, v), etc. (gated)
```

### Modules
```cpp
uint64                base = p.get_module_base("module.dll");
uint64                size = p.get_module_size("module.dll");
array<module_info_t>  mods = p.get_module_list();
uint64                exp  = p.get_proc_address(base, "ExportName");
uint64                imp  = p.get_import_rdata_address(base, "ImportName");
// module_info_t: .name(), .base(), .size()
```

### Pattern Scanning
```cpp
uint64 hit = p.find_code_pattern(start, size, "48 8B 05 ?? ?? ?? ?? 48 85 C0");
array<uint64> hits = p.find_all_code_patterns(start, size, sig);
```

### Memory Scanning
```cpp
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
array<uint64> p.scan_u64(value, heap_only);
array<uint64> p.scan_u32(value, heap_only);
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
```

### VAD / Virtual Query
```cpp
vad_region_t r = p.virtual_query(addr);       // .start(), .size(), .protection()
array<vad_region_t> snap = p.get_vad_snapshot(heap_only);
```

### VM Alloc/Free (gated: `virtual_memory_operations`)
```cpp
uint64 page = p.alloc_vm(4096);
bool ok = p.free_vm(page);
```

## Render API — 2D Drawing

```cpp
import "vec";
import "color";

// Primitives
draw_line(vec2 a, vec2 b, color c, float64 thickness);
draw_rect(vec2 pos, vec2 size, color c, float64 thickness, float64 rounding, uint8 flags);
draw_rect_filled(vec2 pos, vec2 size, color c, float64 rounding, uint8 flags);
draw_circle(vec2 center, float64 radius, color c, float64 thickness, bool filled);
draw_arc(vec2 center, vec2 radii, float64 start, float64 sweep, color c, float64 thick, bool filled);
draw_triangle(vec2 a, vec2 b, vec2 c, color col, float64 thickness, bool filled);
draw_text(string text, vec2 pos, color c, int64 font, int32 effect, color effect_c, float64 effect_amt);
draw_bitmap(int64 bmp, vec2 pos, vec2 size, color tint, bool rounded);

// effect: 0=none, 1=shadow, 2=outline
// rounding_flags: bitmask, 15=all corners

// Fonts
int64 get_font18(); int64 get_font20(); int64 get_font24(); int64 get_font28();
int64 create_font(string path, float64 size, bool aa, bool color, array ranges);
float64 get_text_width(int64 font, string text, int32 maxw, int32 maxh);
float64 get_text_height(int64 font, string text, int32 maxw, int32 maxh);

// Viewport
float64 get_view_width();  float64 get_view_height();
float64 get_view_scale();  float64 get_fps();

// Clipping
clip_push(vec2 pos, vec2 size); clip_pop();

// Shaders (layout: "POSITION:0:FLOAT2, COLOR:0:FLOAT4")
int64 create_shader(string vs, string ps, string layout);
int64 create_compute_shader(string cs);

// Buffers
int64 create_vertex_buffer(uint32 stride, uint32 max, bool dynamic);
int64 create_index_buffer(uint32 max, bool use32, bool dynamic);
int64 create_constant_buffer(uint32 size);
```

## GUI API — Sidebar Widgets

```cpp
int64 sec = create_section("Section Name");
section_checkbox(sec, "Label", bool_ref);
section_slider_float(sec, "Label", float_ref, min, max);
section_slider_int(sec, "Label", int_ref, min, max);
section_button(sec, "Label", callback_fn);
section_text_input(sec, "Label", string_ref);
section_keybind(sec, "Label", key_ref);
section_color_picker(sec, "Label", color_ref);
section_dropdown(sec, "Label", index_ref, items_array);
section_label(sec, "Text");
section_separator(sec);
```

## Input API

```cpp
bool is_key_down(int32 vk);
bool is_key_pressed(int32 vk);       // edge: just pressed
bool is_key_released(int32 vk);      // edge: just released
bool is_mouse_down(int32 button);    // 0=left, 1=right, 2=middle
vec2 get_mouse_pos();
vec2 get_mouse_delta();
```

## CPU API

```cpp
string get_cpu_vendor();
float64 time_ms();     // monotonic milliseconds
float64 time_us();     // monotonic microseconds
int32 get_datetime_year/month/day/hour/minute/second();
```

## Zydis API — x86-64 Disassembler/Assembler

```cpp
zydis_insn_t insn = zydis_decode(bytes_array, addr);
// insn.mnemonic, insn.length, insn.operands[]
array<uint8> encoded = zydis_encode(mnemonic, operands);
```

## Unicorn API — x86-64 Emulation

```cpp
int64 uc = uc_create();
uc_mem_map(uc, addr, size, perms);
uc_mem_write(uc, addr, bytes);
uc_reg_write(uc, reg_id, value);
uc_emu_start(uc, begin, until, timeout, count);
uint64 val = uc_reg_read(uc, reg_id);
array<uint8> data = uc_mem_read(uc, addr, size);
uc_destroy(uc);
```

## Net API

```cpp
string body = http_get(url, headers_map);
string body = http_post(url, post_body, headers_map);
int64 ws = ws_connect(url); ws_send(ws, msg); string r = ws_recv(ws);
int64 sock = udp_create(); udp_send(sock, host, port, data); udp_recv(sock, buf, timeout);
```

## Win API

```cpp
array<window_t> wins = enum_windows();
// window_t: .hwnd(), .title(), .class_name(), .pid(), .rect()
send_key(int32 vk, bool down);
send_mouse(int32 button, bool down, int32 x, int32 y);
string clip = get_clipboard(); set_clipboard(text);
```

## Filesystem API

```cpp
string content = read_file(path);
bool ok = write_file(path, content);
bool exists = file_exists(path);
array<string> entries = list_dir(path);
bool ok = create_dir(path);
bool ok = delete_file(path);
```

## Sound API

```cpp
int64 snd = load_sound(path);   // .wav or .ogg
play_sound(snd);
```

## Lifecycle

```cpp
int64 main() {
    // return > 0 to stay loaded, <= 0 to unload
    register_routine(cast<int64>(my_fn), user_data);
    return 1;
}
void my_fn(int64 data) { /* called every frame */ }
unregister_routine(handle);
```

---

# New API Additions (Feb–June 2026 Changelogs)

## Custom Draw API — Direct GPU Access (D3D11)

Full custom shader pipeline on the Universal API. Write HLSL, create vertex
buffers, textures, render targets, depth buffers, and draw any primitive
topology directly from AngelScript/Enma. Custom draw commands respect draw
order with every existing render function. All resources are tracked
per-script and auto-cleaned on unload.

### Resource Creation (all return `uint64` handle, `0` on failure)
```cpp
uint64 create_shader(string vs_source, string ps_source, string layout);
uint64 create_vertex_buffer(uint32 stride, uint32 max_vertices, bool dynamic);
uint64 create_index_buffer(uint32 max_indices, bool is_32bit, bool dynamic);
uint64 create_constant_buffer(uint32 size);
uint64 create_blend_state(src, dst, op, src_alpha, dst_alpha, op_alpha);
uint64 create_sampler(filter, address_u, address_v);
uint64 create_texture(uint32 width, uint32 height, array<uint8> rgba_data);
uint64 create_render_target(uint32 width, uint32 height);
uint64 create_depth_buffer(uint32 width, uint32 height);
uint64 create_depth_stencil_state(bool depth_enable, bool depth_write, int compare_func);
uint64 create_rasterizer_state(int fill_mode, int cull_mode);
```

### Drawing
```cpp
custom_draw(shader, vb, data, vertex_count, topology,
            blend, sampler, texture, rt, cb, cb_data, cb_slot);
custom_draw_indexed(shader, vb, vert_data, vert_stride,
                    ib, index_data, index_count, topology,
                    blend, sampler, texture, rt, cb, cb_data, cb_slot);
```

### Render Target Operations
```cpp
custom_set_render_target(rt);
custom_set_render_target_ext(rt, depth_buffer);
custom_clear_render_target(rt, r, g, b, a);
custom_clear_depth_buffer(db);
custom_resolve_render_target(rt);     // copy RT -> backbuffer
```

### State Management
```cpp
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs);
custom_set_viewport(x, y, w, h);                          // split-screen / PiP
custom_bind_textures(shader, slot0_tex, slot1_tex, ...);  // multi-texture
custom_bind_constant_buffers(shader, slot, cb, cb_data, cb_size);
```

### Mesh & Texture Loading
```cpp
load_obj_mesh(path);                  // returns vb + ib handles
create_texture_from_file(path);
create_dynamic_texture(width, height);
update_dynamic_texture(tex, rgba_data);
```

### Compute Shaders
```cpp
uint64 cs  = create_compute_shader(cs_source);
uint64 buf = create_structured_buffer(element_size, element_count, data);
dispatch_compute(cs, groups_x, groups_y, groups_z);
read_structured_buffer(buf);
```

### Backbuffer Capture
```cpp
uint64 tex = capture_backbuffer();    // texture handle of current frame
```

### Constants
```cpp
// Topology
TOPO_POINT_LIST, TOPO_LINE_LIST, TOPO_LINE_STRIP,
TOPO_TRIANGLE_LIST, TOPO_TRIANGLE_STRIP

// Compare funcs (depth stencil)
CMP_NEVER, CMP_LESS, CMP_EQUAL, CMP_LESS_EQUAL,
CMP_GREATER, CMP_NOT_EQUAL, CMP_GREATER_EQUAL, CMP_ALWAYS

// Fill modes
FILL_WIREFRAME, FILL_SOLID

// Cull modes
CULL_NONE, CULL_FRONT, CULL_BACK
```

### Layout String Format
Comma-separated `SEMANTIC:slot:TYPE` entries, e.g.
`"POSITION:0:FLOAT2, COLOR:0:FLOAT4"`.

### Key Features
- Indexed rendering with 16-bit and 32-bit index formats
- True 3D depth testing with configurable depth-stencil state
- Rasterizer state control (culling, wireframe)
- Custom viewports for split-screen / picture-in-picture
- Multi-texture and multi-constant-buffer binding
- Compute shaders with structured buffers
- OBJ mesh loading + dynamic texture updates
- Depth-enabled render targets, backbuffer capture for post-processing

### Example: Basic Colored Triangle
```angelscript
string vs = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj);
    o.col = i.col;
    return o;
}
""";

string ps = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

uint64 shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
uint64 vb = create_vertex_buffer(24, 3, true);
uint64 blend = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
```

### Example: Depth-Tested 3D Scene
```angelscript
uint64 db = create_depth_buffer(400, 300);
uint64 ds = create_depth_stencil_state(true, true, CMP_LESS);

custom_set_render_target_ext(rt, db);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
```

## World-to-Screen (updated Feb 2026)

```cpp
bool world_to_screen_rowmajor(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
bool world_to_screen_transposed(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
```
- Use `world_to_screen_rowmajor` for row-major view matrices.
- Use `world_to_screen_transposed` for transposed (column-major) matrices.
- ⚠️ **DEPRECATED:** `source2_world_to_screen` — replace with the variants above.

## Matrix4x4 Double Precision (Feb 2026)

```cpp
mat4 m.readas_float(uint64 addr);      // float-precision read
mat4 m.readas_double(uint64 addr);     // double-precision read
bool m.writeas_float(uint64 addr, mat4 v);
bool m.writeas_double(uint64 addr, mat4 v);
```
- ⚠️ **DEPRECATED:** default `matrix4x4` read/write — use a precision-specific variant.

## Thread Priority Helpers (Feb 2026)

```cpp
set_thread_to_highest_priority();
set_thread_to_lowest_priority();
set_thread_to_normal_priority();
```

## Atomics (Feb 2026)

```cpp
atomic_int32 a;    // lock-free thread-safe 32-bit integer
atomic_int64 b;    // lock-free thread-safe 64-bit integer
```

## GUI Additions (Feb–Mar 2026)

```cpp
get_gui_position(float &out x, float &out y);   // GUI window position
get_gui_size(float &out w, float &out h);       // GUI window size

// List widget ops
list:get(...);              list:remove(...);
list:highlight(...);        list:remove_highlight(...);
list:hide(...);             list:show(...);
```

## Callbacks (Mar 2026)

```cpp
register_callback(string name, func, bool render_on_top = false);
// render_on_top=true renders on top of everything else
```

## Window Additions (Feb 2026)

```cpp
array<uint64> hwnds = get_all_hwnds();   // all window handles
```

## Fonts (Feb 2026)

```cpp
int64 create_font(string name, float64 size, array glyph_ranges);       // glyph_ranges optional
int64 create_font_mem(array<uint8> data, float64 size, array glyph_ranges); // glyph_ranges optional
```

## Input Additions (Feb 2026)

- Controller keybinds via **XINPUT** now supported.
- `get_mouse_delta()` now returns proper movement delta (fixed).

## Unicorn Emulator Updates (Mar 2026)

```cpp
// New hook types
UC_HOOK_INSN_INVALID    // invalid instructions
UC_HOOK_INTR            // software interrupts (INT3, syscalls)

uint64 status = uc_get_last_exception(uc);     // NTSTATUS, e.g. 0xC0000005
uint64 rip    = uc_get_exception_address(uc);  // RIP where exception occurred
```
- Null pointer access is now caught gracefully instead of crashing.

## Sound API — Full Audio Engine (Mar 2026)

44100Hz stereo, up to 64 simultaneous instances. WAV (PCM 8/16-bit) parsed
directly; MP3/AAC/WMA/FLAC decoded via Media Foundation. Auto-cleanup on
script unload.

```cpp
int64 snd = load_sound(path);
free_sound(snd);
play_sound(snd, bool loop);
stop_sound(snd);
stop_all_sounds();
set_sound_volume(snd, float vol);   // 0.0 – 1.0
set_sound_pan(snd, float pan);      // -1.0 (L) – +1.0 (R)
```

## Scan API Updates (Mar 2026)

Scan functions now return `array<uint64>@` directly (no `&out` params).
The `get_vad_snapshot` regression is fixed and returns proper values.

```cpp
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
```
- ⚠️ **REMOVED (never existed):** `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64`.

## Deprecated Functions Summary

| Deprecated | Replacement |
|---|---|
| `source2_world_to_screen` | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| default `matrix4x4` read/write | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` |
| `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64` | removed — use `scan_float` / `scan_double` / `scan_string` / `scan_wstring` / `scan_pointer` |

---

## Source: `knowledge/pcx-cross-language-bridge.md`

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
