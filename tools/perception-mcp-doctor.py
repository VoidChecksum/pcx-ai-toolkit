#!/usr/bin/env python3
"""Perception MCP health checks."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from perception_mcp_client import PerceptionMcpClient  # noqa: E402

EXPECTED = {"tools/list", "script/get_context", "script/validate", "process/list"}


def main() -> int:
    ap = argparse.ArgumentParser(prog="pcx mcp-doctor")
    ap.add_argument("--url", default="http://127.0.0.1:42069/mcp")
    ap.add_argument("--latency-ms", type=float, default=2000)
    args = ap.parse_args()
    c = PerceptionMcpClient(args.url)
    checks = []
    start = time.perf_counter()
    try:
        tools = c.rpc("tools/list", {})
        elapsed = (time.perf_counter() - start) * 1000
        names = {t.get("name") for t in tools.get("result", {}).get("tools", [])} if isinstance(tools.get("result"), dict) else set()
        checks.append({"check": "tools/list", "ok": "error" not in tools, "elapsed_ms": round(elapsed, 3)})
        checks.append({"check": "expected tools", "ok": not names or bool(EXPECTED & names), "tools_seen": len(names)})
        checks.append({"check": "latency", "ok": elapsed <= args.latency_ms, "threshold_ms": args.latency_ms})
    except Exception as exc:
        checks.append({"check": "server reachable", "ok": False, "error": str(exc)})
    ok = all(c["ok"] for c in checks)
    print(json.dumps({"ok": ok, "url": args.url, "checks": checks}, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
