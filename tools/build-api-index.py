#!/usr/bin/env python3
"""Build knowledge/pcx-api-index.json from the two live upstream PCX API docs.

Authoritative roots:
  1. https://docs.perception.cx/perception/enma/overview  (Enma API surface)
     Markdown equivalent: https://docs.perception.cx/perception/enma/readme.md
  2. https://docs.perception.cx/perception/angel-script/overview  (AngelScript API surface)
     Markdown equivalent: https://docs.perception.cx/perception/angel-script/overview.md

Only pages under these two roots contribute API symbols to the index.
The docs.perception.cx `llms.txt` index is used solely to enumerate sub-page
URLs under the two roots; it is not itself a source of API symbols.

Usage:
    python tools/build-api-index.py          # regenerate knowledge/pcx-api-index.json
    python tools/build-api-index.py --check # exit 1 if the JSON drifts from upstream

Stdlib only.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sized
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = REPO_ROOT / "knowledge"
OUT_FILE = KNOWLEDGE / "pcx-api-index.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_parser import (  # noqa: E402
    _base_type,
    extract_api_signatures,
    extract_enma_imports,
)

# ── Upstream endpoints ─────────────────────────────────────────────────────────
ENMA_ROOT_URL = "https://docs.perception.cx/perception/enma/readme.md"
AS_ROOT_URL = "https://docs.perception.cx/perception/angel-script/overview.md"
LLMS_INDEX_URL = "https://docs.perception.cx/perception/llms.txt"

ENMA_PREFIX = "/perception/enma/"
AS_PREFIX = "/perception/angel-script/"

# Language primitives that are not API symbols but must not be flagged as unknown.
ENMA_BUILTIN_TYPES = {
    "bool", "char", "wchar", "wchar_t", "int8", "int16", "int32", "int64",
    "uint8", "uint16", "uint32", "uint64", "aint8", "aint16", "aint32", "aint64",
    "float32", "float64", "double", "string", "wstring", "void", "null", "auto",
    "proc_t", "array", "hash_set", "sorted_map", "list", "map", "variant",
    "json_value",
}

AS_BUILTIN_TYPES = {
    "bool", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
    "float", "double", "string", "void", "any", "array", "dictionary", "grid",
    "proc_t", "mutex_t", "ws_t", "subtab_t", "panel_t", "checkbox_t",
    "slider_double_t", "slider_int_t", "input_t", "multi_select_t",
    "single_select_t", "keybind_t", "button_t", "color_picker_t",
    "vector2", "vector3", "vector4", "matrix4x4", "quaternion",
    "funcdef",
}


def _fetch(url: str, timeout: int = 30) -> str:
    """Fetch a URL and return UTF-8 text."""
    req = urllib.request.Request(url, headers={"User-Agent": "pcx-ai-toolkit/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body: object = resp.read()
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="ignore")
        return str(body)


def _page_url(path: str) -> str:
    """Convert an absolute doc path like /perception/enma/proc-api.md to full URL."""
    return urllib.parse.urljoin("https://docs.perception.cx", path)


def _language_from_path(path: str) -> str:
    if path.startswith(ENMA_PREFIX):
        return "enma"
    if path.startswith(AS_PREFIX):
        return "angelscript"
    return "enma"


def _find_markdown_code_blocks(text: str) -> list[tuple[str, str]]:
    """Return list of (language_hint, body) for fenced code blocks."""
    out: list[tuple[str, str]] = []
    for m in re.finditer(r'^```\s*(\w*)\s*\n(.*?)\n```', text, re.MULTILINE | re.DOTALL):
        out.append((m.group(1).lower(), m.group(2)))
    return out


def _discover_sub_pages() -> list[str]:
    """Return absolute paths (e.g. /perception/enma/proc-api.md) under the two roots.

    The root pages themselves are included.  llms.txt is used only for
    enumeration; every page content is fetched directly from its own URL.
    """
    paths: set[str] = {ENMA_PREFIX + "readme.md", AS_PREFIX + "overview.md"}

    # The Enma root explicitly links to its sub-pages.
    enma_root = _fetch(ENMA_ROOT_URL)
    for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', enma_root):
        href = urllib.parse.urldefrag(m.group(2).strip())[0]
        if href.startswith(ENMA_PREFIX) and href.endswith(".md"):
            paths.add(href)

    # The AngelScript overview does not link to sub-pages in markdown, so we use
    # the site's structured index to discover them.
    index = _fetch(LLMS_INDEX_URL)
    for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', index):
        href = urllib.parse.urldefrag(m.group(2).strip())[0]
        if href.startswith((ENMA_PREFIX, AS_PREFIX)) and href.endswith(".md"):
            paths.add(urllib.parse.urlparse(href).path)

    return sorted(paths)


def _fetch_pages(paths: list[str]) -> dict[str, str]:
    """Fetch every page and return {path: markdown_text}."""
    out: dict[str, str] = {}
    for path in paths:
        url = _page_url(path)
        try:
            out[path] = _fetch(url)
        except urllib.error.HTTPError as e:
            print(f"WARNING: could not fetch {url}: {e.code}", file=sys.stderr)
        except urllib.error.URLError as e:
            print(f"WARNING: could not fetch {url}: {e.reason}", file=sys.stderr)
    return out


def build_index() -> dict[str, object]:
    functions: dict[str, list[dict[str, object]]] = {}
    methods: dict[str, list[dict[str, object]]] = {}
    types: set[str] = set()
    modules: dict[str, set[str]] = {}

    types.update(ENMA_BUILTIN_TYPES)
    types.update(AS_BUILTIN_TYPES)

    page_paths = _discover_sub_pages()
    pages = _fetch_pages(page_paths)

    for path, text in pages.items():
        language = _language_from_path(path)
        source_url = _page_url(path)

        if language == "enma":
            for mod in extract_enma_imports(text):
                modules.setdefault(mod, set())

        for lang_hint, body in _find_markdown_code_blocks(text):
            block_language = lang_hint if lang_hint in {"enma", "angelscript"} else language
            sigs = extract_api_signatures(body, block_language, source_url)
            for sig in sigs:
                name = sig["name"]
                types.add(_base_type(sig.get("return_type") or ""))
                for at in sig.get("arg_types", []):
                    types.add(_base_type(at))

                if sig["kind"] == "method":
                    methods.setdefault(name, []).append(sig)
                else:
                    functions.setdefault(name, []).append(sig)

    # Treat any module-like word imported in Enma examples as a module.
    module_names = set(modules.keys())

    # Drop accidental keyword/type entries and empty/invalid identifiers.
    types = {t for t in types if t and not t[0].isdigit() and t not in {
        "if", "else", "for", "while", "return", "true", "false", "null", "nil",
        "const", "constexpr", "auto", "void", "null",
    }}

    def sig_list_to_json(d: dict[str, list[dict[str, object]]]) -> dict[str, list[dict[str, object]]]:
        return {k: [{kk: vv for kk, vv in s.items() if kk != "line"} for s in v]
                for k, v in sorted(d.items())}

    return {
        "version": 1,
        "generated_by": "tools/build-api-index.py",
        "source_roots": [ENMA_ROOT_URL, AS_ROOT_URL],
        "functions": sig_list_to_json(functions),
        "methods": sig_list_to_json(methods),
        "types": sorted(types),
        "modules": sorted(module_names),
        "doc_count": len(pages),
    }


def write_index(index: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if JSON drifts from upstream docs")
    args = ap.parse_args()

    index = build_index()

    typed_index: dict[str, object] = dict(index)
    if args.check:
        if not OUT_FILE.exists():
            print(f"ERROR: {OUT_FILE} missing; run without --check to generate.", file=sys.stderr)
            return 1
        current = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        if current != typed_index:
            print(f"ERROR: {OUT_FILE} is out of sync with upstream docs. Regenerate with:", file=sys.stderr)
            print(f"    python3 tools/build-api-index.py", file=sys.stderr)
            return 1
        functions = typed_index.get("functions", {})
        methods = typed_index.get("methods", {})
        assert isinstance(functions, Sized) and isinstance(methods, Sized)
        print(f"OK: {OUT_FILE} is up to date ({typed_index['doc_count']} docs, "
              f"{len(functions)} functions, {len(methods)} methods).")
        return 0

    write_index(typed_index, OUT_FILE)
    print(f"Wrote {OUT_FILE}")
    print(f"  docs:        {typed_index['doc_count']}")
    functions = typed_index.get("functions", {})
    methods = typed_index.get("methods", {})
    types = typed_index.get("types", [])
    modules = typed_index.get("modules", [])
    assert isinstance(functions, Sized) and isinstance(methods, Sized)
    assert isinstance(types, Sized) and isinstance(modules, Sized)
    return 0
