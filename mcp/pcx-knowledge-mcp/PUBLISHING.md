# Publishing pcx-knowledge-mcp to PyPI

This guide covers how to build and publish the `pcx-knowledge-mcp` server package to PyPI, allowing developers to install it globally via `pip` or execute it on-the-fly using `uvx`.

---

## 1. Prerequisites

Ensure you have `build` and `twine` installed in your Python environment:

```bash
pip install --upgrade build twine
```

Or, if you use [uv](https://github.com/astral-sh/uv):

No prerequisites are needed, as `uv` manages build environments automatically.

---

## 2. Build the Package

Navigate to the package directory and build the source distribution and wheel:

### Using standard tools:
```bash
cd mcp/pcx-knowledge-mcp
python -m build
```

### Using uv:
```bash
cd mcp/pcx-knowledge-mcp
uv build
```

This will create a `dist/` directory containing the built artifacts:
- `pcx_knowledge_mcp-<version>.tar.gz` (Source distribution)
- `pcx_knowledge_mcp-<version>-py3-none-any.whl` (Built wheel)

---

## 3. Verify Build Integrity

Before uploading, check that the package description renders correctly and has no validation errors:

```bash
twine check dist/*
```

---

## 4. Upload to PyPI

### To TestPyPI (recommended first step):
Upload to TestPyPI to ensure the package structure looks correct on the web interface:

```bash
twine upload --repository testpypi dist/*
```

### To PyPI:
Upload the production release to PyPI:

```bash
twine upload dist/*
```

Enter your API token (username `__token__`) when prompted.

---

## 5. Usage After Publishing

Once published, users can add the server to their AI tools without cloning the toolkit repository:

### Run on-the-fly with uvx:
No installation required; Cursor or Claude Desktop can run the command directly:
```json
"pcx-knowledge": {
  "command": "uvx",
  "args": ["pcx-knowledge-mcp"]
}
```

### Install globally with pip:
```bash
pip install pcx-knowledge-mcp
```
Configure your client to spawn:
```json
"pcx-knowledge": {
  "command": "pcx-knowledge-mcp"
}
```
