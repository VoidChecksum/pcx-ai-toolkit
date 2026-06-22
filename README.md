<div align="center">

<img src="assets/perception-banner.png" alt="Perception.cx" width="600">

<br><br>

# pcx-ai-toolkit

### AI Toolkit for Perception.cx Scripting

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.docs&label=Docs&suffix=%20pages&color=brightgreen)](#documentation)
[![Doc Lines](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.doc_lines&label=Doc%20Lines&color=brightgreen)](#documentation)
[![Languages](https://img.shields.io/badge/Languages-Enma%20%7C%20AngelScript%20%7C%20Lua-orange.svg)](#)
[![MCP Tools](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.mcp_tools&label=MCP%20Tools&color=purple)](#perception-mcp-server)
[![Skills](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.skills&label=AI%20Skills&color=yellow)](#ai-skills)
[![VSIX](https://img.shields.io/badge/VS%20Code-VSIX%20in%20Releases-007ACC.svg)](https://github.com/VoidChecksum/pcx-ai-toolkit/releases)
[![CI](https://github.com/VoidChecksum/pcx-ai-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/VoidChecksum/pcx-ai-toolkit/actions/workflows/ci.yml)

**Anchor LLMs to the live Perception.cx API docs.** This toolkit bundles the Enma, AngelScript, and Lua documentation surfaces for Perception.cx, anti-hallucination rules, an API symbol index sourced only from the two upstream roots, and a unified `pcx` CLI for validation.

</div>

---

## Quick Start

```bash
git clone --recursive https://github.com/VoidChecksum/pcx-ai-toolkit.git
cd pcx-ai-toolkit
./setup.sh
```

> **Requirements:** [Node.js 18+](https://nodejs.org/) · [Git](https://git-scm.com/)

Drop the rules into your project so the AI reads the upstream docs before writing code:

```bash
cp rules/CLAUDE.md /path/to/your/pcx-project/
```

---

## What's Inside

### Documentation

- **Enma language reference** — `docs/enma/`
- **AngelScript language reference** — `docs/angelscript-lang/`
- **Lua language reference** — `docs/lua-lang/`
- **Perception.cx API docs** — `docs/perception/` for Enma, AngelScript, and Lua surfaces
- **Indexed bundles** — `docs/llms.txt` + generated context packs

See [`docs/INDEX.md`](docs/INDEX.md) for the full file list.

### Anti-Hallucination Tooling

- `knowledge/pcx-api-index.json` — generated from the two live upstream roots:
  - `https://docs.perception.cx/perception/enma/overview`
  - `https://docs.perception.cx/perception/angel-script/overview`
- `tools/symbol-check.py` — flags unknown calls, unknown types, and missing imports
- `tools/build-api-index.py` — rebuilds the index from upstream
- `pcx verify <file>` — lint + symbol-check in one pass

### AI Skills

Claude Code / OMC skills under `.claude/skills/`:

- `game-cheat-script-master` — mandatory entry point for PCX scripting requests
- `game-hacking-pcx` — doc index, API rules, scaffolds
- `game-cheat-guidelines` — the 12 behavioral rules
- `pcx-enma-discipline`, `pcx-angelscript-discipline`, `pcx-lua-discipline` — language-specific rules
- `pcx-coding-discipline`, `pcx-knowledge-index`, `pcx-patch-day-playbook`, `pcx-bloat-audit`, `pcx-bloat-review`, `pcx-debug-overlay`, `pcx-defer-ledger`, `mcp-tool-routing`, `pcx-perf-budget`, `pcx-streamproof`

### Editor Support

- **Enma LSP** — `lsp/enma-lsp/`
- **AngelScript+PCX LSP** — `lsp/angel-lsp-pcx/`
- VS Code and Visual Studio extensions built from the LSPs (see Releases)

### MCP Server

- `mcp/pcx-knowledge-mcp/` — `search`, `get_file`, `list_files`, `overview`, `validate_code`

---

## Unified CLI (`pcx`)

```bash
pcx lint <script.em>            # lint Enma against the 12 guidelines
pcx symbol-check <file>         # catch unknown symbols / missing imports
pcx verify <file>               # lint + symbol-check
pcx build-api-index             # regenerate knowledge/pcx-api-index.json
pcx check-drift                 # check doc drift against live upstream
pcx check-mcp                   # verify MCP config sync
pcx update                      # pull latest, rebuild LSPs, refresh skills
```

---

## Sourcing Policy

The only authoritative API sources are:

1. `https://docs.perception.cx/perception/enma/overview`
2. `https://docs.perception.cx/perception/angel-script/overview`

Every PCX API symbol used in generated code must be traceable to one of those two trees. Local docs are a drift-checked mirror; when in doubt, trust upstream. See [`knowledge/pcx-doc-roots.md`](knowledge/pcx-doc-roots.md).

---

## Templates

- [`templates/hello-world.em`](templates/hello-world.em) — minimal upstream-clean Enma script

All templates are validated with `pcx symbol-check` in CI.

---

## License

MIT — see [LICENSE](LICENSE).
