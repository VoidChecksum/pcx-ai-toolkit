// radar.as — 2D world radar
namespace Cheat {

const double RADAR_SCALE  = 0.05;
const double RADAR_RADIUS = 100.0;

bool world_to_map(const vec3&in world, vec2&out map) {
    map = vec2(world.x, world.y);
    return true;
}

void radar_render(int id, int data_index) {
    if (!g_radar_enabled || g_esp_count == 0) return;

    vec3 local_pos = read_vec3(g_local_player + OFF_POS);
    vec2 local2d;
    if (!world_to_map(local_pos, local2d)) return;

    double cx = get_view_width()  - 150.0;
    double cy = get_view_height() - 150.0;

    color bg(0, 0, 0, 160);
    draw_circle(vec2(cx, cy), RADAR_RADIUS, bg, 2.0, true);

    color local_color(255, 255, 255, 255);
    draw_circle(vec2(cx, cy), 4.0, local_color, 1.0, true);

    for (int i = 0; i < g_esp_count; i++) {
        EntityInfo@ e = g_entities[i];
        if (!e.valid) continue;

        vec2 blip;
        if (!world_to_map(e.pos, blip)) continue;
        vec2 rel = blip - local2d;
        rel.x *= RADAR_SCALE;
        rel.y *= RADAR_SCALE;

        if (rel.x*rel.x + rel.y*rel.y > RADAR_RADIUS*RADAR_RADIUS) continue;

        color c = (e.team == g_local_team && g_local_team != 0)
            ? color(80, 255, 80, 255)
            : color(255, 80, 80, 255);
        draw_circle(vec2(cx + rel.x, cy + rel.y), 4.0, c, 1.0, true);
    }
}

}
