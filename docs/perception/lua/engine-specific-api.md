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
