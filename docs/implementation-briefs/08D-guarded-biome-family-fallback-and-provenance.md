# Brief 08D — Guarded biome-family fallback assignment and provenance

## Status

Implementation brief.

This follows Brief 08C and the read-only 08C.1 audit. It addresses the missing **biome-local Common-family assignment** that occurs after the five-tree or shared-eight guards suppress the normal Common selector.

Do not commit or push unless explicitly asked.

## Goal

Extend the reproducer so that it reproduces not only the correct planet-wide inorganic resource set, but also the Common-family resources assigned to each planetary biome after guard fallback.

At the same time, expand provenance so that a biome whose Common resources come from a previously generated family is explicitly identified as reusing/copying that cached family configuration, including where the family was originally generated.

The existing **1,444 / 1,444 planet-wide exact result must remain unchanged**.

---

# Evidence summary

## Existing mechanisms that remain valid

### PROVEN LIVE / STATIC — ordinary new family

A biome normally selects a Common root. If that root has no cached family configuration, the engine generates descendants, caches the resulting family configuration, and assigns it to that biome.

### PROVEN LIVE / STATIC — ordinary cache reuse

A biome normally selects Common root X. If X already has a cached family configuration:

```text
normal Common selector chooses X
→ cache hit
→ no descendant-generation RNG
→ cached root + emitted descendants copied to current biome
```

The current reproducer already models this path correctly through `FamilyAccessResult.family`.

### PROVEN STATIC / LIVE — guard order

Inside `FUN_1415DCFB0`:

```text
five-tree guard
→ shared-eight guard
→ normal Common selector
```

Both guards branch to the same fallback block at approximately:

```text
0x1415DD255
```

The five-tree and shared-eight limits still correctly prevent creation of additional planet-wide family/resource identities.

---

# New recovered mechanism

## PROVEN LIVE — guard does not end biome Common assignment

When either guard suppresses the normal Common selector, the engine enters a fallback assignment stage.

This stage can assign an **already-generated Common family configuration** to the current biome without introducing new planet-wide resource identities.

Therefore the old interpretation:

```text
guard fires
→ Common selector skipped
→ biome receives no Common family
```

is **SUPERSEDED for biome-local execution**.

The correct high-level interpretation is:

```text
guard fires
→ normal Common selector skipped
→ inspect current EffectiveRSGD for Common roots
→ choose an already-generated family according to fallback rules
→ copy chosen cached family configuration into current biome
```

The planet-wide consequence recovered in 08C remains valid: no new Common root/family/resource identity is created by the suppressed normal path.

---

# Fallback candidate construction

## PROVEN LIVE — `FUN_14154C710`

`FUN_14154C710` scans the current biome's effective RSGD.

For each RSGD resource entry:

1. Consider only resources whose IRES category is **Common / category 0**.
2. Record that the RSGD contains at least one Common root.
3. Compare that RSGD Common root FormID against the root FormID of each already-generated cached family.
4. If a root matches, add that cached family to a preferred candidate collection.

Conceptually:

```python
has_common_entries = False
preferred = []

for entry in effective_rsgd.entries_in_stored_order:
    if entry.resource.rarity != COMMON:
        continue

    has_common_entries = True

    for family in generated_families:
        if family.root.form_id == entry.resource.form_id:
            preferred.append(family)
```

Do not introduce chance weighting here. The live helper is matching root identities, not running the category-0 weighted selector.

Ordering must preserve the runtime collection order observed by the engine. Do not sort unless the existing cache/list order is already known to match runtime behavior.

---

# Fallback decision rule

## PROVEN LIVE on Jaffa VII-b

After candidate construction:

```text
if EffectiveRSGD has no Common roots:
    assign no Common family
elif preferred matching cached families is non-empty:
    randomly choose one preferred family
else:
    randomly choose one family from all already-generated families
```

Then copy the selected cached family configuration into the current biome.

In pseudocode:

```python
if not has_common_entries:
    assignment = None
elif preferred_families:
    family = choose_existing_family(preferred_families, rng)
    assignment_mode = GUARD_MATCHED_FALLBACK
else:
    family = choose_existing_family(all_generated_families, rng)
    assignment_mode = GUARD_GENERAL_FALLBACK
```

The selected family is **not regenerated**. No descendant inclusion/candidate-generation sequence runs.

---

# Fallback RNG

## PROVEN LIVE — helper chain

Fallback family choice uses `FUN_14015B4A0`.

The bounded choice is a float-scaled index, not the rejection-based integer helper used by biome shuffle.

The observed arithmetic is equivalent to:

```python
index = trunc(float32(random_probability * float32(candidate_count)))
```

with lower bound zero for this call site.

The random-float call at:

```text
0x1401190CD
```

is a direct jump thunk to the already-recovered:

```text
FUN_140924800 at 0x140924800
```

Therefore fallback selection uses the existing proven MT19937 → binary32 probability helper.

### PROVEN LIVE — candidate count 1 still consumes RNG

A one-element fallback candidate list still invokes the random-float helper and consumes the normal RNG draw. Do **not** optimize bound 1 to zero RNG consumption.

### Distinct RNG mechanisms remain distinct

Do not consolidate these:

1. biome shuffle bounded integer rejection helper;
2. descendant candidate-selection float-scaled index;
3. Special/Common weighted probability selector;
4. guard-fallback family-selection float-scaled index.

Fallback family selection is closest to #2 in arithmetic shape, but give it a semantically distinct operation/event.

---

# Jaffa VII-b live control case

The live run generated these planet-scope families before capacity fallback:

```text
Lead     → Lead, Tungsten, Titanium, Dysprosium
Chlorine → Chlorine, Chlorosilanes
Iron     → Iron
```

After the shared-eight guard:

### No-Common RSGD case

An effective RSGD containing only Water / Everywhere had no Common roots:

```text
preferred = []
has_common_entries = false
→ no Common family assignment
```

### Matched fallback: Lead

Effective RSGD Common roots included:

```text
Uranium
Lead
```

Lead already existed:

```text
preferred = [Lead family]
→ random choice with bound 1
→ Lead family copied
→ Pb, W, Ti, Dy
```

### General fallback

Effective RSGD Common roots included:

```text
Nickel
Copper
```

Neither family existed:

```text
preferred = []
has_common_entries = true
all generated families = [Lead, Chlorine, Iron]
→ random choice with bound 3
→ Lead selected in live trace
→ Pb, W, Ti, Dy
```

### Matched fallback: Iron

Effective RSGD Common roots included:

```text
Iron
Nickel
```

Iron already existed:

```text
preferred = [Iron family]
→ random choice with bound 1
→ Iron copied
→ Fe
```

These assignments match the Creation Kit observations for Jaffa VII-b:

```text
Volcanic → Pb W Ti Dy
Hills    → Fe
Plateau  → Pb W Ti Dy
```

The implementation should determine biome identity from the reproducer's actual shuffled processing/result mapping, not hard-code these names.

---

# Other CK observations to use as regression targets

These were the per-biome mismatches that exposed the missing fallback mechanism.

## Bara VII-d

```text
Hills
  CK: Fe
```

Current path identified by the 08C.1 audit: five-tree guard.

## Indum IV-d

```text
Swamp
  CK: H2O, Fe, Ta

Sandy Desert
  CK: Cu, F, Au, Sb

Wetlands
  CK: H2O, Cu, F, Au, Sb
```

Current path identified by audit: shared-eight guard.

## Zeta Ophiuchi I

```text
Swamp
  CK: H2O, Pb, Ag

Frozen Dunes
  CK: H2O, Fe, HnCn, Ta, Yb

Deciduous Forest
  CK: H2O, Fe, HnCn, Ta, Yb

Savanna
  CK: H2O, Fe, HnCn, Ta, Yb
```

Current path identified by audit: shared-eight guard.

## Pyraas VIII-a

```text
Sandy Desert
  CK: Cl, SiH3Cl
```

Current path identified by audit: five-tree guard.

These are regression evidence, not heuristics. Do not special-case planets, biomes, resources, or names.

---

# Required provenance model

The user explicitly requires provenance to show when one biome receives a previously generated family's resources.

The model should distinguish **family configuration origin** from **current biome assignment mechanism**.

## Required Common assignment mechanisms

Use a clear enum or equivalent explicit representation. Suggested semantic values:

```text
NEW_FAMILY
NORMAL_CACHE_REUSE
GUARD_MATCHED_FALLBACK
GUARD_GENERAL_FALLBACK
NO_COMMON_ASSIGNMENT
```

Names may differ if existing domain conventions suggest better names, but the distinctions must be preserved.

### `NEW_FAMILY`

Current biome normally selected root X and generated the cached family configuration for the first time.

### `NORMAL_CACHE_REUSE`

Current biome normally selected root X and reused an already-generated cached family X.

### `GUARD_MATCHED_FALLBACK`

Normal Common selector was suppressed by a guard. The current effective RSGD contained root X, X already had a cached family, and that family was selected from the preferred matching candidate collection.

### `GUARD_GENERAL_FALLBACK`

Normal Common selector was suppressed by a guard. The current effective RSGD had Common roots, but none matched an existing cached family. A family was selected from the full already-generated family collection.

### `NO_COMMON_ASSIGNMENT`

No Common family was assigned. Preserve enough reason information to distinguish at least:

```text
no Common entries in effective RSGD during guard fallback
```

from ordinary selector returning no result if those are represented by the same high-level type.

---

# Family origin provenance

Every cached `ResourceFamilyResult`, or a closely associated immutable provenance object, must retain the origin at which that exact family configuration was first generated.

At minimum:

```text
origin_biome_index
origin_biome_form_id
origin_biome_name
origin_processing_position
root_form_id
```

Also retain effective RSGD provenance if natural in the existing model:

```text
origin_effective_rsgd_form_id
origin_rsgd_source
```

Do not describe runtime semantics as if the later biome literally copies from another biome object unless proven.

Preferred terminology:

```text
family configuration originally generated while processing biome X
```

The engine appears to reuse a planet-scope cached family configuration. The source biome is the **origin of generation**, not necessarily a direct source-object copy.

---

# Per-biome assignment representation

Every biome result should make its Common-family assignment directly recoverable without reconstructing it from planet-wide insertion events.

A reporting layer should be able to answer:

```text
Biome: Plateau
Assigned Common family: Lead
Resources: Pb, W, Ti, Dy
Assignment mechanism: GUARD_GENERAL_FALLBACK
Family configuration origin biome: <origin>
Candidate mode: general existing-family fallback
```

Do not require consumers to infer biome membership from:

```text
occupied_new_slot
RESOURCE_SLOT_OCCUPIED
planet.family_results
```

Those answer different questions.

---

# Resource occurrence / provenance bookkeeping

A guard fallback copies an already-existing family configuration into another biome without occupying new planet-wide resource slots.

Record biome-context occurrences for the copied root and emitted descendants, analogous to ordinary cache reuse, while preserving:

```text
occupied_new_slot = false
```

for already-occupied FormIDs.

Do not let `PlanetResourceState.at_capacity` suppress recording of an occurrence for a resource identity that already exists. Capacity constrains new identities; it must not erase biome-local assignment provenance.

If current `PlanetResourceState.record()` already supports this behavior for duplicate identities, reuse it rather than creating parallel bookkeeping.

The occurrence or associated assignment metadata must allow the caller to identify the assignment mechanism as guard fallback rather than ordinary cache reuse.

---

# Water / Everywhere and Special remain independent

Per-biome output must combine independently:

```text
Everywhere assignment
Special assignment
Common-family assignment
```

A guard-fallback Common family does not replace or suppress an existing Everywhere resource such as Water.

Examples:

```text
Indum IV-d Wetlands
  H2O from Everywhere
  Cu/F/Au/Sb from guard fallback Common-family assignment
```

Keep provenance separate for each occurrence.

Do not alter existing atmosphere semantics.

---

# Five-tree and shared-eight guard semantics

Both guards suppress the **normal Common selector** and enter the fallback assignment stage.

Preserve which guard triggered the fallback.

Suggested metadata:

```text
guard_reason:
    COMMON_TREE_LIMIT
    SHARED_RESOURCE_CAPACITY
```

This is separate from `assignment_mechanism`.

Example:

```text
guard_reason = SHARED_RESOURCE_CAPACITY
assignment_mechanism = GUARD_MATCHED_FALLBACK
```

or:

```text
guard_reason = COMMON_TREE_LIMIT
assignment_mechanism = GUARD_GENERAL_FALLBACK
```

Do not claim the two guards are semantically identical beyond entering this recovered fallback block.

---

# Data structure guidance

Audit the existing:

```text
BiomeFamilyGenerationResult
FamilyAccessResult
ResourceFamilyResult
ResourceOccurrence
PlanetResourceState
```

Prefer extending existing immutable domain/results structures over creating a reporting-only shadow model.

One reasonable shape would be an explicit immutable Common assignment result attached to each biome, conceptually:

```python
CommonFamilyAssignment(
    family: ResourceFamilyResult | None,
    mechanism: CommonAssignmentMechanism,
    guard_reason: GuardReason | None,
    cache_hit: bool,
    origin: FamilyOrigin | None,
    candidate_roots: tuple[...],
    selected_family_root: ResourceRef | None,
    rng_draw: ...,
)
```

This exact class design is **not mandatory**. Preserve architectural coherence with the existing code.

The important requirement is that the semantics above be first-class and unambiguous.

---

# Generation algorithm integration

In `_run_planet()`:

1. Run Special exactly as now.
2. Evaluate five-tree guard.
3. Evaluate shared-eight guard.
4. If neither guard fires:
   - run normal Common weighted selector;
   - use existing new-family/cache-reuse behavior.
5. If a guard fires:
   - do **not** run the normal Common selector;
   - scan the effective RSGD's stored resource entries for category-0 roots;
   - build preferred candidates by root match against existing cached families;
   - if no Common roots exist: no Common assignment and no fallback RNG draw;
   - if preferred candidates exist: consume one fallback-selection RNG draw and select from them;
   - otherwise: consume one fallback-selection RNG draw and select from all generated families;
   - assign/copy the selected cached family to the biome;
   - record biome-context occurrences for its root and emitted descendants;
   - do not alter the family cache;
   - do not generate descendants;
   - do not occupy new planet-wide slots.
6. Continue with the same RNG state into later biome processing.

If the fallback reaches a state with Common entries but an empty global family cache, do not invent behavior. Determine whether the control flow makes that state impossible under the guards; otherwise represent it defensively and document it as unreachable/OPEN unless evidence exists.

---

# Fallback-selection helper

Implement a semantically named helper using the existing proven binary32 probability primitive.

Do not use the biome-shuffle bounded integer helper.

For candidate count `N > 0`:

```python
roll = existing_probability_float(rng)  # exact existing FUN_140924800 semantics
index = trunc(float32(roll * float32(N)))
```

Preserve the project's existing float32 discipline exactly.

For `N == 1`, still consume the draw.

For `N == 0`, do not call the helper.

If an existing descendant candidate-index helper is exactly bit-compatible, it may be reused internally, but diagnostics and semantic naming must still identify this as **fallback family selection**, not descendant selection.

---

# Diagnostics

Add diagnostic events sufficient to reconstruct the fallback without inference.

Suggested events/fields:

```text
COMMON_GUARD_FALLBACK_BEGIN
  biome
  guard_reason
  generated_family_count
  occupied_resource_count

COMMON_GUARD_FALLBACK_CANDIDATES
  has_common_entries
  rsgd_common_roots
  matching_family_roots
  candidate_mode = MATCHED | GENERAL | NONE

COMMON_GUARD_FALLBACK_ROLL
  candidate_count
  raw draw / converted probability if consistent with existing diagnostics
  selected_index
  selected_family_root

COMMON_GUARD_FALLBACK_ASSIGNED
  family root
  family origin biome
  assigned resources
  guard reason
  assignment mechanism
```

Names may differ to fit current `EventKind`, but diagnostics must preserve:

- why normal Common selection was skipped;
- whether effective RSGD had Common entries;
- preferred matched candidate set;
- whether matched or general pool was used;
- RNG consumption;
- selected cached family;
- family origin;
- current target biome.

Do not relabel fallback assignment as `COMMON_SELECTED`; normal selector selection and fallback family assignment are distinct mechanisms.

---

# Tests

Add focused tests for all recovered branches.

## Unit tests

At minimum:

1. Guard + no Common RSGD entries:
   - no Common family assignment;
   - zero fallback-selection RNG draws.

2. Guard + one matching cached family:
   - matching family assigned;
   - exactly one fallback RNG draw even with candidate count 1;
   - no descendant RNG;
   - no new planet-wide slot;
   - provenance points to origin biome.

3. Guard + multiple matching cached families:
   - candidate pool contains only matches;
   - one float-scaled RNG choice.

4. Guard + Common entries but zero matches:
   - pool becomes all generated families;
   - one float-scaled RNG choice;
   - mechanism `GUARD_GENERAL_FALLBACK`.

5. Five-tree guard enters fallback.

6. Shared-eight guard enters fallback.

7. Fallback copy records later-biome occurrences with `occupied_new_slot=False`.

8. Ordinary cache reuse remains distinct from guard fallback.

9. Bound 1 consumes RNG.

10. No descendant-generation RNG on any fallback copy.

## Live-evidence regression — Jaffa VII-b

Assert per-biome Common-family output reproduces the CK observations:

```text
Volcanic → Pb W Ti Dy
Hills    → Fe
Plateau  → Pb W Ti Dy
```

along with whatever non-Common biome resources are independently present.

Also assert the expected assignment mechanisms from the recovered trace mapping once the code identifies the exact shuffled biome correspondence.

## CK regression set

Add focused tests for:

```text
Bara VII-d — Hills → Fe

Indum IV-d:
  Swamp → H2O, Fe, Ta
  Sandy Desert → Cu, F, Au, Sb
  Wetlands → H2O, Cu, F, Au, Sb

Zeta Ophiuchi I:
  Swamp → H2O, Pb, Ag
  Frozen Dunes → H2O, Fe, HnCn, Ta, Yb
  Deciduous Forest → H2O, Fe, HnCn, Ta, Yb
  Savanna → H2O, Fe, HnCn, Ta, Yb

Pyraas VIII-a:
  Sandy Desert → Cl, SiH3Cl
```

Use stable FormIDs/resources from the canonical source datasets. Do not hard-code display strings where repository conventions prefer IDs.

---

# Validation

After implementation:

1. Run focused tests.
2. Run full test suite.
3. Run mojibake guard.
4. Re-run full 1,444-body canonical planet-wide validation.
5. Confirm:

```text
1444 / 1444 exact
0 mismatches
0 errors
```

6. Produce a biome-local verification report for the CK regression planets above.
7. Report any remaining CK biome mismatches separately.

The existing planet-wide oracle does not validate biome mapping. Do not claim corpus-wide biome validation unless a biome-local oracle is introduced.

---

# Documentation updates

Update relevant architecture/evidence docs to distinguish:

```text
planet-wide unique identity generation
planet-wide family configuration cache
per-biome Common-family assignment
guarded fallback assignment
Everywhere assignment
Special assignment
provenance occurrence bookkeeping
```

Explicitly mark the old “guard means no Common biome family” interpretation as superseded.

Preserve evidence labels.

Recommended documentation wording:

> **PROVEN LIVE:** after the five-tree or shared-eight guard suppresses the normal Common selector, `FUN_1415DCFB0` can assign an already-generated family configuration to the current biome. Matching cached roots present in the current effective RSGD form a preferred candidate pool; if Common roots exist but none match, the engine selects from all generated families. If the effective RSGD has no Common roots, no Common family is assigned.

And:

> **PROVEN LIVE:** fallback family selection uses `FUN_14015B4A0`, which obtains its random probability through thunk `FUN_1401190CD → FUN_140924800`; a one-element candidate pool still consumes the RNG draw.

---

# Provenance output requirement

Provide or extend a reporting helper so that a caller can obtain a biome-centric view resembling:

```text
Biome: Plateau

H2O
  provenance: Everywhere

Pb
W
Ti
Dy
  provenance: Common family
  assignment: GUARD_GENERAL_FALLBACK
  family root: Lead
  family configuration origin biome: <origin biome>
  guard: SHARED_RESOURCE_CAPACITY
```

Do not flatten this to a bare resource set in the underlying domain model.

The reproducer's future planner use case needs to distinguish:

- a resource generated/established by this biome;
- a normally reused cached family;
- a family copied by guard matched fallback;
- a family copied by guard general fallback;
- Everywhere;
- Special;
- atmosphere.

---

# Non-goals

Do not:

- alter the recovered biome shuffle;
- alter Special selection;
- alter Everywhere discovery;
- alter atmosphere inheritance;
- change descendant inclusion or candidate selection;
- change the five-tree limit;
- change the shared-eight limit;
- use CK observations as planet-specific heuristics;
- introduce oracle data into production generation;
- claim retail `Starfield.exe` proof where the live evidence is from Creation Kit Galaxy View Apply.

---

# Deliverable

Implement the recovered guard-fallback biome assignment and provenance model, then report:

1. changed files;
2. tests added/updated;
3. focused test results;
4. full test-suite result;
5. mojibake check;
6. 1,444-body planet-wide validation result;
7. CK biome-regression results;
8. any remaining biome-local mismatches or OPEN questions;
9. no commit/push unless explicitly requested.
