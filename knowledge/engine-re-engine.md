# RE Engine Reverse Engineering Reference

Engine-specific RE notes for Capcom's RE Engine (Resident Evil 2/3/4 remakes, RE7, RE Village, Devil May Cry 5, Monster Hunter Rise / Wilds, Street Fighter 6, Dragon's Dogma 2, Onimusha, Pragmata). Read this before attaching to an RE Engine title — the engine ships a reflected `via.*` type system with a managed-object layer that the community framework (REFramework) parses, which changes the workflow completely versus the pattern-scan grind of Frostbite or CryEngine. This fills the gap left by the UE/Unity/Source guides.

> **Read this before** doing memory analysis on any RE Engine title, and read `skill://authorized-security-research` first — Street Fighter 6 ships kernel-level anti-cheat and several titles ship Denuvo anti-tamper.

---

## Engine Overview

RE Engine is Capcom's in-house C++ engine and successor to MT Framework. Its defining feature is a built-in **reflection system** over a `via.*` type namespace, with a managed-object / singleton layer. The open-source **REFramework** hooks this reflection system and exposes it (plus a Lua scripting surface), which makes RE Engine the best-documented of the proprietary engines in this set — you can often query type and field layout from the engine itself rather than reverse it cold.

| Era | Representative titles |
|-----|-----------------------|
| 2017 | Resident Evil 7 |
| 2019 | RE2 Remake, Devil May Cry 5 |
| 2020–2021 | RE3 Remake, RE Village (RE8), Monster Hunter Rise |
| 2023–2024 | Street Fighter 6, RE4 Remake, Dragon's Dogma 2 |
| 2025+ | Monster Hunter Wilds, Onimusha: Way of the Sword, Pragmata, Kunitsu-Gami |

**Architecture summary:**

- **Custom renderer.** D3D11 / D3D12 backends. Camera and view live behind `via.Camera` / scene-view types.
- **GameObject-Component model with reflection.** The world is a `via.Scene` of `via.GameObject`s, each holding `via.Component`s. The spatial component is `via.Transform` (position / rotation / scale). Every type is described by a **reflection database** (TDB / type-definition table) — class names, field names, field offsets, and method signatures are all queryable at runtime.
- **Managed-object / singleton layer.** Gameplay systems are exposed as managed singletons (REFramework's `sdk.get_managed_singleton("app.…")` pattern). This is the access root: you fetch a system singleton, then walk its reflected fields.
- **Lua via REFramework, not native.** The engine itself is native C++; the Lua scripting surface is provided by REFramework's hook, not shipped by Capcom. The native reflection metadata, however, *is* Capcom's and is the thing REFramework reads.

**Notable quirks:**

- The **type database (TDB)** is the killer feature: instead of `struct_dump`-guessing field offsets, you can resolve a field by name through the reflection system. Find the TDB and field discovery becomes lookup, not search.
- Coordinate convention is commonly **Y-up** with `via.vec3` / `via.mat4` (column-major math in the engine's math types) — but axis handedness and matrix-major order **must be verified empirically** per title; do not assume.
- Many titles ship a **community modding base** (REFramework + EMV/Enhanced Model Viewer Lua mods), so the loose-anti-tamper single-player titles are heavily documented.

---

## Games Using This Engine

Grounded in commonly-known facts. Anti-cheat / anti-tamper column is "publicly associated with the title," generalize where uncertain.

| Game | Notes | Anti-Cheat / Anti-Tamper | Community SDK / modding base |
|------|-------|--------------------------|------------------------------|
| RE2 Remake | Single-player; heavily modded | Denuvo (early), Capcom anti-tamper | REFramework + EMV Engine |
| RE3 Remake | Single-player | Denuvo / Capcom anti-tamper | REFramework |
| RE4 Remake | Single-player + Mercenaries | Denuvo / Capcom anti-tamper | REFramework |
| RE Village (RE8) | Single-player | Denuvo + Capcom DRM (notable stutter) | REFramework |
| RE7 | Single-player | Denuvo | REFramework |
| Devil May Cry 5 | Single-player | Denuvo (early) | REFramework |
| Monster Hunter Rise | Co-op; loose anti-tamper | Denuvo (early) / server checks | REFramework |
| Monster Hunter Wilds | Co-op multiplayer | Server-side + anti-tamper | REFramework (community) |
| Street Fighter 6 | Competitive multiplayer | Kernel-level anti-cheat | Limited (AC restricts) |
| Dragon's Dogma 2 | Single-player | Denuvo / Capcom anti-tamper | REFramework |

> The pattern: **single-player RE Engine titles have loose anti-tamper and rich REFramework modding**; competitive/online titles (Street Fighter 6) lock down hard. Confirm what is actually loaded for your build.

---

## Memory Layout Patterns

Typical shapes. **All offsets vary per build** — the reflection database is precisely how you avoid hardcoding them.

- **Reflection / Type Database (TDB) — the master anchor.** A global structure cataloguing every reflected type: name, parent, fields (name + type + offset), and methods. Resolving "the position field of the player transform" becomes: find the type by name → find the field by name → read its offset. This is what REFramework exposes; reversing it once gives you a name-based field resolver for the whole game.

- **Managed singletons.** Gameplay systems are reachable as named managed singletons (`app.*` types). The singleton table is itself reflected. From a system singleton you walk reflected fields to reach the player, the enemy list, etc.

- **Scene / GameObject / Component.**

```cpp
// Illustrative — resolve real offsets via the TDB, never hardcode
struct via_Scene {
    // holds the active GameObject set for the level
};
struct via_GameObject {
    // name, folder, component list; Transform is a component
};
struct via_Transform {       // via.Transform component
    // world position (via.vec3 / via.mat4), rotation (quat), scale
};
```

- **Player / enemy access.** Through an `app.*` gameplay system singleton → player GameObject → `via.Transform` for position, plus title-specific components for health/state. Enemy/NPC lists hang off the relevant manager singleton. Names of all of these come from the TDB.

- **Camera.** `via.Camera` / scene main-view exposes the view and projection matrices and FOV used for world-to-screen. Read the matrix and verify major order/axis before projecting.

---

## Common Sigs and RIP Patterns

Illustrative shapes only — same construction and resolution rules as `signatures/source-engine/common-sigs.md`. Wildcard the 4-byte RIP displacement, then `resolve_rip(hit, disp_offset, insn_len)`; re-derive per build; verify exactly one hit. On RE Engine you typically need **far fewer raw sigs** than on other engines because the TDB resolves most fields by name.

```
Type Database (TDB) pointer
Description: MOV/LEA reg, [rip+????] loading the global reflection database,
             referenced by every reflected type/field lookup.
Sig shape:   48 8B 0D ?? ?? ?? ?? 48 8B 01        (MOV RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → TDB root
Anchor tip:  xref reflected-type name strings ("via.", "app.") or the
             reflection init path; REFramework's TDB-locate logic documents the
             anchor shape for the current engine revision.
```

```
Managed singleton table
Description: LEA reg, [rip+????] loading the singleton container before a
             get-managed-singleton style lookup.
Sig shape:   48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B    (LEA RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7)
```

```
Scene / main camera
Description: reference to the scene-manager / main-view singleton.
Anchor tip:  xref "via.Scene" / "via.Camera" type strings to the manager that
             owns the active scene and main camera.
```

**Anchor-string strategy (uniquely strong on RE Engine):** the engine literally ships its reflected type names (`via.Transform`, `app.PlayerManager`, etc.) as strings the reflection system uses. Xref those strings to reach the TDB and singleton machinery — then let the reflection system hand you field offsets by name instead of scanning for each one.

---

Once the TDB is anchored, the productive primitive is a **name→offset lookup**, not another byte scan. Conceptually: walk the TDB type list to the type whose name matches (`app.PlayerManager`, `via.Transform`, …), then walk its field list to the field whose name matches, and read the field's stored offset. REFramework implements exactly this; reproducing its TDB-walk for the current engine revision gives you the resolver everything downstream depends on.

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

On RE Engine you maintain **far fewer sigs than on other engines** — typically just the TDB-locate and singleton-table patterns. Once those resolve, field discovery is a TDB name lookup that does not depend on any byte pattern, so a patch that moves code rarely breaks downstream field access. Keep the two structural sigs anchored to `via.`/`app.` type-name strings, and let REFramework's per-revision TDB handling be your reference when the engine version changes.

## Reversal Workflow

Recommended first 60 minutes on an unknown RE Engine build:

1. **Confirm it is RE Engine.** `via.*` / `app.*` type strings in the binary, a single game executable, and the characteristic reflection-init code path confirm it. REFramework loading cleanly is also a strong signal.
2. **Locate the Type Database (TDB) first.** Everything else is a name-lookup once you have it. Use the reflected-type-name xref anchor; REFramework's open source is the reference for the current TDB layout/version.
3. **Enumerate managed singletons** and read their type names from the TDB — this maps the gameplay systems (player manager, enemy manager, camera) by name.
4. **Resolve the player Transform by field name** through the TDB rather than `struct_dump`-guessing. Read your own position to confirm.
5. **Find `via.Camera`** and read the view/projection matrix; **project a known point and verify on screen** before trusting axis/major order.
6. **Tooling.** REFramework first — it exposes the reflection system live and is the fastest path to field layout. IDA/Ghidra for the TDB/singleton machinery and for anything REFramework cannot reach. The TDB makes RE Engine the one engine here where name-based resolution largely replaces opcode sigs.

---

## Anti-Cheat Considerations

Cross-reference `knowledge/anti-cheat-architecture.md`. Guidance level only.

- **Street Fighter 6 → kernel-level anti-cheat.** A competitive title with a ring-0 anti-cheat component; treat it with the same caution as the kernel ACs in `anti-cheat-architecture.md` (foreign-module, integrity, and handle scanning). REFramework-style in-process hooking is the wrong tool against a protected competitive title.
- **RE2/3/4 Remake, RE Village, RE7 → Denuvo + Capcom anti-tamper.** Denuvo is **DRM/anti-tamper, not anti-cheat** — it resists static patching and unpacking, not memory reads from an authorized session. RE Village's DRM stack was notable for performance impact. These are single-player; there is no kernel AC watching memory access.
- **Monster Hunter Rise / Wilds → server-side checks + anti-tamper,** not a kernel AC of the EAC/BattlEye class on PC in the general case. Co-op state is server-authoritative.
- **Engine-specific surface:** the reflection/managed layer is an in-process attack surface. The very thing that makes single-player RE Engine titles easy to mod (loose anti-tamper + REFramework hooking the reflection system) is exactly what a hardened competitive title (SF6) shuts down. Never assume the REFramework approach that works on RE4 works on SF6.

---

## Community Tools and Resources

Refer to categories by name; search for current sources yourself. No live cheat-distribution links.

- **REFramework** (praydog, open source) — the central modding/RE base for RE Engine. Hooks the engine, exposes the reflection system and a Lua scripting surface, and documents TDB/singleton layout per engine revision. Single best resource for this engine.
- **EMV Engine** (Enhanced Model Viewer) — REFramework Lua mod that surfaces GameObjects, components, and field values live; effectively a runtime struct browser.
- **RE Engine modding communities** — REFramework script repositories and modding wikis documenting `app.*` system names per title.
- **TDB dumpers** — community tools that dump the full type database (types, fields, offsets) for a build, giving you a name→offset table.
- **IDA / Ghidra** — for the TDB and singleton machinery and anything outside REFramework's reach.

---

## Coordinate System and World-to-Screen

RE Engine math uses `via.vec3` / `via.mat4`; the convention is commonly **Y-up** with column-major math in the engine's math types. As everywhere, confirm axis handedness and matrix-major order empirically — read the `via.Camera` matrix and project a known point first.

```cpp
// Sketch — project through the via.Camera view-projection (Enma-style).
// Resolve the matrix field by NAME via the TDB rather than a raw offset where possible.
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

> UNVERIFIED for any specific build. RE Engine's column-major math may require transposing the index mapping above — verify against your target.

## Offset Stability Reference

Where the key values typically live. On RE Engine, the reflection database makes most of these **name-resolvable**, which is far more stable than any raw offset.

| Value | Reached via | Stability | Notes |
|-------|-------------|-----------|-------|
| Type Database (TDB) | Module data section, sig + RIP | None (address) / High (sig) | Master anchor; name→offset resolver |
| Managed singleton table | Sig + RIP / off TDB machinery | High | `app.*` system enumeration |
| `app.*` gameplay system | Singleton by name | High (by name) | Player / enemy managers |
| `via.Scene` | Scene-manager singleton | High (by name) | Active GameObject set |
| `via.GameObject` component list | Per-object, name-resolved | High (by name) | Find `via.Transform` here |
| `via.Transform` position | TDB field lookup by name | High (by name) | `via.vec3`, Y-up |
| Player / enemy state fields | TDB field lookup by name | High (by name) | Title-specific components |
| `via.Camera` view / projection | Scene main-view | Medium | Verify major order before W2S |

**Rules of thumb:**
- Find the **TDB first**; after that, resolve fields by name, not by hardcoded offset — this survives patches that a numeric offset would not.
- Only the TDB-locate and singleton-table sigs need raw pattern scanning; everything downstream is a name lookup.
- Cross-check field names against REFramework's known type list for the engine revision.

## Engine / Build Identification

Confirm you are on RE Engine before applying any of the above:

- **Module list** (`p.get_module_list()`): a single game executable; REFramework loading cleanly is a strong positive signal.
- **String markers:** reflected type names with `via.` and `app.` prefixes (`via.Transform`, `via.Scene`, `app.PlayerManager`-style) are unique to RE Engine and are also your TDB anchors.
- **Engine revision:** the TDB layout/version changes across titles (RE2 Remake vs Dragon's Dogma 2 vs Monster Hunter Wilds) — match REFramework's per-title TDB handling to your build.
- **AC posture tells you the approach:** a single-player title (loose anti-tamper + REFramework) is name-resolvable live; a competitive title (Street Fighter 6, kernel AC) is not — identify the title's posture before choosing tooling.

## Common Pitfalls

- **Reversing fields cold instead of using the TDB.** The whole point of RE Engine is name-based resolution. `struct_dump`-guessing field offsets when the reflection database can hand you the offset by name is wasted effort that also breaks every patch.
- **Hardcoding offsets the TDB would resolve.** A numeric offset dies on the next update; a TDB name lookup survives it. Hardcode nothing the reflection system can name.
- **Assuming column-major math is fine in a row-major projection.** RE Engine's `via.mat4` is column-major; if you copy a row-major W2S and points are wrong, transpose the index mapping.
- **Treating Denuvo as anti-cheat.** Denuvo on the RE remakes is anti-tamper/DRM — it resists static patching, not authorized-session memory reads. It is not a reason in itself that a memory approach fails.
- **Carrying the REFramework approach to Street Fighter 6.** SF6 ships kernel anti-cheat; the in-process reflection hooking that works on single-player titles is the wrong tool against a protected competitive game.
- **Mismatching the TDB version.** The type-database layout changes across titles (RE2 Remake vs Dragon's Dogma 2 vs Monster Hunter Wilds). Use the REFramework handling for *your* build's engine revision.
- **Skipping the position correctness check.** After resolving `via.Transform` position by name, read your own position and move in-game to confirm axis mapping before trusting it.

## Cross-References

- `knowledge/anti-cheat-architecture.md` — kernel-AC model to apply to Street Fighter 6.
- `knowledge/game-targets.md` — engine-by-game cross-reference style.
- `knowledge/offset-methodology.md` — RIP resolution and the sig-vs-hardcode discipline; note the TDB lets you prefer name-based resolution here.
- `knowledge/common-patterns.md` — entity-iteration, world-to-screen, GUI patterns for wiring resolved fields into a script.
- `signatures/source-engine/common-sigs.md` — `resolve_rip` helper and uniqueness verification.
- `knowledge/pcx-api-cheatsheet.md` — `read_vec3_fl32`, `read_quat_fl32`, `read_mat4_fl32`, `find_code_pattern`, `rs`/`rws` for reading TDB type-name strings.
- `skill://anti-cheat-re` — six-step AC methodology for Street Fighter 6.
- `skill://authorized-security-research` — scope/authorization before touching a protected build.
- If you derive stable patterns or a TDB-locate sig, add a stub under `signatures/re-engine/` mirroring `signatures/unreal-engine/`.
