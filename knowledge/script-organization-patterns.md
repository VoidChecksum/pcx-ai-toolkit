# Script Organization Patterns

How an Enma project on Perception.cx is laid out once it grows past a single
feature. This file picks up where `templates/full-project/` stops: that scaffold
is five files and one feature; here we cover the patterns that emerge at scale —
ten or twenty features, persistent config, multiple binaries, shared utility
modules, and more than one script alive in the same session.

> **Read this before** turning the `templates/full-project/` scaffold into a real
> multi-feature project. The five-file layout is the *starting point*; everything
> below extends it without re-architecting it. If you are writing a single
> overlay, stop at the scaffold — none of this earns its keep yet.

The one rule the whole toolkit agrees on (`game-cheat-guidelines` #6, *one
feature, one file*) is the floor, not the ceiling. The hard questions start the
moment two features want the same offset, the same `world_to_screen`, or the same
config file. This is the decision guide for those questions.

---

## The 5-file baseline (review)

The scaffold in `templates/full-project/` is the smallest layout that already
honors the guidelines. Five files, one direction of dependency, one bundle order:

```
templates/full-project/
├── globals.em   # proc_t, module base/size, config bound to GUI
├── offsets.em   # named sigs + RIP-relative resolver (imports globals)
├── feature.em   # one feature: update reads, render draws (imports globals, offsets)
├── menu.em      # GUI sidebar + config save/load (imports globals)
└── main.em      # main(): attach, resolve, setup_menu, register routines
```

Bundle order is the dependency order: `globals → offsets → feature → menu →
main`. Nothing imports `main`; `globals` imports nothing project-local. Every
other file reaches *down* toward `globals`, never sideways into a sibling
feature. Keep that arrow pointing one way and the project stays reloadable.

Everything in this document is a way of adding files to that picture *without*
breaking the arrow. When a new pattern tempts you to make `feature_a.em` import
`feature_b.em`, that is the signal that the shared thing belongs in `globals.em`
or a new utility module — not in a sibling.

---

## Shared state: what goes where

**`globals.em` holds state every feature reads. A feature's own tuning lives in
the feature file.** The test: if exactly one feature cares about a variable, it
is not global.

Cross-feature state — the process handle, the module base/size, the resolved
entity-list pointer, a per-tick entity cache — belongs in `globals.em` because
ESP, radar, and aimbot all read the same entities and you walk that list once
(rule #4, separate scan from render; rule #6, don't duplicate reads). Per-feature
tuning — ESP box thickness, aimbot smoothing, radar zoom — belongs to the feature
that owns it, bound to that feature's own GUI section (rule #11).

```cpp
// globals.em — cross-feature state ONLY
import "vec";

proc_t g_proc;
uint64 g_base = 0;            // uint64 always (rule #2)
uint64 g_size = 0;
uint64 g_entity_list = 0;     // resolved once, read by every feature
bool   g_initialized = false;

// One shared entity cache, filled by a single walk in a shared update routine.
array<uint64> g_entities;     // valid entity bases this tick
array<vec3>   g_positions;    // world positions, parallel to g_entities
```

```cpp
// esp.em — this feature's tuning is private to this file
import "vec";
import "color";
import "globals";

bool    g_esp_enabled  = true;   // ESP owns these, not globals.em
float64 g_esp_distance = 3000.0;
color   g_esp_color    = color(80, 170, 255, 220);

void esp_render(int64 data) {
    if (!g_esp_enabled || !g_initialized) return;
    color box = color(80, 170, 255, 220);   // construct per frame (rule #7)
    for (int32 i = 0; i < g_positions.length(); i++) {
        // draw from the shared cache — esp.em never walks the list itself
    }
}
```

**Anti-pattern: a feature writing into another feature's variables.** If `aim.em`
flips `g_esp_color` to flag its current target, you now have two files that can
change one variable and a hot-reload of either that desyncs the other.

```cpp
// WRONG — aim.em reaches into esp.em's state
g_esp_color = color(255, 0, 0, 255);   // "highlight the aim target"

// RIGHT — shared intent goes through globals.em, each feature reads it
// globals.em:  uint64 g_aim_target = 0;
// aim.em:      g_aim_target = best;          // aim owns the write
// esp.em:      if (g_entities[i] == g_aim_target) box = color(255,0,0,255);  // esp owns the read
```

The rule: **a global has exactly one writer.** Many readers are fine; two writers
is a bug waiting for a patch day.

---

## Offset modules: one per binary, not one per feature

**Sigs are grouped by the binary they scan, never by the feature that consumes
them.** Almost every project targets one module and `offsets.em` is enough. The
pattern only branches when you legitimately read two binaries — a game plus its
anti-cheat-adjacent helper DLL, or a launcher plus the game.

```
offsets-game.em      # sigs scanned in game.exe
offsets-engine.em    # sigs scanned in engine.dll
```

Each offset module owns its own base/size and resolves against it; a feature
imports whichever module holds the sig it needs.

```cpp
// offsets-game.em — sigs for game.exe (cite each, rule #1 / #5)
import "globals";

// CEntityList global — LEA RCX, [rip+????]   (sig from IDA, not a hardcode)
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";

bool resolve_game() {
    uint64 hit = g_proc.find_code_pattern(g_base, g_size, SIG_ENTITY_LIST);
    if (hit == 0) { println("[offsets-game] SIG_ENTITY_LIST stale"); return false; }
    int32 disp = g_proc.r32(hit + 3);                       // RIP-relative, 4 bytes
    g_entity_list = hit + 7 + cast<uint64>(disp);           // end-of-insn + disp
    return g_entity_list != 0;                              // validate (rule #3)
}
```

**The hard rule: a signature is defined exactly once.** The moment the same byte
pattern appears in two feature files, a patch breaks one copy and not the other,
and you debug a "half-working" cheat. If two features need `SIG_ENTITY_LIST`,
both import the offset module — they never re-declare the constant.

```
// WRONG: SIG_ENTITY_LIST pasted into both esp.em and radar.em
// RIGHT: declared in offsets-game.em; esp.em and radar.em both `import "offsets-game";`
```

---

## Config persistence pattern

**Serialize GUI state to a JSON file with the JSON addon, load it in `main()`
before building the menu, and save it on an explicit trigger.** There is no
unload callback to hook — see the lifecycle note below — so saving is something
*you* invoke, not something the host does for you.

Load first so widgets come up showing the saved values; the scaffold's
`setup_menu()` already calls `load_config()` at its top. Use the documented
filesystem API (`fs_read_file` / `fs_write_file` / `fs_file_exists`, all gated by
`file_system_access`) and the JSON addon (`json_parse`, `json_object`,
`.set_key` / `.get_key`, `.stringify()` / `.pretty()`).

```cpp
// menu.em — JSON config persistence
import "globals";

const string CFG_PATH = "configs/active.json";

void save_config() {
    json_value root = json_object();
    root.set_key("enabled",      json_parse(to_string(g_esp_enabled)));
    root.set_key("max_distance", json_parse(to_string(g_esp_distance)));
    root.set_key("hotkey",       json_parse(to_string(g_aim_hotkey)));

    if (!fs_dir_exists("configs")) fs_create_directory("configs");
    if (!fs_write_file(CFG_PATH, root.pretty()))     // pretty() so it's hand-editable
        println("[cfg] save failed — check file_system_access permission");
}

void load_config() {
    if (!fs_file_exists(CFG_PATH)) return;           // first run: keep defaults
    json_value root = json_parse(fs_read_file(CFG_PATH));
    if (!root.is_valid()) { println("[cfg] corrupt, using defaults"); return; }

    if (root.has_key("enabled"))      g_esp_enabled  = root.get_key("enabled").as_bool();
    if (root.has_key("max_distance")) g_esp_distance = root.get_key("max_distance").as_num();
    if (root.has_key("hotkey"))       g_aim_hotkey   = cast<int32>(root.get_key("hotkey").as_int());
}
```

`json_parse` returns an invalid value (not a throw) on malformed input, so the
`is_valid()` guard is the whole error path — a truncated or hand-broken config
falls back to defaults instead of taking the script down. `has_key` before
`get_key` means a config written by an older build (missing a field you added
later) loads cleanly: unknown-to-old and missing-from-new both degrade to the
default. That forward/backward tolerance is the reason to prefer JSON objects over
the positional `key=value` text format the scaffold ships with.

**Lifecycle reality — there is no `on_unload` hook.** Per
`docs/perception/lifecycle-and-routines.md`, a script unloads when `main()`
returns `<= 0`, when the user unloads it, or when the host shuts down; routines
simply stop and render resources are freed automatically. Nothing runs *your*
code on the way out. So persistence is triggered one of three ways:

- **Save button** — `section_button(sec, "Save Config", cast<int64>(save_config))`.
  Explicit, zero overhead, what the scaffold uses.
- **Save hotkey** — check `is_key_pressed(g_save_key)` in a routine, call
  `save_config()` on the edge. Convenient mid-game.
- **Autosave on change** — diff GUI state in the update routine and save when it
  moves. Simplest to reason about, but it writes to disk during gameplay; gate it
  behind a debounce so a slider drag isn't a hundred file writes.

```cpp
// defer: explicit Save button only. Autosave-on-change when users complain
//        about losing edits; debounce it so a slider drag isn't N disk writes.
```

---

## Multi-script coordination

Sometimes you want two scripts loaded in the same PCX session — a stable "base"
script you trust, plus a "wip" experimental overlay you reload constantly without
risking the base. The question is whether they can share state, and the honest
answer is *mostly no, and that's usually fine*.

The scripting layer exposes **no IPC primitive** — no named pipes, no shared
memory between scripts. Do not invent one. The filesystem is **sandboxed to a
per-script data root** (`docs/perception/filesystem-api.md`), so a file written
by script A is not guaranteed visible to script B; treat cross-script file
sharing as unsupported unless you have verified on your install that both scripts
resolve to the same root. That leaves three real options:

| Approach | How | When it's worth it |
| --- | --- | --- |
| **Don't share** (default) | Each script attaches its own `proc_t`, resolves its own offsets, walks its own list | Almost always. Duplicate reads are cheap next to the simplicity |
| **Shared file** | One script writes `state/shared.json`, the other polls it | Only if both resolve to the same sandbox root *and* the data is slow-changing (resolved offsets, target id) |
| **Single script, two modules** | Collapse both into one script; the "experimental" part is just another feature file you hot-reload | When you actually need shared live state — this is the supported way to get it |

**The tradeoff is duplicate reads vs. coupling.** Two independent scripts each
walking the entity list costs you two walks per tick — measurable only if the
list is huge. Sharing state via a file couples their reload cycles and adds a
parse on every poll. The "single script, two feature modules" path gives you true
shared state for free (it's just `globals.em` again) at the cost of the isolation
you wanted in the first place. Pick duplication unless a profiler says otherwise.

```cpp
// defer: two independent scripts, duplicate entity walks accepted.
//        Merge into one script with shared globals.em if the double walk
//        shows up in the frame budget.
```

---

## Utility modules: when extraction pays off

**`world_to_screen` lives in exactly one place. So does the pattern-scan
resolver. So does the bone-matrix unpacker.** A second copy of W2S is a second
place to get the behind-camera check wrong (rule #10).

The extraction heuristic is a counting rule, straight from
`pcx-coding-discipline` #5 (*deletion before addition*):

- **3+ features need it → utility module.** Extract to `util-math.em` (or
  `util-mem.em`) and import it everywhere. The shared definition is now the only
  one to fix after a patch.
- **Exactly 2 features need it → leave it duplicated.** Two copies you can see is
  cheaper to reason about than one indirection you have to chase, and the second
  caller is not yet proof the abstraction is right.
- **1 feature needs it → inline it.** A wrapper with one caller adds a name, not
  value. Inline the body.

```cpp
// util-math.em — shared because esp, radar, AND aim all project to screen (3 callers)
import "vec";
import "globals";

bool world_to_screen(vec3 world, out vec2 screen) {
    uint64 m = g_view_matrix;                       // resolved in globals/offsets
    float64 w = g_proc.rf32(m + 12) * world.x
              + g_proc.rf32(m + 28) * world.y
              + g_proc.rf32(m + 44) * world.z
              + g_proc.rf32(m + 60);
    if (w < 0.001) return false;                    // behind camera (rule #10)
    float64 inv = 1.0 / w;
    float64 nx = (g_proc.rf32(m + 0)  * world.x + g_proc.rf32(m + 16) * world.y
                + g_proc.rf32(m + 32) * world.z + g_proc.rf32(m + 48)) * inv;
    float64 ny = (g_proc.rf32(m + 4)  * world.x + g_proc.rf32(m + 20) * world.y
                + g_proc.rf32(m + 36) * world.z + g_proc.rf32(m + 52)) * inv;
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

```cpp
// WRONG — esp.em and radar.em each carry their own W2S; one gets the w-check
//         fixed after a patch, the other still mirrors points behind the camera.
// RIGHT — both `import "util-math";` and call world_to_screen(); one definition.
```

Resist extracting too early. A `util-mem.em` that wraps `g_proc.ru64` in
`read_ptr()` is the one-caller mistake even when three features call it — the
`proc_t` API *is* the interface (rule from `pcx-coding-discipline` #5). Extract
behavior with real logic (W2S, the RIP resolver, bone unpacking), not one-line
passthroughs.

---

## Feature toggles in `main()` vs the feature module

**Two different switches, two different homes.** Conflating them is why a feature
"won't turn off" or "won't turn on."

- **Load switch — does the feature exist at all this session?** Lives in
  `main()`, as whether you call `register_routine` for it. An unregistered
  feature costs zero per frame; its file can even be absent from the bundle.
- **Runtime switch — is the loaded feature drawing right now?** Lives in the
  feature's own GUI checkbox, read at the top of its routine.

```cpp
// main.em — LOAD switch: register or don't. Comment out the line to drop a feature.
int64 main() {
    // ... attach, resolve ...
    setup_menu();
    register_routine(cast<int64>(esp_update),   0);
    register_routine(cast<int64>(esp_render),   0);
    register_routine(cast<int64>(radar_render), 0);
    // register_routine(cast<int64>(aim_update), 0);   // aim left out this build
    g_initialized = true;
    return 1;
}
```

```cpp
// esp.em — RUNTIME switch: the registered routine early-outs when the box is off.
void esp_render(int64 data) {
    if (!g_esp_enabled || !g_initialized) return;     // GUI checkbox (rule #11)
    // ... draw ...
}
```

**Why both:** the load switch is your kill switch — a feature you suspect is
crashing or detectable, you drop by deleting one `register_routine` line and
reloading, with no per-frame cost and no risk it runs. The runtime switch is the
user-facing toggle for a feature you trust enough to ship. A feature with only a
runtime toggle still executes its early-out every frame even when "off"; a
feature with only a load switch can't be turned off without a reload. You want
both levers.

---

## Module-version pinning

**A feature that depends on a specific shape of `globals.em` says so at the top of
its file.** When you change a shared structure, this comment is the list of files
to revisit — Enma won't warn you that `feature.em` expected the old layout, it
will just read the wrong field.

The pattern is a `// requires:` line naming the shared contract the feature was
written against:

```cpp
// radar.em
// requires: globals v2  (g_entities as flat array<uint64>, g_positions parallel)
import "globals";

void radar_render(int64 data) {
    for (int32 i = 0; i < g_positions.length(); i++) {
        // assumes g_positions[i] pairs with g_entities[i] — the v2 contract
    }
}
```

When you bump `globals.em` — say you replace the two parallel arrays with a single
`array<entity_t>` — grep for `requires: globals v2` and every file that needs
updating is named for you. Bump the version in `globals.em`'s header comment and
update each `requires:` as you migrate it:

```cpp
// globals.em
// version: v3  (g_entities is now array<entity_t>; v2 parallel arrays removed)
```

This is documentation, not a runtime check — there is no module-version assert in
the language. Its whole value is that the next reader (often you, post-patch) sees
the dependency without reverse-engineering it. Keep the line honest or delete it;
a stale `requires:` is worse than none.

---

## Dead-code elimination

**A feature you stopped using: drop it from the bundle order, comment out its
`register_routine`, rename the file so it's visibly inactive — but keep it in the
tree.** Don't `git rm` it.

The reasoning is specific to this domain. A feature file is a worked record of a
sig, a struct layout, and the math that turned them into an overlay — knowledge
that took an IDA session to produce. After a patch the *code* is stale but the
*structure* is still the fastest way back: you re-sig, re-verify the offsets, and
the feature is alive again. Git-deleting it buries that record in history where
future-you won't think to look.

The compromise that keeps it from rotting silently: **rename to
`feature-dead-<name>.em`** so it's unmistakably inactive at a glance, and remove
its routine registration so nothing runs it.

```cpp
// main.em
import "esp";
import "radar";
// import "feature-dead-aim";   // parked: offsets stale since the season patch

int64 main() {
    register_routine(cast<int64>(esp_render),   0);
    register_routine(cast<int64>(radar_render), 0);
    // register_routine(cast<int64>(aim_update), 0);   // dead: see feature-dead-aim.em
    return 1;
}
```

```
project/
├── esp.em
├── radar.em
└── feature-dead-aim.em    # inactive, kept as a re-sig starting point
```

The `dead-` prefix is the signal to every tool and reader that this file is not
in the build. When you revive it, rename back to `aim.em`, re-verify the sigs
against the live binary (`game-cheat-guidelines` #12), and re-add the
registration.

---

## The shape of a 20-feature project

A project with many features, two target binaries, and shared utilities still
keeps the one-way dependency arrow from the scaffold — it just has more files at
each layer. Features depend on utils and offsets; utils and offsets depend on
globals; nothing depends on a sibling feature.

```
project/
├── globals.em             # version: v3 — proc_t, bases, shared entity cache
│
├── offsets-game.em        # sigs scanned in game.exe
├── offsets-engine.em      # sigs scanned in engine.dll
│
├── util-math.em           # world_to_screen, angle math   (3+ callers)
├── util-mem.em            # RIP resolver, bone-matrix unpack (3+ callers)
│
├── esp.em                 # requires: globals v3
├── radar.em               # requires: globals v3
├── glow.em                # requires: globals v3
├── aim.em                 # requires: globals v3, offsets-game
├── triggerbot.em          # requires: globals v3, offsets-game
├── nospread.em            # requires: globals v3, offsets-engine
├── loot-esp.em            # requires: globals v3, offsets-game
├── spectator-list.em      # requires: globals v3, offsets-engine
├── ...                    # (more features, each one file)
├── feature-dead-bhop.em   # parked: re-sig after patch
│
├── menu.em                # GUI sections + JSON config persistence
└── main.em                # attach, resolve_game/resolve_engine, register all
```

Dependency direction, top to bottom:

```
  main.em  ──registers──>  every feature
     │
  menu.em  ──reads/writes──>  each feature's config + globals
     │
  esp / radar / aim / ...  ──import──>  util-math, util-mem, offsets-*
     │
  util-*, offsets-*  ──import──>  globals.em
     │
  globals.em  ──imports──>  vec, color   (engine modules only)
```

`main()` grows linearly: resolve each binary, then one `register_routine` per
active feature. `menu.em` grows one `create_section` per feature. Everything else
stays a single file you can reload in isolation — which is the entire point of the
split, and the reason a 20-feature project is still tractable when a single
2000-line `cheat.em` would not be.

---

## Anti-Patterns

A flat list of organizational mistakes and the consequence each one buys you:

- **Monolithic `cheat.em`** — every feature in one file; a hot-reload to fix one
  box re-runs and can break all twenty. Split per feature (#6).
- **Duplicate sig definitions** — the same byte pattern declared in two feature
  files; a patch breaks one copy, you ship a half-working cheat. One sig, one
  module.
- **Features mutating each other's state** — two writers on one global; reload
  either and they desync. One writer per global, many readers.
- **`feature_a.em` importing `feature_b.em`** — sideways dependency; now neither
  reloads cleanly. Shared things go down into `globals.em` or a util module.
- **GUI widgets created in an update/render loop** — `create_section` /
  `section_checkbox` belong in `setup_menu()` run once, not per frame. Per-frame
  widget creation duplicates state and tanks the frame budget (#11).
- **Reading widget state deep inside nested loops** — read the toggle once at the
  top of the routine, then branch; don't re-read per entity.
- **Per-binary offset files split by feature instead** — `esp-offsets.em` +
  `radar-offsets.em` for the same game.exe re-declares shared sigs. Group offsets
  by binary, not by consumer.
- **Caching colors/vecs in globals "to avoid allocation"** — they're stack value
  types; the global only adds mutable state. Construct per frame (#7).
- **One-caller utility wrappers** — `read_ptr()` around a single `g_proc.ru64`
  adds a name, not value. Inline until 3 callers earn the extraction.
- **Config saved on a nonexistent unload hook** — there is no `on_unload`; the
  save never fires. Trigger saves from a button, hotkey, or debounced autosave.
- **Git-deleting a patched-out feature** — buries the sig/struct knowledge in
  history. Rename to `feature-dead-<name>.em` and keep it.
- **Stale `requires:` comments** — a version pin that no longer matches
  `globals.em` misleads the next reader. Keep it honest or remove it.

---

## See Also

- `templates/full-project/` — the five-file scaffold this document extends;
  start there, grow into these patterns.
- `.claude/skills/game-cheat-guidelines/SKILL.md` — the code-shape rules every
  block here honors, especially #1 (ground offsets), #6 (one feature per file),
  and #11 (GUI for tunables).
- `.claude/skills/pcx-coding-discipline/SKILL.md` — the process layer: #5
  (deletion before addition) is the source of the utility-extraction counting
  rule.
- `knowledge/common-patterns.md` — the per-feature building blocks (W2S, entity
  iteration, config) these layouts arrange.
- `docs/enma/lang-modules.md` — the `import` / module-resolution mechanics behind
  the dependency arrow.
- `docs/enma/addon-json.md` and `docs/perception/filesystem-api.md` — the real
  JSON and sandboxed-filesystem APIs used by the config-persistence pattern.
- `docs/perception/lifecycle-and-routines.md` — why there is no unload hook and
  how `register_routine` makes the load switch.
