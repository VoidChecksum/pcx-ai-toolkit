#!/usr/bin/env bash
# Update pcx-ai-toolkit and rebuild Rust tools.
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHECK=0
FORCE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --check) CHECK=1 ;;
        --force) FORCE=1 ;;
        -h|--help)
            echo "Usage: update-toolkit.sh [--check] [--force]"
            exit 0
            ;;
        *) echo "ERROR: unknown option $1" >&2; exit 2 ;;
    esac
    shift
done

cd "$TOOLKIT_DIR"
if [ "$CHECK" -eq 1 ]; then
    git fetch --quiet
    LOCAL="$(git rev-parse HEAD)"
    REMOTE="$(git rev-parse @{u})"
    if [ "$LOCAL" = "$REMOTE" ]; then
        echo "[ok] Toolkit is up to date"
        exit 0
    fi
    echo "[update] Local $LOCAL differs from upstream $REMOTE"
    exit 1
fi

git pull --ff-only

if [ "$FORCE" -eq 1 ] || [ ! -x "$TOOLKIT_DIR/tools/bin/pcx-rs" ]; then
    echo "Building Rust tools..."
    (cd "$TOOLKIT_DIR/tools/pe-parser" && cargo build --release)
    mkdir -p "$TOOLKIT_DIR/tools/bin"
    for tool in pe-parser pcx-rs api-lookup pattern-format-converter \
        sig-uniqueness-checker binary-diff-summary offset-diff \
        anti-debug-scanner identify-protector pe-section-analyzer \
        analyze-vmprotect dump-strings-xor module-export-mapper; do
        cp "$TOOLKIT_DIR/tools/pe-parser/target/release/$tool" "$TOOLKIT_DIR/tools/bin/$tool"
    done
fi

echo "[ok] pcx-ai-toolkit updated"
