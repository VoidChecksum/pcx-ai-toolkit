# AI Agent Operating Manual

This is the shortest safe workflow for any LLM or MCP-aware agent working with
Perception.cx scripts in this repo. It exists to prevent hallucinated PCX APIs,
unsupported language bindings, and stale context loading.

## Non-Negotiable Scope

The supported script language is **Enma (`.em`)**.

AngelScript (`.as`), Lua, and other historical PCX scripting surfaces are outside
this toolkit's AI contract. If a task asks for them, stop and state that this
toolkit is Enma-only.

## Load Order

1. Read `docs/perception/llm-routing.md`.
2. Confirm the target is Enma (`.em`).
3. Load `docs/enma/llms-language.md` plus the relevant `docs/perception/*.md` API page.
4. Load the relevant skill:
   - Game cheat work: `game-cheat-script-master`
   - Enma syntax/binding work: `pcx-enma-discipline`
   - MCP calls: `mcp-tool-routing`
   - Offset/RE work: `pcx-re-discipline` and `re-evidence-log`
5. Verify every host API and language/add-on symbol with `pcx api` or MCP
   `api_lookup`.
6. Validate generated code with `pcx symbol-check`, MCP `validate_code`, or MCP
   `validate_answer`.

For forum, changelog, overlay, client, or migration questions, load
`knowledge/perception-forum-insights.md` after the official docs. It is
secondary context only; it must not override exact API signatures.

## MCP-First Workflow

Use this sequence in MCP-aware clients:

```text
overview()
recommend_context(task, "enma")
get_skill(name)
get_file(path)
api_lookup(symbol, "enma")
validate_code(code, "enma")
validate_answer(markdown)
```

Only use broad `search(query)` after the recommended context does not answer a
question.

## CLI-First Workflow

Use this sequence in terminal-based workflows:

```bash
pcx-rs api draw_text
pcx-rs api atan2
pcx-rs symbol-check script.em
pcx-rs verify script.em
pcx-rs check-answer answer.md
pcx-rs mcp-schema --json
```

## Answer Contract

Every generated answer that contains code should satisfy these rules:

- State the target language: Enma.
- Do not use AngelScript lifecycle, handles, arrays, dictionaries, or render shapes.
- Do not invent API names.
- Include imports required for Enma value types such as `vec2` and `color`.
- Keep scanning/update work out of render callbacks.
- Mark offsets as placeholders unless supplied and verified by the user.
- Run or recommend the relevant validator before final use.

## Failure Policy

When the docs or API index do not prove a symbol exists, do not guess. Say which
doc or lookup must be checked next.
