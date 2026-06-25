---
name: pcx-knowledge-index
description: Route AI tools to the Rust-only pcx-ai-toolkit knowledge surfaces.
license: MIT
---

# PCX Knowledge Index

Use this before choosing context for Perception.cx Enma work.

## Surfaces

| Surface | Use |
|---|---|
| `docs/llms.txt` | First-touch compact index |
| `docs/AI_AGENT_OPERATING_MANUAL.md` | Agent workflow contract |
| `docs/perception/llm-routing.md` | Enma-only routing rules |
| `knowledge/pcx-api-index.json` | Exact API signatures |
| `pcx-rs mcp` | MCP-aware lookup, validation, scaffolding |

## Load Order

1. Read `docs/AI_AGENT_OPERATING_MANUAL.md`.
2. Read `docs/perception/llm-routing.md`.
3. Read the relevant `docs/perception/*.md` API page.
4. Query `pcx-rs api <symbol>` before trusting host API names.
5. Validate code with `pcx-rs symbol-check` or MCP `validate_code`.

## Rust-Only Rule

Do not route to removed compatibility scripts. The toolkit implementation surface is `pcx-rs` and native binaries under `tools/bin/`.
