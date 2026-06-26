# Create a project scaffold

```bash
pcx create --wizard
```

Non-interactive:

```bash
pcx create \
  --name "PCX Enma Script" \
  --language enma \
  --kind full \
  --target game.exe \
  --output ./pcx-enma-script
```

Then check it:

```bash
cd ./pcx-enma-script
pcx verify-project . --allow-placeholders --allow-unverified
```

Before shipping, replace placeholder offsets/signatures with evidence-backed values and run without `--allow-placeholders --allow-unverified`.
