#!/usr/bin/env python3
"""Minimal evidence graph CLI for RE claims."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA = "pcx-evidence-graph-v1"


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"missing evidence graph: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"invalid evidence graph: {path}")
    return data


def save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def next_id(rows: list[dict[str, Any]], prefix: str) -> str:
    nums = [int(r["id"].split("-")[1]) for r in rows if str(r.get("id", "")).startswith(prefix + "-")]
    return f"{prefix}-{(max(nums) if nums else 0) + 1:03d}"


def cmd_init(args: argparse.Namespace) -> int:
    data = {"schema": SCHEMA, "target": {"process": args.process, "module": args.module, "build": args.build, "hash": args.hash}, "claims": [], "evidence": []}
    save(args.file, data)
    print(args.file)
    return 0


def cmd_add_claim(args: argparse.Namespace) -> int:
    data = load(args.file)
    cid = args.id or next_id(data.setdefault("claims", []), "C")
    data["claims"].append({"id": cid, "claim": args.claim, "status": args.status, "evidence": args.evidence})
    save(args.file, data)
    print(cid)
    return 0


def cmd_add_mcp_result(args: argparse.Namespace) -> int:
    data = load(args.file)
    eid = args.id or next_id(data.setdefault("evidence", []), "E")
    row = {"id": eid, "type": args.type, "tool": args.tool, "params": json.loads(args.params), "result": json.loads(args.result), "error": json.loads(args.error) if args.error else None, "ts": datetime.now(UTC).isoformat(), "elapsed_ms": args.elapsed_ms}
    data["evidence"].append(row)
    if args.claim:
        for claim in data.get("claims", []):
            if claim.get("id") == args.claim and eid not in claim.setdefault("evidence", []):
                claim["evidence"].append(eid)
    save(args.file, data)
    print(eid)
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    data = load(args.file)
    ok = data.get("schema") == SCHEMA
    ids = {e.get("id") for e in data.get("evidence", [])}
    missing = [(c.get("id"), e) for c in data.get("claims", []) for e in c.get("evidence", []) if e not in ids]
    if missing:
        ok = False
    print(json.dumps({"ok": ok, "claims": len(data.get("claims", [])), "evidence": len(ids), "missing": missing}, indent=2))
    return 0 if ok else 1


def cmd_stale(args: argparse.Namespace) -> int:
    data = load(args.file)
    cutoff = datetime.now(UTC) - timedelta(days=args.max_age_days)
    stale = []
    for e in data.get("evidence", []):
        ts = e.get("ts")
        if not ts:
            stale.append(e.get("id")); continue
        try:
            if datetime.fromisoformat(ts) < cutoff:
                stale.append(e.get("id"))
        except ValueError:
            stale.append(e.get("id"))
    print(json.dumps({"stale": stale}, indent=2))
    return 1 if stale else 0


def cmd_graph(args: argparse.Namespace) -> int:
    data = load(args.file)
    if args.format != "mermaid":
        raise SystemExit("only --format mermaid is supported")
    print("graph TD")
    for c in data.get("claims", []):
        print(f"  {c['id'].replace('-', '_')}[\"{c['id']}: {c['claim']}\"]")
        for eid in c.get("evidence", []):
            print(f"  {c['id'].replace('-', '_')} --> {eid.replace('-', '_')}")
    for e in data.get("evidence", []):
        print(f"  {e['id'].replace('-', '_')}[\"{e['id']}: {e['type']}\"]")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="pcx evidence")
    ap.add_argument("--file", type=Path, default=Path("evidence.json"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--process", required=True); p.add_argument("--module", default=""); p.add_argument("--build", default="unknown"); p.add_argument("--hash", default=""); p.set_defaults(func=cmd_init)
    p = sub.add_parser("add-claim"); p.add_argument("claim"); p.add_argument("--id"); p.add_argument("--status", default="candidate"); p.add_argument("--evidence", nargs="*", default=[]); p.set_defaults(func=cmd_add_claim)
    p = sub.add_parser("add-mcp-result"); p.add_argument("--tool", required=True); p.add_argument("--type", required=True); p.add_argument("--params", default="{}"); p.add_argument("--result", default="{}"); p.add_argument("--error"); p.add_argument("--elapsed-ms", type=float, default=0); p.add_argument("--claim"); p.add_argument("--id"); p.set_defaults(func=cmd_add_mcp_result)
    p = sub.add_parser("verify"); p.set_defaults(func=cmd_verify)
    p = sub.add_parser("stale"); p.add_argument("--max-age-days", type=int, default=30); p.set_defaults(func=cmd_stale)
    p = sub.add_parser("graph"); p.add_argument("--format", default="mermaid"); p.set_defaults(func=cmd_graph)
    args = ap.parse_args()
    return int(args.func(args))

if __name__ == "__main__":
    raise SystemExit(main())
