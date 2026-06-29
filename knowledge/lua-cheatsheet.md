# Perception Lua Cheat Sheet

Use this for current Perception Lua (`.lua`) scripts. Verify every symbol with `pcx api <symbol> --lang lua` or MCP `api_lookup(symbol, "lua")` before final code.

## Official source set

The Perception Lua docs are the source of truth: https://docs.perception.cx/perception/lua-script/overview.md

Core surfaces include lifecycle, render, input, proc, GUI, system, net, file system, math, engine, JSON, utilities, sound, CS2 extended API, Zydis encoder, and intrinsics.

## Lifecycle

```lua
function main()
    log("PCX Lua loaded")
    return 1
end

function on_frame()
    draw_text("PCX Lua", 20, 20, 255, 255, 255, 255, get_font20(), TE_SHADOW, 0, 0, 0, 180, 1.0)
end

function on_unload()
end
```

## Render

Use scalar `x, y` and `r, g, b, a` arguments. Do not use Enma `vec2` or `color` wrappers.

```lua
draw_rect_filled(20, 20, 300, 88, 20, 20, 20, 210, 8.0, RR_TOP_LEFT)
draw_text("Hello", 36, 46, 255, 255, 255, 255, get_font20(), TE_SHADOW, 0, 0, 0, 180, 1.0)
```

## Proc

```lua
local proc = ref_process("game.exe")
if not proc then return 0 end
local base = proc:base_address()
deref_process(proc)
```

Release `process` handles with `deref_process(proc)` when done or in `on_unload()`.

## Validation commands

```bash
pcx api draw_text --lang lua
pcx symbol-check script.lua
pcx verify script.lua
```
