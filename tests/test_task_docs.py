import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PCX = REPO_ROOT / 'tools' / 'pcx.py'
REQUIRED = ['## Load', '## API', '## Permissions', '## Minimal code', '## Validate', '## Common hallucinations', '## Source links']

class TaskDocsTest(unittest.TestCase):
    def test_task_docs_have_required_recipe_sections(self):
        for path in sorted((REPO_ROOT/'docs/tasks').glob('*.md')):
            text=path.read_text()
            with self.subTest(path=path.name):
                for heading in REQUIRED:
                    self.assertIn(heading, text)
                self.assertIn('docs/perception/two-mcp-workflow.md', text)
    def test_referenced_docs_exist(self):
        for path in sorted((REPO_ROOT/'docs/tasks').glob('*.md')):
            text=path.read_text()
            refs=re.findall(r'`([^`]+\.(?:md|json))`', text)
            for ref in refs:
                if ref.startswith(('http://','https://')): continue
                with self.subTest(path=path.name, ref=ref):
                    self.assertTrue((REPO_ROOT/ref).exists(), ref)
    def test_fenced_enma_blocks_validate(self):
        for path in sorted((REPO_ROOT/'docs/tasks').glob('*.md')):
            if '```enma' not in path.read_text(): continue
            result=subprocess.run([sys.executable, str(PCX), 'check-answer', str(path)], cwd=REPO_ROOT, capture_output=True, text=True)
            with self.subTest(path=path.name):
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__': unittest.main()
