#!/usr/bin/env python3
"""Build docs/COUNTS.json — the single source of truth for README badge numbers.

Every hard-coded count in the README ("110 pages", "35,000+ lines", "MCP Tools 42+",
"AI Skills 23", …) is a drift hazard: someone adds a doc and the badge lies. This
script computes the real numbers from the tree and writes them to a JSON file that
the README's dynamic shields.io badges read from. CI runs `--check` so a committed
COUNTS.json that disagrees with the tree fails the build.

Counts:
  docs        source doc pages under docs/ (excludes INDEX.md and llms-* bundles)
  doc_lines   total lines across those pages
  mcp_tools   length of the `tools` array in mcp/perception-mcp-config.json
  skills      count of .claude/skills/*/SKILL.md
  knowledge   count of knowledge/*.md
  templates   count of starter scripts under templates/ (*.em, *.as, *.lua + scaffold files)
  tools       count of standalone tools/*.py + tools/*.sh (excludes lib/, pe-parser/)
  signatures  count of signature files under signatures/**/*.md
  engines     count of knowledge/engine-*.md references

Usage:
    python tools/build-counts.py             # write docs/COUNTS.json
    python tools/build-counts.py --check     # exit 1 if committed file drifts

Stdlib only.
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "docs" / "COUNTS.json"


def source_docs() -> list[Path]:
    """Mirror the CI doc-count definition exactly:
    all docs/**/*.md except INDEX.md and the generated bundles directly under
    docs/ whose names start with llms- (docs/llms-full.txt etc.). Note this
    INCLUDES docs/enma/llms-language.md and llms-sdk.md — those are real scraped
    single-page references, not generated bundles, so they count as source docs."""
    out = []
    for p in (REPO_ROOT / "docs").rglob("*.md"):
        if p.name == "INDEX.md":
            continue
        # Exclude only the generated bundles sitting directly under docs/.
        if p.parent == (REPO_ROOT / "docs") and p.name.startswith("llms-"):
            continue
        out.append(p)
    return sorted(out)

def count_lines(paths: list[Path]) -> int:
    n = 0
    for p in paths:
        try:
            n += sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return n


def mcp_tool_count() -> int:
    cfg = REPO_ROOT / "mcp" / "perception-mcp-config.json"
    if not cfg.exists():
        return 0
    d = json.loads(cfg.read_text(encoding="utf-8"))
    total = 0
    for srv in d.get("mcpServers", {}).values():
        tools = srv.get("tools", [])
        if isinstance(tools, list):
            total += len(tools)
    return total


def build() -> dict:
    docs = source_docs()
    skills = sorted((REPO_ROOT / ".claude" / "skills").glob("*/SKILL.md"))
    knowledge = sorted((REPO_ROOT / "knowledge").glob("*.md"))
    templates = sorted((REPO_ROOT / "templates").rglob("*"))
    templates = [p for p in templates if p.is_file() and p.suffix in {".em", ".as", ".lua", ".md"} and p.name != "README.md"]
    tools = [p for p in (REPO_ROOT / "tools").iterdir() if p.is_file() and (p.suffix in {".py", ".sh"} or p.name == "pcx")]
    sigs = sorted((REPO_ROOT / "signatures").rglob("*.md"))
    engines = sorted((REPO_ROOT / "knowledge").glob("engine-*.md"))
    return {
        "docs": len(docs),
        "doc_lines": count_lines(docs),
        "mcp_tools": mcp_tool_count(),
        "skills": len(skills),
        "knowledge": len(knowledge),
        "templates": len(templates),
        "tools": len(tools),
        "signatures": len(sigs),
        "engines": len(engines),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the committed COUNTS.json differs from the live tree")
    args = ap.parse_args()

    data = build()
    if args.check:
        if not OUT.exists():
            print("COUNTS.json missing — run: python tools/build-counts.py")
            return 1
        existing = json.loads(OUT.read_text(encoding="utf-8"))
        if existing != data:
            print("COUNTS.json out of sync with the tree. Regenerate:")
            print("  python tools/build-counts.py")
            print(f"  committed: {existing}")
            print(f"  live:      {data}")
            return 1
        print(f"COUNTS.json in sync: {data}")
        return 0

    OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO_ROOT)}:")
    for k, v in data.items():
        print(f"  {k:12} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())