# Brief 07B — Integrate Atmospheric Resources, Provenance-Aware Planet State, and Recovered Special/Everywhere Semantics

Repository:

```text
gooberpede/starfield-resource-reproducer
D:\Projects\starfield-resource-reproducer
```

## Why this is Brief 07B

Brief 07A was the diagnostic/mismatch-analysis pass. This is the natural continuation of the same phase: take the mechanisms isolated during that investigation and integrate them into the reproducer before starting a new phase of residual mismatch research.

Do not rename or fold this into a generic “Brief 07”. Treat it as **Brief 07B**.

---

# 1. Objective

Update the standalone reproducer so that it incorporates the newly recovered planet-generation mechanisms without collapsing their provenance.

The major changes are:

1. load `data/Starfield_PlanetAtmosphericResources.tsv` as a fourth first-class input dataset;
2. represent atmospheric resource occurrences separately from RSGD-derived occurrences;
3. model the proven pre-main-generation ordering:
   - atmospheric resource prepopulation;
   - category-6 / Everywhere pre-pass across all biome/effective-RSGD work;
   - shuffled per-biome generation;
4. update category-5 / Special selection to the now-proven selector behavior;
5. preserve resource provenance through generation and diagnostics;
6. treat the shared eight-resource capacity as a set/count of **unique resource FormIDs** unless implementation evidence in the current code makes that impossible;
7. explicitly avoid inventing a “vapor exception” to the eight-resource limit;
8. rerun the full validation corpus after the implementation and report the new residual mismatch population.

This brief is primarily an implementation/integration task, not a new reverse-engineering expedition.

---

# 2. Current project state

The current loader describes itself as loading “the three canonical Starfield CSV datasets” and `ProjectData` currently contains:

```text
planets
ires_nodes
oracle
```

That boundary now needs to expand to include atmospheric resources.

The current generation layer already contains explicit structures for:

```text
Everywhere
Special
Common roots
descendant families
family cache
```

but some of the surrounding semantics were provisional when implemented. Replace those provisional assumptions only where the new research has resolved them.

Preserve existing correct behavior, tests, diagnostics, and API compatibility where reasonable.

---

# 3. Required reading before editing

Read:

```text
AGENTS.md
README.md
pyproject.toml

src/starfield_resource_reproducer/domain.py
src/starfield_resource_reproducer/load_data.py
src/starfield_resource_reproducer/prng.py
src/starfield_resource_reproducer/generation.py
src/starfield_resource_reproducer/candidates.py
src/starfield_resource_reproducer/diagnostics.py
src/starfield_resource_reproducer/validation.py
src/starfield_resource_reproducer/dossier.py
src/starfield_resource_reproducer/cli.py
```

Inspect the existing tests before changing public/domain shapes.

Also inspect the actual new file:

```text
data/Starfield_PlanetAtmosphericResources.tsv
```

Do **not** assume its exact schema from this brief. Read the header and representative rows first, then design the loader around the real export.

The existing canonical static inputs remain:

```text
data/PlanetResourceGeneration_v5.csv
data/Starfield_IRES_Hierarchy.csv
data/planet-all-resources.csv
```

The atmospheric TSV is now a fourth first-class dataset.

---

# 4. Evidence state to implement

## 4.1 High-level planet-generation order

Current best-supported architecture:

```text
planet orchestration
    |
    |-- atmospheric resource prepopulation
    |
    |-- category 6 / Everywhere pre-pass
    |      over every biome/effective RSGD
    |
    `-- shuffled per-biome main generation
           |
           |-- category 5 / Special weighted selector
           |
           |-- category 0 / Common weighted selector
           |
           `-- descendants 1..4
```

Atmosphere and Everywhere occur **before the first per-biome generator call**.

Special does **not** receive a separate planet-wide pre-pass. It is evaluated inside each biome's main generation turn, immediately before Common-root selection.

---

## 4.2 Shared planet-wide resource state

A single shared resource-ID state is passed through the generation machinery.

Live/static evidence supports a capacity guard of:

```text
8 unique resource IDs
```

for this internal state.

Atmospheric resources, Everywhere resources, Special resources, Common roots, and emitted descendants all interact with this shared state.

Important:

> Do not model the capacity as “eight provenance-specific occurrences”.

The engine state observed in the recovered code is a container of resource FormIDs.

At the same time:

> Do not discard provenance merely because capacity is FormID-based.

These are two separate concerns.

---

# 5. Provenance is a first-class requirement

The reproducer must be able to distinguish **how** a resource appeared even when final player-facing identity is the same FormID.

At minimum distinguish:

```text
ATMO
EVERYWHERE
SPECIAL
COMMON
DESCENDANT
```

If existing structures make a more precise distinction useful, retain additional context such as:

```text
planet
biome
effective RSGD
RSGD source (PNDT / BIOM / PNDT+BIOM)
root family
descendant rarity
```

Do not collapse all resource emissions directly into one set.

A useful conceptual separation is:

```text
ResourceOccurrence
    resource
    provenance
    biome/source context

PlanetResourceState
    occurrences
    occupied_resource_ids
```

The exact class names are up to the implementation, but the semantics are not.

---

# 6. Critical identity/provenance example

A planet may have the same IRES resource through two mechanisms:

```text
ATMO: Chlorine [000057D5]
RSGD: Chlorine [000057D5]
```

For research and validation these are distinct occurrences:

```text
(000057D5, ATMO)
(000057D5, RSGD-derived provenance)
```

For capacity accounting, the current working model is:

```text
occupied_resource_ids = {000057D5}
```

not two slots.

Therefore the implementation must permit:

```text
multiple occurrences
one unique occupied FormID
```

without losing either provenance record.

---

# 7. Do not invent a vapor exception

We have observed/described cases such as:

```text
H2O + H2O (vapor)
Cl  + Cl  (vapor)
```

The current hypothesis is **not**:

```text
“vapor resources are exempt from the 8-resource limit”
```

Instead, test/model the simpler engine-shaped explanation:

> Atmospheric and RSGD appearances of the same IRES FormID may be two provenance-specific occurrences but one unique resource-ID slot.

The implementation should therefore use unique FormID identity for shared-slot accounting unless contrary code/data evidence is discovered during this task.

Do not introduce any hard-coded special case for:

```text
Water
Chlorine
vapor
atmosphere
```

with respect to capacity.

If the atmospheric TSV reveals separate FormIDs for what is displayed as `<resource> (vapor)`, report that explicitly rather than assuming identity.

---

# 8. Atmospheric loader

Add a loader for:

```text
data/Starfield_PlanetAtmosphericResources.tsv
```

## 8.1 Inspect the real schema

Before implementation:

- read the header;
- inspect representative:
  - one-resource planets;
  - two-resource planets;
  - local ATMO overrides;
  - inherited ATMO values if provenance/depth fields are present;
  - any empty/no-resource representation if included.

Do not manufacture columns that are not in the file.

---

## 8.2 Loader responsibilities

The atmospheric loader should:

- parse TSV, not CSV;
- validate required columns;
- normalize `PlanetFormID` through existing `FormId`;
- normalize atmospheric resource FormIDs through `FormId`;
- preserve all useful exporter provenance fields;
- detect duplicate rows that would be contradictory;
- permit multiple atmospheric resources per planet;
- associate atmospheric resources with planets without modifying RSGD definitions;
- expose atmospheric resources independently in `ProjectData`.

If the file contains only planets with one or more resources and omits explicit zero-resource planets, absence should mean “no atmospheric resource row in this export”, not malformed input.

---

## 8.3 Domain shape

Introduce a small immutable atmospheric domain representation.

Prefer an explicit occurrence/record type rather than:

```python
dict[FormId, frozenset[FormId]]
```

because exporter provenance may matter later.

For example, conceptually:

```text
AtmosphericResourceRecord
    planet_form_id
    resource_form_id
    resource metadata if exported
    ATMO provenance fields
    inheritance/source depth if exported
```

and:

```text
atmospheric_resources: dict[FormId, tuple[AtmosphericResourceRecord, ...]]
```

Exact naming is flexible.

Do not contaminate `RSGDDefinition` or `RSGDResourceEntry` with ATMO fields.

---

# 9. Update `ProjectData` and project loading

Update the project-data boundary so atmospheric records are a first-class member.

Conceptually:

```text
ProjectData
    planets
    ires_nodes
    oracle
    atmospheric_resources
```

Update the main project loader/CLI path to accept the atmospheric TSV.

If CLI arguments currently assume exactly three inputs, extend them coherently.

Prefer a clear explicit argument/path rather than silently discovering a file by filename in arbitrary working directories.

Update help text and README usage if required.

---

# 10. Atmospheric prepopulation semantics

Before the Everywhere pre-pass and before the first main biome generation:

1. obtain all effective atmospheric inorganic resources for the planet from the new dataset;
2. record one `ATMO` occurrence for each atmospheric record;
3. insert each resource FormID into the shared occupied-ID state if not already present;
4. do not consume RNG;
5. do not treat the atmospheric resource as an RSGD result;
6. preserve stable input order if the export provides meaningful order.

Capacity behavior:

- a new atmospheric FormID occupies one shared slot;
- an atmospheric FormID already present should not occupy a second slot;
- preserve the additional occurrence/provenance even if no new slot is consumed.

Do not silently truncate atmospheric input to fit eight without diagnostics. If an impossible/contradictory case is encountered, emit an explicit diagnostic or validation failure consistent with project style.

---

# 11. Everywhere / category 6 — replace provisional modeling with recovered behavior

## 11.1 Proven structural behavior

Before any `FUN_1415DCFB0`-equivalent per-biome generation:

```text
for every biome work object / effective RSGD:
    inspect category-6 entries
    if the helper resolves an Everywhere resource:
        associate it with that biome's Everywhere field
        append/deduplicate its FormID into shared planet state
```

The Maal VIII live trace showed the pre-pass genuinely visits **all four** biome/effective-resource contexts, even after one Everywhere resource was found.

Therefore:

- do not stop globally after finding the first Everywhere resource;
- do not model Everywhere as a post-shuffle operation;
- do not model it as category-5-style weighted selection unless existing recovered evidence specifically proves the helper uses that behavior;
- keep the distinct Everywhere mechanism.

---

## 11.2 Physical semantics remain narrower than capacity semantics

Do not claim in code/comments/docs that an Everywhere resource is physically generated in every biome.

What is proven is:

- category-6 entries receive privileged pre-main-generation handling;
- a selected Everywhere resource is associated with a biome work object;
- its FormID enters the shared planet resource-ID state.

Use terminology such as:

```text
Everywhere pre-pass
pre-main-generation category-6 handling
```

rather than stronger physical claims.

---

# 12. Special/Common selector — implement the newly proven behavior

The static Ghidra investigation of:

```text
FUN_141580660
```

resolved the selector.

It is category-generic:

```text
one MT19937 draw
→ binary32 probability in [0, 0.99999]
→ ordered 0x238-byte RSGD entry scan
→ filter resource category by requested category
→ cumulative += chance(category) / 100
→ return first entry where roll < cumulative
```

Relevant recovered addresses, for comments/docs only where useful:

```text
0x1415806A8  one MT19937 probability draw
0x14157C5AA  category comparison
0x14157C5BE  read category-indexed chance
0x14157C5CA  cumulative threshold update
0x14157C5E3  select if roll < cumulative
```

Implementation consequences:

### Special

```text
select(category = 5)
```

- always consumes exactly one raw MT word;
- does so even with:
  - zero eligible Special candidates;
  - one eligible candidate;
  - a 100% Special candidate;
- scans RSGD entries in stored order;
- accumulates `special_chance / 100`;
- chooses the first threshold hit;
- may return no selection;
- if selected, the Special FormID attempts to occupy shared resource state before Common selection.

### Common

```text
select(category = 0)
```

uses the exact same selector machinery, but the category-0 chance column.

Do not maintain separate ad hoc Special RNG behavior.

---

# 13. Callisto regression case

Add/update a targeted regression around:

```text
Callisto
single biome: CrateredNoLife09
effective RSGD: CrateredNoLifeDefaultRes
```

Relevant RSGD configuration:

```text
Iron       Common   30
Aluminum   Common   70
Helium-3   Special 100
```

Observed live sequence:

```text
Special selector:
    category 5
    → Helium-3

shared unique resource count:
    0 → 1

Common selector:
    category 0
    → Iron

shared unique resource count:
    1 → 2
```

The important regression assertions are:

- Special consumes one selector draw despite 100% chance;
- Common consumes the next selector draw;
- Helium-3 is recorded with `SPECIAL` provenance;
- Iron is recorded with `COMMON` provenance;
- both participate in the same shared unique-FormID capacity state.

Do not assert Aluminum is generated; it is merely the losing Common candidate.

---

# 14. Maal VIII atmospheric regression case

Add/update a regression around Maal VIII sufficient to prove the new atmospheric stage is actually wired into generation.

Known atmospheric resource:

```text
Chlorine [000057D5]
```

The regression should establish at minimum:

```text
before main biome generation:
    Chlorine has ATMO provenance
    Chlorine's FormID occupies the shared resource state
```

If Water is also present through Everywhere in the same fixture/data path, assert the ordering:

```text
ATMO Chlorine
then Everywhere Water
then main biome generation
```

Do not overfit the test to undocumented pointer/order details from the CK trace.

---

# 15. Duplicate-FormID / multiple-provenance regression

Add a synthetic unit-level test even if a convenient canonical planet is awkward.

Construct a small controlled case in which:

```text
ATMO supplies Resource X
RSGD generation later supplies Resource X
```

Assert:

```text
occurrences:
    X / ATMO
    X / RSGD-derived provenance

occupied_resource_ids:
    contains X once

capacity consumed by X:
    one slot
```

This test is important because a naive implementation using only a final set would pass capacity but lose provenance, while a naive list implementation would preserve provenance but consume two slots.

The design must do both correctly.

Label this behavior in comments/tests as the current **engine-shaped capacity model**. If the exact duplicate append/dedup semantics are not yet formally proven at every insertion site, do not mislabel broader semantics as PROVEN.

---

# 16. Eight-resource capacity integration

The shared capacity check must be centralized enough that all mechanisms observe the same planet-wide state.

At minimum:

```text
ATMO
Everywhere
Special
Common root
descendant emission
```

must not each maintain independent counts.

Prefer a small state abstraction rather than scattered:

```python
if len(...) < 8
```

checks.

Conceptually:

```text
PlanetResourceState
    occupied IDs
    provenance occurrences
    capacity = 8

record_occurrence(...)
try_occupy(resource_form_id, ...)
```

The exact API is up to Codex.

Important distinction:

```text
occurrence count != occupied slot count
```

---

# 17. Capacity and descendant behavior

Do not regress the already proven descendant helper guard:

```text
if shared unique resource count >= 8:
    return current structural node
    consume no RNG
```

The descendant structural traversal semantics already recovered remain in force.

Likewise preserve:

- root emitted unconditionally after a new Common family is selected, subject to the caller's capacity path;
- family cache behavior;
- cache hit consumes no descendant RNG;
- zero-candidate descendant behavior;
- distinct bounded RNG implementations for:
  - biome shuffle;
  - descendant candidate selection.

Do not “simplify” these RNG mechanisms into a common helper.

---

# 18. Generation result shape

Extend `PlanetGenerationResult` or related structures so downstream validation can ask both:

```text
What unique resources does the planet ultimately contain?
```

and:

```text
How did each resource occurrence arise?
```

At minimum expose:

```text
atmospheric resources/occurrences
Everywhere resources/occurrences
Special resources/occurrences
Common resources/occurrences
descendant resources/occurrences
final unique predicted FormIDs
```

Avoid forcing every consumer to reconstruct provenance from diagnostic events.

Diagnostics should remain rich, but provenance belongs in the result model as data.

---

# 19. Validation semantics

This is critical.

The existing `planet-all-resources.csv` oracle is known to omit at least some atmosphere-derived resources.

Therefore do **not** simply compare:

```text
ATMO + RSGD final union
```

against:

```text
planet-all-resources.csv
```

and call differences failures.

Instead preserve separate validation views.

At minimum produce:

```text
RSGD/CK-visible prediction channel
ATMO prediction channel
final player-facing union
```

The exact semantic contract of `planet-all-resources.csv` remains unresolved.

Current evidence supports:

```text
PROVEN:
planet-all-resources.csv omits at least some atmospheric resources

STRONG / PROVISIONAL:
it closely resembles the CK/biome-visible resource set

OPEN:
its exact SurveyAggregator semantic contract
```

Do not rename it definitively to “biome oracle”.

---

# 20. Atmospheric validation

Validate the new loader/data path independently:

```text
Starfield_PlanetAtmosphericResources.tsv
    ↔ reproducer atmospheric channel
```

Since this dataset is itself the source of atmospheric inputs, this is primarily loader/integrity validation, not an independent oracle.

Useful checks include:

- all atmospheric PlanetFormIDs resolve to known planets where expected;
- no contradictory duplicate planet/resource records;
- resource FormIDs have coherent metadata against known IRES/RSGD metadata where overlap exists;
- multi-resource atmospheric planets load correctly.

Do not require every atmospheric resource to appear in `planet-all-resources.csv`.

---

# 21. Full-corpus rerun

After implementation:

1. run the complete test suite;
2. rerun the full canonical validation corpus;
3. generate a fresh mismatch report;
4. compare headline metrics with the pre-07B baseline.

Pre-07B baseline:

```text
population:       1,444
exact:            1,281
mismatches:         163
exact rate:       88.71%
```

The old mismatch population was heavily associated with dense/resource-capacity cases and atmospheric resources.

Do not promise a target exact-match rate.

The purpose is to discover the **new residual population after proven mechanisms are integrated**.

---

# 22. Required post-run analysis

Report at least:

```text
population
exact count
mismatch count
exact rate
generation-only count
oracle-only count
both-sides count
errors
```

Also stratify residual mismatches by useful characteristics where existing tooling permits:

```text
predicted unique resource count
presence of atmospheric resources
presence of Everywhere
presence of Special
single- vs multi-biome
capacity reached or not
```

If provenance-aware comparison reveals cases where:

```text
final FormID set matches
but provenance/mechanism does not
```

report those separately.

Do not allow final-set agreement to hide a mechanism failure.

---

# 23. Diagnostics

Add diagnostic events only where they materially improve traceability.

Useful new events may include:

```text
ATMOSPHERIC_RESOURCE_LOADED
RESOURCE_OCCURRENCE_RECORDED
RESOURCE_SLOT_OCCUPIED
RESOURCE_SLOT_ALREADY_OCCUPIED
RESOURCE_CAPACITY_REACHED
EVERYWHERE_PREPASS_BEGIN/END
```

Use project naming conventions rather than these exact names if appropriate.

Diagnostics should make it possible to answer:

```text
Why is this FormID in the result?
Did it consume a new slot?
What provenance(s) contributed it?
At what shared count?
```

Avoid noisy per-row loader diagnostics in normal operation.

---

# 24. Loader/file-format boundaries

`Starfield_PlanetAtmosphericResources.tsv` is TSV.

Do not weaken the existing CSV loader globally merely to support TSV.

A clean option is to generalize the internal row reader to accept a delimiter while retaining explicit public loaders.

For example:

```text
load_generation_data(...)        CSV
load_ires_data(...)              CSV
load_oracle_data(...)            CSV
load_atmospheric_data(...)       TSV
```

Do not infer format from filename extension if explicit parsing is simpler and safer.

Update module docstrings that currently claim there are only three canonical datasets.

---

# 25. Source metadata coherence

Where an atmospheric resource FormID overlaps a known IRES/RSGD resource FormID:

- verify compatible identity/name/editor metadata if both sources provide it;
- do not import RSGD rarity/category onto the atmospheric occurrence as if ATMO itself authored that category;
- retain the resource's identity metadata separately from its occurrence provenance.

For example:

```text
Resource identity:
    Chlorine [000057D5]

Occurrence provenance:
    ATMO
```

is different from:

```text
RSGD category:
    Common / Special / Everywhere
```

Do not describe an ATMO Chlorine occurrence itself as “Common” merely because the IRES record's static category is Common.

---

# 26. README/documentation updates

Update the reproducer README sufficiently to explain:

```text
four input datasets
atmospheric resources are a first-class input
provenance-aware generation
shared unique-FormID capacity model
validation-channel distinction
```

Keep research archaeology in the research repository; the reproducer README should explain the operational model and evidence qualification needed to use the code correctly.

---

# 27. Tests

Add targeted tests for at least:

- atmospheric TSV parsing;
- multiple atmospheric resources on one planet;
- malformed atmospheric FormID;
- contradictory duplicate atmospheric row if applicable;
- ProjectData inclusion;
- ATMO prepopulation ordering;
- Special one-draw semantics with 100% candidate;
- Special zero-candidate still consumes one selector draw;
- Common ordered cumulative 30/70 behavior;
- ATMO + RSGD same FormID preserves two provenance occurrences but one capacity slot;
- capacity shared across ATMO / Everywhere / Special / Common / descendants;
- descendant capacity early return consumes no RNG;
- Callisto;
- Maal VIII atmospheric prepopulation;
- existing regression suite remains green.

Prefer canonical fixtures where convenient and minimal synthetic fixtures where they isolate a mechanism better.

---

# 28. Evidence labels in comments/docs

Continue using:

```text
PROVEN
STRONG
PROVISIONAL
COUNTERFACTUAL
SUPERSEDED
```

Be precise.

Examples:

```text
PROVEN:
Special/Common selector consumes exactly one MT word per call.

PROVEN:
Special is evaluated inside the per-biome generator before Common.

PROVEN:
Atmospheric resource(s) are prepopulated before main biome generation in observed CK path.

STRONG:
Shared capacity is best modeled as unique resource FormIDs when preserving duplicate provenance occurrences.

OPEN:
Exact capacity behavior for every possible same-FormID cross-provenance collision has not been live-tested.

OPEN:
Exact semantic contract of planet-all-resources.csv.
```

Do not upgrade the duplicate-slot model beyond the evidence just because it is architecturally plausible.

---

# 29. Non-goals

Do not under this brief:

- perform new x64dbg traces;
- perform new Ghidra reverse engineering;
- modify xEdit exporters;
- re-decode ATMO REFL/RDIF serialization;
- investigate atmosphere inheritance;
- invent vapor-specific capacity exceptions;
- infer the exact SurveyAggregator contract;
- “fix” residual mismatches with heuristics;
- alter IRES hierarchy semantics;
- merge the two proven bounded RNG mechanisms;
- redesign the CLI beyond what atmospheric input requires;
- commit;
- push.

---

# 30. Stop conditions

Stop implementation when:

1. atmospheric data is loaded as a first-class project input;
2. provenance is represented explicitly;
3. shared unique-FormID resource state is used across generation mechanisms;
4. atmosphere prepopulation is integrated;
5. Everywhere pre-pass reflects the recovered ordering;
6. Special/Common selector reflects the recovered weighted logic and RNG consumption;
7. targeted tests pass;
8. the full suite passes;
9. full-corpus validation has been rerun;
10. residual mismatches are reported without speculative fixes.

If residual mismatches remain, **do not chase them under this brief**.

They are the input to the next research/implementation decision.

---

# 31. Required final report

At completion provide:

1. concise implementation summary;
2. actual atmospheric TSV schema discovered;
3. domain-model changes;
4. loader changes;
5. provenance representation;
6. shared capacity representation;
7. generation-order changes;
8. Special/Common selector changes;
9. tests added/updated;
10. full test-suite result;
11. pre-07B vs post-07B validation metrics;
12. residual mismatch stratification;
13. any final-set-match / provenance-mismatch cases;
14. files changed;
15. `git diff --check`;
16. UTF-8/mojibake scan result;
17. `git status --short`;
18. suggested commit message.

Do not commit.

Do not push.

---

# 32. Suggested commit message after review

If the implementation survives review:

```text
feat: integrate atmospheric resource generation
```

A documentation-heavy alternative is not preferred here because this brief materially changes loader/domain/generation behavior.

---

# 33. Central design invariant

Keep this distinction visible throughout the implementation:

```text
RESOURCE IDENTITY / CAPACITY
    unique IRES FormID

RESOURCE OCCURRENCE / PROVENANCE
    ATMO
    Everywhere
    Special
    Common
    Descendant
```

One resource may have multiple occurrences/provenances while occupying only one shared resource-ID slot.

That is the key architectural requirement of Brief 07B.
