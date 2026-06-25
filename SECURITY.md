# Security Policy

This policy covers vulnerabilities in pcx-ai-toolkit's own code: Rust tools under `tools/pe-parser/`, shell/PowerShell setup scripts, npm launcher metadata, LSP wiring, and docs/knowledge assets.

It does not cover end-user Enma scripts, Perception.cx itself, or third-party reverse-engineering tools referenced by the documentation.

## Reporting a Vulnerability

Open a private security advisory or contact the maintainer with:

- Affected file paths.
- Minimal reproduction.
- Impact and preconditions.
- Suggested fix, if known.

Do not publish exploit details before maintainers have had a reasonable chance to patch.

## In Scope

- Rust CLI and native RE tools.
- `pcx-rs mcp` mode.
- Setup/update scripts.
- npm launcher/package metadata.
- LSP/editor integration wiring.

## Out of Scope

- Unauthorized testing of third-party targets.
- Perception.cx product vulnerabilities.
- Game anti-cheat bypass requests outside authorized research.
- User-created scripts built with the toolkit.
