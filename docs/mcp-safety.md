# MCP safety

Perception MCP is loopback-only, but agents can still call tools that read, write, allocate, or execute inside a target process. Treat the MCP surface as a privileged local automation API.

## Safe default tools

Read-only discovery is safe for normal planning:

- `system/info`
- `process/list`
- `process/info_by_pid`
- `process/info_by_name`
- `process/get_modules`
- `process/read_virtual_memory`
- `process/disassemble`
- `script/get_context`
- `script/validate`

## Dangerous tools

Require explicit authorization, a named target process, and a written plan before use:

- `process/write_virtual_memory`
- `process/write_typed_value`
- `process/write_string`
- `process/copy_memory`
- `process/fill_memory`
- `process/allocate_memory`
- `process/free_memory`
- `script/execute`

## Required write workflow

1. Confirm explicit authorization for the target.
2. Resolve a fresh handle with `process/reference_by_pid` or `process/reference_by_name`.
3. Read the original bytes/value first.
4. Apply the smallest write possible.
5. Read back and verify the expected value.
6. Release the handle with `process/dereference` or `process/cleanup_references`.

If any step is unclear, stop before calling a dangerous tool.

## Knowledge MCP file writes

`pcx-knowledge-mcp` keeps `scaffold_project` dry-run by default. Real writes require starting the server with `PCX_MCP_ALLOW_WRITES=1` so accidental agent calls cannot create files silently.
