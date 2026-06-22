# Obfuscation & Protector Taxonomy

Architecture, VM internals, protection layers, and known weaknesses for every major commercial and open-source binary protector. Read this before starting deobfuscation — it tells you what you're fighting and where each protector is weakest.

---

## Commercial Protectors

### Themida / WinLicense (Oreans Technologies)

| Property | Detail |
|----------|--------|
| **Publisher** | Oreans Technologies |
| **Products** | Themida (code protection), WinLicense (code + licensing), Code Virtualizer (VM-only) |
| **Platforms** | Windows x86/x64, .NET |
| **Protection layers** | Anti-debug, anti-dump, code mutation, import redirection, resource encryption, VM virtualization |
| **VM architectures** | FISH, TIGER, DOLPHIN, EAGLE, SHARK (ascending strength) |

**VM Architecture:**

Each Themida VM is a register-based bytecode interpreter:

| Component | Implementation |
|-----------|---------------|
| **Dispatcher** | Computed goto: `jmp [reg*8 + handler_table]` |
| **Virtual PC** | Register (typically `RBX` or `R12`) pointing into bytecode stream |
| **Virtual stack** | Real stack reused, or dedicated memory region |
| **Virtual registers** | 8-16 virtual registers mapped to a stack-frame struct |
| **Bytecode** | Stored in `.themida` or `.winlice` section; optionally encrypted |
| **Handler count** | FISH: ~60, TIGER: ~100, DOLPHIN: ~140, EAGLE: ~180, SHARK: ~220+ |

**Macro VM mode:** Instead of virtualizing whole functions, Themida virtualizes individual instruction sequences (3-10 instructions each). This creates many small VM entries scattered throughout the binary rather than one large VM call. Each entry uses the same VM dispatcher but has its own bytecode blob.

**Known weaknesses:**
- The handler dispatch pattern (`jmp [reg*scale + table]`) is recognizable and consistent across versions
- FISH VM handlers map 1:1 to x86 instructions — nearly direct translation
- Anti-dump can be bypassed with Scylla by dumping before the protection initializes
- The watermark string "Themida" or "WinLicense" often remains in section names or PE overlay

---

### VMProtect (VMProtect Software)

| Property | Detail |
|----------|--------|
| **Publisher** | VMProtect Software |
| **Platforms** | Windows x86/x64, Linux x64, macOS x64/ARM64 |
| **Protection layers** | Packing, import protection, code mutation, virtualization |
| **VM variants** | Multiple per-binary; each function can use a different VM instance |
| **Current version** | 3.8.x (2025-2026) |

**VM Architecture:**

VMProtect uses a **stack-based** bytecode interpreter (unlike Themida's register-based):

| Component | Implementation |
|-----------|---------------|
| **Dispatcher** | Large switch or computed goto; typically the biggest function in the binary |
| **Virtual PC (VIP)** | Register pointing into bytecode; incremented by handler |
| **Virtual stack pointer (VSP)** | Register (often `RBP`) managing the operand stack |
| **Virtual registers** | Memory slots on the real stack, addressed by VM bytecode operands |
| **Bytecode** | Stored in `.vmp0` / `.vmp1` sections; rolling-XOR encrypted |
| **Handler count** | 150-250+ handlers depending on complexity and mutation |

**Handler mutation:** Each handler is code-mutated — the same semantic operation (e.g., "add two stack values") is encoded with different instruction sequences across handlers. This breaks pattern-based handler identification.

**Bytecode encryption:** The bytecode stream is encrypted with a rolling key. The VM entry stub decrypts the bytecode at runtime before the dispatcher loop. The key is derived from the function's entry address.

**Ultra mode:** Nested virtualization — a VM's handlers are themselves virtualized by another VM instance. Two-layer trace required.

**Known weaknesses:**
- Stack-based architecture means every operation goes through push/pop → traces are verbose but regular
- NoVmp (open source) handles VMP 3.x; lifts to LLVM IR
- The VM entry point is always a `push <key>; call vmenter` pattern
- VMP's import protection redirects through per-call stubs that can be traced to resolve the real import

---

### Code Virtualizer (Oreans Technologies)

Same Oreans VM as Themida but sold as a standalone virtualizer without the packer/anti-debug layers. Same FISH/TIGER/DOLPHIN/EAGLE/SHARK VMs.

**Difference from Themida:** No packing, no anti-debug, no import protection. Just the VM. Easier to analyze because you skip layers 0-2.

---

### Enigma Protector

| Property | Detail |
|----------|--------|
| **Platforms** | Windows x86/x64 |
| **Protection** | Packing, import redirection, code encryption, basic VM, registration system |
| **Sections** | `.enigma1`, `.enigma2` |

**Weakness:** The VM is simpler than Themida/VMP (~40 handlers). Unpack first (standard `VirtualProtect` OEP technique), then the VM is tractable with Triton or manual analysis.

---

### Obsidium

| Property | Detail |
|----------|--------|
| **Platforms** | Windows x86/x64 |
| **Protection** | Anti-debug, anti-dump, code encryption, import protection, basic VM |

**Weakness:** Heavy anti-debug but weaker VM than Themida/VMP. ScyllaHide + standard unpacking usually sufficient.

---

## Compiler-Level Obfuscation

### LLVM-Obfuscator (OLLVM)

| Property | Detail |
|----------|--------|
| **Source** | Open-source (academic origin: University of Aix-Marseille) |
| **Mechanism** | Custom LLVM passes applied at compile time |
| **No protector to strip** — the obfuscation IS the compiled code |

**Passes:**

| Pass | What It Does | Counter |
|------|-------------|---------|
| **Bogus Control Flow (BCF)** | Inserts opaque predicates creating unreachable paths | Symbolic execution proves predicates constant → remove dead paths |
| **Control Flow Flattening (CFF)** | Flattens all blocks into a dispatcher loop | D-810 (IDA), deflat (Binary Ninja), manual state tracing |
| **Instruction Substitution (SUB)** | Replaces simple ops with algebraic equivalents | IDA optimizer, Miasm normalization, hrtng |
| **String Encryption** | Encrypts string literals, decrypts at runtime | Break on decryption function, log cleartext |
| **Indirect Branching** | Replaces direct jumps with pointer-based indirect jumps | Resolve targets via constant propagation or tracing |
| **MBA (Mixed Boolean-Arithmetic)** | `x + y` → `(x ^ y) + 2*(x & y)` and worse | SSPAM, Triton simplification, algebraic pattern matching |

---

### Hikari

Fork of OLLVM with additional passes: function call obfuscation, anti-class-dump (Objective-C), indirect global variable access. Same counter techniques as OLLVM.

---

### Pluto-Obfuscator

Modern LLVM-based obfuscator with MBA, CFF, indirect branching, and trap-based opaque predicates. Similar to OLLVM but targets newer LLVM versions (14+).

---

## Runtime Obfuscation Techniques

These are techniques used *by* protectors or *by* developers directly, independent of any specific product:

### Metamorphic Code

**What:** Code that rewrites itself into a functionally equivalent but syntactically different form at runtime. Each execution produces different instruction sequences.

**Counter:** Snapshot the code at a stable point (after self-modification completes), then analyze the snapshot. Or: trace the execution and analyze the trace rather than the code.

### Self-Modifying Code (SMC)

**What:** Code that modifies its own instructions during execution — typically decrypting the next basic block, executing it, then re-encrypting it.

**Counter:** Set hardware breakpoints (not software — int3 will be overwritten by SMC). Trace with HyperDbg or PIN. Dump pages at the moment they're executable.

### API Hashing

**What:** Instead of importing `CreateFileW` by name, the code hashes the name at runtime and walks the export table comparing hashes.

**Counter:** Identify the hash algorithm (commonly ROR13+ADD, CRC32, DJB2, FNV-1a), then pre-compute hashes for all ntdll/kernel32/user32 exports and match. HashDB (IDA plugin) automates this for known hash algorithms.

### Stack String Construction

**What:** Strings built character-by-character on the stack (`mov [rsp], 'H'; mov [rsp+1], 'e'; ...`) to avoid string table detection.

**Counter:** FLOSS (FireEye Labs Obfuscated String Solver) extracts stack strings automatically. Or: run the function and read the constructed string from the stack in the debugger.

### Dynamic Code Generation

**What:** The program generates code at runtime using `VirtualAlloc` + `memcpy` + `VirtualProtect(PAGE_EXECUTE_READWRITE)`. The generated code never exists on disk.

**Counter:** Break on `VirtualProtect` transitions to `PAGE_EXECUTE*`. Dump the generated page. The code exists in memory at execution time — you just need to capture it.

### Nanomites

**What:** Critical instructions are replaced with `int 3` (breakpoint). A parent process catches the exceptions via debug API and executes the original instruction in the exception handler.

**Counter:** Hook the exception handler to log what instruction it emulates, or patch the nanomites back to real instructions using the handler's logic as a guide.

---

## Kernel-Level Obfuscation

### PatchGuard / Kernel Patch Protection (KPP)

**What:** Windows kernel integrity monitor. Periodically checks critical kernel structures (SSDT, IDT, GDT, MSRs, critical function prologues) for unauthorized modifications. Triggers BSOD `CRITICAL_STRUCTURE_CORRUPTION` (0x109) on detection.

**Relevant to:** Anti-cheat driver analysis — some cheat drivers attempt to bypass PatchGuard to hook kernel functions.

**Key facts:**
- Timer-based checks with randomized intervals (every 5-10 minutes, unpredictable)
- The check context is obfuscated — it runs from a DPC, work item, or APC with an encrypted call chain
- The KPP context itself is encrypted in memory and decrypted only during checks
- KPP bypass is a moving target — Microsoft patches bypass techniques regularly

### Driver Signature Enforcement (DSE)

**What:** Windows only loads drivers with valid Microsoft-cross-signed certificates. Unsigned drivers get `STATUS_INVALID_IMAGE_HASH`.

**Bypass methods (for understanding, not recommendation):**
- Test-signing mode (`bcdedit /set testsigning on` — visible watermark)
- EFI bootloader modification (EfiGuard, before DSE initializes)
- Vulnerable signed driver exploitation (BYOVD — Bring Your Own Vulnerable Driver)

### Hypervisor-Based Protection

Some protectors (Denuvo, some anti-cheats) use a custom hypervisor:
- EPT (Extended Page Tables) to hide code pages
- VMFUNC for fast VM exits
- Hypervisor hooks on critical instructions (CPUID, RDMSR)

**Counter:** Nest inside another hypervisor (HyperDbg), or analyze from a hardware debugger / DMA where the hypervisor has no visibility.

---

## Quick Reference: Protector → Counter

| Protector | Primary Technique | Best Counter | Automated Tool |
|-----------|-------------------|-------------|----------------|
| **VMProtect** | Stack-based VM | Trace + lift | NoVmp, VMHunt, vtil |
| **Themida** (FISH) | Register-based VM (simple) | Handler mapping | Community scripts |
| **Themida** (SHARK) | Register-based VM (complex) | Trace + lift | Manual + Triton |
| **Code Virtualizer** | Same as Themida VM | Same as Themida | Same as Themida |
| **OLLVM CFF** | Control flow flattening | CFG recovery | D-810, deflat |
| **OLLVM MBA** | Algebraic obfuscation | Simplification | SSPAM, Triton |
| **OLLVM SUB** | Instruction substitution | Optimization | IDA, hrtng |
| **Enigma** | Packer + weak VM | Unpack + manual | Standard unpacking |
| **Obsidium** | Anti-debug + encryption | ScyllaHide + dump | Scylla, pe-sieve |
| **PatchGuard** | Kernel integrity | Analysis-only | Volatility, WinDbg |
| **Custom VM** | Varies | Manual handler RE | Triton, Miasm |
