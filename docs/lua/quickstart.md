# Perception Lua Quickstart

Source: https://docs.perception.cx/perception/lua-script/overview.md

Lua (`.lua`) is a current Perception scripting surface for UI, rendering, memory analysis, process interaction, and PCX add-ons. Verify every symbol with `pcx api <symbol> --lang lua` before final code.

## Lifecycle

Source: https://docs.perception.cx/perception/lua-script/life-cycle.md

```lua
function main()
    log("Lua script loaded")
    return 1
end

function on_frame()
    draw_text("Hello", 20, 20, 255, 255, 255, 255, get_font20(), TE_SHADOW, 0, 0, 0, 180, 1.0)
end

function on_unload()
end
```

`main()` is required. A script remains active only when `main()` returns `> 0` and `on_frame()` exists. Use `on_unload()` for cleanup. Do not run infinite loops in `main()`.

## Render discipline

Source: https://docs.perception.cx/perception/lua-script/render-api.md

Lua render APIs use scalar coordinates and RGBA arguments. Do not use Enma `vec2(...)` or `color(...)` wrappers in Lua.

## Proc discipline

Source: https://docs.perception.cx/perception/lua-script/proc-api.md

Use `process` userdata handles from `ref_process(...)`, release them with `deref_process(process)`, and treat addresses as `uint64` virtual addresses.

## Validation

```bash
pcx api draw_text --lang lua
pcx symbol-check script.lua
pcx verify script.lua
```
