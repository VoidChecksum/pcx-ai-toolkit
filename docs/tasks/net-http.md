# HTTP Request

## Load

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/llm-routing.md`
- `docs/llms-perception-enma.md`

## API lookup symbols

net HTTP APIs

## Permissions

network_access

## Minimal code

```enma
int64 main(){ println("lookup exact HTTP API, check status=0 and parse JSON explicitly"); return 1; }
```

## Validate

```bash
pcx check-answer docs/tasks/net-http.md
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
