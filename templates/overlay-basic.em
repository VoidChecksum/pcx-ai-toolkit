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

// ── Widget handles (bound in main, synced via on_change) ──
sidebar_section_t g_sec;
checkbox_t        g_cb_enabled;
slider_t          g_sl_size;
colorpicker_t     g_cp_color;
keybind_t         g_kb_toggle;   // bound to VK_F8 in single mode (edge-toggle)

void on_enabled(int64 h) { g_enabled   = g_cb_enabled.get(); }
void on_size(int64 h)    { g_box_size  = g_sl_size.get(); }
void on_color(int64 h)   { g_box_color = g_cp_color.get(); }

// ── Cached state (written by update, read by render) ──
bool    g_visible = true;
float64 g_fps     = 0.0;

// Update routine: logic only, no drawing.
void on_update(int64 data) {
    // Edge-triggered toggle via the keybind (single mode fires once per press).
    if (g_kb_toggle.is_active()) {
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
    g_sec = create_sidebar_section("Overlay", "");
    g_cb_enabled = g_sec.create_checkbox("Enabled", g_enabled);
    g_cb_enabled.on_change(cast<int64>(on_enabled));
    g_sl_size = g_sec.create_slider("Box Size", g_box_size, 20.0, 400.0, 1.0);
    g_sl_size.on_change(cast<int64>(on_size));
    g_cp_color = g_sec.create_colorpicker("Box Color", g_box_color);
    g_cp_color.on_change(cast<int64>(on_color));
    g_kb_toggle = g_sec.create_keybind("Toggle Key");
    g_kb_toggle.bind(0x77, false, false, false, keybind_mode::single); // VK_F8
    g_sec.create_separator();
    g_sec.create_label("F8 toggles visibility", ui_align::left);

    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
