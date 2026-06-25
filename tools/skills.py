#!/usr/bin/env python3
"""Lint and recommend bundled pcx-ai-toolkit skills."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / ".claude" / "skills"
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
REQUIRED_PHRASES = ["trigger", "required input", "output contract", "stop condition", "validation"]


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    key: str | None = None
    for raw in text[4:end].splitlines():
        if not raw.strip():
            continue
        if raw.startswith(" ") and key:
            data[key] = (data[key] + " " + raw.strip()).strip()
            continue
        if ":" in raw:
            key, value = raw.split(":", 1)
            key = key.strip()
            data[key] = value.strip().strip('"').strip("'").strip(">")
    return data


def skill_files() -> list[Path]:
    return sorted(SKILL_ROOT.glob("*/SKILL.md"))


def skill_record(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    fm = parse_frontmatter(text)
    return {
        "name": fm.get("name") or path.parent.name,
        "description": fm.get("description", ""),
        "path": str(path.relative_to(REPO_ROOT)),
        "text": text,
    }


def lint() -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for path in skill_files():
        rec = skill_record(path)
        text = rec["text"]
        low = text.lower()
        if rec["name"] != path.parent.name:
            findings.append({"skill": path.parent.name, "kind": "frontmatter_name", "message": "frontmatter name must match directory"})
        if not rec["description"]:
            findings.append({"skill": path.parent.name, "kind": "frontmatter_description", "message": "missing description"})
        for phrase in REQUIRED_PHRASES:
            if phrase not in low:
                findings.append({"skill": rec["name"], "kind": "missing_contract", "message": f"missing phrase: {phrase}"})
        if not re.search(r"`(?:docs|knowledge|\.claude|tools|mcp)/[^`]+`", text):
            findings.append({"skill": rec["name"], "kind": "missing_link", "message": "missing linked repo doc/tool path"})
    return {"ok": not findings, "skills": len(skill_files()), "findings": findings}


def recommend(task: str, limit: int = 5) -> dict[str, Any]:
    q = set(t.lower() for t in TOKEN_RE.findall(task))
    rows: list[tuple[int, dict[str, Any]]] = []
    for path in skill_files():
        rec = skill_record(path)
        hay = f"{rec['name']} {rec['description']} {rec['text']}".lower()
        tokens = set(TOKEN_RE.findall(hay))
        score = len(q & tokens) * 3 + sum(2 for token in q if token in rec["name"].lower())
        if score:
            rows.append((score, {"name": rec["name"], "path": rec["path"], "description": rec["description"], "score": score}))
    rows.sort(key=lambda item: item[0], reverse=True)
    selected = [row for _, row in rows[: max(1, min(limit, 20))]]
    docs = ["docs/llms.txt", "docs/NAVIGATION.md"]
    tools = ["pcx skills lint", "pcx knowledge search"]
    if any(word in task.lower() for word in ("mcp", "perception")):
        docs.append("docs/perception/mcp-tool-reference.md")
        tools.append("pcx mcp-plan")
    if any(word in task.lower() for word in ("reverse", "devirtual", "vmprotect", "themida", "obfusc")):
        docs.extend(["knowledge/re-workflows/devirtualization-generic.md", "knowledge/vmprotect2-analysis.md"])
        tools.append("pcx re-plan")
    return {"task": task, "skills": selected, "docs": list(dict.fromkeys(docs)), "commands": tools}


def main() -> int:
    ap = argparse.ArgumentParser(prog="pcx skills", description="Lint and recommend PCX skills")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("lint")
    rec = sub.add_parser("recommend")
    rec.add_argument("task", nargs="+")
    rec.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()
    if args.cmd == "lint":
        result = lint()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    if args.cmd == "recommend":
        print(json.dumps(recommend(" ".join(args.task), args.limit), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
