# CryEngine Reverse Engineering Reference

Engine-specific RE notes for the CryEngine family and its derivatives (Lumberyard / Open 3D Engine, Dunia, Star Citizen's "StarEngine" fork). Read this before attaching to a CryEngine title — the global-environment anchor, entity system, and camera math differ enough from Unreal/Unity/Source that the generic dumper workflow does not apply. This fills the gap left by `signatures/unreal-engine/` and `signatures/source2-engine/`, which say nothing about Crytek's `gEnv`-centric architecture.

> **Read this before** doing memory analysis on any CryEngine title, and read `skill://authorized-security-research` before pointing any tool at a live multiplayer build (Hunt: Showdown and Star Citizen both ship kernel anti-cheat).

---

## Engine Overview

CryEngine is Crytek's in-house C++ engine. There is no public offset dumper equivalent to Dumper-7 — you anchor everything from one global and walk pointer chains by hand.

| Generation | Era | Representative titles |
|------------|-----|-----------------------|
| CryEngine 1 | 2004 | Far Cry (original) |
| CryEngine 2 | 2007 | Crysis |
| CryEngine 3 | 2009–2013 | Crysis 2/3, Ryse, MechWarrior Online |
| CryEngine V (5.x) | 2015–present | Hunt: Showdown, Kingdom Come: Deliverance, Crysis Remastered trilogy |

**Architecture summary:**

- **Custom renderer.** D3D11 / D3D12 / Vulkan backends behind `IRenderer`. The engine owns its own deferred renderer; there is no third-party rendering middleware to anchor on.
- **Entity-Component model.** The world is a set of `IEntity` objects managed by `IEntitySystem`. Entities are addressed by a numeric `EntityId` and carry components (`IEntityComponent` in CryEngine V; the older proxy model in CE3). Gameplay code lives in `CryAction` (the game framework) on top of `CrySystem`.
- **In-house scripting / visual scripting.** Older titles embed **Lua** (the `IScriptSystem` surface). CryEngine V adds **Schematyc** (component-graph scripting) and the legacy **Flowgraph** node editor. These leave recognizable artifacts: Lua VM strings, Schematyc GUID tables, and Flowgraph node-name strings are excellent xref anchors.
- **Module split.** Functionality is spread across DLLs: `CrySystem.dll`, `CryEntitySystem.dll`, `CryAction.dll`, `Cry3DEngine.dll`, `CryRenderD3D11.dll`/`D3D12`, plus a per-game game DLL. Identify the module that owns the global before scanning it.

**Notable quirks:**

- The whole engine hangs off one global environment struct, `SSystemGlobalEnvironment`, reached through the `gEnv` pointer. Find `gEnv` and you reach the entity system, renderer, 3D engine, timer, and console from a single root.
- World space is **right-handed, Z-up** (Z is vertical). This is the opposite vertical axis from Y-up engines — bone/position math that assumes Y-up will be wrong here.
- Transforms are stored as CryEngine `Matrix34` (a 3×4 affine matrix, row-major in memory) and `Matrix44`. The camera exposes a `CCamera` with view and projection matrices; world-to-screen goes through these rather than a single packed view-projection global as on Source.

---

## Games Using This Engine

Grounded in commonly-known facts; treat anti-cheat and SDK columns as "what is publicly associated with the title," not a guarantee for the build in front of you.

| Game | Engine version | Notes | Anti-Cheat | Community SDK / dumper |
|------|----------------|-------|-----------|------------------------|
| Hunt: Showdown 1896 | CryEngine V | PvP extraction shooter; `gEnv`-rooted entity walk | EAC (EOS) | Forum-distributed offset tables; no public dumper |
| Star Citizen | Heavily forked CryEngine → Lumberyard ("StarEngine") | Diverged far from stock CryEngine; bespoke zone/entity system | EAC | Community ReClass dumps |
| Kingdom Come: Deliverance / KCD2 | CryEngine V | Single-player RPG; loose anti-tamper | None (SP) | CryEngine SDK as structural reference |
| Crysis Remastered (1/2/3) | CryEngine V (re-engineered) | Single-player | None (SP) | Original CryEngine 2/3 SDK headers |
| Ryse: Son of Rome | CryEngine 3 | Single-player | None (SP) | — |
| MechWarrior Online | CryEngine 3 | Online; per-build pattern scans | Server-side | — |

> Star Citizen's fork has drifted so far from stock CryEngine that generic CryEngine struct knowledge is only a starting hypothesis — confirm every offset against the live build.

---

## Memory Layout Patterns

Typical shapes to expect. **All struct offsets vary per build** — these describe the *kind* of layout, never a number to hardcode.

- **`gEnv` (the master anchor).** A pointer to `SSystemGlobalEnvironment` living in a data section of `CrySystem.dll` (sometimes the game DLL). The struct is a flat table of subsystem pointers:

```cpp
// SSystemGlobalEnvironment — field order varies by version, treat as illustrative
struct SSystemGlobalEnvironment {
    void*            pNetwork;
    IRenderer*       pRenderer;        // renderer + camera access
    void*            pPhysicalWorld;
    IEntitySystem*   pEntitySystem;    // entity enumeration root
    void*            pTimer;
    IScriptSystem*   pScriptSystem;    // Lua VM (older titles)
    I3DEngine*       p3DEngine;
    void*            pGameFramework;   // CryAction
    // ... many more subsystem pointers
};
```

- **Entity system.** `IEntitySystem` owns the live entity set. Internally it keeps an array/map of `CEntity*` indexed by `EntityId`. The iteration entry point is an `IEntityIt` (entity iterator) or a direct array base — both are reachable from the `pEntitySystem` pointer. Each `CEntity` carries its name, flags, world transform (`Matrix34`), and component list.

- **Entity world position.** Stored on the entity's transform as a `Vec3` of `float32` (`read_vec3_fl32`), Z-up. Larger maps may keep a world-segment offset; confirm whether positions are absolute or segment-relative.

- **Local player / camera.** Reached through the game framework (`CryAction`) actor system: `IActorSystem → local actor → entity`. The renderable camera is a `CCamera` exposed by the renderer/view system; it holds the view matrix, projection matrix, position, and FOV used for projection.

- **View / projection matrices.** CryEngine uses `Matrix44` for projection and a `Matrix34` view, row-major. There is generally **no single packed 4×4 view-projection global** to scan for as on Source — build the VP yourself from the camera matrices, or locate the per-frame composed matrix the renderer caches.

---

## Common Sigs and RIP Patterns

Illustrative shapes only — same construction and resolution rules as `signatures/source-engine/common-sigs.md` and `signatures/unreal-engine/ue-reversal-guide.md`. Wildcard the 4-byte RIP displacement, then `resolve_rip(hit, disp_offset, insn_len)`. Re-derive every byte against your target; verify exactly one hit.

```
gEnv pointer
Description: MOV reg, [rip+????] loading the global environment pointer,
             referenced everywhere the engine touches a subsystem.
Sig shape:   48 8B 05 ?? ?? ?? ?? 48 8B 88        (MOV RAX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → SSystemGlobalEnvironment*
Anchor tip:  xref a CrySystem console-variable string ("sys_") or an engine
             init string; the init path stores gEnv.
```

```
Entity system access
Description: LEA/MOV that loads gEnv->pEntitySystem before an entity call.
Sig shape:   48 8B 0D ?? ?? ?? ?? 48 8B 01 FF 50  (MOV RCX, [rip+????]; call vtable)
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7); often easier to read the
             field offset off gEnv than to scan separately.
```

```
Lua VM / script system (older CE titles)
Description: reference to the global lua_State the engine spins up.
Anchor tip:  xref Lua error strings ("attempt to index", "PANIC") or registered
             function-name strings to reach the script system pointer.
```

**Anchor-string strategy (most reliable on CryEngine):** the engine ships thousands of stable strings — CVar names (`"sv_"`, `"sys_"`, `"r_"`, `"e_"`), Flowgraph node names, Schematyc type names, and `.cry`/`.pak` asset paths. Xref a stable string → reach the function that uses the global → copy the load instruction. This beats blind opcode scanning because the recompiled game DLL moves code but keeps the strings.

---

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

On CryEngine the cheapest re-derivation path after a patch is the **string-xref anchor**, not blind opcode search: the CVar / Flowgraph / Schematyc strings survive recompiles even when the surrounding code bytes move, so they regenerate the `gEnv` and subsystem sigs reliably. Keep the anchor string recorded alongside each sig so the offset-maintainer can rebuild it.

## Reversal Workflow

Recommended first 60 minutes on an unknown CryEngine build:

1. **Identify the module that owns `gEnv`.** Enumerate modules (`p.get_module_list()`): `CrySystem.dll`, `CryEntitySystem.dll`, `CryAction.dll`, `Cry3DEngine.dll`, and the per-game DLL confirm CryEngine. Star Citizen ships its fork under different module names — confirm via the renderer DLL and string content.
2. **Find `gEnv` first — everything else hangs off it.** Use the CVar/init-string xref anchor. Resolve it, dereference, and sanity-check that the subsequent pointers land in valid module/heap ranges (`p.is_valid_address`).
3. **Walk to `pEntitySystem`** off `gEnv`, then dump the entity iterator/array. Read a handful of entities' name strings to confirm you have the right field — entity names are the cheapest correctness check on this engine.
4. **Walk to the local actor** through `pGameFramework` (CryAction) → actor system → local actor → entity, and to the **camera** through the renderer/view. Confirm Z-up by reading your own position and moving in-game.
5. **Tooling.** IDA + Ghidra both decompile CryEngine cleanly (it is straightforward C++ with RTTI). Use `analyze_vtable` / `read_rtti` on `IEntitySystem` and `CCamera` — Crytek leaves RTTI in many builds, which names the classes for you. Schematyc/Flowgraph strings give you a second, independent anchor when a CVar sig is ambiguous.
6. **Confirm before hardcoding.** Pattern-scan `gEnv`; resolve subsystem pointers as field reads off it (not separate scans); treat struct field offsets as per-build and re-verify each patch.

---

## Anti-Cheat Considerations

Cross-reference `knowledge/anti-cheat-architecture.md` for AC internals. Guidance level only.

- **Hunt: Showdown 1896 → EAC (EOS).** Full kernel anti-cheat: handle stripping, module/integrity scans, hypervisor checks. Treat exactly as the EAC profile in `anti-cheat-architecture.md`. The single-`gEnv` anchor does nothing to reduce AC exposure — reading still happens against a protected process.
- **Star Citizen → EAC.** Same EAC kernel surface; the engine fork does not change the AC model.
- **Single-player titles (Kingdom Come, Crysis Remastered, Ryse) → no anti-cheat.** Anti-tamper is loose to absent, which is why CryEngine SDK headers and reversed offsets circulate freely for these — but that freedom is specific to the SP titles, not the engine.
- **Engine-specific detection surface:** the Lua/Schematyc scripting layer is an in-process attack surface; titles that expose modding lock it down, and AC builds watch for foreign script registration. Do not assume the scripting hooks that work on KCD work on Hunt.

---

## Community Tools and Resources

Refer to categories by name and search for the current source yourself — no live cheat-distribution links here.

- **CryEngine SDK / CryEngine V launcher source** — the official engine source and headers are the authoritative structural reference for stock CryEngine. Single best resource for class layouts (`IEntity`, `IEntitySystem`, `CCamera`, `SSystemGlobalEnvironment`).
- **CryEngine 2 / 3 leaked or licensee SDK headers** — structural reference for older Crysis-era titles.
- **Star Citizen community reversing groups** — ReClass dumps and forum offset threads for the StarEngine fork.
- **Forum offset tables** ("CryEngine offsets" threads on the usual RE/game-hacking forums) — per-build entity-list and camera offsets; always stale after a patch.
- **RTTI/vtable dumpers** (generic) — because Crytek ships RTTI, a vtable/RTTI dumper recovers class names directly from the binary.

---

## Coordinate System and World-to-Screen

CryEngine world space is **right-handed, Z-up**: X/Y are the ground plane, Z is vertical. Any math copied from a Y-up engine (most Unity/UE bone code) has the vertical axis wrong and must be remapped.

There is generally no single packed view-projection global to scan for. Build the projection from the `CCamera`'s view and projection matrices (or locate the per-frame composed matrix the renderer caches), then project. The matrix-major order must be confirmed by reading it out and projecting a known point — do not assume Source's row-major layout.

```cpp
// Sketch — project a world point through a cached VP matrix (Enma-style).
// OFF_* are resolved via sig/struct_dump per build, never hardcoded here.
// Follows the W2S discipline: read once, w > 0.001 guard, vecs built per frame.
bool world_to_screen(proc_t& p, uint64 vp_addr, vec3 world, vec2& screen) {
    // Read the matrix once; verify row vs column major against your build first.
    float64 w = p.rf32(vp_addr + 12) * world.x
              + p.rf32(vp_addr + 28) * world.y
              + p.rf32(vp_addr + 44) * world.z   // Z is vertical on CryEngine
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

> UNVERIFIED for any specific build — confirm the matrix layout and column/row offsets against your target before trusting projected coordinates.

## Offset Stability Reference

Where the key values typically live and how stable each is. "Stability" is about the *resolution method*, not a number — the address changes every build; a good sig does not.

| Value | Reached via | Stability | Notes |
|-------|-------------|-----------|-------|
| `gEnv` | Module data section, sig + RIP | None (address) / High (sig) | Master anchor; one pointer to all subsystems |
| `gEnv->pEntitySystem` | Field read off `gEnv` | High | Entity enumeration root |
| `gEnv->pRenderer` | Field read off `gEnv` | High | Camera / `CCamera` access |
| `gEnv->p3DEngine` | Field read off `gEnv` | High | World / scene queries |
| `gEnv->pGameFramework` | Field read off `gEnv` | High | CryAction; actor system → local actor |
| `gEnv->pScriptSystem` | Field read off `gEnv` | High | Lua VM (older titles) |
| Entity array / iterator | Off `pEntitySystem` | Medium | Layout varies; confirm via entity-name read |
| `CEntity` world transform | Per-entity offset | Medium | `Matrix34`, Z-up; position is `Vec3` float32 |
| Local actor / pawn | Actor system → local actor → entity | Medium | Game-specific gameplay fields |
| `CCamera` view / projection | Renderer / view system | Medium | Build VP from these; verify major order |

**Rules of thumb:**
- `gEnv` is a pointer in the module image → pattern-scan + RIP-resolve, never hardcode the address.
- Prefer **field reads off `gEnv`** over separate scans for each subsystem — one stable anchor beats five fragile ones.
- Everything below `CEntity` is game-specific; re-derive per build with `struct_dump` and an entity-name correctness check.

## Engine / Build Identification

Confirm you are on CryEngine (and which fork) before applying any of the above:

- **Module list** (`p.get_module_list()`): `CrySystem.dll`, `CryEntitySystem.dll`, `CryAction.dll`, `Cry3DEngine.dll`, `CryRenderD3D11.dll`/`D3D12`, plus a per-game DLL.
- **String markers:** CVar prefixes (`sys_`, `r_`, `e_`, `sv_`), Flowgraph node names, Schematyc type names, `.pak`/`.cry` asset paths.
- **Fork detection:** Star Citizen's StarEngine renames/repackages modules and diverges heavily — confirm via renderer DLL and string content, and treat stock CryEngine struct knowledge as a hypothesis only.
- **Version:** the engine version string (often near init/log strings) tells you CE3 vs CE V; the entity-component model (CE V) vs entity-proxy model (CE3) changes the component-walk shape.

## Common Pitfalls

- **Assuming Y-up.** CryEngine is Z-up. Bone/position math ported from a Y-up engine swaps the wrong axis and puts ESP boxes on their side — the most common first-attempt failure here.
- **Scanning each subsystem separately.** Five fragile sigs (one per subsystem) break independently every patch. Resolve `gEnv` once and read subsystems as field offsets — one anchor to maintain.
- **Hardcoding the entity-array layout.** The entity container shape varies (array vs iterator) across CE3 and CE V. Always confirm with an entity-name read before trusting the iteration.
- **Trusting RTTI on stripped builds.** Crytek leaves RTTI in many builds but not all; when `read_rtti` returns nothing, fall back to string-xref anchors rather than assuming the class is gone.
- **Star Citizen ≠ stock CryEngine.** The StarEngine fork diverges enough that stock struct knowledge is a hypothesis, not a map. Re-derive everything.
- **Forgetting the renderer caches no single VP global.** Build the view-projection from `CCamera`, or find the per-frame composed matrix; do not waste time scanning for a Source-style packed VP that is not there.
- **Reading positions as segment-relative when they are absolute (or vice versa).** Large maps may offset positions by a world segment; verify by comparing a read against your in-game coordinates.

## Cross-References

- `knowledge/anti-cheat-architecture.md` — EAC architecture and detection vectors (Hunt, Star Citizen).
- `knowledge/game-targets.md` — Hunt: Showdown listed under Tactical/Team; engine column = CryEngine.
- `knowledge/offset-methodology.md` — RIP resolution, `struct_dump`, sig-vs-hardcode discipline.
- `knowledge/common-patterns.md` — entity-iteration, world-to-screen, and GUI patterns to wire resolved offsets into a script.
- `signatures/source-engine/common-sigs.md` — `resolve_rip` helper and uniqueness verification (same technique).
- `knowledge/pcx-api-cheatsheet.md` — `read_vec3_fl32`, `read_mat4_fl32`, `find_code_pattern`, `analyze_vtable`/`read_rtti` for class recovery.
- `skill://anti-cheat-re` — six-step AC methodology for the EAC-protected titles.
- `skill://authorized-security-research` — scope/authorization before touching a live protected build.
- If you derive stable patterns, drop a stub under `signatures/cryengine/` mirroring the `signatures/unreal-engine/` layout.
