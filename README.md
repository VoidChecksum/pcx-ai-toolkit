# pcx-ai-toolkit

Rust-only AI toolkit for Perception.cx Enma (`.em`) scripting: source-grounded docs, API oracle, validators, MCP mode, templates, and native reverse-engineering helpers.

## Scope

- Script language: Enma only.
- Runtime implementation: Rust only.
- AngelScript (`.as`) is deprecated and rejected.
- Project-owned Python has been removed; do not add compatibility wrappers, tests, package metadata, or CI steps.

## Quick Start

```bash
git clone --recursive https://github.com/VoidChecksum/pcx-ai-toolkit.git
cd pcx-ai-toolkit
./setup.sh
pcx-rs doctor
```

Requirements: Git, Rust/Cargo, Node.js 18+ for LSP/editor packaging.

## AI Start Here

Before writing Perception code, load:

1. `docs/AI_AGENT_OPERATING_MANUAL.md`
2. `docs/perception/llm-routing.md`
3. Relevant `docs/perception/*.md` API page
4. `knowledge/pcx-api-index.json` for exact signatures

Never invent API names. If docs and API index do not prove a symbol exists, say so.

## CLI

```bash
pcx-rs api draw_text
pcx-rs symbol-check my_script.em
pcx-rs verify-project ./my-project --allow-placeholders --allow-unverified
pcx-rs check-answer answer.md
pcx-rs mcp
pcx-rs mcp-schema --json
pcx-rs counts --json
pcx-rs build-provenance --json
pcx-rs check-drift --json
```

Native RE helpers are built into `tools/bin/` by `setup.sh`:

- `pe-parser`
- `api-lookup`
- `pattern-format-converter`
- `sig-uniqueness-checker`
- `binary-diff-summary`
- `offset-diff`
- `anti-debug-scanner`
- `identify-protector`
- `pe-section-analyzer`
- `analyze-vmprotect`
- `dump-strings-xor`
- `module-export-mapper`

## Build and Test

```bash
cargo build --release --manifest-path tools/pe-parser/Cargo.toml
cargo test --manifest-path tools/pe-parser/Cargo.toml
./tools/test-runner.sh
```

## Knowledge Surface

| Surface | Path |
|---|---|
| LLM index | `docs/llms.txt` |
| API oracle | `knowledge/pcx-api-index.json` |
| Unsupported symbols | `knowledge/unsupported-symbols.json` |
| Provenance | `docs/PROVENANCE.json` |
| Counts | `docs/COUNTS.json` |
| MCP mode | `pcx-rs mcp` |

## Enma Contract

Core shape: `int64 main()`, `register_routine(cast<int64>(fn), data)`, `void fn(int64 data)`, `println(...)`, RAII `proc_t`, `T[]`, `map<K,V>`, `vec2(...)`, and `color(r,g,b,a)`.

Run validators before shipping generated code:

```bash
pcx-rs symbol-check script.em
pcx-rs verify-project . --allow-placeholders --allow-unverified
```

## Safety and Scope

This toolkit is for authorized Perception.cx scripting, reverse engineering, security research, single-player modding, and defensive analysis. Only analyze software you own or are explicitly authorized to test. See `SECURITY.md`.
