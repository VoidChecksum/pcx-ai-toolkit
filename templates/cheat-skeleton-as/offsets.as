// offsets.as — signatures and resolution helpers
namespace Cheat {

// Placeholder signatures. Replace after dumping with IDA/ReClass.
const string SIG_ENTITY_LIST  = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ??"; // UNVERIFIED
const string SIG_LOCAL_PLAYER = "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ??"; // UNVERIFIED
const string SIG_VIEW_MATRIX  = "48 8D 05 ?? ?? ?? ?? 48 89 ?? 48 ?? ??"; // UNVERIFIED

// Resolve RIP-relative mov/lea instruction: hit + displacement + instruction length.
uint64 resolve_rip(uint64 hit, int disp_off, int insn_len) {
    if (hit == 0) return 0;
    int disp = g_proc.r32(hit + uint64(disp_off));
    return hit + uint64(insn_len) + uint64(disp);
}

// Resolve all signatures. Return false if any signature is stale.
bool resolve_all() {
    if (!g_proc.alive() || g_base == 0 || g_size == 0) return false;

    uint64 hit_el = g_proc.find_code_pattern(g_base, g_size, SIG_ENTITY_LIST);
    if (hit_el == 0) { println("[offsets] entity_list sig stale"); return false; }
    g_entity_list = resolve_rip(hit_el, 3, 7);

    uint64 hit_lp = g_proc.find_code_pattern(g_base, g_size, SIG_LOCAL_PLAYER);
    if (hit_lp == 0) { println("[offsets] local_player sig stale"); return false; }
    g_local_player = resolve_rip(hit_lp, 3, 7);

    uint64 hit_vm = g_proc.find_code_pattern(g_base, g_size, SIG_VIEW_MATRIX);
    if (hit_vm == 0) { println("[offsets] view_matrix sig stale"); return false; }
    g_view_matrix = resolve_rip(hit_vm, 3, 7);

    return g_entity_list != 0 && g_local_player != 0 && g_view_matrix != 0;
}

}
