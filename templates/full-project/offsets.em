// offsets.em — named signatures + a RIP-relative resolver.
// Sigs survive game patches; resolved absolute addresses do not.
// See knowledge/offset-methodology.md and signatures/source-engine/common-sigs.md

import "globals";

// ── Signatures (EXAMPLES — replace with sigs for your target) ──
// Document each: the instruction it matches, and what it loads.
const string SIG_EXAMPLE_GLOBAL = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74"; // UNVERIFIED
// MOV RAX, [rip+????] — loads some global pointer

// ── Resolved addresses (filled by resolve_all) ──
uint64 g_example_global = 0;

// Resolve a RIP-relative operand.
//   hit        : where the sig matched
//   disp_off   : byte offset to the 4-byte displacement (3 for `48 8B 05 ..`)
//   insn_len   : full instruction length (7 for a 7-byte MOV/LEA)
// final = hit + insn_len + signed_int32(hit + disp_off)
uint64 resolve_rip(uint64 hit, int32 disp_off, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + cast<uint64>(disp_off));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}

// Scan + resolve every offset. Returns false if any required sig is stale.
bool resolve_all() {
    uint64 hit = g_proc.find_code_pattern(g_base, g_size, SIG_EXAMPLE_GLOBAL);
    if (hit == 0) {
        println("[offsets] SIG_EXAMPLE_GLOBAL stale — re-analyze in IDA");
        return false;
    }
    g_example_global = resolve_rip(hit, 3, 7);
    return g_example_global != 0;
}
