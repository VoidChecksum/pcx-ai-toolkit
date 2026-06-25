import json, subprocess, sys, unittest
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parent.parent
PCX=REPO_ROOT/'tools/pcx.py'
class ModelEvalTest(unittest.TestCase):
    def test_model_eval_scores_output(self):
        out=REPO_ROOT/'tmp-model-output.md'
        out.write_text('Use pcx mcp-plan. process/reference_by_name then process/dereference. Mention permission. Validate with pcx verify and pcx evidence. Evidence C-001/E-001. verified offset 0x401000.')
        r=subprocess.run([sys.executable,str(PCX),'model-eval','--model-output',str(out),'--suite','evals/model-compatibility.json'], cwd=REPO_ROOT, capture_output=True, text=True)
        out.unlink(missing_ok=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertGreaterEqual(json.loads(r.stdout)['percent'],70)
if __name__=='__main__': unittest.main()
