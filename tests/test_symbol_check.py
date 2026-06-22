"""Regression tests for tools/symbol-check.py.

Proves that the symbol-level hallucination checker catches invented API names
while letting real templates and user-defined functions pass.
"""
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYMBOL_CHECK = REPO_ROOT / "tools" / "symbol-check.py"
TEMPLATES = REPO_ROOT / "templates"


def _run(target: str) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(SYMBOL_CHECK), target],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class SymbolCheckTest(unittest.TestCase):
    def test_hello_world_template_clean(self):
        rc, out, err = _run(str(TEMPLATES / "hello-world.em"))
        self.assertEqual(rc, 0, f"hello-world.em should pass symbol-check:\n{out}\n{err}")
        self.assertIn("clean", out)

    def test_hallucinated_function_caught(self):
        bad = """
import "vec";
import "color";

void my_render(int64 data) {
    draw_esp(vec2(0.0, 0.0), color(255, 0, 0, 255));
}

int64 main() {
    register_routine(cast<int64>(my_render), 0);
    return 1;
}
"""
        path = Path("/tmp/pcx_hallucinate_test.em")
        path.write_text(bad, encoding="utf-8")
        try:
            rc, out, err = _run(str(path))
            self.assertEqual(rc, 1, f"hallucinated draw_esp should fail symbol-check:\n{out}\n{err}")
            self.assertIn("draw_esp", out)
        finally:
            path.unlink(missing_ok=True)

    def test_user_defined_callback_allowed(self):
        code = """
import "vec";
import "color";

void my_render(int64 data) {
    draw_text("hi", vec2(0.0, 0.0), color(255,0,0,255), get_font20(), 0, color(0,0,0,0), 0.0);
}

int64 main() {
    register_routine(cast<int64>(my_render), 0);
    return 1;
}
"""
        path = Path("/tmp/pcx_user_callback_test.em")
        path.write_text(code, encoding="utf-8")
        try:
            rc, out, err = _run(str(path))
            self.assertEqual(rc, 0, f"user-defined callback should not be flagged:\n{out}\n{err}")
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
