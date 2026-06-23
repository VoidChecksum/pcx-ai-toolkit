# Perception-First LLM Routing

Use this page before writing any Perception.cx script in this toolkit. The repo
is scoped to Enma and AngelScript only. The same Perception.cx product exposes
similar capability through both languages, but the bindings are not
interchangeable. A correct answer starts by selecting Enma or AngelScript, then
reading the matching API page.

## Load Order

For `.em` Enma work:

1. Read `docs/perception/readme.md` for the registered Enma surface and official
   conventions.
2. Read `docs/perception/lifecycle-and-routines.md` before writing `main()` or
   callbacks.
3. Read the relevant Enma API page under `docs/perception/*.md` before using any
   host function.
4. Read `knowledge/enma-cheatsheet.md` and
   `.claude/skills/pcx-enma-discipline/SKILL.md` for language gotchas.

For `.as` AngelScript work:

1. Read `docs/perception/angelscript/overview.md` for registered AS add-ons and
   PCX add-ons.
2. Read `docs/perception/angelscript/life-cycle.md` before writing `main()`,
   `register_callback`, or unload logic.
3. Read the relevant AngelScript API page under
   `docs/perception/angelscript/*.md` before using any host function.
4. Read `.claude/skills/pcx-angelscript-discipline/SKILL.md` for AS handle,
   float, array, dictionary, and callback rules.

## Non-Negotiable Binding Split

| Concern | Enma `.em` | AngelScript `.as` |
|---|---|---|
| Entry point | `int64 main()` | `int main()` |
| Repeating work | `register_routine(cast<int64>(fn), data)` | `register_callback(fn, interval, data)` |
| Callback shape | `void fn(int64 data)` | `void fn(int id, int data_index)` |
| Logging | `println(...)` | `log(...)` |
| Process ref | `proc_t` value, RAII | `proc_t@` handle, explicit `deref()` |
| Arrays | `T[]`, `.push()`, `.pop()` | `array<T>`, `.insertLast()`, `.removeLast()` |
| Maps | `map<K,V>` | `dictionary` |
| Casts | `cast<T>(x)` | constructor/cast syntax from AS docs |
| Render positions | `vec2(...)` values | raw float parameters unless page says otherwise |
| Render colors | `color(r,g,b,a)` value | integer RGBA parameters unless page says otherwise |

If code crosses a column boundary, treat it as wrong until the target language's
API page proves otherwise.

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

## Perception AngelScript Facts From Upstream

The official Perception AngelScript overview states:

- PCX AngelScript is a lightweight scripting layer for UI, rendering, memory
  analysis, and interaction in Perception.cx.
- Core add-ons include `string`, `array`, `dictionary`, `math`, `any`, `grid`,
  and script helper functions.
- PCX add-ons include Unicorn, atomic types, render, input, host utilities,
  proc, mutex, GUI, system, net, filesystem, extended math, engine-specific
  helpers, JSON, utilities, Zydis encoder, intrinsics, sound, bit reinterpret
  helpers, and the CS2 extended API.

## Answering Rules For Any LLM

Before producing code:

1. Name the target language from the file extension or user request.
2. If the target language is not Enma or AngelScript, stop and say this toolkit
   is scoped to Enma + AngelScript.
3. Load that language's context pack or the load-order pages above.
4. Verify every PCX function name and parameter shape against the matching API
   page, `pcx api <symbol> --lang enma|angelscript`, or MCP
   `api_lookup(symbol, language)`. Use the same lookup for Enma/AngelScript
   language and add-on helpers before assuming a stdlib call exists.
5. Prefer symbolic offsets and placeholders over version-specific magic values
   unless the user supplied verified offsets.
6. Keep update/scanning work out of render callbacks.
7. If a function name only exists in another language's column, do not use it.
8. Before presenting final code, run `pcx symbol-check <file>` or MCP
   `validate_code(code, language)` when available.
9. Before copying a generated Markdown answer into a project, run
   `pcx check-answer <answer.md>` to validate fenced Enma/AngelScript code.

When uncertain, answer with the exact docs that must be checked instead of
inventing a plausible API.
