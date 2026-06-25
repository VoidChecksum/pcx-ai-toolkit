#!/usr/bin/env python3
# mypy: ignore-errors
"""Small deterministic Perception MCP mock server for CI and examples."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures" / "perception_mcp"
CORE_TOOLS = [
    "tools/list", "process/list", "process/reference_by_name", "process/get_module_by_name", "process/is_valid_address",
    "process/read_typed_value", "process/find_string_refs", "process/find_function_bounds", "process/disassemble",
    "process/dereference", "script/get_context", "script/validate",
]
ERR = {
    "permission": {"code": -32001, "message": "permission denied", "data": {"permission": "read_memory"}},
    "stale": {"code": -32002, "message": "stale handle", "data": {"handle": "expired"}},
    "missing": {"code": -32003, "message": "target not found"},
    "failed": {"code": -32004, "message": "operation failed"},
}

class State:
    def __init__(self):
        self.proc = json.loads((FIX / "mock_processes.json").read_text())
        self.mem = json.loads((FIX / "mock_memory.json").read_text())
        self.live_handles = {p["handle"] for p in self.proc["processes"]}

    def call(self, name: str, args: dict[str, Any]) -> Any:
        if name == "process/list":
            return {"processes": self.proc["processes"]}
        if name == "process/reference_by_name":
            target = args.get("name")
            for p in self.proc["processes"]:
                if p["name"] == target:
                    self.live_handles.add(p["handle"]); return {"handle": p["handle"], "pid": p["pid"]}
            raise RpcError(ERR["missing"])
        if name == "process/dereference":
            self.live_handles.discard(args.get("handle")); return {"ok": True}
        if name.startswith("process/") and name not in {"process/list", "process/reference_by_name"}:
            h = args.get("handle")
            if h not in self.live_handles:
                raise RpcError(ERR["stale"])
        if name == "process/get_module_by_name":
            mod = self.proc["modules"][0]; return dict(mod)
        if name == "process/is_valid_address":
            a = int(str(args.get("address", "0")), 16); return {"valid": 0x400000 <= a < 0x500000, "address": hex(a)}
        if name == "process/read_typed_value":
            return {"value": self.mem["values"].get(f"{args.get('address')}:{args.get('type')}", 0), "type": args.get("type")}
        if name == "process/find_string_refs":
            return {"refs": [{"address": a, "text": args.get("text")} for a in self.mem["strings"].get(str(args.get("text")), [])]}
        if name == "process/find_function_bounds":
            return self.mem["functions"].get(str(args.get("address")), {"start": "0x401000", "end": "0x401080"})
        if name == "process/disassemble":
            return {"address": args.get("address", args.get("start", "0x401000")), "instructions": ["push rbp", "mov rbp, rsp", "ret"]}
        if name == "script/get_context":
            return {"language": "Enma", "addons": ["core"], "permissions": ["read_memory"]}
        if name == "script/validate":
            src = str(args.get("source", "")); return {"ok": "syntax_error" not in src, "diagnostics": [] if "syntax_error" not in src else [{"message": "syntax error"}]}
        raise RpcError(ERR["failed"])

class RpcError(Exception):
    def __init__(self, err): self.err = err

state = State()

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("content-length", "0")))
        req = json.loads(raw.decode())
        res = {"jsonrpc": "2.0", "id": req.get("id")}
        try:
            method = req.get("method")
            params = req.get("params") or {}
            if method == "initialize":
                res["result"] = {"protocolVersion": "2024-11-05", "serverInfo": {"name": "mock-perception-mcp"}}
            elif method == "tools/list":
                res["result"] = {"tools": [{"name": t} for t in CORE_TOOLS if t != "tools/list"]}
            elif method == "tools/call":
                res["result"] = state.call(params.get("name", ""), params.get("arguments") or {})
            else:
                raise RpcError(ERR["failed"])
        except RpcError as exc:
            res["error"] = exc.err
        data = json.dumps(res).encode()
        self.send_response(200); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self, *_): pass

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=42069)
    args = ap.parse_args(); ThreadingHTTPServer((args.host, args.port), Handler).serve_forever(); return 0
if __name__ == "__main__": raise SystemExit(main())
