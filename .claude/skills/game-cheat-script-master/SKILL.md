---
name: game-cheat-script-master
description: >
  Master skill for Perception.cx game cheat script development. Activates on any
  request for cheats, hacks, ESP, aimbot, triggerbot, radar, overlay, memory
  reading, pattern scanning, or anti-cheat research. Loads the complete doc
  index, the 12 cheat guidelines, the AI pair-programming workflow, and the
  official cheat templates. Always use this alongside game-cheat-guidelines and
  game-hacking-pcx.
license: MIT
---

# Game Cheat Script Master — Perception.cx

This skill turns any LLM into a specialized Perception.cx cheat-script developer.
It is the single entry point for **ESP, aimbot, triggerbot, radar, overlay,
memory-reading, world-to-screen, pattern-scanning, and anti-cheat research**
requests. It tells the model exactly which docs to read, which rules to follow,
which templates to scaffold from, and how to stay safe and legal.

**Always active when the user asks for any kind of game cheat, hack, overlay,
memory script, or Perception.cx tooling related to games.**

---

## Trigger

- Any request containing: cheat, hack, esp, wallhack, aimbot, triggerbot,
  recoil, no-recoil, radar, overlay, menu, gui, memory read, pattern scan,
  signature, offset, vtable hook, anti-cheat, EAC, BattlEye, Vanguard, GameGuard,
  integrity check, bypass, streamproof, kernel driver, dump, IDA, Ghidra, r5sdk,
  source engine, Unreal Engine, Unity, Frostbite, REDengine, CryEngine, Godot.
- Any file extension: `.em`, `.as` in a Perception.cx context.
- Any mention of `ref_process`, `find_code_pattern`, `ru64`, `draw_rect`,
  `world_to_screen`, `register_routine`, `proc_t`, `perception`, `enma`, `angelscript`.

---

## Mandatory Co-Loaded Skills

Load these on every cheat-script session. They are prerequisites, not options.

| Skill | Why it matters |
|-------|----------------|
| `skill://game-cheat-guidelines` | The 12 hard rules: `uint64` addresses, null checks, scan/render separation, sigs over hardcodes, GUI for tunables, etc. |
| `skill://game-hacking-pcx` | The full doc router: which `docs/perception/` and `docs/enma/` files to read before writing any API call. |
| `skill://ai-pair-programming` | How to drive the AI: read docs first, plan before code, verify sigs with MCP, diff-review, unstuck questions. |
| `skill://pcx-patch-day-playbook` | What to do when the script breaks after a game update. |
| `skill://mcp-tool-routing` | Which of the 59 Perception MCP tools to use for binary discovery. |

---

## Read-First Docs

Before writing **any** cheat script code, read these in order. They are small
and prevent the most expensive mistakes.

1. **Quick API surface:** `knowledge/pcx-api-cheatsheet.md` (15 KB)
2. **The 12 guidelines:** `.claude/skills/game-cheat-guidelines/SKILL.md`
3. **Language reference:** `docs/enma/llms-language.md`
4. **Core APIs for almost every cheat:**
   - `docs/perception/proc-api.md` — process attach, memory reads, pattern scan
   - `docs/perception/render-api.md` — 2D overlay drawing
   - `docs/perception/gui-api.md` — sidebar widgets for every tunable
   - `docs/perception/input-api.md` — keybinds and polling
5. **Math & patterns:**
   - `knowledge/aimbot-math.md` — `calc_angle`, smoothing, FOV checks, angle wrap
   - `knowledge/common-patterns.md` — world-to-screen, ESP boxes, snaplines, radar
   - `knowledge/offset-methodology.md` — how to find and maintain offsets
6. **Engine-specific notes:** `knowledge/engine-*.md` and `signatures/*/*.md`
7. **Anti-cheat research:** `knowledge/anti-cheat-architecture.md`, `signatures/anti-cheat/common-ac-patterns.md`
8. **Cheat cookbook (templates + recipes):** `knowledge/cheat-script-cookbook.md`

---

## Project Scaffolding

Use the official templates. Do **not** invent a layout.

| Template | Use when |
|----------|----------|
| `templates/cheat-skeleton-em/` | Full Enma cheat project (ESP, aim, triggerbot, radar, menu) |
| `templates/full-project/` | Minimal one-feature Enma scaffold |
| `templates/aimbot-skeleton.em` | Standalone aimbot math/reference |
| `templates/overlay-basic.em` | Tiny overlay-only script |

Scaffold command pattern:

```bash
pcx new cheat-skeleton-em my-esp
```

If `pcx new` is not available, copy the template directory manually.

---

## Standard Module Layout

Every full cheat project should look like this. One feature, one file.

```
project/
├── globals.em/as   # proc_t, base/size, entity cache, config state
├── offsets.em/as   # all sigs + resolved addresses + RIP helpers
├── esp.em/as       # entity reads + 2D/3D box / health / name
├── aim.em/as       # target selection + smoothing + angle writeback
├── triggerbot.em/as # trigger timing + crosshair check
├── radar.em/as     # world-to-map + blips
├── menu.em/as      # GUI sidebar, keybinds, config load/save
├── utils.em/as     # W2S, distance, team check, visibility helper
└── main.em/as      # attach, resolve, register routines, unload
```

If the target engine or game is known, name the process string and module
explicitly, but never hardcode an absolute address.

---

## Domain-Specific Rules (In Addition to the 12 Guidelines)

### Anti-Cheat & Legal Scope

- **Analyze only software you own or are authorized to test.**
- Single-player, offline, or your-own-process research is the default scope.
- Multi-player or live-service work requires explicit authorization; if unsure,
  refuse and tell the user to verify their rights.
- Do not produce code whose sole purpose is to bypass kernel anti-cheat or evade
  detection in a protected online environment.
- Defensive anti-cheat analysis (understanding how detection works, writing
  detection tools, mapping integrity checks for authorized research) is allowed.

### Memory Safety

- `uint64` for every address, pointer, module base, and VTable slot.
- Null-check after **every** `ru64`, `find_code_pattern`, `get_module_base`,
  `ref_process`, and pointer-chain step.
- Failed reads return `0`, not exceptions. Treat `0` as "I don't know yet."
- Prefer read-only analysis and visualization. Writes are a last resort,
  minimal bytes, verified with read-back, gated behind permissions.

### Pattern Scanning

- Never generate a sig from memory. Use `mcp:find_pattern` or
  `python tools/sig-uniqueness-checker.py --sig` on the actual binary.
- Keep sigs in `offsets.*`, named, with a comment describing the instruction.
- Resolve RIP-relative displacements correctly: `final = hit + insn_len + signed_disp`.
- Wildcard only the displacement bytes; don't wildcard opcodes that identify the
  instruction pattern.

### Rendering

- Update routines read + build a cache. Render routines draw only from the cache.
- Construct `color`, `vec2`, `vec3` per frame; they are stack value types.
- Always check `w > 0.001` (or engine-equivalent) before trusting world-to-screen.
- Use `get_view_width()` / `get_view_height()` for screen-space scaling.

### Aimbot

- `calc_angle` returns `(pitch, yaw)` in degrees, engine-convention specific.
- Normalize yaw delta to `[-180, 180)` with the `fmod(delta + 540.0, 360.0) - 180.0` trick.
- Clamp pitch to `[-89, 89]` or engine limits; never wrap pitch.
- Smooth with `current + delta * factor`, factor exposed in GUI as a slider.
- FOV check before aiming; prefer the closest in-FOV enemy or the one under
  crosshair, configurable in GUI.

### Triggerbot

- Read the same entity data the ESP uses; do not duplicate entity walks.
- Add a small random delay or fire only when crosshair is stable to avoid robotic
  timing; expose the delay range in the GUI.
- Respect game fire-rate by checking `can_fire()` or equivalent if available.

### Radar

- Project world positions to a 2D map coordinate using a chosen reference origin
  and scale; do not call expensive W2S per blip.
- Draw blips as colored circles with team differentiation.
- Keep the radar in its own render routine with no memory reads.

### Config / Menu

- Every tunable (distance, color, smoothing, FOV, hotkey, toggle) is bound to a
  GUI widget in `menu.*`.
- Load config from a JSON file in `main()` and save on change.
- Use `section_checkbox`, `section_slider_float`, `section_keybind`,
  `section_color_picker`, `section_combo_box` as appropriate.

---

## Decision Tree for "Which Language?"

| User wants... | Default | Alternative |
|---------------|---------|-------------|
| Modern PCX, hot reload, typed, fast | **Enma (.em)** | — |
| Host already loads AngelScript | AngelScript (.as) | — |
| Cross-engine portability | Enma | AngelScript when the host already loads it |

See `docs/perception/llm-routing.md` for the full Enma vs AngelScript comparison.

---

## Decision Tree for "Which Doc First?"

| Task | Read first | Then read |
|------|------------|-----------|
| "Write an ESP" | `docs/perception/proc-api.md` | `docs/perception/render-api.md`, `knowledge/common-patterns.md` |
| "Write an aimbot" | `knowledge/aimbot-math.md` | `docs/perception/proc-api.md`, `docs/perception/input-api.md` |
| "Add a menu" | `docs/perception/gui-api.md` | `knowledge/common-patterns.md` |
| "Find offsets/sigs" | `knowledge/offset-methodology.md` | `signatures/<engine>/*.md`, `skill://mcp-tool-routing` |
| "Script broke after patch" | `skill://pcx-patch-day-playbook` | `knowledge/offset-methodology.md` |
| "Anti-cheat research" | `knowledge/anti-cheat-architecture.md` | `signatures/anti-cheat/common-ac-patterns.md` |

---

## Common Pitfalls to Catch in Diff Review

| Code smell | Rule | Fix |
|------------|------|-----|
| `int64` / `int32` near `addr`, `base`, `ptr`, `offset` | #2 | Change to `uint64` |
| Bare float literal in GPU/vertex data | #8 | Add `f` suffix |
| `ru64()` result used without `== 0` check | #3 | Add null guard |
| `find_code_pattern` in render/update tick | #4 | Move to `main()` / `offsets.*` |
| Hardcoded RVA without citation | #1, #12 | Replace with sig + `// E-NNN` or `// UNVERIFIED` |
| `color` / `vec2` / `vec3` at file scope | #7 | Construct per frame |
| Hotkey hardcoded, no GUI widget | #11 | Add `section_keybind` |
| Memory write not gated / too large | #9 | Minimize bytes, verify, use permissions |
| W2S without `w > 0.001` check | #10 | Add behind-camera guard |
| One giant file | #6 | Split into globals/offsets/esp/aim/menu/main |

---

Before delivering any cheat script:

1. [ ] Read the relevant docs (see "Read-First Docs" above).
2. [ ] Load the mandatory co-skills.
3. [ ] Scaffold from an official template.
4. [ ] Honor the 12 `game-cheat-guidelines` plus the domain rules here.
5. [ ] Verify sigs/offsets against a real binary, not from memory.
6. [ ] Separate update (reads) from render (draws).
7. [ ] Bind every tunable to a GUI widget.
8. [ ] Add `uint64` address checks, null checks, and `w > 0` guards.
9. [ ] Confirm the work is for authorized/single-player/educational targets.
10. [ ] Run `pcx verify <file>` and fix any `unknown_call` / `missing_import` findings.
11. [ ] Suggest `pcx lint <file>` and a diff review before running.
