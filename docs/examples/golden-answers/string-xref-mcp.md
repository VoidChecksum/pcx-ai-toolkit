# string-xref-mcp

## User prompt

How do I solve string-xref-mcp?

## Correct answer

Plan with `pcx mcp-plan`, acquire a fresh handle, record transcript evidence, then cleanup with `process/dereference`.

## Why correct

Uses documented PCX/Perception surfaces and avoids invented APIs.

## Validation commands

```bash
pcx check-answer docs/examples/golden-answers/string-xref-mcp.md
pcx verify <file.em>
```

## Expected validator output

Passes source-backed symbol checks.

## Source docs

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/two-mcp-workflow.md`

