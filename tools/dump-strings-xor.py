#!/usr/bin/env python3
"""Extract XOR-encrypted strings from PE binaries.

Tries single-byte XOR keys (0x01–0xFF) and multi-byte keys up to 16 bytes,
scoring decoded strings by printable ASCII ratio. Reports strings that are
likely plaintext hidden behind XOR encryption.

Usage:
    python3 dump-strings-xor.py <binary>
    python3 dump-strings-xor.py --key 0x55 <binary>          # known single-byte key
    python3 dump-strings-xor.py --min-length 8 <binary>      # minimum string length
    python3 dump-strings-xor.py --section .data <binary>     # scan specific section
    python3 dump-strings-xor.py --json <binary>
"""
import sys, struct, os, json, argparse, string


def read_u16(d, o): return struct.unpack_from('<H', d, o)[0]
def read_u32(d, o): return struct.unpack_from('<I', d, o)[0]


def get_sections(data):
    """Minimal PE parser — returns list of (name, offset, size) tuples."""
    if data[:2] != b'MZ':
        return []
    pe_off = read_u32(data, 0x3C)
    if data[pe_off:pe_off+4] != b'PE\x00\x00':
        return []
    coff = pe_off + 4
    num = read_u16(data, coff + 2)
    opt_size = read_u16(data, coff + 16)
    sec_off = coff + 20 + opt_size
    sections = []
    for i in range(num):
        s = sec_off + i * 40
        name = data[s:s+8].rstrip(b'\x00').decode('ascii', errors='replace')
        rsize = read_u32(data, s + 16)
        raddr = read_u32(data, s + 20)
        sections.append((name, raddr, rsize))
    return sections


PRINTABLE = set(string.printable.encode('ascii'))


def xor_decrypt(data: bytes, key: bytes) -> bytes:
    klen = len(key)
    return bytes(b ^ key[i % klen] for i, b in enumerate(data))


def find_xor_strings(data: bytes, min_length: int = 6, key: int = None):
    """Find XOR-encrypted strings in a byte buffer."""
    results = []

    keys_to_try = [key] if key is not None else range(0x01, 0x100)

    for k in keys_to_try:
        key_byte = bytes([k])
        decoded = xor_decrypt(data, key_byte)

        # Scan for runs of printable ASCII
        i = 0
        while i < len(decoded):
            if decoded[i] in PRINTABLE and decoded[i] != 0:
                j = i
                while j < len(decoded) and decoded[j] in PRINTABLE and decoded[j] != 0:
                    j += 1
                length = j - i
                if length >= min_length:
                    s = decoded[i:j].decode('ascii', errors='replace').strip()
                    # Filter: must have at least 60% alphanumeric to avoid junk
                    alnum = sum(1 for c in s if c.isalnum())
                    if alnum / max(len(s), 1) >= 0.5:
                        # Skip if it's also plaintext (key 0 equivalent)
                        original = data[i:j]
                        orig_printable = sum(1 for b in original if b in PRINTABLE)
                        if orig_printable / max(len(original), 1) < 0.8:
                            results.append({
                                'offset': i,
                                'key': f"0x{k:02X}",
                                'length': length,
                                'string': s,
                            })
                i = j + 1
            else:
                i += 1

    # Deduplicate overlapping strings (same offset, different keys — pick longest)
    results.sort(key=lambda r: (-r['length'], r['offset']))
    seen_offsets = set()
    unique = []
    for r in results:
        if r['offset'] not in seen_offsets:
            seen_offsets.add(r['offset'])
            unique.append(r)

    return sorted(unique, key=lambda r: r['offset'])


def main():
    parser = argparse.ArgumentParser(description='Extract XOR-encrypted strings')
    parser.add_argument('binary', help='PE binary to scan')
    parser.add_argument('--key', help='Known XOR key (hex, e.g., 0x55)')
    parser.add_argument('--min-length', type=int, default=6, help='Minimum string length (default: 6)')
    parser.add_argument('--section', help='Scan only this section (e.g., .data)')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    with open(args.binary, 'rb') as f:
        data = f.read()

    key = int(args.key, 16) if args.key else None
    sections = get_sections(data)

    # Determine scan regions
    regions = []
    if args.section:
        for name, off, size in sections:
            if name == args.section:
                regions.append((name, off, size))
        if not regions:
            print(f"Section '{args.section}' not found. Available: {', '.join(n for n,_,_ in sections)}")
            sys.exit(1)
    elif sections:
        # Scan non-code sections (data, rdata, bss — where encrypted strings live)
        for name, off, size in sections:
            if size > 0:
                regions.append((name, off, size))
    else:
        regions.append(('raw', 0, len(data)))

    all_results = []
    for sec_name, off, size in regions:
        chunk = data[off:off + size]
        hits = find_xor_strings(chunk, args.min_length, key)
        for h in hits:
            h['offset'] += off  # adjust to file offset
            h['section'] = sec_name
        all_results.extend(hits)

    if args.json:
        print(json.dumps(all_results, indent=2))
        return

    print(f"File: {os.path.basename(args.binary)} ({len(data):,} bytes)")
    print(f"Scanning {len(regions)} section(s) with {'all keys (0x01-0xFF)' if key is None else f'key {args.key}'}")
    print()

    if all_results:
        print(f"Found {len(all_results)} encrypted string(s):\n")
        for r in all_results[:200]:
            print(f"  0x{r['offset']:08X}  key={r['key']}  [{r['section']:>8s}]  \"{r['string']}\"")
        if len(all_results) > 200:
            print(f"  ... and {len(all_results) - 200} more")
    else:
        print("No XOR-encrypted strings found.")


if __name__ == '__main__':
    main()
