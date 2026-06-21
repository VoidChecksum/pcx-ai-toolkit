#!/usr/bin/env bash
# pcx-ai-toolkit setup for Linux, macOS, WSL, Git Bash, and Cygwin.
# Windows users without a bash shell: use setup.ps1 instead.
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detect platform (informational)
case "$(uname -s)" in
    Linux*)   PLATFORM="Linux" ;;
    Darwin*)  PLATFORM="macOS" ;;
    CYGWIN*)  PLATFORM="Cygwin" ;;
    MINGW*|MSYS*) PLATFORM="Git Bash / MSYS" ;;
    *)        PLATFORM="$(uname -s)" ;;
esac
# WSL reports Linux but has Microsoft in the kernel string
if [ "$PLATFORM" = "Linux" ] && grep -qiE "microsoft|wsl" /proc/version 2>/dev/null; then
    PLATFORM="WSL"
fi

echo "pcx-ai-toolkit setup"
echo "Platform: $PLATFORM"
echo "Location: $TOOLKIT_DIR"
echo ""

# --- Check prerequisites ---
for cmd in git node npm; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: '$cmd' is required but not found."
        case "$cmd" in
            node|npm) echo "Install Node.js 18+ from https://nodejs.org/" ;;
            git)      echo "Install Git from https://git-scm.com/" ;;
        esac
        exit 1
    fi
done
echo "[ok] git $(git --version | awk '{print $3}'), node $(node --version), npm $(npm --version)"

# --- Run core setup logic via python ---
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3.10+ is required but not found on PATH."
    exit 1
fi

$PYTHON_CMD "$TOOLKIT_DIR/tools/setup-core.py" "$@"

# --- Add tools to PATH ---
PCX_TOOLS_DIR="$TOOLKIT_DIR/tools"
chmod +x "$PCX_TOOLS_DIR/pcx" 2>/dev/null || true
ADD_PATH_LINE="export PATH=\"\$PATH:$PCX_TOOLS_DIR\""

# Determine shell profile
SHELL_PROFILE=""
if [ -n "${ZSH_VERSION:-}" ] && [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
elif [ -f "$HOME/.profile" ]; then
    SHELL_PROFILE="$HOME/.profile"
fi

if [ -n "$SHELL_PROFILE" ]; then
    if ! grep -qF "$PCX_TOOLS_DIR" "$SHELL_PROFILE" 2>/dev/null; then
        echo "" >> "$SHELL_PROFILE"
        echo "# pcx-ai-toolkit CLI" >> "$SHELL_PROFILE"
        echo "$ADD_PATH_LINE" >> "$SHELL_PROFILE"
        echo "[ok] Added $PCX_TOOLS_DIR to $SHELL_PROFILE"
        echo "     Please run: source $SHELL_PROFILE"
    else
        echo "[ok] pcx tools directory already in $SHELL_PROFILE"
    fi
else
    echo "[warn] Could not auto-detect shell profile. Add this manually to your shell profile:"
    echo "  $ADD_PATH_LINE"
fi

# --- Record installed version ---
TOOLKIT_VERSION="$(cat "$TOOLKIT_DIR/VERSION" 2>/dev/null || echo unknown)"
echo "Version: $TOOLKIT_VERSION"

echo ""
echo "Setup complete."
echo ""
echo "Documentation:  $TOOLKIT_DIR/docs/ ($(find "$TOOLKIT_DIR/docs" -name '*.md' | wc -l) files)"
echo "Knowledge base: $TOOLKIT_DIR/knowledge/"
echo "Skills:         $TOOLKIT_DIR/.claude/skills/"
echo "MCP config:     $TOOLKIT_DIR/mcp/"
echo "Templates:      $TOOLKIT_DIR/templates/"
echo ""
echo "Quick start:"
echo "  1. Copy rules/CLAUDE.md to your PCX scripting project"
echo "  2. Start coding — the AI reads docs automatically"
echo "  3. See mcp/claude-code-setup.md for full integration"
