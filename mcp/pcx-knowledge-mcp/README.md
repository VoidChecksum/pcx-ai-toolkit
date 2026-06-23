# pcx-knowledge-mcp

MCP server exposing the pcx-ai-toolkit corpus — docs, skills, knowledge references, IDE drop-ins, templates, and tool source — as a searchable surface for any MCP-aware AI tool.

The "indexed database all LLMs can query" half of the toolkit's LLM-knowledge story. The other half is the static `docs/llms.txt` + concatenated context-pack bundles, which work for tools that don't speak MCP. Use both together; they cover the full spectrum of how AI tools consume external knowledge.

## What It Exposes

**Tools** (MCP-callable functions):

| Tool | Purpose |
|---|---|
| `search(query, limit=10)` | Keyword search across the entire corpus. Returns ranked `{path, score, snippet}` JSON. |
| `get_file(path)` | Fetch full content of any file by repo-relative path. |
| `list_files(category="")` | Enumerate files, optionally filtered by category (`docs`, `skills`, `knowledge`, `rules`, `templates`, `tools`, `signatures`, `mcp`, `evals`). |
| `overview()` | Top-level toolkit summary with file counts per category and starting-point recommendations. |
| `list_skills()` | Enumerate bundled AI skills by stable name, path, and description. |
| `get_skill(name)` | Fetch one bundled skill by name, e.g. `pcx-enma-discipline`. |
| `recommend_context(task, language="")` | Return the smallest useful doc/skill/tool load plan for a task before loading large bundles. |
| `api_lookup(symbol, language="")` | Exact source-backed lookup for a function, method, or type. Returns signatures, language availability, official source URLs, and typo suggestions. |
| `validate_code(code, language, source_path="")` | Check a code snippet against the PCX API index. Catches unknown functions, wrong-language symbols, unknown types, and missing Enma imports. Returns `{findings, ok}` with source-backed repair context. |
| `validate_answer(answer, source_path="answer.md")` | Validate fenced Enma/AngelScript code blocks inside a generated Markdown answer before copying it into a project. |
| `list_project_templates(language="")` | List supported Enma/AngelScript scaffold kinds. |
| `generate_script_plan(task, language, kind, target_process, engine)` | Return docs, skills, commands, and scaffold choice without writing files. |
| `scaffold_project(...)` | Dry-run by default; can write a checked-in template scaffold when `dry_run=false` and `output_dir` is supplied. |
| `validate_project(path, allow_placeholders=false, allow_unverified=false)` | Run project-wide lint, symbol-check, hygiene, and evidence gates. |
| `suggest_imports(code, language="enma")` | Return exact missing Enma addon imports from validation findings. |
| `explain_finding(finding_json, language="")` | Turn one validator finding into a concrete fix. |
| `offset_drift_report(old_offsets_json, new_offsets_json)` | Compare named offset snapshots and classify moved/missing/new offsets. |

**Resources** (MCP-fetchable URIs):

- `file://<repo-relative-path>` — every file in the corpus, addressable directly.

## Install

```bash
# From the repo root:
pip install -e mcp/pcx-knowledge-mcp/

# Verify:
pcx-knowledge-mcp --help    # exits 0 if installed
```

Or install the MCP SDK and point your client at the server script directly:

```bash
pip install mcp
# then in your MCP client config, point at:
#   /absolute/path/to/pcx-ai-toolkit/mcp/pcx-knowledge-mcp/server.py
```

The server uses Python stdlib for everything except the official `mcp` SDK (`pip install mcp`). No vector database, no embeddings model, no external service — keyword search with light TF-IDF-style scoring runs entirely in-process. Index loads in <100ms on a typical machine; cold queries return in <50ms.

## Configure Your AI Tool

### Claude Desktop

In `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "pcx-knowledge": {
      "command": "pcx-knowledge-mcp"
    }
  }
}
```

If you installed via `pip install -e` and the script isn't on PATH:

```json
{
  "mcpServers": {
    "pcx-knowledge": {
      "command": "python3",
      "args": ["/absolute/path/to/pcx-ai-toolkit/mcp/pcx-knowledge-mcp/server.py"]
    }
  }
}
```

### Cline (VS Code)

In `cline_mcp_settings.json` (Settings → MCP Servers → Configure MCP Servers):

```json
{
  "mcpServers": {
    "pcx-knowledge": {
      "command": "pcx-knowledge-mcp"
    }
  }
}
```

### Cursor

In `.cursor/mcp.json` at the project root, or in Cursor settings:

```json
{
  "mcpServers": {
    "pcx-knowledge": {
      "command": "pcx-knowledge-mcp"
    }
  }
}
```

### Continue (VS Code / JetBrains)

In `.continue/config.yaml`:

```yaml
mcpServers:
  - name: pcx-knowledge
    command: pcx-knowledge-mcp
```

### Zed

In `~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "pcx-knowledge": {
      "command": {
        "path": "pcx-knowledge-mcp",
        "args": []
      },
      "settings": {}
    }
  }
}
```

## Typical Workflow

Without the knowledge MCP, the AI workflow is "I think I need `docs/perception/render-api.md`, let me read it" — relying on the AI to guess the right file path.

With it:

1. **Plan the load.** `recommend_context("write an ESP overlay", "enma")` returns the minimal skills, docs, and tools to use.
2. **Load the skill and docs.** `get_skill("game-cheat-script-master")`, then `get_file(...)` for the listed docs.
3. **Search only when needed.** `search("world to screen row-major matrix")` finds relevant supporting references without guessing paths.
4. **Check proposed API names.** `api_lookup("draw_text", "enma")` verifies exact signatures and source URLs before code is written.
5. **Validate generated code.** `validate_code(code, "enma")` catches hallucinated or cross-language symbols before you run it.
6. **Validate full answers.** `validate_answer(markdown)` checks all fenced Enma/AngelScript code blocks in an LLM response.

For tools that support resource URIs (Claude Desktop, Cline): the AI can also discover files lazily — list_files to enumerate, then fetch what's relevant. No hardcoded path knowledge needed.

## Tradeoff vs. the Static Bundles

The static bundles at `docs/llms.txt` / `docs/llms-full.txt` / `docs/llms-perception-*.md` are loaded once-per-session into the AI's context — fast, no infrastructure, but every byte counts against the context window.

The MCP server is lazy — only the files the AI asks for end up in context. Tradeoff is one running process and an MCP-aware client.

Use the bundles for: stateless tools (Aider, Copilot), starter context where you want a known-fixed surface, anything that doesn't speak MCP.

Use the MCP server for: long sessions where you'll touch many files, tools that already speak MCP, anywhere you want search-then-fetch instead of preload-everything.

Or use both — they don't conflict.

## Cross-References

- `tools/build-llms-index.py` — generates the static bundles + `llms.txt`
- `docs/llms.txt` — the static structured index (this server is the dynamic counterpart)
- `mcp/perception-mcp-config.json` — the existing Perception runtime MCP (live process / memory access — different surface, different purpose)
- `.claude/skills/mcp-tool-routing/SKILL.md` — when to use which MCP tool; this server's `search` / `get_file` slot into that routing as the "knowledge layer"
- `.claude/skills/pcx-knowledge-index/SKILL.md` — the AI-facing skill that explains when to reach for this server vs. the static bundles
