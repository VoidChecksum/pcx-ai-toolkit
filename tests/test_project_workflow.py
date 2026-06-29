"""Regression tests for project scaffolding, project verification, AS linting, and evals."""
from __future__ import annotations

import json
import os
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

    def test_create_angelscript_overlay_project(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "as"
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
                    "overlay",
                    "--target",
                    "demo.exe",
                    "--output",
                    str(out),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            meta = json.loads((out / "pcx-project.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["language"], "angelscript")
            self.assertEqual(meta["entrypoint"], "main.as")
            script = (out / "as-project.as").read_text(encoding="utf-8")
            self.assertIn('TARGET_PROCESS = "demo.exe"', script)

    def test_create_defaults_to_angelscript_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "default-as"
            result = subprocess.run(
                [
                    sys.executable,
                    str(PCX),
                    "create",
                    "--name",
                    "Default AS",
                    "--kind",
                    "overlay",
                    "--target",
                    "demo.exe",
                    "--output",
                    str(out),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            meta = json.loads((out / "pcx-project.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["language"], "angelscript")
            self.assertEqual(meta["entrypoint"], "main.as")

    def test_create_lua_overlay_project(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "lua"
            result = subprocess.run(
                [
                    sys.executable,
                    str(PCX),
                    "create",
                    "--name",
                    "Lua Project",
                    "--language",
                    "lua",
                    "--kind",
                    "overlay",
                    "--target",
                    "demo.exe",
                    "--output",
                    str(out),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            meta = json.loads((out / "pcx-project.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["language"], "lua")
            self.assertEqual(meta["entrypoint"], "main.lua")
            script = (out / "lua-project.lua").read_text(encoding="utf-8")
            self.assertIn('TARGET_PROCESS = "demo.exe"', script)

    def test_lua_context_does_not_block_lua(self) -> None:
        text = (REPO_ROOT / "docs" / "llms-perception-lua.md").read_text(encoding="utf-8")
        self.assertIn("pcx api <symbol> --lang lua", text)
        self.assertIn("Perception Lua", text)

    def test_angelscript_context_does_not_block_as(self) -> None:
        text = (REPO_ROOT / "docs" / "llms-perception-angelscript.md").read_text(encoding="utf-8")
        self.assertNotIn("toolkit is Enma-only", text)
        self.assertNotIn("AngelScript (`.as`) is deprecated", text)
        self.assertIn("pcx api <symbol> --lang angelscript", text)

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

    def test_lsp_check_reports_diagnostics_from_stdio_server(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "fake_lsp.py"
            script = Path(td) / "bad.em"
            script.write_text("int64 main(){ return 1; }\n", encoding="utf-8")
            fake.write_text(
                "import json, sys\n"
                "def send(msg):\n"
                "    body=json.dumps(msg)\n"
                "    sys.stdout.write(f'Content-Length: {len(body)}\\r\\n\\r\\n{body}')\n"
                "    sys.stdout.flush()\n"
                "while True:\n"
                "    line=sys.stdin.readline()\n"
                "    if not line:\n"
                "        break\n"
                "    if line == '\\r\\n':\n"
                "        continue\n"
                "    if not line.lower().startswith('content-length:'):\n"
                "        continue\n"
                "    n=int(line.split(':',1)[1])\n"
                "    sys.stdin.readline()\n"
                "    msg=json.loads(sys.stdin.read(n))\n"
                "    if msg.get('method') == 'initialize':\n"
                "        send({'jsonrpc':'2.0','id':msg['id'],'result':{'capabilities':{}}})\n"
                "    elif msg.get('method') == 'textDocument/didOpen':\n"
                "        uri=msg['params']['textDocument']['uri']\n"
                "        send({'jsonrpc':'2.0','method':'textDocument/publishDiagnostics','params':{'uri':uri,'diagnostics':[{'range':{'start':{'line':0,'character':0},'end':{'line':0,'character':5}},'severity':1,'message':'fake compiler error','code':'EN_FAKE'}]}})\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PCX_LSP_COMMAND"] = f"{sys.executable} {fake}"
            result = subprocess.run(
                [sys.executable, str(PCX), "lsp-check", str(script), "--json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["diagnostics"][0]["code"], "EN_FAKE")

    def test_verify_runs_lsp_check_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "fake_lsp.py"
            script = Path(td) / "good.em"
            script.write_text("int64 main(){ return 1; }\n", encoding="utf-8")
            touched = Path(td) / "lsp-called"
            fake.write_text(
                "import json, pathlib, sys\n"
                f"pathlib.Path({str(touched)!r}).write_text('yes')\n"
                "def send(msg):\n"
                "    body=json.dumps(msg)\n"
                "    sys.stdout.write(f'Content-Length: {len(body)}\\r\\n\\r\\n{body}')\n"
                "    sys.stdout.flush()\n"
                "while True:\n"
                "    line=sys.stdin.readline()\n"
                "    if not line:\n"
                "        break\n"
                "    if not line.lower().startswith('content-length:'):\n"
                "        continue\n"
                "    n=int(line.split(':',1)[1])\n"
                "    sys.stdin.readline()\n"
                "    msg=json.loads(sys.stdin.read(n))\n"
                "    if msg.get('method') == 'initialize':\n"
                "        send({'jsonrpc':'2.0','id':msg['id'],'result':{'capabilities':{}}})\n"
                "    elif msg.get('method') == 'textDocument/didOpen':\n"
                "        send({'jsonrpc':'2.0','method':'textDocument/publishDiagnostics','params':{'uri':msg['params']['textDocument']['uri'],'diagnostics':[]}})\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PCX_LSP_COMMAND"] = f"{sys.executable} {fake}"
            result = subprocess.run(
                [sys.executable, str(PCX), "verify", str(script)],
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(touched.exists())
    def test_hallucination_eval_corpus_passes(self) -> None:
        result = subprocess.run([sys.executable, str(HALLUCINATION_EVAL), "--json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)["failed"], 0)


if __name__ == "__main__":
    unittest.main()
