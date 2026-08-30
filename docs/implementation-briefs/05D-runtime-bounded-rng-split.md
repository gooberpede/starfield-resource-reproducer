# Implementation Brief 05D — Split Runtime Bounded-RNG Semantics

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
05C  Bounded-index path divergence investigation
```

Brief 05C established that one generic bounded-index conversion is not runtime-correct.

Subsequent live x64dbg traces resolved the apparent contradiction.

Two distinct runtime bounded-choice mechanisms are now established:

```text
Biome shuffle
    -> dedicated integer bounded-RNG helper
    -> rejection sampling
    -> modulo after acceptance

Descendant candidate selection
    -> probability-style float32 conversion
    -> multiply by candidate count
    -> truncate/floor
```

These are intentionally different runtime mechanisms and must remain distinct in the reproducer.

A future maintainer must not collapse them into one generic `next_index()` implementation merely because they often produce the same answer.

---

# 1. Goal

Implement the runtime-proven split between:

1. integer bounded selection used by biome shuffling; and
2. float-scaled candidate selection used by descendant-family generation.

Brief 05D must:

- reproduce both mechanisms independently;
- make their semantic distinction explicit in code and documentation;
- preserve exact MT19937 raw-draw consumption;
- bring Algorab I into internal trace agreement;
- preserve Kreet's proven shuffle;
- preserve the Brief 05B zero-candidate and cache rules;
- remove the current strict expected failure for Algorab if the corrected implementation resolves it;
- rerun all worked cases;
- stop before full 1,444-body validation.

Do not introduce planet-, family-, biome-, or resource-specific behavior.

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
docs/implementation-briefs/05C-bounded-index-conversion-correction.md

docs/experiments/05A-kreet-zero-candidate-rng.md
docs/experiments/05B-algorab-lead-branch.md
docs/experiments/05C-algorab-bounded-index.md
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

---

# 3. Evidence Summary

## 3.1 Descendant candidate selection — PROVEN

Algorab I, Lead L1:

```text
candidate order:
    0 Silver
    1 Tungsten

raw MT draw:
    draw 18
    raw = 1826241303
    hex = 0x6CDA3B17

candidate count:
    2
```

Modulo would produce:

```text
1826241303 % 2 = 1
```

but runtime produces candidate index:

```text
0
```

The live instruction path shows float32 scaling/truncation consistent with:

```text
raw uint32
    ↓
float32(raw)
    ↓
float32(raw_float * float32(2^-32))
    ↓
float32(unit * float32(0.99999))
    ↓
float32(probability * float32(candidate_count))
    ↓
truncate
```

For Algorab:

```text
scaled ≈ 0.85040134
truncate -> 0
```

Therefore:

```text
PROVEN:
descendant candidate selection is not modulo-based.
```

The runtime-compatible conceptual operation is:

```text
candidate_index = trunc(probability_float32 * candidate_count)
```

using the recovered float32 probability conversion.

---

## 3.2 Biome shuffle selection — PROVEN separate path

Kreet biome shuffling calls a dedicated helper path.

Observed helper chain:

```text
FUN_14152CBC0
    ↓
0x1401714A8
    ↓
bounded helper thunk 0x14001D63D
    ↓
implementation around 0x141587240
```

Kreet live draws:

```text
draw 1:
    raw   = 3789400562
    bound = 2
    result = 0

draw 2:
    raw   = 3546750279
    bound = 3
    result = 0
```

The bounded helper uses integer rejection sampling and returns the accepted raw value modulo the bound.

The trace shows logic equivalent in ordinary 32-bit-bound terms to:

```text
repeat:
    raw = next_uint32()

    quotient_threshold = UINT32_MAX // bound
    quotient_random = raw // bound

until quotient_random < quotient_threshold

return raw % bound
```

The exact implementation may contain wider-range/general-purpose machinery, but the observed 32-bit behavior above is the runtime rule relevant to current biome shuffling.

Critically:

```text
PROVEN:
one biome-shuffle bounded choice may consume MORE THAN ONE MT word
if rejection occurs.
```

For the observed Kreet choices, no rejection occurs.

---

# 4. Required Design Principle

The reproducer must explicitly preserve the fact that Bethesda uses two different random-selection idioms.

Do not hide this behind one generic operation such as:

```python
next_index(bound)
```

unless the API itself requires the caller to specify which runtime mechanism is intended.

Preferred design is two semantically distinct PRNG operations, for example:

```python
next_bounded_integer(bound)
next_scaled_index(bound)
```

Exact names may differ, but they must communicate the distinction.

The code should make clear:

```text
next_bounded_integer
    -> integer rejection-sampling distribution
    -> used by biome shuffle

next_scaled_index
    -> float32 probability scaling/truncation
    -> used by descendant candidate selection
```

Do not name them after planets or tests.

Avoid names so generic that a future maintainer could reasonably assume they are interchangeable.

---

# 5. Mandatory Code Commentary

Add concise comments/docstrings explaining WHY both mechanisms exist in the reproducer.

The comments should convey approximately:

```text
PROVEN: Starfield uses two distinct bounded-random mechanisms here.

Biome shuffling calls a generic integer bounded-RNG helper that uses
rejection sampling before modulo.

Descendant resource candidate selection instead converts the MT19937
word through the engine's float32 probability path, scales by candidate
count, and truncates.

These operations are not interchangeable. Do not consolidate them into
one generic bounded-index helper without new runtime evidence.
```

This distinction must be visible at:

- the PRNG abstraction;
- the biome-shuffle call site; and
- the descendant candidate-selection call site.

Avoid comments that merely restate syntax.

The goal is to prevent a future programmer from "simplifying" the two paths into one.

---

# 6. Integer Shuffle-Bounded Operation

Implement the runtime-compatible integer bounded helper for biome shuffling.

Requirements:

```text
- upper_bound must be > 0;
- each attempt consumes one raw MT19937 word;
- rejected values consume additional raw words;
- accepted result is raw % upper_bound;
- upper_bound == 1 must still consume RNG according to the traced/general helper semantics;
- raw draw count must reflect every rejected and accepted word.
```

Do not implement simple modulo without rejection.

Do not use Python `random.randrange()` or another opaque distribution helper.

Keep the algorithm explicit and auditable.

If the exact rejection inequality requires careful reproduction from the trace, document it and test the boundary explicitly.

---

# 7. Integer Rejection Boundary Tests

Add focused unit tests for the integer bounded helper.

At minimum cover:

### Kreet bound-2 live anchor

```text
raw   = 3789400562
bound = 2
result = 0
```

### Kreet bound-3 live anchor

```text
raw   = 3546750279
bound = 3
result = 0
```

### Rejection case

Construct or locate a raw value inside the helper's rejection region for a small bound where modulo bias exists.

Verify:

```text
first raw:
    rejected

second raw:
    accepted

raw draw count:
    advances twice

returned index:
    accepted_raw % bound
```

The rejection test must exercise actual production helper logic rather than merely testing a duplicate formula in the test.

### Bound 1

Verify the appropriate raw consumption and result:

```text
result = 0
```

without short-circuiting the MT draw.

---

# 8. Float-Scaled Descendant Operation

Implement the runtime-compatible descendant candidate selector separately.

Use the existing recovered probability conversion:

```python
raw_float = _float32(raw_value)
unit_value = _float32(
    raw_float * _float32(1.0 / (1 << 32))
)
probability = _float32(
    unit_value * _float32(0.99999)
)
```

Then:

```python
scaled = _float32(
    probability * _float32(upper_bound)
)
index = trunc(scaled)
```

Preserve float32 rounding boundaries.

Do not substitute Python double-precision arithmetic where the runtime path uses float32 intermediates.

Each normal descendant candidate selection with candidates present consumes exactly one raw MT word.

---

# 9. Algorab I Required Result

Under the corrected descendant mechanism:

```text
Lead L1 candidates:
    Silver
    Tungsten

draw 18:
    raw = 1826241303
    bound = 2
    scaled index = 0

selected:
    Silver
```

The generic IRES traversal should then naturally produce:

```text
Lead
-> Silver
-> Mercury
-> empty Exotic
-> empty Unique
```

Required structural shape:

```text
L1 advance
L2 advance
L3 unchanged
L4 unchanged
```

Required draw count:

```text
22
```

Required canonical inorganic set:

```text
Lead
Uranium
Iridium
```

The final set must remain exact.

Do not hard-code Silver or Mercury.

The result must arise from:

```text
IRES source order
+ scaled descendant candidate selection
+ existing structural traversal
+ existing zero-candidate rule
```

---

# 10. Remove the Algorab Expected Failure

Brief 05C intentionally retained production modulo and added a strict expected failure documenting the live Algorab mismatch.

If 05D correctly resolves that mismatch:

- remove the strict expected failure;
- replace it with an ordinary passing regression test;
- assert the live candidate index;
- assert the Lead structural path;
- assert final draw count 22;
- assert final canonical set equality.

Do not leave obsolete tests implying the mismatch remains unresolved.

---

# 11. Kreet Shuffle Required Result

Biome shuffle must call the new integer rejection-sampled helper, not the float-scaled descendant helper.

Kreet must continue to reproduce:

```text
initial:
[0, 1, 2]

draw 1:
raw   3789400562
bound 2
index 0

draw 2:
raw   3546750279
bound 3
index 0

final:
[2, 0, 1]
```

No rejection occurs for those two known draws.

Do not alter the established shuffle loop merely because the bounded helper is changing.

---

# 12. Kreet Full Generation Regression

Revalidate the complete Kreet sequence.

Brief 05B established:

```text
Lead Exotic empty:
    consumes one raw word

Lead Unique empty:
    consumes one raw word

Neon inclusion:
    draw 17
    raw = 357224398
    roll ≈ 0.08317194879055023
    emitted
```

Current final draw count:

```text
30
```

Expected final set:

```text
Argon
Iron
Lead
Water
Neon
Alkanes
Silver
```

The corrected split should preserve this unless a newly discovered generic consequence changes a later path.

If anything diverges, report the first divergence rather than forcing the old sequence.

---

# 13. Mimas Regression

Expected:

```text
Water
Nickel
Palladium
```

Final draw count:

```text
10
```

Preserve descendant anchors:

```text
L1 inclusion ≈ 0.894184828
L2 inclusion ≈ 0.686025143
L3 inclusion ≈ 0.108883217
L4 inclusion ≈ 0.818136036
```

One-candidate descendant choice still consumes exactly one raw word through the float-scaled descendant path.

Do not replace that with the integer shuffle helper merely because the result is always zero.

---

# 14. Decaran VII-b Regression

Expected:

```text
Helium-3
Uranium
Iridium
Vytinium
```

Final draw count:

```text
10
```

Preserve all existing PNDT override and family-generation behavior.

---

# 15. Oberon Regression

Expected:

```text
Water
Nickel
```

Final draw count:

```text
10
```

Preserve existing Everywhere handling and family generation.

---

# 16. Algorab Uranium Cache Regression

Preserve Brief 05B:

```text
PROVEN:
when the second Algorab biome selects Uranium again,
the cached family is reused;
FUN_14157F120 is bypassed;
no descendant RNG is consumed.
```

Do not allow the PRNG refactor to accidentally rerun descendant generation.

---

# 17. Zero-Candidate Rule

Preserve exactly:

```text
PROVEN:
candidate_count == 0
    -> consume exactly one raw MT19937 word
    -> select no candidate
    -> structural node unchanged
```

Do not route zero-candidate levels through either bounded-selection helper.

Do not assign speculative "scaled index" or "integer bounded choice" semantics to this raw advance.

Its semantic purpose remains deliberately unspecified.

---

# 18. Diagnostics

Update structured diagnostics so bounded RNG operations identify the mechanism used.

Prefer an explicit field/value such as:

```text
operation = shuffle_bounded_integer
operation = descendant_scaled_index
```

or equivalent structured terminology.

For integer shuffle choices, diagnostics should expose where practical:

```text
draw number(s)
raw uint32
bound
accepted/rejected
selected index
```

If rejection occurs, every attempted raw value should be inspectable.

For descendant scaled choices, expose:

```text
draw number
raw uint32
probability float32
bound
scaled float32
selected index
```

Do not create print-only debug paths.

---

# 19. PRNG Architecture

Keep raw MT19937 generation shared.

Conceptually:

```text
                MT19937 raw uint32
                       |
        +--------------+--------------+
        |                             |
integer bounded path          probability float path
        |                             |
rejection + modulo          float32 probability
        |                             |
biome shuffle             +-----------+-----------+
                          |                       |
                    inclusion rolls       scaled candidate index
```

This distinction should be reflected cleanly in `prng.py`.

Do not duplicate the MT generator itself.

---

# 20. Evidence Status Documentation

Update:

```text
docs/DOMAIN-RULES.md
```

to record:

### Biome shuffle

```text
PROVEN:
uses a dedicated integer bounded-RNG helper with rejection sampling
and modulo after acceptance.
```

### Descendant candidate selection

```text
PROVEN:
uses float32 probability conversion, scaling by candidate count,
and truncation.
```

### Important distinction

Explicitly state:

```text
These two mechanisms are not interchangeable.
```

Update:

```text
docs/BACKLOG.md
```

to mark the bounded-selection-path divergence resolved if all required tests pass.

Update:

```text
docs/ARCHITECTURE.md
```

to show the split PRNG conversion paths if the current architecture diagram implies one generic bounded-index operation.

Update:

```text
README.md
```

only where its algorithm summary currently implies a single bounded-index primitive.

---

# 21. Experiment Record

Create:

```text
docs/experiments/05D-runtime-bounded-rng-split.md
```

Record the evidence chain:

```text
Algorab descendant trace
    -> modulo disproven
    -> float scaling observed

Kreet shuffle trace
    -> dedicated helper identified

Kreet bounded-helper trace
    -> integer rejection sampling observed
    -> modulo after acceptance
```

Include:

```text
relevant addresses
known raw values
bounds
returned indices
evidence statuses
production consequence
```

Make clear that the addresses are runtime/build-specific evidence anchors, not production logic.

---

# 22. Do Not Overgeneralize Motivation

Code/documentation may explain the mechanical distinction, but do not state speculative Bethesda design intent as fact.

Do not write assertions such as:

```text
Bethesda deliberately chose the integer helper because...
```

unless explicitly labeled inference.

The reproducer needs to copy runtime semantics, not reconstruct developer intent.

---

# 23. No Full Dataset Validation Yet

Do not begin:

```text
full 1,444-body validation
mismatch clustering
planet-specific repairs
```

Brief 05D is the final worked-case/runtime-semantics correction before Brief 06.

Full validation begins only after this split is implemented and all current worked cases are coherent.

---

# 24. No Special Cases

Do not add logic such as:

```python
if planet == "Kreet":
if planet == "Algorab I":
if root == "Lead":
if upper_bound == 2:
if operation == "shuffle" and raw == ...:
```

The distinction must be semantic:

```text
shuffle operation
vs
descendant candidate operation
```

not data-specific.

---

# 25. Required Tests

Run the complete suite.

Add/update tests covering at minimum:

```text
integer bounded helper:
    Kreet bound-2 anchor
    Kreet bound-3 anchor
    explicit rejection case
    bound 1 consumption

scaled descendant helper:
    Algorab draw-18 index 0
    single-candidate consumption
    float32 intermediate behavior where useful

Algorab:
    Silver branch
    Mercury continuation
    L3 empty
    L4 empty
    final draw 22
    canonical exact

Kreet:
    shuffle [2,0,1]
    exact generation
    Neon draw 17
    final draw 30

Mimas:
    exact final set
    10 draws
    inclusion anchors

Decaran VII-b:
    exact
    10 draws

Oberon:
    exact
    10 draws

cache:
    no descendant RNG on hit

zero candidate:
    exactly one raw word
    structural node unchanged
```

Remove or revise tests that encode the now-disproven idea of one generic bounded-index mechanism.

---

# 26. Failure Discipline

If the split implementation causes a mismatch, report the first divergence precisely.

Include:

```text
planet
operation type
draw number
raw uint32
bound
conversion mechanism
expected result
actual result
candidate set if applicable
structural consequence
```

Do not add compensating draws or special cases.

A precise mismatch is preferable to a false pass.

CK/x64dbg remain available if one further narrow trace is genuinely required.

---

# 27. Acceptance Criteria

Brief 05D is complete when:

- [ ] biome shuffle uses the integer rejection-sampled bounded helper;
- [ ] descendant candidate selection uses the float32 scaled-index helper;
- [ ] both mechanisms are explicitly distinct in code naming/commentary;
- [ ] code warns maintainers not to consolidate the two without new runtime evidence;
- [ ] integer rejection can consume multiple raw MT words;
- [ ] diagnostics can expose rejection attempts;
- [ ] Kreet shuffle remains `[2,0,1]`;
- [ ] Algorab draw 18 returns descendant index 0;
- [ ] Algorab naturally follows Lead -> Silver -> Mercury -> empty -> empty;
- [ ] Algorab final draw count is 22;
- [ ] Algorab canonical set remains exact;
- [ ] the 05C Algorab expected failure is removed/replaced with a passing regression;
- [ ] Kreet remains exact and ends at draw 30;
- [ ] Mimas remains exact at 10 draws;
- [ ] Decaran VII-b remains exact at 10 draws;
- [ ] Oberon remains exact at 10 draws;
- [ ] cache-hit behavior from 05B remains intact;
- [ ] zero-candidate behavior from 05B remains intact;
- [ ] documentation records the two mechanisms separately;
- [ ] an 05D experiment record is created;
- [ ] no planet/family-specific hacks are introduced;
- [ ] full-dataset validation is not started;
- [ ] `git diff --check` passes apart from known line-ending warnings;
- [ ] mojibake scan passes for newly authored/modified prose, excluding intentionally quoted historical examples;
- [ ] full pytest suite passes;
- [ ] canonical CSV files remain unchanged.

---

# 28. Completion Report

When finished, report:

1. files created;
2. files modified;
3. exact integer bounded helper implementation;
4. exact descendant scaled-index implementation;
5. how code distinguishes the two semantics;
6. integer rejection-test result and raw-draw consumption;
7. Kreet shuffle result;
8. Kreet full generation result/final draws;
9. Algorab draw-18 result;
10. Algorab Lead structural path;
11. Algorab final draw count;
12. Algorab canonical result;
13. Mimas result/draw anchors;
14. Decaran VII-b result;
15. Oberon result;
16. cache-hit regression result;
17. zero-candidate regression result;
18. documentation/evidence-status changes;
19. test count/results;
20. whether any x64dbg follow-up is requested;
21. blockers before Brief 06.

Do not commit or push.

---

## Suggested commit after review

If approved:

```text
fix: reproduce distinct bounded RNG paths
```
