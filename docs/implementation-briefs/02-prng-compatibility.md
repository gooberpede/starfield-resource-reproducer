# Implementation Brief 02 — PRNG Compatibility Harness

## Context

Repository:

```text
gooberpede/starfield-resource-reproducer
```

Brief 00 established the Python project scaffold.

Brief 01 established:

```text
src/starfield_resource_reproducer/domain.py
src/starfield_resource_reproducer/load_data.py
```

and validated the three canonical datasets.

Brief 02 is intentionally isolated from resource-generation logic.

Its purpose is to recover and encode the **exact observable pseudo-random interface** used by Starfield's planetary resource-generation path.

The target is not merely:

```text
"uses MT19937"
```

The target is:

```text
same unsigned seed
same MT19937 state evolution
same integer outputs
same float conversion
same bounded-index conversion
same draw consumption
same observable values at the same points
```

A statistically equivalent implementation is insufficient.

---

# 1. Goal

Implement a small PRNG compatibility layer and test harness that can reproduce known live Starfield/Creation Kit trace values exactly enough to support later deterministic generation work.

After Brief 02, the project should have a reusable PRNG abstraction that future generation code can depend on without knowing the implementation details of MT19937 or output conversion.

Brief 02 should answer, with tests:

1. How is `RSCS` applied as a 32-bit seed?
2. How are MT19937 outputs converted into the floating-point values used by weighted/inclusion checks?
3. How are bounded integer/index selections derived?
4. How are draws counted and exposed for diagnostics?
5. Can the implementation reproduce the known Mimas and Kreet live-trace anchors?

Do not implement resource-generation behavior yet.

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
```

Inspect the current implementation and tests before editing.

Treat `docs/DOMAIN-RULES.md` as authoritative for evidence status.

Do not change recovered Starfield behavior merely to make a familiar PRNG API fit.

---

# 3. Evidence Baseline

## 3.1 Seed behavior

**PROVEN**

For nonzero PNDT Resource Creation Seed:

```text
RSCS
  ->
unsigned 32-bit seed
  ->
MT19937
```

Do not reinterpret RSCS as signed.

Examples:

```text
Mimas RSCS = 2008989584
Kreet RSCS = 2842708811
```

The second value is greater than signed 32-bit maximum and must remain:

```text
2842708811
```

not a negative integer.

---

## 3.2 Same evolving state

**PROVEN**

Biome shuffle and later generation consume the same evolving PRNG state.

Therefore Brief 02 must support deterministic sequential draw accounting.

Do not provide independent hidden RNG instances for:

```text
shuffle
root selection
descendant generation
```

unless future evidence explicitly establishes separate streams.

---

# 4. Known Live Anchors

## 4.1 Mimas

Canonical input:

```text
PlanetFormID: 0005DEC0
RSCS:         2008989584
Biome count:  1
```

Because Mimas has only one biome, biome ordering does not create a meaningful permutation.

Known live floating-point generation values include:

```text
Common/root selection:
0.561107993

L1 Uncommon inclusion:
0.894184828

L2 Rare inclusion:
0.686025143

L3 Exotic inclusion:
0.108883217
```

The recovered Mimas descendant path consumed, for each level with one valid candidate:

```text
1 inclusion draw
1 candidate-index draw
```

for four descendant levels.

Therefore candidate-index calls must still consume RNG even when:

```text
candidate_count == 1
```

Brief 02 does not need to perform descendant generation, but its bounded-index primitive must be suitable for this observed behavior.

### Important

Do not assume the four floating-point values above are consecutive raw PRNG outputs.

There may be intervening bounded-index draws.

Tests should reflect the known call sequence once encoded.

Do not make an incorrect "consecutive floats" test simply because the values are listed together in documentation.

---

## 4.2 Kreet

Canonical input:

```text
PlanetFormID: 0003F59F
RSCS:         2842708811
```

Initial PNDT biome order:

```text
[0, 1, 2]
```

Observed live swaps:

```text
swap index 0 with index 1

[0, 1, 2]
->
[1, 0, 2]
```

then:

```text
swap index 0 with index 2

[1, 0, 2]
->
[2, 0, 1]
```

Final observed processing order:

```text
[2, 0, 1]
```

Brief 02 should use this as the primary bounded-index/shuffle compatibility anchor.

However:

> Do not hard-code Kreet's final permutation.

The PRNG/index conversion should naturally reproduce the observed swap choices.

---

# 5. Required Module

Create:

```text
src/starfield_resource_reproducer/prng.py
```

This module should contain the substantive PRNG compatibility implementation.

Follow the project commenting standard in `AGENTS.md`.

The module-level documentation should explain at minimum:

- Purpose
- Responsibilities
- Boundaries / non-responsibilities
- Evidence/compatibility constraints

Comments should explain intent and recovered-runtime constraints, not obvious Python syntax.

---

# 6. Public PRNG Abstraction

Provide one small stateful abstraction.

A reasonable interface is conceptually:

```python
class StarfieldRng:
    def __init__(self, seed: int): ...
    def next_uint32(self) -> int: ...
    def next_float01(self) -> float: ...
    def next_index(self, upper_bound: int) -> int: ...
```

Exact names may differ, but responsibilities should remain clear.

Also expose diagnostics such as:

```text
seed
draw_count
```

and, if useful:

```text
last raw uint32
```

Do not expose the internal MT state unless tests genuinely need it.

---

# 7. Implementation Strategy

## 7.1 Do not assume Python `random.Random` is compatible

Python's standard `random.Random` uses MT19937 internally, but this does **not** prove compatibility because differences may exist in:

- seed initialization;
- extraction method;
- float construction;
- bounded integer selection;
- rejection behavior;
- number of raw draws consumed by helper APIs.

Therefore:

1. it is acceptable to test Python's implementation as a candidate;
2. do not retain it merely because the algorithm name matches;
3. if live anchors disagree, implement the required MT19937 behavior directly.

The final compatibility layer must be justified by tests against Starfield observations.

---

## 7.2 Prefer an explicit MT19937 implementation if needed

If Python's standard API does not reproduce the trace, implement classic 32-bit MT19937 directly in `prng.py`.

Expected characteristics:

```text
state size: 624 uint32
period parameterization: standard MT19937
32-bit masking at required operations
standard tempering
```

Keep implementation small and auditable.

Do not add numpy or another dependency merely to obtain MT19937.

---

# 8. Separate Raw Generation from Conversion

The module should conceptually distinguish:

```text
raw uint32 generation
        |
        +--> probability float conversion
        |
        +--> bounded index conversion
```

This matters because the two downstream operations may consume/transform raw outputs differently.

Do not implement `next_float01()` by calling some opaque general-purpose random API that obscures raw draw consumption.

Do not implement `next_index()` via a library call unless its consumption semantics are proven compatible.

---

# 9. Float Conversion Compatibility

## Requirement

Determine the conversion that reproduces Starfield's observed probability values.

Possible candidates may include forms conceptually like:

```text
u / 2^32
u / (2^32 - 1)
upper bits scaled to [0,1)
multi-word constructions
float32 conversion effects
```

These examples are hypotheses only.

Do not pick one based on convention.

Use the trace anchors.

### Precision

Tests should compare at a precision appropriate to the observed values.

The trace values are recorded approximately to ~9 decimal places:

```text
0.561107993
0.894184828
0.686025143
0.108883217
```

The implementation should seek the exact underlying conversion, but tests against recorded values may use a tight absolute tolerance justified by trace display precision.

Do not weaken tolerance merely to force a match.

Document the chosen tolerance and why it is necessary.

### Diagnostics

For a float draw, it should be possible in tests/debugging to determine:

```text
draw number
raw uint32 input(s)
converted float
```

This does not require a permanent verbose logging system.

A small trace/event mechanism or inspectable return helper is acceptable.

---

# 10. Bounded Index Compatibility

Provide an explicit bounded-index operation:

```text
next_index(upper_bound)
```

with result:

```text
0 <= result < upper_bound
```

Reject:

```text
upper_bound <= 0
```

with a clear exception.

## Important observed behavior

If:

```text
upper_bound == 1
```

the function must still consume the RNG in the way Starfield does.

Do not optimize:

```python
if upper_bound == 1:
    return 0
```

without consuming a draw.

Mimas live tracing established that single-candidate selection still consumes RNG.

## Conversion method

Do not assume `% upper_bound`, `randrange`, multiplication-scaling, or rejection sampling.

Use Kreet's observed shuffle choices and any recoverable static evidence to determine the compatible behavior.

If multiple algorithms reproduce Kreet but remain indistinguishable, choose the simplest compatible candidate but mark the choice **STRONG** or **PROVISIONAL** rather than **PROVEN**.

Do not overstate evidence.

---

# 11. Shuffle Compatibility Harness

Brief 02 may implement a small PRNG-level shuffle helper or test-only harness solely to validate bounded index behavior.

For example:

```python
shuffle_indices([0, 1, 2], rng)
```

This is **not** yet the generation engine's biome-processing implementation.

Its purpose is to reproduce the known Kreet live swaps.

The observed runtime behavior must be preserved:

```text
initial:
[0, 1, 2]

swap:
0 <-> 1

swap:
0 <-> 2

final:
[2, 0, 1]
```

Do not label the implementation "Fisher-Yates" in code/docs unless exact loop semantics have been established.

Use neutral language such as:

```text
recovered shuffle behavior
Starfield-compatible shuffle step
```

until the algorithm is proven more specifically.

---

# 12. Draw Accounting

The PRNG wrapper must maintain an explicit draw counter.

Define clearly what one "draw" means.

Preferred definition:

```text
one extracted raw 32-bit MT19937 output
```

If a float/index operation consumes multiple raw outputs, increment accordingly.

Tests/debugging should be able to establish:

```text
before operation draw_count
after operation draw_count
```

This is essential for mismatch diagnosis later.

Do not count high-level method calls if one method can consume a variable number of raw MT outputs.

---

# 13. Optional Trace Record

A lightweight structured trace facility is encouraged if it stays small.

Example concept:

```python
@dataclass(frozen=True)
class RngDraw:
    raw_index: int
    raw_value: int
    operation: str
    converted_value: float | int | None
```

This is optional.

Do not build the full future `diagnostics.py` system in Brief 02.

If implemented, keep it clearly PRNG-local and reusable by future diagnostics.

---

# 14. Tests

Create focused tests such as:

```text
tests/test_prng.py
tests/test_prng_mimas.py
tests/test_prng_kreet.py
```

Exact file split is up to Codex.

Tests should not load the full resource-generation engine because it does not exist yet.

Use the Brief 01 loaders where useful for obtaining RSCS and canonical biome count/order.

---

# 15. Core Unit Tests

At minimum test:

## Seed validation

Accept:

```text
0
1
0x7FFFFFFF
0x80000000
0xFFFFFFFF
```

Reject:

```text
-1
0x100000000
non-integers
```

unless constructor behavior deliberately supports an explicit `FormId`-like conversion helper.

Do not silently mask arbitrary out-of-range integers into uint32.

---

## Raw output determinism

For the same seed:

```text
same raw sequence
```

For two independent instances:

```text
no shared hidden state
```

---

## Draw count

Verify raw draw count increments exactly as defined.

---

## `next_index(1)`

Verify:

```text
result == 0
```

and that the required raw RNG consumption still occurs.

---

# 16. Mimas Compatibility Tests

Use Mimas RSCS:

```text
2008989584
```

Construct a test sequence matching the known recovered high-level calls.

The test should verify the known floating values at their correct positions in the consumption sequence:

```text
Common/root roll:
~0.561107993

L1 inclusion:
~0.894184828

L2 inclusion:
~0.686025143

L3 inclusion:
~0.108883217
```

Where single-candidate index draws occur between inclusion rolls, include them explicitly.

Do not omit those index calls simply to obtain the expected floats.

The purpose of the test is **sequence compatibility**, not isolated value lookup.

If the exact pre-Common draw history cannot yet be established from current evidence, structure tests in layers:

```text
A. raw/float conversion candidate tests
B. known local sequence from an established trace anchor
C. mark unresolved prefix consumption explicitly
```

Do not fabricate unknown draw positions.

---

# 17. Kreet Compatibility Tests

Use:

```text
RSCS = 2842708811
```

Initial order:

```text
[0, 1, 2]
```

The compatibility harness should naturally produce observed swaps:

```text
0 <-> 1
0 <-> 2
```

and final order:

```text
[2, 0, 1]
```

The test should preferably assert the actual selected swap indices, not only final permutation.

That prevents a different algorithm from coincidentally arriving at the same final order.

If exact loop control is implemented only in a test helper because generation orchestration belongs to Brief 03, keep that helper small and clearly labeled.

---

# 18. Evidence Status in Code

Where an implementation choice is not fully live-proven, record that explicitly.

Examples:

```python
# STRONG: this bounded conversion reproduces the Kreet live swaps, but the
# trace has not yet distinguished it from every mathematically equivalent
# construction.
```

or:

```python
# PROVEN: a one-candidate structural choice still consumes RNG; do not
# short-circuit upper_bound == 1 without advancing the generator.
```

Use the project's evidence vocabulary consistently:

```text
PROVEN
STRONG
PROVISIONAL
```

Do not use comments like "probably Bethesda does X" without status/context.

---

# 19. No Algorithm Leakage

Brief 02 must not implement:

- effective RSGD selection beyond existing domain property;
- Everywhere insertion;
- Special pass;
- Common weighted root selection;
- IRES descendant candidate construction;
- descendant inclusion logic;
- family caching;
- planet resource prediction;
- canonical mismatch reports;
- CLI `--planet`;
- CLI `--all`.

A tiny shuffle compatibility helper is allowed only as a PRNG validation harness.

---

# 20. Dependency Policy

Prefer standard library only.

Do not add:

```text
numpy
randomgen
scipy
```

or other PRNG packages.

The project should remain auditable.

If a third-party dependency appears necessary, stop and report why before adding it.

---

# 21. Failure Behavior

If Codex cannot reproduce the known live anchors:

1. do not weaken tests to make them pass;
2. do not modify known values;
3. do not add planet-specific offsets;
4. do not consume unexplained dummy draws;
5. report the first divergence precisely.

The completion report should include:

```text
seed
operation
expected value/index
actual value/index
raw draw count
candidate conversion attempted
```

A failing compatibility harness with a precise divergence is preferable to a false green test suite.

---

# 22. Documentation Updates

Update:

```text
docs/DOMAIN-RULES.md
```

only if Brief 02 establishes a more precise rule with evidence, for example:

- exact float conversion;
- exact bounded-index conversion;
- exact shuffle loop semantics.

Do not upgrade evidence status without justification.

Update:

```text
docs/ARCHITECTURE.md
```

if the PRNG boundary differs materially from the currently documented design.

Update:

```text
docs/BACKLOG.md
```

to mark genuinely completed Phase 2 items.

Do not mark core generation complete.

---

# 23. Suggested Repository Shape

Likely result:

```text
src/starfield_resource_reproducer/
├── __init__.py
├── cli.py
├── domain.py
├── load_data.py
└── prng.py

tests/
├── ...
├── test_prng.py
├── test_prng_mimas.py
└── test_prng_kreet.py
```

Do not create future generation modules yet.

---

# 24. Required Validation

Run the full suite:

```powershell
python -m pytest
```

using Codex's working validated Python environment.

Also run targeted PRNG tests if useful:

```powershell
python -m pytest tests/test_prng.py
python -m pytest tests/test_prng_mimas.py
python -m pytest tests/test_prng_kreet.py
```

Do not require the user to create a local `.venv`.

---

# 25. Acceptance Criteria

Brief 02 is complete when:

- [ ] `prng.py` exists with a small documented Starfield-compatible RNG abstraction.
- [ ] unsigned 32-bit seed validation is explicit.
- [ ] MT19937 state evolution is deterministic.
- [ ] raw uint32 generation is inspectable/testable.
- [ ] draw count tracks raw MT outputs.
- [ ] float conversion is explicit and not hidden behind an opaque library helper.
- [ ] bounded-index conversion is explicit.
- [ ] `next_index(1)` consumes RNG compatibly rather than short-circuiting.
- [ ] Kreet's observed swap sequence is reproduced without hard-coding Kreet.
- [ ] known Mimas float anchors are reproduced at evidence-supported positions.
- [ ] any unresolved conversion ambiguity is clearly marked with evidence status.
- [ ] no generation-engine behavior is added.
- [ ] no new runtime dependency is added.
- [ ] Brief 00 and Brief 01 tests continue to pass.
- [ ] project code-commenting standards are followed.
- [ ] canonical CSV files remain unchanged.

If exact Mimas/Kreet compatibility cannot be achieved from the currently established evidence, do not falsely mark this brief complete. Report the precise unresolved compatibility point instead.

---

# 26. Commit Guidance

Suggested commit:

```text
feat: add Starfield PRNG compatibility layer
```

If evidence/documentation updates are substantial, an optional second commit may be:

```text
docs: record PRNG compatibility findings
```

Do not mix Brief 03 generation work into these commits.

Track this implementation brief under:

```text
docs/implementation-briefs/02-prng-compatibility.md
```

---

# 27. Codex Completion Report

When finished, report:

1. files created;
2. files modified;
3. whether Python `random.Random` was compatible or rejected;
4. final MT19937 implementation approach;
5. exact float conversion used;
6. exact bounded-index conversion used;
7. raw draw-count semantics;
8. Mimas anchor results;
9. Kreet swap/index results;
10. test count and status;
11. any evidence-status changes made to documentation;
12. any unresolved ambiguity;
13. blockers/questions for Brief 03.

Do not begin Brief 03 automatically.

---

## Next Planned Brief

If Brief 02 achieves exact compatibility, Brief 03 will implement the first deterministic generation core:

```text
PNDT-order biome list
    ->
Starfield-compatible shuffle
    ->
effective RSGD
    ->
Everywhere/Special/Common
    ->
descendant traversal
    ->
family cache
```

using the validated loaders and PRNG abstraction rather than re-implementing either concern.
