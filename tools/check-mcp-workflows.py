#!/usr/bin/env python3
# mypy: ignore-errors
"""Static validation for deterministic Perception MCP workflow plans."""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools' / 'lib'))
from pcx_mcp_workflows import WORKFLOWS, validate_workflow, plan_perception_workflow  # noqa: E402

NO_HANDLE = {'process/list','process/reference_by_name','process/reference_by_pid','process/info_by_name','process/info_by_pid','process/cleanup_references','process/list_references'}


def load_tools():
    rows = json.loads((ROOT / 'docs/perception/mcp-tool-schemas.json').read_text())['tools']
    return {r['name']: r for r in rows}


def param_names(spec):
    return {str(k).rstrip('?') for k in (spec.get('params') or {}).keys()}


def main() -> int:
    ap = argparse.ArgumentParser(prog='check-mcp-workflows')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    tools = load_tools(); errors = []
    for name, spec in WORKFLOWS.items():
        plan = plan_perception_workflow(' '.join(spec['triggers'][:2]), 'target.exe')
        errors.extend(f'{name}: {e}' for e in validate_workflow(plan))
        if not any('dereference' in c or 'cleanup' in c for c in plan.get('cleanup', [])):
            errors.append(f'{name}: missing cleanup')
        for doc in plan.get('docs', []):
            if not (ROOT / doc).exists():
                errors.append(f'{name}: missing doc {doc}')
        for row in plan.get('steps', []):
            tool = row['tool']
            if tool not in tools:
                errors.append(f'{name}: unknown tool {tool}')
                continue
            if tool.startswith('process/') and tool not in NO_HANDLE and 'handle' not in row.get('params', {}):
                errors.append(f'{name}: {tool} missing handle')
            allowed = param_names(tools[tool])
            for param in row.get('params', {}):
                if allowed and param not in allowed:
                    errors.append(f'{name}: {tool} unknown param {param}')
        for fb in plan.get('fallbacks', []):
            if fb.get('missing') not in tools:
                errors.append(f'{name}: fallback missing unknown tool {fb.get("missing")}')
            for tool in fb.get('replacement_steps', []):
                if tool not in tools:
                    errors.append(f'{name}: fallback replacement unknown tool {tool}')
    evals = json.loads((ROOT / 'evals/perception-mcp-workflows.json').read_text())['cases']
    for case in evals:
        if case['workflow'] not in WORKFLOWS:
            errors.append(f'eval {case["name"]}: unknown workflow {case["workflow"]}')
    payload = {'ok': not errors, 'workflows': len(WORKFLOWS), 'errors': errors}
    print(json.dumps(payload, indent=2) if args.json else ('OK' if not errors else '\n'.join(errors)))
    return 0 if not errors else 1

if __name__ == '__main__':
    raise SystemExit(main())
