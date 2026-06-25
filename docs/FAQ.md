# FAQ

## What language does this toolkit support?

Enma (`.em`) only. AngelScript (`.as`) is deprecated and rejected by validators/scaffolding.

## What is required?

| Dependency | Use |
|---|---|
| Git | checkout and updates |
| Rust/Cargo | build `pcx-rs` and native tools |
| Node.js 18+ | build Enma LSP/editor packages |
| OS | Windows 10+, Linux, macOS |

## How do I install from source?

```bash
./setup.sh
pcx-rs doctor
```

On Windows PowerShell:

```powershell
.\setup.ps1
pcx-rs doctor
```

## How do I validate a script?

```bash
pcx-rs symbol-check script.em
pcx-rs verify-project . --allow-placeholders --allow-unverified
```

## How do AI tools get context?

Use `docs/llms.txt` for first-touch context and `pcx-rs mcp` for MCP-aware clients.
