#!/usr/bin/env python3
"""Validate Enma/AngelScript code blocks inside an LLM answer.

Use this on a Markdown transcript, draft response, or generated README before
copying code into Perception. It extracts fenced code blocks tagged as enma,
angelScript, em, or as and runs the source-grounded PCX validator.

Usage:
    python3 tools/check-llm-answer.py answer.md
    python3 tools/check-llm-answer.py answer.md --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_grounding import load_api_index, validate_answer_markdown  # noqa: E402


def check_answer(path: Path) -> dict[str, Any]:
    if not INDEX_FILE.exists():
        return {"error": f"{INDEX_FILE} missing; run `python3 tools/build-api-index.py`"}
    index = load_api_index(INDEX_FILE)
    markdown = path.read_text(encoding="utf-8", errors="ignore")
    result = validate_answer_markdown(markdown, index, str(path))
    result["file"] = str(path)
    return cast(dict[str, Any], result)


def print_human(result: dict[str, Any]) -> None:
    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        return
    if result["ok"]:
        print(f"clean: checked {result['blocks_checked']} Enma/AngelScript code block(s)")
        return
    print(f"LLM answer has {len(result['findings'])} finding(s)")
    for finding in result["findings"]:
        print(
            f"  block {finding['code_block']} ({finding['language']}, starts line "
            f"{finding['code_block_line']}), code line {finding['line']}: "
            f"[{finding['kind']}] {finding['message']}"
        )
        for sig in finding.get("signatures", [])[:3]:
            print(f"      source: {sig.get('text')} — {sig.get('source')}")
        if finding.get("suggestions"):
            print(f"      suggestions: {', '.join(str(s) for s in finding['suggestions'])}")
        if finding.get("fix"):
            print(f"      fix: {finding['fix']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("answer", help="Markdown file containing an LLM answer")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    path = Path(args.answer)
    if not path.exists() or not path.is_file():
        print(f"ERROR: not found: {path}", file=sys.stderr)
        return 2

    result = check_answer(path)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human(result)
    if "error" in result:
        return 2
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
