// offsets.as — pattern signatures, RIP-relative resolution, struct offsets.
//
// All sigs are hex bytes with `??` wildcards. Each sig was verified against
// r5apex_dx12_dump.exe (sha256:43681379...) using the python scanner in
// evidence/r5apex_dx12_dump_43681379.md. After a game update, rerun sigs and
// replace the ones that return 0 hits.
//
// Confidence per claim:
//   CONFIRMED — pattern hits exactly once in .text and resolves to live memory.
//   UNVERIFIED — value not yet verified against the live game process.
//
// Citations: E-NNN IDs cross-reference evidence/r5apex_dx12_dump_43681379.md.

#include "globals.as"

namespace VoidHook {

// ============================================================================
//  SIGNATURES — pattern bytes with wildcards. Replace after each Apex patch.
// ============================================================================

// E-001 — LocalPlayer slot. Pattern: MOV RDX, [rip+disp]; TEST RDX,RDX; JZ +0x40;
//         MOV EAX, [RDX+0x16C]; (m_iSignifierID accessed at +0x16C in C_Player)
// CONFIRMED — exactly one hit at .text rva 0x241D98 in this dump.
const string SIG_LOCAL_PLAYER =
    "48 8B 15 ?? ?? ?? ?? 48 85 D2 74 ?? 8B 82 6C 01 00 00";

// E-002 — CGameEntitySystem pointer. Pattern: MOV RCX, [rip+disp]; TEST RCX,RCX;
//         JZ +0x42; MOV RCX, [RCX+0x2A8]; (entity list lives at system+0x2A8)
// CONFIRMED — exactly one hit at .text rva 0x653C89 in this dump.
const string SIG_ENTITY_SYSTEM =
    "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 48 8B 89 ?? ?? ?? ??";

// E-003 — ViewMatrix global slot. Pattern: MOVSS XMM0, [rip+disp0]; store;
//         MOVSS XMM1, [rip+disp1]; store; (loads consecutive floats from VM)
// CONFIRMED — multiple instruction sites resolve to 0x88B42C0 (verified by
//            cross-referencing 6+ code sites reading from this slot).
const string SIG_VIEW_MATRIX =
    "F3 0F 10 05 ?? ?? ?? ?? F3 0F 11 ?? ?? F3 0F 10 0D ?? ?? ?? ?? F3 0F 11 ?? ??";

// ============================================================================
//  STRUCT OFFSETS — replace UNVERIFIED ones after live confirmation.
// ============================================================================

// CGameEntitySystem → m_pEntityList (IEntityList*)
// CONFIRMED via disasm at rva 0x653C89: the second MOV dereferences +0x2A8
// from the system pointer.
const uint64 OFF_ENTITY_LIST_IN_SYSTEM = 0x2A8;

// EntityHandle's "get index" / array indexing
// UNVERIFIED — Apex's CHandle layout varies; placeholder from r5sdk.
const uint64 OFF_ENTITY_HANDLE_INDEX  = 0x08;
const uint64 OFF_ENTITY_HANDLE_SERIAL = 0x0C;

// C_Player struct offsets (relative to the C_Player* base pointer).
// m_iSignifierID is CONFIRMED via the SIG_LOCAL_PLAYER disasm (E-001 entry).
// All others are PLACEHOLDERS — verify in-game by reading a known legend and
// matching against the visible state.
const uint64 OFF_HEALTH        = 0x043C;  // UNVERIFIED — placeholder; verify
const uint64 OFF_MAX_HEALTH    = 0x0440;  // UNVERIFIED — placeholder; verify
const uint64 OFF_TEAM          = 0x0448;  // UNVERIFIED — placeholder; verify
const uint64 OFF_LIFE_STATE    = 0x0690;  // UNVERIFIED — placeholder; verify
const uint64 OFF_SIGNIFIER_ID  = 0x016C;  // CONFIRMED (E-001 disasm)
const uint64 OFF_ORIGIN        = 0x017C;  // UNVERIFIED — placeholder; verify
const uint64 OFF_EYE_ANGLES    = 0x19B0;  // UNVERIFIED — placeholder; verify

// Head bone vertical offset (Apex character height for the standing head pose).
// UNVERIFIED — depends on the character's pose/bone. Used only as a fallback
// when a bone read fails.
const float PLAYER_HEAD_OFFSET_Z = 72.0f;

// ============================================================================
//  RIP-relative resolver + sig scanner (with uniqueness verification).
// ============================================================================

// Resolve a MOV reg, [rip+disp32] at `hit`: read 4-byte signed displacement at
// (hit + disp_off), add (hit + insn_len + disp).
//   disp_off = 3 for "48 8B/8D ?? 05/0D ?? ?? ?? ??" (7-byte REX+opcode+modrm+disp32)
//   disp_off = 4 for "F3 0F 10 05 ?? ?? ?? ??"       (8-byte legacy prefix + opcode + modrm + disp32)
uint64 resolve_rip(uint64 hit, int disp_off, int insn_len)
{
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + uint64(disp_off));
    int64 disp64 = int64(disp);              // sign-extend 32 → 64
    return hit + uint64(insn_len) + uint64(disp64);
}

// Verify a sig has exactly one hit in .text. If not, log and return 0.
uint64 verify_unique(uint64 search_start, uint64 search_size, const string &in sig)
{
    array<uint64> hits;
    g_proc.find_all_code_patterns(search_start, search_size, sig, hits);
    if (hits.length() == 0)
    {
        log("[VoidHook] sig MISS (0 hits): " + sig);
        return 0;
    }
    if (hits.length() > 1)
    {
        log("[VoidHook] sig AMBIGUOUS (" + hits.length() + " hits): " + sig);
        return 0;
    }
    return hits[0];
}

// Resolve all global slots. Returns false if any sig failed.
// Called from main() — runs every hot-reload.
bool resolve_all()
{
    if (!g_proc.alive() || g_base == 0 || g_size == 0)
    {
        log("[VoidHook] process not alive or module not ready");
        return false;
    }

    uint64 search_lo = g_base;
    uint64 search_hi = g_base + g_size;

    // E-001 — LocalPlayer
    uint64 hit_lp = verify_unique(search_lo, search_hi - search_lo, SIG_LOCAL_PLAYER);
    if (hit_lp == 0) return false;
    g_local_player = resolve_rip(hit_lp, 3, 7);   // disp_off=3, insn_len=7
    if (g_local_player == 0)
    {
        log("[VoidHook] LocalPlayer slot resolved to 0");
        return false;
    }

    // E-002 — CGameEntitySystem
    uint64 hit_es = verify_unique(search_lo, search_hi - search_lo, SIG_ENTITY_SYSTEM);
    if (hit_es == 0) return false;
    g_entity_system = resolve_rip(hit_es, 3, 7);
    if (g_entity_system == 0)
    {
        log("[VoidHook] entity_system slot resolved to 0");
        return false;
    }

    // E-002 cont. — IEntityList pointer at system + OFF_ENTITY_LIST_IN_SYSTEM.
    // The slot contains the IEntityList*; we dereference once at runtime.
    g_entity_list = g_entity_system + OFF_ENTITY_LIST_IN_SYSTEM;

    // E-003 — ViewMatrix
    uint64 hit_vm = verify_unique(search_lo, search_hi - search_lo, SIG_VIEW_MATRIX);
    if (hit_vm == 0) return false;
    g_view_matrix = resolve_rip(hit_vm, 4, 8);   // disp_off=4, insn_len=8 (F3 0F 10 05)
    if (g_view_matrix == 0)
    {
        log("[VoidHook] view_matrix slot resolved to 0");
        return false;
    }

    log("[VoidHook] resolve_all OK — local=0x" + formatInt(g_local_player, "h")
        + " es=0x" + formatInt(g_entity_system, "h")
        + " el=0x" + formatInt(g_entity_list, "h")
        + " vm=0x" + formatInt(g_view_matrix, "h"));
    return true;
}

}
