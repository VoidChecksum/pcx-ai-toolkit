> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt).

# SDK status and local development

_Last verified: 2026-06-25._

Perception's Enma SDK is not public yet. The public upstream Enma SDK docs are useful language-runtime background, but they do not define the supported Perception embedding contract.

## Current support matrix

| Question | Current answer |
|----------|----------------|
| Can users compile `.em` files outside Perception? | Not documented as supported for Perception. Use the Perception IDE/runtime workflow unless a release note says otherwise. |
| Can users produce `.emb` modules for Perception? | Not documented as supported. Treat `.emb` loading as upstream Enma SDK behavior, not a Perception compatibility promise. |
| Does Perception accept upstream Enma SDK output? | Unknown. No public binary-compatibility guarantee exists. |
| Is the upstream Enma SDK binary-compatible with Perception's embedded runtime? | Unknown. Do not assume ABI or serialization compatibility. |
| Is there a public Perception Enma CLI compiler? | Not documented. |
| Are scripts source-only today? | Public docs only support source-level Perception scripting. |
| Are there build flags, permissions, or packaging rules? | Permission gates are documented per API; no public SDK packaging rules are documented. |
| Expected future SDK plan | Not public in this docs mirror. Watch [Changelogs](changelogs.md). |

## Supported workflow today

1. Write source Enma in [Perception IDE](ide.md) or another editor.
2. Check API names against this docs mirror or the generated `llms.txt` index.
3. Validate snippets/projects with this toolkit before relying on generated code.
4. Load and run scripts through Perception's documented Enma script surface.

## What not to assume

* Do not assume upstream `.emb` output loads in Perception.
* Do not assume host-native functions registered through the upstream SDK exist in Perception.
* Do not assume private Perception host registration, build/link steps, headers, libraries, or package formats are stable.
* Do not ship tooling that depends on Perception SDK binary compatibility until Perception publishes that contract.

## Validation examples

If installed as a toolkit command:

```bash
pcx api draw_text
pcx verify-project ./my-script
```

If running from a repo checkout:

```bash
python3 tools/api-lookup.py draw_text
python3 tools/verify-project.py ./my-script
python3 tools/check-llm-answer.py answer.md
```

MCP:

```json
{
  "tool": "validate_code",
  "language": "enma",
  "code": "int64 main() { return 0; }"
}
```
