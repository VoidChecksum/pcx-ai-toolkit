# Common Source Engine Signature Patterns

**These are EXAMPLE patterns only.** Signatures vary by game, build, and platform. Always verify against the actual binary you are targeting. These examples illustrate the methodology — the byte sequences, wildcarding strategy, and resolution technique.

## Methodology

1. Find the function in IDA/Ghidra that accesses the global you need
2. Copy the bytes of the instruction that loads it (typically LEA or MOV with RIP-relative)
3. Wildcard the 4-byte RIP displacement (`?? ?? ?? ??`)
4. Add surrounding bytes until the sig is unique (exactly 1 hit in the module)
5. Resolve: `final_addr = hit + instruction_length + signed_int32_at(hit + disp_offset)`

## Example Patterns

### Entity List Pointer
```
Description: LEA RCX, [rip+????] before a call that initializes the entity iteration
Sig shape:   48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7)
Struct:      CEntityList — array of entity pointers, index by entity index * 0x8
```

### Local Player Pointer
```
Description: MOV RAX, [rip+????] that loads the local player object
Sig shape:   48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? 48 8B 48
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → dereference once for CPlayer*
```

### View Matrix (4x4 float32)
```
Description: LEA RAX, [rip+????] loading the view-projection matrix for rendering
Sig shape:   48 8D 05 ?? ?? ?? ?? 48 89 44 24 ?? F3 0F
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → 64 bytes (16 x float32)
Layout:      Row-major 4x4 matrix. Row 3 = W projection row.
```

### Global Vars (gpGlobals)
```
Description: MOV RCX, [rip+????] loading the engine global vars struct
Sig shape:   48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? F3 0F 10
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7)
Fields:      +0x00 realtime, +0x04 framecount, +0x08 curtime, +0x0C frametime, +0x10 maxclients
```

### Name List / Player Info
```
Description: Accessed when resolving player names from entity indices
Sig shape:   48 8D 15 ?? ?? ?? ?? 48 8B ?? ?? 48 85 C9
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7)
```

## Resolution Helper (Enma)

```cpp
uint64 resolve_rip(proc_t& p, uint64 hit, int32 disp_offset, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = p.r32(hit + cast<uint64>(disp_offset));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}
```

## Uniqueness Verification

After crafting a sig, always verify it produces exactly one hit:

```cpp
array<uint64> hits = p.find_all_code_patterns(base, size, sig);
if (hits.length() != 1) {
    println(format("WARNING: sig has {d} hits, expected 1", hits.length()));
}
```

If hits > 1: extend the sig with more surrounding bytes.
If hits == 0: the sig is stale — the function was recompiled. Re-analyze in IDA.
