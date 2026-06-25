# Perception Forum Insights

Derived from a targeted authenticated read-only crawl of Perception forum pages
on 2026-06-23. Treat this file as secondary operational context, not as an API
contract. The official docs, generated API index, and local validators remain
authoritative for exact Enma and AngelScript symbols.

Do not copy forum text verbatim into generated answers. Use these notes to route
context, identify likely stale docs, and decide which official source to verify.

## Source Threads

| Topic | Forum Source |
|-------|--------------|
| Enma beta announcement | <https://perception.cx/threads/open-beta-perception-enma.1149/> |
| Overlay compatibility note | <https://perception.cx/threads/new-overlay-information-05-27-2026.1171/> |
| Official GitBook pointer | <https://perception.cx/threads/official-gitbook-documentation-perception-v2.712/> |
| Client common issues | <https://perception.cx/threads/perception-client-self-help-guide-for-common-issues.760/> |
| Changelog 2026-04-06 | <https://perception.cx/threads/changelog-%E2%80%93-04-6-2026.1059/> |
| Changelog 2026-04-01 | <https://perception.cx/threads/changelog-%E2%80%93-04-1-2026.1050/> |
| Changelog 2026-03-31 | <https://perception.cx/threads/changelog-%E2%80%93-03-31-2026.1044/> |
| Changelog 2026-03-30 | <https://perception.cx/threads/changelog-%E2%80%93-03-30-2026.1040/> |
| Changelog 2026-03-20 | <https://perception.cx/threads/changelog-3-20-2026.1009/> |
| Changelog 2026-03-17 | <https://perception.cx/threads/changelog-3-17-2026.1000/> |
| Changelog 2026-03-16 | <https://perception.cx/threads/changelog-3-16-2026.996/> |
| Changelog 2026-03-14 | <https://perception.cx/threads/changelog-3-14-2026.983/> |
| Changelog 2026-02-17 | <https://perception.cx/threads/changelog-2-17-2026.921/> |
| Changelog 2026-02-12 | <https://perception.cx/threads/changelog-2-12-2026.905/> |
| Changelog 2026-02-01 | <https://perception.cx/threads/changelog-2-1-2026.878/> |

## Enma Rollout Signals

- Enma is Perception's own script language and is positioned as the next major
  PCX development path. Load `docs/perception/readme.md`,
  `docs/perception/lifecycle-and-routines.md`, and the generated Enma context
  pack before answering Enma questions.
- The forum announcement points to both the Enma GitBook and the Perception Enma
  docs. If the forum and local mirror disagree, verify against
  `docs/perception/readme.md` plus the relevant `docs/perception/*.md` API page,
  or the live official docs before asserting behavior.
- The announcement describes Enma as native-compiled rather than interpreted.
  For LLM routing, prefer Enma-specific lifecycle, imports, value types, and
  compile-time semantics over AngelScript habits.
- The SDK was described as following after language maturity. Do not imply that
  every embedding SDK feature is available inside PCX scripts unless the local
  PCX docs or API index prove it.

## AngelScript And Universal API Changelog Signals

- 2026-03-16 and 2026-03-17 expanded AngelScript Custom Draw into a D3D11-style
  GPU pipeline: shaders, buffers, textures, render targets, indexed rendering,
  depth state, rasterizer state, viewports, structured buffers, compute shaders,
  mesh loading, dynamic textures, and backbuffer capture.
- 2026-03-14 added Sound API coverage for script use and corrected several
  memory-scan/VAD documentation mismatches. If a VAD or scan signature appears
- 2026-02-12 added AngelScript GUI position/size helpers and clarified render
  callback ordering. UI overlap or ordering answers should check the current
  Render and GUI docs before assuming older behavior.
- 2026-02-01 fixed an AngelScript `hash_map` reference issue and added window
  enumeration support across supported bindings. Prefer exact API lookup before
  using these names in examples.
- 2026-02-17 added list widget operations such as get/remove/highlight/show/hide
  in the older AS-era changelog. Use the current GUI docs for exact modern
  function and method names.

## IDE, Analyzer, And Agent Tooling Signals

- 2026-04-01 added and refined IDE agent tools including terminal execution,
  user-waiting, multiple-choice prompts, and note updates. MCP/agent answers
  should still prefer this repo's `pcx-knowledge-mcp` for deterministic source
  lookup and validation.
- 2026-03-30 and 2026-04-01 describe a redesigned IDE, GitHub Models/Copilot
  integration, and expanded analyzer/reconstruction features. These are product
  capabilities, not script APIs; do not call them from Enma or AngelScript code.
- 2026-03-31 and 2026-04-06 describe analyzer memory, reconstruction, decompiler,
  and freeze/deadlock fixes. When users ask about Analyzer behavior, route them
  to `docs/perception/analyzer.md` plus changelog context rather than inventing
  scripting APIs.
- The forum notes previous AI hallucination/context-trimming fixes inside the
  Perception IDE. This repo should keep its stricter answer gate:
  `api_lookup`, `validate_code`, and `validate_answer`.

## Overlay And Client Compatibility Signals

- The 2026-05-27 overlay note says the current overlay path depends on a normal
  Discord client process being present while its overlay components are disabled.
  Treat this as compatibility guidance, not as a script API.
- The 2026-03-20 changelog says fullscreen mode became broadly supported after
  engine and overlay changes, and that overlay refresh behavior may be expected
  during client startup.
- The client self-help guide stresses loading PCX from the desktop before games
  are opened, while scripts can be loaded and unloaded in-game. This belongs in
  troubleshooting context, not code examples.
- If a user asks about overlay crashes, stream/screenshot behavior, or startup
  order, route to this file and the official client docs before answering.

## LLM Routing Implications

- For Enma tasks: load `docs/perception/llm-routing.md`,
  `docs/llms-perception-enma.md`, `docs/perception/readme.md`, and the Enma skill.
- For forum/changelog/overlay/client questions: load this file after the
  official docs. Never let this file override exact symbol signatures.
- For all code-bearing answers: finish with `pcx check-answer` or MCP
  `validate_answer` to catch hallucinated or cross-language API usage.
