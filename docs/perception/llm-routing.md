# Perception-First LLM Routing

Use this page before writing any Perception.cx script in this toolkit. The repo
is scoped to **Enma (`.em`) only**. AngelScript (`.as`) is deprecated and is not
part of the AI contract.

## Load Order

For Enma work:

1. Read `docs/perception/readme.md` for the registered Enma surface and official
   conventions.
2. Read `docs/perception/lifecycle-and-routines.md` before writing `main()` or
   callbacks.
3. Read the relevant Enma API page under `docs/perception/*.md` before using any
   host function.
4. Read `knowledge/enma-cheatsheet.md` and
   `.claude/skills/pcx-enma-discipline/SKILL.md` for language gotchas.

For `.as` or AngelScript requests, stop and say this toolkit only supports Enma.

## Non-Negotiable Enma Contract

| Concern | Enma `.em` |
|---|---|
| Entry point | `int64 main()` |
| Repeating work | `register_routine(cast<int64>(fn), data)` |
| Callback shape | `void fn(int64 data)` |
| Logging | `println(...)` |
| Process ref | `proc_t` value, RAII |
| Arrays | `T[]`, `.push()`, `.pop()` |
| Maps | `map<K,V>` for string keys, `imap<V>` for integer keys |
| Casts | `cast<T>(x)` |
| Render positions | `vec2(...)` values |
| Render colors | `color(r,g,b,a)` value |

If a generated answer uses AngelScript lifecycle, handle, array, dictionary, or
raw render-shape idioms, treat it as wrong.

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

1. Use Enma unless the user asks for something outside toolkit scope.
2. If the target language is not Enma, stop and say this toolkit is Enma-only.
3. Load `docs/llms-perception-enma.md` or the load-order pages above.
4. Verify every PCX function name and parameter shape against the matching API
   page, `pcx api <symbol>`, or MCP `api_lookup(symbol, "enma")`.
5. Prefer symbolic offsets and placeholders over version-specific magic values
   unless the user supplied verified offsets.
6. Keep update/scanning work out of render callbacks.
7. Before presenting final code, run `pcx symbol-check <file.em>` or MCP
   `validate_code(code, "enma")` when available.
8. Before copying a generated Markdown answer into a project, run
   `pcx check-answer <answer.md>` to validate fenced Enma code.

When uncertain, answer with the exact docs that must be checked instead of
inventing a plausible API.
