#!/usr/bin/env python3
"""Record/replay/summarize Perception MCP JSONL transcripts."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append(row)
    return rows


def cmd_replay(args: argparse.Namespace) -> int:
    rows = read_rows(args.file)
    for row in rows:
        print(json.dumps({"tool": row.get("tool"), "params": row.get("params"), "would_call": args.dry_run}, sort_keys=True))
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    rows = read_rows(args.file)
    tools = Counter(r.get("tool") for r in rows)
    errors = Counter(str((r.get("error") or {}).get("code", "ok")) for r in rows)
    elapsed = sum(float(r.get("elapsed_ms") or 0) for r in rows)
    print(json.dumps({"calls": len(rows), "tools": tools, "errors": errors, "elapsed_ms": round(elapsed, 3)}, indent=2))
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.touch()
    print(f"recording target file ready: {args.out}")
    print("Use `pcx mcp-session start --transcript ...` for live call capture.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("record"); p.add_argument("--url", required=True); p.add_argument("--out", type=Path, required=True); p.set_defaults(func=cmd_record)
    p = sub.add_parser("replay"); p.add_argument("file", type=Path); p.add_argument("--dry-run", action="store_true"); p.set_defaults(func=cmd_replay)
    p = sub.add_parser("summarize"); p.add_argument("file", type=Path); p.set_defaults(func=cmd_summarize)
    args = ap.parse_args()
    return int(args.func(args))

if __name__ == "__main__":
    raise SystemExit(main())
