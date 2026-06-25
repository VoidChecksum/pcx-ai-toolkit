---
name: engine-unity-il2cpp-mcp
description: Use for Unity IL2CPP live MCP investigations with GameAssembly and global-metadata evidence.
license: MIT
---

# engine-unity-il2cpp-mcp

Use for Unity IL2CPP live MCP investigations with GameAssembly and global-metadata evidence.

## Required inputs
- target process/module
- task or claim
- permission assumptions
- available Perception MCP tools/capabilities

## Workflow
1. Load `docs/perception/two-mcp-workflow.md`.
2. Load `docs/perception/mcp-workflows.md` and `docs/perception/mcp-safety-policy.md`.
3. If engine-specific, load the matching `knowledge/mcp-workflows/*.md` page.
4. Plan with `pcx mcp-plan` before live calls.
5. Record evidence IDs and cleanup handles.

## Output contract
Every answer must include:
- MCP tools used or planned
- handle lifecycle
- permission assumptions
- evidence IDs
- cleanup step
- validation step
- stop condition

## Trigger/use conditions
Use when the user task needs this skill's named MCP or evidence workflow surface.

## Validation commands
- `pcx mcp-plan "<task>"`
- `pcx mcp-doctor --url <url> --deep` for live Perception MCP support
