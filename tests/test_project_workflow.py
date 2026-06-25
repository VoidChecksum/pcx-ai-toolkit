"""Regression tests for project scaffolding, project verification, AS linting, and evals."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PCX = REPO_ROOT / "tools" / "pcx.py"
VERIFY_PROJECT = REPO_ROOT / "tools" / "verify-project.py"
RE_IMPORTER = REPO_ROOT / "tools" / "re-importer.py"
HALLUCINATION_EVAL = REPO_ROOT / "tools" / "hallucination-eval.py"


class ProjectWorkflowTest(unittest.TestCase):
    def test_create_enma_project_and_verify_scaffold_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "demo"
            create = subprocess.run(
                [
                    sys.executable,
                    str(PCX),
                    "create",
                    "--name",
                    "Demo Project",
                    "--language",
                    "enma",
                    "--kind",
                    "full",
                    "--target",
                    "demo.exe",
                    "--output",
                    str(out),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(create.returncode, 0, create.stderr + create.stdout)
            meta = json.loads((out / "pcx-project.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["language"], "enma")
            self.assertEqual(meta["target_process"], "demo.exe")
            self.assertIn('"demo.exe"', (out / "main.em").read_text(encoding="utf-8"))

            verify = subprocess.run(
                [
                    sys.executable,
                    str(VERIFY_PROJECT),
                    str(out),
                    "--allow-placeholders",
                    "--allow-unverified",
                    "--json",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(verify.returncode, 0, verify.stderr + verify.stdout)
            self.assertTrue(json.loads(verify.stdout)["ok"])

    def test_create_rejects_angelscript(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            result = subprocess.run(
                [
                    sys.executable,
                    str(PCX),
                    "create",
                    "--name",
                    "AS Project",
                    "--language",
                    "angelscript",
                    "--kind",
                    "full",
                    "--output",
                    str(Path(td) / "as"),
                ],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported", result.stderr.lower() + result.stdout.lower())

    def test_re_importer_converts_symbol_csv_from_stdin(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RE_IMPORTER), "--format", "ida-names", "--out-format", "enma-offsets", "-"],
            input="name,address,kind\nLocalPlayer,0x1234,symbol\n",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("const uint64 OFF_LOCALPLAYER = 0x1234;", result.stdout)
        self.assertIn("UNVERIFIED", result.stdout)


    def test_re_importer_evidence_jsonl_has_source_hash(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RE_IMPORTER), "--format", "ida-names", "--out-format", "evidence-jsonl", "-"],
            input="name,address,kind\nLocalPlayer,0x1234,symbol\n",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads(result.stdout)
        self.assertEqual(row["name"], "LocalPlayer")
        self.assertIn("source_sha256", row)
    def test_hallucination_eval_corpus_passes(self) -> None:
        result = subprocess.run([sys.executable, str(HALLUCINATION_EVAL), "--json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)["failed"], 0)


if __name__ == "__main__":
    unittest.main()
