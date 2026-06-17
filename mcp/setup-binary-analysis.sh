#!/usr/bin/env bash
# MCP-only setup — use this if the analysis suite is already installed.
# For a fresh install (suite + MCP together), use installers/install.sh instead.
#
# What this does:
#   1. Installs uv if not present
#   2. Installs ida-pro-mcp via uv tool install (skipped if already present)
#   3. Activates idalib Python bindings against your existing installation
#   4. Writes the binary-analysis entry into ~/.claude/mcp.json
#
# Usage:
#   ./mcp/setup-binary-analysis.sh
#   ./mcp/setup-binary-analysis.sh --install-dir /path/to/installation
#   ./mcp/setup-binary-analysis.sh --skip-pkg      # skip download, already have it
#   ./mcp/setup-binary-analysis.sh --skip-activate # skip idalib activation
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── argument parsing ──────────────────────────────────────────────────────────
INSTALL_DIR=""
SKIP_PKG=0
SKIP_ACTIVATE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --install-dir)   INSTALL_DIR="$2"; shift 2 ;;
        --skip-pkg)      SKIP_PKG=1; shift ;;
        --skip-activate) SKIP_ACTIVATE=1; shift ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# ── platform detection ────────────────────────────────────────────────────────
case "$(uname -s)" in
    Linux*)  PLATFORM="Linux" ;;
    Darwin*) PLATFORM="macOS" ;;
    CYGWIN*|MINGW*|MSYS*) PLATFORM="Git Bash" ;;
    *) PLATFORM="$(uname -s)" ;;
esac
if [ "$PLATFORM" = "Linux" ] && grep -qiE "microsoft|wsl" /proc/version 2>/dev/null; then
    PLATFORM="WSL"
fi

echo "Binary analysis MCP setup (suite already installed)"
echo "Platform: $PLATFORM"
echo ""

# ── step 1: uv ────────────────────────────────────────────────────────────────
if command -v uv >/dev/null 2>&1; then
    echo "[ok] uv $(uv --version 2>/dev/null | head -1)"
else
    echo "[..] Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    command -v uv >/dev/null 2>&1 || { echo "[!!] uv install failed."; exit 1; }
    echo "[ok] uv installed"
fi

# ── step 2: Python 3.11+ ──────────────────────────────────────────────────────
PYTHON=""
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
        VER=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        MAJOR="${VER%%.*}"; MINOR="${VER##*.}"
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
            PYTHON="$py"; echo "[ok] Python $VER ($py)"; break
        fi
    fi
done
if [ -z "$PYTHON" ]; then
    echo "[..] Python 3.11+ not found — installing via uv..."
    uv python install 3.12
    PYTHON="$(uv run python -c 'import sys; print(sys.executable)')"
    echo "[ok] Python installed via uv"
fi

# ── step 3: ida-pro-mcp package ───────────────────────────────────────────────
if [ "$SKIP_PKG" -eq 1 ]; then
    echo "[--] Skipping package install (--skip-pkg)"
elif uv tool list 2>/dev/null | grep -q "ida-pro-mcp"; then
    echo "[ok] ida-pro-mcp already installed  (upgrade: uv tool upgrade ida-pro-mcp)"
else
    echo "[..] Installing ida-pro-mcp..."
    uv tool install ida-pro-mcp
    echo "[ok] ida-pro-mcp installed"
fi

# ── step 4: find installation directory ───────────────────────────────────────
find_install_dir() {
    [ -n "${IDADIR:-}" ] && [ -f "$IDADIR/ida.hlp" ] && { echo "$IDADIR"; return; }

    local cfg_dir="${IDAUSR:-$HOME/.idapro}"
    local cfg="$cfg_dir/ida-config.json"
    if [ -f "$cfg" ]; then
        local dir
        dir=$(python3 -c "
import json
try:
    d=json.load(open('$cfg'))
    print(d.get('Paths',{}).get('ida-install-dir',''))
except: pass
" 2>/dev/null || true)
        [ -n "$dir" ] && [ -f "$dir/ida.hlp" ] && { echo "$dir"; return; }
    fi

    # Platform defaults
    case "$PLATFORM" in
        macOS)
            for app in "/Applications/IDA Professional 9.3.app" "/Applications/IDA Pro 9.3.app"; do
                [ -f "$app/Contents/MacOS/ida.hlp" ] && { echo "$app/Contents/MacOS"; return; }
            done
            ;;
        *)
            for d in /opt/ida-pro-9.3 /opt/idapro-9.3 /opt/ida-9.3 \
                      "$HOME/ida-pro-9.3" "$HOME/idapro-9.3" "$HOME/ida-9.3"; do
                [ -f "$d/ida.hlp" ] && { echo "$d"; return; }
            done
            ;;
    esac
    echo ""
}

if [ "$SKIP_ACTIVATE" -eq 0 ]; then
    if [ -z "$INSTALL_DIR" ]; then
        INSTALL_DIR="$(find_install_dir)"
    fi

    if [ -n "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/ida.hlp" ]; then
        echo "[ok] Found installation: $INSTALL_DIR"
    elif [ -n "$INSTALL_DIR" ]; then
        echo "[!!] Path doesn't look like a valid installation: $INSTALL_DIR"
        exit 1
    else
        echo "[!!] Could not auto-detect installation directory."
        echo "     Re-run with: --install-dir /path/to/installation"
        echo "     Or set IDADIR in your environment."
        echo "     Skipping activation — MCP server will still start if idalib was"
        echo "     previously activated, or set IDADIR at runtime."
        SKIP_ACTIVATE=1
    fi
fi

# ── step 5: activate idalib ───────────────────────────────────────────────────
if [ "$SKIP_ACTIVATE" -eq 0 ]; then
    ACTIVATE="$INSTALL_DIR/idalib/python/py-activate-idalib.py"
    if [ -f "$ACTIVATE" ]; then
        echo "[..] Activating idalib bindings..."
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
fi

# ── step 6: Claude Code MCP config ────────────────────────────────────────────
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
entry = {"command": "uvx", "args": ["idalib-mcp", "--stdio"]}
install_dir = "$INSTALL_DIR" if "$SKIP_ACTIVATE" == "0" else ""
if install_dir:
    entry["env"] = {"IDADIR": install_dir}
cfg["mcpServers"]["binary-analysis"] = entry
with open("$MCP_CFG", "w") as f: json.dump(cfg, f, indent=2)
print("[ok] MCP config written to $MCP_CFG")
PYEOF
    echo "     Restart Claude Code to pick up the change."
else
    echo "[--] Claude Code not detected — add manually:"
    echo '     "binary-analysis": { "command": "uvx", "args": ["idalib-mcp", "--stdio"] }'
fi

# ── done ──────────────────────────────────────────────────────────────────────
echo ""
echo "Done.  Run: uvx idalib-mcp --stdio"
echo "Upgrade:    uv tool upgrade ida-pro-mcp"
