#!/usr/bin/env python3
"""Run the PCX hallucination regression benchmark.

The benchmark is a JSON corpus of model-like answers/snippets.  Each case says
whether the validator should accept it.  This catches regressions where the
toolkit starts allowing invented APIs or rejecting documented ones.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS = REPO_ROOT / "evals" / "hallucination-regression.json"
INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_grounding import load_api_index, validate_answer_markdown, validate_code_against_index  # noqa: E402


def run_case(case: dict[str, Any], index: dict[str, Any]) -> dict[str, Any]:
    mode = case.get("mode", "code")
    should_pass = bool(case.get("should_pass"))
    if mode == "answer":
        result = validate_answer_markdown(str(case.get("input", "")), index, str(case.get("name", "answer.md")))
        ok = bool(result.get("ok"))
        findings = result.get("findings", [])
    else:
        language = str(case.get("language", "enma"))
        findings = validate_code_against_index(str(case.get("input", "")), language, index, str(case.get("name", "case")))
        ok = not findings
        result = {"ok": ok, "findings": findings}
    passed = ok == should_pass
    return {
        "name": case.get("name", "unnamed"),
        "mode": mode,
        "expected_ok": should_pass,
        "actual_ok": ok,
        "passed": passed,
        "findings": findings,
        "result": result,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("corpus", nargs="?", default=str(DEFAULT_CORPUS), help="benchmark JSON file")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    corpus_path = Path(args.corpus)
    if not corpus_path.is_file():
        print(f"ERROR: corpus not found: {corpus_path}", file=sys.stderr)
        return 2
    if not INDEX_FILE.is_file():
        print("ERROR: API index missing; run tools/build-api-index.py", file=sys.stderr)
        return 2

    index = load_api_index(INDEX_FILE)
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    cases = corpus.get("cases", [])
    results = [run_case(case, index) for case in cases]
    failed = [r for r in results if not r["passed"]]
    summary = {
        "corpus": str(corpus_path),
        "cases": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"[{status}] {result['name']} expected_ok={result['expected_ok']} actual_ok={result['actual_ok']}")
            if not result["passed"]:
                for finding in result["findings"][:5]:
                    print(f"  {finding.get('line')}: {finding.get('kind')} {finding.get('symbol')} - {finding.get('message')}")
        print(f"Summary: {summary['passed']}/{summary['cases']} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
