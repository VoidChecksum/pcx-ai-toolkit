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
        println("[main] target not found: " + TARGET_PROCESS);
        return 0;
    }

    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size(TARGET_PROCESS);
    if (g_base == 0 || g_size == 0) {
        println("[main] module not ready");
        return 0;
    }

    if (!resolve_all()) {
        println("[main] signature resolution failed");
        return 0;
    }

    g_initialized = true;
    setup_menu();

    // Memory/update routines
    register_routine(int64(esp_update), 0);
    register_routine(int64(aimbot_update), 0);
    register_routine(int64(triggerbot_update), 0);

    // Render routines
    register_routine(int64(esp_render), 1);
    register_routine(int64(aimbot_render), 1);
    register_routine(int64(triggerbot_render), 1);
    register_routine(int64(radar_render), 1);

    println("[main] cheat skeleton loaded");
    return 1;
}
