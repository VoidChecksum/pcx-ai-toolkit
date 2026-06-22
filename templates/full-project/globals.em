// globals.em — shared state for the project.
// Imported by every other module. Holds the process handle, resolved
// module base/size, and config bound to the GUI.

import "vec";
import "color";

// ── Process handle + module info (resolved in main) ──
proc_t  g_proc;
uint64  g_base = 0;   // module base — uint64, always
uint64  g_size = 0;

// ── Config (bound to GUI widgets in menu.em) ──
bool    g_enabled      = true;
float64 g_max_distance = 3000.0;
color   g_color        = color(80, 170, 255, 220);

// ── Liveness ──
bool g_initialized = false;
