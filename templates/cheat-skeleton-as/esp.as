// esp.as — box ESP, snaplines, health text
namespace Cheat {

const double PLAYER_HEIGHT = 72.0;

void esp_update(int64 data) {
    if (!g_esp_enabled || !g_initialized || !g_proc.alive()) return;

    g_esp_count = 0;

    if (g_local_player != 0) {
        g_local_team = g_proc.r32(g_local_player + OFF_TEAM);
    }

    for (int i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + uint64(i) * 8);
        if (ent == 0) continue;
        if (ent == g_local_player) continue;

        int health = g_proc.r32(ent + OFF_HEALTH);
        if (health <= 0 || health > 999) continue;

        EntityInfo info;
        info.ptr    = ent;
        info.health = health;
        info.team   = g_proc.r32(ent + OFF_TEAM);
        info.pos    = read_vec3(ent + OFF_POS);
        info.head   = info.pos; info.head.z += PLAYER_HEIGHT;
        info.valid  = true;

        g_entities[g_esp_count] = info;
        g_esp_count++;
        if (g_esp_count >= MAX_ENTITIES) break;
    }
}

void esp_render(int64 data) {
    if (!g_esp_enabled || g_esp_count == 0) return;

    color enemy(255, 80, 80, 220);
    color ally(80, 255, 80, 220);
    color white(255, 255, 255, 255);

    double vw = get_view_width();
    vec2 screen_bottom(vw * 0.5, get_view_height());

    for (int i = 0; i < g_esp_count; i++) {
        EntityInfo@ e = g_entities[i];
        if (!e.valid) continue;

        vec2 head2d, feet2d;
        if (!world_to_screen(e.head, head2d)) continue;
        if (!world_to_screen(e.pos,  feet2d)) continue;

        double h = feet2d.y - head2d.y;
        double w = h * 0.5;
        double x = head2d.x - w * 0.5;
        color c = (e.team == g_local_team && e.team != 0) ? ally : enemy;

        draw_rect(vec2(x, head2d.y), vec2(w, h), c, 1.0, false);
        draw_line(screen_bottom, feet2d, color(255, 255, 255, 120), 1.0);

        string hp = format("{}", e.health);
        draw_text(hp, vec2(head2d.x - 10.0, head2d.y - 18.0), white,
                  get_font14(), 0, color(0,0,0,0), 0.0);
    }
}

}
