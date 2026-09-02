# Brief 10A — Canonical resource-occurrence export gap analysis

## Status

Analysis-only brief for `gooberpede/starfield-resource-reproducer`.

This is the first post-v1.0 data-product task.

The purpose is to determine exactly what canonical information the reproducer already has, what it can derive, and what additional authoritative game-file data must be added to the input pipeline before the reproducer can emit a self-contained canonical replacement candidate for the old planet-level `planet-all-resources.csv`.

Do **not** implement the final CSV exporter in this brief. Do **not** modify `starfield-outpost-network`. Do **not** fill gaps from the existing `planet-all-resources.csv`. Do **not** commit or push unless explicitly asked.

## Goal

We want the reproducer eventually to produce a canonical occurrence dataset with a grain conceptually equivalent to:

```text
Planet × Location × Resource
```

where:

```text
LocationType = BIOME
or
LocationType = ATMOSPHERE
```

The intended product is a viable self-contained successor candidate to the old planet-level resource file.

The gap analysis must answer:

> What fields should that file contain, which of those fields are already available to the reproducer, which are derived by the reproducer, and which require new or modified xEdit exports?

The answer must be concrete enough to drive the next xEdit-export revision brief.

## Scope boundary

This exercise belongs entirely to `starfield-resource-reproducer`.

The future consumer migration is a separate project.

Do not:

- modify `starfield-outpost-network`;
- change its current resource source file or build scripts;
- design its future biome-aware UI;
- add downstream display-name aliases or spelling normalization;
- import curated application dictionaries into the reproducer.

The reproducer's domain is canonical game-derived data plus deterministic reproducer-generated metadata.

## Core canonical-data rule

Every eventual occurrence-export field must belong to one of these classes:

```text
A. directly sourced from canonical game/plugin records;
B. deterministically derived from those canonical records by the proven reproducer;
C. neutral export/reproducer metadata generated during production.
```

It must **not** depend on:

```text
the old planet-all-resources.csv as enrichment
starfield-outpost-network dictionaries
bespoke spelling/display-name overrides
manual repair tables
web/community data
```

The old `planet-all-resources.csv` may be used only as a comparison/validation reference.

## Current canonical inputs to audit

At minimum audit:

```text
data/PlanetResourceGeneration_v5.csv
data/Starfield_IRES_Hierarchy.csv
data/Starfield_PlanetAtmosphericResources.tsv
```

Also audit the current loaders/domain objects/results to determine which source fields are preserved versus discarded after loading.

Treat:

```text
data/planet-all-resources.csv
```

as validation-only.

## Existing external canonical body-data source to inspect

The separate `starfield-outpost-network` repository currently contains:

```text
reference-source/planet-directory.tsv
```

and uses it as canonical body metadata.

This is relevant because it demonstrates that some desired metadata is already obtainable from xEdit/game data.

However:

- do not make the reproducer depend directly on the outpost-network repository;
- do not simply copy the file as an implementation shortcut in this brief;
- identify the underlying exporter/data fields and recommend how they should become part of the reproducer's own canonical input pipeline.

Determine whether the existing Planet Directory exporter can be reused unchanged, should be extended, or whether equivalent fields belong in another canonical export.

## Candidate output grain

The future CSV should represent distinct resource occurrences, not a prematurely deduplicated planet-resource set.

Examples:

```text
Planet A + Hills + Water
Planet A + Swamp + Water
Planet A + Atmosphere + Water
```

are distinct rows.

Biome rows should be keyed by planet-local PNDT biome identity:

```text
BiomeIndex + BiomeFormID
```

Do not assume BIOM FormID alone is a unique planet-local occurrence key.

Atmosphere rows should not invent a fake biome. They should use:

```text
LocationType = ATMOSPHERE
AtmosphereFormID = effective ATMO FormID
```

with biome fields blank.

## Candidate output schema to audit

This is a candidate, not yet a frozen contract.

### 1. Production metadata

```text
ReproducerVersion
ExportTimestamp
```

`ExportTimestamp` is one file-production timestamp repeated on every row. It describes when the output file was generated, not when any game record was authored.

A richer sidecar manifest may be proposed separately, but the CSV itself must retain at least the production timestamp.

### 2. Body identity and provenance

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

For each, identify the canonical record/property source and answer:

- already present in `PlanetResourceGeneration_v5.csv`?
- present in another current xEdit export?
- direct game-record data or exporter-derived?
- complete for the current v1.0 population?

### 3. Location identity

Common discriminator:

```text
LocationType
```

Expected values:

```text
BIOME
ATMOSPHERE
```

Biome fields:

```text
BiomeIndex
BiomeFormID
BiomeEditorID
BiomeName
BiomeChance
BiomeSourceFile
```

Audit canonical source, current input availability, loader/model retention, and atmosphere-row nullability.

Atmosphere fields:

```text
AtmosphereFormID
AtmosphereEditorID
AtmosphereSourceFile
```

Audit whether the current atmospheric TSV contains all three, whether `AtmosphereFormID` is the effective inherited ATMO record associated with the planet, and whether provenance distinguishes ATMO source from resource-record source.

Do not invent an atmosphere display name unless it is canonical and useful.

### 4. Resource identity and provenance

```text
ResourceCategory
ResourceFormID
ResourceEditorID
ResourceName
Rarity
ResourceSourceFile
```

For the current product, `ResourceCategory` may be constant `Inorganic`, but retaining it may improve compatibility.

Do **not** add `ResourceDisplayName`.

`ResourceName` remains the canonical game/export value. Player-facing spelling, spacing, aliasing, localization, or UI enrichment belongs downstream.

Determine:

- authoritative current input for each field;
- whether atmosphere and biome rows can use one consistent resource identity source;
- whether IRES loading preserves source-plugin provenance;
- whether anything currently comes only from the old oracle.

### 5. Generation/origin provenance

Candidate:

```text
ResourceOrigin
```

Assess values such as:

```text
ATMOSPHERE
EVERYWHERE
SPECIAL
COMMON_ROOT
DESCENDANT
```

Verify whether the classification can be generated deterministically from current occurrence/result provenance.

Do not conflate resource rarity with generation origin.

### 6. Effective RSGD provenance

Candidate biome fields:

```text
EffectiveRSGDFormID
EffectiveRSGDEditorID
RSGDSource
RSGDSourceFile
```

Expected `RSGDSource` concepts include `BIOM` and `PNDT_OVERRIDE`, or current domain equivalents.

Answer:

- does the current loader retain all values?
- are they present on every biome result?
- should Everywhere, Special, Common and Descendant rows carry them?
- should atmosphere rows leave them blank?

### 7. Common-family assignment lineage

Candidate:

```text
CommonAssignmentMechanism
FamilyRootFormID
FamilyRootEditorID
FamilyOriginBiomeIndex
FamilyOriginBiomeFormID
```

Potential mechanisms already established:

```text
NEW_FAMILY
NORMAL_CACHE_REUSE
GUARD_MATCHED_FALLBACK
GUARD_GENERAL_FALLBACK
NO_COMMON_ASSIGNMENT
```

Determine at what row grain these are meaningful.

Likely rule to assess:

```text
COMMON_ROOT and DESCENDANT rows:
    carry Common-family assignment lineage

EVERYWHERE / SPECIAL / ATMOSPHERE rows:
    lineage fields blank
```

Answer:

- does each descendant have unambiguous family-root access?
- does the result model preserve family-origin biome index/FormID?
- does `NO_COMMON_ASSIGNMENT` belong in a resource-occurrence CSV at all?
- should no-assignment remain diagnostic instead?

Be willing to recommend omitting fields whose semantics do not fit occurrence-row grain.

## File-level versus row-level provenance

Follow the established lightweight export convention:

```text
one repeated file-production timestamp
+
record/source provenance columns where relevant
```

Do not burden the CSV with every possible build detail.

A future optional sidecar manifest may carry:

```text
input filenames
input hashes
input extraction timestamps
Git commit SHA
schema version
production command
row counts
```

but the CSV must remain independently interpretable if separated from the manifest.

## Required gap-analysis matrix

Produce a Markdown field-by-field matrix:

| Candidate Output Field | Meaning / Grain | Classification | Current Source | Current Loader/Model Availability | Gap? | Required Action | Notes |
|---|---|---|---|---|---|---|---|

`Classification`:

```text
CANONICAL_SOURCE
REPRODUCER_DERIVED
EXPORT_METADATA
```

`Gap?`:

```text
NO
PARTIAL
YES
QUESTION
```

For every `YES` or `PARTIAL`, name the recommended upstream change.

Do not guess field origins.

## Required current-input inventory

For each current canonical input, document:

```text
file
row grain
primary record type(s)
key columns
source/provenance columns
file-production timestamp behavior
fields used by current loader
fields discarded by current loader
```

At minimum:

```text
PlanetResourceGeneration_v5.csv
Starfield_IRES_Hierarchy.csv
Starfield_PlanetAtmosphericResources.tsv
```

Also inventory the external `planet-directory.tsv` as a candidate upstream source/export shape.

## Required loader/model inventory

Inspect the current reproducer path:

```text
CSV/TSV column
→ loader object
→ domain object
→ generation result
→ ResourceOccurrence / biome view
```

Distinguish:

```text
data absent from source export
vs
data present in source export but discarded by loader/model
vs
data already available in final result
```

For each desired field, identify the earliest point where it disappears or becomes unavailable.

Only the first category requires xEdit changes.

## Required xEdit-export recommendations

For every true source-data gap, specify which exporter should be changed or added.

Do not write Pascal/xEdit code in this brief.

Recommendations should identify:

```text
record type
field/property to export
desired column name
provenance column(s)
expected row grain
whether value repeats per file or per record
```

Possible outcomes:

```text
A. extend PlanetResourceGeneration exporter
B. extend IRES hierarchy exporter
C. extend atmospheric-resource exporter
D. formalize/reuse Planet Directory exporter as a fourth canonical reproducer input
E. no xEdit change — loader only
F. no change — already available
```

Where an existing exporter already produces a value elsewhere, recommend reuse/refactoring rather than duplicate extraction logic where practical.

## Population coverage analysis

The final occurrence candidate should be self-contained for every body it claims to cover.

Identify:

- body population in `PlanetResourceGeneration_v5.csv`;
- body population in atmospheric export;
- body population in candidate Planet Directory metadata;
- important differences between these sets;
- treatment of water worlds/orbitals/not-landable bodies;
- treatment of missing generation input.

Volii Alpha is an important negative-control case:

```text
atmospheric input known
PNDT/biome generation input absent
```

State whether the eventual CSV should include known ATMOSPHERE rows and omit unsupported BIOME rows rather than dropping the body entirely.

Do not infer terrestrial rows.

## Compatibility comparison with old `planet-all-resources.csv`

Use the old file only to answer:

```text
Which existing columns would the new canonical file preserve?
Which old capabilities would improve?
Which old columns require new canonical body metadata?
```

Do not use it to fill any gap.

Include a short compatibility table:

```text
Old column
→ proposed new equivalent
→ source authority
→ same semantics / changed semantics
```

Call semantic differences out explicitly.

The new file grain is not `Planet × Resource`, so direct row-count comparison is not meaningful.

## Proposed uniqueness/key rules

Recommend canonical row identity rules for the future exporter.

Candidates to assess:

### BIOME occurrence

```text
PlanetFormID
LocationType
BiomeIndex
ResourceFormID
ResourceOrigin
```

### ATMOSPHERE occurrence

```text
PlanetFormID
LocationType
AtmosphereFormID
ResourceFormID
```

Do not freeze these blindly.

Explicitly answer:

> Should multiple same-resource occurrences in one biome with different origins be preserved as separate rows, or collapsed to one biome/resource row with combined provenance?

Default toward preserving information unless there is a strong reason to collapse it.

## Ordering rules

Recommend deterministic export ordering.

It must be stable across runs with identical inputs and must not depend on incidental dictionary iteration.

## Output of this brief

Create a durable analysis document:

```text
docs/CANONICAL-OCCURRENCE-EXPORT-GAP-ANALYSIS.md
```

It should contain:

1. proposed purpose and grain;
2. candidate output schema;
3. current input inventory;
4. current loader/model inventory;
5. field-by-field gap matrix;
6. xEdit exporter changes required;
7. loader/model changes required later;
8. population/coverage analysis;
9. compatibility comparison to old `planet-all-resources.csv`;
10. recommended uniqueness and ordering rules;
11. unresolved design questions;
12. recommended sequence of follow-up briefs.

## Follow-up sequence to recommend

Likely sequence:

```text
10B — xEdit canonical-export revisions
    ↓
regenerate canonical source datasets
    ↓
10C — reproducer loader/domain ingestion changes
    ↓
10D — canonical planet-resource-occurrence exporter
    ↓
validate produced candidate dataset
```

Recommend a different split if the actual gaps justify it.

Do not implement 10B/10C/10D here.

## Evidence and naming discipline

Retain v1.0 rules:

- no oracle-driven production logic;
- no bespoke downstream display-name enrichment;
- no guessed values;
- no loss of provenance without explicit justification;
- missing input means unknown/unavailable, not empty;
- CK-derived source fields must not be described as retail runtime observations;
- use canonical FormIDs and exact source-export names;
- preserve UTF-8/mojibake safeguards.

## Repository changes allowed

Expected changes are documentation-only.

Allowed:

```text
new gap-analysis Markdown document
small README/BACKLOG link if useful
```

Do not modify:

```text
generation logic
PRNG
loaders
domain classes
CLI/export code
canonical input data
xEdit scripts
```

If another repository/exporter reveals a needed change, document it only.

## Verification

Because this is analysis-only:

```text
run existing tests if any tracked non-doc file was touched accidentally
run mojibake/UTF-8 checks
run git diff --check
```

No canonical validation rerun is required for a documentation-only diff unless repository policy already requires it.

## Deliverable report

Report:

1. files changed;
2. path to the completed gap-analysis document;
3. candidate future CSV grain;
4. candidate field count/schema summary;
5. fields already fully available;
6. fields present in source but lost by current loader/model;
7. true source-data gaps requiring xEdit changes;
8. recommended exporter(s) to modify/add;
9. population/coverage findings;
10. unresolved design decisions requiring user input;
11. recommended follow-up brief sequence;
12. confirmation no implementation/exporter changes were made;
13. no commit/push unless explicitly requested.

Suggested commit message after review:

```text
docs: analyse canonical occurrence export gaps
```
