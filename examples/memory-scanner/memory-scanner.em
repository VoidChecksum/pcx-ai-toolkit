// memory-scanner.em — Pattern scanning and offset resolution example
// Demonstrates: sig-based scanning, RIP-relative address resolution, offset caching
// This is the correct way to handle post-patch resilience (Guideline #5).
// Lint: pcx lint memory-scanner.em

import "proc";

// ============================================================
// SIGNATURES — byte patterns to locate code/data in memory
// 0x?? = wildcard byte (any value matches at that position)
// The patterns land on the instruction; we resolve the RIP-relative address below.
// ============================================================
array<uint8> SIG_LOCAL_PLAYER = {
    0x48, 0x8B, 0x0D, 0x??, 0x??, 0x??, 0x??,  // mov rcx, [rip+disp32]
    0x48, 0x85, 0xC9                              // test rcx, rcx
};

array<uint8> SIG_ENTITY_LIST = {
    0x4C, 0x8B, 0x0D, 0x??, 0x??, 0x??, 0x??,  // mov r9, [rip+disp32]
    0x45, 0x33, 0xC0                              // xor r8d, r8d
};

array<uint8> SIG_VIEW_MATRIX = {
    0x48, 0x8D, 0x0D, 0x??, 0x??, 0x??, 0x??,  // lea rcx, [rip+disp32]
    0xF3, 0x0F, 0x10, 0x01                        // movss xmm0, [rcx]
};

// ============================================================
// RESOLVED ADDRESSES — scanned once at startup, cached forever
// Avoids rescanning every frame (which would be slow and detectable).
// ============================================================
uint64 g_local_player_ptr = 0;   // pointer-to-pointer for local player
uint64 g_entity_list_ptr  = 0;   // pointer-to-entity-array
uint64 g_view_matrix_ptr  = 0;   // pointer to 4x4 view matrix
bool   g_offsets_resolved = false;

proc_t g_proc;

// ============================================================
// resolve_rip_relative()
// Helper: given the address of a [rip+disp32] instruction,
// compute the effective address.
//   scan_addr  = address returned by proc_find_pattern()
//   disp_off   = byte offset to the 4-byte displacement (usually 3)
//   instr_len  = full instruction length (used to advance RIP; usually 7)
// ============================================================
uint64 resolve_rip_relative(uint64 scan_addr, uint64 disp_off, uint64 instr_len) {
    // Read the 32-bit signed displacement
    uint32 raw = proc_read_uint32(g_proc, scan_addr + disp_off);
    int32  rel = cast<int32>(raw);   // reinterpret as signed for negative offsets

    // RIP points to the next instruction: scan_addr + instr_len
    // Effective address = RIP + signed_displacement
    uint64 rip = scan_addr + instr_len;
    // Cast carefully: signed int + uint64 requires explicit widening (Guideline #2)
    if (rel >= 0) {
        return rip + cast<uint64>(rel);
    } else {
        return rip - cast<uint64>(-rel);
    }
}

// ============================================================
// resolve_offsets() — scan once, cache forever
// Returns true if all patterns were found, false otherwise.
// ============================================================
bool resolve_offsets() {
    uint64 base = proc_module_base(g_proc, "game.exe");
    if (base == 0) {                          // Guideline #3: validate before use
        print("[Scanner] game.exe module not found");
        return false;
    }

    // Resolve local player pointer
    uint64 scan_lp = proc_find_pattern(g_proc, "game.exe", SIG_LOCAL_PLAYER);
    if (scan_lp == 0) {
        print("[Scanner] SIG_LOCAL_PLAYER not found — update the signature");
        return false;
    }
    // The mov instruction at scan_lp is 7 bytes: opcode(3) + disp32(4)
    g_local_player_ptr = resolve_rip_relative(scan_lp, 3, 7);

    // Resolve entity list pointer
    uint64 scan_el = proc_find_pattern(g_proc, "game.exe", SIG_ENTITY_LIST);
    if (scan_el == 0) {
        print("[Scanner] SIG_ENTITY_LIST not found — update the signature");
        return false;
    }
    g_entity_list_ptr = resolve_rip_relative(scan_el, 3, 7);

    // Resolve view matrix pointer
    uint64 scan_vm = proc_find_pattern(g_proc, "game.exe", SIG_VIEW_MATRIX);
    if (scan_vm == 0) {
        print("[Scanner] SIG_VIEW_MATRIX not found — update the signature");
        return false;
    }
    g_view_matrix_ptr = resolve_rip_relative(scan_vm, 3, 7);

    // Guideline #12: verify with live reads before trusting
    uint64 lp_test = proc_read_uint64(g_proc, g_local_player_ptr);
    print("[Scanner] Offsets resolved:");
    print("  local_player_ptr = 0x" + g_local_player_ptr + "  (points to: 0x" + lp_test + ")");
    print("  entity_list_ptr  = 0x" + g_entity_list_ptr);
    print("  view_matrix_ptr  = 0x" + g_view_matrix_ptr);

    if (lp_test == 0) {
        print("[Scanner] WARNING: local_player_ptr resolved but pointer is currently null (game not in-match?)");
        // Don't fail — this is expected when not in a game session
    }

    return true;
}

// ============================================================
// main() — open process, resolve offsets, register routine
// ============================================================
int32 main() {
    g_proc = proc_open("game.exe");
    if (!g_proc.valid()) {
        print("[Scanner] Failed to open game.exe — is it running?");
        return -1;
    }

    g_offsets_resolved = resolve_offsets();
    if (!g_offsets_resolved) {
        print("[Scanner] Offset resolution failed. The script will not function.");
        print("[Scanner] Update the SIG_* arrays for the current game version and reload.");
        return -1;
    }

    register_routine(cast<int64>(update_routine), null);
    return 1;  // stay loaded
}

// ============================================================
// update_routine — uses cached pointers (no re-scanning)
// ============================================================
void update_routine(void@ data) {
    if (!g_offsets_resolved) return;

    // Two-level dereference: ptr-to-ptr -> actual object (Guideline #3: null each step)
    uint64 local_player = proc_read_uint64(g_proc, g_local_player_ptr);
    if (local_player == 0) return;  // not in-match or pointer chain broken

    uint64 entity_list = proc_read_uint64(g_proc, g_entity_list_ptr);
    if (entity_list == 0) return;

    // ... use local_player and entity_list for feature logic
    // See esp-overlay.em for an example of entity iteration
}
