# Frostbite Reverse Engineering Reference

Engine-specific RE notes for DICE/EA's Frostbite engine (Battlefield, Battlefront, FIFA / EA Sports FC, Dragon Age, Mass Effect Andromeda, Anthem, Need for Speed, Madden). Read this before attaching to a Frostbite title — its data-driven entity bus, manager-chain layout, and `RenderView` camera model are unlike Unreal/Unity/Source, and there is no managed runtime to dump from. This fills the gap left by the existing UE/Unity/Source signature guides.

> **Read this before** doing memory analysis on any Frostbite title, and read `skill://authorized-security-research` first — modern Battlefield and FC titles ship EA AntiCheat (EAAC), a kernel-mode anti-cheat.

---

## Engine Overview

Frostbite is a closed, in-house C++ engine. There is no public SDK and no dumper; the community reverses it by hand, and the canonical entity/manager chain has been stable enough across titles that the *shape* (not the offsets) is well understood.

| Generation | Era | Representative titles |
|------------|-----|-----------------------|
| Frostbite 1 | 2008 | Battlefield: Bad Company |
| Frostbite 2 | 2011 | Battlefield 3 / 4, Need for Speed |
| Frostbite 3 (later just "Frostbite") | 2013–present | Battlefield 1 / V / 2042, Battlefront I / II, Dragon Age: Inquisition / Veilguard, Mass Effect Andromeda, Anthem, FIFA / EA Sports FC, Madden, Plants vs. Zombies |

**Architecture summary:**

- **Custom deferred renderer.** D3D11 / D3D12 backends. The render path exposes a `GameRenderer` → `RenderView`, where `RenderView` carries the view/projection transform used for projection.
- **Data-driven Entity Bus ("EBX").** Frostbite is built around a typed, data-driven asset/object model. Runtime objects derive from a reflected type system; gameplay is assembled from EBX asset data rather than hand-written per-actor C++. There is **no exposed managed scripting layer** (no Mono/IL2CPP, no Lua surface to enumerate) — this is pure native C++ with a custom reflection system, so you reverse it like any C++ binary.
- **Manager-chain object model.** The community-stable access pattern is a chain of singleton managers: `ClientGameContext` → `ClientPlayerManager` → player array → `ClientPlayer` → `ClientSoldierEntity` (the controllable body) → component pointers (health, transform, weapon). Spectator/local input flows through a `BorderInputNode`-style local-player node.
- **DICE C++ with symbols-friendly structure.** Frostbite binaries are large, optimized C++ but FLIRT/IDA signatures and RTTI-style class identification work well — this is one of the more tractable proprietary engines to reverse statically.

**Notable quirks:**

- The local player and the entity list are reached through **different chains** off `ClientGameContext` — one via `ClientPlayerManager`, one via the player array. Don't assume a single root array like Source.
- World-space convention is title-dependent. Frostbite has historically used a **Y-up** world with the renderer composing a view-projection in `RenderView`; whether the cached matrix is row- or column-major has varied across titles — **read it out and verify empirically** before committing W2S math. Do not assume the Source row-major layout.

---

## Games Using This Engine

Grounded in commonly-known facts. Treat the anti-cheat column as "publicly associated with the title," and note EA migrated titles from PunkBuster → FairFight → EA AntiCheat over time.

| Game | Engine | Notes | Anti-Cheat | Community SDK / dumper |
|------|--------|-------|-----------|------------------------|
| Battlefield 2042 | Frostbite | Manager-chain entity walk | EA AntiCheat (EAAC, kernel) | Forum ReClass dumps |
| Battlefield V / 1 | Frostbite | Per-build pattern scans | EAAC (later builds); FairFight (server) | Forum offset tables |
| Battlefield 4 / 3 | Frostbite 2/3 | Most-documented community target | PunkBuster (PB) + FairFight historically | Extensive forum class dumps |
| Star Wars Battlefront II | Frostbite | Similar soldier-entity layout | EAAC / FairFight | — |
| EA Sports FC / FIFA | Frostbite | Sports title; different gameplay objects | EAAC | — |
| Dragon Age: Inquisition / Veilguard | Frostbite | Single-player RPG | None / DRM only (SP) | — |
| Mass Effect: Andromeda | Frostbite | Single-player | None (SP) | — |
| Anthem | Frostbite | Online looter-shooter | EAAC / server-side | — |
| Need for Speed (Frostbite era) | Frostbite | Racing | EAAC (online) | — |

> AC association is era-dependent: a title shipped under PunkBuster years ago may now enforce EAAC. Confirm the loaded AC driver/service at runtime rather than trusting this table for a current build.

---

## Memory Layout Patterns

Typical shapes. **All offsets vary per build** — these describe the layout *kind*, never a number to hardcode.

- **`ClientGameContext` (the manager root).** A global singleton pointer in the game module's data section. From it you reach the player manager, the entity/game-world references, and the level state:

```cpp
// Illustrative — community-stable shape, field offsets per build
struct ClientGameContext {
    ClientPlayerManager* playerManager;   // local + remote players
    void*                gameWorld;        // world / level state
    void*                levelManager;
    // ... additional manager pointers
};
```

- **Player enumeration.** `ClientPlayerManager` holds the local player pointer and an array of `ClientPlayer*` (remote players). Each `ClientPlayer` references its controlled `ClientSoldierEntity`:

```cpp
struct ClientPlayerManager {
    ClientPlayer*  localPlayer;
    ClientPlayer** players;       // array of remote players
    int32          maxPlayers;    // iteration bound
};

struct ClientPlayer {
    ClientSoldierEntity* controlledControllable;  // the soldier body, null when dead/spectating
    int32                teamId;
    // name, ping, score elsewhere in the struct
};
```

- **`ClientSoldierEntity` (the body).** Carries the component pointers cheats read: a health component, a soldier-prediction/transform source for world position (`Vec3`/`Vec4` of `float32`, Y-up), and the weapon/aim components. Position is frequently read off the prediction component or the entity transform — confirm which is authoritative per build.

- **Camera / `RenderView`.** Reached through `GameRenderer` → `RenderView`. `RenderView` holds the view transform, projection, FOV, and camera position. World-to-screen multiplies world position through the `RenderView` matrix — **verify matrix-major order by reading the matrix and projecting a known point**, do not copy Source's layout blindly.

---

## Common Sigs and RIP Patterns

Illustrative shapes only — same construction and resolution rules as `signatures/source-engine/common-sigs.md`. Wildcard the 4-byte RIP displacement, then `resolve_rip(hit, disp_offset, insn_len)`; re-derive per build; verify exactly one hit.

```
ClientGameContext singleton
Description: MOV reg, [rip+????] loading the game-context singleton pointer,
             referenced anywhere gameplay touches the player manager.
Sig shape:   48 8B 05 ?? ?? ?? ?? 48 8B 88        (MOV RAX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → ClientGameContext*
Anchor tip:  xref a Frostbite gameplay/CVar string or a render-pass name string;
             EBX type-name strings also anchor reliably.
```

```
GameRenderer / RenderView
Description: LEA/MOV loading the renderer singleton before composing RenderView.
Sig shape:   48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B   (LEA RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → GameRenderer*
Anchor tip:  xref render-pass / pipeline name strings; the renderer init stores it.
```

**Anchor-string strategy (most reliable on Frostbite):** Frostbite ships stable EBX type names, render-pass names, and gameplay strings. Xref a stable string → reach the function using the manager → copy the load instruction. Because DICE C++ keeps RTTI-style structure, `analyze_vtable` / `read_rtti` on the manager and renderer classes often names them outright, which is a stronger anchor than opcode scanning.

---

```
ClientPlayerManager / local player
Description: access to the player manager and the local-player slot, reached
             off ClientGameContext or via its own load instruction.
Sig shape:   48 8B 0D ?? ?? ?? ?? 48 8B 81 ?? ?? ?? ?? 48 85 C0  (MOV RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7); prefer reading the
             manager as a field off ClientGameContext once that is anchored.
Anchor tip:  xref a player/spawn gameplay string near the manager init.
```

### Verifying and Maintaining Sigs

Every sig must produce exactly one hit in its owning module, or the resolved address is meaningless. Scan, count, and extend:

```cpp
// Confirm a sig is unique before trusting its RIP resolution.
array<uint64> hits = p.find_all_code_patterns(g_base, g_size, sig);
if (hits.length() != 1) {
    println(format("WARNING: sig has {d} hits, expected 1", hits.length()));
    // > 1: extend the sig with more surrounding bytes until unique.
    // 0  : the function was recompiled — re-derive from a fresh string xref.
}
```

Frostbite's large optimized binary tends to repeat short opcode sequences, so raw byte patterns often start non-unique — expect to extend them with several surrounding bytes. The **EBX type-name / render-pass string anchors** are the durable re-derivation path after a patch; because Frostbite keeps RTTI-style structure, `read_rtti` on the manager and renderer classes is often a faster relocate than re-scanning. Record the anchor string and class name with each sig.

## Reversal Workflow

Recommended first 60 minutes on an unknown Frostbite build:

1. **Confirm it is Frostbite.** Module list shows a single large game executable plus Frostbite-characteristic DLLs; render-pass and EBX type strings in the binary confirm it. No `GameAssembly.dll` / `mono*.dll` (not Unity), no `*-Win64-Shipping.exe` UE marker.
2. **Find `ClientGameContext` first.** It is the root of the manager chain — resolve it via the gameplay/EBX string xref anchor, dereference, and sanity-check that `playerManager` lands in a valid range.
3. **Walk to the local player and player array** via `ClientPlayerManager`. Read team IDs and player names early — they are the cheapest correctness check that you have the right offsets.
4. **Walk to `ClientSoldierEntity`** via `controlledControllable`; null it out gracefully (it is null when dead/spectating). Read your own position and health to confirm the transform/health components.
5. **Find `GameRenderer` → `RenderView`** and read the view matrix. **Project a known world point and verify on screen** before trusting matrix-major order or axis convention.
6. **Tooling.** IDA + FLIRT signatures and Ghidra both excel here — Frostbite is large but clean DICE C++. Use `analyze_vtable`/`read_rtti` to name manager and renderer classes. Confirm before hardcoding; treat every offset as patch-volatile.

---

## Anti-Cheat Considerations

Cross-reference `knowledge/anti-cheat-architecture.md`. Guidance level only.

- **Modern Battlefield / Battlefront / FC / Anthem → EA AntiCheat (EAAC).** EA's in-house kernel-mode anti-cheat (`EAAntiCheat.GameService` service + kernel driver). Treat it as a full kernel AC: handle stripping, module/integrity scans, and the usual ring-0 callback surface described for EAC/BattlEye in `anti-cheat-architecture.md`. It loads with the protected title.
- **Legacy / server-side layers.** Older Battlefield titles shipped **PunkBuster (PB)** (user-mode, screenshot + scan) and EA's server-side **FairFight (FF)** statistical/behavioral detection. FairFight runs server-side and is independent of how you read memory. Many titles now run EAAC *plus* FairFight.
- **Single-player titles (Dragon Age, Mass Effect Andromeda) → no anti-cheat,** DRM only. The manager-chain knowledge that circulates for these is SP-specific; do not assume it transfers to a protected multiplayer build untouched.
- **Engine-specific note:** Frostbite ships EAAC integration in the online titles, so the foreign-module and handle-access detection applies the moment you attach. The lack of a managed runtime means there is no script-layer detection surface (unlike RE Engine / Unity), but also no managed metadata to lean on — everything is native.

---

## Community Tools and Resources

Refer to categories by name; search for current sources yourself. No live cheat-distribution links.

- **Battlefield reversing threads** (the usual game-hacking / RE forums) — the most-documented community target is the BF3/BF4 era, where `ClientGameContext`/`ClientPlayerManager`/`ClientSoldierEntity`/`RenderView` class layouts were dumped and re-dumped. Use those as the structural template; offsets are stale.
- **ReClass.NET project files** for Frostbite titles — community-maintained struct definitions you import into ReClass to navigate live memory.
- **Forum offset tables** — per-build entity-array, local-player, and `RenderView` offsets; always re-verify after a patch.
- **IDA / Ghidra + RTTI dumpers** — because Frostbite is clean C++ with RTTI structure, generic vtable/RTTI tooling recovers class names directly.

---

## Coordinate System and World-to-Screen

Frostbite's world convention is title-dependent and historically **Y-up**, with the renderer composing a view-projection into `RenderView`. Crucially, whether the cached matrix is row- or column-major **has varied across Frostbite titles** — this is the single most common source of broken W2S on this engine. Read the matrix out and project a known point before committing.

```cpp
// Sketch — project through the RenderView view-projection matrix (Enma-style).
// OFF_* resolved via sig/struct_dump per build. Verify matrix-major order FIRST.
bool world_to_screen(proc_t& p, uint64 vp_addr, vec3 world, vec2& screen) {
    float64 w = p.rf32(vp_addr + 12) * world.x
              + p.rf32(vp_addr + 28) * world.y
              + p.rf32(vp_addr + 44) * world.z
              + p.rf32(vp_addr + 60);
    if (w < 0.001) return false;                 // behind camera (guideline 10)
    float64 inv_w = 1.0 / w;
    float64 nx = (p.rf32(vp_addr + 0) * world.x + p.rf32(vp_addr + 16) * world.y
               +  p.rf32(vp_addr + 32) * world.z + p.rf32(vp_addr + 48)) * inv_w;
    float64 ny = (p.rf32(vp_addr + 4) * world.x + p.rf32(vp_addr + 20) * world.y
               +  p.rf32(vp_addr + 36) * world.z + p.rf32(vp_addr + 52)) * inv_w;
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

> UNVERIFIED for any specific build. If projected points mirror or invert, your matrix-major assumption is wrong — transpose the index mapping and re-test before touching anything else.

## Offset Stability Reference

Where the key values typically live and how stable each is. "Stability" describes the resolution method, not a number.

| Value | Reached via | Stability | Notes |
|-------|-------------|-----------|-------|
| `ClientGameContext` | Module data section, sig + RIP | None (address) / High (sig) | Manager-chain root |
| `ClientPlayerManager` | Field off `ClientGameContext` | Medium | Local player + remote array |
| Local player | Field off `ClientPlayerManager` | Medium | Distinct from the remote array |
| Remote player array + count | Off `ClientPlayerManager` | Medium | Iterate to `maxPlayers` |
| `ClientPlayer::controlledControllable` | Per-player offset | Medium | Null when dead/spectating |
| `ClientSoldierEntity` position | Transform / prediction component | Medium | `Vec3`/`Vec4` float32, Y-up |
| `ClientSoldierEntity` health | Health component | Medium | Confirm authoritative source |
| `GameRenderer` | Module data section, sig + RIP | None / High | Renderer singleton |
| `RenderView` view-projection | Off `GameRenderer` | Medium | Verify major order before W2S |

**Rules of thumb:**
- The two singletons (`ClientGameContext`, `GameRenderer`) are pointers in the image → sig + RIP, never hardcode.
- Local player and entity list are **separate chains** off the context — resolve both, do not assume one array.
- All `Client*Entity` gameplay fields are per-build → `struct_dump` + a team-ID/name correctness check; re-derive each patch.

## Engine / Build Identification

Confirm you are on Frostbite before applying any of the above:

- **Module list** (`p.get_module_list()`): a single large game executable; **no** `GameAssembly.dll`/`mono*.dll` (rules out Unity) and **no** `*-Win64-Shipping.exe` (rules out UE).
- **String markers:** EBX type names, render-pass / pipeline names, and DICE gameplay strings in the binary.
- **AC markers:** an `EAAntiCheat.GameService` service / EAAC driver indicates a current protected build regardless of the title's launch-era anti-cheat.
- **Era matters for layout:** BF3/BF4-era class layouts are the most-documented community template, but field offsets and even the chain shape drift across Frostbite generations — use the era closest to your target as the starting hypothesis only.

## Common Pitfalls

- **Wrong matrix-major order in `RenderView`.** The single most common Frostbite W2S failure: the cached view-projection has varied between row- and column-major across titles. If points mirror or invert, transpose the index mapping before changing anything else.
- **Treating local player and entity list as one root.** They live on separate chains off `ClientGameContext` (player manager vs player array). Resolve both.
- **Not null-checking `controlledControllable`.** It is null whenever the player is dead or spectating; dereferencing it unguarded crashes the loop on the first downed player.
- **Porting BF3/BF4 offsets directly.** Those are the best-documented layouts but field offsets drift across Frostbite generations; use them as a starting hypothesis, then `struct_dump` and verify.
- **Reading position from the wrong component.** Position may live on a prediction component or the entity transform; pick the authoritative one for the build, or your ESP lags or jitters.
- **Assuming no EAAC because an old guide says PunkBuster.** AC is era-dependent; a title patched onto EAAC is a kernel-AC target now regardless of what shipped at launch. Check the loaded driver/service.
- **Looking for a managed runtime.** There is none — no Mono/IL2CPP, no Lua surface to enumerate. Everything is native C++; reverse it as such.

## Cross-References

- `knowledge/anti-cheat-architecture.md` — EAC/BattlEye kernel model; apply the same lens to EAAC.
- `knowledge/game-targets.md` — engine-by-game table for cross-checking AC associations.
- `knowledge/offset-methodology.md` — RIP resolution, `struct_dump`, sig-vs-hardcode discipline.
- `knowledge/common-patterns.md` — entity-iteration, world-to-screen, GUI patterns for wiring resolved offsets into a script.
- `signatures/source-engine/common-sigs.md` — `resolve_rip` helper and uniqueness verification.
- `knowledge/pcx-api-cheatsheet.md` — `read_vec3_fl32`, `read_mat4_fl32`, `find_code_pattern`, `analyze_vtable`/`read_rtti`.
- `skill://anti-cheat-re` — six-step AC methodology for EAAC-protected titles.
- `skill://authorized-security-research` — scope/authorization before touching a live protected build.
- If you derive stable patterns, add a stub under `signatures/frostbite/` mirroring `signatures/unreal-engine/`.
