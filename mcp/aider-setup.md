# Aider Setup — Perception.cx Toolkit Integration

[Aider](https://github.com/paul-gauthier/aider) is a CLI-first AI pair-programming
agent. It edits files in-place in your repo, commits every change to git for safety,
and auto-loads a `CONVENTIONS.md` from the project root as persistent instructions.
Aider has no MCP support yet — but this toolkit's docs and rules wire in cleanly via
Aider's read-file flags (`--read` / `/read`) and the conventions file. You point Aider
at `rules/CLAUDE.md` and the always-loaded PCX doc set, and it writes Enma the same way
a skill-equipped Claude Code session does.

## Why Aider Here

The niche Aider fills that the GUI tools don't:

- **Terminal-first.** No editor, no IDE. SSH into a box, `cd` into your script dir, work.
  Good fit for headless RE boxes and analysis VMs you provision yourself.
- **Model-agnostic.** Any OpenAI-compatible endpoint — GPT-4o, Claude, local models via
  an OpenAI-compatible proxy. You are not locked to one vendor's chat.
- **Git-aware.** Every accepted change is its own commit. A bad offset edit is one
  `git revert` away. This pairs naturally with guideline 3 (surgical changes) and the
  Karpathy "one feature, one diff" discipline in `rules/CLAUDE.md`.
- **`CONVENTIONS.md` is the 12 guidelines.** Aider reads it on every turn. Drop the
  toolkit rules there once and every edit inherits `uint64` addresses, `f`-suffixed
  floats, sigs-over-offsets, and update/render separation without re-prompting.

## Install

The official method is `pipx` (isolated install) or `pip`:

```bash
# Recommended — isolated environment
pipx install aider-chat

# Or into the current environment
python -m pip install -U aider-chat
```

See Aider's official install documentation for platform notes and model API-key setup.
Aider needs an API key for whatever model you pick (e.g. `OPENAI_API_KEY` /
`ANTHROPIC_API_KEY` in your environment).

## Wire Up the Toolkit

### 1. Conventions file

Aider auto-loads `CONVENTIONS.md` from the project root. The toolkit's rules drop-in
*is* your conventions file:

```bash
# Linux / macOS / WSL
cp rules/CLAUDE.md /path/to/your/pcx-project/CONVENTIONS.md
```

```powershell
# Windows
Copy-Item rules\CLAUDE.md C:\path\to\your\pcx-project\CONVENTIONS.md
```

Prefer a symlink if you want toolkit updates to flow through automatically:

```bash
ln -s /path/to/pcx-ai-toolkit/rules/CLAUDE.md /path/to/your/pcx-project/CONVENTIONS.md
```

Either way, `CONVENTIONS.md` now carries the coding standards, the project structure,
and the 12 guidelines (condensed) — Aider reads it before every edit.

### 2. `.aider.conf.yml`

Aider reads `.aider.conf.yml` from the project root. This pins your model, pre-loads the
always-needed reference docs read-only, and turns on git safety:

```yaml
# .aider.conf.yml — project root
# Model: any OpenAI-compatible endpoint. Pick one.
model: gpt-4o
# model: claude-3-5-sonnet-20241022
# model: openai/<your-local-proxy-model>

# Always-loaded reference set (read-only, never edited by Aider).
# Keep this tight — see Token Budget Tips below.
read:
  - docs/perception/render-api.md
  - docs/perception/proc-api.md
  - knowledge/pcx-api-cheatsheet.md
  - knowledge/common-patterns.md

# Git safety: commit each accepted change.
auto-commits: true

# Honor .gitignore when building the repo map.
gitignore: true
```

Paths in `read:` are relative to where you launch Aider. If your script project lives
outside the toolkit, use absolute paths or copy the doc set in.

### 3. Per-task docs (larger codebases)

Don't pre-load the whole `docs/` tree. For a specific task, pull the one API doc you
need interactively with the `/read` slash-command instead of widening
`.aider.conf.yml`:

```text
/read docs/perception/gui-api.md
/read docs/perception/input-api.md
```

`/read` adds files read-only for the current session — they inform edits but Aider never
rewrites them.

## Typical Workflow

Open Aider in your script directory, add the files it may edit, pull in the reference doc
for the task, then describe the feature:

```text
$ cd ~/projects/my-pcx-script
$ aider

# Add the files Aider is allowed to edit:
/add main.em offsets.em

# Pull in the pattern reference for this task (read-only):
/read knowledge/common-patterns.md

# Describe the change in plain language:
> Add a box ESP feature. Resolve the entity list with a pattern scan in
> offsets.em, validate every pointer, draw in a render routine only.

# Aider proposes a diff. Review it, then accept.
# With auto-commits on, the accepted edit is committed automatically.

# Inspect or roll back via git like any other commit:
/git log --oneline -3
/git revert HEAD        # undo the last Aider commit if the offset was wrong
```

Because `CONVENTIONS.md` is loaded, Aider applies the standards without being told:
addresses come out `uint64`, pointer chains get null-checks, the offset is resolved with
`find_code_pattern` rather than hardcoded, and the draw call lands in a render routine
separate from the memory reads.

## Working with PCX MCP Tools

Aider does not speak MCP. The Perception MCP server (`mcp/perception-mcp-config.json`)
and the binary-analysis MCP server are for MCP-aware clients. Two ways to combine them:

### Option A — split the work (recommended)

Use the right tool for each half and hand off through files:

- **Binary RE** → the Perception IDE's built-in AI chat, which *does* speak MCP. It reads
  process memory, disassembles, and runs pattern scans live, then writes the resolved
  sigs into `offsets.em`.
- **Script editing** → Aider. It reads the `offsets.em` the IDE produced and builds the
  feature on top of it.

The shared file (`offsets.em`) is the contract. The IDE owns the offsets; Aider owns the
feature logic. Each side commits its own changes to the same repo.

### Option B — one-shot CLI via `/run`

If you want binary facts inside an Aider session, lean on Aider's `/run`, which executes
a shell command and offers its output back into the chat context. The toolkit's
standalone analysis tools are pure-stdlib CLIs built for exactly this:

```text
/run python tools/identify-protector.py /path/to/target.exe
/run python tools/pe-section-analyzer.py /path/to/target.exe --json
```

Aider then sees the protector/section report and can reason about it while editing.

For live IDA-backed analysis, install a legitimately-licensed IDA yourself and wire up
the binary-analysis MCP server (see [`binary-analysis-setup.md`](binary-analysis-setup.md)).
Note that `idalib-mcp` is a **stdio MCP server**, not a one-shot CLI — it is meant for the MCP clients in Option A,
not for `/run`. For Aider, prefer the standalone Python tools above; keep `idalib-mcp` as
the handoff target for the IDE chat.

## Aider-Specific Notes

Things Aider gives you that the GUI tools don't:

- **`--show-diffs`** — print the diff for every change as it is applied. Pairs with
  guideline 3: you see exactly which lines moved before accepting.
- **`--no-auto-commits`** — if you prefer to stage and commit yourself, disable
  auto-commits and review with `git diff` between turns.
- **`/architect`** — planning mode. Aider proposes a high-level approach before touching
  code. Use it for a multi-feature script so the file layout matches the project
  structure in `CONVENTIONS.md` (one feature per file) before any edit lands.
- **`--map-tokens N`** — controls how much of the repo-map Aider keeps in context. Set
  this **high** for a toolkit-backed project — the conventions, offsets, and feature
  files all matter to a correct edit:

  ```bash
  aider --map-tokens 4096
  ```

- **`/lint`** — runs your configured linter after an edit and feeds errors back so Aider
  can fix them in the same turn. Wire it to the LSP-backed checks if you build the Enma
  language server from `lsp/`.

## Token Budget Tips

The toolkit ships ~35k lines of docs. Pre-loading all of `docs/` and `knowledge/` blows
the context budget on every turn and buries the relevant API in noise. Keep the loaded
set minimal:

- **Baseline:** load only `knowledge/pcx-api-cheatsheet.md` — the dense single-file
  reference — plus the one `docs/perception/<area>-api.md` the current task touches.
- **Trim `.aider.conf.yml`:** the four-file `read:` set above is a reasonable default for
  general work. For a render-only task, drop `proc-api.md`; for a memory-only task, drop
  `render-api.md`.
- **Pull more on demand:** use `/read docs/perception/<area>-api.md` when a task needs an
  API you haven't loaded, then `/drop` it when you move on.
- **Repo map, not full files:** `--map-tokens` lets Aider see the *shape* of the project
  cheaply without holding every file in full. Raise the map budget before raising the
  loaded-file count.

The cheatsheet plus one API doc covers the vast majority of script edits. Reach for the
full per-API docs only when the cheatsheet is too terse for the call you need.

## Reference

Back to the [Supported AI Tools](../README.md#supported-ai-tools) table in the README for
the other integrations (Claude Code, Cursor, Cline, Perception IDE).
