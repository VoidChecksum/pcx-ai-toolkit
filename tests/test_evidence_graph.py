import json, subprocess, sys, unittest
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parent.parent
PCX=REPO_ROOT/'tools/pcx.py'
class EvidenceGraphTest(unittest.TestCase):
    def test_lab_expected_evidence_validates_and_renders(self):
        for graph in sorted((REPO_ROOT/'labs/re-toy-targets').glob('*/expected-evidence.json')):
            with self.subTest(graph=graph.relative_to(REPO_ROOT)):
                verify=subprocess.run([sys.executable,str(PCX),'evidence','--file',str(graph),'verify'],cwd=REPO_ROOT,capture_output=True,text=True)
                self.assertEqual(verify.returncode,0,verify.stdout+verify.stderr)
                mermaid=subprocess.run([sys.executable,str(PCX),'evidence','--file',str(graph),'graph','--format','mermaid'],cwd=REPO_ROOT,capture_output=True,text=True)
                self.assertEqual(mermaid.returncode,0,mermaid.stdout+mermaid.stderr)
                self.assertIn('graph TD', mermaid.stdout)
                html=subprocess.run([sys.executable,str(PCX),'evidence','--file',str(graph),'graph','--format','html'],cwd=REPO_ROOT,capture_output=True,text=True)
                self.assertEqual(html.returncode,0,html.stdout+html.stderr)
                self.assertIn('<html>', html.stdout)
    def test_rejected_claim_requires_reason(self):
        path=REPO_ROOT/'tmp-evidence-rejected.json'
        path.write_text(json.dumps({'schema':'pcx-evidence-graph-v1','target':{'process':'x'},'claims':[{'id':'C-001','claim':'bad','status':'rejected','evidence':[]}],'evidence':[]})+'\n')
        r=subprocess.run([sys.executable,str(PCX),'evidence','--file',str(path),'verify'],cwd=REPO_ROOT,capture_output=True,text=True)
        path.unlink(missing_ok=True)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('rejected claims need reason', r.stdout)
if __name__=='__main__': unittest.main()
