---
name: pcx-defer-ledger
description: >
  Harvest every `// defer:` comment in the PCX project into a debt ledger.
  Tracks deliberate shortcuts (global handles, hardcoded colors, single-walk
  assumptions) so deferrals don't rot into permanent hacks. Use when the user
  says "defer ledger", "what did we defer", "list shortcuts", "show debt", or
  invokes /pcx-defer-ledger. One-shot report, changes nothing.
license: MIT
---

Every deliberate shortcut is marked `// defer: <ceiling>, <trigger>`. This
collects them into one ledger so a deferral can't quietly become permanent.

## Scan

Search `.em` and `.as` files for `// defer:` markers, skipping build output:

```
grep -rnE '// ?defer:' --include='*.em' --include='*.as' .
```

Also scan for `// UNVERIFIED` — those are offset-confidence markers, tracked
separately but surfaced in the same report.

## Output

### Defer markers

One row per marker, grouped by file:

```
<file>:<line> — <what was simplified>. ceiling: <limit>. trigger: <when to revisit>.
```

Pull ceiling and trigger from the comment. The convention is
`// defer: <ceiling>, <trigger>`.

### Rot risk

Flag `no-trigger` on any `// defer:` that names no upgrade condition — those
rot silently.

### Unverified offsets

Separate section:

```
<file>:<line> — <offset/field>. source: UNVERIFIED.
```

These aren't shortcuts, they're confidence gaps. Surface them so they can be
resolved against the live target.

### Summary

```
<N> defer markers (<M> with no trigger)
<P> UNVERIFIED offsets
```

Nothing found: `No deferred debt. Clean ledger.`

## Boundaries

Reads and reports only, changes nothing. To persist: ask, and it writes the
ledger to `DEFER-LEDGER.md` at the project root. One-shot.
