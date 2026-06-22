// main.as — entry point: attach to Apex, resolve signatures, keep loaded.
//
// PCX AngelScript lifecycle: main() returns > 0 to stay resident.

#include "globals.as"
#include "offsets.as"

using namespace VoidHook;

const string TARGET_PROCESS = "r5apex.exe";

int main() {
    @g_proc = ref_process(TARGET_PROCESS);
    if (g_proc is null || !g_proc.alive()) {
        log("[main] target not found: " + TARGET_PROCESS);
        return 0;
    }

    // Get module base + size atomically; check both.
    if (!g_proc.get_module(TARGET_PROCESS, g_base, g_size)) {
        log("[main] module not ready");
        g_proc.deref();
        return 0;
    }
    if (g_base == 0 || g_size == 0) {
        log("[main] module returned base=0 or size=0");
        g_proc.deref();
        return 0;
    }

    if (!resolve_all()) {
        log("[main] signature resolution failed");
        g_proc.deref();
        return 0;
    }

    g_initialized = true;
    log("[main] Apex offset resolver loaded");
    return 1;
}
