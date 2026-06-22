#!/usr/bin/env python3
"""Resolve API hashes used by obfuscated binaries for dynamic import resolution.

Supports: ROR13+ADD, CRC32, DJB2, FNV-1a, MurmurHash3-32, SDBM, SuperFastHash.

Usage:
    python3 resolve-api-hashes.py <hash_hex> [--algo ror13]
    python3 resolve-api-hashes.py --batch hashes.txt
    python3 resolve-api-hashes.py --scan <binary>  # scan binary for hash constants
    python3 resolve-api-hashes.py --build-db        # rebuild the hash database

The tool ships with a precomputed database of common Windows API hashes. If it
doesn't exist yet, run --build-db first (needs a Windows SDK headers dir or a
manually provided export list).
"""
import struct
import json
import argparse
import zlib

# ── Hash algorithms ──────────────────────────────────────────────────────────

def ror13_add(name: bytes) -> int:
    """ROR13+ADD — the most common shellcode/malware hash algorithm."""
    h = 0
    for b in name:
        h = (((h >> 13) | (h << 19)) + b) & 0xFFFFFFFF
    return h

def djb2(name: bytes) -> int:
    """DJB2 (Bernstein) hash."""
    h = 5381
    for b in name:
        h = ((h * 33) + b) & 0xFFFFFFFF
    return h

def fnv1a_32(name: bytes) -> int:
    """FNV-1a 32-bit."""
    h = 0x811C9DC5
    for b in name:
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h

def crc32_hash(name: bytes) -> int:
    """CRC32 (zlib)."""
    return zlib.crc32(name) & 0xFFFFFFFF

def sdbm(name: bytes) -> int:
    """SDBM hash."""
    h = 0
    for b in name:
        h = (b + (h << 6) + (h << 16) - h) & 0xFFFFFFFF
    return h

def murmur3_32(name: bytes, seed: int = 0) -> int:
    """MurmurHash3 32-bit."""
    c1, c2 = 0xCC9E2D51, 0x1B873593
    h = seed & 0xFFFFFFFF
    length = len(name)
    nblocks = length // 4

    for i in range(nblocks):
        k = struct.unpack_from('<I', name, i * 4)[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xFFFFFFFF
        h = (h * 5 + 0xE6546B64) & 0xFFFFFFFF

    tail = name[nblocks * 4:]
    k = 0
    if len(tail) >= 3:
        k ^= tail[2] << 16
    if len(tail) >= 2:
        k ^= tail[1] << 8
    if len(tail) >= 1:
        k ^= tail[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        h ^= k

    h ^= length
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & 0xFFFFFFFF
    h ^= h >> 16
    return h


ALGORITHMS = {
    'ror13':    ror13_add,
    'djb2':     djb2,
    'fnv1a':    fnv1a_32,
    'crc32':    crc32_hash,
    'sdbm':     sdbm,
    'murmur3':  murmur3_32,
}

# ── Common Windows API exports ───────────────────────────────────────────────

COMMON_APIS = [
    # kernel32.dll
    'LoadLibraryA', 'LoadLibraryW', 'LoadLibraryExA', 'LoadLibraryExW',
    'GetProcAddress', 'GetModuleHandleA', 'GetModuleHandleW',
    'VirtualAlloc', 'VirtualAllocEx', 'VirtualFree', 'VirtualProtect', 'VirtualQuery',
    'CreateFileA', 'CreateFileW', 'ReadFile', 'WriteFile', 'CloseHandle',
    'CreateProcessA', 'CreateProcessW', 'TerminateProcess', 'ExitProcess',
    'OpenProcess', 'GetCurrentProcess', 'GetCurrentProcessId',
    'CreateThread', 'CreateRemoteThread', 'ExitThread', 'GetCurrentThread',
    'WaitForSingleObject', 'WaitForMultipleObjects', 'Sleep', 'SleepEx',
    'GetTickCount', 'QueryPerformanceCounter', 'QueryPerformanceFrequency',
    'HeapAlloc', 'HeapFree', 'HeapCreate', 'GetProcessHeap',
    'GetSystemInfo', 'GetVersionExA', 'GetVersionExW', 'IsWow64Process',
    'DeviceIoControl', 'CreateToolhelp32Snapshot', 'Process32First', 'Process32Next',
    'Thread32First', 'Thread32Next', 'Module32First', 'Module32Next',
    'GetLastError', 'SetLastError', 'GetSystemDirectory', 'GetWindowsDirectory',
    'OutputDebugStringA', 'OutputDebugStringW', 'IsDebuggerPresent',
    'CheckRemoteDebuggerPresent',
    # ntdll.dll
    'NtQueryInformationProcess', 'NtSetInformationThread', 'NtQuerySystemInformation',
    'NtOpenProcess', 'NtClose', 'NtAllocateVirtualMemory', 'NtFreeVirtualMemory',
    'NtReadVirtualMemory', 'NtWriteVirtualMemory', 'NtProtectVirtualMemory',
    'NtCreateThreadEx', 'NtMapViewOfSection', 'NtUnmapViewOfSection',
    'RtlInitUnicodeString', 'RtlGetVersion', 'NtQueryVirtualMemory',
    'NtCreateFile', 'NtDeviceIoControlFile', 'NtDuplicateObject',
    'LdrLoadDll', 'LdrGetProcedureAddress', 'RtlAdjustPrivilege',
    # user32.dll
    'MessageBoxA', 'MessageBoxW', 'FindWindowA', 'FindWindowW',
    'GetForegroundWindow', 'GetWindowTextA', 'GetWindowTextW',
    'EnumWindows', 'SetWindowsHookExA', 'SetWindowsHookExW',
    'GetAsyncKeyState', 'GetKeyState', 'SendInput',
    'GetDC', 'ReleaseDC', 'GetDesktopWindow',
    # ws2_32.dll
    'WSAStartup', 'socket', 'connect', 'send', 'recv', 'closesocket',
    'bind', 'listen', 'accept', 'getaddrinfo', 'inet_addr',
    # advapi32.dll
    'OpenProcessToken', 'LookupPrivilegeValueA', 'AdjustTokenPrivileges',
    'RegOpenKeyExA', 'RegOpenKeyExW', 'RegQueryValueExA', 'RegQueryValueExW',
    'CreateServiceA', 'CreateServiceW', 'OpenSCManagerA', 'OpenSCManagerW',
    'StartServiceA', 'StartServiceW',
    # wininet.dll / winhttp.dll
    'InternetOpenA', 'InternetOpenUrlA', 'InternetReadFile',
    'HttpOpenRequestA', 'HttpSendRequestA',
    'WinHttpOpen', 'WinHttpConnect', 'WinHttpOpenRequest', 'WinHttpSendRequest',
]


def build_hash_db():
    """Build hash database for all algorithms × all known APIs."""
    db = {}
    for algo_name, algo_fn in ALGORITHMS.items():
        db[algo_name] = {}
        for api in COMMON_APIS:
            h = algo_fn(api.encode('ascii'))
            db[algo_name][f"0x{h:08X}"] = api
            # Also hash with null terminator (some hashers include it)
            h2 = algo_fn(api.encode('ascii') + b'\x00')
            if f"0x{h2:08X}" not in db[algo_name]:
                db[algo_name][f"0x{h2:08X}"] = api + ' (null-terminated)'
    return db


def resolve_hash(hash_val: int, algo: str = None, db: dict = None):
    """Resolve a hash value. If algo is None, try all algorithms."""
    if db is None:
        db = build_hash_db()

    hex_key = f"0x{hash_val:08X}"
    results = []

    algos = [algo] if algo else ALGORITHMS.keys()
    for a in algos:
        if a not in db:
            continue
        if hex_key in db[a]:
            results.append({'algo': a, 'api': db[a][hex_key], 'hash': hex_key})

    return results


def scan_binary(filepath: str, db: dict = None):
    """Scan a binary for 32-bit constants that match known API hashes."""
    if db is None:
        db = build_hash_db()

    # Build reverse lookup: hash_value → [(algo, api_name)]
    reverse = {}
    for algo_name, entries in db.items():
        for h, api in entries.items():
            val = int(h, 16)
            if val not in reverse:
                reverse[val] = []
            reverse[val].append((algo_name, api))

    with open(filepath, 'rb') as f:
        data = f.read()

    hits = []
    # Scan for 32-bit immediates in code
    for i in range(0, len(data) - 4, 1):
        val = struct.unpack_from('<I', data, i)[0]
        if val in reverse:
            for algo, api in reverse[val]:
                hits.append({
                    'offset': f"0x{i:X}",
                    'hash': f"0x{val:08X}",
                    'algo': algo,
                    'api': api,
                })

    # Deduplicate by (offset, api) — same offset may match multiple algos
    seen = set()
    unique = []
    for h in hits:
        key = (h['offset'], h['api'])
        if key not in seen:
            seen.add(key)
            unique.append(h)

    return unique


def main():
    parser = argparse.ArgumentParser(description='Resolve API hashes')
    parser.add_argument('hash', nargs='?', help='Hash value (hex, e.g., 0x726774C)')
    parser.add_argument('--algo', choices=list(ALGORITHMS.keys()), help='Force algorithm')
    parser.add_argument('--batch', help='File with one hash per line')
    parser.add_argument('--scan', help='Scan binary for hash constants')
    parser.add_argument('--build-db', action='store_true', help='Dump precomputed hash DB as JSON')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    if args.build_db:
        db = build_hash_db()
        total = sum(len(v) for v in db.values())
        if args.json:
            print(json.dumps(db, indent=2))
        else:
            for algo, entries in db.items():
                print(f"{algo}: {len(entries)} hashes")
            print(f"Total: {total} precomputed hashes across {len(db)} algorithms")
        return

    db = build_hash_db()

    if args.scan:
        hits = scan_binary(args.scan, db)
        if args.json:
            print(json.dumps(hits, indent=2))
        else:
            print(f"Scanning {args.scan}...")
            if hits:
                print(f"Found {len(hits)} API hash matches:\n")
                for h in hits[:100]:
                    print(f"  {h['offset']:>10s}  {h['hash']}  [{h['algo']:>8s}]  {h['api']}")
                if len(hits) > 100:
                    print(f"  ... and {len(hits) - 100} more")
            else:
                print("No API hash constants found.")
        return

    hashes = []
    if args.batch:
        with open(args.batch) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    hashes.append(int(line, 16))
    elif args.hash:
        hashes.append(int(args.hash, 16))
    else:
        parser.print_help()
        return

    for h in hashes:
        results = resolve_hash(h, args.algo, db)
        if args.json:
            print(json.dumps(results, indent=2))
        elif results:
            for r in results:
                print(f"0x{h:08X}  →  {r['api']}  [{r['algo']}]")
        else:
            print(f"0x{h:08X}  →  (no match)")


if __name__ == '__main__':
    main()
