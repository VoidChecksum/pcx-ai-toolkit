#!/usr/bin/env python3
"""Build docs/PROVENANCE.json — the file → upstream-source-URL mapping.

The supported docs/ surface is a scrape of three upstream sources:

  * enma-1.gitbook.io/enma/**           (the Enma language)
  * docs.perception.cx/perception/**    (the Perception.cx host APIs)
  * www.angelcode.com/angelscript/**     (the core AngelScript language manual)

GitBook pages carry their own canonical URL in a header blockquote:
    > ... this page is available as [Markdown](<upstream-url>).
The AngelScript scrape carries its upstream source in an HTML comment header:
    <!-- Source: <upstream-url> ... -->

This script extracts those URLs and writes docs/PROVENANCE.json, consumed by
tools/check-doc-drift.py (weekly CI drift detection against the live upstream).
Only GitBook-sourced files are drift-checkable 1:1 (the local files are markdown
mirrors, modulo internal-link flattening). The AngelScript core-manual files
are hand-converted from Doxygen HTML and are NOT byte-comparable to upstream;
they are recorded for provenance but excluded from automated drift checking
(marked "drift_check": false).

Usage:
    python tools/build-provenance.py             # write docs/PROVENANCE.json
    python tools/build-provenance.py --check     # exit 1 if committed file drifts

Stdlib only.
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
OUT = DOCS / "PROVENANCE.json"

GITBOOK_RE = re.compile(r"available as \[Markdown\]\((https?://[^)]+)\)")
COMMENT_RE = re.compile(r"<!--\s*Source:\s*(https?://\S+)")
# Files / dirs that are generated or local-only — never a drift source.
EXCLUDE_NAMES = {"INDEX.md"}
EXCLUDE_PREFIX = ("llms-",)  # generated bundles under docs/

# Upstream URLs that are known 404 / removed; keep them in provenance but
# don't fail CI drift checks on them.
SKIP_DRIFT_URLS = {
    "https://docs.perception.cx/perception/angel-script/cs2-extended-api.md",
    "https://docs.perception.cx/perception/angel-script/custom-draw-api.md",
    "https://docs.perception.cx/perception/enma/custom-draw-api.md",
    "https://docs.perception.cx/perception/lua-script/cs2-extended-api.md",
}
def is_source_doc(p: Path) -> bool:
    if p.name in EXCLUDE_NAMES:
        return False
    if any(p.name.startswith(pre) for pre in EXCLUDE_PREFIX):
        return False
    rel = p.relative_to(REPO_ROOT).as_posix()
    if rel.startswith(("docs/perception/lua/", "docs/lua-lang/")):
        return False
    return True


def classify(url: str) -> str:
    host = url.lower()
    if "gitbook.io" in host or "docs.perception.cx" in host:
        return "gitbook"
    if "angelcode.com" in host:
        return "angelcode"
    if "lua.org" in host:
        return "lua"
    return "other"


def extract(p: Path) -> tuple[str | None, str]:
    """Return (upstream_url, source) for a doc file, or (None, 'local')."""
    txt = p.read_text(encoding="utf-8", errors="ignore")[:6000]
    m = GITBOOK_RE.search(txt)
    if m:
        return m.group(1).strip(), classify(m.group(1))
    m = COMMENT_RE.search(txt)
    if m:
        return m.group(1).strip(), classify(m.group(1))
    return None, "local"


def build() -> dict:
    files: dict[str, dict] = {}
    unmapped: list[str] = []
    for p in sorted(DOCS.rglob("*.md")):
        if not is_source_doc(p):
            continue
        rel = p.relative_to(REPO_ROOT).as_posix()
        url, source = extract(p)
        if url is None:
            unmapped.append(rel)
            files[rel] = {"source": "local", "url": None, "drift_check": False}
        else:
            # Only GitBook mirrors are byte-comparable (modulo link flattening).
            # Some upstream pages are known 404; keep provenance but skip drift.
            drift = source == "gitbook" and url not in SKIP_DRIFT_URLS
            files[rel] = {"source": source, "url": url, "drift_check": drift}
    return {
        "generated": datetime.date.today().isoformat(),
        "count": len(files),
        "drift_checkable": sum(1 for v in files.values() if v["drift_check"]),
        "unmapped": unmapped,
        "files": files,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the committed PROVENANCE.json differs from what the source would produce")
    args = ap.parse_args()

    data = build()
    if args.check:
        if not OUT.exists():
            print("PROVENANCE.json missing — run: python tools/build-provenance.py")
            return 1
        existing = json.loads(OUT.read_text(encoding="utf-8"))
        # Compare ignoring the generated date (changes daily).
        existing_cmp = {k: v for k, v in existing.items() if k != "generated"}
        new_cmp = {k: v for k, v in data.items() if k != "generated"}
        if existing_cmp != new_cmp:
            print("PROVENANCE.json is out of sync with the source tree. Regenerate:")
            print("  python tools/build-provenance.py")
            return 1
        print(f"PROVENANCE.json in sync ({data['count']} files, {data['drift_checkable']} drift-checkable).")
        return 0

    OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO_ROOT)} — {data['count']} files, "
          f"{data['drift_checkable']} drift-checkable, {len(data['unmapped'])} local-only.")
    if data["unmapped"]:
        print("Local-only (no upstream URL):")
        for u in data["unmapped"]:
            print(f"  {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
