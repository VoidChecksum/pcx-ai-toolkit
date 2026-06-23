# AI Agent Operating Manual

This is the shortest safe workflow for any LLM or MCP-aware agent working with
Perception.cx scripts in this repo. It exists to prevent hallucinated PCX APIs,
wrong-language bindings, and stale context loading.

## Non-Negotiable Scope

The supported script languages are:

- Enma (`.em`)
- AngelScript (`.as`)

If a task asks for another PCX scripting language, stop and state that this
toolkit is scoped to Enma and AngelScript.

## Load Order

1. Read `docs/perception/llm-routing.md`.
2. Determine the target language from file extension or user request.
3. Load the smallest context:
   - Enma: `docs/llms-perception-enma.md`
   - AngelScript: `docs/llms-perception-angelscript.md`
   - Unknown/mixed: call MCP `recommend_context(task, language)` first.
4. Load the relevant skill:
   - Game cheat work: `game-cheat-script-master`
   - Enma syntax/binding work: `pcx-enma-discipline`
   - AngelScript syntax/binding work: `pcx-angelscript-discipline`
   - MCP calls: `mcp-tool-routing`
   - Offset/RE work: `pcx-re-discipline` and `re-evidence-log`
5. Verify every host API symbol with `pcx api` or MCP `api_lookup`.
6. Validate generated code with `pcx symbol-check`, MCP `validate_code`, or MCP
   `validate_answer`.

For forum, changelog, overlay, client, or migration questions, load
`knowledge/perception-forum-insights.md` after the official docs. It is
secondary context only; it must not override exact API signatures.

## MCP-First Workflow

Use this sequence in MCP-aware clients:

```text
overview()
recommend_context(task, language)
get_skill(name)
get_file(path)
api_lookup(symbol, language)
validate_code(code, language)
validate_answer(markdown)
```

Only use broad `search(query)` after the recommended context does not answer a
question.

## CLI-First Workflow

Use this sequence in terminal-based workflows:

```bash
pcx api draw_text --lang enma
pcx symbol-check script.em
pcx verify script.as
pcx check-answer answer.md
python3 tools/check-llm-contract.py
```

## Answer Contract

Every generated answer that contains code should satisfy these rules:

- State the target language.
- Do not mix Enma and AngelScript lifecycle calls.
- Do not invent API names.
- Include imports required for Enma value types such as `vec2` and `color`.
- Keep scanning/update work out of render callbacks.
- Mark offsets as placeholders unless supplied and verified by the user.
- Run or recommend the relevant validator before final use.

## Failure Policy

When the docs or API index do not prove a symbol exists, do not guess. Say which
doc or lookup must be checked next.
