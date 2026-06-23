// aimbot-basic.em — current Enma screen-space aim skeleton.
// Target acquisition is intentionally left as a verified-project step; this file
// demonstrates GUI state, input polling, draw-only render, and mouse movement
// without inventing undocumented PCX helpers.

import "vec";
import "color";
import "strings";
import "math";

bool g_enabled = true;
float64 g_fov = 120.0;
float64 g_smooth = 8.0;
int64 g_aim_key = 0x06; // VK_XBUTTON2

sidebar_section_t g_sec;
checkbox_t g_cb_enabled;
slider_t g_sl_fov;
slider_t g_sl_smooth;
keybind_t g_kb_aim;

bool g_has_target = false;
vec2 g_target_screen = vec2(0.0, 0.0);

void on_enabled(int64 h) { g_enabled = g_cb_enabled.get(); }
void on_fov(int64 h) { g_fov = g_sl_fov.get(); }
void on_smooth(int64 h) { g_smooth = g_sl_smooth.get(); }

void acquire_target_placeholder() {
    // Replace with source-grounded target reads and projection for your game.
    // Keeping this deterministic prevents a sample from implying fake APIs.
    g_has_target = false;
}

void on_update(int64 data) {
    if (!g_enabled) return;
    acquire_target_placeholder();

    if (!g_has_target || !key_down(g_aim_key)) return;

    float64 cx = get_view_width() * 0.5;
    float64 cy = get_view_height() * 0.5;
    float64 dx = g_target_screen.x - cx;
    float64 dy = g_target_screen.y - cy;
    float64 dist = sqrt(dx * dx + dy * dy);
    if (dist > g_fov) return;

    mouse_move_relative(cast<int64>(dx / g_smooth), cast<int64>(dy / g_smooth));
}

void on_render(int64 data) {
    if (!g_enabled) return;

    float64 cx = get_view_width() * 0.5;
    float64 cy = get_view_height() * 0.5;
    color fov = color(80, 170, 255, 180);
    color white = color(255, 255, 255, 255);
    color shadow = color(0, 0, 0, 180);

    draw_circle(vec2(cx, cy), g_fov, fov, 1.5, false);
    draw_text("No target provider installed", vec2(24.0, 24.0),
              white, get_font18(), 1, shadow, 1.0);
}

int64 main() {
    g_sec = create_sidebar_section("Aimbot Example", "");
    g_cb_enabled = g_sec.create_checkbox("Enabled", g_enabled);
    g_cb_enabled.on_change(cast<int64>(on_enabled));
    g_sl_fov = g_sec.create_slider("FOV", g_fov, 20.0, 600.0, 1.0);
    g_sl_fov.on_change(cast<int64>(on_fov));
    g_sl_smooth = g_sec.create_slider("Smooth", g_smooth, 1.0, 30.0, 0.1);
    g_sl_smooth.on_change(cast<int64>(on_smooth));
    g_kb_aim = g_sec.create_keybind("Aim Key");
    g_kb_aim.bind(cast<int64>(g_aim_key), false, false, false, keybind_mode::on);

    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
