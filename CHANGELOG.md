# Changelog

All notable changes to this toolkit are documented here.

## [1.3.0] — 2025-06-17

### Added
- **Prebuilt VS Code extensions** — `enma-language.vsix` and `angel-lsp.vsix` attached to GitHub Releases for one-click install (no build step)
- **GitHub Actions** — `release.yml` auto-builds and attaches both `.vsix` on every version tag; `ci.yml` validates shell/PowerShell syntax, JSON/YAML, doc count, and that both LSP servers build
- LSP servers registered as proper git submodules so `git clone --recursive` and CI work correctly

### Changed
- `.gitignore` — stop ignoring the submodule paths; ignore built `*.vsix` instead
- README — new "VS Code Extensions" section with VSIX install instructions

## [1.2.0] — 2025-06-17

### Added
- **Windows support** — native `setup.ps1` (PowerShell 5.1+, validated against the real parser) for Windows 10/11 users without a bash shell
- `.gitattributes` — enforces LF on `.sh` and CRLF on `.ps1`/`.bat`, preventing line-ending corruption on Windows clones

### Changed
- `setup.sh` — platform detection (Linux/macOS/WSL/Git Bash/Cygwin), prerequisite checks for git/node/npm, and build verification (checks the output file exists instead of blindly reporting success)
- README + Claude Code setup doc — cross-platform commands (bash + PowerShell) for clone, install, skills, and LSP config
- Verified end-to-end: `setup.sh` clones+builds both LSP servers on Linux; `setup.ps1` passes the PowerShell parser with 0 errors

## [1.1.0] — 2025-06-17

### Added
- **Templates** — `hello-world.em`, `overlay-basic.em`, and a 5-file `full-project/` scaffold (globals, offsets, feature, menu, main), all following the 12 guidelines
- `CONTRIBUTING.md`, `CHANGELOG.md`
- GitHub community files: issue templates (bug, docs, feature), PR template, `FUNDING.yml`
- Discussions enabled with welcome + roadmap threads
- Social preview image (5120×2560)

### Changed
- Visual README redesign — badges, Perception banner, IDE screenshots, collapsible doc tables

## [1.0.0] — 2025-06-17

### Added
- **Documentation** — 107/107 gitbook pages (34,032 lines): complete Enma language reference, all 18 standard library addons, full C++ SDK guide, and every Perception.cx API for Enma, AngelScript, and Lua
- **AI Skills** — `game-hacking-pcx` (doc index + API rules) and `game-cheat-guidelines` (12 behavioral rules)
- **Knowledge base** — Enma cheatsheet, PCX API cheatsheet, 13 working code patterns, offset methodology
- **Rules** — drop-in `CLAUDE.md` and `AGENTS.md` (5 agent roles)
- **MCP configs** — Perception.cx (42+ tools), Claude Code, and Cursor setup guides
- **LSP servers** — enma-lsp and angel-lsp-pcx as git submodules, auto-built by `setup.sh`
- **Signatures** — Source Engine methodology and example patterns
- `setup.sh` one-command installer

## Documentation Source Versions

The `docs/` corpus is a snapshot of the upstream gitbooks. To refresh, re-download from:
- Enma: `https://enma-1.gitbook.io/enma/llms.txt`
- Perception.cx: `https://docs.perception.cx/perception/llms.txt`

Last synced: **2025-06-17** — 107 pages.
