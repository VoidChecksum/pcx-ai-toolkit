# VMProtect 2 Static Analysis with vmp2

Sources:
- <https://github.com/backengineering/vmp2>
- <https://raw.githubusercontent.com/backengineering/vmp2/master/UNPACKER.md>
- <https://back.engineering/blog/21/06/2021/>

## Use vmp2 for

- VMProtect 2 architecture vocabulary.
- `.vmp2` trace format and virtual instruction block concepts.
- `vmemu`-style exploration of virtualized control flow.
- `vmprofiler-cli` examples for inspecting handlers, blocks, branches, and VTIL output.
- Training/eval material for LLMs learning what *not* to hallucinate.

## Do not assume

- That every VMProtect sample is VMP2.
- That dumped modules share one standard format.
- That handler byte signatures are stable.
- That `vmdevirt` output is production-quality; vmp2 documents it as experimental.
- That building LLVM-backed components is cheap enough for default CI.

## Minimal safe workflow

```bash
# read-only triage
python3 tools/analyze-vmprotect.py --json target.exe

# if you have an authorized, unpacked VMP2 sample and vmemu installed
vmemu --vmentry 0x12345 --vmpbin unpacked.exe --out trace.vmp2

# inspect trace if vmprofiler-cli is installed
vmprofiler-cli --vmp2file trace.vmp2 --showallblocks
```

## LLM guardrails

Reject answers that:

- invent vmp2 command flags not in the docs,
- claim handler matching alone robustly devirtualizes all VMProtect,
- skip unpacking before VM bytecode analysis,
- omit authorization/sandbox scope,
- present `vmdevirt` as stable production lowering.

## Good answer shape

A good answer names the exact protector/version uncertainty, performs read-only triage first, uses vmp2 as optional external tooling, records evidence, and validates recovered behavior instead of trusting a decompiler-looking result.
