#!/usr/bin/env python3
# mypy: ignore-errors
"""Score model output against PCX compatibility criteria."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

FENCE_RE = re.compile(r'```enma\n(.*?)```', re.S)

def section(text: str, name: str) -> str:
    m = re.search(rf'(?ims)^##\s+{re.escape(name)}\b(.*?)(?=^##\s+|\Z)', text)
    return m.group(1) if m else text

def score_task(task: dict, answer: str) -> list[str]:
    failures=[]; low=answer.lower()
    for sym in task.get('must_use', []):
        if sym.lower() not in low: failures.append(f'missing required symbol {sym}')
    for sym in task.get('must_not_use', []):
        if sym.lower() in low: failures.append(f'used forbidden symbol {sym}')
    if task.get('expected_refusal') and not any(w in low for w in ['cannot', 'refuse', 'not documented', 'hallucinat']):
        failures.append('expected refusal or correction for fake API prompt')
    if 'permission' not in low and task['name'] in {'http-get','read-process-memory'}:
        failures.append('permissions not mentioned')
    if not any(cmd in low for cmd in ['pcx verify','pcx check-answer','pcx mcp-plan','pcx evidence']):
        failures.append('validation commands missing')
    if re.search(r'0x[0-9a-f]{4,}', low) and not any(w in low for w in ['placeholder','verified','evidence']):
        failures.append('offset-like literal lacks placeholder/verification context')
    return failures

def score(text: str, suite: dict) -> dict:
    failures=[]; passed=0
    for task in suite.get('tasks', []):
        ans=section(text, task['name'])
        errs=score_task(task, ans)
        if errs: failures.append({'task': task['name'], 'reason': '; '.join(errs)})
        else: passed += 1
    total=len(suite.get('tasks', [])) or 1
    score=round(100*passed/total)
    return {'score': score, 'passed': passed, 'failed': len(failures), 'failures': failures}

def main() -> int:
    ap=argparse.ArgumentParser(prog='pcx model-eval')
    ap.add_argument('--model-output', '--answers', dest='answers', type=Path, required=True)
    ap.add_argument('--suite', type=Path, required=True)
    args=ap.parse_args(); text=args.answers.read_text(encoding='utf-8'); suite=json.loads(args.suite.read_text(encoding='utf-8'))
    result=score(text, suite); print(json.dumps(result, indent=2)); return 0 if result['score'] >= 70 else 1
if __name__=='__main__': raise SystemExit(main())
