import unittest, sys
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT/'tools/lib'))
from pcx_mcp_workflows import plan_perception_workflow, validate_workflow
class WorkflowStaticValidationTest(unittest.TestCase):
    def test_all_eval_plans_validate(self):
        import json
        cases=json.loads((REPO_ROOT/'evals/perception-mcp-workflows.json').read_text())['cases']
        for case in cases:
            with self.subTest(case=case['name']):
                plan=plan_perception_workflow(case['task'], 'target.exe', capabilities=case.get('capabilities'))
                self.assertEqual(validate_workflow(plan), [])
    def test_fallbacks_are_structured(self):
        plan=plan_perception_workflow('find string refs', 'target.exe', capabilities=['process/reference_by_name','process/get_module_by_name','process/dereference'])
        self.assertEqual(plan['fallbacks'][0]['missing'], 'process/find_string_refs')
        self.assertIn('process/scan_string', plan['fallbacks'][0]['replacement_steps'])
if __name__=='__main__': unittest.main()
