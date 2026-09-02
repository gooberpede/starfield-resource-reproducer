# Brief 10C — Canonical source ingestion and enriched occurrence model

## Status

Implementation brief for:

```text
gooberpede/starfield-resource-reproducer
```

This brief follows:

- Brief 10A — canonical occurrence-export gap analysis;
- Brief 10A.1 — CSV standardization and maintained xEdit script synchronization;
- Brief 10A.2 — Resource Tree provenance;
- Brief 10B — canonical xEdit export audit and dataset refresh.

The canonical source-data layer is now in place.

Current canonical production inputs:

```text
data/planet-resource-generation.csv
data/ires-hierarchy.csv
data/planet-atmospheric-resources.csv
data/planet-directory.csv
```

Validation-only oracle:

```text
data/planet-all-resources.csv
```

The purpose of 10C is to make the reproducer ingest and preserve all canonical metadata required by the future occurrence exporter, while keeping the protected v1.0 generation algorithm unchanged.

Do **not** implement the final occurrence CSV exporter in this brief.

Do **not** modify xEdit scripts unless an unexpected source-data defect is discovered and reported first.

Do **not** modify `starfield-outpost-network`.

Do **not** commit or push unless explicitly asked.

---

# Core objective

After 10C, the reproducer should be able to produce a typed, deterministic, fully enriched in-memory occurrence view from the four canonical source datasets.

That enriched view must contain everything 10D will need to serialize:

```text
Planet × Location × Resource × ResourceOrigin
```

without:

- consulting the validation oracle;
- reading downstream dictionaries;
- re-parsing raw CSVs inside the exporter;
- performing opaque ad hoc joins in export code;
- changing generation/RNG semantics.

10C is an ingestion/model/result-shaping task.

10D will be serialization.

---

# Standing constraints

Read and follow current `AGENTS.md`.

Preserve the protected v1.0 model:

```text
1,444 / 1,444 exact
0 mismatches
0 errors
```

No generation behavior may change unless a genuine regression reveals an existing implementation defect.

The canonical source inputs are independent from the validation-only oracle.

Missing input remains missing/unknown; do not convert missing channels into false empty results.

Preserve UTF-8 and mojibake safeguards.

---

# 1. Add Planet Directory ingestion

Add a loader for:

```text
data/planet-directory.csv
```

Current schema:

```text
SourceFile
ExtractTimestamp
PlanetFormID
PlanetEditorID
PlanetName
BodyType
StarSystemID
SystemName
ParentPlanetID
PlanetID
PlanetNotLandable
OceanWorld
```

## Required domain representation

Introduce a small immutable/value-style body-directory record.

Suggested conceptual fields:

```text
source_file
extract_timestamp
planet_form_id
planet_editor_id
planet_name
body_type
star_system_id
system_name
parent_planet_id
planet_id
planet_not_landable
ocean_world
```

Use existing project naming/style conventions rather than forcing these exact Python attribute names if the repository has a stronger established pattern.

## Required key

Index by:

```text
PlanetFormID
```

Do not use the numeric hierarchy tuple as the primary identity.

## Required loader validation

At minimum validate:

- required header/schema;
- one row per `PlanetFormID`;
- no duplicate `PlanetFormID`;
- exactly one file-wide `ExtractTimestamp`;
- parseability of numeric hierarchy fields;
- parseability/normalization of boolean/flag fields according to actual canonical values;
- nonblank canonical body identity fields where required.

Do not invent data for blank fields.

---

# 2. Integrate Planet Directory into project-level canonical data

The project-level loaded-data structure should gain access to the body directory.

Conceptually:

```text
ProjectData
    generation planets
    IRES hierarchy
    atmosphere records
    planet directory
```

Use the actual current aggregate/domain type if it has another name.

The directory should be available by `PlanetFormID`.

Do not force directory metadata directly into existing generation `Planet` objects if that would blur source responsibilities.

Prefer keeping:

```text
generation-domain Planet
```

and:

```text
canonical body-directory metadata
```

distinct but joinable.

Reason:

- 1,776 directory bodies exist;
- only 1,444 have generation input;
- 297 have atmospheric-resource input;
- the union of current occurrence channels is 1,445 bodies.

A directory body is metadata, not evidence that a terrestrial or atmospheric resource channel exists.

---

# 3. Cross-input coherence validation

Add explicit canonical-input coherence checks.

These checks should fail fast with useful diagnostics if regenerated xEdit datasets drift out of alignment.

## Generation → Directory

Every `PlanetFormID` in:

```text
planet-resource-generation.csv
```

must exist in:

```text
planet-directory.csv
```

For overlapping fields, validate equality where semantics are truly the same:

```text
PlanetEditorID
PlanetName
SourceFile / PlanetSourceFile semantics
```

Do not compare fields whose exporters intentionally derive values differently unless 10B established semantic identity.

## Atmosphere → Directory

Every atmospheric `PlanetFormID` must exist in the directory.

Validate compatible body identity fields where appropriate.

## Generation ↔ Atmosphere

Where a body occurs in both channels, validate compatible canonical identity metadata.

Do not require all generation bodies to have atmosphere rows.

Do not require all atmosphere bodies to have generation rows.

Volii Alpha must remain valid:

```text
directory present
atmosphere present
generation absent
```

## IRES identity coherence

Where the same `ResourceFormID` appears across:

```text
generation RSGD data
IRES hierarchy
atmosphere data
```

validate stable identity fields where available:

```text
FormID
EditorID
Name
Rarity
SourceFile
```

Only compare fields that are actually present in both authoritative sources.

If a source does not carry rarity, do not manufacture or pretend it does.

---

# 4. Retain IRES source provenance

`ires-hierarchy.csv` now carries:

```text
SourceFile
ExtractTimestamp
FormID
EditorID
Name
Rarity
ChildSourceFile
ChildFormID
ChildEditorID
ChildName
ChildRarity
```

Update the IRES loader/domain model so source-plugin provenance is preserved for both:

```text
parent IRES
child IRES
```

Every graph-produced resource identity should retain its canonical source plugin.

This fixes the 10A gap where descendants could be fully identified but lose `ResourceSourceFile`.

## Required behavior

For parent nodes:

```text
ResourceRef.source_file = SourceFile
```

or equivalent.

For child nodes:

```text
ResourceRef.source_file = ChildSourceFile
```

or equivalent.

Leaf rows must remain valid with blank child fields.

Do not infer child source from parent source.

Retain the file extraction timestamp in the loaded dataset metadata if the repository has an appropriate input-metadata representation.

It does **not** need to be copied onto every resource object.

---

# 5. Preserve canonical dataset metadata cleanly

The four xEdit exports each contain a repeated file-production timestamp.

10C should provide a clean way to retain source-dataset metadata without polluting every domain object.

At minimum the loaded project data should be able to expose, per canonical input:

```text
filename / logical dataset identity
ExtractTimestamp
```

Potentially also row count if naturally useful.

Do not over-engineer a generalized metadata framework.

The purpose is:

- diagnostics;
- future manifest production;
- cross-input reproducibility;
- avoiding accidental loss of known source timestamps.

This is source extraction metadata, distinct from the future 10D `ExportTimestamp`.

---

# 6. Freeze canonical resource-origin vocabulary

The future occurrence dataset needs stable origin semantics.

Current internal provenance should map losslessly to these output/domain concepts:

```text
ATMOSPHERE
EVERYWHERE
SPECIAL
COMMON_ROOT
DESCENDANT
```

10C should define this vocabulary in a typed/domain-level way suitable for the future exporter.

Do not merely hard-code strings in 10D later.

If existing enums differ, add a clear semantic mapping or rename only where safe and justified.

Important:

```text
COMMON_ROOT
```

means the accepted root resource occurrence of a Common family.

It is not the same thing as:

```text
NEW_FAMILY
NORMAL_CACHE_REUSE
GUARD_MATCHED_FALLBACK
GUARD_GENERAL_FALLBACK
```

Those describe family assignment mechanism, not resource origin.

Do not collapse these concepts.

---

# 7. Freeze effective-RSGD source vocabulary

10A/10B deliberately did not force a lossy vocabulary.

The source pipeline preserves relationship evidence equivalent to:

```text
BIOM
PNDT
PNDT+BIOM
```

The future occurrence output needs one stable semantic field:

```text
RSGDSource
```

10C should define a lossless typed vocabulary.

Recommended:

```text
BIOM
PNDT
PNDT_AND_BIOM
```

or equivalent existing enum names.

Do **not** map both:

```text
PNDT distinct override
```

and:

```text
PNDT + BIOM both reference the same effective RSGD
```

to one ambiguous `PNDT_OVERRIDE` value.

If an additional semantic convenience such as `is_pndt_override` is useful internally, derive it separately.

The occurrence export should preserve the underlying relationship evidence.

---

# 8. Expose complete family-origin lineage

Brief 10A found that Common/Descendant occurrences already have:

```text
root_form_id
common_assignment_mechanism
```

while family origin remains reachable indirectly through the family cache.

10C should make this lineage explicit and easy to consume.

For every accepted occurrence with origin:

```text
COMMON_ROOT
DESCENDANT
```

the enriched occurrence view must expose:

```text
CommonAssignmentMechanism
FamilyRootFormID
FamilyRootEditorID
FamilyOriginBiomeIndex
FamilyOriginBiomeFormID
```

The source of truth for family origin remains the cached `ResourceFamilyResult.origin` or current equivalent.

Do not reconstruct origin by scanning prior occurrences heuristically.

## Important semantics

`FamilyOriginBiomeIndex` means:

> the biome processing occurrence in which this cached family configuration was first generated.

It does not mean:

> the biome from which a later biome was literally copied.

For cache reuse and guard fallback, retain the original family-generation biome.

---

# 9. Introduce a typed enriched occurrence view

Add a domain/result-layer representation that 10D can serialize directly.

Name it according to repository conventions.

Conceptually it should represent one accepted resource occurrence plus all canonical context needed for output.

It should be built after generation from existing immutable/result state, not mutate algorithmic generation objects unnecessarily.

## Required semantic groups

### Body context

```text
SystemName
PlanetName
BodyType
PlanetFormID
PlanetEditorID
StarSystemID
ParentPlanetID
PlanetID
PlanetSourceFile
```

from Planet Directory.

### Location context

Common:

```text
LocationType
```

with:

```text
BIOME
ATMOSPHERE
```

Biome rows:

```text
BiomeIndex
BiomeFormID
BiomeEditorID
BiomeName
BiomeChance
BiomeSourceFile
```

Atmosphere rows:

```text
AtmosphereFormID
AtmosphereEditorID
AtmosphereSourceFile
```

### Resource identity

```text
ResourceFormID
ResourceEditorID
ResourceName
Rarity
ResourceSourceFile
ResourceOrigin
```

Do not add downstream display names.

### Effective RSGD context for biome occurrences

```text
EffectiveRSGDFormID
EffectiveRSGDEditorID
RSGDSource
RSGDSourceFile
```

Atmosphere rows leave these absent/null.

### Common-family lineage

For Common root/descendant occurrences only:

```text
CommonAssignmentMechanism
FamilyRootFormID
FamilyRootEditorID
FamilyOriginBiomeIndex
FamilyOriginBiomeFormID
```

Other origins leave these absent/null.

### Atmospheric defining-ATMO lineage

For atmosphere rows:

```text
ResourceDefinedByAtmosphereFormID
ResourceDefinedByAtmosphereEditorID
ResourceDefinedByAtmosphereSourceFile
AtmosphereInheritanceDepth
```

Biome rows leave these absent/null.

---

# 10. ResourceCategory remains an export-contract concern

Do not add application/display enrichment.

The future occurrence file is an inorganic-resource product, so 10D may serialize:

```text
ResourceCategory = Inorganic
```

as a constant for compatibility/explicitness.

10C does not need to pollute every in-memory occurrence with a redundant category field unless the typed view benefits materially from it.

If omitted internally, document that 10D adds it as a deterministic product constant.

---

# 11. Accepted occurrences only

The enriched occurrence view must represent accepted resource occurrences only.

Use the established accepted-state semantics:

```text
occupies_state == true
```

or the actual current equivalent.

Do not include:

- capacity-rejected attempts;
- failed candidate attempts;
- `NO_COMMON_ASSIGNMENT`;
- diagnostic-only traversal events.

These remain diagnostics.

---

# 12. Atmosphere and Volii Alpha

Atmosphere occurrences must be representable independently of terrestrial generation input.

The enriched occurrence builder must support:

```text
directory + atmosphere
without generation Planet
```

Volii Alpha is the required regression case.

Expected semantic behavior:

```text
Volii Alpha
    2 accepted ATMOSPHERE occurrences
    no BIOME occurrences
```

Do not drop a body simply because generation input is absent.

Do not fabricate a synthetic `PlanetGenerationResult` with empty biome content just to make the join convenient.

---

# 13. Biome occurrence identity

Preserve planet-local biome identity as:

```text
PlanetFormID
BiomeIndex
BiomeFormID
```

Do not use `BiomeFormID` alone as a location key.

The same BIOM record may be referenced by multiple PNDT biome entries.

The enriched occurrence view must retain `BiomeIndex`.

---

# 14. Preserve different resource origins separately

Do not deduplicate occurrences solely by:

```text
Planet
Biome
Resource
```

If the same accepted resource occurs in the same biome through different mechanisms, preserve distinct enriched occurrences by `ResourceOrigin`.

Future 10D uniqueness validation is expected to distinguish at least:

```text
PlanetFormID
LocationType
BiomeIndex
BiomeFormID
ResourceFormID
ResourceOrigin
```

for biome occurrences.

Do not serialize yet, but ensure 10C's in-memory representation does not destroy this distinction.

---

# 15. Do not change generation semantics

This brief may require reshaping result access, but the generator itself must remain behaviorally identical.

Avoid:

- adding RNG calls;
- reordering generation;
- changing cache behavior;
- changing state occupancy;
- changing provenance creation timing;
- changing Special/Common/Everywhere behavior;
- changing guard fallback;
- changing descendant behavior.

If an enriched view can be built from existing immutable result state, prefer that over inserting export-specific state into the live generation path.

---

# 16. Suggested architecture boundary

Prefer:

```text
raw canonical CSV
    ↓
loader/domain source records
    ↓
protected generation model
    ↓
PlanetGenerationResult / atmospheric accepted state
    ↓
enrichment/projection layer
    ↓
typed canonical occurrence view
```

Then 10D becomes:

```text
typed canonical occurrence view
    ↓
stable sort / schema validation
    ↓
CSV + optional manifest
```

Do not make 10D responsible for reconstructing model relationships.

---

# 17. Tests

Add focused tests for every new contract.

At minimum cover:

## Planet Directory loader

- 1,776 rows;
- unique FormIDs;
- one extraction timestamp;
- representative planet;
- representative moon;
- representative orbital;
- Volii Alpha ocean-world flags.

## Cross-input coherence

- generation bodies all found in directory;
- atmosphere bodies all found in directory;
- Volii Alpha valid despite absent generation input;
- intentional mismatch fixture produces useful failure.

## IRES provenance

- parent source retained;
- child source retained independently;
- leaf child source blank;
- descendant resource gets canonical source plugin.

## Enriched biome occurrence

Use an existing known regression body and assert:

- body-directory metadata;
- biome index/FormID;
- effective RSGD provenance;
- resource origin;
- resource source plugin.

## Common family lineage

Use a case exercising:

```text
NEW_FAMILY
NORMAL_CACHE_REUSE
```

and, if practical with current fixtures:

```text
GUARD_MATCHED_FALLBACK
GUARD_GENERAL_FALLBACK
```

Assert family origin remains the original generation biome.

## Atmosphere occurrence

Assert:

- effective ATMO identity;
- defining ATMO identity;
- source plugins;
- inheritance depth;
- no biome/RSGD/common-family fields.

## Volii Alpha

Assert:

```text
2 atmosphere enriched occurrences
0 biome enriched occurrences
```

without treating missing generation input as empty terrestrial proof.

## Origin separation

Add or reuse a fixture where the same resource/location can be represented through distinct origins if such a canonical case exists.

If no current canonical example exists, test the typed view/invariant using a focused constructed fixture rather than inventing a game-specific claim.

---

# 18. Full regression verification

Run the complete test suite.

Expected:

```text
138 existing tests + new 10C tests
all pass
```

Run canonical validation.

Required invariant:

```text
1,444 / 1,444 exact
0 mismatches
0 errors
```

Any change to the established generation result is a regression unless explained by a pre-existing defect with evidence.

Also run:

```text
python scripts/check_mojibake.py
git diff --check
```

and repository UTF-8 safeguards.

---

# 19. Documentation

Update current-state documentation as necessary.

Likely files:

```text
README.md
AGENTS.md
docs/ARCHITECTURE.md
docs/DOMAIN-RULES.md
docs/BACKLOG.md
docs/CANONICAL-XEDIT-EXPORTS.md
```

Document:

- Planet Directory is now an ingested canonical source;
- IRES source provenance is retained;
- enriched occurrence view architecture;
- origin/RSGD vocabularies;
- family-origin lineage access;
- distinction between production inputs and validation oracle.

Do not rewrite historical experiment/implementation-brief evidence.

---

# 20. Out of scope

Do **not**:

- write `planet-resource-occurrences.csv`;
- choose final CSV column ordering;
- add export timestamp production logic;
- add a manifest;
- remove `planet-all-resources.csv`;
- migrate downstream consumers;
- modify `starfield-outpost-network`;
- change xEdit extraction schemas;
- add display-name enrichment;
- implement GUI/API/database work.

Those belong to 10D, 10E, or later downstream work.

---

# Acceptance criteria

10C is complete when:

1. `planet-directory.csv` is loaded and validated as a fourth canonical input;
2. project-level data exposes directory metadata by `PlanetFormID`;
3. cross-input coherence is validated;
4. IRES parent/child source-plugin provenance survives loading;
5. canonical input extraction timestamps are retained cleanly;
6. stable typed vocabularies exist for resource origin and effective-RSGD source;
7. Common/Descendant occurrences expose complete family-root/origin lineage;
8. an enriched accepted-occurrence view exposes all canonical context required by 10D;
9. atmosphere-only bodies such as Volii Alpha are supported without fabricated terrestrial state;
10. rejected/diagnostic events remain outside the product occurrence view;
11. the protected generation algorithm remains unchanged;
12. full tests and 1,444/1,444 validation pass.

---

# Deliverable report

Report:

1. files changed;
2. Planet Directory loader/domain representation;
3. canonical input metadata handling;
4. cross-input validation rules added;
5. IRES provenance changes;
6. resource-origin vocabulary;
7. RSGD-source vocabulary;
8. family-origin enrichment approach;
9. enriched occurrence view structure;
10. Volii Alpha handling;
11. tests added;
12. total test result;
13. canonical 1,444-body validation result;
14. mojibake/UTF-8/diff-check results;
15. confirmation generation/RNG semantics did not change;
16. confirmation no 10D exporter was implemented;
17. confirmation no commit/push was performed.

Suggested commit message after review:

```text
feat: add canonical occurrence ingestion model
```
