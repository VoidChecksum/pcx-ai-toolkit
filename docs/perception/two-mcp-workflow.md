# Two-MCP Workflow

PCX has two MCP surfaces. Use both; do not make either one do the other's job.

| Surface | Purpose | Best for | Not for |
|---|---|---|---|
| pcx knowledge MCP | Static docs, API lookup, validation, templates | planning, symbol checks, generated-answer validation | live memory/process state |
| Perception runtime MCP | Live process, memory, modules, disassembly, script compiler bridge | RE evidence, string xrefs, signatures, real compile validation | inventing docs or API names |

## Default loop

1. `recommend_context(task, "enma")` from pcx knowledge MCP.
2. `get_file` / `search_docs` for the relevant docs.
3. `api_lookup(symbol, "enma")` before using uncertain API names.
4. `validate_code` or `validate_answer` on generated source.
5. Perception MCP `script/get_context` once per runtime session if generating Enma for the live app.
6. Perception MCP `process/reference_by_name` or `process/reference_by_pid` for live target evidence.
7. Perception MCP process tools for reads/scans/disassembly.
8. Perception MCP `script/validate` for real compiler validation.
9. Perception MCP `process/dereference` or `process/cleanup_references` before ending.

## MCP vs Enma decision table

| Task | Prefer Enma script | Prefer Perception MCP |
|---|---:|---:|
| Long-lived overlay | yes | no |
| GUI/menu | yes | no |
| Read value every frame | yes | no |
| One-time memory inspection | no | yes |
| Search process for string | maybe | yes |
| Generate signature from live binary | no | yes |
| Validate generated code | pcx + `script/validate` | yes |
| Agent-driven RE investigation | no | yes |

## Cleanup rule

Every target-scoped Perception MCP flow ends with `process/dereference(handle)` for one target or `process/cleanup_references()` for session reset. Handles are per-connection hex strings; never reuse one across clients.
