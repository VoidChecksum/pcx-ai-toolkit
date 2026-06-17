> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/system-api-cpu-and-disassembly.md).

# System API (CPU & Disassembly)

The **System API** provides low-level functionality for CPU information, performance timing, and x64 instruction disassembly using **Zydis**.\
All functions listed here are available globally inside Lua scripts.

***

### 📌 **Available Functions**

#### **CPU Information**

| Function       | Returns  | Description                                             |
| -------------- | -------- | ------------------------------------------------------- |
| `cpu_vendor()` | `string` | CPU vendor (e.g. `"AuthenticAMD"` or `"GenuineIntel"`). |
| `cpu_brand()`  | `string` | Human-readable CPU model string.                        |

***

#### **Timing Functions**

| Function           | Returns  | Description                                                           |
| ------------------ | -------- | --------------------------------------------------------------------- |
| `rdtsc()`          | `uint64` | Raw timestamp counter from the CPU. Fast but CPU-frequency dependent. |
| `perf_time()`      | `int64`  | High-resolution performance counter ticks from Windows.               |
| `perf_frequency()` | `int64`  | Number of performance counter ticks per second.                       |

Useful for accurate microbenchmarking:

```
seconds = (perf_time_end - perf_time_start) / perf_frequency()
```

***

#### **Disassembly (Zydis)**

| Function                                   | Returns                         | Description                                                                    |
| ------------------------------------------ | ------------------------------- | ------------------------------------------------------------------------------ |
| `zydis_disasm(bytes_table, [runtime_rip])` | `table` (array of instructions) | Disassembles multiple x64 instructions and returns detailed structured output. |

***

## **Instruction Structure**

`zydis_disasm` returns an **array of `disasm_instruction_t`**.\
Each instruction contains:

```lua
{
    runtime_address       = 0x140000000,  -- uint64
    length                = 5,            -- bytes
    mnemonic              = "mov",        -- "push", "call", etc.
    text                  = "mov rbp, rsp",  -- full Intel syntax
    operand_count         = 3,            -- total (explicit + hidden)
    operand_count_visible = 2,            -- explicit operands only

    operands = { operand_t, operand_t, ... }
}
```

***

## **Operand Structure**

Each operand is an `operand_t` table with a consistent schema:

```lua
{
    id         = 0,
    visibility = "explicit", -- "explicit" | "implicit" | "hidden"
    type       = "reg",      -- "reg" | "mem" | "imm" | "ptr" | "unused"
    size       = 64,         -- bits

    -- Register operand
    reg = {
        name = "rbp"
    },

    -- Memory operand
    mem = {
        segment          = "ss",
        base             = "rsp",
        index            = nil,
        scale            = 1,
        has_displacement = true,
        displacement     = -0x20,
    },

    -- Immediate operand
    imm = {
        is_signed        = true,
        is_relative      = false,
        value            = 48,
        absolute_address = nil, -- if relative & resolvable
    },

    -- Pointer operand
    ptr = {
        segment = 0x1234,
        offset  = 0xABCDEF,
    }
}
```

***

## 🚀 Usage Examples

### **1. CPU Information**

```lua
function main()
    log("CPU Vendor: " .. cpu_vendor())
    log("CPU Brand : " .. cpu_brand())
end
```

***

### **2. High-Resolution Timing**

```lua
function main()
    local freq = perf_frequency()
    local t0 = perf_time()

    -- workload
    for i = 1, 1000000 do end

    local t1 = perf_time()

    local dt = (t1 - t0) / freq
    log("Elapsed seconds: " .. dt)
end
```

***

### **3. Disassemble Raw Bytes**

You can disassemble any byte array:

```lua
function main()
    local bytes = {
        0x55,                    -- push rbp
        0x48, 0x89, 0xE5,        -- mov rbp, rsp
        0x48, 0x83, 0xEC, 0x30   -- sub rsp, 0x30
    }

    local ins = zydis_disasm(bytes, 0x140000000)

    for i, inst in ipairs(ins) do
        log(string.format("0x%X: %s", inst.runtime_address, inst.text))
    end
end
```

***

### **4. Disassemble Memory From a Process**

Works perfectly with your `proc:rvm()`:

```lua
function main()
    local p = ref_process("notepad.exe")
    if not p then return end

    local base = p:base_address()
    local bytes = p:rvm(base, 32)

    local ins = zydis_disasm(bytes, base)

    for _, inst in ipairs(ins) do
        log(inst.runtime_address .. ": " .. inst.text)
    end

    deref_process(p)
end
```

***

## 🛠 Example Output

```asm
0x140000000: push rbp
  mnemonic = push, length = 1, operands = 1/3
    op1: id=0 type=reg vis=explicit size=64
      reg: rbp
    op2: id=1 type=reg vis=hidden size=64
      reg: rsp
    op3: id=2 type=mem vis=hidden size=64
      mem: seg=ss base=rsp index=nil scale=0 has_disp=false disp=nil

0x140000001: mov rbp, rsp
  mnemonic = mov, length = 3, operands = 2/2

0x140000004: sub rsp, 0x30
  mnemonic = sub, length = 4, operands = 2/3
```

***

## 📅 Date & Time API

#### **`get_datetime()`**

Returns a table describing the **local** date and time.

```lua
local dt = get_datetime()
-- dt = {
--     year        = 2025,
--     month       = 11,
--     day         = 27,
--     hour        = 14,        -- 24h clock
--     minute      = 5,
--     second      = 33,
--     msec        = 120,
--
--     day_name    = "Thursday",
--     month_name  = "November",
--
--     hour12      = 2,         -- 12h clock
--     ampm        = "PM"
-- }
```

#### **`get_timestamp()`**

Returns a **Unix timestamp** (UTC) — seconds since `1970-01-01`.

```lua
local ts = get_timestamp()
-- example: 1732734005
```

#### **Example**

```lua
function main()
    local dt = get_datetime()

    log(string.format(
        "Today is %s, %s %d, %d",
        dt.day_name, dt.month_name, dt.day, dt.year
    ))

    log(string.format(
        "Local Time: %d:%02d %s",
        dt.hour12, dt.minute, dt.ampm
    ))

    local ts = get_timestamp()
    log("Unix Timestamp: " .. ts)
end
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/system-api-cpu-and-disassembly.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
