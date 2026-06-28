#!/usr/bin/env python3
from __future__ import annotations
"""Check whether a byte signature uniquely identifies one instruction in a PE.

Scans the executable sections of a PE binary for a candidate pattern and reports
whether it matches 0 (stale), 1 (good), or N (ambiguous) locations. For unique
sigs it measures the uniqueness margin — how many trailing bytes are redundant;
for stale sigs it probes trailing-wildcard variants to locate the changed byte;
for any sig it can list near-misses to show which bytes to wildcard to widen.

Usage:
    python3 sig-uniqueness-checker.py <binary> --sig "48 8B ?? ?? ?? ??"
    python3 sig-uniqueness-checker.py <binary> --sig-file sigs.txt        # name=sig per line
    python3 sig-uniqueness-checker.py <binary> --sig "..." --sections .text,.rdata
    python3 sig-uniqueness-checker.py <binary> --sig "..." --near-misses 1
    python3 sig-uniqueness-checker.py <binary> --sig "..." --json
"""
import sys
import struct
import os
import json
import argparse
import subprocess



# ── PE parser imports ─────────────────────────────────────────────────────────
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.lib.pe_parse import parse_pe

def get_sections(data: bytes) -> list[dict]:
    try:
        pe = parse_pe(data)
    except SystemExit:
        return []
    sections = []
    for s in pe['sections']:
        sections.append({
            'name': s['name'],
            'raddr': s['raddr'],
            'rsize': s['rsize'],
            'vaddr': s['vaddr'],
            'exec': s['exec'],
        })
    return sections


def parse_pattern(text):
    """Parse '48 8B ?? ?? ..' into a list of ints (fixed) and None (wildcard)."""
    out = []
    for tok in text.replace(',', ' ').split():
        out.append(None if tok in ('?', '??') else int(tok, 16))  # int() raises on junk
    if not out:
        raise ValueError('empty pattern')
    return out


def format_pattern(pattern):
    return ' '.join('??' if b is None else f'{b:02X}' for b in pattern)


def scan(buf, pattern):
    """Yield start indices in buf where pattern (None = wildcard) matches."""
    n, m = len(buf), len(pattern)
    if m > n:
        return
    anchor = next((i for i, b in enumerate(pattern) if b is not None), None)
    if anchor is None:                       # all-wildcard pattern matches everywhere
        yield from range(n - m + 1)
        return
    fixed = [(i, b) for i, b in enumerate(pattern) if b is not None]
    needle = bytes([pattern[anchor]])
    # Anchor on the first fixed byte and skip with bytes.find — avoids scanning
    # every offset when the leading byte is rare.
    pos = buf.find(needle, anchor)
    while pos != -1 and pos - anchor + m <= n:
        start = pos - anchor
        if all(buf[start + i] == b for i, b in fixed):
            yield start
        pos = buf.find(needle, pos + 1)


def build_regions(data, sections):
    return [(s, data[s['raddr']:s['raddr'] + s['rsize']]) for s in sections]


def hits_for(regions, pattern):
    hits = []
    for sec, buf in regions:
        for idx in scan(buf, pattern):
            hits.append({'section': sec['name'],
                         'file_offset': sec['raddr'] + idx,
                         'rva': sec['vaddr'] + idx,
                         'context': buf[idx:idx + 16].hex(' ')})
    return hits


def count_for(regions, pattern):
    return sum(1 for _, buf in regions for _ in scan(buf, pattern))


def uniqueness_margin(regions, pattern):
    """Trailing bytes removable while the prefix still matches exactly once."""
    full = len(pattern)
    shortest = full
    for length in range(full - 1, 0, -1):
        # A prefix of a unique pattern can only match the same-or-more places,
        # so once a prefix is no longer unique, shorter ones never are either.
        if count_for(regions, pattern[:length]) == 1:
            shortest = length
        else:
            break
    return full - shortest


def trailing_probe(regions, pattern):
    """For a stale sig, wildcard the last 1/2/4 bytes to find the changed tail."""
    out = []
    for k in (1, 2, 4):
        if k >= len(pattern):
            continue
        probe = pattern[:-k] + [None] * k
        out.append({'wildcarded': k, 'matches': count_for(regions, probe)})
    return out


def near_misses(regions, pattern, max_dist, cap=20):
    """Positions matching all but <= max_dist of the fixed bytes."""
    fixed = [(i, b) for i, b in enumerate(pattern) if b is not None]
    m = len(pattern)
    found = []
    for sec, buf in regions:
        # ponytail: naive O(n*m) sweep, only runs when --near-misses is set.
        for start in range(len(buf) - m + 1):
            d, diff = 0, []
            for i, b in fixed:
                if buf[start + i] != b:
                    d += 1
                    diff.append(i)
                    if d > max_dist:
                        break
            if 1 <= d <= max_dist:
                found.append({'section': sec['name'],
                              'file_offset': sec['raddr'] + start,
                              'rva': sec['vaddr'] + start,
                              'distance': d, 'diff_indices': diff})
                if len(found) >= cap:
                    return found
    return found


def analyze(regions, name, pattern, near):
    hits = hits_for(regions, pattern)
    n = len(hits)
    res = {'name': name, 'pattern': format_pattern(pattern),
           'length': len(pattern), 'matches': n, 'hits': hits}
    if n == 1:
        margin = uniqueness_margin(regions, pattern)
        res['margin'] = margin
        if margin == 0:
            res['verdict'] = 'BRITTLE'
            res['hint'] = ('Every byte is load-bearing; one patched byte makes it stale. '
                           'Append stable trailing context for a safety margin.')
        elif margin >= 8:
            keep = len(pattern) - margin
            res['verdict'] = 'UNIQUE'
            res['hint'] = (f'Overspecified by {margin} bytes; could shorten to '
                           f'"{format_pattern(pattern[:keep])}" and stay unique.')
        else:
            res['verdict'] = 'UNIQUE'
            res['hint'] = f'Unique with a {margin}-byte margin.'
    elif n == 0:
        res['verdict'] = 'STALE'
        res['probe'] = trailing_probe(regions, pattern)
        hit = next((p for p in res['probe'] if p['matches'] >= 1), None)
        if hit:
            res['hint'] = (f'Wildcarding the last {hit["wildcarded"]} byte(s) yields '
                           f'{hit["matches"]} match(es) — a trailing byte changed; re-dump there.')
        else:
            res['hint'] = 'No trailing variant matches; the region moved or was removed. Re-generate.'
    else:
        res['verdict'] = 'AMBIGUOUS'
        res['hint'] = f'{n} matches; lengthen the sig with following bytes to disambiguate.'
    if near > 0:
        res['near_misses'] = near_misses(regions, pattern, near)
    return res


def print_result(r):
    print(f"SIG {r['name']} = {r['pattern']}  ({r['length']} bytes)")
    print(f"  Verdict: {r['verdict']}   Matches: {r['matches']}")
    for h in r['hits']:
        print(f"    {h['section']:<8} off=0x{h['file_offset']:X}  rva=0x{h['rva']:X}  ctx: {h['context']}")
    if 'margin' in r:
        print(f"  Margin: {r['margin']} trailing byte(s) removable while still unique")
    for p in r.get('probe', []):
        print(f"    last {p['wildcarded']} wildcarded -> {p['matches']} match(es)")
    for nm in r.get('near_misses', []):
        cols = ','.join(str(i) for i in nm['diff_indices'])
        print(f"    near rva=0x{nm['rva']:X}  dist={nm['distance']}  "
              f"differs at byte idx [{cols}] -> wildcard these to widen")
    print(f"  Hint: {r['hint']}\n")


def load_sigs(args):
    if args.sig:
        return [('sig', parse_pattern(args.sig))]
    out = []
    with open(args.sig_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            name, sep, sig = line.partition('=')
            if not sep or not sig.strip():
                raise ValueError(f'expected name=sig: {line}')
            out.append((name.strip(), parse_pattern(sig.strip())))
    if not out:
        raise ValueError('sig file has no entries')
    return out


def select(sections, names):
    if names:
        want = set(names)
        return [s for s in sections if s['name'] in want]
    return [s for s in sections if s['exec']]


def main():
    # Attempt to proxy to Rust binary if compiled
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_name = 'sig-uniqueness-checker.exe' if os.name == 'nt' else 'sig-uniqueness-checker'
    binary_path = os.path.join(base_dir, 'bin', bin_name)

    if os.path.exists(binary_path):
        try:
            res = subprocess.run([binary_path] + sys.argv[1:])
            sys.exit(res.returncode)
        except Exception:
            pass

    p = argparse.ArgumentParser(description='Check PE signature uniqueness')
    p.add_argument('binary', help='PE binary to scan')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--sig', help='single pattern, e.g. "48 8B ?? ?? ?? ??"')
    g.add_argument('--sig-file', help='file with one name=sig per line')
    p.add_argument('--sections', help='comma-separated section names (default: all executable)')
    p.add_argument('--near-misses', type=int, default=0, metavar='N',
                   help='also report matches within Hamming distance N on fixed bytes')
    p.add_argument('--json', action='store_true', help='machine-readable output')
    args = p.parse_args()

    if not os.path.isfile(args.binary):
        print(f"Error: {args.binary} not found", file=sys.stderr)
        sys.exit(1)
    with open(args.binary, 'rb') as f:
        data = f.read()
    sections = get_sections(data)
    if not sections:
        print("Error: not a PE file", file=sys.stderr)
        sys.exit(1)

    names = [n.strip() for n in args.sections.split(',')] if args.sections else None
    selected = select(sections, names)
    if not selected:
        print("Error: no matching sections to scan", file=sys.stderr)
        sys.exit(1)
    regions = build_regions(data, selected)

    try:
        sigs = load_sigs(args)
    except (ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    results = [analyze(regions, name, pat, args.near_misses) for name, pat in sigs]

    if args.json:
        print(json.dumps(results, indent=2))
        return
    print(f"File: {args.binary}  Sections scanned: {', '.join(s['name'] for s in selected)}\n")
    for r in results:
        print_result(r)


if __name__ == '__main__':
    main()
