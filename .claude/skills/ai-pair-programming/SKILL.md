---
name: ai-pair-programming
description: >
  Techniques for driving AI coding tools (Claude Code, Cursor, Cline, Aider,
  Copilot) effectively on PCX projects. Covers context loading, prompt
  discipline, and steering the AI to read docs before writing API calls.
  Always active when working with an AI on a PCX scripting project.
license: MIT
---

# AI Pair Programming — Driving Claude / Cursor / Cline / Aider Well on PCX Projects

The other skills cover *what* to write; this one covers *how* to drive the AI to write it well. The user-recurring frustration with AI on PCX projects is uniform: "the AI keeps inventing API names" / "it gave me a script that doesn't compile" / "it skipped the discipline rules." The 32,000+ line supported documentation corpus, the 25 skills, and the rules drop-ins are not magic — they only work if you drive the AI to use them. This skill names the techniques that close the gap.

**Always active when working with an AI on a PCX scripting project.** These techniques apply across Claude Code, Cursor, Cline, Aider, GitHub Copilot, and any other AI coding tool that reads files and writes code.

**Prerequisite:** `rules/CLAUDE.md` / `rules/CURSOR.md` / `rules/CLINE.md` / `rules/COPILOT.md` for the per-tool drop-in; this skill is the workflow that wraps them and makes them stick.

## Source-Grounding Gate

Always force the model through the same gate: read
`docs/perception/llm-routing.md`, call MCP `recommend_context` when available,
verify symbols with `api_lookup` or `pcx api`, and validate the final snippet or
Markdown answer with `validate_code`, `validate_answer`, `pcx symbol-check`, or
`pcx check-answer`.

---

## Trigger

Starting a new PCX feature with AI assistance, asking the AI to implement something across multiple files, debugging "this script doesn't compile" / "the AI hallucinated a function name", code-reviewing AI output, deciding which tool to use for which task, frustrated with the rate at which the AI produces broken code.

---

## 1. Always Make the AI Read the Doc BEFORE Writing the Code

**The single best technique in this skill. One sentence changes the failure rate from ~40% (hallucinated APIs) to ~5%.**

The pattern is universal across tools: an AI asked to write code from prior knowledge will confidently produce code that looks right and doesn't compile, because Perception.cx's APIs aren't in any model's pretraining corpus. The fix is to put the read in the prompt:

```
WRONG  — "Write me an ESP overlay."
RESULT — Invented draw_esp(), used int for addresses, forgot null checks.
         Doesn't compile, wrong types.

RIGHT  — "Read docs/perception/render-api.md and docs/perception/proc-api.md,
         then write me an ESP overlay using the actual APIs you find there.
         Follow the 12 game-cheat-guidelines."
RESULT — Uses draw_rect + draw_text from the actual API, uint64 addresses,
         null checks after every ru64. Compiles. Runs.
```

The mechanism: the AI's context window now contains the *actual* API surface before any code generation happens. Hallucination drops because it's pattern-matching against documents in context, not against fuzzy pretraining recall.

The cost: 1-2 extra tool calls per task (file reads), maybe 5-30 seconds. The win: not having to fix every other line by hand.

When working iteratively (multi-turn): keep the same docs in context for the whole session. Reading them once and asking three follow-up questions is much cheaper than re-reading them three times.

**Why:** Every tool reaches for pretraining first if you let it. Pretraining for Perception.cx is empty. Front-load the doc read; the rest of the session pays for it many times over.

---

## 2. Use the Cheatsheet for Breadth, the Per-API Doc for Depth

**`knowledge/pcx-api-cheatsheet.md` (15 KB) is the right first read for "what's available?" Per-API docs are the second read for "how does this specific call work?" Loading the entire `docs/perception/` (multiple MB) wastes context for almost every task.**

A typical decision-tree for "what should the AI read?":

```
The task is...
  Discovery ("does PCX have a way to...?")
    → cheatsheet first, then the specific API doc the cheatsheet points to.

  Implementation ("write me a draw_text call")
    → docs/perception/render-api.md (the specific surface).

  Multi-API integration ("attach + scan + walk entity list")
    → docs/perception/proc-api.md (primary), plus brief skim of cheatsheet
      for cross-reference to the entity-iteration patterns.

  Debugging an API error
    → docs/perception/<area>-api.md for the API that errored, AND
      knowledge/common-patterns.md for any worked example using it.

  Cross-language work (Enma <-> AngelScript)
    → docs/perception/llm-routing.md and docs/CROSS_LANGUAGE.md first,
      then the per-language API doc.
```

The discipline is per-task, not per-session. A 30-minute session might read 4 different docs — that's fine. Re-loading the cheatsheet at the start of each tool session is also fine; it's small and grounds the AI's API surface.

**Why:** Context is the AI's working memory. Filling it with 32,000+ lines of documentation leaves no room for your code, your conversation, or its own reasoning. The cheatsheet was made for this — use it.

---

## 3. Plan Before Code, Especially for Multi-File Work

**Two-step workflow: (a) ask the AI to *plan* the change, (b) approve the plan, (c) implement. Skipping the plan step produces ~3x more rework on multi-file changes.**

A plan from the AI is a one-shot list of:
- Which files will change (paths + intent)
- Which sigs / offsets need to be resolved or added
- Which APIs each file will call
- Which routines (`on_update` / `on_render`) the work goes into
- What the end-state behavior is

This is cheap to produce, cheap to review, expensive to skip. Reviewing a 200-word plan and saying "yes but put the sig resolution in `main()` not in `on_update`" catches in 30 seconds what would otherwise be 10 minutes of edit-and-retry.

```
ASK:    "Plan the change to add a 'find closest enemy' feature.
         Don't write any code yet — just list the files, sigs, APIs,
         and routines you'd touch. Tell me what existing code you'd
         reuse and what's net-new."

REVIEW: [the plan]
        Push back: "The team check belongs in update, not render."
        "Use the existing entity_cache from globals.em instead of
        re-walking the list."

APPROVE: "Yes, implement that. Honor the 12 guidelines."

IMPLEMENT: [the AI writes code; you diff-review the result]
```

This works in Claude Code as `/plan` (or just asking), in Cline as the explicit Plan/Act mode, in Cursor as the Composer "Edit" mode preview, in Aider as `/architect`. Different surface, same workflow.

For single-file changes that are well-scoped, you can skip the plan step. The trigger to *not* skip: any change touching 3+ files, any change that adds a new sig, any change that touches `main.em`.

**Why:** Implementation is the expensive step. Plan-before-implement front-loads the cheap correction. Pure-implementation mode lets the AI dig itself into a hole across 5 files before you see the first diff.

---

## 4. Verify Offsets and Sigs with the MCP, Not by Asking the AI to Guess

**The AI does not have your binary loaded. When it confidently writes a sig, that sig is a hallucination unless it came from `mcp:find_pattern` or `mcp:generate_signature` on your actual binary.**

The wrong workflow:

```
ASK:    "Write me an ESP for game.exe v1.42.3."
RESULT: AI invents:
          const string SIG_ENTITY_LIST = "48 8B 0D ?? ?? ?? ?? 48 85 C9 74";
        That sig might be plausible-shaped but is not actually in your binary.
        Script runs, sig hits nothing, script does nothing, you debug for
        an hour wondering why.
```

The right workflow:

```
1. ASK the MCP (Perception IDE / Cursor with MCP / Cline with MCP):
   "Find a unique sig for the entity-list global in game.exe."
   The MCP runs find_pattern + generate_signature against the live binary.

2. CONFIRM the sig:
   tools/bin/sig-uniqueness-checker game.exe --sig "<the sig>"
   Verdict: UNIQUE margin=5. Ship it.

3. THEN ask the AI to write the script around the confirmed sig.
   Paste the sig in the prompt: "Use this sig: <sig>. Resolve as
   RIP-relative (disp@+3, insn_len=7). Read the resulting address as a
   uint64 pointer."
```

The discipline: **never let the AI generate sigs from prior knowledge**. Sigs are physical facts about a specific binary; they cannot be "guessed correctly." Same applies to specific RVAs, struct field offsets, and any other binary-specific number.

When using a tool without MCP (Copilot, Aider without an MCP setup): use the MCP-aware tool for discovery, paste the results into the non-MCP tool's session. Cross-tool handoff is fine; trying to make the non-MCP tool guess is not.

**Why:** Hallucinated sigs are silent failures. The script compiles, runs, draws nothing, and burns an hour of debugging that the 30-second MCP query would have prevented. Always.

---

## 5. Insist on the 12 Guidelines in the Prompt, Not Just in the Rules Drop-In

**Even with `rules/CLAUDE.md` (or CURSOR.md or CLINE.md or COPILOT.md) loaded, an AI mid-flow forgets. End every code-writing prompt with "honor the 12 guidelines." Cheap. Works.**

The rules drop-ins establish baseline behavior; the in-prompt reminder is the per-task checkpoint:

```
ASK:    "Add the smoothing slider. Honor the 12 guidelines — especially
         #11 (GUI for every tunable) and #8 (f suffix on float32 literals)."

RESULT: The slider is added as a section_slider_float with bounds, the
        smoothing value is float32 with proper f suffix in arithmetic,
        nothing hardcoded.
```

The framing works because the AI has the guidelines in its context (from the rules drop-in) and now has them at the top of its working attention (from the explicit mention). When the implementation produces a violation, your follow-up is short: "Rule 8 — the 0.5 in line 23 should be 0.5f."

You can also name specific rules to enforce more strictly. For RE-heavy work:

```
"Honor especially #1 (cite sigs with E-NNN), #5 (sigs over hardcodes),
 #12 (mark UNVERIFIED until you've checked the binary)."
```

For render-path work:

```
"Honor especially #4 (no reads in render), #7 (construct primitives per
 frame), #10 (W2S with w > 0.001 check)."
```

This is also where you bring in the other skills explicitly: "Follow `skill://pcx-perf-budget` for the timing discipline; budget render to 1.5 ms at 144 Hz."

**Why:** Without the in-prompt reminder, the AI honors guidelines for the first few lines and drifts. The mention is the per-task gravity well that keeps it on track for the whole completion.

---

## 6. Diff-Review Every Multi-File Change Before Applying

**This is where the AI's mistakes are catchable cheaply. Cursor, Cline, Aider, Claude Code with a permission gate — all show diffs. Read them.**

The high-value pattern matches to scan for in any AI-produced diff:

| Pattern | Rule violated | Fix |
|---|---|---|
| `int64 g_X` or `int32 g_X` near "addr" / "offset" / "base" / "ptr" | #2 | Change to `uint64` |
| Bare float literal (`8.0`, not `8.0f`) inside a `draw_*` call | #8 | Add `f` suffix |
| `ru64(...)` followed by code that uses the result without checking `!= 0` | #3 | Add null check |
| `color(...)` / `vec2(...)` / `vec3(...)` constructed at file scope (not inside a routine) | #7 | Move construction inside `on_render` |
| Hardcoded address (`0x12345678`) without a `// E-NNN` or `// UNVERIFIED` comment | #1, #12 | Add citation or marker |
| Hotkey hardcoded (`if (is_key_down(VK_F2))`) — no `section_keybind` widget | #11 | Add widget, bind to global |
| `find_code_pattern` call in `on_update` or `on_render` | (cost) | Move to `main()`, cache the result in a global |
| `read_memory` for 4-8 bytes where `read_typed_value` would do | (cost) | Use the typed variant |

A 5-minute diff review catches roughly 90% of guideline violations. The remaining 10% — subtle correctness bugs, off-by-one in struct offsets, wrong RIP arithmetic — are the ones worth a closer second pass.

Do not blanket-approve a multi-file change. Even when the AI gets it right, the review *also* serves as your own context-build: you're learning the change you're approving. Bypassing the review means you've shipped code you don't understand.

**Why:** The AI's review is its own output; your review is the independent check. Without it, you're shipping the AI's confidence. With it, you're shipping verified correctness. Five minutes is cheap.

---

## 7. When the AI Gets Stuck, Change the Question

**The AI loops on "this still doesn't work"; the right move is to re-frame to a more specific question that forces a different action.**

Common stuck-loop patterns:

| Stuck pattern | Re-framing |
|---|---|
| "the script crashes" → AI re-reads the same code | "What does the disassembly at `g_entity_list` look like? Use mcp:disassemble on the address we resolved." |
| "the sig doesn't match" → AI suggests a longer sig | "What's the actual byte sequence at the address we expected the sig to hit? Use mcp:read_memory to dump 32 bytes there." |
| "the field is wrong" → AI guesses different offsets | "Use mcp:struct_dump on three entity pointers and show me which offsets contain the values we expect for health (range 0-100) and team (small int)." |
| "the read returns 0" → AI suggests defensive null checks | "Walk the pointer chain step by step: print each intermediate pointer value. Where does the chain become 0?" |
| "the W2S draws at (0,0)" → AI suggests different matrix math | "Print the view matrix bytes; print the world position bytes. Are they non-zero and plausible? Check the matrix layout in `knowledge/aimbot-math.md`." |
| "the AI keeps suggesting the same fix that doesn't work" | "Stop. Tell me what you don't know yet. What's the next question we should answer?" |

The unstuck question is always more specific than "what's wrong." It names a tool call or a fact-finding step the AI can take next, instead of asking it to brainstorm fixes blindly.

This is the highest-skill move in AI pair programming — recognizing when "more of the same" won't work and stepping out to a different angle. It saves more time than any other single technique.

**Why:** Loops happen because the AI has the same information you do and can only re-shuffle it. Adding new information (a disassembly read, a struct dump, a memory peek) breaks the loop. The fastest path forward is rarely "try harder" — it's "look somewhere else."

---

## Per-Tool Quick Recipes

### Claude Code

- Use `/plan` or ask "plan the change" to trigger the plan-before-implement workflow.
- Skills auto-activate when their keywords appear (`patch day` → `pcx-patch-day-playbook`, `aimbot math` → `knowledge/aimbot-math.md` via skill keyword detection).
- Use `@file:docs/perception/render-api.md` (or whatever Claude Code's reference syntax is in your version) to force a specific doc into context.
- The `task` tool spawns subagents for parallel work; use the `cyber-repo-coverage-fanout` managed skill for multi-file PRs to this kind of repo.

### Cursor

- Use Composer mode for multi-file work; Chat mode for single-file or discussion.
- `@docs/perception/render-api.md` adds a file to the conversation context.
- `@codebase` for a project-wide grep; expensive context-wise but useful for "find every place that does X."
- The `.cursorrules` file (or `rules/CURSOR.md` copied to project root) applies project-wide.

### Cline

- Use Plan mode for any change touching 3+ files. The plan output is its own checkpoint.
- Auto-approve read-only MCP tools (`read_memory`, `find_pattern`, `disassemble`); keep write/execute tools gated.
- `@`-reference specific docs to keep them in context.
- Checkpoints before any `memory_write` or `execute_script` — the rollback path is your safety net.

### Aider

- `/read` adds a file to the always-in-context set; persists across the session.
- `/architect` mode for planning without code edits — the analog of Claude Code's `/plan`.
- `/commit` to commit Aider's changes; review the diff in `git log -p HEAD~1..HEAD` immediately after.
- `CONVENTIONS.md` (copy `rules/CLAUDE.md` content) is auto-loaded on every session.

### GitHub Copilot

- Inline completions for typing; Chat for explanation and review.
- `// from: docs/perception/render-api.md` comment above the cursor steers the next completion's API choice.
- Pair with an MCP-aware tool (the Perception IDE or Cursor with MCP) for binary discovery; bring resolved sigs back to Copilot for the typing-out.
- Accept 5-15 line completions, not 60-line ones.

---

## Summary

| # | Technique | One-liner |
|---|---|---|
| 1 | Read doc before writing code | "Read `docs/perception/X.md` then write…" — cuts hallucination from 40% → 5% |
| 2 | Cheatsheet for breadth, per-API for depth | `knowledge/pcx-api-cheatsheet.md` first, specific doc second |
| 3 | Plan before code on multi-file work | Two-step workflow; 30 seconds of plan review saves 10 minutes of rework |
| 4 | Verify sigs with MCP, not AI memory | Sigs are physical facts about your binary; AI cannot guess them |
| 5 | Honor the 12 guidelines per prompt | In-prompt mention beats rules-drop-in alone; cite specific rules per task |
| 6 | Diff-review every multi-file change | Five-minute scan for the 8 high-value pattern matches catches ~90% of violations |
| 7 | When stuck, change the question | Specific tool-call asks beat "try harder"; the unstuck question is more concrete |

**Cross-references:** `rules/CLAUDE.md`, `rules/CURSOR.md`, `rules/CLINE.md`, `rules/COPILOT.md` (the per-tool drop-ins this skill wraps); `skill://mcp-tool-routing` (which of the 59 Perception MCP tools for which task — the technique-4 backbone); `skill://game-cheat-guidelines` (the 12 rules technique #5 enforces); `skill://pcx-patch-day-playbook` (the workflow when the script breaks after a game update — applies techniques 4, 5, 7); `docs/CROSS_LANGUAGE.md` (Enma vs AngelScript binding split).
