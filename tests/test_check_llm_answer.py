"""Regression tests for tools/check-llm-answer.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_ANSWER = REPO_ROOT / "tools" / "check-llm-answer.py"


def _run(markdown: str) -> tuple[int, dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as f:
        f.write(markdown)
        path = Path(f.name)
    try:
        result = subprocess.run(
            [sys.executable, str(CHECK_ANSWER), str(path), "--json"],
            capture_output=True,
            text=True,
        )
        return result.returncode, json.loads(result.stdout)
    finally:
        path.unlink(missing_ok=True)


class CheckLlmAnswerTest(unittest.TestCase):
    def test_clean_enma_block_passes(self):
        rc, data = _run(
            '''Use this:

```enma
int64 main() {
    println("hello");
    return 1;
}
```
'''
        )
        self.assertEqual(rc, 0, data)
        self.assertTrue(data["ok"])
        self.assertEqual(data["blocks_checked"], 1)

    def test_hallucinated_block_fails_with_suggestion_context(self):
        rc, data = _run(
            '''Bad answer:

```enma
void r(int64 d) {
    draw_texxt("hi");
}
```
'''
        )
        self.assertEqual(rc, 1, data)
        self.assertFalse(data["ok"])
        finding = data["findings"][0]
        self.assertEqual(finding["symbol"], "draw_texxt")
        self.assertIn("draw_text", finding["suggestions"])


if __name__ == "__main__":
    unittest.main()
