# Changelog

All notable changes to this toolkit are documented here.

## [1.9.0] — 2026-06-17

### Added
- **Deobfuscation skill** (`deobfuscation`) — six-step methodology for reversing protected binaries: identify protector (section names, DIE, behavioral signals), strip outer layers (anti-debug → unpack → IAT fix), classify obfuscation type (mutation vs. CFF vs. VM), devirtualize VM-protected code (dispatcher → components → trace → lift → verify), handle protector-specific tricks (Themida FISH–SHARK VMs, VMP handler mutation + bytecode encryption + Ultra mode, OLLVM CFF + MBA), and know when to skip (black-box, hook boundaries, patch around)
- **`knowledge/obfuscation-taxonomy.md`** — per-protector architecture reference: Themida/WinLicense (5 VM tiers, macro VM mode), VMProtect (stack-based VM, handler mutation, rolling-key bytecode encryption, Ultra nested VMs), Code Virtualizer, Enigma, Obsidium, LLVM-obfuscator (CFF, BCF, MBA, SUB, indirect branching passes), Hikari, Pluto. Runtime techniques: metamorphic code, self-modifying code, API hashing, stack strings, nanomites. Kernel-level: PatchGuard, DSE, hypervisor-based protection
- **`knowledge/deobfuscation-tools.md`** — tool reference by obfuscation layer: devirtualizers (NoVmp, VMHunt, vtil), symbolic execution (Triton, Miasm, angr), IDA plugins (D-810, hrtng, HashDB), Binary Ninja (deflat), unpacking (ScyllaHide, Scylla, pe-sieve), strings (FLOSS), tracing (PIN, Frida, DynamoRIO). Per-protector tool chain recommendations
- **`signatures/obfuscation/protector-patterns.md`** — identification patterns: section names for 12 protectors, VMP entry stubs + dispatcher fetch loop, Themida computed-goto dispatch, OLLVM CFF dispatcher structure + opaque predicates + MBA patterns, generic packer OEP detection, IAT redirection stubs, anti-debug API byte patterns

### Changed
- README — AI Skills count 6 → 7, directory tree + detail sections for deobfuscation
- `docs/INDEX.md` — added obfuscation-taxonomy, deobfuscation-tools, and protector-patterns entries
- `game-hacking-pcx` skill — added deobfuscation cross-references to RE Tools section

## [1.8.0] — 2026-06-17

### Fixed
- **100 broken internal links** — all Enma docs used GitBook-style absolute paths (`/enma/addons/vec.md`, `/enma/language-guide/basics.md`, etc.) that didn't resolve after files were flattened to `addon-vec.md`, `lang-basics.md` prefixed names. Built a 59-entry path mapping and batch-fixed every cross-reference across 22 files.
- **`docs/INDEX.md` out of sync** — 44 docs missing from the index (AngelScript, Lua, 2 new Enma files, new knowledge/signature docs); 9 entries had wrong relative paths. Rebuilt with all files.
- **README claimed "107 pages, 34,000+ lines"** — actual is 110 pages, 35,000+ lines. Updated both claims and the CI threshold.

### Added
- **CI link checker** — new workflow step validates all internal markdown links on every push/PR. Strips code fences to avoid false positives. Prevents the broken-link class of bug from recurring.
- **`signatures/unity-il2cpp/il2cpp-patterns.md`** — IL2CPP reversal patterns: metadata dumping with Il2CppDumper, static field access via GC handle table, entity/camera/transform struct patterns, Perception integration example. Covers Tarkov, Rust, Arena Breakout Infinite.
- **`signatures/source2-engine/source2-patterns.md`** — Source 2 reversal patterns: schema system resolution (field offsets are runtime, not hardcoded), entity list chunked iteration, view matrix W2S, key schema classes for CS2 (CCSPlayerPawn, CCSPlayerController, CGameSceneNode, CSkeletonInstance). Covers CS2 and Deadlock.
- **`.editorconfig`** — enforces UTF-8, 2-space indent, LF line endings (CRLF for `.ps1`/`.bat`), final newline across all contributors' editors.

### Changed
- **`docs/enma/llms-language.md`** — added `<!-- AUTO-GENERATED -->` header clarifying this is a scraped concatenation of the individual `lang-*.md` / `addon-*.md` files, not to be edited manually.
- **CI doc count threshold** — 107 → 110 to match actual page count.

## [1.7.0] — 2026-06-17

### Added
- **Kernel anti-cheat RE skills** — two AI skills for reversing kernel-level anti-cheat systems:
  - `anti-cheat-re` — six-step methodology: map the component stack, catalog kernel callbacks, trace driver↔user-mode communication, identify detection scans, analyze from below the AC's observation layer, verify against live behavior
  - `kernel-analysis` — technical patterns for driver binary analysis: WDM/KMDF identification, IOCTL dispatch table extraction with `CTL_CODE` decoding, kernel callback structures (ObRegisterCallbacks, Ps* notify, minifilter, ETW TI), integrity check patterns (hashing, RDTSC, CPUID, module walks), obfuscation layers (import resolution, encrypted strings, CFG, VMProtect), shared memory communication
- **`knowledge/anti-cheat-architecture.md`** — architecture reference for EAC, BattlEye, Vanguard, GameGuard, XIGNCODE3, and Theia: components, driver behavior, communication protocols, detection technique matrix (16 techniques × 5 ACs), AC-by-game mapping for all 29 PCX-supported titles
- **`knowledge/kernel-re-tools.md`** — tool reference for kernel RE: static analysis (IDA, Ghidra, r2, Binary Ninja), kernel debugging (WinDbg, VirtualKD-Redux, HyperDbg, QEMU+GDB), memory forensics (Volatility 3, MemProcFS, PCILeech), runtime monitoring (Process Monitor, IRPMon, API Monitor), driver dev/test (WDK, OSR Driver Loader), Perception.cx kernel integration
- **`signatures/anti-cheat/common-ac-patterns.md`** — byte patterns for AC driver identification: driver file names, device name strings, callback registration call sites, dynamic import resolution (MmGetSystemRoutineAddress, hash-based), integrity check patterns (RDTSC pairs, CPUID hypervisor detection)
- **`anti-cheat-researcher` agent role** — added to `rules/AGENTS.md` for kernel AC analysis workflows
- **`knowledge/re-plugins-and-tools.md`** — complete reference for the installed RE toolkit: 6 IDA plugins (hrtng, CodeXplorer, ClassInformer, SigMakerEx, FIRST, RevEng.AI), 4 Ghidra extensions (GhidrAssist, BinDiffHelper, OOAnalyzer, RevEng.AI), 3 FLIRT sig databases (51 MSVC v15 sigs), Diaphora + BinDiff for cross-patch diffing, ret-sync debugger↔disassembler sync, r5sdk (2438 headers). Includes first-load, post-patch, and live-debug workflows.

### Changed
- **`knowledge/game-targets.md`** — added Anti-Cheat column to all game tables (EAC, BattlEye, Vanguard, RICOCHET, Byfron, VAC, custom, none)
- **`knowledge/community-tools.md`** — added "Kernel RE & Anti-Cheat Analysis Tools" section (HyperDbg, Volatility 3, MemProcFS, IRPMon, VirtualKD-Redux, PCILeech)
- README — AI Skills count 4 → 6, directory tree + detail sections for all new content, agent count 5 → 6
- **`game-hacking-pcx` skill** — expanded RE Tools section with cross-references to all new knowledge docs (plugins, AC architecture, kernel tools, AC patterns)

## [1.6.0] — 2026-06-17

### Added
- **Karpathy work-discipline skills** — two AI skills derived from the four Karpathy principles, rewritten for PCX: `pcx-coding-discipline` (think → simplify → surgical → verify, for writing scripts) and `pcx-re-discipline` (the same loop for reverse engineering and offset maintenance). These are the *process* layer; `game-cheat-guidelines` stays the *code-shape* layer.
- **`rules/KARPATHY.md`** — drop-in work-discipline rules (the four principles condensed to one screen), companion to `rules/CLAUDE.md`.

### Changed
- `setup.sh` / `setup.ps1` — install skills by globbing `.claude/skills/*/` instead of a hardcoded name list, so new skills install automatically and can't be silently omitted.
- `rules/CLAUDE.md` — added a "Work Discipline (Karpathy)" section linking the new rules and skills.
- README — AI Skills count 2 → 4, with the two new skills in the directory tree and AI Skills section, and `KARPATHY.md` in Project Rules.

## [1.5.0] — 2026-06-17

### Added
- **Visual Studio 2022 support** — native `ILanguageClient` MEF extensions for Enma and AngelScript under `visualstudio/`, producing VS-compatible `.vsix` (a separate extension model from the VS Code `.vsix`)
- `release-vs.yml` — Windows CI that builds both VS extensions and attaches them to releases
- `visualstudio/README.md` — install + build-from-source guide
- README "Editor Extensions" section now covers both VS Code and Visual Studio 2022

### Verified
- Both language servers respond to a real LSP `initialize` handshake from the exact VSIX bundle layout (Enma via `bin/` launcher + `server/dist`; AngelScript via `server/out` + bundled `server/node_modules`)

## [1.4.0] — 2026-06-17

### Added
- **Custom Draw API documentation** — full D3D11 GPU pipeline docs for both Enma (`docs/perception/custom-draw-api.md`) and AngelScript (`docs/perception/angelscript/custom-draw-api.md`): shaders, vertex/index buffers, depth testing, compute shaders, textures, render targets, mesh loading, backbuffer capture
- **Custom Draw API patterns** — 8 working GPU rendering patterns (`knowledge/custom-draw-patterns.md`): colored shapes, textured quads, 3D cubes, wireframe, glow/blur post-processing, compute shaders, multi-pass rendering, dynamic textures
- **Changelogs archive** — complete Perception.cx changelog (Feb–June 2026) in `docs/perception/changelogs.md` covering all Universal API and CS2 API updates
- **Community tools reference** — `knowledge/community-tools.md` documenting 5 MCP servers (perception-mcp, claude-ception, reclass-mcp, UE Docs MCP, Context7), VS Code extensions (Enma LSP, AngelScript LSP), and utilities (Claude Proxy, Custom GUI base)
- **Game targets reference** — `knowledge/game-targets.md` listing 29 supported games across 5 categories with engine info and considerations
- **Unreal Engine reversal guide** — `signatures/unreal-engine/ue-reversal-guide.md` covering GWorld/GObjects/GNames, Dumper-7 methodology, key UE structures, manual RE approach, and encryption considerations

### Changed
- **PCX API cheatsheet** — added all new API functions from Feb–June 2026 changelogs: Custom Draw API (largest section), world_to_screen variants, matrix double-precision, thread priority, atomics, GUI additions, Unicorn updates, Sound API, scan API fixes, XINPUT support, font glyph ranges
- **Documentation INDEX** — updated with all new files, Knowledge Base section, and Signatures section

### Deprecated (upstream)
- `source2_world_to_screen` → use `world_to_screen_rowmajor` or `world_to_screen_transposed`
- Default matrix4x4 read/write → use precision-specific variants (`readas_float`/`readas_double`)
- Perception IDE & Analyzer — being retired in favor of Perception MCP (60-70+ tools)

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
