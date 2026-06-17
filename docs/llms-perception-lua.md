# Lua Context Pack

> Single-file context pack for AI tools writing Lua scripts on Perception.cx. Bundles the Lua API surface, the discipline skill, and cross-references to the underlying 12 guidelines.

> **Generated** by `tools/build-llms-index.py` — do not edit manually. Re-generate by running the tool from the repo root. CI verifies the committed bundle matches the current source.

**Source files included: 22**

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

## Source: `.claude/skills/pcx-lua-discipline/SKILL.md`

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

# Game Cheat Development Guidelines

Behavioral rules for writing game cheats in Enma, AngelScript, and C++. Derived from the Karpathy principles but rewritten for the domain: memory hacking, ESP, aimbot, hooking, overlay rendering, and reverse engineering workflows on the Perception.cx platform.

**Always active.** These rules apply every time you write or edit cheat code. They are not suggestions.

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

**Each cheat feature lives in its own file. No god scripts.**

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

## 9. Don't Write Memory Unless You Must

**Read-only cheats are invisible. Writes leave forensic traces.**

- ESP, radar, entity highlighting, distance display — all read-only. Prefer these.
- If you must write (aimbot smoothing via angle writes, no-recoil via value patches, speed hacks), write the minimum bytes needed.
- Never `wvm` a large buffer when `wu32` or `wf32` on a single field suffices.
- After writing, verify the write took effect with a read-back if the field is contested (anti-cheat may revert it).
- Gate all writes behind `write_memory` permission checks — Perception enforces this, respect it in your design too.

```cpp
// WRONG — nop-patching 16 bytes of recoil code
array<uint8> nops = {0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90};
p.wvm(recoil_addr, nops);

// RIGHT — write the float that controls recoil spread, minimal footprint
p.wf32(recoil_spread_addr, 0.0f);
```

**Why:** Every memory write is a detection surface. Anti-cheats integrity-check code sections (`.text`), monitor write patterns on game state, and log anomalous page faults. A single float write to a gameplay variable is orders of magnitude harder to detect than a 16-byte NOP sled in executable memory.

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
| 9 | Minimize writes | Reads are invisible |
| 10 | W2S once, correctly | Math, not magic |
| 11 | GUI for all tunables | No magic constants |
| 12 | Verify with the binary | Trust live reads over memory |

---

## Source: `.claude/skills/game-hacking-pcx/SKILL.md`

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
