# Kernel Anti-Cheat Architecture Reference

Architecture, components, and detection techniques for major kernel-level anti-cheat systems. Read this before starting AC analysis — it tells you what you're looking at and what each AC is known to monitor.

> **Scope:** Authorized security research only. See `skill://authorized-security-research` before interacting with any live AC system.

---

## Architecture Overview

Every kernel anti-cheat follows the same layered model, with variation in which layers each AC implements:

```
┌──────────────────────────────────────────────────────────┐
│                     Backend Servers                       │
│  (detection rules, telemetry collection, ban decisions)  │
└─────────────────────────┬────────────────────────────────┘
                          │ HTTPS / custom protocol
┌─────────────────────────▼────────────────────────────────┐
│                   AC User-Mode Service                    │
│  (EasyAntiCheat.exe / BEService.exe / vgc.exe)           │
│  Manages driver lifecycle, relays telemetry, heartbeat   │
└──────┬──────────────────┬────────────────────────────────┘
       │ IOCTL / shared   │ injection / pipe
       │ memory / events  │
┌──────▼──────────┐ ┌─────▼─────────────────────────────┐
│  Kernel Driver   │ │  Game-Injected Module              │
│  (.sys)          │ │  (DLL in game process)             │
│  Ring 0          │ │  User-mode integrity, screenshots, │
│  Callbacks,      │ │  in-process scans, heartbeat       │
│  handle strip,   │ └───────────────────────────────────┘
│  system scans    │
└──────────────────┘
```

---

## Per-AC Architecture

### EAC (Easy Anti-Cheat / EOS Anti-Cheat)

| Property | Detail |
|----------|--------|
| **Publisher** | Epic Games (acquired from Kamu, 2018) |
| **Games** | Fortnite, Apex Legends, Rust, Dead by Daylight, The Finals, Hunt: Showdown, Halo MCC, Dark and Darker, many more |
| **User-mode service** | `EasyAntiCheat.exe` (legacy) or `EasyAntiCheat_EOS.exe` (EOS platform) |
| **Game-injected module** | Loaded into game process; performs in-process scans |
| **Kernel driver** | `EasyAntiCheat.sys` or `EasyAntiCheat_EOS.sys` — loaded on demand when game launches, unloaded on exit |
| **Communication** | IOCTL between driver ↔ service; encrypted heartbeat between service ↔ game module; heartbeat failure = game termination |
| **Update mechanism** | Driver is signed; user-mode module updates with game patches; cloud-based detection rules push without client update |
| **Boot behavior** | Loads with the game, not at boot |

**Known driver callbacks:**
- `ObRegisterCallbacks` — strips `PROCESS_VM_READ`/`PROCESS_VM_WRITE` from external handles to the game
- `PsSetCreateProcessNotifyRoutineEx` — monitors process creation
- `PsSetCreateThreadNotifyRoutineEx` — monitors thread creation (injection detection)
- `PsSetLoadImageNotifyRoutine` — monitors module loading
- Minifilter registration — file system monitoring

**Known detection vectors:**
- External process handle with VM access to game
- Module injection into game process (unsigned DLLs)
- Unsigned kernel driver loading
- Hypervisor presence (CPUID checks)
- Debug registers set on game memory
- Code integrity — `.text` section hashing
- Stack anomalies — return addresses outside loaded modules
- Window class/title scanning for known cheat UIs

---

### BattlEye

| Property | Detail |
|----------|--------|
| **Publisher** | BattlEye Innovations (Germany) |
| **Games** | PUBG, R6 Siege, DayZ, Arma 3, Escape from Tarkov, Destiny 2, Fortnite (previously) |
| **User-mode service** | `BEService.exe` — runs as a Windows service |
| **Game-injected module** | `BEClient.dll` / `BEClient_x64.dll` — injected into game process |
| **Kernel driver** | `BEDaisy.sys` — loaded via SCM when game launches |
| **Communication** | Named pipe between service ↔ driver; `BEClient.dll` ↔ `BEService.exe` over local IPC; service ↔ BattlEye backend over HTTPS |
| **Unique** | **BEClient.dll receives shellcode from BattlEye servers at runtime** — detection logic is streamed, not static. This makes static analysis of detection rules nearly impossible. The shellcode runs in the game process context. |
| **Boot behavior** | Loads with the game, not at boot |

**Known driver callbacks:**
- `ObRegisterCallbacks` — handle stripping
- Process, thread, image notification callbacks
- System thread creation for periodic background scans

**Known detection vectors:**
- All of EAC's vectors, plus:
- Window enumeration (`FindWindow` / `EnumWindows` for known cheat tool class names)
- Process name scanning (checks running process names against a list)
- Memory pattern scans inside the game address space (streamed via shellcode)
- Registry key checks for known cheat tool installations
- Driver signing enforcement monitoring

**Analysis difficulty:** HIGH — the streamed shellcode means detection logic changes server-side without any client update. You must capture and analyze the shellcode during a live session.

---

### Vanguard (Riot Games)

| Property | Detail |
|----------|--------|
| **Publisher** | Riot Games |
| **Games** | Valorant, League of Legends (optional) |
| **Kernel driver** | `vgk.sys` — **always-on, loads at boot** |
| **User-mode client** | `vgc.exe` |
| **System tray** | `vgtray.exe` |
| **Boot mechanism** | ELAM (Early Launch Anti-Malware) — loads before third-party drivers, sees everything that loads after it |
| **Requirements** | TPM 2.0, Secure Boot enabled (enforced) |
| **Communication** | Shared memory + fast mutex between `vgk.sys` ↔ `vgc.exe` |
| **Always-on** | Unlike EAC/BE which load with the game, Vanguard runs from boot until manually disabled. Controversial but effective — detects cheat drivers that load before the game. |

**Known driver capabilities:**
- All standard kernel callbacks (process, thread, image, registry, handle)
- Boot-time driver load monitoring (sees every driver that loads)
- Secure Boot chain validation
- TPM attestation
- Hypervisor-level integrity checks
- System integrity verification before allowing game launch

**Analysis difficulty:** VERY HIGH — boot-time loading means snapshot-before-install VM workflow is essential. The ELAM driver loads before most debugging infrastructure.

---

### nProtect GameGuard

| Property | Detail |
|----------|--------|
| **Publisher** | INCA Internet (South Korea) |
| **Games** | MapleStory, Lineage 2, Aion, Black Desert Online, Lost Ark, many Asian MMOs |
| **Components** | GameGuard service, kernel driver (`GameGuard.des` / `GameMon.des` / `GameMon64.des`), game module |
| **Known for** | Aggressive rootkit-like behavior in older versions — SSDT hooks, process hiding, API interception |
| **Legacy behavior** | Older versions hooked the SSDT (System Service Descriptor Table) directly — pre-PatchGuard technique. Modern versions use standard callbacks. |
| **Detection** | Heavy user-mode API hooking in addition to kernel callbacks; monitors clipboard, screenshots, window messages |

---

### XIGNCODE3

| Property | Detail |
|----------|--------|
| **Publisher** | Wellbia.com (South Korea) |
| **Games** | PUBG Mobile (PC emulator), various Asian MMOs and mobile games |
| **Components** | User-mode module + kernel driver |
| **Known for** | Kernel driver + heavy code obfuscation (VMProtect on critical sections), anti-VM checks, timing-based detection |
| **Obfuscation** | Critical driver sections are virtualized with VMProtect — significantly increases analysis difficulty |

---

### Theia (Embark Studios)

| Property | Detail |
|----------|--------|
| **Publisher** | Embark Studios |
| **Games** | The Finals (alongside EAC) |
| **Architecture** | Primarily **server-side** — AI-based behavioral analysis |
| **Components** | Minimal client-side component; heavy server-side telemetry analysis, screenshot capture and AI analysis |
| **Unique** | Focuses on behavioral detection rather than system-level monitoring; runs alongside a traditional AC (EAC) for the system-level layer |

---

## Detection Technique Matrix

Which AC uses which technique (based on public research and analysis):

| Detection Technique | EAC | BattlEye | Vanguard | GameGuard | XIGNCODE3 |
|---|:---:|:---:|:---:|:---:|:---:|
| **Handle stripping** (ObRegisterCallbacks) | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Process creation notify** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Thread creation notify** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Image load notify** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Registry callbacks** | ✓ | ✓ | ✓ | ✓ | — |
| **Minifilter (file system)** | ✓ | — | ✓ | ✓ | — |
| **ETW Threat Intelligence** | ✓ | — | ✓ | — | — |
| **Code integrity hashing** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Stack walking** | ✓ | ✓ | ✓ | — | — |
| **Hypervisor detection** | ✓ | ✓ | ✓ | — | ✓ |
| **DMA/IOMMU detection** | ✓ | — | ✓ | — | — |
| **RDTSC timing checks** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Debug register checks** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Module scanning (in-process)** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Window enumeration** | — | ✓ | ✓ | ✓ | — |
| **Streamed detection code** | — | ✓ | — | — | — |
| **Boot-time monitoring** | — | — | ✓ | — | — |
| **TPM / Secure Boot** | — | — | ✓ | — | — |
| **SSDT hooks** (legacy) | — | — | — | ✓ | — |
| **Unsigned driver detection** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Server-side AI analysis** | — | — | — | — | — |

> *Theia omitted — its detection is primarily server-side and not comparable to kernel techniques.*

---

## Anti-Cheat by Game (PCX-Supported Titles)

| Game | Primary AC | Secondary AC | Notes |
|------|-----------|-------------|-------|
| Counter-Strike 2 | VAC | — | Server-side + user-mode; no kernel driver |
| Apex Legends | EAC | — | EOS variant |
| Fortnite | EAC | — | EOS variant |
| PUBG (Steam) | BattlEye | — | `BEDaisy.sys` |
| Escape from Tarkov | BattlEye | — | `BEDaisy.sys` |
| Rainbow Six Siege | BattlEye | — | `BEDaisy.sys` |
| Valorant | Vanguard | — | Boot-time `vgk.sys` |
| The Finals | EAC | Theia | EAC for system-level, Theia for behavioral |
| Dead by Daylight | EAC | — | EOS variant |
| DayZ | BattlEye | — | `BEDaisy.sys` |
| Rust | EAC | — | EOS variant |
| Hunt: Showdown 1896 | EAC | — | EOS variant |
| COD: BO7 / Warzone | RICOCHET | — | Activision's custom kernel AC |
| Overwatch 2 | Custom | — | Blizzard proprietary |
| Deadlock | VAC | — | Server-side |
| Arena Breakout Infinite | EAC | — | EOS variant |
| Marvel Rivals | EAC | — | — |
| Roblox | Byfron (Hyperion) | — | Custom kernel AC (acquired 2022) |

> Games not listed here either use no kernel AC (VAC/server-side only) or use a proprietary solution not publicly documented.

---

## Key Structures Reference

Frequently referenced Windows kernel structures in AC analysis:

```c
// Handle stripping callback context
typedef struct _OB_PRE_OPERATION_INFORMATION {
    OB_OPERATION           Operation;       // OB_OPERATION_HANDLE_CREATE or _DUPLICATE
    union {
        ULONG Flags;
        struct { ULONG KernelHandle:1; ULONG Reserved:31; };
    };
    PVOID                  Object;          // the process/thread being opened
    POBJECT_TYPE           ObjectType;
    PVOID                  CallContext;
    POB_PRE_OPERATION_PARAMETERS Parameters; // contains DesiredAccess to modify
} OB_PRE_OPERATION_INFORMATION;

// The AC's PreOperation callback does:
//   if (target_is_game_process && !opener_is_ac_service)
//       info->Parameters->CreateHandleInformation.DesiredAccess &=
//           ~(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION);
```

```c
// Driver callback arrays in ntoskrnl (symbols):
// PspCreateProcessNotifyRoutine  — array of EX_CALLBACK_ROUTINE_BLOCK pointers
// PspCreateThreadNotifyRoutine   — same
// PspLoadImageNotifyRoutine      — same
// PspCreateProcessNotifyRoutineCount/ExCount — counts
//
// Each entry: pointer with low 4 bits as flags.
// Clear low bits to get the EX_CALLBACK_ROUTINE_BLOCK, then read .Function.
```

---

## Practical Workflow

1. **Identify the AC** — check `game-targets.md` or `system/list_drivers` for known driver names
2. **Read this doc** — understand the AC's known architecture and detection vectors
3. **Follow `skill://anti-cheat-re`** — the six-step methodology
4. **Use `skill://kernel-analysis`** — technical patterns for driver reversing
5. **Refer to `knowledge/kernel-re-tools.md`** — tooling for each workflow stage
