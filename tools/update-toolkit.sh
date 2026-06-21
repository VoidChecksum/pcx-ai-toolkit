#!/usr/bin/env bash
# update-toolkit.sh — Self-update pcx-ai-toolkit from its git remote.
#
# Pulls the latest changes from origin/main, rebuilds LSP servers,
# refreshes AI skills, and regenerates the llms-* knowledge bundles
# if they have drifted from the source.
#
# Usage:
#   ./tools/update-toolkit.sh              # normal update
#   ./tools/update-toolkit.sh --check      # check only, no changes
#   ./tools/update-toolkit.sh --force      # force re-run even if up to date
#   ./tools/update-toolkit.sh --skip-lsp   # skip LSP rebuild
#   ./tools/update-toolkit.sh --skip-skills # skip skill refresh
#   ./tools/update-toolkit.sh --skip-bundles # skip bundle regeneration
#
# Exit codes:
#   0  success (or already up to date with --check)
#   1  update needed (when using --check)
#   2  usage error
#   3  update failed
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ── arg parsing ──────────────────────────────────────────────────────────────

CHECK_ONLY=0
FORCE=0
SKIP_LSP=0
SKIP_SKILLS=0
SKIP_BUNDLES=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check)        CHECK_ONLY=1; shift ;;
        --force)        FORCE=1; shift ;;
        --skip-lsp)     SKIP_LSP=1; shift ;;
        --skip-skills)  SKIP_SKILLS=1; shift ;;
        --skip-bundles) SKIP_BUNDLES=1; shift ;;
        -h|--help)
            echo "Usage: $0 [--check] [--force] [--skip-lsp] [--skip-skills] [--skip-bundles]"
            exit 0 ;;
        *) echo "Unknown flag: $1" >&2; exit 2 ;;
    esac
done

cd "$TOOLKIT_DIR"

# ── preflight ────────────────────────────────────────────────────────────────

if ! git remote get-url origin &>/dev/null; then
    echo "No git remote 'origin' found — cannot auto-update." >&2
    exit 3
fi

CURRENT_REF="$(git rev-parse HEAD)"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REMOTE_BRANCH="origin/main"

# Handle detached HEAD — update still works if on a tagged commit
if [ "$CURRENT_BRANCH" = "HEAD" ]; then
    echo "Detached HEAD at $CURRENT_REF"
    echo "Switching to main before updating..."
    git checkout main 2>/dev/null || { echo "Could not checkout main" >&2; exit 3; }
    CURRENT_BRANCH="main"
    REMOTE_BRANCH="origin/main"
fi

# ── fetch ────────────────────────────────────────────────────────────────────

echo "Fetching from origin..."
git fetch origin 2>/dev/null || { echo "Fetch failed — check network" >&2; exit 3; }

REMOTE_REF="$(git rev-parse "$REMOTE_BRANCH" 2>/dev/null || true)"
if [ -z "$REMOTE_REF" ]; then
    echo "Could not resolve $REMOTE_BRANCH" >&2
    exit 3
fi

if [ "$CURRENT_REF" = "$REMOTE_REF" ] && [ "$FORCE" -eq 0 ]; then
    if [ "$CHECK_ONLY" -eq 1 ]; then
        echo "Up to date ($CURRENT_REF)"
        exit 0
    fi
    echo "Already up to date. Use --force to re-run post-update hooks."
    exit 0
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
    BEHIND="$(git rev-list --count HEAD.."$REMOTE_BRANCH" 2>/dev/null || echo '?')"
    AHEAD="$(git rev-list --count "$REMOTE_BRANCH"..HEAD 2>/dev/null || echo '?')"
    echo "Update available: $BEHIND commit(s) behind, $AHEAD commit(s) ahead"
    echo "  local:  $CURRENT_REF"
    echo "  remote: $REMOTE_REF"
    exit 1
fi

# ── safety: abort if local has uncommitted changes ──────────────────────────

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Uncommitted changes detected — stash or commit before updating." >&2
    echo "  Unstaged:  $(git diff --stat)" >&2
    echo "  Staged:    $(git diff --cached --stat)" >&2
    exit 3
fi

# ── update ───────────────────────────────────────────────────────────────────

echo "Updating $CURRENT_BRANCH..."
OLD_VERSION="$(cat VERSION 2>/dev/null || echo unknown)"

if [ "$FORCE" -eq 1 ] && [ "$CURRENT_REF" = "$REMOTE_REF" ]; then
    echo "Forced run — skipping git pull (already at latest)"
else
    git pull --ff-only origin "$CURRENT_BRANCH" 2>/dev/null || {
        echo "Pull failed — local and remote have diverged." >&2
        echo "Resolve manually: git pull --rebase origin $CURRENT_BRANCH" >&2
        exit 3
    }
fi

# Update submodules (LSP servers)
git submodule update --init --recursive 2>/dev/null || true

NEW_REF="$(git rev-parse HEAD)"
NEW_VERSION="$(cat VERSION 2>/dev/null || echo unknown)"

echo "[ok] Updated: $OLD_VERSION → $NEW_VERSION ($NEW_REF)"

# ── post-update: rebuild LSP servers ────────────────────────────────────────

if [ "$SKIP_LSP" -eq 0 ]; then
    echo ""
    echo "Rebuilding LSP servers..."

    for lsp in enma-lsp angel-lsp-pcx; do
        lsp_dir="$TOOLKIT_DIR/lsp/$lsp"
        if [ -d "$lsp_dir" ]; then
            echo "  $lsp..."
            (cd "$lsp_dir" && npm install --silent 2>/dev/null && npm run compile 2>/dev/null) \
                && echo "    [ok]" || echo "    [warn] build failed — run manually: cd $lsp_dir && npm install && npm run compile"
        fi
    done
fi

# ── post-update: rebuild Rust core parser ───────────────────────────────────
if [ "$SKIP_LSP" -eq 0 ] && command -v cargo &>/dev/null; then
    echo ""
    echo "Rebuilding Rust core parser (pe-parser)..."
    ( cd "$TOOLKIT_DIR/tools/pe-parser" && cargo build --release && mkdir -p ../bin && cp target/release/pe-parser ../bin/pe-parser ) >/dev/null 2>&1 || true
    if [ -f "$TOOLKIT_DIR/tools/bin/pe-parser" ]; then
        echo "  [ok] Rust core parser rebuilt: tools/bin/pe-parser"
    else
        echo "  [warn] Rust core build failed — falling back to Python"
    fi
fi

# ── post-update: refresh AI skills ───────────────────────────────────────────

if [ "$SKIP_SKILLS" -eq 0 ] && [ -d "$HOME/.claude" ]; then
    echo ""
    echo "Refreshing AI skills..."
    SKILLS_DIR="$TOOLKIT_DIR/.claude/skills"
    DEST_DIR="$HOME/.claude/skills"

    if [ -d "$SKILLS_DIR" ]; then
        for skill_dir in "$SKILLS_DIR"/*/; do
            skill_name="$(basename "$skill_dir")"
            mkdir -p "$DEST_DIR/$skill_name"
            cp -r "$skill_dir"*.md "$DEST_DIR/$skill_name/" 2>/dev/null || true
        done
        count="$(find "$SKILLS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)"
        echo "  [ok] $count skills refreshed"
    fi
fi

# ── post-update: regenerate knowledge bundles ────────────────────────────────

if [ "$SKIP_BUNDLES" -eq 0 ]; then
    echo ""
    echo "Checking knowledge bundles..."
    BUILDER="$TOOLKIT_DIR/tools/build-llms-index.py"
    if [ -f "$BUILDER" ]; then
        if python3 "$BUILDER" --check 2>/dev/null; then
            echo "  [ok] Bundles in sync"
        else
            echo "  Bundles out of sync — regenerating..."
            python3 "$BUILDER" --quiet 2>/dev/null \
                && echo "  [ok] Bundles regenerated" \
                || echo "  [warn] Bundle regeneration failed — run: python3 tools/build-llms-index.py"
        fi
    fi
fi

# ── done ────────────────────────────────────────────────────────────────────

echo ""
echo "Update complete."
echo "  Version:  $NEW_VERSION"
echo "  Commit:   $NEW_REF"
echo "  Branch:   $CURRENT_BRANCH"
[ "$SKIP_LSP" -eq 0 ]    && echo "  LSP:      rebuilt"
[ "$SKIP_LSP" -eq 0 ]    && command -v cargo &>/dev/null && [ -f "$TOOLKIT_DIR/tools/bin/pe-parser" ] && echo "  Rust:     rebuilt"
[ "$SKIP_SKILLS" -eq 0 ]  && echo "  Skills:   refreshed"
[ "$SKIP_BUNDLES" -eq 0 ] && echo "  Bundles:  checked"
