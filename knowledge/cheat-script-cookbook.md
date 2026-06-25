> **Scope:** Educational cookbook for Perception.cx cheat-script development. Authorized targets only — analyze software you own or have permission to test.

# Cheat Script Cookbook

This file is the practical companion to `game-cheat-guidelines` and `game-hacking-pcx`.
It contains small, reusable recipes for the most common cheat-script tasks. Copy
and adapt them inside your own projects; they follow the 12 guidelines and the
cheat-script master rules.

All examples are written in **Enma (`.em`)**. AngelScript (`.as`) is outside
this toolkit's active support; port old `.as` snippets to Enma before using
these recipes.

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
