import json, subprocess, sys, unittest
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parent.parent
PCX=REPO_ROOT/'tools/pcx.py'
class ReleaseCheckTest(unittest.TestCase):
    def test_release_check_runs_core_gates(self):
        r=subprocess.run([sys.executable,str(PCX),'release-check'],cwd=REPO_ROOT,capture_output=True,text=True,timeout=120)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        payload=json.loads(r.stdout)
        self.assertTrue(payload['ok'])
        names={c['name'] for c in payload['checks']}
        self.assertIn('markdown links', names)
        self.assertIn('mcp workflows', names)
if __name__=='__main__': unittest.main()
