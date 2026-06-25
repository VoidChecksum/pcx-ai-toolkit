import json
import unittest
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
class PerceptionMcpResultSchemaTest(unittest.TestCase):
    def test_every_tool_has_returns_schema(self):
        data=json.loads((REPO_ROOT/'docs/perception/mcp-tool-schemas.json').read_text())
        for tool in data['tools']:
            with self.subTest(tool=tool['name']):
                self.assertIn('returns_schema', tool)
                self.assertIn('type', tool['returns_schema'])
    def test_reference_handle_schema_is_hex(self):
        data=json.loads((REPO_ROOT/'docs/perception/mcp-tool-schemas.json').read_text())
        by={t['name']:t for t in data['tools']}
        self.assertEqual(by['process/reference_by_name']['returns_schema']['properties']['handle']['pattern'], '^0x[0-9a-fA-F]+$')
if __name__=='__main__': unittest.main()
