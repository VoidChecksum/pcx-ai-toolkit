# Anti-Cheat Driver Identification Patterns

Byte patterns and file signatures for identifying known anti-cheat drivers in memory or on disk. Use with `find_code_pattern` or `r2` / IDA pattern search.

> These patterns identify the AC driver for triage. They are NOT bypass patterns — they help you confirm *which* AC you're looking at before starting analysis.

---

## Driver File Identification

### By File Name

| Driver File | Anti-Cheat | Notes |
|---|---|---|
| `EasyAntiCheat.sys` | EAC (legacy) | Older standalone variant |
| `EasyAntiCheat_EOS.sys` | EAC (EOS platform) | Current Epic Online Services variant |
| `BEDaisy.sys` | BattlEye | Named after the BattlEye "daisy" component |
| `vgk.sys` | Vanguard | Riot Games; loads at boot (ELAM) |
| `GameGuard.des` / `GameMon.des` / `GameMon64.des` | nProtect GameGuard | `.des` extension is GameGuard's convention |
| `xhunter1.sys` | XIGNCODE3 | Wellbia kernel driver |
| `mhyprot2.sys` / `mhyprot3.sys` | mhyprotect | miHoYo/HoYoverse (Genshin Impact) |
| `atc_rkl.sys` | RICOCHET | Activision anti-cheat (COD) |
| `byfron.sys` / `hyperion.sys` | Byfron / Hyperion | Roblox anti-cheat |
| `ngc.sys` | Nexon Game Controller | Nexon anti-cheat |

### By Service Registry Key

```
HKLM\SYSTEM\CurrentControlSet\Services\EasyAntiCheat       → EAC (legacy)
HKLM\SYSTEM\CurrentControlSet\Services\EasyAntiCheatEOS    → EAC (EOS)
HKLM\SYSTEM\CurrentControlSet\Services\BEService           → BattlEye service
HKLM\SYSTEM\CurrentControlSet\Services\BEDaisy             → BattlEye driver
HKLM\SYSTEM\CurrentControlSet\Services\vgk                 → Vanguard
HKLM\SYSTEM\CurrentControlSet\Services\vgc                 → Vanguard client
```

---

## Driver Binary Patterns

### DriverEntry Identification

Patterns to locate `DriverEntry` and identify the AC by its initialization sequence. All patterns are x86-64.

**EAC — device name string in DriverEntry:**
```
# Unicode string L"\\Device\\EasyAntiCheat" or L"\\Device\\EasyAntiCheatEOS"
# Search for the UTF-16LE encoded device name:
5C 00 44 00 65 00 76 00 69 00 63 00 65 00 5C 00 45 00 61 00 73 00 79 00
# = \Device\Easy...
```

**BattlEye — BEDaisy device creation:**
```
# Unicode L"\\Device\\BEDaisy"
5C 00 44 00 65 00 76 00 69 00 63 00 65 00 5C 00 42 00 45 00 44 00 61 00
```

**Vanguard — vgk device:**
```
# Unicode L"\\Device\\vgk"
5C 00 44 00 65 00 76 00 69 00 63 00 65 00 5C 00 76 00 67 00 6B 00
```

---

## Kernel Callback Registration Patterns

Patterns for finding where the AC driver registers its kernel callbacks. These match the call site, not the callback function itself.

### ObRegisterCallbacks Call Site

```
# Typical pattern: LEA RCX, [rip+disp] (callback registration struct) followed by CALL ObRegisterCallbacks
# Pattern: LEA RCX, [rip+??] → CALL [rip+??] (or CALL reg)
48 8D 0D ?? ?? ?? ??    # lea rcx, [rip+disp]  ← points to OB_CALLBACK_REGISTRATION
48 8D 15 ?? ?? ?? ??    # lea rdx, [rip+disp]  ← points to output handle
E8 ?? ?? ?? ??          # call ObRegisterCallbacks (or indirect)
```

### PsSetCreateProcessNotifyRoutineEx Call Site

```
# Pattern: LEA RCX, [rip+disp] (callback fn) → XOR EDX, EDX (bRemove=FALSE) → CALL
48 8D 0D ?? ?? ?? ??    # lea rcx, [rip+disp]  ← the notify routine
33 D2                   # xor edx, edx         ← bRemove = FALSE
E8 ?? ?? ?? ??          # call PsSetCreateProcessNotifyRoutineEx
```

### PsSetLoadImageNotifyRoutine Call Site

```
# Same pattern, but only one argument (the callback function):
48 8D 0D ?? ?? ?? ??    # lea rcx, [rip+disp]  ← the notify routine
E8 ?? ?? ?? ??          # call PsSetLoadImageNotifyRoutine
```

---

## Dynamic Import Resolution Patterns

AC drivers resolve NTAPI functions at runtime to avoid appearing in the import table.

### MmGetSystemRoutineAddress Pattern

```
# LEA RCX with UNICODE_STRING → CALL MmGetSystemRoutineAddress
# The UNICODE_STRING contains the API name being resolved
48 8D 0D ?? ?? ?? ??    # lea rcx, [rip+disp]  ← UNICODE_STRING
FF 15 ?? ?? ?? ??       # call [rip+disp]       ← MmGetSystemRoutineAddress
48 89 05 ?? ?? ?? ??    # mov [rip+disp], rax   ← store resolved function pointer
```

### Hash-Based Import Resolution

```
# Loop pattern: iterate ntoskrnl exports, hash each name, compare against constant
# Look for:
# 1. A loop reading export directory entries
# 2. A hash accumulator (ROR/XOR/ADD pattern)
# 3. CMP against a 32-bit constant (the target hash)
# 4. Conditional branch to "found" path

# Common hash: ROR13 + ADD (used by many malware and AC loaders)
# Inner loop body:
0F B6 ??                # movzx reg, byte [ptr]  ← read character
C1 C? 0D                # ror reg, 0x0D          ← rotate right 13
03 ??                   # add reg, reg2           ← accumulate
```

---

## Integrity Check Patterns

### RDTSC Timing Check

```
# Paired RDTSC with delta comparison:
0F 31                   # rdtsc           ← first timestamp
89 C?                   # mov reg, eax    ← save low 32 bits
# ... operations under timing ...
0F 31                   # rdtsc           ← second timestamp
2B C?                   # sub eax, reg    ← compute delta
3D ?? ?? 00 00          # cmp eax, imm32  ← threshold comparison (usually 0x100-0x10000)
```

### CPUID Hypervisor Detection

```
# CPUID leaf 1, check bit 31 of ECX:
B8 01 00 00 00          # mov eax, 1
0F A2                   # cpuid
0F BA E1 1F             # bt ecx, 0x1F   ← test hypervisor present bit
# Or: TEST ECX with mask
F7 C1 00 00 00 80       # test ecx, 0x80000000

# CPUID leaf 0x40000000 (hypervisor brand):
B8 00 00 00 40          # mov eax, 0x40000000
0F A2                   # cpuid
# EBX:ECX:EDX = brand string
```

---

## Usage with Perception

```cpp
// Scan for a known AC driver in the kernel module list
// Requires kernel_rw_access permission
uint64 base = p.get_module_base("EasyAntiCheat_EOS.sys");
if (base != 0) {
    uint64 size = p.get_module_size("EasyAntiCheat_EOS.sys");
    println(format("EAC driver @ 0x{x}, size 0x{x}", base, size));

    // Find ObRegisterCallbacks call site
    uint64 ob_reg = p.find_code_pattern(base, size,
        "48 8D 0D ?? ?? ?? ?? 48 8D 15 ?? ?? ?? ?? E8 ?? ?? ?? ??");
    if (ob_reg != 0) {
        println(format("ObRegisterCallbacks call @ 0x{x}", ob_reg));
        // Resolve the OB_CALLBACK_REGISTRATION struct via RIP-relative
        int32 disp = p.r32(ob_reg + 3);
        uint64 reg_struct = ob_reg + 7 + cast<uint64>(disp);
        println(format("OB_CALLBACK_REGISTRATION @ 0x{x}", reg_struct));
    }
}
```

---

## Notes

- These patterns are for **identification and analysis**, not detection evasion.
- AC drivers update frequently — patterns may shift between versions. Always verify against the current binary.
- Obfuscated drivers (XIGNCODE3/VMProtect, some EAC builds) may not match static patterns — use dynamic analysis for those.
- See `knowledge/anti-cheat-architecture.md` for the full detection taxonomy per AC.
