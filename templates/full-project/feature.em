// feature.em — one feature, one file. Update reads state; render draws it.
// This is a skeleton: replace the read/draw bodies with your logic.

import "vec";
import "color";
import "globals";
import "offsets";

// Cached display data (written in update, read in render).
vec2 g_marker_pos = vec2(0.0, 0.0);
bool g_marker_show = false;

// Update: memory reads only, no drawing. Runs on tick.
void feature_update(int64 data) {
    if (!g_enabled || !g_initialized) return;
    if (!g_proc.alive()) return;

    // Example: read a pointer, validate every link before dereferencing.
    uint64 obj = g_proc.ru64(g_example_global);
    if (obj == 0) { g_marker_show = false; return; }

    // ... read fields off `obj`, project to screen, cache into g_marker_pos.
    // For the skeleton we just place a marker at screen center.
    g_marker_pos  = vec2(get_view_width() * 0.5, get_view_height() * 0.5);
    g_marker_show = true;
}

// Render: drawing only, from cached state.
void feature_render(int64 data) {
    if (!g_enabled || !g_marker_show) return;
    draw_circle(g_marker_pos, 6.0, g_color, 2.0, false);
}
