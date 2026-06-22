# REDengine Reverse Engineering Reference

Engine-specific RE notes for CD Projekt Red's REDengine (Cyberpunk 2077 on REDengine 4, The Witcher 3 on REDengine 3). Read this before attaching to a REDengine title — its RTTI/reflection system, REDscript gameplay VM, and fixed-point world-coordinate quirk differ from Unreal/Unity/Source, and the community framework (RED4ext / Cyber Engine Tweaks) exposes the engine's reflection much like REFramework does for RE Engine. This fills the gap left by the UE/Unity/Source guides.

> **Read this before** doing memory analysis on a REDengine title. **Note:** CDPR's future games (The Witcher 4, "Project Polaris") move to **Unreal Engine 5** — for those, use `signatures/unreal-engine/ue-reversal-guide.md`, not this file. REDengine knowledge applies to Cyberpunk 2077 and Witcher 3 only.

---

## Engine Overview

REDengine is CD Projekt Red's in-house C++ engine. Like RE Engine, it ships an **RTTI / reflection system** describing game classes, fields, and methods, plus a gameplay **scripting VM**. The community framework **RED4ext** hooks the engine and **Cyber Engine Tweaks (CET)** exposes the reflection system over Lua — so, as with RE Engine, you can often query type/field layout from the engine rather than reverse it cold. Both titles are single-player, which keeps anti-tamper loose and documentation rich.

| Generation | Era | Title |
|------------|-----|-------|
| REDengine 1 | 2011 | The Witcher 2 |
| REDengine 3 | 2015 | The Witcher 3: Wild Hunt |
| REDengine 4 | 2020 | Cyberpunk 2077 |
| (successor) | future | **Witcher 4 / Project Polaris → Unreal Engine 5** (not REDengine) |

**Architecture summary:**

- **Custom renderer.** D3D12 (Cyberpunk) with a deferred path; camera/view exposed through the engine's camera system.
- **RTTI / reflection system.** REDengine describes its classes through an RTTI database (class names, field names + offsets, method signatures). CET reads this to expose game classes by name — the same name-based-resolution advantage RE Engine's TDB gives.
- **Gameplay scripting VM.** The Witcher 3 uses **WitcherScript** (`.ws`); Cyberpunk 2077 uses **REDscript** plus a quest/scene scripting layer. Cyberpunk's gameplay objects are reached through a `GameInstance` and a set of game systems (`gamePlayerSystem`, scripting-exposed systems). RED4ext hooks the native side; redscript compiles to the gameplay VM.
- **Entity / world model.** `GameInstance` → game systems → the local player puppet (the controlled `gameObject`/`Entity`), with the world's NPC/entity set reachable through the relevant game system. Names of these come from the reflection database / CET.

**Notable quirks:**

- **Fixed-point world coordinates.** Cyberpunk's open world uses a high-precision world-position representation (an integer/fractional `WorldPosition`-style encoding) in places to avoid float drift over a large map. Do not assume a plain `float32` `Vec3` everywhere — confirm whether a given position field is float or the fixed-point world type before doing math on it.
- **Coordinate convention** is commonly **Z-up, right-handed** for Cyberpunk's world space (vehicles, navigation, world geometry are Z-up). Verify axis and matrix-major order empirically per build before committing world-to-screen math.
- **Reflection-first, like RE Engine.** Prefer resolving fields by name through the RTTI database (via CET / RED4ext knowledge) over `struct_dump`-guessing.

---

## Games Using This Engine

Grounded in commonly-known facts. Both shipped titles are single-player.

| Game | Engine | Notes | Anti-Cheat / Anti-Tamper | Community SDK / modding base |
|------|--------|-------|--------------------------|------------------------------|
| Cyberpunk 2077 | REDengine 4 | Single-player; reflection + REDscript | None (SP); Denuvo dropped post-launch on some platforms | RED4ext, redscript, Cyber Engine Tweaks (CET), TweakXL, ArchiveXL |
| The Witcher 3: Wild Hunt | REDengine 3 | Single-player; WitcherScript | None (SP); GOG/Steam DRM only | Modding community (script + WolvenKit-era tools) |
| The Witcher 2 | REDengine 1 | Single-player; legacy | None (SP) | — |
| Witcher 4 / Project Polaris | **Unreal Engine 5** | Future titles; not REDengine | — | Use the UE guide |

> Because both shipped REDengine titles are single-player with no anti-cheat, REDengine is the loosest anti-tamper of the four engines in this coverage pack — which is why the RED4ext/CET modding ecosystem is so mature. None of that freedom transfers to the UE5 successors.

---

## Memory Layout Patterns

Typical shapes. **All offsets vary per build** — the RTTI/reflection database is how you avoid hardcoding them.

- **RTTI / reflection database — the master anchor.** A global structure cataloguing reflected classes: name, parent, fields (name + type + offset), methods. Locating it gives you a name→offset resolver for the whole game, exactly as CET uses. This is the highest-value first target.

- **`GameInstance` and game systems.** The gameplay root. From `GameInstance` you reach game systems (e.g. a player system) by type; the player system hands you the local player puppet:

```cpp
// Illustrative — resolve real offsets via the reflection DB, never hardcode
struct GameInstance {
    // holds/owns the registered game systems
};
struct gamePlayerSystem {
    // local player puppet accessor: GetLocalPlayerControlledGameObject()-style
};
struct gameObject_Entity {
    // components: transform/placement (position), health/stats, etc.
};
```

- **Local player position.** Read off the player puppet's placement/transform component. **Check whether the field is a `float32` Vec3 or the fixed-point `WorldPosition` type** — Cyberpunk mixes both depending on the system. Convert the fixed-point form to world units before projecting.

- **NPC / entity enumeration.** Through the relevant world/entity game system rather than a single flat array. Names of the system and its container come from the reflection database / CET dumps.

- **Camera.** The engine's camera system exposes the view and projection used for world-to-screen. Read the matrix and verify major order / Z-up handedness before projecting.

---

## Common Sigs and RIP Patterns

Illustrative shapes only — same construction and resolution rules as `signatures/source-engine/common-sigs.md`. Wildcard the 4-byte RIP displacement, then `resolve_rip(hit, disp_offset, insn_len)`; re-derive per build; verify exactly one hit. As on RE Engine, the reflection DB resolves most fields by name, so you need fewer raw sigs.

```
RTTI / reflection database
Description: MOV/LEA reg, [rip+????] loading the reflection database root,
             referenced by every reflected class/field lookup.
Sig shape:   48 8B 0D ?? ?? ?? ?? 48 8B 01        (MOV RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → reflection DB root
Anchor tip:  xref reflected class-name strings ("game", "ent", "world" prefixes)
             or the RTTI init path; RED4ext's open source documents the anchor
             shape for the current game version.
```

```
GameInstance / game-systems container
Description: LEA reg, [rip+????] loading the GameInstance before a
             get-game-system style lookup.
Sig shape:   48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B   (LEA RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7)
```

```
Player system / local puppet
Description: reference to the player system that resolves the controlled puppet.
Anchor tip:  xref player-system / "GetLocalPlayerControlledGameObject" style
             reflected method-name strings to reach the accessor.
```

```
Camera / view system
Description: reference to the camera system exposing the active view + projection.
Anchor tip:  xref camera-system reflected type/method names to reach the matrix
             the renderer composes per frame; read it out and verify Z-up /
             major order before projecting.
```

**Anchor-string strategy:** REDengine ships its reflected class and method names as strings the RTTI system consumes. Xref those to reach the reflection DB and `GameInstance`, then resolve fields by name. RED4ext / CET open source is the authoritative reference for the current game version's anchors — lean on it rather than blind opcode scanning.

---

Once the reflection DB is anchored, the productive primitive is a **name→offset lookup** rather than another byte scan: walk the reflected class list to the class whose name matches (e.g. the player puppet type), then its property list to the named field, and read the stored offset. CET exposes this live over Lua and RED4ext implements the native walk — reproducing it for the current build gives you the resolver the rest of the workflow depends on. This is also where you classify a position property as `float32` versus fixed-point `WorldPosition` from its reflected type.

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

As on RE Engine, you maintain **only a couple of structural sigs** — the reflection-DB-locate and `GameInstance` patterns. Downstream field access is name resolution through the reflection database, so it largely survives code-moving patches. RED4ext/CET track the current build's anchors; keep your two sigs recorded against their `game`/`ent`/`world` class-name string anchors so the offset-maintainer can rebuild them after an update.

## Reversal Workflow

Recommended first 60 minutes on a REDengine build (Cyberpunk 2077 / Witcher 3):

1. **Confirm it is REDengine — and not a UE5 successor.** Cyberpunk ships a single `Cyberpunk2077.exe` with reflected `game*`/`ent*`/`world*` class strings and the REDscript/quest VM. If you are on a future CDPR title, check for UE markers (`*-Win64-Shipping.exe`, `GObjects` machinery) and switch to the UE guide.
2. **Locate the RTTI / reflection database first.** It turns field discovery into name lookup. Use the class-name xref anchor; RED4ext source is the reference for the current layout.
3. **Reach `GameInstance` and enumerate game systems** by name from the reflection DB — this maps player, world, and camera systems.
4. **Resolve the local player puppet** via the player system, then its placement/transform. **Determine float vs. fixed-point `WorldPosition`** before doing position math; read your own position to confirm.
5. **Find the camera** and read view/projection; **project a known world point and verify on screen** before trusting axis/major order.
6. **Tooling.** RED4ext + CET first — CET exposes the reflection system live (browse classes/fields/methods by name) and is the fastest path to layout. IDA/Ghidra for the reflection DB and `GameInstance` machinery and anything the frameworks cannot reach. Name-based resolution largely replaces opcode sigs here.

---

## Anti-Cheat Considerations

Cross-reference `knowledge/anti-cheat-architecture.md`. Guidance level only.

- **Cyberpunk 2077 and The Witcher 3 → no anti-cheat.** Both are single-player. Cyberpunk shipped with Denuvo on some storefronts and later dropped it; Denuvo is **DRM/anti-tamper, not anti-cheat** — it resists static patching, not memory reads from an authorized session. There is no kernel AC monitoring memory access on these titles.
- **Loose anti-tamper → mature modding.** The absence of anti-cheat is precisely why RED4ext/CET can hook the engine in-process and expose the reflection system. This is engine-and-title-specific freedom.
- **Future UE5 titles will differ.** CDPR's Witcher 4 / Project Polaris move to Unreal Engine 5; if any future title is multiplayer it will ship its own anti-cheat. Do not carry REDengine assumptions forward — treat the UE5 successors as standard UE targets under whatever AC they ship.
- **Engine-specific surface:** the REDscript/quest VM and the reflection system are in-process surfaces that the modding frameworks use; on a single-player title there is no AC watching them, but that is a property of the title, not a guarantee.

---

## Community Tools and Resources

Refer to categories by name; search for current sources yourself. No live cheat-distribution links.

- **RED4ext** (open source) — the native hooking framework for Cyberpunk 2077; the RE Engine of CDPR's world. Documents reflection-DB and `GameInstance` layout per game version.
- **Cyber Engine Tweaks (CET)** — exposes the reflection system over Lua: browse and call reflected classes/methods/fields by name live. Effectively a runtime type/field browser, the fastest layout-discovery tool for Cyberpunk.
- **redscript / WitcherScript tooling** — gameplay-script compilers/decompilers; useful for understanding which systems own which state.
- **WolvenKit** — modding toolkit for REDengine asset/archive editing; structural reference for the engine's data model (asset side, not memory).
- **TweakXL / ArchiveXL** — data/record extension frameworks; reference for how game records and systems are named.
- **IDA / Ghidra** — for the reflection DB and `GameInstance` machinery and anything outside the frameworks.

---

## Coordinate System and World-to-Screen

Cyberpunk's world space is commonly **Z-up, right-handed**. The defining hazard is the **fixed-point `WorldPosition` encoding** used to keep precision across a large open world: a position field may be a plain `float32` `Vec3` *or* an integer/fractional world type. Decode the fixed-point form to world units before any projection math, and verify axis/major order by reading the camera matrix and projecting a known point.

```cpp
// Sketch — project through the camera view-projection (Enma-style).
// Resolve fields by NAME via the reflection DB where possible. Confirm the
// position field is float32 vs fixed-point BEFORE calling this.
bool world_to_screen(proc_t& p, uint64 vp_addr, vec3 world, vec2& screen) {
    float64 w = p.rf32(vp_addr + 12) * world.x
              + p.rf32(vp_addr + 28) * world.y
              + p.rf32(vp_addr + 44) * world.z   // Z is vertical on REDengine
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

> UNVERIFIED for any specific build. If world positions are stored fixed-point, feeding them raw into this projection produces garbage — decode first.

## Offset Stability Reference

Where the key values typically live. As on RE Engine, the reflection database makes most of these **name-resolvable**, which beats any raw offset for patch survival.

| Value | Reached via | Stability | Notes |
|-------|-------------|-----------|-------|
| RTTI / reflection DB | Module data section, sig + RIP | None (address) / High (sig) | Master anchor; name→offset resolver |
| `GameInstance` | Sig + RIP / off reflection machinery | High | Game-systems container |
| Player system (`gamePlayerSystem`) | Game system by name | High (by name) | Resolves local puppet |
| Local player puppet | Player-system accessor | High (by name) | `gameObject`/`Entity` |
| Puppet placement / transform | Reflection field by name | Medium | Float32 `Vec3` **or** fixed-point `WorldPosition` |
| Puppet stats / health | Reflection field by name | High (by name) | Stat-pool component |
| NPC / entity set | World/entity game system | Medium | Not a single flat array |
| Camera view / projection | Camera system | Medium | Verify Z-up / major order before W2S |

**Rules of thumb:**
- Find the **reflection DB first**; resolve downstream fields by name. RED4ext/CET source documents the current build's anchors.
- Only the reflection-DB-locate and `GameInstance` sigs need raw pattern scanning.
- Always classify a position field (float vs fixed-point) before doing distance/W2S math — this is the REDengine-specific footgun.

## Engine / Build Identification

Confirm you are on REDengine — **and not a UE5 successor** — before applying any of the above:

- **Module list** (`p.get_module_list()`): `Cyberpunk2077.exe` (a single large executable); RED4ext/CET loading cleanly is a strong positive signal. If you see `*-Win64-Shipping.exe` or UE `GObjects` machinery, you are on a UE5 title → use the UE guide.
- **String markers:** reflected class names with `game`, `ent`, `world` prefixes, REDscript/quest-VM strings, and CET-known method names.
- **Title:** only Cyberpunk 2077 (REDengine 4) and Witcher 3 (REDengine 3) apply here; Witcher 4 / Project Polaris are Unreal Engine 5.
- **AC posture:** both shipped titles are single-player with no anti-cheat, so in-process reflection access (CET/RED4ext) is viable — a property of the title, not transferable to any future protected build.

## Common Pitfalls

- **Feeding fixed-point `WorldPosition` into float math.** The defining REDengine footgun: a position field may be integer/fractional fixed-point, not a `float32` `Vec3`. Classify every position field and decode the fixed-point form to world units before distance or W2S math.
- **Reversing fields cold instead of using the reflection DB.** Like RE Engine, REDengine is name-resolvable via RTTI. CET/RED4ext expose classes/fields/methods by name — use them rather than `struct_dump`-guessing offsets that die each patch.
- **Mistaking a UE5 successor for REDengine.** Witcher 4 / Project Polaris are Unreal Engine 5. Confirm the executable and reflection strings; if you see UE `GObjects` machinery, switch to the UE guide entirely.
- **Assuming Y-up.** Cyberpunk world space is Z-up; ported Y-up math swaps the wrong axis.
- **Expecting an anti-cheat that is not there (or assuming one never will be).** The shipped titles are single-player with no AC — but that freedom is title-specific and does not carry to any future protected CDPR build.
- **Treating Denuvo as a memory-access blocker.** Where present, Denuvo is anti-tamper/DRM; some Cyberpunk versions dropped it entirely. It does not stop authorized-session reads.
- **Skipping the position correctness check.** After resolving the puppet placement by name, read your own position and move in-game to confirm both the axis mapping and the float-vs-fixed-point classification.

## Cross-References

- `signatures/unreal-engine/ue-reversal-guide.md` — **use this for CDPR's future UE5 titles**, not the REDengine notes here.
- `knowledge/anti-cheat-architecture.md` — AC model for any future multiplayer CDPR title.
- `knowledge/game-targets.md` — engine-by-game cross-reference style.
- `knowledge/offset-methodology.md` — RIP resolution and sig-vs-hardcode discipline; prefer name-based resolution via the reflection DB here.
- `knowledge/common-patterns.md` — entity-iteration, world-to-screen, GUI patterns for wiring resolved fields into a script.
- `signatures/source-engine/common-sigs.md` — `resolve_rip` helper and uniqueness verification.
- `knowledge/pcx-api-cheatsheet.md` — `read_vec3_fl32`, `read_mat4_fl32`, `find_code_pattern`, `rs`/`rws` for reading reflected class-name strings; note the fixed-point `WorldPosition` needs manual decode, not a typed read.
- `skill://authorized-security-research` — scope/authorization (relevant for any future protected CDPR title).
- If you derive stable patterns or a reflection-DB-locate sig, add a stub under `signatures/redengine/` mirroring `signatures/unreal-engine/`.
