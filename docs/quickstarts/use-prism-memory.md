# Use Prism memory with PCX

Prism is an optional memory layer for Claude Code and Cursor. Use it to remember PCX habits; keep PCX validators authoritative.

## Install Prism

```bash
git clone https://github.com/ProsusAI/prism.git
cd prism
./install.sh
```

Then initialize it in the project where you write Enma scripts:

```bash
cd ~/your-pcx-project
prism init
```

## Teach PCX rules

```bash
prism learn "Use pcx api before every Perception host API call"
prism learn "Run pcx verify before handing off Enma scripts"
prism learn "Use docs/llms-perception-enma.md as the primary Enma context pack"
```

## Agent workflow

```bash
pcx prism
pcx prompt --model claude
pcx api draw_text --json
pcx verify my_script.em
prism status
```

## Safety

Prism memories are hints, not proof. Do not capture credentials, private offsets, or unauthorized target details. If Prism and PCX disagree, trust `pcx api`, `pcx verify`, and the source-backed docs.
