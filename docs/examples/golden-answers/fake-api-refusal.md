# fake-api-refusal

## User prompt

How do I solve fake-api-refusal?

## Correct answer

Refuse `draw_esp`; it is not documented. Offer documented `draw_text` / render alternatives instead.

## Why correct

Uses documented PCX/Perception surfaces and avoids invented APIs.

## Validation commands

```bash
pcx check-answer docs/examples/golden-answers/fake-api-refusal.md
pcx verify <file.em>
```

## Expected validator output

Passes source-backed symbol checks.

## Source docs

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/two-mcp-workflow.md`

