"""Runtime path helpers for source checkouts and installed packages."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def tool_dir() -> Path:
    """Directory containing the Python CLI tools."""
    return Path(__file__).resolve().parents[1]


def source_root() -> Path:
    """Repository/package root when running from a checkout or npm package."""
    return tool_dir().parent


def _looks_like_data_root(path: Path) -> bool:
    return (path / "knowledge" / "pcx-api-index.json").exists() or (path / "templates").is_dir()


def data_root() -> Path:
    """Root containing toolkit data files.

    Source/npm installs keep data beside ``tools/``. Python wheels install data
    files under ``sys.prefix`` via ``tool.setuptools.data-files``.
    """
    env_root = os.environ.get("PCX_TOOLKIT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([source_root(), Path(sys.prefix)])
    for candidate in candidates:
        if _looks_like_data_root(candidate):
            return candidate
    return source_root()
