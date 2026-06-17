# Multi-Binary Targeting — One Script, N Game Versions

The pattern for supporting multiple binaries (game versions, architectures, storefront builds, beta channels) from one Enma codebase. A well-organized script can target v1.42.3 and v1.42.4, 32-bit and 64-bit, Steam and Epic, release and beta — without forking. The mechanics are simple but get reinvented in every project; this skill names them.

**Trigger when:** the user mentions multiple game versions, cross-build support, 32-bit vs 64-bit, multi-store builds (Steam / Epic / GOG / Microsoft Store), the script breaking on the demo / beta channel / PTU, supporting both an old and a new version simultaneously, or maintaining a "stable" and an "experimental" branch in parallel.

**Prerequisite:** `knowledge/script-organization-patterns.md` for the per-binary offset file layout this skill builds on; `.claude/skills/pcx-patch-day-playbook` for the per-patch maintenance workflow this skill scales up; `.claude/skills/re-evidence-log` for the per-binary evidence tracking that prevents claims from cross-contaminating.

---

## Trigger

`Game.exe` exists at multiple hashes the user wants to support; the user maintains a shared script for both the live and beta channels of a game; cross-architecture work (`game32.exe` and `game64.exe`); Steam and Epic builds of the same game ship with different DRM wrappers; a port from one binary to another that "should be similar" but isn't quite.

---

## 1. Identify the Binary at Runtime

**Hash the `.text` section (or its first N MB) at attach time; look up which offset set to use.**

Without runtime identification, the script has no way to pick offsets — it either hardcodes one binary's values (broken on the others) or relies on the user to manually swap offset files (error-prone, defeats the multi-binary point). The hash gives the script a stable handle for "which build am I attached to."

```cpp
import "vec";

const string TARGET_MODULE = "game.exe";

// Map from `.text` hash to the offset-set identifier (a label your code
// uses internally to pick the right OFFSET_* values per binary).
struct binary_id {
    string  hash_prefix;   // first 8-16 hex chars of the .text hash
    string  label;         // "v1.42.3", "v1.42.4_steam", "v1.42.4_epic"
    string  arch;          // "x64", "x86"
}

const binary_id KNOWN_BINARIES[] = {
    binary_id("7a3f4d1c", "v1.42.3",       "x64"),
    binary_id("9b2e8a07", "v1.42.4_steam", "x64"),
    binary_id("c4f12d83", "v1.42.4_epic",  "x64"),
};

string g_active_label = "unknown";

// Identify by hashing a small range from .text — first 4 MB is usually
// enough to discriminate between builds without being slow at attach.
string identify_binary(proc_t p) {
    uint64 base = p.base_address();
    if (base == 0) return "unknown";

    // (a real implementation reads the .text section bounds via the PE
    //  parser; this sketch uses a fixed window for clarity)
    const uint64 SAMPLE_BYTES = 0x400000;   // 4 MB
    array<uint8> buf;
    buf.resize(SAMPLE_BYTES);
    if (!p.read_memory(base + 0x1000, buf, SAMPLE_BYTES)) return "unknown";

    // Hash via a stable function — md5/sha is fine; even a CRC32 is
    // enough since you only need disambiguation, not cryptographic safety.
    string hash_prefix = format("{x}", crc32_buffer(buf, SAMPLE_BYTES));
    // (crc32_buffer is documented in docs/perception/cpu-api.md; or
    //  compute inline if you prefer)

    for (uint32 i = 0; i < KNOWN_BINARIES.length; i++) {
        if (hash_prefix.starts_with(KNOWN_BINARIES[i].hash_prefix)) {
            return KNOWN_BINARIES[i].label;
        }
    }
    return "unknown";
}
```

Notes on the hash choice:

- **`.text` only**, not the whole binary. `.data` / `.rdata` change with every patch (string updates, asset references); `.text` is stable across content-only updates.
- **Sample the first N MB**, not the whole `.text`. Reading 50 MB at attach to compute a hash is slow; the first 4 MB is enough to discriminate between distinct builds.
- **CRC32 is enough**. You're not checking cryptographic integrity, just disambiguating ~5-50 known builds. CRC32 is cheap and stdlib-trivial.
- **Skip headers and relocations** in the sample window — they change cosmetically across rebuilds without changing code. Start the sample at `.text + 0x1000` (past the prologue padding).

**Why:** Without runtime identification, the script either guesses or asks the user. Guessing breaks; asking-the-user adds a manual step that defeats the multi-binary goal. The hash is the cheap, robust handle.

---

## 2. One `offsets-<label>.em` per Binary, One Common `main.em`

**The canonical layout: a `dispatch` module identifies the binary at attach, then re-exports the right per-binary constants under a common name. Every feature module imports the dispatched constants, not the per-binary ones.**

The project tree:

```
project/
├── globals.em                # proc handle, base, cached state — binary-agnostic
├── offsets-v1.42.3.em        # const uint64 OFF_ENTITY_LIST_V1_42_3 = 0x...;
├── offsets-v1.42.4_steam.em  # const uint64 OFF_ENTITY_LIST_V1_42_4_STEAM = 0x...;
├── offsets-v1.42.4_epic.em   # const uint64 OFF_ENTITY_LIST_V1_42_4_EPIC = 0x...;
├── dispatch.em               # identifies binary, selects offset set
├── esp.em                    # imports from dispatch, never from offsets-*.em
├── aim.em                    # same
├── menu.em
└── main.em
```

The `dispatch.em` module is the trick. It identifies the binary, then exposes a *common* set of names every feature uses:

```cpp
// dispatch.em
import "offsets-v1.42.3";
import "offsets-v1.42.4_steam";
import "offsets-v1.42.4_epic";

// The names every other file imports.
uint64 g_off_entity_list = 0;
uint64 g_off_local_player_slot = 0;
uint64 g_off_view_matrix = 0;
string g_sig_entity_list = "";
// ... (one per offset/sig the project uses)

bool dispatch_select(string label) {
    if (label == "v1.42.3") {
        g_off_entity_list      = OFF_ENTITY_LIST_V1_42_3;
        g_off_local_player_slot = OFF_LOCAL_PLAYER_SLOT_V1_42_3;
        g_off_view_matrix      = OFF_VIEW_MATRIX_V1_42_3;
        g_sig_entity_list      = SIG_ENTITY_LIST_V1_42_3;
        return true;
    } else if (label == "v1.42.4_steam") {
        g_off_entity_list      = OFF_ENTITY_LIST_V1_42_4_STEAM;
        // ... etc
        return true;
    } else if (label == "v1.42.4_epic") {
        // ...
        return true;
    }
    return false;
}
```

And `main.em` wires it up:

```cpp
import "dispatch";
import "globals";
import "esp";
import "aim";
import "menu";

int64 main() {
    g_proc = ref_process(TARGET_MODULE);
    if (!g_proc.alive()) { println("not attached"); return 0; }

    g_active_label = identify_binary(g_proc);
    if (!dispatch_select(g_active_label)) {
        println(format("unknown binary: {s}; no offsets available", g_active_label));
        return 0;
    }
    println(format("loaded offsets for {s}", g_active_label));

    setup_gui();
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
```

Feature modules never know which binary is active:

```cpp
// esp.em
import "dispatch";  // for g_off_entity_list

void update_entities() {
    uint64 list_ptr = g_proc.ru64(g_off_entity_list);
    if (list_ptr == 0) return;
    // ... feature logic ...
}
```

This isolates per-binary churn to `offsets-*.em` and `dispatch.em`. Adding a new build means:

1. Add `offsets-<new>.em` with the per-build constants.
2. Add a row to `KNOWN_BINARIES[]` in `dispatch.em`.
3. Add an `else if (label == "<new>")` branch in `dispatch_select`.
4. Done. Every feature module works against the new build automatically.

**Why:** Without the dispatch indirection, every feature module has to know about every supported binary, and a build-add becomes an N-file change. With it, the per-build delta is localized.

---

## 3. Sig Sets vs Hardcoded Resolved Addresses

**Prefer sigs; they survive minor patches. Fall back to per-build hardcoded RVAs only when sigs are ambiguous, or when the binary varies in a way sigs can't bridge.**

Three modes, in order of preference:

- **Same sig across all builds** (best). The sig matches in every build, RIP-resolves to the right address per build. Only the resolved address differs; the sig string in `offsets-*.em` is identical across files. Verify by running `tools/sig-uniqueness-checker.py` against each binary.
- **Per-build sig variants**. The sig had to drift because the instruction sequence changed in one of the builds. Each `offsets-<label>.em` carries its own sig string; the resolution code is shared.
- **Per-build hardcoded RVAs** (last resort). The sig can't be made to work across builds (instruction layout too different, or the function was inlined in one build); fall back to RVA constants per build. Brittle — the next patch invalidates the RVA — but works when nothing else does.

A unified sig set with per-build RIP-offset overrides covers the middle case:

```cpp
// dispatch.em — when the sig is shared but the RIP arithmetic differs
// (e.g. one build uses LEA r64, [rip+disp32] (7B), another uses
//  LEA r64, [rip+disp8] (4B) — same sig prefix, different insn_len)
struct rip_resolver {
    string sig;
    uint64 disp_at;     // byte offset within the matched instruction
    uint64 insn_len;    // total instruction length
}

rip_resolver g_resolve_entity_list;

void configure_resolvers(string label) {
    if (label == "v1.42.3" || label == "v1.42.4_steam") {
        g_resolve_entity_list = rip_resolver(SIG_ENTITY_LIST, 3, 7);   // standard LEA
    } else if (label == "v1.42.4_epic") {
        g_resolve_entity_list = rip_resolver(SIG_ENTITY_LIST, 3, 4);   // short-disp LEA
    }
}

uint64 resolve_entity_list_addr() {
    uint64 base = g_proc.base_address();
    uint64 size = g_proc.get_module_size(TARGET_MODULE);
    uint64 hit = g_proc.find_code_pattern(base, size, g_resolve_entity_list.sig);
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + g_resolve_entity_list.disp_at);
    return hit + g_resolve_entity_list.insn_len + cast<uint64>(disp);
}
```

Decision tree per offset, per supported build:

```
1. Does the same sig hit uniquely in every supported build? YES → shared sig.
2. Does a per-build sig variant hit uniquely? YES → per-build sig string.
3. Is the resolved RVA stable across at least one rebuild family? YES → hardcoded RVA.
4. None of the above? → re-RE from a closer xref; the current anchor is too unstable.
```

Cross-reference `tools/offset-diff.py` and `tools/sig-uniqueness-checker.py` for the validation workflow per build.

**Why:** Hardcoded RVAs are the multi-binary worst case — they invalidate at every patch and must be re-derived per build. Sigs let you ship one offset string that works on N versions, dropping the maintenance per-version to near zero. The choice between "shared sig + per-build RIP" and "per-build sig" is a 5-second `offset-diff.py` check; reach for it before committing.

---

## 4. Architecture Differences (x86 vs x64)

**Pointer size, calling convention, instruction-length, and sometimes struct layout all change between x86 and x64 builds. The script needs branches per architecture; isolate them in `offsets-<label>.em` and a thin abstraction in `dispatch.em`.**

What changes between a 32-bit and 64-bit build of the same game:

| Property | x86 | x64 |
|---|---|---|
| Pointer size | 4 bytes | 8 bytes |
| Pointer read API | `proc.r32(addr)` | `proc.ru64(addr)` |
| Struct field offsets | Often differ — alignment and pointer fields shift | Typically the canonical layout |
| Calling convention | `__stdcall` / `__cdecl` / `__fastcall` (variable) | MS x64 ABI (Windows) / SysV (Linux) |
| Instruction prefixes in sigs | No REX prefix (`48 ...`) | REX prefix common (`48 8B`, `48 8D`) |
| RIP-relative addressing | Not available (x86 uses absolute disp32) | The norm (most globals are RIP-resolved) |
| Branch/jump encoding | Same form, narrower range | Same form, often the same bytes |

The implication: x86 and x64 builds of the same engine require *largely separate* offset sets, not minor patches. Treat them as different binaries for multi-binary purposes:

```
offsets-v1.42.3_x64.em
offsets-v1.42.3_x86.em
```

Inside `dispatch.em`, the per-arch difference is usually a different *helper* per offset (pointer reads, struct walks) rather than a different *constant*:

```cpp
// Wrapper that reads the right width per active architecture
uint64 ptr_read(uint64 addr) {
    if (g_active_arch == "x64") return g_proc.ru64(addr);
    if (g_active_arch == "x86") return cast<uint64>(g_proc.r32(addr));
    return 0;
}
```

Feature code uses `ptr_read` instead of `ru64` directly, and the script works against either architecture.

When the offset set differs *significantly* in struct layout (because the engine's structs have different field shapes per architecture, not just per build), it's often cleaner to maintain genuinely separate feature implementations per architecture, joined only by the shared `globals.em` and `main.em`. The 30%-divergence heuristic in section 7 below applies.

**Why:** A pointer that's 4 bytes on x86 and 8 bytes on x64 is the single most common silent-failure source in cross-arch scripts. The abstraction is two lines; the bug-class it eliminates is broad.

---

## 5. Storefront Variation (Steam / Epic / GOG / Microsoft Store)

**Same game content, different DRM wrapper. The wrapper changes the entry point and may move `.text`; sigs based on internal engine anchors usually survive, sigs near the original entry point usually don't.**

Storefronts ship the same engine binary wrapped in DRM specific to their platform:

- **Steam** — `steam_api.dll` / `steam_api64.dll` linked; sometimes Steamworks DRM stub at the entry point; Steamworks call sites scattered through code.
- **Epic** — `EOSSDK-Win64-Shipping.dll`; Epic Online Services init shim; usually less invasive than Steamworks.
- **GOG** — Galaxy SDK shim; sometimes plus an Arxan or VMProtect wrapper for DRM.
- **Microsoft Store** — UWP packaging; binary may be inside a `WindowsApps` container with restricted access.
- **Standalone / itch.io** — usually no wrapper at all; closest to the developer's own build.

What this means for offsets:

- Sigs targeting *engine* code (entity list, view matrix, player struct) almost always work across storefronts unchanged.
- Sigs targeting *runtime initialization* (early-attach hooks, DRM-wrapped functions) often need per-store variants.
- The DRM wrapper sometimes alters the module name — `game.exe` vs `game-Win64-Shipping.exe` vs `game_steam.exe`. Identify both the module name AND the binary hash per storefront in your `KNOWN_BINARIES` table.

The detection pattern: a small per-storefront probe runs after attach, looking for the DRM-DLL fingerprint:

```cpp
string detect_storefront(proc_t p) {
    if (p.get_module_base("steam_api64.dll") != 0 ||
        p.get_module_base("steam_api.dll")   != 0) return "steam";
    if (p.get_module_base("EOSSDK-Win64-Shipping.dll") != 0) return "epic";
    if (p.get_module_base("Galaxy64.dll") != 0)             return "gog";
    return "standalone";
}
```

Combine with the hash-based identification — `label = "{version}_{storefront}"` gives you the dispatch key you need.

**Why:** Many users have the same game across multiple stores; the script's user-perceived support breadth is the cross-product of versions × storefronts. Catching the DRM-DLL fingerprint is a 5-line check that doubles or triples how many users your script "just works" for.

---

## 6. Channel Variation (Release / Beta / PTU / Demo)

**Same engine, different content packs, sometimes different telemetry. Engine-code sigs survive across channels; content-script sigs (UI strings, level-specific behaviors) may not.**

Games ship multiple channels for testing and engagement:

- **Release** — the public, stable build.
- **Beta** — early access to upcoming features, semi-public.
- **PTU / PTR** (Public Test Universe / Realm) — pre-release testing channel, semi-public.
- **Demo / Free Trial** — limited content, public.
- **Internal / staff** — not user-facing; if you have access to one, the engine layout may match release but the content does not.

What this means for offsets:

- Engine code is usually identical or near-identical across channels (same binary build pipeline, same engine version) — engine-targeted sigs survive.
- Content-driven offsets (level-specific entity slots, UI panel addresses tied to specific menus) often differ — content-targeted sigs may not.
- Telemetry sometimes differs — the beta channel may have additional anti-cheat instrumentation the release doesn't, or vice versa; the additional code shifts addresses.

The pattern: dispatch on `version_channel` (e.g. `v1.42.3_release`, `v1.42.3_beta`, `v1.42.3_ptu`), treat each as a distinct binary in `KNOWN_BINARIES`. If you find that 95% of offsets are identical between two channels, you can collapse them into a shared dispatch entry — but be explicit about it (a comment in `dispatch.em` saying "v1.42.3 release and beta share all sigs; PTU does not").

**Why:** Users on beta / PTU channels are usually the most engaged users; supporting them well matters disproportionately to the script's reception. The channel-detection layer is the same hash check — adding channel coverage is free if the hash table already exists.

---

## 7. Graceful Degradation When No Offset Set Matches

**The script should not crash on an unknown binary; it should print a clear message and skip its features. Features that don't depend on the missing offsets should still work.**

The failure-handling pattern:

```cpp
int64 main() {
    g_proc = ref_process(TARGET_MODULE);
    if (!g_proc.alive()) {
        println(format("[{s}] target process not attached", SCRIPT_NAME));
        return 0;
    }

    g_active_label = identify_binary(g_proc);
    if (g_active_label == "unknown") {
        uint64 base = g_proc.base_address();
        uint64 size = g_proc.get_module_size(TARGET_MODULE);
        println(format("[{s}] unknown binary build at base 0x{x} (size 0x{x})",
                       SCRIPT_NAME, base, size));
        println(format("[{s}] hash: {s} — add to KNOWN_BINARIES to enable support",
                       SCRIPT_NAME, current_hash));
        // Still register routines — the GUI loads, the user sees the status,
        // but features that need offsets are gracefully no-op.
        setup_gui();
        register_routine(cast<int64>(on_update_unknown), 0);
        register_routine(cast<int64>(on_render_unknown), 0);
        return 1;
    }

    if (!dispatch_select(g_active_label)) {
        println(format("[{s}] dispatch failed for label {s}",
                       SCRIPT_NAME, g_active_label));
        return 0;
    }

    println(format("[{s}] loaded offsets for {s}", SCRIPT_NAME, g_active_label));
    setup_gui();
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

void on_render_unknown(int64 data) {
    // Minimal render — show the user the script is loaded but offsets missing.
    draw_text(format("[{s}] unknown binary — see console", SCRIPT_NAME),
              vec2(10.0, 10.0), color(255, 200, 80, 255),
              get_font20(), 1, color(0, 0, 0, 200), 1.0);
}
```

The principles:

- **Never silently no-op.** A script that loads but does nothing visible is indistinguishable from a broken install. The on-screen text tells the user what happened.
- **Print the hash to the console** so the user can report it ("got hash 8e4f2a... on the new build"); you can add it to `KNOWN_BINARIES` in the next release.
- **Keep the GUI alive.** Even with no offsets, the user can interact with the menu, knows the script is loaded, and gets feedback when they re-attach to a supported build.
- **Cross-reference the patch-day skill.** When users report an unknown hash on a new build, the playbook in `skill://pcx-patch-day-playbook` is the workflow for adding support.

**Why:** Graceful degradation turns "the script is broken on the new build" reports into "the script noticed it doesn't have offsets for the new build" reports. Same problem, much better signal-to-noise for triage.

---

## When NOT to Multi-Target

**The pattern has a maintenance ceiling. When the binary changes structurally between versions, N offset sets become unsustainable; fork the script instead.**

Heuristics for when to fork:

| Signal | Reaction |
|---|---|
| >30% of sigs need per-version overrides | Engine rebuild or major refactor — fork |
| Struct layouts vary materially per version | Rewrite features per version, share only `main.em` |
| IL2CPP regeneration (Unity titles) between versions | Each regen invalidates the offset metadata; multi-target is fragile, fork is cleaner |
| The dispatched offsets file grows past ~500 lines per binary | The complexity is in the per-binary differences, not in shared logic — fork |
| Two versions are being maintained on different release cadences | Effort to keep them merged exceeds effort to maintain separately |

Forking pattern: separate branches (`main-v1.42.x`, `main-v1.43.x`) with selective cherry-picking of feature work between them. Heavier ops-wise, lighter cognition-wise — each branch's `offsets.em` is for one binary.

The threshold is subjective; the rough rule is "if the dispatch table is more complex than the feature code, you're past the ceiling."

**Why:** Multi-binary targeting is a power tool with a sweet spot. Below the sweet spot (2-5 builds, mostly shared code), it's strictly better than forking. Above it (10+ builds, mostly divergent code), it becomes a maintenance trap. Know when to switch.

---

## Summary

| # | Topic | One-liner |
|---|---|---|
| 1 | Identify the binary at runtime | Hash `.text` first N MB → look up in `KNOWN_BINARIES` |
| 2 | Per-binary offsets, common dispatch | `offsets-<label>.em` files; `dispatch.em` re-exports under shared names |
| 3 | Sigs over hardcoded RVAs | Shared sig > per-build sig > per-build RVA, in that preference order |
| 4 | Architecture (x86 vs x64) abstraction | `ptr_read` helper handles 4-vs-8-byte pointers; separate offset sets |
| 5 | Storefront detection | DRM-DLL fingerprint adds `_steam` / `_epic` / `_gog` to the label |
| 6 | Channel detection | Treat release / beta / PTU as distinct hashes; collapse only when verified identical |
| 7 | Graceful degradation | Unknown binary → print hash, keep GUI alive, no-op features |

**When NOT to multi-target:** >30% of sigs need per-version overrides → fork instead of patching.

**Cross-references:** `knowledge/script-organization-patterns.md` (the layered file structure this skill scales up); `.claude/skills/pcx-patch-day-playbook` (per-patch workflow — the multi-binary case is N patch days run in parallel); `.claude/skills/re-evidence-log` (per-binary evidence files keep claims isolated); `tools/offset-diff.py` (per-build sig validation), `tools/sig-uniqueness-checker.py` (per-build sig verdicts), `tools/dumper-to-enma.py` (regenerate per-build offset modules from updated dumper output).
