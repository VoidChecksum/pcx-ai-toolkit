// main.as — entry point and routine registration
#include "globals.as"
#include "offsets.as"
#include "utils.as"
#include "esp.as"
#include "aim.as"
#include "triggerbot.as"
#include "radar.as"
#include "menu.as"

using namespace Cheat;

const string TARGET_PROCESS = "game.exe"; // REPLACE WITH REAL TARGET

int main() {
    @g_proc = ref_process(TARGET_PROCESS);
    if (!g_proc.alive()) {
        log("[main] target not found: " + TARGET_PROCESS);
        return 0;
    }

    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size(TARGET_PROCESS);
    if (g_base == 0 || g_size == 0) {
        log("[main] module not ready");
        return 0;
    }

    if (!resolve_all()) {
        log("[main] signature resolution failed");
        return 0;
    }

    g_initialized = true;
    setup_menu();

    // Memory/update routines (~60 Hz)
    register_callback(@esp_update, 16, 0);
    register_callback(@aimbot_update, 16, 0);
    register_callback(@triggerbot_update, 16, 0);

    // Render routines (~120 Hz)
    register_callback(@esp_render, 8, 1);
    register_callback(@aimbot_render, 8, 1);
    register_callback(@triggerbot_render, 8, 1);
    register_callback(@radar_render, 8, 1);

    log("[main] cheat skeleton loaded");
    return 1;
}
