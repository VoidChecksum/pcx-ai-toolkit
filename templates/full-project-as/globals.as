// globals.as — shared state for the AngelScript project scaffold.
// Imported (in spirit — AS resolves at script-load) by every other module.
// AngelScript counterpart to templates/full-project/globals.em.
//
// AS-specific notes:
//   * proc_t is a HANDLE type — declared with @, null-checked with `is null`,
//     released with .deref() (see skill://pcx-angelscript-discipline rule 3).
//   * uint64 is the address type, same as Enma.
//   * Colors are passed as raw RGBA ints in the draw API, not a struct
//     (see skill://pcx-angelscript-discipline rule 8).

// ── Process handle + module info (resolved in main, derefed on unload) ──
proc_t@ g_proc = null;
uint64  g_base = 0;
uint64  g_size = 0;

// ── Config (bound to GUI widgets in menu.as / wherever) ──
bool     g_enabled       = true;
float    g_max_distance  = 3000.0f;     // f-suffix for float32 literals (rule #8)
// Color palette as four discrete uint8s — AS draw API takes positional rgba.
uint8    g_color_r = 80;
uint8    g_color_g = 170;
uint8    g_color_b = 255;
uint8    g_color_a = 220;

// ── Resolved offsets (filled in main() after sig scans; uint64 always) ──
uint64   g_off_entity_list  = 0;
uint64   g_off_local_player = 0;

// ── Liveness ──
bool     g_initialized = false;

// ── Callback ID (recorded so on_unload() can unregister cleanly) ──
int      g_cb_tick = 0;
