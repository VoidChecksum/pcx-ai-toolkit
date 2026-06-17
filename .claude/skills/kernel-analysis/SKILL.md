# Kernel Driver Analysis — Technical Patterns for AC Driver Reversing

Technical patterns for reversing Windows kernel drivers: WDM/KMDF structure identification, IOCTL dispatch table extraction, kernel callback enumeration, integrity check routines, obfuscation layers, and driver communication protocols. Focused on anti-cheat driver analysis but applicable to any Windows kernel module.

**Always active when analyzing kernel driver binaries.** This is the *technical patterns* layer — structures, commands, and code patterns. The `anti-cheat-re` skill covers the *methodology* (what order to work in and why). Load both.

**Prerequisite:** Read `knowledge/kernel-re-tools.md` for the tool reference.

## Trigger
Analyzing a `.sys` driver binary, reversing IOCTL handlers, mapping kernel callbacks, understanding WDM/KMDF dispatch tables, deobfuscating driver code, reconstructing shared memory communication, or working with kernel structures in IDA/Ghidra/radare2/WinDbg.

---

## 1. Identify the Driver Model Before Reading Instructions

**WDM, KMDF, or legacy — the model determines where the dispatch table lives and how IOCTLs are handled.**

Every Windows kernel driver has a `DriverEntry` function — the entry point. What it calls in the first few instructions tells you the model:

| Pattern in DriverEntry | Driver Model | Dispatch Location |
|---|---|---|
| `IoCreateDevice` + manual `MajorFunction[]` assignment | **WDM (legacy)** | `DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL]` |
| `WdfDriverCreate` + `WdfDeviceCreate` | **KMDF (modern)** | `WdfIoQueueCreate` with `EvtIoDeviceControl` callback |
| `GsDriverEntry` wrapper → real entry | **GS-protected** | Unwrap — the real `DriverEntry` is the first call inside |

Most anti-cheat drivers use **WDM** for direct control over IRP handling. KMDF adds a framework layer that ACs typically avoid.

```
# radare2 — find DriverEntry and identify model
r2 -AA driver.sys
afl~DriverEntry                              # find entry point
pdf @ entry0                                 # disassemble — look for first calls

# IDA — DriverEntry is the entry point
# Look for: IoCreateDevice (WDM) or WdfDriverCreate (KMDF)
# The second argument to IoCreateDevice is the device name

# WinDbg — inspect a loaded driver
!drvobj \Driver\EasyAntiCheat 7              # dump driver object + all MajorFunction handlers
dt nt!_DRIVER_OBJECT <addr>                  # raw driver object structure
```

**Finding the entry point:** In a PE driver, the entry point is `DriverEntry` (or `GsDriverEntry` which calls the real one). IDA labels it automatically with PDB or FLIRT. In r2, it's `entry0`. The function signature is:

```c
NTSTATUS DriverEntry(
    PDRIVER_OBJECT  DriverObject,   // rcx — the driver's identity
    PUNICODE_STRING RegistryPath    // rdx — HKLM\SYSTEM\...\Services\<name>
);
```

**Why:** Jumping into the instruction stream without knowing WDM vs. KMDF means you don't know where the IOCTL handler is. WDM drivers set `DriverObject->MajorFunction[14]` (IRP_MJ_DEVICE_CONTROL = 0x0E) directly in DriverEntry. KMDF drivers register it through `WdfIoQueueCreate`. Wrong model = you look in the wrong place.

---

## 2. Extract the IOCTL Dispatch Table

**The `IRP_MJ_DEVICE_CONTROL` handler contains the switch/jump table on IOCTL codes. Each code maps to a detection or communication function.**

In a WDM driver, the IOCTL handler is assigned in DriverEntry:

```c
DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = IoctlDispatch;
```

The `IoctlDispatch` function extracts the IOCTL code from the IRP stack location and switches on it:

```c
NTSTATUS IoctlDispatch(PDEVICE_OBJECT DeviceObject, PIRP Irp) {
    PIO_STACK_LOCATION stack = IoGetCurrentIrpStackLocation(Irp);
    ULONG code = stack->Parameters.DeviceIoControl.IoControlCode;

    switch (code) {
        case IOCTL_HEARTBEAT:       return HandleHeartbeat(Irp);
        case IOCTL_SCAN_REQUEST:    return HandleScanRequest(Irp);
        case IOCTL_QUERY_STATUS:    return HandleQueryStatus(Irp);
        // ...
    }
}
```

**Decoding IOCTL codes:** The `CTL_CODE` macro packs four fields into a 32-bit value:

```
Bits 31-16: DeviceType    (e.g., 0x22 = FILE_DEVICE_UNKNOWN)
Bits 15-14: Access        (0=ANY, 1=READ, 2=WRITE, 3=READ|WRITE)
Bits 13-2:  Function      (0x800+ = user-defined)
Bits 1-0:   Method        (0=BUFFERED, 1=IN_DIRECT, 2=OUT_DIRECT, 3=NEITHER)

CTL_CODE(DeviceType, Function, Method, Access)
  = (DeviceType << 16) | (Access << 14) | (Function << 2) | Method
```

```python
# Python — decode an IOCTL code
def decode_ioctl(code):
    device_type = (code >> 16) & 0xFFFF
    access      = (code >> 14) & 0x3
    function    = (code >> 2)  & 0xFFF
    method      = code & 0x3
    methods = {0: "BUFFERED", 1: "IN_DIRECT", 2: "OUT_DIRECT", 3: "NEITHER"}
    print(f"DeviceType=0x{device_type:X} Function=0x{function:X} "
          f"Method={methods[method]} Access={access}")

# Example: decode_ioctl(0x22E004) → DeviceType=0x22 Function=0x801 Method=BUFFERED Access=0
```

```
# radare2 — find the IOCTL dispatch
r2 -AA driver.sys
axt @ sym.imp.IoGetCurrentIrpStackLocation   # who calls it?
# navigate to the caller — the switch/cmp chain on the IOCTL code follows

# IDA — find MajorFunction[14] assignment in DriverEntry
# The function pointer stored at offset 0x70 + 14*8 = 0xE0 in the DRIVER_OBJECT
# is the IOCTL dispatch handler
```

**Why:** The IOCTL table is the driver's API surface. Each code corresponds to a specific operation — heartbeat, scan command, status query, configuration. Mapping these codes and their buffer structures gives you the complete protocol between user-mode and kernel.

---

## 3. Enumerate Registered Kernel Callbacks

**Each callback type has a specific structure and a global array in ntoskrnl. Find them in the driver binary (registration calls) and in live memory (the arrays).**

### ObRegisterCallbacks — Handle Filtering

The most important callback for anti-cheat: intercepts `ObOpenObjectByPointer` / `NtOpenProcess` and can modify the granted access mask.

```c
// Registration structure
typedef struct _OB_CALLBACK_REGISTRATION {
    USHORT                    Version;          // OB_FLT_REGISTRATION_VERSION
    USHORT                    OperationRegistrationCount;
    UNICODE_STRING            Altitude;         // e.g., L"321000"
    PVOID                     RegistrationContext;
    OB_OPERATION_REGISTRATION *OperationRegistration;
} OB_CALLBACK_REGISTRATION;

typedef struct _OB_OPERATION_REGISTRATION {
    POBJECT_TYPE              *ObjectType;      // PsProcessType or PsThreadType
    OB_OPERATION              Operations;       // OB_OPERATION_HANDLE_CREATE | _DUPLICATE
    POB_PRE_OPERATION_CALLBACK  PreOperation;   // ← THIS is the stripping function
    POB_POST_OPERATION_CALLBACK PostOperation;
} OB_OPERATION_REGISTRATION;
```

The `PreOperation` callback receives `OB_PRE_OPERATION_INFORMATION` and modifies `DesiredAccess` to strip flags like `PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION`.

```
# WinDbg — find ObCallbacks for process objects
dt nt!_OBJECT_TYPE poi(nt!ObTypeIndexTable + 0x38)
# follow .CallbackList → linked list of OB_CALLBACK_REGISTRATION entries
```

### Process/Thread/Image Notification Callbacks

```
# WinDbg — dump the global callback arrays
# Process creation:
dps nt!PspCreateProcessNotifyRoutine L40

# Thread creation:
dps nt!PspCreateThreadNotifyRoutine L40

# Image (DLL/driver) load:
dps nt!PspLoadImageNotifyRoutine L40

# Each non-zero entry is a pointer (with low bits as flags).
# Clear the low 4 bits and resolve:
ln (<entry_value> & ~0xF)
```

### Registry Callbacks

```c
// CmRegisterCallbackEx registers a callback for all registry operations.
// The callback receives REG_NOTIFY_CLASS (enum) + operation-specific data.
// AC uses this to detect: reading/writing cheat config keys, enumerating
// driver service keys for known cheat tools.
```

### Minifilter (File System)

```c
// FltRegisterFilter uses FLT_REGISTRATION → FLT_OPERATION_REGISTRATION[]
// Each entry specifies: MajorFunction (IRP_MJ_CREATE, IRP_MJ_WRITE, etc.),
//   PreOperation callback, PostOperation callback.
// AC uses this to: detect cheat files on disk, monitor log file access,
//   prevent deletion of AC components.
```

```
# WinDbg — list minifilter instances
!fltkd.filters              # all registered minifilters
!fltkd.filter <filter_addr> # detail on one filter — shows operation callbacks
```

### ETW Threat Intelligence

```c
// The ETW TI provider (Microsoft-Windows-Threat-Intelligence) captures:
//   NtReadVirtualMemory, NtWriteVirtualMemory, NtAllocateVirtualMemory,
//   NtProtectVirtualMemory, NtMapViewOfSection — cross-process.
// AC registers as a consumer of this provider via EtwRegister.
// The provider GUID: {F4E1897C-BB5D-5668-F1D8-040F4D8DD344}
```

**Why:** Each callback is a sensor. Missing one means you don't know the AC is watching that specific operation. A cheat that calls `NtOpenProcess` without knowing about `ObRegisterCallbacks` will silently get a crippled handle and not understand why reads fail.

---

## 4. Analyze Integrity Check Routines

**Integrity checks are loops that hash, compare, or time-measure. Find them by their structure, not their name — they're rarely labeled.**

### Code Section Hashing

Pattern: a loop that reads pages from the game's `.text` section and feeds them to a hash function. Look for:
- `MmCopyVirtualMemory` or `KeStackAttachProcess` + direct read — the driver reads the game's code pages
- A hash accumulator loop (XOR / rotate / add, or a call to `RtlComputeCrc32` / a custom SHA variant)
- A comparison against a stored expected hash — mismatch = detection

```
# In IDA/r2 — find code-hashing routines:
# Look for references to PE section headers (.text base + size)
# followed by a read loop with XOR/rotate/add operations.
# The stored "good" hash is often in the driver's .data section
# or received via IOCTL from the service.
```

### Timing Checks

Pattern: `RDTSC` (or `KeQueryPerformanceCounter`) called twice around a block, delta compared against a threshold. VM exits and single-stepping inflate the delta.

```asm
; Typical RDTSC anti-debug/anti-VM check
rdtsc                    ; read timestamp counter → EDX:EAX
mov esi, eax             ; save low 32 bits
; ... sensitive operation ...
rdtsc
sub eax, esi             ; delta = current - saved
cmp eax, 0x1000          ; threshold — if delta > 0x1000, VM/debugger suspected
ja  detected
```

### Hypervisor Detection

```asm
; CPUID leaf 1 — check VMX bit
mov eax, 1
cpuid
bt  ecx, 31              ; bit 31 = hypervisor present
jc  hypervisor_detected

; CPUID leaf 0x40000000 — hypervisor brand string
mov eax, 0x40000000
cpuid
; EBX:ECX:EDX = brand string: "VMwareVMware", "Microsoft Hv", "KVMKVMKVM", etc.
```

### Manual-Mapped Driver Detection

The AC walks kernel data structures to find drivers loaded outside the normal `IoLoadDriver` path:

- `PsLoadedModuleList` — official module list; manually mapped drivers aren't in it
- `MmUnloadedDrivers` — recently unloaded drivers; some mappers leave traces here
- `PiDDBCacheTable` — driver database cache; SCM-loaded drivers appear here even after unload
- `BigPoolTable` / `MmAllocateIndependentPages` — large kernel allocations that could be mapped driver images

```
# WinDbg — walk loaded module list
lm                                    # all loaded modules
!pool <addr> -t                       # check if an address is in a known pool allocation
dt nt!_KLDR_DATA_TABLE_ENTRY <addr>   # module list entry structure
```

**Why:** Integrity checks are the AC's runtime assertions. Each one is a specific, findable code pattern. Reversing them tells you exactly what invariants the AC enforces — and by exclusion, what it doesn't check.

---

## 5. Decode Obfuscation Layers

**AC drivers obfuscate to slow analysis. Identify the obfuscation type, then defeat it systematically — not by reading obfuscated instructions.**

### Import Obfuscation

Instead of importing `ObRegisterCallbacks` directly (which would appear in the import table), AC drivers resolve functions at runtime:

```c
// Common pattern — hash-based dynamic import
typedef NTSTATUS (*fn_ObRegisterCallbacks)(POB_CALLBACK_REGISTRATION, PVOID*);
fn_ObRegisterCallbacks pObRegister;

// In DriverEntry:
UNICODE_STRING name = RTL_CONSTANT_STRING(L"ObRegisterCallbacks");
pObRegister = (fn_ObRegisterCallbacks)MmGetSystemRoutineAddress(&name);
// Or: hash-based resolution — hash each export in ntoskrnl and compare
```

**Finding dynamically resolved imports:**
```
# radare2 — find MmGetSystemRoutineAddress calls
axt @ sym.imp.MmGetSystemRoutineAddress
# for each call site, the argument (rcx) points to a UNICODE_STRING
# with the function name being resolved
```

### Encrypted Strings

AC drivers encrypt configuration strings, device names, and error messages. Common schemes: XOR with a static key, RC4, AES-128 with a key derived from system state (build number, KUSER_SHARED_DATA timestamp).

**Strategy:** Find the decryption stub (called before each string use), extract the key, and apply it to all encrypted blobs. Or: hook the decryption function in WinDbg and log cleartext outputs.

### Control Flow Flattening

The compiler (or a post-processing tool like LLVM-obfuscator) replaces normal control flow with a state machine: a loop with a switch on a state variable. Each basic block sets the next state and jumps back to the switch.

**Strategy:** Trace the state transitions to recover the original control flow graph. Tools: D-810 (IDA plugin for deobfuscation), or manual state-machine tracing in the debugger.

### Virtualized Code (Themida / VMProtect)

Critical sections may be virtualized — converted to bytecode for a custom VM interpreter embedded in the driver. The VM dispatcher is a loop that fetches, decodes, and executes bytecodes.

**Strategy:** Identify the VM dispatcher (large switch or computed-goto loop), then either:
- Trace the bytecode execution in WinDbg and log the effective operations
- Use devirtualization tools (VMHunt, NoVmp for VMProtect) if available
- Focus on inputs/outputs of the virtualized block rather than reversing the VM itself

**Why:** Obfuscation is meant to waste your time. Identify the *type* of obfuscation, apply the standard counter for that type, and move on. Don't read obfuscated code instruction by instruction — that's what the obfuscation wants you to do.

---

## 6. Reconstruct Driver Communication Structures

**Beyond IOCTLs, drivers use shared memory, events, and direct kernel object manipulation to communicate. Find the shared region and map its layout.**

### Shared Memory

The driver creates a section object and maps it into both kernel and user-mode address space:

```c
// Kernel side (in DriverEntry or IOCTL handler):
ZwCreateSection(&hSection, SECTION_ALL_ACCESS, &oa, &maxSize,
                PAGE_READWRITE, SEC_COMMIT, NULL);
ZwMapViewOfSection(hSection, ZwCurrentProcess(), &kernelAddr, ...);

// User-mode side (in the service):
// The service opens the section by name or receives a handle via IOCTL,
// then calls NtMapViewOfSection to map the same pages.
```

**Finding shared memory in the driver:**
```
# Look for section-creation APIs:
axt @ sym.imp.ZwCreateSection
axt @ sym.imp.MmMapLockedPagesSpecifyCache
axt @ sym.imp.MmAllocateContiguousMemory

# The buffer structure is defined by the driver — you must reverse it from
# how both sides read/write the mapped region.
```

### Kernel Events

```c
// Named event for signaling:
IoCreateNotificationEvent(&eventName, &eventHandle);
// Driver sets: KeSetEvent(event, 0, FALSE);
// Service waits: WaitForSingleObject(eventHandle, INFINITE);
```

### Direct Process Memory

Some ACs write scan results directly into the game process memory (via `KeStackAttachProcess` + `RtlCopyMemory`) to avoid IOCTL round-trips.

**Why:** Not all driver communication goes through IOCTLs. Missing the shared memory region means missing an entire communication channel — heartbeat data, scan results, or configuration that never touches the IOCTL handler.

---

## Summary

| # | Pattern | One-liner |
|---|---------|-----------|
| 1 | Driver model | WDM vs KMDF determines where the dispatch table lives |
| 2 | IOCTL dispatch | Extract codes, decode `CTL_CODE`, reverse buffer structures |
| 3 | Kernel callbacks | Every registration is a detection vector — find them all |
| 4 | Integrity checks | Hash loops, RDTSC pairs, CPUID checks, module walks — find by structure |
| 5 | Obfuscation | Identify the type (import/string/CFG/VM), apply the standard counter |
| 6 | Communication | Shared memory, events, direct writes — not everything is an IOCTL |
