---
name: pcx
description: Runs the PCX AI Toolkit CLI directly from Claude Code. Use this for `/pcx update` or any other pcx command.
license: MIT
---

# PCX CLI Skill

This skill allows the user to run `pcx` commands directly in the Claude Code harness via `/pcx <args>`.

When the user types `/pcx update` or `/pcx <command>`, you MUST execute it using the bash tool.
Do not guess the output, just run `pcx <args>` (or `./tools/pcx <args>` if local) via bash.

Example:
If user says `/pcx update`, you run:
<call:bash>
command: "pcx update"
</call:bash>

If `pcx` is not in PATH, fallback to `npm/bin/pcx.js update` or `python tools/pcx.py update`.