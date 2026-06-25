#!/usr/bin/env python3
# mypy: ignore-errors
"""Perception MCP health checks."""
from __future__ import annotations

import argparse, json, sys, time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from perception_mcp_client import PerceptionMcpClient  # noqa: E402

EXPECTED_MIN = 59
CORE = {"script/get_context", "script/validate", "process/list", "process/reference_by_name", "process/dereference"}

def is_hex(v: Any) -> bool:
    return isinstance(v, str) and v.startswith("0x") and all(c in "0123456789abcdefABCDEF" for c in v[2:])

def add(checks, name, ok, **extra): checks.append({"check": name, "ok": bool(ok), **extra})

def main() -> int:
    ap = argparse.ArgumentParser(prog="pcx mcp-doctor")
    ap.add_argument("--url", default="http://127.0.0.1:42069/mcp"); ap.add_argument("--target", default=""); ap.add_argument("--deep", action="store_true"); ap.add_argument("--latency-ms", type=float, default=2000)
    args = ap.parse_args(); c = PerceptionMcpClient(args.url, args.target); checks=[]; names=set(); start=time.perf_counter()
    try:
        init = c.rpc("initialize", {"protocolVersion":"2024-11-05", "capabilities":{}, "clientInfo":{"name":"pcx-doctor","version":"1"}}); add(checks, "initialize works", "error" not in init)
        listed = c.rpc("tools/list", {}); elapsed=(time.perf_counter()-start)*1000
        names = {t.get("name") for t in listed.get("result", {}).get("tools", [])} if isinstance(listed.get("result"), dict) else set()
        add(checks, "server reachable", True); add(checks, "tools/list works", "error" not in listed, tools_seen=len(names)); add(checks, "expected Perception tools available", len(names) >= EXPECTED_MIN or CORE <= names, tools_seen=len(names), expected=EXPECTED_MIN)
        add(checks, "latency under threshold", elapsed <= args.latency_ms, elapsed_ms=round(elapsed,3), threshold_ms=args.latency_ms)
        for tool in ("process/list", "script/get_context"):
            r = c.call_tool(tool, {}); add(checks, f"{tool} works", r is not None)
        r = c.call_tool("script/validate", {"source":"void main() {}"}); add(checks, "script/validate minimal Enma works", r is not None)
        if args.deep and args.target:
            ref = c.call_tool("process/reference_by_name", {"name": args.target}); handle = ref.get("handle") if isinstance(ref, dict) else str(ref)
            c.handle = handle; add(checks, "process/reference_by_name works", is_hex(handle), handle=handle)
            add(checks, "returned handles are hex strings", is_hex(handle))
            deref = c.call_tool("process/dereference", {"handle": handle}, retry_stale=False); add(checks, "process/dereference cleanup works", deref is not None)
            try:
                c.call_tool("process/read_typed_value", {"handle": handle, "address":"0x1", "type":"u32"}, retry_stale=False)
                add(checks, "stale-handle errors are well-formed", False, error="call unexpectedly succeeded")
            except Exception as exc:
                add(checks, "stale-handle errors are well-formed", "-32002" in str(exc))
    except Exception as exc:
        add(checks, "server reachable", False, error=str(exc))
    ok = all(x["ok"] for x in checks)
    print(json.dumps({"ok": ok, "url": args.url, "checks": checks}, indent=2)); return 0 if ok else 1
if __name__ == "__main__": raise SystemExit(main())
