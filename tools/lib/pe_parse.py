"""Minimal PE parser — shared by the toolkit's RE tools.

Provides parse_pe (full header + sections), rva_to_off, and read_cstr.
Every PE-consuming tool under tools/ should import from here instead of
re-implementing MZ/PE/COFF parsing.

Stdlib-only. No external dependencies.
"""
from __future__ import annotations

import json
import os
import struct
import subprocess
import tempfile
from typing import Any, cast


def read_u16(data: bytes, off: int) -> int:
    return cast(int, struct.unpack_from('<H', data, off)[0])


def read_u32(data: bytes, off: int) -> int:
    return cast(int, struct.unpack_from('<I', data, off)[0])


def read_u64(data: bytes, off: int) -> int:
    return cast(int, struct.unpack_from('<Q', data, off)[0])


def parse_pe(data: bytes) -> dict[str, Any]:
    """Parse PE headers from raw bytes.

    Returns dict with keys:
        pe64        — bool, PE32+ vs PE32
        machine     — uint16 machine type
        image_base  — uint64 (zero-extended for PE32)
        sections    — list of dict(name, vaddr, vsize, raddr, rsize, chars, exec)
        export_dir  — (rva, size) tuple or (0, 0)
        import_dir  — (rva, size) tuple or (0, 0)

    Raises SystemExit on invalid input.
    """
    # Try using Rust compiled parser first
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_name = 'pe-parser.exe' if os.name == 'nt' else 'pe-parser'
    binary_path = os.path.join(base_dir, 'bin', bin_name)

    if os.path.exists(binary_path):
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                res = subprocess.run([binary_path, tmp_path], capture_output=True, text=True)
                if res.returncode == 0:
                    parsed = cast(dict[str, Any], json.loads(res.stdout))
                    if 'error' in parsed:
                        raise SystemExit(parsed['error'])
                    parsed['export_dir'] = tuple(cast(list[int], parsed['export_dir']))
                    parsed['import_dir'] = tuple(cast(list[int], parsed['import_dir']))
                    return parsed
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except SystemExit:
            raise
        except Exception:
            pass

    # Fallback to pure Python implementation
    if data[:2] != b'MZ':
        raise SystemExit('not a PE: missing MZ header')
    pe_off = read_u32(data, 0x3C)
    if data[pe_off:pe_off + 4] != b'PE\x00\x00':
        raise SystemExit('not a PE: missing PE signature')

    coff = pe_off + 4
    machine = read_u16(data, coff)
    num_sections = read_u16(data, coff + 2)
    opt_size = read_u16(data, coff + 16)
    opt_off = coff + 20
    pe64 = read_u16(data, opt_off) == 0x20B

    image_base = cast(int, struct.unpack_from(
        '<Q' if pe64 else '<I',
        data, opt_off + (24 if pe64 else 28),
    )[0])

    dd_off = opt_off + (112 if pe64 else 96)
    export_dir = (read_u32(data, dd_off), read_u32(data, dd_off + 4))
    import_dir = (read_u32(data, dd_off + 8), read_u32(data, dd_off + 12))

    sec_off = opt_off + opt_size
    sections: list[dict[str, Any]] = []
    for i in range(num_sections):
        s = sec_off + i * 40
        if s + 40 > len(data):
            break
        name = data[s:s + 8].rstrip(b'\x00').decode('ascii', errors='replace')
        vsize = read_u32(data, s + 8)
        vaddr = read_u32(data, s + 12)
        rsize = read_u32(data, s + 16)
        raddr = read_u32(data, s + 20)
        chars = read_u32(data, s + 36)
        sections.append({
            'name': name, 'vaddr': vaddr, 'vsize': vsize,
            'raddr': raddr, 'rsize': rsize, 'chars': chars,
            'exec': bool(chars & 0x20000000),
        })

    return {
        'pe64': pe64,
        'machine': machine,
        'image_base': image_base,
        'sections': sections,
        'export_dir': export_dir,
        'import_dir': import_dir,
    }


def rva_to_off(rva: int, sections: list[dict[str, Any]]) -> int | None:
    """Translate an RVA to a file offset using section mappings."""
    for sec in sections:
        vaddr = cast(int, sec['vaddr'])
        vsize = cast(int, sec['vsize'])
        rsize = cast(int, sec['rsize'])
        raddr = cast(int, sec['raddr'])
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return rva - vaddr + raddr
    return None


def read_cstr(data: bytes, off: int | None, maxlen: int = 512) -> str:
    """Read a null-terminated ASCII string at *off*; empty string on None."""
    if off is None or off >= len(data):
        return ''
    end = data.find(b'\x00', off, off + maxlen)
    if end < 0:
        end = min(off + maxlen, len(data))
    return data[off:end].decode('ascii', errors='replace')
