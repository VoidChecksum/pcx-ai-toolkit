# Source 2 Engine Reversal Patterns

Pattern scanning, schema resolution, and struct access for Source 2 games: Counter-Strike 2, Deadlock.

> **These are EXAMPLE patterns.** Source 2's schema system means offsets are runtime-resolved — never hardcode a field offset from one build. Use the schema system or pattern-scan the accessor.

---

## Architecture Overview

Source 2 uses a **runtime schema system** — class field offsets aren't hardcoded in the binary. They're stored in metadata that the engine resolves at startup.

**Key binaries:**
| Module | What |
|--------|------|
| `client.dll` | Client-side game code (entities, rendering, HUD) |
| `engine2.dll` | Core engine (networking, resource system) |
| `schemasystem.dll` | Runtime type metadata |
| `tier0.dll` | Base utilities, memory, threading |
| `inputsystem.dll` | Input handling |

**Key concept:** Instead of `player + 0x100` to read health, you resolve the schema: `CCSPlayerPawn::m_iHealth` → schema tells you the current offset for this build.

---

## Step 1: Schema System Resolution

The `SchemaSystem` singleton provides field offsets at runtime:

**Find SchemaSystem:**
```
# schemasystem.dll exports: CreateInterface → "SchemaSystem_001"
# Pattern: LEA RCX, [RIP+disp] followed by the interface vtable setup
48 8D 0D ?? ?? ?? ??    # lea rcx, [rip+disp]  ← SchemaSystem singleton
```

**Schema field lookup (conceptual):**
```cpp
// Pseudocode — how Source 2 resolves a field offset:
SchemaClassInfoData* classInfo = schemaSystem->FindTypeScopeForModule("client.dll")
    ->FindDeclaredClass("CCSPlayerPawn");
SchemaClassFieldData* field = classInfo->GetFieldByName("m_iHealth");
int offset = field->m_nSingleInheritanceOffset;  // ← this is the runtime offset
```

**Using Perception to resolve schemas directly:**
```cpp
// CS2 Extended API has built-in schema resolution:
// p.cs2_get_schema_offset("CCSPlayerPawn", "m_iHealth")
// Returns the offset for the current build — no hardcoding needed
```

---

## Step 2: Entity System

Source 2 uses `CGameEntitySystem` for entity management.

### Entity List Pattern

```
# Pattern: LEA RCX, [RIP+disp] loading the entity list global
# Usually found near CGameEntitySystem::GetEntityByIndex

# CS2 entity list access:
# entityList = [entityListGlobal]
# chunk = [entityList + 8 * (index >> 9) + 16]
# entity = [chunk + 120 * (index & 0x1FF)]

48 8B 04 C8             # mov rax, [rax+rcx*8]   ← chunk lookup
48 8B 44 C0 ??          # mov rax, [rax+rax*8+??] ← entity within chunk
```

### Entity Iteration

```cpp
// Perception AngelScript — iterate Source 2 entities
uint64 entity_list = p.ru64(client_base + ENTITY_LIST_OFFSET);  // pattern-scanned
for (int i = 1; i < 64; i++) {  // player indices typically 1-63
    uint64 chunk = p.ru64(entity_list + 8 * (i >> 9) + 16);
    if (chunk == 0) continue;
    uint64 entity = p.ru64(chunk + 120 * (i & 0x1FF));
    if (entity == 0) continue;

    // Read via schema offset (resolved once, cached)
    int32 health = p.r32(entity + SCHEMA_m_iHealth);
    vec3 pos = p.read_vec3_fl32(entity + SCHEMA_m_vOldOrigin);
}
```

---

## Step 3: View Matrix (World-to-Screen)

```
# The view matrix is a 4x4 float matrix in client.dll
# Pattern: Find the global that ClientModeShared::GetViewMatrix reads from

# Typical pattern (LEA into the matrix global):
48 8D 05 ?? ?? ?? ??    # lea rax, [rip+disp]  ← view_matrix global address

# Resolve: target = rip + 7 + i32_displacement
# Then read 16 floats (4x4 matrix):
mat4 vm = p.read_mat4_fl32(view_matrix_addr);
```

**W2S calculation (same as any 4x4 matrix engine):**
```cpp
vec3 w2s(vec3 world, mat4 vm, int screen_w, int screen_h) {
    float w = vm.m[3] * world.x + vm.m[7] * world.y + vm.m[11] * world.z + vm.m[15];
    if (w < 0.001f) return vec3(-1, -1, 0);  // behind camera

    float x = vm.m[0] * world.x + vm.m[4] * world.y + vm.m[8]  * world.z + vm.m[12];
    float y = vm.m[1] * world.x + vm.m[5] * world.y + vm.m[9]  * world.z + vm.m[13];

    float inv_w = 1.0f / w;
    x = (screen_w / 2.0f) + (x * inv_w) * (screen_w / 2.0f);
    y = (screen_h / 2.0f) - (y * inv_w) * (screen_h / 2.0f);

    return vec3(x, y, w);
}
```

---

## Step 4: Key Schema Classes

Common schema classes and fields for CS2 (field names stable, offsets change per build):

| Class | Key Fields | Use |
|-------|-----------|-----|
| `CCSPlayerController` | `m_hPlayerPawn`, `m_sSanitizedPlayerName`, `m_iPing` | Controller → pawn handle, player name |
| `CCSPlayerPawn` | `m_iHealth`, `m_iTeamNum`, `m_vOldOrigin`, `m_ArmorValue` | Health, team, position, armor |
| `CCSPlayerPawn` | `m_vecViewOffset`, `m_angEyeAngles`, `m_bIsScoped` | View offset, eye angles, scope state |
| `C_BaseEntity` | `m_iTeamNum`, `m_lifeState`, `m_fFlags` | Team, alive/dead, ground flags |
| `CGameSceneNode` | `m_vecAbsOrigin`, `m_angAbsRotation` | World position/rotation |
| `CSkeletonInstance` | `m_modelState.m_Bones` | Bone positions (skeleton ESP) |
| `CCSPlayerController` | `m_bPawnIsAlive`, `m_bPawnHasHelmet` | Quick alive check, helmet |

### Schema Offset Tools

| Tool | How |
|------|-----|
| **cs2-dumper** | Community tool — dumps all schema offsets per build as C++ headers |
| **Source2Gen** | Generates full SDK from schema metadata |
| **Perception CS2 API** | Built-in `cs2_get_schema_offset()` for live resolution |

---

## Deadlock-Specific Notes

Deadlock uses Source 2 but with Valve's custom hero/ability system:
- Entity classes use `C_CitadelPlayerPawn` instead of `CCSPlayerPawn`
- Schema system works identically — use `schemasystem.dll` resolution
- Different game modules: `citadel.dll` alongside `client.dll`

---

## Anti-Cheat Considerations

- **VAC (CS2, Deadlock):** Server-side + user-mode only — no kernel driver. VAC scans for known cheat signatures in process memory and monitors loaded modules.
- **Schema stability:** Field *names* are stable across patches; *offsets* change. Always re-resolve schemas after a game update.
- **Module timestamps:** `client.dll` and `engine2.dll` change every update — sigs that reference absolute addresses break. RIP-relative sigs with wildcarded displacements survive.
