// triggerbot.as — crosshair-trigger logic
namespace Cheat {

// Engine-specific helper: return the entity under the crosshair.
EntityInfo get_entity_under_crosshair() {
    EntityInfo empty;
    empty.valid = false;
    return empty; // replace with real logic
}

void triggerbot_update(int id, int data_index) {
    if (!g_trigger_enabled || !g_initialized || !g_proc.alive()) return;
    if (!key_down(g_trigger_key)) return;

    EntityInfo t = get_entity_under_crosshair();
    if (!t.valid) return;
    if (t.team == g_local_team && g_local_team != 0) return;
    if (t.health <= 0) return;

    if (get_tickcount64() - g_last_fire < g_trigger_delay_ms) return;
    g_last_fire = get_tickcount64();

    mouse_left_click();
}

void triggerbot_render(int id, int data_index) {
    // no rendering
}

}
