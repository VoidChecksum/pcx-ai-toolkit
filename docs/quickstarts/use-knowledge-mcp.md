# Use the knowledge MCP

The knowledge MCP gives agents lazy access to docs, templates, skills, and validators.

## Install

```bash
pip install -e mcp/pcx-knowledge-mcp/
pcx-knowledge-mcp --help
```

## Agent flow

1. Call `recommend_context(task, "enma")`.
2. Fetch listed docs with `get_file(path)`.
3. Verify API names with `api_lookup(symbol, "enma")`.
4. Validate code with `validate_code(code, "enma")`.
5. Validate final Markdown with `validate_answer(answer)`.

`scaffold_project` is dry-run by default. File writes are disabled unless the server process starts with `PCX_MCP_ALLOW_WRITES=1`.
