<div align="center">

<img src="assets/perception-banner.png" alt="Perception.cx" width="720">

# pcx-ai-toolkit

### Source-Grounded Enma + AngelScript AI Toolkit for Perception.cx

[![CI](https://github.com/VoidChecksum/pcx-ai-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/VoidChecksum/pcx-ai-toolkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Scope](https://img.shields.io/badge/Scope-Enma%20%2B%20AngelScript-f97316.svg)](#language-scope)
[![Docs](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.docs&label=Docs&suffix=%20pages&color=22c55e)](#knowledge-surface)
[![Doc Lines](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.doc_lines&label=Doc%20Lines&color=22c55e)](#knowledge-surface)
[![Knowledge](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.knowledge&label=Knowledge&color=14b8a6)](#knowledge-surface)
[![MCP Tools](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.mcp_tools&label=MCP%20Tools&color=0ea5e9)](#mcp-integration)
[![AI Skills](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.skills&label=AI%20Skills&color=eab308)](#ai-agent-stack)

**Make any LLM write Perception.cx scripts from verified Enma and AngelScript sources instead of hallucinated APIs.**

`llms.txt` context packs · official-doc mirrors · forum-derived changelog context · source-backed API lookup · answer validation · MCP search · Enma/AngelScript LSP packages

[Start Here](#ai-start-here) · [Anti-Hallucination](#anti-hallucination-pipeline) · [Knowledge](#knowledge-surface) · [MCP](#mcp-integration) · [Editors](#editor--vsix-packages) · [Safety](#safety-and-scope)

</div>

---

## AI Start Here

This repository is designed as a boot sequence for AI agents. If an LLM follows
this order, it should know the supported Perception Enma and AngelScript surface
before writing code.

```text
1. Read docs/AI_AGENT_OPERATING_MANUAL.md
2. Read docs/perception/llm-routing.md
3. Select Enma (.em) or AngelScript (.as)
4. Load the matching context pack and skill
5. Verify every API symbol with pcx api or MCP api_lookup
6. Validate code with pcx symbol-check, pcx verify, or MCP validate_answer
```

| Must Load | Why |
|---|---|
| [docs/AI_AGENT_OPERATING_MANUAL.md](docs/AI_AGENT_OPERATING_MANUAL.md) | Shortest safe workflow for LLM/MCP agents |
| [docs/perception/llm-routing.md](docs/perception/llm-routing.md) | Prevents Enma/AngelScript binding mixups |
| [docs/llms-perception-enma.md](docs/llms-perception-enma.md) | Single-file Enma + PCX context pack |
| [docs/llms-perception-angelscript.md](docs/llms-perception-angelscript.md) | Single-file AngelScript + PCX context pack |
| [knowledge/pcx-api-index.json](knowledge/pcx-api-index.json) | Exact source-backed API signatures |
| [knowledge/perception-forum-insights.md](knowledge/perception-forum-insights.md) | Secondary forum/changelog/overlay context, never an API contract |

Recommended model instruction:

```text
Before writing Perception code, load docs/AI_AGENT_OPERATING_MANUAL.md and docs/perception/llm-routing.md.
Use Enma docs for .em and AngelScript docs for .as.
Verify every Perception API symbol with pcx api or MCP api_lookup.
Validate the final code or Markdown answer before returning it.
If the docs/API index do not prove a symbol exists, say so instead of guessing.
```

---

## Why This Exists

LLMs usually do not know Perception.cx, Enma, or the exact AngelScript bindings.
They invent functions, mix lifecycles, copy generic game-hacking patterns, and
produce snippets that look plausible but do not compile in PCX.

| Failure Mode | Toolkit Countermeasure |
|---|---|
| Invented API names like `draw_esp()` | `pcx api`, MCP `api_lookup`, and `knowledge/pcx-api-index.json` |
| Enma code inside `.as`, or AS code inside `.em` | `docs/perception/llm-routing.md` and language-specific validators |
| Stale context from old docs | generated `llms-*` bundles, provenance, and drift checks |
| Long sessions lose critical rules | MCP `recommend_context`, `get_skill`, `get_file`, and `validate_answer` |
| Forum/changelog facts get treated as signatures | `knowledge/perception-forum-insights.md` marks them secondary |

---

## Language Scope

This toolkit is intentionally scoped to **Perception-supported Enma and
AngelScript**. Other historical or unsupported scripting surfaces are excluded
from the AI contract.

| Area | Enma `.em` | AngelScript `.as` |
|---|---|---|
| Entry point | `int64 main()` | `int main()` |
| Repeating work | `register_routine(cast<int64>(fn), data)` | `register_callback(fn, interval, data)` |
| Logging | `println(...)` | `log(...)` |
| Process handle | `proc_t` value, RAII | `proc_t@` handle, explicit cleanup patterns |
| Containers | `T[]`, `map<K,V>` | `array<T>`, `dictionary` |
| Imports/types | Enma imports such as `vec`, `color` where needed | AngelScript add-ons and PCX binding docs |

The routing rule is simple: `.em` uses Enma docs and Enma lifecycle; `.as` uses
AngelScript docs and AngelScript lifecycle. Never blend them without explicit
source proof.

---

## Quick Start

```bash
git clone --recursive https://github.com/VoidChecksum/pcx-ai-toolkit.git
cd pcx-ai-toolkit
./setup.sh
```

Windows PowerShell:

```powershell
git clone --recursive https://github.com/VoidChecksum/pcx-ai-toolkit.git
cd pcx-ai-toolkit
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Copy a rules file into a PCX script project:

```bash
cp rules/CLAUDE.md /path/to/your/pcx-project/
```

Requirements: Git, Python 3.10+, Node.js 18+. Git submodules are required for
LSP and `.vsix` packaging.

---

## Anti-Hallucination Pipeline

Use these checks before trusting generated code.

```bash
# Verify an exact symbol and get official source URLs.
pcx api draw_text --lang enma
pcx api register_callback --lang angelscript

# Validate scripts.
pcx symbol-check my_script.em
pcx verify my_script.as

# Validate fenced Enma/AngelScript blocks in an LLM Markdown answer.
pcx check-answer answer.md
```

MCP-aware clients should use this sequence:

```text
overview()
recommend_context(task, language)
get_skill(name)
get_file(path)
api_lookup(symbol, language)
validate_code(code, language)
validate_answer(markdown)
```

| MCP Tool | Purpose |
|---|---|
| `recommend_context(task, language)` | Smallest useful skill/doc/tool load plan |
| `list_skills()` / `get_skill(name)` | First-class access to bundled AI skills |
| `api_lookup(symbol, language)` | Exact symbol lookup with signatures, source URLs, and suggestions |
| `validate_code(code, language)` | Detects unknown calls, wrong-language symbols, missing imports, unknown types |
| `validate_answer(answer)` | Validates all fenced Enma/AngelScript code blocks in a response |
| `search(query)` / `get_file(path)` | Search-then-fetch corpus access without guessing paths |

Shared grounding logic lives in
[tools/lib/pcx_grounding.py](tools/lib/pcx_grounding.py).

---

## Knowledge Surface

Current generated corpus:

| Docs | Doc Lines | Skills | Knowledge | Templates | Tools | MCP Tools | Engine Guides |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 124 | 32,183 | 25 | 26 | 30 | 36 | 59 | 5 |

| Surface | Path | Best For |
|---|---|---|
| LLM entry index | [docs/llms.txt](docs/llms.txt) | Auto-fetch tools and first-touch sessions |
| Full context pack | [docs/llms-full.txt](docs/llms-full.txt) | One large preload for both supported languages |
| Enma context pack | [docs/llms-perception-enma.md](docs/llms-perception-enma.md) | Enma-only sessions |
| AngelScript context pack | [docs/llms-perception-angelscript.md](docs/llms-perception-angelscript.md) | AngelScript-only sessions |
| Skills bundle | [docs/llms-skills.md](docs/llms-skills.md) | Agent behavior, routing, and workflow rules |
| Knowledge bundle | [docs/llms-knowledge.md](docs/llms-knowledge.md) | RE/game scripting references and forum-derived context |
| Dynamic MCP | [mcp/pcx-knowledge-mcp](mcp/pcx-knowledge-mcp) | Long sessions, lazy loading, source lookup, validation |

High-value knowledge files:

| File | Use |
|---|---|
| [knowledge/pcx-api-cheatsheet.md](knowledge/pcx-api-cheatsheet.md) | PCX APIs at a glance |
| [knowledge/pcx-api-index.json](knowledge/pcx-api-index.json) | Exact machine-readable API oracle |
| [knowledge/common-patterns.md](knowledge/common-patterns.md) | Working Enma patterns |
| [knowledge/custom-draw-patterns.md](knowledge/custom-draw-patterns.md) | GPU/custom draw examples |
| [knowledge/pcx-version-matrix.md](knowledge/pcx-version-matrix.md) | Version and changelog availability matrix |
| [knowledge/perception-forum-insights.md](knowledge/perception-forum-insights.md) | Forum-derived Enma rollout, overlay, IDE, analyzer, changelog context |

Regenerate and verify generated knowledge:

```bash
python3 tools/build-counts.py
python3 tools/build-llms-index.py
python3 tools/build-provenance.py
python3 tools/check-llm-contract.py
python3 tools/check-skill-contract.py
```

---

## PCX CLI

`pcx` is the local command surface for setup, validation, scaffolding, and drift
checks.

```bash
pcx setup
pcx update
pcx doctor
pcx api draw_text --lang enma
pcx symbol-check file.em
pcx verify file.as
pcx check-answer answer.md
pcx new cheat-skeleton-em ./my-enma-script
pcx new cheat-skeleton-as ./my-as-script
```

| Tool | Purpose |
|---|---|
| [tools/api-lookup.py](tools/api-lookup.py) | Exact API oracle |
| [tools/symbol-check.py](tools/symbol-check.py) | Script-level source-grounded validation |
| [tools/check-llm-answer.py](tools/check-llm-answer.py) | Markdown answer code-block validation |
| [tools/build-api-index.py](tools/build-api-index.py) | Rebuild source-backed API index from docs |
| [tools/check-doc-drift.py](tools/check-doc-drift.py) | Compare local docs against upstream |
| [tools/check-skill-contract.py](tools/check-skill-contract.py) | Reject stale/unsupported AI-skill contracts |
| [tools/check-mcp-config.py](tools/check-mcp-config.py) | Keep runtime MCP config aligned with docs |

---

## AI Agent Stack

The repo ships rules and skills for Claude Code, Cursor, Cline, Copilot,
Windsurf, and generic `AGENTS.md` workflows.

| Layer | Files |
|---|---|
| Global rules | [.clinerules](.clinerules), [.cursorrules](.cursorrules), [.windsurfrules](.windsurfrules), [.github/copilot-instructions.md](.github/copilot-instructions.md) |
| Drop-in rules | [rules/](rules/) |
| Claude skills | [.claude/skills/](.claude/skills/) |
| Agent manual | [docs/AI_AGENT_OPERATING_MANUAL.md](docs/AI_AGENT_OPERATING_MANUAL.md) |
| Routing contract | [docs/perception/llm-routing.md](docs/perception/llm-routing.md) |
| Knowledge MCP | [mcp/pcx-knowledge-mcp/](mcp/pcx-knowledge-mcp/) |

Core skills for PCX work:

| Skill | Use |
|---|---|
| `pcx-enma-discipline` | Enma syntax, lifecycle, imports, and binding discipline |
| `pcx-angelscript-discipline` | AngelScript lifecycle and PCX binding discipline |
| `game-cheat-script-master` | End-to-end script architecture patterns |
| `game-cheat-guidelines` | Behavioral guardrails and anti-hallucination rules |
| `pcx-knowledge-index` | Which docs/knowledge files to load |
| `mcp-tool-routing` | When and how to call MCP tools |

---

## Editor & VSIX Packages

### VS Code

Prebuilt VS Code extension packages are stored in the LSP submodules:

| Package | Path | Language |
|---|---|---|
| Enma Language | `lsp/enma-lsp/enma-language-1.1.22.vsix` | `.em`, `.em.predefined`, `.emb` |
| AngelScript for Perception | `lsp/angel-lsp-pcx/angel-lsp-0.4.1.vsix` | `.as`, `.as.predefined` |

Build locally:

```bash
./tools/package-vsix.sh
```

Manual packaging:

```bash
cd lsp/enma-lsp
npm install
npm run compile
npm run package

cd ../angel-lsp-pcx
npm install
npm run compile
npx vsce package
```

### Visual Studio 2022

Visual Studio packages live under [visualstudio/](visualstudio/). They require
Windows, MSBuild, and the Visual Studio extension development workload.

```powershell
msbuild visualstudio\EnmaVS\EnmaVS.csproj /p:Configuration=Release /restore
msbuild visualstudio\AngelScriptVS\AngelScriptVS.csproj /p:Configuration=Release /restore
```

---

## Templates

| Template | Language | Use |
|---|---|---|
| `hello-world` | Enma | Minimal lifecycle sanity check |
| `cheat-skeleton-em` | Enma | Modular ESP/aim/menu/triggerbot scaffold |
| `cheat-skeleton-as` | AngelScript | Equivalent AS scaffold |
| `full-project` | Enma | Multi-file Enma project layout |
| `full-project-as` | AngelScript | Multi-file AS project layout |
| `overlay-basic`, `minimap`, `aimbot-skeleton` | Enma | Focused examples |

Create one:

```bash
pcx new cheat-skeleton-em ./pcx-enma-script
pcx new cheat-skeleton-as ./pcx-as-script
```

---

## MCP Integration

Two MCP surfaces matter:

| MCP | Purpose |
|---|---|
| [mcp/pcx-knowledge-mcp](mcp/pcx-knowledge-mcp) | Local searchable corpus for docs, skills, templates, API lookup, and validation |
| [mcp/perception-mcp-config.json](mcp/perception-mcp-config.json) | Runtime Perception MCP config with 59 live-process tools |

Install the knowledge server:

```bash
pip install -e mcp/pcx-knowledge-mcp/
pcx-knowledge-mcp --help
```

Client setup:

| Client | Guide |
|---|---|
| Claude Code | [mcp/claude-code-setup.md](mcp/claude-code-setup.md) |
| Cursor | [mcp/cursor-setup.md](mcp/cursor-setup.md) |
| Cline | [mcp/pcx-knowledge-mcp/README.md](mcp/pcx-knowledge-mcp/README.md) |
| Continue | [mcp/continue-setup.md](mcp/continue-setup.md) |
| Zed | [mcp/zed-setup.md](mcp/zed-setup.md) |
| Aider | [mcp/aider-setup.md](mcp/aider-setup.md) |

---

## Repository Map

```text
pcx-ai-toolkit/
├── docs/                  Generated LLM bundles + local docs mirror
├── docs/perception/       Perception Enma and AngelScript API docs
├── docs/enma/             Enma language and SDK references
├── docs/angelscript-lang/ AngelScript core language manual
├── knowledge/             API index, patterns, forum insights, RE references
├── templates/             Enma and AngelScript scaffolds
├── tools/                 CLI, validators, builders, RE helpers
├── mcp/                   Knowledge MCP and Perception MCP setup
├── rules/                 Drop-in agent instruction files
├── .claude/skills/        Agent skills for PCX work
├── lsp/                   Enma and AngelScript VS Code extension submodules
└── visualstudio/          Visual Studio 2022 extension projects
```

---

## Safety And Scope

This toolkit is for authorized Perception.cx scripting, reverse engineering,
security research, single-player modding, and defensive analysis. Only analyze
software you own or are explicitly authorized to test. The repo does not provide
malware, stolen offsets, credential material, or binary payloads.

See [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and
[CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT. See [LICENSE](LICENSE).
