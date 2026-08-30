# Implementation Brief 05C — Runtime Bounded-Index Conversion Correction

## Context

Repository:

```text
gooberpede/starfield-resource-reproducer
```

Completed work:

```text
00   Project bootstrap
01   Canonical data loaders
02   PRNG compatibility
03   Generation orchestration
04   Family generation
05   Worked-case validation and diagnostics
05A  Zero-candidate RNG investigation
05B  Producer update / zero-candidate runtime resolution
```

Brief 05B established two important runtime rules:

```text
PROVEN:
family-cache hits bypass descendant generation entirely
and consume no descendant RNG.

PROVEN:
a zero-candidate descendant level consumes exactly one raw
MT19937 word, selects no candidate, and leaves the current
structural node unchanged.
```

With the zero-candidate correction applied:

```text
Oberon         exact
Mimas          exact
Decaran VII-b  exact
Kreet          exact
Algorab I      canonical final set exact
```

However, Algorab I remains internally trace-inexact:

```text
live Lead path:
    L1 advances
    L2 advances
    L3 does not advance
    L4 does not advance
    final draw count = 22

current reproducer:
    Lead
    -> Tungsten
    -> Titanium
    -> Dysprosium
    -> empty Unique
    final draw count = 23
```

A new narrow x64dbg trace of Algorab I's Lead L1 descendant call has now isolated the cause.

---

# 1. Goal

Correct the reproducer's generic bounded-index conversion so it matches the runtime implementation observed in `FUN_14157F120`.

The current implementation uses:

```python
raw % upper_bound
```

That interpretation is now disproven for descendant candidate selection.

Brief 05C must:

1. reconstruct the runtime bounded-index conversion from the new Algorab trace;
2. implement the smallest generic correction in the PRNG layer;
3. preserve exact raw MT19937 consumption;
4. revalidate all existing worked cases;
5. determine whether biome shuffling and descendant selection use the same bounded conversion;
6. resolve Algorab I's internal Lead path if the new conversion naturally does so;
7. identify any new mismatches created by the correction;
8. stop before full 1,444-body validation.

Do not introduce planet-, family-, or candidate-specific behavior.

---

# 2. Required Reading

Before editing, read:

```text
AGENTS.md
README.md
docs/ARCHITECTURE.md
docs/BACKLOG.md
docs/DOMAIN-RULES.md
docs/IMPLEMENTATION-WORKFLOW.md

docs/implementation-briefs/02-prng-compatibility.md
docs/implementation-briefs/03-generation-orchestration.md
docs/implementation-briefs/04-family-generation.md
docs/implementation-briefs/05-worked-case-validation.md
docs/implementation-briefs/05A-zero-candidate-rng.md
docs/implementation-briefs/05B-producer-update.md

docs/experiments/05A-kreet-zero-candidate-rng.md
docs/experiments/05B-algorab-lead-branch.md
```

Inspect current implementations of:

```text
src/starfield_resource_reproducer/prng.py
src/starfield_resource_reproducer/generation.py
src/starfield_resource_reproducer/candidates.py
src/starfield_resource_reproducer/diagnostics.py
src/starfield_resource_reproducer/validation.py
```

and all relevant tests.

Do not assume the original Brief 02 bounded-index rule remains valid merely because earlier worked cases passed.

---

# 3. New Live Evidence

## 3.1 Algorab I Lead L1

Planet:

```text
Algorab I
PlanetFormID 0003F599
RSCS         1654436101
```

The relevant runtime biome is:

```text
VolcanicRoughNoLife02
Common root -> Lead
```

The Lead serialized IRES child order is:

```text
Lead
├─ Silver
└─ Tungsten
```

At Lead L1 / Uncommon, the candidate count is:

```text
2
```

The MT19937 raw word used for candidate choice is:

```text
draw 18
raw = 1826241303
hex = 0x6CDA3B17
```

The current reproducer computes:

```text
1826241303 % 2 = 1
```

and therefore chooses:

```text
candidate 1 -> Tungsten
```

The live trace instead produces bounded index:

```text
0
```

The runtime therefore selects candidate slot 0.

This is a discriminating case:

```text
modulo result  = 1
runtime result = 0
```

Therefore:

```text
PROVEN:
raw % upper_bound is not the runtime bounded-index conversion
used by this descendant candidate-selection call.
```

---

# 4. Runtime Conversion Shape

The new trace shows a floating-point scaling/truncation path rather than integer modulo.

The observed behavior is compatible with the conceptual form:

```text
raw uint32
    ↓
convert to unit-range floating value
    ↓
multiply by upper_bound
    ↓
truncate/floor to integer index
```

For the Algorab discriminating draw:

```text
raw / 2^32 ≈ 0.4252

0.4252 * 2 ≈ 0.8504

truncate -> 0
```

which matches runtime.

However, do not implement this approximate expression blindly.

Brief 05C must inspect the existing recovered float-conversion logic and reconstruct the exact bounded conversion at the same precision and operation order used by the engine.

Important existing float behavior:

```python
raw_float = _float32(raw_value)
unit_value = _float32(raw_float * _float32(1.0 / (1 << 32)))
converted = _float32(unit_value * _float32(0.99999))
```

Determine whether bounded-index conversion reuses this exact converted value or follows a related but distinct floating-point path.

Preserve explicit float32 rounding boundaries where the trace/decompiled code requires them.

Do not replace the logic with Python double-precision arithmetic if runtime uses float32 intermediates.

---

# 5. Evidence Status Change

The previous rule:

```text
STRONG:
bounded index = raw % upper_bound
```

must be retired.

Do not leave documentation implying modulo remains a plausible production rule for descendant candidate selection.

Record instead:

```text
PROVEN:
modulo conversion is wrong for the Algorab L1 descendant
candidate-selection call.
```

The exact replacement rule should be marked:

```text
PROVEN
```

only to the degree directly justified by the runtime trace.

If some arithmetic detail remains equivalent over observed values but not uniquely distinguished, mark that detail:

```text
STRONG
```

rather than overstating it.

---

# 6. API / Implementation Requirements

Prefer correcting the existing PRNG abstraction rather than adding candidate-selection arithmetic inside `generation.py`.

Conceptually:

```python
rng.next_index(upper_bound)
```

should remain the caller-facing operation if possible.

The implementation must:

```text
- consume exactly one raw MT word;
- reject invalid upper_bound values as currently appropriate;
- preserve next_index(1) RNG consumption;
- produce runtime-compatible bounded indices;
- expose raw value and resulting index through existing diagnostics.
```

Do not create separate APIs such as:

```text
next_descendant_index()
next_shuffle_index()
next_algorab_index()
```

unless runtime evidence actually establishes distinct conversion mechanisms.

The default assumption should be one generic bounded-index primitive, but Brief 05C must test that assumption rather than force it.

---

# 7. Critical Question: Shuffle Conversion

The previous modulo implementation also reproduced the known Kreet biome shuffle.

That does not prove shuffle uses modulo.

A scaled conversion can coincidentally produce the same observed index for earlier draws.

Therefore explicitly evaluate every known shuffle anchor under the corrected conversion.

Known Kreet behavior:

```text
initial biome order:
[0, 1, 2]

runtime shuffle selections:
first bounded selection  -> 0
second bounded selection -> 0

final order:
[2, 0, 1]
```

Known Algorab forecast/runtime order:

```text
initial:
[0, 1, 2]

final:
[2, 1, 0]
```

Determine whether the corrected generic `next_index()` reproduces all observed shuffle selections.

Possible outcomes:

### Outcome A

```text
scaled conversion reproduces shuffle and descendants
```

Then use one generic corrected bounded-index primitive.

### Outcome B

```text
scaled conversion reproduces descendants but breaks proven shuffle
```

Do not patch around the discrepancy.

Report that runtime likely has two bounded-conversion paths or that the recovered shuffle interpretation needs revision.

If this occurs, request a narrow live shuffle trace before changing production shuffle behavior.

Do not preserve modulo for shuffle merely because it makes tests green.

---

# 8. Algorab Lead Expected Consequence

If the corrected bounded conversion naturally gives:

```text
draw 18 -> index 0
```

then Lead L1 should select:

```text
Silver
```

Given serialized IRES:

```text
Lead
├─ Silver
│  └─ Mercury
└─ Tungsten
   └─ Titanium
      └─ Dysprosium
```

the expected runtime-compatible structural path is:

```text
Lead
-> Silver
-> Mercury
-> empty Exotic
-> empty Unique
```

This matches the live structural shape:

```text
L1 advance
L2 advance
L3 no advance
L4 no advance
```

and, with the Brief 05B zero-candidate rule:

```text
L3 empty -> consume one raw word
L4 empty -> consume one raw word
```

should produce:

```text
final draw count = 22
```

Do not hard-code Silver or Mercury.

The result must arise naturally from:

```text
IRES source order
+ corrected bounded conversion
+ existing candidate construction
+ existing structural traversal
```

---

# 9. Algorab Validation Requirements

After implementing the corrected conversion, rerun Algorab I and report:

```text
shuffle draws/order
Special/Common draws
Uranium first-generation path
Uranium cache-hit behavior
Lead L1 candidates
Lead L1 candidate-index raw/result
Lead L1 selected node
Lead L2 candidates/result
Lead L3 candidate count
Lead L4 candidate count
final draw count
final inorganic set
canonical comparison
```

Expected if the hypothesis is correct:

```text
Lead:
    L1 -> Silver
    L2 -> Mercury
    L3 -> zero candidates
    L4 -> zero candidates

final Algorab draw count:
    22

canonical set:
    Lead
    Uranium
    Iridium

exact final set:
    Yes

trace-exact internal structural shape:
    Yes
```

If any of those fail, report the first divergence precisely.

---

# 10. Kreet Revalidation

Brief 05B made Kreet exact by establishing one raw word per zero-candidate descendant level.

The corrected bounded-index conversion must not be judged solely by whether Kreet's final set remains exact.

Report Kreet's full relevant sequence again, especially:

```text
biome shuffle
Lead L1 candidate set/index/result
Lead L2 candidate set/index/result
Lead Exotic empty draw
Lead Unique empty draw
Argon descendant path
Neon inclusion draw/value
final draw count
```

Current 05B expectation:

```text
Lead Exotic empty:
draw 8 -> 9

Lead Unique empty:
draw 9 -> 10

Neon inclusion:
draw 17
raw = 357224398
roll ≈ 0.08317194879055023
emitted

final Kreet draws:
30
```

If corrected bounded selection changes an earlier structural branch, do not force the old draw numbering.

Report the new truthful sequence.

---

# 11. Mimas / Decaran / Oberon Regression Anchors

Revalidate:

```text
Oberon
Mimas
Decaran VII-b
```

Current expected final sets:

```text
Oberon:
Water
Nickel

Mimas:
Water
Nickel
Palladium

Decaran VII-b:
Helium-3
Uranium
Iridium
Vytinium
```

Mimas is especially important because it proves that:

```text
upper_bound == 1
```

still consumes one raw MT word.

The corrected bounded-index implementation must preserve:

```text
next_index(1) -> 0
```

while advancing the PRNG exactly once.

Report whether all known Mimas inclusion-roll anchors remain at their expected raw draw positions.

---

# 12. Unit Tests for Bounded Conversion

Add focused tests for the bounded-index primitive.

At minimum include the discriminating Algorab case:

```text
raw         = 1826241303
upper_bound = 2
expected    = 0
```

Also preserve a one-candidate case:

```text
upper_bound = 1
expected    = 0
RNG draw consumed = 1
```

Add representative additional cases where useful to guard arithmetic/float32 behavior.

Tests should verify both:

```text
returned index
raw draw advancement
```

Where possible, assert exact intermediate conversion values if they are now evidence-supported.

Do not write tests that merely encode a guessed formula without tying them to runtime evidence.

---

# 13. Diagnostic Requirements

Existing diagnostics should continue to expose bounded choices as something equivalent to:

```text
draw number
raw uint32
upper bound
converted/scaled value if available
selected index
operation
```

If the corrected implementation has useful intermediate float32 values, expose them in structured diagnostics if doing so is small and consistent with current architecture.

Do not add print-only debugging.

The diagnostic output should make future mismatches explainable without rerunning x64dbg immediately.

---

# 14. Candidate Ordering

Do not change IRES source order as part of this brief unless new evidence independently requires it.

Current Lead serialized order is:

```text
Lead -> Silver
Lead -> Tungsten
```

The Algorab trace now provides a direct explanation for the observed Silver branch through corrected index conversion.

Therefore do not reorder to:

```text
Tungsten, Silver
```

merely to fit previous modulo behavior.

Candidate ordering and bounded conversion are separate concerns.

---

# 15. Zero-Candidate Rule

Preserve Brief 05B exactly:

```text
PROVEN:
candidate_count == 0
    -> consume exactly one raw MT19937 word
    -> select no candidate
    -> structural node unchanged
```

Do not reinterpret that raw word as a candidate-index operation merely because bounded-index code is being changed in 05C.

The semantic nature of the empty-level raw advance remains deliberately unspecified.

---

# 16. Family Cache Rule

Preserve:

```text
PROVEN:
a cached family bypasses descendant generation entirely
and consumes no descendant RNG.
```

Algorab's second Uranium biome remains the canonical live control.

Do not reroll or partially traverse descendants on cache hit.

---

# 17. No Full Dataset Validation Yet

Do not begin:

```text
full 1,444-body validation
mismatch clustering
planet-specific edge-case fixes
```

Brief 05C should first establish that the core bounded-index primitive is correct and that all current worked cases remain internally coherent.

Full validation belongs to Brief 06 after this uncertainty is resolved.

---

# 18. No Special Cases

Do not introduce:

```python
if planet == Algorab:
if root == Lead:
if candidate_count == 2:
if raw == 1826241303:
if biome == Volcanic:
```

Do not reorder Lead candidates by name.

Do not consume extra RNG values to restore old draw positions.

Do not preserve modulo in one path merely because a previous test expected it.

All corrected behavior must arise from generic runtime-compatible rules.

---

# 19. Documentation Updates

Update:

```text
docs/DOMAIN-RULES.md
```

to record:

```text
- modulo bounded-index conversion disproven;
- corrected bounded-index rule and evidence status;
- Algorab discriminating draw;
- whether shuffle and descendant selection share the same conversion.
```

Update:

```text
docs/BACKLOG.md
```

to mark the bounded-index uncertainty resolved only if 05C actually establishes the generic rule.

Update:

```text
docs/ARCHITECTURE.md
```

only if the PRNG abstraction/API changes materially.

Update:

```text
README.md
```

only where the documented recovered algorithm or worked-case status is affected.

Create an experiment note such as:

```text
docs/experiments/05C-algorab-bounded-index.md
```

recording at minimum:

```text
Planet
Biome
root
candidate order
raw draw
bound
old modulo result
live runtime result
reconstructed conversion
structural consequence
evidence status
```

---

# 20. Repository Encoding Rule

If not already present, add a concise repository-wide instruction to:

```text
AGENTS.md
```

requiring text files to remain valid UTF-8 and prohibiting accidental mojibake.

The rule should state approximately:

```text
- preserve UTF-8;
- do not introduce encoding-corrupted sequences such as ÔÇö, Ôëê, Ã, â, or �;
- prefer ASCII punctuation if encoding is uncertain;
- do not "fix" intentionally quoted mojibake used in examples/test fixtures;
- inspect modified prose for encoding corruption before completion;
- run git diff --check.
```

This is repository hygiene, not algorithm behavior.

Do not alter intentionally retained mojibake examples in historical implementation briefs where they are explicitly demonstrating the problem.

---

# 21. Tests

Run the complete test suite.

Add/update tests covering:

```text
Algorab discriminating bounded-index case
generic bounded-index conversion
upper_bound == 1 consumption
Algorab Lead internal path
Algorab final draw count
Algorab canonical set
Kreet exactness
Kreet Neon
Mimas anchors
Decaran exactness
Oberon exactness
cache-hit no descendant RNG
zero-candidate one-word consumption
```

If tests that asserted modulo behavior fail, replace them only where the new live evidence disproves the old rule.

Do not weaken unrelated assertions.

---

# 22. Failure Discipline

If the corrected generic bounded conversion does not reproduce all known runtime anchors, stop at the first divergence.

Report:

```text
planet
operation
draw number
raw uint32
upper bound
old modulo result
new scaled result
known runtime result
candidate set
structural consequence
```

Do not attempt multiple speculative corrections in one implementation pass.

A precise new discrepancy is a successful research result.

CK/x64dbg remain available for one further narrow trace if required.

---

# 23. Acceptance Criteria

Brief 05C is complete when:

* [ ] the modulo bounded-index rule is removed from production where disproven;
* [ ] the replacement conversion is based on the Algorab runtime trace;
* [ ] exact raw MT consumption is preserved;
* [ ] `upper_bound == 1` still consumes one raw draw and returns zero;
* [ ] Algorab draw 18 with bound 2 returns index 0;
* [ ] Algorab Lead naturally selects the runtime-compatible first branch without candidate reordering;
* [ ] Algorab structural shape matches `advance, advance, empty, empty`, if supported by the corrected generic rule;
* [ ] Algorab final draw count becomes 22, if no other divergence intervenes;
* [ ] Algorab canonical final set remains exact;
* [ ] Kreet remains exact or any first divergence is reported precisely;
* [ ] Mimas, Decaran VII-b, and Oberon remain exact or any first divergence is reported precisely;
* [ ] shuffle behavior is explicitly checked under the corrected conversion;
* [ ] documentation evidence status is updated accurately;
* [ ] zero-candidate and cache rules from 05B remain intact;
* [ ] no planet/family-specific hacks are introduced;
* [ ] no full-dataset validation is started;
* [ ] repository encoding guidance is added to `AGENTS.md`;
* [ ] `git diff --check` passes apart from known line-ending warnings;
* [ ] full pytest suite passes unless a newly discovered runtime mismatch is truthfully documented;
* [ ] canonical CSV files remain unchanged.

---

# 24. Completion Report

When finished, report:

1. files created;
2. files modified;
3. exact old bounded-index implementation;
4. exact new bounded-index implementation;
5. reconstructed runtime arithmetic and float precision;
6. evidence status of the corrected rule;
7. Algorab draw-18 result;
8. Algorab Lead structural path;
9. Algorab final draw count;
10. Algorab canonical final-set result;
11. Kreet sequence/result/final draws;
12. Mimas result and draw anchors;
13. Decaran VII-b result;
14. Oberon result;
15. whether shuffle still matches all known live observations;
16. whether one generic bounded-index primitive is sufficient;
17. documentation/evidence-status changes;
18. AGENTS.md encoding rule added;
19. test count/results;
20. any requested follow-up x64dbg trace;
21. blockers before Brief 06.

Do not commit or push.

---

## Suggested commit after review

If the implementation is approved:

```text
fix: reproduce bounded RNG selection
```
