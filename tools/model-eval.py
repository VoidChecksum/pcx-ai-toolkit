#!/usr/bin/env python3
# mypy: ignore-errors
"""Score model output against PCX compatibility criteria."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def score(text: str) -> dict:
    checks = {
        "api_symbol_validity": "pcx api" in text or "pcx check-answer" in text,
        "lifecycle_correctness": all(x in text for x in ["reference_by_name", "dereference"]),
        "permissions_mentioned": "permission" in text.lower(),
        "mcp_workflow_correctness": "pcx mcp-plan" in text or "process/" in text,
        "no_fake_offsets": not re.search(r"0x[0-9a-fA-F]{4,}", text) or "evidence" in text.lower() or "verified" in text.lower(),
        "validation_commands_included": "pcx verify" in text or "pcx check-answer" in text or "pcx evidence" in text,
        "evidence_references_included": bool(re.search(r"\b[CE]-\d{3,}\b", text)),
    }
    passed=sum(checks.values())
    return {"score": passed, "max_score": len(checks), "percent": round(100*passed/len(checks), 1), "checks": checks}

def main() -> int:
    ap=argparse.ArgumentParser(prog='pcx model-eval'); ap.add_argument('--model-output', type=Path, required=True); ap.add_argument('--suite', type=Path, required=True)
    args=ap.parse_args(); text=args.model_output.read_text(encoding='utf-8'); result=score(text); result['suite']=str(args.suite)
    print(json.dumps(result, indent=2)); return 0 if result['percent'] >= 70 else 1
if __name__=='__main__': raise SystemExit(main())
