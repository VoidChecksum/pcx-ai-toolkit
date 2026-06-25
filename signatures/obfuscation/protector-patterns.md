# Protector Identification Patterns

Byte patterns, section names, and behavioral signatures for identifying binary protectors. Use for triage — name the protector before starting analysis.

> These patterns identify the protector. For deobfuscation methodology, see `skill://deobfuscation`. For detailed protector architecture, see `knowledge/obfuscation-taxonomy.md`.

---

## Section Name Identification

The fastest way to identify a protector — check the PE section table:

| Section Name(s) | Protector | Notes |
|-----------------|-----------|-------|
| `.vmp0`, `.vmp1`, `.vmp2` | **VMProtect** | VM bytecode sections; number = VM instance index |
| `.themida`, `.winlice` | **Themida / WinLicense** | Protection data + VM bytecode |
| `.Themida` (capital T) | **Themida** (older) | Pre-3.x versions |
| `.cv` or `.cvirt` | **Code Virtualizer** | Oreans VM-only product |
| `.enigma1`, `.enigma2` | **Enigma Protector** | Protection data |
| `.obsidium` | **Obsidium** | Anti-debug + encryption |
| `.perplex` | **Perplex** | Less common protector |
| `.aspack`, `.adata` | **ASPack** | Simple packer (no VM) |
| `.nsp0`, `.nsp1` | **NSPack** | Simple packer |
| `.petite` | **Petite** | Compression-only packer |
| `.UPX0`, `.UPX1` | **UPX** | Open-source packer (trivially unpackable) |
| `.text` with 0 raw size | **Generic packer** | Section exists but is empty on disk — filled at runtime |

```
# radare2 — check sections
r2 -nn target.exe
iS
# Look for known protector section names
# Also check: section with VirtualSize >> RawSize = unpacked at runtime

# Python (pefile)
import pefile
pe = pefile.PE('target.exe')
for s in pe.sections:
    print(f"{s.Name.decode().rstrip(chr(0)):10s} VS={s.Misc_VirtualSize:#x} RS={s.SizeOfRawData:#x}")
```

---

## VMProtect Patterns

### VM Entry Stub

Every VMP-protected function begins with a VM entry that saves registers, sets up the VM context, and jumps to the dispatcher:

```asm
; VMP entry pattern (x64):
push    <encrypted_key>          ; 68 ?? ?? ?? ??
call    <vmenter>                ; E8 ?? ?? ?? ??
; OR (in newer VMP):
push    <key>
jmp     <vmenter>                ; E9 ?? ?? ?? ??
```

**Byte pattern:**
```
# VM entry: PUSH imm32 + CALL/JMP rel32
68 ?? ?? ?? ?? E8 ?? ?? ?? ??    # push key; call vmenter
68 ?? ?? ?? ?? E9 ?? ?? ?? ??    # push key; jmp vmenter
```

**Python / toolkit snippet:**
```python
# tools/bin/analyze-vmprotect detects these automatically, but you can scan manually:
import re
for m in re.finditer(rb'\x68....[\xe8\xe9]....', code_section):
    print(f"possible VMP entry stub at file offset {m.start()}")
```

### VMProtect 2.x Import Stub

VMP 2.x typically replaces each imported API call with a small stub that loads
the resolved address from a private IAT slot at runtime:

```asm
jmp     qword ptr [rip + iat_entry]
; or
mov     rax, [rip + iat_entry]
jmp     rax
```

```
FF 25 ?? ?? ?? ??          # jmp [rip+imm32]
48 8B 05 ?? ?? ?? ?? FF E0  # mov rax,[rip+imm32]; jmp rax
```

### VM Dispatcher (inner loop)

```asm
; Typical VMP dispatcher loop (x64):
; Fetch opcode from bytecode stream
movzx   eax, byte ptr [<VIP>]     ; fetch bytecode
; Decode — usually XOR with rolling key
xor     al, <key_byte>
; Dispatch via handler table
lea     rdx, [handler_table]
jmp     qword ptr [rdx + rax*8]   ; computed goto to handler
```

**Pattern for dispatcher fetch:**
```
# MOVZX + XOR + LEA + JMP [table] pattern
0F B6 ??                         # movzx reg, byte [VIP]
?? ?? ??                         # XOR/ADD/SUB with key (varies)
48 8D ?? ?? ?? ?? ??             # lea reg, [rip+handler_table]
FF 24 ?? ??                      # jmp [reg + index*8]
```

### VMP Import Stub

VMP's import protection redirects each API call through a unique stub:

```asm
; Import stub pattern:
jmp     qword ptr [rip + <iat_entry>]
; Or through a thunk:
mov     rax, <resolved_addr>
jmp     rax
```

---

## Themida / WinLicense Patterns

### VM Entry

```asm
; Themida VM entry (x64):
push    rbp
push    rdi
push    rsi
push    rbx
; ... save more registers ...
mov     <VPC_reg>, <bytecode_addr>     ; load bytecode pointer
jmp     <dispatcher>
```

### Dispatcher (computed goto)

```asm
; Themida dispatcher (FISH/TIGER):
movzx   eax, byte ptr [<VPC>]         ; fetch opcode
add     <VPC>, 1                       ; advance VPC
jmp     qword ptr [<handler_table> + rax*8]   ; dispatch
```

**Byte pattern for Themida dispatch:**
```
# MOVZX + INC/ADD VPC + JMP [table + reg*8]
0F B6 ??                   # movzx eax, byte [VPC]
48 FF C?                   # inc VPC (or 48 83 C? 01 = add VPC, 1)
FF 24 C5 ?? ?? ?? ??       # jmp [handler_table + rax*8]
```

### Anti-Debug (common in Themida)

```asm
; IsDebuggerPresent check:
64 48 8B 04 25 60 00 00 00   ; mov rax, gs:[0x60]  (PEB via TEB)
0F B6 40 02                   ; movzx eax, [rax+2]  (PEB.BeingDebugged)
85 C0                         ; test eax, eax
0F 85 ?? ?? ?? ??             ; jnz <detected>
```

**Byte pattern:**
```
64 48 8B 04 25 60 00 00 00 0F B6 40 02 85 C0
```

### Watermark Strings

```
# Search for protector watermark strings:
# "THEMIDA" (UTF-16LE):
54 00 48 00 45 00 4D 00 49 00 44 00 41 00

# "WinLicense" (UTF-16LE):
57 00 69 00 6E 00 4C 00 69 00 63 00 65 00 6E 00 73 00 65 00
```

---

## OLLVM / Hikari Patterns

### Control Flow Flattening Dispatcher

```asm
; CFF dispatcher (typical OLLVM output):
; One large basic block with a switch on a state variable
mov     eax, [rbp-0x??]           ; load state variable
cmp     eax, <state_N>            ; compare against state constant
je      <block_N>                 ; jump to state's block
cmp     eax, <state_M>
je      <block_M>
; ... many more comparisons ...
jmp     <default_or_loop_back>
```

**Identifying CFF in the CFG:**
- One function with a single entry and a central dispatcher
- The dispatcher has 10-200+ outgoing edges (one per state)
- Each destination block ends by setting the state variable and jumping back to the dispatcher
- The state variable is usually a local (stack variable)

### Opaque Predicates

```asm
; Opaque predicate (always true):
mov     eax, <random_constant>
imul    eax, eax                   ; eax = x^2
and     eax, 1                     ; x^2 mod 2 — always 0 for even x
jnz     <never_taken_path>         ; this branch is never taken
; Real code continues here

; Opaque predicate (always false — dead path):
; Similar pattern but the condition is always met, making the jnz always jump
```

### MBA Expressions

```asm
; Simple MBA: x + y obfuscated
; Original: add eax, ecx
; MBA form:
mov     edx, eax
xor     edx, ecx                   ; edx = x ^ y
and     eax, ecx                   ; eax = x & y
shl     eax, 1                     ; eax = 2 * (x & y)
add     eax, edx                   ; eax = (x ^ y) + 2*(x & y) = x + y
```

---

## Generic Packer Patterns

### OEP Detection (VirtualProtect breakpoint)

All packers must unpack the code into memory and make it executable. This means calling `VirtualProtect` with `PAGE_EXECUTE_READ` or `PAGE_EXECUTE_READWRITE`:

```
# Break on VirtualProtect, check for:
# - flNewProtect == 0x20 (PAGE_EXECUTE_READ) or 0x40 (PAGE_EXECUTE_READWRITE)
# - dwSize is large (covers most/all of .text)
# - lpAddress points to the main module's .text section
```

### IAT Redirection

Protectors redirect imports through stubs to prevent simple IAT analysis:

```asm
; Direct import (unprotected):
call    qword ptr [rip + <IAT_entry>]    ; calls kernel32!CreateFileW

; Redirected import (protected):
call    <protector_stub>
; Inside the stub:
jmp     qword ptr [<encrypted_ptr>]       ; decrypts + jumps to real API
; Or:
mov     rax, <resolved_addr>              ; address resolved at runtime
jmp     rax
```

---

## Anti-Debug API Patterns

Common anti-debug calls to look for in any protected binary:

```
# x64 — PEB.BeingDebugged via TEB
64 48 8B 04 25 60 00 00 00    # mov rax, gs:[0x60]  — PEB pointer
0F B6 40 02                    # movzx eax, [rax+2]  — BeingDebugged byte

# NtQueryInformationProcess(ProcessDebugPort)
# Look for: syscall or call to ntdll!NtQueryInformationProcess
# with InfoClass = 7 (ProcessDebugPort)

# RDTSC timing pair
0F 31                          # rdtsc (first)
# ... code under timing ...
0F 31                          # rdtsc (second)
# Delta comparison follows

# int 2d (SEH-based debug detection)
CD 2D                          # int 0x2D — raises exception in debugger
```

---

## Usage with Perception

```cpp
// Scan a game module for protector section names
auto mod = p.get_module("GameAssembly.dll");
uint64 base = mod.base();

// Check for VMP sections
uint64 vmp0 = p.find_code_pattern(base, 0x1000,
    "2E 76 6D 70 30");  // ".vmp0" ASCII
if (vmp0 != 0) {
    println("VMProtect detected — .vmp0 section found");
}

// Find VM entry stubs (push imm32; call rel32)
uint64 vm_entry = p.find_code_pattern(base, mod.size(),
    "68 ?? ?? ?? ?? E8 ?? ?? ?? ??");
if (vm_entry != 0) {
    println(format("Potential VM entry @ 0x{x}", vm_entry));
    // Disassemble to confirm
    p.disassemble(vm_entry, 16);
}
```
