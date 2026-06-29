# Perception AngelScript Cheat Sheet

Use this for current production `.as` scripts. Verify every symbol with `pcx api <symbol> --lang angelscript` or MCP `api_lookup(symbol, "angelscript")` before final code.

## Official source set

The Perception AngelScript docs are the source of truth:

- Overview: `https://docs.perception.cx/perception/angel-script/overview.md`
- Life Cycle: `https://docs.perception.cx/perception/angel-script/life-cycle.md`
- Engine: `https://docs.perception.cx/perception/angel-script/engine.md`
- Atomic Types: `https://docs.perception.cx/perception/angel-script/atomic-types.md`
- Unicorn: `https://docs.perception.cx/perception/angel-script/unicorn.md`
- Render API: `https://docs.perception.cx/perception/angel-script/render-api.md`
- Input API: `https://docs.perception.cx/perception/angel-script/input-api.md`
- Proc API: `https://docs.perception.cx/perception/angel-script/proc-api.md`
- Mutex API: `https://docs.perception.cx/perception/angel-script/mutex-api.md`
- GUI API: `https://docs.perception.cx/perception/angel-script/gui-api.md`
- System API: `https://docs.perception.cx/perception/angel-script/system-api-cpu-and-disassembly.md`
- Net API: `https://docs.perception.cx/perception/angel-script/net-api.md`
- File System: `https://docs.perception.cx/perception/angel-script/file-system.md`
- Extended Math API: `https://docs.perception.cx/perception/angel-script/extended-math-api.md`
- Win API: `https://docs.perception.cx/perception/angel-script/win-api.md`
- Engine Specific API: `https://docs.perception.cx/perception/angel-script/engine-specific-api.md`
- Json API: `https://docs.perception.cx/perception/angel-script/json-api.md`
- Utilities: `https://docs.perception.cx/perception/angel-script/utilities.md`
- Zydis Encoder: `https://docs.perception.cx/perception/angel-script/zydis-encoder.md`
- Intrinsics: `https://docs.perception.cx/perception/angel-script/intrinsics.md`
- Sound API: `https://docs.perception.cx/perception/angel-script/sound-api.md`
- Bit Reinterpret Helpers: `https://docs.perception.cx/perception/angel-script/bit-reinterpret-helpers.md`

## Lifecycle

```cpp
int main()
```

Return `> 0` to stay loaded. Return `<= 0` to unload. Register recurring work instead of looping forever in `main()`.

```cpp
void on_tick(int id, int data_index)
{
    // work here
}

int main()
{
    register_callback(on_tick, 16, 0);
    return 1;
}

void on_unload()
{
    // cleanup here
}
```

## Language rules

- Use AngelScript containers: `array<T>`, `dictionary`, `any`.
- Use `string` for text unless an API page documents another type.
- Do not use Enma-only `vec2(...)`, `color(...)`, `T[]`, `map<K,V>`, `imap<V>`, `cast<int64>(fn)`, or `register_routine(...)` in `.as` code.
- Do not use Lua syntax or JavaScript async helpers.

## Render rules

AngelScript Render API calls use the exact scalar/value shapes documented on the AngelScript Render API page. Common Enma wrappers such as `vec2(x, y)` and `color(r, g, b, a)` are wrong in `.as` unless an AngelScript page explicitly documents that value type.

Example text draw shape:

```cpp
draw_text("PCX", 20, 20, 255, 255, 255, 255, get_font20(), TE_SHADOW, 0, 0, 0, 180, 1.0f);
```

## Proc rules

Use `proc_t` and `uint64` addresses. Always release acquired process handles with `deref()` when done or inside `on_unload()`.

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

## Verification commands

```bash
pcx api draw_text --lang angelscript
pcx symbol-check script.as
pcx verify script.as
```
