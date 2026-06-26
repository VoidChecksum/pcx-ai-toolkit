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

## Remaining follow-ups

### Structured MCP return objects

Problem: MCP handlers still return JSON strings for broad client compatibility.

Fix: migrate FastMCP handlers to structured dict/list returns after verifying target clients accept typed objects.

### Generated addon metadata

Problem: addon import hints are still maintained in code.

Fix: generate addon symbol/import metadata from `https://enma-1.gitbook.io/enma/llms-language.md` and addon pages.

### Release-candidate OS install smoke

Problem: CI matrix builds packages on three OSes, but release jobs still publish from Linux.

Fix: add release-candidate workflow that installs the built artifacts on Linux, Windows, and macOS before tag publication.
