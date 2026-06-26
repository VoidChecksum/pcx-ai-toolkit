# CLI reference

Use `pcx --help` for the live command list. This page gives agents a small routing map.

| Command | Use when |
|---|---|
| `pcx setup` | Install/sync LSP, skills, and PATH wiring. |
| `pcx update` | Self-update the toolkit. |
| `pcx lint <file.em>` | Run Enma script lint checks. |
| `pcx symbol-check <file.em>` | Validate symbols against the generated Perception API index. |
| `pcx lsp-check <file.em> [--json]` | Ask the bundled/configured Enma language server for diagnostics. |
| `pcx api <symbol> [--json]` | Look up exact source-backed API signatures. |
| `pcx check-answer <file.md>` | Validate fenced Enma snippets in generated Markdown. |
| `pcx create ...` | Generate or preview an Enma project scaffold. |
| `pcx verify <file.em>` | Run lint, symbol, and LSP checks for one script. |
| `pcx verify-project <dir>` | Run project-level validation and hygiene checks. |
| `pcx check-drift` | Compare local docs against upstream drift inputs. |
| `pcx check-mcp` | Validate Perception MCP config shape. |
| `pcx check-matrix` | Validate version/support matrix data. |
| `pcx counts` | Regenerate/check published corpus counts. |
| `pcx prompt` | Print the copy-paste anti-hallucination prompt. |
| `pcx agent-install --dry-run` | Show MCP/client install plan without writing. |
| `pcx ai-smoke` | Run small AI/tooling smoke checks. |
| `pcx doctor` | Diagnose install and packaging issues. |
| `pcx new` | Alias for project scaffolding. |

## Minimal validation loop

```bash
pcx api draw_text --json
pcx verify my_script.em
pcx check-answer answer.md
```

For runtime MCP tasks, call `pcx check-mcp` first and keep write operations gated by explicit user authorization.
