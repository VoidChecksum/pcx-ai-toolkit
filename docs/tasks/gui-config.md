# GUI Config

## Load

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/llm-routing.md`
- `docs/llms-perception-enma.md`

## API lookup symbols

GUI section/widget APIs

## Permissions

GUI context

## Minimal code

```enma
int64 main(){ println("load GUI template, then validate widget symbols with pcx api"); return 1; }
```

## Validate

```bash
pcx check-answer docs/tasks/gui-config.md
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
