# Custom Draw

## Load

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/llm-routing.md`
- `docs/llms-perception-enma.md`

## API lookup symbols

custom draw/render resource APIs

## Permissions

render/routine context

## Minimal code

```enma
int64 main(){ println("lookup custom draw symbols and validate signatures before resource creation"); return 1; }
```

## Validate

```bash
pcx check-answer docs/tasks/custom-draw.md
pcx verify <file.em>
```

## Common hallucinations

- ImGui-style helpers
- generic C++/Lua/JavaScript helpers
- undocumented game-specific wrappers
- unchecked permission or sentinel failures

## Source links

- `docs/perception/llm-routing.md`
- `knowledge/pcx-api-index.json`
- `docs/COVERAGE.md`
