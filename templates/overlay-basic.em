// overlay-basic.em — a 2D overlay with a GUI menu, following the 12 guidelines.
// Demonstrates: GUI widgets, config-driven rendering, update/render separation,
//               input polling, and an FPS readout.
// See docs/perception/{gui-api,render-api,input-api}.md

import "vec";
import "color";

// ── Config (bound to GUI widgets) ──
bool    g_enabled   = true;
float64 g_box_size  = 120.0;
color   g_box_color = color(80, 170, 255, 220);
int32   g_toggle_key = 0x77; // VK_F8

// ── Cached state (written by update, read by render) ──
bool    g_visible = true;
float64 g_fps     = 0.0;

// Update routine: logic only, no drawing.
void on_update(int64 data) {
    // Edge-triggered toggle so holding the key doesn't flicker.
    if (is_key_pressed(g_toggle_key)) {
        g_visible = !g_visible;
    }
    g_fps = get_fps();
}

// Render routine: drawing only, no heavy logic.
void on_render(int64 data) {
    if (!g_enabled || !g_visible) return;

    float64 vw = get_view_width();
    float64 vh = get_view_height();

    // Centered box — color/vec constructed fresh every frame (they're free).
    float64 x = (vw - g_box_size) * 0.5;
    float64 y = (vh - g_box_size) * 0.5;
    draw_rect(vec2(x, y), vec2(g_box_size, g_box_size), g_box_color, 2.0, 4.0, 15);

    // FPS readout, top-left, with a shadow for legibility.
    color white  = color(255, 255, 255, 255);
    color shadow = color(0, 0, 0, 180);
    string txt = format("FPS: {d}", cast<int32>(g_fps));
    draw_text(txt, vec2(20.0, 20.0), white, get_font20(), 1, shadow, 1.0);
}

int64 main() {
    // GUI sidebar — every tunable is a widget, never a magic constant.
    int64 sec = create_section("Overlay");
    section_checkbox(sec, "Enabled", g_enabled);
    section_slider_float(sec, "Box Size", g_box_size, 20.0, 400.0);
    section_color_picker(sec, "Box Color", g_box_color);
    section_keybind(sec, "Toggle Key", g_toggle_key);
    section_separator(sec);
    section_label(sec, "F8 toggles visibility");

    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
