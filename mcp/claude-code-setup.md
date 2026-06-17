# Setting Up pcx-ai-toolkit with Claude Code

## 1. Install Skills

Copy the skill directories to your Claude Code skills folder:

```bash
# Linux / macOS / WSL / Git Bash
cp -r .claude/skills/game-hacking-pcx ~/.claude/skills/
cp -r .claude/skills/game-cheat-guidelines ~/.claude/skills/
```

```powershell
# Windows (PowerShell)
Copy-Item -Recurse .claude\skills\game-hacking-pcx     $env:USERPROFILE\.claude\skills\
Copy-Item -Recurse .claude\skills\game-cheat-guidelines $env:USERPROFILE\.claude\skills\
```

The skills auto-trigger when you work with `.em`/`.as` files or ask about Perception.cx scripting.

## 2. Add CLAUDE.md to Your Project

Copy the drop-in project rules to your scripting project:

```bash
# Linux / macOS
cp rules/CLAUDE.md /path/to/your/pcx-project/CLAUDE.md
```

```powershell
# Windows
Copy-Item rules\CLAUDE.md C:\path\to\your\pcx-project\CLAUDE.md
```

Claude Code reads this automatically when working in that directory.

## 3. Configure Perception MCP (Optional)

If you run the Perception IDE with MCP enabled, Claude Code can connect to its tool server:

1. Copy the MCP config:
   ```bash
   cp mcp/perception-mcp-config.json ~/.claude/mcp.json
   ```
2. Launch Perception IDE with MCP enabled (Settings -> enable MCP server)
3. The tools (memory read, disassemble, pattern scan, etc.) become available in Claude Code

## 4. Build LSP Servers (Optional)

For Enma and AngelScript language intelligence in your editor:

```bash
cd lsp/enma-lsp && npm install && npm run compile
cd lsp/angel-lsp-pcx && npm install && npm run compile
```

Configure your editor to use:
- Enma LSP: `node lsp/enma-lsp/server/dist/server.js --stdio`
- AngelScript LSP: `node lsp/angel-lsp-pcx/server/out/server.js --stdio`

## 5. Reference Docs

Point Claude at the docs directory when asking questions:

```
Read docs/enma/llms-language.md and then write me a ...
```

Or let the skill handle it — the `game-hacking-pcx` skill instructs Claude to read the relevant doc before writing any code.
