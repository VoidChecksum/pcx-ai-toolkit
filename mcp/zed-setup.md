# Zed Setup — Perception.cx Toolkit Integration

[Zed](https://zed.dev) is a Rust-built editor with AI baked into the core rather than
bolted on as an extension. It ships Edit Predictions (Tab-complete-style inline
suggestions), an Inline Assist for surgical single-file edits, and an Agent panel for
multi-file work — plus MCP support through its `context_servers` setting. It is fast,
terminal-friendly, and built around pair-programming. This toolkit wires in through Zed's
rules-file convention (Zed reads `CLAUDE.md` / `AGENTS.md` natively), its `@`-mention
context system, and the Perception MCP server.

## Why Zed Here

The niche Zed fills that the other GUI tools don't:

- **Ultra-fast file ops on large repos.** Zed's file finder and search are fast enough
  that this toolkit's ~35k-line doc corpus loads and greps interactively. Opening
  `docs/perception/` and fuzzy-jumping between API files has no perceptible lag — useful
  when you are cross-referencing five APIs to build one feature.
- **Built-in AI, no extension setup.** The Agent panel, Inline Assist, and Edit
  Predictions are part of the editor. There is no marketplace install or separate chat
  pane to configure — open the panel and point it at a model.
- **MCP via `context_servers`.** Zed speaks MCP in its settings, so the Perception MCP
  server's live-memory tools land in the Agent panel alongside the docs.
- **vim / helix keybindings work.** If you live in modal editing, Zed's vim mode covers
  the actions, so the toolkit workflow doesn't force you off your muscle memory.

## Install

The official method is the one-line installer or your platform's package:

```bash
# Official installer (macOS / Linux)
curl -f https://zed.dev/install.sh | sh
```

On macOS you can also `brew install --cask zed`; on Linux several distros package it. See
Zed's official install documentation for platform notes. Zed needs an account or a
configured model provider for the AI features — pick a provider in the Agent settings
(below) and supply its API key there.

## Wire Up the Toolkit

### 1. Open the toolkit

Open this repo as a Zed project (`zed /path/to/pcx-ai-toolkit`, or **File → Open Folder**).
If your script project lives elsewhere, open that and add the toolkit `docs/` and
`knowledge/` folders to the workspace so `@`-mentions resolve.

### 2. Configure the AI assistant

Open **Agent Settings** (`agent: open settings`, or the top-right menu in the Agent panel)
to pick a model provider and supply its key. The default model is also settable in
`~/.config/zed/settings.json` under `agent.default_model`:

```json
{
  "agent": {
    "default_model": {
      "provider": "anthropic",
      "model": "claude-sonnet-4"
    }
  }
}
```

Any provider Zed supports works — Anthropic, OpenAI, or an OpenAI-compatible endpoint
configured as a custom provider. Use a capable model; the offset/pointer reasoning the 12
guidelines demand is not a small-model task.

### 3. Drop in the rules

Zed's built-in agent system prompt is fixed — you cannot edit its sections — but Zed reads
project rules files (`CLAUDE.md`, `AGENTS.md`, `.rules`) as always-on instructions. The
toolkit's rules drop-in *is* that file:

```bash
# Linux / macOS / WSL — project-local rules
cp rules/CLAUDE.md /path/to/your/pcx-project/CLAUDE.md
```

```powershell
# Windows
Copy-Item rules\CLAUDE.md C:\path\to\your\pcx-project\CLAUDE.md
```

Zed picks `CLAUDE.md` up automatically from the project root. For rules that apply to
*every* Zed project, copy them into the user-global file instead
(`~/.config/zed/AGENTS.md` on macOS/Linux, `%APPDATA%\Zed\AGENTS.md` on Windows) — open it
with the `agent::OpenGlobalAGENTS.mdRules` action. Either way the agent now inherits the
coding standards, the project structure, and the 12 guidelines (condensed) without
re-prompting: `uint64` addresses, `f`-suffixed `float32` literals, sigs over hardcoded
offsets, and update/render separation.

A symlink keeps toolkit updates flowing through:

```bash
ln -s /path/to/pcx-ai-toolkit/rules/CLAUDE.md /path/to/your/pcx-project/CLAUDE.md
```

### 4. Pin the key docs

Add the reference docs to context with `@`-mentions in the Agent panel. The high-value set
for most script work:

```text
@docs/perception/render-api.md
@docs/perception/proc-api.md
@knowledge/pcx-api-cheatsheet.md
@knowledge/common-patterns.md
```

Pin the cheatsheet as a persistent mention — it is the dense single-file reference that
covers the breadth of the API. Add the per-area API docs (`render`, `proc`, `gui`,
`input`, …) only for the task at hand. See **Token Budget** below.

## MCP Integration

The Perception MCP server (`mcp/perception-mcp-config.json`) is a JSON-RPC server over
local HTTP at `127.0.0.1:42069`, **launched by the Perception IDE** when MCP is enabled in
its settings. Start the IDE with MCP on, then attach Zed to that endpoint.

Zed's `context_servers` launches a local command and talks to it over stdio, so bridge to
the IDE's HTTP endpoint with `mcp-remote`. Add this to `~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "perception": {
      "source": "custom",
      "command": {
        "path": "npx",
        "args": ["-y", "mcp-remote", "http://127.0.0.1:42069"]
      },
      "env": {}
    }
  }
}
```

`source: "custom"` is required for a manually-added server — without it Zed treats the
entry as malformed and skips it. Save the file and Zed restarts the context server
automatically; no editor restart. Confirm the green indicator next to `perception` in the
Agent panel's settings view ("Server is active"). The Agent panel then auto-picks up the
tools.

The authoritative tool list is in [`perception-mcp-config.json`](perception-mcp-config.json)
(kept in sync with `docs/perception/mcp-api.md` by `tools/check-mcp-config.py`): process
discovery + reference lifecycle (`process/list`, `process/info_by_pid`, `process/info_by_name`,
`process/reference_by_*`), reads (`process/read_virtual_memory`, `process/read_typed_value`,
`process/read_pointer_chain`, `process/read_string`), pattern + value scans
(`process/find_pattern`, `process/find_all_patterns`, `process/scan_value`, `process/scan_string`,
`process/scan_pointer_to`, `process/diff_memory`), analysis (`process/disassemble`,
`process/find_xrefs`, `process/find_string_refs`, `process/find_function_bounds`,
`process/analyze_vtable`, `process/read_rtti`, `process/generate_signature`), and the
scripting bridge (`script/get_context`, `script/validate`, `script/execute`). These let the
agent resolve and verify an offset against the live binary instead of guessing — guideline 12.

If your Zed version exposes a native URL/SSE field for remote context servers, point it
straight at `http://127.0.0.1:42069` and drop the bridge.

## Typical Workflow

Open your script directory in Zed; the Agent panel is on the right (`agent: toggle focus`).

1. **Pin context.** Mention the persistent reference once —
   `@knowledge/pcx-api-cheatsheet.md` for cross-API breadth — then add the one
   `@docs/perception/<area>-api.md` the task touches.
2. **Add the working files.** `@`-mention the files the agent may change (`@main.em`,
   `@offsets.em`) so it edits in place rather than inventing new files.
3. **Plan the change.** Ask the Agent panel to lay out a multi-file change before it
   writes. With the rules file loaded, it applies the standards unprompted:

   ```text
   Add a box ESP feature. Resolve the entity list with a pattern scan in
   offsets.em (cite the sig), validate every pointer before dereferencing,
   keep all reads in an update routine and all draw_rect calls in a render
   routine. uint64 addresses, color() built per frame.
   ```

4. **Review the diff, then apply.** The Agent panel shows a diff per file. Read it before
   accepting — guideline 3, surgical changes. Reject and re-prompt if it churned a working
   offset or merged update and render.
5. **Surgical single-file edits → Inline Assist.** Select a region and press
   `Cmd+Enter` (`Ctrl+Enter` on Linux/Windows) to rewrite just that selection in place,
   without the full Agent panel round-trip. Good for fixing one pointer chain or adding a
   GUI widget.
6. **Commit.** Zed has a built-in git panel and diff view; stage and commit from there
   (or your vim/`:` workflow). Keep one feature per commit so a bad offset is one revert
   away.

## Zed-Specific Notes

- **Speed.** Zed's file navigation is fast enough that the 35k-line doc corpus feels
  lightweight. You can fuzzy-find across `docs/` and grep `knowledge/` interactively
  instead of pre-loading everything — which is exactly how you keep the context budget
  small (below).
- **Multiplayer.** Zed supports real-time collaboration. If you are pairing on a script,
  a remote teammate sees your edits live and can drive the Agent panel with you — useful
  when one person owns the RE half (resolving sigs into `offsets.em`) and the other owns
  the feature logic.
- **Vim keybindings.** Enable vim mode in Settings (`"vim_mode": true`). Most editor
  actions have a modal equivalent, including opening the Agent panel and accepting
  predictions, so the toolkit workflow doesn't break your editing model.
- **Predictions vs. Agent panel — different tools.** Edit Predictions (Tab-accepted,
  typing-out style) are for finishing the line you are writing. The Agent panel is the
  multi-file refactor and planning surface. Use predictions while hand-writing a render
  routine; use the Agent panel when a change spans `offsets.em`, a feature file, and the
  menu.
- **Token budget.** Zed shows the context size in the Agent panel. The full docs blow it,
  and a bloated context buries the relevant API in noise. Pin only what the task needs:
  `@knowledge/pcx-api-cheatsheet.md` for cross-API breadth, `@docs/perception/<area>-api.md`
  for depth on one API. Drop a mention when you move off that task. The cheatsheet plus one
  per-area doc covers the vast majority of script edits.

## Reference

Back to the [Supported AI Tools](../README.md#supported-ai-tools) table in the README for
the other integrations (Claude Code, Cursor, Cline, Aider, Perception IDE).
