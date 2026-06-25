---
name: perception-mcp-session
description: Use for live Perception MCP sessions: acquiring handles, making calls, retrying stale handles once, recording transcripts, and cleaning up.
---

# perception-mcp-session

Use for live Perception MCP sessions: acquiring handles, making calls, retrying stale handles once, recording transcripts, and cleaning up.

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
