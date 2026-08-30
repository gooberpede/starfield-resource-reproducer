# Implementation Brief 03 — Generation Orchestration and Shuffle Transparency

## Context

Repository:

```text
gooberpede/starfield-resource-reproducer
```

Completed phases:

```text
Brief 00 — project bootstrap
Brief 01 — canonical data loading and domain model
Brief 02 — PRNG compatibility layer
```

Brief 03 begins the generation engine, but deliberately stops before descendant-family generation.

The goal is to make the **outer generation control flow** explicit, testable, and diagnostically transparent.

The most important unresolved question entering this brief is:

> How many PRNG draws does biome shuffling consume as a function of biome count, especially for a one-biome planet such as Mimas?

This must not be hidden behind a generic shuffle helper.

---

# 1. Goal

Implement the orchestration layer that:

1. starts from PNDT biome order;
2. uses one evolving `StarfieldRng`;
3. performs the recovered biome shuffle;
4. exposes every shuffle step and raw draw;
5. processes biomes sequentially in shuffled order;
6. resolves effective RSGD;
7. performs only the outer resource-selection passes needed before descendant-family generation;
8. produces structured diagnostic events rather than only final values.

Brief 03 should establish the exact or best-supported RNG call sequence from seed through:

```text
biome ordering
shuffle
Everywhere handling
Special pass
Common/root selection
```

It must **not** yet generate Uncommon/Rare/Exotic/Unique descendants.

---

# 2. Required Pre-Implementation Reading

Before editing, read:

```text
AGENTS.md
README.md
docs/ARCHITECTURE.md
docs/BACKLOG.md
docs/DOMAIN-RULES.md
docs/IMPLEMENTATION-WORKFLOW.md

docs/implementation-briefs/00-project-bootstrap.md
docs/implementation-briefs/01-canonical-data-loader.md
docs/implementation-briefs/02-prng-compatibility.md
```

Inspect the current implementations of:

```text
domain.py
load_data.py
prng.py
```

and all current tests.

Preserve the evidence-status distinctions already recorded.

---

# 3. Evidence Baseline

## 3.1 Initial biome list

**PROVEN for Kreet; STRONG as general rule**

The runtime working biome list is constructed in PNDT `BiomeIndex` order.

Kreet:

```text
initial:
[0, 1, 2]
```

corresponding to:

```text
0 Frozen Volcanic
1 Mountains
2 Volcanic
```

---

## 3.2 Shuffled processing

**PROVEN**

The biome list is shuffled before per-biome generation and then processed sequentially using the same evolving RNG state.

Kreet observed:

```text
initial:
[0, 1, 2]

swap:
0 <-> 1

intermediate:
[1, 0, 2]

swap:
0 <-> 2

final:
[2, 0, 1]
```

The later generator calls occur in:

```text
2, 0, 1
```

order.

---

## 3.3 Kreet PRNG selections

Brief 02 established that the first two raw outputs, when passed through the current STRONG bounded-index interpretation, reproduce the two observed Kreet shuffle selections.

Current compatibility observation:

```text
selection 1 -> 0
selection 2 -> 0
```

which produces:

```text
0 <-> 1
0 <-> 2
```

under the recovered loop behavior.

Do not hard-code these values.

---

## 3.4 Mimas unresolved prefix draw

Mimas:

```text
RSCS = 2008989584
Biome count = 1
```

Brief 02 established:

```text
Common/root probability roll occurs at raw draw 2
```

Therefore:

```text
raw draw 1 is consumed before Common selection
```

The consuming operation is still unresolved.

Plausible possibilities include:

```text
one-biome shuffle still consumes a draw
Special selector consumes a draw despite no match
another pre-Common orchestration call
```

These are hypotheses only.

Brief 03 must not choose one silently.

---

# 4. Primary Research Question: Shuffle Draw Count

This brief must make shuffle behavior explicit enough to answer:

```text
For N biomes, how many raw RNG draws are consumed?
```

At minimum investigate behavior for:

```text
N = 1
N = 2
N = 3
```

using the recovered control flow and canonical planets where useful.

The implementation must expose:

```text
input biome count
loop iteration number
current swap positions
bound passed to next_index()
selected index
raw draw number
raw uint32
resulting order
```

for every shuffle operation.

Do not use Python's built-in `shuffle()`.

Do not implement an opaque helper that returns only the final permutation.

---

# 5. Shuffle Evidence Discipline

Do not call the algorithm "Fisher-Yates" merely because it resembles a standard shuffle.

Use neutral terminology such as:

```text
Starfield biome shuffle
recovered shuffle loop
```

until exact loop semantics are established.

If implementation is based on decompiled/static control flow, comment the exact intended runtime correspondence.

If multiple loop formulations produce Kreet's observed result, retain evidence qualification.

---

# 6. Required Modules

Create or extend as appropriate:

```text
src/starfield_resource_reproducer/
├── generation.py
└── diagnostics.py
```

A small dedicated shuffle helper may live in `generation.py` or a narrowly named internal helper module.

Do not create a generic algorithms utility module.

---

# 7. Structured Diagnostics

Diagnostics are mandatory in Brief 03.

Create a small structured event model rather than scattering print statements.

A reasonable event vocabulary includes:

```text
RNG_SEEDED
BIOME_LIST_INITIAL
SHUFFLE_STEP
BIOME_LIST_SHUFFLED
BIOME_BEGIN
RSGD_RESOLVED
EVERYWHERE_DISCOVERED
SPECIAL_PASS_BEGIN
SPECIAL_PASS_RESULT
COMMON_PASS_BEGIN
COMMON_ROLL
COMMON_SELECTED
BIOME_END
PLANET_ORCHESTRATION_END
```

Exact names may differ.

Every event involving RNG should be able to expose:

```text
raw draw count
raw uint32
converted float/index
operation label
```

Do not build the final CLI renderer yet.

Tests may inspect structured events directly.

---

# 8. Orchestration Result Model

Introduce a partial-generation result that clearly communicates that descendants are not yet implemented.

For example:

```text
PlanetOrchestrationResult
BiomeOrchestrationResult
```

A biome-level result may contain:

```text
biome
effective_rsgd
special_selection
common_root
events
```

Do not call this a complete `GenerationResult` if it does not yet represent descendant resources.

Avoid APIs that make Brief 03 outputs look final.

---

# 9. Effective RSGD

Use the existing proven domain rule:

```text
if PNDT RSGD exists:
    use PNDT
else:
    use BIOM
```

Do not re-implement or duplicate precedence logic if `Biome.effective_rsgd` already provides it.

Diagnostics should report:

```text
biome
chosen RSGD
source = PNDT or BIOM
```

Kreet must expose the two ordinary PNDT override cases correctly.

---

# 10. Everywhere Handling Scope

Water / category 6 is known to be populated upstream of the traced per-biome generator.

The exact upstream insertion routine is unresolved.

Brief 03 should therefore model Everywhere handling transparently and provisionally.

Preferred behavior:

1. inspect applicable static generation data;
2. identify Everywhere entries;
3. record them as upstream/provisional resources;
4. emit an explicit diagnostic event;
5. do not pretend they were selected by the per-biome Common/Special selector.

Mark this behavior:

```text
PROVISIONAL
```

unless current evidence justifies a more precise rule.

Do not hard-code:

```text
add Water to every planet
```

Use the generation data.

Do not attempt final canonical output comparison yet.

---

# 11. Special Pass

Implement the category-5/Special outer pass only to the extent supported by current evidence.

Known:

```text
Helium-3 = Special
```

The per-biome generator performs a Special pass before Common selection.

The selector should use the same ordered cumulative behavior as the recovered category selector where applicable.

However, Brief 03 must pay special attention to **RNG consumption when no Special entry matches**.

This is directly relevant to the unresolved Mimas raw draw 1.

Diagnostics must make clear whether:

```text
Special pass:
    consumed RNG
or
    consumed no RNG
```

and why.

Do not insert dummy draws to align Mimas.

The implementation should follow recovered selector/control-flow semantics.

If static/decompiled evidence remains insufficient to determine no-match behavior, encode the ambiguity explicitly and stop short of falsely claiming exact orchestration.

---

# 12. Common/Root Selection

Implement the already-proven Common selector:

```text
eligible category = Common
iterate in RSGDResourceIndex order
cumulative += CommonChance / 100
first cumulative threshold greater than roll wins
```

Do not normalize weights.

Use the existing PRNG float method.

Preserve exact RSGD order.

Diagnostics should include:

```text
raw draw number
roll
eligible entries
entry order
entry weight
cumulative thresholds
winner
```

Do not emit descendants.

The selected Common root is a structural/orchestration result only at this stage.

---

# 13. No Descendant Generation

Brief 03 must stop immediately after Common/root selection for each biome.

Do not implement:

```text
Uncommon traversal
Rare traversal
Exotic traversal
Unique traversal
candidate building
inclusion rolls
candidate-index rolls
family cache
emitted descendant resources
```

Those belong to Brief 04.

---

# 14. One Shared RNG Instance

For one planet orchestration:

```text
one StarfieldRng
```

must be created from RSCS and then passed through:

```text
shuffle
Special pass
Common pass
later biomes
```

Do not reseed per biome.

Do not create separate RNG instances for selection categories.

This is a PROVEN architectural rule.

---

# 15. Shuffle Implementation Requirements

Implement the recovered loop as literally as evidence allows.

The code should be auditable against runtime behavior.

For every iteration, diagnostics must show something conceptually like:

```text
SHUFFLE_STEP
iteration = 0
source_position = ?
bound = ?
selected_index = ?
swap_left = ?
swap_right = ?
draw = 1
```

The exact fields should match the actual recovered loop, not this placeholder.

For Kreet, tests must assert:

```text
initial [0,1,2]
first swap 0<->1
second swap 0<->2
final [2,0,1]
```

and the raw draw numbers used.

---

# 16. One-Biome Transparency

Mimas is a mandatory orchestration test.

The result must clearly answer:

```text
Did the shuffle layer consume raw draw 1?
```

If yes, record:

```text
why the recovered loop executes for N=1
what bound is used
what index is returned
what no-op/self-swap occurs
```

If no, diagnostics must show what later operation consumes draw 1 before the known Common roll.

Do not optimize away a one-biome shuffle step merely because it appears wasteful.

Runtime compatibility takes priority over efficiency.

---

# 17. Suggested Investigation Logic for N=1,2,3

Do not introduce synthetic behavior into production merely for testing, but tests may exercise the shuffle helper directly with lists of lengths:

```text
1
2
3
```

and a fixed RNG.

The purpose is to characterize:

```text
number of raw draws
bounds requested
swap positions
```

This should make the implementation's loop semantics obvious.

If the recovered loop implies:

```text
N draws
N-1 draws
or another count
```

document it explicitly.

---

# 18. Known Planet Tests

## 18.1 Kreet

Required:

```text
initial biome order:
[0,1,2]

shuffle swaps:
0<->1
0<->2

final:
[2,0,1]
```

Then process in:

```text
Volcanic
Frozen Volcanic
Mountains
```

Effective RSGDs:

```text
Volcanic:
PNDT VolcanicDefaultRes_Kreet

Frozen Volcanic:
BIOM FrozenBarrenDefaultRes

Mountains:
PNDT MountainDefaultRes_Kreet
```

Expected Common roots:

```text
Volcanic        -> Lead
Frozen Volcanic -> Argon
Mountains       -> Iron
```

Do not require descendants yet.

---

## 18.2 Mimas

Required:

```text
Biome count: 1
Effective RSGD: FrozenBarrenDefaultRes03
```

Expected Common root:

```text
Nickel
```

Known Common roll:

```text
0.561107993...
```

The orchestration diagnostics must account for the raw draw before it.

This is a central acceptance criterion.

---

## 18.3 Decaran VII-b

Required:

```text
Biome count: 1
Effective RSGD:
PNDT UniqueCrateredBarrenVytiniumRes
```

Expected outer selections:

```text
Special -> Helium-3
Common  -> Uranium
```

Do not generate Iridium/Vytinium yet.

Use this case to test Special + Common sequencing on a one-biome planet.

Its draw sequence may help distinguish Mimas's unexplained prefix behavior.

---

## 18.4 Oberon

Required:

```text
Biome count: 1
Effective RSGD:
known BIOM default
```

Expected Common root:

```text
Nickel
```

Everywhere handling should identify Water separately from Common.

Do not generate descendants.

---

# 19. Selector Failure / No-Match Transparency

Tests should explicitly characterize what happens when a category has:

```text
zero eligible entries
```

At minimum for Special.

The diagnostic output must show:

```text
eligible_count = 0
rng_consumed = yes/no
```

based on implementation/evidence.

Do not silently return `None` without documenting consumption behavior.

This is likely relevant to Mimas.

---

# 20. Weighted Selector Helper

A small internal selector helper is appropriate if it:

- preserves ordered entries;
- accepts requested generation category/chance field;
- exposes diagnostic detail;
- makes RNG consumption explicit.

Do not generalize it into a broad probability library.

Do not normalize weights.

If no candidate exists, its behavior must follow recovered runtime semantics, not a convenient Python convention.

---

# 21. Evidence Labels in Code

Use comments such as:

```python
# PROVEN: Kreet's working biome array is populated in BiomeIndex order.
```

```python
# STRONG: this shuffle loop reproduces the exact two Kreet swaps; broader
# semantics for all biome counts remain under validation.
```

```python
# PROVISIONAL: Everywhere resources are modeled upstream from static data
# because the exact insertion routine has not yet been identified.
```

Do not overstate Mimas draw-1 resolution unless Brief 03 genuinely establishes it.

---

# 22. Documentation Update Requirement

If Brief 03 determines the shuffle draw-count rule, update:

```text
docs/DOMAIN-RULES.md
```

with a dedicated section such as:

```text
Biome Shuffle RNG Consumption
```

State:

```text
for N biomes, number of raw draws = ...
```

only if supported.

If N=1 behavior is established, record it explicitly.

If still unresolved, say so.

Also update:

```text
docs/BACKLOG.md
```

for genuinely completed orchestration items.

Update:

```text
docs/ARCHITECTURE.md
```

if the orchestration/diagnostic boundary materially changes.

---

# 23. Tests

Suggested new tests:

```text
tests/test_shuffle.py
tests/test_orchestration_mimas.py
tests/test_orchestration_kreet.py
tests/test_orchestration_decaran.py
tests/test_orchestration_oberon.py
```

Exact split is up to Codex.

Tests should inspect structured events rather than captured print output.

Keep Brief 00–02 tests passing.

---

# 24. Failure Conditions

Do not force Brief 03 green if Mimas draw 1 cannot be naturally explained.

If orchestration produces:

```text
Common roll at wrong raw draw
```

report:

```text
expected draw
actual draw
preceding operations
their consumption
```

Do not:

```text
skip RNG values
insert dummy calls
special-case Mimas
manually align state
```

A precise mismatch is a valid research result.

---

# 25. Acceptance Criteria

Brief 03 is complete when:

- [ ] outer generation orchestration exists in `generation.py`.
- [ ] one shared `StarfieldRng` is used per planet.
- [ ] initial biome order is preserved from `BiomeIndex`.
- [ ] shuffle behavior is explicit and structured.
- [ ] every shuffle step records raw draw count and swap details.
- [ ] Kreet's exact two observed swaps are reproduced.
- [ ] Kreet processing order is `[2,0,1]`.
- [ ] effective RSGD selection is reported correctly.
- [ ] Everywhere handling is explicit and evidence-qualified.
- [ ] Special pass exists with transparent no-match RNG behavior.
- [ ] Common selector preserves RSGD order and does not normalize weights.
- [ ] Mimas selects Nickel with the known live roll.
- [ ] the operation consuming raw draw 1 before Mimas Common is identified, or the unresolved divergence is reported precisely.
- [ ] Decaran outer selections produce Helium-3 and Uranium.
- [ ] Oberon identifies Water separately and selects Nickel.
- [ ] no descendant-family generation exists yet.
- [ ] no family cache exists yet.
- [ ] structured diagnostic events are testable without CLI parsing.
- [ ] full existing test suite passes unless a documented unresolved orchestration mismatch prevents truthful completion.
- [ ] canonical CSVs remain unchanged.
- [ ] code-commenting standards are followed.

---

# 26. Completion Report

Codex should report:

1. files created;
2. files modified;
3. orchestration API introduced;
4. diagnostic event model;
5. exact implemented shuffle loop;
6. shuffle raw-draw count for N=1, N=2, N=3;
7. Kreet swap sequence and draw numbers;
8. Mimas pre-Common draw explanation;
9. Mimas Common draw number/value;
10. Special no-match RNG behavior;
11. Decaran Special/Common sequence;
12. Oberon Everywhere/Common behavior;
13. evidence-status updates;
14. test count/results;
15. unresolved questions before Brief 04.

Do not begin descendant-family generation automatically.

---

# 27. Commit Guidance

Suggested commit:

```text
feat: add generation orchestration
```

If documentation findings are substantial, optional separate commit:

```text
docs: record shuffle orchestration findings
```

Track this brief under:

```text
docs/implementation-briefs/03-generation-orchestration.md
```

---

## Next Planned Brief

Brief 04 will add:

```text
Common root emission
Uncommon/Rare/Exotic/Unique traversal
IRES candidate construction
inclusion draws
candidate-index draws
structural continuation
family cache
```

using the exact orchestration/RNG sequence established here.
