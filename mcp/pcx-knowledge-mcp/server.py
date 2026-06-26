#!/usr/bin/env python3
"""pcx-knowledge-mcp — MCP server exposing the pcx-ai-toolkit corpus.

Lets any MCP-aware AI tool (Claude Desktop, Cline, Cursor, Continue, Zed, ...)
search and fetch the toolkit's docs, skills, knowledge references, IDE drop-ins,
templates, and tool source. Replaces the @-reference-by-path workflow with a
search-then-fetch surface so the AI doesn't need to know every file's name.

Tools exposed:
  - search(query, limit=10)     : keyword search across the whole corpus
  - get_file(path)              : fetch full file content by repo-relative path
  - list_files(category=None)   : enumerate files, optionally filtered to a category
  - overview()                  : top-level summary of the toolkit's structure
  - list_skills()               : enumerate available AI skills with descriptions
  - get_skill(name)             : fetch a skill by stable name
  - recommend_context(task, language="") : deterministic doc/skill/tool starting set
  - api_lookup(symbol, language="") : exact source-backed API lookup
  - validate_code(code, language, source_path="")
                                : check Enma/AngelScript snippets against the PCX API index
  - validate_answer(answer, source_path="answer.md")
                                : validate fenced Enma/AngelScript code blocks in an LLM answer
  - scaffold_project(...)       : dry-run or write a PCX project scaffold
  - validate_project(path, ...) : run project-wide verifier
  - generate_script_plan(...)   : deterministic script/project plan
  - explain_finding(...)        : turn validator JSON into an actionable fix
  - suggest_imports(...)        : Enma missing-import suggestions
  - offset_drift_report(...)    : compare named offset JSON snapshots

Resources exposed:
  - file://<repo-relative-path> : every file in the corpus, addressable by URI

Install:
  pip install mcp                          # the official Python MCP SDK
  # then in your MCP client config:
  {
    "command": "python3",
    "args": ["/path/to/pcx-ai-toolkit/mcp/pcx-knowledge-mcp/server.py"]
  }

Or install as a package via the pyproject.toml in this directory, then:
  {
    "command": "pcx-knowledge-mcp"
  }
"""
from __future__ import annotations

import json
import re
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "error: mcp Python SDK not installed.\n"
        "    pip install mcp\n",
        file=sys.stderr,
    )
    sys.exit(1)

# Make the shared parser available to validate_code
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_grounding import (  # noqa: E402
    load_api_index,
    lookup_symbol,
    validate_answer_markdown,
    validate_code_against_index,
)
from pcx_scaffold import (  # noqa: E402
    available_templates,
    build_project_plan,
    scaffold_project as write_scaffold_project,
)
from pcx_mcp_workflows import plan_json as plan_perception_mcp_json  # noqa: E402


# ── Corpus scanning ──────────────────────────────────────────────────────────

CATEGORIES = {
    'docs':       ['docs/**/*.md', 'docs/**/*.txt'],
    'skills':     ['.claude/skills/**/*.md'],
    'knowledge':  ['knowledge/*.md'],
    'rules':      ['rules/*.md'],
    'templates':  ['templates/**/*.em', 'templates/**/*.as', 'templates/**/*.md'],
    'tools':      ['tools/*.py', 'tools/*.sh'],
    'signatures': ['signatures/**/*.md'],
    'mcp':        ['mcp/*.md', 'mcp/*.json'],
    'evals':      ['evals/**/*.json', 'evals/**/*.md'],
}

SKIP_PATTERNS = [
    re.compile(r'/(node_modules|\.git|build|dist|lsp)/'),
    re.compile(r'\.(vsix|dll|exe|so|bin)$'),
]


def list_corpus() -> dict[str, list[Path]]:
    """Walk the repo; return {category: [absolute paths]}."""
    out: dict[str, list[Path]] = {}
    for cat, globs in CATEGORIES.items():
        files: list[Path] = []
        for glob in globs:
            for p in sorted(REPO_ROOT.glob(glob)):
                if not p.is_file():
                    continue
                rel = '/' + str(p.relative_to(REPO_ROOT))
                if any(skip.search(rel) for skip in SKIP_PATTERNS):
                    continue
                files.append(p)
        out[cat] = files
    return out


def rel(p: Path) -> str:
    return str(p.relative_to(REPO_ROOT))


def resolve(repo_relative: str) -> Path | None:
    """Resolve a repo-relative path; reject escapes."""
    raw = repo_relative.lstrip('/').replace('\\', '/')
    p = (REPO_ROOT / raw).resolve()
    try:
        p.relative_to(REPO_ROOT)
    except ValueError:
        return None
    if not p.exists() or not p.is_file():
        return None
    return p


# ── Search index ─────────────────────────────────────────────────────────────

class KeywordIndex:
    """In-memory keyword index: tokenize each file once, score queries by overlap."""

    def __init__(self):
        self.docs: list[tuple[Path, str, set[str]]] = []  # (path, full_text, token set)
        self._fts: sqlite3.Connection | None = None
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        corpus = list_corpus()
        for cat, files in corpus.items():
            for p in files:
                try:
                    text = p.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue
                tokens = self._tokenize(text + ' ' + rel(p))
                self.docs.append((p, text, tokens))
        self._build_fts()
        self._loaded = True

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        # Cheap word tokenization: lowercased alphanumeric+underscore runs of len>=3.
        return set(t for t in re.findall(r'[A-Za-z_][A-Za-z0-9_]{2,}', text.lower()))

    def _build_fts(self) -> None:
        try:
            conn = sqlite3.connect(":memory:")
            conn.execute("CREATE VIRTUAL TABLE docs USING fts5(path, content)")
            conn.executemany(
                "INSERT INTO docs(path, content) VALUES (?, ?)",
                [(rel(path), text) for path, text, _tokens in self.docs],
            )
            self._fts = conn
        except sqlite3.Error:
            self._fts = None

    def _search_fts(self, query: str, limit: int) -> list[dict] | None:
        if self._fts is None:
            return None
        tokens = sorted(self._tokenize(query))
        if not tokens:
            return []
        match = " OR ".join(tokens)
        try:
            rows = self._fts.execute(
                "SELECT path, bm25(docs) AS rank, snippet(docs, 1, '', '', ' … ', 12) "
                "FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT ?",
                (match, limit),
            ).fetchall()
        except sqlite3.Error:
            return None
        return [
            {"path": str(path), "score": round(float(-rank), 3), "snippet": str(snippet), "backend": "fts"}
            for path, rank, snippet in rows
        ]

    def search(self, query: str, limit: int = 10) -> list[dict]:
        self.load()
        fts = self._search_fts(query, limit)
        if fts:
            return fts
        qtokens = self._tokenize(query)
        if not qtokens:
            return []

        scored: list[tuple[float, Path, str]] = []
        # Also count substring hits for short phrase queries that don't tokenize well
        substr_needles = [w for w in query.lower().split() if len(w) >= 3]

        for path, text, tokens in self.docs:
            overlap = len(qtokens & tokens)
            if overlap == 0 and not any(n in text.lower() for n in substr_needles):
                continue
            # IDF-ish bias: smaller docs hit higher when they match
            size_kb = max(len(text) / 1024.0, 1.0)
            substr_score = sum(1 for n in substr_needles if n in text.lower())
            score = (overlap * 3 + substr_score * 2) / (size_kb ** 0.3)
            snippet = self._snippet(text, qtokens, substr_needles)
            scored.append((score, path, snippet))

        scored.sort(key=lambda t: t[0], reverse=True)
        return [
            {'path': rel(p), 'score': round(s, 3), 'snippet': snippet, 'backend': 'keyword'}
            for s, p, snippet in scored[:limit]
        ]

    @staticmethod
    def _snippet(text: str, qtokens: set[str], substr_needles: list[str], width: int = 240) -> str:
        lines = text.splitlines()
        # Find first line that mentions any query term
        for i, line in enumerate(lines):
            low = line.lower()
            tokens = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]{2,}', low))
            if (qtokens & tokens) or any(n in low for n in substr_needles):
                # Pull a small window around it
                start = max(0, i - 1)
                end = min(len(lines), i + 4)
                snippet = '\n'.join(lines[start:end]).strip()
                if len(snippet) > width:
                    snippet = snippet[:width].rstrip() + '...'
                return snippet
        return text.splitlines()[0][:width] if text else ''


INDEX = KeywordIndex()


# ── Skill metadata ───────────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    block = text[4:end]
    data: dict[str, str] = {}
    current: str | None = None
    for raw in block.splitlines():
        if not raw.strip():
            continue
        if raw.startswith((" ", "\t")) and current:
            data[current] = (data[current] + " " + raw.strip()).strip()
            continue
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        current = key.strip()
        data[current] = value.strip().strip("'\"").strip(">")
    return data


def skill_index() -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    for path in sorted((REPO_ROOT / ".claude" / "skills").glob("*/SKILL.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        meta = _parse_frontmatter(text)
        name = meta.get("name") or path.parent.name
        desc = " ".join((meta.get("description") or "").split())
        skills.append({
            "name": name,
            "path": rel(path),
            "description": desc,
        })
    return skills


def _skill_by_name(name: str) -> Path | None:
    normalized = name.removeprefix("skill://").strip().lower()
    for item in skill_index():
        if item["name"].lower() == normalized:
            return resolve(item["path"])
    candidate = resolve(f".claude/skills/{normalized}/SKILL.md")
    return candidate


CONTEXT_RULES = [
    (
        {"esp", "aimbot", "triggerbot", "radar", "overlay", "cheat", "hack", "memory"},
        {
            "skills": ["game-cheat-script-master", "game-cheat-guidelines", "game-hacking-pcx"],
            "docs": ["docs/perception/llm-routing.md", "knowledge/cheat-script-cookbook.md", "knowledge/common-patterns.md", "knowledge/perception-forum-insights.md"],
            "tools": ["api_lookup", "validate_code", "search", "get_file"],
        },
    ),
    (
        {"forum", "changelog", "changelogs", "migration", "beta", "client", "fullscreen"},
        {
            "skills": ["pcx-knowledge-index", "ai-pair-programming"],
            "docs": ["knowledge/perception-forum-insights.md", "docs/perception/changelogs.md", "docs/AI_AGENT_OPERATING_MANUAL.md"],
            "tools": ["search", "get_file", "api_lookup", "validate_answer"],
        },
    ),
    (
        {"offset", "signature", "sig", "pattern", "patch", "update", "struct", "reversing"},
        {
            "skills": ["pcx-re-discipline", "re-evidence-log", "pcx-patch-day-playbook"],
            "docs": ["knowledge/offset-methodology.md", "knowledge/pcx-version-matrix.md", "signatures/source-engine/common-sigs.md"],
            "tools": ["search", "get_file"],
        },
    ),
    (
        {"mcp", "tool", "memory", "scan", "disassemble", "process"},
        {
            "skills": ["mcp-tool-routing", "pcx-knowledge-index"],
            "docs": ["docs/perception/mcp-api.md", "mcp/perception-mcp-config.json", "mcp/pcx-knowledge-mcp/README.md"],
            "tools": ["search", "get_file", "api_lookup", "validate_code"],
        },
    ),
    (
        {"package", "bundle", "ship", "release", "vsix", "extension"},
        {
            "skills": ["script-bundler", "pcx-coding-discipline"],
            "docs": ["README.md", "templates/README.md", "visualstudio/README.md"],
            "tools": ["search", "get_file"],
        },
    ),
]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def build_context_recommendation(task: str, language: str = "") -> dict[str, object]:
    lang = language.lower().strip()
    text = f"{task} {lang}".lower()
    tokens = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", text))

    skills = ["ai-pair-programming", "pcx-knowledge-index"]
    docs = ["docs/perception/llm-routing.md", "docs/INDEX.md"]
    tools = ["search", "get_file", "api_lookup", "validate_code", "validate_answer"]

    if lang in {"enma", ".em", "em"} or ".em" in text:
        skills.extend(["pcx-enma-discipline", "game-hacking-pcx"])
        docs.extend(["docs/llms-perception-enma.md", "docs/perception/lifecycle-and-routines.md"])
    if lang in {"angelscript", "angel-script", ".as", "as"} or ".as" in text:
        docs.append("docs/llms-perception-enma.md")

    for triggers, payload in CONTEXT_RULES:
        if tokens & triggers:
            skills.extend(payload["skills"])
            docs.extend(payload["docs"])
            tools.extend(payload["tools"])

    return {
        "task": task,
        "language": lang,
        "load_order": [
            "docs/perception/llm-routing.md",
            "selected skills",
            "selected docs",
            "api_lookup before inventing symbols",
            "validate_code or validate_answer before final output",
        ],
        "skills": _dedupe(skills),
        "docs": _dedupe(docs),
        "mcp_tools": _dedupe(tools),
        "commands": [
            "pcx api <symbol>",
            "pcx symbol-check <file.em>",
            "pcx check-answer <answer.md>",
        ],
    }


# ── MCP server ─────────────────────────────────────────────────────────────────

mcp = FastMCP("pcx-knowledge")


def _mcp_result(payload: Any) -> Any:
    """Return structured MCP payloads; set PCX_MCP_JSON_STRINGS=1 for legacy clients."""
    if os.environ.get("PCX_MCP_JSON_STRINGS") == "1":
        return json.dumps(payload, indent=2)
    return payload


@mcp.tool()
def search(query: str, limit: int = 10) -> str:
    """Search the toolkit corpus by keyword.

    Returns a JSON list of {path, score, snippet} ranked by relevance.
    Searches docs, skills, knowledge, rules, templates, tools, signatures, mcp setup files.
    """
    results = INDEX.search(query, limit=max(1, min(limit, 50)))
    return _mcp_result(results)


@mcp.tool()
def hybrid_search(query: str, limit: int = 10) -> str:
    """Search with optional local vector cache, falling back to keyword search.

    Build cache with: pcx knowledge build-vector-index. Returns the same
    {path, score, snippet} shape as search(), with title when available.
    """
    script = REPO_ROOT / "tools" / "knowledge-index.py"
    index_path = REPO_ROOT / ".pcx" / "index" / "knowledge-vectors.jsonl"
    if script.exists() and index_path.exists():
        try:
            result = subprocess.run([sys.executable, str(script), "search", query, "--limit", str(limit)], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass
    return search(query, limit)


@mcp.tool()
def get_file(path: str) -> str:
    """Fetch full content of a file by repo-relative path.

    Example: get_file("docs/perception/render-api.md")
             get_file("knowledge/aimbot-math.md")
             get_file(".claude/skills/pcx-perf-budget/SKILL.md")
    Returns the file content as text, or an error message if not found.
    """
    p = resolve(path)
    if p is None:
        return f"error: file not found or not in repo: {path}"
    try:
        return p.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return f"error reading {path}: {e}"


@mcp.tool()
def list_files(category: str = '') -> str:
    """List files in the corpus, optionally filtered by category.

    Categories: docs, skills, knowledge, rules, templates, tools, signatures, mcp.
    Empty category returns all categories grouped.
    Returns a JSON object mapping category -> list of repo-relative paths.
    """
    corpus = list_corpus()
    if category:
        if category not in corpus:
            return _mcp_result({'error': f'unknown category: {category}',
                               'available': list(corpus.keys())})
        return _mcp_result({category: [rel(p) for p in corpus[category]]})
    return _mcp_result({cat: [rel(p) for p in files] for cat, files in corpus.items()})


@mcp.tool()
def overview() -> str:
    """Top-level summary of the toolkit's structure.

    Use this first if you don't know what's available. Returns a human-readable
    text overview with counts per category and pointers to the highest-value
    starting points (cheatsheets, common patterns, the 12 guidelines).
    """
    corpus = list_corpus()
    counts = {cat: len(files) for cat, files in corpus.items()}
    total = sum(counts.values())
    return (
        f"pcx-ai-toolkit — knowledge MCP\n"
        f"==============================\n"
        f"Total indexed files: {total}\n\n"
        + ''.join(f"  {cat}: {n}\n" for cat, n in counts.items())
        + "\n"
        "High-leverage starting points:\n"
        "  - docs/perception/llm-routing.md  : load first; language/binding routing\n"
        "  - knowledge/pcx-api-cheatsheet.md  : all PCX APIs at a glance\n"
        "  - knowledge/common-patterns.md     : 13 worked code recipes\n"
        "  - knowledge/perception-forum-insights.md : secondary forum/changelog/client context\n"
        "  - .claude/skills/game-cheat-guidelines/SKILL.md : the 12 behavioral rules\n"
        "  - .claude/skills/pcx-patch-day-playbook/SKILL.md : when the game updates\n"
        "  - docs/llms.txt                    : structured index of the whole corpus\n"
        "  - docs/llms-perception-enma.md     : single-file Enma context pack\n\n"
        "Workflow: recommend_context(task) -> get_skill(name) / get_file(path) -> api_lookup(symbol) -> validate_code(...).\n"
        "Project workflow: generate_script_plan(...) -> scaffold_project(..., dry_run=false) -> validate_project(...).\n"
        "Answer gate: validate_answer(markdown) before copying generated code.\n"
        "Bulk: list_files(category) to enumerate; list_files() for everything.\n"
    )


@mcp.tool()
def list_skills() -> str:
    """List all bundled AI skills with stable names, paths, and descriptions."""
    return _mcp_result(skill_index())


@mcp.tool()
def get_skill(name: str) -> str:
    """Fetch a bundled AI skill by name, e.g. get_skill("pcx-enma-discipline")."""
    path = _skill_by_name(name)
    if path is None:
        return _mcp_result({
            "error": f"skill not found: {name}",
            "available": [item["name"] for item in skill_index()],
        })
    return path.read_text(encoding="utf-8", errors="ignore")


@mcp.tool()
def recommend_context(task: str, language: str = "") -> str:
    """Recommend the smallest useful doc/skill/tool set for a PCX task.

    Use this before loading large bundles. It returns an ordered load plan,
    skill names, docs, MCP tools, and CLI commands for Enma work.
    """
    return _mcp_result(build_context_recommendation(task, language))


# ── API grounding and code validation ─────────────────────────────────────────

API_INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"
REPAIR_TEMPLATES_FILE = REPO_ROOT / "knowledge" / "repair-templates.json"
API_INDEX_CACHE: dict | None = None


def _load_api_index() -> dict | None:
    global API_INDEX_CACHE
    if API_INDEX_CACHE is not None:
        return API_INDEX_CACHE
    if not API_INDEX_FILE.exists():
        return None
    API_INDEX_CACHE = load_api_index(API_INDEX_FILE)
    return API_INDEX_CACHE


@mcp.tool()
def api_lookup(symbol: str, language: str = "") -> str:
    """Look up an exact Perception API symbol with source-backed signatures.

    language may be empty or enma. Use this before inventing a function,
    method, type, argument shape, or lifecycle binding.
    """
    if language and language not in {"enma", "em", ".em"}:
        return _mcp_result({"error": f"unsupported language: {language}; use enma"})
    index = _load_api_index()
    if index is None:
        return _mcp_result({"error": f"API index not found at {API_INDEX_FILE}"})
    return _mcp_result(lookup_symbol(index, symbol, "enma"))


@mcp.tool()
def validate_code(code: str, language: str, source_path: str = "", runtime_mode: str = "project") -> str:
    """Validate a snippet of Enma or AngelScript code against the PCX API index.

    Returns a JSON object with {findings: [...], ok: bool}. Each finding has:
    line, symbol, kind, message. Kinds: unknown_call, unknown_type,
    missing_import, wrong_language_symbol, wrong_language_type, index_missing.
    An empty findings list means no hallucinated or cross-language symbols were
    detected.

    language must be enma.
    """
    if language not in {"enma", "em", ".em"}:
        return _mcp_result({"error": f"unsupported language: {language}; use enma"})
    index = _load_api_index()
    if index is None:
        findings = [{"line": 0, "symbol": "", "kind": "index_missing",
                     "message": f"API index not found at {API_INDEX_FILE}; run `pcx build-api-index`"}]
    else:
        findings = validate_code_against_index(code, language, index, source_path, runtime_mode=runtime_mode)
    return _mcp_result({"findings": findings, "ok": not findings})


@mcp.tool()
def validate_answer(answer: str, source_path: str = "answer.md") -> str:
    """Validate fenced Enma/AngelScript code blocks inside a generated answer.

    Returns {blocks_checked, findings, ok}. This is the MCP equivalent of
    `pcx check-answer <answer.md>` and should be called before copying LLM
    Markdown into a project.
    """
    index = _load_api_index()
    if index is None:
        return _mcp_result({"error": f"API index not found at {API_INDEX_FILE}"})
    return _mcp_result(validate_answer_markdown(answer, index, source_path))



@mcp.tool()
def search_docs(query: str, category: str = "", limit: int = 10) -> str:
    """Search docs/knowledge with an optional corpus category filter."""
    INDEX.ensure()
    results = INDEX.search(query, limit=max(1, min(limit, 50)))
    if category:
        results = [r for r in results if str(r.get("path", "")).startswith(category.rstrip("/") + "/")]
    return _mcp_result(results[:limit])


@mcp.tool()
def get_symbol(symbol: str, language: str = "enma") -> str:
    """Validator-focused alias for api_lookup."""
    return api_lookup(symbol, language)


@mcp.tool()
def get_examples(api_family: str) -> str:
    """Return short source-backed examples for one API family."""
    needle = api_family.lower().strip()
    INDEX.ensure()
    hits = [r for r in INDEX.search(needle, limit=20) if any(part in str(r.get("path", "")) for part in ("examples/", "templates/", "docs/perception/"))]
    return _mcp_result({"family": needle, "examples": hits[:8]})


@mcp.tool()
def get_negative_examples(symbol: str = "") -> str:
    """Return known hallucination examples and repair guidance."""
    path = REPO_ROOT / "knowledge" / "unsupported-symbols.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"symbols": {}}
    symbols = data.get("symbols", {})
    if symbol:
        symbols = {symbol: symbols.get(symbol, "")} if symbol in symbols else {}
    return _mcp_result({"symbols": symbols})


@mcp.tool()
def why_invalid(code: str, language: str = "enma", runtime_mode: str = "project") -> str:
    """Validate code and return findings plus one-line fixes."""
    index = _load_api_index()
    if index is None:
        return _mcp_result({"error": f"API index not found at {API_INDEX_FILE}"})
    findings = validate_code_against_index(code, language, index, "why_invalid", runtime_mode=runtime_mode)
    return _mcp_result({"ok": not findings, "findings": findings})

@mcp.tool()
def plan_perception_mcp_workflow(task: str, target_process: str = "", permissions: str = "") -> str:
    """Return a deterministic Perception runtime MCP call plan for an RE task."""
    return plan_perception_mcp_json(task, target_process, permissions)


# ── Project creation and workflow helpers ────────────────────────────────────

@mcp.tool()
def list_project_templates(language: str = "") -> str:
    """List supported PCX scaffold templates for Enma."""
    try:
        return _mcp_result(available_templates(language or "enma"))
    except ValueError as exc:
        return _mcp_result({"error": str(exc)})


@mcp.tool()
def generate_script_plan(
    task: str,
    language: str = "enma",
    kind: str = "full",
    target_process: str = "game.exe",
    engine: str = "generic",
) -> str:
    """Generate a deterministic source-grounded project/script plan.

    This does not invent APIs. It returns docs, skills, validation commands,
    and the closest scaffold template for the requested language/kind.
    """
    try:
        plan = build_project_plan(task or "pcx-project", language, kind, target_process, engine)
    except ValueError as exc:
        return _mcp_result({"error": str(exc), "templates": available_templates("enma")})
    plan["task"] = task
    plan["mcp_sequence"] = [
        "recommend_context(task, language)",
        "get_file/docs + get_skill/load discipline",
        "api_lookup(symbol, language) before each uncertain API",
        "validate_code or validate_answer",
        "validate_project when files exist",
    ]
    return _mcp_result(plan)


@mcp.tool()
def scaffold_project(
    name: str,
    language: str = "enma",
    kind: str = "full",
    target_process: str = "game.exe",
    engine: str = "generic",
    output_dir: str = "",
    overwrite: bool = False,
    dry_run: bool = True,
) -> str:
    """Create or preview a PCX project scaffold.

    Safe default: dry_run=true returns the exact plan and CLI command without
    writing files. Set dry_run=false and output_dir to write a project.
    """
    try:
        if dry_run or not output_dir:
            plan = build_project_plan(name or "pcx-project", language, kind, target_process, engine)
            plan["dry_run"] = True
            plan["write_command"] = (
                "pcx create "
                f"--name {json.dumps(name or 'pcx-project')} "
                f"--language {plan['language']} --kind {plan['kind']} "
                f"--target {json.dumps(target_process)} --engine {json.dumps(engine)} "
                "--output <project-dir>"
            )
            return _mcp_result(plan)
        if os.environ.get("PCX_MCP_ALLOW_WRITES") != "1":
            return _mcp_result({
                "ok": False,
                "error": "mcp_writes_disabled",
                "message": "Set PCX_MCP_ALLOW_WRITES=1 before starting pcx-knowledge-mcp to allow scaffold_project writes. Dry-run is the safe default.",
            })
        result = write_scaffold_project(
            name or "pcx-project",
            language,
            kind,
            Path(output_dir),
            target_process,
            engine,
            overwrite,
        )
        return _mcp_result(result)
    except ValueError as exc:
        return _mcp_result({"error": str(exc)})
    except Exception as exc:  # noqa: BLE001
        return _mcp_result({"error": f"{type(exc).__name__}: {exc}"})


@mcp.tool()
def validate_project(path: str, allow_placeholders: bool = False, allow_unverified: bool = False) -> str:
    """Run project-wide validation via `pcx verify-project`.

    Returns the verifier JSON: linter steps, symbol-check output, hygiene
    findings, and ok=false if any gate failed.
    """
    cmd = [
        sys.executable,
        str(REPO_ROOT / "tools" / "verify-project.py"),
        path,
        "--json",
    ]
    if allow_placeholders:
        cmd.append("--allow-placeholders")
    if allow_unverified:
        cmd.append("--allow-unverified")
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        payload = json.loads(res.stdout)
    except json.JSONDecodeError:
        payload = {"ok": False, "stdout": res.stdout, "stderr": res.stderr}
    payload["returncode"] = res.returncode
    if res.stderr.strip():
        payload["stderr"] = res.stderr
    return _mcp_result(payload)


def _coerce_finding(finding_json: str) -> dict[str, Any]:
    try:
        data = json.loads(finding_json)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {"kind": "text", "message": finding_json}


@mcp.tool()
def explain_finding(finding_json: str, language: str = "") -> str:
    """Explain one validator finding and provide the next concrete fix."""
    finding = _coerce_finding(finding_json)
    kind = str(finding.get("kind", finding.get("rule", "")))
    symbol = str(finding.get("symbol", ""))
    message = str(finding.get("message", ""))
    fix = str(finding.get("fix", ""))
    templates: dict[str, Any] = {}
    if REPAIR_TEMPLATES_FILE.exists():
        raw = json.loads(REPAIR_TEMPLATES_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("templates"), dict):
            templates = raw["templates"]
    template = templates.get(kind, {}) if isinstance(templates.get(kind, {}), dict) else {}
    advice = str(template.get("repair") or {
        "missing_import": "Add the exact Enma import shown in `fix`, then re-run validate_code.",
        "unknown_call": "Do not invent this API. Use api_lookup for the intended operation and replace the call with a documented symbol.",
        "unknown_type": "Use the language-specific type documented for this binding; check llm-routing before porting types across languages.",
        "wrong_language_symbol": "This is a cross-binding mixup. Rewrite using the selected language lifecycle/API shape.",
        "wrong_language_type": "Replace the type with the selected language's documented equivalent.",
        "placeholder": "Replace scaffold placeholder text with target-specific evidence-backed logic before shipping.",
        "unverified": "Convert UNVERIFIED claims into E-NNN evidence entries before shipping.",
    }.get(kind, "Read the referenced source/signature, apply the smallest code change, then re-run validation."))
    return _mcp_result({
        "language": language,
        "kind": kind,
        "symbol": symbol,
        "message": message,
        "reason": template.get("message", message),
        "source": finding.get("citation", finding.get("source", "")),
        "fix": fix or template.get("repair", ""),
        "minimal_patch": template.get("repair", fix),
        "example": template.get("example", ""),
        "next_action": advice,
    })


@mcp.tool()
def suggest_imports(code: str, language: str = "enma") -> str:
    """Suggest missing Enma imports from source-backed validation findings."""
    if language != "enma":
        return _mcp_result({"imports": [], "note": "AngelScript does not use Enma addon imports."})
    index = _load_api_index()
    if index is None:
        return _mcp_result({"error": f"API index not found at {API_INDEX_FILE}"})
    findings = validate_code_against_index(code, "enma", index)
    imports = []
    for finding in findings:
        if finding.get("kind") == "missing_import" and finding.get("fix"):
            imports.append(str(finding["fix"]))
    return _mcp_result({"imports": _dedupe(imports), "findings": findings})


def _flatten_offsets(payload: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, dict):
                nested = _flatten_offsets(value)
                for nkey, nval in nested.items():
                    out[f"{key}.{nkey}"] = nval
                continue
            if isinstance(value, str):
                try:
                    out[str(key)] = int(value, 16) if value.lower().startswith("0x") else int(value)
                except ValueError:
                    continue
            elif isinstance(value, int) and not isinstance(value, bool):
                out[str(key)] = value
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and "name" in item:
                value = item.get("value", item.get("offset", item.get("rva")))
                try:
                    out[str(item["name"])] = int(str(value), 16) if str(value).lower().startswith("0x") else int(str(value))
                except (TypeError, ValueError):
                    continue
    return out


@mcp.tool()
def offset_drift_report(old_offsets_json: str, new_offsets_json: str) -> str:
    """Compare two named-offset JSON snapshots and report moved/missing/new names."""
    try:
        old = _flatten_offsets(old_offsets_json)
        new = _flatten_offsets(new_offsets_json)
    except Exception as exc:  # noqa: BLE001
        return _mcp_result({"error": f"invalid JSON: {type(exc).__name__}: {exc}"})
    names = sorted(set(old) | set(new))
    rows = []
    for name in names:
        if name not in old:
            rows.append({"name": name, "status": "NEW", "old": None, "new": f"0x{new[name]:X}", "delta": None})
        elif name not in new:
            rows.append({"name": name, "status": "MISSING", "old": f"0x{old[name]:X}", "new": None, "delta": None})
        else:
            delta = new[name] - old[name]
            rows.append({
                "name": name,
                "status": "UNCHANGED" if delta == 0 else "MOVED",
                "old": f"0x{old[name]:X}",
                "new": f"0x{new[name]:X}",
                "delta": f"{'+' if delta >= 0 else '-'}0x{abs(delta):X}",
            })
    return _mcp_result({
        "summary": {
            "old": len(old),
            "new": len(new),
            "moved": sum(1 for row in rows if row["status"] == "MOVED"),
            "unchanged": sum(1 for row in rows if row["status"] == "UNCHANGED"),
            "missing": sum(1 for row in rows if row["status"] == "MISSING"),
            "added": sum(1 for row in rows if row["status"] == "NEW"),
        },
        "offsets": rows,
    })


# ── Resources: every file as a URI ─────────────────────────────────────────────

@mcp.resource("file://{path}")
def file_resource(path: str) -> str:
    """Expose any toolkit file as an MCP resource addressable by `file://<repo-relative-path>`."""
    p = resolve(path)
    if p is None:
        return f"# Not found: {path}"
    return p.read_text(encoding='utf-8', errors='ignore')


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
        print(
            "pcx-knowledge-mcp - MCP server for the pcx-ai-toolkit corpus\n\n"
            "Usage:\n"
            "  pcx-knowledge-mcp\n\n"
            "Configure an MCP client to run this command. Exposed tools include "
            "search, get_file, recommend_context, api_lookup, validate_code, "
            "and validate_answer."
        )
        return

    # Eagerly load the index so the first search is fast.
    INDEX.load()
    mcp.run()


if __name__ == "__main__":
    main()
