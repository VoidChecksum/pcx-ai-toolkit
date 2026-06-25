// esp-overlay.em — current Enma update/render split with source-backed APIs.
// This intentionally avoids undocumented W2S helpers; add projection only after
// verifying the target's matrix layout.

import "vec";
import "color";
import "strings";

const string TARGET_MODULE = "game.exe";
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ??"; // UNVERIFIED
const uint64 OFF_HEALTH = 0x200; // UNVERIFIED
const int32 MAX_ENTITIES = 64;

proc_t g_proc;
uint64 g_base = 0;
uint64 g_size = 0;
uint64 g_entity_list_slot = 0;
bool g_ready = false;

int32[] g_health;
int32 g_count = 0;

uint64 resolve_rip(uint64 hit, int32 disp_off, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + cast<uint64>(disp_off));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}

bool resolve_offsets() {
    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size(TARGET_MODULE);
    if (g_base == 0 || g_size == 0) return false;

    uint64 hit = g_proc.find_code_pattern(g_base, g_size, SIG_ENTITY_LIST);
    if (hit == 0) {
        println("[esp] entity list signature stale");
        return false;
    }
    g_entity_list_slot = resolve_rip(hit, 3, 7);
    return g_entity_list_slot != 0;
}

void on_update(int64 data) {
    g_count = 0;
    if (!g_ready || !g_proc.alive()) return;

    uint64 entity_list = g_proc.ru64(g_entity_list_slot);
    if (entity_list == 0) return;

    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;

        int32 health = g_proc.r32(ent + OFF_HEALTH);
        if (health <= 0 || health > 999) continue;

        g_health[g_count] = health;
        g_count++;
        if (g_count >= MAX_ENTITIES) break;
    }
}

void on_render(int64 data) {
    if (!g_ready) return;

    color box = color(80, 170, 255, 220);
    color text = color(255, 255, 255, 255);
    color shadow = color(0, 0, 0, 180);

    for (int32 i = 0; i < g_count; i++) {
        float64 x = 24.0 + cast<float64>(i % 16) * 48.0;
        float64 y = 72.0 + cast<float64>(i / 16) * 48.0;
        draw_rect(vec2(x, y), vec2(34.0, 24.0), box, 1.0, 3.0, 15);
        draw_text(format("{d}", g_health[i]), vec2(x + 4.0, y + 4.0),
                  text, get_font18(), 1, shadow, 1.0);
    }
}

// Requires process_memory_read permission for ref_process/process reads.
int64 main() {
    g_proc = ref_process(TARGET_MODULE);
    if (!g_proc.alive()) return 0;
    if (!resolve_offsets()) return 0;

    g_health.resize(MAX_ENTITIES);
    g_ready = true;
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
