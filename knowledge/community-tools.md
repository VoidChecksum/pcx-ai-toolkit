# Community Tools & MCP Servers

Third-party tools, MCP servers, VS Code extensions, and utilities built by the Perception.cx community.

---

## MCP Servers

### perception-mcp — by mx13

Full-featured MCP server connecting Claude Code to Perception's RE tools via AngelScript.

**Tools (35+):**
- Memory read/write (typed values, structs, pointer chains, hex dumps)
- IDA-style pattern scanning
- Zydis disassembly
- Function analysis, RTTI, vtable walking
- Full-process value and pointer scanning
- Cross-reference search
- Memory snapshots and diffing
- Unicorn x86_64 emulation
- CS2 interface and schema tools

**Setup:**
```bash
git clone https://github.com/verifizieren/perception-mcp
cd perception-mcp
npm install && npm run build
```

Load `re_server.as` in Perception IDE — it runs in the background and auto-connects.

**MCP Config:**
```json
{
  "mcpServers": {
    "perception-re": {
      "command": "node",
      "args": ["<path-to>/perception-mcp/dist/index.js"]
    }
  }
}
```

**Source:** [github.com/verifizieren/perception-mcp](https://github.com/verifizieren/perception-mcp)

---

### claude-ception — by aewu

Claude Code × Perception MCP bridge for AI-driven live-memory reverse engineering.
Built on ReClass/PerceptionClassEx by segfault and hantschuh.

**Features:**
- Value scans with next-scan filtering
- Pointer-path solving
- Cross-reference sweeps
- Region enumeration and struct reconstruction
- x64 disassembly
- Signature scanning and world-to-screen validation
- AngelScript overlay code generation

**Architecture:**
- `127.0.0.1:9002` — MCP TCP (bridge ↔ plugin, native scans)
- `127.0.0.1:9001` — WebSocket memory reads via Perception

**Setup:**
```
perception-claude-bundle/
├─ README-BUNDLE.md     - quick start
├─ system-prompt.md     - RE system prompt
├─ pclaude.cmd          - launches Claude Code with prompt
├─ .mcp.json            - MCP server registration
├─ reclass-mcp/         - MCP bridge (Node.js)
├─ PCX-runtime/         - ready-to-run exe + plugin + .as script
└─ PCX-src/             - full source (editor + plugin)
```

**Requirements:** Node.js 18+, Claude Code CLI.

**Source:** Available on perception.cx forums (Learning & Research section).

---

### reclass-mcp — by hantschuh

The original ReClass MCP bridge for Claude Code — the foundation claude-ception builds on.

**Features:**
- Memory read/write through PerceptionClassEx
- Pattern scanning
- Struct reconstruction
- Pointer chain resolution

**Source:** Available on perception.cx forums.

---

### Unreal Engine Documentation MCP — by jozkah

MCP server providing direct access to official Unreal Engine documentation with version selection (UE 4.27 — 5.7).

**Tools:**
- `search` — keyword search across all UE docs
- `read_page` — fetch any doc page as clean markdown
- `browse_categories` — list top-level doc sections
- `cpp_api_lookup` — look up classes, structs, functions (AActor, FVector, UObject, etc.)

**Setup:**
```bash
git clone https://github.com/Jozkah/Unreal-Engine-Documentation-MCP.git
cd Unreal-Engine-Documentation-MCP
npm install && npm run build
```

**MCP Config (VS Code):**
```json
{
  "servers": {
    "unreal-engine-docs": {
      "command": "node",
      "args": ["<path>/Unreal-Engine-Documentation-MCP/dist/index.js"]
    }
  }
}
```

No API keys needed — reads public documentation. MIT licensed.

**Source:** [github.com/Jozkah/Unreal-Engine-Documentation-MCP](https://github.com/Jozkah/Unreal-Engine-Documentation-MCP)

---

### Context7 Integration

Hosted MCP server (by Upstash) that indexes official documentation for thousands of libraries with version pinning.

**Relevant Indexed Content:**
- Unreal Engine 5.7 — 80,411 code snippets
- Unity Manual — 47,581 snippets
- Godot Engine 4.5/4.6 — ~20k snippets each
- Ghidra API — 80,664 snippets
- IDA SDK — 535 snippets

**Setup:**
```bash
npx ctx7 setup --claude     # Claude Code
npx ctx7 setup --cursor     # Cursor
```

**Manual MCP Config:**
```json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp",
      "headers": { "CONTEXT7_API_KEY": "your-key-here" }
    }
  }
}
```

Free tier available (rate-limited). Get an API key at `context7.com/dashboard`.

**Source:** [context7.com](https://context7.com)

---

## VS Code Extensions

### Enma LSP — by sin (sinnafuls)

Full-featured VS Code extension for Enma scripting with Perception integration.

**Features:**
- **IntelliSense** — autocompletion for all Perception globals, classes, structs, methods, and Enma stdlib
- **Hover docs** — signatures and descriptions for every function
- **Parameter hints** — active parameter highlighting
- **Go-to-definition** — `Ctrl+Click` any symbol
- **Find references** — across entire project (including f-string interpolations)
- **Safe rename** — across all files
- **Workspace symbol search** — `Ctrl+T`
- **Type-mismatch diagnostics** — real-time error checking
- **Quick-fix imports** — auto-insert missing `import "vec"` etc.

**Bundler:**
- `Ctrl+Alt+B` — bundle `#include`-split project into single `.em`
- `Ctrl+Alt+Shift+B` — bundle and strip comments
- Auto-rebundle on save (configurable)
- Multi-project support

**Engine MCP Client:**
- Run script via MCP (`script/execute`)
- Validate on save (`script/validate`)
- Configurable endpoint (default `http://127.0.0.1:9077/mcp`)

**DAP Debugger:**
- Attach to running Enma DAP server (`F5`, default `localhost:27979`)
- Breakpoints in `.em` files

**Project Commands:**
- `Enma: Initialize Project` — scaffold `source/main.em` + tasks.json
- `Enma: Scaffold From Template…` — `perception-minimal` or `perception-multi`
- `Enma: Generate CI Workflow` — `.github/workflows/enma.yml`

**Install:** Download `.vsix` from [GitHub Releases](https://github.com/sinnafuls/enma-lsp/releases), then `Ctrl+Shift+P` → "Extensions: Install from VSIX…"

**Source:** [github.com/sinnafuls/enma-lsp](https://github.com/sinnafuls/enma-lsp)

---

### AngelScript LSP + Bundler — by Shadow / sin

AngelScript language server with Perception-specific extensions.

**Features:**
- Syntax highlighting and diagnostics
- IntelliSense for PCX AngelScript API
- Script bundling and validation

---

### VS Perception Extension — by banjo

VS Code extension for Perception development workflow.

---

## Utilities

### Claude Proxy — by sin (sinistercodes)

Proxy server that routes Claude API requests to Perception's IDE chatbot.

**Setup:**
```bash
git clone https://github.com/sinistercodes/claude-proxy
cd claude-proxy
npm install
cp .env.example .env  # configure model/thinking budget
node --env-file=.env server.js
```

**Perception IDE Config:**
- Base URL: `http://localhost:4001/v1/chat/completions`
- API key: any string
- Model: sonnet, opus, or haiku

**Source:** [github.com/sinistercodes/claude-proxy](https://github.com/sinistercodes/claude-proxy)

---

### AngelScript Custom GUI + Base — by underscore

Open-source full GUI system and script base for AngelScript.

**Includes:**
- Full custom menu/GUI — windows, tabs, containers
- All widget types: checkboxes, sliders, keybinds, dropdowns, multi-selects, color pickers, list boxes, text inputs, tooltips, labels, buttons
- Config & theme systems with save/load
- Notifications and draggable HUD widgets
- Attachment system — process memory I/O, pattern scanning, UE FString/FText/vector/matrix/quaternion helpers
- Threading/callback system with perf timing

Full API docs in the README. Fork and build on top of it.

**Source:** Available on perception.cx forums (Learning & Research section).

---

### dumpception — by sin

SDK/offset dumping utility for Perception.

---

### Universal Offset Scanner — by ItachiValor

Automated offset discovery tool (private beta).

Available on perception.cx Script Market.
