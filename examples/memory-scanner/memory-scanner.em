// memory-scanner.em — current Enma pattern scanning and RIP-resolution example.
// Replace TARGET_MODULE and SIG_* values with signatures verified for your target.

const string TARGET_MODULE = "game.exe";
const string SIG_LOCAL_PLAYER = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74"; // UNVERIFIED
const string SIG_ENTITY_LIST  = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ??"; // UNVERIFIED

proc_t g_proc;
uint64 g_base = 0;
uint64 g_size = 0;
uint64 g_local_player_slot = 0;
uint64 g_entity_list_slot = 0;
bool g_resolved = false;

uint64 resolve_rip(uint64 hit, int32 disp_off, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + cast<uint64>(disp_off));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}

bool resolve_offsets() {
    if (!g_proc.alive()) return false;

    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size(TARGET_MODULE);
    if (g_base == 0 || g_size == 0) {
        println("[scanner] module not ready");
        return false;
    }

    uint64 hit_local = g_proc.find_code_pattern(g_base, g_size, SIG_LOCAL_PLAYER);
    uint64 hit_entities = g_proc.find_code_pattern(g_base, g_size, SIG_ENTITY_LIST);
    if (hit_local == 0 || hit_entities == 0) {
        println("[scanner] signature miss; update SIG_* for this build");
        return false;
    }

    g_local_player_slot = resolve_rip(hit_local, 3, 7);
    g_entity_list_slot = resolve_rip(hit_entities, 3, 7);
    g_resolved = g_local_player_slot != 0 && g_entity_list_slot != 0;
    return g_resolved;
}

void on_update(int64 data) {
    if (!g_resolved || !g_proc.alive()) return;

    uint64 local = g_proc.ru64(g_local_player_slot);
    uint64 entities = g_proc.ru64(g_entity_list_slot);
    if (local == 0 || entities == 0) return;

    // Add target-specific reads here after validating every pointer hop.
}

int64 main() {
    g_proc = ref_process(TARGET_MODULE);
    if (!g_proc.alive()) {
        println("[scanner] target not found");
        return 0;
    }
    if (!resolve_offsets()) return 0;

    register_routine(cast<int64>(on_update), 0);
    println("[scanner] loaded");
    return 1;
}
