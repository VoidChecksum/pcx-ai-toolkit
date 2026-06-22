#!/usr/bin/env python3
"""Validate an Enma offset module against its per-binary RE evidence log.

Cross-checks offsets.em against evidence/<hash>.md (per the re-evidence-log
skill): every offset must cite an E-NNN entry, every entry should be cited by
some offset, claims should be re-verified within a freshness window, and
UNVERIFIED offsets are surfaced for the author's awareness.

Usage:
    python3 evidence-log-validator.py offsets.em --evidence evidence/7a3f.md
    python3 evidence-log-validator.py offsets.em --evidence-dir evidence/
    python3 evidence-log-validator.py offsets.em --evidence-dir evidence/ --max-age-days 90
    python3 evidence-log-validator.py offsets.em --evidence-dir evidence/ --json
    python3 evidence-log-validator.py offsets.em --evidence-dir evidence/ --strict

Exit: 0 = clean, 1 = errors (or warnings under --strict), 2 = bad usage.
"""
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import date, datetime


# ── Parse rules (tolerant of formatting variation) ────────────────────────────

# const <type> OFF_NAME ...   |   const string SIG_NAME ...
OFFSET_RE = re.compile(r'^\s*const\s+(?:\w+\s+(OFF_\w+)|string\s+(SIG_\w+))\b')
# E-NNN citation as it appears in offsets.em comments (// E-003) and headers.
CITE_RE = re.compile(r'\bE-(\d+)\b', re.I)
UNVERIFIED_RE = re.compile(r'\bUNVERIFIED\b', re.I)
# H2 evidence entry header: "## E-001 — entity_list global pointer"
ENTRY_RE = re.compile(r'^##\s+E-(\d+)\s*[—\-]')
# last_verified field, either "last_verified: 2026-06-17" or a "| last_verified | ... |" row.
LASTVER_RE = re.compile(r'last_verified', re.I)
DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')


def eid(num_str):
    """Canonical display id, integer-normalized so E-3 == E-003."""
    return 'E-%03d' % int(num_str)


def comment_text(line):
    """Return the // comment portion of a line, or '' if none."""
    i = line.find('//')
    return line[i + 2:] if i != -1 else ''


# ── Offset module ─────────────────────────────────────────────────────────────

def parse_offsets(path):
    """Return list of offset dicts: name, line, cites (set of ints), unverified."""
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()
    offsets = []
    for n, line in enumerate(lines):
        m = OFFSET_RE.match(line)
        if not m:
            continue
        name = m.group(1) or m.group(2)
        # Citation/UNVERIFIED may sit on the same line's comment or the line above.
        scope = comment_text(line)
        if n > 0:
            prev = lines[n - 1].strip()
            if prev.startswith('//'):
                scope += ' ' + comment_text(prev)
        cites = {int(c) for c in CITE_RE.findall(scope)}
        offsets.append({
            'name': name,
            'line': n + 1,
            'cites': cites,
            'unverified': bool(UNVERIFIED_RE.search(scope)),
        })
    return offsets


# ── Evidence files ────────────────────────────────────────────────────────────

def parse_evidence(path):
    """Return list of entry dicts: id (int), id_str, source, line, last_verified (date|None)."""
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()
    src = str(path)
    # Find entry header line numbers, then slice each entry's body to the next header.
    heads = [(n, int(m.group(1))) for n, line in enumerate(lines)
             for m in [ENTRY_RE.match(line)] if m]
    entries = []
    for idx, (n, num) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        body = lines[n:end]
        # An entry's freshness is its newest last_verified date (rule #5 keeps a history).
        dates = []
        for bl in body:
            if LASTVER_RE.search(bl):
                dates += [_parse_date(d) for d in DATE_RE.findall(bl)]
        dates = [d for d in dates if d]
        entries.append({
            'id': num,
            'id_str': eid(str(num)),
            'source': src,
            'line': n + 1,
            'last_verified': max(dates) if dates else None,
        })
    return entries


def _parse_date(s):
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def collect_evidence(files):
    entries = []
    for f in files:
        entries += parse_evidence(f)
    return entries


# ── Validation ────────────────────────────────────────────────────────────────

def validate(offsets, entries, max_age_days, today):
    """Produce findings: list of dicts {level, category, message}."""
    known = {e['id'] for e in entries}
    referenced = set()
    for o in offsets:
        referenced |= o['cites']

    findings = []

    for o in offsets:
        loc = '%s (line %d)' % (o['name'], o['line'])
        if not o['cites']:
            findings.append(_f('ERROR', 'uncited',
                               '%s has no E-NNN evidence citation' % loc))
        else:
            missing = sorted(c for c in o['cites'] if c not in known)
            for c in missing:
                findings.append(_f('ERROR', 'missing-entry',
                                   '%s cites %s, absent from every evidence file'
                                   % (loc, eid(str(c)))))
        if o['unverified']:
            findings.append(_f('INFO', 'unverified',
                               '%s is marked UNVERIFIED (guideline #1)' % loc))

    for e in entries:
        where = '%s in %s' % (e['id_str'], e['source'])
        if e['id'] not in referenced:
            findings.append(_f('WARN', 'dead-entry',
                               '%s is referenced by no offset (deprecated, or stale citation?)'
                               % where))
        if e['last_verified'] is not None:
            age = (today - e['last_verified']).days
            if age > max_age_days:
                findings.append(_f('WARN', 'stale',
                                   '%s last_verified %s (%d days old, threshold %d)'
                                   % (where, e['last_verified'].isoformat(), age, max_age_days)))

    return findings


def _f(level, category, message):
    return {'level': level, 'category': category, 'message': message}


# ── Reporting ─────────────────────────────────────────────────────────────────

ORDER = ('ERROR', 'WARN', 'INFO')


def summarize(findings):
    counts = {lvl: 0 for lvl in ORDER}
    for f in findings:
        counts[f['level']] += 1
    return counts


def exit_code(counts, strict):
    if counts['ERROR'] > 0:
        return 1
    if strict and counts['WARN'] > 0:
        return 1
    return 0


def print_report(offsets, entries, findings, counts, code):
    print('Offsets parsed: %d   Evidence entries: %d' % (len(offsets), len(entries)))
    if not findings:
        print('\nClean: every offset cites a live, fresh evidence entry.')
        return
    for lvl in ORDER:
        items = [f for f in findings if f['level'] == lvl]
        if not items:
            continue
        print('\n[%s]  (%d)' % (lvl, len(items)))
        for f in items:
            print('  %-13s %s' % (f['category'], f['message']))
    print('\nSummary: %d ERROR, %d WARN, %d INFO  (exit %d)'
          % (counts['ERROR'], counts['WARN'], counts['INFO'], code))


# ── CLI ───────────────────────────────────────────────────────────────────────

def resolve_evidence(args):
    """Collect evidence file paths from --evidence and --evidence-dir; '' on error."""
    files = []
    for p in args.evidence:
        fp = Path(p)
        if not fp.is_file():
            return None, 'not a file: %s' % p
        files.append(fp)
    if args.evidence_dir:
        d = Path(args.evidence_dir)
        if not d.is_dir():
            return None, 'not a directory: %s' % args.evidence_dir
        files += sorted(f for f in d.glob('*.md') if f.name.lower() != 'readme.md')
    if not files:
        return None, 'no evidence files (pass --evidence or --evidence-dir)'
    return files, None


def main():
    p = argparse.ArgumentParser(description='Validate offsets.em against its RE evidence log')
    p.add_argument('offsets', help='Enma offset module (offsets.em)')
    p.add_argument('--evidence', action='append', default=[], metavar='FILE',
                   help='per-binary evidence file (repeatable)')
    p.add_argument('--evidence-dir', metavar='DIR',
                   help='directory of per-binary evidence *.md files')
    p.add_argument('--max-age-days', type=int, default=180,
                   help='staleness threshold for last_verified (default 180)')
    p.add_argument('--json', action='store_true', help='emit JSON instead of text')
    p.add_argument('--strict', action='store_true', help='warnings also force exit 1')
    args = p.parse_args()

    if not Path(args.offsets).is_file():
        print('error: not a file: %s' % args.offsets, file=sys.stderr)
        sys.exit(2)
    files, err = resolve_evidence(args)
    if err:
        print('error: %s' % err, file=sys.stderr)
        sys.exit(2)

    offsets = parse_offsets(args.offsets)
    entries = collect_evidence(files)
    findings = validate(offsets, entries, args.max_age_days, date.today())
    counts = summarize(findings)
    code = exit_code(counts, args.strict)

    if args.json:
        print(json.dumps({
            'offsets': len(offsets), 'entries': len(entries),
            'findings': findings, 'summary': counts, 'exit': code,
        }, indent=2))
    else:
        print_report(offsets, entries, findings, counts, code)
    sys.exit(code)


if __name__ == '__main__':
    main()
