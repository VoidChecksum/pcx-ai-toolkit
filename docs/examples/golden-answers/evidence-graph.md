# evidence-graph

## User prompt

How do I solve evidence-graph?

## Correct answer

Import transcript with `pcx evidence import-transcript`, verify with `pcx evidence --file evidence.json verify`, render Mermaid.

## Why correct

Uses documented PCX/Perception surfaces and avoids invented APIs.

## Validation commands

```bash
pcx check-answer docs/examples/golden-answers/evidence-graph.md
pcx verify <file.em>
```

## Expected validator output

Passes source-backed symbol checks.

## Source docs

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/two-mcp-workflow.md`

