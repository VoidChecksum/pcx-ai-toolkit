// triggerbot.as — crosshair-trigger logic
namespace Cheat {

// Engine-specific helper: return the entity under the crosshair.
EntityInfo get_entity_under_crosshair() {
    EntityInfo empty;
    empty.valid = false;
    return empty; // replace with real logic
}

void triggerbot_update(int64 data) {
    if (!g_trigger_enabled || !g_initialized || !g_proc.alive()) return;
    if (!is_key_down(g_trigger_key)) return;

    EntityInfo t = get_entity_under_crosshair();
    if (!t.valid) return;
    if (t.team == g_local_team && g_local_team != 0) return;
    if (t.health <= 0) return;

    if (time_ms() - g_last_fire < g_trigger_delay_ms) return;
    g_last_fire = time_ms();

    press_mouse_left();
}

void triggerbot_render(int64 data) {
    // no rendering
}

}
