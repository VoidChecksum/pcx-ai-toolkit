# Documentation Index

## Start Here

| File | Purpose |
|---|---|
| [`AI_AGENT_OPERATING_MANUAL.md`](AI_AGENT_OPERATING_MANUAL.md) | Required workflow for AI agents |
| [`perception/llm-routing.md`](perception/llm-routing.md) | Enma-only routing before writing scripts |
| [`llms.txt`](llms.txt) | Compact LLM entry index |
| [`COUNTS.json`](COUNTS.json) | Repository surface counts |
| [`PROVENANCE.json`](PROVENANCE.json) | Source provenance map |

## Enma Language Docs

- [`enma/llms-language.md`](enma/llms-language.md)
- [`enma/llms-sdk.md`](enma/llms-sdk.md)
- [`enma/language-guide/`](enma/language-guide/)
- [`enma/addons/`](enma/addons/)

## Perception Enma APIs

Read [`perception/readme.md`](perception/readme.md), then the relevant API page under `perception/` before using host APIs.

## Rust Tooling

Native CLI and RE tools live under [`../tools/pe-parser/`](../tools/pe-parser/). Build with:

```bash
cargo build --release --manifest-path tools/pe-parser/Cargo.toml
```

Primary entrypoint: `pcx-rs`.
