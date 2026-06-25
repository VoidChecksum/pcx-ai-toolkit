# pcx-ai-toolkit Roadmap

## Current Direction

The toolkit is Rust-only and Enma-only.

Completed cutovers:
- AngelScript removed from active support.
- Project-owned Python removed from runtime, package, test, and CI surfaces.
- `pcx-rs` is the single CLI and MCP entrypoint.

## Next Work

1. Publish platform-specific `pcx-rs` binaries for npm package installs.
2. Move remaining generated-asset maintenance into Rust where needed.
3. Expand Rust MCP mode with richer search/fetch helpers if real clients need them.
4. Submit Enma LSP packages to editor marketplaces.
5. Keep validators focused: source-backed API names, Enma semantics, and known hallucination traps.

## Non-Goals

- No Python compatibility wrappers.
- No AngelScript support.
- No speculative abstractions for unrequested package managers.
