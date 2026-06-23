# Kernel-Level Reverse Engineering Tools

Tools for reversing kernel drivers, analyzing anti-cheat systems, and inspecting kernel state. Organized by workflow stage.

> **Scope:** Authorized security research only. See `skill://authorized-security-research` before pointing any tool at a live system. AC driver analysis should happen in an isolated VM, never on a production box.

---

## Static Analysis (Driver Binaries)

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **IDA Pro** | Disassembler + decompiler. The standard for driver reversing — FLIRT sigs for ntoskrnl, WDK type libraries, Hex-Rays decompiler. | Win/Linux/macOS | `idalib` MCP wired in this toolkit (`mcp/binary-analysis-setup.md`) |
| **Ghidra** | Free decompiler. Supports PE drivers, PDB loading, WDK headers via GDT. Slower than IDA but scriptable (Java/Python). | Cross-platform | Ghidra MCP available (`ghidra` server) |
| **radare2 / rizin** | CLI disassembler. Fast triage: `r2 -AA driver.sys` → `afl` (function list), `pdf @ sym.DriverEntry` (disasm entry). | Cross-platform | `radare2` MCP wired in this toolkit |
| **Binary Ninja** | Interactive disassembler with IL (BNIL). Good for automated analysis via Python API. | Win/Linux/macOS | — |
| **CFF Explorer** | PE header viewer. Quick check: driver subsystem (NATIVE), imports, sections, certificate chain. | Windows | — |
| **PE-bear** | PE parser. Shows imports, relocations, resources, overlay. | Cross-platform | — |

## Kernel Debugging

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **WinDbg** | Microsoft kernel debugger. The only way to single-step kernel code, inspect EPROCESS/ETHREAD, walk callback arrays. Requires a debug target (VM or serial/net). | Windows | Essential for AC analysis |
| **WinDbg Preview** | Modern UI wrapper for the same engine. Same commands, better UX. | Windows | From Microsoft Store |
| **VirtualKD-Redux** | Patches the VM's `kdcom.dll` to use a fast pipe instead of serial — 10–40× faster kernel debugging in VMware/VirtualBox. | Windows (host+guest) | Use with WinDbg |
| **KD (kd.exe)** | Console-mode kernel debugger. Same engine as WinDbg, scriptable. | Windows | `kd -k net:port=50000,key=...` |
| **HyperDbg** | Hypervisor-level debugger. Sits *below* the OS — invisible to kernel anti-debug. Supports stealth breakpoints, EPT hooks, syscall interception. | Windows | Runs as a custom hypervisor; the AC cannot detect it via standard means |
| **QEMU + GDB** | GDB stub for kernel debugging Linux/Windows guests. `-s -S` flags expose a GDB server on port 1234. | Cross-platform | `target remote :1234` in GDB |

## Memory Forensics (Offline Analysis)

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **Volatility 3** | Memory forensics framework. Analyze memory dumps: driver lists, callback arrays, SSDT, IDT, process trees, handle tables. | Cross-platform (Python) | `vol -f dump.raw windows.driverscan`, `windows.callbacks` |
| **Rekall** | Alternative memory forensics. Similar to Volatility, different plugin architecture. | Cross-platform (Python) | Less actively maintained |
| **WinPmem** | Memory acquisition driver. Dumps physical RAM to a file for offline analysis. | Windows | Requires admin; the AC may detect the acquisition driver |
| **PCILeech** | DMA-based memory acquisition via FPGA or Thunderbolt. Reads physical memory without software on the target — invisible to kernel ACs. | Hardware + host | Requires FPGA board (e.g., Screamer, LambdaConcept) or Thunderbolt access |
| **MemProcFS** | Virtual file system for physical memory analysis. Mount a memory dump (or live DMA feed) as a filesystem and browse processes, modules, registry. | Windows/Linux | Works with PCILeech for live analysis |

## Runtime Monitoring

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **Process Monitor** | Real-time file, registry, process, network, and thread activity. Filter by `driver.sys` to see what the AC touches at load time. | Windows | Sysinternals |
| **Process Explorer** | Enhanced task manager. Shows DLLs, handles, GPU, threads. Check what the AC injects and what handles it opens. | Windows | Sysinternals |
| **IRPMon** | Intercepts IRPs (I/O Request Packets) to/from drivers. Use to capture IOCTL traffic between AC user-mode and kernel components. | Windows | Open source; AC may detect it |
| **API Monitor** | Hooks Win32/NT API calls. Capture `DeviceIoControl` calls, `NtQuerySystemInformation`, `NtOpenProcess` from the AC user-mode module. | Windows | Heavy but detailed |
| **DebugView++** | Captures `DbgPrint` / `OutputDebugString` output from drivers and user-mode. | Windows | Sysinternals successor |
| **OSR Device Monitor** | Legacy IOCTL monitor. Simpler than IRPMon for basic IOCTL capture. | Windows | — |

## Driver Development / Testing

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **WDK (Windows Driver Kit)** | Headers, libs, build tools for kernel development. Essential for understanding AC driver structures — the headers define every callback type, IRP structure, and IOCTL macro. | Windows | Free from Microsoft |
| **OSR Driver Loader** | Loads unsigned drivers for testing (requires test-signing mode). | Windows | — |
| **kdmapper** | Manual-maps a driver into kernel without loading via SCM — no entry in PsLoadedModuleList. Educational: understand how cheat drivers avoid detection. | Windows | Research only |
| **EfiGuard** | Disables DSE (Driver Signature Enforcement) and PatchGuard from the UEFI bootloader. Research tool for understanding boot-time security. | UEFI | Research only — pre-boot |

## Perception.cx Integration

| Tool | Surface | What It Does |
|------|---------|-------------|
| `system/list_drivers` | MCP | Enumerate loaded kernel modules (gated: `kernel_rw_access`) |
| `get_eprocess` | `proc_t` (Enma/AS) | Get target's EPROCESS kernel address (gated: `kernel_rw_access`) |
| `ru64` / `ru32` / `read_struct` (kernel range) | `proc_t` (Enma/AS) | Read kernel memory when `kernel_rw_access` is granted |
| `find_code_pattern` | `proc_t` (Enma/AS) | Pattern-scan driver `.text` sections |
| `struct_dump` | Perception IDE AI tool | Heuristically dump + classify a driver data structure at an address |
| `process/disassemble` | MCP | Disassemble driver code at kernel addresses |
| `process/analyze_vtable` | MCP | Walk vtables in kernel objects |
| `process/find_xrefs` | MCP | Find code references into driver `.text` |

## Recommended Analysis Environment

```
┌─────────────────────────────────────┐
│  Host (Linux/macOS)                 │
│  ├── IDA Pro / Ghidra / r2          │  ← Static analysis of driver binaries
│  ├── Volatility 3                   │  ← Offline analysis of VM snapshots
│  └── WinDbg via network KD          │  ← Kernel debug the VM
│                                     │
│  ┌──────────────────────────────┐   │
│  │  VM (Windows — test-signing) │   │
│  │  ├── Game + anti-cheat       │   │  ← Target
│  │  ├── Process Monitor         │   │  ← Runtime monitoring
│  │  ├── IRPMon                  │   │  ← IOCTL capture
│  │  └── Debug serial/net to host│   │  ← KD pipe to host WinDbg
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Key rule:** Never analyze from the same OS instance the AC is running on. The AC monitors for debugger artifacts, analysis tools, and VM-escape attempts. Use a VM with snapshots — snapshot before installing the AC, so you can revert cleanly.
