# Validate generated Enma

Use this before copying AI-generated `.em` into Perception.

```bash
pcx api draw_text
pcx symbol-check my_script.em
pcx verify my_script.em
pcx check-answer answer.md
```

Expected result: commands exit `0`. If `symbol-check` reports `unknown_call`, verify the symbol with `pcx api <symbol>` or replace it with a documented API.

For projects:

```bash
pcx verify-project ./my-project
```

Only use `--allow-placeholders --allow-unverified` for scaffolds, never for shipped scripts.
