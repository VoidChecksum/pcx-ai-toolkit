"""Tiny JSON-RPC client helpers for Perception MCP automation."""
from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


WRITE_TOOLS = {"process/write_virtual_memory", "process/write_typed_value", "process/write_string", "process/copy_memory", "process/fill_memory", "process/allocate_memory"}


def normalize_hex(value: str) -> str:
    text = str(value).strip()
    if text.startswith("0x"):
        return "0x" + text[2:].lower()
    if text.isdigit():
        return hex(int(text))
    return text


@dataclass
class Transcript:
    path: Path | None = None
    target: str = ""
    handle: str = ""

    def write(self, tool: str, params: dict[str, Any], result: Any, error: Any, elapsed_ms: float) -> None:
        if not self.path:
            return
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tool": tool, "params": params, "result": result, "error": error, "elapsed_ms": round(elapsed_ms, 3), "handle": self.handle, "target": self.target}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


@dataclass
class PerceptionMcpClient:
    url: str
    target: str = ""
    transcript: Transcript = field(default_factory=Transcript)
    rpc_id: int = 0
    handle: str = ""

    def rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.rpc_id += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self.rpc_id, "method": method, "params": params}).encode()
        req = urllib.request.Request(self.url, data=payload, headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())

    def call_tool(self, tool: str, arguments: dict[str, Any] | None = None, retry_stale: bool = True) -> Any:
        args = dict(arguments or {})
        if self.handle and "handle" in args:
            args["handle"] = normalize_hex(args["handle"])
        if tool in WRITE_TOOLS:
            raise PermissionError(f"{tool} requires explicit write permission; use documented rollback workflow")
        start = time.perf_counter()
        result = None; error = None
        try:
            response = self.rpc("tools/call", {"name": tool, "arguments": args})
            if "error" in response:
                error = response["error"]
                if retry_stale and str(error.get("code")) == "-32002" and self.target:
                    self.start()
                    args["handle"] = self.handle
                    return self.call_tool(tool, args, retry_stale=False)
                raise RuntimeError(json.dumps(error))
            result = response.get("result")
            return result
        finally:
            self.transcript.write(tool, args, result, error, (time.perf_counter() - start) * 1000)

    def start(self) -> str:
        result = self.call_tool("process/reference_by_name", {"name": self.target}, retry_stale=False)
        if isinstance(result, dict):
            self.handle = normalize_hex(result.get("handle") or result.get("content", [{}])[0].get("text", ""))
        else:
            self.handle = normalize_hex(str(result))
        self.transcript.handle = self.handle
        self.transcript.target = self.target
        return self.handle

    def cleanup(self) -> None:
        if self.handle:
            try:
                self.call_tool("process/dereference", {"handle": self.handle}, retry_stale=False)
            finally:
                self.handle = ""
        else:
            self.call_tool("process/cleanup_references", {}, retry_stale=False)
