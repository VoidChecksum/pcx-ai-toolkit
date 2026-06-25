#!/usr/bin/env python3
"""Build knowledge/pcx-api-index.json from source-backed PCX language docs.

Authoritative roots:
  1. https://docs.perception.cx/perception/enma/readme.md  (Enma API surface)
  2. Local mirrors of official Enma language/add-on references.

Only official/live PCX pages and checked-in official language mirrors contribute
symbols. The docs.perception.cx `llms.txt` index is used solely to enumerate
PCX sub-page URLs; it is not itself a source of API symbols.

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
from typing import cast

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
LLMS_INDEX_URL = "https://docs.perception.cx/perception/llms.txt"
ENMA_LANGUAGE_ROOT_URL = "https://enma-1.gitbook.io/enma/llms-language.md"

ENMA_PREFIX = "/perception/enma/"

# Language primitives that are not API symbols but must not be flagged as unknown.
ENMA_BUILTIN_TYPES = {
    "bool", "char", "wchar", "wchar_t", "int8", "int16", "int32", "int64",
    "uint8", "uint16", "uint32", "uint64", "aint8", "aint16", "aint32", "aint64",
    "float32", "float64", "double", "string", "wstring", "void", "null", "auto",
    "proc_t", "array", "hash_set", "sorted_map", "list", "map", "variant",
    "json_value",
}


LOCAL_LANGUAGE_DOCS = [
    (REPO_ROOT / "docs" / "enma" / "llms-language.md", "enma"),
]

EXTRA_SOURCE_SIGNATURES = [
    (
        "enma",
        "https://enma-1.gitbook.io/enma/addons/json.md",
        """
json_value json_parse(string text);
json_value json_object();
json_value json_array();
string json_stringify(json_value value);
bool json_value.is_valid();
bool json_value.is_null();
bool json_value.is_bool();
bool json_value.is_num();
bool json_value.is_str();
bool json_value.is_array();
bool json_value.is_obj();
int64 json_value.kind();
bool json_value.as_bool();
float64 json_value.as_num();
int64 json_value.as_int();
string json_value.as_str();
int64 json_value.size();
bool json_value.has_key(string key);
array json_value.keys();
json_value json_value.get_key(string key);
json_value json_value.get_at(int64 index);
bool json_value.set_key(string key, json_value value);
bool json_value.remove_key(string key);
bool json_value.push_value(json_value value);
string json_value.stringify();
string json_value.pretty();
""",
    ),
]


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
    return "enma"


def _local_source_url(path: Path, text: str) -> str:
    """Return the original source URL embedded in a checked-in local mirror."""
    source = re.search(r'Source:\s*(https?://[^\s]+)', text)
    if source:
        return source.group(1)
    markdown = re.search(r'\[Markdown\]\((https?://[^)]+)\)', text)
    if markdown:
        return markdown.group(1)
    return path.relative_to(REPO_ROOT).as_posix()


def _find_markdown_code_blocks(text: str) -> list[tuple[str, str]]:
    """Return list of (language_hint, body) for fenced code blocks."""
    out: list[tuple[str, str]] = []
    for m in re.finditer(r'^```\s*(\w*)\s*\n(.*?)\n```', text, re.MULTILINE | re.DOTALL):
        out.append((m.group(1).lower(), m.group(2)))
    return out


def _find_inline_signature_blocks(text: str, language: str) -> list[str]:
    """Return signature snippets documented outside fenced code blocks.

    Several PCX pages use heading backticks such as
    `bool create_file(const string &in path, ...)` or prose headings like
    `clamp(x, a, b) -> double`. These are official source-backed signatures and
    should feed the same index as fenced declarations.
    """
    snippets: list[str] = []

    for m in re.finditer(r'`([^`\n]*\([^`\n]*\)[^`\n]*)`', text):
        sig = m.group(1).strip().replace("\\_", "_")
        if " " not in sig.split("(", 1)[0]:
            continue
        snippets.append(sig.rstrip(";") + ";")


    return snippets


def _discover_sub_pages() -> list[str]:
    """Return absolute paths (e.g. /perception/enma/proc-api.md) under the two roots.

    The root pages themselves are included.  llms.txt is used only for
    enumeration; every page content is fetched directly from its own URL.
    """
    paths: set[str] = {ENMA_PREFIX + "readme.md"}

    # The Enma root explicitly links to its sub-pages.
    enma_root = _fetch(ENMA_ROOT_URL)
    for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', enma_root):
        href = urllib.parse.urldefrag(m.group(2).strip())[0]
        if href.startswith(ENMA_PREFIX) and href.endswith(".md"):
            paths.add(href)

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


def _local_language_pages() -> list[tuple[Path, str, str]]:
    """Return checked-in language mirrors as (path, language, markdown_text)."""
    out: list[tuple[Path, str, str]] = []
    for path, language in LOCAL_LANGUAGE_DOCS:
        if path.exists():
            out.append((path, language, path.read_text(encoding="utf-8", errors="ignore")))
    return out


def build_index() -> dict[str, object]:
    functions: dict[str, list[dict[str, object]]] = {}
    methods: dict[str, list[dict[str, object]]] = {}
    types: set[str] = set()
    modules: dict[str, set[str]] = {}

    types.update(ENMA_BUILTIN_TYPES)

    page_paths = _discover_sub_pages()
    pages = _fetch_pages(page_paths)
    local_pages = _local_language_pages()

    def add_sig(sig: dict[str, object]) -> None:
        name = str(sig["name"])
        types.add(_base_type(str(sig.get("return_type") or "")))
        raw_arg_types = sig.get("arg_types", [])
        arg_types = cast(list[object], raw_arg_types) if isinstance(raw_arg_types, list) else []
        for at in arg_types:
            types.add(_base_type(str(at)))

        if sig["kind"] == "method":
            methods.setdefault(name, []).append(sig)
        else:
            functions.setdefault(name, []).append(sig)

    for path, text in pages.items():
        language = _language_from_path(path)
        source_url = _page_url(path)

        if language == "enma":
            for mod in extract_enma_imports(text):
                modules.setdefault(mod, set())

        for lang_hint, body in _find_markdown_code_blocks(text):
            block_language = lang_hint if lang_hint == "enma" else language
            sigs = extract_api_signatures(body, block_language, source_url)
            for sig in sigs:
                add_sig(sig)

        for body in _find_inline_signature_blocks(text, language):
            sigs = extract_api_signatures(body, language, source_url)
            for sig in sigs:
                add_sig(sig)

    for local_path, language, text in local_pages:
        source_url = _local_source_url(local_path, text)
        if language == "enma":
            for mod in extract_enma_imports(text):
                modules.setdefault(mod, set())

        for lang_hint, body in _find_markdown_code_blocks(text):
            block_language = lang_hint if lang_hint == "enma" else language
            sigs = extract_api_signatures(body, block_language, source_url)
            for sig in sigs:
                add_sig(sig)

        for body in _find_inline_signature_blocks(text, language):
            sigs = extract_api_signatures(body, language, source_url)
            for sig in sigs:
                add_sig(sig)

    for language, source_url, body in EXTRA_SOURCE_SIGNATURES:
        for sig in extract_api_signatures(body, language, source_url):
            add_sig(sig)

    # Treat any module-like word imported in Enma examples as a module.
    module_names = set(modules.keys())

    # Drop accidental keyword/type entries and empty/invalid identifiers.
    types = {t for t in types if t and not t[0].isdigit() and t not in {
        "if", "else", "for", "while", "return", "true", "false", "null", "nil",
        "const", "constexpr", "auto", "void", "null",
    }}

    def sig_list_to_json(d: dict[str, list[dict[str, object]]]) -> dict[str, list[dict[str, object]]]:
        out: dict[str, list[dict[str, object]]] = {}
        for k, v in sorted(d.items()):
            seen: set[str] = set()
            clean_items: list[dict[str, object]] = []
            for s in v:
                clean = {kk: vv for kk, vv in s.items() if kk != "line"}
                key = json.dumps(clean, sort_keys=True)
                if key in seen:
                    continue
                seen.add(key)
                clean_items.append(clean)
            out[k] = clean_items
        return out

    return {
        "version": 1,
        "generated_by": "tools/build-api-index.py",
        "source_roots": [ENMA_ROOT_URL, ENMA_LANGUAGE_ROOT_URL],
        "functions": sig_list_to_json(functions),
        "methods": sig_list_to_json(methods),
        "types": sorted(types),
        "modules": sorted(module_names),
        "doc_count": len(pages) + len(local_pages),
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


if __name__ == "__main__":
    sys.exit(main())
