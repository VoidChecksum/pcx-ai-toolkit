# Setting Up pcx-ai-toolkit with Claude Code

## 1. Quick Setup (Automated)

Run the setup command from the repository root. This compiles the LSP servers, registers all 30 AI skills to Claude Code, and adds the `pcx` CLI tool to your system `PATH`:

```bash
# Linux / macOS / WSL
./setup.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Restart your terminal after installation. You can now use the `pcx` command from anywhere!

## 2. Add CLAUDE.md to Your Project

You can copy the drop-in project rules to your scripting project using the `pcx` command:

```bash
pcx setup --project /path/to/your/pcx-project
```

*(Manual alternative: `cp rules/CLAUDE.md /path/to/your/pcx-project/CLAUDE.md`)*

Claude Code reads this rules file automatically when launched in your project directory.

## 3. Configure Perception MCP (Optional)

If you run the Perception IDE with MCP enabled, Claude Code can connect to its tool server:

1. Add the streamable HTTP server (replace the port if Perception picked another):
   ```bash
   claude mcp add --transport http perception http://127.0.0.1:42069/mcp
   ```
   Or copy the checked config: `cp mcp/perception-mcp-config.json ~/.claude/mcp.json`.
2. Launch Perception IDE with MCP enabled (Settings -> enable MCP server).
3. The tools (memory read, disassemble, pattern scan, etc.) become available in Claude Code.

## 4. Build LSP Servers (Optional)

For Enma and AngelScript language intelligence in your editor:

```bash
cd lsp/enma-lsp && npm install && npm run compile
```

Configure your editor to use:
- Enma LSP: `node lsp/enma-lsp/server/dist/server.js --stdio`

## 5. Reference Docs

Point Claude at the docs directory when asking questions:

```
Read docs/enma/llms-language.md and then write me a ...
```

Or let the skill handle it — the `game-hacking-pcx` skill instructs Claude to read the relevant doc before writing any code.

## 6. Binary Analysis MCP (Optional)

Gives Claude Code static analysis tools (disassemble, decompile, xrefs, type info,
pattern search, rename, …) without needing the GUI open.

**Requires a legitimately-licensed IDA** you already have on this machine — the toolkit
does not provide, patch, or license IDA. With IDA present, activate the idalib bindings
and register the MCP server:

```bash
./mcp/setup-binary-analysis.sh                           # Linux / macOS / WSL
./mcp/setup-binary-analysis.sh --skip-pkg                # already have ida-pro-mcp
./mcp/setup-binary-analysis.sh --install-dir /your/path  # non-standard location
```
```powershell
.\mcp\setup-binary-analysis.ps1
.\mcp\setup-binary-analysis.ps1 -SkipPkg
.\mcp\setup-binary-analysis.ps1 -InstallDir "D:\tools\ida"
```

Both scripts write this entry to `~/.claude/mcp.json` automatically:
```json
{
  "mcpServers": {
    "binary-analysis": {
      "command": "uvx",
      "args": ["idalib-mcp", "--stdio"],
      "env": { "IDADIR": "/path/to/installation" }
    }
  }
}
```

Restart Claude Code after running either script.
Full reference: [`binary-analysis-setup.md`](binary-analysis-setup.md)
