#!/usr/bin/env python3
# mypy: ignore-errors
"""Record, replay, and summarize Perception MCP JSONL transcripts."""
from __future__ import annotations

import argparse, json, sys, time
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from perception_mcp_client import PerceptionMcpClient, Transcript, NO_AUTO_HANDLE  # noqa: E402


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if isinstance(row, dict): rows.append(row)
    return rows


def _call(c: PerceptionMcpClient, tool: str, params: dict[str, Any]) -> Any:
    if c.handle and tool.startswith("process/") and tool not in NO_AUTO_HANDLE and "handle" not in params:
        params = {**params, "handle": c.handle}
    return c.call_tool(tool, params)


def cmd_record(args: argparse.Namespace) -> int:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    transcript = Transcript(args.out, args.target or "")
    c = PerceptionMcpClient(args.url, args.target or "", transcript)
    if args.stdin:
        for line in sys.stdin:
            if not line.strip(): continue
            row = json.loads(line)
            _call(c, row["tool"], row.get("params") or {})
    elif args.follow:
        state = json.loads(args.follow.read_text())
        src = Path(state.get("transcript", ""))
        if not src.exists(): raise SystemExit(f"missing followed transcript: {src}")
        args.out.write_text(src.read_text())
    else:
        c.start()
        _call(c, "process/list", {})
        _call(c, "script/get_context", {})
        c.cleanup()
    print(json.dumps({"out": str(args.out), "calls": len(read_rows(args.out))}, indent=2))
    return 0


def result_shape(value: Any) -> str:
    if isinstance(value, dict): return "object:" + ",".join(sorted(value.keys()))
    if isinstance(value, list): return "array"
    return type(value).__name__


def cmd_replay(args: argparse.Namespace) -> int:
    rows = read_rows(args.file)
    if args.dry_run:
        for row in rows:
            print(json.dumps({"tool": row.get("tool"), "params": row.get("params"), "would_call": True}, sort_keys=True))
        return 0
    if args.mock:
        print(json.dumps({"ok": True, "mode": "mock", "calls": len(rows), "tools": [r.get("tool") for r in rows]}, indent=2))
        return 0
    if not args.url: raise SystemExit("--url required unless --dry-run or --mock")
    c = PerceptionMcpClient(args.url)
    comparisons = []
    ok = True
    for row in rows:
        tool = row.get("tool"); params = row.get("params") or {}
        start = time.perf_counter(); error = None; result = None
        try:
            result = _call(c, tool, dict(params))
        except Exception as exc:
            error = str(exc)
        elapsed = (time.perf_counter() - start) * 1000
        if args.compare:
            same_error = (row.get("error") is None) == (error is None)
            shape_ok = error is not None or result_shape(result) == result_shape(row.get("result")) or row.get("result") is None
            delta = elapsed - float(row.get("elapsed_ms") or 0)
            item = {"tool": tool, "same_error_state": same_error, "shape_compatible": shape_ok, "elapsed_delta_ms": round(delta, 3)}
            comparisons.append(item); ok = ok and same_error and shape_ok
    print(json.dumps({"ok": ok, "calls": len(rows), "compare": comparisons}, indent=2))
    return 0 if ok else 1


def cmd_summarize(args: argparse.Namespace) -> int:
    rows = read_rows(args.file)
    tools = Counter(r.get("tool") for r in rows)
    errors = Counter(str((r.get("error") or {}).get("code", "ok")) if isinstance(r.get("error"), dict) else str(r.get("error") or "ok") for r in rows)
    elapsed = sum(float(r.get("elapsed_ms") or 0) for r in rows)
    print(json.dumps({"calls": len(rows), "tools": dict(tools), "errors": dict(errors), "elapsed_ms": round(elapsed, 3)}, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("record"); p.add_argument("--url", default="http://127.0.0.1:42069/mcp"); p.add_argument("--target", default=""); p.add_argument("--out", type=Path, required=True); p.add_argument("--follow", type=Path); p.add_argument("--stdin", action="store_true"); p.set_defaults(func=cmd_record)
    p = sub.add_parser("replay"); p.add_argument("file", type=Path); p.add_argument("--dry-run", action="store_true"); p.add_argument("--mock", action="store_true"); p.add_argument("--url"); p.add_argument("--compare", action="store_true"); p.set_defaults(func=cmd_replay)
    p = sub.add_parser("summarize"); p.add_argument("file", type=Path); p.set_defaults(func=cmd_summarize)
    args = ap.parse_args(); return int(args.func(args))
if __name__ == "__main__": raise SystemExit(main())
