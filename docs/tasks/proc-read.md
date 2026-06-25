# Process Read

## Load

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/llm-routing.md`
- `docs/llms-perception-enma.md`

## API lookup symbols

proc_t and typed read APIs

## Permissions

process_memory_read

## Minimal code

```enma
int64 main(){ println("open proc_t with verified target and read only evidence-backed offsets"); return 1; }
```

## Validate

```bash
pcx check-answer docs/tasks/proc-read.md
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
