// aimbot-skeleton.em — single-file FOV aimbot skeleton, following the 12 guidelines.
// Demonstrates: one-shot sig resolution, null-guarded entity walk, W2S targeting,
//               closest-in-FOV selection, write-free mouse aim, update/render split.
// Offsets/sigs are UNVERIFIED placeholders — fill them from YOUR target's IDB/SDK.
// See docs/perception/{win-api,input-api,render-api}.md, knowledge/common-patterns.md,
//     knowledge/offset-methodology.md, and .claude/skills/game-cheat-guidelines.

import "vec";
import "color";
import "math";
import "math3d";
import "strings";

// ── Signatures (UNVERIFIED — instruction patterns, not version offsets) ──
// Each matches the instruction that loads a global pointer; the 4-byte
// RIP-relative displacement is wildcarded and resolved at runtime (rule 5).
const string SIG_ENTITY_LIST  = "48 8B 0D ?? ?? ?? ?? 48 85 C9 74"; // UNVERIFIED — MOV RCX,[rip+????]
const string SIG_LOCAL_PLAYER = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74"; // UNVERIFIED — MOV RAX,[rip+????]
const string SIG_VIEW_MATRIX  = "48 8D 0D ?? ?? ?? ?? 48 89";       // UNVERIFIED — LEA RCX,[rip+????]

// ── Struct field offsets (UNVERIFIED — fill from YOUR target before use) ──
const uint64 OFF_HEALTH      = 0x0;  // UNVERIFIED — int32 health field
const uint64 OFF_TEAM        = 0x0;  // UNVERIFIED — int32 team id
const uint64 OFF_POSITION    = 0x0;  // UNVERIFIED — vec3 origin (float32)
const uint64 OFF_BONE_ARRAY  = 0x0;  // UNVERIFIED — uint64 ptr to bone-matrix array
const uint64 BONE_STRIDE     = 0x30; // UNVERIFIED — bytes per bone matrix entry
const uint64 BONE_POS_OFFSET = 0x0;  // UNVERIFIED — vec3 within a bone matrix
const int32  MAX_ENTITIES    = 64;   // engine entity cap — adjust per game
const uint64 ENTITY_STRIDE   = 0x8;  // pointer-array stride (8 bytes per slot)

// ── Config (bound to GUI widgets) ──
bool    g_enabled      = true;
float64 g_fov_radius   = 120.0;             // screen-pixel FOV around the crosshair
float64 g_smoothing    = 6.0;               // higher = slower/softer pull
float64 g_target_bone  = 8.0;               // bone index (e.g. head) — cast to uint64 to index
float64 g_max_distance = 3000.0;            // world-unit distance gate
int32   g_hotkey       = 0x06;              // VK_XBUTTON2 — hold to aim
color   g_fov_color    = color(80, 170, 255, 200);
color   g_target_color = color(255, 60, 60, 230);

// ── Widget handles (bound in main, synced via on_change) ──
sidebar_section_t g_sec;
checkbox_t        g_cb_enabled;
slider_t          g_sl_fov;
slider_t          g_sl_smooth;
slider_t          g_sl_bone;
slider_t          g_sl_dist;
keybind_t         g_kb_aim;
colorpicker_t     g_cp_fov;
colorpicker_t     g_cp_target;

void on_enabled(int64 h)       { g_enabled      = g_cb_enabled.get(); }
void on_fov(int64 h)           { g_fov_radius   = g_sl_fov.get(); }
void on_smooth(int64 h)        { g_smoothing    = g_sl_smooth.get(); }
void on_bone(int64 h)          { g_target_bone  = g_sl_bone.get(); }
void on_dist(int64 h)          { g_max_distance = g_sl_dist.get(); }
void on_fov_color(int64 h)     { g_fov_color    = g_cp_fov.get(); }
void on_target_color(int64 h)  { g_target_color = g_cp_target.get(); }

// ── Process + resolved globals (uint64 throughout, rule 2) ──
proc_t  g_proc;
uint64  g_base = 0;
uint64  g_size = 0;
bool    g_resolved     = false;
uint64  g_entity_list  = 0;
uint64  g_local_player = 0;
uint64  g_view_matrix  = 0;

// ── Cached state (written in update, read in render) ──
bool  g_have_target   = false;
int32 g_target_idx    = -1;
vec2  g_target_screen = vec2(0.0, 0.0);

// Resolve a RIP-relative operand: final = hit + insn_len + signed_int32(hit + disp_off).
uint64 resolve_rip(uint64 hit, int32 disp_off, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + cast<uint64>(disp_off));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}

// One-shot attach + sig scan (rule 4: scans happen once, not every frame).
bool ensure_resolved() {
    if (g_resolved) return true;
    g_proc = ref_process("game.exe");           // <- set your process name
    if (!g_proc.alive()) return false;           // rule 3: check after ref_process
    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    if (g_base == 0 || g_size == 0) return false;
    uint64 hit_el = g_proc.find_code_pattern(g_base, g_size, SIG_ENTITY_LIST);
    uint64 hit_lp = g_proc.find_code_pattern(g_base, g_size, SIG_LOCAL_PLAYER);
    uint64 hit_vm = g_proc.find_code_pattern(g_base, g_size, SIG_VIEW_MATRIX);
    if (hit_el == 0 || hit_lp == 0 || hit_vm == 0) { // rule 3 + 12: stale sig table
        println("[aim] a signature is stale — re-analyze the current build in IDA");
        return false;
    }

    g_entity_list  = resolve_rip(hit_el, 3, 7);
    g_local_player = resolve_rip(hit_lp, 3, 7);
    g_view_matrix  = resolve_rip(hit_vm, 3, 7);
    g_resolved = g_entity_list != 0 && g_local_player != 0 && g_view_matrix != 0;
    return g_resolved;
}

// Update: memory reads + aim logic only, no drawing (rule 4).
bool project_world_to_screen(vec3 world, mat4 vm, out vec2 screen) {
    // Enma currently exposes matrix reads but not the AngelScript W2S helpers.
    // Replace this with target-specific projection math once your matrix layout
    // is verified; returning false is safer than pretending a helper exists.
    screen = vec2(0.0, 0.0);
    return false;
}

void on_update(int64 data) {
    g_have_target = false;
    if (!g_enabled) return;
    if (!ensure_resolved()) return;
    if (!g_proc.alive()) { g_resolved = false; return; } // re-scan on reattach
    // Local player: needed for the team filter and the distance gate.
    uint64 local = g_proc.ru64(g_local_player);
    if (local == 0) return;                               // rule 3
    int32 local_team = g_proc.r32(local + OFF_TEAM);
    vec3  local_pos  = g_proc.read_vec3_fl32(local + OFF_POSITION);
    // View matrix read once per tick (rule 10: W2S done once, correctly).
    mat4 vm = g_proc.read_mat4_fl32(g_view_matrix);
    float64 cx = get_view_width()  * 0.5;
    float64 cy = get_view_height() * 0.5;
    float64 best_dist = g_fov_radius;                     // only consider targets in FOV
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * ENTITY_STRIDE);
        if (ent == 0) continue;                           // rule 3

        int32 health = g_proc.r32(ent + OFF_HEALTH);
        if (health <= 0) continue;                        // skip dead
        int32 team = g_proc.r32(ent + OFF_TEAM);
        if (team == local_team) continue;                 // skip friendly

        // Bone position: deref the bone-matrix array, then index by bone id.
        uint64 bones = g_proc.ru64(ent + OFF_BONE_ARRAY);
        if (bones == 0) continue;                         // rule 3
        uint64 bone_addr = bones + cast<uint64>(g_target_bone) * BONE_STRIDE + BONE_POS_OFFSET;
        vec3   bone = g_proc.read_vec3_fl32(bone_addr);

        // World-distance gate.
        float64 ddx = bone.x - local_pos.x;
        float64 ddy = bone.y - local_pos.y;
        float64 ddz = bone.z - local_pos.z;
        if (sqrt(ddx*ddx + ddy*ddy + ddz*ddz) > g_max_distance) continue;

        // Project the bone; measure pixel distance to the crosshair.
        vec2 screen;
        if (!project_world_to_screen(bone, vm, screen)) continue; // behind camera (rule 10)
        float64 pdx = screen.x - cx;
        float64 pdy = screen.y - cy;
        float64 pixel = sqrt(pdx*pdx + pdy*pdy);
        if (pixel < best_dist) {
            best_dist       = pixel;
            g_target_screen = screen;
            g_target_idx    = i;
            g_have_target   = true;
        }
    }

    // Aim: hotkey held + locked target -> nudge the crosshair toward it.
    // mouse_move_relative (win-api.md, SendInput) is write-free — no memory
    // write, no .text patch (rule 9). Avoid wf32 to a view-angle address.
    if (g_have_target && g_kb_aim.is_active()) {
        float64 mdx = (g_target_screen.x - cx) / g_smoothing;
        float64 mdy = (g_target_screen.y - cy) / g_smoothing;
        mouse_move_relative(cast<int64>(mdx), cast<int64>(mdy));
    }
}

// Render: drawing only, from cached state — NO memory reads (rule 4).
void on_render(int64 data) {
    if (!g_enabled) return;

    // FOV circle around the crosshair — color/vec constructed fresh (rule 7).
    float64 cx = get_view_width()  * 0.5;
    float64 cy = get_view_height() * 0.5;
    draw_circle(vec2(cx, cy), g_fov_radius, g_fov_color, 1.5, false);

    // Mark the current target from the cache.
    if (g_have_target) {
        draw_circle(g_target_screen, 6.0, g_target_color, 2.0, false);
        color  tag_shadow = color(0, 0, 0, 180);
        string tag = format("TARGET #{d}", g_target_idx);
        draw_text(tag, vec2(g_target_screen.x + 8.0, g_target_screen.y - 6.0),
                  g_target_color, get_font18(), 1, tag_shadow, 1.0);
    }
}

int64 main() {
    // GUI sidebar — every tunable is a widget, never a magic constant (rule 11).
    g_sec = create_sidebar_section("Aimbot", "");
    g_cb_enabled = g_sec.create_checkbox("Enabled", g_enabled);
    g_cb_enabled.on_change(cast<int64>(on_enabled));
    g_sl_fov    = g_sec.create_slider("FOV Radius (px)", g_fov_radius, 10.0, 600.0, 1.0);
    g_sl_fov.on_change(cast<int64>(on_fov));
    g_sl_smooth = g_sec.create_slider("Smoothing", g_smoothing, 1.0, 30.0, 0.1);
    g_sl_smooth.on_change(cast<int64>(on_smooth));
    g_sl_bone   = g_sec.create_slider("Bone Index", g_target_bone, 0.0, 30.0, 1.0);
    g_sl_bone.on_change(cast<int64>(on_bone));
    g_sl_dist   = g_sec.create_slider("Max Distance", g_max_distance, 100.0, 10000.0, 10.0);
    g_sl_dist.on_change(cast<int64>(on_dist));
    g_kb_aim    = g_sec.create_keybind("Aim Key");
    g_kb_aim.bind(cast<int64>(g_hotkey), false, false, false, keybind_mode::on); // hold to aim
    g_cp_fov    = g_sec.create_colorpicker("FOV Color", g_fov_color);
    g_cp_fov.on_change(cast<int64>(on_fov_color));
    g_cp_target = g_sec.create_colorpicker("Target Color", g_target_color);
    g_cp_target.on_change(cast<int64>(on_target_color));
    g_sec.create_separator();
    g_sec.create_label("Hold the Aim Key to lock the closest target in FOV", ui_align::left);
    g_sec.create_label("Offsets are UNVERIFIED placeholders — fill before use", ui_align::left);

    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
