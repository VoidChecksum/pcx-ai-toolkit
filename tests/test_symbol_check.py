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
            self.assertIn("Invented helper", out)
        finally:
            path.unlink(missing_ok=True)

    def test_unsupported_symbol_uses_denylist_reason(self):
        code = """
int64 main() {
    draw_esp();
    return 1;
}
"""
        path = Path("/tmp/pcx_unsupported_symbol_test.em")
        path.write_text(code, encoding="utf-8")
        try:
            rc, out, err = _run(str(path))
            self.assertEqual(rc, 1, f"denylisted draw_esp should fail symbol-check:\n{out}\n{err}")
            self.assertIn("unsupported_symbol", out)
            self.assertIn("Invented helper", out)
        finally:
            path.unlink(missing_ok=True)

    def test_common_hallucinated_aim_helper_uses_denylist_reason(self):
        code = """
int64 main() {
    read_view_angles();
    return 1;
}
"""
        path = Path("/tmp/pcx_unsupported_aim_test.em")
        path.write_text(code, encoding="utf-8")
        try:
            rc, out, err = _run(str(path))
            self.assertEqual(rc, 1, f"denylisted read_view_angles should fail symbol-check:\n{out}\n{err}")
            self.assertIn("unsupported_symbol", out)
            self.assertIn("not in the Perception API index", out)
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

    def test_angelscript_rejects_enma_lifecycle(self):
        code = """
int main() {
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

void on_render(int data) {
    println("wrong language");
}
"""
        path = Path("/tmp/pcx_wrong_language_as_test.as")
        path.write_text(code, encoding="utf-8")
        try:
            rc, out, err = _run(str(path))
            self.assertEqual(rc, 1, f"AS using Enma lifecycle should fail:\n{out}\n{err}")
            self.assertIn("wrong_language_symbol", out)
            self.assertIn("register_routine", out)
        finally:
            path.unlink(missing_ok=True)

    def test_enma_rejects_angelscript_lifecycle(self):
        code = """
int64 main() {
    register_callback(on_tick, 16, 0);
    log("wrong language");
    return 1;
}

void on_tick(int64 data) {}
"""
        path = Path("/tmp/pcx_wrong_language_enma_test.em")
        path.write_text(code, encoding="utf-8")
        try:
            rc, out, err = _run(str(path))
            self.assertEqual(rc, 1, f"Enma using AS lifecycle should fail:\n{out}\n{err}")
            self.assertIn("wrong_language_symbol", out)
            self.assertIn("register_callback", out)
        finally:
            path.unlink(missing_ok=True)


    def test_enma_semantic_edges_match_rust_validator(self):
        cases = {
            "pcx_py_map_key_bad.em": (
                'import "maps"\nint64 main(){map<int64, int64> counts; return 1;}\n',
                "semantic_error",
                "imap<V>",
            ),
            "pcx_py_pointer_escape_bad.em": (
                "int64* leak(){int64 local = 1; return &local;}\n",
                "semantic_error",
                "escaping local addresses",
            ),
            "pcx_py_file_perm_bad.em": (
                'import "file"\nint64 main(){return fs_read_file("x.txt").length();}\n',
                "missing_permission",
                "PERM_FILE",
            ),
        }
        for name, (code, kind, expected) in cases.items():
            with self.subTest(name=name):
                path = Path("/tmp") / name
                path.write_text(code, encoding="utf-8")
                try:
                    rc, out, err = _run(str(path))
                    self.assertEqual(rc, 1, f"{name} should fail symbol-check:\n{out}\n{err}")
                    self.assertIn(kind, out)
                    self.assertIn(expected, out)
                finally:
                    path.unlink(missing_ok=True)

    def test_enma_file_permission_annotation_allowed(self):
        path = Path("/tmp/pcx_py_file_perm_ok.em")
        path.write_text(
            'import "file"\n// Host must grant PERM_FILE before compile.\nint64 main(){return fs_read_file("x.txt").length();}\n',
            encoding="utf-8",
        )
        try:
            rc, out, err = _run(str(path))
            self.assertEqual(rc, 0, f"PERM_FILE host annotation should pass:\n{out}\n{err}")
        finally:
            path.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
