// aim.as — smooth aimbot with FOV filter
namespace Cheat {

// Engine-specific helpers — replace with your target's angle read/write.
vec2 read_view_angles() {
    // placeholder: read from your engine's view-angle address
    return vec2(0, 0);
}

void write_view_angles(const vec2&in angles) {
    // placeholder: clamp pitch to [-89, 89] and write to engine memory
}

void aimbot_update(int id, int data_index) {
    if (!g_aim_enabled || !g_initialized || !g_proc.alive()) return;
    if (!is_key_down(g_aim_key)) { g_aim_target.valid = false; return; }

    vec3 local_pos = read_vec3(g_local_player + OFF_POS);
    vec2 current   = read_view_angles();

    EntityInfo best;
    double best_score = 1e9;

    for (int i = 0; i < g_esp_count; i++) {
        EntityInfo@ e = g_entities[i];
        if (!e.valid || e.team == g_local_team || e.health <= 0) continue;
        if (!in_fov(local_pos, current, e.head, g_aim_fov)) continue;

        vec2 target_ang = calc_angle(local_pos, e.head);
        double yaw_delta   = normalize_delta(target_ang.y - current.y);
        double pitch_delta = clamp(target_ang.x - current.x, -89.0, 89.0);
        double score = yaw_delta*yaw_delta + pitch_delta*pitch_delta;

        if (score < best_score) {
            best_score = score;
            best = e;
        }
    }

    g_aim_target = best;
}

void aimbot_render(int id, int data_index) {
    if (!g_aim_enabled || !g_aim_target.valid) return;

    vec3 local_pos = read_vec3(g_local_player + OFF_POS);
    vec2 target = calc_angle(local_pos, g_aim_target.head);
    vec2 current = read_view_angles();

    double yaw_delta   = normalize_delta(target.y - current.y);
    double pitch_delta = clamp(target.x - current.x, -89.0, 89.0);

    vec2 smoothed(
        current.x + pitch_delta * g_aim_smooth,
        current.y + yaw_delta   * g_aim_smooth
    );

    write_view_angles(smoothed);
}

}
