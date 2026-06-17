> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/system-api-cpu-and-disassembly.md).

# System API (CPU & Disassembly)

Low-level CPU information, high-precision timing, and full multi-instruction x64 disassembly using **Zydis**.

***

## 📌 Overview

The System API provides:

* **CPU Information**
* **High-Resolution Performance Timers**
* **x64 Instruction Disassembly** using **Zydis**
* Full operand breakdown: registers, memory operands, immediates, pointer operands, etc.

All functions are **global** inside AngelScript.

***

## 📘 Available Functions

### 🔧 CPU Information

| Function              | Returns                                 | Description              |
| --------------------- | --------------------------------------- | ------------------------ |
| `string cpu_vendor()` | `"AuthenticAMD"`, `"GenuineIntel"`      | CPU vendor ID            |
| `string cpu_brand()`  | `"AMD Ryzen 9 7900X 12-Core Processor"` | Human-readable CPU model |

***

### ⏱ Timing

| Function                 | Returns                             | Description                         |
| ------------------------ | ----------------------------------- | ----------------------------------- |
| `uint64 rdtsc()`         | Raw CPU timestamp counter           | Fast but CPU-frequency dependent    |
| `int64 perf_time()`      | High-resolution performance counter | Use with `perf_frequency()`         |
| `int64 perf_frequency()` | Ticks per second                    | For converting perf\_time → seconds |

#### 📌 Example (timing a loop)

```cpp
int64 freq = perf_frequency();
int64 t0   = perf_time();

for (uint i = 0; i < 1000000; i++) { }

int64 t1 = perf_time();
double dt_sec = double(t1 - t0) / double(freq);

log("Elapsed seconds: " + dt_sec);
```

***

## 🧩 Zydis Disassembly API

### Functions

| Function                                                                                                 | Returns              | Description                   |
| -------------------------------------------------------------------------------------------------------- | -------------------- | ----------------------------- |
| `void zydis_disasm(const array<uint8>& in bytes, array<dictionary@>& out out_insts)`                     | `array<dictionary@>` | Full decode starting at RIP=0 |
| `void zydis_disasm(const array<uint8>& in bytes, uint64 runtime_rip, array<dictionary@>& out out_insts)` | `array<dictionary@>` | Full decode with custom RIP   |

Both return a **list of instructions**, where each item is a **dictionary** with metadata and operand array.

***

## 🧱 Instruction Structure (`disasm_instruction_t`)

Each instruction dictionary contains:

| Key                       | Type                 | Description                 |
| ------------------------- | -------------------- | --------------------------- |
| `"runtime_address"`       | `int64`              | Instruction RIP             |
| `"length"`                | `int64`              | Size in bytes               |
| `"mnemonic"`              | `string`             | `"mov"`, `"push"`, `"lea"`  |
| `"text"`                  | `string`             | Full Intel disassembly text |
| `"operand_count"`         | `int64`              | Total operands              |
| `"operand_count_visible"` | `int64`              | Non-hidden operands         |
| `"operands"`              | `array<dictionary@>` | List of operand tables      |

***

## 🔍 Operand Structure (`operand_t`)

Each operand dictionary contains:

| Key            | Type     | Example                               | Notes         |
| -------------- | -------- | ------------------------------------- | ------------- |
| `"id"`         | `int64`  | `0`                                   | Operand index |
| `"type"`       | `string` | `"reg"` / `"mem"` / `"imm"` / `"ptr"` | Operand type  |
| `"visibility"` | `string` | `"explicit"` / `"hidden"`             |               |
| `"size"`       | `int64`  | `64`                                  | Bit size      |

#### Register operand

| Key          | Type     | Description                |
| ------------ | -------- | -------------------------- |
| `"reg_name"` | `string` | `"rax"`, `"rcx"`, `"xmm0"` |

#### Memory operand

| Key                      | Type          | Description                 |
| ------------------------ | ------------- | --------------------------- |
| `"mem_segment"`          | `string`      | `"ss"`                      |
| `"mem_base"`             | `string`      | `"rbp"`                     |
| `"mem_index"`            | `string`      | `"rax"` or ""               |
| `"mem_scale"`            | `int64`       | Scale (1,2,4,8)             |
| `"mem_has_displacement"` | `int64` (0/1) | Whether displacement exists |
| `"mem_displacement"`     | `int64`       | Signed displacement         |

#### Immediate operand

| Key                      | Type          | Description              |
| ------------------------ | ------------- | ------------------------ |
| `"imm_is_signed"`        | `int64` (0/1) | Signed flag              |
| `"imm_is_relative"`      | `int64` (0/1) | Is relative jump?        |
| `"imm_value"`            | `int64`       | Immediate value          |
| `"imm_absolute_address"` | `int64`       | Computed RIP + relOffset |

#### Pointer operand

| Key             | Type    | Description |
| --------------- | ------- | ----------- |
| `"ptr_segment"` | `int64` |             |
| `"ptr_offset"`  | `int64` |             |

***

## 🚀 AngelScript Example

This example shows **CPU info**, **timing**, and full **multi-instruction disassembly** — the same script you used for validation.

```cpp
int main()
{
    log("=== AS SYSTEM / ZYDIS FULL TEST START ===");

    // CPU info
    log("CPU Vendor: " + cpu_vendor());
    log("CPU Brand : " + cpu_brand());

    // Timing test
    int64 freq = perf_frequency();
    int64 t0   = perf_time();

    uint64 sum = 0;
    for (uint i = 0; i < 1000000; i++) sum += i;

    int64 t1 = perf_time();
    log("perf_frequency (ticks/sec): " + freq);
    log("perf_time delta seconds   : " + double(t1 - t0) / double(freq));

    log("RDTSC: " + rdtsc());

    // Example code to disassemble
    array<uint8> bytes = {
        0x55,                    // push rbp
        0x48, 0x89, 0xE5,        // mov rbp, rsp
        0x48, 0x83, 0xEC, 0x30   // sub rsp, 0x30
    };

    array<dictionary@> ins;
    zydis_disasm(bytes, 0x140000000, ins);

    log("=== ZYDIS TEST (HARDCODED BYTES) ===");
    for (uint i = 0; i < ins.length(); i++)
    {
        dictionary@ inst = ins[i];

        int64 addr; 
        inst.get("runtime_address", addr);

        string text;
        inst.get("text", text);

        log(formatInt(addr, "0x%X") + ": " + text);
    }

    log("=== AS SYSTEM / ZYDIS FULL TEST END ===");
    return 1;
}
```

***

## 🔥 Example Output

```cpp
=== AS SYSTEM / ZYDIS FULL TEST START ===
CPU Vendor: AuthenticAMD
CPU Brand : AMD Ryzen 9 7900X 12-Core Processor

perf_frequency (ticks/sec): 10000000
perf_time delta seconds : 0.0094
RDTSC: 161134003150540

=== ZYDIS TEST (HARDCODED BYTES) ===
0x140000000: push rbp
0x140000001: mov rbp, rsp
0x140000004: sub rsp, 0x30

=== AS SYSTEM / ZYDIS FULL TEST END ===
```

***

## 📅 Date & Time API

Provides local date/time information, including readable names, 12-hour formatting, and Unix timestamps.

### 🧭 Functions

#### **`dictionary@ get_datetime()`**

Returns a dictionary with the following keys:

| Key            | Type   | Description                    |
| -------------- | ------ | ------------------------------ |
| `"year"`       | int    | e.g. 2025                      |
| `"month"`      | int    | 1–12                           |
| `"day"`        | int    | 1–31                           |
| `"hour"`       | int    | 0–23                           |
| `"minute"`     | int    | 0–59                           |
| `"second"`     | int    | 0–59                           |
| `"msec"`       | int    | 0–999                          |
| `"day_name"`   | string | `"Monday"`, `"Tuesday"`, ...   |
| `"month_name"` | string | `"January"`, `"February"`, ... |
| `"hour12"`     | int    | 1–12                           |
| `"ampm"`       | string | `"AM"` or `"PM"`               |

***

#### **`uint64 get_timestamp()`**

Returns a **Unix timestamp** in **UTC**, measured in seconds since `1970-01-01`.

***

## 🧪 Example: Getting Time & Date

```cpp
int main()
{
    dictionary@ dt = get_datetime();
    
    int year, month, day, hour12, minute;
    string dayName, monthName, ampm;
    
    dt.get("year", year);
    dt.get("month", month);
    dt.get("day", day);
    dt.get("hour12", hour12);
    dt.get("minute", minute);
    dt.get("day_name", dayName);
    dt.get("month_name", monthName);
    dt.get("ampm", ampm);
    
    log("Today is: " + dayName + ", " + monthName + " " + day + ", " + year);
    log("Local Time: " +
    hour12 +
    ":" +
    (minute < 10 ? "0" + formatInt(minute) : formatInt(minute)) +
    " " + ampm);
    
    uint64 ts = get_timestamp();
    log("Unix Timestamp: " + ts);
    return 1;
}

```

***

#### Thread Priority

* `bool set_thread_to_highest_priority()` — Set current thread to highest priority.
* `bool set_thread_to_lowest_priority()` — Set current thread to lowest priority.
* `bool set_thread_to_normal_priority()` — Set current thread to normal priority.

**What this is useful for:**\
Use these helpers when you have a **callback (os thread)** that must stay responsive (e.g., high-frequency polling, tight timing loops, heavy disassembly / scan batches, or avoiding stutter in critical update logic). You can temporarily raise priority during a burst of work, then restore **normal** afterward to avoid starving other threads and the UI.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/system-api-cpu-and-disassembly.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
