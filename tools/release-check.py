#!/usr/bin/env python3
# mypy: ignore-errors
"""One-command release readiness gate."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def run(name, cmd):
    r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {'name': name, 'ok': r.returncode == 0, 'cmd': cmd, 'stdout': r.stdout[-2000:], 'stderr': r.stderr[-2000:]}

def main() -> int:
    py=sys.executable
    checks=[
      ('markdown links', [py,'-m','unittest','tests.test_all_markdown_links']),
      ('docs drift', [py,'tools/check-doc-drift.py']),
      ('api index', [py,'tools/build-api-index.py','--check']),
      ('llms index', [py,'tools/build-llms-index.py','--check']),
      ('coverage dashboard', [py,'tools/build-coverage-dashboard.py','--check']),
      ('internal links tool', [py,'tools/check-internal-links.py']),
      ('hallucination eval', [py,'tools/hallucination-eval.py']),
      ('mcp config', [py,'tools/check-mcp-config.py','--check']),
      ('mcp workflows', [py,'tools/check-mcp-workflows.py','--json']),
      ('task docs', [py,'-m','unittest','tests.test_task_docs']),
      ('mock mcp', [py,'-m','unittest','tests.test_mock_perception_mcp']),
      ('workflow eval', [py,'-m','unittest','tests.test_perception_mcp_workflow_evals']),
      ('evidence graph', [py,'-m','unittest','tests.test_evidence_graph','tests.test_evidence_graph_integrity']),
      ('model compatibility', [py,'-m','unittest','tests.test_model_eval']),
    ]
    results=[run(n,c) for n,c in checks]
    ok=all(r['ok'] for r in results)
    print(json.dumps({'ok': ok, 'checks': results}, indent=2))
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
