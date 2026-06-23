#!/usr/bin/env python3
"""Validate the toolkit's LLM-facing anti-hallucination contract.

This is intentionally deterministic and dependency-free. It checks that every
high-value LLM loading surface points at the Perception-first routing document
and that generated per-language bundles put that routing document first.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROUTING = "docs/perception/llm-routing.md"

MUST_REFERENCE_ROUTING = [
    "README.md",
    "docs/INDEX.md",
    "docs/llms.txt",
    "rules/CLAUDE.md",
    "rules/CURSOR.md",
    "rules/CLINE.md",
    "rules/COPILOT.md",
    "rules/WINDSURF.md",
    ".github/copilot-instructions.md",
    ".clinerules",
    ".cursorrules",
    ".windsurfrules",
]

BUNDLES = [
    "docs/llms-perception-enma.md",
    "docs/llms-perception-angelscript.md",
]


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")


def main() -> int:
    errors: list[str] = []

    if not (REPO_ROOT / ROUTING).exists():
        errors.append(f"missing routing doc: {ROUTING}")

    for rel in MUST_REFERENCE_ROUTING:
        path = REPO_ROOT / rel
        if not path.exists():
            errors.append(f"missing LLM surface: {rel}")
            continue
        text = read(rel)
        if ROUTING not in text:
            errors.append(f"{rel}: must reference {ROUTING}")

    for rel in BUNDLES:
        text = read(rel)
        needle = f"## Source: `{ROUTING}`"
        pos = text.find(needle)
        if pos == -1:
            errors.append(f"{rel}: missing source block for {ROUTING}")
            continue
        first_source = text.find("## Source:")
        if pos != first_source:
            errors.append(f"{rel}: {ROUTING} must be the first source block")

    llms = read("docs/llms.txt") if (REPO_ROOT / "docs/llms.txt").exists() else ""
    if "llms-perception-lua.md" in llms or "## Lua APIs" in llms or "## Lua Language" in llms:
        errors.append("docs/llms.txt: public LLM index must be Enma + AngelScript only")

    if errors:
        print("LLM contract check failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("LLM contract in sync: routing doc is present and loaded first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
