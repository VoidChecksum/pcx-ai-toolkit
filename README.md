# pcx-ai-toolkit

AI-powered scripting toolkit for the [Perception.cx](https://perception.cx) platform. Complete documentation, coding guidelines, MCP server configs, LSP language servers, code templates, and drop-in AI skills for Claude Code, Cursor, and Cline.

Covers **Enma** (.em), **AngelScript** (.as), **Lua**, and **C++** — every language Perception.cx supports.

## What's Included

| Component | Description |
|-----------|-------------|
| **Documentation** | 33,580 lines across 104 markdown files — the complete Enma language spec, SDK embedding guide, all 18 standard library addons, and every Perception.cx API (Proc, Render, GUI, Input, CPU, Zydis, Unicorn, Net, Win, Filesystem, Sound, MCP) for Enma, AngelScript, and Lua |
| **AI Skills** | Two Claude Code skills: `game-hacking-pcx` (API doc index + coding rules) and `game-cheat-guidelines` (12 behavioral rules for correct, maintainable scripts) |
| **Rules** | Drop-in `CLAUDE.md` and `AGENTS.md` for any PCX scripting project |
| **Knowledge Base** | Enma cheatsheet, PCX API cheatsheet, common scripting patterns with full working examples, offset-finding methodology |
| **MCP Configs** | Perception.cx MCP server config for Claude Code and Cursor — connects the AI to live process memory tools |
| **LSP Servers** | Enma LSP and AngelScript+PCX LSP as git submodules (auto-built by setup.sh) |
| **Signatures** | Example Source Engine signature patterns with methodology documentation |
| **Templates** | Starter project scaffold and individual feature templates |

## Quick Start

```bash
git clone https://github.com/youruser/pcx-ai-toolkit.git
cd pcx-ai-toolkit
./setup.sh
```

This will:
1. Clone and build the Enma and AngelScript LSP servers
2. Install AI skills to `~/.claude/skills/` (if Claude Code is detected)
3. Print a summary of everything available

Then copy `rules/CLAUDE.md` into your PCX scripting project and start coding.

## Directory Structure

```
pcx-ai-toolkit/
├── .claude/skills/                 # AI skills (auto-trigger on PCX work)
│   ├── game-hacking-pcx/           #   Full doc index + API rules
│   └── game-cheat-guidelines/      #   12 behavioral coding rules
├── docs/                           # Complete offline documentation
│   ├── enma/                       #   Language ref, addons, SDK (48 files, 13,166 lines)
│   └── perception/                 #   Platform APIs for Enma, AngelScript, Lua
│       ├── *.md                    #     Enma APIs (16 files, 3,815 lines)
│       ├── angelscript/            #     AngelScript APIs (23 files, 10,820 lines)
│       └── lua/                    #     Lua APIs (17 files, 5,779 lines)
├── knowledge/                      # Quick references and patterns
│   ├── enma-cheatsheet.md          #   Language quick reference
│   ├── pcx-api-cheatsheet.md       #   All PCX APIs at a glance
│   ├── common-patterns.md          #   Working code examples for common features
│   └── offset-methodology.md       #   How to find and maintain offsets
├── mcp/                            # MCP server configurations
│   ├── perception-mcp-config.json  #   Perception MCP for Claude Code
│   ├── claude-code-setup.md        #   Claude Code integration guide
│   └── cursor-setup.md             #   Cursor integration guide
├── rules/                          # Drop-in project rules
│   ├── CLAUDE.md                   #   For Claude Code projects
│   └── AGENTS.md                   #   Agent definitions
├── lsp/                            # Language servers (git submodules)
│   ├── enma-lsp/                   #   Enma LSP (syntax, completion, hover, diagnostics)
│   └── angel-lsp-pcx/             #   AngelScript+PCX LSP
├── signatures/                     # Byte signature examples
│   └── source-engine/
│       └── common-sigs.md
├── templates/                      # Starter templates
├── setup.sh                        # One-command install
├── LICENSE                         # MIT
└── README.md
```

## Documentation Coverage

| Corpus | Files | Lines | What's Covered |
|--------|-------|-------|----------------|
| Enma Language | 10 | 3,150 | Types, operators, control flow, functions, pointers, structs, classes, templates, advanced features, annotations, modules, preprocessor, semantics |
| Enma Addons | 18 | 2,528 | Core, strings, arrays, maps, math, SIMD, vectors, 3D math, variant, atomic, bits, time, regex, file, thread, hash_set, sorted_map, list, JSON |
| Enma SDK | 17 | 3,795 | Engine lifecycle, compilation, execution, type registration, native functions, hot reload, serialization, introspection, RAII, debug, safety, custom addons |
| Enma Single-Page Refs | 2 | 3,693 | `llms-language.md` (complete language) + `llms-sdk.md` (complete SDK) |
| PCX Enma APIs | 16 | 3,815 | Proc, Render, GUI, Input, CPU, Zydis, Unicorn, Net, Win, Filesystem, Sound, Lifecycle, MCP, IDE, Extensions, Analyzer |
| PCX AngelScript APIs | 23 | 10,820 | Same API surface in AngelScript syntax |
| PCX Lua APIs | 17 | 5,779 | Same API surface in Lua syntax |
| **Total** | **104** | **33,580** | |

## Supported AI Tools

| Tool | Integration | How |
|------|-------------|-----|
| **Claude Code** | Skills + CLAUDE.md + MCP | `setup.sh` auto-installs; see `mcp/claude-code-setup.md` |
| **Cursor** | .cursorrules + MCP + docs | Copy CLAUDE.md to .cursorrules; see `mcp/cursor-setup.md` |
| **Cline** | MCP + system prompt | Use MCP config + paste CLAUDE.md into system prompt |
| **Perception IDE** | Native | Built-in AI already has tool access; add `docs/` as workspace folder for context |

## The 12 Guidelines

| # | Rule | One-liner |
|---|------|-----------|
| 1 | Ground every offset | Cite the source — sig, SDK header, or IDA xref |
| 2 | `uint64` for all addresses | No sign-extension bugs |
| 3 | Validate every pointer | Check for 0 before dereferencing |
| 4 | Separate update from render | No memory reads in the draw path |
| 5 | Sigs over hardcodes | Survive game patches |
| 6 | One feature, one file | No monolith scripts |
| 7 | Construct colors/vecs every frame | They're 4-8 byte stack values |
| 8 | `f` suffix on float32 literals | The GPU cares |
| 9 | Minimize memory writes | Reads leave no trace |
| 10 | World-to-screen once, correctly | Check `w > 0`, match engine matrix layout |
| 11 | GUI for all tunables | No magic constants in code |
| 12 | Verify with live reads | Trust the binary, not cached offsets |

## Contributing

1. Fork and clone
2. Add docs, patterns, templates, or sigs
3. Test with `./setup.sh` on a clean clone
4. Open a PR

Documentation updates are especially welcome — if you've reversed an API or found a new pattern, add it.

## License

MIT. See [LICENSE](LICENSE).

## Credits

- [Perception.cx](https://perception.cx) — the platform and Enma language
- [Enma Documentation](https://enma-1.gitbook.io/enma) — language specification
- [sinnafuls/enma-lsp](https://github.com/sinnafuls/enma-lsp) — Enma language server
- [sinnafuls/angel-lsp-pcx](https://github.com/sinnafuls/angel-lsp-pcx) — AngelScript+PCX language server
