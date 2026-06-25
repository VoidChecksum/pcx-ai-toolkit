# Continue Setup — Perception.cx Toolkit Integration

[Continue](https://continue.dev) is an open-source AI coding assistant that runs as a
VS Code or JetBrains extension. It is model-agnostic — point it at OpenAI, Anthropic, or
a local model served by Ollama / vLLM — and it supports custom system prompts, MCP
servers as tool sources, and project-level config overrides. You wire the toolkit in by
dropping `rules/CLAUDE.md` into Continue's config as a rule, pinning the always-needed
PCX docs as context, and registering the Perception MCP server so the assistant can read
process memory and resolve sigs live while you write Enma in the editor you already use.

## Why Continue Here

The niche Continue fills that the other integrations don't:

- **Runs in editors you already use.** VS Code and the whole JetBrains family (CLion,
  IntelliJ, Rider, PyCharm). No new IDE, no context switch — the assistant is a sidebar
  in the editor your RE box already has open.
- **Open-source, no vendor lock-in.** The extension and the config format are MIT/Apache
  and live in your repo. You are not renting a closed chat surface.
- **Model-agnostic.** Route each task to whatever model fits: a strong Anthropic /
  OpenAI model for architecture and offset reasoning, a cheap fast one for autocomplete,
  a local model for offline work. One config, many providers.
- **MCP-as-a-tool-source.** Continue speaks the Model Context Protocol in agent mode, so
  the Perception MCP server's `process/read_virtual_memory` / `process/find_pattern` /
  `process/generate_signature` tools become callable from inside the editor — the same
  live-verification loop the Perception IDE chat gives you, without leaving VS Code or JetBrains.

## Install

Install from the VS Code Marketplace (extension id `Continue.continue`) or from the
JetBrains Marketplace (search "Continue"):

```text
# VS Code: Extensions view (Ctrl+Shift+X) → search "Continue" → Install
# JetBrains: Settings → Plugins → Marketplace → search "Continue" → Install
```

See Continue's official install documentation for platform notes and provider API-key
setup. Continue needs an API key for whatever remote model you select (e.g.
`ANTHROPIC_API_KEY` / `OPENAI_API_KEY`); local providers (Ollama / vLLM) need no key.

## Wire Up the Toolkit

Open the toolkit (or your PCX script project) in your IDE, then configure Continue.

### 1. Config file location

Continue reads config from your global directory and from the project:

- **Global:** `~/.continue/config.yaml` (newer format) or `~/.continue/config.json`
  (legacy). If both exist, `config.yaml` wins.
- **Per-project:** a `.continue/` directory in the project root. Assistants, rules, and
  MCP server files placed here override or extend the global config for that workspace.

Keep the toolkit-specific wiring in the project's `.continue/` so it travels with the
repo and doesn't leak into unrelated projects.

### 2. System prompt → the rules drop-in

`rules/CLAUDE.md` is your system prompt. In the current `config.yaml` schema, system
instructions live under `rules:` (an array of strings — `systemMessage` was the old
`config.json` field and is deprecated). Paste a condensed pointer that defers to the
full drop-in:

```yaml
# .continue/config.yaml
name: pcx-toolkit
version: 1.0.0
schema: v1

rules:
  - |
    You are working on a Perception.cx scripting project (Enma .em / AngelScript .as).
    Follow rules/CLAUDE.md for the full rules drop-in.
    Always read docs/perception/<area>-api.md before writing any API call.
    Honor the 12 game-cheat-guidelines: uint64 addresses, f-suffixed float32 literals,
    validate every pointer, sigs over hardcoded offsets, separate update from render.
```

On the legacy `config.json`, the equivalent is a single `systemMessage` string — but
prefer `config.yaml`; it is the format Continue is built around going forward.

For the full text rather than a pointer, you can author a project rule that loads the
file. Drop a Markdown rule into `.continue/rules/` whose body is `rules/CLAUDE.md`:

```bash
mkdir -p .continue/rules
cp rules/CLAUDE.md .continue/rules/pcx.md
```

Continue applies every rule in `.continue/rules/` to chat, edit, and agent requests.

### 3. Pin the key context files

Continue pulls files into context on demand via `@`-mentions in the chat (`@files`,
`@docs`, `@codebase`). You do not pre-load whole trees — see Token Budget below. The one
file worth keeping reachable by default is the dense single-file reference:

```text
@knowledge/pcx-api-cheatsheet.md
```

For a documentation set you query often, register it as a `@docs` source so Continue
indexes it once and you can `@docs` into it by name. Otherwise pull the specific
`docs/perception/<area>-api.md` per task with `@files`.

## MCP Integration

Continue loads MCP servers as tool sources in **agent mode**. The Perception MCP server
ships with the toolkit (`mcp/perception-mcp-config.json`) — it is JSON-RPC over local
HTTP, launched automatically by the Perception IDE when MCP is enabled in settings, and
listens on `http://127.0.0.1:42069/mcp`. Register it in `config.yaml` with the
`streamable-http` transport:

```yaml
# .continue/config.yaml
mcpServers:
  - name: perception
    type: streamable-http
    url: http://127.0.0.1:42069/mcp
```

Start the Perception IDE with MCP enabled first so the endpoint is live, then reload
Continue. In agent mode the assistant can now call the server's tools directly —
`process/list`, `process/read_virtual_memory`, `process/find_pattern`, `process/read_pointer_chain`,
`process/generate_signature`, `process/analyze_vtable`, `process/disassemble`, and the rest. See
`mcp/perception-mcp-config.json` for the full tool list and
`.claude/skills/mcp-tool-routing/SKILL.md` for which tool to reach for when (scan vs.
read vs. xref vs. signature generation).

If you came from Cursor or Cline, Continue also auto-picks-up any JSON MCP config files
dropped into `.continue/mcpServers/` — so `mcp/perception-mcp-config.json` can be copied
there verbatim instead of translating it to YAML.

For binary analysis backed by IDA, install a legitimately-licensed IDA yourself and wire
up the binary-analysis MCP server (see [`binary-analysis-setup.md`](binary-analysis-setup.md)),
then register its stdio MCP server alongside `perception` with `type: stdio`.

## Typical Workflow

Continue surfaces in your IDE sidebar. The core loop:

- **`Cmd+L`** (macOS) / **`Ctrl+L`** (Windows / Linux) opens the chat panel.
- **`Cmd+I`** / **`Ctrl+I`** starts an inline edit on the current selection.
- **`@files` / `@docs` / `@codebase` / `@terminal`** add context to a request:
  `@files` pins specific files, `@docs` queries an indexed doc source, `@codebase`
  searches the repo semantically, `@terminal` feeds recent terminal output back in.
- **Edit mode shows a diff before applying** — review every changed line, then accept or
  reject. Pairs with guideline 3 (surgical changes): you see exactly which offsets and
  render calls moved before anything lands on disk.
- **Slash commands** (the `prompts:` field in `config.yaml`) capture repeatable
  workflows. Define one for "add a feature module per the layered pattern":

```yaml
# .continue/config.yaml
prompts:
  - name: feature
    description: Add a feature module following the toolkit's layered structure
    prompt: |
      Add a new feature in its own file under features/ (guideline 6, one feature
      per file). Resolve any offset with a pattern scan in offsets.em (guideline 5),
      validate every pointer returned by ru64/find_code_pattern before dereferencing
      (guideline 3), and do all drawing in a render routine separate from the memory
      reads (guideline 4). Bind every tunable to a GUI widget (guideline 11).
```

Invoke it with `/feature` in chat. Because the rule drop-in is loaded, the assistant
applies the standards without re-prompting: addresses come out `uint64`, float literals
get the `f` suffix, colors and vecs are constructed per frame, and the offset is
resolved with `find_code_pattern` rather than hardcoded.

## Continue-Specific Notes

Things Continue gives you that the single-model tools don't:

- **Multiple models per config.** Continue's `models:` array uses a `roles` field
  (`chat`, `autocomplete`, `edit`, `apply`, `embed`) so you can assign a different model
  to each job. Match model strength to task — a faster, cheaper model for autocomplete,
  a stronger one for chat and architecture:

  ```yaml
  models:
    - name: Architect
      provider: anthropic
      model: claude-sonnet-4-6
      roles: [chat, edit, apply]
    - name: Fast completion
      provider: ollama
      model: qwen2.5-coder:7b
      roles: [autocomplete]
  ```

- **Local model support.** If you run Ollama or vLLM on the RE box, point Continue at it
  with `provider: ollama` (or an `openai`-compatible base URL for vLLM). It behaves the
  same as a remote provider — useful on an air-gapped analysis VM where the target
  binary should never touch a third-party endpoint.
- **`@codebase` context.** Searches the whole repo semantically. It is context-expensive,
  so reach for it deliberately — but it is the right call for "find every place that
  reads the entity list" or "where else do we resolve this sig." For one known file,
  `@files` is cheaper.
- **Token budget.** Pin only the cheatsheet (`@knowledge/pcx-api-cheatsheet.md`) by
  default. The toolkit ships ~35k lines of docs; pulling all of `docs/` into every turn
  buries the relevant API in noise and burns budget. Pull the specific
  `docs/perception/<area>-api.md` per task with `@files` or a `@docs` source, then drop
  it when you move on. The cheatsheet plus one API doc covers the vast majority of edits.

## Reference

Back to the [Supported AI Tools](../README.md#supported-ai-tools) table in the README for
the other integrations (Claude Code, Cursor, Cline, Aider, Perception IDE).
