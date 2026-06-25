# Perception MCP Error Recovery

| Code | Meaning | First recovery | Stop condition |
|---:|---|---|---|
| `-32001` | permission denied | surface missing permission and ask for explicit authorization | user does not grant permission |
| `-32002` | stale / cross-connection handle | reacquire handle once with `process/reference_by_name` or `_by_pid` | second failure after reacquire |
| `-32003` | target not found | call `process/list`, confirm name/PID, retry with exact image name | target absent |
| `-32004` | operation failed | shrink scope, validate params, check address/module bounds | repeated failure with validated params |

## -32001 permission denied

Likely cause: `write_memory`, `virtual_memory_operations`, or `kernel_rw_access` is disabled in Perception.

Recovery:
1. Do not retry blindly.
2. Report the exact missing permission.
3. If write/kernel/alloc is involved, ask for explicit authorization.
4. Prefer read-only verification when possible.

## -32002 stale / cross-connection handle

Likely cause: handle came from another MCP connection, the client disconnected, or the target exited.

Recovery:
1. `process/list_references`.
2. `process/reference_by_name` or `process/reference_by_pid` again.
3. Retry the failed call once with the new handle.
4. If it still fails, stop and report target state.

## -32003 target not found

Recovery:
1. `process/list`.
2. Match exact process image name or PID.
3. Retry `process/reference_by_name` / `_by_pid`.
4. If absent, stop; do not guess process names.

## -32004 operation failed

Recovery:
1. Check every address/handle is a hex string.
2. Check address validity with `process/is_valid_address`.
3. Bound scans to module sections.
4. Reduce `size`, `max_bytes`, or search scope.
5. Stop after one scoped retry.
