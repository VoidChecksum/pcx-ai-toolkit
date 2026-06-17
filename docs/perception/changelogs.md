# Perception.cx Changelogs (2026)

Complete changelog archive from the Perception.cx forums, covering Universal API and CS2 API updates.

---

## April 6, 2026 — Universal API

### Analyzer
- Significantly reduced overall memory usage
- Fixed access violation exceptions caused by the reconstruction system
- Fixed freezes and deadlocks in the reconstruction pipeline during function decompilation and optimizer state handling
- Significantly improved the decompiler, with better calibration for obfuscated routines and added switch statement resolution

---

## April 1, 2026 — Universal API

### IDE + Tooling Updates
- Fixed the tool call system and state cleanup when resending, starting a new chat, or clearing chat
- Added scroll-to-top and scroll-to-bottom actions in the assistant dropdown
- Ctrl+C no longer cancels streaming — only copies text as expected
- **run_in_terminal** — fixed multiline output capture; description now warns against blocking commands
- **wait_for_user** — pauses the AI until the user clicks Continue
- **ask_mcq** — added inline multiple choice UI with checkbox/radio selection
- **update_notes** — added append mode for incremental note-taking

### IDE
- Added support for **.tsx**, **.jsx**, **.vue**, **.go**, and **.cs**
- Expanded IntelliSense keywords and snippets across 11 languages

### Analyzer — Stronger Decompiler
- Fixed 32-bit register width handling where x64 zero-extension was being lost
- Noreturn detection now works for indirect jump-through-IAT patterns (e.g. NtTerminateProcess)
- Added semantic variable naming for API results (status, buffer, isSpace, etc.)
- Merged declaration + initialization output where possible
- Simple bodies now emit single-line `if` statements when appropriate
- Hex literals enabled by default (toggle in settings)
- Removed fake saved-register arguments from function signatures
- Struct field generation more conservative — prevents phantom `field_0xNN` members
- Added opaque predicate stripping, empty-if removal, argument alias elimination

### Assembly Output
- Added checkbox to make `.asm` generation optional

### Reconstruction System
- Reworked the reconstruction system (still maturing — may freeze in decompiler-heavy cases)

---

## March 31, 2026 (b) — Universal API

### Perceptproof Overlay Protection
New dropdown under overlay protection settings with three protection levels:

| Mode | Description |
|------|-------------|
| **Disabled** | Zero protection — overlay visible to recording software (Discord, OBS, etc.) |
| **Default** | Standard protection for Discord, clips, most games (CS2, COD, etc.) |
| **Perceptproof** | Maximum protection for aggressive screenshot-based anti-cheat systems |

Perceptproof handles visuals in a way that keeps them fully hidden from aggressive screenshot systems. Uses more GPU resources while active.

For normal games, Default mode is sufficient. Perceptproof is proactive protection against AI/kernel screenshot-based detection trends in modern anti-cheats.

---

## March 31, 2026 (a) — Universal API

### Analyzer
- Reconstruction fixes and proper progress display
- Fixed several out-of-memory issues, memory leaks, and excessive memory usage
- Decompiler structural improvements

### IDE Chatbot
- Fixed hallucination issues caused by context trimming during context saving
- Improved context handling to save more tokens; updated the notes system

---

## March 30, 2026 (b) — Universal API

### Major Update

- **Fully redesigned IDE**
- **Copilot + GitHub Models integration** — connect your GitHub Copilot account and use your Copilot tokens
- **Expanded RE Utilities into full Analysis Tool** — faster module analysis + experimental binary-to-source extraction and decompiler
  - Full analysis of 100MB+ binaries in ~12 seconds (multithreaded, 1M+ targets)
  - Compared to IDA Pro which can take over an hour for the same task

### GUI
- New taskbar (top-middle) — minimize, maximize, or force Perception GUI / Analyzer / Editor / Console Logger to stay on top

### IDE Changes (UI + Copilot)
- Entire IDE UI reworked
- Summarise and Continue refined for smoother experience
- Added GitHub Models and Copilot Auth
- IDE chatbot not limited to Perception scripting — assists with website creation, general development, VS/VS Code projects

### Overlay
- Screenshot proofing hardened (stream proof cannot be disabled due to this addition)

---

## March 30, 2026 (a) — Universal API

- Re-added option to enable/disable Stream Proof / Anti Screenshot
- Improved overall stability of the Stream Proof / Anti Screenshot system

---

## March 20, 2026 — Universal API

### Perception Engine
- **Fullscreen mode** — universal support for all games, enabled by engine and overlay improvements

### Overlay
- Backend redone — PCX client now "refreshes" Windows Explorer (expected behavior)
- Message queue optimizations
- Fixed memory-related BSODs under low RAM conditions
- Overlay no longer crashes on Alt+F4

### Allocation API
- Updated virtual memory allocation — no longer causes BSODs or instability
- **NOTE:** Must disable Control Flow Guard (CFG) to execute allocated memory + enable Insecure API in menu

### IDE
- **Enter key indent fix** — only `{` triggers indentation (not `if()`/`for()`/`while()`)
- **Symbol occurrence highlighting** — double-click a variable/function name to highlight all matching occurrences (VS Code-style)
- **Scrollbar marks** — find matches and highlighted occurrences shown in scrollbar

---

## March 18, 2026 — Universal API

### Security
- All configuration files and data now encrypted as `.pak` files for file-system heuristic protection
- **Clear Documents/My Games folder entirely before loading this update**

### AngelScript API — Unicorn Emulator
- Null pointer access now caught gracefully — emulation stops instead of crashing
- Added `UC_HOOK_INSN_INVALID` — invalid instructions stop emulation with a logged message
- Added `UC_HOOK_INTR` — software interrupts (INT3, syscalls) stop emulation cleanly
- Added `uc_get_last_exception(handle)` — returns NTSTATUS exception code (e.g. `0xC0000005` for access violation)
- Added `uc_get_exception_address(handle)` — returns RIP where the exception occurred

### GUI
- Config files encrypted into `.pak` files
- UI state encrypted
- Added **force render key** — RE Tools rendered while UI hidden using configured keybind

### IDE
- Timeline backups, chat history, editor state all saved as encrypted `.pak` files
- Backups now saved in platform data directory instead of project root

### RE Tools
- Saved state and structures encrypted (`re_state.pak`, `re_structs.pak`)
- Added **Ctrl+C** in scanner — copies all scan results to clipboard as tab-separated text

---

## March 17, 2026 (b) — Universal API

### AngelScript API
- Fixed `get_gui_pos` position issue
- Added optional `bool render_on_top = false` argument to `register_callback` — renders callback content on top of everything else

### IDE — Tandem AI
- **Tandem AI** — two models cooperate via `switch_model` tool. Planning/Reasoning model handles analysis; Implementation/Coder model handles code and validation. Optional separate endpoint + API key for coder model. Leave coder field empty for single-model mode
- Automatic context trimming — tool results and write arguments compressed to compact summaries after each turn
- Added `manage_context` tool — AI can drop unneeded tool categories or trim old history
- Improved Summarize & Continue — larger limits, structured summaries preserving goal/changes/pending work
- Send validation — error message if URL or model is missing
- Fixed auto-scroll on single click near editor edges
- Fixed crash on editor close when background AI threads were mid-request

---

## March 17, 2026 (a) — Universal API

### 🔺 Custom Draw API — Major 3D, Compute & Rendering Expansion

Indexed rendering, depth testing, rasterizer state, viewports, multi-texture binding, compute shaders, structured buffers, mesh loading, dynamic textures, backbuffer capture.

**New in this update:**
- **Indexed Drawing** — shared vertices reused via 16-bit and 32-bit index buffers
- **Depth Testing** — depth buffer creation, clearing, binding, configurable depth-stencil state
- **Rasterizer State** — culling and fill mode control (wireframe, solid, no-cull)
- **Custom Viewports** — split-screen or picture-in-picture rendering
- **Multi-Texture Binding** — bind multiple textures to a shader simultaneously
- **Compute Shaders** — GPU compute from AngelScript with structured buffers
- **OBJ Mesh Loading** — load `.obj` files, returns vertex + index buffer handles
- **Dynamic Textures** — create and update textures at runtime
- **Multi-Constant-Buffer Binding** — bind multiple constant buffers to different slots
- **Depth-Enabled Render Targets** — render targets with attached depth buffers
- **Backbuffer Capture** — capture current frame as a texture for post-processing

---

## March 16, 2026 — Universal API

### 🔺 Custom Draw API — Direct GPU Access from AngelScript

Full custom shader pipeline. Direct D3D11 GPU access — HLSL shaders, vertex buffers, textures, render targets, any primitive topology.

Custom draw commands respect draw order with all existing render functions.

**New Features:**
- **Shaders** — write HLSL vertex and pixel shaders, compiled at runtime. Layout defined with format string
- **GPU Resources** — vertex buffers, constant buffers, blend states, samplers, textures, render targets
- **All Primitive Topologies** — triangle list/strip, line list/strip, point list
- **Render Targets** — offscreen rendering for multi-pass effects
- **Textures & Samplers** — create textures from raw RGBA data, point/linear/anisotropic filtering

All resources encrypted, automatically cleaned up on script unload.

---

## March 16, 2026 — Counter-Strike 2

Custom Draw API (same as Universal API update) pushed to CS2 product.

---

## March 14, 2026 — Universal API

### Sound API (new)
- Full audio engine with waveOut double-buffered mixer, 44100Hz stereo, up to 64 simultaneous instances
- `load_sound` / `free_sound` / `play_sound` / `stop_sound` / `stop_all_sounds`
- Real-time `set_sound_volume` (0–1) and `set_sound_pan` (-1 to +1)
- Looping via `play_sound(..., loop=true)`
- WAV (PCM 8/16-bit) parsed directly, MP3/AAC/WMA/FLAC decoded via Media Foundation
- All audio decoded to PCM at load time — `play_sound` is zero-cost
- Auto-cleanup: leaked sound handles freed on script unload

### VAD / Memory Scan API Fixes
- Fixed `get_vad_snapshot` returning all-zero fields
- Scan functions return `array<uint64>@` (not void with `&out` params)
- Removed nonexistent functions from docs: `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64`
- Added missing functions: `scan_float`, `scan_double`, `scan_string`, `scan_wstring`, `scan_pointer`

### Extensions
- Extension system — `.as` files in `extensions/` auto-detected, ON/OFF toggle, reload, error display
- Full lifecycle hooks: activate, deactivate, tick, file/tab events
- AI pipeline hooks: intercept prompts, inject system context, register custom tools
- Custom IntelliSense: completions and hover tooltips for any file type
- Widget API for settings: checkboxes, sliders, buttons, inputs, text areas, progress bars, dropdowns, color pickers, keybinds
- Platform API access: rendering, input, CPU intrinsics, WinAPI, JSON, Zydis
- Editor API: insert/replace text, set selection, open/save files, goto line
- File I/O, clipboard, synchronization

---

## March 12, 2026 — Universal API

### IDE AI Chatbot Fixes
- Fixed auto-compaction breaking chat after compacting tool call sequences
- Fixed `read_file` overwriting wrong buffer when only one file open
- Fixed workspace path confusion across workspaces
- Fixed `create_file` failing when parent directories don't exist
- Fixed assistant text Copy button not working when overlapping Thinking block
- Fixed AI freezing on certain tool calls involving large files

### New Features
- **OpenRouter Web Search** — `web_search` tool works automatically on OpenRouter endpoints
- **Text selection** in chat — click and drag to select, Ctrl+C to copy
- **Markdown rendering** for links, blockquotes, lists, task checkboxes (during streaming)
- Explorer shows actual directory name instead of hardcoded "Root"
- AI checks file size before reading unknown files

---

## March 11, 2026 — Universal API

### IDE Update — Major Quality Improvement

**AI:**
- Full absolute paths for all file operations
- Context lists all workspace roots with full paths and labeled file trees
- `list_files` shows all workspace roots at once
- Perception API IntelliSense injects both AngelScript and Lua API references when enabled

**Workspace:**
- Multi-root workspace folders — add additional project folders alongside main root
- Manage extra workspace folders from Settings → Project

**Explorer:**
- Right-click context menu: Cut, Copy, Paste, Copy Path
- Recursive folder copy with rename-on-conflict

**Compaction:**
- Fixed auto-compaction triggering too early

---

## March 8, 2026 — Universal API

- **Heavy CPU optimizations** — average scene CPU usage reduced from ~10% down to ~1% (0.8–2% typical)
- **Added professional IDE** with built-in AI assistant (separate GUI)
- **Added reverse engineering tools** (separate GUI)
- Removed legacy RE tools and old chatbot system
- **Added 32-bit games support**

---

## February 17, 2026 — Universal API

### GUI
- Added list widget functions: `list:get`, `list:remove`, `list:highlight`, `list:remove_highlight`, `list:hide`, `list:show`
- Clear button removed for console (use third button)

### Console Logger
- Completely redone, now resizable

---

## February 12, 2026 — Universal API

### Input System
- Mouse delta now returns proper movement delta instead of screen-space delta
- Controller keybinds supported via XINPUT

### RE Tools
- Executable-section-only pattern searches
- Fixed single-hit pattern searches

### Render System
- Script render order reversed — newly created callbacks render first

### AI Chatbot
- Added support for GLM-5

### AngelScript
- Added: `get_gui_position(float &out x, float &out y)`
- Added: `get_gui_size(float &out w, float &out h)`

---

## February 3, 2026 (b) — Universal API

### Render Engine
- Optimized backend performance
- Font loading now instant

### AngelScript & Lua
- Optional `glyph_ranges` argument added to `create_font` and `create_font_mem`
- Matrix4x4 double-precision functions:
  - `readas_float` / `writeas_float` — float precision
  - `readas_double` / `writeas_double` — double precision
- Replaced `source2_world_to_screen` with:
  - `world_to_screen_rowmajor(...)` ⚠️ migration required
  - `world_to_screen_transposed(...)` (new)

### AngelScript
- Thread priority: `set_thread_to_highest_priority()`, `set_thread_to_lowest_priority()`, `set_thread_to_normal_priority()`
- **Atomic API** — `atomic_int32`, `atomic_int64` for lock-free thread-safe shared state

### Deprecated
- `source2_world_to_screen` → migrate to `world_to_screen_rowmajor` or `world_to_screen_transposed`
- Default matrix4x4 read/write → use precision-specific variants

---

## February 3, 2026 (a) — Universal API

### GUI
- Fixed list widget selected index becoming incorrect on add/remove

### RE Tools
- Fixed process selection becoming unselected
- Fixed pattern scan log output
- Fixed "Selected address" and "offset" not populating from scan results
- Disassembly output now includes section name (e.g. `winlogon.exe+0x2000 (.text)`)

### AngelScript
- Added optional viewport parameter to Source 2 W2S:
  ```
  bool source2_world_to_screen(const vector3 &in, const matrix4x4 &in, vector2 &out, const vector2 &in viewport = vector2(0, 0))
  ```

---

## February 1, 2026 — Universal API

### AngelScript & Lua
- Added `get_all_hwnds()` — returns all window handles

### AngelScript
- Fixed `hash_map` reference issue when initializing as global

---

## Enma Open Beta — Phase 2 (May 2026)

### Enma Language
- Perception's proprietary programming language, built from scratch
- **Pure Full-Module AOT and JIT** — no interpreter, no VM, compiles to native machine code
- **C/Rust-tier performance** — real benchmarks (600+ FPS in Rust, single-threaded)
- **C++-flavored syntax** — mostly familiar, cleaner and easier to pick up
- Battle-tested in private beta

**Documentation:**
- [enma-1.gitbook.io/enma](https://enma-1.gitbook.io/enma)
- [docs.perception.cx/perception/enma](https://docs.perception.cx/perception/enma)

### New Modular UI System
- Fully modular — independent, reusable UI components
- Rich new APIs from community most-requested list

### Perception MCP (60-70+ tools)
- Direct AI integration (Claude Opus, etc.)
- Script execution & validation
- Logging & error analysis
- Memory analysis tooling

### IDE & Analyzer Discontinued
- IDE and Analyzer being retired — replaced by Perception MCP
- Maintaining them solo was no longer sustainable

### New Script Market (Coming Summer 2026)
- Brand new website, built from ground up
- Single payment systems (OxaPay, crypto)
- Better moderation and quality control
- Collaborative features
- Direct Perception integration

### Subscription Tiers
| Tier | Price | Includes |
|------|-------|----------|
| **Universal API** | $54.99/month | Full access: all APIs, IDE, AI, Analyzer |
| **CS2 API** | $7.99/30 days | CS2-only framework, script execution + API access |

Universal API capped at 450 users maximum.
