# MCP Transcript: Attach and Read

User: Read a u32 at `target.exe + 0x1234`.

Assistant:
1. I need a fresh handle for this MCP connection.
2. Call `process/reference_by_name` with `{ "name": "target.exe" }` → `$handle`.
3. Call `process/get_module_by_name` with `{ "handle": "$handle", "name": "target.exe" }` → `$module`.
4. Compute `$address = $module.base + 0x1234` as a hex string.
5. Call `process/is_valid_address`. If false, stop.
6. Call `process/read_typed_value` with `{ "type": "u32" }`.
7. Call `process/dereference` with `$handle`.
8. Report value with evidence ID and module offset.
