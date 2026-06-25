> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt).

# Versioning and migration notes

_Last verified: 2026-06-25._

The Perception docs prove current symbol existence, but they do not always prove which historical build first introduced a symbol. Do not infer build compatibility from a current API page alone.

## Symbol version metadata

Machine-readable symbol metadata lives in [`../../knowledge/perception-symbol-versions.json`](../../knowledge/perception-symbol-versions.json). Narrative version history lives in [`../../knowledge/pcx-version-matrix.md`](../../knowledge/pcx-version-matrix.md). Unknown dates are explicit:

```json
{
  "symbol": "draw_polygon",
  "introduced": "unknown",
  "first_documented": "2026-02-01-or-earlier",
  "source": "docs/perception/render-api.md",
  "changelog_source": null
}
```

Use `introduced: "unknown"` when a symbol exists in docs but is not named in a changelog row.

## Enma language versioning

Enma is mirrored as a single unversioned language reference. The only dated language anchor in this toolkit is `Enma Open Beta — Phase 2 (May 2026)`, so exact introduction versions remain unknown for annotations, FFI, coroutines, `defer`, `match`, `goto`, exceptions, atomic types, preprocessor support, templates, pointer behavior, string behavior, and `.emb` serialization/linking.

Until upstream publishes an Enma language changelog or per-feature `Introduced in` metadata, generated code should target the current documented runtime or ask the user for their Perception build.

## Migration patterns

| Old / historical pattern | Current Enma pattern | Since / status |
|--------------------------|----------------------|----------------|
| Scan functions with `&out` params | Return `array<uint64>` directly | 2026-03-14 changelog family |
| AngelScript callback names | Enma `main()` plus routines/lifecycle | Enma beta |
| AngelScript handles / refs | Enma values plus encrypted `int64` handles | Enma beta |
| Old W2S helper assumptions | Row-major/transposed helpers where documented | See `knowledge/pcx-version-matrix.md` |

## Wrong-language warning

Perception history includes AngelScript-era examples and labels. These Enma pages are the source for Enma syntax. Do not copy AngelScript handle syntax, array syntax, callback syntax, or GUI patterns into Enma without checking the Enma-specific docs and API index.
