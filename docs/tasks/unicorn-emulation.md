# Unicorn Emulation

## Load

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/llm-routing.md`
- `docs/llms-perception-enma.md`

## API lookup symbols

Unicorn APIs

## Permissions

no special permission

## Minimal code

```enma
int64 main(){ println("lookup unicorn CPU/memory APIs and validate emulation error paths"); return 1; }
```

## Validate

```bash
pcx check-answer docs/tasks/unicorn-emulation.md
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
