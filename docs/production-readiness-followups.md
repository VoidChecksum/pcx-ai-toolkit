# Production-readiness follow-ups

This file tracks large production-readiness work and whether it is done.

## Completed in this hardening pass

### LSP-backed validation

Status: done. `pcx lsp-check <file.em>` talks to the Enma language server over stdio, and `pcx verify` runs it when a built server or `PCX_LSP_COMMAND` is available.

### Package install matrix

Status: done. CI package smoke now runs on Linux, Windows, and macOS.

### Enma addon coverage

Status: done for documented import-gating gaps. Import hints now cover `variant`, `regex`, `hash_set`, `sorted_map`, and `list` in addition to the older addon set.

### live Perception MCP integration

Status: done as an optional test harness. Set `PCX_MCP_URL` to run live tests for `script/get_context` and `script/validate`.

### Typed MCP schemas

Status: initial schema surface done. Published schemas cover `api_lookup`, `validate_code`, `validation-finding`, and `scaffold_project`/plan responses.

### Search quality

Status: initial SQLite FTS5 backend done. The knowledge MCP uses in-memory FTS when available and falls back to keyword overlap.


### Structured MCP return objects

Status: done with compatibility escape hatch. MCP tools now return dict/list payloads by default; set `PCX_MCP_JSON_STRINGS=1` for legacy clients that still require serialized JSON strings.

### Generated addon metadata

Status: done. `tools/build-enma-addon-metadata.py` generates `knowledge/enma-addon-imports.json`, and validators load that file before checking missing imports.

### Release-candidate OS install smoke

Status: done. Release packages now run a Linux/Windows/macOS install smoke before the GitHub Release job.

### MCP response schemas

Status: extended. Published schemas now cover search, context recommendation, finding explanation, and generated script plans.

### CLI and MCP reference docs

Status: done. See `docs/cli-reference.md` and `docs/mcp-tool-reference.md`.

