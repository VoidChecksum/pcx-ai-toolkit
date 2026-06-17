#!/usr/bin/env bash
# Full setup: installs the analysis suite permanently, patches it,
# activates idalib, installs the binary analysis MCP server, and
# configures Claude Code.
#
# Supports: Linux x64, Linux ARM64, macOS x64, macOS ARM64, WSL
# Windows without bash: use install.ps1 instead.
#
# Usage:
#   ./installers/install.sh
#   ./installers/install.sh --prefix /opt/mydir
#   ./installers/install.sh --skip-mcp
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── argument parsing ──────────────────────────────────────────────────────────
PREFIX=""
SKIP_MCP=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prefix)   PREFIX="$2"; shift 2 ;;
        --skip-mcp) SKIP_MCP=1; shift ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# ── platform detection ────────────────────────────────────────────────────────
OS=""; ARCH=""
case "$(uname -s)" in
    Linux*)  OS="linux" ;;
    Darwin*) OS="mac" ;;
    CYGWIN*|MINGW*|MSYS*)
        echo "[!!] Running inside Git Bash / Cygwin — use install.ps1 for Windows."
        exit 1 ;;
    *) echo "Unsupported OS: $(uname -s)"; exit 1 ;;
esac
if [ "$OS" = "linux" ] && grep -qiE "microsoft|wsl" /proc/version 2>/dev/null; then
    OS="wsl"
fi
case "$(uname -m)" in
    x86_64|amd64) ARCH="x64" ;;
    aarch64|arm64) ARCH="arm" ;;
    *) echo "Unsupported arch: $(uname -m)"; exit 1 ;;
esac

echo "Analysis suite installer"
echo "Platform: $OS / $ARCH"
echo ""

# ── pick installer ────────────────────────────────────────────────────────────
case "${OS}_${ARCH}" in
    linux_x64|wsl_x64) INSTALLER="$SCRIPT_DIR/ida-pro_93_x64linux.run" ;;
    linux_arm|wsl_arm) INSTALLER="$SCRIPT_DIR/ida-pro_93_armlinux.run" ;;
    mac_x64)           INSTALLER="$SCRIPT_DIR/ida-pro_93_x64mac.app.zip" ;;
    mac_arm)           INSTALLER="$SCRIPT_DIR/ida-pro_93_armmac.app.zip" ;;
esac

if [ ! -f "$INSTALLER" ]; then
    echo "[!!] Installer not found: $INSTALLER"
    echo "     Pull LFS files first:  git lfs pull"
    exit 1
fi

# Detect LFS pointer (real installers are 500 MB+; pointers are <200 bytes)
FSIZE=$(stat -c%s "$INSTALLER" 2>/dev/null || stat -f%z "$INSTALLER")
if [ "$FSIZE" -lt 1000000 ]; then
    echo "[!!] $INSTALLER looks like a Git LFS pointer (${FSIZE}B)."
    echo "     Run:  git lfs pull"
    exit 1
fi

# ── default prefix ────────────────────────────────────────────────────────────
if [ -z "$PREFIX" ]; then
    case "$OS" in
        linux|wsl)
            if [ -w /opt ] || sudo -n true 2>/dev/null; then
                PREFIX="/opt/ida-pro-9.3"
            else
                PREFIX="$HOME/ida-pro-9.3"
            fi
            ;;
        mac) PREFIX="/Applications" ;;
    esac
fi
echo "[..] Install location: $PREFIX"
echo ""

# ── prerequisite: Node.js ─────────────────────────────────────────────────────
if ! command -v node >/dev/null 2>&1; then
    echo "[!!] Node.js is required. Install from https://nodejs.org/ then re-run."
    exit 1
fi
echo "[ok] node $(node --version)"

# ── step 1: run the installer ─────────────────────────────────────────────────
echo "[..] Running installer (this takes a minute)..."

case "$OS" in
    linux|wsl)
        chmod +x "$INSTALLER"
        if [ -w "$(dirname "$PREFIX")" ] || [ -w "$PREFIX" ] 2>/dev/null; then
            "$INSTALLER" --mode unattended --prefix "$PREFIX"
        else
            sudo "$INSTALLER" --mode unattended --prefix "$PREFIX"
        fi
        INSTALL_DIR="$PREFIX"
        ;;
    mac)
        TMPDIR_MAC="$(mktemp -d)"
        echo "[..] Extracting macOS bundle..."
        unzip -q "$INSTALLER" -d "$TMPDIR_MAC"
        INNER="$(find "$TMPDIR_MAC" -name "installbuilder.sh" -o -name "osx-*" -type f | head -1)"
        if [ -z "$INNER" ]; then
            echo "[!!] Could not find installer binary inside zip."
            rm -rf "$TMPDIR_MAC"; exit 1
        fi
        chmod +x "$INNER"
        "$INNER" --mode unattended --prefix "$PREFIX"
        rm -rf "$TMPDIR_MAC"
        APP="$(ls "$PREFIX" | grep -i "IDA" | head -1)"
        INSTALL_DIR="$PREFIX/$APP/Contents/MacOS"
        ;;
esac

echo "[ok] Installed to: $INSTALL_DIR"

# ── step 2: patch ─────────────────────────────────────────────────────────────
echo "[..] Patching (keygen + license)..."
cp "$SCRIPT_DIR/keygen.js" "$INSTALL_DIR/"
cd "$INSTALL_DIR"
node keygen.js
cd - >/dev/null

if [ ! -f "$INSTALL_DIR/idapro.hexlic" ]; then
    echo "[!!] License file not generated — check node output above."
    exit 1
fi
rm -f "$INSTALL_DIR/keygen.js"
echo "[ok] Patch applied, license written"

# ── step 3: uv ────────────────────────────────────────────────────────────────
if command -v uv >/dev/null 2>&1; then
    echo "[ok] uv $(uv --version 2>/dev/null | head -1)"
else
    echo "[..] Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    command -v uv >/dev/null 2>&1 || { echo "[!!] uv install failed. See https://docs.astral.sh/uv/"; exit 1; }
    echo "[ok] uv installed"
fi

# ── step 4: Python 3.11+ ──────────────────────────────────────────────────────
PYTHON=""
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
        VER=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        MAJOR="${VER%%.*}"; MINOR="${VER##*.}"
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
            PYTHON="$py"
            echo "[ok] Python $VER ($py)"
            break
        fi
    fi
done
if [ -z "$PYTHON" ]; then
    echo "[..] Python 3.11+ not found — installing via uv..."
    uv python install 3.12
    PYTHON="$(uv run python -c 'import sys; print(sys.executable)')"
    echo "[ok] Python installed via uv"
fi

# ── step 5: activate idalib ───────────────────────────────────────────────────
echo "[..] Activating idalib Python bindings..."
ACTIVATE="$INSTALL_DIR/idalib/python/py-activate-idalib.py"
if [ -f "$ACTIVATE" ]; then
    uv run "$ACTIVATE" --ida-install-dir "$INSTALL_DIR"
    echo "[ok] idalib activated"
else
    echo "[!!] Activation script not found: $ACTIVATE"
fi

WHEEL=$(ls "$INSTALL_DIR/idalib/python/idapro"*.whl 2>/dev/null | head -1 || true)
if [ -n "$WHEEL" ] && ! "$PYTHON" -c "import idapro" >/dev/null 2>&1; then
    "$PYTHON" -m pip install --quiet "$WHEEL"
    echo "[ok] idapro wheel installed"
fi

# ── step 6: MCP server ────────────────────────────────────────────────────────
if [ "$SKIP_MCP" -eq 0 ]; then
    if uv tool list 2>/dev/null | grep -q "ida-pro-mcp"; then
        echo "[ok] ida-pro-mcp already installed"
    else
        echo "[..] Installing binary analysis MCP server..."
        uv tool install ida-pro-mcp
        echo "[ok] ida-pro-mcp installed"
    fi

    CLAUDE_DIR="$HOME/.claude"
    if [ -d "$CLAUDE_DIR" ]; then
        MCP_CFG="$CLAUDE_DIR/mcp.json"
        echo "[..] Configuring Claude Code MCP..."
        "$PYTHON" - <<PYEOF
import json, os
cfg = {}
if os.path.exists("$MCP_CFG"):
    try:
        with open("$MCP_CFG") as f: cfg = json.load(f)
    except Exception: pass
cfg.setdefault("mcpServers", {})
cfg["mcpServers"]["binary-analysis"] = {
    "command": "uvx",
    "args": ["idalib-mcp", "--stdio"],
    "env": {"IDADIR": "$INSTALL_DIR"},
}
with open("$MCP_CFG", "w") as f: json.dump(cfg, f, indent=2)
print("[ok] MCP config written to $MCP_CFG")
PYEOF
        echo "     Restart Claude Code to pick up the change."
    else
        echo "[--] Claude Code not detected — skipping MCP config."
        echo '     Add to your MCP client config manually:'
        echo '       "binary-analysis": {'
        echo '         "command": "uvx",'
        echo '         "args": ["idalib-mcp", "--stdio"],'
        echo "         \"env\": { \"IDADIR\": \"$INSTALL_DIR\" }"
        echo '       }'
    fi
fi

# ── done ──────────────────────────────────────────────────────────────────────
echo ""
echo "Done."
echo "  Installed to : $INSTALL_DIR"
echo "  License      : $INSTALL_DIR/idapro.hexlic"
[ "$SKIP_MCP" -eq 0 ] && echo "  MCP (headless): uvx idalib-mcp --stdio"
echo "  MCP (GUI plugin, optional): pip install ida-pro-mcp && ida-pro-mcp --install"
echo "  Upgrade later: uv tool upgrade ida-pro-mcp"
