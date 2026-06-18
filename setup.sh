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

# --- Clone + build an LSP server, verifying the output file exists ---
install_lsp() {
    local name="$1" url="$2" out_file="$3"
    local dir="$TOOLKIT_DIR/lsp/$name"

    if [ ! -d "$dir/.git" ]; then
        echo "[..] Cloning $name..."
        git clone --depth 1 "$url" "$dir"
    else
        echo "[ok] $name already present"
    fi

    echo "[..] Building $name..."
    ( cd "$dir" && npm install && npm run compile ) >/dev/null 2>&1 || true

    if [ -f "$dir/$out_file" ]; then
        echo "[ok] $name built: $out_file"
    else
        echo "[!!] $name build did not produce $out_file"
        echo "     Run manually:  cd lsp/$name && npm install && npm run compile"
    fi
}

install_lsp "enma-lsp"      "https://github.com/sinnafuls/enma-lsp.git"      "server/dist/server.js"
install_lsp "angel-lsp-pcx" "https://github.com/sinnafuls/angel-lsp-pcx.git" "server/out/server.js"

# --- Build Rust tools if cargo is available ---
if command -v cargo &>/dev/null; then
    echo ""
    echo "[..] Building Rust tools (pe-parser, sig-uniqueness-checker, binary-diff-summary, offset-diff)..."
    ( cd "$TOOLKIT_DIR/tools/pe-parser" && cargo build --release && mkdir -p ../bin && cp target/release/pe-parser ../bin/pe-parser && cp target/release/sig-uniqueness-checker ../bin/sig-uniqueness-checker && cp target/release/binary-diff-summary ../bin/binary-diff-summary && cp target/release/offset-diff ../bin/offset-diff ) >/dev/null 2>&1 || true
    if [ -f "$TOOLKIT_DIR/tools/bin/pe-parser" ]; then
        echo "[ok] Rust tools built: tools/bin/pe-parser, tools/bin/sig-uniqueness-checker, tools/bin/binary-diff-summary, tools/bin/offset-diff"
    else
        echo "[!!] Rust tools build failed — falling back to Python implementations"
    fi
else
    echo ""
    echo "[--] Cargo not found — using Python implementations"
fi

# --- Install skills to Claude Code if present ---
# On Git Bash/WSL, $HOME maps to the Windows user profile, so this works there too.
if [ -d "$HOME/.claude" ]; then
    echo ""
    echo "[..] Claude Code detected — installing skills..."
    for skill_dir in "$TOOLKIT_DIR"/.claude/skills/*/; do
        [ -f "$skill_dir/SKILL.md" ] || continue
        skill="$(basename "$skill_dir")"
        mkdir -p "$HOME/.claude/skills/$skill"
        cp "$skill_dir/SKILL.md" "$HOME/.claude/skills/$skill/"
    done
    echo "[ok] Skills installed to ~/.claude/skills/"
else
    echo ""
    echo "[--] Claude Code not detected — skip skill install."
    echo "     Manual: cp -r .claude/skills/* ~/.claude/skills/"
fi

# --- Optional: copy CLAUDE.md to a project ---
if [ "${1:-}" = "--project" ] && [ -n "${2:-}" ]; then
    if [ -d "$2" ]; then
        cp "$TOOLKIT_DIR/rules/CLAUDE.md" "$2/CLAUDE.md"
        echo "[ok] Project rules copied to $2/CLAUDE.md"
    else
        echo "[!!] Project path not found: $2"
    fi
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
