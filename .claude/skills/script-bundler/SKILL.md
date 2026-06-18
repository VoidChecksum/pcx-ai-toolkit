---
name: script-bundler
description: >
  Build and deployment workflow for PCX scripts: .em vs .emb, bundle order
  respecting the module-import graph, hot-reload survival, pre-ship hygiene
  checklist, runtime-version pinning, and distribution metadata. Triggers
  when packaging, distributing, or releasing scripts to other users.
license: MIT
---

# Script Bundler — Packaging and Shipping PCX Scripts

The build and deployment workflow for PCX scripts: when to distribute raw `.em` source vs precompiled `.emb`, the bundle order that respects the module-import graph, what survives hot-reload, the pre-ship hygiene checklist, runtime-version pinning, and the distribution metadata that goes alongside the script. Closes the "how do I package this for someone else to use" gap; sits beside `pcx-patch-day-playbook` (the inbound workflow for receiving updates) as the outbound workflow for sending them.

**Trigger when:** the user mentions building, shipping, releasing, packaging, distributing, `.emb`, `.em` archive, sharing with someone, multi-user setup, marketplace upload, or asks about what survives hot-reload, what to strip before publishing, or how to handle multi-file projects across editors.

**Prerequisite:** `docs/enma/sdk-serialization-and-linking.md` for the `.emb` binary format and `serialize` / `link` APIs; `docs/enma/sdk-hot-reload.md` for what persists across reloads; `docs/enma/lang-modules.md` for the import system the bundler resolves; `templates/full-project/` as the canonical 5-file scaffold this skill builds on.

---

## Trigger

Shipping a script to a user, packaging a project for distribution, multi-file project that needs a single-file artifact, marketplace upload requiring source stripping, hot-reload questions about what state survives, pre-release hygiene check, version compatibility planning, sharing with a teammate who is on a different PCX version.

---

## 1. When to Ship `.em` vs `.emb`

**Plain `.em` source is debuggable and user-editable; precompiled `.emb` loads faster, hides incidental file paths, and obfuscates trivially-inspectable strings. The choice is per audience, not per project.**

| Property | `.em` (source) | `.emb` (precompiled) |
|---|---|---|
| Recipient can read the code | Yes | No (XOR-obfuscated body) |
| Recipient can edit/tune | Yes (open in editor) | No (must rebuild from source) |
| Recipient sees your file paths | Yes (and your username if absolute) | No when `keep_debug=false` |
| Load time | Compile + link on every load | Deserialize only (faster) |
| Version compatibility | Source compiles against any compatible runtime | Locked to the `.emb` format version (`k_emb_version`); breaks across major bumps |
| Stack traces / error messages | Full file:line | Reduced when `keep_debug=false` (`get_last_executed_line` returns 0) |
| Casual `strings` inspection reveals API/struct names | Yes | No (header-stored salt XORs strings) |

Decision matrix:

- **Internal team / single developer** — `.em`. You're the recipient; the source-readability win compounds with editor tooling.
- **Trusted partner who will tune knobs** — `.em` with a `README` pointing at the config block. They'll tweak; `.emb` would force a rebuild round-trip.
- **Public release / marketplace** — `.emb` with `keep_debug=false`. The host-side serializer call is `serialize(mod, data, false)`; this drops the `source_map` and `debug_functions` tables so your absolute source paths don't ship.
- **Library you ship for others to depend on** — `.emb`, document the `k_emb_version` it was built against, ship a source bundle alongside for users who want to recompile.

The two formats are *not* mutually exclusive — many projects ship the `.emb` as the primary artifact and the `.em` source in an `src/` folder for users who want to inspect or modify.

**Why:** Picking `.emb` because "it's faster" is rarely the right reason — load-time difference is milliseconds either way. Picking it because you want path stripping, body obfuscation, or distribution-format consistency *is* the right reason. State the reason in the project README so a future maintainer doesn't switch formats arbitrarily.

---

## 2. The Canonical Bundle Order

**The `templates/full-project/` scaffold defines the order: `globals → offsets → feature → menu → main`. Each file imports only files above it; there are no cycles. Violating the order produces link errors at bundle time or, worse, run-time symbol resolution failures that surface only when the unlinked code path is hit.**

The import graph as ASCII:

```
                          main.em
                         /   |   \
                        /    |    \
                     menu  feature1 feature2  (... featureN)
                       \    /   |    /
                        \  /    |   /
                       offsets-<binary>.em
                              |
                          globals.em
                              |
                            (stdlib)
```

What each layer is allowed to import:

| Layer | May import |
|---|---|
| `globals.em` | stdlib only — `vec`, `color`, `math`, `time`, etc. |
| `offsets-<binary>.em` | `globals.em` plus stdlib |
| `feature-<name>.em` | `globals.em`, `offsets.em`, plus stdlib — never another feature |
| `menu.em` | `globals.em` plus stdlib (no offsets, no features — menu state is config, not gameplay) |
| `main.em` | every other file in the project |

The rules in plain language:

- A feature **never** imports another feature. If two features need the same data, the data lives in `globals.em` (read) or a `utils-*.em` module (function library). See `knowledge/script-organization-patterns.md` for the "when to extract a util" heuristic.
- The menu **never** imports a feature. Widgets bind to globals in `globals.em`; features read those globals. The decoupling means a disabled feature still has working widgets (they just don't do anything).
- `offsets.em` is per-binary, not per-feature. If you target multiple binaries (rare), `offsets-game.em` and `offsets-editor.em` each exist, and the right one is imported in `main.em` based on which binary you attached to.

When you violate the order:

- **Cycle (`featureA` imports `featureB` which imports `featureA`)** — bundle-time error from the linker.
- **Feature imports another feature** — link succeeds, but you've coupled them; touching one now risks the other.
- **Menu imports a feature** — link succeeds, but disabling the feature in the bundle breaks the menu, which is the opposite of what the layering exists to enable.

For the host-side `link()` call (when you're embedding the engine yourself and combining modules at the C++ level):

```cpp
const char* names[] = { "globals", "offsets", "feature_esp", "feature_aim", "menu", "main" };
module_t*   mods[]  = { /* compiled in the same order */ };
module_t*   linked  = link(e, names, mods, 6);
```

The `names` array is the symbol prefix per module — `globals::g_proc` is how `feature_esp` accesses a global. This means even at the linker level, the dependency graph is explicit and any forbidden reference is a compile-time error.

**Why:** Layering is the cheapest enforcement of `game-cheat-guidelines` #6 (one feature per file). It forces every cross-feature interaction through `globals.em`, which is where you can audit them. Without the layering, the project's modules drift into a hairball within a month.

---

## 3. Hot-Reload-Safe Boundaries

**Reload replaces only the script code. Globals, registered types, and native functions persist. Design state lifetimes around this.**

What survives a hot reload (per `docs/enma/sdk-hot-reload.md`):

- The target process and its memory (you do not re-attach; the `proc_t` handle remains valid in your globals if you stored one — but you should re-attach in `main()` anyway as a freshness check)
- Registered native functions and types — unchanged
- The engine and all live contexts — same `context_t*` pointers continue to work
- Host-side state — your C++ code holding the module pointer

What does NOT survive a hot reload:

- Script-level globals (in Enma terms, the script's runtime state) — reset to their declaration defaults
- Cached pattern-scan results — re-resolve in the new `main()` or in the first frame after reload
- GUI section state in the script's data — re-create the section, re-bind widgets to the new globals
- Any in-script delegate / function pointer table — must be re-built

The implication is a strict separation between *script state* (lost on reload) and *host state* (preserved):

```cpp
// In your script — assume everything resets each load
proc_t g_proc;
uint64 g_base = 0;
bool   g_resolved = false;
uint64 g_entity_list = 0;

int64 main() {
    // EVERY load runs this — sigs resolve fresh, no carry-over
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) return 0;
    g_base = g_proc.base_address();

    uint64 size = g_proc.get_module_size("game.exe");
    uint64 hit = g_proc.find_code_pattern(g_base, size, SIG_ENTITY_LIST);
    if (hit == 0) return 0;
    g_entity_list = resolve_rip(g_proc, hit, 3, 7);
    g_resolved = g_entity_list != 0;

    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
```

For state you *want* to survive a reload (config tunings the user has set, last-used hotkey), persist to disk and reload in `main()`:

```cpp
import "json";

int64 main() {
    // ... process attach ...
    load_config_from_disk();        // restores g_esp_enabled, g_smoothing, etc.
    setup_gui();                    // widgets bind to the restored values
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
```

`knowledge/script-organization-patterns.md` covers the file/JSON persistence pattern in detail.

**Why:** Code that assumes globals survive a reload reads stale or zero data on the first frame after reload — the overlay draws nothing, the user notices, you waste twenty minutes debugging what "broke" since the last edit. Treating `main()` as the authoritative initializer (every reload, every load, fresh state) avoids the entire class of bug.

---

## 4. Pre-Ship Hygiene Checklist

**Before zipping, uploading, or sending the artifact anywhere, run through every item. Cost: five minutes. Cost of skipping: the embarrassing thing on someone else's machine.**

```
PRE-SHIP HYGIENE CHECKLIST

[ ] No hardcoded usernames, machine names, or absolute paths in default config values
    grep -nE '(C:\\Users\\|/home/|/Users/)' src/

[ ] No debug println of resolved offsets / addresses / process handles in production paths
    grep -nE 'println\(.*0x[0-9A-Fa-f]+' src/

[ ] No `// TODO`, `// FIXME`, `// HACK`, `// XXX` left in shipped code
    grep -nE '(TODO|FIXME|HACK|XXX)' src/

[ ] No file-system writes outside the documented config dir
    grep -nE 'fs_write_file\(' src/   # then audit each path

[ ] No network calls to anything that isn't a documented service
    grep -nE 'http_(get|post)|websocket' src/

[ ] No leftover XOR-encrypted strings revealing internal infrastructure
    (run tools/dump-strings-xor.py against your built .emb to check)

[ ] All offsets carry `// E-NNN` references into evidence/<hash>.md (per skill://re-evidence-log)
    grep -cE '// E-[0-9]+' offsets.em   # should be > 0

[ ] All sigs verified UNIQUE on the target binary
    (run tools/sig-uniqueness-checker.py against the offsets file)

[ ] Module name in ref_process() is the actual target, not a placeholder
    grep -nE 'ref_process\("' src/

[ ] No commented-out blocks of "old experiment" code — delete them; git keeps history

[ ] GUI defaults are sensible for a first-time user (not your tuned-for-you values)

[ ] LICENSE file present and accurate

[ ] README points at the right PCX version, the right game, the right install path

[ ] CHANGELOG entry for THIS release exists, with the user-visible changes named
```

Most of these are one-line greps you can wire into a shell script run before every release. Save it as `pre-ship.sh` in your project — when the grep output is non-empty, the release is not ready.

**Why:** Every item on the list maps to a specific class of complaint the recipient will file. Hardcoded paths break on Windows vs Linux. Debug printlns leak internals. TODOs imply the script isn't finished. Network calls to your private server make the recipient's network admin nervous. The five minutes is cheap insurance against the "but it worked on my machine" support burden.

---

## 5. Runtime Version Pinning

**The script should declare which PCX runtime version it expects. The consumer should fail fast if the runtime is too old — clear error message, not silent wrong behavior.**

PCX evolves; APIs are added across versions. A script that uses `world_to_screen_rowmajor` (added in a specific PCX version per `docs/perception/changelogs.md`) will not link on a runtime that predates it — but the error message can be confusing if the user doesn't know which runtime they're on.

The defensive pattern:

```cpp
// At the very top of main.em
#define PCX_REQUIRED_MAJOR 2
#define PCX_REQUIRED_MINOR 4

int64 main() {
    // If the runtime exposes a version-query API, use it (check docs/perception/changelogs.md
    // for the canonical accessor name; this is a defensive sketch).
    //
    // Fallback when no version API exists: rely on the link-time error from a known API
    // that exists only in PCX_REQUIRED_MAJOR.PCX_REQUIRED_MINOR+; that becomes the
    // version-check by proxy.

    println(format("script requires PCX v{d}.{d}+", PCX_REQUIRED_MAJOR, PCX_REQUIRED_MINOR));

    // ... rest of main ...
    return 1;
}
```

In the project README, document the version requirement explicitly:

```markdown
## Requirements
- Perception.cx runtime **2.4+** (this script uses `world_to_screen_rowmajor`,
  introduced in 2.4 — earlier versions will not link).
- Game build verified against: **MyGame v1.42.3** (SHA-256: 7a3f4d1c...).
- Tested with PCX scripting frontend versions: 2.4.0, 2.4.1, 2.4.3.
```

Cross-reference `knowledge/pcx-version-matrix.md` (the by-version API availability table) when deciding which version to pin to.

For `.emb` artifacts, the `k_emb_version` format version is encoded in the binary header and the host-side `deserialize` will reject too-new or too-old `.emb` files cleanly. You don't need to do anything; this is how the runtime enforces format compatibility independent of your code.

**Why:** Without explicit pinning, a user on an older runtime gets a cryptic "function not found" or, worse, silently runs on a partial-feature install. Pinning at the top of the file makes the requirement self-documenting, and the README echo means the requirement is visible *before* the user runs the script.

---

## 6. Distribution Metadata

**Alongside the script artifact: a recipient-facing `README.md`, a `LICENSE`, and a `CHANGELOG`. One page each. Cheap to write, expensive to omit.**

Template — `README.md` for the recipient (not your developer README; that's separate):

```markdown
# <project_name>

What it does: <one sentence>.
Target: <game> v<X.Y.Z> (other versions may or may not work).
Requires: Perception.cx runtime <X.Y>+ (see "Requirements" below).

## Install
1. Copy `<project>.em` (or `<project>.emb`) into your PCX scripts directory:
   - Windows: `%LOCALAPPDATA%\Perception\scripts\`
   - macOS / Linux: see the official PCX install path docs
2. In the PCX IDE, load the script.
3. Open the `<project>` GUI section in the sidebar.
4. Toggle features as desired; hotkeys default per the GUI labels.

## Requirements
- Game: <name> v<X.Y.Z>
- Runtime: PCX v<X.Y>+
- Binary hash (target): <sha256>

## Configuration
The script auto-saves your GUI tunings to `<config_path>` after every change.
On first run, defaults are loaded.

## Verify Install
- Attach the script in the IDE; expect a one-line console message: "<project> v<X.Y.Z> loaded".
- If you see "process not found", the game isn't running.
- If you see "signature scan failed", the game version doesn't match — see Patch Day.

## Patch Day
When the game updates and the script stops working, see the project's `patch-log.md` for known affected sigs. If not yet patched, the script will say which sig failed; report it back to the project.

## Known Limitations
- <list>

## Credits / License
MIT (or whatever). Author: <name>. Source: <link>.
```

`LICENSE` — pick one, ship it. Most PCX scripts use MIT; some use GPL. Don't ship anything without a `LICENSE`; recipients will redistribute and the absence makes the legal situation unclear.

`CHANGELOG.md` — one entry per release, newest first:

```markdown
# Changelog

## [1.2.0] — 2026-06-17
### Added
- Minimap with rotation.
- GUI hotkey: F8 toggles overlay.

### Fixed
- ESP no longer draws behind the camera (w > 0.001 gate).
- Entity-list sig moved in game v1.42.3 — re-derived.

### Changed
- Smoothing default 6.0 → 8.0 (felt too snappy in playtests).

## [1.1.0] — 2026-05-30
...
```

The CHANGELOG is what the user reads when "I just updated and something is different." It's the most-read file in the package after the README.

**Why:** Recipients don't read your code; they read your README. They don't grep your git log; they read your CHANGELOG. They will redistribute if there's a LICENSE and won't if there isn't (or won't legally, anyway). Each file takes five minutes; together they cover ~90% of the support burden you would otherwise field directly.

---

## Pre-Ship Checklist (Condensed)

Run through this every release:

```
[ ] No hardcoded paths / usernames / machine names
[ ] No debug println leaking offsets or addresses
[ ] No TODO / FIXME / HACK / XXX
[ ] No file-system writes outside the documented config dir
[ ] No network calls to non-public endpoints
[ ] No commented-out experimental code blocks
[ ] All offsets cite an evidence entry (skill://re-evidence-log)
[ ] All sigs verdict UNIQUE (tools/sig-uniqueness-checker.py)
[ ] Runtime version pinned at top of main.em
[ ] README.md present, current, recipient-facing
[ ] LICENSE present and accurate
[ ] CHANGELOG entry for this release exists
[ ] (If shipping .emb) serialize called with keep_debug=false
[ ] (If shipping .emb) tested by deserialize on a clean runtime
[ ] Sensible GUI defaults for a first-time user
```

If you script the checklist, save it as `pre-ship.sh` and run it before every `git tag`.

---

## Summary

| # | Topic | One-liner |
|---|---|---|
| 1 | `.em` vs `.emb` | Source for trusted users + tuning; precompiled for marketplace / path stripping |
| 2 | Bundle order | `globals → offsets → feature → menu → main`; features never import features |
| 3 | Hot-reload boundaries | Globals reset, target process survives; `main()` is the authoritative initializer |
| 4 | Pre-ship hygiene | Greppable checklist; five minutes; prevents most support tickets |
| 5 | Runtime version pinning | `#define PCX_REQUIRED_MAJOR/MINOR` at top of main.em; README echoes it |
| 6 | Distribution metadata | `README` + `LICENSE` + `CHANGELOG` — one page each, cover 90% of support |

**Cross-references:** `skill://pcx-patch-day-playbook` (inbound workflow for receiving updates; this skill is the outbound workflow for sending them); `skill://re-evidence-log` (offsets ship with stable `E-NNN` IDs cross-referenced from the bundle); `knowledge/script-organization-patterns.md` (the layered structure the bundle order respects); `knowledge/pcx-version-matrix.md` (lookup table for which APIs landed in which runtime version, used for version pinning); `docs/enma/sdk-serialization-and-linking.md` (host-side `serialize` / `link` APIs the bundler invokes); `docs/enma/sdk-hot-reload.md` (the reload semantics this skill designs around).
