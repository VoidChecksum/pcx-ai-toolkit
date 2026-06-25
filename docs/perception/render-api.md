> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/render-api.md).

# Render API

All render natives are auto-registered into every loaded script.

Handles (`int64`) are encrypted pointers. Pass them back into other render calls. Don't dereference or arithmetic them.

For custom HLSL shaders, compute shaders, GPU buffers, textures, render targets, depth buffers, and primitive topology, start with [Custom Draw](custom-draw-api.md). It is part of Render but large enough to treat as its own feature.

## `color` type

`color` is a source-level module. Opt in with `import "color";`:

```enma
import "vec";
import "color";

int64 main() {
    color red = color(255, 0, 0, 255);
    draw_rect_filled(vec2(10.0, 10.0), vec2(100.0, 50.0), red, 4.0, 15);
    return 0;
}
```

`color` is a `[[packed]]` 4-byte struct with `r` / `g` / `b` / `a` fields plus `with_alpha(uint8 _a)` to copy with a different alpha. Non-escaping locals are stack-allocated; the byte layout matches the native `pixelcolor4` so every `draw_*` call reads them directly.

Read fields directly: `c.r`, `c.g`, `c.b`, `c.a` (each returns `uint8`).

## 2D primitives

```cpp
int64 draw_rect(vec2 pos, vec2 size, color c, float64 thickness, float64 rounding, uint8 rounding_flags);
int64 draw_rect_filled(vec2 pos, vec2 size, color c, float64 rounding, uint8 rounding_flags);
int64 draw_line(vec2 a, vec2 b, color c, float64 thickness);
int64 draw_circle(vec2 center, float64 radius, color c, float64 thickness, bool filled);
int64 draw_arc(vec2 center, vec2 radii, float64 start_deg, float64 sweep_deg, color c, float64 thickness, bool filled);
int64 draw_triangle(vec2 a, vec2 b, vec2 c, color col, float64 thickness, bool filled);
int64 draw_four_corner_gradient(vec2 pos, vec2 size, color tl, color tr, color bl, color br, float64 rounding);
int64 draw_polygon(array xy_pairs, uint32 count_pairs, color c, float64 thickness, bool filled);
int64 draw_bitmap(int64 bmp, vec2 pos, vec2 size, color tint, bool rounded);
int64 draw_text(string text, vec2 pos, color c, int64 font, int32 effect, color effect_color, float64 effect_amount);
```

`effect`: 0=none, 1=shadow, 2=outline. `rounding_flags`: bitmask of which corners to round (ImGui-style, `15` = all corners).

## Text and fonts

```cpp
float64 get_text_width(int64 font, string text, int32 maxw, int32 maxh);
float64 get_text_height(int64 font, string text, int32 maxw, int32 maxh);
int32   get_char_advance(int64 font, uint32 wchar32);

int64 create_font(string path, float64 size, bool antialias, bool load_color, array glyph_ranges);
int64 create_font_mem(string label, float64 size, array buf, bool antialias, bool load_color, array glyph_ranges);
int64 create_bitmap(array data);

int64 get_font18();
int64 get_font20();
int64 get_font24();
int64 get_font28();
```

`create_font` first tries the path as-is, then retries under perception's main dir. `glyph_ranges` may be an empty array.

## Clipping

```cpp
int64 clip_push(vec2 pos, vec2 size);
int64 clip_pop();
```

## Viewport

```cpp
float64 get_view_width();
float64 get_view_height();
float64 get_view_scale();
float64 get_fps();
```

## Shaders

```cpp
int64 create_shader(string vs_source, string ps_source, string layout);
int64 destroy_shader(int64 shader);
int64 create_compute_shader(string cs_source);
int64 destroy_compute_shader(int64 cs);
```

Layout format: `"SEMANTIC:INDEX:TYPE, ..."`. Example: `"POSITION:0:FLOAT2, COLOR:0:FLOAT4"`. Types: `FLOAT1`, `FLOAT2`, `FLOAT3`, `FLOAT4`, `BYTE4` (unorm), `UINT1`.

## Buffers

```cpp
int64 create_vertex_buffer(uint32 stride, uint32 max_vertices, bool dynamic);
int64 destroy_vertex_buffer(int64 vb);
int64 create_index_buffer(uint32 max_indices, bool use_32bit, bool dynamic);
int64 destroy_index_buffer(int64 ib);
int64 create_constant_buffer(uint32 size);
int64 destroy_constant_buffer(int64 cb);
int64 create_structured_buffer(uint32 element_size, uint32 element_count, bool cpu_write, bool gpu_write);
int64 destroy_structured_buffer(int64 sb);
```

## Pipeline state

```cpp
int64 create_blend_state(int32 src, int32 dst, int32 op, int32 src_alpha, int32 dst_alpha, int32 op_alpha);
int64 destroy_blend_state(int64 bs);
int64 create_sampler(int32 filter, int32 address_u, int32 address_v);
int64 destroy_sampler(int64 s);
int64 create_depth_stencil_state(bool depth_enable, bool depth_write, int32 compare_func);
int64 destroy_depth_stencil_state(int64 ds);
int64 create_rasterizer_state(int32 cull_mode, int32 fill_mode, bool scissor_enable);
int64 destroy_rasterizer_state(int64 rs);
```

Enum values (all `int32`):

* `blend_factor`: 0=ZERO, 1=ONE, 2=SRC\_ALPHA, 3=INV\_SRC\_ALPHA, 4=DEST\_ALPHA, 5=INV\_DEST\_ALPHA, 6=SRC\_COLOR, 7=INV\_SRC\_COLOR, 8=DEST\_COLOR, 9=INV\_DEST\_COLOR.
* `blend_op`: 0=ADD, 1=SUBTRACT, 2=REV\_SUBTRACT, 3=MIN, 4=MAX.
* `filter`: 0=POINT, 1=LINEAR, 2=ANISOTROPIC.
* `address`: 0=WRAP, 1=CLAMP, 2=MIRROR, 3=BORDER.
* `compare_func`: 0=NEVER, 1=LESS, 2=EQUAL, 3=LESS\_EQUAL, 4=GREATER, 5=NOT\_EQUAL, 6=GREATER\_EQUAL, 7=ALWAYS.

## Render targets and textures

```cpp
int64 create_render_target(uint32 width, uint32 height);
int64 destroy_render_target(int64 rt);
int64 create_depth_buffer(uint32 width, uint32 height);
int64 destroy_depth_buffer(int64 db);
int64 create_texture(uint32 width, uint32 height, array rgba_data);
int64 destroy_texture(int64 tex);
int64 load_texture(string path);
int64 load_texture_mem(array data);
float64 get_texture_width(int64 tex);
float64 get_texture_height(int64 tex);
```

`create_texture` wants `width * height * 4` bytes of RGBA.

## Meshes

```cpp
int64 create_mesh_raw(array vertex_data, uint32 vertex_count, uint32 stride, array index_data, uint32 index_count, bool use_32bit);
int64 load_mesh(string path);
int64 load_mesh_mem(array data);
int64 destroy_mesh(int64 mesh);
int64 get_mesh_vert_count(int64 mesh);
int64 get_mesh_index_count(int64 mesh);
float64 get_mesh_stride(int64 mesh);
float64 get_mesh_bounds_min_x(int64 mesh);
float64 get_mesh_bounds_min_y(int64 mesh);
float64 get_mesh_bounds_min_z(int64 mesh);
float64 get_mesh_bounds_max_x(int64 mesh);
float64 get_mesh_bounds_max_y(int64 mesh);
float64 get_mesh_bounds_max_z(int64 mesh);
```

## Custom draw

```cpp
int64 custom_draw(int64 shader, int64 vb, array vertex_data, uint32 vertex_count, int32 topology,
                  int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                  int64 cb, array cb_data, int32 cb_slot);

int64 custom_draw_indexed(int64 shader, int64 vb, array vertex_data, uint32 vertex_count,
                          int64 ib, array index_data, uint32 index_count, int32 topology,
                          int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                          int64 cb, array cb_data, int32 cb_slot);

int64 draw_mesh(int64 mesh, int64 shader, int32 topology,
                int64 blend, int64 sampler, int64 texture, int32 tex_slot,
                int64 cb, array cb_data, int32 cb_slot);

int64 dispatch_compute(int64 cs, uint32 x, uint32 y, uint32 z);
```

`topology`: 0=TRIANGLE\_LIST, 1=TRIANGLE\_STRIP, 2=LINE\_LIST, 3=LINE\_STRIP, 4=POINT\_LIST.

Any of `blend` / `sampler` / `texture` / `cb` can be `0` to skip binding. `cb_data` may be an empty array.

## Binding and state

```cpp
int64 custom_set_render_target(int64 rt);
int64 custom_set_render_target_ext(int64 rt, int64 depth_buffer);
int64 custom_reset_render_target();
int64 custom_bind_rt_as_texture(int64 rt, int32 slot);
int64 custom_restore_state();
int64 custom_set_depth_stencil_state(int64 ds);
int64 custom_set_rasterizer_state(int64 rs);
int64 custom_set_viewport(float64 x, float64 y, float64 w, float64 h);
int64 custom_reset_viewport();
int64 custom_bind_texture(int64 texture, int64 sampler, int32 slot);
int64 custom_bind_constant_buffer(int64 cb, array data, int32 slot, int32 stage);
int64 custom_update_texture(int64 tex, uint32 x, uint32 y, uint32 w, uint32 h, array rgba_data);
int64 custom_clear_render_target(int64 rt, float64 r, float64 g, float64 b, float64 a);
int64 custom_clear_depth_buffer(int64 db);
int64 bind_structured_buffer(int64 sb, int32 slot, int32 stage);
int64 update_structured_buffer(int64 sb, array data);
int64 capture_backbuffer(int32 slot);
```

`stage`: 0=VS, 1=PS, 2=CS (matches D3D11 shader stages).

Call `custom_restore_state()` after any custom-pipeline sequence before returning control to the 2D layer.

## Minimal triangle

```cpp
int64 g_shader;
int64 g_vb;

int64 main() {
    string vs = "struct VSIn { float2 pos : POSITION; float4 color : COLOR; };\nstruct VSOut { float4 pos : SV_Position; float4 color : COLOR; };\nVSOut main(VSIn i) { VSOut o; o.pos = float4(i.pos, 0.0, 1.0); o.color = i.color; return o; }\n";
    string ps = "struct VSOut { float4 pos : SV_Position; float4 color : COLOR; };\nfloat4 main(VSOut i) : SV_Target { return i.color; }\n";

    g_shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    g_vb = create_vertex_buffer(24, 3, true);  // 2*4 + 4*4 = 24 bytes per vertex
    register_routine(cast<int64>(my_draw), 0);
    return 1;
}

void my_draw(int64 data) {
    float32[] verts;
    // vertex 0: pos(-0.5, -0.5) color(1, 0, 0, 1)
    verts.push(-0.5f); verts.push(-0.5f);
    verts.push(1.0f);  verts.push(0.0f); verts.push(0.0f); verts.push(1.0f);
    // vertex 1: pos(0.5, -0.5) color(0, 1, 0, 1)
    verts.push(0.5f);  verts.push(-0.5f);
    verts.push(0.0f);  verts.push(1.0f); verts.push(0.0f); verts.push(1.0f);
    // vertex 2: pos(0, 0.5) color(0, 0, 1, 1)
    verts.push(0.0f);  verts.push(0.5f);
    verts.push(0.0f);  verts.push(0.0f); verts.push(1.0f); verts.push(1.0f);

    float32[] no_cb;
    custom_draw(g_shader, g_vb, verts, 3, 0, 0, 0, 0, 0, 0, no_cb, 0);
}
```

## Cleanup

On script unload, every handle returned by `create_*` / `load_*` is destroyed automatically. Explicit `destroy_*` is optional and only needed if you want to free a resource mid-script.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/render-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
