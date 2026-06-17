> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/zydis-api.md).

# Zydis API

All Zydis natives are auto-registered into every loaded script.

Two handle types:

* `zydis_req_t` — single-instruction encoder request (mnemonic + operands).
* `zydis_builder_t` — sequence of requests + raw byte chunks; encodes to a flat byte buffer with absolute addressing.

Constants are exposed as enums (`zydis_machine_mode::long_64` etc.) so no header import is needed.

## `zydis_req_t`

```cpp
zydis_req_t r;                                          // factory: defaults to MODE_LONG_64
r.set_mnemonic(int64 mnemonic);                         // ZydisMnemonic value (use zydis_mnemonic_from_string)
r.set_machine_mode(zydis_machine_mode mode);
r.set_operand_count(int64 count);                       // 0..4
r.set_branch_type (zydis_branch_type type);
r.set_branch_width(zydis_branch_width width);

r.set_operand_reg(int64 idx, int64 reg);                                              // ZydisRegister value
r.set_operand_imm(int64 idx, int64 imm);
r.set_operand_mem(int64 idx, int64 base, int64 idx_reg, int64 scale, int64 disp, int64 size);
r.set_operand_ptr(int64 idx, int64 segment, int64 offset);

int64              r.get_mnemonic();
zydis_machine_mode r.get_machine_mode();
int64              r.get_operand_count();
```

## Encoding

```cpp
array<uint8> zydis_encode         (zydis_req_t req);                       // empty array on failure
array<uint8> zydis_encode_absolute(zydis_req_t req, int64 runtime_rip);    // bakes RIP-relative immediates
array<uint8> zydis_nop_fill       (int64 length);                          // minimal NOP padding
zydis_req_t  zydis_decoded_to_request(array<uint8> bytes, int64 runtime_rip);
```

`zydis_decoded_to_request` decodes the bytes and returns a fresh request you can mutate and re-encode (useful for instruction patching).

## Mnemonic / register name lookup

```cpp
int64  zydis_mnemonic_from_string(string name);    // case-insensitive; 0 (INVALID) if no match
string zydis_mnemonic_to_string  (int64 mnemonic);

int64  zydis_register_from_string(string name);    // case-insensitive; 0 (NONE) if no match
string zydis_register_to_string  (int64 reg);
```

## Disassembly (textual)

```cpp
array<string> zydis_disasm(array<uint8> bytes, int64 runtime_rip);
```

One element per decoded instruction, formatted as Zydis's intel syntax (e.g. `"mov rax, 0x1234"`). Decoding stops at the first invalid byte.

For per-operand structure, decode + convert to a `zydis_req_t` via `zydis_decoded_to_request` and read the request fields.

## `zydis_builder_t`

Builds a sequence of instructions (and raw bytes) into one flat output buffer. Tracks a base address so RIP-relative encoding produces correct offsets.

```cpp
zydis_builder_t b;
b.set_machine_mode(zydis_machine_mode mode);
b.set_base_address(int64 addr);
b.clear();

b.push        (zydis_req_t req);
b.push_bytes  (array<uint8> bytes);
b.push_byte   (uint8 b);
b.push_u16    (uint16 v);    // little-endian
b.push_u32    (uint32 v);    // little-endian
b.push_u64    (uint64 v);    // little-endian
b.push_nop    (int64 count);
b.push_int3   ();
b.push_ret    ();

array<uint8> b.build();      // encode every entry in order
int64 b.get_count();         // number of entries
```

## Enums (no header needed)

```cpp
zydis_machine_mode::long_64 / long_compat_32 / long_compat_16 / legacy_32 / legacy_16 / real_16
zydis_branch_type::none / short / near / far
zydis_branch_width::none / w8 / w16 / w32 / w64
```

## Example: encode `mov rax, 0x42`, then disasm

```cpp
int64 mov_id = zydis_mnemonic_from_string("mov");
int64 rax_id = zydis_register_from_string("rax");

zydis_req_t r;
r.set_mnemonic(mov_id);
r.set_operand_count(2);
r.set_operand_reg(0, rax_id);
r.set_operand_imm(1, 0x42);

array<uint8> bytes  = zydis_encode(r);
array<string> texts = zydis_disasm(bytes, 0);

println(texts.get(0));    // "mov rax, 0x42"
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/zydis-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
