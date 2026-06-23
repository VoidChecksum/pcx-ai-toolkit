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
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_grounding import load_api_index, validate_code_against_index  # noqa: E402

LANG_ALIASES = {
    "enma": "enma",
    "em": "enma",
    ".em": "enma",
    "angelscript": "angelscript",
    "angel-script": "angelscript",
    "as": "angelscript",
    ".as": "angelscript",
}

FENCE_RE = re.compile(r'^```\s*([A-Za-z_.-]*)[^\n]*\n(.*?)\n```', re.MULTILINE | re.DOTALL)


def extract_code_blocks(markdown: str) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    for idx, match in enumerate(FENCE_RE.finditer(markdown), 1):
        hint = match.group(1).strip().lower()
        language = LANG_ALIASES.get(hint)
        if not language:
            continue
        line = markdown[:match.start()].count("\n") + 1
        blocks.append({
            "index": idx,
            "line": line,
            "language": language,
            "code": match.group(2),
        })
    return blocks


def check_answer(path: Path) -> dict[str, object]:
    if not INDEX_FILE.exists():
        return {"error": f"{INDEX_FILE} missing; run `python3 tools/build-api-index.py`"}
    index = load_api_index(INDEX_FILE)
    markdown = path.read_text(encoding="utf-8", errors="ignore")
    blocks = extract_code_blocks(markdown)
    findings: list[dict[str, object]] = []
    for block in blocks:
        source = f"{path}:code-block-{block['index']}"
        block_findings = validate_code_against_index(
            str(block["code"]),
            str(block["language"]),
            index,
            source,
        )
        for finding in block_findings:
            finding["code_block"] = block["index"]
            finding["code_block_line"] = block["line"]
            finding["language"] = block["language"]
            findings.append(finding)
    return {
        "file": str(path),
        "blocks_checked": len(blocks),
        "findings": findings,
        "ok": not findings,
    }


def print_human(result: dict[str, object]) -> None:
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
