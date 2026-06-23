// esp.as — box ESP, snaplines, health text
namespace Cheat {

const double PLAYER_HEIGHT = 72.0;

void esp_update(int id, int data_index) {
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

void esp_render(int id, int data_index) {
    if (!g_esp_enabled || g_esp_count == 0) return;

    float vw;
    float vh;
    get_view(vw, vh);
    vector2 screen_bottom = vector2(vw * 0.5, vh);

    for (int i = 0; i < g_esp_count; i++) {
        EntityInfo@ e = g_entities[i];
        if (!e.valid) continue;

        vector2 head2d, feet2d;
        if (!world_to_screen(e.head, head2d)) continue;
        if (!world_to_screen(e.pos,  feet2d)) continue;

        double h = feet2d.y - head2d.y;
        double w = h * 0.5;
        double x = head2d.x - w * 0.5;
        bool friendly = (e.team == g_local_team && e.team != 0);
        uint8 cr = friendly ? 80 : 255;
        uint8 cg = friendly ? 255 : 80;
        uint8 cb = friendly ? 80 : 80;

        draw_rect(float(x), float(head2d.y), float(w), float(h), cr, cg, cb, 220, 1.0f, 0.0f, 0);
        draw_line(screen_bottom.x, screen_bottom.y, float(feet2d.x), float(feet2d.y), 255, 255, 255, 120, 1.0f);

        string hp = "" + e.health;
        draw_text(hp, float(head2d.x - 10.0), float(head2d.y - 18.0), 255, 255, 255, 255,
                  get_font18(), 0, 0, 0, 0, 0, 0.0f);
    }
}

}
