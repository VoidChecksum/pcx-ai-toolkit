// aimbot-basic.em — Basic aimbot skeleton
// Demonstrates: FOV check, bone targeting, smooth mouse movement
// Guidelines: uint64 addresses, f suffix, null checks, separate update/render, sigs
// NOTE: This demonstrates the mathematical and API patterns only.
// Lint: pcx lint aimbot-basic.em

import "vec";
import "color";
import "proc";
import "input";  // for mouse_move(), key_down()

// ============================================================
// CONFIGURATION (Guideline #11: GUI for all tunables)
// ============================================================
bool  g_aimbot_enabled = false;   // disabled by default — enable via GUI
float g_fov_degrees    = 10.0f;   // only target within this cone from crosshair
float g_smoothing      = 5.0f;    // larger = slower/smoother aim movement
bool  g_hold_key       = true;    // true = must hold activation key
int32 g_aim_key        = KEY_LALT; // key that activates aim assist

// ============================================================
// OFFSETS — pattern signatures (Guideline #5: no hardcodes)
// ============================================================
array<uint8> SIG_LOCAL_PLAYER = {
    0x48, 0x8B, 0x0D, 0x??, 0x??, 0x??, 0x??,
    0x48, 0x85, 0xC9
};
array<uint8> SIG_ENTITY_LIST = {
    0x4C, 0x8B, 0x0D, 0x??, 0x??, 0x??, 0x??,
    0x45, 0x33, 0xC0
};

// Entity structure offsets (game-specific)
const uint64 OFF_HEALTH      = 0x100;
const uint64 OFF_BONE_HEAD   = 0x6D8;  // head bone world position
const uint64 OFF_BONE_CHEST  = 0x638;  // chest bone world position (fallback)
const uint64 OFF_TEAM        = 0x258;  // team ID

// ============================================================
// STATE — updated in update_routine, consumed in render_routine
// ============================================================
struct AimTarget {
    vec2  screen_pos;   // projected aim point
    float dist_px;      // distance from crosshair in pixels
    bool  valid;
}

AimTarget g_best_target;
proc_t    g_proc;
uint64    g_local_player_ptr = 0;
uint64    g_entity_list_ptr  = 0;
int32     g_local_team       = -1;

// ============================================================
// is_in_fov() — is the screen position within our FOV cone?
// Uses screen-space distance from center. Fast, no trig needed.
// ============================================================
bool is_in_fov(vec2 screen_pos, out float dist_px) {
    float cx = cast<float>(screen_width())  * 0.5f;
    float cy = cast<float>(screen_height()) * 0.5f;
    float dx = screen_pos.x - cx;
    float dy = screen_pos.y - cy;
    // Approximate FOV radius in pixels (screen_width * fov / 90 gives a reasonable mapping)
    float fov_px = cast<float>(screen_width()) * (g_fov_degrees / 90.0f);
    dist_px = sqrt(dx * dx + dy * dy);
    return dist_px < fov_px;
}

// ============================================================
// smooth_move_to() — move mouse toward target with smoothing
// Smoothing of 1.0 = instant snap; higher values = gradual
// ============================================================
void smooth_move_to(vec2 target_screen) {
    float cx  = cast<float>(screen_width())  * 0.5f;
    float cy  = cast<float>(screen_height()) * 0.5f;
    float dx  = (target_screen.x - cx) / g_smoothing;
    float dy  = (target_screen.y - cy) / g_smoothing;
    mouse_move(cast<int32>(dx), cast<int32>(dy));
}

int32 main() {
    g_proc = proc_open("game.exe");
    if (!g_proc.valid()) return -1;

    // Resolve sigs (see memory-scanner.em for full resolution logic with RIP-relative)
    g_local_player_ptr = proc_find_pattern(g_proc, "game.exe", SIG_LOCAL_PLAYER);
    g_entity_list_ptr  = proc_find_pattern(g_proc, "game.exe", SIG_ENTITY_LIST);

    if (g_local_player_ptr == 0 || g_entity_list_ptr == 0) {
        print("[Aimbot] Signature resolution failed — update SIG_* arrays");
        return -1;
    }

    register_routine(cast<int64>(update_routine), null);
    register_render(cast<int64>(render_routine), null);
    return 1;
}

// ============================================================
// update_routine — finds the best valid target this tick
// ============================================================
void update_routine(void@ data) {
    g_best_target.valid = false;

    if (!g_aimbot_enabled) return;
    if (g_hold_key && !key_down(g_aim_key)) return;

    // Resolve local player (Guideline #3: null check)
    uint64 local_player = proc_read_uint64(g_proc, g_local_player_ptr);
    if (local_player == 0) return;

    // Cache local team to avoid friendly-fire
    g_local_team = proc_read_int32(g_proc, local_player + OFF_TEAM);

    uint64 entity_list = proc_read_uint64(g_proc, g_entity_list_ptr);
    if (entity_list == 0) return;  // Guideline #3

    float best_dist = 1e9f;

    for (int i = 0; i < 100; i++) {
        uint64 entity = proc_read_uint64(g_proc, entity_list + cast<uint64>(i) * 8);
        if (entity == 0) continue;          // Guideline #3
        if (entity == local_player) continue; // skip self

        // Skip dead entities
        int32 health = proc_read_int32(g_proc, entity + OFF_HEALTH);
        if (health <= 0) continue;

        // Skip teammates
        int32 team = proc_read_int32(g_proc, entity + OFF_TEAM);
        if (team == g_local_team && g_local_team >= 0) continue;

        // Project head bone to screen (Guideline #10: w > 0 guard)
        vec3 head_world = proc_read_vec3(g_proc, entity + OFF_BONE_HEAD);
        vec2 head_screen;
        float w;
        if (!world_to_screen(head_world, head_screen, w)) continue;
        if (w <= 0.0f) continue;

        // Check FOV cone
        float dist_px;
        if (!is_in_fov(head_screen, dist_px)) continue;

        // Pick the target closest to crosshair
        if (dist_px < best_dist) {
            best_dist = dist_px;
            g_best_target.screen_pos = head_screen;
            g_best_target.dist_px   = dist_px;
            g_best_target.valid     = true;
        }
    }

    // Move toward best target (done in update, not render)
    if (g_best_target.valid) {
        smooth_move_to(g_best_target.screen_pos);
    }
}

// ============================================================
// render_routine — draw visual indicator, no memory reads
// ============================================================
void render_routine(void@ data) {
    if (!g_aimbot_enabled) return;

    // Draw FOV circle (visual reference)
    float fov_px = cast<float>(screen_width()) * (g_fov_degrees / 90.0f);
    float cx = cast<float>(screen_width())  * 0.5f;
    float cy = cast<float>(screen_height()) * 0.5f;
    draw_circle_outline(cx, cy, fov_px, color(100, 100, 100, 80), 1.0f);

    // Highlight locked target
    if (g_best_target.valid) {
        draw_circle(
            g_best_target.screen_pos.x,
            g_best_target.screen_pos.y,
            6.0f,
            color(255, 50, 50, 200)
        );
    }
}

// ============================================================
// gui — all tunables as GUI controls (Guideline #11)
// ============================================================
void gui() {
    gui_checkbox("Aimbot",       g_aimbot_enabled);
    gui_slider_float("FOV",      g_fov_degrees, 1.0f, 90.0f);
    gui_slider_float("Smoothing", g_smoothing,  1.0f, 20.0f);
    gui_checkbox("Hold Key Required", g_hold_key);
}
