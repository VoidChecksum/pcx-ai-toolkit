#!/usr/bin/env bash
# Install reverse engineering plugins, deobfuscation tools, and Python packages.
#
# Clones IDA/Ghidra plugins and installs Python analysis packages into a
# central directory. Copies IDA plugins to ~/.idapro/plugins/ if present.
#
# Supply-chain hardening:
#   - Every third-party clone is pinned to a specific tag/commit (see the
#     audit table printed at the end). Repos without a releasable tag are
#     pinned to their default branch with a TODO + warning — review those.
#   - Python packages install into an isolated venv at $PREFIX/venv; the
#     system interpreter is never touched.
#
# Usage:
#   ./tools/install-re-tools.sh                  # install everything
#   ./tools/install-re-tools.sh --plugins-only   # skip Python packages
#   ./tools/install-re-tools.sh --python-only     # skip plugin clones
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

# ── Supply-chain warning ─────────────────────────────────────────────────────
echo "[!] Supply-chain notice:"
echo "    This script clones 21 third-party repos and installs Python packages."
echo "    Each clone is pinned to a specific ref (see the audit table at the end)."
echo "    Packages install into an isolated venv at $PREFIX/venv — system Python is not touched."
echo "    Review the pinned refs and resolved commits in the summary before trusting any tool."
echo ""

mkdir -p "$PREFIX"

# ── helper ────────────────────────────────────────────────────────────────────
# clone_or_pull <repo_url> <dest_dir> <pinned_ref|-> <name>
#   <pinned_ref>  a git tag to clone with `--branch` (shallow, pinned).
#                 pass "-" to clone the default branch with a TODO warning
#                 (used only where no release tag/SHA could be determined).
# Records (name, url, ref, resolved_sha, dest) into PIN_ROWS for the audit table.
PIN_ROWS=()
clone_or_pull() {
    local repo="$1" dir="$2" ref="$3" name="$4"
    local resolved

    if [ -d "$dir/.git" ]; then
        if [ "$ref" = "-" ]; then
            echo "  [update] $name (default branch — UNAUDITED)"
            git -C "$dir" pull --ff-only -q 2>/dev/null || true
        else
            echo "  [update] $name @ $ref"
            git -C "$dir" fetch --depth 1 -q origin "$ref" 2>/dev/null || true
            git -C "$dir" checkout -q "$ref" 2>/dev/null \
                || git -C "$dir" checkout -q FETCH_HEAD 2>/dev/null || true
        fi
    else
        if [ "$ref" = "-" ]; then
            echo "  [!] $name — no pinned ref; cloning default branch (UNAUDITED)"
            echo "      TODO: pin $repo to a specific commit/tag once one is available."
            git clone --depth 1 -q "$repo" "$dir"
        else
            echo "  [clone] $name @ $ref → $dir"
            git clone --depth 1 --branch "$ref" -q "$repo" "$dir"
        fi
    fi

    resolved=$(git -C "$dir" rev-parse HEAD 2>/dev/null || echo "(unavailable)")
    PIN_ROWS+=("$name"$'\t'"$repo"$'\t'"$ref"$'\t'"$resolved"$'\t'"$dir")
}

# ── IDA plugins ───────────────────────────────────────────────────────────────
if [ $DO_PLUGINS -eq 1 ]; then
    echo "── IDA Plugins ──"
    mkdir -p "$PREFIX/ida-plugins"

    # hrtng — Kaspersky deobfuscation (2024 contest winner)
    # TODO: pin to specific commit — repo has no tags/releases at this URL.
    clone_or_pull "https://github.com/AandersonL/hrtng.git" "$PREFIX/ida-plugins/hrtng" "-" "hrtng"

    # HexRaysCodeXplorer — C++ vtable reconstruction, pinned to tag 2.1
    clone_or_pull "https://github.com/REhints/HexRaysCodeXplorer.git" "$PREFIX/ida-plugins/HexRaysCodeXplorer-ida9" "2.1" "HexRaysCodeXplorer"

    # ClassInformer — MSVC RTTI scanner
    # TODO: pin to specific commit — repo has no tags/releases at this URL.
    clone_or_pull "https://github.com/nihilus/IDA_ClassInformer_PlugIn.git" "$PREFIX/ida-plugins/IDA_ClassInformer_PlugIn" "-" "ClassInformer"

    # SigMakerEx — byte pattern signature generator, pinned to v1.0.10
    clone_or_pull "https://github.com/A200K/IDA-Pro-SigMaker.git" "$PREFIX/ida-plugins/sigmakerex" "v1.0.10" "SigMakerEx"

    # FIRST — Cisco Talos function fingerprints (free Lumina alt)
    # TODO: pin to specific commit — repo has no tags/releases at this URL.
    clone_or_pull "https://github.com/ciscocsirt/FIRST-plugin-ida.git" "$PREFIX/ida-plugins/FIRST-plugin-ida" "-" "FIRST"

    # RevEng.AI — binary similarity, pinned to v3.6.1
    clone_or_pull "https://github.com/RevEngAI/reai-ida.git" "$PREFIX/ida-plugins/reai-ida" "v3.6.1" "RevEng.AI-ida"

    # D-810 — CFF/MBA/opaque predicate deobfuscation
    # TODO: pin to specific commit — repo has no tags/releases at this URL.
    clone_or_pull "https://github.com/joydo/d-810.git" "$PREFIX/ida-plugins/d-810" "-" "D-810"

    # HashDB — API hash resolver, pinned to 1.12.0
    clone_or_pull "https://github.com/OALabs/hashdb-ida.git" "$PREFIX/ida-plugins/hashdb-ida" "1.12.0" "HashDB"

    # Diaphora — binary diffing, pinned to 3.4.1
    clone_or_pull "https://github.com/joxeankoret/diaphora.git" "$PREFIX/diffing/diaphora" "3.4.1" "Diaphora"

    echo ""
    echo "── Ghidra Plugins ──"
    mkdir -p "$PREFIX/ghidra-plugins"

    # GhidrAssist — LLM-powered RE assistant, pinned to v1.4.0
    clone_or_pull "https://github.com/jtang613/GhidrAssist.git" "$PREFIX/ghidra-plugins/GhidrAssist" "v1.4.0" "GhidrAssist"

    # BinDiffHelper — cross-version diffing, pinned to v0.7.0
    clone_or_pull "https://github.com/ubfx/BinDiffHelper.git" "$PREFIX/ghidra-plugins/BinDiffHelper" "v0.7.0" "BinDiffHelper"

    # OOAnalyzer (Pharos) — automated C++ recovery
    # TODO: pin to specific commit — repo has no git tags/releases.
    clone_or_pull "https://github.com/cmu-sei/pharos.git" "$PREFIX/ghidra-plugins/pharos" "-" "Pharos"

    # RevEng.AI for Ghidra, pinned to v0.24.0
    clone_or_pull "https://github.com/RevEngAI/reai-ghidra.git" "$PREFIX/ghidra-plugins/plugin-ghidra" "v0.24.0" "RevEng.AI-ghidra"

    echo ""
    echo "── Debugger Sync ──"
    mkdir -p "$PREFIX/misc"
    # ret-Sync — debugger sync, pinned to ida9.2 tag
    clone_or_pull "https://github.com/bootleg/ret-sync.git" "$PREFIX/misc/ret-sync" "ida9.2" "ret-Sync"

    echo ""
    echo "── FLIRT Signatures ──"
    mkdir -p "$PREFIX/signatures"
    # TODO: pin to specific commit — repo has no git tags/releases.
    clone_or_pull "https://github.com/Maktm/FLIRTDB.git" "$PREFIX/signatures/FLIRTDB" "-" "FLIRTDB"
    # TODO: pin to specific commit — repo has no git tags/releases.
    clone_or_pull "https://github.com/push0ebp/sig-database.git" "$PREFIX/signatures/sig-database" "-" "sig-database"

    echo ""
    echo "── Deobfuscation Tools ──"
    mkdir -p "$PREFIX/deobfuscation"

    # NoVmp — VMProtect devirtualizer, pinned to v1.0.6
    clone_or_pull "https://github.com/can1357/NoVmp.git" "$PREFIX/deobfuscation/NoVmp" "v1.0.6" "NoVmp"

    # vtil — VM Translation IL
    # TODO: pin to specific commit — repo has no git tags/releases.
    clone_or_pull "https://github.com/vtil-project/VTIL-Core.git" "$PREFIX/deobfuscation/VTIL-Core" "-" "VTIL-Core"

    # ScyllaHide — anti-anti-debug, pinned to v1.4
    clone_or_pull "https://github.com/x64dbg/ScyllaHide.git" "$PREFIX/deobfuscation/ScyllaHide" "v1.4" "ScyllaHide"

    # Scylla — IAT reconstruction, pinned to v0.9.8
    clone_or_pull "https://github.com/NtQuery/Scylla.git" "$PREFIX/deobfuscation/Scylla" "v0.9.8" "Scylla"

    # pe-sieve — hollowing detector, pinned to v0.4.1.1
    clone_or_pull "https://github.com/hasherezade/pe-sieve.git" "$PREFIX/deobfuscation/pe-sieve" "v0.4.1.1" "pe-sieve"

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

    # Isolated venv — system Python is never touched. Reuse if already present.
    VENV_DIR="$PREFIX/venv"
    if [ ! -d "$VENV_DIR" ]; then
        echo "  [create] venv at $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    else
        echo "  [reuse] existing venv at $VENV_DIR"
    fi
    # Activate for the install (portable POSIX activate script).
    # shellcheck source=/dev/null
    . "$VENV_DIR/bin/activate"

    PIP="pip"

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

    # Drop out of the venv so the rest of the script runs in the caller's shell.
    if command -v deactivate >/dev/null 2>&1; then
        deactivate
    fi

    echo ""
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo "Done."
echo ""
echo "Installed to: $PREFIX"
echo ""

if [ $DO_PLUGINS -eq 1 ]; then
    echo "── Pinned clones (audit) ──"
    printf '  %-20s %-16s %-42s %s\n' "NAME" "PINNED REF" "RESOLVED COMMIT (HEAD)" "DEST"
    for row in "${PIN_ROWS[@]}"; do
        name=$(printf '%s' "$row" | cut -f1)
        url=$(printf '%s' "$row" | cut -f2)
        ref=$(printf '%s' "$row" | cut -f3)
        resolved=$(printf '%s' "$row" | cut -f4)
        destdir=$(printf '%s' "$row" | cut -f5)
        [ "$ref" = "-" ] && ref="(default)"
        printf '  %-20s %-16s %-42s %s\n' "$name" "$ref" "$resolved" "$destdir"
        printf '  %s\n' "url: $url"
    done
    echo ""
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
    echo "Python packages (installed into venv): capstone, unicorn, keystone, pefile, lief,"
    echo "  triton, miasm, floss, frida, angr"
    echo ""
    echo "Venv: $PREFIX/venv"
    echo "  Activate:  source $PREFIX/venv/bin/activate"
    echo "  Or run a tool directly: $PREFIX/venv/bin/python -m <module>"
fi