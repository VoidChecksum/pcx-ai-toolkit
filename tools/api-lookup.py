#!/usr/bin/env python3
"""Look up a Perception Enma/AngelScript API symbol from the generated index.

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
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_grounding import load_api_index, lookup_symbol  # noqa: E402


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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("symbol", help="function, method, or type name")
    ap.add_argument("--lang", choices=["enma", "angelscript"], help="restrict lookup to one language")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    if not INDEX_FILE.exists():
        print(f"ERROR: {INDEX_FILE} missing; run `python3 tools/build-api-index.py`", file=sys.stderr)
        return 2

    index = load_api_index(INDEX_FILE)
    result = lookup_symbol(index, args.symbol, args.lang)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_human(result)
    return 0 if result["found"] else 1


if __name__ == "__main__":
    sys.exit(main())
