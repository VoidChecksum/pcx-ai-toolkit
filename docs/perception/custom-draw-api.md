> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/custom-draw-api.md).

# Custom Draw API

The Custom Draw API gives scripts direct access to the **D3D11 GPU pipeline**. Write HLSL vertex, pixel, and compute shaders, create vertex/index/constant/structured buffers, textures, render targets, and depth buffers, then submit geometry with any primitive topology — all from script.

Custom draw commands respect draw order with every other render function. If you call `draw_rect_filled`, then `custom_draw`, then `draw_text`, they render in exactly that submission order.

These natives are part of the Render API and are auto-registered into every loaded script. Handles (`int64`) are encrypted pointers — pass them back into other calls, never dereference or do arithmetic on them. Every `create_*` / `load_*` handle is freed automatically on script unload.

## Constants

`topology` selects the primitive assembly mode:

| Constant | Value | Meaning |
| --- | --- | --- |
| `TOPO_TRIANGLE_LIST` | 0 | Default. 3 vertices per triangle. |
| `TOPO_TRIANGLE_STRIP` | 1 | Shared edges. N vertices = N-2 triangles. |
| `TOPO_LINE_LIST` | 2 | 2 vertices per line segment. |
| `TOPO_LINE_STRIP` | 3 | Connected line segments. |
| `TOPO_POINT_LIST` | 4 | Individual points. |

`compare_func` (depth-stencil), `int32`:

| Constant | Value | Constant | Value |
| --- | --- | --- | --- |
| `CMP_NEVER` | 0 | `CMP_GREATER` | 4 |
| `CMP_LESS` | 1 | `CMP_NOT_EQUAL` | 5 |
| `CMP_EQUAL` | 2 | `CMP_GREATER_EQUAL` | 6 |
| `CMP_LESS_EQUAL` | 3 | `CMP_ALWAYS` | 7 |

`fill_mode` and `cull_mode` (rasterizer), `int32`:

* `fill_mode`: `FILL_SOLID` (default), `FILL_WIREFRAME`.
* `cull_mode`: `CULL_BACK` (default), `CULL_FRONT`, `CULL_NONE` (render both sides).

`blend_factor` / `blend_op` / `filter` / `address` are shared with the rest of the Render API:

* `blend_factor`: 0=ZERO, 1=ONE, 2=SRC\_ALPHA, 3=INV\_SRC\_ALPHA, 4=DEST\_ALPHA, 5=INV\_DEST\_ALPHA, 6=SRC\_COLOR, 7=INV\_SRC\_COLOR, 8=DEST\_COLOR, 9=INV\_DEST\_COLOR.
* `blend_op`: 0=ADD, 1=SUBTRACT, 2=REV\_SUBTRACT, 3=MIN, 4=MAX.
* `filter`: 0=POINT, 1=LINEAR, 2=ANISOTROPIC.
* `address`: 0=WRAP, 1=CLAMP, 2=MIRROR, 3=BORDER.

`stage` selects the shader stage for binding calls: 0=VS, 1=PS, 2=CS (matches D3D11 shader stages).

## Layout string format

`create_shader` takes a vertex input layout as a comma-separated string of `SEMANTIC:INDEX:TYPE` entries:

```
"POSITION:0:FLOAT2, COLOR:0:FLOAT4"
"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2"
"POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2"
```

| Type | Bytes | Notes |
| --- | --- | --- |
| `FLOAT1` | 4 | single float |
| `FLOAT2` | 8 | |
| `FLOAT3` | 12 | |
| `FLOAT4` | 16 | |
| `BYTE4` | 4 | normalized 0–1 (unorm) |
| `UINT1` | 4 | |

The sum of all element sizes is the vertex **stride** — it must match the `stride` you pass to `create_vertex_buffer` and the byte layout you pack into `vertex_data`.

## Resource creation

All creation calls return an `int64` handle, or `0` on failure (shader compilation failure, allocation failure, etc). Always check for `0` before using a handle.

```cpp
int64 create_shader(string vs_source, string ps_source, string layout);
int64 create_compute_shader(string cs_source);
int64 create_vertex_buffer(uint32 stride, uint32 max_vertices, bool dynamic);
int64 create_index_buffer(uint32 max_indices, bool use_32bit, bool dynamic);
int64 create_constant_buffer(uint32 size);
int64 create_structured_buffer(uint32 element_size, uint32 element_count, bool cpu_write, bool gpu_write);
int64 create_blend_state(int32 src, int32 dst, int32 op, int32 src_alpha, int32 dst_alpha, int32 op_alpha);
int64 create_sampler(int32 filter, int32 address_u, int32 address_v);
int64 create_texture(uint32 width, uint32 height, array rgba_data);
int64 create_render_target(uint32 width, uint32 height);
int64 create_depth_buffer(uint32 width, uint32 height);
int64 create_depth_stencil_state(bool depth_enable, bool depth_write, int32 compare_func);
int64 create_rasterizer_state(int32 cull_mode, int32 fill_mode, bool scissor_enable);
```

* `create_shader` — Compiles `vs_5_0` + `ps_5_0` from HLSL source. Both entry points must be named `main`. `layout` describes the vertex input (see above).
* `create_compute_shader` — Compiles a `cs_5_0` compute shader. Entry point must be `main`.
* `create_vertex_buffer` — `stride` is bytes per vertex (must match shader layout). `dynamic` = `true` for per-frame updates (typical), `false` for static geometry.
* `create_index_buffer` — `use_32bit` = `true` for 32-bit indices (needed past 65535 vertices), `false` for 16-bit.
* `create_constant_buffer` — `size` is automatically aligned up to 16 bytes.
* `create_structured_buffer` — `element_size` is bytes per element (16 for `float4`). `cpu_write` creates an SRV updatable from script; `gpu_write` creates a UAV writable from compute shaders.
* `create_blend_state` — Standard alpha: `(SRC_ALPHA, INV_SRC_ALPHA, ADD, ONE, INV_SRC_ALPHA, ADD)`. Premultiplied (recommended for overlays): `(ONE, INV_SRC_ALPHA, ADD, ONE, INV_SRC_ALPHA, ADD)`.
* `create_sampler` — `LINEAR` for smooth scaling, `POINT` for pixel-perfect.
* `create_texture` — `rgba_data` must be exactly `width * height * 4` bytes.
* `create_render_target` — Offscreen color target for multi-pass rendering. Pass `0, 0` to match the viewport size.
* `create_depth_buffer` — D24S8 depth/stencil buffer. Pass `0, 0` to match the viewport size.
* `create_depth_stencil_state` — `depth_write` controls writes on pass. For solid 3D use `(true, true, CMP_LESS)`.
* `create_rasterizer_state` — `scissor_enable` should usually be `true` so clipping works.

## Drawing

```cpp
int64 custom_draw(int64 shader, int64 vb, array vertex_data, uint32 vertex_count, int32 topology,
                  int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                  int64 cb, array cb_data, int32 cb_slot);

int64 custom_draw_indexed(int64 shader, int64 vb, array vertex_data, uint32 vertex_count,
                          int64 ib, array index_data, uint32 index_count, int32 topology,
                          int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                          int64 cb, array cb_data, int32 cb_slot);
```

* `vertex_data` — Raw vertex bytes packed to match the shader layout stride.
* `vertex_count` — Number of vertices.
* `index_data` / `index_count` (indexed only) — Index bytes (16- or 32-bit per the index buffer) and count.
* `topology` — One of the `TOPO_*` constants.
* `blend` / `sampler` / `texture` / `cb` — Optional; pass `0` to skip binding any of them.
* `tex_slot` — Texture/sampler register slot (usually `0`).
* `cb_data` — Raw constant bytes, or an empty array if `cb` is `0`.
* `cb_slot` — Constant buffer register slot (usually `0`).

`custom_draw_indexed` reuses shared vertices through an index buffer — use it for cubes, grids, and any geometry with shared edges.

## Render target operations

```cpp
int64 custom_set_render_target(int64 rt);
int64 custom_set_render_target_ext(int64 rt, int64 depth_buffer);
int64 custom_reset_render_target();
int64 custom_bind_rt_as_texture(int64 rt, int32 slot);
int64 custom_clear_render_target(int64 rt, float64 r, float64 g, float64 b, float64 a);
int64 custom_clear_depth_buffer(int64 db);
int64 custom_restore_state();
```

* `custom_set_render_target` — Redirects subsequent `custom_draw` calls to an offscreen render target.
* `custom_set_render_target_ext` — Binds a render target with a depth buffer for proper 3D occlusion. Auto-clears both and sets the viewport/scissor to the RT dimensions. Pass `0` for the depth buffer for color-only.
* `custom_reset_render_target` — Switches back to the main backbuffer.
* `custom_bind_rt_as_texture` — Binds a render target's contents as a sampleable texture at `slot` — the way to blit an offscreen pass back to the screen.
* `custom_clear_render_target` — Clears an RT to an explicit color without re-binding it.
* `custom_clear_depth_buffer` — Clears depth to 1.0 and stencil to 0.
* `custom_restore_state` — Resets the D3D11 pipeline state. **Call after any custom-pipeline sequence** before returning control to the 2D layer.

## State management

```cpp
int64 custom_set_depth_stencil_state(int64 ds);
int64 custom_set_rasterizer_state(int64 rs);
int64 custom_set_viewport(float64 x, float64 y, float64 w, float64 h);
int64 custom_reset_viewport();
int64 custom_bind_texture(int64 texture, int64 sampler, int32 slot);
int64 custom_bind_constant_buffer(int64 cb, array data, int32 slot, int32 stage);
```

* `custom_set_depth_stencil_state` — Applies a depth-stencil state. Pass `0` to reset to default (no depth testing).
* `custom_set_rasterizer_state` — Applies a rasterizer state. Pass `0` to reset to default.
* `custom_set_viewport` — Restricts rendering to a sub-region — split-screen, picture-in-picture, or confining a 3D scene to a panel.
* `custom_reset_viewport` — Restores the full viewport.
* `custom_bind_texture` — Binds a texture + sampler to `slot`, persisting across subsequent draws. Pass `0` for the texture to bind the most recent backbuffer capture.
* `custom_bind_constant_buffer` — Binds a constant buffer to a specific `slot` and `stage` independently of draw calls, persisting until changed. Enables multi-buffer setups (camera on `b0`, material on `b1`, lighting on `b2`). When binding the MVP this way, pass `0` for the `cb` parameter of the draw call so it doesn't overwrite your manual bindings.

## Mesh & texture loading

```cpp
int64   create_mesh_raw(array vertex_data, uint32 vertex_count, uint32 stride,
                        array index_data, uint32 index_count, bool use_32bit);
int64   load_mesh(string path);
int64   load_mesh_mem(array data);
int64   get_mesh_vert_count(int64 mesh);
int64   get_mesh_index_count(int64 mesh);
float64 get_mesh_stride(int64 mesh);
float64 get_mesh_bounds_min_x(int64 mesh);  // ...min_y, min_z, max_x, max_y, max_z

int64   create_texture_from_file(string path);  // alias of load_texture
int64   load_texture(string path);
int64   load_texture_mem(array data);
int64   create_dynamic_texture(uint32 width, uint32 height);
int64   custom_update_texture(int64 tex, uint32 x, uint32 y, uint32 w, uint32 h, array rgba_data);
float64 get_texture_width(int64 tex);
float64 get_texture_height(int64 tex);

int64 draw_mesh(int64 mesh, int64 shader, int32 topology,
                int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                int64 cb, array cb_data, int32 cb_slot);
```

* `create_mesh_raw` — Builds a mesh from raw vertex + index bytes with any layout. The shader must match the stride. Use for procedural terrain, generated geometry, or particle quads.
* `load_mesh` / `load_mesh_mem` — Parses Wavefront OBJ (positions, normals, texcoords, 3+ vertex faces auto-triangulated, negative indices). Loaded meshes use a fixed layout `POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2` (32 bytes/vertex); shaders must match it. `load_mesh` tries the script directory first.
* `get_mesh_*` — Vertex/index counts, stride, and the axis-aligned bounding box.
* `load_texture` / `load_texture_mem` — Decodes PNG, JPG, BMP, TGA, or GIF. `load_texture` tries the script directory first, then the absolute path. `create_texture_from_file` is an alias of `load_texture`.
* `create_dynamic_texture` — Allocates an updatable texture; feed it per-frame with `custom_update_texture`.
* `custom_update_texture` — Partial update of an existing texture; `rgba_data` must be exactly `w * h * 4` bytes. Use for sprite sheets, minimaps, or procedural atlases.
* `draw_mesh` — Convenience draw for loaded/procedural meshes: binds the mesh's internal vertex/index buffers and issues `DrawIndexed` in one call. Pass `0` for optional handles. The shader layout must match the mesh's vertex format.

## Compute shaders & structured buffers

```cpp
int64 create_compute_shader(string cs_source);
int64 dispatch_compute(int64 cs, uint32 x, uint32 y, uint32 z);
int64 create_structured_buffer(uint32 element_size, uint32 element_count, bool cpu_write, bool gpu_write);
int64 update_structured_buffer(int64 sb, array data);
int64 bind_structured_buffer(int64 sb, int32 slot, int32 stage);
array read_structured_buffer(int64 sb);
```

* `dispatch_compute` — Dispatches a compute shader with thread group counts `(x, y, z)`. Dispatched as a state-only command — no geometry is drawn. Use structured buffers for input/output.
* `create_structured_buffer` — `cpu_write` makes it script-updatable (SRV); `gpu_write` makes it compute-writable (UAV). A buffer can be both.
* `update_structured_buffer` — Uploads new element bytes from script (requires `cpu_write`).
* `bind_structured_buffer` — Binds to a `slot` on `stage`. The CS stage with `gpu_write` binds as a UAV; otherwise as an SRV.
* `read_structured_buffer` — Reads element bytes back to script (GPU → CPU).

## Backbuffer capture

```cpp
int64 capture_backbuffer(int32 slot);
```

Captures the current backbuffer to a staging texture and binds it as a shader resource at `slot`. Combine with a custom pixel shader for post-processing — bloom, blur, color grading, screen-space effects:

```cpp
capture_backbuffer(0);
custom_bind_texture(0, sampler, 0);  // texture=0 uses the captured backbuffer
custom_draw(post_fx_shader, vb, fullscreen_quad, 6, TOPO_TRIANGLE_LIST,
            blend, sampler, 0, 0, cb, fx_cb, 0);
```

## Examples

### Basic colored triangle

```cpp
int64 g_shader;
int64 g_vb;

int64 main() {
    string vs = "struct VSIn { float2 pos : POSITION; float4 color : COLOR; };\n"
                "struct VSOut { float4 pos : SV_Position; float4 color : COLOR; };\n"
                "VSOut main(VSIn i) { VSOut o; o.pos = float4(i.pos, 0.0, 1.0); o.color = i.color; return o; }\n";
    string ps = "struct VSOut { float4 pos : SV_Position; float4 color : COLOR; };\n"
                "float4 main(VSOut i) : SV_Target { return i.color; }\n";

    g_shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    g_vb = create_vertex_buffer(24, 3, true);  // 2*4 + 4*4 = 24 bytes per vertex
    register_routine(cast<int64>(my_draw), 0);
    return 1;
}

void my_draw(int64 data) {
    float32[] verts;
    verts.push(-0.5f); verts.push(-0.5f);  verts.push(1); verts.push(0); verts.push(0); verts.push(1);
    verts.push( 0.5f); verts.push(-0.5f);  verts.push(0); verts.push(1); verts.push(0); verts.push(1);
    verts.push( 0.0f); verts.push( 0.5f);  verts.push(0); verts.push(0); verts.push(1); verts.push(1);

    float32[] no_cb;
    custom_draw(g_shader, g_vb, verts, 3, TOPO_TRIANGLE_LIST, 0, 0, 0, 0, 0, no_cb, 0);
}
```

### Depth-tested 3D scene

Render two meshes into an offscreen target with real depth occlusion, then blit the result to the screen:

```cpp
int64 rt = create_render_target(400, 300);
int64 db = create_depth_buffer(400, 300);
int64 ds = create_depth_stencil_state(true, true, CMP_LESS);
int64 rs = create_rasterizer_state(CULL_NONE, FILL_SOLID, true);

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

### Compute shader with structured buffer

```cpp
string cs = "RWStructuredBuffer<float4> particles : register(u0);\n"
            "[numthreads(64, 1, 1)]\n"
            "void main(uint3 id : SV_DispatchThreadID) {\n"
            "    particles[id.x].xy += particles[id.x].zw;  // advance by velocity\n"
            "}\n";

int64 compute = create_compute_shader(cs);
int64 sb = create_structured_buffer(16, 1024, false, true);  // float4 x 1024, GPU-writable

// Simulate on the GPU
bind_structured_buffer(sb, 0, 2 /* STAGE_CS */);
dispatch_compute(compute, 16, 1, 1);  // 16 groups * 64 threads = 1024 particles

// Read positions back (or bind to STAGE_PS to render directly)
bind_structured_buffer(sb, 0, 1 /* STAGE_PS */);
```

### Post-processing (full-screen blur of the current frame)

```cpp
void on_frame(int64 data) {
    capture_backbuffer(0);               // current frame -> texture slot 0
    custom_bind_texture(0, g_sampler, 0);
    custom_draw(g_blur_shader, g_vb, g_fullscreen_quad, 6, TOPO_TRIANGLE_LIST,
                g_blend, g_sampler, 0, 0, g_cb, g_fx_cb, 0);
    custom_restore_state();
}
```

## Cleanup

On script unload, every handle returned by a `create_*` / `load_*` call is destroyed automatically. Explicit destruction is optional and only needed to free a resource mid-script:

```cpp
int64 destroy_shader(int64 shader);
int64 destroy_compute_shader(int64 cs);
int64 destroy_vertex_buffer(int64 vb);
int64 destroy_index_buffer(int64 ib);
int64 destroy_constant_buffer(int64 cb);
int64 destroy_structured_buffer(int64 sb);
int64 destroy_blend_state(int64 bs);
int64 destroy_sampler(int64 s);
int64 destroy_texture(int64 tex);
int64 destroy_render_target(int64 rt);
int64 destroy_depth_buffer(int64 db);
int64 destroy_depth_stencil_state(int64 ds);
int64 destroy_rasterizer_state(int64 rs);
int64 destroy_mesh(int64 mesh);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/custom-draw-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
