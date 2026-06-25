# pattern-to-function-mcp

## User prompt

How do I solve pattern-to-function-mcp?

## Correct answer

Plan with `pcx mcp-plan`, acquire a fresh handle, record transcript evidence, then cleanup with `process/dereference`.

## Why correct

Uses documented PCX/Perception surfaces and avoids invented APIs.

## Validation commands

```bash
pcx check-answer docs/examples/golden-answers/pattern-to-function-mcp.md
pcx verify <file.em>
```

## Expected validator output

Passes source-backed symbol checks.

## Source docs

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/two-mcp-workflow.md`

