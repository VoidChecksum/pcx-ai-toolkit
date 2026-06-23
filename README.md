<div align="center">

<img src="assets/perception-banner.png" alt="Perception.cx" width="680">

# pcx-ai-toolkit

### Enma + AngelScript AI Toolkit for Perception.cx

[![CI](https://github.com/VoidChecksum/pcx-ai-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/VoidChecksum/pcx-ai-toolkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Languages](https://img.shields.io/badge/Languages-Enma%20%7C%20AngelScript-f97316.svg)](#language-scope)
[![Docs](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.docs&label=Docs&suffix=%20pages&color=22c55e)](#knowledge-surface)
[![Doc Lines](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.doc_lines&label=Doc%20Lines&color=22c55e)](#knowledge-surface)
[![MCP Tools](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.mcp_tools&label=MCP%20Tools&color=0ea5e9)](#mcp-integration)
[![AI Skills](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.skills&label=AI%20Skills&color=eab308)](#ai-agent-stack)

**Make AI tools write Perception.cx scripts from the real Enma and AngelScript docs, not guesses.**

`llms.txt` context packs · source-backed API lookup · hallucination checks · MCP search · Enma/AngelScript LSP · VSIX packages

[Quick Start](#quick-start) · [Anti-Hallucination](#anti-hallucination-pipeline) · [Knowledge](#knowledge-surface) · [Editors](#editor--vsix-packages) · [CLI](#pcx-cli) · [Safety](#safety-and-scope)

</div>

---

## Why This Exists

LLMs usually do not know Perception.cx, Enma, or the exact AngelScript bindings. They invent APIs such as `draw_esp()`, mix Enma lifecycle code into `.as`, use the wrong address widths, or copy generic game-hacking patterns that do not compile in PCX.

This repo gives AI tools a constrained, verifiable surface:

| Without this toolkit | With this toolkit |
|---|---|
| Guesses function names from general training data | Loads `docs/perception/llm-routing.md` first |
| Mixes Enma and AngelScript bindings | Uses language-specific context packs |
| Produces plausible but wrong snippets | Runs `pcx api`, `pcx symbol-check`, and `pcx check-answer` |
| Requires manual path hunting | Searches the corpus through MCP |
| Relies on generic editor support | Uses Enma and AngelScript LSP packages |

---

## Language Scope

This toolkit is intentionally scoped to **Perception-supported Enma and AngelScript**.

| Area | Enma `.em` | AngelScript `.as` |
|---|---|---|
| Entry point | `int64 main()` | `int main()` |
| Repeating work | `register_routine(cast<int64>(fn), data)` | `register_callback(fn, interval, data)` |
| Logging | `println(...)` | `log(...)` |
| Process handle | `proc_t` value, RAII | `proc_t@` handle, `deref()` cleanup |
| Containers | `T[]`, `map<K,V>` | `array<T>`, `dictionary` |
| Render shapes | `vec2(...)`, `color(...)` | Binding-specific raw/value forms from AS docs |

The first file an LLM should read is [docs/perception/llm-routing.md](docs/perception/llm-routing.md). It defines the binding split and the required lookup flow.

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

Then copy a rules file into your PCX project:

```bash
cp rules/CLAUDE.md /path/to/your/pcx-project/
```

Requirements: Git, Python 3.10+, Node.js 18+. Git submodules are required for LSP/VSIX builds.

---

## Anti-Hallucination Pipeline

The repo now includes deterministic checks for both generated code and generated answers.

```bash
# Verify an API symbol and get official source URLs.
pcx api draw_text --lang enma
pcx api register_callback --lang angelscript

# Validate a real script before running it.
pcx symbol-check my_script.em
pcx verify my_script.as

# Validate fenced Enma/AngelScript code blocks in a Markdown LLM answer.
pcx check-answer answer.md
```

For MCP-aware clients, use:

| MCP tool | Use |
|---|---|
| `api_lookup(symbol, language)` | Exact API lookup with signatures, source URLs, and typo suggestions |
| `validate_code(code, language)` | Finds unknown calls, wrong-language symbols, missing imports, and unknown types |
| `search(query)` | Finds relevant docs/skills/knowledge files without guessing paths |
| `get_file(path)` | Loads the exact source file into context |

The shared source-grounding logic lives in [tools/lib/pcx_grounding.py](tools/lib/pcx_grounding.py), backed by [knowledge/pcx-api-index.json](knowledge/pcx-api-index.json).

---

## Knowledge Surface

| Surface | Path | Best For |
|---|---|---|
| LLM entry index | [docs/llms.txt](docs/llms.txt) | Tools that auto-fetch `llms.txt` |
| Full context pack | [docs/llms-full.txt](docs/llms-full.txt) | One large preload for both languages |
| Enma context pack | [docs/llms-perception-enma.md](docs/llms-perception-enma.md) | Enma-only sessions |
| AngelScript context pack | [docs/llms-perception-angelscript.md](docs/llms-perception-angelscript.md) | AngelScript-only sessions |
| Skills bundle | [docs/llms-skills.md](docs/llms-skills.md) | Agent behavior and workflow rules |
| Knowledge bundle | [docs/llms-knowledge.md](docs/llms-knowledge.md) | RE/game scripting references |
| Dynamic MCP | [mcp/pcx-knowledge-mcp](mcp/pcx-knowledge-mcp) | Search-then-fetch during long sessions |

Current generated counts:

| Docs | Lines | Skills | Knowledge | Templates | Tools | MCP tools |
|---:|---:|---:|---:|---:|---:|---:|
| 123 | 32,231 | 25 | 25 | 30 | 34 | 59 |

Regenerate and verify:

```bash
python3 tools/build-counts.py
python3 tools/build-llms-index.py
python3 tools/build-provenance.py
python3 tools/check-llm-contract.py
```

---

## PCX CLI

`pcx` is the local command surface for setup, validation, scaffolding, and drift checks.

```bash
pcx setup                 # build LSPs, sync skills, install CLI helper
pcx update                # pull, rebuild, sync generated knowledge
pcx lint script.em        # guideline lint for Enma scripts
pcx symbol-check file.em  # source-grounded symbol validation
pcx api draw_text --lang enma
pcx check-answer answer.md
pcx verify file.as
pcx new cheat-skeleton-em ./my-script
pcx doctor
```

High-value standalone tools:

| Tool | Purpose |
|---|---|
| [tools/api-lookup.py](tools/api-lookup.py) | Exact API oracle |
| [tools/symbol-check.py](tools/symbol-check.py) | Script-level hallucination check |
| [tools/check-llm-answer.py](tools/check-llm-answer.py) | Markdown answer code-block validation |
| [tools/build-api-index.py](tools/build-api-index.py) | Rebuild source-backed API index from Perception docs |
| [tools/check-doc-drift.py](tools/check-doc-drift.py) | Compare local docs against upstream |
| [tools/check-mcp-config.py](tools/check-mcp-config.py) | Keep MCP config aligned with `mcp-api.md` |

---

## AI Agent Stack

The toolkit ships agent instructions for Claude Code, Cursor, Cline, Copilot, Windsurf, and generic `AGENTS.md` workflows.

| Layer | Files |
|---|---|
| Global rules | [.clinerules](.clinerules), [.cursorrules](.cursorrules), [.windsurfrules](.windsurfrules), [.github/copilot-instructions.md](.github/copilot-instructions.md) |
| Drop-in rules | [rules/](rules/) |
| Claude skills | [.claude/skills/](.claude/skills/) |
| Routing contract | [docs/perception/llm-routing.md](docs/perception/llm-routing.md) |
| MCP knowledge server | [mcp/pcx-knowledge-mcp/](mcp/pcx-knowledge-mcp/) |

Recommended LLM instruction:

```text
Before writing Perception code, load docs/perception/llm-routing.md.
Use Enma docs for .em and AngelScript docs for .as.
Verify every API with pcx api or MCP api_lookup.
Run pcx symbol-check or MCP validate_code before final output.
```

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

Manual VS Code packaging:

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

Visual Studio packages are separate projects under [visualstudio/](visualstudio/). They require Windows, MSBuild, and the Visual Studio extension development workload.

```powershell
msbuild visualstudio\EnmaVS\EnmaVS.csproj /p:Configuration=Release /restore
msbuild visualstudio\AngelScriptVS\AngelScriptVS.csproj /p:Configuration=Release /restore
```

The Linux development environment can rebuild VS Code `.vsix` packages; Visual Studio `.vsix` packages must be rebuilt on Windows or by the release workflow.

---

## Templates

| Template | Language | Use |
|---|---|---|
| `hello-world` | Enma | Minimal lifecycle sanity check |
| `cheat-skeleton-em` | Enma | Modular ESP/aim/menu/triggerbot skeleton |
| `cheat-skeleton-as` | AngelScript | Equivalent AS scaffold |
| `full-project` | Enma | Multi-file project layout |
| `full-project-as` | AngelScript | Multi-file AS layout |
| `overlay-basic`, `minimap`, `aimbot-skeleton` | Enma | Focused examples |

Create one:

```bash
pcx new cheat-skeleton-em ./pcx-script
pcx new cheat-skeleton-as ./pcx-as-script
```

---

## MCP Integration

Two MCP surfaces matter:

| MCP | Purpose |
|---|---|
| `mcp/pcx-knowledge-mcp` | Local searchable corpus for docs, rules, templates, and API validation |
| `mcp/perception-mcp-config.json` | Runtime Perception MCP tool config with 59 live-process tools |

Install the knowledge server:

```bash
pip install -e mcp/pcx-knowledge-mcp/
pcx-knowledge-mcp --help
```

Client setup docs:

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
├── docs/perception/       Enma and AngelScript Perception API docs
├── docs/enma/             Enma language and SDK references
├── docs/angelscript-lang/ AngelScript core language manual
├── knowledge/             API index, cheat patterns, RE references
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

This toolkit is for authorized Perception.cx scripting, reverse engineering, security research, single-player modding, and defensive analysis. Only analyze software you own or are explicitly authorized to test. The repo does not provide anti-cheat bypasses, malware, stolen offsets, or binary payloads.

See [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT. See [LICENSE](LICENSE).
