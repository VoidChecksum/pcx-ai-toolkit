# pcx-ai-toolkit — Knowledge Bundle

> Every knowledge reference in the pcx-ai-toolkit concatenated into one file. Covers engine RE references, anti-cheat architecture, common scripting patterns, aimbot math, API cheatsheets, GUI design, multi-binary organization, network protocol RE, and the cross-language bridge.

> **Generated** by `tools/build-llms-index.py` — do not edit manually. Re-generate by running the tool from the repo root. CI verifies the committed bundle matches the current source.

**Source files included: 10**

---

## Source: `knowledge/cheat-script-cookbook.md`

> **Scope:** Educational cookbook for Perception.cx cheat-script development. Authorized targets only — analyze software you own or have permission to test.

# Cheat Script Cookbook

This file is the practical companion to `game-cheat-guidelines` and `game-hacking-pcx`.
It contains small, reusable recipes for the most common cheat-script tasks. Copy
and adapt them inside your own projects; they follow the 12 guidelines and the
cheat-script master rules.

All examples are written in **Enma (.em)** because that is the default PCX
language. AngelScript and Lua equivalents follow the same logic with their own
syntax (see `knowledge/pcx-cross-language-bridge.md`).

---

## Table of Contents

1. [Project skeleton](#project-skeleton)
2. [Process attach + pattern scan](#process-attach--pattern-scan)
3. [Pointer chain walk](#pointer-chain-walk)
4. [World-to-screen](#world-to-screen)
5. [ESP box](#esp-box)
6. [Snapline](#snapline)
7. [Aimbot angle + smoothing](#aimbot-angle--smoothing)
8. [FOV cone check](#fov-cone-check)
9. [Triggerbot](#triggerbot)
10. [Radar](#radar)
11. [Config save/load](#config-saveload)
12. [Unload cleanup](#unload-cleanup)

---

## Project skeleton

```
my_cheat/
├── globals.em    # proc_t, base/size, cache, config
├── offsets.em    # sigs + resolved addresses
├── utils.em      # W2S, distance, team check
├── esp.em        # read + render ESP
├── aim.em        # aimbot logic
├── triggerbot.em # trigger logic
├── radar.em      # 2D radar
├── menu.em       # GUI + config
└── main.em       # setup + routines
```

Compile bundle order: `globals` → `offsets` → `utils` → `esp` → `aim` → `triggerbot`
→ `radar` → `menu` → `main`.

---

## Process attach + pattern scan

```cpp
// main.em
import "globals";
import "offsets";
import "menu";
import "esp";
import "aim";

int64 main() {
    g_proc = ref_process("game.exe");     // set real process name
    if (!g_proc.alive()) {
        println("[main] target not found");
        return 0;
    }

    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    if (g_base == 0 || g_size == 0) {
        println("[main] module not ready");
        return 0;
    }

    if (!resolve_all()) {
        println("[main] sigs stale");
        return 0;
    }

    setup_menu();
    register_routine(cast<int64>(on_update), 0);  // memory reads
    register_routine(cast<int64>(on_render), 0);  // drawing

    println("[main] loaded");
    return 1;
}
```

```cpp
// offsets.em
import "globals";

const string SIG_ENTITY_LIST = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ??"; // UNVERIFIED
const string SIG_LOCAL_PLAYER = "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ??"; // UNVERIFIED

uint64 resolve_rip(uint64 hit, int32 disp_off, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + cast<uint64>(disp_off));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}

bool resolve_all() {
    uint64 hit_el = g_proc.find_code_pattern(g_base, g_size, SIG_ENTITY_LIST);
    if (hit_el == 0) { println("[offsets] entity_list sig stale"); return false; }
    g_entity_list = resolve_rip(hit_el, 3, 7);

    uint64 hit_lp = g_proc.find_code_pattern(g_base, g_size, SIG_LOCAL_PLAYER);
    if (hit_lp == 0) { println("[offsets] local_player sig stale"); return false; }
    g_local_player = resolve_rip(hit_lp, 3, 7);

    return g_entity_list != 0 && g_local_player != 0;
}
```

---

## Pointer chain walk

```cpp
// utils.em
import "globals";

uint64 read_chain(uint64 base, int32[] offsets) {
    uint64 addr = base;
    for (int32 i = 0; i < offsets.length(); i++) {
        if (addr == 0) return 0;
        addr = g_proc.ru64(addr);
        if (addr == 0) return 0;
        addr += cast<uint64>(offsets[i]);
    }
    return addr;
}
```

Usage:

```cpp
int32[] health_chain = { 0x10, 0x20, 0xE8 };
uint64 health_addr = read_chain(g_local_player, health_chain);
if (health_addr == 0) return;
int32 health = g_proc.r32(health_addr);
```

---

## World-to-screen

Source-engine column-major 4x4. Adapt matrix layout for your engine.

```cpp
// utils.em
import "vec";
import "color";
import "globals";

bool world_to_screen(vec3 world, out vec2 screen) {
    float64 m[16];
    // read 16 floats from g_view_matrix (set in offsets.em)
    for (int32 i = 0; i < 16; i++) {
        m[i] = g_proc.rf32(g_view_matrix + cast<uint64>(i * 4));
    }

    float64 w = m[3]*world.x + m[7]*world.y + m[11]*world.z + m[15];
    if (w < 0.001) return false;

    float64 inv_w = 1.0 / w;
    float64 nx = (m[0]*world.x + m[4]*world.y + m[8]*world.z + m[12]) * inv_w;
    float64 ny = (m[1]*world.x + m[5]*world.y + m[9]*world.z + m[13]) * inv_w;

    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

---

## ESP box

```cpp
// esp.em
import "vec";
import "color";
import "globals";
import "utils";

void esp_update(int64 data) {
    if (!g_esp_enabled || !g_initialized || !g_proc.alive()) return;

    g_esp_count = 0;
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;
        if (ent == g_local_player) continue;

        EntityInfo info;
        info.pos = g_proc.read_vec3_fl32(ent + OFF_POS);     // verify in IDA
        info.health = g_proc.r32(ent + OFF_HEALTH);
        info.team = g_proc.r32(ent + OFF_TEAM);
        info.valid = true;

        g_entities[g_esp_count] = info;
        g_esp_count++;
        if (g_esp_count >= MAX_ENTITIES) break;
    }
}

void esp_render(int64 data) {
    if (!g_esp_enabled) return;

    color enemy = color(255, 80, 80, 220);
    color ally  = color(80, 255, 80, 220);
    color white = color(255, 255, 255, 255);

    for (int32 i = 0; i < g_esp_count; i++) {
        EntityInfo e = g_entities[i];
        if (!e.valid) continue;

        vec2 head2d, feet2d;
        vec3 head = e.pos; head.z += 72.0;  // approximate player height
        vec3 feet = e.pos;

        if (!world_to_screen(head, head2d)) continue;
        if (!world_to_screen(feet, feet2d)) continue;

        float64 h = feet2d.y - head2d.y;
        float64 w = h * 0.5;
        color c = (e.team == g_local_team) ? ally : enemy;

        draw_rect(vec2(head2d.x - w*0.5, head2d.y), vec2(w, h), c, 1.0, false);

        string hp_text = format("{}", e.health);
        draw_text(hp_text, vec2(head2d.x - 10.0, head2d.y - 18.0), white,
                  get_font14(), 0, color(0,0,0,0), 0.0);
    }
}
```

---

## Snapline

```cpp
// esp.em (inside esp_render)
vec2 screen_center = vec2(get_view_width() * 0.5, get_view_height());
for (int32 i = 0; i < g_esp_count; i++) {
    EntityInfo e = g_entities[i];
    if (!e.valid) continue;
    vec2 pos;
    if (!world_to_screen(e.pos, pos)) continue;
    draw_line(screen_center, pos, color(255, 255, 255, 120), 1.0);
}
```

---

## Aimbot angle + smoothing

```cpp
// aim.em
import "vec";
import "math";
import "globals";
import "utils";

const float64 PI = 3.14159265358979;
const float64 RAD2DEG = 180.0 / PI;

vec2 calc_angle(vec3 src, vec3 dst) {
    vec3 d = dst.sub(src);
    float64 dist_xy = sqrt(d.x*d.x + d.y*d.y);
    float64 pitch = atan2(-d.z, dist_xy) * RAD2DEG;
    float64 yaw   = atan2(d.y, d.x) * RAD2DEG;
    return vec2(pitch, yaw);
}

float64 normalize_delta(float64 delta) {
    return fmod(delta + 540.0, 360.0) - 180.0;
}

void aimbot_update(int64 data) {
    if (!g_aim_enabled || !g_initialized || !g_proc.alive()) return;
    if (!is_key_down(g_aim_key)) { g_aim_target.valid = false; return; }

    vec3 local_pos = g_proc.read_vec3_fl32(g_local_player + OFF_POS);
    vec2 current = read_view_angles();  // engine-specific helper

    EntityInfo best;
    float64 best_score = 1e9;
    for (int32 i = 0; i < g_esp_count; i++) {
        EntityInfo e = g_entities[i];
        if (!e.valid || e.team == g_local_team || e.health <= 0) continue;

        vec2 target_ang = calc_angle(local_pos, e.pos);
        float64 yaw_delta = normalize_delta(target_ang.y - current.y);
        float64 pitch_delta = fclamp(target_ang.x - current.x, -89.0, 89.0);
        float64 score = yaw_delta*yaw_delta + pitch_delta*pitch_delta;

        if (score < best_score) {
            best_score = score;
            best = e;
        }
    }

    g_aim_target = best;
}

void aimbot_render(int64 data) {
    if (!g_aim_enabled || !g_aim_target.valid) return;

    vec3 local_pos = g_proc.read_vec3_fl32(g_local_player + OFF_POS);
    vec2 target = calc_angle(local_pos, g_aim_target.pos);
    vec2 current = read_view_angles();

    float64 yaw_delta   = normalize_delta(target.y - current.y);
    float64 pitch_delta = fclamp(target.x - current.x, -89.0, 89.0);

    vec2 smoothed = vec2(
        current.x + pitch_delta * g_aim_smooth,
        current.y + yaw_delta   * g_aim_smooth
    );

    write_view_angles(smoothed);  // engine-specific helper
}
```

---

## FOV cone check

```cpp
// utils.em
import "math";
import "vec";
import "globals";

vec3 angles_to_forward(float64 pitch_deg, float64 yaw_deg) {
    float64 p = pitch_deg * (PI / 180.0);
    float64 y = yaw_deg * (PI / 180.0);
    float64 cp = cos(p);
    return vec3(cp * cos(y), cp * sin(y), -sin(p));
}

bool in_fov(vec3 src, vec2 view_angles, vec3 target, float64 fov_deg) {
    vec3 dir = target.sub(src);
    float64 len = sqrt(dir.x*dir.x + dir.y*dir.y + dir.z*dir.z);
    if (len == 0.0) return false;
    dir = vec3(dir.x / len, dir.y / len, dir.z / len);

    vec3 fwd = angles_to_forward(view_angles.x, view_angles.y);
    float64 dot = fwd.x*dir.x + fwd.y*dir.y + fwd.z*dir.z;
    return dot >= cos(fov_deg * (PI / 180.0));
}
```

Use it inside `aimbot_update` to filter candidates before scoring.

---

## Triggerbot

```cpp
// triggerbot.em
import "globals";
import "utils";

void triggerbot_update(int64 data) {
    if (!g_trigger_enabled || !g_initialized || !g_proc.alive()) return;
    if (!is_key_down(g_trigger_key)) return;

    EntityInfo crosshair_target = get_entity_under_crosshair(); // engine helper
    if (!crosshair_target.valid) return;
    if (crosshair_target.team == g_local_team) return;
    if (crosshair_target.health <= 0) return;

    // simple fire-rate gate: last fire timestamp
    if (time_ms() - g_last_fire < g_trigger_delay_ms) return;
    g_last_fire = time_ms();

    press_mouse_left();  // or engine-specific fire command
}

void triggerbot_render(int64 data) {
    // nothing to draw; render routine present for registration symmetry
}
```

---

## Radar

```cpp
// radar.em
import "vec";
import "color";
import "globals";

const float64 RADAR_SCALE = 0.05;  // world-units per radar-pixel

void radar_render(int64 data) {
    if (!g_radar_enabled) return;

    vec2 local2d;
    vec3 local_pos = g_proc.read_vec3_fl32(g_local_player + OFF_POS);
    if (!world_to_map(local_pos, local2d)) return;  // project X/Z to 2D

    float64 cx = get_view_width()  - 150.0;
    float64 cy = get_view_height() - 150.0;
    float64 radius = 100.0;

    color bg = color(0, 0, 0, 160);
    draw_circle(vec2(cx, cy), radius, bg, 2.0, true);

    for (int32 i = 0; i < g_esp_count; i++) {
        EntityInfo e = g_entities[i];
        if (!e.valid) continue;

        vec2 blip;
        if (!world_to_map(e.pos, blip)) continue;
        vec2 rel = blip.sub(local2d);
        rel = vec2(rel.x * RADAR_SCALE, rel.y * RADAR_SCALE);
        if (rel.x*rel.x + rel.y*rel.y > radius*radius) continue;

        color c = (e.team == g_local_team) ? color(80,255,80,255) : color(255,80,80,255);
        draw_circle(vec2(cx + rel.x, cy + rel.y), 4.0, c, 1.0, true);
    }
}
```

---

## Config save/load

```cpp
// menu.em
import "json";
import "file";
import "globals";

const string CONFIG_PATH = "my_cheat_config.json";

void save_config() {
    json_value root = json_object();
    root["esp_enabled"] = json_bool(g_esp_enabled);
    root["aim_enabled"] = json_bool(g_aim_enabled);
    root["aim_smooth"]  = json_float(g_aim_smooth);
    root["aim_fov"]     = json_float(g_aim_fov);
    root["trigger_enabled"] = json_bool(g_trigger_enabled);
    root["radar_enabled"]   = json_bool(g_radar_enabled);

    string text = json_stringify(root, 2);
    file_write(CONFIG_PATH, text);
}

void load_config() {
    if (!file_exists(CONFIG_PATH)) return;
    string text = file_read(CONFIG_PATH);
    json_value root = json_parse(text);
    if (root.type() != JSON_OBJECT) return;

    g_esp_enabled     = root["esp_enabled"].as_bool(g_esp_enabled);
    g_aim_enabled     = root["aim_enabled"].as_bool(g_aim_enabled);
    g_aim_smooth      = root["aim_smooth"].as_float(g_aim_smooth);
    g_aim_fov         = root["aim_fov"].as_float(g_aim_fov);
    g_trigger_enabled = root["trigger_enabled"].as_bool(g_trigger_enabled);
    g_radar_enabled   = root["radar_enabled"].as_bool(g_radar_enabled);
}
```

---

## Unload cleanup

```cpp
// main.em
void on_unload() {
    g_initialized = false;
    // no explicit proc_t release in Enma; handle goes out of scope
    println("[main] unloaded");
}
```

For AngelScript, explicitly `deref()` the handle and unregister callbacks.

---

## See Also

- `skill://game-cheat-guidelines` — the 12 hard rules
- `skill://game-hacking-pcx` — full doc index
- `knowledge/aimbot-math.md` — angle math in depth
- `knowledge/common-patterns.md` — W2S, ESP, radar patterns
- `knowledge/offset-methodology.md` — finding and maintaining offsets
- `templates/cheat-skeleton-em/` — full working scaffold

---

## Source: `knowledge/common-patterns.md`

# Common Enma Scripting Patterns for Perception.cx

## Pattern: Process Attach and Module Resolve

```cpp
proc_t g_proc;
uint64 g_base;
uint64 g_size;

bool init_process() {
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) return false;
    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    return g_base != 0;
}
```

## Pattern: Signature Scanning with RIP-Relative Resolution

```cpp
// Resolve a RIP-relative LEA/MOV: instruction at `hit` has a 4-byte displacement at `hit+disp_offset`
// Final address = hit + instruction_length + signed_displacement
uint64 resolve_rip(proc_t& p, uint64 hit, int32 disp_offset, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = p.r32(hit + cast<uint64>(disp_offset));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}

// Example: LEA RCX, [rip+????] = 48 8D 0D ?? ?? ?? ??
// disp_offset=3 (skip 48 8D 0D), insn_len=7
uint64 find_global(proc_t& p, uint64 base, uint64 size, string sig) {
    uint64 hit = p.find_code_pattern(base, size, sig);
    return resolve_rip(p, hit, 3, 7);
}
```

## Pattern: Entity List Iteration with Null Guards

```cpp
void iterate_entities(proc_t& p, uint64 entity_list, int32 max_count) {
    for (int32 i = 0; i < max_count; i++) {
        uint64 ent = p.ru64(entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;

        // Read position (Source Engine typically stores as float32 vec3)
        vec3 pos = p.read_vec3_fl32(ent + OFFSET_POSITION);
        int32 health = p.r32(ent + OFFSET_HEALTH);
        int32 team = p.r32(ent + OFFSET_TEAM);

        if (health <= 0) continue;       // skip dead
        if (team == local_team) continue; // skip friendly

        // ... process entity
    }
}
```

## Pattern: World-to-Screen Projection (Source Engine 4x4 Matrix)

```cpp
// Source Engine stores the view-projection matrix as 16 floats (4x4, row-major)
bool world_to_screen(proc_t& p, uint64 matrix_addr, vec3 world, out vec2 screen) {
    // Read the 4 rows (w-component row is row 3)
    float64 w = p.rf32(matrix_addr + 12) * world.x
              + p.rf32(matrix_addr + 28) * world.y
              + p.rf32(matrix_addr + 44) * world.z
              + p.rf32(matrix_addr + 60);

    if (w < 0.001) return false; // behind camera

    float64 inv_w = 1.0 / w;

    float64 nx = (p.rf32(matrix_addr + 0)  * world.x
                + p.rf32(matrix_addr + 16) * world.y
                + p.rf32(matrix_addr + 32) * world.z
                + p.rf32(matrix_addr + 48)) * inv_w;

    float64 ny = (p.rf32(matrix_addr + 4)  * world.x
                + p.rf32(matrix_addr + 20) * world.y
                + p.rf32(matrix_addr + 36) * world.z
                + p.rf32(matrix_addr + 52)) * inv_w;

    float64 vw = get_view_width();
    float64 vh = get_view_height();

    screen = vec2(
        (vw * 0.5) + (nx * vw * 0.5),
        (vh * 0.5) - (ny * vh * 0.5)
    );
    return true;
}
```

## Pattern: 2D Box Overlay with Health Bar

```cpp
import "vec";
import "color";

void draw_entity_box(vec2 head_screen, vec2 feet_screen, float64 health_pct, string name) {
    color c_box = color(255, 50, 50, 200);
    color c_hp  = color(50, 255, 50, 200);
    color c_text = color(255, 255, 255, 255);
    color c_shadow = color(0, 0, 0, 180);

    float64 height = feet_screen.y - head_screen.y;
    float64 width = height * 0.4;
    float64 x = head_screen.x - width * 0.5;
    float64 y = head_screen.y;

    // Box
    draw_rect(vec2(x, y), vec2(width, height), c_box, 1.0, 0.0, 0);

    // Health bar (left side)
    float64 bar_h = height * health_pct;
    float64 bar_y = y + height - bar_h;
    draw_rect_filled(vec2(x - 4.0, bar_y), vec2(2.0, bar_h), c_hp, 0.0, 0);

    // Name text above box
    draw_text(name, vec2(head_screen.x, y - 14.0), c_text, get_font18(), 2, c_shadow, 1.0);
}
```

## Pattern: Snapline Drawing

```cpp
void draw_snapline(vec2 entity_screen) {
    float64 screen_w = get_view_width();
    float64 screen_h = get_view_height();
    vec2 bottom_center = vec2(screen_w * 0.5, screen_h);
    color c = color(255, 255, 255, 120);
    draw_line(bottom_center, entity_screen, c, 1.0);
}
```

## Pattern: Distance Calculation and Display

```cpp
float64 distance_3d(vec3 a, vec3 b) {
    float64 dx = a.x - b.x;
    float64 dy = a.y - b.y;
    float64 dz = a.z - b.z;
    return sqrt(dx*dx + dy*dy + dz*dz);
}

void draw_distance(vec2 screen_pos, float64 dist) {
    string text = format("{d}m", cast<int32>(dist / 39.37)); // units to meters
    color white = color(255, 255, 255, 200);
    draw_text(text, vec2(screen_pos.x, screen_pos.y + 12.0), white, get_font18(), 0, color(0,0,0,0), 0.0);
}
```

## Pattern: Angle Calculation (Atan2-Based)

```cpp
vec2 calc_angle(vec3 src, vec3 dst) {
    vec3 delta;
    delta.x = dst.x - src.x;
    delta.y = dst.y - src.y;
    delta.z = dst.z - src.z;
    float64 dist_xy = sqrt(delta.x * delta.x + delta.y * delta.y);
    float64 pitch = atan2(-delta.z, dist_xy) * (180.0 / 3.14159265);
    float64 yaw   = atan2(delta.y, delta.x) * (180.0 / 3.14159265);
    return vec2(pitch, yaw);
}

float64 angle_fov(vec2 current, vec2 target) {
    float64 dp = current.x - target.x;
    float64 dy = current.y - target.y;
    // Normalize yaw delta to [-180, 180]
    while (dy > 180.0)  dy = dy - 360.0;
    while (dy < -180.0) dy = dy + 360.0;
    return sqrt(dp*dp + dy*dy);
}
```

## Pattern: Smooth Angle Interpolation

```cpp
vec2 smooth_angle(vec2 current, vec2 target, float64 smooth_factor) {
    float64 dx = target.x - current.x;
    float64 dy = target.y - current.y;
    while (dy > 180.0)  dy = dy - 360.0;
    while (dy < -180.0) dy = dy + 360.0;
    return vec2(
        current.x + dx / smooth_factor,
        current.y + dy / smooth_factor
    );
}
```

## Pattern: GUI Menu with Config

```cpp
bool g_enabled = true;
float64 g_max_dist = 3000.0;
float64 g_smooth = 5.0;
int32 g_hotkey = 0x06; // VK_XBUTTON2
color g_color = color(255, 50, 50, 255);

void setup_menu() {
    int64 sec = create_section("Settings");
    section_checkbox(sec, "Enable", g_enabled);
    section_slider_float(sec, "Max Distance", g_max_dist, 100.0, 10000.0);
    section_slider_float(sec, "Smooth Factor", g_smooth, 1.0, 30.0);
    section_keybind(sec, "Hotkey", g_hotkey);
    section_color_picker(sec, "Overlay Color", g_color);
    section_separator(sec);
    section_label(sec, "v1.0");
}
```

## Pattern: Config Save/Load

```cpp
void save_config() {
    string cfg = "";
    cfg = cfg + "enabled=" + cast<string>(g_enabled) + "\n";
    cfg = cfg + "max_dist=" + cast<string>(g_max_dist) + "\n";
    cfg = cfg + "smooth=" + cast<string>(g_smooth) + "\n";
    write_file("config.txt", cfg);
}

void load_config() {
    if (!file_exists("config.txt")) return;
    string cfg = read_file("config.txt");
    // Parse key=value pairs
    array<string> lines = cfg.split("\n");
    for (string line : lines) {
        array<string> kv = line.split("=");
        if (kv.length() < 2) continue;
        string key = kv[0];
        string val = kv[1];
        if (key == "enabled")  g_enabled = val == "true" || val == "1";
        if (key == "max_dist") g_max_dist = val.to_float();
        if (key == "smooth")   g_smooth = val.to_float();
    }
}
```

## Pattern: Minimap / Radar

```cpp
void draw_radar(vec3 local_pos, float64 local_yaw, vec3[] positions, float64 radar_range) {
    color c_bg    = color(0, 0, 0, 150);
    color c_dot   = color(255, 50, 50, 255);
    color c_self  = color(50, 255, 50, 255);
    float64 radar_size = 150.0;
    float64 cx = 90.0;
    float64 cy = 90.0;

    // Background
    draw_rect_filled(vec2(cx - radar_size*0.5, cy - radar_size*0.5),
                     vec2(radar_size, radar_size), c_bg, 4.0, 15);

    // Self dot at center
    draw_circle(vec2(cx, cy), 3.0, c_self, 1.0, true);

    float64 yaw_rad = local_yaw * (3.14159265 / 180.0);

    for (int32 i = 0; i < positions.length(); i++) {
        float64 dx = positions[i].x - local_pos.x;
        float64 dy = positions[i].y - local_pos.y;

        // Rotate by -yaw so "up" on radar = forward
        float64 rx = dx * cos(-yaw_rad) - dy * sin(-yaw_rad);
        float64 ry = dx * sin(-yaw_rad) + dy * cos(-yaw_rad);

        // Scale to radar
        float64 scale = (radar_size * 0.5) / radar_range;
        float64 px = cx + rx * scale;
        float64 py = cy - ry * scale;

        // Clamp to radar bounds
        float64 half = radar_size * 0.5 - 4.0;
        if (px < cx - half) px = cx - half;
        if (px > cx + half) px = cx + half;
        if (py < cy - half) py = cy - half;
        if (py > cy + half) py = cy + half;

        draw_circle(vec2(px, py), 2.5, c_dot, 1.0, true);
    }
}
```

## Pattern: Complete Script Skeleton

```cpp
import "vec";
import "color";

// Globals
proc_t g_proc;
uint64 g_base;
uint64 g_size;
bool   g_running = false;

// Config (bound to GUI)
bool    g_enabled = true;
float64 g_max_distance = 3000.0;

void on_update(int64 data) {
    if (!g_enabled) return;
    if (!g_proc.alive()) return;
    // ... read game state into cache
}

void on_render(int64 data) {
    if (!g_enabled) return;
    // ... draw from cached state (no proc reads here)
}

int64 main() {
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) {
        println("Process not found");
        return 0;
    }
    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    if (g_base == 0) return 0;

    // Resolve offsets via pattern scans here
    // ...

    // Setup GUI
    int64 sec = create_section("My Script");
    section_checkbox(sec, "Enable", g_enabled);
    section_slider_float(sec, "Max Distance", g_max_distance, 0.0, 10000.0);

    // Register routines
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);

    g_running = true;
    return 1; // stay loaded
}
```

---

## Source: `knowledge/custom-draw-patterns.md`

# Custom Draw API Patterns for Perception.cx

Direct D3D11 GPU access from AngelScript/Enma. Write HLSL shaders, create
vertex/index/constant buffers, textures, render targets, and depth buffers,
then draw with any primitive topology. Custom draw commands respect draw
order with every existing render function.

> Resource creators return a `uint64` handle (`0` on failure). All resources
> are tracked per-script and auto-cleaned on script unload, so you create them
> once and reuse the handles every frame.

## Pattern: Basic 2D Colored Shape with Shader

Use case: a custom-shaded overlay primitive (gradient triangle, FOV wedge,
crosshair quad) that the built-in `draw_*` helpers can't express. Demonstrates
the minimal shader + vertex buffer + draw-call loop.

```cpp
// --- HLSL: vertex shader transforms 2D screen-space pos by an ortho matrix ---
string vs = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj); // 2D -> clip space
    o.col = i.col;
    return o;
}
""";

// --- HLSL: pixel shader just passes the interpolated vertex color ---
string ps = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

// Created ONCE (e.g. in on_load), reused every frame
uint64 g_shader = 0;
uint64 g_vb     = 0;
uint64 g_blend  = 0;

void cd_init_shape() {
    // layout: POSITION = float2, COLOR = float4 -> 24-byte stride
    g_shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    g_vb     = create_vertex_buffer(24, 3, true); // stride, max verts, dynamic
    g_blend  = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
}

void cd_draw_shape(float4x4 ortho) {
    // Interleaved vertex data: 3 verts x (pos.xy, col.rgba)
    array<float> verts = {
        100.0, 100.0,  1.0, 0.0, 0.0, 1.0,   // red
        300.0, 100.0,  0.0, 1.0, 0.0, 1.0,   // green
        200.0, 300.0,  0.0, 0.0, 1.0, 1.0    // blue
    };
    // proj matrix goes into constant buffer slot b0
    array<float> cb_data = ortho.to_array();

    custom_draw(g_shader, g_vb, verts, 3, TOPO_TRIANGLE_LIST,
                g_blend, 0, 0,        // no sampler/texture for solid color
                0,                    // rt=0 -> draw to backbuffer
                0, cb_data, 0);       // cb auto-managed, data, slot b0
}
```

## Pattern: Textured Quad with Custom Texture

Use case: render a logo, sprite sheet, watermark, or a CPU-generated image
onto a screen-space quad. Loads a texture, binds a sampler, and samples it in
the pixel shader.

```cpp
string vs_tex = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float2 uv : TEXCOORD; };
struct VS_OUT { float4 pos : SV_Position; float2 uv : TEXCOORD; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj);
    o.uv  = i.uv;
    return o;
}
""";

string ps_tex = """
Texture2D    tex : register(t0);
SamplerState smp : register(s0);
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target { return tex.Sample(smp, i.uv); }
""";

uint64 g_tex_shader = 0;
uint64 g_tex_vb     = 0;
uint64 g_tex        = 0;
uint64 g_sampler    = 0;
uint64 g_tex_blend  = 0;

void cd_init_textured() {
    g_tex_shader = create_shader(vs_tex, ps_tex, "POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2");
    g_tex_vb     = create_vertex_buffer(16, 6, true);  // float2 pos + float2 uv = 16 bytes
    g_tex        = create_texture_from_file("logo.png"); // RGBA from disk
    g_sampler    = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
    g_tex_blend  = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                      BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
}

void cd_draw_textured(float4x4 ortho, float64 x, float64 y, float64 w, float64 h) {
    float fx = float(x); float fy = float(y);
    float fw = float(w); float fh = float(h);
    // Two triangles forming a quad: (pos.xy, uv.xy)
    array<float> verts = {
        fx,      fy,      0.0, 0.0,
        fx + fw, fy,      1.0, 0.0,
        fx,      fy + fh, 0.0, 1.0,
        fx + fw, fy,      1.0, 0.0,
        fx + fw, fy + fh, 1.0, 1.0,
        fx,      fy + fh, 0.0, 1.0
    };
    array<float> cb_data = ortho.to_array();

    custom_draw(g_tex_shader, g_tex_vb, verts, 6, TOPO_TRIANGLE_LIST,
                g_tex_blend, g_sampler, g_tex, // bind sampler + texture
                0, 0, cb_data, 0);
}
```

## Pattern: 3D Cube with Depth Testing

Use case: render a true 3D object (debug box, chams cage, world marker) that
correctly occludes itself. Uses an index buffer to share cube corners, a
depth buffer, and a depth-stencil state with `CMP_LESS`.

```cpp
string vs_3d = """
cbuffer cb : register(b0) { float4x4 mvp; };
struct VS_IN  { float3 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 1), mvp); // model-view-projection
    o.col = i.col;
    return o;
}
""";

string ps_3d = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

uint64 g_cube_shader = 0;
uint64 g_cube_vb     = 0;
uint64 g_cube_ib     = 0;
uint64 g_depth_buf   = 0;
uint64 g_ds_state    = 0;
uint64 g_cube_blend  = 0;

void cd_init_cube(int32 vw, int32 vh) {
    g_cube_shader = create_shader(vs_3d, ps_3d, "POSITION:0:FLOAT3, COLOR:0:FLOAT4");
    g_cube_vb     = create_vertex_buffer(28, 8, false);   // float3 pos + float4 col = 28 bytes, 8 corners
    g_cube_ib     = create_index_buffer(36, false, false); // 12 tris * 3 = 36 indices, 16-bit
    g_depth_buf   = create_depth_buffer(vw, vh);
    g_ds_state    = create_depth_stencil_state(true, true, CMP_LESS); // depth on, write on
    g_cube_blend  = create_blend_state(BLEND_ONE, BLEND_ZERO, BLEND_OP_ADD,
                                       BLEND_ONE, BLEND_ZERO, BLEND_OP_ADD); // opaque
}

void cd_draw_cube(float4x4 mvp, int32 vw, int32 vh) {
    // 8 cube corners: (pos.xyz, col.rgba)
    array<float> verts = {
        -1,-1,-1, 1,0,0,1,   1,-1,-1, 0,1,0,1,
         1, 1,-1, 0,0,1,1,  -1, 1,-1, 1,1,0,1,
        -1,-1, 1, 1,0,1,1,   1,-1, 1, 0,1,1,1,
         1, 1, 1, 1,1,1,1,  -1, 1, 1, 0,0,0,1
    };
    // 12 triangles (two per face), CCW winding
    array<uint16> indices = {
        0,1,2, 0,2,3,   4,6,5, 4,7,6,   // back, front
        4,5,1, 4,1,0,   3,2,6, 3,6,7,   // bottom, top
        1,5,6, 1,6,2,   4,0,3, 4,3,7    // right, left
    };
    array<float> cb_data = mvp.to_array();

    // Bind a depth-enabled render target + clear it, then set depth state
    custom_set_render_target_ext(0, g_depth_buf); // 0 = backbuffer color
    custom_clear_depth_buffer(g_depth_buf);
    custom_set_depth_stencil_state(g_ds_state);
    custom_set_viewport(0, 0, vw, vh);

    custom_draw_indexed(g_cube_shader, g_cube_vb, verts, 28,
                        g_cube_ib, indices, 36, TOPO_TRIANGLE_LIST,
                        g_cube_blend, 0, 0, 0, 0, cb_data, 0);
}
```

## Pattern: Wireframe Rendering

Use case: debug visualization of geometry, hitbox cages, or a "skeleton"
look. Identical geometry path as the solid cube but with a rasterizer state
set to `FILL_WIREFRAME` so only triangle edges are drawn.

```cpp
// Reuses g_cube_shader / g_cube_vb / g_cube_ib / g_depth_buf from the 3D cube pattern.
uint64 g_rs_wire  = 0;
uint64 g_rs_solid = 0;

void cd_init_wireframe() {
    // Wireframe + no culling so back edges are visible too
    g_rs_wire  = create_rasterizer_state(FILL_WIREFRAME, CULL_NONE);
    g_rs_solid = create_rasterizer_state(FILL_SOLID, CULL_BACK); // to restore afterwards
}

void cd_draw_wireframe(float4x4 mvp, int32 vw, int32 vh) {
    array<float> verts = {
        -1,-1,-1, 0,1,0,1,   1,-1,-1, 0,1,0,1,
         1, 1,-1, 0,1,0,1,  -1, 1,-1, 0,1,0,1,
        -1,-1, 1, 0,1,0,1,   1,-1, 1, 0,1,0,1,
         1, 1, 1, 0,1,0,1,  -1, 1, 1, 0,1,0,1
    };
    array<uint16> indices = {
        0,1,2, 0,2,3,   4,6,5, 4,7,6,
        4,5,1, 4,1,0,   3,2,6, 3,6,7,
        1,5,6, 1,6,2,   4,0,3, 4,3,7
    };
    array<float> cb_data = mvp.to_array();

    custom_set_render_target_ext(0, g_depth_buf);
    custom_clear_depth_buffer(g_depth_buf);
    custom_set_depth_stencil_state(g_ds_state);
    custom_set_rasterizer_state(g_rs_wire);  // <-- switch to wireframe fill
    custom_set_viewport(0, 0, vw, vh);

    custom_draw_indexed(g_cube_shader, g_cube_vb, verts, 28,
                        g_cube_ib, indices, 36, TOPO_TRIANGLE_LIST,
                        g_cube_blend, 0, 0, 0, 0, cb_data, 0);

    custom_set_rasterizer_state(g_rs_solid); // restore so later draws are solid
}
```

## Pattern: Glow / Blur Post-Processing

Use case: a soft glow around overlay elements or a bloom effect. Render the
source into an off-screen render target, run a separable blur pass that
samples the RT, then composite the blurred result back over the backbuffer
with additive blending.

```cpp
// Fullscreen-triangle vertex shader (no vertex buffer needed; uses SV_VertexID)
string vs_fs = """
struct VS_OUT { float4 pos : SV_Position; float2 uv : TEXCOORD; };
VS_OUT main(uint id : SV_VertexID) {
    VS_OUT o;
    o.uv  = float2((id << 1) & 2, id & 2);            // 0,0 / 2,0 / 0,2
    o.pos = float4(o.uv * float2(2, -2) + float2(-1, 1), 0, 1);
    return o;
}
""";

// Separable Gaussian blur; direction passed via constant buffer (1,0)=horiz, (0,1)=vert
string ps_blur = """
Texture2D    src : register(t0);
SamplerState smp : register(s0);
cbuffer cb : register(b0) { float2 dir; float2 texel; };
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target {
    float w[5] = { 0.227, 0.194, 0.121, 0.054, 0.016 };
    float4 c = src.Sample(smp, i.uv) * w[0];
    for (int k = 1; k < 5; k++) {
        float2 off = dir * texel * k;
        c += src.Sample(smp, i.uv + off) * w[k];
        c += src.Sample(smp, i.uv - off) * w[k];
    }
    return c;
}
""";

// Additive composite of blurred RT over the backbuffer
string ps_composite = """
Texture2D    src : register(t0);
SamplerState smp : register(s0);
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target { return src.Sample(smp, i.uv); }
""";

uint64 g_blur_shader = 0;
uint64 g_comp_shader = 0;
uint64 g_rt_a = 0;
uint64 g_rt_b = 0;
uint64 g_blur_smp   = 0;
uint64 g_add_blend  = 0;
int32  g_rt_w = 0;
int32  g_rt_h = 0;

void cd_init_glow(int32 w, int32 h) {
    g_rt_w = w; g_rt_h = h;
    g_blur_shader = create_shader(vs_fs, ps_blur, "");       // no input layout
    g_comp_shader = create_shader(vs_fs, ps_composite, "");
    g_rt_a = create_render_target(w, h);  // ping
    g_rt_b = create_render_target(w, h);  // pong
    g_blur_smp  = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
    g_add_blend = create_blend_state(BLEND_ONE, BLEND_ONE, BLEND_OP_ADD, // additive
                                     BLEND_ONE, BLEND_ONE, BLEND_OP_ADD);
}

// `source_tex` is what you want to glow (e.g. a captured/rendered RT texture)
void cd_draw_glow(uint64 source_tex) {
    float tx = 1.0 / float(g_rt_w);
    float ty = 1.0 / float(g_rt_h);

    // Pass 1: horizontal blur, source_tex -> rt_a
    array<float> cb_h = { 1.0, 0.0, tx, ty };
    custom_clear_render_target(g_rt_a, 0, 0, 0, 0);
    custom_draw(g_blur_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                0, g_blur_smp, source_tex, g_rt_a, 0, cb_h, 0);

    // Pass 2: vertical blur, rt_a -> rt_b
    array<float> cb_v = { 0.0, 1.0, tx, ty };
    custom_clear_render_target(g_rt_b, 0, 0, 0, 0);
    custom_draw(g_blur_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                0, g_blur_smp, g_rt_a, g_rt_b, 0, cb_v, 0);

    // Pass 3: composite blurred rt_b additively onto the backbuffer (rt=0)
    custom_draw(g_comp_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                g_add_blend, g_blur_smp, g_rt_b, 0, 0, array<float>(), 0);
}
```

## Pattern: Compute Shader Data Processing

Use case: offload heavy per-element math to the GPU — batch world-to-screen
projection, particle simulation, or bulk distance/visibility checks. Creates
a compute shader, a structured buffer of input/output data, dispatches thread
groups, then reads the results back to the CPU.

```cpp
// Compute shader: multiplies every element by 2 (stand-in for real batch work)
string cs = """
RWStructuredBuffer<float> data : register(u0);
[numthreads(64, 1, 1)]
void main(uint3 id : SV_DispatchThreadID) {
    data[id.x] = data[id.x] * 2.0;
}
""";

uint64 g_compute = 0;

void cd_init_compute() {
    g_compute = create_compute_shader(cs);
}

array<float> cd_run_compute(array<float> input) {
    uint element_count = input.length();

    // 4-byte float elements; upload initial data
    uint64 buf = create_structured_buffer(4, element_count, input);

    // Each group handles 64 elements (matches numthreads); round up
    uint groups = (element_count + 63) / 64;
    dispatch_compute(g_compute, groups, 1, 1);

    // Read processed data back into an AngelScript array
    array<float> result = read_structured_buffer(buf);
    return result; // each element doubled
}
```

## Pattern: Multi-Pass Rendering with Multiple Render Targets

Use case: composing a final image from several layers — e.g. render solid
geometry to one RT, an outline/mask to another, then combine both in a final
fullscreen pass. Demonstrates rendering into separate targets and sampling
multiple textures in the composite shader.

```cpp
// Final composite samples two render-target textures and blends them
string ps_mrt_composite = """
Texture2D    sceneTex : register(t0);
Texture2D    maskTex  : register(t1);
SamplerState smp      : register(s0);
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target {
    float4 scene = sceneTex.Sample(smp, i.uv);
    float  mask  = maskTex.Sample(smp, i.uv).r;
    // Tint the masked region (outline) cyan, leave the rest as the scene
    float3 outline = float3(0, 1, 1) * mask;
    return float4(scene.rgb + outline, 1);
}
""";

uint64 g_mrt_comp_shader = 0;
uint64 g_rt_scene = 0;
uint64 g_rt_mask  = 0;
uint64 g_mrt_smp  = 0;

void cd_init_mrt(int32 w, int32 h) {
    g_mrt_comp_shader = create_shader(vs_fs, ps_mrt_composite, ""); // reuse fullscreen VS
    g_rt_scene = create_render_target(w, h);
    g_rt_mask  = create_render_target(w, h);
    g_mrt_smp  = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
}

void cd_draw_mrt(float4x4 mvp, array<float> scene_verts, array<float> mask_verts) {
    array<float> cb = mvp.to_array();

    // Pass 1: render the scene geometry into g_rt_scene
    custom_clear_render_target(g_rt_scene, 0, 0, 0, 1);
    custom_draw(g_cube_shader, g_cube_vb, scene_verts, 3, TOPO_TRIANGLE_LIST,
                g_cube_blend, 0, 0, g_rt_scene, 0, cb, 0);

    // Pass 2: render the mask/outline geometry into g_rt_mask
    custom_clear_render_target(g_rt_mask, 0, 0, 0, 1);
    custom_draw(g_cube_shader, g_cube_vb, mask_verts, 3, TOPO_TRIANGLE_LIST,
                g_cube_blend, 0, 0, g_rt_mask, 0, cb, 0);

    // Pass 3: composite both RTs onto the backbuffer.
    // custom_bind_textures binds extra texture slots (t0, t1, ...) for one shader.
    custom_bind_textures(g_mrt_comp_shader, g_rt_scene, g_rt_mask);
    custom_draw(g_mrt_comp_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                0, g_mrt_smp, g_rt_scene, 0, 0, array<float>(), 0);
}
```

## Pattern: Dynamic Texture Update

Use case: a CPU-generated image that changes every frame — a software-drawn
minimap, a spectrogram, a heatmap, or scrolling text. Create a dynamic
texture once, rewrite its RGBA pixel buffer each frame, then draw it with the
textured-quad path.

```cpp
// Reuses g_tex_shader / g_tex_vb / g_sampler / g_tex_blend from the textured-quad pattern.
uint64 g_dyn_tex = 0;
int32  g_dyn_w = 256;
int32  g_dyn_h = 256;

void cd_init_dynamic() {
    g_dyn_tex = create_dynamic_texture(g_dyn_w, g_dyn_h); // allocated once
}

// Builds a fresh RGBA8 buffer and uploads it. `t` animates the pattern.
void cd_update_dynamic(float64 t) {
    array<uint8> pixels(g_dyn_w * g_dyn_h * 4); // 4 bytes per pixel (RGBA)

    for (int32 y = 0; y < g_dyn_h; y++) {
        for (int32 x = 0; x < g_dyn_w; x++) {
            int32 idx = (y * g_dyn_w + x) * 4;
            // Simple animated plasma so the update is visible per-frame
            uint8 r = uint8((sin(x * 0.05 + t) * 0.5 + 0.5) * 255.0);
            uint8 g = uint8((sin(y * 0.05 + t) * 0.5 + 0.5) * 255.0);
            uint8 b = uint8((sin((x + y) * 0.05 + t) * 0.5 + 0.5) * 255.0);
            pixels[idx + 0] = r;
            pixels[idx + 1] = g;
            pixels[idx + 2] = b;
            pixels[idx + 3] = 255; // opaque
        }
    }

    update_dynamic_texture(g_dyn_tex, pixels); // re-upload to GPU
}

void cd_draw_dynamic(float4x4 ortho, float64 x, float64 y) {
    float fx = float(x); float fy = float(y);
    float fw = float(g_dyn_w); float fh = float(g_dyn_h);
    array<float> verts = {
        fx,      fy,      0.0, 0.0,
        fx + fw, fy,      1.0, 0.0,
        fx,      fy + fh, 0.0, 1.0,
        fx + fw, fy,      1.0, 0.0,
        fx + fw, fy + fh, 1.0, 1.0,
        fx,      fy + fh, 0.0, 1.0
    };
    array<float> cb_data = ortho.to_array();

    custom_draw(g_tex_shader, g_tex_vb, verts, 6, TOPO_TRIANGLE_LIST,
                g_tex_blend, g_sampler, g_dyn_tex, // bind the dynamic texture
                0, 0, cb_data, 0);
}
```

---

## Source: `knowledge/enma-cheatsheet.md`

# Enma Language Quick Reference

## Primitives

| Type | Size | Notes |
|------|------|-------|
| `bool` | 1B | `true` / `false` |
| `char` / `wchar` | 1B / 2B | ASCII / wide |
| `int8/16/32/64` | 1-8B | Signed |
| `uint8/16/32/64` | 1-8B | Unsigned |
| `aint8/16/32/64` | 1-8B | Atomic |
| `float32` / `float64` | 4B / 8B | IEEE single/double |
| `string` / `wstring` | ptr | UTF-8 / UTF-16 heap |
| `void` / `null` / `auto` | - | No value / null literal / inferred |

## Conversion Rules (COMPILE-TIME ENFORCED)

- `signed ↔ unsigned` → **COMPILE ERROR** — use `cast<uint64>(x)`
- `float → int` → **COMPILE ERROR** — use `cast<int32>(f)`
- `int → float` → implicit OK
- `float32 → float64` → implicit OK
- `float64 → float32` → **COMPILE ERROR** — use `cast<float32>(d)`
- `pointer ↔ int64/uint64` → implicit (both 8-byte)

## Variables

```cpp
int32 x = 42;
const float64 PI = 3.14;           // runtime-initialized, not reassignable
constexpr int32 MAX = 100;          // compile-time only
auto y = x + 1;                     // inferred
nullable int32 n = null;            // can hold null
```

## Operators

Arithmetic: `+ - * / %`  |  Comparison: `== != < > <= >=`  |  Logical: `&& || !`
Bitwise: `& | ^ ~ << >>`  |  Compound: `+= -= *= /= %= &= |= ^= <<= >>=`
Inc/Dec: `++ --`  |  Ternary: `cond ? a : b`  |  Cast: `cast<T>(x)`
Size: `sizeof(T)` `offsetof(Struct, field)`  |  Heap: `new T(args)` `delete`

## Control Flow

```cpp
if (x > 0) { } else if (x == 0) { } else { }
while (x > 0) x--;
do { x++; } while (x < 10);
for (int32 i = 0; i < 10; i++) { }
for (int32 v : arr) { }                          // for-each
for (string k, int64 v : m) { }                  // map for-each
switch (x) { case 1: break; default: break; }
int32 r = match (x) { 1 => 10, 2 => 20, _ => 0 };
defer { cleanup(); }                              // runs at scope exit
goto label; label: /* ... */
```

## Functions

```cpp
int32 add(int32 a, int32 b = 10) { return a + b; }   // default param
void swap(int32& a, int32& b) { /* pass by ref */ }   // reference
bool parse(string s, out int32 v) { /* write-only out */ }
void log(string fmt, ...) { /* variadic */ }
auto fn = (int32 x) => x * 2;                         // lambda
auto fn2 = [&cap](int32 x) -> int32 { return cap + x; }; // closure
```

## Structs (value types) vs Classes (reference types)

```cpp
struct Vec2 { float64 x; float64 y; }   // stack-allocated, copied on assign
class Player {                            // heap-allocated via new, virtual dispatch
    int32 health;
    Player(int32 h) { health = h; }
    virtual void update() { }
}
interface IDrawable { void draw(); }
mixin Logging for Player { void log() { println("hp=" + cast<string>(health)); } }
```

## Templates

```cpp
template<typename T>
T max(T a, T b) { return a > b ? a : b; }
template<typename T>
struct Stack { T[] items; void push(T v) { items.push(v); } }
```

## Arrays & Maps

```cpp
int32[] arr = {1, 2, 3};
arr.push(4); arr.pop(); arr.sort(); arr.reverse();
arr.contains(2); arr.index_of(3); arr.slice(0, 2);
arr.length(); arr.remove(0); arr.insert(1, 99);

map<string, int64> m;
m["key"] = 42; m.get("key"); m.contains("key");
m.remove("key"); m.length();
```

## Strings

```cpp
string s = f"value={x}";                         // interpolation
string h = format("addr=0x{x} name={s}", addr, name);  // format
s.length(); s.substr(0, 5); s.find("abc");
s.contains("x"); s.starts_with("pre"); s.ends_with("suf");
s.to_upper(); s.to_lower(); s.trim(); s.replace("a","b");
s.split(","); s.to_int(); s.to_float();
```

## Pointers

```cpp
int32* p = new int32(42);    // heap alloc
int32 v = *p;                // dereference (shallow copy)
delete p;                     // free
int32 x = 5; int32* px = &x; // address-of
Player* pl = new Player(100);
pl->update();                 // member access via pointer
```

## Coroutines

```cpp
coroutine int32 counter() { int32 i = 0; while (true) { yield i; i++; } }
coroutine_t c = counter();
c.next(); int32 v = c.value();
```

## Exceptions

```cpp
try { throw "error"; }
catch (string e) { println(e); }
// dtors and defer blocks run during stack unwinding
```

## Modules & Preprocessor

```cpp
import "math";                    // import module
import "utils" as u;              // aliased
using namespace MyLib;            // bring names into scope

#define DEBUG
#ifdef DEBUG
  println("debug mode");
#endif
#include "shared.em"
```

## Annotations

```cpp
[[packed]] struct Data { uint8 a; uint32 b; }     // no padding
[[align(16)]] struct Aligned { float32 v[4]; }
[[reflect]] struct Config { int32 x; }             // queryable from host
[[dll("user32.dll")]] extern int32 MessageBoxA(/*...*/);  // FFI
[[noopt]] void sensitive() { }                      // skip optimization
[[export]] void api_func() { }                      // visible to host
```

---

## Source: `knowledge/gui-design-patterns.md`

# GUI Design Patterns

The Perception.cx sidebar GUI is a fixed-width vertical strip. Good layouts make features discoverable, tunings easy to find, and state visible at a glance. The 12 game-cheat-guidelines say "GUI for every tunable" (rule #11), but say nothing about how to lay it out well. This file fills that gap with section-organization patterns, widget order, label conventions, slider range discipline, hotkey conventions, color discipline, conditional widgets, state visibility, and the anti-patterns to avoid.

> **Read this before** designing a new feature's GUI section, or auditing an existing one. Pair with `templates/overlay-basic.em` (small example) and `templates/full-project/` (multi-feature example) for working code.

---

## Section Organization: One Feature Per Section

**Mirrors `game-cheat-guidelines` rule #6 (one feature per file). The GUI shape follows the code shape.**

The sidebar is composed of independent sections — `create_section("ESP")`, `create_section("Aimbot")`, `create_section("Radar")`. Each section is collapsible by the user. Users disable a feature *socially* by collapsing its section ("I'm not using radar today; collapse it"); mixing concerns inside one section defeats the affordance.

```cpp
// RIGHT — one feature per section
int64 sec_esp    = create_section("ESP");
int64 sec_aim    = create_section("Aimbot");
int64 sec_radar  = create_section("Radar");
int64 sec_misc   = create_section("Misc");

// WRONG — all features in one section
int64 sec_all = create_section("Features");  // user has to scroll past 40 widgets
```

The exception: tiny features (a single checkbox) that don't justify their own section header. Group them under a `Misc` section at the bottom. The rule is one *feature* per section, not one widget — a section with 6-10 widgets is normal.

**Why:** Collapsibility is the discoverability mechanism. Mixing makes the sidebar a wall of widgets that the user scans linearly; separating makes it a directory the user can collapse-and-skip.

---

## Widget Order Within a Section

**Canonical order: master toggle → hotkey → primary tuning → secondary tunings → color picker(s) → separator → status label.**

Users scan top-to-bottom. The widget order reflects the frequency of interaction: the master toggle is touched most often (turn the feature on/off), the status label is glanced at most often (is it working?). Put both where the eye naturally lands.

```cpp
int64 sec = create_section("ESP");

// 1. Master toggle — top of section, always.
section_checkbox(sec, "Enabled", g_esp_enabled);

// 2. Hotkey — the second-most-touched widget after the toggle.
section_keybind(sec, "Toggle hotkey", g_esp_hotkey);

// 3. Primary tuning — the most-used slider or combo.
section_combo(sec, "Mode", g_esp_mode, "Box,Skeleton,Both");

// 4. Secondary tunings — less-frequent.
section_slider_float(sec, "Max distance", g_esp_max_dist, 0.0, 500.0);
section_slider_int(sec, "Line thickness", g_esp_thickness, 1, 5);
section_checkbox(sec, "Show distance label", g_esp_show_dist);

// 5. Color pickers — group at the end so the color noise doesn't dominate.
section_color_picker(sec, "Friendly", g_esp_color_friendly);
section_color_picker(sec, "Enemy",    g_esp_color_enemy);

// 6. Separator — visually break "controls" from "diagnostics".
section_separator(sec);

// 7. Status label — what is the feature doing right now?
section_label(sec, "Drawing 12 entities (3 friendly, 9 enemy)");
```

(The status label text is updated each frame from the render routine — the API takes a `string`, so build it with `format(...)` against your cached counts.)

The order isn't sacred (a feature with no hotkey skips that slot), but the *gravity* is: most-touched at the top, diagnostics at the bottom.

**Why:** A GUI that lets the user find the toggle in 200ms is one they actually use. A GUI where the user has to scroll past four color pickers to find the toggle is one they fight with.

---

## Label Conventions

**Imperative for toggles, units in slider labels, no jargon.**

```cpp
// RIGHT — clear, scannable, action-oriented
section_checkbox(sec, "Show ESP", g_esp_enabled);
section_slider_float(sec, "Smoothing (frames)", g_aim_smoothing, 0.0, 15.0);
section_slider_int(sec, "Max distance (meters)", g_esp_max_dist, 0, 500);
section_combo(sec, "Target priority", g_target_mode, "Closest,Lowest HP,Crosshair");

// WRONG — past-tense, abbreviated, unit-less
section_checkbox(sec, "ESP enabled", g_esp_enabled);          // past-tense state
section_slider_float(sec, "SM", g_aim_smoothing, 0, 15);      // what is SM?
section_slider_int(sec, "Dist", g_esp_max_dist, 0, 500);      // dist in what?
section_combo(sec, "Pri", g_target_mode, "C,L,X");            // unreadable
```

Imperative phrasing reads as a button label: "Show ESP" / "Hide ESP" maps directly to the checkbox state. "ESP enabled" makes the user parse a sentence to know what clicking it does.

Units in slider labels save support questions. "Smoothing" is ambiguous (frames? seconds? ticks?). "Smoothing (frames)" is not.

Abbreviations are fine when they're industry-standard (FOV, ESP, HP, AC); not fine when they're project-internal (AB for aimbot, SM for smoothing). The rule of thumb: would a Discord support request use this abbreviation? If yes, ship it. If you'd have to expand it on first use in a support reply, expand it in the label.

**Why:** A label is the entire UX of a widget. A clear label is self-documenting; an unclear one needs a doc the user won't read.

---

## Slider Ranges: Useful, Not Possible

**Set min/max to the *useful* range, not the *possible* range. A smoothing slider's useful range is 0..15; setting it 0..1000 makes the useful range one pixel wide.**

The slider widget maps the entire visible track to the `[min, max]` interval. If the useful range is 0..15 and the slider is 0..1000, the user can only meaningfully tune in the first 1.5% of the track, and dragging past that produces values that don't change behavior (or, worse, crash).

```cpp
// WRONG — possible range, useless slider
section_slider_float(sec, "Smoothing", g_aim_smoothing, 0.0, 1000.0);
section_slider_int(sec, "FOV (px)", g_aim_fov, 0, 10000);
section_slider_float(sec, "Max distance (m)", g_max_dist, 0.0, 100000.0);

// RIGHT — useful range, every drag matters
section_slider_float(sec, "Smoothing", g_aim_smoothing, 0.0, 15.0);
section_slider_int(sec, "FOV (px)", g_aim_fov, 8, 400);
section_slider_float(sec, "Max distance (m)", g_max_dist, 0.0, 500.0);
```

How to pick useful ranges:

- Measure or estimate the *real* range your feature operates in (smoothing past 15 frames is sluggish; aimbot FOV past 400px is "aim at the whole screen").
- Add 20-50% headroom past the practical upper bound (the user might want to go higher than you expect).
- Set the minimum to the smallest sensible value (0 if the feature can be disabled by the slider; 1 if it needs at least some value to function).

When the truly useful range is dynamic (depends on game state — e.g. max-distance varies between a small arena and a large open world), pick a static range that covers the wider case and document it in a comment.

**Why:** A slider's value is the area where it's draggable. A 0..1000 slider for a 0..15 problem is a configuration error, not a feature.

---

## Defaults That Work for First-Time Users

**Ship the tuning a new user would want, not the tuning you've personally settled on.**

The first time a user loads the script, every widget has its default value. If the defaults are bad, the script appears broken and the user gives up before reaching the GUI to fix them.

| Widget | Bad default | Good default |
|---|---|---|
| `g_esp_enabled` | `false` (user has to find the toggle) | `true` (user sees the feature immediately) |
| `g_esp_color` | `color(0, 0, 0, 255)` (invisible on dark UI) | `color(255, 50, 50, 255)` (red, contrasts with most game UIs) |
| `g_aim_smoothing` | `0.0` (instant snap — detection vector + jarring) | `8.0` (perceptibly smooth, still useful) |
| `g_aim_hotkey` | (no default) | Right-mouse-button (industry convention for "aim assist") |
| `g_aim_fov` | `1000.0` (whole screen) | `60.0` (focused, sane starting point) |
| `g_esp_max_distance` | `0.0` (draws nothing) | `200.0` (covers most engagements) |
| `g_radar_radius` | `40.0` (too small to read) | `90.0` (readable on 1080p+ displays) |

The pre-ship hygiene check (`tools/pre-ship-check.sh`) does NOT catch bad defaults — they look like normal values to grep. Reviewers must consciously test the fresh-config experience: delete your saved config, restart the script, verify it does something visible without any user tuning.

**Why:** Defaults are the product. A user who has to tune 20 widgets before the feature works will conclude the feature doesn't work. The two minutes you spend picking defaults that work for a first-time user pay back in every install.

---

## Hotkey Conventions

**Don't bind features to letter keys the game uses (WASD, R, E, F, Q). Provide a `section_keybind` widget for every hotkey — hardcoded hotkeys are rule-#11 violations.**

Safe default hotkeys, ordered by convention:

| Action | Conventional default |
|---|---|
| Toggle aim assist (hold) | Right Mouse Button (`VK_RBUTTON`) — industry standard |
| Toggle aim assist (toggle) | `F1` or `Mouse5` (`XBUTTON2`) |
| Open / close menu | `Insert` (PCX default) or `End` |
| Toggle ESP | `F2` |
| Toggle radar | `F3` |
| Misc feature toggles | `F4` – `F11` |
| Panic / hide all overlays | `End` or `\` |
| Reload sigs | `Home` (rare, RE-only utility) |
| Snapshot for debugging | `Pause` |

What to NEVER use:
- `WASD` — movement keys
- `Q`, `E`, `R`, `F` — typical ability / interact keys
- `Space`, `Shift`, `Ctrl`, `Alt` — modifier keys the game routes
- `1`–`0` — weapon swap / hotbar
- `Escape` — game-menu trigger
- `~` — chat or console
- Mouse4 / Mouse5 — generally OK, but check; some games bind these

Every hotkey is exposed as a `section_keybind` widget so the user can rebind:

```cpp
// RIGHT — hotkey is configurable
int64 g_esp_hotkey = vk::f2;
section_keybind(sec, "ESP toggle", g_esp_hotkey);

void on_update(int64 data) {
    if (key_fired(g_esp_hotkey)) {
        g_esp_enabled = !g_esp_enabled;
    }
}

// WRONG — hardcoded hotkey, user can't rebind
void on_update(int64 data) {
    if (key_fired(vk::f2)) {
        g_esp_enabled = !g_esp_enabled;
    }
}
```

`key_fired` is edge-triggered (true once per press); `key_down` is level-triggered (true while held). Toggles use fired; hold-to-activate uses down.
**Why:** Hotkey conflicts kill scripts. The user reports "the script doesn't work" — actually the script's `F` hotkey collides with the game's interact key, and pressing it both triggers the script and opens a door. Configurable hotkeys eliminate the entire class of report.

---

## Color Discipline

**Every drawable color is GUI-tunable (per rule #11). The discipline: a small palette per feature (FG / BG / accent) rather than per-pixel colors.**

A feature with 12 distinct hardcoded colors is one the user can't recolor for high-contrast, colorblind-friendly, or stream-friendly use. A feature with 3-4 tunable palette slots is one the user can adapt.

```cpp
// RIGHT — small palette, all tunable
color g_esp_friendly = color(60, 170, 255, 255);
color g_esp_enemy    = color(255, 60, 60, 255);
color g_esp_text     = color(255, 255, 255, 255);
color g_esp_outline  = color(0, 0, 0, 180);

int64 sec = create_section("ESP");
section_color_picker(sec, "Friendly",  g_esp_friendly);
section_color_picker(sec, "Enemy",     g_esp_enemy);
section_color_picker(sec, "Text",      g_esp_text);
section_color_picker(sec, "Outline",   g_esp_outline);

// In render — pull from the palette, never construct ad-hoc colors:
void on_render(int64 data) {
    for (int32 i = 0; i < g_count; i++) {
        color box = g_cache[i].friendly ? g_esp_friendly : g_esp_enemy;
        draw_rect(g_cache[i].screen_pos, g_cache[i].screen_size,
                  box, 1.5, 0.0, 15);
    }
}

// WRONG — hardcoded per-call colors
void on_render(int64 data) {
    for (int32 i = 0; i < g_count; i++) {
        draw_rect(g_cache[i].screen_pos, g_cache[i].screen_size,
                  color(255, 0, 0, 255),   // hardcoded red
                  1.5, 0.0, 15);
    }
}
```

Community conventions for color roles:

| Role | Conventional color |
|---|---|
| Friendly / teammate | Blue (`60, 170, 255`) or Green (`60, 220, 100`) |
| Enemy | Red (`255, 60, 60`) or Yellow (`255, 200, 50`) |
| Neutral / NPC / object | Gray (`180, 180, 180`) |
| Important / priority target | Magenta (`255, 60, 255`) or Bright Orange (`255, 140, 0`) |
| Hostile NPC (distinct from enemy player) | Dark red (`140, 30, 30`) or Crimson |
| Loot / pickup | Yellow (`255, 220, 80`) or Gold |

These are conventions, not laws — users will adjust. The point is to ship defaults that match what most users expect from prior cheats / games, so the first impression makes visual sense.

**Why:** Colors are accessibility. ~8% of male users have some form of red-green color blindness; ship colors they can tell apart, and let users override them if your defaults don't work for them.

---

## State Visibility

**A small label at the bottom of each section showing the runtime state. When users report "the script isn't working," the first thing they read is the state label.**

The state label closes the support loop before it opens. Without it, a user with a broken script reaches for Discord; with it, the user reads "0 entities (sig scan failed)" and knows the problem is the sig, not the feature.

```cpp
// In render — build status from cached state, update each frame
void on_render(int64 data) {
    // ... drawing ...

    // Status label — built from cached state
    string status;
    if (!g_proc.alive()) {
        status = "process not attached";
    } else if (g_entity_list == 0) {
        status = "sig scan failed (entity_list)";
    } else if (g_ent_count == 0) {
        status = "0 entities (in menu?)";
    } else {
        status = format("{d} entities ({d} friendly, {d} enemy)",
                        g_ent_count, g_ent_friendly_count, g_ent_enemy_count);
    }
    section_label(sec, status);
}
```

The status should:
- Always be visible (don't gate on `g_enabled` — the user wants status even when the feature is off)
- Use plain English (no internal error codes)
- Differentiate the common failure modes from "working fine"
- Include a count or sample value when the feature is working (proves it)

For features that have multiple status dimensions (aimbot: "no target / target locked: enemy_42 / smoothing: 8 frames"), one label is enough — `format` them together.

**Why:** The status label is the support burden's lightning rod. A user who can read the status doesn't ask in Discord; a user who can't, does.

---

## Conditional Widgets

**If widget B only makes sense when widget A is enabled, hide or gray out B when A is off.**

PCX's GUI API may or may not expose disable-state styling natively — check `docs/perception/gui-api.md` for the available widget states. If a disable-state is available, use it; if not, fall back to *conditionally creating* the dependent widgets, or document the dependency with a comment.

```cpp
// PATTERN 1 — if PCX supports a `section_*_disabled` variant or visibility flag,
// use it (check docs):
section_checkbox(sec, "Aim assist",  g_aim_enabled);
// Hypothetical: section_set_enabled(g_aim_smoothing_widget, g_aim_enabled);

// PATTERN 2 — fall-back: only create the dependent widget when the
// parent is enabled, on a per-frame basis. PCX GUI API permitting,
// recreate-per-frame is fine; if not, fall back to PATTERN 3.

// PATTERN 3 — universal fall-back: keep the widgets always created,
// but make the dependency explicit in the label and ignore the value
// at runtime when the parent is off:
section_checkbox(sec, "Aim assist", g_aim_enabled);
section_slider_float(sec, "Smoothing (needs Aim assist)",
                     g_aim_smoothing, 0.0, 15.0);
// In on_update: read g_aim_smoothing only inside `if (g_aim_enabled)`.
```

The labeled-dependency pattern (#3) is uglier than gray-out but always works. Use the prettier patterns when PCX exposes them; document with a `// requires: g_aim_enabled` comment either way.

**Why:** A user enabling smoothing without realizing aim assist is off, then concluding "the script is broken," is the exact kind of confused-customer report a 12-character label change prevents.

---

## Don't Ship a Debug Panel by Default

**A separate "Debug" section with profiler readouts and address dumps is great for development; hide or remove for release. The pre-ship checklist catches this.**

```cpp
// During development
int64 sec_debug = create_section("Debug");
section_label(sec_debug, format("entity_list: 0x{x}", g_entity_list));
section_label(sec_debug, format("local_player: 0x{x}", g_local_player));
section_label(sec_debug, format("entity count: {d}", g_ent_count));
section_label(sec_debug, format("update_us: {d}", g_avg_update_us));
section_label(sec_debug, format("render_us: {d}", g_avg_render_us));

// Before shipping — either remove the section entirely, or gate it
// behind a build flag / runtime "Show debug" checkbox in Misc.
#if DEBUG
    int64 sec_debug = create_section("Debug");
    // ... debug widgets ...
#endif
```

(PCX's preprocessor supports `#if`/`#ifdef`; see `docs/enma/lang-pre-processor.md`.)

The recipient of a shipped script does not need to see your internal address layout, your profiler bucket timings, or your sig-resolution status. Worse, debug info exposes the script's internals to anyone watching over the recipient's shoulder, which is bad for both privacy and competitive dynamics.

When shipping with a "Show debug" toggle (the gentler approach), default it off, and document in the README that flipping it on reveals diagnostic info useful only for support tickets.

**Why:** Debug surfaces are for the author, not the user. Shipping them on by default is leaking implementation; shipping them gated off (with documentation) is offering a support feature without imposing it.

---

## Persistence (Cross-Reference)

The GUI state must be persisted across script reloads — the user doesn't want to retune sliders every time. See `knowledge/script-organization-patterns.md` section "Config persistence pattern" for the JSON-to-disk pattern, and `.claude/skills/script-bundler/SKILL.md` for when to save (on each widget change, on a debounced timer, or on a save hotkey).

The relevant `fs_*` and `json_*` APIs are in `docs/perception/file-api.md` and `docs/enma/addon-json.md`. The summary: read on `main()` startup, write on a save hotkey or a debounced timer.

---

## Worked Example: A Well-Laid-Out ESP Section

```cpp
import "vec";
import "color";

// ── Config (GUI-bound; persisted to disk by main()) ──
bool   g_esp_enabled       = true;            // default ON (rule: defaults that work)
int32  g_esp_hotkey        = 0x71;            // VK_F2 toggle
int32  g_esp_mode          = 0;               // 0=box, 1=skeleton, 2=both
float64 g_esp_max_dist     = 200.0;
int32  g_esp_thickness     = 2;
bool   g_esp_show_distance = true;
color  g_esp_color_friendly = color(60, 170, 255, 255);   // blue convention
color  g_esp_color_enemy    = color(255, 60, 60, 255);    // red convention
color  g_esp_color_outline  = color(0, 0, 0, 180);

// ── Runtime state (status label reads these) ──
int32 g_esp_count_drawn    = 0;
int32 g_esp_count_friendly = 0;
int32 g_esp_count_enemy    = 0;
string g_esp_status_text   = "initializing";

int64 setup_esp_gui() {
    int64 sec = create_section("ESP");

    // 1. Master toggle (top)
    section_checkbox(sec, "Show ESP", g_esp_enabled);
    // 2. Hotkey
    section_keybind(sec, "Toggle hotkey", g_esp_hotkey);
    // 3. Primary tuning
    section_combo(sec, "Mode", g_esp_mode, "Box,Skeleton,Both");
    // 4. Secondary tunings (useful ranges, not possible ranges)
    section_slider_float(sec, "Max distance (m)", g_esp_max_dist, 0.0, 500.0);
    section_slider_int(sec, "Line thickness (px)", g_esp_thickness, 1, 5);
    section_checkbox(sec, "Show distance label", g_esp_show_distance);
    // 5. Color pickers (palette, not per-pixel)
    section_color_picker(sec, "Friendly", g_esp_color_friendly);
    section_color_picker(sec, "Enemy",    g_esp_color_enemy);
    section_color_picker(sec, "Outline",  g_esp_color_outline);
    // 6. Separator
    section_separator(sec);
    // 7. Status label (always-visible feedback)
    section_label(sec, g_esp_status_text);

    return sec;
}
```

This is 12 widgets in 7 logical roles. A user scanning this section knows in seconds: "ESP is on (toggle), F2 toggles it (keybind), it's drawing boxes (mode), out to 200m (distance), in blue/red (palette), and right now is drawing 12 entities (status)."

---

## Anti-Patterns

Flat list — each is a real failure mode that ships in scripts and gets reported:

- **All features in one section.** Sidebar becomes a wall of widgets; users can't collapse-and-skip.
- **Hotkeys hardcoded.** User can't rebind, hotkey collides with a game key, support ticket follows.
- **Slider ranges 0..1000 for 0..15 problems.** Slider is unusable for the actual range.
- **No master toggle.** User can't disable the feature without quitting the script.
- **`color()` / `vec2()` globals at file scope.** Per-frame construction rule (#7) violated; harder to recolor.
- **Labels "foo" / "bar" / "new feature".** Self-evident at write time, opaque a week later.
- **Defaults of 0 / false on user-facing toggles.** Script appears broken on fresh install.
- **No status label.** Every support ticket reads "the script isn't working" with no diagnostic info.
- **Debug section always visible in release.** Leaks internals; clutters the UX.
- **All widgets enabled regardless of dependencies.** User enables smoothing without aim assist on, concludes script is broken.
- **No section separators.** Every section looks the same; visual fatigue.
- **Tooltips encoded into labels.** "Smoothing (higher = smoother, lower = snappier, default 8)" doesn't fit; use a separator + label below instead, or a dedicated `Help` section.

---

## Cross-References

- `docs/perception/gui-api.md` — the authoritative widget API for your PCX version
- `templates/overlay-basic.em` — a working small-overlay GUI
- `templates/full-project/` — the multi-feature project scaffold
- `knowledge/common-patterns.md` — Enma code patterns that consume the widget values
- `knowledge/script-organization-patterns.md` — the persistence pattern, the menu-vs-feature split
- `.claude/skills/game-cheat-guidelines/SKILL.md` rules #6 (one feature per file) and #11 (GUI for every tunable)
- `.claude/skills/script-bundler/SKILL.md` — the pre-ship hygiene checklist that includes "sensible GUI defaults"
- `.claude/skills/ai-pair-programming/SKILL.md` — technique #6 for diff-reviewing AI-generated GUI code

---

## Source: `knowledge/pcx-api-cheatsheet.md`

# Perception.cx Enma API Quick Reference

All natives are auto-registered. No import needed (except `import "vec"; import "color";` for those types).

## Proc API — Process Memory

```cpp
proc_t p = ref_process("game.exe");       // by name
proc_t p = ref_process(1234);              // by PID
bool alive = p.alive();
uint64 base = p.base_address();
uint64 peb  = p.peb();
uint32 pid  = p.pid();
bool valid  = p.is_valid_address(addr);
```

### Read Primitives
```cpp
uint8/16/32/64  p.ru8/ru16/ru32/ru64(uint64 addr);
int8/16/32/64   p.r8/r16/r32/r64(uint64 addr);
float32         p.rf32(uint64 addr);
float64         p.rf64(uint64 addr);
string          p.rs(uint64 addr, int32 max_chars);    // ASCII
string          p.rws(uint64 addr, int32 max_chars);   // UTF-16→UTF-8
array<uint8>    p.rvm(uint64 addr, uint64 size);       // bulk
```

### Write Primitives (gated: `write_memory`)
```cpp
bool p.wu8/wu16/wu32/wu64(uint64 addr, uintN v);
bool p.w8/w16/w32/w64(uint64 addr, intN v);
bool p.wf32(uint64 addr, float32 v);
bool p.wf64(uint64 addr, float64 v);
bool p.wvm(uint64 addr, array<uint8> bytes);
```

### Typed Reads (vec/quat/mat)
```cpp
vec2 p.read_vec2_fl32(uint64 addr);     // also: _fl64 variant
vec3 p.read_vec3_fl32(uint64 addr);
vec4 p.read_vec4_fl32(uint64 addr);
quat p.read_quat_fl32(uint64 addr);
mat4 p.read_mat4_fl32(uint64 addr);
// write variants: p.write_vec3_fl32(addr, v), etc. (gated)
```

### Modules
```cpp
uint64                base = p.get_module_base("module.dll");
uint64                size = p.get_module_size("module.dll");
array<module_info_t>  mods = p.get_module_list();
uint64                exp  = p.get_proc_address(base, "ExportName");
uint64                imp  = p.get_import_rdata_address(base, "ImportName");
// module_info_t: .name(), .base(), .size()
```

### Pattern Scanning
```cpp
uint64 hit = p.find_code_pattern(start, size, "48 8B 05 ?? ?? ?? ?? 48 85 C0");
array<uint64> hits = p.find_all_code_patterns(start, size, sig);
```

### Memory Scanning
```cpp
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
array<uint64> p.scan_u64(value, heap_only);
array<uint64> p.scan_u32(value, heap_only);
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
```

### VAD / Virtual Query
```cpp
vad_region_t r = p.virtual_query(addr);       // .start(), .size(), .protection()
array<vad_region_t> snap = p.get_vad_snapshot(heap_only);
```

### VM Alloc/Free (gated: `virtual_memory_operations`)
```cpp
uint64 page = p.alloc_vm(4096);
bool ok = p.free_vm(page);
```

## Render API — 2D Drawing

```cpp
import "vec";
import "color";

// Primitives
draw_line(vec2 a, vec2 b, color c, float64 thickness);
draw_rect(vec2 pos, vec2 size, color c, float64 thickness, float64 rounding, uint8 flags);
draw_rect_filled(vec2 pos, vec2 size, color c, float64 rounding, uint8 flags);
draw_circle(vec2 center, float64 radius, color c, float64 thickness, bool filled);
draw_arc(vec2 center, vec2 radii, float64 start, float64 sweep, color c, float64 thick, bool filled);
draw_triangle(vec2 a, vec2 b, vec2 c, color col, float64 thickness, bool filled);
draw_text(string text, vec2 pos, color c, int64 font, int32 effect, color effect_c, float64 effect_amt);
draw_bitmap(int64 bmp, vec2 pos, vec2 size, color tint, bool rounded);

// effect: 0=none, 1=shadow, 2=outline
// rounding_flags: bitmask, 15=all corners

// Fonts
int64 get_font18(); int64 get_font20(); int64 get_font24(); int64 get_font28();
int64 create_font(string path, float64 size, bool aa, bool color, array ranges);
float64 get_text_width(int64 font, string text, int32 maxw, int32 maxh);
float64 get_text_height(int64 font, string text, int32 maxw, int32 maxh);

// Viewport
float64 get_view_width();  float64 get_view_height();
float64 get_view_scale();  float64 get_fps();

// Clipping
clip_push(vec2 pos, vec2 size); clip_pop();

// Shaders (layout: "POSITION:0:FLOAT2, COLOR:0:FLOAT4")
int64 create_shader(string vs, string ps, string layout);
int64 create_compute_shader(string cs);

// Buffers
int64 create_vertex_buffer(uint32 stride, uint32 max, bool dynamic);
int64 create_index_buffer(uint32 max, bool use32, bool dynamic);
int64 create_constant_buffer(uint32 size);
```

## GUI API — Sidebar Widgets

```cpp
int64 sec = create_section("Section Name");
section_checkbox(sec, "Label", bool_ref);
section_slider_float(sec, "Label", float_ref, min, max);
section_slider_int(sec, "Label", int_ref, min, max);
section_button(sec, "Label", callback_fn);
section_text_input(sec, "Label", string_ref);
section_keybind(sec, "Label", key_ref);
section_color_picker(sec, "Label", color_ref);
section_dropdown(sec, "Label", index_ref, items_array);
section_label(sec, "Text");
section_separator(sec);
```

## Input API

```cpp
bool key_down       (int64 vk);      // host-debounced down state
bool key_raw_down   (int64 vk);      // OS-level pressed state
bool key_fired      (int64 vk);      // up->down this frame (one-shot)
bool key_toggle     (int64 vk);      // caps-lock-style toggle
bool key_singlepress(int64 vk);      // fired but suppressed if modifiers held
bool key_prev_down  (int64 vk);      // down state from previous frame

key_state_t  get_key_state(int64 vk); // atomic snapshot of all 6 flags
array<int32> get_keys_down();         // virtual-key codes currently pressed
string       get_recent_key_input();  // buffered text input (UTF-8)
string       get_key_name(int64 vk);  // localized key name (e.g. "F1")

vec2 get_mouse_pos();                 // render-window pixels
vec2 get_mouse_pos_desktop();         // desktop pixels (full screen)
vec2 get_mouse_delta();               // raw movement this frame
vec2 get_mouse_delta_desktop();       // desktop-space delta this frame
bool mouse_movement_received();       // any movement this frame
bool is_hovered(vec2 pos, vec2 size); // mouse inside rect
float64 get_scroll_delta();           // wheel ticks; positive = up
```

## CPU API

```cpp
string get_cpu_vendor();
float64 time_ms();     // monotonic milliseconds
float64 time_us();     // monotonic microseconds
int32 get_datetime_year/month/day/hour/minute/second();
```

## Zydis API — x86-64 Disassembler/Assembler

```cpp
zydis_insn_t insn = zydis_decode(bytes_array, addr);
// insn.mnemonic, insn.length, insn.operands[]
array<uint8> encoded = zydis_encode(mnemonic, operands);
```

## Unicorn API — x86-64 Emulation

```cpp
int64 uc = uc_create();
uc_mem_map(uc, addr, size, perms);
uc_mem_write(uc, addr, bytes);
uc_reg_write(uc, reg_id, value);
uc_emu_start(uc, begin, until, timeout, count);
uint64 val = uc_reg_read(uc, reg_id);
array<uint8> data = uc_mem_read(uc, addr, size);
uc_destroy(uc);
```

## Net API

```cpp
string body = http_get(url, headers_map);
string body = http_post(url, post_body, headers_map);
int64 ws = ws_connect(url); ws_send(ws, msg); string r = ws_recv(ws);
int64 sock = udp_create(); udp_send(sock, host, port, data); udp_recv(sock, buf, timeout);
```

## Win API

```cpp
array<window_t> wins = enum_windows();
// window_t: .hwnd(), .title(), .class_name(), .pid(), .rect()
send_key(int32 vk, bool down);
send_mouse(int32 button, bool down, int32 x, int32 y);
string clip = get_clipboard(); set_clipboard(text);
```

## Filesystem API

```cpp
string content = read_file(path);
bool ok = write_file(path, content);
bool exists = file_exists(path);
array<string> entries = list_dir(path);
bool ok = create_dir(path);
bool ok = delete_file(path);
```

## Sound API

```cpp
int64 snd = load_sound(path);   // .wav or .ogg
play_sound(snd);
```

## Lifecycle

```cpp
int64 main() {
    // return > 0 to stay loaded, <= 0 to unload
    register_routine(cast<int64>(my_fn), user_data);
    return 1;
}
void my_fn(int64 data) { /* called every frame */ }
unregister_routine(handle);
```

---

# New API Additions (Feb–June 2026 Changelogs)

## Custom Draw API — Direct GPU Access (D3D11)

Full custom shader pipeline on the Universal API. Write HLSL, create vertex
buffers, textures, render targets, depth buffers, and draw any primitive
topology directly from AngelScript/Enma. Custom draw commands respect draw
order with every existing render function. All resources are tracked
per-script and auto-cleaned on unload.

### Resource Creation (all return `uint64` handle, `0` on failure)
```cpp
uint64 create_shader(string vs_source, string ps_source, string layout);
uint64 create_vertex_buffer(uint32 stride, uint32 max_vertices, bool dynamic);
uint64 create_index_buffer(uint32 max_indices, bool is_32bit, bool dynamic);
uint64 create_constant_buffer(uint32 size);
uint64 create_blend_state(src, dst, op, src_alpha, dst_alpha, op_alpha);
uint64 create_sampler(filter, address_u, address_v);
uint64 create_texture(uint32 width, uint32 height, array<uint8> rgba_data);
uint64 create_render_target(uint32 width, uint32 height);
uint64 create_depth_buffer(uint32 width, uint32 height);
uint64 create_depth_stencil_state(bool depth_enable, bool depth_write, int compare_func);
uint64 create_rasterizer_state(int fill_mode, int cull_mode);
```

### Drawing
```cpp
custom_draw(shader, vb, data, vertex_count, topology,
            blend, sampler, texture, rt, cb, cb_data, cb_slot);
custom_draw_indexed(shader, vb, vert_data, vert_stride,
                    ib, index_data, index_count, topology,
                    blend, sampler, texture, rt, cb, cb_data, cb_slot);
```

### Render Target Operations
```cpp
custom_set_render_target(rt);
custom_set_render_target_ext(rt, depth_buffer);
custom_clear_render_target(rt, r, g, b, a);
custom_clear_depth_buffer(db);
custom_resolve_render_target(rt);     // copy RT -> backbuffer
```

### State Management
```cpp
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs);
custom_set_viewport(x, y, w, h);                          // split-screen / PiP
custom_bind_textures(shader, slot0_tex, slot1_tex, ...);  // multi-texture
custom_bind_constant_buffers(shader, slot, cb, cb_data, cb_size);
```

### Mesh & Texture Loading
```cpp
load_obj_mesh(path);                  // returns vb + ib handles
create_texture_from_file(path);
create_dynamic_texture(width, height);
update_dynamic_texture(tex, rgba_data);
```

### Compute Shaders
```cpp
uint64 cs  = create_compute_shader(cs_source);
uint64 buf = create_structured_buffer(element_size, element_count, data);
dispatch_compute(cs, groups_x, groups_y, groups_z);
read_structured_buffer(buf);
```

### Backbuffer Capture
```cpp
uint64 tex = capture_backbuffer();    // texture handle of current frame
```

### Constants
```cpp
// Topology
TOPO_POINT_LIST, TOPO_LINE_LIST, TOPO_LINE_STRIP,
TOPO_TRIANGLE_LIST, TOPO_TRIANGLE_STRIP

// Compare funcs (depth stencil)
CMP_NEVER, CMP_LESS, CMP_EQUAL, CMP_LESS_EQUAL,
CMP_GREATER, CMP_NOT_EQUAL, CMP_GREATER_EQUAL, CMP_ALWAYS

// Fill modes
FILL_WIREFRAME, FILL_SOLID

// Cull modes
CULL_NONE, CULL_FRONT, CULL_BACK
```

### Layout String Format
Comma-separated `SEMANTIC:slot:TYPE` entries, e.g.
`"POSITION:0:FLOAT2, COLOR:0:FLOAT4"`.

### Key Features
- Indexed rendering with 16-bit and 32-bit index formats
- True 3D depth testing with configurable depth-stencil state
- Rasterizer state control (culling, wireframe)
- Custom viewports for split-screen / picture-in-picture
- Multi-texture and multi-constant-buffer binding
- Compute shaders with structured buffers
- OBJ mesh loading + dynamic texture updates
- Depth-enabled render targets, backbuffer capture for post-processing

### Example: Basic Colored Triangle
```angelscript
string vs = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj);
    o.col = i.col;
    return o;
}
""";

string ps = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

uint64 shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
uint64 vb = create_vertex_buffer(24, 3, true);
uint64 blend = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
```

### Example: Depth-Tested 3D Scene
```angelscript
uint64 db = create_depth_buffer(400, 300);
uint64 ds = create_depth_stencil_state(true, true, CMP_LESS);

custom_set_render_target_ext(rt, db);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
```

## World-to-Screen (updated Feb 2026)

```cpp
bool world_to_screen_rowmajor(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
bool world_to_screen_transposed(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
```
- Use `world_to_screen_rowmajor` for row-major view matrices.
- Use `world_to_screen_transposed` for transposed (column-major) matrices.
- ⚠️ **DEPRECATED:** `source2_world_to_screen` — replace with the variants above.

## Matrix4x4 Double Precision (Feb 2026)

```cpp
mat4 m.readas_float(uint64 addr);      // float-precision read
mat4 m.readas_double(uint64 addr);     // double-precision read
bool m.writeas_float(uint64 addr, mat4 v);
bool m.writeas_double(uint64 addr, mat4 v);
```
- ⚠️ **DEPRECATED:** default `matrix4x4` read/write — use a precision-specific variant.

## Thread Priority Helpers (Feb 2026)

```cpp
set_thread_to_highest_priority();
set_thread_to_lowest_priority();
set_thread_to_normal_priority();
```

## Atomics (Feb 2026)

```cpp
atomic_int32 a;    // lock-free thread-safe 32-bit integer
atomic_int64 b;    // lock-free thread-safe 64-bit integer
```

## GUI Additions (Feb–Mar 2026)

```cpp
get_gui_position(float &out x, float &out y);   // GUI window position
get_gui_size(float &out w, float &out h);       // GUI window size

// List widget ops
list:get(...);              list:remove(...);
list:highlight(...);        list:remove_highlight(...);
list:hide(...);             list:show(...);
```

## Callbacks (Mar 2026)

```cpp
register_callback(string name, func, bool render_on_top = false);
// render_on_top=true renders on top of everything else
```

## Window Additions (Feb 2026)

```cpp
array<uint64> hwnds = get_all_hwnds();   // all window handles
```

## Fonts (Feb 2026)

```cpp
int64 create_font(string name, float64 size, array glyph_ranges);       // glyph_ranges optional
int64 create_font_mem(array<uint8> data, float64 size, array glyph_ranges); // glyph_ranges optional
```

## Input Additions (Feb 2026)

- Controller keybinds via **XINPUT** now supported.
- `get_mouse_delta()` now returns proper movement delta (fixed).

## Unicorn Emulator Updates (Mar 2026)

```cpp
// New hook types
UC_HOOK_INSN_INVALID    // invalid instructions
UC_HOOK_INTR            // software interrupts (INT3, syscalls)

uint64 status = uc_get_last_exception(uc);     // NTSTATUS, e.g. 0xC0000005
uint64 rip    = uc_get_exception_address(uc);  // RIP where exception occurred
```
- Null pointer access is now caught gracefully instead of crashing.

## Sound API — Full Audio Engine (Mar 2026)

44100Hz stereo, up to 64 simultaneous instances. WAV (PCM 8/16-bit) parsed
directly; MP3/AAC/WMA/FLAC decoded via Media Foundation. Auto-cleanup on
script unload.

```cpp
int64 snd = load_sound(path);
free_sound(snd);
play_sound(snd, bool loop);
stop_sound(snd);
stop_all_sounds();
set_sound_volume(snd, float vol);   // 0.0 – 1.0
set_sound_pan(snd, float pan);      // -1.0 (L) – +1.0 (R)
```

## Scan API Updates (Mar 2026)

Scan functions now return `array<uint64>@` directly (no `&out` params).
The `get_vad_snapshot` regression is fixed and returns proper values.

```cpp
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
```
- ⚠️ **REMOVED (never existed):** `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64`.

## Deprecated Functions Summary

| Deprecated | Replacement |
|---|---|
| `source2_world_to_screen` | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| default `matrix4x4` read/write | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` |
| `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64` | removed — use `scan_float` / `scan_double` / `scan_string` / `scan_wstring` / `scan_pointer` |

---

## Source: `knowledge/pcx-cross-language-bridge.md`

# PCX Cross-Language Bridge — Enma vs AngelScript vs Lua

Perception.cx supports three scripting languages: Enma (the native one), AngelScript, and Lua. Each has a different API surface, different performance characteristics, and different ergonomic strengths. The AI keeps defaulting to whichever language the user opened the editor in — missing the cases where another language is materially better for the feature. This file is the comparison and decision guide, plus the patterns for cross-language coordination when one project genuinely needs multiple.

> **Read this before** starting a new feature, picking a language for a new project, or wondering whether a slow / awkward feature would be better in a different language.

---

## At-a-Glance Comparison

| Property | Enma | AngelScript | Lua |
|---|---|---|---|
| **Language family** | C++-like with extensions (FFI, coroutines, annotations) | C++-like, AngelScript registration model | Dynamic, table-centric |
| **Typing** | Static, optionally inferred | Static | Dynamic, with optional type hints in 5.4 |
| **Memory model** | Manual + RAII (deterministic destructors, no GC) | Refcounted handles for objects; value types for math primitives | Garbage-collected |
| **Performance tier** | Fastest (JIT / bytecode, no GC) | Fast (interpreted with type-erased dispatch) | Slower (interpreted, GC pauses possible) |
| **Startup cost** | Low (precompiled `.emb` deserializes fast) | Medium (compile from source on load) | Low (LuaJIT-class speed if exposed; otherwise interpreted) |
| **Hot-reload semantics** | Yes (script code replaced; globals + types persist host-side) | Yes (callbacks released on unload; `proc_t` must `deref()`) | Yes (globals reset; package cache may persist) |
| **Concurrency / threading** | First-class via `addon-thread` (mutex, condvar) and atomics | Mutex / Atomic types per registered addon | Coroutines (idiomatic Lua); no native threads |
| **FFI / native function registration** | Direct via SDK; many built-ins | Via the AngelScript registration model (host-side `RegisterObjectMethod`, etc.) | Via Lua C API (host-side `lua_register`) |
| **Error handling** | Exceptions (`try`/`catch`); rich error types | Exceptions; AS-specific exception types | `pcall` / `xpcall` returning ok-flag + value |
| **Compile-time checking** | Strong (type-checks on compile) | Strong (type-checks on compile) | Weak (most errors are runtime) |
| **Has `vec2`/`vec3`/`vec4`/`quat`/`mat4`** | Yes (math addon) | Yes (vector / matrix types per the engine-specific-api docs) | Yes via the extended-math API (`vector3`, `quaternion`, `matrix4x4`, `mat4` namespace) |
| **Has SIMD intrinsics** | Yes (`addon-simd`: `f32x4`, `i32x4`) | Not as a first-class addon at last check | Not as a first-class addon at last check |
| **Has atomic types** | Yes (`addon-atomic`: `aint32`, `aint64`) | Yes (per AS docs) | No |
| **JSON support** | Yes (`addon-json`) | Yes (per AS docs) | Yes (via `package` addon) |
| **Regex support** | Yes (`addon-regex`) | Available per AS surface | Standard Lua `string.match` patterns |
| **Coroutines** | Yes (per `lang-advanced.md`) | Variable per build — check `docs/perception/angelscript/overview.md` | Native and idiomatic |
| **AS Intrinsics namespace** | n/a | Yes — PCX-specific AS extension (per the README's AngelScript section) | n/a |
| **Debugger tooling at dev time** | Strong (LSP via `lsp/enma-lsp`, full SDK debug hooks) | Strong (LSP via `lsp/angel-lsp-pcx`) | Variable per host integration |

The single most important row is **performance tier**. For hot-path code (render routines at 144 Hz, entity loops over 256 entities, per-frame math), Enma is materially faster than AngelScript, which is materially faster than Lua. The differences below render-rate are usually negligible; at render-rate, they're felt.

Verify each row against the per-language docs for your PCX version — `docs/enma/`, `docs/perception/angelscript/`, `docs/perception/lua/`. The table is a guide; the docs are authoritative.

---

## Per-Use-Case Routing

The decision-tree, ordered by frequency:

### High-frequency render-path code → **Enma**

Render routines running at 144-240 Hz are budget-tight (see `skill://pcx-perf-budget`). Static typing avoids per-call dispatch overhead; no GC eliminates pause variance; the precompiled `.emb` format means no compile cost at script load. For ESP, radar, HUD, anything called from `on_render`: Enma is the default.

### Complex stateful UI logic with rich object lifecycle → **AngelScript**

Features with many in-flight objects with non-trivial lifetimes (target tracker that maintains per-entity state across frames, queue-of-attempts state machine, menu system with nested panels) lean on AngelScript's refcounted handles. The `Type@` syntax + automatic `deref()` (when scoped correctly) handles ownership without manual bookkeeping. See `skill://pcx-angelscript-discipline` rules 2-3 for the discipline.

### Quick prototyping / config DSL / one-off scripts → **Lua**

Dynamic typing is the fastest iteration loop. A table-based config file ("here are my hotkey assignments, my color preferences, my distance thresholds") in Lua is one screen; in Enma it's three. For exploratory work where the shape of the data isn't known yet, Lua's tables-as-everything pattern wins.

### CPU-bound math (matrix transforms, pathfinding, simulation) → **Enma**

The `addon-math3d` (`quat`, `mat4`) and `addon-simd` (`f32x4`, `i32x4`) addons give Enma the native math primitives modern game-math work needs. AngelScript has matrix types but no SIMD addon. Lua's math library is general-purpose, not game-shaped. For pathfinding / physics-y simulation / matrix-heavy work: Enma.

### Network protocol handling / file I/O → **any (use the project's primary language)**

`addon-net` (Enma) and equivalents in AS / Lua all cover sockets, HTTP, websockets. File I/O similarly (`addon-file`, `fs_*` in Lua, AS file APIs). Pick based on what the rest of the script uses; the per-call cost of network I/O dwarfs the per-call cost of the language dispatch overhead.

### Cross-binary compatibility shims → **Enma**

The `.emb` precompiled format (per `docs/enma/sdk-serialization-and-linking.md`) is portable across compatible runtime versions and ships without the script source. AngelScript scripts ship as source by default; Lua scripts ship as source or LuaJIT bytecode. For a library you'll distribute to other users running varying PCX versions, Enma's `.emb` is the most portable artifact.

### Coroutine-heavy state machines → **Enma or Lua**

Enma's coroutines are first-class (per `docs/enma/lang-advanced.md`); Lua's are idiomatic and well-documented. AngelScript's support varies per build. For a stateful "send command → await response → handle result → loop" pattern: pick by what your rest-of-the-project uses.

---

## Cross-Language Coordination

When one feature genuinely spans languages (a render-rate ESP in Enma that consumes data from a config file maintained in Lua, or an AngelScript menu wrapping an Enma compute kernel), three patterns:

### 1. Shared state via files

```
language A writes  ───>  config.json on disk  ───>  language B reads
```

- Cheap; asynchronous; no language-level coupling
- Latency = filesystem-write + filesystem-read; fine for config, slow for per-frame data
- Robust against crashes (file persists)
- Use for: config, persisted state, occasional cross-script communication

### 2. Shared state via the host process

If PCX exposes a host-side state bridge (check `docs/perception/` for cross-language data sharing — the surface is host-specific), one script can write a global the host exposes; another reads it.

- Latency low (in-process)
- Coupling: high (both scripts must agree on the global's shape)
- Use only when the latency of pattern #1 is genuinely too high (per-frame coordination)

### 3. Don't

In most cases, picking one language per feature is cheaper than coordinating across two. If you find yourself reaching for cross-language plumbing, ask: would rewriting the smaller side in the larger side's language eliminate the bridge? Usually yes. Usually it's cheaper.

The rule of thumb: cross-language coordination is for cases where the languages have genuinely different strengths the feature needs. Lua for a config DSL + Enma for the render-rate consumer is a fair split. Two features in two languages "because we have a multi-language codebase" usually means you've imported maintenance overhead for no gain.

---

## Performance Notes

Measured-style guidance (the actual numbers vary per binary, build, and platform — verify on your target):

### Equivalent across languages

These dominate the cost of any non-trivial script regardless of language choice:

- Cross-process memory reads (`ru64`, `read_memory`, etc.) — kernel transition cost dominates, language overhead invisible
- Render API calls (`draw_*`) — GPU command submission dominates
- File I/O — disk latency dominates
- Network calls — network latency dominates

If your script is dominated by these, the language choice barely matters.

### Materially different across languages

These are where the choice shows up:

- **Per-script-call native function overhead** — Enma's dispatch is the tightest; AS adds a type-check pass; Lua's varies by integration. In a tight loop of 1000 native calls per frame, the difference can be 100s of µs.
- **Garbage collection pauses** — Lua has GC; pauses are usually sub-ms but can spike. Enma has none. AS uses refcounting (deterministic, no pauses, but cycles need manual handling).
- **Hot-path arithmetic** — Enma + the SIMD addon outperforms AS + scalar math, which outperforms Lua's general-purpose number type.
- **Allocation overhead** — Lua's table allocations on the hot path show up; Enma's stack-allocated value types don't allocate; AS's refcounted handles allocate but predictably.

The implication: a render-rate routine in Lua + a render-rate routine in Enma differ by 10-50% in CPU time *not* counting the cross-process reads. With cross-process reads dominating, the user-visible difference is smaller, but on a tight script the choice matters.

---

## Migration Notes

When you start a feature in one language and realize another would be better:

### Enma ↔ AngelScript

- Type names mostly align (`uint64`, `float`, `string`, etc.).
- The proc API surface is parallel but the spellings differ — see `skill://pcx-angelscript-discipline` rule 1 for the mapping table (e.g. Enma's `register_routine(cast<int64>(on_render), 0)` becomes AS's `register_callback(on_tick, 16, 0)` with a different callback signature).
- Handle vs value: AS uses `Type@` for refs; Enma uses references / pointers. Conversion is mechanical but per-variable.
- Render APIs differ in shape: Enma takes `color` / `vec2` structs; AS takes raw RGBA ints and separate x/y floats. See `skill://pcx-angelscript-discipline` rule 8.

### Enma ↔ Lua

- Bigger jump. Lua's dynamic typing means every Enma type annotation gets discarded; in return, every Enma type-check happens at runtime.
- Numbers are subtle: Lua 5.4 has a 64-bit integer subtype, so addresses survive; pre-5.4 Lua loses precision past 2^53. See `skill://pcx-lua-discipline` rule 1.
- Lifecycle: Enma's `on_update` / `on_render` map to Lua's `register_routine` (or equivalent — check `docs/perception/lua/life-cycle.md`).
- Tables replace structs; field access syntax is `.` either way; iteration syntax differs.

### AngelScript ↔ Lua

- Largest jump. AS is C++-with-handles; Lua is dynamic + tables. Plan to rewrite, not translate.
- Reuse the architecture (what feature does what, how data flows), not the code.

For all three: the underlying *engine* knowledge (sigs, offsets, struct layouts) is language-agnostic. Port the language-specific parts; keep the offset table.

---

## Recommended Default by Project Size

| Project size | Recommendation |
|---|---|
| 1-3 file script | Pick whichever you know best; the differences don't matter at this scale. |
| 5-15 file project | **Enma is the default** unless a specific feature wants AS or Lua per the routing above. |
| 20+ file production project | **Enma** with selective AS / Lua per feature; **consistency** in the bulk of the codebase matters more than the marginal per-language wins. |
| Library you'll distribute | **Enma** — `.emb` is the most portable artifact. |
| Quick personal experiment | **Lua** — fastest iteration. |
| Performance-critical feature pulled out of a larger project | **Enma** — even if the project is in another language. |

The recommendation against mixing languages in mid-size projects isn't arbitrary: every cross-language boundary is a coupling point, a maintenance overhead, and a context switch for the next maintainer. Use the boundary when the benefit is concrete; default to one language when it's not.

---

## Cross-References

- `docs/enma/` — Enma language + SDK (50 files; start at `enma/readme.md`)
- `docs/perception/angelscript/` — AngelScript APIs (23 files; start at `overview.md`)
- `docs/perception/lua/` — Lua APIs (17 files; start at `overview.md`)
- `skill://pcx-angelscript-discipline` — 10 AS-specific rules (handles, `&out`, `array<T>`, `register_callback` shape)
- `skill://pcx-lua-discipline` — 10 Lua-specific rules (int subtype for addresses, `pcall`, hot-reload boundaries)
- `skill://pcx-perf-budget` — the perf budgets the language choice affects
- `skill://script-bundler` — `.emb` packaging that makes Enma especially portable
- `knowledge/script-organization-patterns.md` — multi-file organization patterns (largely language-agnostic, with notes per language)
- `knowledge/pcx-api-cheatsheet.md` — cross-API surface at a glance

---

## Source: `knowledge/pcx-doc-roots.md`

# PCX Documentation Roots

The only authoritative sources for Perception.cx scripting APIs are these two
documentation trees on `docs.perception.cx`:

1. **Enma (Perception.cx Enma API)**  
   Canonical entry point: `https://docs.perception.cx/perception/enma/overview`  
   Markdown equivalent (when GitBook exposes it): `https://docs.perception.cx/perception/enma/readme.md`  
   Sub-pages follow the convention: `https://docs.perception.cx/perception/enma/<page>.md`

2. **AngelScript (Perception.cx AngelScript API)**  
   Canonical entry point: `https://docs.perception.cx/perception/angel-script/overview`  
   Markdown equivalent: `https://docs.perception.cx/perception/angel-script/overview.md`  
   Sub-pages follow the convention: `https://docs.perception.cx/perception/angel-script/<page>.md`

## What this means

- Every PCX API symbol used in generated code must be traceable to one of these
  two trees, or to the generated `knowledge/pcx-api-index.json` that is built
  from those trees.
- Do not use the local `docs/` copy as a primary authority; it is a drift-checked
  mirror. If a local doc and the live upstream disagree, the live upstream wins.
- The Enma *language* reference (grammar, types, addons) lives at
  `https://enma-1.gitbook.io/enma/` and is referenced for language semantics,
  but the PCX API surface itself comes only from the two roots above.

## Navigating the trees

GitBook exposes a structured index at `https://docs.perception.cx/perception/llms.txt`.
Use it to discover the exact sub-page paths under each root. In code, prefer
fetching the `.md` variant of any page so the model receives structured
markdown rather than rendered HTML.

## Generated index

`knowledge/pcx-api-index.json` is derived by scanning the local mirrors of the
pages under these two roots (plus the Enma addon docs that the Enma API
references). It exists so tools like `pcx symbol-check` and the
`mcp:pcx-knowledge` `validate_code` tool can catch invented API names without
performing a live fetch on every keystroke.

---

## Source: `knowledge/pcx-version-matrix.md`

# PCX API Version Matrix

This file maps each PCX API addition / change / removal to the version it landed in, so scripts that target older PCX runtimes know what's safe. Drawn from `docs/perception/changelogs.md`.

> **Read this before** committing to a script that must run on a specific PCX runtime version.

PCX ships **date-stamped rolling releases**, not semantic versions. The changelog
(`docs/perception/changelogs.md`) is keyed by release date and product line
(`Universal API` vs `Counter-Strike 2`). There is no `vX.Y` version number in any
shipped artifact, so this matrix uses the **changelog release date** as the version
anchor. When a `## How to Use` example writes `// Requires: PCX v<X.Y>+`, read the
placeholder as the corresponding **release date** (e.g. `// Requires: PCX 2026-03-16+`).

Two same-day Universal API posts are disambiguated as the changelog does — `(a)`
(earlier) and `(b)` (later). Where the changelog never dates an API but the cheatsheet
or per-API docs document it, the row reads `<= <earliest dated release that references it>`
or `unknown` — never a guessed date.

---

## How to Use This File

1. **Pin the target at the top of the script.** A one-line comment records the oldest
   runtime the script is allowed to load on:

   ```cpp
   // Requires: PCX 2026-03-17+   (custom-draw 3D: depth testing + compute shaders)
   ```

2. **Before using an API, check the matrix.** Find the API's row in
   `## API Matrix — By Category`. If its `Since` date is **after** your pin, either
   raise the pin or do not call it. If the `Deprecated/Removed In` column is set and
   your target is **at or after** that date, use the `Replacement` instead.

3. **Targeting multiple runtimes? Fall back gracefully.** PCX exposes no runtime
   version query (see next section), so multi-version support is done with
   preprocessor `#define` guards set from the SDK, gated by what you tested. Example:

   ```cpp
   // Build host passes the target via the SDK:
   //   define(engine, "PCX_2026_03_17", "1");   // only on >= 2026-03-17 builds
   #ifdef PCX_2026_03_17
       uint64 cs = create_compute_shader(cs_src);   // since 2026-03-17(a)
       dispatch_compute(cs, 64, 1, 1);
   #else
       // conservative path: CPU fallback, no compute shaders
   #endif
   ```

---

## Runtime Version Detection

**There is no documented API to ask the PCX runtime its version.** No
`get_version` / `api_version` / `client_version` / `build_version` native appears in
`docs/perception/*` or `knowledge/pcx-api-cheatsheet.md`. Do not invent one — a call to
a nonexistent native fails to compile (Enma) or aborts the script.

Use the **conservative approach**: drive feature availability from preprocessor
symbols the build host injects, set only after you have tested the target build.

```cpp
// ── SDK side (host C++), set per known-good target build ──
//   define(engine, "PCX_BUILD", "20260317");   // numeric YYYYMMDD of tested build
//   add_include_path(engine, "includes/");

// ── Script side ──
#ifndef PCX_BUILD
    #error "PCX_BUILD not defined — host must declare the tested runtime build"
#endif

#if PCX_BUILD >= 20260317
    // depth testing + compute shaders available (since 2026-03-17(a))
#elif PCX_BUILD >= 20260316
    // base custom-draw shader pipeline only (since 2026-03-16)
#else
    // pre-custom-draw: 2D primitives only
#endif
```

`#define`, `#ifdef`/`#ifndef`/`#if`/`#elif`/`#else`/`#endif`, and SDK-side
`define(engine, name, value)` are all documented in `docs/enma/lang-pre-processor.md`.
The numeric `YYYYMMDD` form lets you use `#if PCX_BUILD >= …` integer comparisons.
The runtime cannot self-report, so **the host is the source of truth** — never branch
on a value the script tries to read at runtime.

---

## API Matrix — By Category

Columns: `API` | `Since` | `Notes` | `Deprecated/Removed In` | `Replacement`.
Every `Since` cites the changelog release date or is marked `unknown` / `<= <date>`.

### Render — 2D Primitives & Fonts

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `draw_line` | `<= 2026-02-01` | Line, `thickness` arg. `docs/perception/render-api.md`. | — | — |
| `draw_rect` / `draw_rect_filled` | `<= 2026-02-01` | Rect with `rounding` + corner flags. | — | — |
| `draw_circle` | `<= 2026-02-01` | `filled` bool. | — | — |
| `draw_arc` | `<= 2026-02-01` | `radii`, `start`, `sweep`. | — | — |
| `draw_triangle` | `<= 2026-02-01` | `filled` bool. | — | — |
| `draw_text` | `<= 2026-02-01` | `effect` 0=none/1=shadow/2=outline. | — | — |
| `draw_bitmap` | `<= 2026-02-01` | Tinted bitmap blit. | — | — |
| `draw_four_corner_gradient` | unknown | In `docs/perception/render-api.md` but never named in the changelog. Treat as `<= 2026-02-01` core. | — | — |
| `draw_polygon` | unknown | In `docs/perception/render-api.md`; no changelog row. Treat as `<= 2026-02-01` core. | — | — |
| `get_font18/20/24/28`, `get_text_width`, `get_text_height` | `<= 2026-02-01` | Built-in font handles; predate the window. | — | — |
| `create_font` / `create_font_mem` — optional `glyph_ranges` arg | `2026-02-03(b)` | Optional `glyph_ranges` added to both (changelog `Feb 3 (b) → AngelScript & Lua`). Older builds: no `glyph_ranges` parameter. | — | — |
| Font loading latency | `2026-02-03(b)` | "Font loading now instant" + render backend optimized (changelog `Feb 3 (b) → Render Engine`). Behavior change, not a new symbol. | — | — |
| Script render order | `2026-02-12` | Changed: "newly created callbacks render first" (changelog `Feb 12 → Render System`). Order reversed vs earlier builds. | — | — |

### Render — Custom Draw (Direct D3D11 / GPU)

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `create_shader`, `create_vertex_buffer`, `create_constant_buffer`, `create_blend_state`, `create_sampler`, `create_texture`, `create_render_target` | `2026-03-16` | Base custom-draw pipeline — HLSL VS/PS compiled at runtime, all primitive topologies (changelog `Mar 16 → Custom Draw API — Direct GPU Access`). | — | — |
| Custom draw on CS2 product | `2026-03-16` (CS2) | Same Custom Draw API pushed to the CS2 line (changelog `Mar 16 — Counter-Strike 2`). | — | — |
| `create_index_buffer`, `custom_draw_indexed` | `2026-03-17(a)` | Indexed drawing, 16-bit and 32-bit index buffers (changelog `Mar 17 (a) → Indexed Drawing`). | — | — |
| `create_depth_buffer`, `create_depth_stencil_state`, `custom_set_depth_stencil_state`, `custom_clear_depth_buffer`, `custom_set_render_target_ext` | `2026-03-17(a)` | Depth testing + depth-enabled render targets (changelog `Mar 17 (a) → Depth Testing`, `Depth-Enabled Render Targets`). | — | — |
| `create_rasterizer_state`, `custom_set_rasterizer_state` | `2026-03-17(a)` | Cull / fill mode, wireframe (changelog `Mar 17 (a) → Rasterizer State`). | — | — |
| `custom_set_viewport` | `2026-03-17(a)` | Split-screen / picture-in-picture (changelog `Mar 17 (a) → Custom Viewports`). | — | — |
| `custom_bind_textures` (multi-texture) | `2026-03-17(a)` | Bind multiple textures to one shader (changelog `Mar 17 (a) → Multi-Texture Binding`). | — | — |
| `custom_bind_constant_buffers` (multi-CB) | `2026-03-17(a)` | Multiple constant buffers to different slots (changelog `Mar 17 (a) → Multi-Constant-Buffer Binding`). | — | — |
| `create_compute_shader`, `create_structured_buffer`, `dispatch_compute`, `read_structured_buffer` | `2026-03-17(a)` | GPU compute from script (changelog `Mar 17 (a) → Compute Shaders`). | — | — |
| `load_obj_mesh` | `2026-03-17(a)` | Loads `.obj`, returns vb+ib handles (changelog `Mar 17 (a) → OBJ Mesh Loading`). | — | — |
| `create_dynamic_texture`, `update_dynamic_texture`, `create_texture_from_file` | `2026-03-17(a)` | Runtime-updatable textures (changelog `Mar 17 (a) → Dynamic Textures`). | — | — |
| `capture_backbuffer`, `custom_resolve_render_target` | `2026-03-17(a)` | Backbuffer capture for post-processing (changelog `Mar 17 (a) → Backbuffer Capture`). | — | — |

### Render — Custom Draw Constants & Enums

| Symbol group | Since | Notes | Deprecated/Removed In | Replacement |
|--------------|-------|-------|-----------------------|-------------|
| `BLEND_SRC_ALPHA`, `BLEND_INV_SRC_ALPHA`, `BLEND_ONE`, `BLEND_OP_ADD`, … (blend constants) | `2026-03-16` | Args to `create_blend_state`; ship with the base pipeline (changelog `Mar 16`). | — | — |
| Layout string format `"SEMANTIC:slot:TYPE"` | `2026-03-16` | Vertex layout for `create_shader` (changelog `Mar 16 → Shaders`, "Layout defined with format string"). | — | — |
| `TOPO_POINT_LIST`, `TOPO_LINE_LIST`, `TOPO_LINE_STRIP`, `TOPO_TRIANGLE_LIST`, `TOPO_TRIANGLE_STRIP` | `2026-03-16` | All primitive topologies present at base pipeline (changelog `Mar 16 → All Primitive Topologies`). | — | — |
| `CMP_NEVER` … `CMP_ALWAYS` (depth compare funcs) | `2026-03-17(a)` | Args to `create_depth_stencil_state` (changelog `Mar 17 (a) → Depth Testing`). | — | — |
| `FILL_WIREFRAME`, `FILL_SOLID` | `2026-03-17(a)` | Args to `create_rasterizer_state` (changelog `Mar 17 (a) → Rasterizer State`). | — | — |
| `CULL_NONE`, `CULL_FRONT`, `CULL_BACK` | `2026-03-17(a)` | Args to `create_rasterizer_state` (changelog `Mar 17 (a) → Rasterizer State`). | — | — |

### Proc — Memory Read / Write & Typed Reads

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `ref_process` (by name / by PID), `alive`, `base_address`, `peb`, `pid`, `is_valid_address` | `<= 2026-02-01` | Process handle + validity. `docs/perception/proc-api.md`. | — | — |
| `ru8/16/32/64`, `r8/16/32/64`, `rf32/64` | `<= 2026-02-01` | Scalar read primitives. | — | — |
| `rs`, `rws`, `rvm` | `<= 2026-02-01` | ASCII / UTF-16 / bulk reads. | — | — |
| `wu8/16/32/64`, `w8/16/32/64`, `wf32/64`, `wvm` | `<= 2026-02-01` | Write primitives (gated: `write_memory`). | — | — |
| `read_vec2/3/4_fl32`, `read_vec2/3/4_fl64`, `read_quat_fl32/64`, `read_mat4_fl32/64` + write mirrors | unknown | Documented in `docs/perception/proc-api.md` but **not named in the changelog**. Do not date precisely; treat as `<= 2026-02-01` core typed reads. Distinct from the `mat4` method `readas_*` below. | — | — |
| `get_module_base/size/list`, `get_proc_address`, `get_import_rdata_address` | `<= 2026-02-01` | Core module surface. | — | — |
| `find_code_pattern`, `find_all_code_patterns` | `<= 2026-02-01` | Core scanning. Executable-section-only + single-hit fixes landed `2026-02-12 → RE Tools`. | — | — |
| `scan_float`, `scan_double`, `scan_string`, `scan_wstring`, `scan_pointer` | `2026-03-14` | Added (changelog `Mar 14 → VAD / Memory Scan API Fixes`: "Added missing functions"). | — | — |
| Scan return shape | `2026-03-14` | Changed: scan functions now return `array<uint64>@` directly, no `&out` params (changelog `Mar 14`). Pre-`2026-03-14` callers used the old `&out` form. | — | — |
| `get_vad_snapshot` | `<= 2026-02-01` | Existed earlier but returned all-zero fields until fixed `2026-03-14` (changelog `Mar 14`: "Fixed `get_vad_snapshot` returning all-zero fields"). | — | — |
| `virtual_query`, `vad_region_t` | `<= 2026-02-01` | Core VAD query. | — | — |
| `alloc_vm` / `free_vm` | unknown | Allocation API existed pre-window; `2026-03-20` reworked it ("no longer causes BSODs", changelog `Mar 20 → Allocation API`). Requires CFG disabled + Insecure API enabled to execute allocated memory. | — | — |

### Proc / Threading — Matrix Precision, Atomics, Thread Priority

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `mat4.readas_float` / `readas_double` / `writeas_float` / `writeas_double` | `2026-02-03(b)` | Matrix4x4 double-precision read/write variants (changelog `Feb 3 (b) → AngelScript & Lua`). | — | — |
| default `matrix4x4` read/write (no precision suffix) | `<= 2026-02-03(a)` | — | `2026-02-03(b)` (deprecated) | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` |
| `atomic_int32`, `atomic_int64` | `2026-02-03(b)` | Lock-free shared state (changelog `Feb 3 (b) → AngelScript → Atomic API`). AngelScript-only entry. | — | — |
| `set_thread_to_highest_priority` / `lowest` / `normal_priority` | `2026-02-03(b)` | Thread priority helpers (changelog `Feb 3 (b) → AngelScript`). AngelScript-only entry. | — | — |

### World-to-Screen

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `source2_world_to_screen` (no viewport) | `<= 2026-02-01` | Original Source 2 W2S. | `2026-02-03(b)` (deprecated) | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| `source2_world_to_screen` — optional `viewport` arg | `2026-02-03(a)` | Added optional `const vector2 &in viewport = vector2(0,0)` (changelog `Feb 3 (a) → AngelScript`). Superseded one release later. | `2026-02-03(b)` (deprecated) | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| `world_to_screen_rowmajor` | `2026-02-03(b)` | Replaces `source2_world_to_screen` for row-major matrices (changelog `Feb 3 (b) → AngelScript & Lua`, "migration required"). | — | — |
| `world_to_screen_transposed` | `2026-02-03(b)` | New, for transposed/column-major matrices (changelog `Feb 3 (b)`). | — | — |

### Input

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `is_key_down`, `is_key_pressed`, `is_key_released` | `<= 2026-02-01` | Legacy keyboard state functions. | `2026-02-12` (deprecated) | `key_down` / `key_fired` / `key_toggle` |
| `is_mouse_down` | `<= 2026-02-01` | Legacy mouse button check. | `2026-02-12` (deprecated) | `key_down` with `vk::lbutton` / `vk::rbutton` |
| `key_down`, `key_fired`, `key_toggle`, `key_raw_down` | `2026-02-12` | Current unified keyboard and mouse button state queries. | — | — |
| `get_mouse_delta` | `<= 2026-02-01` | Existed earlier; behavior fixed `2026-02-12` to return proper movement delta instead of screen-space delta (changelog `Feb 12 → Input System`). | — | — |
| Controller keybinds (XINPUT) | `2026-02-12` | XINPUT controller keybind support added (changelog `Feb 12 → Input System`). | — | — |
| `get_gui_position(float &out x, float &out y)`, `get_gui_size(float &out w, float &out h)` | `2026-02-12` | Added (changelog `Feb 12 → AngelScript`). | — | — |
| `get_gui_pos` (legacy) | `<= 2026-02-12` | Position bug fixed `2026-03-17(b)` (changelog `Mar 17 (b) → AngelScript`, "Fixed `get_gui_pos` position issue"). Prefer `get_gui_position`. | — | `get_gui_position` |

### GUI — Sections, Widgets, Lists, Callbacks

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `create_section` | `<= 2026-02-01` | Returns section handle. `docs/perception/gui-api.md`. | — | — |
| `section_checkbox`, `section_slider_float`, `section_slider_int` | `<= 2026-02-01` | Toggle + numeric inputs. | — | — |
| `section_button`, `section_text_input`, `section_keybind` | `<= 2026-02-01` | Action / text / key-capture widgets. | — | — |
| `section_color_picker`, `section_dropdown` | `<= 2026-02-01` | Color ref / indexed dropdown. | — | — |
| `section_label`, `section_separator` | `<= 2026-02-01` | Static layout elements. | — | — |
| `list:get`, `list:remove`, `list:highlight`, `list:remove_highlight`, `list:hide`, `list:show` | `2026-02-17` | List widget op set added (changelog `Feb 17 → GUI`). | — | — |
| List widget selected-index correctness | `2026-02-03(a)` | Fixed: selected index becoming incorrect on add/remove (changelog `Feb 3 (a) → GUI`). | — | — |
| `register_callback` — optional `bool render_on_top = false` | `2026-03-17(b)` | Added (changelog `Mar 17 (b) → AngelScript`). Older builds: no `render_on_top` argument. | — | — |
| Taskbar (top-middle), force-on-top toggles | `2026-03-30(b)` | GUI taskbar for GUI/Analyzer/Editor/Console (changelog `Mar 30 (b) → GUI`). UI feature, not a script symbol. | — | — |
| Force render key (RE Tools while UI hidden) | `2026-03-18` | Configurable keybind (changelog `Mar 18 → GUI`). UI feature. | — | — |

### Sound

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `load_sound`, `free_sound`, `play_sound`, `stop_sound`, `stop_all_sounds`, `set_sound_volume`, `set_sound_pan`, `play_sound(..., loop=true)` | `2026-03-14` | Entire Sound API is new in this release — waveOut mixer, 44100Hz stereo, ≤64 instances, WAV direct + MF decode (changelog `Mar 14 → Sound API (new)`). No sound API exists before `2026-03-14`. | — | — |

### Net

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `http_get`, `http_post`, `ws_connect`, `ws_send`, `ws_recv`, `udp_create`, `udp_send`, `udp_recv` | unknown | Documented in `knowledge/pcx-api-cheatsheet.md` / `docs/perception/net-api.md`; **no changelog row dates them**. Treat as `<= 2026-02-01` core; do not assert a precise version. | — | — |

### Win

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `enum_windows`, `window_t`, `send_key`, `send_mouse`, `get_clipboard`, `set_clipboard` | `<= 2026-02-01` | Core Win API. `docs/perception/win-api.md`. | — | — |
| `get_all_hwnds()` | `2026-02-01` | Added (changelog `Feb 1 → AngelScript & Lua`, "returns all window handles"). | — | — |

### Filesystem

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `read_file`, `write_file`, `file_exists`, `list_dir`, `create_dir`, `delete_file` | unknown | Documented in `knowledge/pcx-api-cheatsheet.md` / `docs/perception/filesystem-api.md`; **no changelog row dates them**. Treat as `<= 2026-02-01` core. (Note: the same names also appear as IDE-AI tools in the changelog — those are tooling, not the script FS API.) | — | — |

### CPU / Time

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `get_cpu_vendor`, `time_ms`, `time_us`, `get_datetime_*` | `<= 2026-02-01` | Core CPU/time surface. `docs/perception/cpu-api.md`. | — | — |

### Zydis (disassembler / assembler)

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `zydis_decode`, `zydis_encode`, `zydis_insn_t` | `<= 2026-02-01` | Core. `docs/perception/zydis-api.md`. | — | — |

### Unicorn (x86-64 emulation)

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `uc_create`, `uc_mem_map`, `uc_mem_write/read`, `uc_reg_write/read`, `uc_emu_start`, `uc_destroy` | `<= 2026-02-01` | Core emulation surface. `docs/perception/unicorn-api.md`. | — | — |
| `UC_HOOK_INSN_INVALID` | `2026-03-18` | Invalid instructions stop emulation with a logged message (changelog `Mar 18 → AngelScript API — Unicorn Emulator`). | — | — |
| `UC_HOOK_INTR` | `2026-03-18` | Software interrupts (INT3, syscalls) stop emulation cleanly (changelog `Mar 18`). | — | — |
| `uc_get_last_exception(handle)` | `2026-03-18` | Returns NTSTATUS (e.g. `0xC0000005`) (changelog `Mar 18`). | — | — |
| `uc_get_exception_address(handle)` | `2026-03-18` | Returns RIP at exception (changelog `Mar 18`). | — | — |
| Null-pointer access handling | `2026-03-18` | Changed: caught gracefully, emulation stops instead of crashing (changelog `Mar 18`). | — | — |

### Platform / Engine (non-API capabilities affecting scripts)

| Capability | Since | Notes | Deprecated/Removed In | Replacement |
|------------|-------|-------|-----------------------|-------------|
| 32-bit games support | `2026-03-08` | Added (changelog `Mar 8`). Scripts targeting x86 processes require `>= 2026-03-08`. | — | — |
| Fullscreen mode (universal) | `2026-03-20` | Engine + overlay support for all games (changelog `Mar 20 → Perception Engine`). | — | — |
| Extensions system (`.as` in `extensions/`) | `2026-03-14` | Lifecycle hooks, AI-pipeline hooks, widget/platform/editor APIs (changelog `Mar 14 → Extensions`). | — | — |
| `hash_map` global-init | `<= 2026-02-01` | Reference issue when initialized as global fixed `2026-02-01` (changelog `Feb 1 → AngelScript`). | — | — |
| Overlay protection modes (Disabled / Default / Perceptproof) | `2026-03-31(b)` | Three-level dropdown (changelog `Mar 31 (b) → Perceptproof Overlay Protection`). | — | — |
| Stream Proof / Anti-Screenshot toggle | `2026-03-30(a)` | Re-added enable/disable option (changelog `Mar 30 (a)`); note `2026-03-30(b)` hardened it so stream proof "cannot be disabled". | — | — |
| Config/data encrypted as `.pak` | `2026-03-18` | All config + state encrypted (changelog `Mar 18 → Security`). Clear `Documents/My Games` before this update. | — | — |

---

## Removed / Deprecated APIs

| API | Status | Since | Replacement | Source row |
|-----|--------|-------|-------------|------------|
| `source2_world_to_screen` | Deprecated | `2026-02-03(b)` | `world_to_screen_rowmajor` (row-major) / `world_to_screen_transposed` (transposed/column-major) | changelog `Feb 3 (b) → AngelScript & Lua → Deprecated`; also `Mar 16` cheatsheet note |
| default `matrix4x4` read/write (no precision suffix) | Deprecated | `2026-02-03(b)` | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` | changelog `Feb 3 (b) → Deprecated` |
| `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64` | Removed (never actually existed) | `2026-03-14` | `scan_float` / `scan_double` / `scan_string` / `scan_wstring` / `scan_pointer` | changelog `Mar 14 → VAD / Memory Scan API Fixes`, "Removed nonexistent functions from docs" |
| Legacy RE tools + old chatbot | Removed | `2026-03-08` | New RE tools GUI + IDE AI assistant (same release) | changelog `Mar 8` |
| IDE + Analyzer | Discontinued | `Enma Open Beta — Phase 2 (May 2026)` | Perception MCP (60-70+ tools) | changelog `Enma Open Beta — Phase 2` |

`scan_bytes` and friends were doc-only ghosts — they never shipped, so calling them
fails on **every** build. The `Since` of `2026-03-14` marks when they were struck from
the docs, not when they worked.

---

## Language Version Quirks

PCX has hosted three scripting front-ends. The timeline below is what the changelog
and `docs/` support; exact per-feature introduction dates inside a language reference
that ships unversioned are marked `unknown`.

### Front-end split history

| Era | Languages | Evidence |
|-----|-----------|----------|
| `<= 2026-03` | AngelScript + Lua | Changelog entries split between `AngelScript` (AS-only) and `AngelScript & Lua` (both) throughout Feb–Mar 2026. `2026-03-11`: "Perception API IntelliSense injects both AngelScript and Lua API references". |
| `Enma Open Beta — Phase 2 (May 2026)` | Enma (new, proprietary AOT/JIT) added | Changelog `Enma Open Beta — Phase 2`: "Perception's proprietary programming language, built from scratch … compiles to native machine code". |

**AS-only vs AS+Lua intrinsics** (from the changelog's section headers):

| Feature | Scope at introduction | Since |
|---------|-----------------------|-------|
| `get_all_hwnds()` | AngelScript & Lua | `2026-02-01` |
| `create_font` / `create_font_mem` `glyph_ranges` | AngelScript & Lua | `2026-02-03(b)` |
| `mat4.readas_*` / `writeas_*` precision variants | AngelScript & Lua | `2026-02-03(b)` |
| `world_to_screen_rowmajor` / `_transposed` | AngelScript & Lua | `2026-02-03(b)` |
| `atomic_int32` / `atomic_int64` | **AngelScript only** | `2026-02-03(b)` |
| `set_thread_to_*_priority` | **AngelScript only** | `2026-02-03(b)` |
| `hash_map` global-init fix | **AngelScript only** | `2026-02-01` |
| `get_gui_position` / `get_gui_size` | **AngelScript only** | `2026-02-12` |
| `register_callback` `render_on_top` | **AngelScript only** | `2026-03-17(b)` |
| Unicorn `UC_HOOK_*`, `uc_get_*_exception*` | **AngelScript only** | `2026-03-18` |

Treat AngelScript-only rows as **not present in Lua** at that date unless a later
`AngelScript & Lua` entry restates them.

### Enma

Enma is documented in `docs/enma/` as a single unversioned reference. The only dated
anchor is the changelog's `Enma Open Beta — Phase 2 (May 2026)`. Every Enma language
feature below is therefore `<= Enma Open Beta Phase 2 (May 2026)`; an exact
introduction version is `unknown`.

| Feature | Available | Notes / source |
|---------|-----------|----------------|
| Full-module AOT + JIT to native x64 | `<= Enma Open Beta Phase 2 (May 2026)` | changelog `Enma Open Beta — Phase 2`; `docs/enma/llms-language.md §0` |
| Annotations (`[[...]]`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-annotations.md` |
| FFI (`[[dll(...)]]`, requires `PERM_FFI`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-advanced.md → FFI` |
| Coroutines (`coroutine` / `yield` / `coroutine_t`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-advanced.md → Coroutines`; runtime-auto-registered per `addon-core.md` |
| `defer`, `match`, `goto`, exceptions | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/llms-language.md §5` |
| Atomic types (`aint8/16/32/64`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/llms-language.md §2`; `addon-atomic.md` |
| Preprocessor (`#define`, `#if`/`#ifdef`, `#include`, SDK `define()`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-pre-processor.md` |

No Enma changelog predates the May 2026 Open Beta Phase 2 post, so anything finer than
"present in Open Beta Phase 2" is a guess and is left `unknown` here.

### AngelScript

PCX's AngelScript dialect is the historical default (pre-Enma). Feature deltas that
are dated land in the AS-specific rows of the matrix above (atomics, thread priority,
`render_on_top`, Unicorn hooks, etc.). The base AngelScript language itself is the
upstream AngelScript spec; PCX does not changelog core-language grammar changes.

### Lua

PCX exposes a Lua binding alongside AngelScript through `2026-03`. Only the
`AngelScript & Lua` changelog rows apply to it (font `glyph_ranges`, matrix precision
variants, W2S replacement, `get_all_hwnds`). No Lua-only language feature is dated in
the changelog; assume the AS+Lua shared surface and nothing more.

---

## Release Timeline Index

Reverse-chronological. Each row lists the script-facing API surface a release
introduced or changed, so a `// Requires:` pin can be picked from the oldest
release carrying every API a script needs. Pure IDE/Analyzer/decompiler internals
(no script API) are omitted; see `docs/perception/changelogs.md` for the full text.

| Release | Script-facing API added / changed |
|---------|-----------------------------------|
| `Enma Open Beta — Phase 2 (May 2026)` | Enma language added (AOT/JIT); Perception MCP (60-70+ tools); IDE + Analyzer discontinued |
| `2026-04-06` | Analyzer memory usage reduced; no script-facing API changes |
| `2026-03-31(b)` | Overlay protection modes: Disabled / Default / Perceptproof |
| `2026-03-30(b)` | GUI taskbar + force-on-top; stream proof hardened (no longer disableable) |
| `2026-03-30(a)` | Stream Proof / Anti-Screenshot enable-disable toggle re-added |
| `2026-03-20` | Fullscreen mode (universal); `alloc_vm`/`free_vm` rework (CFG-disable + Insecure API to execute) |
| `2026-03-18` | Unicorn `UC_HOOK_INSN_INVALID`, `UC_HOOK_INTR`, `uc_get_last_exception`, `uc_get_exception_address`, graceful null deref; config `.pak` encryption; GUI force render key |
| `2026-03-17(b)` | `register_callback` `render_on_top` arg; `get_gui_pos` position fix |
| `2026-03-17(a)` | Custom Draw 3D/compute: `create_index_buffer`, `custom_draw_indexed`, `create_depth_buffer`/`create_depth_stencil_state`, `custom_set_render_target_ext`, `create_rasterizer_state`, `custom_set_viewport`, `custom_bind_textures`, `custom_bind_constant_buffers`, `create_compute_shader`/`dispatch_compute`/`create_structured_buffer`/`read_structured_buffer`, `load_obj_mesh`, dynamic textures, `capture_backbuffer`, `custom_resolve_render_target` |
| `2026-03-16` | Custom Draw base pipeline: `create_shader`, `create_vertex_buffer`, `create_constant_buffer`, `create_blend_state`, `create_sampler`, `create_texture`, `create_render_target` (Universal + CS2) |
| `2026-03-14` | Sound API (entire surface); scan `scan_float/double/string/wstring/pointer` + `array<uint64>@` return; `get_vad_snapshot` fix; `scan_bytes`/`scan_all_*` struck from docs; Extensions system |
| `2026-03-11` | Combined AngelScript + Lua API IntelliSense; multi-root workspace |
| `2026-03-08` | 32-bit games support; legacy RE tools + old chatbot removed |
| `2026-02-17` | GUI list ops: `list:get/remove/highlight/remove_highlight/hide/show` |
| `2026-02-12` | XINPUT controller keybinds; `get_mouse_delta` fix; `get_gui_position`/`get_gui_size`; render order reversed |
| `2026-02-03(b)` | `world_to_screen_rowmajor`/`_transposed` (deprecate `source2_world_to_screen`); `mat4.readas_*`/`writeas_*` (deprecate default matrix r/w); `atomic_int32/64`; `set_thread_to_*_priority`; `create_font`/`create_font_mem` `glyph_ranges`; instant font load |
| `2026-02-03(a)` | `source2_world_to_screen` optional `viewport` arg; list selected-index fix |
| `2026-02-01` | `get_all_hwnds()`; `hash_map` global-init fix |
| `<= 2026-02-01` | Core surfaces (proc r/w + typed reads, render 2D, GUI sections, input, net, win, filesystem, CPU/time, Zydis, Unicorn base) predate the dated changelog window |

---

## Cross-References

- `docs/perception/changelogs.md` — the live primary source; every `Since` here traces to a dated row in it. Re-read it when a new release lands and update this matrix.
- `knowledge/pcx-api-cheatsheet.md` — the full current API surface this matrix versions.
- `docs/perception/render-api.md`, `proc-api.md`, `gui-api.md`, `input-api.md`, `sound-api.md`, `net-api.md`, `win-api.md`, `filesystem-api.md`, `unicorn-api.md`, `zydis-api.md`, `cpu-api.md`, `custom-draw-api.md`, `extensions-api.md` — per-API signatures.
- `docs/enma/llms-language.md`, `lang-pre-processor.md`, `lang-annotations.md`, `lang-advanced.md` — Enma language reference for the Language Version Quirks section.
- `skill://pcx-angelscript-discipline` — AngelScript usage discipline.
- `.claude/skills/game-cheat-guidelines/SKILL.md` — the 12 rules every script in this repo follows.

---

## Source: `knowledge/script-organization-patterns.md`

# Script Organization Patterns

How an Enma project on Perception.cx is laid out once it grows past a single
feature. This file picks up where `templates/full-project/` stops: that scaffold
is five files and one feature; here we cover the patterns that emerge at scale —
ten or twenty features, persistent config, multiple binaries, shared utility
modules, and more than one script alive in the same session.

> **Read this before** turning the `templates/full-project/` scaffold into a real
> multi-feature project. The five-file layout is the *starting point*; everything
> below extends it without re-architecting it. If you are writing a single
> overlay, stop at the scaffold — none of this earns its keep yet.

The one rule the whole toolkit agrees on (`game-cheat-guidelines` #6, *one
feature, one file*) is the floor, not the ceiling. The hard questions start the
moment two features want the same offset, the same `world_to_screen`, or the same
config file. This is the decision guide for those questions.

---

## The 5-file baseline (review)

The scaffold in `templates/full-project/` is the smallest layout that already
honors the guidelines. Five files, one direction of dependency, one bundle order:

```
templates/full-project/
├── globals.em   # proc_t, module base/size, config bound to GUI
├── offsets.em   # named sigs + RIP-relative resolver (imports globals)
├── feature.em   # one feature: update reads, render draws (imports globals, offsets)
├── menu.em      # GUI sidebar + config save/load (imports globals)
└── main.em      # main(): attach, resolve, setup_menu, register routines
```

Bundle order is the dependency order: `globals → offsets → feature → menu →
main`. Nothing imports `main`; `globals` imports nothing project-local. Every
other file reaches *down* toward `globals`, never sideways into a sibling
feature. Keep that arrow pointing one way and the project stays reloadable.

Everything in this document is a way of adding files to that picture *without*
breaking the arrow. When a new pattern tempts you to make `feature_a.em` import
`feature_b.em`, that is the signal that the shared thing belongs in `globals.em`
or a new utility module — not in a sibling.

---

## Shared state: what goes where

**`globals.em` holds state every feature reads. A feature's own tuning lives in
the feature file.** The test: if exactly one feature cares about a variable, it
is not global.

Cross-feature state — the process handle, the module base/size, the resolved
entity-list pointer, a per-tick entity cache — belongs in `globals.em` because
ESP, radar, and aimbot all read the same entities and you walk that list once
(rule #4, separate scan from render; rule #6, don't duplicate reads). Per-feature
tuning — ESP box thickness, aimbot smoothing, radar zoom — belongs to the feature
that owns it, bound to that feature's own GUI section (rule #11).

```cpp
// globals.em — cross-feature state ONLY
import "vec";

proc_t g_proc;
uint64 g_base = 0;            // uint64 always (rule #2)
uint64 g_size = 0;
uint64 g_entity_list = 0;     // resolved once, read by every feature
bool   g_initialized = false;

// One shared entity cache, filled by a single walk in a shared update routine.
array<uint64> g_entities;     // valid entity bases this tick
array<vec3>   g_positions;    // world positions, parallel to g_entities
```

```cpp
// esp.em — this feature's tuning is private to this file
import "vec";
import "color";
import "globals";

bool    g_esp_enabled  = true;   // ESP owns these, not globals.em
float64 g_esp_distance = 3000.0;
color   g_esp_color    = color(80, 170, 255, 220);

void esp_render(int64 data) {
    if (!g_esp_enabled || !g_initialized) return;
    color box = color(80, 170, 255, 220);   // construct per frame (rule #7)
    for (int32 i = 0; i < g_positions.length(); i++) {
        // draw from the shared cache — esp.em never walks the list itself
    }
}
```

**Anti-pattern: a feature writing into another feature's variables.** If `aim.em`
flips `g_esp_color` to flag its current target, you now have two files that can
change one variable and a hot-reload of either that desyncs the other.

```cpp
// WRONG — aim.em reaches into esp.em's state
g_esp_color = color(255, 0, 0, 255);   // "highlight the aim target"

// RIGHT — shared intent goes through globals.em, each feature reads it
// globals.em:  uint64 g_aim_target = 0;
// aim.em:      g_aim_target = best;          // aim owns the write
// esp.em:      if (g_entities[i] == g_aim_target) box = color(255,0,0,255);  // esp owns the read
```

The rule: **a global has exactly one writer.** Many readers are fine; two writers
is a bug waiting for a patch day.

---

## Offset modules: one per binary, not one per feature

**Sigs are grouped by the binary they scan, never by the feature that consumes
them.** Almost every project targets one module and `offsets.em` is enough. The
pattern only branches when you legitimately read two binaries — a game plus its
anti-cheat-adjacent helper DLL, or a launcher plus the game.

```
offsets-game.em      # sigs scanned in game.exe
offsets-engine.em    # sigs scanned in engine.dll
```

Each offset module owns its own base/size and resolves against it; a feature
imports whichever module holds the sig it needs.

```cpp
// offsets-game.em — sigs for game.exe (cite each, rule #1 / #5)
import "globals";

// CEntityList global — LEA RCX, [rip+????]   (sig from IDA, not a hardcode)
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";

bool resolve_game() {
    uint64 hit = g_proc.find_code_pattern(g_base, g_size, SIG_ENTITY_LIST);
    if (hit == 0) { println("[offsets-game] SIG_ENTITY_LIST stale"); return false; }
    int32 disp = g_proc.r32(hit + 3);                       // RIP-relative, 4 bytes
    g_entity_list = hit + 7 + cast<uint64>(disp);           // end-of-insn + disp
    return g_entity_list != 0;                              // validate (rule #3)
}
```

**The hard rule: a signature is defined exactly once.** The moment the same byte
pattern appears in two feature files, a patch breaks one copy and not the other,
and you debug a "half-working" cheat. If two features need `SIG_ENTITY_LIST`,
both import the offset module — they never re-declare the constant.

```
// WRONG: SIG_ENTITY_LIST pasted into both esp.em and radar.em
// RIGHT: declared in offsets-game.em; esp.em and radar.em both `import "offsets-game";`
```

---

## Config persistence pattern

**Serialize GUI state to a JSON file with the JSON addon, load it in `main()`
before building the menu, and save it on an explicit trigger.** There is no
unload callback to hook — see the lifecycle note below — so saving is something
*you* invoke, not something the host does for you.

Load first so widgets come up showing the saved values; the scaffold's
`setup_menu()` already calls `load_config()` at its top. Use the documented
filesystem API (`fs_read_file` / `fs_write_file` / `fs_file_exists`, all gated by
`file_system_access`) and the JSON addon (`json_parse`, `json_object`,
`.set_key` / `.get_key`, `.stringify()` / `.pretty()`).

```cpp
// menu.em — JSON config persistence
import "globals";

const string CFG_PATH = "configs/active.json";

void save_config() {
    json_value root = json_object();
    root.set_key("enabled",      json_parse(to_string(g_esp_enabled)));
    root.set_key("max_distance", json_parse(to_string(g_esp_distance)));
    root.set_key("hotkey",       json_parse(to_string(g_aim_hotkey)));

    if (!fs_dir_exists("configs")) fs_create_directory("configs");
    if (!fs_write_file(CFG_PATH, root.pretty()))     // pretty() so it's hand-editable
        println("[cfg] save failed — check file_system_access permission");
}

void load_config() {
    if (!fs_file_exists(CFG_PATH)) return;           // first run: keep defaults
    json_value root = json_parse(fs_read_file(CFG_PATH));
    if (!root.is_valid()) { println("[cfg] corrupt, using defaults"); return; }

    if (root.has_key("enabled"))      g_esp_enabled  = root.get_key("enabled").as_bool();
    if (root.has_key("max_distance")) g_esp_distance = root.get_key("max_distance").as_num();
    if (root.has_key("hotkey"))       g_aim_hotkey   = cast<int32>(root.get_key("hotkey").as_int());
}
```

`json_parse` returns an invalid value (not a throw) on malformed input, so the
`is_valid()` guard is the whole error path — a truncated or hand-broken config
falls back to defaults instead of taking the script down. `has_key` before
`get_key` means a config written by an older build (missing a field you added
later) loads cleanly: unknown-to-old and missing-from-new both degrade to the
default. That forward/backward tolerance is the reason to prefer JSON objects over
the positional `key=value` text format the scaffold ships with.

**Lifecycle reality — there is no `on_unload` hook.** Per
`docs/perception/lifecycle-and-routines.md`, a script unloads when `main()`
returns `<= 0`, when the user unloads it, or when the host shuts down; routines
simply stop and render resources are freed automatically. Nothing runs *your*
code on the way out. So persistence is triggered one of three ways:

- **Save button** — `section_button(sec, "Save Config", cast<int64>(save_config))`.
  Explicit, zero overhead, what the scaffold uses.
- **Save hotkey** — check `key_fired(g_save_key)` in a routine, call
  `save_config()` on the edge. Convenient mid-game.
- **Autosave on change** — diff GUI state in the update routine and save when it
  moves. Simplest to reason about, but it writes to disk during gameplay; gate it
  behind a debounce so a slider drag isn't a hundred file writes.

```cpp
// defer: explicit Save button only. Autosave-on-change when users complain
//        about losing edits; debounce it so a slider drag isn't N disk writes.
```

---

## Multi-script coordination

Sometimes you want two scripts loaded in the same PCX session — a stable "base"
script you trust, plus a "wip" experimental overlay you reload constantly without
risking the base. The question is whether they can share state, and the honest
answer is *mostly no, and that's usually fine*.

The scripting layer exposes **no IPC primitive** — no named pipes, no shared
memory between scripts. Do not invent one. The filesystem is **sandboxed to a
per-script data root** (`docs/perception/filesystem-api.md`), so a file written
by script A is not guaranteed visible to script B; treat cross-script file
sharing as unsupported unless you have verified on your install that both scripts
resolve to the same root. That leaves three real options:

| Approach | How | When it's worth it |
| --- | --- | --- |
| **Don't share** (default) | Each script attaches its own `proc_t`, resolves its own offsets, walks its own list | Almost always. Duplicate reads are cheap next to the simplicity |
| **Shared file** | One script writes `state/shared.json`, the other polls it | Only if both resolve to the same sandbox root *and* the data is slow-changing (resolved offsets, target id) |
| **Single script, two modules** | Collapse both into one script; the "experimental" part is just another feature file you hot-reload | When you actually need shared live state — this is the supported way to get it |

**The tradeoff is duplicate reads vs. coupling.** Two independent scripts each
walking the entity list costs you two walks per tick — measurable only if the
list is huge. Sharing state via a file couples their reload cycles and adds a
parse on every poll. The "single script, two feature modules" path gives you true
shared state for free (it's just `globals.em` again) at the cost of the isolation
you wanted in the first place. Pick duplication unless a profiler says otherwise.

```cpp
// defer: two independent scripts, duplicate entity walks accepted.
//        Merge into one script with shared globals.em if the double walk
//        shows up in the frame budget.
```

---

## Utility modules: when extraction pays off

**`world_to_screen` lives in exactly one place. So does the pattern-scan
resolver. So does the bone-matrix unpacker.** A second copy of W2S is a second
place to get the behind-camera check wrong (rule #10).

The extraction heuristic is a counting rule, straight from
`pcx-coding-discipline` #5 (*deletion before addition*):

- **3+ features need it → utility module.** Extract to `util-math.em` (or
  `util-mem.em`) and import it everywhere. The shared definition is now the only
  one to fix after a patch.
- **Exactly 2 features need it → leave it duplicated.** Two copies you can see is
  cheaper to reason about than one indirection you have to chase, and the second
  caller is not yet proof the abstraction is right.
- **1 feature needs it → inline it.** A wrapper with one caller adds a name, not
  value. Inline the body.

```cpp
// util-math.em — shared because esp, radar, AND aim all project to screen (3 callers)
import "vec";
import "globals";

bool world_to_screen(vec3 world, out vec2 screen) {
    uint64 m = g_view_matrix;                       // resolved in globals/offsets
    float64 w = g_proc.rf32(m + 12) * world.x
              + g_proc.rf32(m + 28) * world.y
              + g_proc.rf32(m + 44) * world.z
              + g_proc.rf32(m + 60);
    if (w < 0.001) return false;                    // behind camera (rule #10)
    float64 inv = 1.0 / w;
    float64 nx = (g_proc.rf32(m + 0)  * world.x + g_proc.rf32(m + 16) * world.y
                + g_proc.rf32(m + 32) * world.z + g_proc.rf32(m + 48)) * inv;
    float64 ny = (g_proc.rf32(m + 4)  * world.x + g_proc.rf32(m + 20) * world.y
                + g_proc.rf32(m + 36) * world.z + g_proc.rf32(m + 52)) * inv;
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

```cpp
// WRONG — esp.em and radar.em each carry their own W2S; one gets the w-check
//         fixed after a patch, the other still mirrors points behind the camera.
// RIGHT — both `import "util-math";` and call world_to_screen(); one definition.
```

Resist extracting too early. A `util-mem.em` that wraps `g_proc.ru64` in
`read_ptr()` is the one-caller mistake even when three features call it — the
`proc_t` API *is* the interface (rule from `pcx-coding-discipline` #5). Extract
behavior with real logic (W2S, the RIP resolver, bone unpacking), not one-line
passthroughs.

---

## Feature toggles in `main()` vs the feature module

**Two different switches, two different homes.** Conflating them is why a feature
"won't turn off" or "won't turn on."

- **Load switch — does the feature exist at all this session?** Lives in
  `main()`, as whether you call `register_routine` for it. An unregistered
  feature costs zero per frame; its file can even be absent from the bundle.
- **Runtime switch — is the loaded feature drawing right now?** Lives in the
  feature's own GUI checkbox, read at the top of its routine.

```cpp
// main.em — LOAD switch: register or don't. Comment out the line to drop a feature.
int64 main() {
    // ... attach, resolve ...
    setup_menu();
    register_routine(cast<int64>(esp_update),   0);
    register_routine(cast<int64>(esp_render),   0);
    register_routine(cast<int64>(radar_render), 0);
    // register_routine(cast<int64>(aim_update), 0);   // aim left out this build
    g_initialized = true;
    return 1;
}
```

```cpp
// esp.em — RUNTIME switch: the registered routine early-outs when the box is off.
void esp_render(int64 data) {
    if (!g_esp_enabled || !g_initialized) return;     // GUI checkbox (rule #11)
    // ... draw ...
}
```

**Why both:** the load switch is your kill switch — a feature you suspect is
crashing or detectable, you drop by deleting one `register_routine` line and
reloading, with no per-frame cost and no risk it runs. The runtime switch is the
user-facing toggle for a feature you trust enough to ship. A feature with only a
runtime toggle still executes its early-out every frame even when "off"; a
feature with only a load switch can't be turned off without a reload. You want
both levers.

---

## Module-version pinning

**A feature that depends on a specific shape of `globals.em` says so at the top of
its file.** When you change a shared structure, this comment is the list of files
to revisit — Enma won't warn you that `feature.em` expected the old layout, it
will just read the wrong field.

The pattern is a `// requires:` line naming the shared contract the feature was
written against:

```cpp
// radar.em
// requires: globals v2  (g_entities as flat array<uint64>, g_positions parallel)
import "globals";

void radar_render(int64 data) {
    for (int32 i = 0; i < g_positions.length(); i++) {
        // assumes g_positions[i] pairs with g_entities[i] — the v2 contract
    }
}
```

When you bump `globals.em` — say you replace the two parallel arrays with a single
`array<entity_t>` — grep for `requires: globals v2` and every file that needs
updating is named for you. Bump the version in `globals.em`'s header comment and
update each `requires:` as you migrate it:

```cpp
// globals.em
// version: v3  (g_entities is now array<entity_t>; v2 parallel arrays removed)
```

This is documentation, not a runtime check — there is no module-version assert in
the language. Its whole value is that the next reader (often you, post-patch) sees
the dependency without reverse-engineering it. Keep the line honest or delete it;
a stale `requires:` is worse than none.

---

## Dead-code elimination

**A feature you stopped using: drop it from the bundle order, comment out its
`register_routine`, rename the file so it's visibly inactive — but keep it in the
tree.** Don't `git rm` it.

The reasoning is specific to this domain. A feature file is a worked record of a
sig, a struct layout, and the math that turned them into an overlay — knowledge
that took an IDA session to produce. After a patch the *code* is stale but the
*structure* is still the fastest way back: you re-sig, re-verify the offsets, and
the feature is alive again. Git-deleting it buries that record in history where
future-you won't think to look.

The compromise that keeps it from rotting silently: **rename to
`feature-dead-<name>.em`** so it's unmistakably inactive at a glance, and remove
its routine registration so nothing runs it.

```cpp
// main.em
import "esp";
import "radar";
// import "feature-dead-aim";   // parked: offsets stale since the season patch

int64 main() {
    register_routine(cast<int64>(esp_render),   0);
    register_routine(cast<int64>(radar_render), 0);
    // register_routine(cast<int64>(aim_update), 0);   // dead: see feature-dead-aim.em
    return 1;
}
```

```
project/
├── esp.em
├── radar.em
└── feature-dead-aim.em    # inactive, kept as a re-sig starting point
```

The `dead-` prefix is the signal to every tool and reader that this file is not
in the build. When you revive it, rename back to `aim.em`, re-verify the sigs
against the live binary (`game-cheat-guidelines` #12), and re-add the
registration.

---

## The shape of a 20-feature project

A project with many features, two target binaries, and shared utilities still
keeps the one-way dependency arrow from the scaffold — it just has more files at
each layer. Features depend on utils and offsets; utils and offsets depend on
globals; nothing depends on a sibling feature.

```
project/
├── globals.em             # version: v3 — proc_t, bases, shared entity cache
│
├── offsets-game.em        # sigs scanned in game.exe
├── offsets-engine.em      # sigs scanned in engine.dll
│
├── util-math.em           # world_to_screen, angle math   (3+ callers)
├── util-mem.em            # RIP resolver, bone-matrix unpack (3+ callers)
│
├── esp.em                 # requires: globals v3
├── radar.em               # requires: globals v3
├── glow.em                # requires: globals v3
├── aim.em                 # requires: globals v3, offsets-game
├── triggerbot.em          # requires: globals v3, offsets-game
├── nospread.em            # requires: globals v3, offsets-engine
├── loot-esp.em            # requires: globals v3, offsets-game
├── spectator-list.em      # requires: globals v3, offsets-engine
├── ...                    # (more features, each one file)
├── feature-dead-bhop.em   # parked: re-sig after patch
│
├── menu.em                # GUI sections + JSON config persistence
└── main.em                # attach, resolve_game/resolve_engine, register all
```

Dependency direction, top to bottom:

```
  main.em  ──registers──>  every feature
     │
  menu.em  ──reads/writes──>  each feature's config + globals
     │
  esp / radar / aim / ...  ──import──>  util-math, util-mem, offsets-*
     │
  util-*, offsets-*  ──import──>  globals.em
     │
  globals.em  ──imports──>  vec, color   (engine modules only)
```

`main()` grows linearly: resolve each binary, then one `register_routine` per
active feature. `menu.em` grows one `create_section` per feature. Everything else
stays a single file you can reload in isolation — which is the entire point of the
split, and the reason a 20-feature project is still tractable when a single
2000-line `cheat.em` would not be.

---

## Anti-Patterns

A flat list of organizational mistakes and the consequence each one buys you:

- **Monolithic `cheat.em`** — every feature in one file; a hot-reload to fix one
  box re-runs and can break all twenty. Split per feature (#6).
- **Duplicate sig definitions** — the same byte pattern declared in two feature
  files; a patch breaks one copy, you ship a half-working cheat. One sig, one
  module.
- **Features mutating each other's state** — two writers on one global; reload
  either and they desync. One writer per global, many readers.
- **`feature_a.em` importing `feature_b.em`** — sideways dependency; now neither
  reloads cleanly. Shared things go down into `globals.em` or a util module.
- **GUI widgets created in an update/render loop** — `create_section` /
  `section_checkbox` belong in `setup_menu()` run once, not per frame. Per-frame
  widget creation duplicates state and tanks the frame budget (#11).
- **Reading widget state deep inside nested loops** — read the toggle once at the
  top of the routine, then branch; don't re-read per entity.
- **Per-binary offset files split by feature instead** — `esp-offsets.em` +
  `radar-offsets.em` for the same game.exe re-declares shared sigs. Group offsets
  by binary, not by consumer.
- **Caching colors/vecs in globals "to avoid allocation"** — they're stack value
  types; the global only adds mutable state. Construct per frame (#7).
- **One-caller utility wrappers** — `read_ptr()` around a single `g_proc.ru64`
  adds a name, not value. Inline until 3 callers earn the extraction.
- **Config saved on a nonexistent unload hook** — there is no `on_unload`; the
  save never fires. Trigger saves from a button, hotkey, or debounced autosave.
- **Git-deleting a patched-out feature** — buries the sig/struct knowledge in
  history. Rename to `feature-dead-<name>.em` and keep it.
- **Stale `requires:` comments** — a version pin that no longer matches
  `globals.em` misleads the next reader. Keep it honest or remove it.

---

## See Also

- `templates/full-project/` — the five-file scaffold this document extends;
  start there, grow into these patterns.
- `.claude/skills/game-cheat-guidelines/SKILL.md` — the code-shape rules every
  block here honors, especially #1 (ground offsets), #6 (one feature per file),
  and #11 (GUI for tunables).
- `.claude/skills/pcx-coding-discipline/SKILL.md` — the process layer: #5
  (deletion before addition) is the source of the utility-extraction counting
  rule.
- `knowledge/common-patterns.md` — the per-feature building blocks (W2S, entity
  iteration, config) these layouts arrange.
- `docs/enma/lang-modules.md` — the `import` / module-resolution mechanics behind
  the dependency arrow.
- `docs/enma/addon-json.md` and `docs/perception/filesystem-api.md` — the real
  JSON and sandboxed-filesystem APIs used by the config-persistence pattern.
- `docs/perception/lifecycle-and-routines.md` — why there is no unload hook and
  how `register_routine` makes the load switch.
