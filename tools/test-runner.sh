#!/usr/bin/env bash
# test-runner.sh — Smoke test the core PCX toolkit tools.
#
# Verifies that the upstream-only API index builder, symbol checker, and
# script linter all load and run without crashing.
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Running core PCX tool smoke tests..."

echo "  1. build-api-index --check..."
python3 "$TOOLKIT_DIR/tools/build-api-index.py" --check > /dev/null

echo "  2. symbol-check on hello-world template..."
python3 "$TOOLKIT_DIR/tools/symbol-check.py" "$TOOLKIT_DIR/templates/hello-world.em" > /dev/null

echo "  3. script-linter --help..."
python3 "$TOOLKIT_DIR/tools/script-linter.py" --help > /dev/null

echo "  4. check-doc-drift --help..."
python3 "$TOOLKIT_DIR/tools/check-doc-drift.py" --help > /dev/null

echo "  5. pcx verify on hello-world..."
python3 "$TOOLKIT_DIR/tools/pcx.py" verify "$TOOLKIT_DIR/templates/hello-world.em" > /dev/null

echo "[ok] All core PCX smoke tests passed successfully!"
