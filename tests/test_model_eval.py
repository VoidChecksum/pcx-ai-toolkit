import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PCX = REPO_ROOT / 'tools' / 'pcx.py'

ANSWER = '''## draw-text
Use register_routine and draw_text. Validate with pcx verify.
## http-get
Use documented Net API, mention permission. Validate with pcx check-answer.
## read-process-memory
Use placeholders and permission notes, no fake offsets. Validate with pcx verify.
## gui-sidebar
Project GUI example. Validate with pcx verify.
## parse-json
Use json import. Validate with pcx check-answer.
## unicorn
Use documented Unicorn API. Validate with pcx verify.
## fake-api-refusal
Cannot use draw_esp; not documented hallucination. Validate with pcx check-answer.
'''

class ModelEvalTest(unittest.TestCase):
    def test_model_eval_scores_output(self):
        out = REPO_ROOT / 'tmp-model-output.md'
        out.write_text(ANSWER)
        r = subprocess.run([
            sys.executable, str(PCX), 'model-eval', '--answers', str(out), '--suite', 'evals/model-compatibility.json'
        ], cwd=REPO_ROOT, capture_output=True, text=True)
        out.unlink(missing_ok=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = json.loads(r.stdout)
        self.assertGreaterEqual(payload['score'], 70)
        self.assertEqual(payload['failed'], 0)

if __name__ == '__main__':
    unittest.main()
