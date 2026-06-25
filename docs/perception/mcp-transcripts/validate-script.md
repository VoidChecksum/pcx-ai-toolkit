# MCP Transcript: Validate Script

User: Check this generated Enma script.

Assistant:
1. Use pcx knowledge MCP `validate_code` first for fast hallucination checks.
2. Call Perception MCP `script/get_context` once if the session has not loaded it.
3. Call `script/validate` with the full source.
4. If ok, say it compile-validates.
5. If errors exist, fix only the failing source lines and rerun both validators.
6. Do not use `script/execute` for GUI/thread/overlay code.
