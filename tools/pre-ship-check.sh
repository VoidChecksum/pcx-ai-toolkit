#!/usr/bin/env bash
#
# pre-ship-check.sh — pre-release hygiene checklist for PCX scripting projects.
#
# Implements the checklist from .claude/skills/script-bundler/SKILL.md section 4.
# Pure bash + grep + find. No Python, no new dependencies.
#
# Usage:
#   bash tools/pre-ship-check.sh [project-dir]
#   bash tools/pre-ship-check.sh --strict [project-dir]
#   bash tools/pre-ship-check.sh --quiet [project-dir]
#   bash tools/pre-ship-check.sh --json  [project-dir]
#
# Flags:
#   --strict   exit 1 on any WARN (default: exit 1 only on FAIL)
#   --quiet    print only WARN and FAIL lines (default: also print PASS)
#   --json     emit machine-readable JSON instead of human text
#   -h|--help  show this help
#
# Exit codes:
#   0  all checks PASS (or only WARN without --strict)
#   1  one or more FAIL, or any WARN with --strict
#   2  bad usage
#
# Portable across bash 4+ on Linux, macOS, WSL, Git Bash. Uses POSIX grep -E,
# avoids GNU --include / GNU find -printf. Safe to wire into CI.

set -euo pipefail

VERSION="1.0.0"

# ── arg parse ────────────────────────────────────────────────────────────────

STRICT=0
QUIET=0
JSON=0
PROJECT_DIR="."

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            sed -n '2,28p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        --strict) STRICT=1; shift ;;
        --quiet)  QUIET=1;  shift ;;
        --json)   JSON=1;   shift ;;
        --version) echo "pre-ship-check.sh ${VERSION}"; exit 0 ;;
        -*) echo "unknown flag: $1" >&2; exit 2 ;;
        *)  PROJECT_DIR="$1"; shift ;;
    esac
done

if [ ! -d "$PROJECT_DIR" ]; then
    echo "error: not a directory: $PROJECT_DIR" >&2
    exit 2
fi

cd "$PROJECT_DIR"

# ── result accumulator ──────────────────────────────────────────────────────

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
RESULTS=()   # each entry: STATUS|NUMBER|TITLE|DETAIL_LINES (\\n-separated)

emit() {
    # emit STATUS NUMBER TITLE DETAIL
    local status="$1" number="$2" title="$3" detail="$4"
    case "$status" in
        PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
        WARN) WARN_COUNT=$((WARN_COUNT + 1)) ;;
        FAIL) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    esac
    RESULTS+=("${status}|${number}|${title}|${detail}")
}

# ── file-set helpers ────────────────────────────────────────────────────────

src_files() {
    # all source files we care about, NUL-separated so paths-with-spaces survive
    find . -type f \( -name '*.em' -o -name '*.as' -o -name '*.lua' \) \
        -not -path './.git/*' -not -path '*/node_modules/*' \
        -not -path '*/build/*' -not -path '*/dist/*'  2>/dev/null
}

src_files_md() {
    # Source + config + docs. Used for the LICENSE/README/CHANGELOG existence
    # checks; path-leak scan (check 1) restricts further to source files only.
    find . -type f \( -name '*.em' -o -name '*.as' -o -name '*.lua' \
                   -o -name '*.json' -o -name '*.md' \) \
        -not -path './.git/*' -not -path '*/node_modules/*' \
        -not -path '*/build/*' -not -path '*/dist/*' 2>/dev/null
}

# grep that handles "no matches" cleanly (no error exit) and prints with -n
ngrep() {
    grep -EnH "$@" 2>/dev/null || true
}

# count occurrences (line count of grep output)
ncount() {
    local out; out=$(grep -Ec "$@" 2>/dev/null || true)
    echo "${out:-0}"
}

# ── checks ──────────────────────────────────────────────────────────────────

check_1_paths() {
    local hits
    # Restrict to source files; markdown docs may legitimately contain Windows
    # path examples in API documentation that are not user-path leaks.
    hits=$(src_files | xargs grep -EnH 'C:\\Users\\|/home/[a-zA-Z_]|/Users/[a-zA-Z_]' 2>/dev/null || true)
    if [ -z "$hits" ]; then
        emit PASS 1 "No hardcoded user paths" ""
    else
        emit FAIL 1 "Hardcoded user/system paths" "$hits"
    fi
}

check_2_debug_println() {
    local hits
    hits=$(src_files | xargs grep -EnH 'println\(.*0x[0-9A-Fa-f]{4,}' 2>/dev/null || true)
    if [ -z "$hits" ]; then
        emit PASS 2 "No debug println of raw addresses" ""
    else
        emit WARN 2 "Debug println with raw addresses" "$hits"
    fi
}

check_3_todos() {
    local hits
    hits=$(src_files | xargs grep -EnH '(TODO|FIXME|HACK|XXX)' 2>/dev/null | \
           grep -vE '// (shipped|known):' || true)
    if [ -z "$hits" ]; then
        emit PASS 3 "No TODO/FIXME/HACK/XXX markers" ""
    else
        emit WARN 3 "Unresolved TODO/FIXME/HACK/XXX" "$hits"
    fi
}

check_4_fs_writes() {
    local hits
    hits=$(src_files | xargs grep -EnH 'fs_write_file\(' 2>/dev/null || true)
    if [ -z "$hits" ]; then
        emit PASS 4 "No filesystem writes" ""
    else
        emit WARN 4 "Filesystem writes (manual review)" "$hits"
    fi
}

check_5_network() {
    local hits
    hits=$(src_files | xargs grep -EnH 'http_(get|post)|websocket|tcp_(connect|listen)' 2>/dev/null || true)
    if [ -z "$hits" ]; then
        emit PASS 5 "No network calls" ""
    else
        emit WARN 5 "Network calls (manual review)" "$hits"
    fi
}

check_6_emb_strings() {
    local emb_files; emb_files=$(find . -name '*.emb' -not -path './.git/*' 2>/dev/null)
    if [ -z "$emb_files" ]; then
        emit PASS 6 ".emb scan skipped (no .emb files in project)" ""
        return
    fi
    if ! command -v strings >/dev/null 2>&1; then
        emit PASS 6 ".emb scan skipped (strings(1) not on PATH)" ""
        return
    fi
    local hits=""
    while IFS= read -r emb; do
        local matches
        matches=$(strings "$emb" 2>/dev/null | grep -EnH '(secret_|internal_|debug_)' || true)
        if [ -n "$matches" ]; then
            hits="${hits}${emb}:\n${matches}\n"
        fi
    done <<<"$emb_files"
    if [ -z "$hits" ]; then
        emit PASS 6 "No suspicious .emb string artifacts" ""
    else
        emit WARN 6 "Suspicious .emb string artifacts" "$hits"
    fi
}

check_7_offset_citations() {
    local em_files; em_files=$(find . -name '*.em' -not -path './.git/*' 2>/dev/null)
    [ -z "$em_files" ] && { emit PASS 7 "No .em files to check" ""; return; }
    local total cited uncited
    # Count offset/sig declarations across all .em
    total=$( (echo "$em_files" | xargs grep -Ec 'const[[:space:]]+(uint64[[:space:]]+OFF(SET)?_|string[[:space:]]+SIG_)' 2>/dev/null || true) | \
             awk -F: '{s+=$2} END{print s+0}')
    # Lines with `// E-NNN` annotation
    cited=$( (echo "$em_files" | xargs grep -Ec '// E-[0-9]+' 2>/dev/null || true) | \
             awk -F: '{s+=$2} END{print s+0}')
    if [ "$total" -eq 0 ]; then
        emit PASS 7 "No offsets/sigs declared" ""
        return
    fi
    uncited=$((total - cited))
    if [ "$uncited" -le 0 ]; then
        emit PASS 7 "All ${total} offsets cite evidence (E-NNN)" ""
    elif [ "$cited" -eq 0 ]; then
        emit FAIL 7 "No offsets cite evidence (0/${total} cited)" \
             "Run: python3 tools/evidence-log-validator.py <offsets.em> --evidence-dir evidence/"
    else
        emit WARN 7 "${uncited}/${total} offsets lack evidence citation" \
             "Run: python3 tools/evidence-log-validator.py <offsets.em> --evidence-dir evidence/"
    fi
}

check_8_placeholder_module() {
    local hits
    hits=$(find . -name '*.em' -not -path './.git/*' -print0 2>/dev/null | \
           xargs -0 grep -EnH 'ref_process\("(<TARGET|target\.exe|game\.exe|YOUR_GAME)' 2>/dev/null || true)
    if [ -z "$hits" ]; then
        emit PASS 8 "ref_process module name is not a placeholder" ""
    else
        emit WARN 8 "Placeholder module name in ref_process()" "$hits"
    fi
}

check_9_commented_blocks() {
    # Detect runs of 5+ consecutive `//` lines (likely dead/experimental code)
    local hits=""
    while IFS= read -r f; do
        # awk: emit "file:start-end" for runs of >= 5 lines that start with //
        local m
        m=$(awk -v file="$f" '
            BEGIN { run = 0; start = 0 }
            /^[[:space:]]*\/\// { if (run == 0) start = NR; run++; next }
            { if (run >= 5) print file ":" start "-" (NR-1); run = 0 }
            END { if (run >= 5) print file ":" start "-" NR }
        ' "$f" 2>/dev/null)
        [ -n "$m" ] && hits="${hits}${m}"$'\n'
    done < <(src_files)
    if [ -z "$hits" ]; then
        emit PASS 9 "No long commented-out blocks (5+ lines)" ""
    else
        emit WARN 9 "Long commented-out blocks (likely dead code)" "$hits"
    fi
}

check_10_license() {
    if [ -f LICENSE ] || [ -f LICENSE.md ] || [ -f LICENSE.txt ]; then
        emit PASS 10 "LICENSE present" ""
    else
        emit FAIL 10 "LICENSE missing" "Recipients need a license to redistribute. MIT is a common default."
    fi
}

check_11_readme() {
    if [ -f README.md ] || [ -f README.txt ] || [ -f README ]; then
        emit PASS 11 "README present" ""
    else
        emit FAIL 11 "README missing" "Recipients read this before your code."
    fi
}

check_12_changelog() {
    if [ ! -f CHANGELOG.md ] && [ ! -f CHANGELOG ] && [ ! -f CHANGES.md ]; then
        emit FAIL 12 "CHANGELOG missing" "Users need to know what changed each release."
        return
    fi
    # Look for a `## [` version header in the first 30 lines of whichever exists
    local cl
    for cl in CHANGELOG.md CHANGELOG CHANGES.md; do
        [ -f "$cl" ] || continue
        if head -n 30 "$cl" | grep -Eq '^## (\[|v?[0-9])' 2>/dev/null; then
            emit PASS 12 "CHANGELOG has version entry near top" ""
            return
        fi
    done
    emit WARN 12 "CHANGELOG present but no version header in first 30 lines" \
         "Add a '## [X.Y.Z] — YYYY-MM-DD' entry for this release."
}

# ── run all checks ──────────────────────────────────────────────────────────

check_1_paths
check_2_debug_println
check_3_todos
check_4_fs_writes
check_5_network
check_6_emb_strings
check_7_offset_citations
check_8_placeholder_module
check_9_commented_blocks
check_10_license
check_11_readme
check_12_changelog

# ── output ──────────────────────────────────────────────────────────────────

print_human() {
    echo "PRE-SHIP CHECK — ${PROJECT_DIR}"
    local entry status num title detail
    for entry in "${RESULTS[@]}"; do
        status="${entry%%|*}"
        local rest="${entry#*|}"
        num="${rest%%|*}"
        rest="${rest#*|}"
        title="${rest%%|*}"
        detail="${rest#*|}"
        if [ "$QUIET" -eq 1 ] && [ "$status" = "PASS" ]; then
            continue
        fi
        printf "[%s] %2d. %s\n" "$status" "$num" "$title"
        if [ -n "$detail" ] && [ "$status" != "PASS" ]; then
            # indent each detail line by 2 spaces
            printf '%s\n' "$detail" | sed 's/^/  /'
        fi
    done
    echo
    echo "Summary: ${PASS_COUNT} PASS, ${WARN_COUNT} WARN, ${FAIL_COUNT} FAIL"
}

print_json() {
    # Build JSON manually to avoid jq/python deps
    printf '{\n'
    printf '  "project_dir": "%s",\n' "$(printf '%s' "$PROJECT_DIR" | sed 's/"/\\"/g')"
    printf '  "summary": { "pass": %d, "warn": %d, "fail": %d },\n' \
           "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"
    printf '  "checks": [\n'
    local i=0 entry status num title detail
    local n=${#RESULTS[@]}
    for entry in "${RESULTS[@]}"; do
        status="${entry%%|*}"
        local rest="${entry#*|}"
        num="${rest%%|*}"
        rest="${rest#*|}"
        title="${rest%%|*}"
        detail="${rest#*|}"
        # escape backslashes, quotes, newlines for JSON
        local d_esc
        d_esc=$(printf '%s' "$detail" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e ':a;N;$!ba;s/\n/\\n/g')
        local t_esc
        t_esc=$(printf '%s' "$title"  | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
        i=$((i + 1))
        printf '    { "number": %d, "status": "%s", "title": "%s", "detail": "%s" }' \
               "$num" "$status" "$t_esc" "$d_esc"
        [ "$i" -lt "$n" ] && printf ','
        printf '\n'
    done
    printf '  ]\n'
    printf '}\n'
}

if [ "$JSON" -eq 1 ]; then
    print_json
else
    print_human
fi

# ── exit code ───────────────────────────────────────────────────────────────

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi
if [ "$STRICT" -eq 1 ] && [ "$WARN_COUNT" -gt 0 ]; then
    exit 1
fi
exit 0
