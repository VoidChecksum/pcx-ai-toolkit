> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/engine-specific-api.md).

# Engine Specific API

### Unreal Engine Helpers

The following helpers are designed for Unreal Engine–based games (UE4 & UE5), including both float-precision and double-precision view structures.

***

#### `bool unreal_read_tarray(proc_t &in proc, uint64 tarray_addr, array<uint64> &out result, uint max_count = 4096)`

Reads an Unreal `TArray` from memory and fills a script array with the pointer values inside it.

**Parameters**

* **proc** — target process handle
* **tarray\_addr** — memory address of the `TArray`
* **result** — output array that will receive the entries
* **max\_count** — safety limit for max number of elements (default 4096)

**Returns**

`true` on success, `false` on invalid address, invalid process, or corrupted data.

On failure, `result` will be empty.

**Example**

```cpp
array<uint64> actors;
if (unreal_read_tarray(proc, actors_addr, actors))
{
    for (uint i = 0; i < actors.length(); i++)
        log("Actor pointer: " + actors[i]);
}
```

***

#### `bool unreal_read_minimal_view_info(proc_t &in proc, uint64 pov_addr, vector3 &out location, vector3 &out rotation, double &out fov)`

Reads a **float-precision** Unreal camera view.

**Parameters**

* **proc** — process handle
* **pov\_addr** — address of camera/view structure
* **location** — output camera world position
* **rotation** — output camera rotation (pitch, yaw, roll)
* **fov** — output field-of-view

**Returns**

`true` on success, `false` on invalid input.

***

#### `bool unreal_read_minimal_view_info_f64(proc_t &in proc, uint64 pov_addr, vector3 &out location, vector3 &out rotation, double &out fov)`

Same as above but for **double-precision** UE5 view structures.

Use this if the game uses large-world coordinates or 64-bit FOV/rotation data.

***

#### `bool unreal_world_to_screen(const vector3 &in world_pos, const vector3 &in cam_location, const vector3 &in cam_rotation, double fov_deg, vector2 &out screen_pos)`

Projects a 3D world point into 2D screen coordinates using a UE-style camera.

**Parameters**

* **world\_pos** — world-space position
* **cam\_location** — camera location
* **cam\_rotation** — camera rotation (pitch, yaw, roll)
* **fov\_deg** — vertical field-of-view in degrees
* **screen\_pos** — output pixel coordinate

**Returns**

* `true` if the point is visible, and `screen_pos` is valid
* `false` if the point is behind the camera

**Example**

```cpp
vector2 screen;
if (unreal_world_to_screen(targetPos, viewLoc, viewRot, viewFov, screen))
{
    draw_text("Target", screen.x, screen.y);
}
```

***

#### World-to-Screen Projection&#xD;

Convert 3D world coordinates to 2D screen positions using view matrices.

```cpp
// Row-major matrix layout (DirectX-style, Source engine, etc.)
bool world_to_screen_rowmajor(
    const vector3 &in world_pos,
    const matrix4x4 &in view_matrix,
    vector2 &out screen_pos,
    const vector2 &in viewport = vector2(0, 0)
);

// Transposed/column-major layout (Unity, OpenGL-style)
bool world_to_screen_transposed(
    const vector3 &in world_pos,
    const matrix4x4 &in view_matrix,
    vector2 &out screen_pos,
    const vector2 &in viewport = vector2(0, 0)
);

//Example
matrix4x4 view_matrix;
view_matrix.readas_float(proc, view_matrix_address);

vector3 enemy_head(100.0, 200.0, 50.0);
vector2 screen;

if (world_to_screen_rowmajor(enemy_head, view_matrix, screen))
{
    draw_circle(screen.x, screen.y, 5, 255, 0, 0, 255, 1, true);
    draw_text("Enemy", screen.x, screen.y - 20, 255, 255, 255, 255, get_font18(), 0, 0, 0, 0, 0, 0);
}
```

***

### Fortnite Helper

#### `string fortnite_get_player_name(proc_t &in proc, uint64 addr)`

Reads and decrypts a Fortnite player name from memory.

**Returns**

* Player name on success
* Empty string `""` on failure

**Example**

```cpp
string name = fortnite_get_player_name(proc, name_addr);
if (name.length() > 0)
    log("Player: " + name);
```

***

### Rust Helper

#### `vector3 rust_get_transform_position(proc_t &in proc, uint64 addr)`

Resolves the world-space position of a Rust (Unity) transform hierarchy.

**Returns**

* A `vector3` world position on success
* `(0,0,0)` on invalid memory or failure

**Example**

```cpp
vector3 pos = rust_get_transform_position(proc, transform_ptr);
if (pos.x != 0 || pos.y != 0 || pos.z != 0)
{
    vector2 s;
    if (unreal_world_to_screen(pos, camLoc, camRot, camFov, s))
        draw_point(s.x, s.y, color_green);
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/engine-specific-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
