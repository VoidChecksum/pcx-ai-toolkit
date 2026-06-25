"""Deterministic Perception MCP workflow plans."""
from __future__ import annotations
import json, re
from typing import Any

BASE_DOCS=["docs/perception/mcp-api.md","docs/perception/mcp-workflows.md","docs/perception/mcp-error-recovery.md","docs/perception/two-mcp-workflow.md"]
BASE_WARNINGS=["Handles and addresses must be hex strings, not JSON numbers.","Acquire a fresh process handle per MCP connection.","Release handles with process/dereference or process/cleanup_references."]
COST={"cheap":{"tier":"cheap","round_trips":1,"max_bytes":65536,"safe_in_loop":True,"default_timeout_ms":3000},"medium":{"tier":"medium","round_trips":1,"max_bytes":1048576,"safe_in_loop":False,"default_timeout_ms":5000},"expensive":{"tier":"expensive","round_trips":1,"max_bytes":16777216,"safe_in_loop":False,"default_timeout_ms":15000},"dangerous":{"tier":"dangerous","round_trips":1,"max_bytes":16777216,"safe_in_loop":False,"default_timeout_ms":5000}}
NO_HANDLE={"process/list","process/reference_by_name","process/reference_by_pid","process/info_by_name","process/info_by_pid","process/cleanup_references","process/list_references"}
FALLBACKS={
 "process/find_string_refs":["process/scan_string","process/find_xrefs","process/find_function_bounds","process/disassemble"],
 "process/read_rtti":["process/analyze_vtable","process/lookup_symbol","process/disassemble"],
 "process/find_all_patterns":["process/find_pattern","process/find_function_bounds","process/generate_signature"],
}

def step(tool:str, params:dict[str,Any]|None=None, save_as:str|None=None, *, cost:str="medium", optional:bool=False)->dict[str,Any]:
    row={"tool":tool,"params":params or {},"cost":COST[cost],"requires_capability":tool}
    if save_as: row["save_as"]=save_as
    if optional: row["optional"]=True
    if tool in FALLBACKS: row["fallback"]=" + ".join(FALLBACKS[tool])
    return row

def proc(tool, params=None, save_as=None, cost="medium", optional=False):
    if params is None and tool.startswith("process/") and tool not in NO_HANDLE: params={"handle":"$handle"}
    return step(tool, params, save_as, cost=cost, optional=optional)

WORKFLOWS={
 "attach_read":{"triggers":("attach","read","typed","value","address","process read","memory read"),"title":"Attach and read a typed value","docs":[*BASE_DOCS,"docs/tasks/proc-read.md"],"steps":[proc("process/reference_by_name",{"name":"$target_process"},"handle","cheap"),proc("process/get_module_by_name",{"handle":"$handle","name":"$target_process"},"module","cheap"),proc("process/is_valid_address",{"handle":"$handle","address":"$address"},cost="cheap"),proc("process/read_typed_value",{"handle":"$handle","address":"$address","type":"u32"},cost="cheap"),proc("process/dereference",{"handle":"$handle"},cost="cheap")]},
 "string_xref":{"triggers":("string","xref","refs","ui text","literal","owning function"),"title":"Find code references to a string and disassemble the owning function","docs":[*BASE_DOCS,"docs/perception/mcp-transcripts/string-xref.md"],"steps":[proc("process/reference_by_name",{"name":"$target_process"},"handle","cheap"),proc("process/get_module_by_name",{"handle":"$handle","name":"$target_process"},"module","cheap"),proc("process/find_string_refs",{"handle":"$handle","module_base":"$module.base","text":"$text","encoding":"ascii","heap_only":True,"string_module":"$module.base"},"xrefs","medium"),proc("process/find_function_bounds",{"handle":"$handle","address":"$xrefs[0].address"},"bounds"),proc("process/disassemble",{"handle":"$handle","start":"$bounds.start","end":"$bounds.end"}),proc("process/dereference",{"handle":"$handle"},cost="cheap")]},
 "pattern_function":{"triggers":("pattern","signature","aob","function","disassemble","patch"),"title":"Resolve a byte pattern to a function and generate a safe signature","docs":[*BASE_DOCS,"knowledge/offset-methodology.md"],"steps":[proc("process/reference_by_name",{"name":"$target_process"},"handle","cheap"),proc("process/get_module_by_name",{"handle":"$handle","name":"$target_process"},"module","cheap"),proc("process/find_all_patterns",{"handle":"$handle","start":"$module.text_start","size":"$module.text_size","signature":"$ida_pattern"},"hits","expensive"),proc("process/find_function_bounds",{"handle":"$handle","address":"$hits[0]"},"bounds"),proc("process/generate_signature",{"handle":"$handle","start":"$bounds.start","end":"$bounds.end"}),proc("process/dereference",{"handle":"$handle"},cost="cheap")]},
 "pointer_chain":{"triggers":("pointer","chain","dereference","entity","base offset"),"title":"Validate a pointer chain","docs":[*BASE_DOCS,"docs/tasks/proc-read.md"],"steps":[proc("process/reference_by_name",{"name":"$target_process"},"handle","cheap"),proc("process/get_module_by_name",{"handle":"$handle","name":"$target_process"},"module","cheap"),proc("process/read_pointer_chain",{"handle":"$handle","base_address":"$module.base + 0x1234","offsets":[0,16,32]},"leaf","cheap"),proc("process/is_valid_address",{"handle":"$handle","address":"$leaf"},cost="cheap"),proc("process/dereference",{"handle":"$handle"},cost="cheap")]},
 "script_validate":{"triggers":("script","validate","compile","enma","execute","context"),"title":"Validate generated Enma with Perception compiler surface","docs":["docs/perception/mcp-script-bridge.md","docs/AI_AGENT_OPERATING_MANUAL.md"],"steps":[step("script/get_context",{},"context",cost="cheap"),step("script/validate",{"source":"$enma_source"},cost="medium"),step("script/execute",{"source":"$one_shot_source"},cost="dangerous",optional=True)],"warnings":["Call script/get_context once per session before generating code.","script/execute does not register GUI/thread addons and may touch GUI/thread state."]},
}
EXTRA={
 "module_inventory":(("module","inventory","modules","map"),"Inventory process modules",["process/reference_by_name","process/get_module_list","process/list_module_exports","process/dereference"]),
 "rtti_class_analysis":(("rtti","class","typeinfo"),"Analyze RTTI class evidence",["process/reference_by_name","process/get_module_by_name","process/analyze_vtable","process/read_rtti","process/find_xrefs","process/disassemble","process/dereference"]),
 "vtable_analysis":(("vtable","virtual","method"),"Analyze vtable slots",["process/reference_by_name","process/analyze_vtable","process/read_rtti","process/find_function_bounds","process/disassemble","process/dereference"]),
 "heap_value_scan":(("heap","value scan","scan value"),"Scan heap values",["process/reference_by_name","process/enumerate_memory_regions","process/scan_value","process/dereference"]),
 "scan_next_narrowing":(("scan next","narrow","rescan"),"Narrow previous scan results",["process/reference_by_name","process/scan_value","process/scan_next","process/dereference"]),
 "diff_memory":(("diff memory","compare memory","changed bytes"),"Diff memory snapshots",["process/reference_by_name","process/read_virtual_memory","process/read_virtual_memory","process/diff_memory","process/dereference"]),
 "patch_safe_write":(("write","patch","poke","modify","rollback"),"Patch-safe write with rollback",["process/reference_by_name","process/get_module_by_name","process/read_virtual_memory","process/is_valid_address","process/write_virtual_memory","process/read_virtual_memory","process/write_virtual_memory","process/dereference"]),
 "allocation_scratchpad":(("allocate","allocation","scratchpad","alloc"),"Allocate scratch memory safely",["process/reference_by_name","process/allocate_memory","process/write_virtual_memory","process/read_virtual_memory","process/free_memory","process/dereference"]),
 "driver_listing_permission":(("driver","drivers","kernel"),"List drivers with permission awareness",["system/info","system/list_drivers","process/list"]),
 "import_export_analysis":(("import","export","iat","eat"),"Analyze imports and exports",["process/reference_by_name","process/get_module_by_name","process/list_module_exports","process/list_module_imports","process/dereference"]),
 "exception_table_bounds":(("exception","unwind","function bounds"),"Use exception tables for function bounds",["process/reference_by_name","process/get_module_by_name","process/find_function_bounds","process/disassemble","process/dereference"]),
 "patch_rollback":(("rollback","restore patch","undo patch"),"Rollback a patch from saved bytes",["process/reference_by_name","process/write_virtual_memory","process/read_virtual_memory","process/dereference"]),
 "stale_handle_recovery":(("stale handle","expired handle","reacquire"),"Recover from stale process handle",["process/reference_by_name","process/read_typed_value","process/reference_by_name","process/read_typed_value","process/dereference"]),
 "target_not_found_recovery":(("target not found","missing target","process missing"),"Recover target-not-found errors",["process/list","process/reference_by_name"]),
}
for key,(triggers,title,tools) in EXTRA.items():
    steps=[]
    for t in tools:
        if t=="process/reference_by_name": steps.append(proc(t,{"name":"$target_process"},"handle","cheap"))
        else: steps.append(proc(t, cost=("dangerous" if any(x in t for x in ("write","allocate","free")) else "medium")))
    WORKFLOWS[key]={"triggers":triggers,"title":title,"docs":BASE_DOCS,"steps":steps}

def _pick(task:str)->str:
    text=task.lower()
    if "rollback" in text or "restore patch" in text or "undo patch" in text: return "patch_rollback"
    if "full user-space" in text and "scan" in text: return "heap_value_scan"
    scores={n:sum(1 for w in s["triggers"] if w in text) for n,s in WORKFLOWS.items()}
    return max(scores,key=scores.get) if max(scores.values()) else "attach_read"

def _apply_capabilities(spec:dict[str,Any], capabilities:set[str]):
    if not capabilities: return spec["steps"], [], []
    warnings=[]; fallbacks=[]; steps=[]
    for row in spec["steps"]:
        tool=row["tool"]
        if tool in capabilities or tool not in FALLBACKS:
            if tool in capabilities or not capabilities: steps.append(row)
            elif tool not in capabilities: warnings.append(f"{tool} unavailable and no fallback is defined")
        else:
            repl=[step(t,{"handle":"$handle"} if t.startswith("process/") else {}) for t in FALLBACKS[tool]]
            steps.extend(repl); fallbacks.append({"missing":tool,"replacement_steps":[r["tool"] for r in repl]}); warnings.append(f"{tool} unavailable; using concrete fallback plan")
    return steps,warnings,fallbacks

def validate_workflow(plan:dict[str,Any])->list[str]:
    produced={"target_process","address","text","ida_pattern","enma_source","one_shot_source"}; errors=[]
    for i,row in enumerate(plan.get("steps",[]),1):
        tool=row["tool"]; params=row.get("params",{})
        if tool.startswith("process/") and tool not in NO_HANDLE and "handle" not in params: errors.append(f"step {i} {tool} missing handle")
        for v in re.findall(r"\$([A-Za-z_][A-Za-z0-9_]*(?:\[[0-9]+\])?(?:\.[A-Za-z_][A-Za-z0-9_]*)?)", json.dumps(params)):
            base=v.split("[")[0].split(".")[0]
            if base not in produced: errors.append(f"step {i} uses ${v} before production")
        if row.get("save_as"): produced.add(row["save_as"])
    return errors

def plan_perception_workflow(task:str, target_process:str="", permissions:str="", capabilities:list[str]|None=None)->dict[str,Any]:
    key=_pick(task or ""); spec=WORKFLOWS[key]; steps,cap_warnings,fallbacks=_apply_capabilities(spec,set(capabilities or [])); warnings=[*BASE_WARNINGS,*spec.get("warnings",[]),*cap_warnings]
    perms={p.strip() for p in permissions.replace(","," ").split() if p.strip()}
    if any(s["tool"] in {"process/write_virtual_memory","process/write_typed_value","process/write_string","process/copy_memory","process/fill_memory","process/allocate_memory"} for s in steps) and "write_memory" not in perms: warnings.append("Write/allocation workflow requires explicit write_memory permission, old bytes, read-back, and rollback.")
    if any(s["cost"]["tier"]=="expensive" for s in steps): warnings.append("Do not place expensive scans in loops; bound scans to module .text or selected regions.")
    if "broad" in task.lower() or "full user-space" in task.lower(): warnings.append("Broad/full user-space scans need explicit bounds and user confirmation.")
    plan={"task":task,"workflow":key,"title":spec["title"],"target_process":target_process or "target.exe","steps":steps,"fallbacks":fallbacks,"cleanup":["process/dereference(handle) after target-scoped work","process/cleanup_references() before ending a long session"],"warnings":warnings,"docs":spec["docs"]}
    errs=validate_workflow(plan)
    if errs: plan["static_validation_errors"]=errs
    return plan

def plan_json(task:str,target_process:str="",permissions:str="",capabilities:list[str]|None=None)->str:
    return json.dumps(plan_perception_workflow(task,target_process,permissions,capabilities),indent=2)
