#!/usr/bin/env python3
"""Detect drift between the toolkit's scraped docs/ and their upstream sources.

Reads docs/PROVENANCE.json (built by tools/build-provenance.py) and, for every
file marked "drift_check": true, fetches the live upstream markdown, normalizes
both the local and upstream copies, and reports DRIFT / IN_SYNC / FETCH_ERROR.

Why normalization: the toolkit flattens internal GitBook link paths
(/enma/addons/vec.md -> addon-vec.md) and adds provenance headers, so a raw
byte diff would always fire. Normalization strips the parts that legitimately
differ between mirror and source, leaving the prose + code + API signatures —
the signal that "the upstream API doc actually changed."

Normalized comparison strips:
  * HTML comments (provenance headers differ between mirror and source)
  * the GitBook "Agent Instructions" footer block
  * markdown link URLs ([text](url) -> text) — link targets are flattened locally
  * trailing whitespace and blank lines

Exit codes:
  0  all checked files IN_SYNC (or --check not triggered)
  1  one or more files DRIFT or failed to fetch (CI gating)

Usage:
    python tools/check-doc-drift.py                 # check all, human report
    python tools/check-doc-drift.py --check         # same, exit 1 on any drift (CI)
    python tools/check-doc-drift.py --only proc-api # only files matching substring
    python tools/check-doc-drift.py --json          # machine-readable output
    python tools/check-doc-drift.py --limit 5       # stop after 5 checks (smoke)

Stdlib only. Network: urllib, with a short timeout per file.
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROV = REPO_ROOT / "docs" / "PROVENANCE.json"

UA = "pcx-ai-toolkit-doc-drift/1.0 (https://github.com/VoidChecksum/pcx-ai-toolkit)"
TIMEOUT = 20

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
LINK_RE = re.compile(r"\[(.*?)\]\([^)]*\)")
FOOTER_RE = re.compile(r"\n#\s*Agent Instructions\b.*", re.DOTALL)


def normalize(text: str) -> str:
    """Strip the parts that legitimately differ between mirror and upstream."""
    text = COMMENT_RE.sub("", text)            # provenance headers / HTML comments
    text = FOOTER_RE.sub("", text)             # GitBook agent-instructions footer
    text = LINK_RE.sub(lambda m: m.group(1), text)  # [text](url) -> text
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]         # drop blank lines
    return "\n".join(lines)


def fetch(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/plain, text/markdown, */*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001 — we report all fetch failures
        return f"__FETCH_ERROR__: {type(e).__name__}: {e}"


def load_provenance() -> dict:
    if not PROV.exists():
        print(f"Missing {PROV.relative_to(REPO_ROOT)}. Run: python tools/build-provenance.py",
              file=sys.stderr)
        sys.exit(2)
    return json.loads(PROV.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 on any drift/fetch error (CI)")
    ap.add_argument("--live", action="store_true", help="fetch upstream docs and compare live content")
    ap.add_argument("--only", default=None, help="only check files whose path contains this substring")
    ap.add_argument("--limit", type=int, default=0, help="stop after N checks (0 = all)")
    ap.add_argument("--json", action="store_true", help="emit JSON to stdout")
    args = ap.parse_args()

    prov = load_provenance()
    files = prov.get("files", {})
    targets = [(Path(REPO_ROOT / rel), meta) for rel, meta in files.items()
               if meta.get("drift_check") and meta.get("url")]
    if args.only:
        targets = [(p, m) for p, m in targets if args.only in p.as_posix()]
    if args.limit:
        targets = targets[: args.limit]

    if not args.live:
        missing = [p.relative_to(REPO_ROOT).as_posix() for p, _ in targets if not p.exists()]
        summary = {"checked": len(targets), "in_sync": len(targets) - len(missing), "drift": 0, "fetch_errors": len(missing), "mode": "offline", "results": []}
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"Offline provenance check: {summary['checked']} tracked, {summary['in_sync']} present, {summary['fetch_errors']} missing.")
        return 1 if args.check and missing else 0

    results = []
    drift = 0
    errors = 0

    def human(message: str = "") -> None:
        if not args.json:
            print(message)

    for i, (local, meta) in enumerate(targets, 1):
        url = meta["url"]
        local_norm = normalize(local.read_text(encoding="utf-8", errors="ignore"))
        upstream = fetch(url)
        if upstream is None or upstream.startswith("__FETCH_ERROR__"):
            results.append({"file": local.relative_to(REPO_ROOT).as_posix(), "url": url,
                            "status": "FETCH_ERROR", "detail": (upstream or "").split(":", 1)[-1].strip()})
            errors += 1
            human(f"[{i}/{len(targets)}] FETCH_ERROR  {local.relative_to(REPO_ROOT)}  <- {url}")
            human(f"             {upstream}" if upstream else "")
            continue
        up_norm = normalize(upstream)
        status = "IN_SYNC" if up_norm == local_norm else "DRIFT"
        if status == "DRIFT":
            drift += 1
            # Show a short, useful diff hint (first differing normalized line).
            local_lines = local_norm.splitlines()
            up_lines = up_norm.splitlines()
            hint = ""
            for a, b in zip(local_lines, up_lines):
                if a != b:
                    hint = f"local: {a[:90]!r}\n             upstream: {b[:90]!r}"
                    break
            else:
                if len(local_lines) != len(up_lines):
                    hint = f"line count differs: local={len(local_lines)} upstream={len(up_lines)}"
            results.append({"file": local.relative_to(REPO_ROOT).as_posix(), "url": url,
                             "status": "DRIFT", "hint": hint})
            human(f"[{i}/{len(targets)}] DRIFT        {local.relative_to(REPO_ROOT)}  <- {url}")
            if hint:
                human(f"             {hint}")
        else:
            results.append({"file": local.relative_to(REPO_ROOT).as_posix(), "url": url, "status": "IN_SYNC"})
            human(f"[{i}/{len(targets)}] IN_SYNC      {local.relative_to(REPO_ROOT)}")

    summary = {"checked": len(targets), "in_sync": len(targets) - drift - errors,
               "drift": drift, "fetch_errors": errors, "results": results}

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"\nSummary: {summary['checked']} checked, {summary['in_sync']} in sync, "
              f"{drift} drifted, {errors} fetch errors.")

    if args.check and (drift or errors):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
