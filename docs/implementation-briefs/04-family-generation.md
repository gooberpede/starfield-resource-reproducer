# Implementation Brief 04 — Family Generation and Cache Semantics

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
```

Brief 04 adds the resource-family mechanics that begin **after a Common root has been selected**.

The orchestration boundary established by Brief 03 is now:

```text
planet seeded
    ->
biomes shuffled
    ->
effective RSGD resolved
    ->
Everywhere handled provisionally
    ->
Special pass
    ->
Common/root selected
    ->
[Brief 04 begins here]
```

The objective is to reproduce the recovered runtime descendant-generation behavior without yet turning the whole system into a final canonical-validation workflow.

---

# 1. Goal

Implement deterministic resource-family generation for a newly selected Common root.

Brief 04 must cover:

1. unconditional Common-root emission;
2. descendant processing for:
   - Uncommon
   - Rare
   - Exotic
   - Unique
3. structural candidate construction from the IRES graph;
4. inclusion rolls;
5. candidate-index rolls;
6. traversal through a selected structural node even when that node is not emitted;
7. per-root family result caching at planet scope;
8. reuse of an already-generated family without regenerating descendants.

The primary live regression case is Mimas.

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
```

Inspect the current implementations of:

```text
domain.py
load_data.py
prng.py
diagnostics.py
generation.py
```

and all existing tests.

Preserve existing evidence statuses.

---

# 3. Evidence Baseline

## 3.1 Root emission

**PROVEN**

Once a Common/root resource is selected:

```text
root is emitted unconditionally
```

Descendant inclusion logic does not control root emission.

Example:

```text
Mimas
Common root = Nickel
Nickel is always present
```

---

## 3.2 Descendant rarity levels

**PROVEN**

The generator processes four descendant levels in order:

```text
1 = Uncommon
2 = Rare
3 = Exotic
4 = Unique
```

---

## 3.3 Per-level behavior

**PROVEN**

At each descendant level:

```text
1. build the structurally valid candidate set
2. perform inclusion probability draw
3. perform candidate-selection draw
4. emit chosen candidate only if inclusion succeeds
5. advance structural traversal through chosen candidate regardless of emission
```

The structural candidate remains the current traversal node even when omitted.

---

## 3.4 One-candidate selection still consumes RNG

**PROVEN**

Mimas live tracing established that a candidate-index RNG operation still occurs when:

```text
candidate_count == 1
```

Therefore do not optimize one-candidate selection by returning index 0 without advancing `StarfieldRng`.

---

## 3.5 Family result reuse

**PROVEN**

If a later biome selects a Common root already generated elsewhere on the same planet:

```text
reuse the existing family result
```

Do not independently reroll descendants.

The descendant configuration is therefore planet-wide per Common root.

Exact RNG consumption on a cache hit remains a potential edge-case question unless already established by current control flow.

Do not invent extra draws on cache hits.

---

# 4. IRES Candidate Construction

This is central to Brief 04.

The serialized IRES graph is not traversed as a simple linear tree.

For each descendant rarity level, runtime candidate construction scans:

```text
children(root)
+
children(previously_selected_structural_node)
```

then filters the combined set to the requested rarity.

This rule is **PROVEN** from decompilation/runtime behavior.

---

# 5. Candidate Construction Examples

## 5.1 Nickel family

Serialized graph:

```text
Nickel
├─ Cobalt      Uncommon
│  └─ Platinum Rare
└─ Palladium   Exotic
   └─ Tasine   Unique
```

Recovered runtime traversal:

```text
L1 Uncommon
children(Nickel) + children(Nickel)
-> Cobalt

L2 Rare
children(Nickel) + children(Cobalt)
-> Platinum

L3 Exotic
children(Nickel) + children(Platinum)
-> Palladium

L4 Unique
children(Nickel) + children(Palladium)
-> Tasine
```

The important point is that Palladium is rediscovered from the root at L3.

---

## 5.2 Copper family

Serialized graph:

```text
Copper
├─ Fluorine
│  └─ Tetrafluorides
│     └─ Ionic Liquids
└─ Gold
   └─ Antimony
```

Runtime-effective branching at Rare can include both:

```text
Gold
Tetrafluorides
```

because candidates are drawn from:

```text
children(root)
+
children(current_structural_node)
```

Do not flatten the graph into a precomputed single path.

---

## 5.3 Uranium family

Serialized graph:

```text
Uranium
├─ Iridium     Uncommon
├─ Vanadium    Rare
└─ Plutonium   Exotic
      └─ Vytinium Unique
```

Expected recovered traversal:

```text
L1 -> Iridium
L2 -> Vanadium
L3 -> Plutonium
L4 -> Vytinium
```

---

# 6. Candidate Ordering

Preserve IRES child ordering as loaded from the canonical hierarchy.

Candidate ordering must be deterministic.

The combination rule should be explicit and auditable.

Use:

```text
children(root)
then
children(current_structural_node)
```

unless runtime evidence in current docs specifies a different order.

If the same FormID appears twice in the combined list, do not silently alter semantics without checking current evidence.

If deduplication is required by recovered runtime behavior, document it explicitly.

Do not sort candidates by:

```text
name
FormID
rarity
```

unless runtime evidence supports that.

---

# 7. Descendant Chance Source

The selected Common root's `RSGDResourceEntry` supplies descendant inclusion probabilities:

```text
BiomeUncommonChance
BiomeRareChance
BiomeExoticChance
BiomeUniqueChance
```

Example: Mimas Nickel:

```text
Uncommon = 50%
Rare     = 25%
Exotic   = 15%
Unique   = 0%
```

These percentages are not candidate weights.

They are inclusion probabilities for the corresponding descendant level.

Do not normalize them.

---

# 8. Inclusion Roll

For each descendant level with a candidate set:

```text
inclusion_roll = rng.next_float01()
```

Compare against:

```text
chance / 100
```

The observed semantics are:

```text
emit if roll < threshold
```

Use the exact comparison recovered from current evidence.

Do not special-case:

```text
0%
100%
```

unless runtime control flow proves short-circuit behavior.

If the runtime consumes the inclusion RNG even at 0% or 100%, preserve that.

Mimas L4 with 0% is a mandatory regression case.

---

# 9. Candidate Selection Roll

After the inclusion roll:

```text
candidate_index = rng.next_index(candidate_count)
```

This happens even when there is exactly one candidate.

Candidate selection determines the structural node regardless of whether inclusion succeeds.

The chosen node becomes the current traversal node for the next level.

---

# 10. Zero-Candidate Behavior

Candidate count = 0 remains an important edge case.

Do not guess.

Implement according to current recovered control flow if sufficiently established.

At minimum, diagnostics must report:

```text
requested rarity
candidate_count = 0
whether inclusion RNG was consumed
whether candidate-index RNG was consumed
whether structural node changed
```

If current evidence does not establish exact zero-candidate RNG behavior, mark it explicitly:

```text
PROVISIONAL
```

and avoid inventing unexplained draws.

Do not fabricate an empty selection roll simply for uniformity.

---

# 11. Family Result Model

Introduce a family-specific result model, conceptually:

```text
ResourceFamilyResult
```

It should contain at least:

```text
root
structural selections by level
emitted descendants
complete emitted resource set
events
```

A useful shape might include:

```text
root
levels
emitted_resources
```

where each level records:

```text
rarity
candidate list
inclusion roll
inclusion threshold
selected candidate
emitted yes/no
```

Do not reduce family generation to only a final set.

The structural path is diagnostically important.

---

# 12. Family Cache

Add planet-scope caching keyed by Common root FormID.

Conceptually:

```python
family_cache[root_form_id] = ResourceFamilyResult
```

When a new Common root is first selected:

```text
generate family
cache result
```

When the same root is selected again:

```text
reuse cached family
```

Diagnostics must distinguish:

```text
FAMILY_GENERATED
FAMILY_CACHE_HIT
```

Do not mutate cached results per biome.

Prefer immutable family results.

---

# 13. Cache-Hit RNG Behavior

Do not assume descendants consume RNG again on a cache hit.

The known behavior is:

```text
existing family result is reused
```

If current runtime evidence says the descendant routine is bypassed, preserve that.

Diagnostics should expose:

```text
root
cache hit yes/no
draw_count before
draw_count after
```

If no additional descendant draws occur, lock that behavior with a test.

If evidence remains incomplete, label it accurately.

---

# 14. Integration with Brief 03 Orchestration

Extend the existing orchestration without destroying the partial diagnostic boundary.

A reasonable design is:

```text
orchestrate_planet()
    ->
selected Common roots

generate_planet_families()
    ->
family results
```

or a single evolving pipeline with clearly separated internal phases.

Avoid rewriting Brief 03 diagnostics.

Preserve visibility of:

```text
shuffle
Special
Common
```

before descendant events begin.

Do not make `generation.py` one monolithic function.

---

# 15. Structured Diagnostic Events

Add family-generation events such as:

```text
FAMILY_BEGIN
ROOT_EMITTED
DESCENDANT_LEVEL_BEGIN
DESCENDANT_CANDIDATES
DESCENDANT_INCLUSION_ROLL
DESCENDANT_CANDIDATE_SELECTED
DESCENDANT_EMITTED
DESCENDANT_OMITTED
FAMILY_END
FAMILY_CACHE_HIT
```

Exact names may differ.

Each RNG event must preserve:

```text
raw draw count
raw uint32
converted value/index
```

Candidate diagnostics should include FormIDs and names.

---

# 16. Mimas Mandatory Regression

Mimas is the primary Brief 04 acceptance case.

Known state before descendants:

```text
RSCS = 2008989584

draw 1:
empty Special pass

draw 2:
Common roll
0.5611079931259155
-> Nickel
```

Descendant phase begins immediately after draw 2.

Expected descendant behavior:

```text
L1 Uncommon
candidate: Cobalt
inclusion: 0.894184828
chance: 50%
emitted: no
selected structurally: Cobalt

L2 Rare
candidate: Platinum
inclusion: 0.686025143
chance: 25%
emitted: no
selected structurally: Platinum

L3 Exotic
candidate: Palladium
inclusion: 0.108883217
chance: 15%
emitted: yes
selected structurally: Palladium

L4 Unique
candidate: Tasine
inclusion: 0.818136036
chance: 0%
emitted: no
selected structurally: Tasine
```

Final family:

```text
Nickel
Palladium
```

Expected structural path:

```text
Nickel
-> Cobalt
-> Platinum
-> Palladium
-> Tasine
```

The omitted Cobalt and Platinum must still affect later traversal.

---

# 17. Mimas Draw Consumption

The four descendant levels consume:

```text
4 inclusion draws
4 candidate-index draws
```

for:

```text
8 raw RNG draws total
```

because every level has exactly one candidate.

Tests must assert the interleaving:

```text
L1 inclusion
L1 candidate index
L2 inclusion
L2 candidate index
L3 inclusion
L3 candidate index
L4 inclusion
L4 candidate index
```

Do not group all inclusions first.

Do not skip `next_index(1)`.

---

# 18. Mimas Full Draw Positions

Given Brief 03:

```text
draw 1 = empty Special
draw 2 = Common
```

Brief 04 should verify descendants occupy the next eight raw draws:

```text
draw 3  L1 inclusion
draw 4  L1 candidate index
draw 5  L2 inclusion
draw 6  L2 candidate index
draw 7  L3 inclusion
draw 8  L3 candidate index
draw 9  L4 inclusion
draw 10 L4 candidate index
```

If current implementation shows a different offset, report it rather than adjusting manually.

---

# 19. Decaran VII-b Regression

Use Decaran VII-b as the second major family test.

Known outer selections:

```text
Special -> Helium-3
Common  -> Uranium
```

Expected Uranium family traversal:

```text
L1 -> Iridium
L2 -> Vanadium
L3 -> Plutonium
L4 -> Vytinium
```

The final emitted set must be based on actual inclusion rolls/chances.

At minimum, the structural path must match the recovered IRES behavior.

The canonical observed inorganic output is:

```text
Helium3
Uranium
Iridium
Vytinium
```

Do not special-case Vytinium.

It must emerge through the same generic descendant algorithm.

---

# 20. Copper Branching Unit Test

Add a synthetic or static graph-level unit test around Copper to verify candidate construction.

At the Rare level, after Fluorine has been structurally selected, candidates should be derivable from:

```text
children(Copper)
+
children(Fluorine)
```

and rarity-filtered accordingly.

This test should prove the implementation does not simply follow one serialized branch.

Do not require a complete planet generation case if a focused graph test is clearer.

---

# 21. Nickel Graph Unit Test

Verify:

```text
children(Nickel):
Cobalt
Palladium
```

Then with current structural node Cobalt:

```text
Rare candidates:
Platinum
```

Then with current structural node Platinum:

```text
Exotic candidates:
Palladium
```

This should directly lock the root-plus-current candidate rule.

---

# 22. Root Emission

The Common root should appear once in the emitted family result.

Do not duplicate it if encountered structurally later.

Use FormID identity.

Do not use resource names as keys.

---

# 23. Result Identity and Ordering

For diagnostics:

```text
preserve deterministic generation order
```

For membership comparisons:

```text
use FormID-based sets/frozensets
```

A family result may therefore expose both:

```text
emitted_sequence
emitted_form_ids
```

or equivalent.

Avoid relying on Python set iteration order for diagnostic output.

---

# 24. No Final Canonical Validation Yet

Brief 04 should not run all 1,444 planets against the oracle.

That belongs later.

Worked cases may compare their partial/full family result to known canonical outputs.

Do not add:

```text
--all
global match percentage
mismatch classification
```

yet.

---

# 25. No Planet-Specific Fixes

Do not add logic such as:

```python
if planet.name == "Mimas":
```

or:

```python
if root.name == "Nickel":
```

to produce expected results.

All behavior must arise from:

```text
RSGD
IRES
PRNG
generic generation rules
```

---

# 26. Evidence Labels

Use existing evidence vocabulary.

Examples:

```python
# PROVEN: structural traversal advances through the selected node even when
# its inclusion roll fails.
```

```python
# PROVEN: a one-candidate selection still consumes one bounded-index draw.
```

```python
# PROVISIONAL: zero-candidate draw behavior has not yet been observed live.
```

Do not convert an unobserved edge case into a PROVEN rule because the implementation is convenient.

---

# 27. Suggested API

A reasonable public/internal boundary is conceptually:

```python
generate_family(
    root_entry,
    ires_nodes,
    rng,
) -> ResourceFamilyResult
```

and a planet-scope helper:

```python
get_or_generate_family(
    root_entry,
    family_cache,
    ires_nodes,
    rng,
) -> ResourceFamilyResult
```

Exact signatures may differ.

Keep RSGD inclusion chances associated with the selected root entry.

Do not look them up again by name.

---

# 28. Tests

Suggested new tests:

```text
tests/test_family_candidates.py
tests/test_family_mimas.py
tests/test_family_decaran.py
tests/test_family_cache.py
```

Exact file split is up to Codex.

Tests must inspect diagnostics where RNG sequencing matters.

---

# 29. Cache Test

Create a focused test where the same root is requested twice in one planet context.

Assert:

```text
first request:
family generated
RNG advances through descendants

second request:
same family result reused
no descendant reroll
```

Also assert cache key uses FormID.

If exact RNG consumption on cache hit remains unresolved, report that instead of inventing behavior.

---

# 30. Zero-Candidate Test

Create at least one controlled test for a level with no valid candidate.

The test should document the implementation's current evidence-backed behavior:

```text
candidate list empty
selected structural node remains ?
RNG consumption = ?
```

If this remains PROVISIONAL, the test should lock the current interpretation while making evidence status clear.

Do not hide the uncertainty.

---

# 31. Required Documentation Updates

Update:

```text
docs/DOMAIN-RULES.md
```

with any newly implemented/clarified family-generation rules.

At minimum ensure it records:

```text
root emitted unconditionally
root + current-node candidate construction
structural continuation on failed inclusion
single-candidate index draw
family cache reuse
```

Update:

```text
docs/BACKLOG.md
```

for genuinely completed family-generation items.

Update:

```text
docs/ARCHITECTURE.md
```

if the family/cache layer materially changes the documented design.

---

# 32. Required Validation

Run:

```powershell
python -m pytest
```

using Codex's validated Python environment.

Targeted runs may include:

```powershell
python -m pytest tests/test_family_mimas.py
python -m pytest tests/test_family_candidates.py
python -m pytest tests/test_family_cache.py
```

Keep all previous tests passing.

Canonical CSVs must remain unchanged.

---

# 33. Acceptance Criteria

Brief 04 is complete when:

- [ ] Common root is emitted unconditionally.
- [ ] descendant levels run in Uncommon -> Rare -> Exotic -> Unique order.
- [ ] candidate sets are built from `children(root) + children(current_structural_node)`.
- [ ] candidates are filtered by requested rarity.
- [ ] inclusion rolls use the selected root's RSGD descendant chances.
- [ ] candidate selection occurs after inclusion roll.
- [ ] one-candidate selection still consumes RNG.
- [ ] selected structural node advances even if not emitted.
- [ ] Mimas produces structural path Nickel -> Cobalt -> Platinum -> Palladium -> Tasine.
- [ ] Mimas emits exactly Nickel + Palladium for the family.
- [ ] Mimas descendant draw sequence occupies raw draws 3–10.
- [ ] Mimas L4 inclusion anchor ~0.818136036 is asserted.
- [ ] Decaran Uranium traversal reaches Vytinium generically.
- [ ] Copper branching candidate construction is tested.
- [ ] family cache is keyed by Common root FormID.
- [ ] repeated root selection reuses cached family result.
- [ ] cache-hit RNG behavior is transparent and evidence-qualified.
- [ ] zero-candidate behavior is transparent and evidence-qualified.
- [ ] structured diagnostics include family/level/candidate/inclusion/selection events.
- [ ] no planet-specific hacks are introduced.
- [ ] no full 1,444-body validation is added yet.
- [ ] full existing test suite passes.
- [ ] canonical CSVs remain unchanged.
- [ ] code-commenting standards are followed.

---

# 34. Failure Conditions

If Mimas fails:

Do not:

```text
change known trace values
skip draws
insert dummy draws
hard-code Palladium
special-case Nickel
reorder IRES candidates arbitrarily
```

Report the first divergence with:

```text
draw number
rarity level
candidate set
expected structural node
actual structural node
expected inclusion roll
actual roll
```

A precise mismatch is preferable to a false pass.

---

# 35. Completion Report

Codex should report:

1. files created;
2. files modified;
3. family-generation API;
4. family result/cache models;
5. candidate construction implementation;
6. zero-candidate behavior;
7. cache-hit RNG behavior;
8. Mimas full descendant draw sequence;
9. Mimas structural path;
10. Mimas emitted family result;
11. Decaran Uranium structural/emission result;
12. Copper branching test result;
13. evidence-status updates;
14. test count/results;
15. unresolved questions before Brief 05.

Do not begin full worked-planet validation automatically.

---

# 36. Commit Guidance

Suggested commit:

```text
feat: add resource family generation
```

Optional separate documentation commit:

```text
docs: record family generation rules
```

Track this brief under:

```text
docs/implementation-briefs/04-family-generation.md
```

---

## Next Planned Brief

Brief 05 will combine the now-implemented orchestration and family layers into exact worked-planet reproduction for:

```text
Oberon
Mimas
Decaran VII-b
Kreet
```

and verify complete predicted inorganic output against the canonical oracle before expanding to all 1,444 bodies.
