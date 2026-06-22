# PCX Documentation Roots

The only authoritative sources for Perception.cx scripting APIs are these two
documentation trees on `docs.perception.cx`:

1. **Enma (Perception.cx Enma API)**  
   Canonical entry point: `https://docs.perception.cx/perception/enma/overview`  
   Markdown equivalent (when GitBook exposes it): `https://docs.perception.cx/perception/enma/readme.md`  
   Sub-pages follow the convention: `https://docs.perception.cx/perception/enma/<page>.md`

2. **AngelScript (Perception.cx AngelScript API)**  
   Canonical entry point: `https://docs.perception.cx/perception/angel-script/overview`  
   Markdown equivalent: `https://docs.perception.cx/perception/angel-script/overview.md`  
   Sub-pages follow the convention: `https://docs.perception.cx/perception/angel-script/<page>.md`

## What this means

- Every PCX API symbol used in generated code must be traceable to one of these
  two trees, or to the generated `knowledge/pcx-api-index.json` that is built
  from those trees.
- Do not use the local `docs/` copy as a primary authority; it is a drift-checked
  mirror. If a local doc and the live upstream disagree, the live upstream wins.
- The Enma *language* reference (grammar, types, addons) lives at
  `https://enma-1.gitbook.io/enma/` and is referenced for language semantics,
  but the PCX API surface itself comes only from the two roots above.

## Navigating the trees

GitBook exposes a structured index at `https://docs.perception.cx/perception/llms.txt`.
Use it to discover the exact sub-page paths under each root. In code, prefer
fetching the `.md` variant of any page so the model receives structured
markdown rather than rendered HTML.

## Generated index

`knowledge/pcx-api-index.json` is derived by scanning the local mirrors of the
pages under these two roots (plus the Enma addon docs that the Enma API
references). It exists so tools like `pcx symbol-check` and the
`mcp:pcx-knowledge` `validate_code` tool can catch invented API names without
performing a live fetch on every keystroke.
