#!/usr/bin/env bash
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "pcx-ai-toolkit setup"
echo "Location: $TOOLKIT_DIR"
echo ""

# Check node/npm
if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
    echo "ERROR: node and npm are required for LSP servers."
    echo "Install Node.js 18+ from https://nodejs.org/"
    exit 1
fi
echo "[ok] node $(node --version), npm $(npm --version)"

# Clone LSP submodules if not present
if [ ! -d "$TOOLKIT_DIR/lsp/enma-lsp/.git" ]; then
    echo "[..] Cloning enma-lsp..."
    git clone --depth 1 https://github.com/sinnafuls/enma-lsp.git "$TOOLKIT_DIR/lsp/enma-lsp"
else
    echo "[ok] enma-lsp already present"
fi

if [ ! -d "$TOOLKIT_DIR/lsp/angel-lsp-pcx/.git" ]; then
    echo "[..] Cloning angel-lsp-pcx..."
    git clone --depth 1 https://github.com/sinnafuls/angel-lsp-pcx.git "$TOOLKIT_DIR/lsp/angel-lsp-pcx"
else
    echo "[ok] angel-lsp-pcx already present"
fi

# Build enma-lsp
echo "[..] Building enma-lsp..."
cd "$TOOLKIT_DIR/lsp/enma-lsp"
npm install --silent 2>/dev/null
npm run compile --silent 2>/dev/null
echo "[ok] enma-lsp built: server/dist/server.js"

# Build angel-lsp-pcx
echo "[..] Building angel-lsp-pcx..."
cd "$TOOLKIT_DIR/lsp/angel-lsp-pcx"
npm install --silent 2>/dev/null
npm run compile --silent 2>/dev/null
echo "[ok] angel-lsp-pcx built: server/out/server.js"

cd "$TOOLKIT_DIR"

# Install skills to Claude Code if present
if [ -d "$HOME/.claude" ]; then
    echo ""
    echo "[..] Claude Code detected — installing skills..."
    mkdir -p "$HOME/.claude/skills/game-hacking-pcx"
    mkdir -p "$HOME/.claude/skills/game-cheat-guidelines"
    cp "$TOOLKIT_DIR/.claude/skills/game-hacking-pcx/SKILL.md" "$HOME/.claude/skills/game-hacking-pcx/"
    cp "$TOOLKIT_DIR/.claude/skills/game-cheat-guidelines/SKILL.md" "$HOME/.claude/skills/game-cheat-guidelines/"
    echo "[ok] Skills installed to ~/.claude/skills/"
else
    echo ""
    echo "[--] Claude Code not detected — skip skill install."
    echo "     To install manually: cp -r .claude/skills/* ~/.claude/skills/"
fi

# Optional: copy CLAUDE.md to project
if [ "${1:-}" = "--project" ] && [ -n "${2:-}" ]; then
    echo "[..] Copying CLAUDE.md to $2"
    cp "$TOOLKIT_DIR/rules/CLAUDE.md" "$2/CLAUDE.md"
    echo "[ok] Project rules installed"
fi

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
