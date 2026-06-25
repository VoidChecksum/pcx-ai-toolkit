# Pattern Scan

## Load

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/llm-routing.md`
- `docs/llms-perception-enma.md`

## API lookup symbols

pattern scan APIs from pcx api

## Permissions

process_memory_read

## Minimal code

```enma
int64 main(){ println("lookup exact pattern scan API before use; keep pattern evidence in evidence log"); return 1; }
```

## Validate

```bash
pcx check-answer docs/tasks/pattern-scan.md
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
