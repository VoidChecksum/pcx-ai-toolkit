> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/render-api.md).

# Render API

**📐 Constants**

```cpp
const uint8 RR_TOP_LEFT
const uint8 RR_TOP_RIGHT
const uint8 RR_BOTTOM_LEFT
const uint8 RR_BOTTOM_RIGHT
```

> Rectangle-corner rounding flags (bitmask).

```cpp
const int TE_NONE
const int TE_OUTLINE
const int TE_SHADOW
const int TE_GLOW
```

> Text rendering effects.

***

**🎨 Viewport**

```cpp
void get_view(float &out w, float &out h)
float get_view_scale()
double get_fps()
```

* `get_view` — Returns the current viewport width/height in pixels.
* `get_view_scale` — Returns the viewport reference scale (for DPI scaling, etc).
* `get_fps()` — Returns current frames per second.

***

**📏 Basic Shapes**

**Rectangle**

```cpp
void draw_rect(float x,float y,float w,float h,
               uint8 r,uint8 g,uint8 b,uint8 a,
               float thickness, float rounding, uint8 rounding_flags)
```

Draws an **outlined rectangle**.

**Filled Rectangle**

```cpp
void draw_rect_filled(float x,float y,float w,float h,
                      uint8 r,uint8 g,uint8 b,uint8 a,
                      float rounding, uint8 rounding_flags)
```

Draws a **filled rectangle**.

**Line**

```cpp
void draw_line(float x1,float y1,float x2,float y2,
               uint8 r,uint8 g,uint8 b,uint8 a, float thickness)
```

Draws a line between `(x1,y1)` and `(x2,y2)`.

**Arc**

```cpp
void draw_arc(float cx, float cy, float rx, float ry,
              float start_angle_deg, float sweep_angle_deg,
              uint8 r, uint8 g, uint8 b, uint8 a,
              float thickness, bool filled)
```

Draws an arc or pie-slice centered at `(cx, cy)`.

**Circle**

```cpp
void draw_circle(float cx,float cy,float radius,
                 uint8 r,uint8 g,uint8 b,uint8 a,
                 float thickness, bool filled)
```

**Triangle**

```cpp
void draw_triangle(float ax,float ay,float bx,float by,float cx,float cy,
                   uint8 r,uint8 g,uint8 b,uint8 a,
                   float thickness, bool filled)
```

**Polygon**

```cpp
void draw_polygon(const array<float> &in xy_pairs, uint count_pairs,
                  uint8 r,uint8 g,uint8 b,uint8 a,
                  float thickness, bool filled)
```

* `xy_pairs` — `[x0, y0, x1, y1, …]`
* `count_pairs` — optional; set `0` to use full array length.

**Four Corner Gradient**

```cpp
void draw_four_corner_gradient(float x,float y,float w,float h,
    uint8 tlr,uint8 tlg,uint8 tlb,uint8 tla,
    uint8 trr,uint8 trg,uint8 trb,uint8 tra,
    uint8 blr,uint8 blg,uint8 blb,uint8 bla,
    uint8 brr,uint8 brg,uint8 brb,uint8 bra,
    float rounding)
```

Draws a gradient rectangle with individual RGBA colors for each corner.

***

**🖼️ Bitmaps**

```cpp
uint64 create_bitmap(const array<uint8> &in data)
void   draw_bitmap(uint64 bmp, float x,float y,float w,float h,
                   uint8 r,uint8 g,uint8 b,uint8 a, bool rounded)
```

* `create_bitmap` — Creates a bitmap from raw RGBA or compressed bytes. Returns an **encrypted handle** (`uint64`) used for drawing.
* `draw_bitmap` — Draws the bitmap tinted with color `(r,g,b,a)`.

***

**🔤 Fonts & Text**

```cpp
uint64 create_font(const string &in path, float size, bool antialias, 
bool load_color, array<uint> @glyph_ranges = null)
//load color should only be used for fonts that require texture coloring (e.g. emojis)

/* Automatically resolves font paths within the API directory
   (e.g., verdana_custom.ttf or fonts/verdana_custom.ttf).
   The API may also fall back to searching system font locations.
   If a system font shares the same name, it may be loaded instead.
   Use unique font names to avoid naming conflicts. */

uint64 create_font_mem(const string &in label, float size, const array<uint8> &in buf, 
 bool antialias, bool load_color, array<uint> @glyph_ranges = null)

uint64 get_font18() // default font of size 18
uint64 get_font20() // default font of size 20
uint64 get_font24() // default font of size 24
uint64 get_font28() // default font of size 28

// Using custom glyph ranges
array<uint> ranges = {
    0x0020, 0x00FF,   // Basic Latin + Latin-1 Supplement
    0x0400, 0x04FF,   // Cyrillic
    0
};
uint64 font2 = create_font("Arial", 16.0f, true, false, ranges);
```

**Text Drawing**

```cpp
void draw_text(const string &in text, float x,float y,
               uint8 r,uint8 g,uint8 b,uint8 a,
               uint64 font, int effect,
               uint8 er,uint8 eg,uint8 eb,uint8 ea,
               float effect_amount)
```

* `effect` — One of `TE_NONE`, `TE_OUTLINE`, `TE_SHADOW`, `TE_GLOW`.
* `effect_color` — `(er,eg,eb,ea)`.
* `effect_amount` — Intensity scalar.

**Text Metrics**

```cpp
void get_text_size(uint64 font, const string &in text, int maxw, int maxh,
                   float &out w, float &out h)
int get_char_advance(uint64 font, uint wchar32)
```

> Measure text dimensions or a single character's advance width.

***

**✂️ Clipping**

```cpp
void clip_push(float x,float y,float w,float h)
void clip_pop()
```

***

**Example**

```cpp
void draw_ui()
{
    float vw, vh; get_view(vw, vh);
    float cx = vw * 0.5f, cy = vh * 0.5f;

    uint64 font = get_font20();

    draw_rect_filled(cx - 100, cy - 50, 200, 100,
                     40, 40, 40, 255, 8.0f, RR_TOP_LEFT|RR_TOP_RIGHT);

    draw_text("Hello World", cx - 60, cy - 10,
              255,255,255,255, font, TE_SHADOW,
              0,0,0,180, 1.0f);
}
```

***

**🔺 Custom Draw (Shaders & Direct GPU Access)**

The custom draw API gives scripts direct access to the D3D11 GPU pipeline — custom HLSL shaders, vertex buffers, textures, render targets, and all primitive topologies. Custom draw commands respect draw order with all other render functions.

**Constants**

**Topology**

```cpp
const int TOPO_TRIANGLE_LIST    // Default. 3 vertices per triangle.
const int TOPO_TRIANGLE_STRIP   // Shared edges. N vertices = N-2 triangles.
const int TOPO_LINE_LIST        // 2 vertices per line segment.
const int TOPO_LINE_STRIP       // Connected line segments.
const int TOPO_POINT_LIST       // Individual points.
```

**Blend Factors**

```cpp
const int BLEND_ZERO
const int BLEND_ONE
const int BLEND_SRC_ALPHA
const int BLEND_INV_SRC_ALPHA
const int BLEND_DEST_ALPHA
const int BLEND_INV_DEST_ALPHA
const int BLEND_SRC_COLOR
const int BLEND_INV_SRC_COLOR
const int BLEND_DEST_COLOR
const int BLEND_INV_DEST_COLOR
```

**Blend Operations**

```cpp
const int BLEND_OP_ADD
const int BLEND_OP_SUBTRACT
const int BLEND_OP_REV_SUBTRACT
const int BLEND_OP_MIN
const int BLEND_OP_MAX
```

**Vertex Layout Element Types**

```cpp
const int ELEM_FLOAT1       // 4 bytes
const int ELEM_FLOAT2       // 8 bytes
const int ELEM_FLOAT3       // 12 bytes
const int ELEM_FLOAT4       // 16 bytes
const int ELEM_BYTE4_UNORM  // 4 bytes (normalized 0-1)
const int ELEM_UINT1        // 4 bytes
```

**Texture Filter Modes**

```cpp
const int FILTER_POINT
const int FILTER_LINEAR
const int FILTER_ANISOTROPIC
```

**Texture Address Modes**

```cpp
const int ADDRESS_WRAP
const int ADDRESS_CLAMP
const int ADDRESS_MIRROR
const int ADDRESS_BORDER
```

**Shaders**

```cpp
uint64 create_shader(const string &in vs_source, const string &in ps_source,
                     const string &in layout)
void   destroy_shader(uint64 shader)
```

Creates a compiled shader from HLSL source strings. The `layout` parameter is a format string describing the vertex input layout:

```
"POSITION:0:FLOAT2, COLOR:0:FLOAT4"
"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2"
"POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2"
```

Format: `SEMANTIC:semantic_index:TYPE` separated by commas. Supported types: `FLOAT1`, `FLOAT2`, `FLOAT3`, `FLOAT4`, `BYTE4`, `UINT1`.

Returns `0` on compilation failure. Shader entry point must be `main` for both VS and PS.

**Vertex Buffers**

```cpp
uint64 create_vertex_buffer(uint stride, uint max_vertices, bool dynamic)
void   destroy_vertex_buffer(uint64 vb)
```

* `stride` — Bytes per vertex (must match shader layout).
* `max_vertices` — Maximum number of vertices the buffer can hold.
* `dynamic` — `true` for per-frame updates (typical), `false` for static geometry.

**Constant Buffers**

```cpp
uint64 create_constant_buffer(uint size)
void   destroy_constant_buffer(uint64 cb)
```

Size is automatically aligned to 16 bytes. Bound to both VS and PS at the specified slot.

**Blend States**

```cpp
uint64 create_blend_state(int src, int dst, int op,
                          int src_alpha, int dst_alpha, int op_alpha)
void   destroy_blend_state(uint64 bs)
```

For premultiplied alpha (recommended for overlay rendering):

```cpp
uint64 blend = create_blend_state(BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                   BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
```

For standard alpha blending:

```cpp
uint64 blend = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                   BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
```

**Samplers**

```cpp
uint64 create_sampler(int filter, int address_u, int address_v)
void   destroy_sampler(uint64 s)
```

Controls how textures are sampled. `FILTER_LINEAR` for smooth scaling, `FILTER_POINT` for pixel-perfect rendering.

**Textures**

```cpp
uint64 create_texture(uint width, uint height, const array<uint8> &in rgba_data)
void   destroy_texture(uint64 tex)
```

Creates a texture from raw RGBA pixel data. The `rgba_data` array must be exactly `width * height * 4` bytes.

**Render Targets**

```cpp
uint64 create_render_target(uint width, uint height)
void   destroy_render_target(uint64 rt)
```

Creates an offscreen render target for multi-pass rendering. Pass `0` for width/height to match the viewport size.

**Drawing**

```cpp
void custom_draw(uint64 shader, uint64 vb,
                 const array<uint8> &in vertex_data, uint vertex_count,
                 int topology,
                 uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
                 uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

The main draw call. Submits custom geometry to the GPU using the specified shader and resources.

* `shader` — Required. Handle from `create_shader`.
* `vb` — Required. Handle from `create_vertex_buffer`.
* `vertex_data` — Raw vertex bytes packed into `array<uint8>`. Must match the shader's layout stride.
* `vertex_count` — Number of vertices to draw.
* `topology` — One of the `TOPO_*` constants.
* `blend` — Blend state handle, or `0` for default blending.
* `sampler` — Sampler handle, or `0` for no sampler.
* `texture` — Texture handle, or `0` for no texture.
* `tex_slot` — Texture/sampler register slot (usually `0`).
* `cb` — Constant buffer handle, or `0` for no constants.
* `cb_data` — Raw constant data as `array<uint8>`, or `null` if no constants.
* `cb_slot` — Constant buffer register slot (usually `0`).

> Custom draw commands respect draw order with all other render functions. If you call `draw_rect_filled`, then `custom_draw`, then `draw_text`, they render in exactly that order.

**Render Target Control**

```cpp
void custom_set_render_target(uint64 rt)
void custom_reset_render_target()
void custom_bind_rt_as_texture(uint64 rt, int slot)
void custom_restore_state()
```

* `custom_set_render_target` — Redirects subsequent `custom_draw` calls to an offscreen render target.
* `custom_reset_render_target` — Switches back to the main backbuffer.
* `custom_bind_rt_as_texture` — Binds a render target's contents as a texture for sampling in a shader.
* `custom_restore_state` — Resets the D3D11 pipeline state. Call after render target operations to ensure normal rendering continues correctly.

**Packing Vertex Data**

Since `custom_draw` takes raw bytes, you need to pack floats into `array<uint8>`. Use `fpToIEEE` to convert floats:

```cpp
void pack_float(array<uint8> &b, int offset, float val)
{
    uint bits = fpToIEEE(val);
    b[offset]     = uint8(bits & 0xFF);
    b[offset + 1] = uint8((bits >> 8) & 0xFF);
    b[offset + 2] = uint8((bits >> 16) & 0xFF);
    b[offset + 3] = uint8((bits >> 24) & 0xFF);
}
```

**Resource Cleanup**

All custom draw resources are automatically destroyed when a script is unloaded. You can also destroy them manually:

```cpp
destroy_shader(shader);
destroy_vertex_buffer(vb);
destroy_constant_buffer(cb);
destroy_blend_state(blend);
destroy_sampler(sampler);
destroy_texture(tex);
destroy_render_target(rt);
destroy_index_buffer(ib);
destroy_depth_stencil_state(ds);
destroy_rasterizer_state(rs);
destroy_compute_shader(cs);
destroy_structured_buffer(sb);
destroy_mesh(mesh);
destroy_depth_buffer(db);
```

***

**🔢 Index Buffers & Indexed Drawing**

```cpp
uint64 create_index_buffer(uint max_indices, bool use_32bit, bool dynamic)
void   destroy_index_buffer(uint64 ib)
```

* `max_indices` — Maximum number of indices the buffer can hold.
* `use_32bit` — `true` for 32-bit indices (`uint`), `false` for 16-bit (`uint16`). Use 32-bit for meshes with more than 65535 vertices.
* `dynamic` — `true` for per-frame updates, `false` for static geometry.

```cpp
void custom_draw_indexed(uint64 shader, uint64 vb,
    const array<uint8> &in vertex_data, uint vertex_count,
    uint64 ib, const array<uint8> &in index_data, uint index_count,
    int topology,
    uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
    uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

Same as `custom_draw` but uses an index buffer to avoid duplicating shared vertices. Useful for cubes, grids, and any geometry with shared edges.

***

**🧊 Depth/Stencil State**

```cpp
uint64 create_depth_stencil_state(bool depth_enable, bool depth_write, int compare_func)
void   destroy_depth_stencil_state(uint64 ds)
void   custom_set_depth_stencil_state(uint64 ds)
```

**Depth Comparison Constants**

```cpp
const int CMP_NEVER
const int CMP_LESS           // Standard 3D depth testing
const int CMP_EQUAL
const int CMP_LESS_EQUAL
const int CMP_GREATER
const int CMP_NOT_EQUAL
const int CMP_GREATER_EQUAL
const int CMP_ALWAYS         // Disable depth test (still writes if depth_write=true)
```

* `depth_enable` — Enable depth testing.
* `depth_write` — Write to depth buffer on pass.
* `compare_func` — One of the `CMP_*` constants.
* `custom_set_depth_stencil_state(0)` — Resets to default (no depth testing).

For solid 3D rendering, use `create_depth_stencil_state(true, true, CMP_LESS)`.

***

**🔳 Rasterizer State**

```cpp
uint64 create_rasterizer_state(int cull_mode, int fill_mode, bool scissor_enable)
void   destroy_rasterizer_state(uint64 rs)
void   custom_set_rasterizer_state(uint64 rs)
```

**Cull/Fill Constants**

```cpp
const int CULL_NONE          // Render both sides
const int CULL_FRONT
const int CULL_BACK          // Default — cull back-facing triangles

const int FILL_SOLID         // Default
const int FILL_WIREFRAME
```

* `scissor_enable` — Typically `true`. Required for clipping to work.
* `custom_set_rasterizer_state(0)` — Resets to default.

For 3D meshes where you want to see all faces (pyramids, etc), use `CULL_NONE`.

***

**📺 Viewport & Texture Binding**

```cpp
void custom_set_viewport(float x, float y, float w, float h)
void custom_reset_viewport()
void custom_bind_texture(uint64 texture, uint64 sampler, int slot)
```

* `custom_set_viewport` — Restricts rendering to a sub-region of the screen. Use before `draw_mesh` or `custom_draw` to confine 3D rendering to a panel.
* `custom_reset_viewport` — Restores the full viewport.
* `custom_bind_texture` — Binds a texture + sampler to a slot, persisting across subsequent draw calls. Pass `0` for texture to bind the backbuffer capture result.

***

**💻 Compute Shaders**

```cpp
uint64 create_compute_shader(const string &in cs_source)
void   destroy_compute_shader(uint64 cs)
void   dispatch_compute(uint64 cs, uint x, uint y, uint z)
```

Creates and dispatches a compute shader (cs\_5\_0). Entry point must be `main`. Thread group counts `(x, y, z)` are passed to `Dispatch()`.

Compute shaders are dispatched as state-only commands — no geometry is drawn. Use structured buffers for CS input/output.

**Bind Stage Constants**

```cpp
const int STAGE_VS   // Vertex shader (0)
const int STAGE_PS   // Pixel shader (1)
const int STAGE_CS   // Compute shader (2)
```

***

**📊 Structured Buffers**

```cpp
uint64 create_structured_buffer(uint element_size, uint element_count, bool cpu_write, bool gpu_write)
void   destroy_structured_buffer(uint64 sb)
void   update_structured_buffer(uint64 sb, const array<uint8> &in data)
void   bind_structured_buffer(uint64 sb, int slot, int stage)
```

* `element_size` — Size of each element in bytes (typically 16 for `float4`).
* `element_count` — Number of elements.
* `cpu_write` — `true` to allow CPU updates via `update_structured_buffer`. Creates SRV only.
* `gpu_write` — `true` to allow GPU writes from compute shaders. Creates both SRV and UAV.
* `bind_structured_buffer` — Binds the buffer to a shader stage. CS stage with `gpu_write` binds as UAV, otherwise SRV. Use `STAGE_VS`, `STAGE_PS`, or `STAGE_CS`.

**Example: GPU particle buffer**

```cpp
// Create: 16 bytes per particle (float4), 1024 particles, GPU-writable
uint64 sb = create_structured_buffer(16, 1024, false, true);

// In compute shader: bind as UAV for writing
bind_structured_buffer(sb, 0, STAGE_CS);
dispatch_compute(cs, 16, 1, 1);  // 16 groups × 64 threads = 1024 particles

// In pixel shader: bind as SRV for reading
bind_structured_buffer(sb, 0, STAGE_PS);
```

***

**📷 Backbuffer Capture**

```cpp
void capture_backbuffer(int slot)
```

Captures the current backbuffer contents to a staging texture and binds it as a shader resource at the specified slot. Use with a custom pixel shader to create post-processing effects like bloom, blur, color grading, or screen-space reflections.

```cpp
capture_backbuffer(0);
custom_bind_texture(0, sampler, 0);  // texture=0 uses the captured backbuffer
custom_draw(post_fx_shader, vb, fullscreen_quad, 6, TOPO_TRIANGLE_LIST, ...);
```

***

**🖼️ Texture Loading**

```cpp
uint64 load_texture_mem(const array<uint8> &in data)
uint64 load_texture(const string &in path)
void   get_texture_info(uint64 tex, float &out w, float &out h)
```

* `load_texture_mem` — Decodes PNG, JPG, BMP, TGA, or GIF from a byte array. Returns a texture handle (same type as `create_texture`).
* `load_texture` — Loads an image file from disk. Tries the script directory first, then the absolute path.
* `get_texture_info` — Returns the texture dimensions.
* Destroy with `destroy_texture(handle)`.

***

**🏔️ Mesh Loading (OBJ)**

```cpp
uint64 load_mesh_mem(const array<uint8> &in data)
uint64 load_mesh(const string &in path)
void   get_mesh_info(uint64 mesh, float &out vert_count, float &out index_count,
                     float &out min_x, float &out min_y, float &out min_z,
                     float &out max_x, float &out max_y, float &out max_z)
void   destroy_mesh(uint64 mesh)
```

Parses Wavefront OBJ format with support for positions (`v`), normals (`vn`), texture coordinates (`vt`), faces with 3+ vertices (auto-triangulated), and negative indices.

**Fixed vertex layout:** `POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2` — 32 bytes per vertex. Shaders used with loaded meshes must match this layout.

* `get_mesh_info` — Returns vertex/index counts and the axis-aligned bounding box.
* `load_mesh` — Loads from disk, tries script directory first.

***

**🔺 Drawing Meshes**

```cpp
void draw_mesh(uint64 mesh, uint64 shader, int topology,
               uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
               uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

Convenience draw call for loaded or procedural meshes. Binds the mesh's internal vertex/index buffers and calls `DrawIndexed` in one step. Pass `0` for optional handles (sampler, texture, cb). The shader layout must match the mesh's vertex format.

**Example: render a lit OBJ mesh**

```cpp
// Create mesh and shader
uint64 mesh = load_mesh("model.obj");
uint64 shader = create_shader(vs_3d, ps_lit,
    "POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2");
uint64 cb_mvp = create_constant_buffer(64);

// Each frame: build MVP matrix, draw
custom_set_viewport(x, y, w, h);
custom_set_rasterizer_state(rs_nocull);
custom_set_depth_stencil_state(ds_off);
draw_mesh(mesh, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb_mvp, mvp_data, 0);
custom_reset_viewport();
custom_set_rasterizer_state(0);
custom_set_depth_stencil_state(0);
custom_restore_state();
```

***

**🌊 Depth Buffers & 3D Rendering**

```cpp
uint64 create_depth_buffer(uint width, uint height)
void   destroy_depth_buffer(uint64 db)
void   custom_set_render_target_ext(uint64 rt, uint64 depth_buffer)
void   custom_clear_render_target(uint64 rt, float r, float g, float b, float a)
void   custom_clear_depth_buffer(uint64 db)
```

* `create_depth_buffer` — Creates a D24S8 depth/stencil buffer. Pass `0, 0` to match viewport size.
* `custom_set_render_target_ext` — Binds a render target with an optional depth buffer for proper 3D occlusion. Auto-clears both, sets viewport and scissor to RT dimensions. Pass `0` for depth buffer to use color-only (same behavior as `custom_set_render_target`).
* `custom_clear_render_target` — Clears a render target to a specific color without re-binding it.
* `custom_clear_depth_buffer` — Clears depth to 1.0 and stencil to 0.

**Example: solid 3D scene with depth**

```cpp
uint64 rt = create_render_target(400, 300);
uint64 db = create_depth_buffer(400, 300);
uint64 ds = create_depth_stencil_state(true, true, CMP_LESS);

// Render pass
custom_set_render_target_ext(rt, db);
custom_clear_render_target(rt, 0, 0, 0, 1);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs_nocull);
draw_mesh(mesh1, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb, mvp1_data, 0);
draw_mesh(mesh2, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb, mvp2_data, 0);
custom_reset_render_target();
custom_set_rasterizer_state(0);
custom_set_depth_stencil_state(0);

// Blit result to screen
custom_bind_rt_as_texture(rt, 0);
custom_draw(blit_shader, vb, quad, 6, TOPO_TRIANGLE_LIST, blend, sampler, 0, 0, cb, screen_cb, 0);
custom_restore_state();
```

***

**🎛️ Multi-CB Binding**

```cpp
void custom_bind_constant_buffer(uint64 cb, const array<uint8> &in data, int slot, int stage)
```

Binds a constant buffer to a specific register slot and shader stage, independently of draw calls. This persists across subsequent draws until changed. Use `STAGE_VS`, `STAGE_PS`, or `STAGE_CS`.

This enables multi-buffer shader setups where camera data lives on `b0`, material properties on `b1`, and lighting on `b2`:

```cpp
custom_bind_constant_buffer(cb_camera, camera_data, 0, STAGE_VS);   // b0 in VS
custom_bind_constant_buffer(cb_material, mat_data, 1, STAGE_PS);    // b1 in PS
custom_bind_constant_buffer(cb_light, light_data, 2, STAGE_PS);     // b2 in PS
draw_mesh(mesh, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, 0, null, 0);
```

Note: when using `custom_bind_constant_buffer` for the MVP, pass `0` for the `cb` parameter of `draw_mesh` to avoid it overwriting your manually bound buffers.

***

**🧱 Procedural Mesh**

```cpp
uint64 create_mesh_raw(const array<uint8> &in vertex_data, uint vertex_count, uint stride,
                       const array<uint8> &in index_data, uint index_count, bool use_32bit)
float  get_mesh_stride(uint64 mesh)
```

* `create_mesh_raw` — Builds a mesh from raw vertex and index byte arrays with any vertex layout. The shader must match the stride. Use for procedural terrain, generated geometry, or particle quads.
* `get_mesh_stride` — Returns the vertex stride in bytes (32 for OBJ-loaded meshes).
* Destroy with `destroy_mesh(handle)`.

The vertex data can use any layout — it's not restricted to the OBJ format's position+normal+uv.

***

**🎨 Dynamic Texture Update**

```cpp
void custom_update_texture(uint64 tex, uint x, uint y, uint w, uint h,
                           const array<uint8> &in rgba_data)
```

Performs a partial update of an existing texture. The `rgba_data` must be exactly `w * h * 4` bytes. Use for dynamic sprite sheets, minimaps, procedural atlases, or any per-frame texture content.

```cpp
// Update an 8x8 region at position (10, 10)
array<uint8> pixels(8 * 8 * 4);
// ... fill pixels ...
custom_update_texture(tex, 10, 10, 8, 8, pixels);
```

***

**🌌 Example: Nebula Shader**

```cpp
string vs_src =
"cbuffer cb : register(b0) { float2 screen; float time; float pad; };\n"
"struct vi { float2 pos : POSITION; float2 uv : TEXCOORD0; };\n"
"struct vo { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; float time : TEXCOORD1; float2 res : TEXCOORD2; };\n"
"vo main(vi i) {\n"
"    vo o;\n"
"    o.pos = float4(i.pos.x / screen.x * 2.0 - 1.0,\n"
"                   1.0 - i.pos.y / screen.y * 2.0, 0.0, 1.0);\n"
"    o.uv = i.uv;\n"
"    o.time = time;\n"
"    o.res = screen;\n"
"    return o;\n"
"}\n";

string ps_src =
"struct vo { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; float time : TEXCOORD1; float2 res : TEXCOORD2; };\n"
"\n"
"float hash(float2 p) {\n"
"    float3 p3 = frac(float3(p.xyx) * 0.1031);\n"
"    p3 += dot(p3, p3.yzx + 33.33);\n"
"    return frac((p3.x + p3.y) * p3.z);\n"
"}\n"
"\n"
"float noise(float2 p) {\n"
"    float2 i = floor(p);\n"
"    float2 f = frac(p);\n"
"    f = f * f * (3.0 - 2.0 * f);\n"
"    float a = hash(i);\n"
"    float b = hash(i + float2(1.0, 0.0));\n"
"    float c = hash(i + float2(0.0, 1.0));\n"
"    float d = hash(i + float2(1.0, 1.0));\n"
"    return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);\n"
"}\n"
"\n"
"float fbm(float2 p) {\n"
"    float v = 0.0;\n"
"    float a = 0.5;\n"
"    float2x2 rot = float2x2(0.8, 0.6, -0.6, 0.8);\n"
"    for (int i = 0; i < 5; i++) {\n"
"        v += a * noise(p);\n"
"        p = mul(rot, p) * 2.0;\n"
"        a *= 0.5;\n"
"    }\n"
"    return v;\n"
"}\n"
"\n"
"float4 main(vo i) : SV_TARGET {\n"
"    float2 uv = i.uv;\n"
"    float t = i.time * 0.25;\n"
"\n"
"    float2 p = uv * 3.0;\n"
"    float f1 = fbm(p + float2(t * 0.7, t * 0.4));\n"
"    float f2 = fbm(p + float2(f1 * 1.5 + t * 0.1, f1 * 1.2 - t * 0.2));\n"
"    float f3 = fbm(p + float2(f2 * 1.8 - t * 0.3, f2 * 0.9 + t * 0.5));\n"
"\n"
"    float3 c1 = float3(0.02, 0.01, 0.08);\n"
"    float3 c2 = float3(0.08, 0.3, 0.7);\n"
"    float3 c3 = float3(0.5, 0.08, 0.75);\n"
"    float3 c4 = float3(0.0, 0.7, 0.5);\n"
"\n"
"    float3 col = c1;\n"
"    col = lerp(col, c2, smoothstep(0.0, 0.6, f1));\n"
"    col = lerp(col, c3, smoothstep(0.2, 0.8, f2));\n"
"    col = lerp(col, c4, smoothstep(0.3, 0.7, f3 * f1));\n"
"\n"
"    col += float3(0.3, 0.15, 0.5) * pow(f3, 3.0) * 1.2;\n"
"\n"
"    float vignette = 1.0 - length((uv - 0.5) * 1.4);\n"
"    vignette = smoothstep(0.0, 0.7, vignette);\n"
"    col *= vignette;\n"
"\n"
"    float edge = smoothstep(0.0, 0.06, uv.x) * smoothstep(0.0, 0.06, uv.y)\n"
"               * smoothstep(0.0, 0.06, 1.0 - uv.x) * smoothstep(0.0, 0.06, 1.0 - uv.y);\n"
"\n"
"    float alpha = saturate(length(col) * 1.2) * edge * 0.9;\n"
"    return float4(col * alpha, alpha);\n"
"}\n";

uint64 g_shader = 0;
uint64 g_vb = 0;
uint64 g_cb = 0;
uint64 g_blend = 0;
int g_cb_id = 0;
float g_time = 0.0f;

void pack_float(array<uint8> &buf, int offset, float val)
{
    uint bits = fpToIEEE(val);
    buf[offset + 0] = uint8(bits & 0xFF);
    buf[offset + 1] = uint8((bits >> 8) & 0xFF);
    buf[offset + 2] = uint8((bits >> 16) & 0xFF);
    buf[offset + 3] = uint8((bits >> 24) & 0xFF);
}

void pack_quad(array<uint8> &buf, int offset,
    float x0, float y0, float x1, float y1)
{
    int o = offset;
    pack_float(buf, o,    x0); pack_float(buf, o+4,  y0);
    pack_float(buf, o+8,  0.0f); pack_float(buf, o+12, 0.0f); o += 16;
    pack_float(buf, o,    x1); pack_float(buf, o+4,  y0);
    pack_float(buf, o+8,  1.0f); pack_float(buf, o+12, 0.0f); o += 16;
    pack_float(buf, o,    x0); pack_float(buf, o+4,  y1);
    pack_float(buf, o+8,  0.0f); pack_float(buf, o+12, 1.0f); o += 16;
    pack_float(buf, o,    x1); pack_float(buf, o+4,  y0);
    pack_float(buf, o+8,  1.0f); pack_float(buf, o+12, 0.0f); o += 16;
    pack_float(buf, o,    x1); pack_float(buf, o+4,  y1);
    pack_float(buf, o+8,  1.0f); pack_float(buf, o+12, 1.0f); o += 16;
    pack_float(buf, o,    x0); pack_float(buf, o+4,  y1);
    pack_float(buf, o+8,  0.0f); pack_float(buf, o+12, 1.0f);
}

void on_frame(int cb_id, int data)
{
    double fps = get_fps();
    if (fps > 0.0)
        g_time += float(1.0 / fps);

    float sw, sh;
    get_view(sw, sh);

    float panel_w = 440.0f;
    float panel_h = 270.0f;
    float panel_x = (sw - panel_w) * 0.5f;
    float panel_y = (sh - panel_h) * 0.5f - 60.0f;

    draw_rect_filled(panel_x - 2, panel_y - 2, panel_w + 4, panel_h + 4,
        120, 80, 200, 35, 12.0f,
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT);

    array<uint8> verts(6 * 16);
    pack_quad(verts, 0, panel_x, panel_y, panel_x + panel_w, panel_y + panel_h);

    array<uint8> cb_data(16);
    pack_float(cb_data, 0,  sw);
    pack_float(cb_data, 4,  sh);
    pack_float(cb_data, 8,  g_time);
    pack_float(cb_data, 12, 0.0f);

    custom_draw(g_shader, g_vb, verts, 6, TOPO_TRIANGLE_LIST,
        g_blend, 0, 0, 0,
        g_cb, cb_data, 0);

    draw_rect(panel_x - 1, panel_y - 1, panel_w + 2, panel_h + 2,
        255, 255, 255, 25, 1.0f, 12.0f,
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT);

    uint64 font = get_font18();
    float tw, th;

    string title = "Perception.cx";
    get_text_size(font, title, -1, -1, tw, th);
    draw_text(title, panel_x + (panel_w - tw) * 0.5f, panel_y + panel_h + 12,
        200, 180, 255, 190, font, TE_NONE, 0, 0, 0, 0, 0.0f);

    string info = "FPS: " + formatFloat(fps, "", 0, 1);
    get_text_size(font, info, -1, -1, tw, th);
    draw_text(info, panel_x + (panel_w - tw) * 0.5f, panel_y + panel_h + 32,
        140, 140, 140, 130, font, TE_NONE, 0, 0, 0, 0, 0.0f);
}

int main()
{
    g_shader = create_shader(vs_src, ps_src, "POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2");

    if (g_shader == 0)
    {
        log_error("shader compilation failed");
        return -1;
    }

    g_vb    = create_vertex_buffer(16, 64, true);
    g_cb    = create_constant_buffer(16);
    g_blend = create_blend_state(BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);

    if (g_vb == 0 || g_cb == 0 || g_blend == 0)
    {
        log_error("resource creation failed");
        return -1;
    }

    log("custom shader test loaded");
    g_cb_id = register_callback(@on_frame, 1, 0);
    return 1;
}

void on_unload()
{
    if (g_cb_id > 0)
        unregister_callback(g_cb_id);

    if (g_shader != 0) destroy_shader(g_shader);
    if (g_vb != 0)     destroy_vertex_buffer(g_vb);
    if (g_cb != 0)     destroy_constant_buffer(g_cb);
    if (g_blend != 0)  destroy_blend_state(g_blend);

    log("custom shader test unloaded");
}
```

***

**🧪 Example: Full API Test**

```cpp
string vs_uv =
"cbuffer cb:register(b0){float2 screen;float time;float pad;};\n"
"struct vi{float2 pos:POSITION;float2 uv:TEXCOORD0;};\n"
"struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
"vo main(vi i){vo o;\n"
"  o.pos=float4(i.pos.x/screen.x*2-1,1-i.pos.y/screen.y*2,0,1);\n"
"  o.uv=i.uv;o.time=time;return o;}\n";

string ps_nebula =
"struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
"float hash(float2 p){float3 p3=frac(float3(p.xyx)*0.1031);p3+=dot(p3,p3.yzx+33.33);return frac((p3.x+p3.y)*p3.z);}\n"
"float noise(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);\n"
"  return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+float2(1,1)),f.x),f.y);}\n"
"float fbm(float2 p){float v=0,a=0.5;float2x2 r={0.8,0.6,-0.6,0.8};\n"
"  for(int i=0;i<5;i++){v+=a*noise(p);p=mul(r,p)*2;a*=0.5;}return v;}\n"
"float4 main(vo i):SV_TARGET{\n"
"  float t=i.time*0.25;float2 p=i.uv*3;\n"
"  float f1=fbm(p+float2(t*0.7,t*0.4));\n"
"  float f2=fbm(p+float2(f1*1.5+t*0.1,f1*1.2-t*0.2));\n"
"  float f3=fbm(p+float2(f2*1.8-t*0.3,f2*0.9+t*0.5));\n"
"  float3 c=float3(0.02,0.01,0.08);\n"
"  c=lerp(c,float3(0.08,0.3,0.7),smoothstep(0,0.6,f1));\n"
"  c=lerp(c,float3(0.5,0.08,0.75),smoothstep(0.2,0.8,f2));\n"
"  c=lerp(c,float3(0,0.7,0.5),smoothstep(0.3,0.7,f3*f1));\n"
"  c+=float3(0.3,0.15,0.5)*pow(f3,3)*1.2;\n"
"  float v=smoothstep(0,0.7,1-length((i.uv-0.5)*1.4));\n"
"  float e=smoothstep(0,0.05,i.uv.x)*smoothstep(0,0.05,i.uv.y)*smoothstep(0,0.05,1-i.uv.x)*smoothstep(0,0.05,1-i.uv.y);\n"
"  float a=saturate(length(c)*1.2)*v*e*0.92;\n"
"  return float4(c*a,a);}\n";

string ps_tex =
"Texture2D tex0:register(t0);SamplerState samp0:register(s0);\n"
"struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
"float4 main(vo i):SV_TARGET{float4 c=tex0.Sample(samp0,i.uv);return float4(c.rgb*c.a,c.a);}\n";

string vs_col =
"cbuffer cb:register(b0){float2 screen;float time;float pad;};\n"
"struct vi{float2 pos:POSITION;float4 col:COLOR;};\n"
"struct vo{float4 pos:SV_POSITION;float4 col:COLOR;};\n"
"vo main(vi i){vo o;o.pos=float4(i.pos.x/screen.x*2-1,1-i.pos.y/screen.y*2,0,1);o.col=i.col;return o;}\n";

string ps_col =
"struct vo{float4 pos:SV_POSITION;float4 col:COLOR;};\n"
"float4 main(vo i):SV_TARGET{return float4(i.col.rgb*i.col.a,i.col.a);}\n";

uint64 g_sh_nebula=0, g_sh_tex=0, g_sh_col=0;
uint64 g_vb_uv=0, g_vb_col=0, g_cb=0, g_blend=0;
uint64 g_samp_linear=0, g_samp_point=0;
uint64 g_texture=0, g_rt=0;
int g_cb_id=0;
float g_time=0;

void pf(array<uint8> &b,int o,float v){uint bits=fpToIEEE(v);b[o]=uint8(bits&0xFF);b[o+1]=uint8((bits>>8)&0xFF);b[o+2]=uint8((bits>>16)&0xFF);b[o+3]=uint8((bits>>24)&0xFF);}

int vu(array<uint8> &b,int o,float x,float y,float u,float v){pf(b,o,x);pf(b,o+4,y);pf(b,o+8,u);pf(b,o+12,v);return o+16;}
int vc(array<uint8> &b,int o,float x,float y,float r,float g,float bl,float a){pf(b,o,x);pf(b,o+4,y);pf(b,o+8,r);pf(b,o+12,g);pf(b,o+16,bl);pf(b,o+20,a);return o+24;}

int qu(array<uint8> &b,int o,float x0,float y0,float x1,float y1){
    o=vu(b,o,x0,y0,0,0);o=vu(b,o,x1,y0,1,0);o=vu(b,o,x0,y1,0,1);
    o=vu(b,o,x1,y0,1,0);o=vu(b,o,x1,y1,1,1);o=vu(b,o,x0,y1,0,1);return o;}

array<uint8> mcb(float sw,float sh){array<uint8> c(16);pf(c,0,sw);pf(c,4,sh);pf(c,8,g_time);pf(c,12,0);return c;}

void label(uint64 font,float cx,float y,const string &in text,uint8 a=180){
    float tw,th; get_text_size(font,text,-1,-1,tw,th);
    draw_text(text,cx-tw*0.5f,y,190,175,235,a,font,TE_NONE,0,0,0,0,0);
}

void sublabel(uint64 font,float cx,float y,const string &in text){
    float tw,th; get_text_size(font,text,-1,-1,tw,th);
    draw_text(text,cx-tw*0.5f,y,140,135,160,140,font,TE_NONE,0,0,0,0,0);
}

void border(float x,float y,float w,float h,float r=6){
    draw_rect(x-1,y-1,w+2,h+2,255,255,255,25,1,r,RR_TOP_LEFT|RR_TOP_RIGHT|RR_BOTTOM_LEFT|RR_BOTTOM_RIGHT);
}

void on_frame(int cb_id,int data)
{
    double fps=get_fps();
    if(fps>0) g_time+=float(1.0/fps);

    float sw,sh; get_view(sw,sh);
    array<uint8> cb_data=mcb(sw,sh);
    uint64 font=get_font18();

    float total_w=780, total_h=340;
    float ox=(sw-total_w)*0.5f;
    float oy=(sh-total_h)*0.5f;
    float row1_y=oy+30;
    float gap=15;

    // title
    draw_rect_filled(ox-10,oy-10,total_w+20,total_h+20,20,15,35,140,12,
        RR_TOP_LEFT|RR_TOP_RIGHT|RR_BOTTOM_LEFT|RR_BOTTOM_RIGHT);
    border(ox-10,oy-10,total_w+20,total_h+20,12);
    label(font,ox+total_w*0.5f,oy+2,"Perception.cx  -  Custom Draw API Test",220);

    float p1x=ox, p1y=row1_y, p1w=300, p1h=200;
    {
        custom_set_render_target(g_rt);

        array<uint8> rt_cb(16);
        pf(rt_cb,0,320);pf(rt_cb,4,200);pf(rt_cb,8,g_time);pf(rt_cb,12,0);

        array<uint8> rv(6*16);int o=0;
        o=qu(rv,o,0,0,320,200);

        custom_draw(g_sh_nebula,g_vb_uv,rv,6,TOPO_TRIANGLE_LIST,g_blend,0,0,0,g_cb,rt_cb,0);
        custom_reset_render_target();

        custom_bind_rt_as_texture(g_rt,0);
        array<uint8> sv(6*16);o=0;
        o=qu(sv,o,p1x,p1y,p1x+p1w,p1y+p1h);
        custom_draw(g_sh_tex,g_vb_uv,sv,6,TOPO_TRIANGLE_LIST,g_blend,g_samp_linear,0,0,g_cb,cb_data,0);
        custom_restore_state();

        border(p1x,p1y,p1w,p1h);
        label(font,p1x+p1w*0.5f,p1y+p1h+6,"Render Target -> Blit");
        sublabel(font,p1x+p1w*0.5f,p1y+p1h+24,"set_rt / reset_rt / bind_rt / restore");
    }

    float p2x=p1x+p1w+gap, p2y=row1_y, p2w=150, p2h=200;
    {
        float half=p2w*0.5f;

        array<uint8> lv(6*16);int o=0;
        o=qu(lv,o,p2x,p2y,p2x+half,p2y+p2h);
        custom_draw(g_sh_tex,g_vb_uv,lv,6,TOPO_TRIANGLE_LIST,g_blend,g_samp_linear,g_texture,0,g_cb,cb_data,0);

        array<uint8> rv(6*16);o=0;
        o=qu(rv,o,p2x+half,p2y,p2x+p2w,p2y+p2h);
        custom_draw(g_sh_tex,g_vb_uv,rv,6,TOPO_TRIANGLE_LIST,g_blend,g_samp_point,g_texture,0,g_cb,cb_data,0);

        border(p2x,p2y,p2w,p2h,0);
        draw_line(p2x+half,p2y,p2x+half,p2y+p2h,255,255,255,40,1);

        label(font,p2x+p2w*0.5f,p2y+p2h+6,"LINEAR | POINT");
        sublabel(font,p2x+p2w*0.5f,p2y+p2h+24,"texture + sampler");
    }
    
    float p3x=p2x+p2w+gap, p3y=row1_y, p3w=300, p3h=200;
    {
        draw_rect_filled(p3x,p3y,p3w,p3h,15,12,30,100,6,
            RR_TOP_LEFT|RR_TOP_RIGHT|RR_BOTTOM_LEFT|RR_BOTTOM_RIGHT);
        border(p3x,p3y,p3w,p3h);

        float sec=p3h/5.0f;
        float ty=p3y;
        float draw_x=p3x+p3w*0.45f;
        float draw_w=p3w*0.48f;

        // TRIANGLE_LIST
        {
            array<uint8> v(3*24);int o=0;
            float cx=draw_x+draw_w*0.5f;
            o=vc(v,o,cx,ty+6,1,0.2f,0.2f,1);
            o=vc(v,o,cx+16,ty+sec-6,0.2f,1,0.2f,1);
            o=vc(v,o,cx-16,ty+sec-6,0.2f,0.2f,1,1);
            custom_draw(g_sh_col,g_vb_col,v,3,TOPO_TRIANGLE_LIST,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("TRIANGLE_LIST",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
            ty+=sec;
        }

        // TRIANGLE_STRIP
        {
            array<uint8> v(4*24);int o=0;
            float lx=draw_x+draw_w*0.3f;
            o=vc(v,o,lx,ty+6,1,0.6f,0,1);
            o=vc(v,o,lx+30,ty+6,1,0.9f,0.2f,1);
            o=vc(v,o,lx+8,ty+sec-6,0.9f,1,0.3f,1);
            o=vc(v,o,lx+38,ty+sec-6,1,1,0.5f,1);
            custom_draw(g_sh_col,g_vb_col,v,4,TOPO_TRIANGLE_STRIP,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("TRIANGLE_STRIP",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
            ty+=sec;
        }

        // LINE_LIST
        {
            array<uint8> v(4*24);int o=0;
            float lx=draw_x+draw_w*0.2f;
            o=vc(v,o,lx,ty+8,0,1,1,1);
            o=vc(v,o,lx+draw_w*0.5f,ty+sec-8,0,1,1,1);
            o=vc(v,o,lx+15,ty+8,1,0,1,1);
            o=vc(v,o,lx+draw_w*0.5f+15,ty+sec-8,1,0,1,1);
            custom_draw(g_sh_col,g_vb_col,v,4,TOPO_LINE_LIST,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("LINE_LIST",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
            ty+=sec;
        }

        // LINE_STRIP (animated)
        {
            array<uint8> v(8*24);int o=0;
            for(int i=0;i<8;i++){
                float f=float(i)/7.0f;
                float lx=draw_x+draw_w*0.15f+f*draw_w*0.7f;
                float ly=ty+sec*0.5f+sin(g_time*3+f*6.28f)*12;
                o=vc(v,o,lx,ly,f,1-f,0.5f,1);
            }
            custom_draw(g_sh_col,g_vb_col,v,8,TOPO_LINE_STRIP,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("LINE_STRIP",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
            ty+=sec;
        }

        // POINT_LIST
        {
            array<uint8> v(12*24);int o=0;
            for(int i=0;i<12;i++){
                float f=float(i)/11.0f;
                float px=draw_x+draw_w*0.15f+f*draw_w*0.7f;
                float py=ty+sec*0.5f+sin(f*6.28f*2+g_time)*6;
                o=vc(v,o,px,py,1,1,1,0.9f);
            }
            custom_draw(g_sh_col,g_vb_col,v,12,TOPO_POINT_LIST,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("POINT_LIST",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
        }

        label(font,p3x+p3w*0.5f,p3y+p3h+6,"All Topologies");
        sublabel(font,p3x+p3w*0.5f,p3y+p3h+24,"5 primitive types + per-vertex color");
    }
    
    string s="FPS: "+formatFloat(fps,"",0,1)+"   |   3 shaders   2 VBs   1 CB   1 blend   2 samplers   1 texture   1 RT   5 topologies";
    sublabel(font,ox+total_w*0.5f,oy+total_h-12,s);
}

array<uint8> make_checker(uint sz,uint tile){
    array<uint8> d(sz*sz*4);
    for(uint y=0;y<sz;y++){
        for(uint x=0;x<sz;x++){
            uint i=(y*sz+x)*4;
            bool w=(((x/tile)+(y/tile))%2)==0;
            d[i]=w?230:30;d[i+1]=w?220:30;d[i+2]=w?250:70;d[i+3]=255;
        }
    }
    return d;
}

int main()
{
    g_sh_nebula=create_shader(vs_uv,ps_nebula,"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2");
    g_sh_tex=create_shader(vs_uv,ps_tex,"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2");
    g_sh_col=create_shader(vs_col,ps_col,"POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    if(g_sh_nebula==0||g_sh_tex==0||g_sh_col==0){log_error("shader fail");return 1;}

    g_vb_uv=create_vertex_buffer(16,128,true);
    g_vb_col=create_vertex_buffer(24,128,true);
    if(g_vb_uv==0||g_vb_col==0){log_error("vb fail");return 1;}

    g_cb=create_constant_buffer(16);
    if(g_cb==0){log_error("cb fail");return 1;}

    g_blend=create_blend_state(BLEND_ONE,BLEND_INV_SRC_ALPHA,BLEND_OP_ADD,BLEND_ONE,BLEND_INV_SRC_ALPHA,BLEND_OP_ADD);
    if(g_blend==0){log_error("blend fail");return 1;}

    g_samp_linear=create_sampler(FILTER_LINEAR,ADDRESS_CLAMP,ADDRESS_CLAMP);
    g_samp_point=create_sampler(FILTER_POINT,ADDRESS_WRAP,ADDRESS_WRAP);
    if(g_samp_linear==0||g_samp_point==0){log_error("sampler fail");return 1;}

    array<uint8> checker=make_checker(8,2);
    g_texture=create_texture(8,8,checker);
    if(g_texture==0){log_error("texture fail");return 1;}

    g_rt=create_render_target(320,200);
    if(g_rt==0){log_error("rt fail");return 1;}

    log("custom draw test loaded — all resources created");
    g_cb_id=register_callback(@on_frame,1,0);
    return 1;
}

void on_unload()
{
    if(g_cb_id>0) unregister_callback(g_cb_id);
    if(g_sh_nebula!=0) destroy_shader(g_sh_nebula);
    if(g_sh_tex!=0) destroy_shader(g_sh_tex);
    if(g_sh_col!=0) destroy_shader(g_sh_col);
    if(g_vb_uv!=0) destroy_vertex_buffer(g_vb_uv);
    if(g_vb_col!=0) destroy_vertex_buffer(g_vb_col);
    if(g_cb!=0) destroy_constant_buffer(g_cb);
    if(g_blend!=0) destroy_blend_state(g_blend);
    if(g_samp_linear!=0) destroy_sampler(g_samp_linear);
    if(g_samp_point!=0) destroy_sampler(g_samp_point);
    if(g_texture!=0) destroy_texture(g_texture);
    if(g_rt!=0) destroy_render_target(g_rt);
    log("custom draw test unloaded");
}
```

***

**🧪 Example: Full API Test 2 — Advanced (3D, Compute, Mesh Loading)**

```cpp
uint64 g_sh_2d, g_sh_mat, g_sh_sb, g_sh_bb, g_sh_mesh_tex;
uint64 g_cs;
uint64 g_vb, g_cb_scr, g_cb_mvp, g_cb_mat;
uint64 g_blend, g_samp_lin, g_samp_pt;
uint64 g_rt, g_db, g_ds_on, g_ds_off, g_rs_nc;
uint64 g_mesh_pyr, g_mesh_quad;
uint64 g_tex_loaded, g_tex_dyn;
uint64 g_sb_gpu, g_sb_params;
int g_cb_id = 0;
float g_time = 0;
bool g_ok = false;

void wf(array<uint8> &buf, uint off, float val) {
    if (val == 0.0f) { buf[off]=0; buf[off+1]=0; buf[off+2]=0; buf[off+3]=0; return; }
    int s = 0;
    float v = val;
    if (v < 0.0f) { s = 1; v = -v; }
    int e = 127;
    while (v >= 2.0f && e < 254) { v /= 2.0f; e++; }
    while (v < 1.0f && e > 1) { v *= 2.0f; e--; }
    v -= 1.0f;
    uint m = uint(v * 8388608.0f);
    uint bits = uint(s) << 31 | uint(e) << 23 | (m & 0x7FFFFF);
    buf[off]   = uint8(bits & 0xFF);
    buf[off+1] = uint8((bits >> 8) & 0xFF);
    buf[off+2] = uint8((bits >> 16) & 0xFF);
    buf[off+3] = uint8((bits >> 24) & 0xFF);
}

float rf(const array<uint8> &buf, uint off) {
    uint bits = uint(buf[off]) | (uint(buf[off+1]) << 8) | (uint(buf[off+2]) << 16) | (uint(buf[off+3]) << 24);
    if (bits == 0) return 0.0f;
    int s = int((bits >> 31) & 1);
    int e = int((bits >> 23) & 0xFF) - 127;
    float val = 1.0f + float(bits & 0x7FFFFF) / 8388608.0f;
    if (e > 0) { for (int i = 0; i < e; i++) val *= 2.0f; }
    else if (e < 0) { for (int i = 0; i < -e; i++) val /= 2.0f; }
    return s != 0 ? -val : val;
}

array<uint8> fb(float a, float b, float c, float d) {
    array<uint8> r(16, 0);
    wf(r, 0, a); wf(r, 4, b); wf(r, 8, c); wf(r, 12, d);
    return r;
}

array<uint8> mat4_persp(float fov, float asp, float zn, float zf) {
    float f = cos(fov * 0.5f) / sin(fov * 0.5f);
    float r = zn - zf;
    array<uint8> m(64, 0);
    wf(m, 0, f / asp); wf(m, 20, f);
    wf(m, 40, (zf + zn) / r); wf(m, 44, -1);
    wf(m, 56, (2 * zf * zn) / r);
    return m;
}

array<uint8> mat4_roty(float a) {
    float c = cos(a), s = sin(a);
    array<uint8> m(64, 0);
    wf(m, 0, c); wf(m, 8, s); wf(m, 20, 1);
    wf(m, 32, -s); wf(m, 40, c);
    wf(m, 60, 1);
    return m;
}

array<uint8> mat4_rotx(float a) {
    float c = cos(a), s = sin(a);
    array<uint8> m(64, 0);
    wf(m, 0, 1); wf(m, 20, c); wf(m, 24, -s);
    wf(m, 36, s); wf(m, 40, c);
    wf(m, 60, 1);
    return m;
}

array<uint8> mat4_trans(float tx, float ty, float tz) {
    array<uint8> m(64, 0);
    wf(m, 0, 1); wf(m, 20, 1); wf(m, 40, 1);
    wf(m, 48, tx); wf(m, 52, ty); wf(m, 56, tz); wf(m, 60, 1);
    return m;
}

array<uint8> mat4_mul(const array<uint8> &a, const array<uint8> &b) {
    array<float> fa(16), fb2(16);
    for (uint i = 0; i < 16; i++) { fa[i] = rf(a, i * 4); fb2[i] = rf(b, i * 4); }
    array<uint8> r(64, 0);
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++) {
            float s = 0;
            for (int k = 0; k < 4; k++) s += fa[i * 4 + k] * fb2[k * 4 + j];
            wf(r, uint((i * 4 + j) * 4), s);
        }
    return r;
}

void quad_verts(array<uint8> &buf, uint off, float x0, float y0, float x1, float y1) {
    wf(buf, off,      x0); wf(buf, off + 4,  y0); wf(buf, off + 8,  0); wf(buf, off + 12, 0);
    wf(buf, off + 16, x1); wf(buf, off + 20, y0); wf(buf, off + 24, 1); wf(buf, off + 28, 0);
    wf(buf, off + 32, x1); wf(buf, off + 36, y1); wf(buf, off + 40, 1); wf(buf, off + 44, 1);
    wf(buf, off + 48, x0); wf(buf, off + 52, y0); wf(buf, off + 56, 0); wf(buf, off + 60, 0);
    wf(buf, off + 64, x1); wf(buf, off + 68, y1); wf(buf, off + 72, 1); wf(buf, off + 76, 1);
    wf(buf, off + 80, x0); wf(buf, off + 84, y1); wf(buf, off + 88, 0); wf(buf, off + 92, 1);
}

string g_vs_2d =
    "cbuffer cb:register(b0){float2 screen;float time;float pad;};\n"
    "struct vi{float2 pos:POSITION;float2 uv:TEXCOORD0;};\n"
    "struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
    "vo main(vi i){vo o;o.pos=float4(i.pos.x/screen.x*2-1,-(i.pos.y/screen.y*2-1),0,1);o.uv=i.uv;o.time=time;return o;}\n";

string g_ps_tex =
    "Texture2D tex0:register(t0);SamplerState samp0:register(s0);\n"
    "struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{return tex0.Sample(samp0,i.uv);}\n";

string g_vs_mesh =
    "cbuffer cb:register(b0){float4x4 mvp;};\n"
    "struct vi{float3 pos:POSITION;float3 norm:NORMAL;float2 uv:TEXCOORD0;};\n"
    "struct vo{float4 pos:SV_POSITION;float3 norm:TEXCOORD0;float2 uv:TEXCOORD1;};\n"
    "vo main(vi i){vo o;o.pos=mul(mvp,float4(i.pos,1));o.norm=i.norm;o.uv=i.uv;return o;}\n";

string g_ps_mat =
    "cbuffer cb_mat:register(b1){float4 mat_color;};\n"
    "struct vo{float4 pos:SV_POSITION;float3 norm:TEXCOORD0;float2 uv:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  float3 L=normalize(float3(0.4,0.8,0.6));\n"
    "  float ndl=saturate(dot(normalize(i.norm),L));\n"
    "  float3 col=mat_color.rgb*(ndl*0.7+0.3);\n"
    "  return float4(col,mat_color.a);}\n";

string g_ps_lit =
    "struct vo{float4 pos:SV_POSITION;float3 norm:TEXCOORD0;float2 uv:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  float3 L=normalize(float3(0.5,1.0,0.3));\n"
    "  float ndl=saturate(dot(normalize(i.norm),L));\n"
    "  return float4(float3(0.2,0.6,1.0)*ndl+float3(0.05,0.05,0.1),1);}\n";

string g_ps_mesh_tex =
    "Texture2D tex0:register(t0);SamplerState samp0:register(s0);\n"
    "struct vo{float4 pos:SV_POSITION;float3 norm:TEXCOORD0;float2 uv:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  float3 L=normalize(float3(0.5,1.0,0.3));\n"
    "  float ndl=saturate(dot(normalize(i.norm),L));\n"
    "  float4 tc=tex0.Sample(samp0,i.uv);\n"
    "  return float4(tc.rgb*(ndl*0.8+0.2),1);}\n";

string g_ps_sb_vis =
    "StructuredBuffer<float4> colors:register(t0);\n"
    "struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  uint x=clamp(uint(i.uv.x*16),0,15);\n"
    "  uint y=clamp(uint(i.uv.y*16),0,15);\n"
    "  return float4(colors[y*16+x].rgb,1);}\n";

string g_cs_src =
    "StructuredBuffer<float4> params:register(t1);\n"
    "RWStructuredBuffer<float4> buf:register(u0);\n"
    "[numthreads(16,16,1)] void main(uint3 id:SV_DispatchThreadID){\n"
    "  uint idx=id.y*16+id.x;\n"
    "  float t=params[0].x;\n"
    "  float u=id.x/15.0,v=id.y/15.0;\n"
    "  float r=0.5+0.5*sin(t*2+u*6.28);\n"
    "  float g=0.5+0.5*sin(t*1.5+v*6.28);\n"
    "  float b=0.5+0.5*cos(t+(u+v)*3.14);\n"
    "  buf[idx]=float4(r,g,b,1);}\n";

string g_ps_bb =
    "Texture2D tex0:register(t0);SamplerState samp0:register(s0);\n"
    "struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  float4 c=tex0.Sample(samp0,i.uv);\n"
    "  float3 inv=1.0-c.rgb;\n"
    "  float br=max(max(c.r,c.g),c.b);\n"
    "  return float4(br>0.01?inv:float3(0.12,0.12,0.18),1);}\n";

string g_obj =
    "v 0 0.8 0\nv -0.6 -0.5 0.6\nv 0.6 -0.5 0.6\nv 0.6 -0.5 -0.6\nv -0.6 -0.5 -0.6\n"
    "vn 0 0.447 0.894\nvn 0.894 0.447 0\nvn 0 0.447 -0.894\nvn -0.894 0.447 0\nvn 0 -1 0\n"
    "vt 0.5 1\nvt 0 0\nvt 1 0\n"
    "f 1/1/1 2/2/1 3/3/1\nf 1/1/2 3/2/2 4/3/2\nf 1/1/3 4/2/3 5/3/3\nf 1/1/4 5/2/4 2/3/4\n"
    "f 2/2/5 5/3/5 4/2/5\nf 2/2/5 4/2/5 3/3/5\n";

uint64 g_sh_lit;

void label(float x, float y, string text, uint8 r, uint8 g, uint8 b) {
    draw_text(text, x, y, r, g, b, 255, get_font18(), 0, 0, 0, 0, 0, 0.0f);
}

void border(float x, float y, float w, float h, uint8 r, uint8 g, uint8 b) {
    draw_rect(x - 2, y - 2, w + 4, h + 4, r, g, b, 255, 2, 0.0f, 0);
}

void render_cb(int callback_id, int data_index) {
    if (!g_ok) {
        draw_text("INIT FAILED", 100, 100, 255, 80, 80, 255, get_font24(), 0, 0, 0, 0, 0, 0.0f);
        return;
    }

    g_time += 0.016f;
    float sw = 0, sh = 0;
    get_view(sw, sh);
    array<uint8> cb_scr = fb(sw, sh, g_time, 0);

    float total_w = 740, total_h = 620;
    float ox = (sw - total_w) * 0.5f;
    float oy = (sh - total_h) * 0.5f;
    float gap = 14;
    float lbl_h = 22;

    draw_rect_filled(ox - 16, oy - 40, total_w + 32, total_h + 56, 10, 10, 18, 220, 6.0f, 0);
    draw_text("PCX Draw API - All 26 New Functions", ox, oy - 28, 200, 220, 255, 255, get_font20(), 0, 0, 0, 0, 0, 0.0f);

    // ===== ROW 1 =====
    float r1y = oy + 4;

    // A: Compute Shader + Structured Buffer
    float aw = 230, ah = 150;
    float ax = ox, ay = r1y + lbl_h;
    label(ax + 4, r1y, "A: Compute Shader + SB", 0, 255, 0);
    border(ax, ay, aw, ah, 0, 255, 0);

    array<uint8> params_data = fb(g_time, 0, 0, 0);
    update_structured_buffer(g_sb_params, params_data);
    bind_structured_buffer(g_sb_params, 1, STAGE_CS);
    bind_structured_buffer(g_sb_gpu, 0, STAGE_CS);
    dispatch_compute(g_cs, 1, 1, 1);
    bind_structured_buffer(g_sb_gpu, 0, STAGE_PS);
    array<uint8> va(96, 0);
    quad_verts(va, 0, ax, ay, ax + aw, ay + ah);
    custom_draw(g_sh_sb, g_vb, va, 6, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, g_cb_scr, cb_scr, 0);
    custom_restore_state();

    // B: Depth Buffer + draw_mesh into RT
    float bw = total_w - aw - gap, bh = ah + lbl_h;
    float bx = ax + aw + gap, by = r1y + lbl_h;
    label(bx + 4, r1y, "B: Depth Buffer + Multi-CB", 255, 160, 0);
    border(bx, by, bw, ah, 255, 160, 0);

    custom_set_render_target_ext(g_rt, g_db);
    custom_clear_render_target(g_rt, 0.04f, 0.04f, 0.08f, 1.0f);
    custom_clear_depth_buffer(g_db);
    custom_set_rasterizer_state(g_rs_nc);
    custom_set_depth_stencil_state(g_ds_on);

    array<uint8> proj = mat4_persp(1.0f, 256.0f / 180.0f, 0.1f, 100.0f);
    array<uint8> rxm = mat4_rotx(0.4f);

    array<uint8> ry1 = mat4_roty(g_time * 0.9f);
    array<uint8> t1 = mat4_trans(-0.5f, 0, -3.5f);
    array<uint8> tmp1 = mat4_mul(ry1, rxm);
    array<uint8> tmp2 = mat4_mul(tmp1, t1);
    array<uint8> mvp1 = mat4_mul(tmp2, proj);
    array<uint8> mat_blue = fb(0.2f, 0.4f, 1.0f, 1.0f);
    custom_bind_constant_buffer(g_cb_mat, mat_blue, 1, STAGE_PS);
    draw_mesh(g_mesh_pyr, g_sh_mat, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, g_cb_mvp, mvp1, 0);

    array<uint8> ry2 = mat4_roty(g_time * 0.9f + 0.6f);
    array<uint8> t2 = mat4_trans(0.5f, 0, -2.5f);
    array<uint8> tmp3 = mat4_mul(ry2, rxm);
    array<uint8> tmp4 = mat4_mul(tmp3, t2);
    array<uint8> mvp2 = mat4_mul(tmp4, proj);
    array<uint8> mat_red = fb(1.0f, 0.25f, 0.15f, 1.0f);
    custom_bind_constant_buffer(g_cb_mat, mat_red, 1, STAGE_PS);
    draw_mesh(g_mesh_pyr, g_sh_mat, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, g_cb_mvp, mvp2, 0);

    custom_reset_render_target();
    custom_set_rasterizer_state(0);
    custom_set_depth_stencil_state(0);
    custom_bind_rt_as_texture(g_rt, 0);
    array<uint8> vb2(96, 0);
    quad_verts(vb2, 0, bx, by, bx + bw, by + ah);
    custom_draw(g_sh_2d, g_vb, vb2, 6, TOPO_TRIANGLE_LIST, g_blend, g_samp_lin, 0, 0, g_cb_scr, cb_scr, 0);
    custom_restore_state();

    // ===== ROW 2 =====
    float r2y = ay + ah + gap;

    // C: Loaded Texture
    float cw = 160, ch = 120;
    float cx2 = ox, cy = r2y + lbl_h;
    label(cx2 + 4, r2y, "C: Texture Load", 255, 0, 255);
    border(cx2, cy, cw, ch, 255, 0, 255);
    custom_bind_texture(g_tex_loaded, g_samp_pt, 0);
    array<uint8> vc(96, 0);
    quad_verts(vc, 0, cx2, cy, cx2 + cw, cy + ch);
    custom_draw(g_sh_2d, g_vb, vc, 6, TOPO_TRIANGLE_LIST, g_blend, g_samp_pt, g_tex_loaded, 0, g_cb_scr, cb_scr, 0);
    custom_restore_state();

    // D: Lit Mesh
    float dw = 190, dh = 120;
    float dx2 = cx2 + cw + gap, dy = r2y + lbl_h;
    label(dx2 + 4, r2y, "D: Lit Mesh", 255, 50, 50);
    border(dx2, dy, dw, dh, 255, 50, 50);
    {
        array<uint8> projd = mat4_persp(1.0f, dw / dh, 0.1f, 100.0f);
        array<uint8> ryd = mat4_roty(g_time * 1.2f);
        array<uint8> rxd = mat4_rotx(0.3f);
        array<uint8> td = mat4_trans(0, 0, -3.0f);
        array<uint8> t1d = mat4_mul(ryd, rxd);
        array<uint8> t2d = mat4_mul(t1d, td);
        array<uint8> mvpd = mat4_mul(t2d, projd);

        custom_set_viewport(dx2, dy, dw, dh);
        custom_set_rasterizer_state(g_rs_nc);
        custom_set_depth_stencil_state(g_ds_off);
        draw_mesh(g_mesh_pyr, g_sh_lit, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, g_cb_mvp, mvpd, 0);
        custom_reset_viewport();
        custom_set_rasterizer_state(0);
        custom_set_depth_stencil_state(0);
        custom_restore_state();
    }

    // E: Textured Mesh
    float ew = total_w - cw - dw - gap * 2, eh = 120;
    float ex = dx2 + dw + gap, ey = r2y + lbl_h;
    label(ex + 4, r2y, "E: Textured Mesh", 255, 255, 255);
    border(ex, ey, ew, eh, 255, 255, 255);
    {
        array<uint8> proje = mat4_persp(1.0f, ew / eh, 0.1f, 100.0f);
        array<uint8> rye = mat4_roty(-g_time * 0.8f);
        array<uint8> rxe = mat4_rotx(0.5f);
        array<uint8> te = mat4_trans(0, 0, -3.0f);
        array<uint8> t1e = mat4_mul(rye, rxe);
        array<uint8> t2e = mat4_mul(t1e, te);
        array<uint8> mvpe = mat4_mul(t2e, proje);

        custom_set_viewport(ex, ey, ew, eh);
        custom_set_rasterizer_state(g_rs_nc);
        custom_set_depth_stencil_state(g_ds_off);
        draw_mesh(g_mesh_pyr, g_sh_mesh_tex, TOPO_TRIANGLE_LIST, g_blend, g_samp_lin, g_tex_loaded, 0, g_cb_mvp, mvpe, 0);
        custom_reset_viewport();
        custom_set_rasterizer_state(0);
        custom_set_depth_stencil_state(0);
        custom_restore_state();
    }

    // ===== ROW 3 =====
    float r3y = cy + ch + gap;

    // F: Dynamic Texture
    float fw = 200, fh = 120;
    float fx = ox, fy = r3y + lbl_h;
    label(fx + 4, r3y, "F: Dynamic Texture", 0, 200, 180);
    border(fx, fy, fw, fh, 0, 200, 180);
    {
        array<uint8> clear_px(32 * 32 * 4);
        for (uint i = 0; i < clear_px.length(); i += 4) {
            clear_px[i] = 25; clear_px[i+1] = 25; clear_px[i+2] = 45; clear_px[i+3] = 255;
        }
        custom_update_texture(g_tex_dyn, 0, 0, 32, 32, clear_px);

        int blk_x = int(g_time * 6) % 24;
        int blk_y = int(g_time * 4) % 24;
        array<uint8> block(8 * 8 * 4);
        for (int py = 0; py < 8; py++)
            for (int px = 0; px < 8; px++) {
                uint idx = uint((py * 8 + px) * 4);
                block[idx]     = uint8(255.0f * (0.5f + 0.5f * sin(g_time * 3.0f)));
                block[idx + 1] = uint8(255.0f * (0.5f + 0.5f * sin(g_time * 3.0f + 2.0f)));
                block[idx + 2] = 255;
                block[idx + 3] = 255;
            }
        custom_update_texture(g_tex_dyn, uint(blk_x), uint(blk_y), 8, 8, block);

        custom_bind_texture(g_tex_dyn, g_samp_pt, 0);
        array<uint8> vf(96, 0);
        quad_verts(vf, 0, fx, fy, fx + fw, fy + fh);
        custom_draw(g_sh_2d, g_vb, vf, 6, TOPO_TRIANGLE_LIST, g_blend, g_samp_pt, g_tex_dyn, 0, g_cb_scr, cb_scr, 0);
        custom_restore_state();
    }

    // G: Raw Mesh + Multi-CB
    float gw = 190, gh = 120;
    float gx = fx + fw + gap, gy = r3y + lbl_h;
    label(gx + 4, r3y, "G: Raw Mesh + Multi-CB", 100, 180, 255);
    border(gx, gy, gw, gh, 100, 180, 255);
    {
        float hue = g_time * 0.8f;
        array<uint8> mat_anim = fb(0.5f + 0.5f * sin(hue), 0.5f + 0.5f * sin(hue + 2.09f), 0.5f + 0.5f * sin(hue + 4.19f), 1.0f);
        array<uint8> projg = mat4_persp(1.0f, gw / gh, 0.1f, 100.0f);
        array<uint8> tg = mat4_trans(0, 0, -2.0f);
        array<uint8> mvpg = mat4_mul(tg, projg);

        custom_set_viewport(gx, gy, gw, gh);
        custom_set_rasterizer_state(g_rs_nc);
        custom_set_depth_stencil_state(g_ds_off);
        custom_bind_constant_buffer(g_cb_mvp, mvpg, 0, STAGE_VS);
        custom_bind_constant_buffer(g_cb_mat, mat_anim, 1, STAGE_PS);
        draw_mesh(g_mesh_quad, g_sh_mat, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, 0, null, 0);
        custom_reset_viewport();
        custom_set_rasterizer_state(0);
        custom_set_depth_stencil_state(0);
        custom_restore_state();
    }

    // H: Backbuffer Capture
    float hw = total_w - fw - gw - gap * 2, hh = 120;
    float hx = gx + gw + gap, hy = r3y + lbl_h;
    label(hx + 4, r3y, "H: Backbuffer Capture", 0, 255, 255);
    border(hx, hy, hw, hh, 0, 255, 255);
    {
        capture_backbuffer(0);
        custom_bind_texture(0, g_samp_lin, 0);
        array<uint8> vh(96, 0);
        quad_verts(vh, 0, hx, hy, hx + hw, hy + hh);
        custom_draw(g_sh_bb, g_vb, vh, 6, TOPO_TRIANGLE_LIST, g_blend, g_samp_lin, 0, 0, g_cb_scr, cb_scr, 0);
        custom_restore_state();
    }

    // Status bar
    float sy = fy + fh + 12;
    draw_rect_filled(ox - 8, sy - 4, total_w + 16, 22, 20, 20, 35, 200, 4.0f, 0);
    string status = "mesh_pyr=" + (g_mesh_pyr != 0 ? "OK" : "FAIL")
        + "   mesh_quad=" + (g_mesh_quad != 0 ? "OK" : "FAIL")
        + "   tex=" + (g_tex_loaded != 0 ? "OK" : "FAIL")
        + "   depth=" + (g_db != 0 ? "OK" : "FAIL")
        + "   rt=" + (g_rt != 0 ? "OK" : "FAIL")
        + "   cs=" + (g_cs != 0 ? "OK" : "FAIL");
    draw_text(status, ox, sy, 140, 160, 200, 255, get_font18(), 0, 0, 0, 0, 0, 0.0f);
}

int main() {
    log("PCX Draw API Test - init");

    string ly_2d = "POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2";
    string ly_mesh = "POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2";

    g_sh_2d       = create_shader(g_vs_2d, g_ps_tex, ly_2d);
    g_sh_sb       = create_shader(g_vs_2d, g_ps_sb_vis, ly_2d);
    g_sh_bb       = create_shader(g_vs_2d, g_ps_bb, ly_2d);
    g_sh_mat      = create_shader(g_vs_mesh, g_ps_mat, ly_mesh);
    g_sh_lit      = create_shader(g_vs_mesh, g_ps_lit, ly_mesh);
    g_sh_mesh_tex = create_shader(g_vs_mesh, g_ps_mesh_tex, ly_mesh);
    g_cs          = create_compute_shader(g_cs_src);

    g_vb       = create_vertex_buffer(16, 128, true);
    g_cb_scr   = create_constant_buffer(16);
    g_cb_mvp   = create_constant_buffer(64);
    g_cb_mat   = create_constant_buffer(16);
    g_blend    = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD, BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
    g_samp_lin = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
    g_samp_pt  = create_sampler(FILTER_POINT, ADDRESS_CLAMP, ADDRESS_CLAMP);

    g_rt     = create_render_target(256, 180);
    g_db     = create_depth_buffer(256, 180);
    g_ds_on  = create_depth_stencil_state(true, true, CMP_LESS);
    g_ds_off = create_depth_stencil_state(false, false, CMP_ALWAYS);
    g_rs_nc  = create_rasterizer_state(CULL_NONE, FILL_SOLID, true);

    g_sb_gpu    = create_structured_buffer(16, 256, false, true);
    g_sb_params = create_structured_buffer(16, 1, true, false);

    array<uint8> obj_bytes(g_obj.length());
    for (uint i = 0; i < g_obj.length(); i++) obj_bytes[i] = uint8(g_obj[i]);
    g_mesh_pyr = load_mesh_mem(obj_bytes);
    if (g_mesh_pyr != 0) {
        float vc, ic, mnx, mny, mnz, mxx, mxy, mxz;
        get_mesh_info(g_mesh_pyr, vc, ic, mnx, mny, mnz, mxx, mxy, mxz);
        log("Mesh: " + int(vc) + " verts, " + int(ic) + " idx, bounds " + mnx + "," + mny + "," + mnz + " -> " + mxx + "," + mxy + "," + mxz);
    } else {
        log_error("load_mesh_mem FAILED");
    }

    array<uint8> tga(18 + 16 * 16 * 4, 0);
    tga[2] = 2; tga[12] = 16; tga[14] = 16; tga[16] = 32; tga[17] = 0x20;
    for (int y = 0; y < 16; y++)
        for (int x = 0; x < 16; x++) {
            uint i = 18 + uint((y * 16 + x) * 4);
            bool cross = (x == y) || (x == 15 - y);
            tga[i]     = uint8(x * 17);
            tga[i + 1] = cross ? 255 : uint8(y * 17);
            tga[i + 2] = uint8((15 - x) * 17);
            tga[i + 3] = 255;
        }
    g_tex_loaded = load_texture_mem(tga);
    if (g_tex_loaded != 0) {
        float tw, th;
        get_texture_info(g_tex_loaded, tw, th);
        log("Texture: " + int(tw) + "x" + int(th));
    }

    array<uint8> dyn_px(32 * 32 * 4);
    for (uint i = 0; i < dyn_px.length(); i += 4) {
        dyn_px[i] = 30; dyn_px[i+1] = 30; dyn_px[i+2] = 50; dyn_px[i+3] = 255;
    }
    g_tex_dyn = create_texture(32, 32, dyn_px);

    array<uint8> raw_vb(4 * 32, 0);
    wf(raw_vb,  0,-0.6f); wf(raw_vb,  4,-0.5f); wf(raw_vb,  8, 0); wf(raw_vb, 12, 0); wf(raw_vb, 16, 0); wf(raw_vb, 20, 1); wf(raw_vb, 24, 0); wf(raw_vb, 28, 1);
    wf(raw_vb, 32, 0.6f); wf(raw_vb, 36,-0.5f); wf(raw_vb, 40, 0); wf(raw_vb, 44, 0); wf(raw_vb, 48, 0); wf(raw_vb, 52, 1); wf(raw_vb, 56, 1); wf(raw_vb, 60, 1);
    wf(raw_vb, 64, 0.6f); wf(raw_vb, 68, 0.5f); wf(raw_vb, 72, 0); wf(raw_vb, 76, 0); wf(raw_vb, 80, 0); wf(raw_vb, 84, 1); wf(raw_vb, 88, 1); wf(raw_vb, 92, 0);
    wf(raw_vb, 96,-0.6f); wf(raw_vb,100, 0.5f); wf(raw_vb,104, 0); wf(raw_vb,108, 0); wf(raw_vb,112, 0); wf(raw_vb,116, 1); wf(raw_vb,120, 0); wf(raw_vb,124, 0);
    array<uint8> raw_ib(24, 0);
    raw_ib[0]=0; raw_ib[4]=1; raw_ib[8]=2; raw_ib[12]=0; raw_ib[16]=2; raw_ib[20]=3;
    g_mesh_quad = create_mesh_raw(raw_vb, 4, 32, raw_ib, 6, true);
    if (g_mesh_quad != 0) {
        float stride = get_mesh_stride(g_mesh_quad);
        log("Raw mesh: stride=" + int(stride));
    }

    g_ok = g_sh_2d != 0 && g_sh_mat != 0 && g_sh_lit != 0 && g_sh_sb != 0
        && g_sh_bb != 0 && g_sh_mesh_tex != 0 && g_cs != 0
        && g_vb != 0 && g_cb_scr != 0 && g_cb_mvp != 0 && g_cb_mat != 0
        && g_blend != 0 && g_samp_lin != 0 && g_samp_pt != 0
        && g_rt != 0 && g_db != 0 && g_ds_on != 0 && g_ds_off != 0 && g_rs_nc != 0
        && g_mesh_pyr != 0 && g_mesh_quad != 0
        && g_tex_loaded != 0 && g_tex_dyn != 0
        && g_sb_gpu != 0 && g_sb_params != 0;

    if (!g_ok) { log_error("INIT FAILED"); return 0; }

    log("All OK");
    g_cb_id = register_callback(@render_cb, 16, 0);
    return g_cb_id > 0 ? 1 : 0;
}

void on_unload() {
    if (g_cb_id > 0) unregister_callback(g_cb_id);
}

```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/render-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
