#!/usr/bin/env bash
# pcx-ai-toolkit setup for Linux, macOS, WSL, Git Bash, and Cygwin.
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")" && pwd)"

case "$(uname -s)" in
    Linux*)   PLATFORM="Linux" ;;
    Darwin*)  PLATFORM="macOS" ;;
    CYGWIN*)  PLATFORM="Cygwin" ;;
    MINGW*|MSYS*) PLATFORM="Git Bash / MSYS" ;;
    *)        PLATFORM="$(uname -s)" ;;
esac
if [ "$PLATFORM" = "Linux" ] && grep -qiE "microsoft|wsl" /proc/version 2>/dev/null; then
    PLATFORM="WSL"
fi

echo "pcx-ai-toolkit setup"
echo "Platform: $PLATFORM"
echo "Location: $TOOLKIT_DIR"
echo ""

for cmd in git node npm cargo; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: '$cmd' is required but not found."
        case "$cmd" in
            node|npm) echo "Install Node.js 18+ from https://nodejs.org/" ;;
            git)      echo "Install Git from https://git-scm.com/" ;;
            cargo)    echo "Install Rust from https://rustup.rs/" ;;
        esac
        exit 1
    fi
done
echo "[ok] git $(git --version | awk '{print $3}'), node $(node --version), npm $(npm --version), cargo $(cargo --version | awk '{print $2}')"

echo "Building Rust tools..."
(
    cd "$TOOLKIT_DIR/tools/pe-parser"
    cargo build --release
)
mkdir -p "$TOOLKIT_DIR/tools/bin"
for tool in pe-parser pcx-rs api-lookup pattern-format-converter \
    sig-uniqueness-checker binary-diff-summary offset-diff \
    anti-debug-scanner identify-protector pe-section-analyzer \
    analyze-vmprotect dump-strings-xor module-export-mapper; do
    cp "$TOOLKIT_DIR/tools/pe-parser/target/release/$tool" "$TOOLKIT_DIR/tools/bin/$tool"
done

PCX_TOOLS_DIR="$TOOLKIT_DIR/tools/bin"
ADD_PATH_LINE="export PATH=\"\$PATH:$PCX_TOOLS_DIR\""
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

TOOLKIT_VERSION="$(cat "$TOOLKIT_DIR/VERSION" 2>/dev/null || echo unknown)"
echo "Version: $TOOLKIT_VERSION"
echo ""
echo "Setup complete."
echo ""
echo "Documentation:  $TOOLKIT_DIR/docs/"
echo "Knowledge base: $TOOLKIT_DIR/knowledge/"
echo "Skills:         $TOOLKIT_DIR/.claude/skills/"
echo "MCP config:     $TOOLKIT_DIR/mcp/"
echo "Templates:      $TOOLKIT_DIR/templates/"
echo ""
echo "Quick start:"
echo "  1. Add $PCX_TOOLS_DIR to PATH"
echo "  2. Run: pcx-rs doctor"
echo "  3. See docs/AI_AGENT_OPERATING_MANUAL.md"
