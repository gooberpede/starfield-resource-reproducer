# Implementation Brief 07A — Dense-Planet Diagnostic Dossier

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
05B  Zero-candidate runtime correction + cache proof
05C  Bounded-index path divergence investigation
05D  Distinct bounded-RNG runtime paths
06   Full canonical planet validation
```

Brief 06 established the first complete canonical baseline:

```text
Validation population:     1,444 planets
Exact final-set matches:   1,281
Mismatches:                  163
Exact-match rate:          88.71%
Generation errors:             0
```

Mismatch shape:

```text
Missing only:               14
Unexpected only:           148
Missing + unexpected:        1

Missing occurrences:        15
    all Water

Unexpected occurrences:   324
    across 38 FormIDs
```

Strong corpus-level pattern:

```text
139 / 163 mismatches predict more than eight resources
another 9 predict eight where canonical contains seven
no single-biome mismatches
```

This is consistent with a still-unrecovered **planet-wide resource/family insertion-limit boundary**, but the exact runtime rule is not proven.

Brief 07A is an investigation-preparation brief.

It must not change generation behavior.

---

# 1. Goal

Build a precise diagnostic dossier for three high-value representative mismatches:

```text
Fermi VII-a
Maal VIII
Fermi III
```

The dossier must reconstruct, from the current reproducer and static canonical data:

1. the complete RNG/generation timeline;
2. biome processing order;
3. Common-root selections;
4. descendant selections and omissions;
5. cache hits;
6. every resource insertion in order;
7. running planet-wide resource count after each insertion;
8. running generated-family/root count after each relevant event;
9. the exact first point where the predicted state becomes incompatible with the canonical final set;
10. what existing Ghidra/repository evidence may correspond to the suspected resource/family limits.

The purpose is to choose the smallest discriminating live/static experiment.

Do not implement a limit.

Do not alter production generation behavior.

---

# 2. Required Reading

Before making changes, read:

```text
AGENTS.md
README.md
docs/ARCHITECTURE.md
docs/BACKLOG.md
docs/DOMAIN-RULES.md
docs/IMPLEMENTATION-WORKFLOW.md

docs/implementation-briefs/05B-producer-update.md
docs/implementation-briefs/05C-bounded-index-conversion-correction.md
docs/implementation-briefs/05D-runtime-bounded-rng-split.md
docs/implementation-briefs/06-full-canonical-validation.md

docs/experiments/05B-algorab-lead-branch.md
docs/experiments/05C-algorab-bounded-index.md
docs/experiments/05D-runtime-bounded-rng-split.md
docs/experiments/06-full-canonical-validation.md
```

Inspect current:

```text
src/starfield_resource_reproducer/domain.py
src/starfield_resource_reproducer/generation.py
src/starfield_resource_reproducer/diagnostics.py
src/starfield_resource_reproducer/validation.py
src/starfield_resource_reproducer/prng.py
```

and relevant tests.

Also inspect repository-held Ghidra notes/exports and prior reverse-engineering documents for evidence related to:

```text
resource slots
generated family/configuration limits
maximum resource count
maximum family count
5-family boundary
8-slot boundary
planet resource insertion
resource array/vector/container
BGSPlanetDataManager
FUN_1415DCFB0
FUN_14157F120
```

Do not infer missing Ghidra evidence from memory if it is not present in the repository/docs.

---

# 3. Representative Planets

The three primary cases are intentionally different.

## 3.1 Fermi VII-a

Brief 06 characterized this as a strong dense-planet representative.

Expected diagnostic value:

```text
- one unexpected descendant;
- predicted final count exceeds canonical;
- cache reuse present;
- useful for testing whether cache/family state interacts with a planet-wide limit.
```

## 3.2 Maal VIII

Expected diagnostic value:

```text
- one unexpected descendant;
- canonical count below the naïve "eight resources" idea;
- no cache reuse;
- strong discriminator against a simple final-cardinality cap.
```

This case is especially important.

Do not assume the limit is:

```python
if len(resources) >= 8:
    stop
```

Maal VIII already suggests the actual state variable is more subtle.

## 3.3 Fermi III

Expected diagnostic value:

```text
- unexpected Common/root-level resource rather than only a descendant;
- no cache reuse;
- useful for determining whether the runtime may stop whole family insertions rather than only descendant expansion.
```

---

# 4. Canonical Comparison Discipline

Use:

```text
PlanetResourceGeneration_v5.csv
Starfield_IRES_Hierarchy.csv
planet-all-resources.csv
```

with the existing canonical loaders.

Compare canonical resources by FormID.

The oracle must not affect generation.

For each representative planet, explicitly list:

```text
predicted final FormIDs/names
canonical final FormIDs/names
missing FormIDs/names
unexpected FormIDs/names
```

Then identify the earliest production event whose insertion is incompatible with the canonical final set.

Do not retroactively alter branches based on canonical membership.

---

# 5. Required Per-Planet Timeline

Produce a deterministic event timeline for each representative.

Every relevant event should include fields equivalent to:

```text
EventIndex
RawDrawNumber
BiomeRuntimePosition
BiomeIndex
BiomeEditorID / useful identity
EffectiveRSGD
Operation
CommonRoot
CurrentStructuralNode
CandidateCount
SelectedCandidate
EmittedResource
CacheHit
PlanetResourceCountBefore
PlanetResourceCountAfter
GeneratedFamilyCountBefore
GeneratedFamilyCountAfter
CanonicalMembershipOfInsertedResource
```

Not every field applies to every event; use null/blank where appropriate.

Important operations include:

```text
shuffle selection
Special selection
Common selection
root emission
descendant inclusion
descendant candidate selection
descendant emission
zero-candidate advance
cache hit
Everywhere/static upstream insertion
```

The timeline must make insertion order visually obvious.

---

# 6. Resource Insertion Ledger

In addition to the full RNG timeline, produce a simplified **resource insertion ledger** per planet.

Example shape:

```text
Seq | Biome | Family Root | Resource | Rarity | Source/Event | Cache? | Count After | Canonical?
```

This should answer, at a glance:

```text
What was the 1st inserted resource?
What was the 5th?
What was the 8th?
What was the first unexpected insertion?
Was it a root or descendant?
Was it generated before or after a cache hit?
```

Include Everywhere and Special resources in the running count, but clearly identify them by category.

Do not assume that the runtime's unknown "slot" concept maps one-to-one to this visible resource count.

Call this a **resource insertion count**, not a proven slot count.

---

# 7. Family/Configuration Ledger

Create a separate family/root ledger.

For each planet, record in runtime processing order:

```text
root selected
new family vs cache hit
family result generated/reused
root emitted?
descendants emitted
running number of distinct generated Common-family configurations
```

Be precise about terminology.

Known/proven behavior:

```text
cache hit:
    family result is reused
    descendant generation is bypassed
```

Unknown:

```text
whether cache hits consume a family/configuration slot
whether a "generated family configuration" corresponds exactly to our cache entries
whether Special/Everywhere resources affect that limit
```

Do not collapse these unknowns.

---

# 8. First-Divergence Analysis

For each planet, identify:

```text
the earliest insertion event that cannot coexist with the canonical final set
```

Classify it structurally:

```text
unexpected Common root
unexpected descendant
unexpected Special
unexpected Everywhere
```

Then report the state immediately before that insertion:

```text
visible predicted resource count
distinct family-cache entry count
number of new Common roots generated so far
number of cache hits so far
current biome position
current effective RSGD
current root
current descendant level
```

This pre-divergence state is the key output of 07A.

---

# 9. Counterfactual Cutoff Table

Build a diagnostics-only cutoff table.

Do not change production.

For each representative planet, ask:

```text
If insertion had stopped before event N, what final set would result?
```

At minimum test candidate thresholds around:

```text
visible insertion count 5
visible insertion count 6
visible insertion count 7
visible insertion count 8
distinct new families 4
distinct new families 5
```

Also test event-relative cutoffs around the actual first unexpected insertion.

The purpose is not to discover the rule by brute force.

The purpose is to show which simple hypotheses are immediately compatible or incompatible with each planet.

Report hypotheses as:

```text
COMPATIBLE WITH THIS CASE
INCOMPATIBLE WITH THIS CASE
NON-DISCRIMINATING
```

Never promote a cutoff to production based on this table.

---

# 10. Cross-Planet Hypothesis Matrix

Produce a compact matrix comparing at least these candidate hypotheses:

```text
H1: hard cap on visible final resource count
H2: hard cap on total insertion attempts
H3: hard cap on distinct Common families/configurations
H4: Special/Everywhere consume visible resource capacity
H5: Special/Everywhere consume a different reserved capacity
H6: cache hits consume family/configuration capacity
H7: cache hits do not consume family/configuration capacity
H8: limit blocks entire new family before root insertion
H9: limit allows root but blocks later descendants
H10: insertion priority/order matters once capacity is reached
```

For each of Fermi VII-a, Maal VIII, and Fermi III, mark:

```text
compatible
incompatible
not discriminated
```

based only on the dossier evidence.

Do not add speculative hypotheses unless the planet timelines motivate them.

---

# 11. Existing Ghidra Evidence Search

Search existing repository/project notes and exports for the previously observed apparent limits.

We have prior contextual references to possible runtime boundaries around:

```text
5 generated Common family configurations
8 resource slots
```

Brief 07A must determine what evidence actually survives in current project materials.

For every relevant code fragment/function found, record:

```text
function/address
source file/export path
comparison constant
container/field offset if known
surrounding operation
branch direction
whether it occurs before or after insertion
whether it appears planet-wide or family-local
confidence/evidence status
```

Do not merely repeat "we saw 5 and 8 before."

Recover the concrete evidence if available.

If the evidence is absent or too weak in the repository, say so explicitly.

---

# 12. Ghidra Candidate Functions

Prioritize evidence around:

```text
FUN_1415DCFB0
FUN_14157F120
BGSPlanetDataManager.cpp-associated functions
callers of FUN_1415DCFB0
resource container insertion helpers
family-cache/container helpers
```

Also search for comparisons against constants:

```text
5
8
0x5
0x8
```

but only in structurally relevant contexts.

Do not perform a broad meaningless constant search across the entire executable dump.

The goal is to identify one or two high-value static anchors suitable for follow-up Ghidra work or live breakpoints.

---

# 13. Diagnostics Changes

Brief 07A may add diagnostics-only instrumentation if needed.

Allowed:

```text
new structured diagnostic event fields
new analysis helpers
new report serializers
test-only/counterfactual analysis helpers
```

Not allowed:

```text
generation rule changes
new stopping conditions
new caps
new cache semantics
new insertion suppression
```

Keep diagnostic additions clearly separated from production behavior.

If generation.py must expose an event already implicit in current code, do so without changing the event order or RNG consumption.

---

# 14. Output Files

Create:

```text
docs/experiments/07A-dense-planet-diagnostic-dossier.md
```

This is the primary human-readable report.

Also create a machine-readable timeline file, preferably:

```text
validation/07A-dense-planet-events.csv
```

or another deterministic repository-local path consistent with Brief 06.

The CSV should include all three planets and enough columns to reconstruct insertion order.

If useful, a second compact file may be created:

```text
validation/07A-dense-planet-insertions.csv
```

Do not create many redundant artifacts.

---

# 15. Human-Readable Report Structure

The 07A experiment report should contain:

```text
1. Objective
2. Evidence status / known limits
3. Fermi VII-a dossier
4. Maal VIII dossier
5. Fermi III dossier
6. Cross-case comparison
7. Counterfactual cutoff matrix
8. Existing Ghidra evidence
9. Candidate runtime hypotheses
10. Recommended next live/static experiment
```

For each planet include:

```text
static inputs
canonical final set
predicted final set
runtime biome order
family ledger
resource insertion ledger
first divergence
pre-divergence state
```

Keep full event dumps in CSV rather than bloating Markdown.

---

# 16. Representative-Control Planets

Use these only if helpful to disambiguate a hypothesis:

```text
Bohr III
Katydid III
Schrodinger II
```

Brief 06 identified them as useful cache / PNDT-override controls.

Do not automatically produce full dossiers for all three.

Only include a control if it materially answers a question raised by the primary cases.

Explain why it was added.

---

# 17. Huygens VII-b / Water

Do not fold the Everywhere/Water discrepancy into this investigation.

Huygens VII-b should remain a separate future experiment.

Water mismatches are structurally distinct:

```text
15 missing occurrences
all Water
14 Water-only mismatches
```

Brief 07A is about unexpected resources on dense planets.

Do not let provisional Everywhere handling contaminate the slot/family-limit inference.

---

# 18. Evidence Vocabulary

Use:

```text
PROVEN
STRONG
PROVISIONAL
COUNTERFACTUAL
```

Examples:

```text
PROVEN:
Fermi VII-a's current reproducer inserts resource X as event N.

PROVEN:
resource X is absent from the canonical oracle.

STRONG:
the corpus pattern is consistent with a planet-wide capacity boundary.

PROVISIONAL:
the runtime may maintain eight insertion slots.

COUNTERFACTUAL:
stopping after seven visible insertions would reproduce this one planet.
```

Do not call a numerical cap PROVEN without static/live evidence.

---

# 19. Recommended Experiment Selection

The final purpose of 07A is to recommend the next reverse-engineering step.

At completion, choose:

```text
one primary planet
one primary function/address or runtime event
one deterministic automated trace boundary
```

Prefer the case that best discriminates between:

```text
visible-resource cap
family/configuration cap
root-vs-descendant suppression
cache-sensitive behavior
insertion-order behavior
```

If existing Ghidra evidence is strong enough to resolve the rule without x64dbg, recommend a static-analysis step instead.

Do not perform the trace in 07A.

---

# 20. No Manual-Stepping Workflow

If a future x64dbg experiment is recommended, design it for automated trace capture.

Preferred pattern:

```text
break at deterministic function/event
StartRunTrace
run/rtr
StopRunTrace
analyze offline
```

Do not recommend manual instruction stepping or register archaeology.

---

# 21. Tests

Add tests for any new diagnostic infrastructure.

At minimum verify:

```text
event ordering is deterministic
resource insertion count is monotonic
family ledger is deterministic
canonical-membership annotation does not affect generation
counterfactual cutoff analysis does not mutate production state
CSV output is deterministic
worked-case generation remains unchanged
```

If the three primary dossiers are encoded in tests, assert only stable structural facts useful for research.

Do not turn speculative cutoff hypotheses into production expectations.

---

# 22. Regression Gate

Before completing 07A, all five established worked cases must remain:

```text
Oberon         exact, 10 draws
Mimas          exact, 10 draws
Decaran VII-b  exact, 10 draws
Kreet          exact, 30 draws
Algorab I      exact, 22 draws
```

The Brief 06 full validation baseline must also remain:

```text
1,444 validation planets
1,281 exact
163 mismatches
88.71% exact
```

If diagnostic code changes any of these, treat that as a bug.

Do not accept a new baseline in 07A.

---

# 23. No Production Algorithm Changes

This is mandatory.

Do not modify:

```text
RNG semantics
biome shuffle
Common selection
descendant selection
zero-candidate consumption
family cache behavior
PNDT override semantics
Everywhere handling
Special handling
resource insertion/stopping rules
```

No new cap should be introduced.

No mismatch should be "fixed."

The output of 07A is evidence and an experiment plan.

---

# 24. Acceptance Criteria

Brief 07A is complete when:

- [ ] full diagnostic dossiers exist for Fermi VII-a, Maal VIII, and Fermi III;
- [ ] each dossier includes canonical and predicted sets;
- [ ] runtime biome order is recorded;
- [ ] Common/family selection order is recorded;
- [ ] cache hits are recorded;
- [ ] every emitted resource is recorded in insertion order;
- [ ] running visible resource count is recorded;
- [ ] running generated-family/cache count is recorded;
- [ ] first canonical-incompatible insertion is identified for each planet;
- [ ] pre-divergence state is captured;
- [ ] counterfactual cutoff analysis is produced without changing production;
- [ ] a cross-planet hypothesis matrix is produced;
- [ ] existing Ghidra/repository evidence for 5/8-style limits is recovered or explicitly reported absent;
- [ ] one primary follow-up planet is recommended;
- [ ] one primary static/runtime anchor is recommended;
- [ ] any proposed x64dbg experiment is automated, not manual-stepping;
- [ ] Huygens VII-b/Water remains out of scope;
- [ ] no generation behavior changes;
- [ ] Brief 06 aggregate baseline remains unchanged;
- [ ] all worked cases remain exact;
- [ ] full test suite passes;
- [ ] CSV/report output is deterministic;
- [ ] canonical CSV files remain unchanged;
- [ ] `git diff --check` passes apart from known line-ending warnings;
- [ ] mojibake scan passes;
- [ ] no commit or push is performed.

---

# 25. Completion Report

When finished, report:

1. files created;
2. files modified;
3. Fermi VII-a canonical vs predicted counts/resources;
4. Fermi VII-a first divergence and pre-divergence state;
5. Maal VIII canonical vs predicted counts/resources;
6. Maal VIII first divergence and pre-divergence state;
7. Fermi III canonical vs predicted counts/resources;
8. Fermi III first divergence and pre-divergence state;
9. insertion-count comparison across all three;
10. family/configuration-count comparison across all three;
11. cache-hit comparison;
12. counterfactual cutoff matrix conclusions;
13. hypotheses ruled out;
14. hypotheses still compatible;
15. recovered Ghidra evidence for apparent 5-family/8-slot limits;
16. relevant function/address candidates;
17. whether current evidence favors slot count, family count, insertion order, or another state variable;
18. primary recommended follow-up planet;
19. primary recommended breakpoint/function/static target;
20. proposed automated trace boundary, if applicable;
21. machine-readable output paths;
22. Markdown experiment-report path;
23. Brief 06 baseline regression result;
24. worked-case regression result;
25. test count/results;
26. whether any generation behavior changed;
27. whether canonical data changed;
28. blockers/questions before the next reverse-engineering step.

Do not commit or push.

---

## Suggested commit after review

If approved:

```text
test: add dense-planet diagnostic dossier
```
