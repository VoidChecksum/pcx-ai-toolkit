# Binary Analysis MCP — Reference

Integrates **[mrexodia/ida-pro-mcp](https://github.com/mrexodia/ida-pro-mcp)** (~9,400 stars)
as an MCP server. Supports headless (`idalib-mcp --stdio`) and GUI plugin (SSE) modes.
Works on Windows, Linux, and macOS.

---

## Which script to use

| Situation | Script |
|---|---|
| Fresh install — suite not yet on this machine | `installers/install.sh` or `installers/install.ps1` |
| Suite already installed, just need MCP | `mcp/setup-binary-analysis.sh` or `mcp/setup-binary-analysis.ps1` |

---

## Full install (suite not yet installed)

See [`installers/install.sh`](../installers/install.sh) and [`installers/install.ps1`](../installers/install.ps1).

Requires Git LFS:
```bash
git lfs pull
./installers/install.sh           # Linux / macOS / WSL
.\installers\install.ps1          # Windows
```

---

## MCP-only setup (suite already installed)

```bash
# Linux / macOS / WSL
./mcp/setup-binary-analysis.sh

# Already have the package, just activate + configure:
./mcp/setup-binary-analysis.sh --skip-pkg

# Non-standard install location:
./mcp/setup-binary-analysis.sh --install-dir /path/to/installation
```

```powershell
# Windows
.\mcp\setup-binary-analysis.ps1
.\mcp\setup-binary-analysis.ps1 -SkipPkg
.\mcp\setup-binary-analysis.ps1 -InstallDir "D:\tools\ida"
```

Both scripts are fully idempotent.

---

## What the MCP-only scripts install

| Step | What | Skip flag |
|---|---|---|
| 1 | uv (Python package manager) | auto-skipped if present |
| 2 | Python 3.11+ | auto-skipped if present |
| 3 | `ida-pro-mcp` via `uv tool install` | `--skip-pkg` / `-SkipPkg` |
| 4 | Auto-detect installation directory | `--install-dir` / `-InstallDir` |
| 5 | Activate idalib Python bindings | `--skip-activate` / `-SkipActivate` |
| 6 | Write `~/.claude/mcp.json` entry | auto-skipped if Claude Code not found |

---

## Modes

### Headless (recommended)

Uses idalib — no GUI required. Open binaries directly from Claude Code.

```bash
uvx idalib-mcp --stdio                          # stdio transport (Claude Code, Cursor, Zed)
uvx idalib-mcp --host 127.0.0.1 --port 8745    # HTTP transport
uvx idalib-mcp --host 127.0.0.1 --port 8745 path/to/binary   # pre-open a binary
```

### GUI plugin (optional)

Connects to a running interactive session via SSE.

```bash
pip install ida-pro-mcp
ida-pro-mcp --install   # installs the plugin, configures SSE
```

Restart the application completely after install.
MCP client connects to: `http://127.0.0.1:8744/sse`

---

## Claude Code config (`~/.claude/mcp.json`)

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

The install scripts write this automatically. `IDADIR` can be omitted if idalib
was activated system-wide via `py-activate-idalib.py`.

---

## Upgrading

```bash
uv tool upgrade ida-pro-mcp
```

---

## Troubleshooting

**`git lfs pull` fails / files are tiny text files**
Install Git LFS: `sudo apt install git-lfs` (Linux), `brew install git-lfs` (macOS),
or download from https://git-lfs.github.com/. Then run `git lfs install && git lfs pull`.

**`idapro` not importable after activation**
Run `py-activate-idalib.py` again with `--ida-install-dir` pointing to your exact install path.
Config is written to `~/.idapro/ida-config.json` (Linux/macOS) or
`%APPDATA%\Hex-Rays\IDA Pro\ida-config.json` (Windows).

**MCP server not showing in Claude Code**
Fully quit and restart Claude Code — it reads `mcp.json` only at startup.

**Analysis results differ between runs**
Headless mode waits for auto-analysis before returning from `open_database`.
For existing databases, ensure analysis completed before the database was saved.
