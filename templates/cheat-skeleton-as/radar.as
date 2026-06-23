// radar.as — 2D world radar
namespace Cheat {

const double RADAR_SCALE  = 0.05;
const double RADAR_RADIUS = 100.0;

bool world_to_map(const vector3&in world, vector2&out map) {
    map = vector2(world.x, world.y);
    return true;
}

void radar_render(int id, int data_index) {
    if (!g_radar_enabled || g_esp_count == 0) return;

    vector3 local_pos = read_vec3(g_local_player + OFF_POS);
    vector2 local2d;
    if (!world_to_map(local_pos, local2d)) return;

    float vw;
    float vh;
    get_view(vw, vh);
    double cx = vw - 150.0;
    double cy = vh - 150.0;

    draw_circle(float(cx), float(cy), float(RADAR_RADIUS), 0, 0, 0, 160, 2.0f, true);

    draw_circle(float(cx), float(cy), 4.0f, 255, 255, 255, 255, 1.0f, true);

    for (int i = 0; i < g_esp_count; i++) {
        EntityInfo@ e = g_entities[i];
        if (!e.valid) continue;

        vector2 blip;
        if (!world_to_map(e.pos, blip)) continue;
        vector2 rel = blip - local2d;
        rel.x *= RADAR_SCALE;
        rel.y *= RADAR_SCALE;

        if (rel.x*rel.x + rel.y*rel.y > RADAR_RADIUS*RADAR_RADIUS) continue;

        bool friendly = (e.team == g_local_team && g_local_team != 0);
        uint8 cr = friendly ? 80 : 255;
        uint8 cg = friendly ? 255 : 80;
        uint8 cb = 80;
        draw_circle(float(cx + rel.x), float(cy + rel.y), 4.0f, cr, cg, cb, 255, 1.0f, true);
    }
}

}
