# PCX API Version Matrix

This file maps each PCX API addition / change / removal to the version it landed in, so scripts that target older PCX runtimes know what's safe. Drawn from `docs/perception/changelogs.md`.

> **Read this before** committing to a script that must run on a specific PCX runtime version.

PCX ships **date-stamped rolling releases**, not semantic versions. The changelog
(`docs/perception/changelogs.md`) is keyed by release date and product line
(`Universal API` vs `Counter-Strike 2`). There is no `vX.Y` version number in any
shipped artifact, so this matrix uses the **changelog release date** as the version
anchor. When a `## How to Use` example writes `// Requires: PCX v<X.Y>+`, read the
placeholder as the corresponding **release date** (e.g. `// Requires: PCX 2026-03-16+`).

Two same-day Universal API posts are disambiguated as the changelog does — `(a)`
(earlier) and `(b)` (later). Where the changelog never dates an API but the cheatsheet
or per-API docs document it, the row reads `<= <earliest dated release that references it>`
or `unknown` — never a guessed date.

---

## How to Use This File

1. **Pin the target at the top of the script.** A one-line comment records the oldest
   runtime the script is allowed to load on:

   ```cpp
   // Requires: PCX 2026-03-17+   (custom-draw 3D: depth testing + compute shaders)
   ```

2. **Before using an API, check the matrix.** Find the API's row in
   `## API Matrix — By Category`. If its `Since` date is **after** your pin, either
   raise the pin or do not call it. If the `Deprecated/Removed In` column is set and
   your target is **at or after** that date, use the `Replacement` instead.

3. **Targeting multiple runtimes? Fall back gracefully.** PCX exposes no runtime
   version query (see next section), so multi-version support is done with
   preprocessor `#define` guards set from the SDK, gated by what you tested. Example:

   ```cpp
   // Build host passes the target via the SDK:
   //   define(engine, "PCX_2026_03_17", "1");   // only on >= 2026-03-17 builds
   #ifdef PCX_2026_03_17
       uint64 cs = create_compute_shader(cs_src);   // since 2026-03-17(a)
       dispatch_compute(cs, 64, 1, 1);
   #else
       // conservative path: CPU fallback, no compute shaders
   #endif
   ```

---

## Runtime Version Detection

**There is no documented API to ask the PCX runtime its version.** No
`get_version` / `api_version` / `client_version` / `build_version` native appears in
`docs/perception/*` or `knowledge/pcx-api-cheatsheet.md`. Do not invent one — a call to
a nonexistent native fails to compile (Enma) or aborts the script.

Use the **conservative approach**: drive feature availability from preprocessor
symbols the build host injects, set only after you have tested the target build.

```cpp
// ── SDK side (host C++), set per known-good target build ──
//   define(engine, "PCX_BUILD", "20260317");   // numeric YYYYMMDD of tested build
//   add_include_path(engine, "includes/");

// ── Script side ──
#ifndef PCX_BUILD
    #error "PCX_BUILD not defined — host must declare the tested runtime build"
#endif

#if PCX_BUILD >= 20260317
    // depth testing + compute shaders available (since 2026-03-17(a))
#elif PCX_BUILD >= 20260316
    // base custom-draw shader pipeline only (since 2026-03-16)
#else
    // pre-custom-draw: 2D primitives only
#endif
```

`#define`, `#ifdef`/`#ifndef`/`#if`/`#elif`/`#else`/`#endif`, and SDK-side
`define(engine, name, value)` are all documented in `docs/enma/lang-pre-processor.md`.
The numeric `YYYYMMDD` form lets you use `#if PCX_BUILD >= …` integer comparisons.
The runtime cannot self-report, so **the host is the source of truth** — never branch
on a value the script tries to read at runtime.

---

## API Matrix — By Category

Columns: `API` | `Since` | `Notes` | `Deprecated/Removed In` | `Replacement`.
Every `Since` cites the changelog release date or is marked `unknown` / `<= <date>`.

### Render — 2D Primitives & Fonts

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `draw_line` | `<= 2026-02-01` | Line, `thickness` arg. `docs/perception/render-api.md`. | — | — |
| `draw_rect` / `draw_rect_filled` | `<= 2026-02-01` | Rect with `rounding` + corner flags. | — | — |
| `draw_circle` | `<= 2026-02-01` | `filled` bool. | — | — |
| `draw_arc` | `<= 2026-02-01` | `radii`, `start`, `sweep`. | — | — |
| `draw_triangle` | `<= 2026-02-01` | `filled` bool. | — | — |
| `draw_text` | `<= 2026-02-01` | `effect` 0=none/1=shadow/2=outline. | — | — |
| `draw_bitmap` | `<= 2026-02-01` | Tinted bitmap blit. | — | — |
| `draw_four_corner_gradient` | unknown | In `docs/perception/render-api.md` but never named in the changelog. Treat as `<= 2026-02-01` core. | — | — |
| `draw_polygon` | unknown | In `docs/perception/render-api.md`; no changelog row. Treat as `<= 2026-02-01` core. | — | — |
| `get_font18/20/24/28`, `get_text_width`, `get_text_height` | `<= 2026-02-01` | Built-in font handles; predate the window. | — | — |
| `create_font` / `create_font_mem` — optional `glyph_ranges` arg | `2026-02-03(b)` | Optional `glyph_ranges` added to both (changelog `Feb 3 (b) → AngelScript & Lua`). Older builds: no `glyph_ranges` parameter. | — | — |
| Font loading latency | `2026-02-03(b)` | "Font loading now instant" + render backend optimized (changelog `Feb 3 (b) → Render Engine`). Behavior change, not a new symbol. | — | — |
| Script render order | `2026-02-12` | Changed: "newly created callbacks render first" (changelog `Feb 12 → Render System`). Order reversed vs earlier builds. | — | — |

### Render — Custom Draw (Direct D3D11 / GPU)

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `create_shader`, `create_vertex_buffer`, `create_constant_buffer`, `create_blend_state`, `create_sampler`, `create_texture`, `create_render_target` | `2026-03-16` | Base custom-draw pipeline — HLSL VS/PS compiled at runtime, all primitive topologies (changelog `Mar 16 → Custom Draw API — Direct GPU Access`). | — | — |
| Custom draw on CS2 product | `2026-03-16` (CS2) | Same Custom Draw API pushed to the CS2 line (changelog `Mar 16 — Counter-Strike 2`). | — | — |
| `create_index_buffer`, `custom_draw_indexed` | `2026-03-17(a)` | Indexed drawing, 16-bit and 32-bit index buffers (changelog `Mar 17 (a) → Indexed Drawing`). | — | — |
| `create_depth_buffer`, `create_depth_stencil_state`, `custom_set_depth_stencil_state`, `custom_clear_depth_buffer`, `custom_set_render_target_ext` | `2026-03-17(a)` | Depth testing + depth-enabled render targets (changelog `Mar 17 (a) → Depth Testing`, `Depth-Enabled Render Targets`). | — | — |
| `create_rasterizer_state`, `custom_set_rasterizer_state` | `2026-03-17(a)` | Cull / fill mode, wireframe (changelog `Mar 17 (a) → Rasterizer State`). | — | — |
| `custom_set_viewport` | `2026-03-17(a)` | Split-screen / picture-in-picture (changelog `Mar 17 (a) → Custom Viewports`). | — | — |
| `custom_bind_textures` (multi-texture) | `2026-03-17(a)` | Bind multiple textures to one shader (changelog `Mar 17 (a) → Multi-Texture Binding`). | — | — |
| `custom_bind_constant_buffers` (multi-CB) | `2026-03-17(a)` | Multiple constant buffers to different slots (changelog `Mar 17 (a) → Multi-Constant-Buffer Binding`). | — | — |
| `create_compute_shader`, `create_structured_buffer`, `dispatch_compute`, `read_structured_buffer` | `2026-03-17(a)` | GPU compute from script (changelog `Mar 17 (a) → Compute Shaders`). | — | — |
| `load_obj_mesh` | `2026-03-17(a)` | Loads `.obj`, returns vb+ib handles (changelog `Mar 17 (a) → OBJ Mesh Loading`). | — | — |
| `create_dynamic_texture`, `update_dynamic_texture`, `create_texture_from_file` | `2026-03-17(a)` | Runtime-updatable textures (changelog `Mar 17 (a) → Dynamic Textures`). | — | — |
| `capture_backbuffer`, `custom_resolve_render_target` | `2026-03-17(a)` | Backbuffer capture for post-processing (changelog `Mar 17 (a) → Backbuffer Capture`). | — | — |

### Render — Custom Draw Constants & Enums

| Symbol group | Since | Notes | Deprecated/Removed In | Replacement |
|--------------|-------|-------|-----------------------|-------------|
| `BLEND_SRC_ALPHA`, `BLEND_INV_SRC_ALPHA`, `BLEND_ONE`, `BLEND_OP_ADD`, … (blend constants) | `2026-03-16` | Args to `create_blend_state`; ship with the base pipeline (changelog `Mar 16`). | — | — |
| Layout string format `"SEMANTIC:slot:TYPE"` | `2026-03-16` | Vertex layout for `create_shader` (changelog `Mar 16 → Shaders`, "Layout defined with format string"). | — | — |
| `TOPO_POINT_LIST`, `TOPO_LINE_LIST`, `TOPO_LINE_STRIP`, `TOPO_TRIANGLE_LIST`, `TOPO_TRIANGLE_STRIP` | `2026-03-16` | All primitive topologies present at base pipeline (changelog `Mar 16 → All Primitive Topologies`). | — | — |
| `CMP_NEVER` … `CMP_ALWAYS` (depth compare funcs) | `2026-03-17(a)` | Args to `create_depth_stencil_state` (changelog `Mar 17 (a) → Depth Testing`). | — | — |
| `FILL_WIREFRAME`, `FILL_SOLID` | `2026-03-17(a)` | Args to `create_rasterizer_state` (changelog `Mar 17 (a) → Rasterizer State`). | — | — |
| `CULL_NONE`, `CULL_FRONT`, `CULL_BACK` | `2026-03-17(a)` | Args to `create_rasterizer_state` (changelog `Mar 17 (a) → Rasterizer State`). | — | — |

### Proc — Memory Read / Write & Typed Reads

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `ref_process` (by name / by PID), `alive`, `base_address`, `peb`, `pid`, `is_valid_address` | `<= 2026-02-01` | Process handle + validity. `docs/perception/proc-api.md`. | — | — |
| `ru8/16/32/64`, `r8/16/32/64`, `rf32/64` | `<= 2026-02-01` | Scalar read primitives. | — | — |
| `rs`, `rws`, `rvm` | `<= 2026-02-01` | ASCII / UTF-16 / bulk reads. | — | — |
| `wu8/16/32/64`, `w8/16/32/64`, `wf32/64`, `wvm` | `<= 2026-02-01` | Write primitives (gated: `write_memory`). | — | — |
| `read_vec2/3/4_fl32`, `read_vec2/3/4_fl64`, `read_quat_fl32/64`, `read_mat4_fl32/64` + write mirrors | unknown | Documented in `docs/perception/proc-api.md` but **not named in the changelog**. Do not date precisely; treat as `<= 2026-02-01` core typed reads. Distinct from the `mat4` method `readas_*` below. | — | — |
| `get_module_base/size/list`, `get_proc_address`, `get_import_rdata_address` | `<= 2026-02-01` | Core module surface. | — | — |
| `find_code_pattern`, `find_all_code_patterns` | `<= 2026-02-01` | Core scanning. Executable-section-only + single-hit fixes landed `2026-02-12 → RE Tools`. | — | — |
| `scan_float`, `scan_double`, `scan_string`, `scan_wstring`, `scan_pointer` | `2026-03-14` | Added (changelog `Mar 14 → VAD / Memory Scan API Fixes`: "Added missing functions"). | — | — |
| Scan return shape | `2026-03-14` | Changed: scan functions now return `array<uint64>@` directly, no `&out` params (changelog `Mar 14`). Pre-`2026-03-14` callers used the old `&out` form. | — | — |
| `get_vad_snapshot` | `<= 2026-02-01` | Existed earlier but returned all-zero fields until fixed `2026-03-14` (changelog `Mar 14`: "Fixed `get_vad_snapshot` returning all-zero fields"). | — | — |
| `virtual_query`, `vad_region_t` | `<= 2026-02-01` | Core VAD query. | — | — |
| `alloc_vm` / `free_vm` | unknown | Allocation API existed pre-window; `2026-03-20` reworked it ("no longer causes BSODs", changelog `Mar 20 → Allocation API`). Requires CFG disabled + Insecure API enabled to execute allocated memory. | — | — |

### Proc / Threading — Matrix Precision, Atomics, Thread Priority

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `mat4.readas_float` / `readas_double` / `writeas_float` / `writeas_double` | `2026-02-03(b)` | Matrix4x4 double-precision read/write variants (changelog `Feb 3 (b) → AngelScript & Lua`). | — | — |
| default `matrix4x4` read/write (no precision suffix) | `<= 2026-02-03(a)` | — | `2026-02-03(b)` (deprecated) | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` |
| `atomic_int32`, `atomic_int64` | `2026-02-03(b)` | Lock-free shared state (changelog `Feb 3 (b) → AngelScript → Atomic API`). AngelScript-only entry. | — | — |
| `set_thread_to_highest_priority` / `lowest` / `normal_priority` | `2026-02-03(b)` | Thread priority helpers (changelog `Feb 3 (b) → AngelScript`). AngelScript-only entry. | — | — |

### World-to-Screen

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `source2_world_to_screen` (no viewport) | `<= 2026-02-01` | Original Source 2 W2S. | `2026-02-03(b)` (deprecated) | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| `source2_world_to_screen` — optional `viewport` arg | `2026-02-03(a)` | Added optional `const vector2 &in viewport = vector2(0,0)` (changelog `Feb 3 (a) → AngelScript`). Superseded one release later. | `2026-02-03(b)` (deprecated) | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| `world_to_screen_rowmajor` | `2026-02-03(b)` | Replaces `source2_world_to_screen` for row-major matrices (changelog `Feb 3 (b) → AngelScript & Lua`, "migration required"). | — | — |
| `world_to_screen_transposed` | `2026-02-03(b)` | New, for transposed/column-major matrices (changelog `Feb 3 (b)`). | — | — |

### Input

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `is_key_down`, `is_key_pressed`, `is_key_released` | `<= 2026-02-01` | Legacy keyboard state functions. | `2026-02-12` (deprecated) | `key_down` / `key_fired` / `key_toggle` |
| `is_mouse_down` | `<= 2026-02-01` | Legacy mouse button check. | `2026-02-12` (deprecated) | `key_down` with `vk::lbutton` / `vk::rbutton` |
| `key_down`, `key_fired`, `key_toggle`, `key_raw_down` | `2026-02-12` | Current unified keyboard and mouse button state queries. | — | — |
| `get_mouse_delta` | `<= 2026-02-01` | Existed earlier; behavior fixed `2026-02-12` to return proper movement delta instead of screen-space delta (changelog `Feb 12 → Input System`). | — | — |
| Controller keybinds (XINPUT) | `2026-02-12` | XINPUT controller keybind support added (changelog `Feb 12 → Input System`). | — | — |
| `get_gui_position(float &out x, float &out y)`, `get_gui_size(float &out w, float &out h)` | `2026-02-12` | Added (changelog `Feb 12 → AngelScript`). | — | — |
| `get_gui_pos` (legacy) | `<= 2026-02-12` | Position bug fixed `2026-03-17(b)` (changelog `Mar 17 (b) → AngelScript`, "Fixed `get_gui_pos` position issue"). Prefer `get_gui_position`. | — | `get_gui_position` |

### GUI — Sections, Widgets, Lists, Callbacks

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `create_section` | `<= 2026-02-01` | Returns section handle. `docs/perception/gui-api.md`. | — | — |
| `section_checkbox`, `section_slider_float`, `section_slider_int` | `<= 2026-02-01` | Toggle + numeric inputs. | — | — |
| `section_button`, `section_text_input`, `section_keybind` | `<= 2026-02-01` | Action / text / key-capture widgets. | — | — |
| `section_color_picker`, `section_dropdown` | `<= 2026-02-01` | Color ref / indexed dropdown. | — | — |
| `section_label`, `section_separator` | `<= 2026-02-01` | Static layout elements. | — | — |
| `list:get`, `list:remove`, `list:highlight`, `list:remove_highlight`, `list:hide`, `list:show` | `2026-02-17` | List widget op set added (changelog `Feb 17 → GUI`). | — | — |
| List widget selected-index correctness | `2026-02-03(a)` | Fixed: selected index becoming incorrect on add/remove (changelog `Feb 3 (a) → GUI`). | — | — |
| `register_callback` — optional `bool render_on_top = false` | `2026-03-17(b)` | Added (changelog `Mar 17 (b) → AngelScript`). Older builds: no `render_on_top` argument. | — | — |
| Taskbar (top-middle), force-on-top toggles | `2026-03-30(b)` | GUI taskbar for GUI/Analyzer/Editor/Console (changelog `Mar 30 (b) → GUI`). UI feature, not a script symbol. | — | — |
| Force render key (RE Tools while UI hidden) | `2026-03-18` | Configurable keybind (changelog `Mar 18 → GUI`). UI feature. | — | — |

### Sound

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `load_sound`, `free_sound`, `play_sound`, `stop_sound`, `stop_all_sounds`, `set_sound_volume`, `set_sound_pan`, `play_sound(..., loop=true)` | `2026-03-14` | Entire Sound API is new in this release — waveOut mixer, 44100Hz stereo, ≤64 instances, WAV direct + MF decode (changelog `Mar 14 → Sound API (new)`). No sound API exists before `2026-03-14`. | — | — |

### Net

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `http_get`, `http_post`, `ws_connect`, `ws_send`, `ws_recv`, `udp_create`, `udp_send`, `udp_recv` | unknown | Documented in `knowledge/pcx-api-cheatsheet.md` / `docs/perception/net-api.md`; **no changelog row dates them**. Treat as `<= 2026-02-01` core; do not assert a precise version. | — | — |

### Win

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `enum_windows`, `window_t`, `send_key`, `send_mouse`, `get_clipboard`, `set_clipboard` | `<= 2026-02-01` | Core Win API. `docs/perception/win-api.md`. | — | — |
| `get_all_hwnds()` | `2026-02-01` | Added (changelog `Feb 1 → AngelScript & Lua`, "returns all window handles"). | — | — |

### Filesystem

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `read_file`, `write_file`, `file_exists`, `list_dir`, `create_dir`, `delete_file` | unknown | Documented in `knowledge/pcx-api-cheatsheet.md` / `docs/perception/filesystem-api.md`; **no changelog row dates them**. Treat as `<= 2026-02-01` core. (Note: the same names also appear as IDE-AI tools in the changelog — those are tooling, not the script FS API.) | — | — |

### CPU / Time

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `get_cpu_vendor`, `time_ms`, `time_us`, `get_datetime_*` | `<= 2026-02-01` | Core CPU/time surface. `docs/perception/cpu-api.md`. | — | — |

### Zydis (disassembler / assembler)

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `zydis_decode`, `zydis_encode`, `zydis_insn_t` | `<= 2026-02-01` | Core. `docs/perception/zydis-api.md`. | — | — |

### Unicorn (x86-64 emulation)

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `uc_create`, `uc_mem_map`, `uc_mem_write/read`, `uc_reg_write/read`, `uc_emu_start`, `uc_destroy` | `<= 2026-02-01` | Core emulation surface. `docs/perception/unicorn-api.md`. | — | — |
| `UC_HOOK_INSN_INVALID` | `2026-03-18` | Invalid instructions stop emulation with a logged message (changelog `Mar 18 → AngelScript API — Unicorn Emulator`). | — | — |
| `UC_HOOK_INTR` | `2026-03-18` | Software interrupts (INT3, syscalls) stop emulation cleanly (changelog `Mar 18`). | — | — |
| `uc_get_last_exception(handle)` | `2026-03-18` | Returns NTSTATUS (e.g. `0xC0000005`) (changelog `Mar 18`). | — | — |
| `uc_get_exception_address(handle)` | `2026-03-18` | Returns RIP at exception (changelog `Mar 18`). | — | — |
| Null-pointer access handling | `2026-03-18` | Changed: caught gracefully, emulation stops instead of crashing (changelog `Mar 18`). | — | — |

### Platform / Engine (non-API capabilities affecting scripts)

| Capability | Since | Notes | Deprecated/Removed In | Replacement |
|------------|-------|-------|-----------------------|-------------|
| 32-bit games support | `2026-03-08` | Added (changelog `Mar 8`). Scripts targeting x86 processes require `>= 2026-03-08`. | — | — |
| Fullscreen mode (universal) | `2026-03-20` | Engine + overlay support for all games (changelog `Mar 20 → Perception Engine`). | — | — |
| Extensions system (`.as` in `extensions/`) | `2026-03-14` | Lifecycle hooks, AI-pipeline hooks, widget/platform/editor APIs (changelog `Mar 14 → Extensions`). | — | — |
| `hash_map` global-init | `<= 2026-02-01` | Reference issue when initialized as global fixed `2026-02-01` (changelog `Feb 1 → AngelScript`). | — | — |
| Overlay protection modes (Disabled / Default / Perceptproof) | `2026-03-31(b)` | Three-level dropdown (changelog `Mar 31 (b) → Perceptproof Overlay Protection`). | — | — |
| Stream Proof / Anti-Screenshot toggle | `2026-03-30(a)` | Re-added enable/disable option (changelog `Mar 30 (a)`); note `2026-03-30(b)` hardened it so stream proof "cannot be disabled". | — | — |
| Config/data encrypted as `.pak` | `2026-03-18` | All config + state encrypted (changelog `Mar 18 → Security`). Clear `Documents/My Games` before this update. | — | — |

---

## Removed / Deprecated APIs

| API | Status | Since | Replacement | Source row |
|-----|--------|-------|-------------|------------|
| `source2_world_to_screen` | Deprecated | `2026-02-03(b)` | `world_to_screen_rowmajor` (row-major) / `world_to_screen_transposed` (transposed/column-major) | changelog `Feb 3 (b) → AngelScript & Lua → Deprecated`; also `Mar 16` cheatsheet note |
| default `matrix4x4` read/write (no precision suffix) | Deprecated | `2026-02-03(b)` | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` | changelog `Feb 3 (b) → Deprecated` |
| `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64` | Removed (never actually existed) | `2026-03-14` | `scan_float` / `scan_double` / `scan_string` / `scan_wstring` / `scan_pointer` | changelog `Mar 14 → VAD / Memory Scan API Fixes`, "Removed nonexistent functions from docs" |
| Legacy RE tools + old chatbot | Removed | `2026-03-08` | New RE tools GUI + IDE AI assistant (same release) | changelog `Mar 8` |
| IDE + Analyzer | Discontinued | `Enma Open Beta — Phase 2 (May 2026)` | Perception MCP (60-70+ tools) | changelog `Enma Open Beta — Phase 2` |

`scan_bytes` and friends were doc-only ghosts — they never shipped, so calling them
fails on **every** build. The `Since` of `2026-03-14` marks when they were struck from
the docs, not when they worked.

---

## Language Version Quirks

PCX has hosted three scripting front-ends. The timeline below is what the changelog
and `docs/` support; exact per-feature introduction dates inside a language reference
that ships unversioned are marked `unknown`.

### Front-end split history

| Era | Languages | Evidence |
|-----|-----------|----------|
| `<= 2026-03` | AngelScript + Lua | Changelog entries split between `AngelScript` (AS-only) and `AngelScript & Lua` (both) throughout Feb–Mar 2026. `2026-03-11`: "Perception API IntelliSense injects both AngelScript and Lua API references". |
| `Enma Open Beta — Phase 2 (May 2026)` | Enma (new, proprietary AOT/JIT) added | Changelog `Enma Open Beta — Phase 2`: "Perception's proprietary programming language, built from scratch … compiles to native machine code". |

**AS-only vs AS+Lua intrinsics** (from the changelog's section headers):

| Feature | Scope at introduction | Since |
|---------|-----------------------|-------|
| `get_all_hwnds()` | AngelScript & Lua | `2026-02-01` |
| `create_font` / `create_font_mem` `glyph_ranges` | AngelScript & Lua | `2026-02-03(b)` |
| `mat4.readas_*` / `writeas_*` precision variants | AngelScript & Lua | `2026-02-03(b)` |
| `world_to_screen_rowmajor` / `_transposed` | AngelScript & Lua | `2026-02-03(b)` |
| `atomic_int32` / `atomic_int64` | **AngelScript only** | `2026-02-03(b)` |
| `set_thread_to_*_priority` | **AngelScript only** | `2026-02-03(b)` |
| `hash_map` global-init fix | **AngelScript only** | `2026-02-01` |
| `get_gui_position` / `get_gui_size` | **AngelScript only** | `2026-02-12` |
| `register_callback` `render_on_top` | **AngelScript only** | `2026-03-17(b)` |
| Unicorn `UC_HOOK_*`, `uc_get_*_exception*` | **AngelScript only** | `2026-03-18` |

Treat AngelScript-only rows as **not present in Lua** at that date unless a later
`AngelScript & Lua` entry restates them.

### Enma

Enma is documented in `docs/enma/` as a single unversioned reference. The only dated
anchor is the changelog's `Enma Open Beta — Phase 2 (May 2026)`. Every Enma language
feature below is therefore `<= Enma Open Beta Phase 2 (May 2026)`; an exact
introduction version is `unknown`.

| Feature | Available | Notes / source |
|---------|-----------|----------------|
| Full-module AOT + JIT to native x64 | `<= Enma Open Beta Phase 2 (May 2026)` | changelog `Enma Open Beta — Phase 2`; `docs/enma/llms-language.md §0` |
| Annotations (`[[...]]`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-annotations.md` |
| FFI (`[[dll(...)]]`, requires `PERM_FFI`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-advanced.md → FFI` |
| Coroutines (`coroutine` / `yield` / `coroutine_t`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-advanced.md → Coroutines`; runtime-auto-registered per `addon-core.md` |
| `defer`, `match`, `goto`, exceptions | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/llms-language.md §5` |
| Atomic types (`aint8/16/32/64`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/llms-language.md §2`; `addon-atomic.md` |
| Preprocessor (`#define`, `#if`/`#ifdef`, `#include`, SDK `define()`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-pre-processor.md` |

No Enma changelog predates the May 2026 Open Beta Phase 2 post, so anything finer than
"present in Open Beta Phase 2" is a guess and is left `unknown` here.

### AngelScript

PCX's AngelScript dialect is the historical default (pre-Enma). Feature deltas that
are dated land in the AS-specific rows of the matrix above (atomics, thread priority,
`render_on_top`, Unicorn hooks, etc.). The base AngelScript language itself is the
upstream AngelScript spec; PCX does not changelog core-language grammar changes.

### Lua

PCX exposes a Lua binding alongside AngelScript through `2026-03`. Only the
`AngelScript & Lua` changelog rows apply to it (font `glyph_ranges`, matrix precision
variants, W2S replacement, `get_all_hwnds`). No Lua-only language feature is dated in
the changelog; assume the AS+Lua shared surface and nothing more.

---

## Release Timeline Index

Reverse-chronological. Each row lists the script-facing API surface a release
introduced or changed, so a `// Requires:` pin can be picked from the oldest
release carrying every API a script needs. Pure IDE/Analyzer/decompiler internals
(no script API) are omitted; see `docs/perception/changelogs.md` for the full text.

| Release | Script-facing API added / changed |
|---------|-----------------------------------|
| `Enma Open Beta — Phase 2 (May 2026)` | Enma language added (AOT/JIT); Perception MCP (60-70+ tools); IDE + Analyzer discontinued |
| `2026-03-31(b)` | Overlay protection modes: Disabled / Default / Perceptproof |
| `2026-03-30(b)` | GUI taskbar + force-on-top; stream proof hardened (no longer disableable) |
| `2026-03-30(a)` | Stream Proof / Anti-Screenshot enable-disable toggle re-added |
| `2026-03-20` | Fullscreen mode (universal); `alloc_vm`/`free_vm` rework (CFG-disable + Insecure API to execute) |
| `2026-03-18` | Unicorn `UC_HOOK_INSN_INVALID`, `UC_HOOK_INTR`, `uc_get_last_exception`, `uc_get_exception_address`, graceful null deref; config `.pak` encryption; GUI force render key |
| `2026-03-17(b)` | `register_callback` `render_on_top` arg; `get_gui_pos` position fix |
| `2026-03-17(a)` | Custom Draw 3D/compute: `create_index_buffer`, `custom_draw_indexed`, `create_depth_buffer`/`create_depth_stencil_state`, `custom_set_render_target_ext`, `create_rasterizer_state`, `custom_set_viewport`, `custom_bind_textures`, `custom_bind_constant_buffers`, `create_compute_shader`/`dispatch_compute`/`create_structured_buffer`/`read_structured_buffer`, `load_obj_mesh`, dynamic textures, `capture_backbuffer`, `custom_resolve_render_target` |
| `2026-03-16` | Custom Draw base pipeline: `create_shader`, `create_vertex_buffer`, `create_constant_buffer`, `create_blend_state`, `create_sampler`, `create_texture`, `create_render_target` (Universal + CS2) |
| `2026-03-14` | Sound API (entire surface); scan `scan_float/double/string/wstring/pointer` + `array<uint64>@` return; `get_vad_snapshot` fix; `scan_bytes`/`scan_all_*` struck from docs; Extensions system |
| `2026-03-11` | Combined AngelScript + Lua API IntelliSense; multi-root workspace |
| `2026-03-08` | 32-bit games support; legacy RE tools + old chatbot removed |
| `2026-02-17` | GUI list ops: `list:get/remove/highlight/remove_highlight/hide/show` |
| `2026-02-12` | XINPUT controller keybinds; `get_mouse_delta` fix; `get_gui_position`/`get_gui_size`; render order reversed |
| `2026-02-03(b)` | `world_to_screen_rowmajor`/`_transposed` (deprecate `source2_world_to_screen`); `mat4.readas_*`/`writeas_*` (deprecate default matrix r/w); `atomic_int32/64`; `set_thread_to_*_priority`; `create_font`/`create_font_mem` `glyph_ranges`; instant font load |
| `2026-02-03(a)` | `source2_world_to_screen` optional `viewport` arg; list selected-index fix |
| `2026-02-01` | `get_all_hwnds()`; `hash_map` global-init fix |
| `<= 2026-02-01` | Core surfaces (proc r/w + typed reads, render 2D, GUI sections, input, net, win, filesystem, CPU/time, Zydis, Unicorn base) predate the dated changelog window |

---

## Cross-References

- `docs/perception/changelogs.md` — the live primary source; every `Since` here traces to a dated row in it. Re-read it when a new release lands and update this matrix.
- `knowledge/pcx-api-cheatsheet.md` — the full current API surface this matrix versions.
- `docs/perception/render-api.md`, `proc-api.md`, `gui-api.md`, `input-api.md`, `sound-api.md`, `net-api.md`, `win-api.md`, `filesystem-api.md`, `unicorn-api.md`, `zydis-api.md`, `cpu-api.md`, `custom-draw-api.md`, `extensions-api.md` — per-API signatures.
- `docs/enma/llms-language.md`, `lang-pre-processor.md`, `lang-annotations.md`, `lang-advanced.md` — Enma language reference for the Language Version Quirks section.
- `skill://pcx-angelscript-discipline` — AngelScript usage discipline.
- `.claude/skills/game-cheat-guidelines/SKILL.md` — the 12 rules every script in this repo follows.
