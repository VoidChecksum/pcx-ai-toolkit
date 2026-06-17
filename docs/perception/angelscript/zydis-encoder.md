> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/zydis-encoder.md).

# Zydis Encoder

The **Zydis Encoder API** lets you **assemble instructions into raw machine code** at runtime. It’s designed for:

* Re-assembling disassembled code into **position-independent shellcode**
* Dynamically building/modifying shellcode for **Unicorn emulation**
* Inserting breakpoints (`int3`) or patching code on the fly

This encoder complements your Zydis disassembler by providing a structured way to **create `ZydisEncoderRequest` objects** and turn them into bytes.

***

### Concepts

#### Machine Mode

Most encoding depends on the active CPU mode:

* `MODE_LONG_64` (x86-64)
* `MODE_LONG_COMPAT_32`, `MODE_LONG_COMPAT_16`
* `MODE_LEGACY_32`, `MODE_LEGACY_16`
* `MODE_REAL_16`

Set the machine mode either:

* per-request (`ZydisEncoderRequest.set_machine_mode`)
* globally in a builder (`ZydisBuilder.set_machine_mode`)

***

### Enums

#### `ZYDIS_MACHINE_MODE`

* `MODE_LONG_64`
* `MODE_LONG_COMPAT_32`
* `MODE_LONG_COMPAT_16`
* `MODE_LEGACY_32`
* `MODE_LEGACY_16`
* `MODE_REAL_16`

#### `ZYDIS_BRANCH_TYPE`

Controls how a branch should be encoded.

* `BRANCH_NONE`
* `BRANCH_SHORT`
* `BRANCH_NEAR`
* `BRANCH_FAR`

#### `ZYDIS_BRANCH_WIDTH`

Controls displacement width for branch encoding.

* `WIDTH_NONE`
* `WIDTH_8`
* `WIDTH_16`
* `WIDTH_32`
* `WIDTH_64`

***

### Types

### `ZydisEncoderRequest` (value type)

A request describes a **single instruction** to be encoded.

#### Mnemonic & mode

* `void set_mnemonic(int mnemonic)`
* `int get_mnemonic()`
* `void set_machine_mode(int mode)`
* `int get_machine_mode()`

#### Operands

* `void set_operand_count(int count)`
* `int get_operand_count()`

#### Branch controls

* `void set_branch_type(int type)`
* `void set_branch_width(int width)`

#### Operand setters

* `void set_operand_reg(int index, int reg)`
* `void set_operand_imm(int index, int64 imm)`
* `void set_operand_mem(int index, int base, int idx, int scale, int64 disp, int size)`
* `void set_operand_ptr(int index, uint16 segment, uint32 offset)`

**Notes**

* Operand indexing is **0-based**.
* You must call `set_operand_count(n)` before setting operands.
* For memory operands, `base` and `idx` are register IDs (or `0` / none depending on your bindings), with:
  * `scale`: typically 1, 2, 4, 8
  * `disp`: signed displacement
  * `size`: operand size in bytes (e.g., `4` for dword, `8` for qword)

***

### `ZydisBuilder` (reference type)

A builder collects **instructions + raw bytes** and emits a single byte array.

#### Construction

* `ZydisBuilder@ ZydisBuilder()` — factory

#### Configuration

* `void set_machine_mode(int mode)`
* `void set_base_address(uint64 addr)`

#### Managing entries

* `void clear()`
* `void push(const ZydisEncoderRequest &in req)`
* `int get_instruction_count()`

#### Raw bytes helpers

* `void push_bytes(const array<uint8> &in bytes)`
* `void push_byte(uint8 b)`
* `void push_u16(uint16 value)` — little-endian
* `void push_u32(uint32 value)` — little-endian
* `void push_u64(uint64 value)` — little-endian

#### Convenience opcodes

* `void push_nop(int count = 1)`
* `void push_int3()`
* `void push_ret()`

#### Build output

* `bool build(array<uint8> &out bytes)`

**Notes**

* `set_base_address()` matters for **relative branches** and RIP-based calculations.
* `push_*` functions let you interleave **code and data** (useful for shellcode blobs).

***

### Global Functions

#### Encoding

* `bool zydis_encode(ZydisEncoderRequest &in req, array<uint8> &out bytes)`
* `bool zydis_encode_absolute(ZydisEncoderRequest &in req, uint64 runtime_address, array<uint8> &out bytes)`

Use `zydis_encode_absolute` when the instruction’s encoding depends on the actual runtime address (e.g., some branch forms / relative addressing decisions).

#### Utilities

* `bool zydis_nop_fill(array<uint8> &out bytes, uint32 length)`
* `bool zydis_decoded_to_request(const array<uint8> &in bytes, uint64 runtime_rip, ZydisEncoderRequest &out req)`

#### Mnemonic and register conversion

* `int zydis_mnemonic_from_string(const string &in name)`
* `string zydis_mnemonic_to_string(int mnemonic)`
* `int zydis_register_from_string(const string &in name)`
* `string zydis_register_to_string(int reg)`

***

## Full Test Example

```cpp
int main()
{
    test_basic_encoding();
    test_builder_api();
    test_raw_bytes();
    test_decode_to_request();
    test_nop_fill();
    test_memory_operands();
    test_branch_instructions();
    test_mixed_shellcode();
    log("All Zydis encoder tests completed!");
    return 0;
}

void test_basic_encoding()
{
    log("=== Testing basic instruction encoding ===");
    
    ZydisEncoderRequest req;
    req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    req.set_operand_count(2);
    req.set_operand_reg(0, zydis_register_from_string("rax"));
    req.set_operand_imm(1, 0x1234567890ABCDEF);
    
    array<uint8> bytes;
    if (zydis_encode(req, bytes))
    {
        log("mov rax, 0x1234567890ABCDEF encoded (" + bytes.length() + " bytes): " + bytes_to_hex(bytes));
        disasm_and_print(bytes, 0);
    }
    else
    {
        log_error("Failed to encode mov rax, imm64");
    }
    
    ZydisEncoderRequest req2;
    req2.set_mnemonic(zydis_mnemonic_from_string("xor"));
    req2.set_operand_count(2);
    req2.set_operand_reg(0, zydis_register_from_string("eax"));
    req2.set_operand_reg(1, zydis_register_from_string("eax"));
    
    array<uint8> bytes2;
    if (zydis_encode(req2, bytes2))
    {
        log("xor eax, eax encoded (" + bytes2.length() + " bytes): " + bytes_to_hex(bytes2));
        disasm_and_print(bytes2, 0);
    }
    else
    {
        log_error("Failed to encode xor eax, eax");
    }
    
    ZydisEncoderRequest req3;
    req3.set_mnemonic(zydis_mnemonic_from_string("inc"));
    req3.set_operand_count(1);
    req3.set_operand_reg(0, zydis_register_from_string("rcx"));
    
    array<uint8> bytes3;
    if (zydis_encode(req3, bytes3))
    {
        log("inc rcx encoded (" + bytes3.length() + " bytes): " + bytes_to_hex(bytes3));
        disasm_and_print(bytes3, 0);
    }
}

void test_builder_api()
{
    log("=== Testing ZydisBuilder API ===");
    
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140001000);
    builder.set_machine_mode(MODE_LONG_64);
    
    ZydisEncoderRequest mov_req;
    mov_req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    mov_req.set_operand_count(2);
    mov_req.set_operand_reg(0, zydis_register_from_string("rax"));
    mov_req.set_operand_imm(1, 0x42);
    builder.push(mov_req);
    
    ZydisEncoderRequest push_req;
    push_req.set_mnemonic(zydis_mnemonic_from_string("push"));
    push_req.set_operand_count(1);
    push_req.set_operand_reg(0, zydis_register_from_string("rax"));
    builder.push(push_req);
    
    ZydisEncoderRequest pop_req;
    pop_req.set_mnemonic(zydis_mnemonic_from_string("pop"));
    pop_req.set_operand_count(1);
    pop_req.set_operand_reg(0, zydis_register_from_string("rbx"));
    builder.push(pop_req);
    
    builder.push_nop(3);
    builder.push_int3();
    builder.push_ret();
    
    log("Instruction count: " + builder.get_instruction_count());
    
    array<uint8> shellcode;
    if (builder.build(shellcode))
    {
        log("Built shellcode (" + shellcode.length() + " bytes): " + bytes_to_hex(shellcode));
        disasm_and_print(shellcode, 0x140001000);
    }
    else
    {
        log_error("Failed to build shellcode");
    }
}

void test_raw_bytes()
{
    log("=== Testing raw bytes push ===");
    
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140002000);
    
    builder.push_byte(0xCC);
    
    builder.push_u16(0xBEEF);
    
    builder.push_u32(0xDEADBEEF);
    
    builder.push_u64(0xCAFEBABE12345678);
    
    array<uint8> raw_data = {0x90, 0x90, 0x48, 0x89, 0xC3};
    builder.push_bytes(raw_data);
    
    builder.push_ret();
    
    log("Entry count (mixed): " + builder.get_instruction_count());
    
    array<uint8> result;
    if (builder.build(result))
    {
        log("Mixed raw bytes result (" + result.length() + " bytes): " + bytes_to_hex(result));
        
        log("Breakdown:");
        log("  Byte 0 (CC): 0x" + format_hex_byte(result[0]));
        log("  U16 (BEEF): 0x" + format_hex_byte(result[1]) + format_hex_byte(result[2]));
        log("  U32 (DEADBEEF): 0x" + format_hex_byte(result[3]) + format_hex_byte(result[4]) + format_hex_byte(result[5]) + format_hex_byte(result[6]));
        log("  U64 starts at byte 7...");
    }
    else
    {
        log_error("Failed to build mixed raw bytes");
    }
}

void test_decode_to_request()
{
    log("=== Testing decode to request (re-encoding) ===");
    
    array<uint8> original = {0x48, 0x89, 0xC3};
    
    ZydisEncoderRequest req;
    if (zydis_decoded_to_request(original, 0x140001000, req))
    {
        log("Decoded mnemonic: " + zydis_mnemonic_to_string(req.get_mnemonic()));
        log("Operand count: " + req.get_operand_count());
        
        array<uint8> reencoded;
        if (zydis_encode(req, reencoded))
        {
            log("Original:   " + bytes_to_hex(original));
            log("Re-encoded: " + bytes_to_hex(reencoded));
            
            if (compare_arrays(original, reencoded))
            {
                log("SUCCESS: Re-encoding matches original!");
            }
            else
            {
                log("WARN: Re-encoding differs (may still be semantically equivalent)");
            }
        }
    }
    else
    {
        log_error("Failed to decode instruction");
    }
    
    array<uint8> lea_bytes = {0x48, 0x8D, 0x04, 0x8B};
    ZydisEncoderRequest lea_req;
    if (zydis_decoded_to_request(lea_bytes, 0, lea_req))
    {
        log("Decoded LEA mnemonic: " + zydis_mnemonic_to_string(lea_req.get_mnemonic()));
        array<uint8> lea_reenc;
        if (zydis_encode(lea_req, lea_reenc))
        {
            log("LEA original:   " + bytes_to_hex(lea_bytes));
            log("LEA re-encoded: " + bytes_to_hex(lea_reenc));
        }
    }
}

void test_nop_fill()
{
    log("=== Testing NOP fill ===");
    
    array<uint8> nops5;
    if (zydis_nop_fill(nops5, 5))
    {
        log("NOP sled (5 bytes): " + bytes_to_hex(nops5));
        disasm_and_print(nops5, 0);
    }
    
    array<uint8> nops15;
    if (zydis_nop_fill(nops15, 15))
    {
        log("NOP sled (15 bytes): " + bytes_to_hex(nops15));
        disasm_and_print(nops15, 0);
    }
    
    array<uint8> nops1;
    if (zydis_nop_fill(nops1, 1))
    {
        log("NOP sled (1 byte): " + bytes_to_hex(nops1));
    }
}

void test_memory_operands()
{
    log("=== Testing memory operands ===");
    
    ZydisEncoderRequest req;
    req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    req.set_operand_count(2);
    req.set_operand_reg(0, zydis_register_from_string("rax"));
    int rbx = zydis_register_from_string("rbx");
    int rcx = zydis_register_from_string("rcx");
    req.set_operand_mem(1, rbx, rcx, 8, 0x100, 8);
    
    array<uint8> bytes;
    if (zydis_encode(req, bytes))
    {
        log("mov rax, [rbx+rcx*8+0x100] (" + bytes.length() + " bytes): " + bytes_to_hex(bytes));
        disasm_and_print(bytes, 0);
    }
    
    ZydisEncoderRequest req2;
    req2.set_mnemonic(zydis_mnemonic_from_string("mov"));
    req2.set_operand_count(2);
    int rax = zydis_register_from_string("rax");
    int none = 0;
    req2.set_operand_mem(0, rax, none, 0, 0, 4);
    req2.set_operand_reg(1, zydis_register_from_string("edx"));
    
    array<uint8> bytes2;
    if (zydis_encode(req2, bytes2))
    {
        log("mov [rax], edx (" + bytes2.length() + " bytes): " + bytes_to_hex(bytes2));
        disasm_and_print(bytes2, 0);
    }
    
    ZydisEncoderRequest req3;
    req3.set_mnemonic(zydis_mnemonic_from_string("lea"));
    req3.set_operand_count(2);
    int rsp = zydis_register_from_string("rsp");
    req3.set_operand_reg(0, zydis_register_from_string("rax"));
    req3.set_operand_mem(1, rsp, none, 0, 0x20, 8);
    
    array<uint8> bytes3;
    if (zydis_encode(req3, bytes3))
    {
        log("lea rax, [rsp+0x20] (" + bytes3.length() + " bytes): " + bytes_to_hex(bytes3));
        disasm_and_print(bytes3, 0);
    }
}

void test_branch_instructions()
{
    log("=== Testing branch instructions ===");
    
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140001000);
    
    ZydisEncoderRequest jmp_req;
    jmp_req.set_mnemonic(zydis_mnemonic_from_string("jmp"));
    jmp_req.set_operand_count(1);
    jmp_req.set_operand_imm(0, 0x140001020);
    jmp_req.set_branch_type(BRANCH_NEAR);
    jmp_req.set_branch_width(WIDTH_32);
    builder.push(jmp_req);
    
    ZydisEncoderRequest call_req;
    call_req.set_mnemonic(zydis_mnemonic_from_string("call"));
    call_req.set_operand_count(1);
    call_req.set_operand_imm(0, 0x140002000);
    builder.push(call_req);
    
    ZydisEncoderRequest jz_req;
    jz_req.set_mnemonic(zydis_mnemonic_from_string("jz"));
    jz_req.set_operand_count(1);
    jz_req.set_operand_imm(0, 0x140001050);
    builder.push(jz_req);
    
    builder.push_ret();
    
    array<uint8> code;
    if (builder.build(code))
    {
        log("Branch code (" + code.length() + " bytes): " + bytes_to_hex(code));
        disasm_and_print(code, 0x140001000);
    }
}

void test_mixed_shellcode()
{
    log("=== Testing mixed shellcode (instructions + data) ===");
    
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140003000);
    
    ZydisEncoderRequest lea_req;
    lea_req.set_mnemonic(zydis_mnemonic_from_string("lea"));
    lea_req.set_operand_count(2);
    int rip = zydis_register_from_string("rip");
    int none = 0;
    lea_req.set_operand_reg(0, zydis_register_from_string("rcx"));
    lea_req.set_operand_mem(1, rip, none, 0, 0x20, 8);
    builder.push(lea_req);
    
    ZydisEncoderRequest mov_req;
    mov_req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    mov_req.set_operand_count(2);
    mov_req.set_operand_reg(0, zydis_register_from_string("rax"));
    mov_req.set_operand_imm(1, 0x0);
    builder.push(mov_req);
    
    builder.push_ret();
    
    builder.push_nop(5);
    
    builder.push_u64(0x6F6C6C6548);
    builder.push_byte(0x00);
    
    array<uint8> shellcode;
    if (builder.build(shellcode))
    {
        log("Mixed shellcode (" + shellcode.length() + " bytes): " + bytes_to_hex(shellcode));
        log("Disassembly of code portion:");
        disasm_and_print(shellcode, 0x140003000);
    }
}

string bytes_to_hex(const array<uint8> &in bytes)
{
    string result;
    for (uint i = 0; i < bytes.length(); i++)
    {
        if (i > 0) result += " ";
        result += format_hex_byte(bytes[i]);
    }
    return result;
}

string format_hex_byte(uint8 val)
{
    string chars = "0123456789ABCDEF";
    string hex;
    hex += chars[(val >> 4) & 0xF];
    hex += chars[val & 0xF];
    return hex;
}

bool compare_arrays(const array<uint8> &in a, const array<uint8> &in b)
{
    if (a.length() != b.length()) return false;
    for (uint i = 0; i < a.length(); i++)
    {
        if (a[i] != b[i]) return false;
    }
    return true;
}

void disasm_and_print(const array<uint8> &in bytes, uint64 rip)
{
    array<dictionary@> insts;
    zydis_disasm(bytes, rip, insts);
    for (uint i = 0; i < insts.length(); i++)
    {
        string text;
        insts[i].get("text", text);
        int64 addr;
        insts[i].get("runtime_address", addr);
        int64 len;
        insts[i].get("length", len);
        log("  0x" + formatInt(addr, "H") + " [" + len + "]: " + text);
    }
}
```

***

### Examples

### 1) Basic encoding

```cpp
void test_basic_encoding()
{
    ZydisEncoderRequest req;
    req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    req.set_operand_count(2);
    req.set_operand_reg(0, zydis_register_from_string("rax"));
    req.set_operand_imm(1, 0x1234567890ABCDEF);

    array<uint8> bytes;
    if (zydis_encode(req, bytes))
    {
        log("mov rax, imm64: " + bytes_to_hex(bytes));
        disasm_and_print(bytes, 0);
    }
    else
    {
        log_error("Failed to encode mov rax, imm64");
    }
}
```

***

### 2) Building shellcode with `ZydisBuilder`

```cpp
void test_builder_api()
{
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140001000);
    builder.set_machine_mode(MODE_LONG_64);

    ZydisEncoderRequest mov_req;
    mov_req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    mov_req.set_operand_count(2);
    mov_req.set_operand_reg(0, zydis_register_from_string("rax"));
    mov_req.set_operand_imm(1, 0x42);
    builder.push(mov_req);

    builder.push_nop(3);
    builder.push_int3();
    builder.push_ret();

    array<uint8> shellcode;
    if (builder.build(shellcode))
    {
        log("Shellcode: " + bytes_to_hex(shellcode));
        disasm_and_print(shellcode, 0x140001000);
    }
}
```

***

### 3) Mixing instructions + data

```cpp
void test_mixed_shellcode()
{
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140003000);
    builder.set_machine_mode(MODE_LONG_64);

    ZydisEncoderRequest lea_req;
    lea_req.set_mnemonic(zydis_mnemonic_from_string("lea"));
    lea_req.set_operand_count(2);
    lea_req.set_operand_reg(0, zydis_register_from_string("rcx"));
    lea_req.set_operand_mem(1, zydis_register_from_string("rip"), 0, 0, 0x20, 8);
    builder.push(lea_req);

    builder.push_ret();

    builder.push_nop(5);
    builder.push_u64(0x6F6C6C6548); // "Hello" (little endian-ish)
    builder.push_byte(0x00);

    array<uint8> blob;
    if (builder.build(blob))
    {
        log("Mixed blob: " + bytes_to_hex(blob));
        disasm_and_print(blob, 0x140003000);
    }
}
```

***

### 4) Decode → Request → Re-encode

```cpp
void test_decode_to_request()
{
    array<uint8> original = {0x48, 0x89, 0xC3}; // mov rbx, rax (example)

    ZydisEncoderRequest req;
    if (zydis_decoded_to_request(original, 0x140001000, req))
    {
        log("Decoded: " + zydis_mnemonic_to_string(req.get_mnemonic()));

        array<uint8> reencoded;
        if (zydis_encode(req, reencoded))
        {
            log("Original:   " + bytes_to_hex(original));
            log("Re-encoded: " + bytes_to_hex(reencoded));
        }
    }
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/zydis-encoder.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
