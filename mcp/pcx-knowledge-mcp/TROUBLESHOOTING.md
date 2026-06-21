# Troubleshooting pcx-knowledge-mcp

This guide covers common issues, diagnostics, and fixes when setting up or running the `pcx-knowledge-mcp` server.

---

## 1. Stdio Corruption (Most Common Issue)

**Symptoms:** The server starts but immediately disconnects, crashes, or the client reports `invalid JSON` / `JSON parse error`.

**Cause:** The Model Context Protocol (MCP) communicates over standard input/output (`stdin`/`stdout`). If the server script, any imported library, or the Python interpreter itself prints arbitrary text (e.g., debug logs, warnings, deprecation notices) to `stdout`, the client's JSON-RPC parser will corrupt and terminate the connection.

**Fixes:**
1. **Never use `print()` in server code** for debugging. Use standard Python `logging` configured to write to `stderr` or a file.
2. In `server.py`, ensure all logging is directed to `sys.stderr`:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO, stream=sys.stderr)
   ```
3. Run Python with the unbuffered flag `-u` to ensure stdout/stderr streams do not buffer and cause timing-based parse errors.
   - Example command: `python -u /path/to/server.py`

---

## 2. Command Not Found / PATH Issues

**Symptoms:** The MCP client logs show `spawn pcx-knowledge-mcp ENOENT` or `command not found`.

**Cause:** The executable package `pcx-knowledge-mcp` was installed, but your system's global environment does not have the python `Scripts/` (Windows) or `bin/` (Linux/macOS) directory on PATH.

**Fixes:**
- **Option A (Recommended):** Bypass PATH resolution by using absolute paths in your client config:
  ```json
  "pcx-knowledge": {
    "command": "python",
    "args": ["C:/Users/krist/pcx-ai-toolkit/mcp/pcx-knowledge-mcp/server.py"]
  }
  ```
- **Option B (Re-install):** Install the package in editable mode with your current Python user directory:
  ```bash
  pip install --user -e mcp/pcx-knowledge-mcp/
  ```
  Ensure the printed script location is added to your environment `PATH` variable.

---

## 3. Library Import Errors (e.g., `ModuleNotFoundError: No module named 'mcp'`)

**Symptoms:** The client fails to launch the server. If run manually, Python prints `ModuleNotFoundError: No module named 'mcp'`.

**Cause:** The `mcp` SDK is not installed in the Python environment being executed by the MCP client.

**Fixes:**
1. Ensure the package is installed:
   ```bash
   pip install mcp
   ```
2. If your client uses a custom Python executable or virtual environment, make sure to point the command to the correct Python interpreter:
   - **Virtual Env:** `/path/to/venv/bin/python`
   - **Windows Store Python:** `python.exe` vs `python3.exe`
3. Run `pcx doctor` to verify python dependencies are configured correctly.

---

## 4. Client-Specific Diagnostics

### Claude Desktop
- **Log Location (Windows):** `%APPDATA%\Claude\logs\mcp*.log`
- **Log Location (macOS):** `~/Library/Logs/Claude/mcp*.log`
- Open these logs to see the raw stdout/stderr output from the server startup.

### Cursor
- Open the Developer Tools via **Help -> Toggle Developer Tools**.
- Go to the **Console** tab and search for `mcp` to inspect error payloads and lifecycle logs.
- You can also check **Cursor Settings -> Features -> MCP** to see the status (Green/Red dot).

### Cline / VS Code
- Open the **Output** panel in VS Code.
- Select `Cline MCP` from the dropdown list on the right.
- This will show the stream of JSON-RPC requests/responses and error logs.

---

## 5. Manual Diagnostics Check

You can test if the server can run outside of the MCP client context by executing it manually:

```bash
# Run with python (use absolute path)
python C:/Users/krist/pcx-ai-toolkit/mcp/pcx-knowledge-mcp/server.py
```

If it starts successfully, it will wait for input on stdin (it won't exit immediately). Press `Ctrl+C` to terminate it. If it crashes with a traceback immediately, resolve the traceback before adding it back to your MCP config.
