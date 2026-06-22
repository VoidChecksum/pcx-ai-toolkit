---
name: rust-python-integration
description: >
  Guidelines for developing hybrid Rust-Python tools in pcx-ai-toolkit.
  Covers the multi-binary Cargo architecture, transparent Python proxying
  with fallbacks, match ergonomics, and zero-dependency mock PE testing.
license: MIT
---

# Rust-Python Integration & Native Proxying Discipline

Guidelines for designing, developing, and extending hybrid Rust-Python tools in the `pcx-ai-toolkit` environment. 

This discipline ensures that performance-critical RE tasks (such as binary diffing, signature scanning, and format parsing) are offloaded to compiled, native Rust code, while keeping the toolkit lightweight, portable, and backward-compatible with pure-Python fallback implementations.

---

## Trigger
Writing or editing any tool under `tools/`, introducing a new binary analysis script, porting Python logic to Rust, or modifying the core parser library (`tools/pe-parser`).

---

## 1. Crate Architecture (Multi-Binary Layout)

To avoid duplicate parsing code, all native tools share a single unified Cargo project at `tools/pe-parser`.

- **`src/lib.rs` (Shared Library)**: 
  Exposes common binary structure parsing (PE, ELF, Mach-O), helper functions (such as `rva_to_off` and `load_binary_data`), and common structs.
- **`src/main.rs` (Primary Binary)**: 
  The default compiled binary (`pe-parser`). Focuses on exporting parsed JSON metadata to stdout.
- **`src/bin/*.rs` (Auxiliary Binaries)**: 
  Individual tools (such as `sig-uniqueness-checker`, `binary-diff-summary`, and `offset-diff`). They import shared logic from the library using `use pe_parser::*` and execute specific CLI tasks.

---

## 2. Match Ergonomics & Clean Rust Style

To maintain a clean and modern codebase, strictly adhere to match ergonomics:

- **Do NOT use explicit `ref` or `ref mut` patterns.**
- Instead, borrow the scrutinee (the value being matched) and let the compiler infer references in the let bindings.

```rust
// AVOID
if let Some(ref sig_str) = args.sig { ... }

// ENFORCE (Match Ergonomics)
if let Some(sig_str) = &args.sig { ... }
```

---

## 3. Transparent Python Proxying & Fallbacks

Every Python tool ported to Rust must keep its Python script as a proxy with a seamless fallback to the pure-Python implementation:

1. **Proxy check**: Verify if the compiled Rust binary exists at `tools/bin/`.
2. **Execute and Exit**: If the binary exists, call it using `subprocess.run` with `sys.argv[1:]`, and exit with the return code of the subprocess.
3. **Fallback**: If the binary is missing, uncompiled, or fails to execute, pass through to the legacy Python implementation.

```python
# Canonical Proxy Template
import os
import sys
import subprocess

def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_name = 'my-tool.exe' if os.name == 'nt' else 'my-tool'
    binary_path = os.path.join(base_dir, 'bin', bin_name)

    if os.path.exists(binary_path):
        try:
            res = subprocess.run([binary_path] + sys.argv[1:])
            sys.exit(res.returncode)
        except Exception:
            pass  # Fallback to pure-Python logic on execution failure
```

---

## 4. Multi-Format Binary Parsing (PE, ELF, Mach-O)

To keep the RE tools cross-platform, the core parser (`src/lib.rs`) dynamically detects the file format by checking the magic bytes at the beginning of the file buffer:

- **PE (Windows)**: Starts with `MZ` at `0x00`, with `PE\0\0` at the offset read from `0x3C`.
- **ELF (Linux/Android)**: Starts with `\x7fELF` at `0x00`. TRAVERSE the Program/Section Header Tables and decode section names using the String Table (`shstrtab`).
- **Mach-O (macOS/iOS)**: Detects magic bytes (`0xFEEDFACE`/`0xFEEDFACF` or big-endian equivalents), traverses load commands, and parses segments (`LC_SEGMENT` / `LC_SEGMENT_64`).

---

## 5. Parallel Signature Scanning (Rayon)

When processing batch signature evaluations or diffing large lists of patterns, use `rayon` to scale performance across all available CPU cores:

```rust
use rayon::prelude::*;

let results: Vec<SigResult> = sigs
    .par_iter() // rayon parallel iterator
    .map(|sig| {
        // CPU-bound scanning logic
    })
    .collect();
```

---

## 6. Zero-Dependency Mock Binary Generation for Testing

When writing automated tests (such as `tools/test-runner.sh`), avoid checked-in binary blobs. Instead, dynamically construct a minimal, valid x64 PE structure on-the-fly in Python:

- Set standard headers: MZ header at `0x00`, PE offset at `0x3C`, `PE\0\0` at `0x80`.
- Populate a COFF header, Optional Header (magic `0x20B`), and Section Headers.
- Construct valid mock Import Tables (e.g., `kernel32.dll!IsDebuggerPresent`) and Export Tables.
- Write raw bytes representing target assembly signatures (e.g., PEB walks).
- Execute the ported tools against this generated file to verify correctness.
