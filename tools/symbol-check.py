#!/usr/bin/env python3
"""Symbol-level hallucination checker for Enma and AngelScript scripts.

Loads knowledge/pcx-api-index.json (built by tools/build-api-index.py) and
reports unknown function/method calls and unknown declared types. This catches
the most common LLM hallucinations: invented function names, wrong method
names, and missing imports for Enma addon modules.

Usage:
    python tools/symbol-check.py file.em
    python tools/symbol-check.py file.as
    python tools/symbol-check.py --json file_or_dir

Exit code: 0 if clean, 1 if any unknown symbol found.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_grounding import load_api_index, validate_code_against_index  # noqa: E402


def load_index(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Build it first:\n  python3 tools/build-api-index.py"
        )
    return load_api_index(path)


def detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".em":
        return "enma"
    if ext == ".as":
        return "angelscript"
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if text.startswith("import \"") or "register_routine" in text[:500]:
        return "enma"
    if "register_callback" in text[:500] or "@" in text[:200]:
        return "angelscript"
    return "enma"


def collect_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(p for p in target.rglob("*") if p.suffix.lower() in {".em", ".as"})


def check_file(path: Path, index: dict[str, object], language: str | None = None) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if language is None:
        language = detect_language(path)
    return validate_code_against_index(text, language, index, str(path))


def print_findings(findings: list[dict[str, object]], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(findings, indent=2))
        return
    if not findings:
        print("clean: no unknown symbols")
        return
    by_file: dict[str, list[dict[str, object]]] = {}
    for f in findings:
        by_file.setdefault(str(f["file"]), []).append(f)
    for file_path, items in by_file.items():
        print(f"\n{file_path}")
        for it in sorted(items, key=lambda x: int(str(x["line"]))):
            print(f"  {it['line']}: [{it['kind']}] {it['message']}")
            for sig in it.get("signatures", [])[:3]:
                print(f"      source: {sig.get('text')} — {sig.get('source')}")
            if it.get("suggestions"):
                print(f"      suggestions: {', '.join(str(s) for s in it['suggestions'])}")
            if it.get("fix"):
                print(f"      fix: {it['fix']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="file or directory to check")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--lang", choices=["enma", "angelscript"], help="force language detection")
    args = ap.parse_args()

    try:
        index = load_index(INDEX_FILE)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    target = Path(args.target)
    if not target.exists():
        print(f"ERROR: not found: {target}", file=sys.stderr)
        return 2

    all_findings: list[dict[str, object]] = []
    for path in collect_files(target):
        all_findings.extend(check_file(path, index, args.lang))

    print_findings(all_findings, args.json)
    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
