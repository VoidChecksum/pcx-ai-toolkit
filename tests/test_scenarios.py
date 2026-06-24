import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class ScenarioCoverageTest(unittest.TestCase):
    def test_all_planned_scenarios_exist(self):
        expected = {
            "lifecycle-enma/main.em",
            "lifecycle-angelscript/main.as",
            "render-enma/main.em",
            "render-angelscript/main.as",
            "gui-enma/main.em",
            "gui-angelscript/main.as",
            "proc-enma/main.em",
            "proc-angelscript/main.as",
            "net-enma/main.em",
            "net-angelscript/main.as",
            "filesystem-enma/main.em",
            "filesystem-angelscript/main.as",
            "zydis-enma/main.em",
            "zydis-angelscript/main.as",
            "unicorn-enma/main.em",
            "mcp-answer-validation/answer.md",
        }
        root = REPO_ROOT / "examples" / "scenarios"
        found = {
            str(path.relative_to(root))
            for path in root.rglob("*")
            if path.suffix in {".em", ".as", ".md"} and path.name != "README.md"
        }
        self.assertTrue(expected <= found, sorted(expected - found))

    def test_scenarios_verify(self):
        result = subprocess.run(
            [
                "python3",
                "tools/verify-project.py",
                "examples/scenarios",
                "--allow-placeholders",
                "--allow-unverified",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
