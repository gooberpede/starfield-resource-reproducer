# Implementation Brief 05 — Worked-Case Reproduction and Mismatch Diagnostics

## Context

Repository:

```text
gooberpede/starfield-resource-reproducer
```

Completed phases:

```text
Brief 00 — Project Bootstrap
Brief 01 — Canonical Data Loading and Domain Model
Brief 02 — PRNG Compatibility Layer
Brief 03 — Generation Orchestration and Shuffle Transparency
Brief 04 — Family Generation and Cache Semantics
```

The implementation now contains:

```text
canonical static inputs
canonical runtime oracle
Starfield-compatible PRNG
biome orchestration
Special/Common selection
family generation
structured diagnostics
family caching
```

Brief 05 is the first point where those layers are combined into a complete worked-planet reproduction pipeline and compared against the canonical runtime oracle.

The purpose is not merely to obtain four green examples.

The purpose is to make any mismatch precise enough to become the next reverse-engineering experiment.

---

# 1. Goal

Implement complete worked-case reproduction for:

```text
Oberon
Mimas
Decaran VII-b
Kreet
```

and compare predicted inorganic resources against:

```text
planet-all-resources.csv
```

Brief 05 must provide:

1. a complete per-planet predicted inorganic result;
2. canonical expected inorganic result;
3. exact-match status;
4. missing resources;
5. unexpected resources;
6. deterministic generation/event history;
7. first-divergence diagnostics where a worked case fails;
8. evidence-qualified classification of likely mismatch source.

Kreet is explicitly allowed to fail during this brief if the failure is diagnosed precisely.

Do not insert planet-specific workarounds.

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
docs/implementation-briefs/03-generation-orchestration.md
docs/implementation-briefs/04-family-generation.md
```

Inspect current implementations:

```text
domain.py
load_data.py
prng.py
diagnostics.py
candidates.py
generation.py
```

and all existing tests.

Preserve all existing evidence labels.

---

# 3. Worked Cases

## 3.1 Oberon

Expected canonical inorganic result:

```text
Water
Nickel
```

This case primarily exercises:

```text
Everywhere discovery
empty/no-match Special pass
Common root selection
simple family result
```

---

## 3.2 Mimas

Expected canonical inorganic result:

```text
Water
Nickel
Palladium
```

This is the primary exact RNG/family regression.

Known sequence:

```text
draw 1   empty Special
draw 2   Common -> Nickel
draw 3   L1 inclusion
draw 4   L1 index
draw 5   L2 inclusion
draw 6   L2 index
draw 7   L3 inclusion
draw 8   L3 index
draw 9   L4 inclusion
draw 10  L4 index
```

Expected family:

```text
Nickel
Palladium
```

---

## 3.3 Decaran VII-b

Expected canonical inorganic result:

```text
Helium3
Uranium
Iridium
Vytinium
```

This case exercises:

```text
Special selection
Common selection
Uranium family traversal
Unique descendant
```

Do not special-case the `Helium-3` / `Helium3` naming difference.

Compare by FormID.

---

## 3.4 Kreet

Expected canonical inorganic result:

```text
Argon
Iron
Lead
Water
Neon
Alkanes
Silver
```

Known runtime biome processing order:

```text
Volcanic
Frozen Volcanic
Mountains
```

Known Common roots:

```text
Volcanic        -> Lead
Frozen Volcanic -> Argon
Mountains       -> Iron
```

An exploratory Brief 04 run omitted Neon.

Brief 05 must treat this as a diagnostic target, not as permission to special-case Kreet.

---

# 4. Complete Predicted Planet Result

Add a complete prediction model, conceptually:

```text
PlanetGenerationResult
```

It should represent the full inorganic output currently predicted by the implemented model.

At minimum include:

```text
planet
shuffled biome order
Everywhere resources
Special resources
family results
predicted inorganic FormIDs
events
final RNG draw count
```

Avoid mixing oracle data into the generation result itself.

The generator must remain capable of running without the oracle loaded.

---

# 5. Oracle Comparison Model

Create a separate comparison model, conceptually:

```text
PlanetValidationResult
```

with at least:

```text
planet_form_id
predicted_form_ids
expected_form_ids
missing_form_ids
unexpected_form_ids
exact_match
```

Retain resource metadata for readable diagnostics.

Comparison identity must be:

```text
FormID
```

not resource name.

---

# 6. Validation Boundary

Keep generation and validation separate.

Preferred conceptual flow:

```text
generate_planet(...)
    ->
PlanetGenerationResult

compare_planet_to_oracle(...)
    ->
PlanetValidationResult
```

Do not allow the oracle to influence generation decisions.

Do not fill missing generated resources from canonical data.

---

# 7. First-Divergence Diagnostics

This is a mandatory Brief 05 feature.

When a worked planet does not match, diagnostics should help answer:

> Where did the model first diverge from the known runtime behavior?

For a mismatch, expose:

```text
biome processing order
effective RSGD
Special selection
Common root
family structural path
family emissions
draw numbers
raw uint32 values
float/index conversions
candidate lists
inclusion thresholds
cache hits
zero-candidate levels
final predicted set
```

Do not merely report:

```text
missing Neon
```

The diagnostic output should make it possible to reason backwards to the earliest plausible divergence.

---

# 8. Diagnostic Timeline

Provide a deterministic timeline abstraction or formatter over existing structured events.

This may be:

```text
diagnostic timeline
trace formatter
event summary
```

but should not require parsing ad hoc print statements.

A worked-case trace should be able to render conceptually like:

```text
Planet Kreet
Seed 2842708811

draw 1  shuffle bound=2 index=0
draw 2  shuffle bound=3 index=0

Biome Volcanic
RSGD PNDT VolcanicDefaultRes_Kreet
draw 3  Special no-match
draw 4  Common -> Lead
...
```

Continue through all family levels.

Do not require the CLI to expose this yet if tests can use the formatter directly.

---

# 9. Kreet Mismatch Investigation

The Brief 04 exploratory result suggests:

```text
predicted Kreet misses Neon
```

The leading hypothesis is that the model's provisional zero-candidate RNG consumption differs from the runtime, possibly during the Lead family before Argon begins.

Brief 05 should test this hypothesis diagnostically.

At minimum identify:

1. every zero-candidate descendant level encountered before Argon's Neon decision;
2. current model RNG consumption at each;
3. Argon's inclusion draw number/value under the current model;
4. whether the wrong Neon outcome can plausibly be explained by earlier draw-stream displacement.

Do not alter zero-candidate behavior merely to make Neon appear.

---

# 10. Counterfactual Diagnostic Helper

A small **test-only or diagnostics-only** counterfactual helper is allowed if it helps identify likely RNG displacement.

For example, it may answer:

```text
If one extra raw draw were consumed at this earlier zero-candidate level,
what would Argon's later inclusion roll become?
```

This must not modify production generation behavior.

Clearly label such results:

```text
COUNTERFACTUAL
NOT RUNTIME-PROVEN
```

The purpose is to prioritize the next reverse-engineering experiment.

Do not commit speculative consumption into `generate_family()` based only on counterfactual matching.

---

# 11. Zero-Candidate Visibility

Every zero-candidate descendant level must emit a structured diagnostic event containing:

```text
root
current structural node
requested rarity
candidate_count = 0
draw_count_before
draw_count_after
inclusion_rng_consumed
index_rng_consumed
structural_node_after
```

This should make the current provisional behavior auditable.

---

# 12. Cache-Hit Visibility

Every family cache hit must expose:

```text
root FormID
draw_count_before
draw_count_after
cached emitted family
```

This is important even if none of the four worked cases exercises a meaningful collision.

Do not hide cache reuse inside a dictionary lookup.

---

# 13. Complete Resource Assembly

The final predicted inorganic set should be assembled from generic generation outputs:

```text
Everywhere
+
Special
+
emitted Common-family resources
```

Use FormID identity.

Deduplicate deterministically.

Do not use canonical output to decide whether a resource belongs.

---

# 14. Result Ordering

For set comparison:

```text
use frozenset/FormID membership
```

For diagnostics/display:

use a deterministic order, preferably generation order with stable fallback ordering.

Do not rely on arbitrary set iteration order.

---

# 15. Worked-Case API

Add a small high-level API, conceptually:

```python
generate_planet(
    planet,
    ires_nodes,
) -> PlanetGenerationResult
```

The function should:

```text
create one StarfieldRng from RSCS
perform orchestration
perform family generation
assemble final predicted set
return structured result
```

Exact signature may also accept injected RNG for tests.

Do not make oracle data a required parameter.

---

# 16. Validation API

A reasonable validation API is conceptually:

```python
compare_to_oracle(
    generation_result,
    canonical_body,
) -> PlanetValidationResult
```

and optionally:

```python
validate_worked_cases(project_data) -> tuple[PlanetValidationResult, ...]
```

Do not build full-dataset batch validation yet.

---

# 17. Worked-Case Regression Tests

Add exact tests for:

```text
Oberon
Mimas
Decaran VII-b
Kreet
```

## Passing cases

If the current implementation reproduces a case exactly:

assert:

```text
predicted == canonical
missing == empty
unexpected == empty
exact_match is True
```

## Kreet

If Kreet still misses Neon:

do not force a passing exact-match assertion.

Instead assert:

```text
the current mismatch is deterministic
missing contains Neon
diagnostics identify first plausible RNG divergence region
```

If Brief 05 naturally resolves Kreet through evidence-backed implementation already supported by current control flow, then assert exact match.

Do not add a special case.

---

# 18. Mimas Exact Regression

Mimas must remain fully exact.

Assert final predicted set:

```text
Water
Nickel
Palladium
```

and final draw count expected from current model.

Also retain family-path assertions.

A Brief 05 refactor must not regress the precise Mimas draw sequence.

---

# 19. Decaran Exact Regression

Assert final predicted FormID set matches the canonical oracle exactly.

Do not compare resource names.

Keep the generic Special + Common + family flow.

---

# 20. Oberon Exact Regression

Assert:

```text
Water
Nickel
```

and verify Water is still accounted for via the explicit provisional Everywhere layer rather than being misclassified into Common generation.

---

# 21. Kreet Trace Regression

The Kreet test should preserve:

```text
initial biome order
shuffle steps
final order [2,0,1]
Common roots Lead, Argon, Iron
```

and then record complete family-generation histories.

If Neon is missing, report the exact Argon inclusion roll and draw number.

---

# 22. Mismatch Classification

Introduce a small diagnostic classification enum or label system if useful.

Examples:

```text
SHUFFLE_MISMATCH
RSGD_MISMATCH
SPECIAL_MISMATCH
COMMON_ROOT_MISMATCH
DESCENDANT_CANDIDATE_MISMATCH
DESCENDANT_INCLUSION_MISMATCH
CACHE_BEHAVIOR_SUSPECT
RNG_CONSUMPTION_SUSPECT
EVERYWHERE_MODEL_SUSPECT
UNKNOWN
```

Do not pretend classification is certain when it is heuristic.

Use labels such as:

```text
suspected cause
first plausible divergence
```

rather than "root cause" unless proven.

---

# 23. No Global Dataset Run Yet

Do not validate all 1,444 planets in Brief 05.

The worked cases should first establish:

```text
complete prediction API
comparison API
diagnostic quality
mismatch workflow
```

Full-dataset validation belongs to Brief 06.

---

# 24. No CLI Expansion Required

Do not add `--all`.

A small developer-facing `--planet` option is still optional and should not distract from the core implementation.

Tests and Python APIs are the acceptance surface.

---

# 25. Documentation Updates

Update:

```text
docs/ARCHITECTURE.md
```

to describe:

```text
generation result
validation result
diagnostic comparison boundary
```

Update:

```text
docs/DOMAIN-RULES.md
```

only for newly established behavior.

Do not upgrade:

```text
zero-candidate consumption
cache-hit consumption
Everywhere insertion mechanism
```

without evidence.

Update:

```text
docs/BACKLOG.md
```

to mark worked-case reproduction/diagnostic tasks completed as appropriate.

---

# 26. Evidence Discipline

The implementation must clearly distinguish:

```text
PROVEN
STRONG
PROVISIONAL
COUNTERFACTUAL
```

Counterfactual diagnostics must never be mistaken for production rules.

Example:

```python
# COUNTERFACTUAL: advancing one raw word here makes the later Argon inclusion
# roll match the observed Neon outcome. This is diagnostic evidence only and
# must not alter production generation until the zero-candidate branch is
# verified.
```

---

# 27. Failure Behavior

If a worked case fails:

Do not:

```text
special-case the planet
special-case the resource
insert unexplained draws
change canonical expected data
weaken comparison identity
pull missing resources from the oracle
```

Instead report:

```text
expected set
actual set
missing
unexpected
first suspicious event
draw position
candidate state
evidence status
```

---

# 28. Suggested Modules

A reasonable result is:

```text
src/starfield_resource_reproducer/
├── candidates.py
├── diagnostics.py
├── domain.py
├── generation.py
├── load_data.py
├── prng.py
└── validation.py
```

`validation.py` should contain oracle-comparison logic rather than generation logic.

Do not create broad generic framework modules.

---

# 29. Tests

Suggested new tests:

```text
tests/test_worked_oberon.py
tests/test_worked_mimas.py
tests/test_worked_decaran.py
tests/test_worked_kreet.py
tests/test_validation.py
tests/test_mismatch_diagnostics.py
```

Exact split is up to Codex.

Keep all existing tests passing.

---

# 30. Required Validation

Run:

```powershell
python -m pytest
```

using Codex's validated Python environment.

Also run worked-case tests separately if helpful.

Canonical CSVs must remain unchanged.

---

# 31. Acceptance Criteria

Brief 05 is complete when:

- [ ] a complete `PlanetGenerationResult` or equivalent exists.
- [ ] final predicted inorganic resources are assembled generically.
- [ ] generation does not require oracle data.
- [ ] a separate oracle-comparison result exists.
- [ ] validation compares by FormID.
- [ ] missing and unexpected resources are reported.
- [ ] structured event history spans seed through final family generation.
- [ ] deterministic diagnostic timeline is available.
- [ ] zero-candidate events expose RNG consumption explicitly.
- [ ] cache-hit events expose RNG consumption explicitly.
- [ ] Oberon reproduces its canonical inorganic set exactly.
- [ ] Mimas reproduces its canonical inorganic set exactly.
- [ ] Decaran VII-b reproduces its canonical inorganic set exactly.
- [ ] Kreet either reproduces exactly or fails with precise diagnostics.
- [ ] Kreet's known biome order and Common roots remain correct.
- [ ] if Kreet misses Neon, the Argon roll/draw and preceding zero-candidate events are reported.
- [ ] optional counterfactual diagnostics do not modify production behavior.
- [ ] no planet-specific or resource-specific workaround is introduced.
- [ ] no full 1,444-body validation is added.
- [ ] all prior tests remain green except any deliberately evidence-preserving Kreet exact-match expectation.
- [ ] canonical CSV files remain unchanged.
- [ ] code-commenting standards are followed.

---

# 32. Completion Report

Codex should report:

1. files created;
2. files modified;
3. complete generation API;
4. validation/comparison API;
5. final predicted sets for Oberon, Mimas, Decaran VII-b, Kreet;
6. exact-match status for each;
7. missing/unexpected resources for any mismatch;
8. final RNG draw count for each;
9. Kreet's Argon/Neon diagnostic sequence;
10. every zero-candidate event before the Kreet divergence;
11. any counterfactual findings;
12. evidence-status changes;
13. test count/results;
14. blockers/questions for Brief 06 or further reverse-engineering.

Do not begin full-dataset validation automatically.

---

# 33. Commit Guidance

Suggested commit:

```text
feat: add worked-case validation
```

If diagnostics are substantial enough to justify a separate commit:

```text
feat: add generation mismatch diagnostics
```

Track this brief under:

```text
docs/implementation-briefs/05-worked-case-validation.md
```

---

## Next Planned Step

If all four worked cases match:

```text
Brief 06 — full 1,444-body canonical validation
```

If Kreet or another worked case still fails:

```text
perform the smallest targeted reverse-engineering experiment needed to
resolve the first diagnosed mismatch
```

before expanding to all planets.

At this stage, a precise mismatch is a useful research result, not a failed project.
