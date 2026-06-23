"""Lightweight, regex-based parsers for Enma, AngelScript, and Lua scripts.

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
    out = []
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


def strip_lua_comments(code: str) -> str:
    """Remove Lua -- and --[[ ]] comments."""
    out = []
    i = 0
    n = len(code)
    while i < n:
        if code[i : i + 2] == "--" and code[i : i + 4] != "--[[":
            out.append(" ")
            i = code.find("\n", i)
            if i == -1:
                break
            continue
        if code[i : i + 4] == "--[[":
            out.append(" ")
            j = code.find("--]]", i + 4)
            if j == -1:
                break
            i = j + 4
            continue
        out.append(code[i])
        i += 1
    return "".join(out)


def strip_strings(code: str) -> str:
    """Blank out double-quoted and single-quoted string contents."""
    out = []
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


def strip_lua_strings(code: str) -> str:
    """Blank out Lua double-quoted, single-quoted, and [[ ]] strings."""
    out = []
    i = 0
    n = len(code)
    while i < n:
        ch = code[i]
        if ch == '"' or ch == "'":
            quote = ch
            out.append(quote)
            i += 1
            while i < n:
                c = code[i]
                if c == "\\":
                    out.extend([" ", " "])
                    i += 2
                    continue
                if c == quote:
                    out.append(quote)
                    i += 1
                    break
                out.append(" ")
                i += 1
            continue
        if code[i : i + 2] == "[[":
            out.append("[[")
            j = code.find("]]", i + 2)
            if j == -1:
                out.append(" " * (n - i - 2))
                break
            out.append(" " * (j - i - 2))
            out.append("]]")
            i = j + 2
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
    clean = strip_c_comments(strip_strings(code))
    out: list[str] = []
    for line in clean.splitlines():
        m = AS_IMPORT_RE.match(line)
        if m:
            out.append(m.group(1))
    return out


def extract_lua_requires(code: str) -> list[str]:
    """Return Lua require() / dofile() targets if present."""
    clean = strip_lua_comments(strip_lua_strings(code))
    return re.findall(r'\brequire\s*\(\s*"([^"]+)"\s*\)', clean)


# ── Calls ────────────────────────────────────────────────────────────────────

CALL_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(')
METHOD_CALL_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\(')
LUA_COLON_CALL_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\:([A-Za-z_][A-Za-z0-9_]*)\s*\(')


def _is_keyword(name: str, lang: str) -> bool:
    common = {
        "if", "else", "for", "while", "do", "switch", "case", "default",
        "return", "break", "continue", "goto", "sizeof", "typeof", "cast",
        "new", "delete", "try", "catch", "throw", "namespace", "using",
        "public", "private", "protected", "static", "const", "constexpr",
        "class", "struct", "enum", "union", "template", "typename",
        "interface", "mixin", "funcdef", "true", "false", "null",
    }
    lua_keywords = {
        "and", "or", "not", "then", "end", "in", "local", "function",
        "repeat", "until", "elseif", "return", "if", "else", "for",
        "while", "do", "true", "false", "nil",
    }
    if lang == "lua":
        return name in lua_keywords
    return name in common


def _strip_for_calls(code: str, lang: str) -> str:
    if lang == "lua":
        return strip_lua_comments(strip_lua_strings(code))
    return strip_c_comments(strip_strings(code))


def extract_calls(code: str, lang: str) -> list[tuple[str, int]]:
    """Return (name, line) for every function-like call.

    For method calls the method name is reported, not the object.
    """
    clean = _strip_for_calls(code, lang)
    calls: list[tuple[str, int]] = []
    for lineno, line in enumerate(clean.splitlines(), 1):
        simple = METHOD_CALL_RE.sub(lambda m: f" {m.group(2)}(", line)
        simple = LUA_COLON_CALL_RE.sub(lambda m: f" {m.group(2)}(", simple)
        for m in CALL_RE.finditer(simple):
            name = m.group(1)
            if _is_keyword(name, lang):
                continue
            calls.append((name, lineno))
    return calls


# ── Declarations ────────────────────────────────────────────────────────────

DECL_RE = re.compile(
    r'^\s*(?:const\s+)?(?:nullable\s+)?'
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*\s]*?)\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)'
    r'(?:\s*[=;]|\s*,)',
    re.MULTILINE,
)
LUA_LOCAL_DECL_RE = re.compile(r'^\s*local\s+([A-Za-z_][A-Za-z0-9_\,\s]*)\s*=')
LUA_ASSIGN_RE = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=')


def extract_declarations(code: str, lang: str) -> list[tuple[str, str, int]]:
    """Return (type, name, line) for variable/parameter declarations.

    For Lua, type is "" and the name is the variable being assigned.
    """
    if lang == "lua":
        clean = strip_lua_comments(strip_lua_strings(code))
        out: list[tuple[str, str, int]] = []
        for lineno, line in enumerate(clean.splitlines(), 1):
            m = LUA_LOCAL_DECL_RE.match(line)
            if m:
                for n in m.group(1).split(","):
                    out.append(("", n.strip(), lineno))
                continue
            m = LUA_ASSIGN_RE.match(line)
            if m:
                out.append(("", m.group(1), lineno))
        return out

    clean = strip_c_comments(strip_strings(code))
    out = []
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
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*\s]*?)\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*(?:\{|;)'
)


def extract_function_defs(code: str, lang: str) -> list[tuple[str, int]]:
    """Return (name, line) for function definitions in supported PCX languages."""
    out: list[tuple[str, int]] = []
    if lang == "lua":
        clean = strip_lua_comments(strip_lua_strings(code))
        for lineno, line in enumerate(clean.splitlines(), 1):
            m = re.match(r'^\s*(?:local\s+)?function\s+([A-Za-z_][A-Za-z0-9_\.:]*)\s*\(', line)
            if m:
                out.append((m.group(1).rsplit(":", 1)[-1].rsplit(".", 1)[-1], lineno))
        return out

    clean = strip_c_comments(strip_strings(code))
    for lineno, line in enumerate(clean.splitlines(), 1):
        m = FUNC_DEF_RE.match(line)
        if m:
            name = m.group(2)
            if _is_keyword(name, lang):
                continue
            out.append((name, lineno))
    return out


# ── Signature extraction from documentation code blocks ───────────────────────

SIG_GLOBAL_RE = re.compile(
    r'^\s*(?:const\s+)?'
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*\s]*?)\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*;?\s*$',
)
SIG_METHOD_RE = re.compile(
    r'^\s*(?:const\s+)?'
    r'([A-Za-z_][A-Za-z0-9_\u003c\u003e,\[\]\*\s]*?)\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*;?\s*$',
)
# Slash-abbreviated method signatures, e.g.
#   uint8/16/32/64 proc.ru8/ru16/ru32/ru64(uint64 addr);
#   bool proc.wu8/wu16/wu32/wu64(uint64 addr, uintN v);
# The return width and every method name after a '/' are expanded into one
# signature per concrete name so the index doesn't miss ru16/ru32/ru64 etc.
SIG_METHOD_SLASH_RE = re.compile(
    r'^\s*(?:const\s+)?'
    r'([A-Za-z_][A-Za-z0-9_]*)'            # base return type (first width)
    r'(?:/[0-9A-Za-z_]+)*\s+'              # optional slash-abbreviated return widths
    r'([A-Za-z_][A-Za-z0-9_]*)\.'          # parent type
    r'([A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)+)\s*'  # slash-abbreviated names
    r'\(([^)]*)\)\s*;?\s*$',
)
LUA_FUNC_RE = re.compile(
    r'^\s*(?:local\s+)?function\s+([A-Za-z_][A-Za-z0-9_\.:]*)\s*\(([^)]*)\)\s*$',
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
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = re.match(r'(?:const\s+)?(?:in\s+|out\+|&?\s*)?([A-Za-z_][A-Za-z0-9_]*)', p)
        if m:
            out.append(m.group(1))
    return out


def _base_type(t: str) -> str:
    t = t.strip().rstrip("@").replace("&", "").replace("*", "").strip()
    t = re.sub(r'<.*>', "", t)
    t = re.sub(r'\[.*\]', "", t)
    return t.strip()


def extract_api_signatures(text: str, language: str, source: str) -> list[dict[str, object]]:
    """Yield signature dicts from a markdown code fence body."""
    found: list[dict[str, object]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        mm = SIG_METHOD_RE.match(line)
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

        if language == "lua":
            lm = LUA_FUNC_RE.match(line)
            if lm:
                fullname, args = lm.groups()
                parent = None
                if ":" in fullname:
                    parent, name = fullname.rsplit(":", 1)
                elif "." in fullname:
                    parent, name = fullname.rsplit(".", 1)
                else:
                    name = fullname
                if _is_keyword(name, language):
                    continue
                found.append({
                    "name": name,
                    "language": language,
                    "source": source,
                    "kind": "method" if parent else "global",
                    "parent_type": parent,
                    "arity": _count_args(args),
                    "arg_types": _split_arg_types(args),
                    "return_type": "",
                    "line": lineno,
                })
    return found
