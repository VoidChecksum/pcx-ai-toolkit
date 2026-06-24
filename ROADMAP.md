# pcx-ai-toolkit Roadmap

This document outlines the planned work, feature focus, and future direction for the `pcx-ai-toolkit`. We welcome contributions and feedback on any of these areas in [GitHub Discussions](https://github.com/VoidChecksum/pcx-ai-toolkit/discussions).

---

## 🗺️ Future Vision

Our goal is to make AI-assisted game hacking and scripting on the Perception.cx platform **100% reliable, zero-hallucination, and high-productivity**.

---

## 📍 Phase 1: Foundation (Completed / In Progress)

- [x] **Complete documentation coverage** — Scraped and flattened all GitBook and platform docs into static markdown.
- [x] **CLI Manager** — Built the `pcx` CLI with helper commands (`setup`, `update`, `lint`, `doctor`, `new`).
- [x] **Claude Code & Editor Rules** — Added drop-in configurations for Claude Code (`.claude/skills/`), Cursor (`.cursorrules`), Copilot, Windsurf, and Cline.
- [x] **LSP Support** — Compiled Enma and AngelScript language servers with diagnostics and completion.

---

## 🚀 Phase 2: Advanced Tooling & DX (Target: Q3 2026)

### 0. Rust-First Toolkit Migration
- Make the Rust command layer the default for native reverse-engineering tools, API lookup, doctor checks, and binary smoke tests.
- Port the remaining Python validator/scaffold commands into `pcx-rs`: `symbol-check`, `verify`, `verify-project`, `check-answer`, `create`, `build-api-index`, `check-drift`, `counts`, and provenance generation.
- Add a native MCP server mode so agent clients can run source lookup, code validation, answer validation, and scaffolding without a Python process.
- Keep Python wrappers only as compatibility launchers during the transition, then remove them after the Rust CLI reaches feature parity.

### 1. Package Registry Distribution
- Publish `pcx-knowledge-mcp` to PyPI to enable direct installation via `pip install pcx-knowledge-mcp` or execution via `uvx`.
- Submit the VS Code LSP extensions directly to the VS Code Marketplace and Open VSX Registry for automatic updates.

### 2. Editor Ecosystem Expansion
- Add native Neovim and Helix configuration examples in the documentation, making LSP integration plug-and-play for terminal-focused developers.
- Build a unified setup command for Neovim config integration (`pcx setup --nvim`).

### 3. Verification & Testing Tools
- Enhance the `test-discipline` skill with boilerplate test script generation commands (`pcx new test-reader`).
- Integrate offset change alert scans that automatically alert the user if a pattern resolves to a different instruction size after game updates.
- Add scenario fixtures for Enma and AngelScript API families: lifecycle, render/custom draw, GUI, Proc, Net, filesystem, Zydis, Unicorn, and MCP.
- Export Rust RE findings directly to `offsets.em`, `evidence.jsonl`, patch-day signature health summaries, and project verification inputs.

---

## 🧠 Phase 3: Cognitive & Deep AI Integrations (Target: Q4 2026)

### 1. Visual Debug Overlay Generation
- Expose helper tools to auto-generate debug overlays (e.g. bounding boxes, bone meshes, text labels) directly from structural definitions in a C++ SDK or memory layouts.

### 2. Fine-Tuning Corpus & Datasets
- Collect high-quality, lint-passing Enma/AngelScript scripts to construct instruction-tuning datasets for open-weights models (e.g. Llama-3, Qwen-2).

### 3. Interactive Agent Workflows
- Build multi-agent orchestration pipelines where a `reverse-engineer` agent automatically outputs a memory trace that is fed into a `script-writer` agent, automating offset resolution to working code.
