# Perception.cx Game Support Reference

Every game with active scripts in the Perception.cx Script Market (as of June 2026), organized by category. Scripting language is **AngelScript** (`AS`) across the board; CS2 additionally exposes a **Lua** surface.

> Counts are minimums (`N+`) — they reflect publicly listed market entries, not private/loader-only scripts.

## FPS / Battle Royale

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| Counter-Strike 2 | Source 2 | 10+ | VAC | Official + community suite | AS, Lua |
| Apex Legends | Source (Respawn) | 5+ | EAC (EOS) | UFOHOOK, ATLAS, ARIEngine | AS |
| COD: Black Ops 7 / Warzone | IW Engine | 2+ | RICOCHET | — | AS |
| Fortnite | Unreal Engine | 1+ | EAC (EOS) | — | AS |
| PUBG (Steam) | Unreal Engine | 2+ | BattlEye | — | AS |
| Overwatch / Overwatch 2 | Custom | 3+ | Custom (Blizzard) | — | AS |
| The Finals | Embark / Theia | 2+ | EAC + Theia | — | AS |
| Deadlock | Source 2 | 2+ | VAC | — | AS |
| Arena Breakout Infinite | Unity | 3+ | EAC (EOS) | — | AS |
| BloodStrike | Unreal Engine | 1+ | EAC | — | AS |
| Farlight 84 | Unreal Engine | 1+ | EAC | — | AS |

## Survival / Open World

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| Escape from Tarkov | Unity | 1+ | BattlEye | Official | AS |
| Rust | Unity | 2+ | EAC (EOS) | — | AS |
| DayZ | Enfusion | 1+ | BattlEye | — | AS |
| Scum | Unreal Engine | 1+ | EAC | — | AS |
| Ark: Survival Evolved | Unreal Engine | 1+ | BattlEye | — | AS |
| The Isle: Evrima | Unreal Engine | 1+ | EAC | — | AS |
| Dark and Darker | Unreal Engine | SDK | EAC (EOS) | SDK available | AS |

## Tactical / Team

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| Rainbow Six Siege | AnvilNext | 1+ | BattlEye | Private | AS |
| Hunt: Showdown 1896 | CryEngine | 2+ | EAC (EOS) | — | AS |
| Marvel Rivals | Unreal Engine | 2+ | EAC (EOS) | — | AS |
| The Division 2 | Snowdrop | 1+ | EAC | — | AS |

## Horror / Other

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| Dead by Daylight | Unreal Engine | 1+ | EAC (EOS) | Official, Featured | AS |
| Chivalry 2 | Unreal Engine | 1+ | EAC | — | AS |
| Far Far West | Unknown | 1+ | Unknown | — | AS |
| KovaaK's | Unreal Engine | 1+ | None | Aim trainer | AS |
| GeoGuessr | Web / Steam | 1+ | None | — | AS |

## Modded / Custom Clients

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| GTA V (RAGE:MP / ALT:V) | RAGE | 1+ | None (mod client) | Multiplayer mods | AS |
| Roblox | Custom | 1+ | Byfron (Hyperion) | Official | AS |

**Total: 29 supported games.**

## Engine Summary

| Engine | Games |
|--------|-------|
| Source 2 | CS2, Deadlock |
| Source (Respawn) | Apex Legends |
| Unreal Engine | Fortnite, PUBG, Dead by Daylight, Marvel Rivals, Arena Breakout Infinite, Scum, The Isle, Dark and Darker, Ark, Chivalry 2, KovaaK's, BloodStrike, Farlight 84 |
| IW Engine | COD: Black Ops 7 / Warzone |
| Unity | Escape from Tarkov, Rust, Arena Breakout Infinite |
| CryEngine | Hunt: Showdown 1896 |
| Enfusion | DayZ |
| AnvilNext | Rainbow Six Siege |
| Snowdrop | The Division 2 |
| Embark / Theia | The Finals |
| RAGE | GTA V |
| Custom / Other | Overwatch, Roblox, GeoGuessr, Far Far West |

> Arena Breakout Infinite appears under both Unreal Engine and Unity in market metadata; treat its engine as version-dependent and confirm at runtime via the module list.

## Engine-Specific Considerations

### Unreal Engine
- **Dumper required.** Object/name resolution goes through `GObjects` and `GNames`. Use an offset dumper (e.g. Dumper-7 / UE4SS output) and feed the resulting struct offsets into your script; do not hardcode across patches.
- **GWorld → GameInstance → PersistentLevel → Actors** is the canonical entity walk. Cache `GWorld` once per frame, then iterate the actor array.
- **FName** decoding needs the name pool. Resolve via `GNames` chunked array; class names come from `UObject::ClassPrivate->Name`.
- Coordinates are typically `FVector` (3×`float32`) — read with `read_vec3_fl32`. World-to-screen needs the camera `POV` (location + rotation + FOV) from the local player controller.

### Source 2 (CS2, Deadlock)
- **Schema system.** Field offsets are not static — they live in the runtime schema. Resolve member offsets via the `SchemaSystem` / `client.dll` schema classes (e.g. `C_CSPlayerPawn`) rather than fixed numbers.
- Entity list via `entity_list` / `CGameEntitySystem`; iterate identity chunks.
- View matrix is exposed in `client.dll` — pattern-scan for the `view_matrix` global; W2S is a straight `mat4` multiply (`read_mat4_fl32`).

### Source (Respawn — Apex)
- Heavily modified Source; entity walk differs from Valve Source. Use community offset tables; highlight pointers and entity list are pattern-scanned per build.

### Unity (Tarkov, Rust, ABI)
- **IL2CPP.** Managed code is AOT-compiled; use `il2cpp_dump` / Il2CppDumper to recover class and field metadata, then resolve via `GameAssembly.dll` + `global-metadata.dat`.
- Mono (legacy) builds expose typedefs directly via the Mono API; check which backend the title ships.
- Static fields are reached through the IL2CPP class' static field pointer; instance offsets come from the dumped metadata.

### IW Engine (COD)
- Aggressive anti-tamper and frequently rotating offsets; entity/bone access usually requires per-build pattern scans. Treat all offsets as volatile.

### CryEngine (Hunt) / Enfusion (DayZ) / AnvilNext (R6) / Snowdrop (Division 2)
- Proprietary entity systems with no public dumper. Rely on pattern scanning to anchor the entity list and local player, then map structs manually per build.

### RAGE (GTA V)
- Targeted via multiplayer mod frameworks (RAGE:MP, ALT:V). Entity pools (`CPed`, `CVehicle`) are reached through the replay/pool managers; scope is mod-client memory, not the base game.

### Custom / Web (Overwatch, Roblox, GeoGuessr)
- No shared tooling. Overwatch uses a bespoke engine (pattern-scan everything). Roblox runs its own VM — official script handles the surface. GeoGuessr is web/Steam wrapper, DOM/state-driven rather than classic memory ESP.

## Practical Workflow

1. **Identify the engine** — `p.get_module_list()` reveals the giveaways: `UnrealEditor`/`*-Win64-Shipping.exe` (UE), `client.dll` + `engine2.dll` (Source 2), `GameAssembly.dll` (Unity IL2CPP), `mono-2.0-bdwgc.dll` (Unity Mono).
2. **Get offsets** — dumper for UE/Unity, schema resolution for Source 2, pattern scans for proprietary engines.
3. **Anchor per frame** — cache the world/entity-list root once, then iterate; never re-scan inside the actor loop.
4. **Treat every offset as patch-volatile** — prefer schema/dumper resolution over literals so a game update doesn't silently corrupt reads.
