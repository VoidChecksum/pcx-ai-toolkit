import json, subprocess, sys, unittest
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parent.parent
PCX=REPO_ROOT/'tools/pcx.py'
class McpWorkflowStaticToolTest(unittest.TestCase):
    def test_cli_workflow_checker_passes(self):
        r=subprocess.run([sys.executable,str(PCX),'check-mcp-workflows','--json'],cwd=REPO_ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertTrue(json.loads(r.stdout)['ok'])
if __name__=='__main__': unittest.main()
