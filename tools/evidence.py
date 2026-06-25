#!/usr/bin/env python3
# mypy: ignore-errors
"""Evidence graph CLI for RE claims."""
from __future__ import annotations

import argparse, json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA = "pcx-evidence-graph-v1"
KNOWN_TOOLS = {r["name"] for r in json.loads((Path(__file__).resolve().parent.parent / "docs/perception/mcp-tool-schemas.json").read_text()).get("tools", [])}
TYPE_MAP = {"process/find_string_refs":"string_xref", "process/find_all_patterns":"unique_signature", "process/read_pointer_chain":"pointer_chain_validation", "process/is_valid_address":"address_validation", "process/disassemble":"disassembly_context"}

def load(path: Path) -> dict[str, Any]:
    if not path.exists(): raise SystemExit(f"missing evidence graph: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict): raise SystemExit(f"invalid evidence graph: {path}")
    return data

def save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

def next_id(rows: list[dict[str, Any]], prefix: str) -> str:
    nums = [int(r["id"].split("-")[1]) for r in rows if str(r.get("id", "")).startswith(prefix + "-")]
    return f"{prefix}-{(max(nums) if nums else 0) + 1:03d}"

def cmd_init(args):
    save(args.file, {"schema": SCHEMA, "target": {"process": args.process, "module": args.module, "build": args.build, "hash": args.hash}, "claims": [], "evidence": []}); print(args.file); return 0

def cmd_add_claim(args):
    data=load(args.file); cid=args.id or next_id(data.setdefault("claims", []), "C"); row={"id":cid,"claim":args.claim,"status":args.status,"evidence":args.evidence}
    if args.reason: row["reason"] = args.reason
    data["claims"].append(row); save(args.file,data); print(cid); return 0

def cmd_add_mcp_result(args):
    data=load(args.file); eid=args.id or next_id(data.setdefault("evidence", []), "E")
    row={"id":eid,"type":args.type,"tool":args.tool,"params":json.loads(args.params),"result":json.loads(args.result),"error":json.loads(args.error) if args.error else None,"ts":datetime.now(UTC).isoformat(),"elapsed_ms":args.elapsed_ms}
    data["evidence"].append(row)
    if args.claim:
        for claim in data.get("claims", []):
            if claim.get("id") == args.claim and eid not in claim.setdefault("evidence", []): claim["evidence"].append(eid)
    save(args.file,data); print(eid); return 0

def cmd_verify(args):
    data=load(args.file); problems=[]; claim_ids=[c.get("id") for c in data.get("claims", [])]; ev_ids=[e.get("id") for e in data.get("evidence", [])]
    dup_claims=sorted({x for x in claim_ids if claim_ids.count(x)>1}); dup_ev=sorted({x for x in ev_ids if ev_ids.count(x)>1}); ev_set=set(ev_ids)
    missing=[(c.get("id"), e) for c in data.get("claims", []) for e in c.get("evidence", []) if e not in ev_set]
    referenced={e for c in data.get("claims", []) for e in c.get("evidence", [])}; orphan=sorted(ev_set-referenced) if not args.allow_orphan_evidence else []
    claim_errors=[]
    for c in data.get("claims", []):
        if c.get("status") == "confirmed" and len(c.get("evidence", [])) < 2: claim_errors.append([c.get("id"), "confirmed claims need at least two evidence entries"])
        if c.get("status") == "rejected" and not c.get("reason"): claim_errors.append([c.get("id"), "rejected claims need reason"])
        if c.get("status") == "stale" and not (c.get("stale_date") and c.get("reason")): claim_errors.append([c.get("id"), "stale claims need stale_date and reason"])
    evidence_errors=[]
    for e in data.get("evidence", []):
        if e.get("tool") not in KNOWN_TOOLS: evidence_errors.append([e.get("id"), "unknown MCP tool", e.get("tool")])
        if "params" not in e or not ("result" in e or "error" in e): evidence_errors.append([e.get("id"), "MCP evidence needs tool/params/result or error"])
    ok = data.get("schema") == SCHEMA and not (dup_claims or dup_ev or missing or orphan or claim_errors or evidence_errors)
    print(json.dumps({"ok": ok, "claims": len(claim_ids), "evidence": len(ev_ids), "duplicate_claim_ids": dup_claims, "duplicate_evidence_ids": dup_ev, "missing_references": missing, "orphan_evidence": orphan, "claim_errors": claim_errors, "evidence_errors": evidence_errors}, indent=2)); return 0 if ok else 1

def cmd_import_transcript(args):
    rows=[json.loads(line) for line in args.transcript.read_text().splitlines() if line.strip()]
    target=(rows[0].get("target") if rows else "") or args.target
    data={"schema": SCHEMA, "target": {"process": target}, "claims": [{"id": args.claim, "claim": args.claim_text or f"Evidence imported from {args.transcript.name}", "status": "candidate", "evidence": []}], "evidence": []}
    for i,row in enumerate(rows, 1):
        eid=f"E-{i:03d}"; tool=row.get("tool", "")
        ev={"id":eid,"type":TYPE_MAP.get(tool, "mcp_call"),"tool":tool,"params":row.get("params") or {},"result":row.get("result") or {},"error":row.get("error"),"ts":row.get("ts") or datetime.now(UTC).isoformat(),"elapsed_ms":float(row.get("elapsed_ms") or 0)}
        data["evidence"].append(ev); data["claims"][0]["evidence"].append(eid)
    save(args.out, data); print(args.out); return 0

def cmd_stale(args):
    data=load(args.file); cutoff=datetime.now(UTC)-timedelta(days=args.max_age_days); stale=[]
    for e in data.get("evidence", []):
        ts=e.get("ts")
        try:
            if not ts or datetime.fromisoformat(ts.replace("Z", "+00:00")) < cutoff: stale.append(e.get("id"))
        except ValueError: stale.append(e.get("id"))
    print(json.dumps({"stale": stale}, indent=2)); return 1 if stale else 0

def render_mermaid(data):
    lines=["graph TD"]
    for c in data.get("claims", []):
        cid=c["id"].replace("-", "_")
        lines.append(f"  {cid}[\"{c['id']}: {c['claim']}\"]")
        for eid in c.get("evidence", []): lines.append(f"  {cid} --> {eid.replace('-', '_')}")
    for e in data.get("evidence", []): lines.append(f"  {e['id'].replace('-', '_')}[\"{e['id']}: {e['type']}\"]")
    return "\n".join(lines)

def cmd_graph(args):
    data=load(args.file)
    mermaid=render_mermaid(data)
    if args.format == "mermaid":
        print(mermaid); return 0
    if args.format == "html":
        print("<html><body><pre class=\"mermaid\">" + mermaid.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;") + "</pre></body></html>"); return 0
    raise SystemExit("--format must be mermaid or html")

def main():
    ap=argparse.ArgumentParser(prog="pcx evidence"); ap.add_argument("--file", type=Path, default=Path("evidence.json")); sub=ap.add_subparsers(dest="cmd", required=True)
    p=sub.add_parser("init"); p.add_argument("--process", required=True); p.add_argument("--module", default=""); p.add_argument("--build", default="unknown"); p.add_argument("--hash", default=""); p.set_defaults(func=cmd_init)
    p=sub.add_parser("add-claim"); p.add_argument("claim"); p.add_argument("--id"); p.add_argument("--status", default="candidate"); p.add_argument("--evidence", nargs="*", default=[]); p.add_argument("--reason"); p.set_defaults(func=cmd_add_claim)
    p=sub.add_parser("add-mcp-result"); p.add_argument("--tool", required=True); p.add_argument("--type", required=True); p.add_argument("--params", default="{}"); p.add_argument("--result", default="{}"); p.add_argument("--error"); p.add_argument("--elapsed-ms", type=float, default=0); p.add_argument("--claim"); p.add_argument("--id"); p.set_defaults(func=cmd_add_mcp_result)
    p=sub.add_parser("verify"); p.add_argument("--allow-orphan-evidence", action="store_true"); p.set_defaults(func=cmd_verify)
    p=sub.add_parser("import-transcript"); p.add_argument("transcript", type=Path); p.add_argument("--claim", required=True); p.add_argument("--out", type=Path, required=True); p.add_argument("--target", default=""); p.add_argument("--claim-text", default=""); p.set_defaults(func=cmd_import_transcript)
    p=sub.add_parser("stale"); p.add_argument("--max-age-days", type=int, default=30); p.set_defaults(func=cmd_stale)
    p=sub.add_parser("graph"); p.add_argument("--format", default="mermaid"); p.set_defaults(func=cmd_graph)
    args=ap.parse_args(); return int(args.func(args))
if __name__ == "__main__": raise SystemExit(main())
