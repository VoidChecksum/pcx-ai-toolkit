"""Lightweight, regex-based parsers for Enma and AngelScript scripts.

These are intentionally shallow: they extract imports, function/method calls,
declarations, and function definitions well enough for symbol-level
hallucination checks without building a full AST. They blank string literals
and comments so identifiers inside labels/urls don't create false matches.
"""
from __future__ import annotations

import re


# ── Comment / literal stripping ──────────────────────────────────────────────

def strip_c_comments(code: str) -> str:
    """Remove // and /* */ comments."""
    out: list[str] = []
    i = 0
    n = len(code)
    while i < n:
        if code[i : i + 2] == "/*":
            j = code.find("*/", i + 2)
            if j == -1:
                break
            out.append(" ")
            i = j + 2
            continue
        if code[i : i + 2] == "//":
            out.append(" ")
            i = code.find("\n", i)
            if i == -1:
                break
            continue
        out.append(code[i])
        i += 1
    return "".join(out)


def strip_strings(code: str) -> str:
    """Blank out double-quoted and single-quoted string contents."""
    out: list[str] = []
    i = 0
    n = len(code)
    while i < n:
        ch = code[i]
        if ch == '"':
            out.append('"')
            i += 1
            while i < n:
                c = code[i]
                if c == "\\":
                    out.extend([" ", " "])
                    i += 2
                    continue
                if c == '"':
                    out.append('"')
                    i += 1
                    break
                out.append(" ")
                i += 1
            continue
        if ch == "'":
            out.append("'")
            i += 1
            while i < n:
                c = code[i]
                if c == "\\":
                    out.extend([" ", " "])
                    i += 2
                    continue
                if c == "'":
                    out.append("'")
                    i += 1
                    break
                out.append(" ")
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


# ── Imports ──────────────────────────────────────────────────────────────────

ENMA_IMPORT_RE = re.compile(r'import\s+"([^"]+)"\s*;')
AS_IMPORT_RE = re.compile(r'^\s*import\s+([A-Za-z_][A-Za-z0-9_:.]*)\s*(?:\w+\s+)?;')


def extract_enma_imports(code: str) -> list[str]:
    """Return module names imported with `import "foo";`."""
    return ENMA_IMPORT_RE.findall(strip_c_comments(code))


def extract_as_imports(code: str) -> list[str]:
    """Return AngelScript import module identifiers."""
    clean = strip_strings(strip_c_comments(code))
    out: list[str] = []
    for line in clean.splitlines():
        m = AS_IMPORT_RE.match(line)
        if m:
            out.append(m.group(1))
    return out


# ── Calls ────────────────────────────────────────────────────────────────────

CALL_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(')
METHOD_CALL_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\(')


def _is_keyword(name: str, lang: str) -> bool:
    common = {
        "if", "else", "for", "while", "do", "switch", "case", "default",
        "return", "break", "continue", "goto", "sizeof", "typeof", "cast",
        "new", "delete", "try", "catch", "throw", "namespace", "using",
        "public", "private", "protected", "static", "const", "constexpr",
        "class", "struct", "enum", "union", "template", "typename",
        "interface", "mixin", "funcdef", "true", "false", "null",
    }
    return name in common


def _strip_for_calls(code: str, lang: str) -> str:
    return strip_strings(strip_c_comments(code))


def extract_calls(code: str, lang: str) -> list[tuple[str, int]]:
    """Return (name, line) for every function-like call.

    For method calls the method name is reported, not the object.
    """
    clean = _strip_for_calls(code, lang)
    calls: list[tuple[str, int]] = []
    for lineno, line in enumerate(clean.splitlines(), 1):
        simple = METHOD_CALL_RE.sub(lambda m: f" {m.group(2)}(", line)
        for m in CALL_RE.finditer(simple):
            name = m.group(1)
            if _is_keyword(name, lang):
                continue
            calls.append((name, lineno))
    return calls


# ── Declarations ────────────────────────────────────────────────────────────

DECL_RE = re.compile(
    r'^\s*(?:const\s+)?(?:nullable\s+)?'
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e\[\]\*\s]*?)\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)'
    r'(?:\s*[=;]|\s*,)',
    re.MULTILINE,
)
def extract_declarations(code: str, lang: str) -> list[tuple[str, str, int]]:
    """Return (type, name, line) for variable/parameter declarations.

    The parser is intentionally shallow and only targets Enma/AngelScript-style
    declarations used by PCX scripts.
    """
    clean = strip_strings(strip_c_comments(code))
    out: list[tuple[str, str, int]] = []
    for lineno, line in enumerate(clean.splitlines(), 1):
        if re.match(r'^\s*(?:struct|class|enum|union|template|funcdef)\b', line):
            continue
        for m in DECL_RE.finditer(line):
            type_part, name = m.group(1).strip(), m.group(2).strip()
            if _is_keyword(type_part.split()[0], lang):
                continue
            if _is_keyword(name, lang):
                continue
            out.append((type_part, name, lineno))
    return out


# ── Function definitions ─────────────────────────────────────────────────────

FUNC_DEF_RE = re.compile(
    r'^\s*(?:const\s+)?'
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*@\s]*?)\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*(?:\{|;)'
)
FUNC_DEF_HEAD_RE = re.compile(
    r'^\s*(?:const\s+)?'
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*@\s]*?)\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*$'
)


def extract_function_defs(code: str, lang: str) -> list[tuple[str, int]]:
    """Return (name, line) for function definitions in supported PCX languages."""
    out: list[tuple[str, int]] = []
    clean = strip_strings(strip_c_comments(code))
    pending: tuple[str, int] | None = None
    for lineno, line in enumerate(clean.splitlines(), 1):
        stripped = line.strip()
        if pending:
            if not stripped:
                continue
            if stripped.startswith("{"):
                out.append(pending)
            pending = None

        m = FUNC_DEF_RE.match(line)
        if m:
            name = m.group(2)
            if _is_keyword(name, lang):
                continue
            out.append((name, lineno))
            continue

        hm = FUNC_DEF_HEAD_RE.match(line)
        if hm:
            name = hm.group(2)
            if not _is_keyword(name, lang):
                pending = (name, lineno)
    return out


# ── Signature extraction from documentation code blocks ───────────────────────

SIG_GLOBAL_RE = re.compile(
    r'^\s*(?:const\s+)?'
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*@\s]*?)\s+@?\s*'
    r'([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*(?:const\s*)?;?\s*$',
)
SIG_METHOD_RE = re.compile(
    r'^\s*(?:const\s+)?'
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*@\s]*?)\s+@?\s*'
    r'([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*(?:const\s*)?;?\s*$',
)
SIG_METHOD_SCOPE_RE = re.compile(
    r'^\s*(?:const\s+)?'
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*@\s]*?)\s+@?\s*'
    r'([A-Za-z_][A-Za-z0-9_]*)::([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*(?:const\s*)?;?\s*$',
)
# Slash-abbreviated method signatures, e.g.
#   uint8/16/32/64 proc.ru8/ru16/ru32/ru64(uint64 addr);
#   bool proc.wu8/wu16/wu32/wu64(uint64 addr, uintN v);
# The return width and every method name after a '/' are expanded into one
# signature per concrete name so the index doesn't miss ru16/ru32/ru64 etc.
SIG_METHOD_SLASH_RE = re.compile(
    r'^\s*(?:const\s+)?'
    r'([A-Za-z_][A-Za-z0-9_]*(?:/[0-9A-Za-z_]+)*)\s+'  # optional slash-abbreviated return widths
    r'([A-Za-z_][A-Za-z0-9_]*)\.'          # parent type
    r'([A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)+)\s*'  # slash-abbreviated names
    r'\(([^)]*)\)\s*(?:const\s*)?;?\s*$',
)
def _count_args(args_str: str) -> int:
    s = args_str.strip()
    if not s:
        return 0
    depth = 0
    count = 0
    for ch in s:
        if ch in "(\u003c[{":
            depth += 1
        elif ch in ")\u003e]}":
            depth -= 1
        elif ch == "," and depth == 0:
            count += 1
    return count + 1


def _split_arg_types(args_str: str) -> list[str]:
    s = args_str.strip()
    if not s:
        return []
    depth = 0
    parts: list[str] = [""]
    for ch in s:
        if ch in "(\u003c[{":
            depth += 1
            parts[-1] += ch
        elif ch in ")\u003e]}":
            depth -= 1
            parts[-1] += ch
        elif ch == "," and depth == 0:
            parts.append("")
        else:
            parts[-1] += ch
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = re.match(r'(?:const\s+)?(?:in\s+|out\+|&?\s*)?([A-Za-z_][A-Za-z0-9_]*)', p)
        if m:
            out.append(m.group(1))
    return out


def _base_type(t: str) -> str:
    t = t.strip().rstrip("@").replace("@", "").replace("&", "").replace("*", "").strip()
    t = re.sub(r'<.*>', "", t)
    t = re.sub(r'\[.*\]', "", t)
    return t.strip()


def _split_top_level_semicolons(line: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    for i, ch in enumerate(line):
        if ch in "(\u003c[{":
            depth += 1
        elif ch in ")\u003e]}":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            parts.append(line[start:i])
            start = i + 1
    parts.append(line[start:])
    return parts


def _expand_signature_fragments(line: str) -> list[str]:
    """Expand compact docs rows like `float64 sin(...); cos(...);`."""
    fragments = [p.strip() for p in _split_top_level_semicolons(line) if p.strip()]
    if not fragments:
        return []

    expanded: list[str] = []
    current_return = ""
    typed_head = re.compile(
        r'^\s*((?:const\s+)?[A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*@\s]*?)\s+@?\s*'
        r'([A-Za-z_][A-Za-z0-9_:.]*)\s*\('
    )
    untyped_head = re.compile(r'^\s*[A-Za-z_][A-Za-z0-9_:.]*\s*\(')

    for fragment in fragments:
        typed = typed_head.match(fragment)
        if typed:
            current_return = typed.group(1).strip()
            expanded.append(fragment)
            continue
        if current_return and untyped_head.match(fragment):
            expanded.append(f"{current_return} {fragment}")
            continue
        expanded.append(fragment)
    return expanded


def _signature_lines(text: str) -> list[tuple[int, str]]:
    """Return single-line signatures, joining multiline declaration blocks."""
    out: list[tuple[int, str]] = []
    pending: list[str] = []
    start_line = 0
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = strip_c_comments(raw).strip()
        if not line:
            continue
        if pending:
            pending.append(line)
            if ")" in line:
                for expanded in _expand_signature_fragments(" ".join(pending)):
                    out.append((start_line, expanded))
                pending = []
            continue
        if "(" in line and ")" not in line and re.match(
            r'^(?:const\s+)?[A-Za-z_][A-Za-z0-9_<>,\[\]*@\s]*\s+@?[A-Za-z_][A-Za-z0-9_:.\-/]*\s*\(',
            line,
        ):
            pending = [line]
            start_line = lineno
            continue
        for expanded in _expand_signature_fragments(line):
            out.append((lineno, expanded))
    return out


def _expanded_return_types(ret_expr: str, names: list[str]) -> list[str]:
    parts = ret_expr.split("/")
    if len(parts) == 1 or len(parts) != len(names):
        return [_base_type(parts[0])] * len(names)
    first = parts[0]
    prefix = re.match(r'^[A-Za-z_]+', first)
    base_prefix = prefix.group(0) if prefix else ""
    returns = [first]
    returns.extend(p if re.match(r'^[A-Za-z_]', p) else base_prefix + p for p in parts[1:])
    return [_base_type(item) for item in returns]


def extract_api_signatures(text: str, language: str, source: str) -> list[dict[str, object]]:
    """Yield signature dicts from a markdown code fence body."""
    found: list[dict[str, object]] = []
    for lineno, line in _signature_lines(text):
        sm = SIG_METHOD_SLASH_RE.match(line)
        if sm:
            ret, parent, names, args = sm.groups()
            expanded_names = names.split("/")
            return_types = _expanded_return_types(ret, expanded_names)
            for name, return_type in zip(expanded_names, return_types, strict=False):
                if _is_keyword(name, language):
                    continue
                found.append({
                    "name": name,
                    "language": language,
                    "source": source,
                    "kind": "method",
                    "parent_type": parent.strip(),
                    "arity": _count_args(args),
                    "arg_types": _split_arg_types(args),
                    "return_type": return_type,
                    "line": lineno,
                })
            continue

        mm = SIG_METHOD_RE.match(line)
        if not mm:
            mm = SIG_METHOD_SCOPE_RE.match(line)
        if mm:
            ret, parent, name, args = mm.groups()
            if _is_keyword(name, language):
                continue
            found.append({
                "name": name,
                "language": language,
                "source": source,
                "kind": "method",
                "parent_type": parent.strip(),
                "arity": _count_args(args),
                "arg_types": _split_arg_types(args),
                "return_type": _base_type(ret),
                "line": lineno,
            })
            continue

        gm = SIG_GLOBAL_RE.match(line)
        if gm:
            ret, name, args = gm.groups()
            if _is_keyword(name, language):
                continue
            if re.search(r'\)\s*=', args):
                continue
            found.append({
                "name": name,
                "language": language,
                "source": source,
                "kind": "global",
                "parent_type": None,
                "arity": _count_args(args),
                "arg_types": _split_arg_types(args),
                "return_type": _base_type(ret),
                "line": lineno,
            })
            continue

    return found
