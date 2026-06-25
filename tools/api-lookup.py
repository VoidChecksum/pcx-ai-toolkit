#!/usr/bin/env python3
"""Look up a Perception Enma API symbol from the generated index.

This is the fast, deterministic oracle to use before trusting an LLM-proposed
function, method, type, or signature.

Usage:
    python3 tools/api-lookup.py draw_text
    python3 tools/api-lookup.py draw_text --lang enma
    python3 tools/api-lookup.py draw_text --json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR / "lib"))
from pcx_paths import data_root  # noqa: E402
from pcx_grounding import load_api_index, lookup_symbol  # noqa: E402

REPO_ROOT = data_root()
INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"


def _print_human(result: dict[str, Any]) -> None:
    symbol = result["symbol"]
    language = result.get("language") or "any language"
    if not result["found"]:
        print(f"not found: {symbol} ({language})")
        suggestions = result.get("suggestions") or []
        if suggestions:
            print("near matches:")
            for item in suggestions:
                print(f"  - {item}")
        return

    print(f"found: {symbol} ({language})")
    languages = result.get("languages") or []
    if languages:
        print(f"languages: {', '.join(str(x) for x in languages)}")
    if result.get("type"):
        print("type: yes")

    signatures = result.get("signatures") or []
    if signatures:
        print("signatures:")
        for sig in signatures:
            print(f"  - [{sig.get('language')}] {sig.get('text')}")
            print(f"    source: {sig.get('source')}")


def main() -> int:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_name = "api-lookup.exe" if os.name == "nt" else "api-lookup"
    binary_path = os.path.join(base_dir, "bin", bin_name)
    if os.path.exists(binary_path):
        try:
            res = subprocess.run([binary_path] + sys.argv[1:])
            return res.returncode
        except Exception:
            pass

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("symbol", help="function, method, or type name")
    ap.add_argument("--lang", default="", help="restrict lookup to Enma (default)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    if not INDEX_FILE.exists():
        print(f"ERROR: {INDEX_FILE} missing; run `python3 tools/build-api-index.py`", file=sys.stderr)
        return 2

    language = (args.lang or "enma").lower()
    if language not in {"enma", "em", ".em"}:
        print(f"ERROR: unsupported --lang {args.lang!r}; use enma", file=sys.stderr)
        return 2
    index = load_api_index(INDEX_FILE)
    result = lookup_symbol(index, args.symbol, "enma")
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_human(result)
    return 0 if result["found"] else 1


if __name__ == "__main__":
    sys.exit(main())
