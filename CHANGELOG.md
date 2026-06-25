# Changelog

## v1.18.0 - 2026-06-25

- chore: normalize provenance output
- chore: refresh generated hardening metadata
- fix: quiet workflow pyright diagnostics
- fix: satisfy mcp hardening ci
- feat: harden perception mcp workflows

## v1.17.0 - 2026-06-25

- fix(examples): document process permissions
- fix(ci): satisfy native permission gate
- fix(ci): restore validation fixtures
- fix(skills): add license metadata
- fix(validation): allow local routines
- fix(ci): refresh generated docs
- feat(ci): automate releases from main
- feat: operationalize perception mcp workflows
- chore: ignore local session artifacts
- chore: remove session plan artifacts
- feat: add perception mcp workflow planner
- feat: deepen anti-hallucination coverage
- fix: relax validator shape checks
- docs: redesign README
- feat: harden anti-hallucination evals
- feat: add anti-hallucination rails
- Merge remote-tracking branch 'origin/main' into docs/enma-gap-fixes
- feat(docs): add coverage rails
- Merge pull request #8 from VoidChecksum/docs/enma-gap-fixes
- docs: clarify Enma language limitations
- Merge pull request #7 from VoidChecksum/docs/enma-gap-fixes
- docs: clarify Enma documentation gaps
- Merge pull request #6 from VoidChecksum/docs/enma-gap-fixes
- docs: clarify Enma documentation gaps
- Merge pull request #5 from VoidChecksum/docs/enma-gap-fixes
- docs: clarify Enma documentation gaps
- ci: skip existing registry releases

All notable changes to this toolkit are documented here.

## [1.16.0] — 2026-06-18

### Added
- **Auto-update feature**:
  - `tools/update-toolkit.sh` (bash) and `tools/update-toolkit.ps1` (PowerShell) for cross-platform self-updating of the toolkit.
  - Automatically pulls from git remote, updates submodules, rebuilds LSP servers (`enma-lsp`, `angel-lsp-pcx`), refreshes AI skills, and checks/regenerates knowledge bundles.
  - Supports `--check` (no-op drift detection), `--force` (run hooks even if up to date), and `--skip-lsp`/`--skip-skills`/`--skip-bundles` flags.
- **Rust Tools Integration**:
  - Reimplemented the PE parsing core in Rust (`tools/pe-parser`) which compiles to `tools/bin/pe-parser`. It is used by `tools/lib/pe_parse.py` for incredibly fast, memory-safe, out-of-bounds protected PE parsing.
  - Reimplemented `sig-uniqueness-checker` in Rust (`tools/bin/sig-uniqueness-checker`), moving the performance-critical byte pattern scanning and near-miss calculations to compiled native code.
  - Provided seamless Python fallbacks for all ported tools, ensuring the toolkit remains 100% functional on platforms where Rust/Cargo is not installed.
- **Smoke test suite**:
  - `tools/test-runner.sh` — automates end-to-end smoke testing. Generates a valid mock 16KB x64 PE binary with import/export directories, walks sections, and runs all 13 tools to verify correct functionality and zero crashes.
- **Version tracking**:
  - Added `VERSION` file containing `"1.16.0"` to the repository root.

### Changed
- Refactored 8 PE-consuming python tools to import from the shared `tools.lib.pe_parse` library:
  - `anti-debug-scanner.py`
  - `binary-diff-summary.py`
  - `dump-strings-xor.py`
  - `identify-protector.py`
  - `module-export-mapper.py`
  - `offset-diff.py`
  - `pe-section-analyzer.py`
  - `sig-uniqueness-checker.py`
- `.github/workflows/ci.yml`:
  - Added syntax validation steps for `update-toolkit.sh` and `update-toolkit.ps1`.
  - Added compile checks for all python scripts under `tools/` and `tools/lib/`.
  - Added verification that `VERSION` file exists.
- `setup.sh` & `setup.ps1`:
  - Updated to print the currently installed toolkit version on setup complete.

## [1.15.0] — 2026-06-17

### Added — Indexed Knowledge Surfaces

Three complementary surfaces let any AI tool reach the toolkit's corpus efficiently. Use one, two, or all three depending on the tool's integration model. See `.claude/skills/pcx-knowledge-index/SKILL.md` for the decision tree.

**Static surface (auto-fetch convention):**
- `docs/llms.txt` (45 KB) — Anthropic / Mintlify `llms.txt` convention. Structured index of every doc / skill / knowledge file / IDE drop-in / template / signature guide / tool, grouped by category, with title + URL + 1-line description per entry. Tools that auto-fetch this convention (Claude, Cursor, others) discover the entire toolkit's surface from one file.

**Static surface (concatenated context packs):**
- `docs/llms-full.txt` (~2 MB) — entire toolkit content concatenated with stable separators and source paths preserved.
- `docs/llms-perception-enma.md` (~950 KB) — Enma language + APIs + Enma-discipline skills + cheatsheet. Single-file `@`-reference for tools working in Enma.
- `docs/llms-perception-angelscript.md` (~400 KB) — AngelScript APIs + AS discipline + cheatsheet.
- `docs/llms-perception-lua.md` (~215 KB) — Lua APIs + Lua discipline + cheatsheet.
- `docs/llms-skills.md` (~300 KB) — all 17 skills concatenated.
- `docs/llms-knowledge.md` (~350 KB) — all 20 knowledge references concatenated.

**Dynamic surface (MCP server):**
- `mcp/pcx-knowledge-mcp/` — Python MCP server exposing the corpus as searchable resources. Tools: `search(query, limit)` (keyword search with light TF-IDF scoring), `get_file(path)` (fetch by repo-relative path), `list_files(category)` (enumerate by category), `overview()` (top-level summary). Resources: every file as `file://<repo-path>`. 211 documents indexed; <100 ms cold load, <5 ms warm queries. Pure Python + the official `mcp` SDK (no vector DB, no embedding model, no external service). Install: `pip install -e mcp/pcx-knowledge-mcp/`. Config snippets for Claude Desktop, Cline, Cursor, Continue, Zed in the README.

**Generator tool:**
- `tools/build-llms-index.py` — stdlib-only Python; generates all 7 static bundles from the live source tree. Idempotent (re-running produces byte-identical output). `--check` flag detects drift between committed bundles and current source for CI gating.

**Decision-tree skill:**
- `.claude/skills/pcx-knowledge-index/SKILL.md` (220 lines) — names the three surfaces and the decision tree for which to reach for under which circumstances. Per-tool recipes (Claude Code / Claude Desktop / Cursor / Cline / Aider / Copilot / Continue / Zed). The "combine #2 + #5" recommendation: small upfront language-bundle + MCP search for everything else, the best of both for long sessions.

### Changed
- `.github/workflows/ci.yml` — new step `build-llms-index.py --check` enforces bundles stay in sync with source on every push. Doc-count check tightened to exclude generated bundles from the source-doc tally. Link checker now skips `docs/llms-*` bundles (they concatenate cross-directory content; relative links inside no longer resolve relative to `docs/`; source files are checked individually).
- README.md — AI Skills `17` → `18`; new "Indexed Knowledge Surfaces" subsection introduces the three surfaces; tree refreshed.
- `docs/INDEX.md` — new "Indexed Knowledge Surfaces" subsection at the top linking to all 7 bundles and the MCP server README.

## [1.14.0] — 2026-06-17

### Added
- **1 new RE tool** in `tools/`:
  - `binary-diff-summary.py` — high-level diff summary between two PE binaries (sister tool to `offset-diff.py`). Per-section table with `%SAME` / `%CHG` / `%NEW` / `%DEL` block counts (4 KB blocks, hash-based set comparison), `.text` classifier: `RECOMPILE` (>95% blocks identical → sigs likely survive, patch-day viable), `REFACTOR` (30-95% → many sigs break), `MAJOR_CHANGE` (<30% → full re-RE). Answers the patch-day prep question "how much did this binary actually change?" before you decide whether to patch or re-RE.
- **1 new AI skill** under `.claude/skills/`:
  - `pcx-debug-overlay` (330 lines) — the pattern for shipping diagnostic / profiler / address-dump info as a separate overlay routine gated behind a hotkey. 6 rules: two-overlays-always-separate, five-standard-sections (Process / Sigs / Runtime / Profile / Errors), hotkey-gated-off-by-default, read-only-diagnostics (lab features are separate), atomic counters for cross-routine state via `addon-atomic`, ship-two-builds (production + diagnostic via `#define BUILD_FLAVOR_DEBUG`). Cross-refs `pcx-perf-budget` (profiler recipe) and `gui-design-patterns` ("no debug panel by default").
- **1 new knowledge reference** under `knowledge/`:
  - `network-protocol-re.md` (296 lines) — packet-capture toolchain (Wireshark / tshark / mitmproxy / dumpcap / eBPF), message-boundary identification (length-prefixed / type-tagged / self-describing for TCP, sequence-numbered / type-prefixed / encrypted-blob for UDP), encoding scheme recognition (struct dump / length-prefixed strings / varint / protobuf-shaped / FlatBuffers / bit-packed / compressed), encryption recognition (TLS / DTLS / custom XOR / custom block cipher), wire-to-memory cross-referencing workflow, QUIC / HTTP3 capture options for modern AAA titles, Wireshark Lua dissector worked example. Authorized targets only — explicit scope callout to `skill://authorized-security-research`.
- **1 new template scaffold** under `templates/`:
  - `templates/full-project-as/` (4 files, 222 lines) — AngelScript parallel to the existing Enma `templates/full-project/`. `globals.as` (`proc_t@` handle, uint64 base/size, palette as 4 uint8s per AS draw API), `feature.as` (one tick callback combining update + read first / draws second), `main.as` (attach + resolve + `register_callback`, full `on_unload` deref cleanup per AS discipline rule #3), `README.md` documenting the differences from the Enma scaffold. Honors all 12 game-cheat-guidelines.
- **2 new MCP setup guides** under `mcp/`:
  - `zed-setup.md` (215 lines) — Zed editor integration (Rust-built AI-native editor, MCP via `context_servers` setting in `~/.config/zed/settings.json`, agent panel + `@file` references, Inline Assist, Edit Predictions, vim mode, multiplayer for pair-programming). Uses `mcp-remote` bridge to the authoritative HTTP MCP endpoint at `127.0.0.1:42069`.
  - `continue-setup.md` (210 lines) — Continue extension integration (open-source AI for VS Code / JetBrains, model-agnostic, MCP servers via `config.yaml`'s `mcpServers` block, multi-model config — separate models for chat / autocomplete / inline edit, local-model support via Ollama / vLLM).

### Changed
- README.md — AI Skills badge `16` → `17`; tree, skills box, knowledge box, templates list, MCP setups list, tools list refreshed.
- `docs/INDEX.md` — 1 new knowledge entry (`network-protocol-re.md`).

## [1.13.0] — 2026-06-17

### Added
- **3 new validation / build tools** in `tools/`:
  - `evidence-log-validator.py` — directly enforces `re-evidence-log` discipline. Cross-checks every offset / sig in an Enma module against per-binary evidence files (`evidence/<hash>.md`): catches offsets without `// E-NNN` citations, evidence entries no offset references (dead entries), and stale `last_verified` dates older than `--max-age-days` (default 180). Output categories `ERROR` / `WARN` / `INFO`; `--strict` promotes warnings to exit 1; `--evidence-dir` validates against all per-binary files at once.
  - `pre-ship-check.sh` — pure-bash implementation of the `script-bundler` Section 4 pre-ship hygiene checklist. 12 checks: hardcoded paths, debug `println` of raw addresses, TODO/FIXME/HACK/XXX markers, `fs_write_file` calls, network calls, suspicious `.emb` string artifacts, offset evidence-citation ratio, placeholder module name in `ref_process`, long commented-out blocks, LICENSE/README/CHANGELOG existence. `--strict` / `--quiet` / `--json` flags; portable across bash 4+ on Linux/macOS/WSL/Git Bash.
  - `script-linter.py` — light static check for the most-violated 12-guideline rules in `.em` files. Rule 1 (offsets cite evidence), Rule 7 (color/vec at file scope), Rule 11 (tunables without GUI widgets). Excludes offset/sig/stride constants from rule-11 firing via prefix list. Tight false-positive budget — rule 8 (f-suffix) intentionally narrowed by the implementing agent to avoid noise on legitimate `float64`-typed contexts. `--rules N,M` filter; `--severity error,warn,info`; `--json` machine output.
- **2 new AI skills** under `.claude/skills/`:
  - `ai-pair-programming` (291 lines) — the meta-workflow skill for working with Claude / Cursor / Cline / Aider / Copilot on PCX projects. 7 numbered techniques (read doc before code, cheatsheet first then per-API doc, plan before code on multi-file work, verify sigs with MCP not AI memory, in-prompt guideline reminder, diff-review every multi-file change, re-frame when stuck) plus per-tool quick recipes. Wraps all four IDE drop-ins (CLAUDE / CURSOR / CLINE / COPILOT).
  - `multi-binary-targeting` (444 lines) — one script supporting N game versions / architectures / storefronts / channels. 7 sections: runtime binary identification via `.text` hash, per-binary `offsets-<label>.em` + common `dispatch.em` re-export, sig sets vs hardcoded RVAs, x86 vs x64 abstraction with `ptr_read` helper, storefront detection via DRM-DLL fingerprint, channel variation handling, graceful degradation when no offset set matches. "When NOT to multi-target" heuristic: fork at >30% per-version sig overrides.
- **2 new knowledge references** under `knowledge/`:
  - `gui-design-patterns.md` (453 lines) — PCX sidebar GUI layout discipline beyond rule #11. Section organization (one feature per section), widget order within section, label conventions, slider range discipline (useful vs possible), defaults that work for first-time users, hotkey conventions (safe vs game-conflicting), color discipline (small palette per feature), state visibility, conditional widgets, debug-panel-not-by-default policy. Worked ESP-section example + anti-pattern flat list.
  - `pcx-cross-language-bridge.md` (183 lines) — Enma vs AngelScript vs Lua decision guide. At-a-glance comparison table (13 properties × 3 languages), per-use-case routing (render-path / stateful UI / quick prototyping / CPU math / network / cross-binary / coroutines), cross-language coordination patterns (files / host process / don't), performance notes (equivalent vs materially different), migration notes (Enma ↔ AS, Enma ↔ Lua, AS ↔ Lua), recommended defaults by project size.
- **`rules/COPILOT.md`** (116 lines) — GitHub Copilot drop-in (`.github/copilot-instructions.md` or per-workspace custom-instructions field). Parallel structure to CURSOR.md / CLINE.md with Copilot-specific notes: what Copilot is good at (inline completions, doc-comments, single-file pattern-following) and bad at (multi-file refactors, less-common API names, unprompted guideline enforcement). Steering pattern via `// from: docs/...` comments above the cursor.

### Changed
- README.md — AI Skills badge `14` → `16`; tree, skills box, knowledge box, rules section, tools list refreshed.
- `docs/INDEX.md` — 2 new knowledge entries (gui-design-patterns, pcx-cross-language-bridge).

## [1.12.0] — 2026-06-17

### Added
- **2 new RE tools** in `tools/` (stdlib-only Python, matches the round-1 contract):
  - `anti-debug-scanner.py` — flags anti-debug surfaces in a PE: direct-check imports (`IsDebuggerPresent` / `NtQueryInformationProcess` / `CheckRemoteDebuggerPresent`), PEB-walk byte patterns (`fs:[30h]` 32-bit, `gs:[60h]` 64-bit), `NtGlobalFlag` heap-flag CMP heuristic, RDTSC timing-loop pair detection, INT 2D + long INT 3 fill patterns, debug-register CONTEXT manipulation (Get/SetThreadContext + `CONTEXT_DEBUG_REGISTERS` literal), VEH chain manipulation, debugger process/window-class string scans (ASCII + UTF-16LE). Categorized output with `STRONG`/`SUSPICIOUS`/`INFO` severity, `--category` filter, `--json` mode.
  - `module-export-mapper.py` — list a PE's exports (ordinal | name | RVA, with mangled-name short hint) and optionally cross-reference which other PE files in a target directory import each export (`--consumers /game/dir/`). Detects PE forward exports (`FORWARD -> module.func`). `--filter`, `--ordinal-only`, `--json`. Exit 0 with a friendly message when the binary has no export directory (most EXEs).
- **3 new AI skills** under `.claude/skills/`:
  - `re-evidence-log` (313 lines) — every claimed offset / sig / struct layout cites its proof. 6 numbered rules (one file per binary, stable `E-NNN` entry IDs, required citation fields, sigs cite their disassembly context, structs cite SDK source + per-field confidence tier, `last_verified` dates, negative-result tracking) + paste-ready templates. Sits between `pcx-re-discipline` (the discipline) and `pcx-patch-day-playbook` (which writes per-patch entries into the log).
  - `script-bundler` (374 lines) — packaging and shipping workflow. When to ship `.em` vs `.emb` (with `serialize keep_debug=false` for path stripping), canonical bundle order (`globals → offsets → feature → menu → main`), hot-reload-safe boundaries (what survives a reload, what doesn't), greppable pre-ship hygiene checklist, runtime-version pinning via `#define PCX_REQUIRED_*`, distribution metadata (recipient `README` / `LICENSE` / `CHANGELOG` templates). The outbound counterpart to `pcx-patch-day-playbook`.
  - `mcp-tool-routing` (287 lines) — decision guide across the 37 Perception MCP tools. Organized by user goal (read N bytes / find something in memory / understand a function / understand a class / generate a sig / process+module info / file+script ops), with explicit cost tiers (cheap / medium / expensive / side-effecting) and named composition workflows (sig→validate, scan-string→find-refs→analyze, snapshot→action→diff). Closes the "which of the 37 tools for this task" gap.
- **3 new knowledge references** under `knowledge/`:
  - `engine-godot.md` (129 lines) — Godot 3.x / 4.x engine RE reference. Open-source advantage (pull matching headers from GitHub by version), node-tree + `ObjectDB` architecture, `.pck` payload + `GDPC` magic footer, per-game table (Brotato / Cassette Beasts / Halls of Torment / Slay the Princess / Cruelty Squad), reversal-workflow first-60-minutes, community tools (gdsdecomp, godot-pck-explorer, godot-cpp). Fills the 6th engine gap.
  - `pcx-version-matrix.md` (383 lines) — API availability matrix by PCX version, drawn from `docs/perception/changelogs.md`. Per-category since-version tables (Render 2D / Custom-Draw / Proc / Input / GUI / Sound / Net / Win / Filesystem / CPU / Zydis / Unicorn), removed/deprecated section with replacements (`source2_world_to_screen` → `world_to_screen_rowmajor`), language-version quirks (Enma / AngelScript / Lua), reverse-chronological release timeline. Every claim cites a changelog row or is marked `unknown` — no invented versions.
  - `script-organization-patterns.md` (549 lines) — multi-file Enma project organization beyond `templates/full-project/`. Shared state placement rules, per-binary offset modules, JSON config persistence (using real `json_*` / `fs_*` APIs), multi-script coordination, utility module extraction heuristic ("3 uses → extract; 2 → leave duplicated"), feature toggles, module-version pinning, dead-code policy, the 20-feature project shape. Companion to the 5-file scaffold.
- **2 new infrastructure drop-ins**:
  - `rules/CLINE.md` (115 lines) — Cline (VS Code AI agent) custom-instructions drop-in, parallel to `rules/CURSOR.md`. Cline-specific notes on auto-approval gating (read-only MCP tools safe, write/execute tools gated), Plan/Act mode workflow, token-budget guidance (`@`-reference specific docs vs preloading), checkpoint discipline before side-effecting operations.
  - `mcp/aider-setup.md` (227 lines) — Aider CLI integration guide. Setup via `pipx install aider-chat`, project config in `.aider.conf.yml` (model, always-loaded `read:` doc list, `auto-commits`), `CONVENTIONS.md` wiring (copy or symlink `rules/CLAUDE.md`), typical workflow walkthrough, MCP-handoff strategy (Aider for script edits + Perception IDE for live MCP), `--map-tokens` guidance for the 35k-line doc corpus.

### Changed
- README — AI Skills count `11` → `14`; tree, skills box, knowledge box, templates list, tools list, and MCP-supported-tools section refreshed.
- `docs/INDEX.md` — 3 new knowledge entries (engine-godot, pcx-version-matrix, script-organization-patterns) added under their respective subsections.
- `mcp/perception-mcp-config.json` — unchanged; `mcp-tool-routing` skill cross-references its 37-tool list authoritatively.

## [1.11.0] — 2026-06-17

### Added
- **4 new RE tools** in `tools/` (stdlib-only Python, matches the existing tool-shape contract):
  - `offset-diff.py` — diff named sigs between two binary versions. Reads a `sigs.json` list of `{name, pattern, kind: direct|rip, rip_offset, insn_len}` entries, scans both binaries' executable sections, RIP-resolves where requested, prints a status table per sig (`UNCHANGED` / `MOVED` / `LOST_IN_NEW` / `NEW_IN_NEW` / `MULTIPLE_HITS_*`) with the signed delta. JSON output for scripting. **The patch-day workflow's missing tool.**
  - `sig-uniqueness-checker.py` — verdict per candidate sig: `UNIQUE` (with margin), `AMBIGUOUS` (with all hit addresses + 16-byte context for each), `STALE` (with `--near-misses N` reporting wildcarded variants that do hit), `BRITTLE` (margin=0, one byte from collision). Batch mode via `--sig-file name=sig` lines, section filtering, JSON output. **Closes the "is my sig still good after this patch?" loop in seconds.**
  - `pattern-format-converter.py` — round-trips byte patterns between 8 formats: `ida`, `ghidra`, `x64dbg`, `ce` (Cheat Engine AOB), `enma` (quoted literal), `cstyle` (`\x..` + mask), `bytes` (Python `b"..."`), `sig_mask` (separate). `--to all` dumps every format at once. Strict validation rejects odd-length hex / unknown chars. **The per-session paper cut.**
  - `dumper-to-enma.py` — converts community-dumper output into a paste-ready `offsets.em` module. Auto-detects Dumper-7 (UE), IL2CPPDumper (Unity, parses `// RVA:` annotations above struct fields), hazedumper (Source-style JSON/YAML), Source2Gen-style flat JSON, and Cheat Engine `.CT` tables. Outputs `const uint64 OFFSET_X = 0x...;` for fields, `const string SIG_Y = "...";` for sigs, category headers per source struct. `--module-name`, `--prefix`, `--out`, `--json`. **Bridges the dumper ecosystem to PCX.**
- **5 new AI skills** under `.claude/skills/`:
  - `pcx-angelscript-discipline` (406 lines) — AngelScript-specific companion to `game-cheat-guidelines`. 10 numbered rules covering handles vs values (`Type@`), `deref()` requirement, `&out` parameter syntax, `array<T>` / `dictionary` containers, raw RGBA ints in draw calls, `register_callback` signature and hot-reload boundaries. Closes the gap where the AI defaulted to Enma idioms inside `.as` files.
  - `pcx-lua-discipline` (369 lines) — Lua-specific companion. 10 numbered rules: 64-bit integer subtype handling for addresses, `0`-is-truthy versus return-checking, table-as-array-or-map discipline, metatable boundaries for PCX userdata, function-value callback registration, closure-over-loop-variable trap, `pcall` for risky reads, hot-reload-safe globals via the package add-on.
  - `pcx-patch-day-playbook` (289 lines) — the ordered triage workflow when a game update breaks the script. Seven steps: snapshot first → `offset-diff.py` triage → bisect the cascade (process / base / first-sig / RIP / read in dependency order) → re-sig with `--near-misses` → re-verify RIP math (instruction-length drift is half of patch breakage) → live-target validation → patch-log entry. Decision matrix for when to patch vs when to re-RE from scratch.
  - `pcx-streamproof` (185 lines) — capture compatibility for PCX overlays. Maps the three capture categories (process-internal swap-chain hook / desktop-composited DXGI / signal-level HDMI) against the render surfaces PCX exposes; explains why "OBS Game Capture didn't see it but Discord screenshare does" is a capture-path mismatch, not a bug. Pre-stream checklist, differential-diagnosis script for the "friend on Discord sees my menu" report.
  - `pcx-perf-budget` (323 lines) — turns `game-cheat-guidelines` rule #4 into numeric targets. Per-refresh-rate frame budgets (60 / 120 / 144 / 240 / 360 Hz), per-call cost rules of thumb (cross-process reads = expensive, draws + math = cheap), drop-in `profile_begin/end` recipe using `mono_us()` with fixed bucket accumulators and second-window dumps, read-coalescing examples (single `read_memory` struct-dump vs N scalar reads), cache-what / recompute-what matrix.
- **5 new knowledge references** under `knowledge/`:
  - `aimbot-math.md` (554 lines) — the math half of `common-patterns.md` (which only covers W2S). Angle calc (`atan2`, engine conventions), wrap-around delta `((d+540)%360)-180`, FOV cone (3D dot + 2D pixel), target selection (screen / angular / world / hybrid), ordered validation gate (cheap checks first, traces last), linear and gravity-aware prediction (closed-form quadratic intercept), recoil compensation, smoothing (linear / exponential / SmoothDamp), radians-vs-degrees and handedness pitfalls. Full Enma snippets using `vec3`, `atan2`, real `proc_t` reads.
  - `engine-cryengine.md` (250 lines) — CryEngine family (Hunt: Showdown, Star Citizen, Kingdom Come): `gEnv` global anchor, entity system, camera math; reversal workflow first-60-minutes; anti-cheat coverage.
  - `engine-frostbite.md` (255 lines) — DICE/EA Frostbite (Battlefield, FIFA / FC25, Anthem, Mass Effect Andromeda): data-driven entity bus, manager-chain layout, RenderView camera model; EAAC kernel-level integration notes.
  - `engine-re-engine.md` (250 lines) — Capcom RE Engine (RE2/3/4 remakes, Monster Hunter Rise/Wilds, Street Fighter 6, Dragon's Dogma 2): reflected `via.*` type system, REFramework parsing layer, anti-tamper landscape (Denuvo + SF6 kernel AC).
  - `engine-redengine.md` (253 lines) — CD Projekt Red REDengine (Cyberpunk 2077 on RED4, Witcher 3 on RED3): RTTI/reflection system, REDscript gameplay VM, fixed-point world-coord quirk, RED4ext / Cyber Engine Tweaks parsing layer. Note: Witcher 4 / Polaris move to UE5 — out of scope for this file.
- **2 new templates** under `templates/`, both following all 12 game-cheat-guidelines:
  - `aimbot-skeleton.em` (180 lines) — FOV-based closest-target picker with one-shot sig resolution, null-guarded entity walk, RIP-relative resolver, `world_to_screen_rowmajor` for projection, write-free aim via `mouse_move_relative`, full GUI binding for every tunable. UNVERIFIED placeholders for target-specific offsets.
  - `minimap.em` (180 lines) — rotation-aware player-relative radar with rim clamping, GUI-tunable scale and screen position, pre-sized read-side caches (legitimate caching, distinct from per-frame color/vec construction), correct `-yaw` rotation math (cross-referenced with `knowledge/aimbot-math.md`).
- **`rules/CURSOR.md`** — drop-in `.cursorrules` companion to `rules/CLAUDE.md`, parallel structure tailored for Cursor's tighter token budget. References `mcp/cursor-setup.md` for MCP wiring without duplicating it; references `rules/KARPATHY.md` for workflow discipline.

### Changed
- README — AI Skills count `6` → `11`; directory tree updated to show new tools, skills, knowledge files, and templates; "AI Skills" section enumerates the five new ones with one-line descriptions.
- `docs/INDEX.md` — added the 5 new knowledge files (4 engines + aimbot-math) under a new "Engine RE References" subsection.
- `.claude/skills/game-hacking-pcx` — cross-references added to the new skills (angelscript / lua / patch-day / streamproof / perf-budget) and the new tools (`offset-diff.py`, `sig-uniqueness-checker.py`, `pattern-format-converter.py`, `dumper-to-enma.py`).

## [1.10.0] — 2026-06-17

### Added
- **`tools/` directory** — standalone RE tools, zero external dependencies (stdlib Python only):
  - `identify-protector.py` — detect VMProtect/Themida/UPX/Enigma/Obsidium/ASPack/etc. by PE section names, byte signatures (VM entry stubs, RDTSC pairs, PEB.BeingDebugged, INT 2D), import analysis, and packing heuristics. JSON output mode for scripting.
  - `pe-section-analyzer.py` — per-section entropy analysis with visual bar graph, packed-section detection (VS/RS ratio), writable+executable flags, empty-on-disk sections, overlay detection. Tested on 237MB PE.
  - `resolve-api-hashes.py` — resolve API hashes used by obfuscated binaries for dynamic import resolution. 6 algorithms (ROR13+ADD, CRC32, DJB2, FNV-1a, MurmurHash3-32, SDBM), 1,560 precomputed hashes across 130 common Windows APIs. Batch mode, binary scan mode (finds hash constants in .text).
  - `dump-strings-xor.py` — extract XOR-encrypted strings by brute-forcing single-byte keys (0x01–0xFF), scoring by printable ASCII ratio, filtering junk. Per-section targeting, known-key mode, JSON output.
  - `install-re-tools.sh` — one-command installer: clones 17 repos (IDA plugins: hrtng, CodeXplorer, ClassInformer, SigMakerEx, FIRST, RevEng.AI, D-810, HashDB, Diaphora; Ghidra: GhidrAssist, BinDiffHelper, Pharos, RevEng.AI; deobf: NoVmp, VTIL, ScyllaHide, Scylla, pe-sieve; sync: ret-sync; sigs: FLIRTDB, sig-database), installs Python packages (capstone, unicorn, keystone, pefile, lief, triton, miasm, floss, frida, angr), copies plugins to `~/.idapro/plugins/` and FLIRT sigs to IDA sig dirs.

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
