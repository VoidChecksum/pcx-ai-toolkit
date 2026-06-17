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
