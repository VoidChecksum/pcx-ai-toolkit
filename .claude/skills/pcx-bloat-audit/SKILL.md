---
name: pcx-bloat-audit
description: >
  Whole-project audit for over-engineering in PCX scripts. Scans every .em and
  .as file for wrappers, dead abstractions, duplicate entity walks, unused
  offsets, and config systems that outweigh their settings. Ranked by lines
  recoverable. Use when the user says "audit for bloat", "what can I delete",
  "find over-engineering", "slim this project", or invokes /pcx-bloat-audit.
  One-shot report, does not apply fixes.
license: MIT
---

pcx-bloat-review, project-wide. Scan every `.em` and `.as` file. Rank
findings by lines recoverable, biggest first.

## Tags

Same as pcx-bloat-review:

- `delete:` dead code, unused feature path, speculative abstraction.
- `pcx-api:` hand-rolled thing the PCX API ships. Name the function + doc.
- `inline:` wrapper/class/helper with one caller.
- `yagni:` abstraction with one implementation, config for nothing.
- `shrink:` same logic, fewer lines.
- `merge:` two routines/walks that should be one.

## Hunt List

Scan for these in priority order:

1. **Dead offsets** — sig constants or hardcodes nothing reads. Post-patch debris.
2. **Single-caller wrappers** — functions that wrap one `p.ru64()` / `p.wu64()` call.
3. **Class hierarchies for one feature** — `IFeature`, `BaseEntity`, `AbstractRenderer` with one concrete child.
4. **Config systems vs setting count** — if the config loader is longer than the settings it loads, flag it.
5. **Duplicate entity walks** — two routines independently iterating the same list.
6. **Files exporting one symbol** — `utils.em` with one function, `types.em` with one typedef.
7. **Unused imports** — `import` statements for modules nothing in the file calls.
8. **Commented-out code blocks** — not `// defer:` or `// UNVERIFIED`, just dead code behind `//`.

## Output

One line per finding, ranked by lines recoverable:

```
<tag> <what to cut>. <replacement or "nothing">. [<file>:<lines>] (-<N> lines)
```

End with:

```
net: -<N> lines, -<M> files possible across <P> findings.
```

Nothing to cut: `Lean already. Ship.`

## Boundaries

Complexity only. Does not flag correctness, security, or performance issues.
Does not touch `// defer:` or `// UNVERIFIED` markers — those are
deliberate/tracked. Does not apply fixes.
