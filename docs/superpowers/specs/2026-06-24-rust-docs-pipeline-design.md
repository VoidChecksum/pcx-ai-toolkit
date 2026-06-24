# Rust Docs Pipeline Design

Goal: move the docs provenance and offline drift-check core into `pcx-rs` so release/CI validation depends less on Python scripts and live network behavior.

## Approved scope

Implement the Rust docs pipeline in two safe layers:

1. Native provenance generation/checking.
2. Native offline drift-check JSON/report plumbing that consumes the provenance map.

Python remains as compatibility shims where existing commands or workflows call `tools/build-provenance.py` and `tools/check-doc-drift.py`. The shims may delegate to `pcx-rs` when the binary is available, but existing CLI contracts must keep working.

## Architecture

Add a small Rust docs module under `tools/pe-parser/src/` rather than a new crate. It should own:

- scanning `docs/**/*.md` while excluding generated bundles and local-only files exactly as the Python provenance builder does;
- extracting upstream source URLs from GitBook blockquote metadata and AngelScript `<!-- Source: ... -->` comments;
- classifying sources as `gitbook`, `angelcode`, `local`, or `other`;
- producing deterministic `docs/PROVENANCE.json` data;
- selecting offline drift-check targets from provenance entries;
- normalizing local markdown the same way `tools/check-doc-drift.py` does before any future live comparison.

Keep this module boring: serde structs, filesystem walks, string parsing, and deterministic sorted output. No HTTP dependency in the first implementation slice.

## CLI behavior

Extend `pcx-rs` with native commands:

- `build-provenance [--check] [--json]`
- `check-drift [--json] [--limit N]`

`build-provenance --check` exits non-zero when generated provenance differs from the committed file. Without `--check`, it writes `docs/PROVENANCE.json`.

`check-drift` stays offline in this slice. It reports provenance health and target counts without fetching upstream pages. Live fetching remains a later `--live` enhancement because correct HTTPS support would add dependency weight and the current reliability problem is CI/live-network fragility.

## Data flow

```text
docs/**/*.md
  -> source URL extraction
  -> source classification
  -> deterministic provenance model
  -> docs/PROVENANCE.json
  -> offline drift target summary
```

Generated bundles such as `docs/llms*.txt`, local guidance files, and known removed upstream URLs remain excluded from drift failure semantics but preserved in provenance as local-only when appropriate.

## Error handling

- Missing repo root or unreadable docs directory: clear stderr error, exit `2`.
- `--check` mismatch: print regeneration command and exit `1`.
- Malformed individual docs: classify as local-only instead of crashing unless the committed Python behavior currently fails.
- Unknown command args: keep existing `pcx-rs` command-line behavior.

## Tests

Use TDD. Add failing tests before production code:

1. `pcx-rs build-provenance --check` passes against committed `docs/PROVENANCE.json`.
2. `pcx-rs build-provenance --json` returns deterministic count/source fields.
3. `pcx-rs check-drift --json --limit 1` emits offline summary with `mode: offline`, `snapshot: docs/PROVENANCE.json`, and parseable result rows.
4. Existing Python provenance and doc-drift tests keep passing.

Run focused Rust CLI tests first, then Python provenance/drift tests, then the project verification chain used in prior slices.

## Non-goals

- No live HTTPS fetch in this slice.
- No full `build-api-index` Rust parser port in this slice.
- No Streamable HTTP MCP transport.
- No unrelated README gap-table rewrites beyond reflecting the completed docs-pipeline slice.
