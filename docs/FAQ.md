# Frequently Asked Questions

A quick reference for common issues and questions when using pcx-ai-toolkit.

---

## Installation & Setup

### Why does `pcx setup` / `pcx update` fail?

**Symptoms:** `git: command not found`, submodule errors, or LSP build failure.

**Fixes:**
1. Ensure [Git](https://git-scm.com/) is installed and on PATH.
2. Ensure [Node.js 18+](https://nodejs.org/) is installed.
3. If you cloned without `--recursive`, run: `git submodule update --init --recursive`
4. Run `pcx doctor` to get a full diagnostic report.

### Why is the `pcx` command not found after setup?

The setup script adds `pcx` to your PATH. You need to **restart your terminal** after running setup.

If it still doesn't work:
- **Linux/macOS**: Check `~/.local/bin/pcx` exists and `~/.local/bin` is in your `$PATH`.
- **Windows**: Check that the toolkit's `tools/` directory was added to your system PATH in Environment Variables.

### What are the minimum requirements?

| Dependency | Minimum | Notes |
|------------|---------|-------|
| Git | Any recent | Required for clone + submodules |
| Node.js | 18+ | Required to build LSP servers |
| Python | 3.10+ | Required for CLI tools |
| OS | Windows 10+, Linux, macOS | All supported |

---

## Enma Scripting

### Why won't my Enma script compile?

Common compile errors and their fixes:

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot implicitly convert 'int64' to 'uint64'` | Using signed int for addresses | Use `uint64` for all addresses |
| `Float literal requires 'f' suffix` | Missing `f` on float literals | Change `0.2` to `0.2f` |
| `Type 'color' undefined` | Missing import | Add `import "color";` at top |
| `Type 'vec2' undefined` | Missing import | Add `import "vec";` at top |
| `Signed/unsigned mismatch` | Mixed sign arithmetic | Use `cast<uint64>(x)` |
| `Cannot implicitly convert 'float' to 'int'` | float-to-int assignment | Use `cast<int32>(f)` |
| `main() must return int32` | Wrong return type | Ensure `main()` returns `int32` |
| `'proc_t' is not declared` | Missing import | Add `import "proc";` at top |

### Why does my script crash silently?

Silent crashes are almost always null pointer dereferences. Every value returned by a memory read or `proc_read_*` can be zero.

**Debug approach:**
1. Validate every pointer in a chain before using it:
   ```enma
   uint64 base = proc_module_base(proc, "game.exe");
   if (base == 0) return;  // bail early
   uint64 ptr = proc_read_uint64(proc, base + offset);
   if (ptr == 0) return;
   ```
2. Use a debug overlay (see `skill://pcx-debug-overlay`) to display intermediate values on screen.
3. Add `print("checkpoint")` calls to narrow down where execution stops.

### How do I keep offsets up-to-date after a game patch?

Don't use hardcoded offsets. Use **pattern signatures** instead:

```enma
// Bad: hardcoded offset
uint64 entity_list = base + 0x1A2B3C;

// Good: pattern scan
array<uint8> sig = { 0x48, 0x8B, 0x05, 0x??, 0x??, 0x??, 0x?? };
uint64 entity_list = proc_find_pattern(proc, "game.exe", sig);
```

See `knowledge/offset-methodology.md` and the `pcx-patch-day-playbook` skill for the full patch-day workflow.

### What's the difference between Enma and AngelScript for PCX?

| | Enma | AngelScript |
|---|---|---|
| **Primary use** | Modern PCX scripting and new projects | Compatibility with existing `.as` scripts |
| **Type safety** | Strong static typing | Strong static typing |
| **Lifecycle** | `int64 main()` + `register_routine` | `int main()` + `register_callback` |
| **Process handle** | `proc_t` value with RAII cleanup | `proc_t@` handle with explicit `deref()` |
| **Render style** | `vec2(...)` and `color(...)` values | Raw/value shapes from the AS API pages |
| **File extension** | `.em` |
| **Skill** | `pcx-enma-discipline` |

For new scripts, use Enma. AngelScript is deprecated and unsupported.

---

## LSP & Editor Support

### Why is the LSP not providing completions?

1. **LSP servers aren't built**: Run `pcx setup` to compile them. Check with `pcx doctor`.
2. **Wrong server path**: Verify your editor settings point to the correct server files:
   - Enma: `lsp/enma-lsp/server/dist/server.js`
3. **Node.js not on PATH**: The servers require Node.js 18+. Run `node --version` to check.
4. **Extension not installed**: Install the VSIX from [Releases](https://github.com/VoidChecksum/pcx-ai-toolkit/releases).

See also: [docs/marketplace-install.md](marketplace-install.md) for full extension installation instructions.

### The LSP shows errors but my script compiles fine. Why?

The LSP uses static analysis which can be more conservative than the runtime compiler. Common false positives:
- Addon types (`color`, `vec2`) — ensure the LSP knows about your `import` statements
- PCX-specific builtins — the LSP includes PCX API stubs, but edge cases may exist

Report persistent false positives as GitHub issues with label `lsp`.

---

## MCP Integration

### Why are MCP tools not appearing in Claude/Cursor?

1. **MCP server not running**: The Perception MCP server must be running (it's part of the Perception.cx platform, not this toolkit).
2. **Wrong MCP config**: Check `mcp/perception-mcp-config.json` is correctly configured in your AI client.
3. **Port mismatch**: The default Perception MCP port is `42069`. Ensure nothing else is using it.
4. **Restart required**: Most AI clients require a restart after MCP config changes.

See `mcp/troubleshooting.md` for detailed diagnostics.

### Why does `pcx check-mcp` fail?

`pcx check-mcp` verifies that `mcp/perception-mcp-config.json` matches the documented API in `docs/perception/mcp-api.md`. If they're out of sync, update the config or the docs to match.

---

## Documentation

### How do I know which doc to read for a given API?

Start with:
- `docs/llms.txt` — the 45 KB structured index of all docs (designed for AI tools)
- `docs/enma/llms-language.md` — complete Enma language reference (single page, 2861 lines)
- `docs/perception/*.md` — all PCX Enma APIs
- `knowledge/enma-cheatsheet.md` — quick reference card

Or use the MCP server: the `pcx-knowledge-mcp` server supports `search <query>` to find relevant docs instantly.

### How do I report a documentation error?

Open a [GitHub Issue](https://github.com/VoidChecksum/pcx-ai-toolkit/issues) with the label `documentation`. Include:
- The file path of the incorrect documentation
- What the doc says vs. what it should say
- The Perception.cx version where you observed the discrepancy

---

## Still Stuck?

- Run `pcx doctor` for a full environment diagnostic
- Check [GitHub Discussions](https://github.com/VoidChecksum/pcx-ai-toolkit/discussions) for community help
- Open an [Issue](https://github.com/VoidChecksum/pcx-ai-toolkit/issues) for bugs
