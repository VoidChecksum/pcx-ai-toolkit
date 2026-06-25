import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "tools" / "knowledge-index.py"
PCX = REPO_ROOT / "tools" / "pcx.py"


class KnowledgeIndexTest(unittest.TestCase):
    def test_build_and_search_finds_vmp2_knowledge(self):
        with tempfile.TemporaryDirectory() as td:
            index = Path(td) / "index.jsonl"
            build = subprocess.run([sys.executable, str(TOOL), "build-vector-index", "--out", str(index)], cwd=REPO_ROOT, capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            self.assertTrue(index.exists())
            search = subprocess.run([sys.executable, str(TOOL), "search", "vmprotect devirtualization", "--index", str(index)], cwd=REPO_ROOT, capture_output=True, text=True)
            self.assertEqual(search.returncode, 0, search.stdout + search.stderr)
            rows = json.loads(search.stdout)
            self.assertTrue(any("vmprotect" in row["path"].lower() or "devirtual" in row["path"].lower() for row in rows))

    def test_pcx_knowledge_command_dispatches(self):
        result = subprocess.run([sys.executable, str(PCX), "knowledge", "search", "render overlay", "--limit", "1"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIsInstance(json.loads(result.stdout), list)


if __name__ == "__main__":
    unittest.main()
