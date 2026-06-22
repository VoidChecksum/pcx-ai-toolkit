// globals.as — shared state for Apex Legends resolver
//
// All addresses are uint64. No int64, no int for memory addresses.

namespace VoidHook {

// Target process handle (set in main.as)
proc_t@ g_proc;
uint64  g_base = 0;
uint64  g_size = 0;
bool    g_initialized = false;

// Resolved in offsets.as
uint64 g_local_player = 0;   // E-001
uint64 g_entity_system = 0;   // E-002
uint64 g_entity_list = 0;     // E-002 cont.
uint64 g_view_matrix = 0;     // E-003

}
