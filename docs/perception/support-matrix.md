# Perception Support Matrix

| Surface | Status | Docs | Validation | Examples | Known gaps | Last verified |
|---|---|---|---|---|---|---|
| Enma scripts | supported | `docs/perception/llm-routing.md` | `pcx verify` | templates, task docs | no full compiler in pcx | 2026-06-25 |
| Perception IDE | documented | `docs/perception/ide.md` | doc drift | IDE docs | runtime availability varies | 2026-06-25 |
| Perception Analyzer | documented | `docs/perception/analyzer.md` | doc drift | analyzer docs | limited local automation | 2026-06-25 |
| Perception runtime MCP | operational docs | `docs/perception/mcp-api.md` | MCP contract tests | schema/examples | live server needed for E2E | 2026-06-25 |
| pcx knowledge MCP | supported | `docs/perception/two-mcp-workflow.md` | unit tests | planner docs | static knowledge only | 2026-06-25 |
| CLI validators | supported | `docs/AI_AGENT_OPERATING_MANUAL.md` | pytest/docs-check | task docs | heuristic parser | 2026-06-25 |
| Templates | supported | `templates/` | project workflow tests | scaffold templates | not every task has template | 2026-06-25 |
| Skills | supported | `.claude/skills/` | skill contract checks | operational skills | agent runtime varies | 2026-06-25 |
| Weak-model workflow | supported | `docs/model-guides/weak-local-models.md` | prompt smoke | `pcx plan --weak-model` | conservative by design | 2026-06-25 |
| Task docs | supported | `docs/tasks/` | `pcx check-answer` | 9 task guides | not full app tutorials | 2026-06-25 |
