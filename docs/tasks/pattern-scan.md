# Pattern Scan

## Goal

Search a bounded module region for an evidence-backed byte signature, then disassemble the owning function before trusting it.

## Load

- `docs/perception/proc-api.md`
- `docs/perception/mcp-workflows.md`
- `knowledge/offset-methodology.md`

## Exact Enma imports

No addon import is required for Proc pattern scan APIs.

## API

`ref_process`, `proc_t.get_module_base`, `proc_t.get_module_size`, `proc_t.find_code_pattern`, `proc_t.find_all_code_patterns`.

## Permissions

Process read access is required. Kernel ranges require `kernel_rw_access`; keep scans inside a user-mode module unless explicitly authorized.

## Minimal code

```enma
// Requires process_memory_read permission.
int64 main() {
    proc_t p = ref_process("target.exe");
    if (!p.alive()) return 0;

    uint64 base = p.get_module_base("target.exe");
    uint64 size = p.get_module_size("target.exe");
    if (base == 0 || size == 0) return 0;

    uint64 hit = p.find_code_pattern(base, size, "48 8B ?? ?? ?? ?? ?? 48 85 C0"); // E-002 unique sig
    if (hit == 0) {
        println("pattern not found");
        return 0;
    }

    println("pattern hit=0x" + cast<string>(hit));
    return 1;
}
```

## Failure and sentinel checks

- Module base/size return `0` when missing.
- Pattern APIs return `0` or empty arrays when no match.
- A match is not evidence by itself; require uniqueness and a live-memory check.

## Perception MCP equivalent

1. `process/reference_by_name`.
2. `process/get_module_by_name`.
3. `process/find_all_patterns` over the module `.text` region.
4. `process/find_function_bounds` for each hit.
5. `process/disassemble`.
6. `process/generate_signature` after confirming the function.
7. `process/dereference`.

## Validate

```bash
pcx check-answer docs/tasks/pattern-scan.md
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
