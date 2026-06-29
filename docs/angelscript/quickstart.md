# Perception AngelScript Quickstart

Source: https://docs.perception.cx/perception/angel-script/overview.md

AngelScript (`.as`) is the current production scripting surface while Enma AOT is unreleased. Use this mode for UI, rendering, memory analysis, process interaction, and PCX add-ons documented under `https://docs.perception.cx/perception/angel-script/`.

## Lifecycle

Source: https://docs.perception.cx/perception/angel-script/life-cycle.md

```cpp
int main()
```

Return `> 0` to keep the script loaded. Return `<= 0` to unload after `main()` completes. Use `void on_unload()` for cleanup. Do not run infinite loops inside `main()`; register callbacks instead.

```cpp
void on_tick(int id, int data_index)
{
    float w, h;
    get_view(w, h);
    draw_text("Hello", 20, 20, 255,255,255,255, get_font20(), TE_SHADOW, 0,0,0,180, 1.0f);
}

int main()
{
    register_callback(on_tick, 16, 0);
    return 1;
}
```

## Core types and add-ons

AngelScript has `string`, `array<T>`, `dictionary`, `any`, and PCX host add-ons including Render, Input, Proc, Mutex, GUI, System, Net, File System, Extended Math, Engine Specific, Json, Zydis Encoder, Intrinsics, Sound, Bit Reinterpret Helpers, and Unicorn.

## Proc discipline

Source: https://docs.perception.cx/perception/angel-script/proc-api.md

Use `proc_t` handles and `uint64` virtual addresses. Release acquired process handles with `deref()` when done or on unload.

```cpp
proc_t p = ref_process("game.exe");
if (p.pid() == 0)
{
    log("process not found");
    return 0;
}
uint64 base = p.base_address();
p.deref();
```

## Render discipline

Source: https://docs.perception.cx/perception/angel-script/render-api.md

AngelScript Render API uses scalar coordinates and RGBA arguments. Do not use Enma `vec2(...)` or `color(...)` wrappers in `.as` code.
