<div align="center">

<img src="assets/perception-banner.png" alt="Perception.cx" width="760">

# pcx-ai-toolkit

### The Source-Grounded AI Toolkit for Perception.cx Enma

[![CI](https://github.com/VoidChecksum/pcx-ai-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/VoidChecksum/pcx-ai-toolkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Scope](https://img.shields.io/badge/Scope-Enma-f97316.svg)](#language-scope)
[![Docs](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.docs&label=Docs&suffix=%20pages&color=22c55e)](#knowledge-surface)
[![Doc Lines](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.doc_lines&label=Doc%20Lines&color=22c55e)](#knowledge-surface)
[![MCP Tools](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.mcp_tools&label=MCP%20Tools&color=0ea5e9)](#mcp-integration)
[![AI Skills](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.skills&label=AI%20Skills&color=eab308)](#ai-agent-stack)
[![Native Tools](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/VoidChecksum/pcx-ai-toolkit/main/docs/COUNTS.json&query=$.native_tools&label=Native%20Tools&color=64748b)](#native-re-tools)

**Make LLMs write Perception.cx code from verified Enma sources, not guessed APIs.**

`llms.txt` context packs | source-backed API oracle | MCP tools | validators | native Rust RE tools | templates | AI skills | VS Code and Visual Studio packages

[AI Start Here](#ai-start-here) | [Anti-Hallucination](#anti-hallucination-pipeline) | [Knowledge](#knowledge-surface) | [MCP](#mcp-integration) | [Editors](#editor-and-vsix-packages) | [Safety](#safety-and-scope)

</div>

---
## First Decision

```text
Writing Enma?        Load docs/llms-perception-enma.md, then run pcx symbol-check.
Need API proof?      Run pcx api <symbol>.
Need MCP context?    Run pcx-rs mcp, pcx-rs mcp-schema --json, or pcx-knowledge-mcp.
Need RE artifacts?   Use re-importer.py exporters; keep evidence before shipping.
```

Unsupported or hallucinated surfaces live in [`knowledge/unsupported-symbols.json`](knowledge/unsupported-symbols.json) and are rejected by validators when seen.

<table>
<tr>
<td width="50%">

## What This Is

`pcx-ai-toolkit` is an AI-facing knowledge and validation layer for Perception.cx scripting.

It teaches agents the supported **Enma** APIs, routes them to source docs, rejects unsupported symbols, and validates generated code before it reaches PCX.

</td>
<td width="50%">

## What This Is Not

This is not a generic cheat dump, offset pack, malware toolkit, or unsupported language bundle.

AngelScript, Lua, and other historical surfaces are intentionally excluded from the AI contract. If a symbol is not proven by docs or the API index, the agent must not invent it.

</td>
</tr>
</table>

## AI Start Here

Load this sequence before writing any Perception code:

```text
1. docs/AI_AGENT_OPERATING_MANUAL.md
2. docs/perception/llm-routing.md
3. Use Enma (`.em`)
4. Load `docs/llms-perception-enma.md`
5. Verify every API or language add-on symbol with pcx api or MCP api_lookup
6. Validate code with pcx symbol-check, pcx verify, or MCP validate_answer
```

| Must Load | Purpose |
|---|---|
| [docs/AI_AGENT_OPERATING_MANUAL.md](docs/AI_AGENT_OPERATING_MANUAL.md) | Minimal safe workflow for LLM and MCP agents |
| [docs/perception/llm-routing.md](docs/perception/llm-routing.md) | Enma-only source-grounding workflow |
| [docs/llms-perception-enma.md](docs/llms-perception-enma.md) | Single-file Enma + PCX context pack |
| [knowledge/pcx-api-index.json](knowledge/pcx-api-index.json) | Machine-readable oracle for PCX host APIs and language add-ons |
| [knowledge/perception-forum-insights.md](knowledge/perception-forum-insights.md) | Secondary forum/changelog context, never an API contract |

Recommended model instruction:

```text
Before writing Perception code, load docs/AI_AGENT_OPERATING_MANUAL.md and docs/perception/llm-routing.md.
Use Enma docs for `.em` files; `.as` is unsupported.
Verify every Perception host API and language/add-on symbol with pcx api or MCP api_lookup.
Validate final code or Markdown answers before returning them.
If the docs/API index do not prove a symbol exists, say so instead of guessing.
```

## Language Scope

The toolkit is intentionally scoped to **Perception-supported Enma (`.em`) only**. AngelScript (`.as`) is deprecated and rejected by validators/scaffolding.

Core Enma contract: `int64 main()`, `register_routine(cast<int64>(fn), data)`, `void fn(int64 data)`, `println(...)`, RAII `proc_t`, `T[]`, `map<K,V>`, `vec2(...)`, and `color(r,g,b,a)`.

## Quick Start

PyPI:

```bash
python -m pip install pcx-ai-toolkit
pcx doctor
```

npm / Bun:

```bash
npm install -g pcx-ai-toolkit
# or
bun add -g pcx-ai-toolkit
pcx doctor
```

Source checkout:

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

Requirements: Git, Python 3.10+, Node.js 18+. Git submodules are required for LSP and `.vsix` packaging.

## Registry Publishing Setup

For automatic package publishing from GitHub Actions, configure trusted publishers once in each registry.

PyPI Trusted Publisher for `pcx-ai-toolkit`:
- Owner: `VoidChecksum`
- Repository: `pcx-ai-toolkit`
- Workflow filename: `release.yml`

npm Trusted Publisher for `pcx-ai-toolkit`:
- Owner/user: `VoidChecksum`
- Repository: `pcx-ai-toolkit`
- Workflow filename: `release.yml`
- Allowed action: `npm publish`

## Anti-Hallucination Pipeline

Use these checks before trusting generated code:

```bash
# Exact source-backed lookup.
pcx api draw_text
pcx api json_object

# Script validation.
pcx symbol-check my_script.em
pcx verify my_script.em
pcx verify-project ./my-project

# Markdown answer validation.
pcx check-answer answer.md

# Regression benchmark for hallucinated answers/snippets.
python3 tools/hallucination-eval.py
```

MCP-aware clients should use this sequence:

```text
overview()
recommend_context(task, language)
generate_script_plan(task, language)
scaffold_project(..., dry_run=true)
get_skill(name)
get_file(path)
api_lookup(symbol, language)
validate_code(code, language)
validate_answer(markdown)
validate_project(path)
```

| Failure Mode | Countermeasure |
|---|---|
| Invented API names like `draw_esp()` | `pcx api`, MCP `api_lookup`, and `knowledge/pcx-api-index.json` |
| Enma lifecycle inside `.as` | `docs/perception/llm-routing.md`, symbol validation, wrong-language detection |
| Missing Enma imports | `validate_code` missing-import findings for `vec`, `color`, `math`, `json`, and more |
| Enma semantic traps | Rust `symbol-check` flags integer-keyed `map<K,V>`, escaping `return &local`, and missing `PERM_FILE` for file APIs |
| Stale docs | provenance, drift checks, `tools/regenerate-docs.py`, regenerated `llms-*` bundles |
| Forum facts treated as APIs | `knowledge/perception-forum-insights.md` is marked secondary |
| Regressed validators | `tools/hallucination-eval.py` golden corpus |

## Knowledge Surface

| Docs | Doc Lines | API Docs Indexed | API Functions | API Methods | Skills | Templates | MCP Tools | Native Tools |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 124 | 32,186 | 39 | 836 | 333 | 25 | 30 | 59 | 13 |

| Surface | Path | Best For |
|---|---|---|
| LLM entry index | [docs/llms.txt](docs/llms.txt) | Auto-fetch tools and first-touch sessions |
| Full context pack | [docs/llms-full.txt](docs/llms-full.txt) | One preload for both supported languages |
| Enma context pack | [docs/llms-perception-enma.md](docs/llms-perception-enma.md) | Enma-only work |
| Skills bundle | [docs/llms-skills.md](docs/llms-skills.md) | Agent behavior and workflow rules |
| Knowledge bundle | [docs/llms-knowledge.md](docs/llms-knowledge.md) | Patterns, forum-derived context, RE references |
| API oracle | [knowledge/pcx-api-index.json](knowledge/pcx-api-index.json) | Exact signatures with source URLs |
| Dynamic MCP | [mcp/pcx-knowledge-mcp](mcp/pcx-knowledge-mcp) | Long sessions, lazy loading, validation |

High-value files:

| File | Use |
|---|---|
| [knowledge/pcx-api-cheatsheet.md](knowledge/pcx-api-cheatsheet.md) | PCX APIs at a glance |
| [knowledge/common-patterns.md](knowledge/common-patterns.md) | Working Enma patterns |
| [knowledge/custom-draw-patterns.md](knowledge/custom-draw-patterns.md) | GPU/custom draw examples |
| [knowledge/pcx-version-matrix.md](knowledge/pcx-version-matrix.md) | Version and changelog availability matrix |
| [knowledge/perception-forum-insights.md](knowledge/perception-forum-insights.md) | Forum-derived Enma rollout, overlay, IDE, analyzer, changelog context |

Regenerate and verify generated knowledge:

```bash
python3 tools/build-counts.py
python3 tools/build-api-index.py
python3 tools/build-llms-index.py
python3 tools/build-provenance.py
python3 tools/regenerate-docs.py --check
python3 tools/check-llm-contract.py
python3 tools/check-skill-contract.py
```

## PCX CLI

```bash
pcx setup
pcx update
pcx doctor
pcx api draw_text
pcx symbol-check file.em
pcx verify file.em
pcx check-answer answer.md
pcx create --wizard
pcx create --name "My ESP" --language enma --kind full --target game.exe --output ./my-esp
pcx verify-project ./my-esp --allow-placeholders --allow-unverified
```

| Tool | Purpose |
|---|---|
| [tools/api-lookup.py](tools/api-lookup.py) | Exact API oracle |
| [tools/symbol-check.py](tools/symbol-check.py) | Script-level source-grounded validation |
| [tools/verify-project.py](tools/verify-project.py) | Project-wide lint, symbol, hygiene, and evidence verification |
| [tools/check-llm-answer.py](tools/check-llm-answer.py) | Markdown answer code-block validation |
| [tools/hallucination-eval.py](tools/hallucination-eval.py) | Golden regression benchmark for hallucination gates |
| [tools/build-api-index.py](tools/build-api-index.py) | Rebuild source-backed API index |
| [tools/check-doc-drift.py](tools/check-doc-drift.py) | Compare local docs against upstream |
| [tools/regenerate-docs.py](tools/regenerate-docs.py) | Fetch drift-checkable upstream Markdown into `docs/` |
| [tools/re-importer.py](tools/re-importer.py) | Convert IDA/Ghidra/Binja/ReClass exports into PCX offset/evidence seeds |
| [tools/anti-debug-scanner.py](tools/anti-debug-scanner.py) | Native-backed anti-debug import, byte-pattern, and string scanner |
| [tools/identify-protector.py](tools/identify-protector.py) | Native-backed protector, packer, overlay, and anti-debug indicator scan |
| [tools/pe-section-analyzer.py](tools/pe-section-analyzer.py) | Native-backed section entropy, flag, overlay, and anomaly report |
| [tools/analyze-vmprotect.py](tools/analyze-vmprotect.py) | Native-backed VMProtect section, VM-entry, and workflow analyzer |
| [tools/dump-strings-xor.py](tools/dump-strings-xor.py) | Native-backed single-byte XOR string extraction |
| [tools/module-export-mapper.py](tools/module-export-mapper.py) | Native-backed export listing and named consumer cross-reference |
| [tools/sig-uniqueness-checker.py](tools/sig-uniqueness-checker.py) | Validate byte signatures; proxies to native Rust when built |
| [tools/binary-diff-summary.py](tools/binary-diff-summary.py) | Patch-day section diff and recompile/refactor/major-change classifier; proxies to native Rust when built |
| [tools/offset-diff.py](tools/offset-diff.py) | Diff named direct/RIP signatures across binary versions; proxies to native Rust when built |
| [tools/check-skill-contract.py](tools/check-skill-contract.py) | Reject stale or unsupported AI-skill contracts |
| [tools/check-mcp-config.py](tools/check-mcp-config.py) | Keep runtime MCP config aligned with docs |

## Native RE Tools

The high-volume binary-analysis path is Rust-first with Python compatibility wrappers. Running `setup.sh`, `setup.ps1`, or CI builds these binaries into `tools/bin/`; if Cargo is unavailable, the same Python commands fall back automatically.

```bash
cargo build --release --manifest-path tools/pe-parser/Cargo.toml
mkdir -p tools/bin
for tool in pe-parser anti-debug-scanner identify-protector pe-section-analyzer \
  pcx-rs api-lookup pattern-format-converter analyze-vmprotect \
  dump-strings-xor module-export-mapper \
  sig-uniqueness-checker binary-diff-summary offset-diff; do
  cp "tools/pe-parser/target/release/$tool" "tools/bin/$tool"
done
```

| Native binary | Wrapper | Use |
|---|---|---|
| `pcx-rs` | [tools/pcx](tools/pcx) | Rust-first manager command layer and native command router |
| `api-lookup` | [tools/api-lookup.py](tools/api-lookup.py) | Source-backed Enma and AngelScript API lookup |
| `pattern-format-converter` | [tools/pattern-format-converter.py](tools/pattern-format-converter.py) | Pattern conversion across IDA, Ghidra, x64dbg, CE, Enma, and mask formats |
| `pe-parser` | [tools/lib/pe_parse.py](tools/lib/pe_parse.py) | PE/ELF/Mach-O metadata extraction for all RE tools |
| `anti-debug-scanner` | [tools/anti-debug-scanner.py](tools/anti-debug-scanner.py) | Anti-debug imports, byte patterns, timing, context, and debugger-string scan |
| `identify-protector` | [tools/identify-protector.py](tools/identify-protector.py) | Protector and packer heuristics from sections, imports, stubs, and overlays |
| `pe-section-analyzer` | [tools/pe-section-analyzer.py](tools/pe-section-analyzer.py) | Entropy, flags, overlay, and section anomaly analysis |
| `analyze-vmprotect` | [tools/analyze-vmprotect.py](tools/analyze-vmprotect.py) | VMProtect-specific section, entry-stub, and tooling recommendations |
| `dump-strings-xor` | [tools/dump-strings-xor.py](tools/dump-strings-xor.py) | XOR-hidden string extraction across selected sections |
| `module-export-mapper` | [tools/module-export-mapper.py](tools/module-export-mapper.py) | Export table mapping and named import consumer cross-reference |
| `sig-uniqueness-checker` | [tools/sig-uniqueness-checker.py](tools/sig-uniqueness-checker.py) | Unique/stale/ambiguous signature verdicts with near-miss support |
| `binary-diff-summary` | [tools/binary-diff-summary.py](tools/binary-diff-summary.py) | Fast patch-day section survival summary |
| `offset-diff` | [tools/offset-diff.py](tools/offset-diff.py) | Direct and RIP-relative offset movement report |

Keep new binary-analysis tools in the same Cargo package under [tools/pe-parser](tools/pe-parser), then expose a small Python wrapper so existing agent commands do not change.

## Gap Analysis And Feature Improvements

The docs surface is strong, but the toolkit still has a few high-value gaps when measured against the current Perception Enma surface:

| Gap | Why It Matters | Improvement |
|---|---|---|
| Native parity is still incomplete | `symbol-check`, `verify-project`, `check-answer`, `create`, `counts`, `build-provenance`, offline `check-drift`, and core MCP handlers now run in Rust, but docs/index generation and some compatibility commands remain Python-backed | Port `build-api-index` and package/update commands only where native speed or release reliability pays for the code |
| MCP server parity is partial | `pcx-rs mcp` supports line-delimited JSON-RPC plus `initialize`, `ping`, `tools/list`, `tools/call`, and toolkit validation tools, but not Streamable HTTP | Add HTTP transport only if real MCP clients need direct `pcx-rs` attachment instead of stdio |
| API drift checks still rely on live Python doc scraping | The upstream docs change frequently, and live CI checks can fail from network instability | Keep native `pcx-rs build-provenance` and offline `pcx-rs check-drift` as the CI-safe path; add explicit `--live` Rust fetching and API-index parsing only if the Python scripts keep causing release failures |
| Binary-analysis tools report findings but do not produce every PCX-ready remediation artifact | Analysts still manually turn some RE findings into Enma offsets, signatures, and evidence logs | Expand direct exporters for `offsets.em`, `evidence.jsonl`, signature health reports, and patch-day migration summaries |
| Scenario coverage can go deeper | Current fixtures cover the major API families plus Enma JSON/map/file/OOB usage, and red/green validator tests cover cast, pointer escape, permission, and map-key mistakes | Add more tiny scenarios only when they catch a documented compiler/runtime edge that current tests miss |
| Safety scope is metadata-backed but not policy-enforced | Templates and MCP responses preserve authorized-use context, but tooling does not block all dual-use misuse patterns | Keep metadata in generated artifacts and add narrow denylist checks only for common hallucinated abuse helpers |

## AI Agent Stack

| Layer | Files |
|---|---|
| Global rules | [.clinerules](.clinerules), [.cursorrules](.cursorrules), [.windsurfrules](.windsurfrules), [.github/copilot-instructions.md](.github/copilot-instructions.md) |
| Drop-in rules | [rules/](rules/) |
| Claude skills | [.claude/skills/](.claude/skills/) |
| Agent manual | [docs/AI_AGENT_OPERATING_MANUAL.md](docs/AI_AGENT_OPERATING_MANUAL.md) |
| Routing contract | [docs/perception/llm-routing.md](docs/perception/llm-routing.md) |
| Knowledge MCP | [mcp/pcx-knowledge-mcp/](mcp/pcx-knowledge-mcp/) |

Core skills:

| Skill | Use |
|---|---|
| `pcx-enma-discipline` | Enma syntax, lifecycle, imports, and binding discipline |
| `game-cheat-script-master` | End-to-end script architecture patterns |
| `game-cheat-guidelines` | Behavioral guardrails and anti-hallucination rules |
| `pcx-knowledge-index` | Which docs and knowledge files to load |
| `mcp-tool-routing` | When and how to call MCP tools |

## MCP Integration

| MCP Surface | Purpose |
|---|---|
| [mcp/pcx-knowledge-mcp](mcp/pcx-knowledge-mcp) | Searchable corpus, API lookup, project scaffolding, code/project validation, answer validation |
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

## Editor and VSIX Packages

Prebuilt VS Code extension packages are stored in the LSP submodules:

| Package | Path | Language |
|---|---|---|
| Enma Language | `lsp/enma-lsp/enma-language-1.1.22.vsix` | `.em`, `.em.predefined`, `.emb` |

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

```

Visual Studio packages live under [visualstudio/](visualstudio/). They require Windows, MSBuild, and the Visual Studio extension development workload.

```powershell
msbuild visualstudio\EnmaVS\EnmaVS.csproj /p:Configuration=Release /restore
```

## Templates

| Template | Language | Use |
|---|---|---|
| `hello-world` | Enma | Minimal lifecycle sanity check |
| `cheat-skeleton-em` | Enma | Modular ESP, aim, menu, radar, triggerbot scaffold |
| `full-project` | Enma | Multi-file Enma project layout |
| `overlay-basic`, `minimap`, `aimbot-skeleton` | Enma | Focused examples |

Create one:

```bash
pcx create --wizard
pcx create --name "PCX Enma Script" --language enma --kind cheat --target game.exe --output ./pcx-enma-script
pcx verify-project ./pcx-enma-script --allow-placeholders --allow-unverified
```

## Repository Map

```text
pcx-ai-toolkit/
├── docs/                  Generated LLM bundles + local docs mirror
├── docs/perception/       Perception Enma API docs
├── docs/enma/             Enma language and SDK references
├── knowledge/             API index, patterns, forum insights, RE references
├── templates/             Enma scaffolds
├── tools/                 CLI, validators, builders, RE helpers
├── tools/pe-parser/       Rust-native parser, signature, diff, and offset tools
├── evals/                 Hallucination regression corpus
├── signatures/            Engine and protector reversal signature packs
├── mcp/                   Knowledge MCP and Perception MCP setup
├── rules/                 Drop-in agent instruction files
├── .claude/skills/        Agent skills for PCX work
├── lsp/                   Enma VS Code extension submodule
└── visualstudio/          Visual Studio 2022 extension projects
```

## Safety and Scope

This toolkit is for authorized Perception.cx scripting, reverse engineering, security research, single-player modding, and defensive analysis. Only analyze software you own or are explicitly authorized to test.

The repo does not provide malware, stolen offsets, credential material, or binary payloads. See [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
