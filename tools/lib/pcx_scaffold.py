"""Project scaffolding helpers for Perception.cx Enma and AngelScript.

The CLI and MCP server both use this module so project creation stays
deterministic and testable.  It intentionally copies from checked-in templates
instead of generating large source strings from memory.
"""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


from pcx_paths import data_root

REPO_ROOT = data_root()
TEMPLATES_DIR = REPO_ROOT / "templates"

LANG_ALIASES = {
    "enma": "enma",
    "em": "enma",
    ".em": "enma",
    "angelscript": "angelscript",
    "angel-script": "angelscript",
    "as": "angelscript",
    ".as": "angelscript",
}


@dataclass(frozen=True)
class TemplateSpec:
    language: str
    kind: str
    source: str
    description: str
    entrypoint: str


TEMPLATE_SPECS: tuple[TemplateSpec, ...] = (
    TemplateSpec("enma", "full", "full-project", "Multi-file Enma feature scaffold", "main.em"),
    TemplateSpec("enma", "cheat", "cheat-skeleton-em", "Full Enma ESP/aim/radar/trigger scaffold", "main.em"),
    TemplateSpec("enma", "overlay", "overlay-basic.em", "Single-file Enma overlay/menu starter", "overlay-basic.em"),
    TemplateSpec("enma", "aimbot", "aimbot-skeleton.em", "Single-file Enma aimbot scaffold", "aimbot-skeleton.em"),
    TemplateSpec("enma", "minimap", "minimap.em", "Single-file Enma radar/minimap scaffold", "minimap.em"),
    TemplateSpec("enma", "hello", "hello-world.em", "Minimal Enma lifecycle starter", "hello-world.em"),
    TemplateSpec("angelscript", "full", "full-project-as", "Multi-file AngelScript feature scaffold", "main.as"),
    TemplateSpec("angelscript", "cheat", "cheat-skeleton-as", "Full AngelScript ESP/aim/radar/trigger scaffold", "main.as"),
)


def normalize_language(language: str) -> str:
    lang = LANG_ALIASES.get(language.strip().lower())
    if not lang:
        raise ValueError(f"unsupported language: {language}; expected enma or angelscript")
    return lang


def available_templates(language: str = "") -> list[dict[str, str]]:
    lang = normalize_language(language) if language else ""
    rows: list[dict[str, str]] = []
    for spec in TEMPLATE_SPECS:
        if lang and spec.language != lang:
            continue
        rows.append({
            "language": spec.language,
            "kind": spec.kind,
            "source": spec.source,
            "description": spec.description,
            "entrypoint": spec.entrypoint,
        })
    return rows


def select_template(language: str, kind: str) -> TemplateSpec:
    lang = normalize_language(language)
    normalized_kind = kind.strip().lower()
    aliases = {
        "project": "full",
        "starter": "full",
        "esp": "cheat",
        "radar": "cheat",
        "triggerbot": "cheat",
        "memory-scanner": "full",
        "minimal": "hello",
    }
    normalized_kind = aliases.get(normalized_kind, normalized_kind)
    for spec in TEMPLATE_SPECS:
        if spec.language == lang and spec.kind == normalized_kind:
            return spec
    choices = ", ".join(t["kind"] for t in available_templates(lang))
    raise ValueError(f"unsupported {lang} template kind: {kind}; choices: {choices}")


def slugify(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", name.strip()).strip("-._").lower()
    return slug or "pcx-project"


def build_project_plan(
    name: str,
    language: str,
    kind: str,
    target_process: str = "game.exe",
    engine: str = "generic",
) -> dict[str, Any]:
    spec = select_template(language, kind)
    project = slugify(name)
    docs = [
        "docs/AI_AGENT_OPERATING_MANUAL.md",
        "docs/perception/llm-routing.md",
        "knowledge/pcx-api-cheatsheet.md",
        "knowledge/offset-methodology.md",
    ]
    skills = ["game-cheat-script-master", "pcx-re-discipline", "re-evidence-log"]
    if spec.language == "enma":
        docs.extend(["docs/llms-perception-enma.md", "docs/perception/lifecycle-and-routines.md"])
        skills.append("pcx-enma-discipline")
    else:
        docs.extend(["docs/llms-perception-angelscript.md", "docs/perception/angelscript/life-cycle.md"])
        skills.append("pcx-angelscript-discipline")

    return {
        "name": name,
        "slug": project,
        "language": spec.language,
        "kind": spec.kind,
        "template": spec.source,
        "entrypoint": spec.entrypoint,
        "target_process": target_process,
        "engine": engine,
        "load_order": [
            "Read llm-routing before choosing symbols",
            "Use api_lookup before adding any PCX API call",
            "Keep offsets/signatures in one module",
            "Run pcx verify-project before loading in Perception",
        ],
        "authorized_use": {
            "scope": "owned-lab-ctf-or-authorized-research",
            "requires_evidence": True,
            "no_public_multiplayer_abuse": True,
        },
        "docs": docs,
        "skills": skills,
        "commands": [
            f"pcx api <symbol> --lang {spec.language}",
            "pcx verify-project . --allow-placeholders --allow-unverified",
            "pcx check-answer answer.md",
        ],
    }


def _copy_template(src: Path, dst: Path, project_slug: str) -> list[Path]:
    written: list[Path] = []
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            target = dst / child.name
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)
        written.extend(p for p in dst.rglob("*") if p.is_file())
        return written

    suffix = src.suffix or ".txt"
    out = dst / f"{project_slug}{suffix}"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, out)
    written.append(out)
    return written


def _replace_target_process(paths: list[Path], target_process: str) -> None:
    if not target_process or target_process == "game.exe":
        return
    for path in paths:
        if path.suffix.lower() not in {".em", ".as", ".md", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        updated = text.replace('"game.exe"', json.dumps(target_process))
        updated = updated.replace("TARGET_PROCESS = \"game.exe\"", f"TARGET_PROCESS = {json.dumps(target_process)}")
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def _write_project_metadata(dst: Path, plan: dict[str, Any]) -> list[Path]:
    written: list[Path] = []
    meta = {
        "schema": "https://github.com/VoidChecksum/pcx-ai-toolkit/schema/pcx-project-v1",
        "name": plan["name"],
        "language": plan["language"],
        "kind": plan["kind"],
        "target_process": plan["target_process"],
        "engine": plan["engine"],
        "entrypoint": plan["entrypoint"],
        "validation": plan["commands"],
        "docs": plan["docs"],
        "skills": plan["skills"],
        "authorized_use": plan["authorized_use"],
    }
    meta_path = dst / "pcx-project.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    written.append(meta_path)

    evidence_dir = dst / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    evidence_readme = evidence_dir / "README.md"
    evidence_readme.write_text(
        "# Evidence Log\n\n"
        "Every offset, signature, struct layout, and pointer chain used by this project "
        "should cite an `E-NNN` entry here before shipping.\n\n"
        "Template entry:\n\n"
        "```text\n"
        "E-001\n"
        f"target: {plan['target_process']}\n"
        "binary_sha256: <sha256>\n"
        "tool: IDA/Ghidra/Binary Ninja/ReClass/Perception Analyzer\n"
        "claim: <offset/signature/struct field>\n"
        "evidence: <xref, disassembly, dump path, or live read proof>\n"
        "last_verified: YYYY-MM-DD\n"
        "confidence: confirmed|candidate|unverified\n"
        "```\n",
        encoding="utf-8",
    )
    written.append(evidence_readme)

    project_readme = dst / "README.md"
    if not project_readme.exists():
        project_readme.write_text(
            f"# {plan['name']}\n\n"
            f"Language: `{plan['language']}`\n\n"
            f"Target process: `{plan['target_process']}`\n\n"
            f"Engine profile: `{plan['engine']}`\n\n"
            "## Verify\n\n"
            "```bash\n"
            "pcx verify-project . --allow-placeholders --allow-unverified\n"
            "```\n\n"
            "Replace placeholder signatures and offsets with evidence-backed values before shipping.\n",
            encoding="utf-8",
        )
        written.append(project_readme)
    return written


def scaffold_project(
    name: str,
    language: str,
    kind: str,
    output_dir: Path,
    target_process: str = "game.exe",
    engine: str = "generic",
    overwrite: bool = False,
) -> dict[str, Any]:
    plan = build_project_plan(name, language, kind, target_process, engine)
    dst = output_dir.expanduser().resolve()
    if dst.exists() and any(dst.iterdir()) and not overwrite:
        raise FileExistsError(f"output directory already exists and is not empty: {dst}")
    dst.mkdir(parents=True, exist_ok=True)

    src = TEMPLATES_DIR / str(plan["template"])
    if not src.exists():
        raise FileNotFoundError(f"template missing: {src}")

    written = _copy_template(src, dst, str(plan["slug"]))
    _replace_target_process(written, target_process)
    written.extend(_write_project_metadata(dst, plan))
    return {
        "ok": True,
        "project_dir": str(dst),
        "plan": plan,
        "files": sorted(str(p.relative_to(dst)) for p in written if p.exists()),
    }
