import re
import unittest
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parent.parent
SKILLS=['perception-mcp-session','perception-mcp-safety','perception-mcp-re-workflows','engine-source2-mcp','engine-unreal-mcp','engine-unity-il2cpp-mcp','evidence-graph','mcp-tool-routing']
class SkillContractTest(unittest.TestCase):
    def test_new_mcp_skills_have_control_contracts(self):
        for name in SKILLS:
            path=REPO_ROOT/'.claude/skills'/name/'SKILL.md'
            text=path.read_text()
            with self.subTest(skill=name):
                self.assertRegex(text, r'(?s)^---.*name:\s*'+re.escape(name)+r'.*description:.*---')
                lowered=text.lower()
                for phrase in ['required input','output contract','stop condition','validation']:
                    self.assertIn(phrase, lowered)
                self.assertRegex(text, r'`(?:docs|knowledge|\.claude)/[^`]+`')
if __name__=='__main__': unittest.main()
