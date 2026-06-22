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
  - validate_code(code, language, source_path="")
                                : check a code snippet against the PCX API index

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
import sys
from pathlib import Path

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
from pcx_parser import (  # noqa: E402
    extract_calls,
    extract_declarations,
    extract_enma_imports,
    extract_function_defs,
)


# ── Corpus scanning ──────────────────────────────────────────────────────────

CATEGORIES = {
    'docs':       ['docs/**/*.md', 'docs/**/*.txt'],
    'skills':     ['.claude/skills/**/*.md'],
    'knowledge':  ['knowledge/*.md'],
    'rules':      ['rules/*.md'],
    'templates':  ['templates/**/*.em', 'templates/**/*.as', 'templates/**/*.lua', 'templates/**/*.md'],
    'tools':      ['tools/*.py', 'tools/*.sh'],
    'signatures': ['signatures/**/*.md'],
    'mcp':        ['mcp/*.md', 'mcp/*.json'],
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
        self._loaded = True

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        # Cheap word tokenization: lowercased alphanumeric+underscore runs of len>=3.
        return set(t for t in re.findall(r'[A-Za-z_][A-Za-z0-9_]{2,}', text.lower()))

    def search(self, query: str, limit: int = 10) -> list[dict]:
        self.load()
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
            {'path': rel(p), 'score': round(s, 3), 'snippet': snippet}
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


# ── MCP server ─────────────────────────────────────────────────────────────────

mcp = FastMCP("pcx-knowledge")


@mcp.tool()
def search(query: str, limit: int = 10) -> str:
    """Search the toolkit corpus by keyword.

    Returns a JSON list of {path, score, snippet} ranked by relevance.
    Searches docs, skills, knowledge, rules, templates, tools, signatures, mcp setup files.
    """
    results = INDEX.search(query, limit=max(1, min(limit, 50)))
    return json.dumps(results, indent=2)


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
            return json.dumps({'error': f'unknown category: {category}',
                               'available': list(corpus.keys())}, indent=2)
        return json.dumps({category: [rel(p) for p in corpus[category]]}, indent=2)
    return json.dumps({cat: [rel(p) for p in files] for cat, files in corpus.items()}, indent=2)


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
        "  - knowledge/pcx-api-cheatsheet.md  : all PCX APIs at a glance\n"
        "  - knowledge/common-patterns.md     : 13 worked code recipes\n"
        "  - .claude/skills/game-cheat-guidelines/SKILL.md : the 12 behavioral rules\n"
        "  - .claude/skills/pcx-patch-day-playbook/SKILL.md : when the game updates\n"
        "  - docs/llms.txt                    : structured index of the whole corpus\n"
        "  - docs/llms-perception-enma.md     : single-file Enma context pack\n\n"
        "Workflow: search(query) -> get_file(path) for the most relevant hits.\n"
        "Bulk: list_files(category) to enumerate; list_files() for everything.\n"
    )


# ── Code validation helper ─────────────────────────────────────────────────────

API_INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"
API_INDEX_CACHE: dict | None = None

ENMA_IMPORT_REQUIRED_TYPES = {"vec2", "vec3", "vec4", "color", "quat", "mat4"}
ENMA_MODULE_HINTS: dict[str, set[str]] = {
    "vec": {"vec2", "vec3", "vec4"},
    "color": {"color"},
    "math3d": {"quat", "mat4"},
}


def _load_api_index() -> dict | None:
    global API_INDEX_CACHE
    if API_INDEX_CACHE is not None:
        return API_INDEX_CACHE
    if not API_INDEX_FILE.exists():
        return None
    data = json.loads(API_INDEX_FILE.read_text(encoding="utf-8"))
    API_INDEX_CACHE = {
        "functions": set(data.get("functions", {}).keys()),
        "methods": set(data.get("methods", {}).keys()),
        "types": set(data.get("types", [])),
    }
    return API_INDEX_CACHE


def _base_type(t: str) -> str:
    t = t.strip().rstrip("@").replace("&", "").replace("*", "").strip()
    t = re.sub(r'<.*>', "", t)
    t = re.sub(r'\[.*\]', "", t)
    return t.strip()


def _validate_code_impl(code: str, language: str) -> list[dict]:
    findings: list[dict] = []
    index = _load_api_index()
    if index is None:
        return [{"line": 0, "symbol": "", "kind": "index_missing",
                 "message": f"API index not found at {API_INDEX_FILE}; run `pcx build-api-index`"}]

    user_funcs = {name for name, _ in extract_function_defs(code, language)}

    for name, line in extract_calls(code, language):
        if name in index["functions"] or name in index["methods"] or name in user_funcs:
            continue
        if language == "enma" and name in {"main", "on_render", "on_update", "on_unload"}:
            continue
        if language == "angelscript" and name in {"main", "on_tick", "on_unload", "on_frame"}:
            continue
        if language == "lua" and name in {"main", "on_frame", "on_unload", "on_tick"}:
            continue
        findings.append({
            "line": line,
            "symbol": name,
            "kind": "unknown_call",
            "message": f"'{name}' is not a known PCX or Enma function/method",
        })

    if language in {"enma", "angelscript"}:
        for type_part, name, line in extract_declarations(code, language):
            base = _base_type(type_part)
            if not base or base in index["types"] or base in user_funcs:
                continue
            if base[0].isupper():
                continue
            findings.append({
                "line": line,
                "symbol": base,
                "kind": "unknown_type",
                "message": f"'{base}' is not a known type (in declaration of '{name}')",
            })

    if language == "enma":
        imports = set(extract_enma_imports(code))
        used = {t for t in ENMA_IMPORT_REQUIRED_TYPES if re.search(r'\b' + re.escape(t) + r'\b', code)}
        for t in used:
            if any(t in names and mod in imports for mod, names in ENMA_MODULE_HINTS.items()):
                continue
            for mod, names in ENMA_MODULE_HINTS.items():
                if t in names:
                    findings.append({
                        "line": 1,
                        "symbol": t,
                        "kind": "missing_import",
                        "message": f"'{t}' requires `import \"{mod}\";`",
                    })
                    break

    return findings


@mcp.tool()
def validate_code(code: str, language: str, source_path: str = "") -> str:
    """Validate a snippet of Enma, AngelScript, or Lua code against the PCX API index.

    Returns a JSON object with {findings: [...], ok: bool}. Each finding has:
    line, symbol, kind, message. Kinds: unknown_call, unknown_type,
    missing_import, index_missing. An empty findings list means no hallucinated
    symbols were detected.

    language must be one of: enma, angelscript, lua.
    """
    if language not in {"enma", "angelscript", "lua"}:
        return json.dumps({"error": f"unsupported language: {language}"}, indent=2)
    findings = _validate_code_impl(code, language)
    return json.dumps({"findings": findings, "ok": not findings}, indent=2)


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
    # Eagerly load the index so the first search is fast.
    INDEX.load()
    mcp.run()


if __name__ == "__main__":
    main()
