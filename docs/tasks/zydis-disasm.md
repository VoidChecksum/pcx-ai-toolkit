# Zydis Disassembly / Encoding

## Goal

Use documented Zydis helpers to encode, decode, and display instructions without inventing C++ bindings.

## Load

- `docs/perception/zydis-api.md`
- `docs/perception/mcp-workflows.md`

## Exact Enma imports

No import is required for Zydis API registration in Perception scripts.

## Exact symbols

`zydis_req_t`, `zydis_mnemonic_from_string`, `zydis_register_from_string`, `zydis_encode`, `zydis_disasm`, `zydis_nop_fill`.

## Permissions

Encoding/disassembly of byte arrays does not require memory write permission. Patching target memory with encoded bytes does require `write_memory` through MCP or host-gated write APIs.

## Enma example

```enma
int64 main() {
    uint8[] code;
    code.push(cast<uint8>(0x48));
    code.push(cast<uint8>(0xC7));
    code.push(cast<uint8>(0xC0));
    code.push(cast<uint8>(0x42));
    code.push(cast<uint8>(0x00));
    code.push(cast<uint8>(0x00));
    code.push(cast<uint8>(0x00));

    string[] asm = zydis_disasm(code, 0x140000000);
    if (asm.length() == 0) {
        println("decode failed");
        return 0;
    }
    for (string line : asm) println(line);
    return 1;
}
```

## Failure and sentinel checks

`zydis_encode` returns an empty array on failure. Name lookup returns invalid/none sentinels for unknown mnemonic/register names.

## Perception MCP equivalent

For live target bytes use `process/disassemble`. For source validation use `script/validate`. For patch workflows, generate bytes first, read old bytes, then write only with explicit authorization and rollback bytes.

## Validate

```bash
pcx check-answer docs/tasks/zydis-disasm.md
pcx verify <file.em>
```

## When to use Perception MCP instead of Enma

Use Enma for long-lived scripts, overlays, GUI, per-frame reads, and logic that runs inside Perception. Use Perception MCP for one-shot inspection, string/xref discovery, function bounds, signature generation, script validation from an agent, and stale-handle/error recovery.

## Common hallucinations

- Inventing helper APIs instead of checking `pcx api <symbol>`.
- Passing raw `x, y` or RGBA integers instead of `vec2(...)` and `color(...)`.
- Treating sentinel `0`, `false`, empty arrays, or empty strings as exceptions.
- Skipping permission notes for process, file, net, write, or kernel-gated work.

## Related skills

- `.claude/skills/mcp-tool-routing/SKILL.md`
- `.claude/skills/pcx-re-discipline/SKILL.md`
- `docs/AI_AGENT_OPERATING_MANUAL.md`

## Source links

- `docs/perception/mcp-api.md`
- `docs/perception/two-mcp-workflow.md`
- `knowledge/pcx-api-index.json`
