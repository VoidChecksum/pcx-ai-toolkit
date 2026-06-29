#!/usr/bin/env python3
"""Symbol-level hallucination checker for PCX scripts.

Loads knowledge/pcx-api-index.json (built by tools/build-api-index.py) and
reports unknown function/method calls and unknown declared types. This catches
the most common LLM hallucinations: invented function names, wrong method
names, missing imports for Enma addon modules, and cross-language API drift.

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
from typing import Any, cast

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR / "lib"))
from pcx_language_modes import language_for_path, normalize_language, supported_languages  # noqa: E402
from pcx_paths import data_root  # noqa: E402
from pcx_grounding import load_api_index, validate_code_against_index  # noqa: E402

REPO_ROOT = data_root()
INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"


def load_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Build it first:\n  python3 tools/build-api-index.py"
        )
    return cast(dict[str, Any], load_api_index(path))


def detect_language(path: Path) -> str:
    try:
        return language_for_path(path)
    except ValueError:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if text.startswith("import \"") or "register_routine" in text[:500]:
            return "enma"
        if "register_callback" in text[:500] or text.startswith("int main("):
            return "angelscript"
        return normalize_language("")


def collect_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(p for p in target.rglob("*") if p.suffix.lower() in {".em", ".as"})


def _project_functions(paths: list[Path]) -> dict[str, set[str]]:
    funcs: dict[str, set[str]] = {lang: set() for lang in supported_languages()}
    for path in paths:
        language = detect_language(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        from pcx_parser import extract_function_defs  # noqa: PLC0415

        funcs[language].update(name for name, _ in extract_function_defs(text, language))
    return funcs


def check_file(
    path: Path,
    index: dict[str, Any],
    language: str | None = None,
    extra_user_functions: set[str] | None = None,
) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if language is None:
        language = detect_language(path)
    return cast(
        list[dict[str, Any]],
        validate_code_against_index(text, language, index, str(path), extra_user_functions),
    )


def print_findings(findings: list[dict[str, Any]], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(findings, indent=2))
        return
    if not findings:
        print("clean: no unknown symbols")
        return
    by_file: dict[str, list[dict[str, Any]]] = {}
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
    ap.add_argument("--lang", choices=supported_languages(), help="force language detection")
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

    paths = collect_files(target)
    project_funcs = _project_functions(paths) if args.lang is None else {}
    all_findings: list[dict[str, Any]] = []
    for path in paths:
        try:
            language = args.lang or detect_language(path)
            all_findings.extend(check_file(path, index, language, project_funcs.get(language)))
        except ValueError as exc:
            all_findings.append({"file": str(path), "line": 0, "kind": "unsupported_language", "symbol": path.suffix, "message": str(exc)})

    print_findings(all_findings, args.json)
    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
