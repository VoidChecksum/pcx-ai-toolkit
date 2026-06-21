# GUI Design Patterns

The Perception.cx sidebar GUI is a fixed-width vertical strip. Good layouts make features discoverable, tunings easy to find, and state visible at a glance. The 12 game-cheat-guidelines say "GUI for every tunable" (rule #11), but say nothing about how to lay it out well. This file fills that gap with section-organization patterns, widget order, label conventions, slider range discipline, hotkey conventions, color discipline, conditional widgets, state visibility, and the anti-patterns to avoid.

> **Read this before** designing a new feature's GUI section, or auditing an existing one. Pair with `templates/overlay-basic.em` (small example) and `templates/full-project/` (multi-feature example) for working code.

---

## Section Organization: One Feature Per Section

**Mirrors `game-cheat-guidelines` rule #6 (one feature per file). The GUI shape follows the code shape.**

The sidebar is composed of independent sections — `create_section("ESP")`, `create_section("Aimbot")`, `create_section("Radar")`. Each section is collapsible by the user. Users disable a feature *socially* by collapsing its section ("I'm not using radar today; collapse it"); mixing concerns inside one section defeats the affordance.

```cpp
// RIGHT — one feature per section
int64 sec_esp    = create_section("ESP");
int64 sec_aim    = create_section("Aimbot");
int64 sec_radar  = create_section("Radar");
int64 sec_misc   = create_section("Misc");

// WRONG — all features in one section
int64 sec_all = create_section("Features");  // user has to scroll past 40 widgets
```

The exception: tiny features (a single checkbox) that don't justify their own section header. Group them under a `Misc` section at the bottom. The rule is one *feature* per section, not one widget — a section with 6-10 widgets is normal.

**Why:** Collapsibility is the discoverability mechanism. Mixing makes the sidebar a wall of widgets that the user scans linearly; separating makes it a directory the user can collapse-and-skip.

---

## Widget Order Within a Section

**Canonical order: master toggle → hotkey → primary tuning → secondary tunings → color picker(s) → separator → status label.**

Users scan top-to-bottom. The widget order reflects the frequency of interaction: the master toggle is touched most often (turn the feature on/off), the status label is glanced at most often (is it working?). Put both where the eye naturally lands.

```cpp
int64 sec = create_section("ESP");

// 1. Master toggle — top of section, always.
section_checkbox(sec, "Enabled", g_esp_enabled);

// 2. Hotkey — the second-most-touched widget after the toggle.
section_keybind(sec, "Toggle hotkey", g_esp_hotkey);

// 3. Primary tuning — the most-used slider or combo.
section_combo(sec, "Mode", g_esp_mode, "Box,Skeleton,Both");

// 4. Secondary tunings — less-frequent.
section_slider_float(sec, "Max distance", g_esp_max_dist, 0.0, 500.0);
section_slider_int(sec, "Line thickness", g_esp_thickness, 1, 5);
section_checkbox(sec, "Show distance label", g_esp_show_dist);

// 5. Color pickers — group at the end so the color noise doesn't dominate.
section_color_picker(sec, "Friendly", g_esp_color_friendly);
section_color_picker(sec, "Enemy",    g_esp_color_enemy);

// 6. Separator — visually break "controls" from "diagnostics".
section_separator(sec);

// 7. Status label — what is the feature doing right now?
section_label(sec, "Drawing 12 entities (3 friendly, 9 enemy)");
```

(The status label text is updated each frame from the render routine — the API takes a `string`, so build it with `format(...)` against your cached counts.)

The order isn't sacred (a feature with no hotkey skips that slot), but the *gravity* is: most-touched at the top, diagnostics at the bottom.

**Why:** A GUI that lets the user find the toggle in 200ms is one they actually use. A GUI where the user has to scroll past four color pickers to find the toggle is one they fight with.

---

## Label Conventions

**Imperative for toggles, units in slider labels, no jargon.**

```cpp
// RIGHT — clear, scannable, action-oriented
section_checkbox(sec, "Show ESP", g_esp_enabled);
section_slider_float(sec, "Smoothing (frames)", g_aim_smoothing, 0.0, 15.0);
section_slider_int(sec, "Max distance (meters)", g_esp_max_dist, 0, 500);
section_combo(sec, "Target priority", g_target_mode, "Closest,Lowest HP,Crosshair");

// WRONG — past-tense, abbreviated, unit-less
section_checkbox(sec, "ESP enabled", g_esp_enabled);          // past-tense state
section_slider_float(sec, "SM", g_aim_smoothing, 0, 15);      // what is SM?
section_slider_int(sec, "Dist", g_esp_max_dist, 0, 500);      // dist in what?
section_combo(sec, "Pri", g_target_mode, "C,L,X");            // unreadable
```

Imperative phrasing reads as a button label: "Show ESP" / "Hide ESP" maps directly to the checkbox state. "ESP enabled" makes the user parse a sentence to know what clicking it does.

Units in slider labels save support questions. "Smoothing" is ambiguous (frames? seconds? ticks?). "Smoothing (frames)" is not.

Abbreviations are fine when they're industry-standard (FOV, ESP, HP, AC); not fine when they're project-internal (AB for aimbot, SM for smoothing). The rule of thumb: would a Discord support request use this abbreviation? If yes, ship it. If you'd have to expand it on first use in a support reply, expand it in the label.

**Why:** A label is the entire UX of a widget. A clear label is self-documenting; an unclear one needs a doc the user won't read.

---

## Slider Ranges: Useful, Not Possible

**Set min/max to the *useful* range, not the *possible* range. A smoothing slider's useful range is 0..15; setting it 0..1000 makes the useful range one pixel wide.**

The slider widget maps the entire visible track to the `[min, max]` interval. If the useful range is 0..15 and the slider is 0..1000, the user can only meaningfully tune in the first 1.5% of the track, and dragging past that produces values that don't change behavior (or, worse, crash).

```cpp
// WRONG — possible range, useless slider
section_slider_float(sec, "Smoothing", g_aim_smoothing, 0.0, 1000.0);
section_slider_int(sec, "FOV (px)", g_aim_fov, 0, 10000);
section_slider_float(sec, "Max distance (m)", g_max_dist, 0.0, 100000.0);

// RIGHT — useful range, every drag matters
section_slider_float(sec, "Smoothing", g_aim_smoothing, 0.0, 15.0);
section_slider_int(sec, "FOV (px)", g_aim_fov, 8, 400);
section_slider_float(sec, "Max distance (m)", g_max_dist, 0.0, 500.0);
```

How to pick useful ranges:

- Measure or estimate the *real* range your feature operates in (smoothing past 15 frames is sluggish; aimbot FOV past 400px is "aim at the whole screen").
- Add 20-50% headroom past the practical upper bound (the user might want to go higher than you expect).
- Set the minimum to the smallest sensible value (0 if the feature can be disabled by the slider; 1 if it needs at least some value to function).

When the truly useful range is dynamic (depends on game state — e.g. max-distance varies between a small arena and a large open world), pick a static range that covers the wider case and document it in a comment.

**Why:** A slider's value is the area where it's draggable. A 0..1000 slider for a 0..15 problem is a configuration error, not a feature.

---

## Defaults That Work for First-Time Users

**Ship the tuning a new user would want, not the tuning you've personally settled on.**

The first time a user loads the script, every widget has its default value. If the defaults are bad, the script appears broken and the user gives up before reaching the GUI to fix them.

| Widget | Bad default | Good default |
|---|---|---|
| `g_esp_enabled` | `false` (user has to find the toggle) | `true` (user sees the feature immediately) |
| `g_esp_color` | `color(0, 0, 0, 255)` (invisible on dark UI) | `color(255, 50, 50, 255)` (red, contrasts with most game UIs) |
| `g_aim_smoothing` | `0.0` (instant snap — detection vector + jarring) | `8.0` (perceptibly smooth, still useful) |
| `g_aim_hotkey` | (no default) | Right-mouse-button (industry convention for "aim assist") |
| `g_aim_fov` | `1000.0` (whole screen) | `60.0` (focused, sane starting point) |
| `g_esp_max_distance` | `0.0` (draws nothing) | `200.0` (covers most engagements) |
| `g_radar_radius` | `40.0` (too small to read) | `90.0` (readable on 1080p+ displays) |

The pre-ship hygiene check (`tools/pre-ship-check.sh`) does NOT catch bad defaults — they look like normal values to grep. Reviewers must consciously test the fresh-config experience: delete your saved config, restart the script, verify it does something visible without any user tuning.

**Why:** Defaults are the product. A user who has to tune 20 widgets before the feature works will conclude the feature doesn't work. The two minutes you spend picking defaults that work for a first-time user pay back in every install.

---

## Hotkey Conventions

**Don't bind features to letter keys the game uses (WASD, R, E, F, Q). Provide a `section_keybind` widget for every hotkey — hardcoded hotkeys are rule-#11 violations.**

Safe default hotkeys, ordered by convention:

| Action | Conventional default |
|---|---|
| Toggle aim assist (hold) | Right Mouse Button (`VK_RBUTTON`) — industry standard |
| Toggle aim assist (toggle) | `F1` or `Mouse5` (`XBUTTON2`) |
| Open / close menu | `Insert` (PCX default) or `End` |
| Toggle ESP | `F2` |
| Toggle radar | `F3` |
| Misc feature toggles | `F4` – `F11` |
| Panic / hide all overlays | `End` or `\` |
| Reload sigs | `Home` (rare, RE-only utility) |
| Snapshot for debugging | `Pause` |

What to NEVER use:
- `WASD` — movement keys
- `Q`, `E`, `R`, `F` — typical ability / interact keys
- `Space`, `Shift`, `Ctrl`, `Alt` — modifier keys the game routes
- `1`–`0` — weapon swap / hotbar
- `Escape` — game-menu trigger
- `~` — chat or console
- Mouse4 / Mouse5 — generally OK, but check; some games bind these

Every hotkey is exposed as a `section_keybind` widget so the user can rebind:

```cpp
// RIGHT — hotkey is configurable
int64 g_esp_hotkey = vk::f2;
section_keybind(sec, "ESP toggle", g_esp_hotkey);

void on_update(int64 data) {
    if (key_fired(g_esp_hotkey)) {
        g_esp_enabled = !g_esp_enabled;
    }
}

// WRONG — hardcoded hotkey, user can't rebind
void on_update(int64 data) {
    if (key_fired(vk::f2)) {
        g_esp_enabled = !g_esp_enabled;
    }
}
```

`key_fired` is edge-triggered (true once per press); `key_down` is level-triggered (true while held). Toggles use fired; hold-to-activate uses down.
**Why:** Hotkey conflicts kill scripts. The user reports "the script doesn't work" — actually the script's `F` hotkey collides with the game's interact key, and pressing it both triggers the script and opens a door. Configurable hotkeys eliminate the entire class of report.

---

## Color Discipline

**Every drawable color is GUI-tunable (per rule #11). The discipline: a small palette per feature (FG / BG / accent) rather than per-pixel colors.**

A feature with 12 distinct hardcoded colors is one the user can't recolor for high-contrast, colorblind-friendly, or stream-friendly use. A feature with 3-4 tunable palette slots is one the user can adapt.

```cpp
// RIGHT — small palette, all tunable
color g_esp_friendly = color(60, 170, 255, 255);
color g_esp_enemy    = color(255, 60, 60, 255);
color g_esp_text     = color(255, 255, 255, 255);
color g_esp_outline  = color(0, 0, 0, 180);

int64 sec = create_section("ESP");
section_color_picker(sec, "Friendly",  g_esp_friendly);
section_color_picker(sec, "Enemy",     g_esp_enemy);
section_color_picker(sec, "Text",      g_esp_text);
section_color_picker(sec, "Outline",   g_esp_outline);

// In render — pull from the palette, never construct ad-hoc colors:
void on_render(int64 data) {
    for (int32 i = 0; i < g_count; i++) {
        color box = g_cache[i].friendly ? g_esp_friendly : g_esp_enemy;
        draw_rect(g_cache[i].screen_pos, g_cache[i].screen_size,
                  box, 1.5, 0.0, 15);
    }
}

// WRONG — hardcoded per-call colors
void on_render(int64 data) {
    for (int32 i = 0; i < g_count; i++) {
        draw_rect(g_cache[i].screen_pos, g_cache[i].screen_size,
                  color(255, 0, 0, 255),   // hardcoded red
                  1.5, 0.0, 15);
    }
}
```

Community conventions for color roles:

| Role | Conventional color |
|---|---|
| Friendly / teammate | Blue (`60, 170, 255`) or Green (`60, 220, 100`) |
| Enemy | Red (`255, 60, 60`) or Yellow (`255, 200, 50`) |
| Neutral / NPC / object | Gray (`180, 180, 180`) |
| Important / priority target | Magenta (`255, 60, 255`) or Bright Orange (`255, 140, 0`) |
| Hostile NPC (distinct from enemy player) | Dark red (`140, 30, 30`) or Crimson |
| Loot / pickup | Yellow (`255, 220, 80`) or Gold |

These are conventions, not laws — users will adjust. The point is to ship defaults that match what most users expect from prior cheats / games, so the first impression makes visual sense.

**Why:** Colors are accessibility. ~8% of male users have some form of red-green color blindness; ship colors they can tell apart, and let users override them if your defaults don't work for them.

---

## State Visibility

**A small label at the bottom of each section showing the runtime state. When users report "the script isn't working," the first thing they read is the state label.**

The state label closes the support loop before it opens. Without it, a user with a broken script reaches for Discord; with it, the user reads "0 entities (sig scan failed)" and knows the problem is the sig, not the feature.

```cpp
// In render — build status from cached state, update each frame
void on_render(int64 data) {
    // ... drawing ...

    // Status label — built from cached state
    string status;
    if (!g_proc.alive()) {
        status = "process not attached";
    } else if (g_entity_list == 0) {
        status = "sig scan failed (entity_list)";
    } else if (g_ent_count == 0) {
        status = "0 entities (in menu?)";
    } else {
        status = format("{d} entities ({d} friendly, {d} enemy)",
                        g_ent_count, g_ent_friendly_count, g_ent_enemy_count);
    }
    section_label(sec, status);
}
```

The status should:
- Always be visible (don't gate on `g_enabled` — the user wants status even when the feature is off)
- Use plain English (no internal error codes)
- Differentiate the common failure modes from "working fine"
- Include a count or sample value when the feature is working (proves it)

For features that have multiple status dimensions (aimbot: "no target / target locked: enemy_42 / smoothing: 8 frames"), one label is enough — `format` them together.

**Why:** The status label is the support burden's lightning rod. A user who can read the status doesn't ask in Discord; a user who can't, does.

---

## Conditional Widgets

**If widget B only makes sense when widget A is enabled, hide or gray out B when A is off.**

PCX's GUI API may or may not expose disable-state styling natively — check `docs/perception/gui-api.md` for the available widget states. If a disable-state is available, use it; if not, fall back to *conditionally creating* the dependent widgets, or document the dependency with a comment.

```cpp
// PATTERN 1 — if PCX supports a `section_*_disabled` variant or visibility flag,
// use it (check docs):
section_checkbox(sec, "Aim assist",  g_aim_enabled);
// Hypothetical: section_set_enabled(g_aim_smoothing_widget, g_aim_enabled);

// PATTERN 2 — fall-back: only create the dependent widget when the
// parent is enabled, on a per-frame basis. PCX GUI API permitting,
// recreate-per-frame is fine; if not, fall back to PATTERN 3.

// PATTERN 3 — universal fall-back: keep the widgets always created,
// but make the dependency explicit in the label and ignore the value
// at runtime when the parent is off:
section_checkbox(sec, "Aim assist", g_aim_enabled);
section_slider_float(sec, "Smoothing (needs Aim assist)",
                     g_aim_smoothing, 0.0, 15.0);
// In on_update: read g_aim_smoothing only inside `if (g_aim_enabled)`.
```

The labeled-dependency pattern (#3) is uglier than gray-out but always works. Use the prettier patterns when PCX exposes them; document with a `// requires: g_aim_enabled` comment either way.

**Why:** A user enabling smoothing without realizing aim assist is off, then concluding "the script is broken," is the exact kind of confused-customer report a 12-character label change prevents.

---

## Don't Ship a Debug Panel by Default

**A separate "Debug" section with profiler readouts and address dumps is great for development; hide or remove for release. The pre-ship checklist catches this.**

```cpp
// During development
int64 sec_debug = create_section("Debug");
section_label(sec_debug, format("entity_list: 0x{x}", g_entity_list));
section_label(sec_debug, format("local_player: 0x{x}", g_local_player));
section_label(sec_debug, format("entity count: {d}", g_ent_count));
section_label(sec_debug, format("update_us: {d}", g_avg_update_us));
section_label(sec_debug, format("render_us: {d}", g_avg_render_us));

// Before shipping — either remove the section entirely, or gate it
// behind a build flag / runtime "Show debug" checkbox in Misc.
#if DEBUG
    int64 sec_debug = create_section("Debug");
    // ... debug widgets ...
#endif
```

(PCX's preprocessor supports `#if`/`#ifdef`; see `docs/enma/lang-pre-processor.md`.)

The recipient of a shipped script does not need to see your internal address layout, your profiler bucket timings, or your sig-resolution status. Worse, debug info exposes the script's internals to anyone watching over the recipient's shoulder, which is bad for both privacy and competitive dynamics.

When shipping with a "Show debug" toggle (the gentler approach), default it off, and document in the README that flipping it on reveals diagnostic info useful only for support tickets.

**Why:** Debug surfaces are for the author, not the user. Shipping them on by default is leaking implementation; shipping them gated off (with documentation) is offering a support feature without imposing it.

---

## Persistence (Cross-Reference)

The GUI state must be persisted across script reloads — the user doesn't want to retune sliders every time. See `knowledge/script-organization-patterns.md` section "Config persistence pattern" for the JSON-to-disk pattern, and `.claude/skills/script-bundler/SKILL.md` for when to save (on each widget change, on a debounced timer, or on a save hotkey).

The relevant `fs_*` and `json_*` APIs are in `docs/perception/file-api.md` and `docs/enma/addon-json.md`. The summary: read on `main()` startup, write on a save hotkey or a debounced timer.

---

## Worked Example: A Well-Laid-Out ESP Section

```cpp
import "vec";
import "color";

// ── Config (GUI-bound; persisted to disk by main()) ──
bool   g_esp_enabled       = true;            // default ON (rule: defaults that work)
int32  g_esp_hotkey        = 0x71;            // VK_F2 toggle
int32  g_esp_mode          = 0;               // 0=box, 1=skeleton, 2=both
float64 g_esp_max_dist     = 200.0;
int32  g_esp_thickness     = 2;
bool   g_esp_show_distance = true;
color  g_esp_color_friendly = color(60, 170, 255, 255);   // blue convention
color  g_esp_color_enemy    = color(255, 60, 60, 255);    // red convention
color  g_esp_color_outline  = color(0, 0, 0, 180);

// ── Runtime state (status label reads these) ──
int32 g_esp_count_drawn    = 0;
int32 g_esp_count_friendly = 0;
int32 g_esp_count_enemy    = 0;
string g_esp_status_text   = "initializing";

int64 setup_esp_gui() {
    int64 sec = create_section("ESP");

    // 1. Master toggle (top)
    section_checkbox(sec, "Show ESP", g_esp_enabled);
    // 2. Hotkey
    section_keybind(sec, "Toggle hotkey", g_esp_hotkey);
    // 3. Primary tuning
    section_combo(sec, "Mode", g_esp_mode, "Box,Skeleton,Both");
    // 4. Secondary tunings (useful ranges, not possible ranges)
    section_slider_float(sec, "Max distance (m)", g_esp_max_dist, 0.0, 500.0);
    section_slider_int(sec, "Line thickness (px)", g_esp_thickness, 1, 5);
    section_checkbox(sec, "Show distance label", g_esp_show_distance);
    // 5. Color pickers (palette, not per-pixel)
    section_color_picker(sec, "Friendly", g_esp_color_friendly);
    section_color_picker(sec, "Enemy",    g_esp_color_enemy);
    section_color_picker(sec, "Outline",  g_esp_color_outline);
    // 6. Separator
    section_separator(sec);
    // 7. Status label (always-visible feedback)
    section_label(sec, g_esp_status_text);

    return sec;
}
```

This is 12 widgets in 7 logical roles. A user scanning this section knows in seconds: "ESP is on (toggle), F2 toggles it (keybind), it's drawing boxes (mode), out to 200m (distance), in blue/red (palette), and right now is drawing 12 entities (status)."

---

## Anti-Patterns

Flat list — each is a real failure mode that ships in scripts and gets reported:

- **All features in one section.** Sidebar becomes a wall of widgets; users can't collapse-and-skip.
- **Hotkeys hardcoded.** User can't rebind, hotkey collides with a game key, support ticket follows.
- **Slider ranges 0..1000 for 0..15 problems.** Slider is unusable for the actual range.
- **No master toggle.** User can't disable the feature without quitting the script.
- **`color()` / `vec2()` globals at file scope.** Per-frame construction rule (#7) violated; harder to recolor.
- **Labels "foo" / "bar" / "new feature".** Self-evident at write time, opaque a week later.
- **Defaults of 0 / false on user-facing toggles.** Script appears broken on fresh install.
- **No status label.** Every support ticket reads "the script isn't working" with no diagnostic info.
- **Debug section always visible in release.** Leaks internals; clutters the UX.
- **All widgets enabled regardless of dependencies.** User enables smoothing without aim assist on, concludes script is broken.
- **No section separators.** Every section looks the same; visual fatigue.
- **Tooltips encoded into labels.** "Smoothing (higher = smoother, lower = snappier, default 8)" doesn't fit; use a separator + label below instead, or a dedicated `Help` section.

---

## Cross-References

- `docs/perception/gui-api.md` — the authoritative widget API for your PCX version
- `templates/overlay-basic.em` — a working small-overlay GUI
- `templates/full-project/` — the multi-feature project scaffold
- `knowledge/common-patterns.md` — Enma code patterns that consume the widget values
- `knowledge/script-organization-patterns.md` — the persistence pattern, the menu-vs-feature split
- `.claude/skills/game-cheat-guidelines/SKILL.md` rules #6 (one feature per file) and #11 (GUI for every tunable)
- `.claude/skills/script-bundler/SKILL.md` — the pre-ship hygiene checklist that includes "sensible GUI defaults"
- `.claude/skills/ai-pair-programming/SKILL.md` — technique #6 for diff-reviewing AI-generated GUI code
