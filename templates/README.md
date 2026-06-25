# Templates

Starter Enma scripts for Perception.cx. All follow the [12 guidelines](../.claude/skills/game-cheat-guidelines/SKILL.md) and validate against the generated API index.

## Single-file starters

| File | What it shows |
|------|---------------|
| [`hello-world.em`](hello-world.em) | Minimal script — lifecycle, one render routine, text drawing |
| [`overlay-basic.em`](overlay-basic.em) | GUI menu, config-driven rendering, update/render separation, input polling, FPS readout |

## Multi-file project scaffold

[`full-project/`](full-project/) — the recommended structure for anything non-trivial. One concern per file:

| File | Role |
|------|------|
| [`globals.em`](full-project/globals.em) | Shared state: process handle, module base/size, config |
| [`offsets.em`](full-project/offsets.em) | Named signatures + RIP-relative resolver |
| [`feature.em`](full-project/feature.em) | One feature: update (reads) + render (draws), separated |
| [`menu.em`](full-project/menu.em) | GUI sidebar + config save/load |
| [`main.em`](full-project/main.em) | Entry point: attach, resolve, register routines |

**Bundle order:** `globals → offsets → feature → menu → main` (each imports the ones above it).


## Using these

1. Copy a template into your Perception scripting directory
2. Replace `"game.exe"` with your target process name
3. Replace the example signatures in `offsets.em` with real sigs for your target (see [offset methodology](../knowledge/offset-methodology.md))
4. Build/verify in the Perception IDE (`check_script` / Verify button)

Every template is a skeleton — the structure and API calls are correct, but the offsets and read logic are placeholders you fill in for your specific target.
