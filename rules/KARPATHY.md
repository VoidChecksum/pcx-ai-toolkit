# Karpathy Discipline for PCX Scripting

Drop-in work-discipline rules for any AI tool writing Perception.cx scripts. Companion to `CLAUDE.md` (which covers code standards). Copy both into your project.

The four Karpathy principles, rewritten for cheat development and reverse engineering. `CLAUDE.md`'s 12 guidelines say *what the code must look like*; these say *how to work* so you don't ship a confident guess.

## 1. Think Before Coding

**State assumptions before writing a line.** Name the game, engine, and module. Say where every offset comes from — sig scan, SDK header, or hardcode. Mark guesses `// UNVERIFIED`. Surface the tradeoff the user didn't ask about (read-only ESP is invisible; a memory write is a detection surface). If a doc is ambiguous or an API is permission-gated, read the doc — never invent function names or assume field sizes.

## 2. Simplicity First

**Build the minimum feature that works.** Ship the box before the skeleton ESP; the snap-aim before velocity prediction. No config system for a value that never changes, no abstraction over the proc API, no feature-manager framework for three features. Three registered routines *is* the framework. Every speculative line is a line someone debugs after the next patch.

## 3. Surgical Changes

**One feature, one diff.** Editing ESP color? Edit `esp.em` — don't reformat `menu.em`, rename globals, or "tidy" `main.em`. Match the existing module's style. Remove the imports/globals your change orphans; mention unrelated dead code, don't delete it. Don't churn offsets that still hit and resolve to valid data. Perception's hot reload exists so you can change one file without disturbing the rest — honor it.

## 4. Goal-Driven Execution

**Done means it works on the target, not "it compiles."** Write success criteria as observable facts before coding ("boxes track enemies at any distance, nothing draws behind the camera, count matches the scoreboard"). The overlay is your debugger — draw raw W2S coords and `print` counts instead of guessing. Loop: compile → load → look → compare → fix. When the IDB, the SDK, and the live read disagree, trust the live read; the SDK may be from an older season.

---

| Principle | The one-liner |
|-----------|---------------|
| Think before coding | Name the target, the offset source, and the tradeoff first |
| Simplicity first | Ship the box, not the framework |
| Surgical changes | One feature, one diff; clean only your own orphans |
| Goal-driven execution | Done = visible criteria met on the live target |

Full detail with examples: `skill://pcx-coding-discipline` (writing scripts) and `skill://pcx-re-discipline` (reverse engineering).
