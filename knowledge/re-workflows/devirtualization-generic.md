# Generic VM Devirtualization Workflow

Source-grounded workflow distilled from Back Engineering Labs' VMProtect 2 and Themida research.

Sources:
- <https://github.com/backengineering/vmp2>
- <https://back.engineering/blog/21/06/2021/>
- <https://back.engineering/blog/09/05/2026/>

## Core lesson

Do **not** build new tooling around exact VM-handler identification unless the task is explicitly handler taxonomy. The `backengineering/vmp2` README now calls this approach brittle: handler layouts, opcode tables, and dispatch logic vary enough that handler matching silently fails across versions.

Prefer a generic lifting/evaluation loop:

1. Identify packed/virtualized regions and unpack first.
2. Lift native instructions into an IR or symbolic state.
3. Promote reads from VM-private constant ranges only.
4. Run small optimizations to convergence:
   - constant promotion,
   - constant folding,
   - load/store propagation,
   - dead store elimination scoped to VM-private memory,
   - instruction combination,
   - branch folding,
   - dead dependency analysis.
5. Concretize indirect branch targets as optimization exposes them.
6. Track virtual instruction pointers to avoid unbounded loop unrolling.
7. Classify VMEXIT behavior before lowering or patching.
8. Validate recovered behavior against the original under controlled inputs.

## Why this works

VM handlers spend most of their work moving VM-private state, decoding bytecode, computing dispatch targets, and updating virtual stack/context memory. Once bytecode loads and VM-private memory reads become constants, the decode arithmetic collapses and the dispatcher becomes ordinary control flow.

## Where VM-specific knowledge remains useful

Use VM-specific knowledge sparingly:

- VMProtect: VIP often corresponds to the last module/bytecode load feeding the dispatch target.
- Themida: virtualized conditional branches may require following a branch-taken flag through VPC update logic.
- VMEXIT calls: stack displacement can distinguish call-shaped exits from returns or unsupported exits.

## Evidence outputs

For each recovered function, record:

- protector identification evidence,
- unpacking/OEP evidence,
- bytecode or dispatcher region,
- lifted block graph or trace,
- optimization pass summary,
- recovered CFG,
- behavioral equivalence checks.

Use `pcx evidence add-mcp-result` for MCP-backed findings or `pcx evidence add-claim` / `pcx evidence verify` for manual evidence graphs.
