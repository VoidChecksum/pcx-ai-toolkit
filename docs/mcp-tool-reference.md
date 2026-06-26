# Knowledge MCP tool reference

`pcx-knowledge-mcp` exposes the toolkit corpus and validators to MCP clients. Outputs are structured objects/lists by default; set `PCX_MCP_JSON_STRINGS=1` only for legacy clients that require JSON strings.

| Tool | Return shape | Use when |
|---|---|---|
| `search(query, limit=10)` / `search_docs(...)` | `schemas/search-docs.schema.json` | Find docs, skills, templates, tools, or knowledge files. |
| `hybrid_search(query, limit=10)` | search result list | Use vector cache when present, otherwise FTS/keyword. |
| `get_file(path)` | text | Fetch an exact repo-relative file. |
| `list_files(category="")` | object | Enumerate corpus files. |
| `overview()` | text | First-call repository map. |
| `list_skills()` / `get_skill(name)` | list/text | Load bundled agent skills. |
| `recommend_context(task, language="")` | `schemas/recommend-context.schema.json` | Get the smallest docs/skills/tools load plan. |
| `api_lookup(symbol, language="enma")` | `schemas/api-lookup.schema.json` | Verify exact Perception API signatures. |
| `validate_code(code, language, ...)` | `schemas/validate-code.schema.json` | Check Enma snippets for hallucinated APIs/imports. |
| `validate_answer(answer, source_path)` | validate-code-like object | Validate fenced code in an LLM answer. |
| `why_invalid(code, language)` | validate-code-like object | Get validation findings for repair. |
| `explain_finding(finding_json, language)` | `schemas/explain-finding.schema.json` | Turn one finding into a concrete fix. |
| `suggest_imports(code, language)` | object | Collect missing `import "...";` fixes. |
| `list_project_templates(language)` | list | See scaffold choices. |
| `generate_script_plan(...)` | `schemas/generate-script-plan.schema.json` | Produce a grounded project/script plan. |
| `scaffold_project(..., dry_run=true)` | `schemas/scaffold-plan.schema.json` | Preview/write project scaffolds. Real writes require `PCX_MCP_ALLOW_WRITES=1`. |
| `validate_project(path, ...)` | object | Run project verifier via CLI. |
| `offset_drift_report(old_json, new_json)` | object | Compare named offset snapshots. |

## Safe call order

```text
recommend_context(task, "enma")
get_skill(...) / get_file(...)
api_lookup(symbol, "enma")
validate_code(code, "enma") or validate_answer(markdown)
```

## Write safety

`scaffold_project` dry-runs by default. Start the MCP server with `PCX_MCP_ALLOW_WRITES=1` only for an explicitly authorized workspace, and prefer a repo-local `output_dir`.
