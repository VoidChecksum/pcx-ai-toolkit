# Process Read

## Goal

Attach to a target process, resolve a module base, validate an evidence-backed address, and read a typed value safely.

## Load

- `docs/perception/proc-api.md`
- `docs/perception/mcp-api.md`
- `knowledge/offset-methodology.md`

## Exact Enma imports

No addon import is required for `proc_t` / `ref_process`; Proc is registered by Perception.

## API

`ref_process`, `proc_t.alive`, `proc_t.get_module_base`, `proc_t.is_valid_address`, `proc_t.r32`.

## Permissions

Requires process memory read access in the host. Kernel fields require `kernel_rw_access`; this example does not use kernel fields. Failed reads return `0`, not exceptions.

## Minimal code

```enma
// Requires process_memory_read permission.
int64 main() {
    proc_t p = ref_process("target.exe");
    if (!p.alive()) {
        println("[proc] target not alive");
        return 0;
    }

    uint64 base = p.get_module_base("target.exe");
    if (base == 0) {
        println("[proc] module missing");
        return 0;
    }

    uint64 addr = base + 0x1234; // E-001 verified offset
    if (!p.is_valid_address(addr)) {
        println("[proc] invalid address");
        return 0;
    }

    int32 value = p.r32(addr);
    println("value=" + cast<string>(value));
    return 1;
}
```

## Failure and sentinel checks

- `ref_process` can return a non-alive `proc_t`; always call `.alive()`.
- `get_module_base` returns `0` when missing.
- Typed reads return `0` on failure, so validate the address first when `0` is a valid value.

## Perception MCP equivalent

1. `process/reference_by_name` with `{"name": "target.exe"}`.
2. `process/get_module_by_name` with handle + module name.
3. `process/is_valid_address` with handle + hex address.
4. `process/read_typed_value` with `type: "i32"`.
5. `process/dereference` to release the handle.

## Validate

```bash
pcx check-answer docs/tasks/proc-read.md
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
