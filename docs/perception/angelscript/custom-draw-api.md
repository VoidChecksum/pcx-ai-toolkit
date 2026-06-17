> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/custom-draw-api.md).

# Custom Draw API

The Custom Draw API gives scripts direct access to the **D3D11 GPU pipeline** — custom HLSL vertex, pixel, and compute shaders, vertex/index/constant/structured buffers, textures, render targets, depth buffers, and all primitive topologies.

Custom draw commands respect draw order with all other render functions. If you call `draw_rect_filled`, then `custom_draw`, then `draw_text`, they render in exactly that order.

All handles are `uint64` **encrypted handles** — pass them back into other calls, never dereference them. Every resource is automatically destroyed when the script unloads.

***

**📐 Constants**

**Topology**

```cpp
const int TOPO_TRIANGLE_LIST    // Default. 3 vertices per triangle.
const int TOPO_TRIANGLE_STRIP   // Shared edges. N vertices = N-2 triangles.
const int TOPO_LINE_LIST        // 2 vertices per line segment.
const int TOPO_LINE_STRIP       // Connected line segments.
const int TOPO_POINT_LIST       // Individual points.
```

**Depth Comparison**

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

**Cull / Fill Modes**

```cpp
const int CULL_NONE          // Render both sides
const int CULL_FRONT
const int CULL_BACK          // Default — cull back-facing triangles

const int FILL_SOLID         // Default
const int FILL_WIREFRAME
```

**Blend Factors / Operations**

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

const int BLEND_OP_ADD
const int BLEND_OP_SUBTRACT
const int BLEND_OP_REV_SUBTRACT
const int BLEND_OP_MIN
const int BLEND_OP_MAX
```

**Texture Filter / Address Modes**

```cpp
const int FILTER_POINT
const int FILTER_LINEAR
const int FILTER_ANISOTROPIC

const int ADDRESS_WRAP
const int ADDRESS_CLAMP
const int ADDRESS_MIRROR
const int ADDRESS_BORDER
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

**Bind Stage**

```cpp
const int STAGE_VS   // Vertex shader (0)
const int STAGE_PS   // Pixel shader (1)
const int STAGE_CS   // Compute shader (2)
```

***

**🧵 Layout String Format**

`create_shader` takes the vertex input layout as a comma-separated string of `SEMANTIC:semantic_index:TYPE` entries:

```
"POSITION:0:FLOAT2, COLOR:0:FLOAT4"
"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2"
"POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2"
```

Supported types: `FLOAT1` (4B), `FLOAT2` (8B), `FLOAT3` (12B), `FLOAT4` (16B), `BYTE4` (4B unorm), `UINT1` (4B). The sum of element sizes is the vertex **stride** — it must match the `stride` passed to `create_vertex_buffer` and the bytes you pack into `vertex_data`.

***

**🧩 Shaders**

```cpp
uint64 create_shader(const string &in vs_source, const string &in ps_source,
                     const string &in layout)
void   destroy_shader(uint64 shader)
```

Compiles `vs_5_0` + `ps_5_0` from HLSL source strings. Both entry points must be `main`. Returns `0` on compilation failure — always check before use.

***

**🎮 Resource Creation**

All creation functions return a `uint64` handle, or `0` on failure.

```cpp
uint64 create_vertex_buffer(uint stride, uint max_vertices, bool dynamic)
uint64 create_index_buffer(uint max_indices, bool use_32bit, bool dynamic)
uint64 create_constant_buffer(uint size)
uint64 create_blend_state(int src, int dst, int op, int src_alpha, int dst_alpha, int op_alpha)
uint64 create_sampler(int filter, int address_u, int address_v)
uint64 create_texture(uint width, uint height, const array<uint8> &in rgba_data)
uint64 create_render_target(uint width, uint height)
uint64 create_depth_buffer(uint width, uint height)
uint64 create_depth_stencil_state(bool depth_enable, bool depth_write, int compare_func)
uint64 create_rasterizer_state(int cull_mode, int fill_mode, bool scissor_enable)
```

* `create_vertex_buffer` — `stride` is bytes per vertex (must match the shader layout). `dynamic` = `true` for per-frame updates (typical), `false` for static geometry.
* `create_index_buffer` — `use_32bit` = `true` for 32-bit (`uint`) indices, `false` for 16-bit (`uint16`). Use 32-bit past 65535 vertices.
* `create_constant_buffer` — `size` is auto-aligned to 16 bytes.
* `create_blend_state` — Standard alpha: `(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD, BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD)`. Premultiplied (recommended for overlays): `(BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD, BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD)`.
* `create_sampler` — `FILTER_LINEAR` for smooth scaling, `FILTER_POINT` for pixel-perfect.
* `create_texture` — `rgba_data` must be exactly `width * height * 4` bytes.
* `create_render_target` — Offscreen color target. Pass `0, 0` to match the viewport size.
* `create_depth_buffer` — D24S8 depth/stencil buffer. Pass `0, 0` to match the viewport size.
* `create_depth_stencil_state` — For solid 3D use `create_depth_stencil_state(true, true, CMP_LESS)`.
* `create_rasterizer_state` — `scissor_enable` should usually be `true` so clipping works.

***

**🔺 Drawing**

```cpp
void custom_draw(uint64 shader, uint64 vb,
                 const array<uint8> &in vertex_data, uint vertex_count,
                 int topology,
                 uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
                 uint64 cb, const array<uint8> @cb_data, int cb_slot)

void custom_draw_indexed(uint64 shader, uint64 vb,
    const array<uint8> &in vertex_data, uint vertex_count,
    uint64 ib, const array<uint8> &in index_data, uint index_count,
    int topology,
    uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
    uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

* `shader`, `vb` — Required handles.
* `vertex_data` — Raw vertex bytes packed into `array<uint8>`, matching the shader's layout stride.
* `vertex_count` — Number of vertices to draw.
* `ib` / `index_data` / `index_count` (indexed only) — Index buffer handle, 16- or 32-bit index bytes, and count.
* `topology` — One of the `TOPO_*` constants.
* `blend` / `sampler` / `texture` / `cb` — Optional; pass `0` to skip binding.
* `tex_slot` — Texture/sampler register slot (usually `0`).
* `cb_data` — Raw constant data as `array<uint8>`, or `null` if no constants.
* `cb_slot` — Constant buffer register slot (usually `0`).

`custom_draw_indexed` reuses shared vertices through the index buffer — use it for cubes, grids, and any geometry with shared edges.

> Custom draw commands respect draw order with all other render functions.

**Packing Vertex Data**

`custom_draw` takes raw bytes, so floats must be packed into `array<uint8>`. Use `fpToIEEE`:

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

***

**🖼️ Render Target Operations**

```cpp
void custom_set_render_target(uint64 rt)
void custom_set_render_target_ext(uint64 rt, uint64 depth_buffer)
void custom_reset_render_target()
void custom_bind_rt_as_texture(uint64 rt, int slot)
void custom_clear_render_target(uint64 rt, float r, float g, float b, float a)
void custom_clear_depth_buffer(uint64 db)
void custom_restore_state()
```

* `custom_set_render_target` — Redirects subsequent `custom_draw` calls to an offscreen render target.
* `custom_set_render_target_ext` — Binds an RT with a depth buffer for proper 3D occlusion. Auto-clears both and sets viewport/scissor to RT dimensions. Pass `0` for the depth buffer for color-only.
* `custom_reset_render_target` — Switches back to the main backbuffer.
* `custom_bind_rt_as_texture` — Binds an RT's contents as a sampleable texture at `slot` — used to blit an offscreen pass to the screen.
* `custom_clear_render_target` — Clears an RT to a color without re-binding it.
* `custom_clear_depth_buffer` — Clears depth to 1.0 and stencil to 0.
* `custom_restore_state` — Resets the D3D11 pipeline state. **Call after any custom-pipeline sequence** before returning control to the 2D layer.

***

**🧊 State Management**

```cpp
void custom_set_depth_stencil_state(uint64 ds)
void custom_set_rasterizer_state(uint64 rs)
void custom_set_viewport(float x, float y, float w, float h)
void custom_reset_viewport()
void custom_bind_texture(uint64 texture, uint64 sampler, int slot)
void custom_bind_constant_buffer(uint64 cb, const array<uint8> &in data, int slot, int stage)
```

* `custom_set_depth_stencil_state` — Applies a depth-stencil state; pass `0` to reset to default (no depth testing).
* `custom_set_rasterizer_state` — Applies a rasterizer state; pass `0` to reset to default.
* `custom_set_viewport` — Restricts rendering to a sub-region — split-screen, picture-in-picture, or a 3D panel.
* `custom_reset_viewport` — Restores the full viewport.
* `custom_bind_texture` — Binds a texture + sampler to `slot`, persisting across draws. Pass `0` for the texture to bind the latest backbuffer capture.
* `custom_bind_constant_buffer` — Binds a constant buffer to a `slot` and `stage` independently of draw calls, persisting until changed. Enables multi-buffer setups (camera on `b0`, material on `b1`, lighting on `b2`). When binding the MVP this way, pass `0` for the draw call's `cb` so it doesn't overwrite your manual bindings.

***

**🏔️ Mesh & Texture Loading**

```cpp
uint64 create_mesh_raw(const array<uint8> &in vertex_data, uint vertex_count, uint stride,
                       const array<uint8> &in index_data, uint index_count, bool use_32bit)
uint64 load_mesh(const string &in path)
uint64 load_mesh_mem(const array<uint8> &in data)
void   get_mesh_info(uint64 mesh, float &out vert_count, float &out index_count,
                     float &out min_x, float &out min_y, float &out min_z,
                     float &out max_x, float &out max_y, float &out max_z)
float  get_mesh_stride(uint64 mesh)
void   destroy_mesh(uint64 mesh)

uint64 create_texture_from_file(const string &in path)   // alias of load_texture
uint64 load_texture(const string &in path)
uint64 load_texture_mem(const array<uint8> &in data)
uint64 create_dynamic_texture(uint width, uint height)
void   custom_update_texture(uint64 tex, uint x, uint y, uint w, uint h,
                             const array<uint8> &in rgba_data)
void   get_texture_info(uint64 tex, float &out w, float &out h)

void draw_mesh(uint64 mesh, uint64 shader, int topology,
               uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
               uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

* `create_mesh_raw` — Builds a mesh from raw vertex + index byte arrays with any layout. The shader must match the stride. Use for procedural terrain, generated geometry, or particle quads.
* `load_mesh` / `load_mesh_mem` — Parses Wavefront OBJ (`v`, `vn`, `vt`, 3+ vertex faces auto-triangulated, negative indices). Fixed layout `POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2` — 32 bytes/vertex; shaders must match. `load_mesh` tries the script directory first.
* `get_mesh_info` — Vertex/index counts and the axis-aligned bounding box. `get_mesh_stride` returns the vertex stride in bytes.
* `load_texture` / `load_texture_mem` — Decodes PNG, JPG, BMP, TGA, or GIF. `load_texture` tries the script directory first, then the absolute path. `create_texture_from_file` is an alias of `load_texture`.
* `create_dynamic_texture` — Allocates an updatable texture; feed it per-frame with `custom_update_texture`.
* `custom_update_texture` — Partial update; `rgba_data` must be exactly `w * h * 4` bytes. Use for sprite sheets, minimaps, or procedural atlases.
* `draw_mesh` — Convenience draw: binds the mesh's internal buffers and issues `DrawIndexed` in one call. Pass `0` for optional handles. The shader layout must match the mesh's vertex format.

***

**💻 Compute Shaders & Structured Buffers**

```cpp
uint64 create_compute_shader(const string &in cs_source)
void   destroy_compute_shader(uint64 cs)
void   dispatch_compute(uint64 cs, uint x, uint y, uint z)

uint64 create_structured_buffer(uint element_size, uint element_count, bool cpu_write, bool gpu_write)
void   destroy_structured_buffer(uint64 sb)
void   update_structured_buffer(uint64 sb, const array<uint8> &in data)
void   bind_structured_buffer(uint64 sb, int slot, int stage)
array<uint8> read_structured_buffer(uint64 sb)
```

* `create_compute_shader` — Compiles a `cs_5_0` shader. Entry point must be `main`.
* `dispatch_compute` — Dispatches with thread group counts `(x, y, z)`. A state-only command — no geometry is drawn.
* `create_structured_buffer` — `element_size` is bytes per element (16 for `float4`). `cpu_write` creates an SRV updatable from script; `gpu_write` creates a UAV writable from compute shaders. A buffer can be both.
* `update_structured_buffer` — Uploads new element bytes from script (requires `cpu_write`).
* `bind_structured_buffer` — Binds to a `slot` on `stage`. The `STAGE_CS` stage with `gpu_write` binds as a UAV; otherwise as an SRV.
* `read_structured_buffer` — Reads element bytes back to script (GPU → CPU).

**Example: GPU particle buffer**

```cpp
// 16 bytes per particle (float4), 1024 particles, GPU-writable
uint64 sb = create_structured_buffer(16, 1024, false, true);

bind_structured_buffer(sb, 0, STAGE_CS);   // bind as UAV for writing
dispatch_compute(cs, 16, 1, 1);            // 16 groups × 64 threads = 1024 particles

bind_structured_buffer(sb, 0, STAGE_PS);   // bind as SRV for reading in the pixel shader
```

***

**📷 Backbuffer Capture**

```cpp
void capture_backbuffer(int slot)
```

Captures the current backbuffer to a staging texture and binds it as a shader resource at `slot`. Combine with a custom pixel shader for post-processing — bloom, blur, color grading, screen-space reflections:

```cpp
capture_backbuffer(0);
custom_bind_texture(0, sampler, 0);  // texture=0 uses the captured backbuffer
custom_draw(post_fx_shader, vb, fullscreen_quad, 6, TOPO_TRIANGLE_LIST,
            blend, sampler, 0, 0, cb, fx_cb, 0);
```

***

**🟢 Example: Basic Colored Triangle**

```cpp
uint64 g_shader = 0;
uint64 g_vb = 0;
uint64 g_blend = 0;

void pack_float(array<uint8> &b, int o, float v)
{
    uint bits = fpToIEEE(v);
    b[o] = uint8(bits & 0xFF); b[o+1] = uint8((bits >> 8) & 0xFF);
    b[o+2] = uint8((bits >> 16) & 0xFF); b[o+3] = uint8((bits >> 24) & 0xFF);
}

int main()
{
    string vs =
        "struct vi { float2 pos : POSITION; float4 col : COLOR; };\n"
        "struct vo { float4 pos : SV_Position; float4 col : COLOR; };\n"
        "vo main(vi i) { vo o; o.pos = float4(i.pos, 0.0, 1.0); o.col = i.col; return o; }\n";
    string ps =
        "struct vo { float4 pos : SV_Position; float4 col : COLOR; };\n"
        "float4 main(vo i) : SV_Target { return i.col; }\n";

    g_shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    g_vb     = create_vertex_buffer(24, 3, true);  // 8 + 16 = 24 bytes/vertex
    g_blend  = create_blend_state(BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                   BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
    if (g_shader == 0 || g_vb == 0) { log_error("triangle setup failed"); return -1; }

    register_callback(@on_frame, 1, 0);
    return 1;
}

void on_frame(int cb_id, int data)
{
    array<uint8> v(3 * 24);
    // pos.xy, col.rgba per vertex
    pack_float(v, 0,  -0.5f); pack_float(v, 4,  -0.5f);
    pack_float(v, 8,   1.0f); pack_float(v, 12,  0.0f); pack_float(v, 16, 0.0f); pack_float(v, 20, 1.0f);
    pack_float(v, 24,  0.5f); pack_float(v, 28, -0.5f);
    pack_float(v, 32,  0.0f); pack_float(v, 36,  1.0f); pack_float(v, 40, 0.0f); pack_float(v, 44, 1.0f);
    pack_float(v, 48,  0.0f); pack_float(v, 52,  0.5f);
    pack_float(v, 56,  0.0f); pack_float(v, 60,  0.0f); pack_float(v, 64, 1.0f); pack_float(v, 68, 1.0f);

    custom_draw(g_shader, g_vb, v, 3, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, 0, null, 0);
    custom_restore_state();
}
```

***

**🧊 Example: Depth-Tested 3D Scene**

```cpp
uint64 rt = create_render_target(400, 300);
uint64 db = create_depth_buffer(400, 300);
uint64 ds = create_depth_stencil_state(true, true, CMP_LESS);
uint64 rs = create_rasterizer_state(CULL_NONE, FILL_SOLID, true);

// Render pass
custom_set_render_target_ext(rt, db);
custom_clear_render_target(rt, 0, 0, 0, 1);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs);
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

**💻 Example: Compute Shader**

```cpp
string cs =
    "RWStructuredBuffer<float4> particles : register(u0);\n"
    "[numthreads(64, 1, 1)]\n"
    "void main(uint3 id : SV_DispatchThreadID) {\n"
    "    particles[id.x].xy += particles[id.x].zw;  // advance by velocity\n"
    "}\n";

uint64 compute = create_compute_shader(cs);
uint64 sb = create_structured_buffer(16, 1024, false, true);  // float4 x 1024, GPU-writable

bind_structured_buffer(sb, 0, STAGE_CS);
dispatch_compute(compute, 16, 1, 1);        // 16 groups × 64 threads = 1024 particles

bind_structured_buffer(sb, 0, STAGE_PS);    // read positions in the pixel shader
```

***

**🌀 Example: Post-Processing (full-screen blur of the current frame)**

```cpp
void on_frame(int cb_id, int data)
{
    capture_backbuffer(0);                  // current frame -> texture slot 0
    custom_bind_texture(0, g_sampler, 0);
    custom_draw(g_blur_shader, g_vb, g_fullscreen_quad, 6, TOPO_TRIANGLE_LIST,
                g_blend, g_sampler, 0, 0, g_cb, g_fx_cb, 0);
    custom_restore_state();
}
```

***

**🧹 Resource Cleanup**

All custom draw resources are automatically destroyed when a script is unloaded. Manual destruction is optional and only needed to free a resource mid-script:

```cpp
destroy_shader(shader);
destroy_compute_shader(cs);
destroy_vertex_buffer(vb);
destroy_index_buffer(ib);
destroy_constant_buffer(cb);
destroy_structured_buffer(sb);
destroy_blend_state(blend);
destroy_sampler(sampler);
destroy_texture(tex);
destroy_render_target(rt);
destroy_depth_buffer(db);
destroy_depth_stencil_state(ds);
destroy_rasterizer_state(rs);
destroy_mesh(mesh);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/custom-draw-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
