#!/usr/bin/env python3
"""Build and query a tiny local hybrid knowledge index for pcx-ai-toolkit."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / ".pcx" / "index" / "knowledge-vectors.jsonl"
CATEGORIES = {
    "docs": ["docs/**/*.md", "docs/**/*.txt"],
    "skills": [".claude/skills/**/*.md"],
    "knowledge": ["knowledge/**/*.md"],
    "rules": ["rules/*.md"],
    "templates": ["templates/**/*.md", "templates/**/*.em", "templates/**/*.as"],
    "tools": ["tools/*.py"],
    "signatures": ["signatures/**/*.md"],
    "mcp": ["mcp/**/*.md", "mcp/**/*.json"],
    "evals": ["evals/**/*.json", "evals/**/*.md"],
}
SKIP_PARTS = {".git", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache"}
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
DIM = 256


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def corpus_files() -> list[Path]:
    files: list[Path] = []
    for globs in CATEGORIES.values():
        for pattern in globs:
            for path in REPO_ROOT.glob(pattern):
                if not path.is_file():
                    continue
                if any(part in SKIP_PARTS for part in path.parts):
                    continue
                files.append(path)
    return sorted(set(files), key=rel)


def vector(tokens: list[str]) -> dict[str, float]:
    counts: dict[int, int] = {}
    for token in tokens:
        h = int(hashlib.blake2b(token.encode(), digest_size=4).hexdigest(), 16) % DIM
        counts[h] = counts.get(h, 0) + 1
    norm = math.sqrt(sum(v * v for v in counts.values())) or 1.0
    return {str(k): round(v / norm, 6) for k, v in counts.items()}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())


def snippet(text: str, terms: set[str], width: int = 220) -> str:
    for line in text.splitlines():
        low = line.lower()
        if any(term in low for term in terms):
            return line.strip()[:width]
    return (text.splitlines() or [""])[0][:width]


def build_index(out: Path = INDEX_PATH) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in corpus_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        toks = tokenize(text + " " + rel(path))
        if not toks:
            continue
        rows.append({
            "path": rel(path),
            "tokens": sorted(set(toks))[:2000],
            "vector": vector(toks),
            "title": next((ln.lstrip("# ").strip() for ln in text.splitlines() if ln.startswith("#")), rel(path)),
            "bytes": len(text.encode("utf-8")),
        })
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
    
    try:
        shown = str(out.relative_to(REPO_ROOT))
    except ValueError:
        shown = str(out)
    return {"ok": True, "path": shown, "documents": len(rows), "dimensions": DIM}


def load_index(path: Path = INDEX_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def search(query: str, limit: int = 10, index_path: Path = INDEX_PATH) -> list[dict[str, Any]]:
    rows = load_index(index_path)
    qtokens = tokenize(query)
    qset = set(qtokens)
    qvec = vector(qtokens)
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        tokens = set(row.get("tokens", []))
        overlap = len(qset & tokens)
        path_boost = sum(1 for token in qset if token in row.get("path", "").lower())
        score = cosine(qvec, row.get("vector", {})) * 10 + overlap * 2 + path_boost * 3
        if score <= 0:
            continue
        p = REPO_ROOT / row["path"]
        text = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
        scored.append((score, {"path": row["path"], "score": round(score, 3), "title": row.get("title", row["path"]), "snippet": snippet(text, qset)}))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[: max(1, min(limit, 50))]]


def main() -> int:
    ap = argparse.ArgumentParser(prog="pcx knowledge", description="Build/query local PCX knowledge index")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-vector-index")
    b.add_argument("--out", type=Path, default=INDEX_PATH)
    s = sub.add_parser("search")
    s.add_argument("query", nargs="+")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--index", type=Path, default=INDEX_PATH)
    args = ap.parse_args()
    if args.cmd == "build-vector-index":
        print(json.dumps(build_index(args.out), indent=2))
        return 0
    if args.cmd == "search":
        if not args.index.exists():
            build_index(args.index)
        print(json.dumps(search(" ".join(args.query), args.limit, args.index), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
