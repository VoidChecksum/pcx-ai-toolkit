#!/usr/bin/env python3
"""Convert byte patterns (signatures) between RE-tool formats.

A signature is a sequence of fixed bytes and wildcards. Every tool spells it
differently: IDA uses ``?``, Ghidra uses ``..``, x64dbg/Cheat Engine use
``??``, C-style code splits it into a byte string plus a mask. This tool reads
one form and prints any other — most usefully ``--to all`` to get every form
of a sig at once when porting it between IDA, Ghidra, x64dbg, CE, and Enma.

Supported formats (both --from and --to):
    ida       48 8B ? ? ? ?              IDA Pro (single ?, also accepts ??)
    ghidra    48 8b .. .. .. ..          Ghidra (lowercase, .. ; also accepts ??)
    x64dbg    48 8B ?? ?? ?? ??          x64dbg Find Pattern dialog
    ce        48 8B ?? ?? ?? ??          Cheat Engine AOB scan
    enma      "48 8B ?? ?? ?? ??"        quoted, paste into find_code_pattern()
    cstyle    "\\x48\\x8B..." "xx????"     two-string pattern + mask
    bytes     b"\\x48\\x8B..."  # mask     Python bytes literal + mask comment
    sig_mask  48 8B 00 00 / xx????       hex pattern + mask, one line each

Formats cstyle, bytes, and sig_mask encode wildcards in a separate mask, so
they require --mask when used as --from.

Usage:
    python3 pattern-format-converter.py --from ida --to enma --pat "48 8B ? ? ? ?"
    python3 pattern-format-converter.py --from cstyle --to ida --pat "\\x48\\x8B\\x00\\x00" --mask "xx??"
    python3 pattern-format-converter.py --from ida --to all --pat "48 8B ?? ?? ?? ??"
    python3 pattern-format-converter.py --from sig_mask --to enma --pat "48 8B 00 00" --mask "xx??" --json
"""
import sys
import json
import argparse
import os
import subprocess

FORMATS = ['ida', 'ghidra', 'x64dbg', 'ce', 'enma', 'cstyle', 'bytes', 'sig_mask']
MASK_FORMATS = ('cstyle', 'bytes', 'sig_mask')  # need a separate mask to parse
HEX = set('0123456789abcdefABCDEF')

# A normalized pattern is a list where each element is an int byte (0-255)
# or None for a wildcard. All parsing converts to this; all emitting reads it.


def _strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in '"\'':
        s = s[1:-1]
    return s


def _hex_byte(tok):
    """Parse a 2-char hex token, or raise. Rejects odd length / non-hex."""
    if len(tok) != 2 or not (tok[0] in HEX and tok[1] in HEX):
        raise ValueError(f"invalid hex byte {tok!r} (need 2 hex digits)")
    return int(tok, 16)


def parse_tokens(pat):
    """Parse space-separated tokens with inline wildcards (?, ??, ..)."""
    norm = []
    for tok in pat.split():
        if tok in ('?', '??', '..'):
            norm.append(None)
        else:
            norm.append(_hex_byte(tok))
    if not norm:
        raise ValueError("empty pattern")
    return norm


def parse_escapes(pat):
    """Parse a \\xHH...\\xHH byte literal (cstyle/bytes), ignoring b/quotes."""
    s = _strip_quotes(pat.strip()[1:] if pat.strip()[:1] in 'bB' else pat)
    vals, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s) and s[i + 1] in 'xX':
            vals.append(_hex_byte(s[i + 2:i + 4]))
            i += 4
        else:
            raise ValueError(f"unexpected char {s[i]!r} in byte literal")
    if not vals:
        raise ValueError("empty pattern")
    return vals


def apply_mask(byte_vals, mask):
    """Combine raw bytes with a mask string (x = keep, ? or . = wildcard)."""
    if mask is None:
        raise ValueError("this --from format requires --mask")
    mask = _strip_quotes(mask)
    if len(mask) != len(byte_vals):
        raise ValueError(f"mask length {len(mask)} != byte count {len(byte_vals)}")
    norm = []
    for b, m in zip(byte_vals, mask):
        if m == 'x':
            norm.append(b)
        elif m in '?.':
            norm.append(None)
        else:
            raise ValueError(f"invalid mask char {m!r} (use x, ?, or .)")
    return norm


def to_norm(fmt, pat, mask):
    """Parse any supported input format into the normalized list."""
    if fmt == 'enma':
        return parse_tokens(_strip_quotes(pat))
    if fmt in ('ida', 'ghidra', 'x64dbg', 'ce'):
        return parse_tokens(pat)
    if fmt in ('cstyle', 'bytes'):
        return apply_mask(parse_escapes(pat), mask)
    if fmt == 'sig_mask':
        return apply_mask([_hex_byte(t) for t in pat.split()], mask)
    raise ValueError(f"unknown format {fmt!r}")


def _tokens(norm, wild, lower=False):
    fmt = "{:02x}" if lower else "{:02X}"
    return ' '.join(wild if b is None else fmt.format(b) for b in norm)


def _escapes(norm):
    return ''.join('\\x00' if b is None else f"\\x{b:02X}" for b in norm)


def _mask_str(norm):
    return ''.join('?' if b is None else 'x' for b in norm)


def emit(fmt, norm):
    """Render the normalized list as the requested output format."""
    if fmt == 'ida':
        return _tokens(norm, '?')
    if fmt == 'ghidra':
        return _tokens(norm, '..', lower=True)
    if fmt in ('x64dbg', 'ce'):
        return _tokens(norm, '??')
    if fmt == 'enma':
        return '"' + _tokens(norm, '??') + '"'
    if fmt == 'cstyle':
        return f'"{_escapes(norm)}" "{_mask_str(norm)}"'
    if fmt == 'bytes':
        return f'b"{_escapes(norm)}"  # mask: {_mask_str(norm)}'
    if fmt == 'sig_mask':
        return _tokens(norm, '00') + '\n' + _mask_str(norm)
    raise ValueError(f"unknown format {fmt!r}")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_name = 'pattern-format-converter.exe' if os.name == 'nt' else 'pattern-format-converter'
    binary_path = os.path.join(base_dir, 'bin', bin_name)
    if os.path.exists(binary_path):
        try:
            res = subprocess.run([binary_path] + sys.argv[1:])
            sys.exit(res.returncode)
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description='Convert byte patterns between IDA/Ghidra/x64dbg/CE/Enma/C formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="formats: " + ', '.join(FORMATS) + "\n"
               "cstyle, bytes, and sig_mask need --mask when used as --from.")
    parser.add_argument('--from', dest='src', required=True, choices=FORMATS,
                        help='source format')
    parser.add_argument('--to', dest='dst', required=True, choices=FORMATS + ['all'],
                        help="target format, or 'all' to show every format")
    parser.add_argument('--pat', required=True, help='the pattern to convert')
    parser.add_argument('--mask', help='mask string (required for cstyle/bytes/sig_mask input)')
    parser.add_argument('--json', action='store_true', help='machine-readable JSON output')
    args = parser.parse_args()

    try:
        norm = to_norm(args.src, args.pat, args.mask)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    targets = FORMATS if args.dst == 'all' else [args.dst]
    rendered = {f: emit(f, norm) for f in targets}

    if args.json:
        print(json.dumps({
            'from': args.src,
            'length': len(norm),
            'wildcards': sum(1 for b in norm if b is None),
            'normalized': norm,  # ints, null for wildcards
            'formats': rendered,
        }, indent=2))
        return

    if args.dst != 'all':
        print(rendered[args.dst])
        return

    width = max(len(f) for f in FORMATS) + 2
    for f in FORMATS:
        lines = rendered[f].split('\n')
        print(f"{f:<{width}}{lines[0]}")
        for cont in lines[1:]:
            print(f"{'':<{width}}{cont}")


if __name__ == '__main__':
    main()
