# Offset Finding and Maintenance Methodology

## When to Pattern Scan vs Hardcode

**Pattern scan** (preferred): any global pointer, vtable address, or function address that the compiler may relocate between builds. The instruction sequence referencing it is stable; the address it points to is not.

**Hardcode** (acceptable): struct field offsets within a known type. `m_iHealth` at `+0x43E0` inside `CPlayer` changes only when Respawn reorders the class — which happens less often than code relocations. Still document the source.

## Signature Construction

1. Open the function in IDA/Ghidra. Find the instruction that loads/references the value you need.
2. Copy the raw bytes of that instruction and 1-2 neighboring instructions for uniqueness.
3. Replace **RIP-relative displacements** (4 bytes after the opcode) with `??` wildcards — these change every build.
4. Replace **immediate addresses** and **jump targets** with `??` — also unstable.
5. Keep **opcode bytes** and **register encodings** — these are stable unless the compiler changes register allocation.

```
Example instruction:  48 8B 05 [A0 B3 2A 01]  ← MOV RAX, [rip+0x12AB3A0]
                      ^^^^^^^^ ^^^^^^^^^^^^^^
                      opcode   RIP displacement (changes every build)

Signature:           "48 8B 05 ?? ?? ?? ??"
```

Verify uniqueness: `find_all_code_patterns` should return exactly 1 hit. If multiple, extend the sig with more surrounding bytes.

## RIP-Relative Address Resolution

Most x64 instructions use RIP-relative addressing. The displacement is a **signed 32-bit integer** relative to the **end** of the instruction (i.e., the address of the next instruction).

```
hit        = address where the sig matched
disp_off   = offset from hit to the displacement bytes (e.g., 3 for LEA reg,[rip+??])
insn_len   = total instruction length (e.g., 7 for a 7-byte LEA)
displacement = read_int32(hit + disp_off)      ← signed!
resolved   = hit + insn_len + displacement
```

Common instruction shapes:

| Pattern | Instruction | disp_off | insn_len |
|---------|-------------|----------|----------|
| `48 8B 05 ?? ?? ?? ??` | MOV RAX, [rip+disp] | 3 | 7 |
| `48 8D 0D ?? ?? ?? ??` | LEA RCX, [rip+disp] | 3 | 7 |
| `48 8B 0D ?? ?? ?? ??` | MOV RCX, [rip+disp] | 3 | 7 |
| `E8 ?? ?? ?? ??` | CALL rel32 | 1 | 5 |
| `E9 ?? ?? ?? ??` | JMP rel32 | 1 | 5 |

## Pointer Chain Walking

Game data is often behind multiple levels of indirection:

```
base_address → entity_list_ptr → entity_ptr → field
```

Strategy:
1. Find the first pointer via sig scan + RIP resolution.
2. Dereference each level with `ru64`, checking for 0 at every step.
3. Document the full chain: `base + 0x... → deref → + 0x... → deref → + 0x...`
4. The final offset into the struct is typically a hardcoded field offset.

```cpp
uint64 entity_list = resolve_sig(p, base, size, SIG_ENTITY_LIST);  // sig scan
if (entity_list == 0) return;                                       // stale sig
uint64 list_ptr = p.ru64(entity_list);                              // deref level 1
if (list_ptr == 0) return;                                          // null
uint64 entity = p.ru64(list_ptr + cast<uint64>(index) * 0x8);      // deref level 2
if (entity == 0) return;                                            // null entry
int32 health = p.r32(entity + 0x43E0);                             // struct field
```

## Using struct_dump for Discovery

When you don't know a struct layout, read raw memory and classify fields:

```cpp
// In Perception IDE, the AI can use struct_dump tool:
// struct_dump(addr, size=0x100)
// Returns: offset, raw hex, heuristic type (pointer/vtable/float/int/null)
```

Look for:
- **Pointers**: values in the `0x7FF...` range (usermode x64)
- **VTable ptrs**: first 8 bytes of an object, pointing into .rdata
- **Floats**: values like `100.0`, `0.0`, `-1.0` that make sense as game state
- **Ints**: small values (health, ammo, team ID)

## Cross-Referencing with IDA/Ghidra

1. Find the ConVar or string that names the feature (e.g., `"cl_interp"`, `"m_iHealth"`).
2. Xref the string → find the registration function → find the global variable or struct field.
3. Verify the offset in the reversed SDK headers if available (e.g., `r5sdk/src/game/server/player.h`).
4. Remember: SDK headers may be from an older game version. Always verify with a live read.

## Offset Table Format

Maintain a structured offset file:

```cpp
// offsets.em — auto-resolved via pattern scans
// Last verified: 2025-06-15, game version 1.98

const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";
// LEA RCX, [rip+????] — loads CEntityList global
// Source: sub_1400ABCDE in IDA, xref from "cl_entitylist"

const string SIG_VIEW_MATRIX = "48 8D 05 ?? ?? ?? ?? 48 89 44 24 ?? F3 0F";
// LEA RAX, [rip+????] — loads view-projection matrix (16 floats)

const string SIG_LOCAL_PLAYER = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? 48 8B 48";
// MOV RAX, [rip+????] — loads local player pointer

// Struct field offsets (hardcoded, verified against SDK)
const uint64 OFF_HEALTH   = 0x43E0;   // CPlayer::m_iHealth (int32)
const uint64 OFF_TEAM     = 0x0448;   // CBaseEntity::m_iTeamNum (int32)
const uint64 OFF_POSITION = 0x014C;   // CBaseEntity::m_vecAbsOrigin (vec3 float32)
const uint64 OFF_NAME     = 0x0589;   // CBaseEntity::m_iName (string ptr)
```

## What Breaks on Game Updates

| What | Stability | Why |
|------|-----------|-----|
| Pattern signatures | **High** | Instruction sequences rarely change unless the function is rewritten |
| RIP-relative resolved addresses | **None** | Absolute addresses change every build |
| Struct field offsets | **Medium** | Change when devs add/remove/reorder fields |
| VTable indices | **Medium** | Change when virtual functions are added/removed |
| Function addresses | **None** | Change every build — always use sigs |
| String literals | **High** | Rarely change — good anchor points for xrefs |
