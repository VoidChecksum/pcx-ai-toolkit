#!/usr/bin/env bash
# test-runner.sh — Smoke test all python tools against a mock PE binary.
#
# Generates a valid x64 PE binary with imports, exports, and PEB-walk
# signatures, then runs all tools to verify zero crashes and correct outputs.
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_EXE="/tmp/pcx_test.exe"
SIGS_JSON="/tmp/pcx_sigs.json"
PROJECT_TMP="/tmp/pcx_project_smoke"
cleanup() {
    rm -f "$TEST_EXE" "$SIGS_JSON"
    rm -rf "$PROJECT_TMP"
}
trap cleanup EXIT

echo "Generating mock PE binary..."
python3 - <<'PY'
import struct
pe = bytearray(16384)
pe[0:2] = b'MZ'
struct.pack_into('<I', pe, 0x3C, 0x80)
pe[0x80:0x84] = b'PE\x00\x00'
struct.pack_into('<HHIIIHH', pe, 0x84, 0x8664, 2, 0, 0, 0, 0xF0, 0x22)
struct.pack_into('<H', pe, 0x98, 0x20B)
struct.pack_into('<I', pe, 0x98 + 16, 0x1000)
struct.pack_into('<Q', pe, 0x98 + 24, 0x140000000)
struct.pack_into('<II', pe, 0x98 + 32, 0x1000, 0x200)
struct.pack_into('<II', pe, 0x98 + 56, 0x4000, 0x200)
# Export dir: RVA=0x3000, Size=0x28
struct.pack_into('<II', pe, 0x98 + 112, 0x3000, 0x28)
# Import dir: RVA=0x2000, Size=0x28
struct.pack_into('<II', pe, 0x98 + 120, 0x2000, 0x28)
pe[0x188:0x190] = b'.text\x00\x00\x00'
struct.pack_into('<IIIIIIHHI', pe, 0x188 + 8, 0x1000, 0x1000, 0x200, 0x400, 0, 0, 0, 0, 0x60000020)
pe[0x1B0:0x1B8] = b'.rdata\x00\x00'
struct.pack_into('<IIIIIIHHI', pe, 0x1B0 + 8, 0x2000, 0x2000, 0x2000, 0x600, 0, 0, 0, 0, 0x40000040)
# Import Descriptor
struct.pack_into('<IIIII', pe, 0x600, 0x2028, 0, 0, 0x203C, 0x2030)
struct.pack_into('<QQ', pe, 0x628, 0x204A, 0)
struct.pack_into('<QQ', pe, 0x630, 0x204A, 0)
pe[0x63C:0x63C+12] = b'kernel32.dll\x00'
pe[0x64A:0x64A+2] = b'\x00\x00'
pe[0x64C:0x64C+18] = b'IsDebuggerPresent\x00'
pe[0x400:0x409] = b'\x65\x48\x8b\x04\x25\x60\x00\x00\x00'
# Export Table at RVA 0x3000 (Raw 0x1600)
struct.pack_into('<IIHHIIIIIII', pe, 0x1600, 0, 0, 0, 0, 0x3040, 1, 2, 2, 0x3028, 0x3030, 0x3038)
struct.pack_into('<II', pe, 0x1628, 0x1000, 0x1010)
struct.pack_into('<II', pe, 0x1630, 0x304A, 0x3055)
struct.pack_into('<HH', pe, 0x1638, 0, 1)
pe[0x1640:0x1649] = b'test.dll\x00'
pe[0x164A:0x1654] = b'FuncFirst\x00'
pe[0x1655:0x1660] = b'FuncSecond\x00'
with open("/tmp/pcx_test.exe", "wb") as f: f.write(pe)
PY

python3 -c '
import json
sigs = [{"name": "test_peb", "pattern": "65 48 8b 04 25 60 00 00 00", "kind": "direct"}]
with open("/tmp/pcx_sigs.json", "w") as f: json.dump(sigs, f)
'

echo "Running tool smoke tests..."

echo "  1. anti-debug-scanner..."
python3 "$TOOLKIT_DIR/tools/anti-debug-scanner.py" --json "$TEST_EXE" > /dev/null

echo "  2. identify-protector..."
python3 "$TOOLKIT_DIR/tools/identify-protector.py" --json "$TEST_EXE" > /dev/null

echo "  3. module-export-mapper..."
python3 "$TOOLKIT_DIR/tools/module-export-mapper.py" "$TEST_EXE" > /dev/null

echo "  4. pe-section-analyzer..."
python3 "$TOOLKIT_DIR/tools/pe-section-analyzer.py" --json "$TEST_EXE" > /dev/null

echo "  5. sig-uniqueness-checker..."
python3 "$TOOLKIT_DIR/tools/sig-uniqueness-checker.py" --json --sig "65 48 8B 04 25 60 00 00 00" "$TEST_EXE" > /dev/null

echo "  6. binary-diff-summary..."
python3 "$TOOLKIT_DIR/tools/binary-diff-summary.py" --json --old "$TEST_EXE" --new "$TEST_EXE" > /dev/null

echo "  7. offset-diff..."
python3 "$TOOLKIT_DIR/tools/offset-diff.py" --json --old "$TEST_EXE" --new "$TEST_EXE" --sigs "$SIGS_JSON" > /dev/null

echo "  8. dump-strings-xor..."
python3 "$TOOLKIT_DIR/tools/dump-strings-xor.py" --json "$TEST_EXE" > /dev/null

echo "  9. pattern-format-converter..."
python3 "$TOOLKIT_DIR/tools/pattern-format-converter.py" --from ida --to all --pat "48 8B ? ? ? ?" > /dev/null

echo " 10. resolve-api-hashes..."
# Run with help to verify it loads and executes
python3 "$TOOLKIT_DIR/tools/resolve-api-hashes.py" --help > /dev/null

echo " 11. script-linter..."
python3 "$TOOLKIT_DIR/tools/script-linter.py" --help > /dev/null

echo " 12. dumper-to-enma..."
python3 "$TOOLKIT_DIR/tools/dumper-to-enma.py" --help > /dev/null

echo " 13. evidence-log-validator..."
python3 "$TOOLKIT_DIR/tools/evidence-log-validator.py" --help > /dev/null

echo " 14. analyze-vmprotect..."
python3 "$TOOLKIT_DIR/tools/analyze-vmprotect.py" --json "$TEST_EXE" > /dev/null

echo " 15. build-api-index --check..."
python3 "$TOOLKIT_DIR/tools/build-api-index.py" --check > /dev/null

echo " 16. symbol-check on hello-world template..."
python3 "$TOOLKIT_DIR/tools/symbol-check.py" "$TOOLKIT_DIR/templates/hello-world.em" > /dev/null

echo " 17. as-linter..."
python3 "$TOOLKIT_DIR/tools/as-linter.py" --strict "$TOOLKIT_DIR/templates/full-project-as" > /dev/null

echo " 18. verify-project on templates..."
python3 "$TOOLKIT_DIR/tools/verify-project.py" "$TOOLKIT_DIR/templates" --allow-placeholders --allow-unverified > /dev/null

echo " 19. pcx create scaffold..."
rm -rf "$PROJECT_TMP"
python3 "$TOOLKIT_DIR/tools/pcx.py" create --name Smoke --language enma --kind full --target smoke.exe --output "$PROJECT_TMP" > /dev/null
python3 "$TOOLKIT_DIR/tools/verify-project.py" "$PROJECT_TMP" --allow-placeholders --allow-unverified > /dev/null

echo " 20. re-importer..."
printf 'name,address,kind\nLocalPlayer,0x1234,symbol\n' \
    | python3 "$TOOLKIT_DIR/tools/re-importer.py" --format ida-names --out-format enma-offsets - \
    | grep -q 'OFF_LOCALPLAYER'

echo " 21. hallucination-eval..."
python3 "$TOOLKIT_DIR/tools/hallucination-eval.py" > /dev/null

echo "Cleaning up..."
echo "[ok] All smoke tests passed successfully!"
