# Filesystem Config

## Load

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/llm-routing.md`
- `docs/llms-perception-enma.md`

## API lookup symbols

fs_file_exists, fs_read_file, fs_write_file

## Permissions

file_system_access

## Minimal code

```enma
import "file";
int64 main(){ string path="config.json"; if (!fs_file_exists(path)){ println("missing config"); return 1; } string body=fs_read_file(path); return 1; }
```

## Validate

```bash
pcx check-answer docs/tasks/filesystem-config.md
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
