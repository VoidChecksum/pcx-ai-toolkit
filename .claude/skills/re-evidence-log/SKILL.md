# RE Evidence Log — Every Claim Cites Its Proof

The discipline of recording *why* you trust each offset and sig in your project. The offset table is data; the evidence log is the proof behind it. Without the log, every patch day starts from zero on the same offsets you derived three months ago — you remember roughly what you did, not the citations that let you confirm it. This skill is the artifact half of `pcx-re-discipline` (which is the discipline itself) and the input to `pcx-patch-day-playbook` Step 7 (which writes a per-patch entry into the log).

**Always active when doing RE work.** Every offset you add, every sig you derive, every struct layout you commit to the project comes with an evidence entry. The cost is one paragraph per claim; the payoff is being able to answer "why do we trust this?" three months later without re-reversing.

**Prerequisite:** `skill://pcx-re-discipline` for the underlying discipline rules; `knowledge/offset-methodology.md` for the sig-derivation mechanics the log entries reference; `tools/sig-uniqueness-checker.py` for the verdict you record alongside each sig.

---

## Trigger

Starting RE work on a new binary, adding an offset to `offsets.em`, committing a struct layout to a feature, recovering from a patch (the patch-day skill produces a log entry), onboarding a teammate to existing offsets, code-review of RE claims, suspicious behavior in a script you wrote weeks ago and can't remember why a field is at +0x40.

---

## 1. One File per Binary, One Entry per Claim

**The canonical layout: `evidence/<binary-hash-prefix>.md`, one file per binary you reverse, one numbered entry per claim.** Filed by content hash, not by game name or version — the same game across patches produces different binaries with different hashes; each gets its own file.

```
project/
├── globals.em
├── offsets.em
├── ...
└── evidence/
    ├── README.md                          ← what's in here, naming convention
    ├── 7a3f4d1c-game-v1.42.3.md           ← per-binary log
    ├── 7a3f4d1c-game-v1.42.3.sha256       ← cached hash for trivial verification
    ├── 9b2e8a07-game-v1.42.4.md           ← next patch = new file
    └── archive/                           ← old entries kept for diffing
        └── 7a3f4d1c-game-v1.42.3.md
```

Inside one file, each claim is its own section:

```markdown
# Evidence Log — game.exe v1.42.3
SHA-256: 7a3f4d1c8e2b5a019f3d4c7e2b1a8f6d...
Module size: 158,720,000 bytes (.text 0x00400000–0x00C12000)
First verified: 2026-06-15
Last verified: 2026-06-17

## E-001 — entity_list global pointer
## E-002 — local_player slot
## E-003 — view matrix (4x4 row-major)
## E-004 — CEntity::m_iHealth field offset
## E-005 — CEntity::m_vecOrigin field offset
...
```

Entry IDs (`E-001` … `E-NNN`) are stable across patches — `offsets.em` references them in comments (`// E-003`), so when you rewrite the offset for the next version, you keep the same ID and update the per-version file. The ID is the cross-reference; the file is the version-specific evidence.

**Why:** Without a per-binary file, you can't diff what changed between patches. Without numbered entries, you can't reference a claim from your code or a teammate's review. The file naming by hash means the system survives renames, re-downloads, and side-by-side comparison.

---

## 2. Every Claim Cites: Binary, Address, Xref Source, Last-Verified Date

**The minimum citation per entry. Anything shorter is a vague memory dressed up as a fact.**

The required fields per entry:

| Field | Why |
|---|---|
| `id` | Stable cross-reference for `offsets.em` and patch logs |
| `name` | Human-readable label (matches the constant in `offsets.em`) |
| `binary_hash` | The binary this claim is verified against |
| `rva` (or `sig`) | Where the thing is |
| `xref_source` | Function symbol, sig pattern, or string xref that found it |
| `derived_via` | How: pattern scan? SDK header lookup? Struct dump? |
| `last_verified` | Date of the most recent successful run on this binary |
| `verified_against` | The in-game observation that confirmed it works |

```markdown
## E-001 — entity_list global pointer

| Field             | Value |
|---|---|
| name              | `OFF_ENTITY_LIST` |
| kind              | RIP-relative pointer (loaded by LEA) |
| rva               | 0x04A2B100  (resolved from sig hit at 0x00872F40) |
| sig               | `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8` |
| sig_uniqueness    | UNIQUE (margin=5, per `tools/sig-uniqueness-checker.py`) |
| xref_source       | Called by `CGameWorld::Update`, identified via string xref "entity_list_full" |
| derived_via       | Pattern scan + RIP resolve (disp@+3, insn_len=7) |
| last_verified     | 2026-06-17 |
| verified_against  | ESP showed 12 entities in a match; entity count matched scoreboard |
```

WRONG — the kind of "evidence" that's actually nothing:

```markdown
## entity_list
Found in some function, +0x18 or +0x20, I think? Worked last time I checked.
```

This will cost you an hour the next time you touch it.

RIGHT — every field present, every claim verifiable:

```markdown
## E-001 — entity_list
hash 7a3f4d1c..., rva 0x04A2B100, sig "48 8D 0D ?? ...", from CGameWorld::Update,
verified 2026-06-17 against the scoreboard entity count.
```

The detail level is up to you — a table per entry or a single dense line — but the *fields* are mandatory.

**Why:** Three months from now, you will not remember which function you found this in. The patch-day playbook Step 4 (re-sig with near-miss) needs the original `derived_via` to know what the sig was trying to match. A teammate reviewing your offsets needs `xref_source` to know where to look themselves. The `last_verified` date is the brittleness signal (rule #5).

---

## 3. Sigs Cite the Disassembly They Were Derived From

**A sig alone is a number. A sig with its disassembly context is a hypothesis you can re-derive.** When the sig breaks, the disassembly tells you what the instruction *was*, so you can find what it *became* in the patched binary.

Format: the sig as a literal, then a small fenced block of the instructions it covers, then a one-line explanation of which bytes are wildcarded and why.

```markdown
## E-001 — entity_list (sig derivation)

sig: `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8`

Derived from (game.exe v1.42.3, at .text+0x00872F40):
    48 8D 0D 5B 80 1B 04       LEA  rcx, [rip+0x041B805B]   ; -> &g_entity_list
    E8 2A 4F 12 00             CALL CGameWorld::Lookup       ; ret in rax
    48 8B D8                   MOV  rbx, rax                 ; save list ptr

Wildcards:
  - bytes 3..6   (4-byte RIP disp32 in the LEA — relocatable)
  - bytes 8..11  (4-byte CALL target relative disp — relocatable)
Total signature length: 15 bytes.
Unique-match verdict at derivation time: UNIQUE (margin=5).
```

When this sig later returns 0 after a patch, you have *exactly* what to look for in the new binary: a `LEA rcx, [rip+disp]` immediately followed by a `CALL` and `MOV rbx, rax`, near the same string xref ("entity_list_full") that originally led you here.

**Why:** A bare hex string strips out everything you knew when you wrote it. The disassembly preserves the *intent*: this is the LEA that loads the entity-list pointer into RCX, called immediately. If the compiler changed `MOV` to `LEA` in the patch (different opcode, different sig), you still know what to look for.

---

## 4. Struct Layouts Cite SDK Header AND In-Memory Verification

**Most struct layouts are partially known: some fields come from a community SDK header, others from your own struct dumping, others from guessing. Flag which are which.**

When a struct layout is wrong, the bug is silent — your script reads garbage that doesn't crash. The cost of being wrong is high; the cost of citing your source per field is two lines.

```markdown
## E-004 — CEntity struct layout (partial)

source: `r5sdk/include/game/server/entity.h` (commit 8a4c2e7, fetched 2026-06-10)
in-memory verification: 2026-06-17, walked g_entity_list[0..3] in a live match

| offset  | size | field         | source              | confidence |
|---------|------|---------------|---------------------|------------|
| 0x0000  | 8    | vtable_ptr    | SDK header          | HIGH       |
| 0x0008  | 4    | netvar_id     | SDK header          | HIGH       |
| 0x0040  | 4    | m_iHealth     | SDK header          | HIGH       |
| 0x0044  | 4    | m_iMaxHealth  | SDK header          | HIGH       |
| 0x00F0  | 4    | m_iTeamNum    | SDK header          | HIGH       |
| 0x0170  | 12   | m_vecOrigin   | SDK header          | HIGH       |
| 0x017C  | 12   | m_vecVelocity | OBSERVED (struct dump, three entities, values match expected ranges) | MEDIUM |
| 0x0188  | 4    | m_flAimYaw    | GUESS (correlated with on-screen view direction) | LOW |
| 0x1234  | 8    | m_pPlayerCtl  | GUESS (looks like a pointer; value is within module range) | LOW |
```

Three confidence tiers, three response policies:

- `HIGH` — SDK-cited or directly observed. Use without ceremony.
- `MEDIUM` — observed but not SDK-confirmed. Flag in `offsets.em` with a one-line comment.
- `LOW` — guess. Mark `UNVERIFIED` per `game-cheat-guidelines` rule #1. Treat reads as suspect; cross-validate (e.g. compare the supposed `m_flAimYaw` against the on-screen view direction over 100 frames before trusting it).

When code-reviewing, the question "where did you get this field?" is answered by looking at the table.

**Why:** Partial-layout bugs are the worst class of RE error. The script "works" — it draws ESP, it reads health, it pulls coords — but one field is wrong and the feature using that field silently produces garbage. Marking confidence per field makes the wrong-field call inspectable instead of invisible.

---

## 5. Update the Verified-On Date After Every Successful Run

**The age of the last verification is the brittleness signal. A sig last verified six months ago is more suspect than one verified yesterday, even if both are technically "in the log."**

The discipline: at the end of any session where the script ran correctly against the live target, walk through the log and bump `last_verified` for every claim that was actually exercised. Five seconds of editing per session.

```markdown
## E-001 — entity_list
last_verified: 2026-06-17  ← yesterday, fresh
last_verified: 2026-04-02  ← two months old, recheck before trusting
last_verified: 2025-12-15  ← six months — assume stale; revalidate or re-derive
```

At code-review time or before a release, sort entries by age:

```bash
# rough one-liner — adapt to your log format
grep -E '^last_verified:' evidence/*.md | sort -k2 | head -10
```

The oldest entries are the next ones to verify (or retire if they're no longer used by any feature).

A second related discipline: when you add a NEW claim, also list which claims it *depends on*. If E-006 is "`CEntity::m_pPlayer` reads `CPlayer` at the pointed address" and `CPlayer`'s layout is E-007, then E-006's evidence cites "depends on E-007." When E-007 becomes stale, the dependent claim is suspect too.

**Why:** Without freshness tracking, every entry has the same epistemic weight, which is wrong. A six-month-old "I verified this once" is closer to a guess than to fresh evidence. Dating gives you a triage signal for free, the cost of which is one date edit per session.

---

## 6. Cite Negative Results Too

**"Tried sig X, returned 0; tried sig Y, returned 3 hits; settled on sig Z" is data. Future-you debugging a regression needs to know what's *already been ruled out*.**

Most evidence logs record only the *successful* derivation. The next time the sig breaks and you reach for one of the *other* candidates you ruled out months ago, you'll re-rule it out again — costing the same hour.

Format: under each entry, a brief "Considered and rejected" subsection.

```markdown
## E-001 — entity_list

[main entry as above]

### Considered and rejected
- Sig `48 8B 0D ?? ?? ?? ??` (just the MOV form): too short, matched 47 places in .text.
- Hardcoded offset 0x04A2B100: that's the resolved address from THIS binary; will not
  survive a patch. Kept as the resolved value but the sig is the canonical source.
- Walking from `CGameWorld::Init` (xref candidate): the init function is in .data
  and gets re-inlined per build; brittle xref starting point.
- Reading PEB.LdrData to find a "game module" data segment: technically possible
  but adds a per-frame cost we don't want.
```

The same pattern applies to struct layout dead-ends ("field at +0x180 looked like a vec3 origin but the values were screen-space coords, not world; it's actually the last frame's m_vecOldPosition") and to struct-walking dead-ends ("the second pointer in this list is null in solo play; only populated in team modes — don't use as a liveness check").

**Why:** Negative results are the second-most-valuable thing in the log after positive ones. A teammate looking at this log can immediately see "ah, the obvious short sig is ambiguous — that's why we have a long one." The cost of recording is one line; the cost of not recording is rediscovery.

---

## Template

Drop-in skeleton for `evidence/<hash>.md` — copy, fill in:

```markdown
# Evidence Log — <binary_name> <version>

SHA-256: <full hash>
Module size: <bytes>  (.text <start>–<end>)
First verified: <YYYY-MM-DD>
Last verified: <YYYY-MM-DD>

Cross-reference: this file lists entries E-001..E-NNN; each entry's ID is
stable across patches and is referenced from `offsets.em` and `patch-log.md`.

---

## E-001 — <short name matching offsets.em constant>

| Field             | Value |
|---|---|
| name              | `OFF_X` |
| kind              | <RIP-relative pointer / direct address / field offset / sig> |
| rva               | <0x...> (resolved from sig hit at <0x...>) |
| sig               | `<bytes>` |
| sig_uniqueness    | <UNIQUE margin=N / AMBIGUOUS / etc per sig-uniqueness-checker.py> |
| xref_source       | <function, string xref, or other anchor> |
| derived_via       | <pattern scan + RIP resolve / SDK header / struct dump / xref walk> |
| last_verified     | <YYYY-MM-DD> |
| verified_against  | <in-game observation that confirmed it works> |
| depends_on        | <E-NNN, E-NNN — or "none"> |

Disassembly context (for sigs):
    <4-6 lines of asm covering the matched bytes; wildcards explained below>

Wildcards:
  - bytes A..B  (<what relocatable thing they cover>)

### Considered and rejected
- <alternative sig / approach / source>: <why it didn't pan out>

---

## E-002 — ...
```

A second template for struct entries:

```markdown
## E-NNN — <StructName> layout (<partial|complete>)

source: <SDK header path or "self-derived">
in-memory verification: <date>, <how many instances walked>

| offset | size | field | source | confidence |
|--------|------|-------|--------|------------|
| 0x0000 | 8    | vtable_ptr | SDK / observed | HIGH |
| ...    |      |       |        |            |

### Considered and rejected
- <field-shape alternative>: <why rejected>
```

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | One file per binary, one entry per claim | Stable IDs (E-NNN) cross-reference `offsets.em` and patch logs |
| 2 | Cite binary + address + xref + date | Six fields mandatory per entry; vague memory is not evidence |
| 3 | Sigs cite their disassembly | The intent of the sig is the hypothesis you re-derive from |
| 4 | Structs cite source + verification per field | HIGH / MEDIUM / LOW confidence tiers; LOW = `UNVERIFIED` in code |
| 5 | Update `last_verified` per successful run | Age is the brittleness signal — six months old is suspect |
| 6 | Cite negative results too | "Tried and rejected" prevents the next person re-deriving the same dead end |

**Cross-references:** `skill://pcx-re-discipline` (the discipline rules), `skill://pcx-patch-day-playbook` (Step 7 writes a per-patch log entry), `knowledge/offset-methodology.md` (the mechanics being cited), `tools/sig-uniqueness-checker.py` (produces the `sig_uniqueness` field value), `tools/offset-diff.py` (per-patch diff feeds the negative-results section).
