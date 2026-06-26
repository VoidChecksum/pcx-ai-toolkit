# Run a live Perception MCP check

Use this when Perception is running and MCP is enabled.

1. In Perception, open **Settings → Perception MCP**.
2. Enable the server and copy the loopback URL, for example `http://127.0.0.1:42069/mcp`.
3. Add it to your MCP client:

```bash
claude mcp add --transport http perception http://127.0.0.1:42069/mcp
```

Safe first calls:

```text
system/info
process/list
script/get_context
script/validate
```

Avoid write/execute tools until you have explicit authorization and a written plan. Dangerous examples: `process/write_virtual_memory`, `process/write_typed_value`, `process/allocate_memory`, `script/execute`.
