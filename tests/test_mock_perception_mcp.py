import json
import socket
import subprocess
import sys
import time
import unittest
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MOCK = REPO_ROOT / "tools" / "mock-perception-mcp.py"
PCX = REPO_ROOT / "tools" / "pcx.py"


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close(); return port


class MockPerceptionMcpTest(unittest.TestCase):
    def setUp(self):
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}/mcp"
        self.proc = subprocess.Popen([sys.executable, str(MOCK), "--port", str(self.port)], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                self.rpc("tools/list", {})
                return
            except Exception:
                time.sleep(0.05)
        self.fail("mock MCP server did not start")

    def tearDown(self):
        self.proc.terminate(); self.proc.wait(timeout=5)

    def rpc(self, method, params):
        req = urllib.request.Request(self.url, data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(), headers={"content-type":"application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=5).read().decode())

    def test_mock_serves_core_tools_and_errors(self):
        tools = self.rpc("tools/list", {})["result"]["tools"]
        names = {t["name"] for t in tools}
        self.assertIn("process/read_typed_value", names)
        self.assertIn("process/generate_signature", names)
        self.assertIn("process/read_rtti", names)
        ok = self.rpc("tools/call", {"name":"process/reference_by_name", "arguments":{"name":"game.exe"}})
        self.assertEqual(ok["result"]["handle"], "0x1000")
        sig = self.rpc("tools/call", {"name":"process/generate_signature", "arguments":{"handle":"0x1000", "address":"0x401200"}})
        self.assertTrue(sig["result"]["unique"])
        denied = self.rpc("tools/call", {"name":"process/write_virtual_memory", "arguments":{"handle":"0x1000", "address":"0x401200", "bytes":"90"}})
        self.assertEqual(denied["error"]["code"], -32001)
        stale = self.rpc("tools/call", {"name":"process/read_typed_value", "arguments":{"handle":"0xdead", "address":"0x401000", "type":"u32"}})
        self.assertEqual(stale["error"]["code"], -32002)

    def test_doctor_record_replay_session_against_mock(self):
        out = REPO_ROOT / "tmp-mock-session.jsonl"
        if out.exists(): out.unlink()
        doctor = subprocess.run([sys.executable, str(PCX), "mcp-doctor", "--url", self.url, "--target", "game.exe", "--deep", "--latency-ms", "5000"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
        record = subprocess.run([sys.executable, str(PCX), "mcp-record", "--url", self.url, "--target", "game.exe", "--out", str(out)], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(record.returncode, 0, record.stdout + record.stderr)
        rows = [json.loads(line) for line in out.read_text().splitlines()]
        self.assertTrue(rows)
        self.assertIn("bytes_in", rows[0]); self.assertIn("bytes_out", rows[0]); self.assertIn("session_id", rows[0])
        replay = subprocess.run([sys.executable, str(PCX), "mcp-replay", str(out), "--url", self.url, "--compare"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
        self.assertTrue(json.loads(replay.stdout)["ok"])
        out.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
