"""Deterministic Perception MCP workflow plans."""

from __future__ import annotations

import json
from typing import Any

BASE_DOCS = [
    "docs/perception/mcp-api.md",
    "docs/perception/mcp-workflows.md",
    "docs/perception/mcp-error-recovery.md",
    "docs/perception/two-mcp-workflow.md",
]

BASE_WARNINGS = [
    "Handles and addresses must be hex strings, not JSON numbers.",
    "Acquire a fresh process handle per MCP connection.",
    "Release handles with process/dereference or process/cleanup_references.",
]

WORKFLOWS: dict[str, dict[str, Any]] = {
    "attach_read": {
        "triggers": ("attach", "read", "typed", "value", "address", "process read", "memory read"),
        "title": "Attach and read a typed value",
        "docs": [*BASE_DOCS, "docs/tasks/proc-read.md"],
        "steps": [
            {"tool": "process/reference_by_name", "params": {"name": "$target_process"}, "save_as": "handle"},
            {"tool": "process/get_module_by_name", "params": {"handle": "$handle", "name": "$target_process"}, "save_as": "module"},
            {"tool": "process/is_valid_address", "params": {"handle": "$handle", "address": "$address"}},
            {"tool": "process/read_typed_value", "params": {"handle": "$handle", "address": "$address", "type": "u32"}},
            {"tool": "process/dereference", "params": {"handle": "$handle"}},
        ],
    },
    "string_xref": {
        "triggers": ("string", "xref", "refs", "ui text", "literal", "owning function"),
        "title": "Find code references to a string and disassemble the owning function",
        "docs": [*BASE_DOCS, "docs/perception/mcp-transcripts/string-xref.md"],
        "steps": [
            {"tool": "process/reference_by_name", "params": {"name": "$target_process"}, "save_as": "handle"},
            {"tool": "process/get_module_by_name", "params": {"handle": "$handle", "name": "$target_process"}, "save_as": "module"},
            {"tool": "process/find_string_refs", "params": {"handle": "$handle", "module_base": "$module.base", "text": "$text", "encoding": "ascii", "heap_only": True, "string_module": "$module.base"}, "save_as": "xrefs"},
            {"tool": "process/find_function_bounds", "params": {"handle": "$handle", "address": "$xref.address"}, "save_as": "bounds"},
            {"tool": "process/disassemble", "params": {"handle": "$handle", "address": "$bounds.start", "max_bytes": "$bounds.size"}},
            {"tool": "process/lookup_symbol", "params": {"handle": "$handle", "address": "$call_target"}},
            {"tool": "process/dereference", "params": {"handle": "$handle"}},
        ],
        "warnings": ["Do not use process/find_pattern for string search.", "Use encoding=utf16 for wide strings."],
    },
    "pattern_function": {
        "triggers": ("pattern", "signature", "aob", "function", "disassemble", "patch"),
        "title": "Resolve a byte pattern to a function and generate a safe signature",
        "docs": [*BASE_DOCS, "knowledge/offset-methodology.md"],
        "steps": [
            {"tool": "process/reference_by_name", "params": {"name": "$target_process"}, "save_as": "handle"},
            {"tool": "process/get_module_by_name", "params": {"handle": "$handle", "name": "$target_process"}, "save_as": "module"},
            {"tool": "process/find_all_patterns", "params": {"handle": "$handle", "start": "$module.text_start", "size": "$module.text_size", "signature": "$ida_pattern"}, "save_as": "hits"},
            {"tool": "process/find_function_bounds", "params": {"handle": "$handle", "address": "$hit"}, "save_as": "bounds"},
            {"tool": "process/disassemble", "params": {"handle": "$handle", "address": "$bounds.start", "max_bytes": "$bounds.size"}},
            {"tool": "process/generate_signature", "params": {"handle": "$handle", "address": "$bounds.start", "max_length": 48}},
            {"tool": "process/dereference", "params": {"handle": "$handle"}},
        ],
        "warnings": ["Bound pattern searches to a module .text region.", "Do not write patches without explicit write_memory permission and rollback bytes."],
    },
    "pointer_chain": {
        "triggers": ("pointer", "chain", "dereference", "entity", "base offset"),
        "title": "Validate a pointer chain",
        "docs": [*BASE_DOCS, "docs/tasks/proc-read.md"],
        "steps": [
            {"tool": "process/reference_by_name", "params": {"name": "$target_process"}, "save_as": "handle"},
            {"tool": "process/get_module_by_name", "params": {"handle": "$handle", "name": "$target_process"}, "save_as": "module"},
            {"tool": "process/read_pointer_chain", "params": {"handle": "$handle", "base_address": "$module.base + 0x1234", "offsets": [0, 16, 32]}, "save_as": "leaf"},
            {"tool": "process/is_valid_address", "params": {"handle": "$handle", "address": "$leaf"}},
            {"tool": "process/dereference", "params": {"handle": "$handle"}},
        ],
    },
    "script_validate": {
        "triggers": ("script", "validate", "compile", "enma", "execute", "context"),
        "title": "Validate generated Enma with Perception compiler surface",
        "docs": ["docs/perception/mcp-script-bridge.md", "docs/AI_AGENT_OPERATING_MANUAL.md"],
        "steps": [
            {"tool": "script/get_context", "params": {}, "save_as": "context"},
            {"tool": "script/validate", "params": {"source": "$enma_source"}},
            {"tool": "script/execute", "params": {"source": "$one_shot_source"}, "optional": True},
        ],
        "warnings": ["Call script/get_context once per session before generating code.", "script/execute does not register GUI/thread addons."],
    },
}


def _pick(task: str) -> str:
    text = task.lower()
    scores = {name: sum(1 for word in spec["triggers"] if word in text) for name, spec in WORKFLOWS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "attach_read"


def plan_perception_workflow(task: str, target_process: str = "", permissions: str = "") -> dict[str, Any]:
    key = _pick(task or "")
    spec = WORKFLOWS[key]
    perms = {p.strip() for p in permissions.replace(",", " ").split() if p.strip()}
    warnings = [*BASE_WARNINGS, *spec.get("warnings", [])]
    if any(step["tool"] in {"process/write_virtual_memory", "process/write_typed_value", "process/write_string", "process/copy_memory", "process/fill_memory"} for step in spec["steps"]):
        if "write_memory" not in perms:
            warnings.append("Write workflow requires explicit write_memory permission and rollback bytes.")
    return {
        "task": task,
        "workflow": key,
        "title": spec["title"],
        "target_process": target_process or "target.exe",
        "steps": spec["steps"],
        "cleanup": ["process/dereference(handle) after target-scoped work", "process/cleanup_references() before ending a long session"],
        "warnings": warnings,
        "docs": spec["docs"],
    }


def plan_json(task: str, target_process: str = "", permissions: str = "") -> str:
    return json.dumps(plan_perception_workflow(task, target_process, permissions), indent=2)
