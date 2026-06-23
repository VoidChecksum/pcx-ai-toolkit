// esp-overlay.em — Basic ESP overlay example
// Demonstrates: entity iteration, world-to-screen, box rendering, text labels
// Guidelines: uint64 addresses, null checks, separate update/render, pattern sigs
// Lint: pcx lint esp-overlay.em

import "vec";     // required for vec2, vec3
import "color";   // required for color type
import "proc";    // process access

// ============================================================
// CONFIGURATION — all tunables exposed via GUI (Guideline #11)
// ============================================================
bool  g_esp_enabled    = true;
bool  g_show_names     = true;
bool  g_show_distance  = false;
float g_max_distance   = 500.0f;        // f suffix required (Guideline #8)
color g_box_color      = color(0, 255, 0, 200);    // fresh per frame is fine (Guideline #7)
color g_name_color     = color(255, 255, 255, 255);

// ============================================================
// OFFSETS — pattern signatures, NOT hardcoded (Guideline #5)
// Update these patterns for your target game.
// ============================================================
array<uint8> SIG_ENTITY_LIST = {
    0x48, 0x8B, 0x05, 0x??, 0x??, 0x??, 0x??,  // mov rax, [rip+?]
    0x48, 0x85, 0xC0                              // test rax, rax
};

// Entity structure field offsets (game-specific, update as needed)
const uint64 OFF_HEALTH      = 0x100;
const uint64 OFF_HEAD_BONE   = 0x6D8;
const uint64 OFF_WORLD_POS   = 0x118;
const uint64 OFF_NAME_PTR    = 0x28;

// ============================================================
// STATE — cached in update, consumed in render (Guideline #4)
// No proc_read_* calls are allowed in the render routine.
// ============================================================
struct EntityData {
    vec2   screen_foot;   // projected foot position (bottom of box)
    vec2   screen_head;   // projected head position (top of box)
    float  distance;      // world-space distance to local player origin
    string name;          // entity name string (empty if not fetched)
    bool   valid;         // was the entity valid this update tick?
}

array<EntityData> g_entities;   // rebuilt each update tick
proc_t            g_proc;       // RAII handle — auto-released on scope exit
uint64            g_entity_list_ptr = 0;  // resolved once at startup

// ============================================================
// main() — entry point
// Return > 0 to stay loaded, <= 0 to unload immediately.
// ============================================================
int32 main() {
    // Open the target process
    g_proc = proc_open("game.exe");
    if (!g_proc.valid()) {
        print("[ESP] Failed to open game.exe — is it running?");
        return -1;
    }

    // Verify module base (Guideline #3: validate before use)
    uint64 base = proc_module_base(g_proc, "game.exe");
    if (base == 0) {
        print("[ESP] Could not locate game.exe base address");
        return -1;
    }

    // Resolve entity list via pattern scan (Guideline #5: sigs over hardcodes)
    g_entity_list_ptr = proc_find_pattern(g_proc, "game.exe", SIG_ENTITY_LIST);
    if (g_entity_list_ptr == 0) {
        print("[ESP] Entity list signature not found — update SIG_ENTITY_LIST for this game version");
        return -1;
    }

    // Register separate update and render routines (Guideline #4)
    register_routine(cast<int64>(update_routine), null);
    register_render(cast<int64>(render_routine), null);

    print("[ESP] Loaded successfully");
    return 1;  // stay loaded
}

// ============================================================
// UPDATE ROUTINE — runs every game tick, reads memory
// ALL memory reads must happen here, never in render_routine.
// ============================================================
void update_routine(void@ data) {
    if (!g_esp_enabled) {
        g_entities.resize(0);
        return;
    }

    // Dereference the entity list pointer (Guideline #3: null check)
    uint64 entity_list = proc_read_uint64(g_proc, g_entity_list_ptr);
    if (entity_list == 0) {
        g_entities.resize(0);
        return;
    }

    g_entities.resize(0);

    // Iterate entities (adjust max count for your game)
    for (int i = 0; i < 100; i++) {
        // Read entity pointer from the list (Guideline #3: null check each step)
        uint64 entity = proc_read_uint64(g_proc, entity_list + cast<uint64>(i) * 8);
        if (entity == 0) continue;

        // Skip dead entities
        int32 health = proc_read_int32(g_proc, entity + OFF_HEALTH);
        if (health <= 0) continue;

        // Read foot world position and project to screen
        // Guideline #10: check w > 0, only use results when in front of camera
        vec3 foot_world = proc_read_vec3(g_proc, entity + OFF_WORLD_POS);
        vec2 foot_screen;
        float foot_w;
        if (!world_to_screen(foot_world, foot_screen, foot_w)) continue;
        if (foot_w <= 0.0f) continue;  // behind camera

        // Read head bone position and project
        vec3 head_world = proc_read_vec3(g_proc, entity + OFF_HEAD_BONE);
        vec2 head_screen;
        float head_w;
        if (!world_to_screen(head_world, head_screen, head_w)) continue;
        if (head_w <= 0.0f) continue;

        // Filter by distance
        float dist = vec3_distance(foot_world, get_local_origin());
        if (dist > g_max_distance) continue;

        // Optionally fetch entity name
        string name = "";
        if (g_show_names) {
            uint64 name_ptr = proc_read_uint64(g_proc, entity + OFF_NAME_PTR);
            if (name_ptr != 0) {
                name = proc_read_string(g_proc, name_ptr, 32);
            }
        }

        // Cache for render routine
        EntityData ed;
        ed.screen_foot = foot_screen;
        ed.screen_head = head_screen;
        ed.distance    = dist;
        ed.name        = name;
        ed.valid       = true;
        g_entities.push(ed);
    }
}

// ============================================================
// RENDER ROUTINE — draws only, zero memory reads (Guideline #4)
// No proc_read_* calls here. Read from g_entities cache only.
// ============================================================
void render_routine(void@ data) {
    if (!g_esp_enabled) return;

    for (uint i = 0; i < g_entities.length(); i++) {
        const EntityData@ ed = g_entities[i];
        if (!ed.valid) continue;

        // Derive box dimensions from head/foot screen positions
        float height = ed.screen_foot.y - ed.screen_head.y;
        if (height < 5.0f) continue;  // too small to draw meaningfully
        float width  = height * 0.4f;
        float x      = ed.screen_foot.x - width * 0.5f;
        float y      = ed.screen_head.y;

        // Draw bounding box outline
        // color() constructed here each frame — it's a 4-byte stack value (Guideline #7)
        draw_rect_outline(x, y, width, height, g_box_color, 1.5f);

        // Draw entity name above box
        if (g_show_names && ed.name.length() > 0) {
            draw_text(ed.name,
                      ed.screen_foot.x,
                      ed.screen_head.y - 14.0f,
                      g_name_color,
                      12.0f,
                      TEXT_ALIGN_CENTER);
        }

        // Draw distance below box
        if (g_show_distance) {
            string dist_str = cast<int32>(ed.distance) + "m";
            draw_text(dist_str,
                      ed.screen_foot.x,
                      ed.screen_foot.y + 2.0f,
                      color(200, 200, 200, 180),  // fresh color value (Guideline #7)
                      10.0f,
                      TEXT_ALIGN_CENTER);
        }
    }
}

// ============================================================
// GUI — all tunables exposed as interactive controls (Guideline #11)
// Called by PCX to render the settings panel.
// ============================================================
void gui() {
    gui_checkbox("ESP Enabled",    g_esp_enabled);
    gui_checkbox("Show Names",     g_show_names);
    gui_checkbox("Show Distance",  g_show_distance);
    gui_slider_float("Max Distance", g_max_distance, 50.0f, 2000.0f);
    gui_color_picker("Box Color",    g_box_color);
    gui_color_picker("Name Color",   g_name_color);
}
