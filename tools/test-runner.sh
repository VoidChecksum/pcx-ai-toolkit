#!/usr/bin/env bash
# Rust-only smoke runner for pcx-ai-toolkit.
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Building Rust tools..."
(
    cd "$TOOLKIT_DIR/tools/pe-parser"
    cargo build --release >/dev/null
)

mkdir -p "$TOOLKIT_DIR/tools/bin"
for tool in pe-parser pcx-rs api-lookup pattern-format-converter \
    sig-uniqueness-checker binary-diff-summary offset-diff \
    anti-debug-scanner identify-protector pe-section-analyzer \
    analyze-vmprotect dump-strings-xor module-export-mapper; do
    cp "$TOOLKIT_DIR/tools/pe-parser/target/release/$tool" "$TOOLKIT_DIR/tools/bin/$tool"
done

echo "Running Rust tests..."
cargo test --manifest-path "$TOOLKIT_DIR/tools/pe-parser/Cargo.toml"

echo "Checking pcx-rs smoke commands..."
"$TOOLKIT_DIR/tools/bin/pcx-rs" doctor >/dev/null
"$TOOLKIT_DIR/tools/bin/pcx-rs" api draw_text --json >/dev/null
"$TOOLKIT_DIR/tools/bin/pcx-rs" symbol-check "$TOOLKIT_DIR/templates/hello-world.em" >/dev/null
"$TOOLKIT_DIR/tools/bin/pcx-rs" verify-project "$TOOLKIT_DIR/examples/scenarios" --allow-placeholders --allow-unverified >/dev/null

echo "[ok] Rust-only smoke tests passed"
