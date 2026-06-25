# Weak Local Model Workflow

Use this when the model is small, quantized, weak at API recall, or prone to filling gaps.

## Rules

1. Choose a template first; do not create a free-form project layout.
2. Load only:
   - `docs/AI_AGENT_OPERATING_MANUAL.md`
   - `docs/perception/llm-routing.md`
   - `docs/llms-perception-enma.md`
3. Use only symbols returned by `pcx api <symbol>` or MCP `api_lookup`.
4. Output one file at a time.
5. Validate every code block before writing the next file.
6. Do not infer offsets, structures, signatures, permissions, or helper APIs.
7. Mark offsets/placeholders as unverified until evidence exists.

## Command

```bash
pcx plan --weak-model "make a GUI config"
pcx create --wizard
pcx verify file.em
pcx verify-project ./project
```

## Prompt

```text
You are a weak/local model. Do not invent Perception APIs.
Use Enma only. Choose a template first. Use only symbols confirmed by pcx api or api_lookup.
Write one file at a time and validate each code block before continuing.
If a symbol, offset, permission, or helper is not source-proven, stop and ask for lookup/evidence.
```
