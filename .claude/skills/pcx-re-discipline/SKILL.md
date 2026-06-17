# PCX Reverse-Engineering Discipline — Finding Offsets Without Fooling Yourself

Workflow discipline for reverse engineering and offset maintenance: locating structs, generating signatures, resolving RIP-relative addresses, and keeping an offset table alive across game patches. Derived from the four Karpathy principles — *think before coding, simplicity first, surgical changes, goal-driven execution* — rewritten for RE work, where the failure mode isn't a crash but a confident wrong answer.

**Always active when doing RE or offset work.** This complements `game-cheat-guidelines` #1 (ground every offset) and #12 (verify with the binary), and the `knowledge/offset-methodology.md` mechanics. Those cover *how* to scan; this covers *how to work* so you don't ship a guess.

## Trigger
Disassembling a function, mapping a struct layout, generating a byte signature, resolving an offset, updating an offset table after a patch, or cross-referencing an SDK against a live binary. Tools: IDA, Ghidra, radare2, and the Perception RE tools (`struct_dump`, `find_xrefs`, `analyze_vtable`, `read_rtti`, `generate_signature`, `find_code_pattern`, `build_call_graph`).

---

## 1. Hypothesize Before You Disassemble

**Form a claim about what a function or field *is*, then look for evidence — don't reverse aimlessly and rationalize whatever you find.**

A float at `entity+0x43E0` that reads `100.0` might be health. It might be armor, a timer, or a shield that happens to start at 100. Guessing wrong here is silent and expensive.

- **State the hypothesis first.** "This sig should land on the LEA that loads `CEntityList`. Expected: `48 8D 0D` followed by a RIP displacement."
- **Use the cheapest evidence before manual disasm.** RTTI names (`read_rtti`) and string xrefs (`find_xrefs`) identify a class faster than reading instructions. Reach for them first.
- **Mark unverified findings `UNVERIFIED` and cite the source** — r5sdk header path, RTTI string, IDA xref address. An offset without a citation is a rumor.
- **One value is not proof.** Confirm a field by watching it change as you'd expect in-game, or by matching the SDK layout — not by a single plausible read.

```
Before: "0x43E0 is health, it reads 100."

After:  "Hypothesis: 0x43E0 = m_iHealth (int32).
         Evidence: r5sdk/player.h offset matches; read_rtti confirms class CPlayer;
         value drops to 73 after taking damage in-game. CONFIRMED."
```

**Why:** RE has no compiler to catch you. The only thing standing between a wrong offset and an hour of debugging ESP-at-(0,0) is the evidence you demanded before believing your own hypothesis.

---

## 2. The Simplest Signature That's Unique

**The shortest byte pattern that hits exactly one location. Not longer, not vaguer.**

A sig is a tradeoff: too specific and it breaks on the next compiler tweak; too loose and it matches three places and resolves to garbage.

- **Wildcard only the relocatable bytes** — RIP-relative displacements, absolute immediates, jump targets. Keep the opcodes. `48 8D 0D ?? ?? ?? ??` wildcards the displacement, keeps the `LEA RCX` opcode.
- **Stop at the first length that's unique.** Verify it with `find_code_pattern` over the module — one hit means stop. Don't bolt on ten more bytes "to be safe"; that's the brittleness you'll pay for next patch.
- **Don't reverse a whole class to read one field.** `struct_dump` the instance and xref the accessor function. Map the entire vtable only when you actually need the entire vtable.
- **Don't build a full offset dumper for three offsets.** Three sigs in `offsets.em` is the right size for three offsets.

```cpp
// WRONG — 24 bytes, spans an immediate that changes per build → dead next patch
"48 8D 0D 30 AF 25 02 E8 1A 4C 00 00 48 8B D8 48 85 DB 74 12 8B 05 ..."

// RIGHT — shortest unique hit, displacement wildcarded
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";
// verify: find_code_pattern(base, size, SIG_ENTITY_LIST) returns exactly one hit
```

**Why:** Every non-wildcarded byte is a bet that the compiler emits it identically next build. The minimal unique sig makes the fewest bets, so it survives the most patches — which is the entire point of using sigs over hardcodes.

---

## 3. After a Patch, Re-verify Only What Broke

**Run the whole table, fix the misses, leave the hits alone. Don't regenerate offsets that still work.**

The temptation after a game update is to rebuild the offset table from scratch. That's churn: it risks the offsets that were fine and buries the one real change in noise.

- **Run every sig.** `find_code_pattern` returning 0 is a miss — that sig needs a new pattern. A hit that resolves to valid data is fine; leave it untouched.
- **Verify the survivors didn't silently shift.** A sig can still hit while the *struct field* behind it moved. Spot-check resolved pointers with `struct_dump`.
- **Touch only the broken entries.** Re-sig the misses, update their resolved addresses, bump the version stamp, and log exactly what changed in a changelog. The diff should be the patch's actual damage, nothing more.

```
Post-patch checklist:
[ ] Ran all N sigs                          → 3 misses, N-3 hits
[ ] Hits resolve to valid data              → struct_dump spot-check OK
[ ] Re-sigged ONLY the 3 misses             → no churn on working entries
[ ] Bumped version stamp + changelog        → "Season 22: re-sigged entity_list,
                                               view_matrix, local_player"
```

**Why:** A surgical post-patch diff is reviewable and reversible — you can see precisely what the update moved. A full-table rewrite hides the signal, re-introduces transcription bugs into offsets that were already correct, and turns a 20-minute fix into a re-audit.

---

## 4. Trust Live Memory, Loop Until It Agrees

**Success is a sig that resolves to an address whose *live contents* match the expected layout. Loop until the three sources agree, and when they don't, the running process wins.**

The IDB, the SDK headers, and live memory are three views that drift apart. The IDB is a snapshot; the SDK may be an old season; only live memory is the truth right now.

- **Define done concretely:** "sig hits once, RIP resolves to an address, the bytes there `struct_dump` to the layout I expect."
- **Loop:** sig hit → resolve RIP-relative (4-byte signed displacement added to the *end* of the instruction) → read at the target → `struct_dump` / `print` → does it match the hypothesis? → if not, fix the sig or the resolution math and repeat.
- **Resolve RIP correctly or everything downstream is wrong:** `target = hit + instr_len + read_i32(hit + disp_offset)`. Off-by-one on the instruction length points you at the wrong global.
- **When the SDK says one offset and the live read says another, trust the live read** and update your notes. The header was written for a build that no longer exists.

```cpp
// The verify loop, made explicit
uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
if (hit == 0) { println("MISS — sig is stale, re-RE the load instruction"); return; }
int32 disp   = p.r32(hit + 3);          // displacement at LEA+3
uint64 target = hit + 7 + cast<uint64>(disp);  // end of 7-byte LEA + signed disp
uint64 list  = p.ru64(target);
println(format("entity_list global @ 0x{x} -> 0x{x}", target, list));
// struct_dump `list` and confirm it looks like a CEntityList before trusting it
```

**Why:** A sig that compiles into your script proves nothing. A sig that resolves to live memory matching your expected struct is the only evidence that the offset is real — and demanding that evidence is what separates a maintained offset table from a pile of hopeful constants.

---

## Summary

| # | Principle (Karpathy) | In RE terms |
|---|----------------------|-------------|
| 1 | Think Before Coding | Hypothesize + cite evidence before believing a field's meaning |
| 2 | Simplicity First | Shortest unique sig; wildcard only relocatable bytes |
| 3 | Surgical Changes | Post-patch: fix only the misses, never churn working offsets |
| 4 | Goal-Driven Execution | Done = sig resolves to live memory matching the expected layout |
