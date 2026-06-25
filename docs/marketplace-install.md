# Extension Installation Guide

## VS Code Extensions

Two VS Code extensions are available for pcx-ai-toolkit:

| Extension | Language | Purpose |
|-----------|----------|---------| 
| `enma-lsp` | Enma (`.em`) | Syntax highlighting, completions, hover docs, diagnostics |

### Install from VSIX (Current Method)

1. Download the latest `.vsix` files from the [GitHub Releases](https://github.com/VoidChecksum/pcx-ai-toolkit/releases) page.
2. In VS Code, open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run **Extensions: Install from VSIX...**
3. Select the downloaded `.vsix` file.
4. Repeat for the second extension if needed.
5. Restart VS Code.

### VS Code Marketplace

> **Status**: Marketplace publication is planned for a future release.
> Subscribe to [GitHub Releases](https://github.com/VoidChecksum/pcx-ai-toolkit/releases) to be notified when it goes live.

Once published, installation will be as simple as:
```
ext install VoidChecksum.enma-lsp
```

Or search for `Perception.cx` in the VS Code Extensions panel.

### Via Setup Script (Recommended for New Installs)

The setup script builds LSP servers from source and installs them automatically:

```bash
# Linux / macOS / WSL
./setup.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File setup.ps1
```

This builds the servers at:
- Enma: `lsp/enma-lsp/server/dist/server.js`

Then configure your editor to use these paths (see your editor's setup guide in `mcp/`).

---

## Visual Studio 2022 Extensions

Native Visual Studio 2022 extensions (`.vsix`) are also provided for Windows developers:

| Extension | Language |
|-----------|----------|
| `PcxEnmaVS` | Enma (`.em`) |

### Install

1. Download `PcxEnmaVS-*.vsix` from [GitHub Releases](https://github.com/VoidChecksum/pcx-ai-toolkit/releases).
2. **Close Visual Studio** before installing.
3. Double-click the downloaded `.vsix` file to launch the VSIX Installer.
4. Follow the prompts and restart Visual Studio.

The extension adds syntax highlighting and LSP-powered completions to the VS IDE.

---

## Troubleshooting

- **Extension not activating**: Ensure you have Node.js 18+ installed and run `pcx setup` to build the LSP servers.
- **No completions in VS Code**: Check that the LSP server path in your workspace settings matches the built server location (`lsp/enma-lsp/server/dist/server.js`).
- **Run `pcx doctor`** to automatically diagnose extension and LSP issues.
- **Still stuck?** See [docs/FAQ.md](FAQ.md) or open a [GitHub Issue](https://github.com/VoidChecksum/pcx-ai-toolkit/issues) with label `lsp`.
