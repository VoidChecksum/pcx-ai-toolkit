# cheat-skeleton-em

A complete Perception.cx Enma skeleton for educational game-cheat-script development.

## Contents

| File | Purpose |
|------|---------|
| `globals.em` | Shared handles, config, entity cache |
| `offsets.em` | Pattern signatures and address resolution |
| `utils.em` | W2S, chain reader, distance, team helpers |
| `esp.em` | Box ESP + snaplines + info |
| `aim.em` | Smooth aimbot with FOV cone filter |
| `triggerbot.em` | Crosshair-trigger logic |
| `radar.em` | 2D world radar |
| `menu.em` | Config, keybinds, save/load |
| `main.em` | Entry point, setup, update/render hooks |

## Usage

1. Copy the directory into your cheat project.
2. Update `offsets.em` signatures and `OFF_*` constants for your target (verify in IDA/ReClass).
3. Set the real process name in `main.em`.
4. Compile with the Enma bundle order shown in `main.em`.
5. Extend modules; do not hard-code live memory values.

## Warning

All signatures and offsets in this skeleton are **UNVERIFIED placeholders**.
They will not work until you replace them with values derived from your own
authorized target. Use this only on software you own or have explicit
permission to analyze.
