---
name: pcx-knowledge-index
description: >
  Guide to the three surfaces (llms.txt static index, bundle files, MCP
  server) through which AI tools reach the toolkit corpus, and which to pick
  under which integration model. Always active when working with the
  pcx-ai-toolkit knowledge base from any AI tool (Claude Code, Cursor, Cline,
  Aider, Copilot, Continue, Zed).
license: MIT
---

# PCX Knowledge Index — The Three Ways AI Tools Reach the Toolkit's Corpus

The toolkit publishes its docs / skills / knowledge / templates / tools via three complementary surfaces, each optimized for a different AI-tool integration model. This skill names which surface to reach for under which circumstances, so a session doesn't waste tokens preloading a 4 MB bundle when MCP search would do, and doesn't fail mid-task because the tool only supports `@`-file references and you reached for a search call instead.

**Always active when working with the pcx-ai-toolkit corpus from an AI tool.** Applies to Claude Code, Claude Desktop, Cursor, Cline, Aider, Copilot, Continue, Zed, and any other AI tool that consumes external knowledge.

**Prerequisite:** `tools/build-llms-index.py` (the generator for the static surface), `mcp/pcx-knowledge-mcp/` (the dynamic surface), the per-IDE drop-ins (`rules/CLAUDE.md`, `rules/CURSOR.md`, etc.) for how each tool wires in its preferred surface.

---

## Trigger

About to load the toolkit's docs into AI context, the user asked which doc to use, the AI is preloading too much / too little context, deciding whether to ship the toolkit content as bundles vs MCP server vs both, debugging "the AI doesn't know about the PCX X API," configuring a new AI tool to consume the toolkit.

---

## The Three Surfaces

### 1. `llms.txt` — the Auto-Fetch Convention

Located at `docs/llms.txt` (also `docs/llms-full.txt` for the full bundle).

**What it is.** A structured plain-text index of the entire toolkit, following the Anthropic / Mintlify `llms.txt` convention. ~45 KB; lists every doc, skill, knowledge file, IDE drop-in, template, signature guide, and tool with its title, URL, and one-line description grouped by category.

**Who uses it.** Tools that auto-fetch this convention from a project's root:
- Claude (when given a repo URL, often auto-fetches `<repo>/llms.txt`)
- Cursor (configurable)
- Cline (via project context)
- Several others, growing

**When to reach for it.** First-touch with a new tool, or any time you want the tool to discover the toolkit's surface area without manually `@`-referencing every file.

**Cost.** ~45 KB of context (the index, not the full content). Tiny relative to the value.

### 2. Concatenated Context Packs — the Bundle Surface

Located at `docs/llms-full.txt`, `docs/llms-perception-{enma,angelscript,lua}.md`, `docs/llms-skills.md`, `docs/llms-knowledge.md`.

**What it is.** Per-language and per-category single-file concatenations of the relevant subset of the toolkit. Each file carries every member document inline with stable separators and the original source path preserved.

| Bundle | Scope | Size |
|---|---|---:|
| `llms-full.txt` | Everything (docs / skills / knowledge / rules / templates / signatures) | ~2 MB |
| `llms-perception-enma.md` | Enma language + APIs + Enma-discipline skills + cheatsheet | ~950 KB |
| `llms-perception-angelscript.md` | AngelScript APIs + AS discipline + cheatsheet | ~400 KB |
| `llms-perception-lua.md` | Lua APIs + Lua discipline + cheatsheet | ~215 KB |
| `llms-skills.md` | All 17 skills concatenated | ~300 KB |
| `llms-knowledge.md` | All 20 knowledge references concatenated | ~350 KB |

**Who uses it.** Any tool that accepts a single file as context:
- Aider (`/read docs/llms-perception-enma.md`)
- Copilot (paste-into custom instructions, or `@file` reference)
- Cursor (`@docs/llms-perception-enma.md`)
- Continue (`@files`)
- Any AI editor that has a "load file as context" surface

**When to reach for it.** Tools without MCP support, sessions where you know upfront which language you'll work in (load the matching pack), or anywhere the AI client is stateless across calls and you want a known-fixed context surface.

**Cost.** The chosen bundle's full byte cost loaded into context. The per-language bundles are much smaller than `llms-full.txt`; default to the per-language pack unless you're working across all three.

### 3. The Knowledge MCP Server — the Dynamic Surface

Located at `mcp/pcx-knowledge-mcp/` (Python package).

**What it is.** An MCP server exposing four tools (`search`, `get_file`, `list_files`, `overview`) and every file as a `file://<repo-path>` resource. Search is keyword-based with light TF-IDF scoring, runs in-process, no embeddings model, no external service. Returns ranked `{path, score, snippet}` results.

**Who uses it.** Any MCP-aware tool:
- Claude Desktop
- Cline
- Cursor (MCP support varies by version)
- Continue
- Zed
- Custom MCP clients

**When to reach for it.** Long sessions where you'll touch many files unpredictably, sessions where you don't know upfront which docs you need, or any time you want lazy loading instead of preload-everything. The AI calls `search("entity list walk")` first, then `get_file(top_hit)` — only the relevant slice ends up in context.

**Cost.** One running Python process. Per-query latency <50ms cold, <5ms warm. Memory: ~5-10 MB resident.

---

## The Decision Tree

```
Which surface should I use right now?

  ┌─ Is the AI tool MCP-aware AND will the session span many files?
  │
  ├── YES → MCP server (mcp/pcx-knowledge-mcp/)
  │        Configure once per client; the AI searches lazily.
  │        Examples: Claude Desktop, Cline, Continue.
  │
  └── NO  → continue
            │
            ├─ Will the session work primarily in ONE language (Enma / AS / Lua)?
            │
            ├── YES → the matching per-language bundle (docs/llms-perception-<lang>.md)
            │        Smallest preload that covers the typical session.
            │        Examples: Aider /read, Cursor @file, Continue @files.
            │
            └── NO  → continue
                      │
                      ├─ Does the tool auto-fetch llms.txt conventions?
                      │
                      ├── YES → let it; no manual setup needed.
                      │        Examples: Claude when given the repo URL.
                      │
                      └── NO  → load docs/llms-full.txt (~2 MB) or
                                a category-specific bundle (llms-skills.md / llms-knowledge.md).
```

The choices are not exclusive — combining the MCP server with a small upfront bundle (e.g. `llms-perception-enma.md` for "you work in Enma" baseline + MCP for "and you can search the rest") is the recommended setup for long, complex sessions.

---

## Recipe per AI Tool

### Claude Code (this tool)

- Primary: skills auto-load; this skill IS one of them.
- For specific docs: `@`-reference by path, or use the perception MCP (the runtime one in `mcp/perception-mcp-config.json` — not the knowledge one). The knowledge MCP is more useful for Claude Desktop than Claude Code.

### Claude Desktop

- **Wire the knowledge MCP** (see `mcp/pcx-knowledge-mcp/README.md` for the JSON config).
- Optionally also drop `docs/llms-perception-enma.md` content into Claude Desktop's "Files" feature for persistent context.

### Cursor

- **First choice**: `@docs/llms-perception-<lang>.md` per session, scoped to the language.
- **For wider exploration**: configure the knowledge MCP via `.cursor/mcp.json`.
- The `.cursorrules` file (`rules/CURSOR.md`) handles project-rule baseline.

### Cline

- **Wire the knowledge MCP** via `cline_mcp_settings.json` (see `rules/CLINE.md`).
- Use Plan mode + the MCP's `search` tool to explore before any edits.
- Auto-approve read-only MCP tools (search, get_file, list_files, overview) — they're safe.

### Aider

- **Per-session**: `/read docs/llms-perception-enma.md` (or matching language pack).
- For broader work: `/read docs/llms-full.txt` (large; only when you'll truly use the breadth).
- Pair with `CONVENTIONS.md` carrying `rules/CLAUDE.md` content.
- The knowledge MCP works but Aider's MCP support is newer/less mature than Continue's or Cline's.

### Copilot

- **Wire `.github/copilot-instructions.md`** with `rules/COPILOT.md` content.
- For session context: paste `docs/llms-perception-<lang>.md` excerpts into the chat (Copilot Chat) when working on a specific area.
- Copilot doesn't speak MCP, so the static bundles are the only surface.

### Continue

- **Wire the knowledge MCP** via `.continue/config.yaml` `mcpServers` block.
- Pin `knowledge/pcx-api-cheatsheet.md` as always-loaded context via Continue's per-project config.

### Zed

- **Wire the knowledge MCP** via `~/.config/zed/settings.json` `context_servers`.
- For agent panel: `@`-reference docs as needed; the MCP search handles the discovery half.

---

## When the Bundles Drift

The static bundles (`docs/llms*.{txt,md}`) are generated by `tools/build-llms-index.py`. If you commit changes to docs / skills / knowledge / etc. *without* regenerating the bundles, they go stale. The fix:

```bash
python3 tools/build-llms-index.py          # regenerate
git add docs/llms*
git commit
```

CI runs `python3 tools/build-llms-index.py --check`; the build fails on drift. This is the same discipline as committing a generated lockfile or compiled-protobuf — if you change the source, regenerate the artifact.

---

## When You Don't Need the Index at All

For one-off lookups of a specific known doc, just read the file directly. The whole indexing apparatus is for the case where the AI doesn't know what's there to read; if you (the human) know the path, just `read docs/perception/render-api.md` and skip the index entirely.

The index also doesn't help with content the toolkit doesn't have — if you're working on a different PCX runtime version with different APIs, the toolkit's docs are the wrong source regardless of which surface you reach them through. See `knowledge/pcx-version-matrix.md` for the version dimension.

---

## Summary

| # | Surface | When to use | Cost |
|---|---|---|---|
| 1 | `docs/llms.txt` | First-touch with a new tool; auto-fetch convention | ~45 KB context |
| 2 | `docs/llms-perception-<lang>.md` | One-language session in a non-MCP tool | ~215-950 KB context |
| 3 | `docs/llms-full.txt` | All-language session in a non-MCP tool | ~2 MB context |
| 4 | `docs/llms-skills.md` / `llms-knowledge.md` | Skills- or knowledge-focused session | ~300-350 KB context |
| 5 | `mcp/pcx-knowledge-mcp/` server | MCP-aware tool, long session, lazy loading | One running process |

**Combine #2 + #5** for the best of both: small upfront context for your primary language + searchable depth for everything else. Recommended for long sessions.

**Cross-references:** `tools/build-llms-index.py` (generates the static bundles), `mcp/pcx-knowledge-mcp/` (the server + install guide), `.claude/skills/mcp-tool-routing/SKILL.md` (which Perception runtime MCP tool for which task — different MCP, different purpose), `.claude/skills/ai-pair-programming/SKILL.md` (the meta-workflow this skill slots into at the "load context" step).
