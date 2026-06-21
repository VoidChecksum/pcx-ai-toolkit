# cheat-skeleton-as

A complete Perception.cx AngelScript skeleton for educational game-cheat-script development.

## Contents

| File | Purpose |
|------|---------|
| `globals.as` | Shared handles, config, entity cache |
| `offsets.as` | Pattern signatures and address resolution |
| `utils.as` | W2S, chain reader, distance, team helpers |
| `esp.as` | Box ESP + snaplines + info |
| `aim.as` | Smooth aimbot with FOV cone filter |
| `triggerbot.as` | Crosshair-trigger logic |
| `radar.as` | 2D world radar |
| `menu.as` | Config, keybinds, save/load |
| `main.as` | Entry point, setup, update/render hooks |

## Usage

1. Copy the directory into your cheat project.
2. Update `offsets.as` signatures and `OFF_*` constants for your target (verify in IDA/ReClass).
3. Set the real process name in `main.as`.
4. Compile with the AngelScript bundle order shown in `main.as`.
5. Extend modules; do not hard-code live memory values.

## Warning

All signatures and offsets in this skeleton are **UNVERIFIED placeholders**.
They will not work until you replace them with values derived from your own
authorized target. Use this only on software you own or have explicit
permission to analyze.
