#!/usr/bin/env bash
# Install reverse engineering plugins, deobfuscation tools, and Python packages.
#
# Clones IDA/Ghidra plugins and installs Python analysis packages into a
# central directory. Copies IDA plugins to ~/.idapro/plugins/ if present.
#
# Usage:
#   ./tools/install-re-tools.sh                 # install everything
#   ./tools/install-re-tools.sh --plugins-only   # skip Python packages
#   ./tools/install-re-tools.sh --python-only    # skip plugin clones
#   ./tools/install-re-tools.sh --prefix ~/tools # custom install dir
set -euo pipefail

PREFIX="${HOME}/re-tools"
DO_PLUGINS=1
DO_PYTHON=1

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prefix)       PREFIX="$2"; shift 2 ;;
        --plugins-only) DO_PYTHON=0; shift ;;
        --python-only)  DO_PLUGINS=0; shift ;;
        *)              echo "Unknown arg: $1"; exit 1 ;;
    esac
done

echo "RE Tools Installer"
echo "  Install dir: $PREFIX"
echo "  Plugins: $([ $DO_PLUGINS -eq 1 ] && echo yes || echo skip)"
echo "  Python:  $([ $DO_PYTHON -eq 1 ] && echo yes || echo skip)"
echo ""

mkdir -p "$PREFIX"

# ── helper ────────────────────────────────────────────────────────────────────
clone_or_pull() {
    local repo="$1" dir="$2"
    if [ -d "$dir/.git" ]; then
        echo "  [pull] $dir"
        git -C "$dir" pull --ff-only -q 2>/dev/null || true
    else
        echo "  [clone] $repo → $dir"
        git clone --depth 1 -q "$repo" "$dir"
    fi
}

# ── IDA plugins ───────────────────────────────────────────────────────────────
if [ $DO_PLUGINS -eq 1 ]; then
    echo "── IDA Plugins ──"
    mkdir -p "$PREFIX/ida-plugins"

    # hrtng — Kaspersky deobfuscation (2024 contest winner)
    clone_or_pull "https://github.com/AandersonL/hrtng.git" "$PREFIX/ida-plugins/hrtng"

    # HexRaysCodeXplorer — C++ vtable reconstruction
    clone_or_pull "https://github.com/REhints/HexRaysCodeXplorer.git" "$PREFIX/ida-plugins/HexRaysCodeXplorer-ida9"

    # ClassInformer — MSVC RTTI scanner
    clone_or_pull "https://github.com/nihilus/IDA_ClassInformer_PlugIn.git" "$PREFIX/ida-plugins/IDA_ClassInformer_PlugIn"

    # SigMakerEx — byte pattern signature generator
    clone_or_pull "https://github.com/A200K/IDA-Pro-SigMaker.git" "$PREFIX/ida-plugins/sigmakerex"

    # FIRST — Cisco Talos function fingerprints (free Lumina alt)
    clone_or_pull "https://github.com/ciscocsirt/FIRST-plugin-ida.git" "$PREFIX/ida-plugins/FIRST-plugin-ida"

    # RevEng.AI — binary similarity
    clone_or_pull "https://github.com/RevEngAI/reai-ida.git" "$PREFIX/ida-plugins/reai-ida"

    # D-810 — CFF/MBA/opaque predicate deobfuscation
    clone_or_pull "https://github.com/joydo/d-810.git" "$PREFIX/ida-plugins/d-810"

    # HashDB — API hash resolver
    clone_or_pull "https://github.com/OALabs/hashdb-ida.git" "$PREFIX/ida-plugins/hashdb-ida"

    # Diaphora — binary diffing
    clone_or_pull "https://github.com/joxeankoret/diaphora.git" "$PREFIX/diffing/diaphora"

    echo ""
    echo "── Ghidra Plugins ──"
    mkdir -p "$PREFIX/ghidra-plugins"

    # GhidrAssist — LLM-powered RE assistant
    clone_or_pull "https://github.com/jtang613/GhidrAssist.git" "$PREFIX/ghidra-plugins/GhidrAssist"

    # BinDiffHelper — cross-version diffing
    clone_or_pull "https://github.com/ubfx/BinDiffHelper.git" "$PREFIX/ghidra-plugins/BinDiffHelper"

    # OOAnalyzer (Pharos) — automated C++ recovery
    clone_or_pull "https://github.com/cmu-sei/pharos.git" "$PREFIX/ghidra-plugins/pharos"

    # RevEng.AI for Ghidra
    clone_or_pull "https://github.com/RevEngAI/reai-ghidra.git" "$PREFIX/ghidra-plugins/plugin-ghidra"

    echo ""
    echo "── Debugger Sync ──"
    mkdir -p "$PREFIX/misc"
    clone_or_pull "https://github.com/bootleg/ret-sync.git" "$PREFIX/misc/ret-sync"

    echo ""
    echo "── FLIRT Signatures ──"
    mkdir -p "$PREFIX/signatures"
    clone_or_pull "https://github.com/Maktm/FLIRTDB.git" "$PREFIX/signatures/FLIRTDB"
    clone_or_pull "https://github.com/push0ebp/sig-database.git" "$PREFIX/signatures/sig-database"

    echo ""
    echo "── Deobfuscation Tools ──"
    mkdir -p "$PREFIX/deobfuscation"

    # NoVmp — VMProtect devirtualizer
    clone_or_pull "https://github.com/can1357/NoVmp.git" "$PREFIX/deobfuscation/NoVmp"

    # vtil — VM Translation IL
    clone_or_pull "https://github.com/vtil-project/VTIL-Core.git" "$PREFIX/deobfuscation/VTIL-Core"

    # ScyllaHide — anti-anti-debug
    clone_or_pull "https://github.com/x64dbg/ScyllaHide.git" "$PREFIX/deobfuscation/ScyllaHide"

    # Scylla — IAT reconstruction
    clone_or_pull "https://github.com/NtQuery/Scylla.git" "$PREFIX/deobfuscation/Scylla"

    # pe-sieve — hollowing detector
    clone_or_pull "https://github.com/hasherezade/pe-sieve.git" "$PREFIX/deobfuscation/pe-sieve"

    # ── Copy IDA plugins to ~/.idapro/plugins/ if it exists ──
    IDAPRO_PLUGINS="$HOME/.idapro/plugins"
    if [ -d "$IDAPRO_PLUGINS" ]; then
        echo ""
        echo "── Copying Python plugins to $IDAPRO_PLUGINS ──"

        # FIRST
        if [ -d "$PREFIX/ida-plugins/FIRST-plugin-ida/first_plugin_ida" ]; then
            cp -r "$PREFIX/ida-plugins/FIRST-plugin-ida/first_plugin_ida/"* "$IDAPRO_PLUGINS/" 2>/dev/null || true
            echo "  [ok] FIRST"
        fi

        # D-810
        if [ -d "$PREFIX/ida-plugins/d-810/d810" ]; then
            cp -r "$PREFIX/ida-plugins/d-810/d810" "$IDAPRO_PLUGINS/" 2>/dev/null || true
            cp "$PREFIX/ida-plugins/d-810/d810.py" "$IDAPRO_PLUGINS/" 2>/dev/null || true
            echo "  [ok] D-810"
        fi

        # HashDB
        if [ -f "$PREFIX/ida-plugins/hashdb-ida/hashdb.py" ]; then
            cp "$PREFIX/ida-plugins/hashdb-ida/hashdb.py" "$IDAPRO_PLUGINS/" 2>/dev/null || true
            echo "  [ok] HashDB"
        fi

        # Diaphora
        if [ -f "$PREFIX/diffing/diaphora/diaphora.py" ]; then
            cp "$PREFIX/diffing/diaphora/diaphora.py" "$IDAPRO_PLUGINS/" 2>/dev/null || true
            echo "  [ok] Diaphora"
        fi
    fi

    # ── Copy FLIRT sigs to IDA sig dirs ──
    for sigdir in "$HOME/.idapro/sig/pc" "$HOME/ida-pro-"*/sig/pc; do
        [ -d "$sigdir" ] || continue
        echo ""
        echo "── Copying FLIRT sigs to $sigdir ──"
        find "$PREFIX/signatures" -name '*.sig' -exec cp {} "$sigdir/" \; 2>/dev/null
        count=$(find "$sigdir" -name '*.sig' | wc -l)
        echo "  [ok] $count sig files"
        break
    done

    echo ""
fi

# ── Python packages ───────────────────────────────────────────────────────────
if [ $DO_PYTHON -eq 1 ]; then
    echo "── Python Analysis Packages ──"

    PIP="pip3"
    command -v pip3 >/dev/null 2>&1 || PIP="pip"

    # Core RE packages
    $PIP install --quiet --upgrade \
        capstone \
        unicorn \
        keystone-engine \
        pefile \
        lief \
        2>/dev/null && echo "  [ok] capstone, unicorn, keystone, pefile, lief" || echo "  [!!] some core packages failed"

    # Symbolic execution & deobfuscation
    $PIP install --quiet --upgrade \
        triton-library \
        miasm \
        floss \
        frida-tools \
        2>/dev/null && echo "  [ok] triton, miasm, floss, frida" || echo "  [!!] some analysis packages failed (may need build deps)"

    # angr is large — install separately
    echo "  [..] angr (large install, may take a minute)..."
    $PIP install --quiet --upgrade angr 2>/dev/null \
        && echo "  [ok] angr" \
        || echo "  [!!] angr failed (needs Python 3.10+, may need: pip install angr)"

    echo ""
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo "Done."
echo ""
echo "Installed to: $PREFIX"
echo ""
if [ $DO_PLUGINS -eq 1 ]; then
    echo "IDA Plugins (need IDA SDK to build native ones):"
    echo "  hrtng, HexRaysCodeXplorer, ClassInformer, SigMakerEx"
    echo "  FIRST, RevEng.AI, D-810, HashDB, Diaphora"
    echo ""
    echo "Ghidra Plugins:"
    echo "  GhidrAssist, BinDiffHelper, OOAnalyzer (Pharos), RevEng.AI"
    echo ""
    echo "Deobfuscation:"
    echo "  NoVmp (build: cd NoVmp && cmake -B build && cmake --build build)"
    echo "  VTIL-Core, ScyllaHide, Scylla, pe-sieve"
    echo ""
fi
if [ $DO_PYTHON -eq 1 ]; then
    echo "Python packages: capstone, unicorn, keystone, pefile, lief,"
    echo "  triton, miasm, floss, frida, angr"
fi
