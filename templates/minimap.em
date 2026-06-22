// minimap.em — a rotation-aware minimap / radar, following the 12 guidelines.
// Demonstrates: player-relative (top-up) rotation, entity dots, update/render
//               separation, and GUI-tunable scale + screen position.
// See docs/perception/render-api.md, docs/enma/addon-math.md (sin/cos),
//     knowledge/common-patterns.md ("Minimap / Radar").
// Rotation derivation (yaw in DEGREES, Source-style; convert to radians):
//   local_x = dx*cos(-yaw) - dy*sin(-yaw)
//   local_y = dx*sin(-yaw) + dy*cos(-yaw)
// Rotating world deltas by -yaw puts player forward at the top of the map.
// Same math the aimbot uses for view-relative angles — see knowledge/aimbot-math.md.

import "vec";
import "color";

// ── Offsets / sigs (rule #1: ground every offset; rule #5: prefer sigs) ──
// All UNVERIFIED — placeholders. Resolve against YOUR target before use; never
// ship a game-version offset (CONTRIBUTING.md). Module name is a placeholder.
const string TARGET_MODULE   = "game.exe";
// LEA REG, [rip+????] that loads the entity-list global. Wildcard the disp.
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8"; // UNVERIFIED
// MOV REG, [rip+????] that loads the local-player pointer slot.
const string SIG_LOCAL_PLAYER = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? 8B 88";   // UNVERIFIED
const uint64 OFF_POS       = 0x170;   // UNVERIFIED — vec3 world position
const uint64 OFF_TEAM      = 0xF4;    // UNVERIFIED — int32 team id
const uint64 OFF_VIEW_YAW  = 0x4D80;  // UNVERIFIED — float32 view yaw (degrees)
const int32  MAX_ENTITIES  = 256;
const uint64 ENT_STRIDE    = 0x8;     // entity-list slots are pointers

// ── Config (bound to GUI widgets — rule #11) ──
bool    g_enabled         = true;
float64 g_radius          = 90.0;   // minimap radius in pixels
float64 g_pos_x           = 110.0;  // minimap center X (two sliders: GUI has no vec2 widget)
float64 g_pos_y           = 110.0;  // minimap center Y
float64 g_world_scale     = 12.0;   // world units per pixel
bool    g_show_friendlies = true;
color   g_friendly_color  = color(60, 170, 255, 255);
color   g_enemy_color     = color(255, 60, 60, 255);
int32   g_background_alpha = 150;

// ── Resolved once in main() (rule #2: addresses are uint64) ──
proc_t g_proc;
uint64 g_entity_list = 0;  // address of the entity-list global
uint64 g_local_slot  = 0;  // address holding the local-player pointer

// ── Cached state: written by update, read by render (rule #4) ──
// Pre-sized parallel arrays: legit read-side caching reused every frame (unlike colors/vecs — rule #7).
vec3      g_local_pos;
float64   g_view_yaw  = 0.0;   // degrees
int32     g_local_team = 0;
float64[] g_ent_x;             // world X per cached entity
float64[] g_ent_y;             // world Y per cached entity
int32[]   g_ent_team;          // team id per cached entity
int32     g_ent_count = 0;     // valid entries this frame

// Resolve a RIP-relative LEA/MOV: signed 4-byte disp at hit+disp_at, added to hit+insn_len.
uint64 resolve_rip(uint64 hit, uint64 disp_at, uint64 insn_len) {
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + disp_at);
    return hit + insn_len + cast<uint64>(disp);
}

// Update routine: reads only, no drawing (rule #4).
void on_update(int64 data) {
    g_ent_count = 0;
    if (!g_enabled) return;
    if (!g_proc.alive()) return;
    if (g_entity_list == 0 || g_local_slot == 0) return;

    uint64 local = g_proc.ru64(g_local_slot);   // rule #3: validate every link
    if (local == 0) return;

    g_local_pos  = g_proc.read_vec3_fl32(local + OFF_POS);
    g_view_yaw   = g_proc.rf32(local + OFF_VIEW_YAW);
    g_local_team = g_proc.r32(local + OFF_TEAM);

    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * ENT_STRIDE);
        if (ent == 0) continue;
        if (ent == local) continue;             // self drawn separately at center

        vec3 pos = g_proc.read_vec3_fl32(ent + OFF_POS);
        g_ent_x[g_ent_count]    = pos.x;
        g_ent_y[g_ent_count]    = pos.y;
        g_ent_team[g_ent_count] = g_proc.r32(ent + OFF_TEAM);
        g_ent_count++;
    }
}

// Render routine: draws from cache, no memory reads (rule #4).
void on_render(int64 data) {
    if (!g_enabled) return;

    // Background + rim — color built fresh with the GUI alpha (rule #7).
    vec2  center = vec2(g_pos_x, g_pos_y);
    color bg     = color(15, 15, 20, cast<uint8>(g_background_alpha));
    color rim    = color(255, 255, 255, 90);
    draw_circle(center, g_radius, bg, 1.0, true);
    draw_circle(center, g_radius, rim, 1.5, false);
    draw_line(vec2(g_pos_x, g_pos_y - g_radius), vec2(g_pos_x, g_pos_y - g_radius + 8.0), rim, 1.5); // forward tick

    float64 yaw_rad = g_view_yaw * (pi() / 180.0);
    float64 c = cos(-yaw_rad);
    float64 s = sin(-yaw_rad);
    float64 edge = g_radius - 3.0;   // keep dots inside the rim

    for (int32 i = 0; i < g_ent_count; i++) {
        bool friendly = (g_ent_team[i] == g_local_team);
        if (friendly && !g_show_friendlies) continue;

        // World delta, rotated by -yaw into player-relative space.
        float64 dx = g_ent_x[i] - g_local_pos.x;
        float64 dy = g_ent_y[i] - g_local_pos.y;
        float64 rx = dx * c - dy * s;
        float64 ry = dx * s + dy * c;

        // Scale world units → pixels. Y negated so forward maps to screen-up.
        float64 px = rx / g_world_scale;
        float64 py = -(ry / g_world_scale);

        // Clip to radius: clamp out-of-range dots onto the rim (keeps direction).
        float64 dist = hypot(px, py);
        if (dist > edge && dist > 0.0001) {
            float64 k = edge / dist;
            px *= k;
            py *= k;
        }

        color dot = friendly ? g_friendly_color : g_enemy_color;
        draw_circle(vec2(g_pos_x + px, g_pos_y + py), 2.5, dot, 1.0, true);
    }

    // Local player dot at center — color/vec constructed fresh (rule #7).
    draw_circle(center, 3.0, color(80, 255, 120, 255), 1.0, true);
}

int64 main() {
    g_proc = ref_process(TARGET_MODULE);
    if (!g_proc.alive()) {
        println("minimap: target process not found");
        return 0;
    }

    uint64 base = g_proc.base_address();
    uint64 size = g_proc.get_module_size(TARGET_MODULE);
    if (base == 0 || size == 0) return 0;

    // Resolve globals via sig + RIP-relative (rule #5). Check every hit (rule #3).
    uint64 hit_ents = g_proc.find_code_pattern(base, size, SIG_ENTITY_LIST);
    uint64 hit_self = g_proc.find_code_pattern(base, size, SIG_LOCAL_PLAYER);
    if (hit_ents == 0 || hit_self == 0) {
        println("minimap: sig scan failed — offset table is stale");
        return 0;
    }
    // LEA r64,[rip+d]: disp at +3, 7-byte instruction. MOV r64,[rip+d]: same shape.
    g_entity_list = resolve_rip(hit_ents, 3, 7);
    g_local_slot  = resolve_rip(hit_self, 3, 7);

    // Pre-size the read-side cache once (legitimate caching, not premature opt).
    g_ent_x.resize(MAX_ENTITIES);
    g_ent_y.resize(MAX_ENTITIES);
    g_ent_team.resize(MAX_ENTITIES);

    // GUI — every tunable is a widget, no magic constants (rule #11).
    int64 sec = create_section("Minimap");
    section_checkbox(sec, "Enabled", g_enabled);
    section_slider_float(sec, "Radius (px)", g_radius, 40.0, 240.0);
    section_slider_float(sec, "Position X", g_pos_x, 0.0, 1920.0);
    section_slider_float(sec, "Position Y", g_pos_y, 0.0, 1080.0);
    section_slider_float(sec, "World Scale (units/px)", g_world_scale, 1.0, 80.0);
    section_slider_int(sec, "Background Alpha", g_background_alpha, 0, 255);
    section_checkbox(sec, "Show Friendlies", g_show_friendlies);
    section_color_picker(sec, "Friendly Color", g_friendly_color);
    section_color_picker(sec, "Enemy Color", g_enemy_color);
    section_separator(sec);
    section_label(sec, "Top of map = player forward");

    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1; // stay loaded
}
