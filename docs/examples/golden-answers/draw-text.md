# draw-text

## User prompt

How do I solve draw-text?

## Correct answer

Use `pcx api`, documented symbols, and validation before finalizing.

## Why correct

Uses documented PCX/Perception surfaces and avoids invented APIs.

## Validation commands

```bash
pcx check-answer docs/examples/golden-answers/draw-text.md
pcx verify <file.em>
```

## Expected validator output

Passes source-backed symbol checks.

## Source docs

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/two-mcp-workflow.md`

