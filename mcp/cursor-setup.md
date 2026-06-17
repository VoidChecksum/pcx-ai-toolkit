# Setting Up pcx-ai-toolkit with Cursor

## 1. Add Rules

Copy the CLAUDE.md content into your project's `.cursorrules` file:

```bash
cp rules/CLAUDE.md /path/to/your/project/.cursorrules
```

Cursor reads `.cursorrules` as persistent system instructions.

## 2. Add Docs to Context

Add the docs directory to your Cursor workspace so `@docs` references work:

1. Open your project in Cursor
2. Add `docs/` folder to your workspace
3. Reference docs with `@docs/enma/llms-language.md` in chat

## 3. Configure MCP (Cursor 0.45+)

Cursor supports MCP servers. Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "perception": {
      "url": "http://127.0.0.1:42069",
      "transport": "http"
    }
  }
}
```

## 4. LSP Integration

Add to `.vscode/settings.json` (Cursor uses VS Code settings):

```json
{
  "enma.server.path": "./lsp/enma-lsp/server/dist/server.js",
  "angelscript.server.path": "./lsp/angel-lsp-pcx/server/out/server.js"
}
```
