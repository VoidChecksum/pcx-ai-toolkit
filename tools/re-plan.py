#!/usr/bin/env python3
"""Deterministic reverse-engineering workflow planner."""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

UNSAFE = {"scan internet", "exploit", "bypass anticheat online", "unauthorized", "steal", "credential", "live target"}

WORKFLOWS: list[dict[str, Any]] = [
    {
        "name": "vmprotect_devirtualization",
        "triggers": {"vmprotect", "vmp", "vmp2", "devirtual", "devirtualization", "vmemu", "vmprofiler"},
        "docs": ["knowledge/vmprotect2-analysis.md", "knowledge/re-workflows/vmp2-static-analysis.md", "knowledge/re-workflows/devirtualization-generic.md", ".claude/skills/deobfuscation/SKILL.md"],
        "tools": ["python3 tools/analyze-vmprotect.py --json <sample>", "vmemu --vmentry <rva> --vmpbin <unpacked.exe> --out trace.vmp2", "vmprofiler-cli --vmp2file trace.vmp2 --showallblocks"],
        "evidence": ["protector_identification", "unpacked_oep", "vmentry_rva", "trace_vmp2", "recovered_cfg", "behavioral_equivalence"],
        "warnings": ["vmp2 is optional external tooling", "do not rely on handler matching alone", "vmdevirt is experimental"],
    },
    {
        "name": "themida_guided_symbolic_eval",
        "triggers": {"themida", "codevirtualizer", "oreans", "guided", "symbolic", "devirtual"},
        "docs": ["knowledge/re-workflows/themida-guided-symbolic-eval.md", "knowledge/re-workflows/devirtualization-generic.md", ".claude/skills/deobfuscation/SKILL.md"],
        "tools": ["r2 -nn <sample>", "x64dbg + ScyllaHide for authorized dynamic unpacking", "pcx evidence init --target <sample>"],
        "evidence": ["protector_identification", "unpacked_layer", "vm_private_ranges", "optimization_pass_log", "vmexit_classification", "behavioral_equivalence"],
        "warnings": ["promote constants only from VM-private ranges", "Themida VJCC handling differs from VMProtect"],
    },
    {
        "name": "control_flow_flattening",
        "triggers": {"cff", "flatten", "flattening", "opaque", "predicate", "ollvm", "hikari"},
        "docs": [".claude/skills/deobfuscation/SKILL.md", "knowledge/obfuscation-taxonomy.md", "knowledge/re-workflows/devirtualization-generic.md"],
        "tools": ["r2 -nn <sample>", "Ghidra decompiler for candidate dispatcher", "symbolic execution tool if available"],
        "evidence": ["dispatcher_block", "state_variable", "transition_table", "opaque_predicate_proof", "recovered_cfg"],
        "warnings": ["do not patch branches until constant/opaque predicate proof exists"],
    },
]


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", text.lower()))


def choose(task: str) -> dict[str, Any]:
    t = tokens(task)
    scored = [(len(t & set(w["triggers"])), w) for w in WORKFLOWS]
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1] if scored and scored[0][0] else WORKFLOWS[2]


def plan(task: str, target: str = "<sample>") -> dict[str, Any]:
    low = task.lower()
    wf = choose(task)
    safety = {
        "authorized_scope_required": True,
        "sandbox_unknown_binaries": True,
        "remote_or_offensive_warning": any(word in low for word in UNSAFE),
        "allowed_scope": "owned binaries, explicit client authorization, CTF/lab samples, or malware/research sandbox",
    }
    return {
        "task": task,
        "target": target,
        "workflow": wf["name"],
        "safety": safety,
        "steps": [
            {"name": "scope", "action": "Confirm authorization and sandbox unknown samples", "outputs": ["scope_note"]},
            {"name": "triage", "action": "Identify protector/obfuscation and outer packing", "outputs": ["protector", "sections", "imports", "strings"]},
            {"name": "prepare", "action": "Unpack/decrypt outer layers before inner VM or CFF analysis", "outputs": ["unpacked_sample", "oep"]},
            {"name": "recover", "action": "Apply selected workflow and record intermediate evidence", "outputs": wf["evidence"]},
            {"name": "validate", "action": "Compare recovered behavior against original under controlled inputs", "outputs": ["validation_report"]},
        ],
        "docs": wf["docs"],
        "commands": [cmd.replace("<sample>", target) for cmd in wf["tools"]],
        "evidence_outputs": wf["evidence"],
        "warnings": wf["warnings"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(prog="pcx re-plan", description="Plan authorized RE workflows")
    ap.add_argument("task", nargs="+")
    ap.add_argument("--target", default="<sample>")
    args = ap.parse_args()
    print(json.dumps(plan(" ".join(args.task), args.target), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
