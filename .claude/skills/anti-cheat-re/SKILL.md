---
name: anti-cheat-re
description: >
  Methodology for reverse engineering kernel-level anti-cheat systems: EAC,
  BattlEye, Vanguard, GameGuard, XIGNCODE3. Covers component enumeration,
  detection-vector cataloging, and verified understanding of the AC
  observation surface. Always active when analyzing anti-cheat systems.
license: MIT
---

# Anti-Cheat Reverse Engineering — Kernel-Level Game Protection Analysis

Methodology for reverse engineering kernel-level anti-cheat systems: EAC (Easy Anti-Cheat), BattlEye, Vanguard, GameGuard, XIGNCODE3, and similar kernel drivers that protect game processes. Covers the full workflow from component enumeration through detection-vector cataloging to verified understanding of the AC's observation surface.

**Always active when analyzing anti-cheat systems.** This is the *methodology* layer — how to approach and work through kernel AC analysis. The `kernel-analysis` skill covers the *technical patterns* (IOCTL dispatch, callback structures, WDM/KMDF internals). Load both.

**Prerequisite:** Read `knowledge/anti-cheat-architecture.md` for per-AC component names, detection matrices, and architecture diagrams before starting analysis. Read `knowledge/kernel-re-tools.md` for the tool reference.

## Trigger
Reversing an anti-cheat driver, analyzing kernel callbacks, mapping IOCTL protocols, understanding detection vectors, researching handle stripping, studying kernel-level game protection, or any mention of EAC, BattlEye, Vanguard, GameGuard, or kernel anti-cheat.

---

## 1. Map the AC's Full Component Stack Before Touching the Driver

**Enumerate every component — user-mode service, injected module, kernel driver, boot driver — and identify how they communicate. Start with user-mode, not kernel.**

A kernel anti-cheat is never just a driver. It's a stack:

- **User-mode service** — `EasyAntiCheat.exe`, `BEService.exe`, `vgc.exe`. Runs as a system service or high-privilege process. Manages the driver lifecycle, communicates with backend servers, relays scan results.
- **Game-injected module** — `EasyAntiCheat_EOS.dll`, `BEClient.dll`. Loaded into the game process. Performs user-mode integrity checks, reports to the service.
- **Kernel driver** — `EasyAntiCheat.sys`, `BEDaisy.sys`, `vgk.sys`. Registers kernel callbacks, strips handles, monitors system state.
- **Boot/ELAM driver** (Vanguard) — loads before third-party drivers at boot time.
- **Backend servers** — BattlEye streams shellcode to `BEClient.dll` at runtime. EAC pushes cloud detection rules. These are out of scope for local RE but explain why static analysis of detection logic is incomplete.

**Start with the user-mode service, not the driver.** The service is unobfuscated (or lightly obfuscated) and reveals:
- The IPC protocol to the driver (IOCTL codes, shared memory layout)
- The heartbeat/keepalive mechanism
- What data it sends to backend servers
- How it launches and communicates with the game-injected module

```
Workflow:
1. Identify components:
   - Process list → find AC processes (service, tray, game-injected)
   - Driver list → find AC kernel module
   - r2 -AA EasyAntiCheat.exe → map imports, find DeviceIoControl calls

2. Map communication:
   - User-mode → driver: DeviceIoControl (IOCTL codes)
   - Service → game module: shared memory / named pipe / RPC
   - Service → backend: HTTPS / custom protocol

3. THEN analyze the driver with the IPC protocol already understood.
```

**Why:** Jumping straight into the driver binary is like reading a server without knowing the protocol. The user-mode component *tells you* what the driver expects — IOCTL codes, buffer structures, heartbeat cadence. Reverse the client first, the server second.

---

## 2. Catalog Every Kernel Callback the Driver Registers

**The driver's `DriverEntry` registers callbacks that ARE the detection surface. Find every one — a missed callback is a missed detection vector.**

The kernel driver's power comes from OS notification callbacks. These are the standard ones, in order of importance for AC analysis:

| Callback Registration | What It Monitors | AC Use |
|---|---|---|
| `ObRegisterCallbacks` | Process/thread handle operations | **Handle stripping** — removes `PROCESS_VM_READ`/`PROCESS_VM_WRITE` from external handles to the game. This is the #1 reason external memory tools fail. |
| `PsSetCreateProcessNotifyRoutineEx` | Process creation/exit | Monitors for known cheat tools launching. Logs process names, paths, hashes. |
| `PsSetCreateThreadNotifyRoutineEx` | Thread creation | Detects remote thread injection (`CreateRemoteThread` into game process). |
| `PsSetLoadImageNotifyRoutine` | DLL/driver loading | Detects foreign modules loaded into game process or unsigned drivers loading into kernel. |
| `CmRegisterCallbackEx` | Registry access | Monitors for cheat-related registry keys (tool configs, driver service entries). |
| `FltRegisterFilter` | File system operations | Minifilter watching for cheat binaries on disk, log files, config files. |
| `EtwRegister` (TI provider) | Syscall-level telemetry | ETW Threat Intelligence provider captures `NtReadVirtualMemory`, `NtWriteVirtualMemory`, `NtAllocateVirtualMemory` across processes. |

**How to find them:** In IDA/r2, open the driver's import table and search for these function names. Each import is a registration call — xref it to find the callback function being registered.

```
# radare2 — find callback registrations in a driver
r2 -AA driver.sys
afl~ObRegister                    # find ObRegisterCallbacks
afl~PsSetCreate                   # find process/thread notify
afl~PsSetLoadImage                # find image load notify
afl~CmRegister                    # find registry callbacks
afl~FltRegister                   # find minifilter registration
afl~EtwRegister                   # find ETW providers

# For each hit, disassemble the caller to find the callback function:
pdf @ sym.imp.ObRegisterCallbacks  # see who calls it
axt @ sym.imp.ObRegisterCallbacks  # xrefs to the import
```

```
// WinDbg — enumerate live callback arrays in kernel
!callback                                    // all registered callbacks
dt nt!_OBJECT_TYPE poi(nt!ObTypeIndexTable+0x38) // process object type callbacks
!object \ObjectTypes\Process                  // OB callbacks on process objects
```

**Why:** If you miss a callback, you miss a detection vector. An AC with an `ObRegisterCallbacks` handler will strip your handles silently — your `OpenProcess` succeeds but returns a handle with no VM access, and your reads return STATUS_ACCESS_DENIED without you understanding why. Map them all.

---

## 3. Trace the Driver ↔ User-Mode Communication Channel

**The driver and user-mode service talk constantly. Find the protocol: IOCTLs, shared memory, events. The heartbeat is the first thing to understand.**

Every kernel AC has a communication channel between its driver and user-mode components. This channel carries:
- **Heartbeat/keepalive** — periodic "I'm alive and unmodified" messages. If the heartbeat stops (driver unloaded, communication interrupted), the AC kills the game.
- **Scan requests** — the service asks the driver to scan specific memory regions, verify integrity, or enumerate handles.
- **Results** — the driver reports detected anomalies back to the service, which relays them to backend servers.

**Finding the channel:**

1. **IOCTLs:** Reverse the driver's `IRP_MJ_DEVICE_CONTROL` handler. This is a switch/jump table on IOCTL codes. Each code has an input and output buffer structure. See `skill://kernel-analysis` §2 for the technical pattern.

2. **Shared memory:** Look for `ZwMapViewOfSection` or `MmMapLockedPagesSpecifyCache` in the driver — these map a kernel buffer into user-mode address space for zero-copy communication.

3. **Events:** `IoCreateNotificationEvent` / `KeSetEvent` / `KeWaitForSingleObject` — the driver and service signal each other through named kernel events.

**The heartbeat pattern:**
```
Service                          Driver
   │                               │
   ├─── IOCTL_HEARTBEAT ──────────►│  (periodic, e.g. every 5-15 seconds)
   │    {timestamp, token, hash}   │
   │                               │── verify token + timing
   │◄── IOCTL_HEARTBEAT_ACK ──────┤
   │    {next_token, scan_cmd}     │
   │                               │
   │  (if no heartbeat for N sec)  │
   │                               │── KeSetEvent(game_kill_event)
   │                               │── or: ZwTerminateProcess(game)
```

**Why:** The heartbeat is the AC's self-integrity check. If you understand its cadence and token scheme, you understand what happens when the driver is absent, modified, or interrupted. Every bypass vector starts from knowing this protocol.

---

## 4. Identify What the AC Actually Scans For

**Don't guess at detection vectors — find the scan routines in the driver and catalog exactly what they check.**

Detection is not magic. It's code that reads specific locations and compares them to expected values. Common scan categories:

### Memory Integrity
- **Code section hashing:** The AC hashes the game's `.text` section periodically and compares against a known-good value. A modified instruction (NOP sled, hook, patch) fails the hash check.
- **Import table validation:** Verifies the game's IAT hasn't been hooked (function pointers still point into the expected module).
- **Stack walking:** Walks the call stack from a game function; an anomalous return address (pointing outside any loaded module) indicates injected code.

### System State
- **Hypervisor detection:** `CPUID` with `EAX=1` checks the VMX bit (ECX bit 31). `CPUID` with `EAX=0x40000000` returns a hypervisor brand string. Timing checks (`RDTSC` pairs) detect VM exit latency.
- **Debug register checks:** Reads `DR0`–`DR3` and `DR7` — hardware breakpoints on game memory are a strong cheat indicator.
- **DMA detection:** Queries IOMMU/VT-d status via `NtQuerySystemInformation`. If DMA remapping is disabled, a DMA device could be reading game memory externally.
- **Unsigned driver detection:** Walks `PsLoadedModuleList` and cross-references with `PiDDBCacheTable` / `MmUnloadedDrivers` to find manually mapped or unsigned kernel modules.

### Process/Handle Monitoring
- **Handle table walks:** Enumerates handles to the game process across all processes. Any external handle with VM read/write access is suspicious.
- **Module injection detection:** `PsSetLoadImageNotifyRoutine` flags DLLs loaded into the game that aren't on an allowlist.
- **Window enumeration:** Scans for windows with known cheat tool class names or titles (user-mode, but often triggered by the driver's scan commands).

```
# How to find scan routines in the driver:

# 1. Look for hash computation — scan for loops with XOR/rotate/add patterns
#    or calls to known hash functions (SHA256, CRC32, xxHash)

# 2. Look for NtQuerySystemInformation imports — these are system state queries
r2 -AA driver.sys
axt @ sym.imp.NtQuerySystemInformation    # who calls it?
# check the SystemInformationClass argument:
#   0x4D = SystemModuleInformation (driver list)
#   0x42 = SystemBigPoolInformation (pool allocations)
#   0x40 = SystemExtendedHandleInformation (handle table)

# 3. Look for MmGetSystemRoutineAddress — dynamic import resolution
#    AC drivers resolve NTAPI functions at runtime to avoid static import analysis
axt @ sym.imp.MmGetSystemRoutineAddress
```

**Why:** You can't avoid detection you don't understand. Each scan is a specific check with specific failure conditions. Catalog them, and you know exactly what's off-limits and what isn't monitored.

---

## 5. Analyze from Below the AC's Observation Layer

**Never run analysis tools on the same system as the AC. Use a VM, hardware debugger, or hypervisor-level tools.**

The AC monitors the system it runs on. If you run IDA, r2, Ghidra, Process Monitor, or even `tasklist` on the same box, the AC may detect and flag it. Analysis must happen from a layer the AC cannot observe.

### Environment Setup

| Layer | Tool | Visibility to AC |
|---|---|---|
| **Hardware debugger** | JTAG / Intel DCI | Invisible — hardware-level, no software artifacts |
| **Hypervisor debugger** | HyperDbg | Below the AC's hypervisor checks (if done right) |
| **Host → VM kernel debug** | WinDbg + VirtualKD-Redux | The AC sees a debugger-enabled boot (`KdDebuggerEnabled`), but can't prevent it from a hardware/pipe debugger |
| **Offline memory dump** | WinPmem → Volatility 3 | No live interaction — analyze a snapshot |
| **DMA acquisition** | PCILeech + MemProcFS | Physical memory access — invisible to software ACs |
| **Same-system tools** | Process Monitor, API Monitor | **Visible** — AC may detect and flag |

### Best Practice

```
1. VM with snapshot:
   - Take snapshot BEFORE installing the AC
   - Install game + AC → analyze → revert to clean snapshot
   - The AC's boot-time checks (Vanguard ELAM) require a fresh boot in the VM

2. Kernel debug from host:
   - bcdedit /debug on (in VM)
   - WinDbg on host: File → Kernel Debug → Net (or pipe via VirtualKD)
   - Set breakpoints in the AC driver: bp EasyAntiCheat!DriverEntry

3. Static analysis on host:
   - Copy the driver binary OUT of the VM before the AC loads
   - Analyze the .sys file in IDA/Ghidra on the host
   - No interaction with the live AC system
```

**Why:** Analyzing an AC from the same system it protects is like auditing a security camera while standing in front of it. The VM boundary is the minimum isolation; offline analysis of extracted binaries is the safest.

---

## 6. Verify Your Understanding Against Live Behavior

**A reversed IOCTL table or callback list is a hypothesis until you confirm it against the running AC. Diff after updates — the AC evolves silently.**

Anti-cheat drivers update without notice. EAC pushes cloud rules. BattlEye streams shellcode. Vanguard updates `vgk.sys` with game patches. Your understanding from last week may be wrong today.

### Verification loop:
1. **Confirm callbacks are active:** In WinDbg, walk the callback arrays (`PspCreateProcessNotifyRoutine`, `PspCreateThreadNotifyRoutine`, `PspLoadImageNotifyRoutine`) and verify the AC driver's functions are in the list.
2. **Confirm IOCTL handling:** Send a known IOCTL from a test user-mode program (or log it via IRPMon) and verify the driver dispatches it as expected.
3. **Confirm detection triggers:** In a test VM, trigger a known detection vector (e.g., `OpenProcess` with `PROCESS_VM_READ` on the game) and observe whether the AC strips the handle, logs the event, or takes action.
4. **Diff after updates:** Extract the driver binary before and after a game update. Binary diff in IDA (`BinDiff`) or r2 (`radiff2`) to see what changed.

```
# radare2 — diff two driver versions
radiff2 -C EasyAntiCheat_old.sys EasyAntiCheat_new.sys

# WinDbg — check process notify callbacks
kd> dd nt!PspCreateProcessNotifyRoutine L10
# each non-zero entry is a callback — resolve to module:
kd> ln <address_from_above>

# WinDbg — verify ObRegisterCallbacks on process objects
kd> !object \ObjectTypes\Process
kd> dt nt!_OBJECT_TYPE poi(<process_type_addr>) .CallbackList
```

**Why:** The AC is a moving target. A callback you reversed last month may have been replaced, reordered, or supplemented. A verified understanding is current; everything else is stale. Treat every analysis session as potentially outdated and re-confirm the critical paths.

---

## Summary

| # | Step | One-liner |
|---|------|-----------|
| 1 | Map the stack | Enumerate all components and communication channels; start with user-mode |
| 2 | Catalog callbacks | Find every kernel callback registration — each one is a detection vector |
| 3 | Trace communication | Reverse the IOCTL protocol and heartbeat mechanism |
| 4 | Identify scans | Find what the AC checks: code integrity, system state, handles, modules |
| 5 | Analyze from below | VM + host debugger + offline analysis; never from the same OS instance |
| 6 | Verify live | Confirm against the running AC; diff after every update |
