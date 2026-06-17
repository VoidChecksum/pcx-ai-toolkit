---
name: pcx-bloat-review
description: >
  Code review focused on over-engineering in PCX scripts. Finds what to delete:
  proc_t wrappers, entity managers for three entities, config systems for two
  settings, class hierarchies for one feature. One line per finding. Use when
  the user says "review for bloat", "is this over-engineered", "what can I
  delete", or invokes /pcx-bloat-review. Complements correctness review — this
  one only hunts unnecessary complexity in Enma/AngelScript scripts.
license: MIT
---

Review PCX script diffs for unnecessary complexity. One line per finding.
The diff's best outcome is getting shorter.

## Format

`L<line>: <tag> <what>. <replacement>.`, or `<file>:L<line>: ...` for
multi-file diffs.

## Tags

- `delete:` dead code, unused feature path, speculative abstraction. Replacement: nothing.
- `pcx-api:` hand-rolled thing the PCX API already ships. Name the function + doc page.
- `inline:` wrapper/class/helper with one caller. Inline it.
- `yagni:` abstraction with one implementation, config nobody sets, manager for one thing.
- `shrink:` same logic, fewer lines. Show the shorter form.
- `merge:` two routines/walks that should be one. Name the merge.

## PCX-Specific Hunts

- **proc_t wrappers** — `ReadMemory()` / `ReadEntity()` functions that just call `p.ru64()` with no added validation. The proc API *is* the interface.
- **Entity managers / registries** — `EntityManager`, `FeatureRegistry`, `IFeature` interface for ≤3 features. Three routines registered in `main()` is the framework.
- **Config systems for few settings** — JSON/file config loader for 2-5 `bool` toggles. A `bool g_esp = true;` + sidebar checkbox is the config system.
- **Color/theme abstractions** — `ThemeManager`, `ColorScheme` classes when `color(r,g,b,a)` constructed per-frame costs nothing.
- **Over-split files** — `utils.em` exporting one function, `types.em` defining one typedef. Inline into the caller.
- **Duplicate entity walks** — two `on_update` routines walking the same entity list independently. One walk, two consumers.
- **Dead offset blocks** — sig constants or hardcoded offsets that nothing reads anymore. Post-patch leftover.

## Examples

✅ `esp.em:L12-38: inline: ReadEntity() wraps p.ru64() once with no guard. Inline the call, save 26 lines.`

✅ `main.em:L5-44: yagni: FeatureRegistry class for 2 features. register_routine() twice in main(), done.`

✅ `menu.em:L80-130: yagni: JSON config loader for 3 bools. bool globals + sidebar checkbox, 6 lines.`

✅ `globals.em:L22: delete: g_old_entity_list — nothing reads it since the sig update.`

✅ `esp.em:L60, radar.em:L40: merge: both walk entity_list independently. One walk in on_update, both draw in on_render.`

✅ `utils.em:L1-8: inline: exports only clamp(). Move to the one file that calls it, delete utils.em.`

## Scoring

End with: `net: -<N> lines, -<M> files possible.`

Nothing to cut: `Lean already. Ship.`

## Boundaries

Complexity only. Correctness bugs (wrong offsets, missing null guards, sign
extension), security (detection surface), and performance (read frequency)
belong to a normal review pass.

Does not touch `// defer:` comments — those are tracked deliberately.
Does not apply fixes, only lists them.
