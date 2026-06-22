# cheat-skeleton-lua

A complete Perception.cx Lua skeleton for educational game-cheat-script development.

## Contents

| File | Purpose |
|------|---------|
| `globals.lua` | Shared handles, config, entity cache |
| `offsets.lua` | Pattern signatures and address resolution |
| `utils.lua` | W2S, chain reader, distance, team helpers |
| `esp.lua` | Box ESP + snaplines + info |
| `aim.lua` | Smooth aimbot with FOV cone filter |
| `triggerbot.lua` | Crosshair-trigger logic |
| `radar.lua` | 2D world radar |
| `menu.lua` | Config, keybinds, save/load |
| `main.lua` | Entry point, setup, frame hook |

## Usage

1. Copy the directory into your cheat project.
2. Update `offsets.lua` signatures and `OFF_*` constants for your target (verify in IDA/ReClass).
3. Set the real process name in `main.lua`.
4. Load `main.lua` into the PCX Lua runtime.
5. Extend modules; do not hard-code live memory values.

## Warning

All signatures and offsets in this skeleton are **UNVERIFIED placeholders**.
They will not work until you replace them with values derived from your own
authorized target. Use this only on software you own or have explicit
permission to analyze.
