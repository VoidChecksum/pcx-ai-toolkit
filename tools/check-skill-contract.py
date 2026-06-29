#!/usr/bin/env python3
"""Validate AI-facing skill and operating-doc contracts.

This is intentionally narrow: it checks files that agents read as behavioral
instructions, not upstream mirrors that may mention unrelated languages in
historical or embedding contexts.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SKILL_DIR = REPO_ROOT / ".claude" / "skills"
AI_DOCS = [
    REPO_ROOT / "docs" / "AI_AGENT_OPERATING_MANUAL.md",
    REPO_ROOT / "docs" / "perception" / "llm-routing.md",
    REPO_ROOT / "docs" / "FAQ.md",
    REPO_ROOT / "docs" / "INDEX.md",
    REPO_ROOT / "mcp" / "pcx-knowledge-mcp" / "README.md",
]

FORBIDDEN_PATTERNS = {
    "deleted bridge doc": re.compile(r"pcx-cross-language-bridge"),
    "old docs count": re.compile(r"43,000\+? lines|139\s+files|35,000\+? lines"),
    "old MCP count": re.compile(r"37\s+Perception\s+MCP"),
}


def _frontmatter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    return text[4:end]


def check_skill(path: Path) -> list[str]:
    rel = path.relative_to(REPO_ROOT)
    text = path.read_text(encoding="utf-8", errors="ignore")
    errors: list[str] = []
    block = _frontmatter(text)
    if block is None:
        errors.append(f"{rel}: missing YAML frontmatter")
        return errors
    for field in ("name:", "description:", "license:"):
        if field not in block:
            errors.append(f"{rel}: missing frontmatter field {field}")
    expected_name = path.parent.name
    name_match = re.search(r"^name:\s*['\"]?([^'\"\n]+)", block, re.MULTILINE)
    if not name_match:
        errors.append(f"{rel}: missing skill name")
    elif name_match.group(1).strip() != expected_name:
        errors.append(f"{rel}: frontmatter name does not match directory {expected_name}")
    return errors


def check_forbidden(path: Path) -> list[str]:
    rel = path.relative_to(REPO_ROOT)
    text = path.read_text(encoding="utf-8", errors="ignore")
    errors: list[str] = []
    for label, pattern in FORBIDDEN_PATTERNS.items():
        for match in pattern.finditer(text):
            line = text[:match.start()].count("\n") + 1
            errors.append(f"{rel}:{line}: forbidden {label}: {match.group(0)}")
    return errors


def main() -> int:
    errors: list[str] = []
    skill_files = sorted(SKILL_DIR.glob("*/SKILL.md"))
    for path in skill_files:
        errors.extend(check_skill(path))
        errors.extend(check_forbidden(path))
    for path in AI_DOCS:
        if path.exists():
            errors.extend(check_forbidden(path))
        else:
            errors.append(f"{path.relative_to(REPO_ROOT)}: missing AI-facing doc")

    if errors:
        print(f"Skill/doc contract errors ({len(errors)}):")
        for error in errors:
            print(f"  {error}")
        return 1
    print(f"Skill/doc contract clean: {len(skill_files)} skills and {len(AI_DOCS)} AI-facing docs checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
