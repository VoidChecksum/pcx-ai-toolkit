# Workflow Cookbook

Intent-first index for PCX, Perception MCP, RE workflows, task docs, and skills.

## I want to inspect a process

- Start with `docs/tasks/proc-read.md`.
- Plan: `pcx mcp-plan "attach and read typed value" --target game.exe`.
- Live support: `pcx mcp-doctor --url http://127.0.0.1:42069/mcp --target game.exe --deep`.

## I want to find a string xref

- Read `knowledge/mcp-workflows/string-xref.md` and `docs/perception/mcp-workflows.md`.
- Plan: `pcx mcp-plan "find xrefs to PlayerHealth" --target game.exe`.
- Record evidence: `pcx mcp-record --url http://127.0.0.1:42069/mcp --target game.exe --out session.jsonl`.

## I want to create an overlay

- Use `docs/tasks/render-overlay.md`, `docs/tasks/custom-draw.md`, and `docs/perception/overlay-api.md`.
- Validate snippets with `pcx check-answer docs/tasks/render-overlay.md`.

## I want to validate Enma

- Use `docs/perception/mcp-script-bridge.md`.
- Plan: `pcx mcp-plan "validate an Enma script"`.
- Minimal live check: `script/get_context` before `script/validate`.

## I want to recover after a patch

- Use `knowledge/re-workflows/patch-day.md` and `knowledge/offset-methodology.md`.
- Plan: `pcx mcp-plan "patch rollback restore patch" --permissions write_memory`.

## I want to use Source 2

- Use `.claude/skills/engine-source2-mcp/SKILL.md` and `knowledge/mcp-workflows/source2.md`.

## I want to record evidence

- Record: `pcx mcp-record --url http://127.0.0.1:42069/mcp --target game.exe --out session.jsonl`.
- Import: `pcx evidence import-transcript session.jsonl --claim C-001 --out evidence.json`.
- Verify: `pcx evidence --file evidence.json verify`.
