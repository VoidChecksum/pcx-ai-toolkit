#!/usr/bin/env python3
"""Build LLM-readable index files for the pcx-ai-toolkit.

Generates four kinds of artifacts under docs/:

  1. llms.txt              — Anthropic / Mintlify llms.txt convention. Short,
                             structured directory of every doc grouped by
                             category, with URL + 1-line description. Tools
                             that auto-fetch this convention (Claude, Cursor,
                             Cline, etc.) discover the whole toolkit from one
                             file.

  2. llms-full.txt         — Full concatenation of every doc, skill, knowledge
                             file, rule, and template into a single text
                             stream with stable separators. For tools that can
                             ingest one big file but don't speak the llms.txt
                             convention.

  3. llms-perception-*.md  — Per-language context packs (Enma / AngelScript)
                             for tools like Cursor / Aider / Continue
                             that want to @-reference a single bundle scoped
                             to one scripting language.

  4. llms-skills.md /      — Per-category bundles (skills + knowledge) for
     llms-knowledge.md       deeper drilling.

The tool is idempotent: re-running it on a clean repo regenerates byte-
identical output. CI runs it with --check to detect drift between the
committed bundles and what the current source would produce.

Usage:
    python3 tools/build-llms-index.py                # regenerate everything
    python3 tools/build-llms-index.py --check        # diff vs committed; exit 1 if drift
    python3 tools/build-llms-index.py --out docs/    # custom output dir
    python3 tools/build-llms-index.py --quiet        # don't print per-file progress

Stdlib only — no pip dependencies.
"""
import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

# ── Repo layout ──────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_OUT  = REPO_ROOT / 'docs'

REPO_URL = 'https://github.com/VoidChecksum/pcx-ai-toolkit'
RAW_URL  = f'{REPO_URL}/raw/main'

# Categories: glob pattern -> (label, description for llms.txt section header)
CATEGORIES = [
    ('docs/enma/**/*.md',              'Enma Language Docs',     'The native Perception.cx scripting language: syntax, addons, SDK, lifecycle.'),
    ('docs/perception/*.md',           'Enma Platform APIs',     'The Perception.cx host API surface as exposed to Enma.'),
    ('docs/perception/angelscript/**/*.md', 'AngelScript APIs',  'The Perception.cx host API surface as exposed to AngelScript.'),
    ('docs/angelscript-lang/**/*.md', 'AngelScript Language (Core)', 'The core AngelScript language manual scraped from angelcode.com (zlib/libpng license): datatypes, strings, arrays, expressions, statements, functions, classes, handles, generics, delegates, enums, namespaces, coroutines, add-ons.'),
    ('.claude/skills/*/SKILL.md',      'AI Skills',              'Behavioral / discipline skills loaded automatically by AI tools (Claude Code / OMC).'),
    ('knowledge/*.md',                 'Knowledge References',   'Quick references for engines, anti-cheat architecture, patterns, methodology.'),
    ('rules/*.md',                     'IDE Drop-Ins',           'Project-rules drop-ins for Claude Code / Cursor / Cline / Copilot / Aider / Zed / Continue.'),
    ('templates/**/*.em',              'Enma Templates',         'Starter scripts; copy and customize for your project.'),
    ('templates/**/*.as',              'AngelScript Templates',  'Starter AngelScript scaffolds.'),
    ('signatures/*/*.md',              'Signatures & RE Guides', 'Engine-specific reversal guides (Source, UE, Unity IL2CPP, Source 2, anti-cheat, obfuscation).'),
    ('tools/*.py',                     'Standalone Tools',       'Stdlib-only Python tools for binary RE / sig validation / dumper conversion / linting.'),
    ('tools/*.sh',                     'Build Scripts',          'Bash scripts for pre-ship hygiene checks and one-shot installers.'),
]

# Skip generated outputs, lock files, and submodules
SKIP_PATTERNS = [
    re.compile(r'docs/llms[-_].*'),
    re.compile(r'docs/INDEX\.md$'),
    re.compile(r'docs/(perception/lua|lua-lang)/'),
    re.compile(r'\.claude/skills/pcx-lua-discipline/'),
    re.compile(r'knowledge/pcx-cross-language-bridge\.md$'),
    re.compile(r'lsp/'),
    re.compile(r'visualstudio/.*\.(vsix|dll|exe)$'),
    re.compile(r'tools/pe-parser/'),
    re.compile(r'tools/bin/'),
]

# ── Per-language bundle scoping ──────────────────────────────────────────────

LANG_BUNDLES = {
    'enma': {
        'title': 'Enma Context Pack',
        'desc':  'Single-file context pack for AI tools writing Enma scripts. Bundles the language docs, platform APIs, behavioral skills, and quick-reference knowledge most relevant when working in Enma.',
        'globs': [
            'docs/perception/llm-routing.md',
            'docs/enma/**/*.md',
            'docs/perception/*.md',
            '.claude/skills/game-cheat-guidelines/SKILL.md',
            '.claude/skills/game-hacking-pcx/SKILL.md',
            '.claude/skills/pcx-coding-discipline/SKILL.md',
            '.claude/skills/pcx-re-discipline/SKILL.md',
            '.claude/skills/pcx-perf-budget/SKILL.md',
            '.claude/skills/pcx-patch-day-playbook/SKILL.md',
            '.claude/skills/re-evidence-log/SKILL.md',
            'knowledge/pcx-api-cheatsheet.md',
            'knowledge/enma-cheatsheet.md',
            'knowledge/common-patterns.md',
            'knowledge/aimbot-math.md',
            'knowledge/offset-methodology.md',
        ],
    },
    'angelscript': {
        'title': 'AngelScript Context Pack',
        'desc':  'Single-file context pack for AI tools writing AngelScript scripts on Perception.cx. Bundles the AngelScript API surface, the discipline skill, and cross-references to the underlying 12 guidelines.',
        'globs': [
            'docs/perception/llm-routing.md',
            'docs/perception/angelscript/**/*.md',
            'docs/angelscript-lang/**/*.md',
            '.claude/skills/pcx-angelscript-discipline/SKILL.md',
            '.claude/skills/game-cheat-guidelines/SKILL.md',
            '.claude/skills/game-hacking-pcx/SKILL.md',
            'knowledge/pcx-api-cheatsheet.md',
        ],
    },
}

# ── File metadata extraction ─────────────────────────────────────────────────

def is_skipped(rel_path: str) -> bool:
    return any(p.search(rel_path) for p in SKIP_PATTERNS)


def extract_title_and_desc(path: Path) -> tuple[str, str]:
    """Pull first H1 (or filename) as title and first non-empty prose line as description."""
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return (path.stem, '')

    title = path.stem
    desc = ''
    seen_h1 = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(('---', '```', '#!')):
            continue
        if line.startswith('# ') and not seen_h1:
            title = line[2:].strip()
            seen_h1 = True
            continue
        if line.startswith(('## ', '### ', '> ', '|', '-', '*', '+', '<')):
            continue
        # First non-heading prose line wins for description
        if seen_h1 and not desc:
            # Strip markdown emphasis / inline code
            cleaned = re.sub(r'[`*_]', '', line)
            cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
            desc = cleaned[:200]
            break
    return (title, desc)


def find_files(glob: str) -> list[Path]:
    out = []
    for p in sorted(REPO_ROOT.glob(glob), key=lambda x: str(x.relative_to(REPO_ROOT)).replace(os.sep, '/')):
        if not p.is_file():
            continue
        rel = str(p.relative_to(REPO_ROOT)).replace(os.sep, '/')
        if is_skipped(rel):
            continue
        out.append(p)
    return out


# ── llms.txt builder (Anthropic / Mintlify convention) ───────────────────────

def build_llms_txt() -> str:
    """Build the llms.txt index — short, structured, link-heavy."""
    out = []
    out.append('# pcx-ai-toolkit')
    out.append('')
    out.append('> AI-powered scripting toolkit for the Perception.cx game-hacking research platform. '
               'Ships behavioral skills, language and API references, reverse-engineering knowledge, '
               'discipline rules, multi-IDE drop-ins, and stdlib-only Python tools. '
               'MIT-licensed and public.')
    out.append('')
    out.append('Repository: ' + REPO_URL)
    out.append('License: MIT')
    out.append('')
    out.append('## Overview')
    out.append('')
    out.append('See `docs/INDEX.md` for the complete file index. The most useful single-file context '
               'packs are listed below per language.')
    out.append('')
    out.append('## Single-File Context Packs')
    out.append('')
    for lang_id, b in LANG_BUNDLES.items():
        url = f'{RAW_URL}/docs/llms-perception-{lang_id}.md'
        out.append(f'- [{b["title"]}]({url}): {b["desc"]}')
    out.append(f'- [Full Skills Bundle]({RAW_URL}/docs/llms-skills.md): every AI skill in one file.')
    out.append(f'- [Full Knowledge Bundle]({RAW_URL}/docs/llms-knowledge.md): every knowledge reference in one file.')
    out.append(f'- [Full Toolkit Bundle]({RAW_URL}/docs/llms-full.txt): the entire toolkit concatenated.')
    out.append('')

    for glob, label, label_desc in CATEGORIES:
        files = find_files(glob)
        if not files:
            continue
        out.append(f'## {label}')
        out.append('')
        if label_desc:
            out.append(label_desc)
            out.append('')
        for p in files:
            rel = str(p.relative_to(REPO_ROOT)).replace(os.sep, '/')
            title, desc = extract_title_and_desc(p)
            url = f'{RAW_URL}/{rel}'
            line = f'- [{title}]({url})'
            if desc:
                line += f': {desc}'
            out.append(line)
        out.append('')

    return '\n'.join(out).rstrip() + '\n'


# ── Concatenated bundle builder ──────────────────────────────────────────────

def build_concat_bundle(title: str, description: str, files: list[Path]) -> str:
    """Concatenate files into one bundle with stable separators + source paths."""
    out = []
    out.append(f'# {title}')
    out.append('')
    out.append(f'> {description}')
    out.append('')
    out.append('> **Generated** by `tools/build-llms-index.py` — do not edit manually. '
               'Re-generate by running the tool from the repo root. CI verifies the committed '
               'bundle matches the current source.')
    out.append('')
    out.append(f'**Source files included: {len(files)}**')
    out.append('')
    out.append('---')
    out.append('')

    for p in files:
        rel = str(p.relative_to(REPO_ROOT)).replace(os.sep, '/')
        try:
            content = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            content = ''
        out.append(f'## Source: `{rel}`')
        out.append('')
        out.append(content.rstrip())
        out.append('')
        out.append('---')
        out.append('')

    # Trim trailing separator
    while out and out[-1] in ('', '---'):
        out.pop()
    return '\n'.join(out) + '\n'


def build_llms_full() -> str:
    files = []
    seen = set()
    for glob, _label, _desc in CATEGORIES:
        # Skip binary tools + signatures-only files from the full bundle to keep
        # it focused on prose / docs / skills / knowledge. Tools are referenced
        # from llms.txt but not inlined.
        if glob.startswith('tools/'):
            continue
        for p in find_files(glob):
            if p in seen:
                continue
            seen.add(p)
            files.append(p)
    desc = ('Full text concatenation of every doc, skill, knowledge reference, IDE drop-in, '
            'signature guide, and template in the pcx-ai-toolkit. ~MB-sized; load into AI tools '
            'that accept a single bundle. For per-language context, use the smaller '
            'llms-perception-{enma,angelscript}.md packs instead.')
    return build_concat_bundle('pcx-ai-toolkit — Full Bundle', desc, files)


def build_lang_bundle(lang_id: str) -> str:
    b = LANG_BUNDLES[lang_id]
    files = []
    seen = set()
    for glob in b['globs']:
        for p in find_files(glob):
            if p in seen:
                continue
            seen.add(p)
            files.append(p)
    return build_concat_bundle(b['title'], b['desc'], files)


def build_skills_bundle() -> str:
    files = find_files('.claude/skills/*/SKILL.md')
    desc = ('Every AI skill in the pcx-ai-toolkit concatenated into one file. Drop into '
            'tools that load a single context document, or @-reference from Cursor / Aider / '
            'Continue when you want the full behavioral discipline surface available.')
    return build_concat_bundle('pcx-ai-toolkit — Skills Bundle', desc, files)


def build_knowledge_bundle() -> str:
    files = find_files('knowledge/*.md')
    desc = ('Every knowledge reference in the pcx-ai-toolkit concatenated into one file. '
            'Covers engine RE references, anti-cheat architecture, common scripting patterns, '
            'aimbot math, API cheatsheets, GUI design, multi-binary organization, network protocol RE, '
            'and the cross-language bridge.')
    return build_concat_bundle('pcx-ai-toolkit — Knowledge Bundle', desc, files)


# ── Orchestration ────────────────────────────────────────────────────────────

GENERATORS = {
    'llms.txt':                       build_llms_txt,
    'llms-full.txt':                  build_llms_full,
    'llms-perception-enma.md':        lambda: build_lang_bundle('enma'),
    'llms-perception-angelscript.md': lambda: build_lang_bundle('angelscript'),
    'llms-skills.md':                 build_skills_bundle,
    'llms-knowledge.md':              build_knowledge_bundle,
}


def short_hash(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def write_outputs(out_dir: Path, quiet: bool) -> dict[str, str]:
    """Generate all outputs; write to out_dir; return path -> sha1 prefix map."""
    out_dir.mkdir(parents=True, exist_ok=True)
    digests = {}
    for name, gen in GENERATORS.items():
        text = gen()
        path = out_dir / name
        path.write_text(text, encoding='utf-8')
        digests[name] = short_hash(text)
        if not quiet:
            size_kb = len(text.encode('utf-8')) / 1024
            print(f'  wrote {path.relative_to(REPO_ROOT)}  ({size_kb:.1f} KB, sha {digests[name]})')
    return digests


def check_drift(out_dir: Path, quiet: bool) -> int:
    """Compare current committed bundles vs. what regeneration would produce."""
    drift = []
    for name, gen in GENERATORS.items():
        path = out_dir / name
        expected = gen()
        if not path.exists():
            drift.append(f'  MISSING: {path.relative_to(REPO_ROOT)}')
            continue
        actual = path.read_text(encoding='utf-8', errors='ignore')
        if actual != expected:
            drift.append(f'  DRIFT: {path.relative_to(REPO_ROOT)}  '
                         f'(committed sha {short_hash(actual)} vs. expected {short_hash(expected)})')
    if drift:
        print('llms-index drift detected:')
        for line in drift:
            print(line)
        print()
        print('Re-run: python3 tools/build-llms-index.py')
        return 1
    if not quiet:
        print('llms-index in sync (all generated bundles match source).')
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description='Build LLM-readable index for pcx-ai-toolkit')
    p.add_argument('--out',   default=str(DOCS_OUT), help='output directory (default: docs/)')
    p.add_argument('--check', action='store_true',  help='check for drift, exit 1 if regen would differ')
    p.add_argument('--quiet', action='store_true',  help='suppress per-file progress')
    args = p.parse_args()

    out_dir = Path(args.out).resolve()
    if args.check:
        return check_drift(out_dir, args.quiet)
    write_outputs(out_dir, args.quiet)
    return 0


if __name__ == '__main__':
    sys.exit(main())
