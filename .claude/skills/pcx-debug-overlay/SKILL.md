# Debug Overlay — Diagnostic Surfaces Separate from the Production Overlay

The pattern for shipping diagnostic / profiler / address-dump information as a separate, gated overlay rather than mixed into the production rendering. Companion to `pcx-perf-budget` (which gives the timing primitives) and `gui-design-patterns` (which says "no debug section by default"). This skill names the structure that lets you ship a script that's diagnosable when you need it and clean when you don't.

**Trigger when:** the user is debugging a script that "isn't working," wants to ship a script with a built-in support-mode panel, profiling a feature to find a slow path, building a diagnostic build vs a release build of the same code, debugging "the AI says it resolved the sig but the script does nothing."

**Prerequisite:** `skill://pcx-perf-budget` for the `mono_us()`-based profiler recipe this skill consumes; `knowledge/gui-design-patterns.md` section "Don't ship a debug panel by default" for the layout discipline this skill extends.

---

## Trigger

Debugging a non-working script, building a support-mode panel for end users, profiling a script's per-routine costs, tracing why an offset resolution succeeded but a read returns 0, designing a script that needs to be diagnosable in the field without the user having to grep logs.

---

## 1. Two Overlays: Production and Diagnostic — Always Separate

**Production overlay shows what the user wants to see (ESP boxes, HUD, target indicators). Diagnostic overlay shows what the script knows about itself (sigs resolved, addresses, profiler timings, error counts). Never mix.**

When you mix them, the user permanently sees diagnostic noise during normal play, and you can't ship a diagnostic-rich build to a tester without also shipping the noise to everyone else. The separation is the only way to have both.

```cpp
// WRONG — diagnostic info in the production render path
void on_render(int64 data) {
    // ... ESP drawing ...

    // Inline diagnostic — every user sees this, every match
    draw_text(format("entity_list=0x{x} count={d}", g_entity_list, g_ent_count),
              vec2(10.0, 10.0), color(255, 255, 0, 255),
              get_font20(), 1, color(0, 0, 0, 200), 1.0);
}

// RIGHT — diagnostic overlay is its own routine, its own render path
void on_render(int64 data) {
    // ... ESP drawing only ...
}

void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    // ... diagnostic drawing, separately registered, separately controlled ...
}

int64 main() {
    // Both registered; the diagnostic one no-ops when g_diag_enabled is false
    register_routine(cast<int64>(on_render),            0);
    register_routine(cast<int64>(on_render_diagnostic), 0);
    return 1;
}
```

The separation is also a CPU-budget thing: when `g_diag_enabled` is false, the diagnostic routine no-ops on the first line and costs nothing. When it's true, it draws every frame. Letting users (or you, in development) toggle that with a single global is the discipline.

**Why:** Mixed render paths are impossible to ship to two audiences. Separated render paths let you ship one binary that's clean by default and rich-on-demand. Cost is one extra global, one extra routine registration; benefit is permanent.

---

## 2. The Diagnostic Overlay Has Five Standard Sections

**Diagnostic overlays converge on the same shape across projects. Pin it once; reuse it.**

The five sections, in display order:

1. **Process & module status** — `g_proc.alive()` result, base address, module size, whether base resolution succeeded.
2. **Sig resolution status** — per-named-sig: hit address (or 0), resolved address (after RIP), uniqueness margin (if you ran the checker at build time).
3. **Runtime data sanity** — first few entity-list entries, local-player address, view-matrix sample value, whether the values look plausible (in range, non-zero, etc.).
4. **Profiler readouts** — per-routine `avg / max / count` from the `pcx-perf-budget` profiler recipe.
5. **Error counters** — counts of failed reads, null pointer cases caught, sig-resolution fallbacks, exception catches. (Use atomic counters per `addon-atomic` if features can write to them concurrently.)

```cpp
void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;

    float64 x = 10.0;
    float64 y = 200.0;
    float64 line_h = 16.0;
    uint64 font = get_font20();
    color fg = color(220, 220, 220, 255);
    color hdr = color(255, 200, 80, 255);
    color shadow = color(0, 0, 0, 180);

    // Section 1: Process & module
    draw_text("[ Process ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  alive: {s}  base: 0x{x}  size: 0x{x}",
                     g_proc.alive() ? "yes" : "no", g_module_base, g_module_size),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h + 4.0;

    // Section 2: Sig resolution
    draw_text("[ Sigs ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  entity_list: hit=0x{x} resolved=0x{x}",
                     g_sig_entity_list_hit, g_off_entity_list),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  view_matrix: hit=0x{x} resolved=0x{x}",
                     g_sig_view_matrix_hit, g_off_view_matrix),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h + 4.0;

    // Section 3: Runtime sanity
    draw_text("[ Runtime ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  ent count: {d}  first ent: 0x{x}",
                     g_ent_count, g_first_ent_ptr),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h + 4.0;

    // Section 4: Profiler (read from pcx-perf-budget bucket accumulators)
    draw_text("[ Profile ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    for (int32 i = 0; i < NUM_BUCKETS; i++) {
        if (g_bucket_count[i] == 0) continue;
        int64 avg = g_bucket_total_us[i] / g_bucket_count[i];
        draw_text(format("  {s}: avg {d}us  max {d}us",
                         g_bucket_name[i], avg, g_bucket_max_us[i]),
                  vec2(x, y), fg, font, 1, shadow, 1.0);
        y += line_h;
    }
    y += 4.0;

    // Section 5: Error counters
    draw_text("[ Errors ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  null reads: {d}  sig fallbacks: {d}",
                     g_err_null_reads, g_err_sig_fallbacks),
              vec2(x, y), fg, font, 1, shadow, 1.0);
}
```

The five-section structure is enough to diagnose ~90% of script issues without further instrumentation. When a user reports "the script isn't working," the screenshot of this panel answers the question.

**Why:** Ad-hoc diagnostics in different scripts use different shapes; you waste mental energy each time figuring out which info is shown where. The five-section structure is a contract — once your team agrees on it, every script's diagnostic surface is interchangeable.

---

## 3. Gate the Toggle Behind a Hotkey, Not a GUI Widget Default

**The diagnostic overlay should default to OFF and be toggleable via a hotkey. A GUI checkbox is fine *as well*, but the hotkey is the primary control.**

End users won't navigate to a GUI section just to enable diagnostics — they'll Discord-message the author asking "why doesn't this work?" A hotkey they can hit gives them (and you, helping them) a 1-second path to the diagnostic info.

```cpp
bool   g_diag_enabled = false;
int32  g_diag_hotkey  = 0x77;   // VK_F8 by default

int64 main() {
    // ... process attach ...

    int64 sec = create_section("Debug");
    section_checkbox(sec, "Show diagnostic overlay", g_diag_enabled);
    section_keybind(sec, "Toggle diagnostic hotkey", g_diag_hotkey);
    section_separator(sec);
    section_label(sec, "Hotkey toggles section 1-5 readout.");

    register_routine(cast<int64>(on_update),            0);
    register_routine(cast<int64>(on_render),            0);
    register_routine(cast<int64>(on_render_diagnostic), 0);
    return 1;
}

void on_update(int64 data) {
    if (is_key_pressed(g_diag_hotkey)) {
        g_diag_enabled = !g_diag_enabled;
    }
    // ... feature update logic ...
}
```

When the user reports a problem, the support cycle is:

```
You:    "Hit F8 in-game, screenshot the panel, paste it to me."
User:   [screenshot]
You:    "entity_list resolved=0 — your binary doesn't match the supported version.
        See README requirements."
```

The diagnostic panel + hotkey reduces a 20-message back-and-forth to a 2-message exchange.

**Why:** Hotkeys are the universal "I need diagnostic info now" gesture. GUI checkboxes are good for opt-in features the user explicitly knows they want; diagnostic toggles need to be reachable when the user is *confused*, which is when they're not navigating GUI panels.

---

## 4. Diagnostic Routines Are Read-Only — Never Modify Game State

**The diagnostic overlay reads everything it shows. It never writes, never patches, never calls into game functions, never modifies the script's own behavior.**

This is the rule that lets you leave the diagnostic surface enabled in production builds for support purposes — it cannot break anything by being on. If the diagnostic does any of these:

- Calls `memory_write` to patch a value
- Calls a game function via a hook
- Modifies any other feature's globals (e.g. forcing `g_aim_target_id = X` "to test")
- Reads in a way that has side effects (rare, but some MMIO regions do)

...then the diagnostic itself is now a feature, with its own correctness concerns. It needs its own evidence entries (`skill://re-evidence-log`), its own validation, its own bug surface. Conflating "diagnostic" and "active feature" produces neither well.

The cost of pure-read diagnostics: occasionally you want to verify a write path. Don't put that in the diagnostic overlay; put it in a *separate* "lab" feature in `Misc` with its own master toggle, its own warnings, its own GUI gating. The lab feature is opt-in destructive; the diagnostic overlay is opt-in observational.

```cpp
// RIGHT — pure read diagnostic
void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    // reads only — g_proc.ru64, g_proc.read_memory, accumulator dereferences
}

// WRONG — diagnostic that also writes
void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    if (is_key_pressed(VK_F9)) {
        g_proc.write_u32(g_off_health, 100);   // "just testing health write"
    }
    // ... drawing ...
}

// RIGHT — separate lab feature, GUI-gated, distinct toggle
bool g_lab_enabled = false;
void on_update_lab(int64 data) {
    if (!g_lab_enabled) return;
    if (is_key_pressed(VK_F9)) {
        g_proc.write_u32(g_off_health, 100);   // intentional, opted-in
    }
}
```

**Why:** A read-only diagnostic can stay enabled during gameplay without consequence; an active diagnostic can't. The discipline preserves the diagnostic overlay's "safe to leave on" property, which is what makes it useful for support.

---

## 5. Atomic Counters for Cross-Routine State

**When multiple routines (update + render + features) increment error counters or sample profile buckets, use atomic types (`addon-atomic`) — not plain integers.**

PCX scripts can have multiple routines firing on different scheduler cadences; if both `on_update` and `on_render` write to `g_err_null_reads`, the increments can interleave and lose counts on plain integers. `aint32` / `aint64` (per `docs/enma/addon-atomic.md`) handle this correctly without locks.

```cpp
import "atomic";

aint32 g_err_null_reads;
aint32 g_err_sig_fallbacks;
aint64 g_total_reads;

void on_update(int64 data) {
    uint64 entity = g_proc.ru64(g_off_entity_list);
    g_total_reads.add(1);                  // atomic increment
    if (entity == 0) {
        g_err_null_reads.add(1);
        return;
    }
    // ...
}

void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    // load() reads the current atomic value
    int32 nulls = g_err_null_reads.load();
    int64 total = g_total_reads.load();
    draw_text(format("  null reads: {d} / {d} total", nulls, total),
              vec2(x, y), fg, font, 1, shadow, 1.0);
}
```

For single-writer counters (only `on_update` increments, only `on_render_diagnostic` reads), plain integers are fine — atomic is overkill. The atomic discipline applies when multiple writers exist.

**Why:** Lost counts in error counters silently hide bugs (you report "10 null reads" when the actual was 47 because 37 increments interleaved and overwrote each other). Atomics are cheap; the bug they prevent is invisible.

---

## 6. Ship a Diagnostic-Only Build for Power Users

**Some users want the diagnostic build by default — the streamer doing tech-content, the long-tail debugger, the script's contributor. Ship two `.emb` artifacts: production (`script.emb`) and diagnostic (`script-debug.emb`).**

The split:

| Build | `g_diag_enabled` default | `g_diag_hotkey` works | Extra debug features |
|---|---|---|---|
| `script.emb` (production) | `false` | yes | none |
| `script-debug.emb` (diagnostic) | `true` | yes | profiler dumps to file, extra logging |

The implementation: a single `#define` (per `docs/enma/lang-pre-processor.md`) controls the build flavor:

```cpp
// At the top of main.em
#define BUILD_FLAVOR_DEBUG     // comment out for production

#ifdef BUILD_FLAVOR_DEBUG
    bool g_diag_enabled_default = true;
#else
    bool g_diag_enabled_default = false;
#endif

bool g_diag_enabled = g_diag_enabled_default;

#ifdef BUILD_FLAVOR_DEBUG
    // Extra debug-only routines
    void on_update_log_to_file(int64 data) {
        // periodic snapshot of profiler buckets to disk for offline analysis
    }
#endif

int64 main() {
    // ... process attach ...
    register_routine(cast<int64>(on_render),            0);
    register_routine(cast<int64>(on_render_diagnostic), 0);
    #ifdef BUILD_FLAVOR_DEBUG
        register_routine(cast<int64>(on_update_log_to_file), 0);
    #endif
    return 1;
}
```

Build both flavors as part of your release process (see `skill://script-bundler`). Ship the production one as the headline download; ship the debug one as a "for support / contributors" link in the README.

**Why:** Two builds from one source is cheap (one `#define` swap, two compilations); the value to users who need diagnostics-by-default (streamers, contributors, support) is real. The alternative is shipping one build and asking users to enable diagnostics manually each time — fine for most, friction for the power users you want engaged.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | Two overlays, always separate | Production renders user-visible features; diagnostic renders script-internal state |
| 2 | Five standard sections | Process / Sigs / Runtime / Profile / Errors — covers ~90% of "script isn't working" reports |
| 3 | Hotkey-gated, off by default | Default off, F8 toggles on — reachable when the user is confused, invisible otherwise |
| 4 | Read-only diagnostics | No writes, no hooks; lab/test features are separate, opt-in destructive features |
| 5 | Atomic counters for cross-routine state | `aint32` / `aint64` for multi-writer counters; plain ints for single-writer |
| 6 | Two builds: production + diagnostic | `#define BUILD_FLAVOR_DEBUG` switch; both shipped, production headline |

**Cross-references:** `skill://pcx-perf-budget` (the `mono_us()` profiler recipe section 4 consumes); `knowledge/gui-design-patterns.md` (the "no debug panel by default" rule this skill extends); `skill://script-bundler` (the two-build process); `skill://re-evidence-log` (the lab features' citation discipline); `docs/enma/addon-atomic.md` (the atomic types section 5 uses); `docs/enma/lang-pre-processor.md` (the `#ifdef` mechanism section 6 uses).
