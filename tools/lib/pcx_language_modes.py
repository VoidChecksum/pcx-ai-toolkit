"""Language-mode registry for PCX script surfaces.

The JSON registry is the source of truth so Python shims, MCP tools, and the
small Go helper can agree on aliases, extensions, docs, and scaffold entrypoints.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pcx_paths import data_root

REGISTRY_PATH = data_root() / "knowledge" / "language-modes.json"


@lru_cache(maxsize=1)
def load_language_modes() -> dict[str, Any]:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    modes = raw.get("modes")
    if not isinstance(modes, dict):
        raise ValueError(f"invalid language mode registry: {REGISTRY_PATH}")
    return raw


@lru_cache(maxsize=1)
def _alias_map() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for mode_id, mode in load_language_modes()["modes"].items():
        aliases[str(mode_id).lower()] = str(mode_id)
        for alias in mode.get("aliases", []):
            aliases[str(alias).lower()] = str(mode_id)
    return aliases


@lru_cache(maxsize=1)
def _extension_map() -> dict[str, str]:
    extensions: dict[str, str] = {}
    for mode_id, mode in load_language_modes()["modes"].items():
        for ext in mode.get("extensions", []):
            extensions[str(ext).lower()] = str(mode_id)
    return extensions


def supported_languages() -> list[str]:
    return sorted(str(key) for key in load_language_modes()["modes"].keys())


def default_language() -> str:
    return str(load_language_modes().get("default") or supported_languages()[0])


def normalize_language(language: str) -> str:
    text = (language or default_language()).strip().lower()
    lang = _alias_map().get(text)
    if not lang:
        choices = ", ".join(supported_languages())
        raise ValueError(f"unsupported language: {language}; use one of: {choices}")
    return lang


def language_for_path(path: Path) -> str:
    ext = path.suffix.lower()
    lang = _extension_map().get(ext)
    if not lang:
        choices = ", ".join(sorted(_extension_map()))
        raise ValueError(f"unsupported script extension: {ext or '<none>'}; use one of: {choices}")
    return lang


def language_mode(language: str) -> dict[str, Any]:
    lang = normalize_language(language)
    return dict(load_language_modes()["modes"][lang])
