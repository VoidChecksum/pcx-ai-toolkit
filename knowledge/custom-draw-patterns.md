# Custom Draw API Patterns for Perception.cx

Direct D3D11 GPU access from AngelScript/Enma. Write HLSL shaders, create
vertex/index/constant buffers, textures, render targets, and depth buffers,
then draw with any primitive topology. Custom draw commands respect draw
order with every existing render function.

> Resource creators return a `uint64` handle (`0` on failure). All resources
> are tracked per-script and auto-cleaned on script unload, so you create them
> once and reuse the handles every frame.

## Pattern: Basic 2D Colored Shape with Shader

Use case: a custom-shaded overlay primitive (gradient triangle, FOV wedge,
crosshair quad) that the built-in `draw_*` helpers can't express. Demonstrates
the minimal shader + vertex buffer + draw-call loop.

```cpp
// --- HLSL: vertex shader transforms 2D screen-space pos by an ortho matrix ---
string vs = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj); // 2D -> clip space
    o.col = i.col;
    return o;
}
""";

// --- HLSL: pixel shader just passes the interpolated vertex color ---
string ps = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

// Created ONCE (e.g. in on_load), reused every frame
uint64 g_shader = 0;
uint64 g_vb     = 0;
uint64 g_blend  = 0;

void cd_init_shape() {
    // layout: POSITION = float2, COLOR = float4 -> 24-byte stride
    g_shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    g_vb     = create_vertex_buffer(24, 3, true); // stride, max verts, dynamic
    g_blend  = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
}

void cd_draw_shape(float4x4 ortho) {
    // Interleaved vertex data: 3 verts x (pos.xy, col.rgba)
    array<float> verts = {
        100.0, 100.0,  1.0, 0.0, 0.0, 1.0,   // red
        300.0, 100.0,  0.0, 1.0, 0.0, 1.0,   // green
        200.0, 300.0,  0.0, 0.0, 1.0, 1.0    // blue
    };
    // proj matrix goes into constant buffer slot b0
    array<float> cb_data = ortho.to_array();

    custom_draw(g_shader, g_vb, verts, 3, TOPO_TRIANGLE_LIST,
                g_blend, 0, 0,        // no sampler/texture for solid color
                0,                    // rt=0 -> draw to backbuffer
                0, cb_data, 0);       // cb auto-managed, data, slot b0
}
```

## Pattern: Textured Quad with Custom Texture

Use case: render a logo, sprite sheet, watermark, or a CPU-generated image
onto a screen-space quad. Loads a texture, binds a sampler, and samples it in
the pixel shader.

```cpp
string vs_tex = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float2 uv : TEXCOORD; };
struct VS_OUT { float4 pos : SV_Position; float2 uv : TEXCOORD; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj);
    o.uv  = i.uv;
    return o;
}
""";

string ps_tex = """
Texture2D    tex : register(t0);
SamplerState smp : register(s0);
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target { return tex.Sample(smp, i.uv); }
""";

uint64 g_tex_shader = 0;
uint64 g_tex_vb     = 0;
uint64 g_tex        = 0;
uint64 g_sampler    = 0;
uint64 g_tex_blend  = 0;

void cd_init_textured() {
    g_tex_shader = create_shader(vs_tex, ps_tex, "POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2");
    g_tex_vb     = create_vertex_buffer(16, 6, true);  // float2 pos + float2 uv = 16 bytes
    g_tex        = create_texture_from_file("logo.png"); // RGBA from disk
    g_sampler    = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
    g_tex_blend  = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                      BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
}

void cd_draw_textured(float4x4 ortho, float64 x, float64 y, float64 w, float64 h) {
    float fx = float(x); float fy = float(y);
    float fw = float(w); float fh = float(h);
    // Two triangles forming a quad: (pos.xy, uv.xy)
    array<float> verts = {
        fx,      fy,      0.0, 0.0,
        fx + fw, fy,      1.0, 0.0,
        fx,      fy + fh, 0.0, 1.0,
        fx + fw, fy,      1.0, 0.0,
        fx + fw, fy + fh, 1.0, 1.0,
        fx,      fy + fh, 0.0, 1.0
    };
    array<float> cb_data = ortho.to_array();

    custom_draw(g_tex_shader, g_tex_vb, verts, 6, TOPO_TRIANGLE_LIST,
                g_tex_blend, g_sampler, g_tex, // bind sampler + texture
                0, 0, cb_data, 0);
}
```

## Pattern: 3D Cube with Depth Testing

Use case: render a true 3D object (debug box, chams cage, world marker) that
correctly occludes itself. Uses an index buffer to share cube corners, a
depth buffer, and a depth-stencil state with `CMP_LESS`.

```cpp
string vs_3d = """
cbuffer cb : register(b0) { float4x4 mvp; };
struct VS_IN  { float3 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 1), mvp); // model-view-projection
    o.col = i.col;
    return o;
}
""";

string ps_3d = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

uint64 g_cube_shader = 0;
uint64 g_cube_vb     = 0;
uint64 g_cube_ib     = 0;
uint64 g_depth_buf   = 0;
uint64 g_ds_state    = 0;
uint64 g_cube_blend  = 0;

void cd_init_cube(int32 vw, int32 vh) {
    g_cube_shader = create_shader(vs_3d, ps_3d, "POSITION:0:FLOAT3, COLOR:0:FLOAT4");
    g_cube_vb     = create_vertex_buffer(28, 8, false);   // float3 pos + float4 col = 28 bytes, 8 corners
    g_cube_ib     = create_index_buffer(36, false, false); // 12 tris * 3 = 36 indices, 16-bit
    g_depth_buf   = create_depth_buffer(vw, vh);
    g_ds_state    = create_depth_stencil_state(true, true, CMP_LESS); // depth on, write on
    g_cube_blend  = create_blend_state(BLEND_ONE, BLEND_ZERO, BLEND_OP_ADD,
                                       BLEND_ONE, BLEND_ZERO, BLEND_OP_ADD); // opaque
}

void cd_draw_cube(float4x4 mvp, int32 vw, int32 vh) {
    // 8 cube corners: (pos.xyz, col.rgba)
    array<float> verts = {
        -1,-1,-1, 1,0,0,1,   1,-1,-1, 0,1,0,1,
         1, 1,-1, 0,0,1,1,  -1, 1,-1, 1,1,0,1,
        -1,-1, 1, 1,0,1,1,   1,-1, 1, 0,1,1,1,
         1, 1, 1, 1,1,1,1,  -1, 1, 1, 0,0,0,1
    };
    // 12 triangles (two per face), CCW winding
    array<uint16> indices = {
        0,1,2, 0,2,3,   4,6,5, 4,7,6,   // back, front
        4,5,1, 4,1,0,   3,2,6, 3,6,7,   // bottom, top
        1,5,6, 1,6,2,   4,0,3, 4,3,7    // right, left
    };
    array<float> cb_data = mvp.to_array();

    // Bind a depth-enabled render target + clear it, then set depth state
    custom_set_render_target_ext(0, g_depth_buf); // 0 = backbuffer color
    custom_clear_depth_buffer(g_depth_buf);
    custom_set_depth_stencil_state(g_ds_state);
    custom_set_viewport(0, 0, vw, vh);

    custom_draw_indexed(g_cube_shader, g_cube_vb, verts, 28,
                        g_cube_ib, indices, 36, TOPO_TRIANGLE_LIST,
                        g_cube_blend, 0, 0, 0, 0, cb_data, 0);
}
```

## Pattern: Wireframe Rendering

Use case: debug visualization of geometry, hitbox cages, or a "skeleton"
look. Identical geometry path as the solid cube but with a rasterizer state
set to `FILL_WIREFRAME` so only triangle edges are drawn.

```cpp
// Reuses g_cube_shader / g_cube_vb / g_cube_ib / g_depth_buf from the 3D cube pattern.
uint64 g_rs_wire  = 0;
uint64 g_rs_solid = 0;

void cd_init_wireframe() {
    // Wireframe + no culling so back edges are visible too
    g_rs_wire  = create_rasterizer_state(FILL_WIREFRAME, CULL_NONE);
    g_rs_solid = create_rasterizer_state(FILL_SOLID, CULL_BACK); // to restore afterwards
}

void cd_draw_wireframe(float4x4 mvp, int32 vw, int32 vh) {
    array<float> verts = {
        -1,-1,-1, 0,1,0,1,   1,-1,-1, 0,1,0,1,
         1, 1,-1, 0,1,0,1,  -1, 1,-1, 0,1,0,1,
        -1,-1, 1, 0,1,0,1,   1,-1, 1, 0,1,0,1,
         1, 1, 1, 0,1,0,1,  -1, 1, 1, 0,1,0,1
    };
    array<uint16> indices = {
        0,1,2, 0,2,3,   4,6,5, 4,7,6,
        4,5,1, 4,1,0,   3,2,6, 3,6,7,
        1,5,6, 1,6,2,   4,0,3, 4,3,7
    };
    array<float> cb_data = mvp.to_array();

    custom_set_render_target_ext(0, g_depth_buf);
    custom_clear_depth_buffer(g_depth_buf);
    custom_set_depth_stencil_state(g_ds_state);
    custom_set_rasterizer_state(g_rs_wire);  // <-- switch to wireframe fill
    custom_set_viewport(0, 0, vw, vh);

    custom_draw_indexed(g_cube_shader, g_cube_vb, verts, 28,
                        g_cube_ib, indices, 36, TOPO_TRIANGLE_LIST,
                        g_cube_blend, 0, 0, 0, 0, cb_data, 0);

    custom_set_rasterizer_state(g_rs_solid); // restore so later draws are solid
}
```

## Pattern: Glow / Blur Post-Processing

Use case: a soft glow around overlay elements or a bloom effect. Render the
source into an off-screen render target, run a separable blur pass that
samples the RT, then composite the blurred result back over the backbuffer
with additive blending.

```cpp
// Fullscreen-triangle vertex shader (no vertex buffer needed; uses SV_VertexID)
string vs_fs = """
struct VS_OUT { float4 pos : SV_Position; float2 uv : TEXCOORD; };
VS_OUT main(uint id : SV_VertexID) {
    VS_OUT o;
    o.uv  = float2((id << 1) & 2, id & 2);            // 0,0 / 2,0 / 0,2
    o.pos = float4(o.uv * float2(2, -2) + float2(-1, 1), 0, 1);
    return o;
}
""";

// Separable Gaussian blur; direction passed via constant buffer (1,0)=horiz, (0,1)=vert
string ps_blur = """
Texture2D    src : register(t0);
SamplerState smp : register(s0);
cbuffer cb : register(b0) { float2 dir; float2 texel; };
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target {
    float w[5] = { 0.227, 0.194, 0.121, 0.054, 0.016 };
    float4 c = src.Sample(smp, i.uv) * w[0];
    for (int k = 1; k < 5; k++) {
        float2 off = dir * texel * k;
        c += src.Sample(smp, i.uv + off) * w[k];
        c += src.Sample(smp, i.uv - off) * w[k];
    }
    return c;
}
""";

// Additive composite of blurred RT over the backbuffer
string ps_composite = """
Texture2D    src : register(t0);
SamplerState smp : register(s0);
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target { return src.Sample(smp, i.uv); }
""";

uint64 g_blur_shader = 0;
uint64 g_comp_shader = 0;
uint64 g_rt_a = 0;
uint64 g_rt_b = 0;
uint64 g_blur_smp   = 0;
uint64 g_add_blend  = 0;
int32  g_rt_w = 0;
int32  g_rt_h = 0;

void cd_init_glow(int32 w, int32 h) {
    g_rt_w = w; g_rt_h = h;
    g_blur_shader = create_shader(vs_fs, ps_blur, "");       // no input layout
    g_comp_shader = create_shader(vs_fs, ps_composite, "");
    g_rt_a = create_render_target(w, h);  // ping
    g_rt_b = create_render_target(w, h);  // pong
    g_blur_smp  = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
    g_add_blend = create_blend_state(BLEND_ONE, BLEND_ONE, BLEND_OP_ADD, // additive
                                     BLEND_ONE, BLEND_ONE, BLEND_OP_ADD);
}

// `source_tex` is what you want to glow (e.g. a captured/rendered RT texture)
void cd_draw_glow(uint64 source_tex) {
    float tx = 1.0 / float(g_rt_w);
    float ty = 1.0 / float(g_rt_h);

    // Pass 1: horizontal blur, source_tex -> rt_a
    array<float> cb_h = { 1.0, 0.0, tx, ty };
    custom_clear_render_target(g_rt_a, 0, 0, 0, 0);
    custom_draw(g_blur_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                0, g_blur_smp, source_tex, g_rt_a, 0, cb_h, 0);

    // Pass 2: vertical blur, rt_a -> rt_b
    array<float> cb_v = { 0.0, 1.0, tx, ty };
    custom_clear_render_target(g_rt_b, 0, 0, 0, 0);
    custom_draw(g_blur_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                0, g_blur_smp, g_rt_a, g_rt_b, 0, cb_v, 0);

    // Pass 3: composite blurred rt_b additively onto the backbuffer (rt=0)
    custom_draw(g_comp_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                g_add_blend, g_blur_smp, g_rt_b, 0, 0, array<float>(), 0);
}
```

## Pattern: Compute Shader Data Processing

Use case: offload heavy per-element math to the GPU — batch world-to-screen
projection, particle simulation, or bulk distance/visibility checks. Creates
a compute shader, a structured buffer of input/output data, dispatches thread
groups, then reads the results back to the CPU.

```cpp
// Compute shader: multiplies every element by 2 (stand-in for real batch work)
string cs = """
RWStructuredBuffer<float> data : register(u0);
[numthreads(64, 1, 1)]
void main(uint3 id : SV_DispatchThreadID) {
    data[id.x] = data[id.x] * 2.0;
}
""";

uint64 g_compute = 0;

void cd_init_compute() {
    g_compute = create_compute_shader(cs);
}

array<float> cd_run_compute(array<float> input) {
    uint element_count = input.length();

    // 4-byte float elements; upload initial data
    uint64 buf = create_structured_buffer(4, element_count, input);

    // Each group handles 64 elements (matches numthreads); round up
    uint groups = (element_count + 63) / 64;
    dispatch_compute(g_compute, groups, 1, 1);

    // Read processed data back into an AngelScript array
    array<float> result = read_structured_buffer(buf);
    return result; // each element doubled
}
```

## Pattern: Multi-Pass Rendering with Multiple Render Targets

Use case: composing a final image from several layers — e.g. render solid
geometry to one RT, an outline/mask to another, then combine both in a final
fullscreen pass. Demonstrates rendering into separate targets and sampling
multiple textures in the composite shader.

```cpp
// Final composite samples two render-target textures and blends them
string ps_mrt_composite = """
Texture2D    sceneTex : register(t0);
Texture2D    maskTex  : register(t1);
SamplerState smp      : register(s0);
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target {
    float4 scene = sceneTex.Sample(smp, i.uv);
    float  mask  = maskTex.Sample(smp, i.uv).r;
    // Tint the masked region (outline) cyan, leave the rest as the scene
    float3 outline = float3(0, 1, 1) * mask;
    return float4(scene.rgb + outline, 1);
}
""";

uint64 g_mrt_comp_shader = 0;
uint64 g_rt_scene = 0;
uint64 g_rt_mask  = 0;
uint64 g_mrt_smp  = 0;

void cd_init_mrt(int32 w, int32 h) {
    g_mrt_comp_shader = create_shader(vs_fs, ps_mrt_composite, ""); // reuse fullscreen VS
    g_rt_scene = create_render_target(w, h);
    g_rt_mask  = create_render_target(w, h);
    g_mrt_smp  = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
}

void cd_draw_mrt(float4x4 mvp, array<float> scene_verts, array<float> mask_verts) {
    array<float> cb = mvp.to_array();

    // Pass 1: render the scene geometry into g_rt_scene
    custom_clear_render_target(g_rt_scene, 0, 0, 0, 1);
    custom_draw(g_cube_shader, g_cube_vb, scene_verts, 3, TOPO_TRIANGLE_LIST,
                g_cube_blend, 0, 0, g_rt_scene, 0, cb, 0);

    // Pass 2: render the mask/outline geometry into g_rt_mask
    custom_clear_render_target(g_rt_mask, 0, 0, 0, 1);
    custom_draw(g_cube_shader, g_cube_vb, mask_verts, 3, TOPO_TRIANGLE_LIST,
                g_cube_blend, 0, 0, g_rt_mask, 0, cb, 0);

    // Pass 3: composite both RTs onto the backbuffer.
    // custom_bind_textures binds extra texture slots (t0, t1, ...) for one shader.
    custom_bind_textures(g_mrt_comp_shader, g_rt_scene, g_rt_mask);
    custom_draw(g_mrt_comp_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                0, g_mrt_smp, g_rt_scene, 0, 0, array<float>(), 0);
}
```

## Pattern: Dynamic Texture Update

Use case: a CPU-generated image that changes every frame — a software-drawn
minimap, a spectrogram, a heatmap, or scrolling text. Create a dynamic
texture once, rewrite its RGBA pixel buffer each frame, then draw it with the
textured-quad path.

```cpp
// Reuses g_tex_shader / g_tex_vb / g_sampler / g_tex_blend from the textured-quad pattern.
uint64 g_dyn_tex = 0;
int32  g_dyn_w = 256;
int32  g_dyn_h = 256;

void cd_init_dynamic() {
    g_dyn_tex = create_dynamic_texture(g_dyn_w, g_dyn_h); // allocated once
}

// Builds a fresh RGBA8 buffer and uploads it. `t` animates the pattern.
void cd_update_dynamic(float64 t) {
    array<uint8> pixels(g_dyn_w * g_dyn_h * 4); // 4 bytes per pixel (RGBA)

    for (int32 y = 0; y < g_dyn_h; y++) {
        for (int32 x = 0; x < g_dyn_w; x++) {
            int32 idx = (y * g_dyn_w + x) * 4;
            // Simple animated plasma so the update is visible per-frame
            uint8 r = uint8((sin(x * 0.05 + t) * 0.5 + 0.5) * 255.0);
            uint8 g = uint8((sin(y * 0.05 + t) * 0.5 + 0.5) * 255.0);
            uint8 b = uint8((sin((x + y) * 0.05 + t) * 0.5 + 0.5) * 255.0);
            pixels[idx + 0] = r;
            pixels[idx + 1] = g;
            pixels[idx + 2] = b;
            pixels[idx + 3] = 255; // opaque
        }
    }

    update_dynamic_texture(g_dyn_tex, pixels); // re-upload to GPU
}

void cd_draw_dynamic(float4x4 ortho, float64 x, float64 y) {
    float fx = float(x); float fy = float(y);
    float fw = float(g_dyn_w); float fh = float(g_dyn_h);
    array<float> verts = {
        fx,      fy,      0.0, 0.0,
        fx + fw, fy,      1.0, 0.0,
        fx,      fy + fh, 0.0, 1.0,
        fx + fw, fy,      1.0, 0.0,
        fx + fw, fy + fh, 1.0, 1.0,
        fx,      fy + fh, 0.0, 1.0
    };
    array<float> cb_data = ortho.to_array();

    custom_draw(g_tex_shader, g_tex_vb, verts, 6, TOPO_TRIANGLE_LIST,
                g_tex_blend, g_sampler, g_dyn_tex, // bind the dynamic texture
                0, 0, cb_data, 0);
}
```
