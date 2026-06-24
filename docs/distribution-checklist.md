# Distribution Checklist

Safe release/publishing path for pcx-ai-toolkit.

## Binary releases

Build `tools/pe-parser` in CI and upload `pcx-rs` plus native helpers from `tools/bin/`.

## MCP package

Publish `mcp/pcx-knowledge-mcp` as `pcx-knowledge-mcp`; smoke with `python3 mcp/pcx-knowledge-mcp/server.py --help`.

## Editor extensions

Build VS Code/Open VSX packages from `lsp/` after CI validates language-server compile.

## No credentials in repo

Publishing tokens belong in GitHub Actions secrets or local keychains, never committed files.
