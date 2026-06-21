#!/usr/bin/env python3
"""Advisory check: are all API-relevant Perception releases reflected in the
version matrix?

knowledge/pcx-version-matrix.md is "drawn from docs/perception/changelogs.md"
(its own header says so). When Perception ships a release that adds/changes a
scripting-API surface, the matrix should reference that release's date. This
script flags changelog release dates that (a) mention a scripting API surface
and (b) are not referenced anywhere in the matrix — the "a new release landed
and the matrix wasn't updated" gap.

This is ADVISORY: it exits 0 with WARN lines by default (the mapping is
heuristic — some API-keyword matches are non-additive changes). Pass --strict
to exit 1 on any unreferenced API-relevant date, for a hard gate.

Usage:
    python tools/check-version-matrix.py          # advisory, exit 0 + warnings
    python tools/check-version-matrix.py --strict # exit 1 on any gap
    python tools/check-version-matrix.py --json

Stdlib only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOGS = REPO_ROOT / "docs" / "perception" / "changelogs.md"
MATRIX = REPO_ROOT / "knowledge" / "pcx-version-matrix.md"

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}

# Scripting-API surface keywords that make a changelog release "API-relevant".
API_KEYWORDS = re.compile(
    r"\b(render|proc|gui|input|cpu|zydis|unicorn|net|win|filesystem|sound|mcp|"
    r"custom[- ]?draw|atomic|simd|json|regex|hash_set|sorted_map|hashmap|"
    r"vec|math3d|variant|bits|scan|signature|memory|disassembl|hot[- ]?reload|"
    r"world_to_screen|matrix|thread|module|pattern)\b",
    re.IGNORECASE,
)

DATE_HEADER_RE = re.compile(r"^##\s+([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})\s*[—\-]")


def changelog_releases() -> list[tuple[str, str, bool]]:
    """Return [(iso_date, header, api_relevant)] for each dated release."""
    out = []
    txt = CHANGELOGS.read_text(encoding="utf-8", errors="ignore")
    # Split into release blocks at each `## <Month> ...` header.
    blocks = re.split(r"\n(?=##\s+[A-Z][a-z]+\s+\d{1,2},\s+\d{4})", txt)
    for blk in blocks:
        m = DATE_HEADER_RE.match(blk.lstrip())
        if not m:
            continue
        month, day, year = m.group(1), int(m.group(2)), int(m.group(3))
        iso = f"{year:04d}-{MONTHS[month]:02d}-{day:02d}"
        header = blk.lstrip().splitlines()[0]
        api = bool(API_KEYWORDS.search(blk))
        out.append((iso, header, api))
    return out


def matrix_dates() -> set[str]:
    """All ISO dates referenced in the matrix, plus month-name forms."""
    txt = MATRIX.read_text(encoding="utf-8", errors="ignore") if MATRIX.exists() else ""
    refs = set(re.findall(r"\d{4}-\d{2}-\d{2}", txt))
    # Also collect `Month DD, YYYY` forms and normalize to ISO for matching.
    for m in re.finditer(r"([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})", txt):
        if m.group(1) in MONTHS:
            refs.add(f"{int(m.group(3)):04d}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}")
    return refs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="exit 1 on any unreferenced API-relevant date")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    if not CHANGELOGS.exists() or not MATRIX.exists():
        print("ERROR: missing changelogs.md or pcx-version-matrix.md", file=sys.stderr)
        return 2

    releases = changelog_releases()
    mrefs = matrix_dates()
    gaps = [(iso, header) for iso, header, api in releases if api and iso not in mrefs]
    total = len(releases)
    api_total = sum(1 for _, _, a in releases if a)

    report = {
        "changelog_releases": total,
        "api_relevant_releases": api_total,
        "matrix_referenced_dates": len(mrefs),
        "unreferenced_api_releases": [{"date": iso, "header": h} for iso, h in gaps],
    }

    if args.json:
        print(json.dumps(report, indent=2))

    print(f"Changelog releases: {total} ({api_total} API-relevant). "
          f"Matrix references {len(mrefs)} dates.")
    if not gaps:
        print("OK — every API-relevant changelog release is referenced in the version matrix.")
        return 0
    print(f"WARN — {len(gaps)} API-relevant release(s) not referenced in pcx-version-matrix.md:")
    for iso, h in gaps:
        print(f"  {iso}  {h}")
    print("Review and add a matrix row for each, or confirm the release added no scripting API.")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())