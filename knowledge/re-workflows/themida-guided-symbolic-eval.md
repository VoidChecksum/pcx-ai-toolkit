# Themida Guided Symbolic Evaluation Workflow

Source: <https://back.engineering/blog/09/05/2026/>

## Summary

Back Engineering Labs' 2026 Themida article argues for reducing VM-based obfuscators with mostly generic symbolic evaluation and optimizer passes, not brittle per-handler pattern matching.

## Workflow

1. Confirm authorization and sandbox unknown samples.
2. Identify Themida/CodeVirtualizer indicators.
3. Unpack/decrypt outer layers before virtualized-code recovery.
4. Lift native instructions with all registers/flags symbolic except a deliberately concrete initial stack pointer when practical.
5. Configure memory promotion ranges to VM-private regions only.
6. Run optimization passes to convergence:
   - constant promotion,
   - constant folding,
   - load/store propagation,
   - VM-private dead store elimination,
   - instruction combination,
   - branch folding.
7. Handle virtualized control flow explicitly:
   - record virtual instruction pointers,
   - detect loops/backedges,
   - follow Themida branch-taken/VPC update logic for virtualized JCCs.
8. Classify VMEXIT forms by stack displacement and call/return behavior.
9. Before lowering, run dead dependency analysis against native code after VMEXIT.
10. Validate with behavior, not aesthetics: recovered code must execute equivalently.

## Practical pcx use

Use this doc with:

```bash
pcx re-plan "Themida devirtualization of an authorized sample"
pcx evidence init --target sample.exe
```

For unsupported live tooling, produce a plan and evidence checklist rather than pretending pcx has BLARE2-level lifting built in.

## Anti-hallucination checks

A model response is suspicious if it:

- claims Themida and VMProtect have identical VJCC handling,
- treats LLVM lowering as automatically clean/reinsertable,
- promotes arbitrary memory loads as constants,
- removes dead stores outside VM-private memory,
- unrolls virtualized loops without tracking VIP/backedges.
