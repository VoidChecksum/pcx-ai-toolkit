#!/usr/bin/env python3
"""Regenerate drift-checkable mirrored docs from docs/PROVENANCE.json.

This is the write-capable counterpart to check-doc-drift.py.  It fetches the
canonical upstream Markdown URL recorded in docs/PROVENANCE.json, compares the
normalized local/upstream bodies, and optionally writes the upstream Markdown
back into the mirror.

AngelScript core manual pages are provenance-only because they are converted
from Doxygen HTML; this tool intentionally skips non drift-checkable pages.
"""
from __future__ import annotations

import argparse
import json
import sys
import re
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = REPO_ROOT / "docs" / "PROVENANCE.json"
UA = "pcx-ai-toolkit-doc-regenerator/1.0 (https://github.com/VoidChecksum/pcx-ai-toolkit)"
TIMEOUT = 30
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
LINK_RE = re.compile(r"\[(.*?)\]\([^)]*\)")
FOOTER_RE = re.compile(r"\n#\s*Agent Instructions\b.*", re.DOTALL)


def normalize(text: str) -> str:
    text = COMMENT_RE.sub("", text)
    text = FOOTER_RE.sub("", text)
    text = LINK_RE.sub(lambda m: m.group(1), text)
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/markdown, text/plain, */*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
        return res.read().decode("utf-8", errors="replace")


def load_targets(only: str = "", limit: int = 0) -> list[tuple[Path, dict[str, Any]]]:
    data = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = []
    for rel, meta in data.get("files", {}).items():
        if not meta.get("drift_check") or not meta.get("url"):
            continue
        if only and only not in rel and only not in str(meta.get("url", "")):
            continue
        rows.append((REPO_ROOT / rel, meta))
    rows.sort(key=lambda item: item[0].as_posix())
    return rows[:limit] if limit else rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", default="", help="only files/URLs containing this substring")
    ap.add_argument("--limit", type=int, default=0, help="stop after N files")
    ap.add_argument("--write", action="store_true", help="write changed upstream Markdown into docs/")
    ap.add_argument("--check", action="store_true", help="exit 1 if any target would change")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    if not PROVENANCE.exists():
        print("ERROR: docs/PROVENANCE.json missing; run tools/build-provenance.py", file=sys.stderr)
        return 2

    results: list[dict[str, Any]] = []
    changed = 0
    errors = 0
    for local, meta in load_targets(args.only, args.limit):
        rel = local.relative_to(REPO_ROOT).as_posix()
        url = str(meta["url"])
        try:
            upstream = fetch(url)
            local_text = local.read_text(encoding="utf-8", errors="ignore")
            is_changed = normalize(upstream) != normalize(local_text)
            if is_changed:
                changed += 1
                if args.write:
                    local.write_text(upstream.rstrip() + "\n", encoding="utf-8")
            results.append({"file": rel, "url": url, "status": "CHANGED" if is_changed else "IN_SYNC"})
            if not args.json:
                action = "WROTE" if is_changed and args.write else ("CHANGED" if is_changed else "IN_SYNC")
                print(f"{action:8} {rel} <- {url}")
        except Exception as exc:  # noqa: BLE001
            errors += 1
            results.append({"file": rel, "url": url, "status": "FETCH_ERROR", "error": f"{type(exc).__name__}: {exc}"})
            if not args.json:
                print(f"ERROR    {rel} <- {url}: {type(exc).__name__}: {exc}")

    summary = {"checked": len(results), "changed": changed, "fetch_errors": errors, "written": changed if args.write else 0, "results": results}
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Summary: {summary['checked']} checked, {changed} changed, {errors} fetch errors, {summary['written']} written.")
    if args.check and (changed or errors):
        return 1
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
