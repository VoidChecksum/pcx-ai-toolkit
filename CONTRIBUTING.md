# Contributing to pcx-ai-toolkit

## What We Need

- **Documentation fixes** — typos, outdated API signatures, missing parameters
- **New knowledge files** — patterns, techniques, engine-specific guides
- **New signatures** — for games and engines beyond Source Engine
- **Template scripts** — well-structured starter scripts for common tasks
- **Tool integrations** — setup guides for AI tools beyond Claude Code and Cursor

## How to Contribute

1. Fork this repo
2. Clone with `--recursive` to pull LSP submodules
3. Make your changes
4. Test: run `./setup.sh` on a clean clone to verify nothing breaks
5. Open a pull request with a clear description of what changed and why

## Documentation Standards

- All docs are Markdown (`.md`)
- Code examples must use real API signatures from the official Perception.cx docs
- Enma code must follow the coding standards in `rules/CLAUDE.md`
- Every API function in a cheatsheet includes its return type and parameter types
- Working code examples must be complete (compilable with the right imports)

## File Organization

| Content | Where it goes |
|---------|---------------|
| Official API docs (downloaded from perception.cx / gitbook) | `docs/` |
| Quick references and cheatsheets | `knowledge/` |
| Working code examples and patterns | `knowledge/common-patterns.md` or `templates/` |
| Byte signature collections | `signatures/<engine>/` |
| AI tool setup guides | `mcp/` |
| Project rules and agent definitions | `rules/` |
| Claude Code / OMC skills | `.claude/skills/` |

## What NOT to Include

- Compiled binaries or executables
- API keys, tokens, or credentials
- Copyrighted game assets
- Offsets tied to a specific game version (these belong in your project, not the toolkit)

## Good First Issues & Tasks

If you are looking for somewhere to start, here are some recommended first contributions:

### 1. Document additional PCX APIs
Help expand documentation for less covered APIs. See `docs/` and look for any missing details or parameter explanations.

### 2. Add new working patterns
Add a recipe for common tasks (e.g., retrieving bones, configuring a customizable GUI color palette, or handling thread safety) in `knowledge/common-patterns.md`.

### 3. Add game signature templates
Create pattern signatures for a popular game engine (e.g., Unreal Engine 5 or Unity) under `signatures/`.

### 4. Improve LSP configuration guides
Help write or refine integration setups for other code editors (e.g., Emacs, Sublime Text, or Vim) in the `mcp/` folder.
