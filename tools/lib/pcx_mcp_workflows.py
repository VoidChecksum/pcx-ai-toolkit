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

COST = {
    "cheap": {"tier": "cheap", "round_trips": 1, "max_bytes": 65536, "safe_in_loop": True, "default_timeout_ms": 3000},
    "medium": {"tier": "medium", "round_trips": 1, "max_bytes": 1048576, "safe_in_loop": False, "default_timeout_ms": 5000},
    "expensive": {"tier": "expensive", "round_trips": 1, "max_bytes": 16777216, "safe_in_loop": False, "default_timeout_ms": 15000},
    "dangerous": {"tier": "dangerous", "round_trips": 1, "max_bytes": 16777216, "safe_in_loop": False, "default_timeout_ms": 5000},
}


def step(tool: str, params: dict[str, Any] | None = None, save_as: str | None = None, *, cost: str = "medium", fallback: str | None = None, optional: bool = False) -> dict[str, Any]:
    row: dict[str, Any] = {"tool": tool, "params": params or {}, "cost": COST[cost], "requires_capability": tool}
    if save_as:
        row["save_as"] = save_as
    if fallback:
        row["fallback"] = fallback
    if optional:
        row["optional"] = True
    return row


WORKFLOWS: dict[str, dict[str, Any]] = {
    "attach_read": {"triggers": ("attach", "read", "typed", "value", "address", "process read", "memory read"), "title": "Attach and read a typed value", "docs": [*BASE_DOCS, "docs/tasks/proc-read.md"], "steps": [step("process/reference_by_name", {"name": "$target_process"}, "handle", cost="cheap"), step("process/get_module_by_name", {"handle": "$handle", "name": "$target_process"}, "module", cost="cheap"), step("process/is_valid_address", {"handle": "$handle", "address": "$address"}, cost="cheap"), step("process/read_typed_value", {"handle": "$handle", "address": "$address", "type": "u32"}, cost="cheap"), step("process/dereference", {"handle": "$handle"}, cost="cheap")]},
    "string_xref": {"triggers": ("string", "xref", "refs", "ui text", "literal", "owning function"), "title": "Find code references to a string and disassemble the owning function", "docs": [*BASE_DOCS, "docs/perception/mcp-transcripts/string-xref.md"], "steps": [step("process/reference_by_name", {"name": "$target_process"}, "handle", cost="cheap"), step("process/get_module_by_name", {"handle": "$handle", "name": "$target_process"}, "module", cost="cheap"), step("process/find_string_refs", {"handle": "$handle", "module_base": "$module.base", "text": "$text", "encoding": "ascii", "heap_only": True, "string_module": "$module.base"}, "xrefs", cost="medium", fallback="process/scan_string + process/find_xrefs"), step("process/find_function_bounds", {"handle": "$handle", "address": "$xref.address"}, "bounds", cost="cheap"), step("process/disassemble", {"handle": "$handle", "address": "$bounds.start", "max_bytes": "$bounds.size"}, cost="medium"), step("process/lookup_symbol", {"handle": "$handle", "address": "$call_target"}, cost="cheap"), step("process/dereference", {"handle": "$handle"}, cost="cheap")], "warnings": ["Do not use process/find_pattern for string search.", "Use encoding=utf16 for wide strings."]},
    "pattern_function": {"triggers": ("pattern", "signature", "aob", "function", "disassemble", "patch"), "title": "Resolve a byte pattern to a function and generate a safe signature", "docs": [*BASE_DOCS, "knowledge/offset-methodology.md"], "steps": [step("process/reference_by_name", {"name": "$target_process"}, "handle", cost="cheap"), step("process/get_module_by_name", {"handle": "$handle", "name": "$target_process"}, "module", cost="cheap"), step("process/find_all_patterns", {"handle": "$handle", "start": "$module.text_start", "size": "$module.text_size", "signature": "$ida_pattern"}, "hits", cost="expensive", fallback="process/find_pattern bounded to .text"), step("process/find_function_bounds", {"handle": "$handle", "address": "$hit"}, "bounds", cost="cheap"), step("process/disassemble", {"handle": "$handle", "address": "$bounds.start", "max_bytes": "$bounds.size"}, cost="medium"), step("process/generate_signature", {"handle": "$handle", "address": "$bounds.start", "max_length": 48}, cost="medium"), step("process/dereference", {"handle": "$handle"}, cost="cheap")], "warnings": ["Bound pattern searches to a module .text region.", "Do not write patches without explicit write_memory permission and rollback bytes."]},
    "pointer_chain": {"triggers": ("pointer", "chain", "dereference", "entity", "base offset"), "title": "Validate a pointer chain", "docs": [*BASE_DOCS, "docs/tasks/proc-read.md"], "steps": [step("process/reference_by_name", {"name": "$target_process"}, "handle", cost="cheap"), step("process/get_module_by_name", {"handle": "$handle", "name": "$target_process"}, "module", cost="cheap"), step("process/read_pointer_chain", {"handle": "$handle", "base_address": "$module.base + 0x1234", "offsets": [0, 16, 32]}, "leaf", cost="cheap"), step("process/is_valid_address", {"handle": "$handle", "address": "$leaf"}, cost="cheap"), step("process/dereference", {"handle": "$handle"}, cost="cheap")]},
    "script_validate": {"triggers": ("script", "validate", "compile", "enma", "execute", "context"), "title": "Validate generated Enma with Perception compiler surface", "docs": ["docs/perception/mcp-script-bridge.md", "docs/AI_AGENT_OPERATING_MANUAL.md"], "steps": [step("script/get_context", {}, "context", cost="cheap"), step("script/validate", {"source": "$enma_source"}, cost="medium"), step("script/execute", {"source": "$one_shot_source"}, cost="dangerous", optional=True)], "warnings": ["Call script/get_context once per session before generating code.", "script/execute does not register GUI/thread addons."]},
}

# Small extra workflows: compose from real tools, keep planner deterministic.
EXTRA = {
    "module_inventory": (("module", "inventory", "modules", "map"), "Inventory process modules", ["process/reference_by_name", "process/get_module_list", "process/list_module_exports", "process/dereference"]),
    "rtti_class_analysis": (("rtti", "class", "typeinfo"), "Analyze RTTI class evidence", ["process/reference_by_name", "process/get_module_by_name", "process/analyze_vtable", "process/read_rtti", "process/find_xrefs", "process/disassemble", "process/dereference"]),
    "vtable_analysis": (("vtable", "virtual", "method"), "Analyze vtable slots", ["process/reference_by_name", "process/analyze_vtable", "process/read_rtti", "process/find_function_bounds", "process/disassemble", "process/dereference"]),
    "handle_inventory": (("handle", "handles", "references"), "Inventory MCP handles", ["process/list_references", "process/cleanup_references"]),
    "memory_region_scan": (("memory region", "regions", "scan region"), "Scan bounded memory regions", ["process/reference_by_name", "process/enumerate_memory_regions", "process/scan_value", "process/dereference"]),
    "heap_value_scan": (("heap", "value scan", "scan value"), "Scan heap values", ["process/reference_by_name", "process/enumerate_memory_regions", "process/scan_value", "process/dereference"]),
    "patch_safe_write": (("write", "patch", "poke", "modify"), "Patch-safe write with rollback", ["process/reference_by_name", "process/get_module_by_name", "process/read_virtual_memory", "process/is_valid_address", "process/write_virtual_memory", "process/read_virtual_memory", "process/write_virtual_memory", "process/dereference"]),
    "allocation_scratchpad": (("allocate", "scratchpad", "alloc"), "Allocate scratch memory safely", ["process/reference_by_name", "process/allocate_memory", "process/write_virtual_memory", "process/read_virtual_memory", "process/free_memory", "process/dereference"]),
    "environment_inspection": (("environment", "system", "drivers"), "Inspect runtime environment", ["system/info", "system/list_drivers", "process/list"]),
    "thread_inventory": (("thread", "threads"), "Inventory process threads", ["process/reference_by_name", "process/list_threads", "process/dereference"]),
    "import_export_analysis": (("import", "export", "iat", "eat"), "Analyze imports and exports", ["process/reference_by_name", "process/get_module_by_name", "process/list_module_exports", "process/list_module_imports", "process/dereference"]),
    "exception_table_bounds": (("exception", "unwind", "function bounds"), "Use exception tables for function bounds", ["process/reference_by_name", "process/get_module_by_name", "process/find_function_bounds", "process/disassemble", "process/dereference"]),
    "signature_regeneration_after_patch": (("regenerate", "patch day", "after patch"), "Regenerate signatures after a patch", ["process/reference_by_name", "process/get_module_by_name", "process/find_all_patterns", "process/find_function_bounds", "process/generate_signature", "process/dereference"]),
}
for key, (triggers, title, tools) in EXTRA.items():
    WORKFLOWS[key] = {"triggers": triggers, "title": title, "docs": BASE_DOCS, "steps": [step(t, {"handle": "$handle"} if t.startswith("process/") and t not in {"process/reference_by_name", "process/list_references", "process/cleanup_references", "process/list"} else ({"name": "$target_process"} if t == "process/reference_by_name" else {}), cost=("dangerous" if "write" in t or "allocate" in t else "medium")) for t in tools]}


def _pick(task: str) -> str:
    text = task.lower()
    scores = {name: sum(1 for word in spec["triggers"] if word in text) for name, spec in WORKFLOWS.items()}
    return max(scores, key=lambda name: scores[name]) if max(scores.values()) else "attach_read"


def _apply_capabilities(spec: dict[str, Any], capabilities: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    if not capabilities:
        return spec["steps"], []
    warnings: list[str] = []
    steps: list[dict[str, Any]] = []
    for row in spec["steps"]:
        if row["tool"] in capabilities:
            steps.append(row)
        elif row.get("fallback"):
            warnings.append(f"{row['tool']} unavailable; use fallback: {row['fallback']}")
        else:
            warnings.append(f"{row['tool']} unavailable and no fallback is defined")
    return steps, warnings


def plan_perception_workflow(task: str, target_process: str = "", permissions: str = "", capabilities: list[str] | None = None) -> dict[str, Any]:
    key = _pick(task or "")
    spec = WORKFLOWS[key]
    perms = {p.strip() for p in permissions.replace(",", " ").split() if p.strip()}
    steps, cap_warnings = _apply_capabilities(spec, set(capabilities or []))
    warnings = [*BASE_WARNINGS, *spec.get("warnings", []), *cap_warnings]
    if any(step["tool"] in {"process/write_virtual_memory", "process/write_typed_value", "process/write_string", "process/copy_memory", "process/fill_memory", "process/allocate_memory"} for step in steps):
        if "write_memory" not in perms:
            warnings.append("Write/allocation workflow requires explicit write_memory permission, old bytes, read-back, and rollback.")
    if any(step["cost"]["tier"] == "expensive" for step in steps):
        warnings.append("Do not place expensive scans in loops; bound scans to module .text or selected regions.")
    return {"task": task, "workflow": key, "title": spec["title"], "target_process": target_process or "target.exe", "steps": steps, "cleanup": ["process/dereference(handle) after target-scoped work", "process/cleanup_references() before ending a long session"], "warnings": warnings, "docs": spec["docs"]}


def plan_json(task: str, target_process: str = "", permissions: str = "", capabilities: list[str] | None = None) -> str:
    return json.dumps(plan_perception_workflow(task, target_process, permissions, capabilities), indent=2)
