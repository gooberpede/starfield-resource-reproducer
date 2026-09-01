# Brief 08D.1 — Correct Special insertion ordering before Common guards

## Status

Correction brief for Brief 08D.

This is a narrowly scoped implementation correction. It should be completed **before committing Brief 08D**.

Do not introduce new reverse-engineering hypotheses. The ordering correction is already supported by existing live evidence.

Do not commit or push unless explicitly asked.

---

# Purpose

Correct the per-biome generation order so that a newly selected **Special** resource occupies shared planet resource state **before** the five-tree and shared-eight Common guards are evaluated.

The current implementation selects Special first but delays `PlanetResourceState.record()` until after the Common guard/selection path.

That ordering is inconsistent with the recovered live behavior.

Also make one small reporting robustness improvement: prefer biome index as the primary key when associating occurrences with biome results.

---

# Existing live evidence

## PROVEN LIVE — Special precedes Common state/guard evaluation

The recovered `FUN_1415DCFB0` path establishes:

```text
Special / category 5
    ↓
shared Special append/state update
    ↓
five-tree guard
    ↓
shared-eight guard
    ↓
Common / category 0
```

The Callisto trace is the clearest control case:

```text
Special selector → Helium-3
Helium-3 written to biome Special slot
Helium-3 appended to shared resource state
shared count increments
Common selector → Iron
```

Therefore the Common guard logic must observe any shared-state change caused by the current biome's Special assignment.

The current source ordering is conceptually:

```text
select Special
↓
evaluate Common guards
↓
normal/fallback Common path
↓
record Special into PlanetResourceState
```

That is incorrect.

---

# Required corrected order

Within each shuffled biome invocation, implement the order as:

```text
resolve effective RSGD
↓
run Special selector
↓
if Special selected:
    record Special occurrence immediately
    update shared unique resource state immediately
↓
evaluate five-tree guard
↓
evaluate shared-eight guard
↓
normal Common selector OR guard fallback
↓
Common-family assignment
↓
biome end
```

Do not change the existing ordering of:

```text
five-tree guard
→ shared-eight guard
→ normal Common selector
```

The only required change is moving the Special state/occurrence update to its proven position **before those guards**.

---

# Why this matters

Consider a biome beginning with:

```text
shared occupied unique resource count = 7
```

and whose Special selector chooses a **new** FormID.

Correct engine behavior:

```text
count 7
↓
Special new FormID recorded
↓
count becomes 8
↓
five-tree guard evaluated
↓
shared-eight guard sees 8
↓
normal Common selector is skipped
↓
guard fallback assignment path runs
```

Current incorrect behavior can instead do:

```text
count 7
↓
Special selected but not yet recorded
↓
shared-eight guard still sees 7
↓
normal Common selector runs
↓
Special recorded later
```

This can change:

- Common-selector RNG consumption;
- fallback RNG consumption;
- Common-family assignment mechanism;
- biome-local resources;
- provenance;
- subsequent planet RNG state.

Even if planet-wide final membership remains unchanged, biome-local reproduction can diverge.

---

# Duplicate-Special distinction

The correction must preserve existing shared-state deduplication semantics.

If the selected Special FormID is **already occupied**:

```text
count 7
↓
Special occurrence recorded
↓
occupied_new_slot = false
↓
count remains 7
↓
shared-eight guard does not fire solely because of this Special
```

Therefore tests must distinguish:

```text
new Special identity
vs
already-occupied Special identity
```

Do not special-case by resource name or rarity beyond the existing Special path.

---

# Implementation guidance

Primary likely surface:

```text
src/starfield_resource_reproducer/generation.py
```

Audit the current `_run_planet()` biome loop.

The existing block that records `special_entry.resource` into `PlanetResourceState` should be moved so that it executes immediately after Special selection and **before** Common guard checks.

Preserve:

- `ResourceProvenance.SPECIAL`;
- biome context;
- effective RSGD provenance;
- `SPECIAL_EMITTED` diagnostics;
- `special_resources` behavior;
- occurrence/slot events;
- no extra RNG.

Do not duplicate the Special recording block.

There must still be exactly one Special occurrence record per selected Special resource for that biome.

---

# Diagnostics

Ensure event ordering reflects runtime semantics.

For a biome with a selected Special, diagnostics should make it possible to observe:

```text
SPECIAL_PASS_BEGIN / result
↓
SPECIAL_EMITTED
↓
RESOURCE_OCCURRENCE_RECORDED
↓
RESOURCE_SLOT_OCCUPIED or RESOURCE_SLOT_ALREADY_OCCUPIED
↓
COMMON_TREE_LIMIT_REACHED or COMMON_RESOURCE_CAPACITY_REACHED
   OR normal COMMON_PASS_BEGIN
```

The exact internal event sequence may follow existing event conventions, but the shared-state mutation caused by Special must precede the Common guard event.

Do not claim Special consumes additional RNG beyond its existing selector draw.

---

# Required regression tests

Add focused tests covering at least these cases.

## 1. New Special fills the eighth slot

Synthetic setup:

```text
shared occupied identities before biome = 7
Special selector returns a new FormID
```

Assert:

```text
Special is recorded first
occupied count becomes 8
shared-eight guard fires
normal Common selector is not invoked
no Common-selector RNG draw occurs
guard fallback path is entered
```

If the effective RSGD has Common entries and cached families, assert the resulting fallback behavior using the existing 08D rules.

Most important invariant:

```text
Special draw
→ Special state mutation
→ capacity guard
```

not:

```text
Special draw
→ Common draw
→ Special state mutation
```

## 2. Duplicate Special does not fill the eighth slot

Synthetic setup:

```text
shared occupied identities before biome = 7
Special selector returns a FormID already in occupied state
```

Assert:

```text
Special occurrence is recorded
occupied_new_slot = false
occupied count remains 7
shared-eight guard does not fire solely due to Special
normal Common path remains eligible
```

Any normal Common RNG behavior should follow existing rules.

## 3. Event ordering

Add a focused diagnostic assertion showing that Special state/slot events precede the Common capacity/tree guard or Common selector events.

## 4. No duplicate Special occurrence

Assert the refactor does not cause the Special occurrence to be recorded twice.

---

# Existing regression set

Re-run all Brief 08D focused biome regressions unchanged:

```text
Bara VII-d
Jaffa VII-b
Indum IV-d
Zeta Ophiuchi I
Pyraas VIII-a
```

Expected result:

```text
all 12 CK-observed biome assignments still match
```

Do not modify those expectations to accommodate this correction.

---

# Planet-wide validation

Re-run canonical validation and confirm:

```text
1,444 / 1,444 exact
0 mismatches
0 errors
```

If this changes, investigate before proceeding. Do not weaken the oracle or special-case bodies.

---

# Reporting robustness correction

While making this correction, update biome-centric occurrence aggregation so that **biome index** is the primary association key rather than biome FormID alone.

Reason:

```text
PNDT biome index
```

is the direct per-planet biome-entry identity already carried in occurrence context.

A BIOM FormID may theoretically be reused by more than one PNDT biome entry; a reporting layer should not silently assume BIOM FormID uniqueness within a planet.

Preferred behavior:

```text
match occurrence.biome_index == biome_result.biome.index
```

Optionally also validate FormID consistency when present.

Do not change generation semantics for this reporting refinement.

Add a focused test if practical showing that two biome entries sharing the same BIOM FormID can still be distinguished by biome index.

If the current domain model makes such a synthetic fixture awkward, document the change and cover the actual index-based lookup directly.

---

# Non-goals

Do not:

- alter Special weighted selection;
- alter Common weighted selection;
- alter fallback candidate construction;
- alter fallback RNG;
- alter family-cache semantics;
- alter descendant generation;
- alter Everywhere discovery;
- alter atmosphere handling;
- change five-tree or shared-eight constants;
- add planet-specific heuristics;
- introduce new evidence claims;
- change Brief 08D provenance mechanism names unless needed for consistency.

---

# Documentation

Update only documentation that currently implies or encodes the wrong Special/Common ordering.

The corrected architecture should read:

```text
Atmosphere
    ↓
Everywhere
    ↓
shuffled per-biome generation
    ↓
Special selector
    ↓
Special shared-state update
    ↓
five-tree guard
    ↓
shared-eight guard
    ↓
normal Common selector OR guard fallback assignment
    ↓
descendant generation / cached-family reuse as applicable
```

Preserve evidence labels.

Recommended wording:

> **PROVEN LIVE:** within a biome invocation, a selected Special resource is written/recorded into shared resource state before the five-tree and shared-eight Common guards are evaluated. Therefore a new Special identity can itself raise the shared count to eight and force Common guard fallback for that biome.

---

# Verification

After implementation, run:

1. new 08D.1 focused tests;
2. existing 08D focused tests;
3. full test suite;
4. CK biome regression suite;
5. 1,444-body canonical validation;
6. mojibake guard;
7. `git diff --check`.

Report:

```text
focused tests
full suite
CK biome regressions
canonical validation
mojibake
diff-check
```

Also report whether the change altered any existing RNG draw counts in real regression planets.

---

# Commit guidance

Do not commit automatically.

If all checks remain clean, Brief 08D + 08D.1 may be committed together using the existing suggested message:

```text
feat: add guarded biome family fallback provenance
```

No separate correction commit is necessary unless the user prefers one.

---

# Deliverable

Implement this correction on top of the current uncommitted Brief 08D work and report:

1. exact code changes;
2. tests added/updated;
3. whether any existing 08D behavior changed;
4. full verification results;
5. any new mismatches or OPEN questions;
6. no commit/push unless explicitly requested.
