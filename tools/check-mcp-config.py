#!/usr/bin/env python3
"""Keep mcp/perception-mcp-config.json 100% in sync with docs/perception/mcp-api.md.

The Perception MCP server's tool list is the source of truth for "what can an
MCP client call." mcp-api.md is the scraped, drift-checked mirror of that surface
(tools/check-doc-drift.py keeps it synced to docs.perception.cx). This script
ensures the toolkit's client config (`mcp/perception-mcp-config.json`) lists
exactly those tool method names — no stale names, no missing tools, no extras.

Compatibility contract: every name in the config `tools` array MUST appear in
mcp-api.md, and every `process/*` / `system/*` / `script/*` method documented in
mcp-api.md MUST be listed in the config. Drift either way fails CI.

Usage:
    python tools/check-mcp-config.py          # human report, exit 1 on mismatch
    python tools/check-mcp-config.py --check   # same (CI gating)
    python tools/check-mcp-config.py --json    # machine-readable

Stdlib only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG = REPO_ROOT / "mcp" / "perception-mcp-config.json"
DOC = REPO_ROOT / "docs" / "perception" / "mcp-api.md"

METHOD_RE = re.compile(r"`((?:process|system|script)/[a-z_0-9]+)`")


def doc_tools() -> set[str]:
    txt = DOC.read_text(encoding="utf-8", errors="ignore")
    # Cut the "Agent Instructions" footer — it mentions urls, not tools.
    txt = re.split(r"\n#\s*Agent Instructions\b", txt)[0]
    return set(METHOD_RE.findall(txt))


def config_tools() -> set[str]:
    d = json.loads(CONFIG.read_text(encoding="utf-8"))
    out: set[str] = set()
    for srv in d.get("mcpServers", {}).values():
        for t in srv.get("tools", []) or []:
            if isinstance(t, str):
                out.add(t)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 on mismatch (CI)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    if not CONFIG.exists() or not DOC.exists():
        print("ERROR: missing config or mcp-api.md", file=sys.stderr)
        return 2

    doc = doc_tools()
    cfg = config_tools()
    in_cfg_not_doc = sorted(cfg - doc)
    in_doc_not_cfg = sorted(doc - cfg)

    ok = not in_cfg_not_doc and not in_doc_not_cfg
    report = {
        "doc_tools": len(doc),
        "config_tools": len(cfg),
        "in_config_not_in_doc": in_cfg_not_doc,
        "in_doc_not_in_config": in_doc_not_cfg,
        "in_sync": ok,
    }

    if args.json:
        print(json.dumps(report, indent=2))

    if ok:
        print(f"MCP config in sync with mcp-api.md: {len(doc)} tools.")
        return 0

    print("MCP config OUT OF SYNC with docs/perception/mcp-api.md:")
    if in_cfg_not_doc:
        print(f"  in config but NOT in mcp-api.md ({len(in_cfg_not_doc)}):")
        for t in in_cfg_not_doc:
            print(f"    + {t}")
    if in_doc_not_cfg:
        print(f"  in mcp-api.md but NOT in config ({len(in_doc_not_cfg)}):")
        for t in in_doc_not_cfg:
            print(f"    - {t}")
    print("Fix: update mcp/perception-mcp-config.json `tools` to match mcp-api.md,")
    print("then regenerate docs/COUNTS.json (python tools/build-counts.py).")
    return 1 if args.check or not args.json else 0


if __name__ == "__main__":
    sys.exit(main())