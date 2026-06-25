#!/usr/bin/env python3
"""Operate a Perception MCP session with transcript recording."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from perception_mcp_client import PerceptionMcpClient, Transcript, normalize_hex  # noqa: E402

STATE = Path(".pcx-mcp-session.json")


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(data: dict) -> None:
    STATE.write_text(json.dumps(data, indent=2) + "\n")


def client_from(args: argparse.Namespace) -> PerceptionMcpClient:
    state = load_state()
    url = getattr(args, "url", None) or state.get("url")
    if not url:
        raise SystemExit("missing --url and no session state")
    target = getattr(args, "target", None) or state.get("target", "")
    transcript = Transcript(Path(getattr(args, "transcript", "") or state.get("transcript", "")) if (getattr(args, "transcript", "") or state.get("transcript")) else None, target, state.get("handle", ""))
    c = PerceptionMcpClient(url, target, transcript)
    c.handle = state.get("handle", "")
    return c


def cmd_start(args: argparse.Namespace) -> int:
    c = client_from(args)
    handle = c.start()
    save_state({"url": args.url, "target": args.target, "handle": handle, "transcript": args.transcript})
    print(json.dumps({"target": args.target, "handle": handle}, indent=2))
    return 0


def parse_kv(items: list[str]) -> dict:
    out = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"expected key=value: {item}")
        k, v = item.split("=", 1)
        if k in {"address", "base_address", "start", "module_base", "handle"}:
            v = normalize_hex(v)
        out[k.replace("-", "_")] = v
    return out


def cmd_call(args: argparse.Namespace) -> int:
    c = client_from(args)
    params = parse_kv(args.params)
    if c.handle and "handle" not in params and args.tool.startswith("process/") and args.tool not in {"process/list", "process/reference_by_name", "process/reference_by_pid", "process/info_by_name", "process/info_by_pid", "process/cleanup_references", "process/list_references"}:
        params["handle"] = c.handle
    result = c.call_tool(args.tool, params)
    save_state({**load_state(), "handle": c.handle})
    print(json.dumps(result, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    print(json.dumps(load_state(), indent=2))
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    c = client_from(args)
    c.cleanup()
    if STATE.exists():
        STATE.unlink()
    print("cleaned")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="pcx mcp-session")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("start"); p.add_argument("--url", required=True); p.add_argument("--target", required=True); p.add_argument("--transcript", default="mcp-session.jsonl"); p.set_defaults(func=cmd_start)
    p = sub.add_parser("call"); p.add_argument("tool"); p.add_argument("params", nargs="*"); p.add_argument("--url"); p.add_argument("--target"); p.add_argument("--transcript", default=""); p.set_defaults(func=cmd_call)
    p = sub.add_parser("status"); p.set_defaults(func=cmd_status)
    p = sub.add_parser("cleanup"); p.add_argument("--url"); p.add_argument("--target"); p.add_argument("--transcript", default=""); p.set_defaults(func=cmd_cleanup)
    args = ap.parse_args()
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
