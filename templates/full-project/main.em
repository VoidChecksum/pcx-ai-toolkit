// main.em — entry point. Wires the modules together and registers routines.
// Bundle order matters: globals -> offsets -> feature -> menu -> main.

import "globals";
import "offsets";
import "feature";
import "menu";

int64 main() {
    // 1. Attach to the target process.
    g_proc = ref_process("game.exe");   // <- set your process name
    if (!g_proc.alive()) {
        println("[main] target process not found");
        return 0; // unload
    }

    // 2. Resolve the module base/size (uint64 throughout).
    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    if (g_base == 0 || g_size == 0) {
        println("[main] module not loaded yet");
        return 0;
    }

    // 3. Resolve offsets via pattern scans. Bail if sigs are stale.
    if (!resolve_all()) {
        println("[main] offset resolution failed — update sigs");
        return 0;
    }

    // 4. GUI + routines.
    setup_menu();
    register_routine(cast<int64>(feature_update), 0);
    register_routine(cast<int64>(feature_render), 0);

    g_initialized = true;
    println("[main] loaded");
    return 1; // stay loaded
}
