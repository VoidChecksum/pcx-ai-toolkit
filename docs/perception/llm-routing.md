# Perception-First LLM Routing

Use this page before writing any Perception.cx script in this toolkit. The repo
supports **AngelScript (`.as`) and Lua (`.lua`) as current production targets**
and **Enma (`.em`) as the future AOT transition target**. Never mix syntax or
APIs between modes.

## Load Order

For AngelScript work:

1. Read `docs/llms-perception-angelscript.md` or the official AngelScript page
   matching the API surface under `https://docs.perception.cx/perception/angel-script/`.
2. Read `docs/angelscript/quickstart.md` before writing `main()`, callbacks,
   render code, or proc code.
3. Verify every host API and add-on symbol with `pcx api <symbol> --lang
   angelscript` or MCP `api_lookup(symbol, "angelscript")`.
4. Validate final `.as` code with `pcx symbol-check <file.as>`, `pcx verify
   <file.as>`, or MCP `validate_code(code, "angelscript")`.

For Lua work:

1. Read `docs/llms-perception-lua.md` or the official Lua page matching the API
   surface under `https://docs.perception.cx/perception/lua-script/`.
2. Read `docs/lua/quickstart.md` before writing `main()`, callbacks, render
   code, or proc code.
3. Verify every host API and add-on symbol with `pcx api <symbol> --lang lua`
   or MCP `api_lookup(symbol, "lua")`.
4. Validate final `.lua` code with `pcx symbol-check <file.lua>`, `pcx verify
   <file.lua>`, or MCP `validate_code(code, "lua")`.

For Enma migration/AOT work:

1. Read `docs/perception/readme.md` for the registered Enma surface and official
   conventions.
2. Read `docs/perception/lifecycle-and-routines.md` before writing `main()` or
   routines.
3. Read the relevant Enma API page under `docs/perception/*.md` before using any
   host function.
4. Read `knowledge/enma-cheatsheet.md` and
   `.claude/skills/pcx-enma-discipline/SKILL.md` for language gotchas.

## Language Contracts

| Concern | AngelScript `.as` | Lua `.lua` | Enma `.em` |
|---|---|---|---|
| Status | Current production surface | Current production surface | Future AOT transition |
| Entry point | `int main()` | `function main()` | `int64 main()` |
| Repeating work | `register_callback(fn, interval_ms, data_index)` | `register_callback(fn, interval_ms, data_index)` or `on_frame()` | `register_routine(cast<int64>(fn), data)` |
| Callback shape | `void fn(int id, int data_index)` | `function fn(id, data_index)` | `void fn(int64 data)` |
| Logging | `log(...)` | `log(...)` | `println(...)` |
| Process ref | `proc_t` handle; call `deref()` | `process` userdata; call `deref_process(proc)` | `proc_t` value, RAII |
| Arrays | `array<T>` | tables | `T[]`, `.push()`, `.pop()` |
| Maps | `dictionary` | tables | `map<K,V>` / `imap<V>` |
| Render positions | scalar `x, y` arguments unless the AS page says otherwise | scalar `x, y` arguments unless the Lua page says otherwise | `vec2(...)` values |
| Render colors | scalar RGBA arguments unless the AS page says otherwise | scalar RGBA arguments unless the Lua page says otherwise | `color(r,g,b,a)` values |

If generated code mixes AngelScript/Lua lifecycle, containers, or render calls
into Enma, or Enma `vec2`/`color` wrappers into AngelScript/Lua, treat it as wrong.

## Perception Enma Facts From Upstream

The official Perception Enma overview states:

- Enma is Perception's proprietary full-module AOT and JIT-compiled scripting
  language.
- Perception's public Enma docs cover the APIs registered on top of Enma; the
  language itself is documented separately in the upstream Enma docs.
- Colors and positions should be wrapped: `color(255, 255, 255, 255)` and
  `vec2(10.0, 20.0)`.
- Fresh color/vector temporaries each frame are fine because Enma drops them at
  scope exit.
- `float32` literals use the `f` suffix, for example `0.2f`; do not write
  `cast<float32>(0.2)` for a literal.
- `create_*` and `load_*` natives return encrypted `int64` handles. Pass them
  back unchanged into draw, bind, or destroy calls. Do not inspect them.
- The Perception Enma SDK is not public yet.

## Answering Rules For Any LLM

Before producing code:

1. Infer the target language from the user, filename, or explicit `--language`.
   Default to AngelScript for current Perception production scripts; use Lua
   when requested or when the source file is `.lua`; use Enma only when the task
   explicitly asks for Enma or migration prep.
2. Load the matching context pack:
   - AngelScript: `docs/llms-perception-angelscript.md`
   - Lua: `docs/llms-perception-lua.md`
   - Enma: `docs/llms-perception-enma.md`
3. Verify every PCX function name and parameter shape against the matching API
   page, `pcx api <symbol> --lang <language>`, or MCP
   `api_lookup(symbol, "<language>")`.
4. Prefer symbolic offsets and placeholders over version-specific magic values
   unless the user supplied verified offsets.
5. Keep update/scanning work out of render callbacks.
6. Before presenting final code, run `pcx symbol-check <file.as|file.lua|file.em>`
   or MCP `validate_code(code, "<language>")` when available.
7. Before copying a generated Markdown answer into a project, run
   `pcx check-answer <answer.md>` to validate fenced code.

When uncertain, answer with the exact docs that must be checked instead of
inventing a plausible API.
