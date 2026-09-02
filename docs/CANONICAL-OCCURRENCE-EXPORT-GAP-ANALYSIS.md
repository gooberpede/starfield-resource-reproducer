# Canonical Resource-Occurrence Export Gap Analysis

## Status and scope

This document implements Brief 10A as an analysis-only deliverable. It audits
the canonical inputs and current reproducer model; it does not implement an
occurrence exporter, change an xEdit script, alter generation behavior, or use
`planet-all-resources.csv` as production input.

The proposed product is a self-contained canonical inorganic-resource
occurrence dataset. Every output value must be one of:

- canonical game/plugin record data;
- a deterministic result of the proven reproducer; or
- neutral production metadata.

The old oracle, downstream dictionaries, manual fixes, and display-name aliases
are excluded from production.

## 1. Purpose and row grain

The future CSV should contain one accepted resource occurrence at this grain:

```text
Planet x Location x Resource x ResourceOrigin
```

`LocationType` is either `BIOME` or `ATMOSPHERE`.

- A biome location is the planet-local PNDT biome occurrence identified by
  `PlanetFormID + BiomeIndex + BiomeFormID`. `BiomeFormID` alone is not a
  location key: 3,210 planet-local biome occurrences currently reuse 427
  distinct BIOM FormIDs.
- An atmosphere location is identified by the planet's effective associated
  `AtmosphereFormID`. It has no synthetic biome and all biome fields are blank.
- Only `ResourceOccurrence.occupies_state == true` contributions are product
  rows. Capacity-rejected diagnostic attempts are not canonical occurrences.
- The same resource in the same biome through different origins remains in
  separate rows. This preserves information already held by the provenance log.
  Exact duplicates with the same location, resource, and origin should fail
  export validation rather than be silently discarded.

The output does not contain empty body rows. A body is claimed only for the
channels for which the reproducer has authoritative input and an accepted
occurrence.

## 2. Recommended candidate schema

The audited schema contains **41 columns**: the brief's 37 candidate columns
plus four already-available atmospheric definition-lineage columns. Retaining
the latter avoids discarding the distinction between the effective planet ATMO
record and an inherited ATMO record that actually defines a resource.

### Production metadata (2)

```text
ReproducerVersion
ExportTimestamp
```

`ExportTimestamp` is one production timestamp repeated on every row. It is not
an xEdit extraction timestamp. Use an unambiguous UTC ISO 8601 value in the
future exporter.

### Body identity and provenance (9)

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

### Location identity (10)

```text
LocationType
BiomeIndex
BiomeFormID
BiomeEditorID
BiomeName
BiomeChance
BiomeSourceFile
AtmosphereFormID
AtmosphereEditorID
AtmosphereSourceFile
```

Biome fields are blank on atmosphere rows. Atmosphere fields are blank on biome
rows.

### Resource identity and generation origin (7)

```text
ResourceCategory
ResourceFormID
ResourceEditorID
ResourceName
Rarity
ResourceSourceFile
ResourceOrigin
```

For this product `ResourceCategory` is the constant `Inorganic`.
`ResourceName` is the canonical export value; there is no
`ResourceDisplayName`. Recommended `ResourceOrigin` values are
`ATMOSPHERE`, `EVERYWHERE`, `SPECIAL`, `COMMON_ROOT`, and `DESCENDANT`.
These are origin mechanisms, not rarity values.

### Effective RSGD provenance (4)

```text
EffectiveRSGDFormID
EffectiveRSGDEditorID
RSGDSource
RSGDSourceFile
```

All accepted biome occurrences, including Everywhere and Special, carry the
effective RSGD context in which that occurrence was produced. Atmosphere rows
leave these fields blank.

### Common-family lineage (5)

```text
CommonAssignmentMechanism
FamilyRootFormID
FamilyRootEditorID
FamilyOriginBiomeIndex
FamilyOriginBiomeFormID
```

These fields apply only to `COMMON_ROOT` and `DESCENDANT` rows. Everywhere,
Special, and Atmosphere rows leave them blank. `NO_COMMON_ASSIGNMENT` does not
belong in an occurrence CSV because no Common occurrence exists to carry it; it
remains a biome diagnostic.

### Atmospheric definition lineage (4)

```text
ResourceDefinedByAtmosphereFormID
ResourceDefinedByAtmosphereEditorID
ResourceDefinedByAtmosphereSourceFile
AtmosphereInheritanceDepth
```

These fields apply only to atmosphere rows. They are blank on biome rows. In the
current atmospheric export, 222 of 335 rows are inherited from an ATMO other
than the planet-associated `AtmosphereFormID`, with a maximum inheritance depth
of 2. Omitting these columns would lose useful canonical provenance that the
source and loader already preserve.

`AtmosphericResourceCount` and `AtmosphericResourceIndex` are not proposed as
product columns. Count is derivable after filtering; index is preserved in the
input for validation and input-order diagnostics but is not part of occurrence
identity. The future exporter can use an explicit stable sort instead of
exposing incidental production order.

## 3. Current input inventory

### `data/PlanetResourceGeneration_v5.csv`

| Property | Audit result |
|---|---|
| Rows / population | 7,920 rows; 1,444 planets; 3,210 planet-local biome occurrences; 3,220 source-specific RSGD-definition occurrences; 32 distinct RSGDs |
| Row grain | PNDT x biome entry x distinct referenced RSGD x ordered RSGD resource entry |
| Primary records | PNDT, BIOM, RSGD, and referenced IRES identity/rarity |
| Keys / ordering | `PlanetFormID`; planet-local `BiomeIndex + BiomeFormID`; source-specific `RSGDSource + RSGDFormID`; `RSGDResourceIndex` |
| Source/provenance columns | `SourceFile`, `BiomeSourceFile`, `RSGDSource`, `RSGDSourceFile`, `ResourceSourceFile` |
| Timestamp | One repeated `ExtractTimestamp`: `2026-08-30 11:40:41` |
| Fields used by loader | Every column except `ExtractTimestamp`; `SourceFile` becomes `Planet.source_file`; all biome values, both RSGD relationships, resource metadata/order, and all rarity chances are retained |
| Fields discarded by loader | `ExtractTimestamp` only |

The checked-in xEdit script documents the row grain and extracts PNDT identity,
RSCS, PNDT biome order, BIOM identity/chance/provenance, PNDT and BIOM RSGD
relationships, RSGD identity/provenance/order, and referenced IRES metadata and
source file. No candidate identity field requires an extension to this exporter.

### `data/Starfield_IRES_Hierarchy.csv`

| Property | Audit result |
|---|---|
| Rows / population | 56 parent/child rows; 47 distinct parent records; 48 distinct nodes after including child-only nodes |
| Row grain | Selected IRES parent x direct child; one blank-child row for a leaf parent |
| Primary records | IRES parent and direct child IRES |
| Keys / ordering | `FormID + ChildFormID`; source edge-list order is retained |
| Source/provenance columns | None |
| Timestamp | None |
| Fields used by loader | All eight fields: parent and child FormID, EditorID, Name, and Rarity |
| Fields discarded by loader | None |

The xEdit script confirms the absence of record plugin provenance and a file
timestamp. Consequently, resources materialized from the IRES graph - notably
descendants and the current atmosphere-to-IRES identity conversion - have
`ResourceRef.source_file == None`, even though root/Special/Everywhere rows can
obtain source provenance from RSGD entries and atmosphere rows retain it on the
atmospheric record.

### `data/Starfield_PlanetAtmosphericResources.tsv`

| Property | Audit result |
|---|---|
| Rows / population | 335 rows; 297 bodies; 259 bodies with one resource and 38 with two |
| Row grain | Effective planet ATMO x effective inorganic atmospheric resource |
| Primary records | PNDT/body identity, effective associated ATMO, inherited defining ATMO, and IRES resource |
| Keys / ordering | `PlanetFormID + ResourceFormID`; `AtmosphericResourceIndex` is contiguous within each planet |
| Source/provenance columns | Body `SourceFile`, `AtmosphereSourceFile`, `ResourceSourceFile`, `ResourceDefinedByAtmosphereSourceFile`, inheritance depth and defining ATMO identity |
| Timestamp | One repeated `ExtractTimestamp`: `2026-08-31 14:12:17` |
| Fields used by loader | All 23 columns are retained on `AtmosphericResourceRecord` |
| Fields discarded by loader | None |

`AtmosphereFormID` is treated as the effective planet-associated ATMO record by
the authoritative current export. The separate `ResourceDefinedByAtmosphere*`
columns show where an inherited resource was actually defined, and
`ResourceSourceFile` independently identifies the IRES plugin source. Thus ATMO
record provenance and resource-record provenance are already distinct.

The atmospheric exporter source is not checked into this repository, so the
exact xEdit property paths cannot be re-audited here. Brief 10B should preserve
the current schema and bring the maintained exporter/source instructions under
the reproducer's canonical data-production process rather than reconstruct its
semantics from column names.

### External `starfield-outpost-network/reference-source/planet-directory.tsv`

| Property | Audit result |
|---|---|
| Rows / population | 1,776 rows and 1,776 unique bodies: 693 planets, 1,009 moons, and 74 orbitals |
| Row grain | One canonical body/PNDT directory record |
| Primary records | PNDT/body record plus star-system relationship/name lookup; exact exporter property paths are not present in either inspected repository |
| Keys | `PlanetFormID`; `StarSystemID + ParentPlanetID + PlanetID` is body hierarchy metadata, not a replacement for FormID identity |
| Source/provenance columns | `SourceFile` |
| Timestamp | One repeated `ExtractTimestamp`: `2026-08-28 10:47:54` |
| Fields used by reproducer loader | None; this is not currently a reproducer input |
| Available fields | All nine proposed body columns (with `SourceFile` renamed on output to `PlanetSourceFile`) plus `PlanetNotLandable` and `OceanWorld` coverage flags |

The existing shape can be reused unchanged as a fourth canonical reproducer
input. Its population is a strict superset of both generation and atmosphere
inputs. Do not create a runtime dependency on the other repository and do not
copy the current file as a shortcut. Brief 10B should locate or formalize the
underlying exporter, document the exact game record/property or exporter lookup
behind each field, and regenerate a reproducer-owned canonical dataset.

The available evidence supports the following authority distinctions without
inventing absent property paths:

| Body field | Current authority | Direct vs derived status |
|---|---|---|
| `PlanetFormID` | Planet Directory and both current channel exports | Direct fixed PNDT FormID |
| `PlanetEditorID` | Planet Directory and both current channel exports | Direct PNDT EditorID |
| `PlanetName` | Planet Directory and both current channel exports | Canonical game/export name; exact exporter lookup should be documented in 10B |
| `PlanetSourceFile` | `SourceFile` in Planet Directory and both channel exports | Direct source-plugin provenance for the body record |
| `SystemName` | Planet Directory; atmospheric export for 297 bodies | Canonical related-system name lookup; exporter-derived join |
| `BodyType` | Planet Directory; atmospheric export for 297 bodies | Canonical exported classification; exact record/property or classification rule is unresolved because the exporter source is absent |
| `StarSystemID` | Planet Directory; atmospheric export for 297 bodies | Canonical exported numeric relationship value; exact PNDT property path must be documented in 10B |
| `ParentPlanetID` | Planet Directory; atmospheric export for 297 bodies | Canonical exported hierarchy value; exact PNDT property path must be documented in 10B |
| `PlanetID` | Planet Directory; atmospheric export for 297 bodies | Canonical exported hierarchy value; exact PNDT property path must be documented in 10B |

The Planet Directory is complete for the current v1.0 generation population:
all 1,444 generation PlanetFormIDs and all 297 atmosphere PlanetFormIDs occur in
it.

### Validation-only `data/planet-all-resources.csv`

This file has 7,663 rows at deduplicated `Planet x Resource` grain. It contains
6,040 inorganic rows for the 1,444 generation bodies and 1,623 organic rows for
185 bodies. Its only body outside the generation population is Volii Alpha, and
that oracle row is Organic. It is not a source for any candidate field or row.

## 4. Loader, model, and result inventory

### Current path

```text
PlanetResourceGeneration_v5.csv
  -> load_generation_data
  -> Planet -> Biome -> RSGDDefinition -> RSGDResourceEntry
  -> generate_planet
  -> PlanetGenerationResult + ResourceOccurrence + BiomeResourceView

Starfield_IRES_Hierarchy.csv
  -> load_ires_hierarchy
  -> IRESNode + child ResourceRef
  -> family generation / resource identity lookup
  -> ResourceFamilyResult + ResourceOccurrence

Starfield_PlanetAtmosphericResources.tsv
  -> load_atmospheric_resources
  -> AtmosphericResourceRecord
  -> pre-generation atmosphere insertion
  -> ResourceOccurrence.atmospheric_record
```

### Preservation and first loss point

| Data group | Source state | Loader/domain state | Result/occurrence state | First unavailable point / later action |
|---|---|---|---|---|
| Planet FormID, EditorID, name, source plugin | Generation source | Retained on `Planet` | Reachable from `PlanetGenerationResult.planet` | No loss |
| Generation extraction timestamp | Present | Read for schema validation but discarded | Unavailable | Loader loss, but not a candidate output field; output production time is different metadata |
| Full body directory metadata | Present only in external Planet Directory (and atmosphere subset) | No reproducer directory loader/object | Unavailable for biome-only export | Add fourth canonical input and loader; do not use oracle |
| Planet-local biome identity/name/chance/source | Present | Retained on `Biome` | `biome_index` and FormID are direct on occurrence; all values reachable through biome/result join | Reshape during exporter implementation |
| Effective RSGD identity/editor/source plugin | Present | Retained on `Biome.effective_rsgd` | FormID and source relationship direct on occurrence; editor/source plugin reachable through biome join | Reshape during exporter implementation |
| RSGD resource identity/rarity/source plugin | Present for RSGD entries | Retained on entry/`ResourceRef` | Retained for roots, Special, and Everywhere | No loss |
| IRES identity/name/rarity | Present | Retained on `IRESNode`/child `ResourceRef` | Retained on family and occurrence resources | No loss |
| IRES parent/child source plugin | Absent | Cannot retain | Unavailable for graph-derived resource references | True source gap: extend IRES exporter |
| Atmosphere body/effective ATMO/resource/definition provenance | Present | All fields retained | Full source record retained on atmosphere occurrence | No loss |
| Resource origin | Not a static field | Deterministically assigned by generator | Direct `ResourceOccurrence.provenance`; map `ATMO` to `ATMOSPHERE` and `COMMON` to `COMMON_ROOT` for output | Export mapping only |
| Common family root and mechanism | Derived | Direct on each Common/Descendant occurrence | Direct `root_form_id` and `common_assignment_mechanism` | Root EditorID is a deterministic IRES join |
| Common family origin biome | Derived | Retained once on `ResourceFamilyResult.origin` | Reachable through `family_cache[root_form_id]`, but not copied onto each occurrence | Later result/export shaping; no xEdit change |
| No Common assignment | Derived biome diagnostic | Retained on `CommonFamilyAssignment` | No resource occurrence by definition | Keep out of occurrence CSV |

No proposed candidate field is present in a current canonical source and then
irrecoverably discarded by the model. Several values are not flattened onto
`ResourceOccurrence`, but remain reachable through the immutable planet,
biome, RSGD, family-cache, or atmospheric record structures. The only current
source field discarded outright is the generation input's extraction timestamp,
which is intentionally not the future output's `ExportTimestamp`.

Every emitted descendant has unambiguous family-root access through
`ResourceOccurrence.root_form_id`. One family configuration exists per root in
the planet-scope cache, and `ResourceFamilyResult.origin` retains the origin
biome index and FormID. This makes family-origin enrichment deterministic even
for normal cache reuse and both guard fallback mechanisms.

## 5. Field-by-field gap matrix

`Gap?` describes readiness for a self-contained reproducer-owned occurrence
export, not whether a value happens to exist in the validation oracle.

| Candidate Output Field | Meaning / Grain | Classification | Current Source | Current Loader/Model Availability | Gap? | Required Action | Notes |
|---|---|---|---|---|---|---|---|
| `ReproducerVersion` | Producing implementation version; file-wide | EXPORT_METADATA | Package `__version__` (`1.0.0`) | Available | NO | F | Repeat on every row |
| `ExportTimestamp` | One file-production time | EXPORT_METADATA | Future exporter clock | Not implemented because exporter is out of scope | NO | F/10D | UTC ISO 8601; not input extract time |
| `SystemName` | Body's canonical system name | CANONICAL_SOURCE | External Planet Directory; atmosphere subset | No directory loader; atmosphere records cover 297 bodies | YES | D | Import a reproducer-owned directory dataset |
| `PlanetName` | Canonical body name | CANONICAL_SOURCE | Generation, atmosphere, Planet Directory | Retained on `Planet`/atmosphere | NO | F | Directory should become uniform authority at export time |
| `BodyType` | Planet/moon/orbital classification | CANONICAL_SOURCE | External Planet Directory; atmosphere subset | No directory loader | YES | D | Exact exporter rule must be documented |
| `PlanetFormID` | Stable body identity | CANONICAL_SOURCE | All body/channel exports | Retained | NO | F | Primary body join key |
| `PlanetEditorID` | Canonical PNDT EditorID | CANONICAL_SOURCE | All body/channel exports | Retained | NO | F |  |
| `StarSystemID` | Canonical numeric system relation | CANONICAL_SOURCE | External Planet Directory; atmosphere subset | No directory loader | YES | D | Exact property path must be documented |
| `ParentPlanetID` | Canonical parent hierarchy value | CANONICAL_SOURCE | External Planet Directory; atmosphere subset | No directory loader | YES | D | Exact property path must be documented |
| `PlanetID` | Canonical body hierarchy value | CANONICAL_SOURCE | External Planet Directory; atmosphere subset | No directory loader | YES | D | Exact property path must be documented |
| `PlanetSourceFile` | Body record plugin provenance | CANONICAL_SOURCE | Generation/atmosphere `SourceFile`; Planet Directory | Retained for current channel records | NO | F | Rename only at output boundary |
| `LocationType` | `BIOME` or `ATMOSPHERE` | REPRODUCER_DERIVED | Channel being serialized | Not a current field | NO | E/10D | Deterministic discriminator |
| `BiomeIndex` | Planet-local PNDT biome position | CANONICAL_SOURCE | Generation export | Retained on `Biome` and occurrence | NO | F | Blank on atmosphere rows |
| `BiomeFormID` | BIOM identity within planet-local key | CANONICAL_SOURCE | Generation export | Retained on `Biome` and occurrence | NO | F | Blank on atmosphere rows |
| `BiomeEditorID` | Canonical BIOM EditorID | CANONICAL_SOURCE | Generation export | Retained on `Biome`; join from result | NO | E/10D | Blank on atmosphere rows |
| `BiomeName` | Canonical BIOM name | CANONICAL_SOURCE | Generation export | Retained on `Biome`; join from result | NO | E/10D | Blank on atmosphere rows |
| `BiomeChance` | PNDT biome-entry chance | CANONICAL_SOURCE | Generation export | Retained on `Biome`; join from result | NO | E/10D | Blank on atmosphere rows |
| `BiomeSourceFile` | BIOM plugin provenance | CANONICAL_SOURCE | Generation export | Retained on `Biome`; join from result | NO | E/10D | Blank on atmosphere rows |
| `AtmosphereFormID` | Effective associated ATMO identity | CANONICAL_SOURCE | Atmospheric export | Retained on atmospheric record | NO | F | Blank on biome rows |
| `AtmosphereEditorID` | Effective ATMO EditorID | CANONICAL_SOURCE | Atmospheric export | Retained | NO | F | Blank on biome rows |
| `AtmosphereSourceFile` | Effective ATMO plugin provenance | CANONICAL_SOURCE | Atmospheric export | Retained | NO | F | Distinct from IRES source and defining ATMO source |
| `ResourceCategory` | Product resource channel | REPRODUCER_DERIVED | Product contract | Not a field | NO | E/10D | Constant `Inorganic`; do not use oracle category |
| `ResourceFormID` | Stable IRES identity | CANONICAL_SOURCE | RSGD, IRES, atmosphere | Retained on every occurrence | NO | F |  |
| `ResourceEditorID` | Canonical IRES EditorID | CANONICAL_SOURCE | RSGD, IRES, atmosphere | Retained on every occurrence | NO | F |  |
| `ResourceName` | Canonical game/export name | CANONICAL_SOURCE | RSGD, IRES, atmosphere | Retained on every occurrence | NO | F | No downstream display alias |
| `Rarity` | Static IRES generation rarity | CANONICAL_SOURCE | RSGD/IRES; atmosphere identity checked against IRES | Retained on `ResourceRef` | NO | F | Do not substitute oracle rarity |
| `ResourceSourceFile` | IRES record plugin provenance | CANONICAL_SOURCE | RSGD and atmosphere provide it; IRES hierarchy does not | Available for RSGD/ATMO records, absent on graph-derived refs | PARTIAL | B | Add parent and child source columns to IRES export/loader |
| `ResourceOrigin` | Deterministic generation mechanism | REPRODUCER_DERIVED | Proven generation path | Direct occurrence enum | NO | E/10D | Output vocabulary mapping only |
| `EffectiveRSGDFormID` | RSGD effective for this biome occurrence | CANONICAL_SOURCE | Generation export + proven PNDT precedence | Direct on occurrence | NO | F | Carry on all biome origins |
| `EffectiveRSGDEditorID` | Effective RSGD EditorID | CANONICAL_SOURCE | Generation export | Retained on `Biome.effective_rsgd` | NO | E/10D | Join by biome/result; blank on atmosphere |
| `RSGDSource` | Effective RSGD relationship provenance | REPRODUCER_DERIVED | Exported PNDT/BIOM relationships + precedence | Definition provenance and resolution source retained | NO | E/10D | Freeze output vocabulary in 10C/10D |
| `RSGDSourceFile` | Effective RSGD plugin provenance | CANONICAL_SOURCE | Generation export | Retained on `RSGDDefinition` | NO | E/10D | Blank on atmosphere rows |
| `CommonAssignmentMechanism` | How this biome obtained the family | REPRODUCER_DERIVED | Generation/cache/fallback path | Direct on Common/Descendant occurrence | NO | F | Never emit `NO_COMMON_ASSIGNMENT` as a resource row |
| `FamilyRootFormID` | Common family identity | REPRODUCER_DERIVED | Selected/cached family | Direct `root_form_id` | NO | F | Blank outside Common/Descendant |
| `FamilyRootEditorID` | Common root EditorID | REPRODUCER_DERIVED | Family root/IRES identity | Available by deterministic root join | NO | E/10D | Blank outside Common/Descendant |
| `FamilyOriginBiomeIndex` | Biome that first generated cached family | REPRODUCER_DERIVED | `ResourceFamilyResult.origin` | Retained, indirect from occurrence through root/cache | PARTIAL | E/10C | Add explicit occurrence/export access or a tested join |
| `FamilyOriginBiomeFormID` | FormID of family-origin biome occurrence | REPRODUCER_DERIVED | `ResourceFamilyResult.origin` | Retained, indirect from occurrence through root/cache | PARTIAL | E/10C | Pair with origin index; BIOM FormID alone is insufficient |
| `ResourceDefinedByAtmosphereFormID` | ATMO that defines inherited resource | CANONICAL_SOURCE | Atmospheric export | Retained | NO | F | Blank on biome rows |
| `ResourceDefinedByAtmosphereEditorID` | Defining ATMO EditorID | CANONICAL_SOURCE | Atmospheric export | Retained | NO | F | Blank on biome rows |
| `ResourceDefinedByAtmosphereSourceFile` | Defining ATMO plugin provenance | CANONICAL_SOURCE | Atmospheric export | Retained | NO | F | Blank on biome rows |
| `AtmosphereInheritanceDepth` | Effective-to-defining ATMO depth | CANONICAL_SOURCE | Atmospheric export | Retained | NO | F | Blank on biome rows |

Action codes are the brief's outcomes: A extend generation exporter; B extend
IRES exporter; C extend atmospheric exporter; D formalize/reuse Planet Directory
as a fourth canonical input; E loader/model/export shaping only; F no change.

## 6. Required xEdit export changes

### B. Extend the IRES hierarchy exporter

This is the only field-level extraction deficiency found in the three current
canonical inputs.

| Requirement | Recommendation |
|---|---|
| Record type | IRES parent and direct child IRES |
| Existing grain | One parent x direct child; leaf parent has one blank-child row |
| New columns | `SourceFile`, `ExtractTimestamp`, `ChildSourceFile` |
| Value source | Parent record plugin; one file-production timestamp; child record plugin when a child exists |
| Repetition | Parent source and timestamp repeat per output row; child source repeats with child identity |
| Loader consequence | Add source plugin to `IRESNode` and ensure all parent/child `ResourceRef` values carry it |

Use the same one-timestamp-per-file convention as the generation, atmosphere,
and Planet Directory exports. This is not a request to change resource identity,
rarity, edge order, or selection scope.

### D. Formalize the Planet Directory exporter/input

The existing 12-column export already supplies the required body metadata and
coverage flags. Reuse its shape unchanged rather than duplicating these fields
into the generation or atmospheric exporters.

| Requirement | Recommendation |
|---|---|
| Record type | PNDT/body directory, with related star-system lookup as already implemented upstream |
| Grain | One row per canonical body, including planets, moons, and orbitals |
| Columns | Existing `SourceFile`, `ExtractTimestamp`, `PlanetFormID`, `PlanetEditorID`, `PlanetName`, `BodyType`, `StarSystemID`, `SystemName`, `ParentPlanetID`, `PlanetID`, `PlanetNotLandable`, `OceanWorld` |
| Repetition | One common extract timestamp repeated on every record row |
| Ownership | Regenerate a reproducer-owned canonical input; do not load the file from `starfield-outpost-network` at runtime |
| Evidence task | Locate/formalize the source exporter and document exact xEdit record/property paths and any classification/lookup logic before freezing it |

Because the exporter source was not found in either inspected repository, it is
not safe to claim exact property paths for `BodyType`, the three numeric
hierarchy fields, or the system-name lookup. Resolving that provenance is a 10B
requirement, not a reason to infer or repair values manually.

### A and C. No schema extension found

- The Planet Resource Generation exporter already supplies every required
  planet, biome, effective-RSGD, RSGD-resource, and record-source field.
- The atmospheric export already supplies effective ATMO identity/provenance,
  resource identity/provenance, defining ATMO identity/provenance, inheritance
  depth, and complete body metadata for its own population. Its exporter source
  should be formalized alongside regeneration instructions, but no new output
  field is required by this analysis.

## 7. Loader/model changes required later

These belong to Brief 10C, not this change.

1. Add a reproducer-owned Planet Directory TSV path, schema validation, immutable
   body-directory object, and ProjectData mapping keyed by `PlanetFormID`.
2. Validate directory uniqueness, one file timestamp, body identity coherence
   against generation and atmosphere records, and complete coverage for every
   body the occurrence exporter claims.
3. Load new IRES parent/child source-plugin fields and retain source provenance
   on every `IRESNode` and graph-produced `ResourceRef`.
4. Provide an explicit, tested way to obtain family origin from every accepted
   Common/Descendant occurrence. Copying origin fields onto occurrences or
   exposing a result-level enriched occurrence view are both viable; avoid an
   exporter-only opaque search.
5. Provide a typed occurrence-export view that joins planet, biome, effective
   RSGD, family, and atmosphere context without consulting the oracle.
6. Define the output vocabulary for effective RSGD source. The current model
   preserves `PNDT`, `BIOM`, and `PNDT+BIOM`; if the product uses
   `PNDT_OVERRIDE`, its exact mapping must distinguish a distinct override from
   the same RSGD referenced by both records.
7. Keep rejected capacity attempts and `NO_COMMON_ASSIGNMENT` in diagnostics,
   not product occurrence rows.

No generation algorithm change is required.

## 8. Population and coverage analysis

### Current set relationships

| Population | Bodies | Relationship |
|---|---:|---|
| Planet Resource Generation | 1,444 | All are in Planet Directory |
| Atmospheric resource export | 297 | All are in Planet Directory; 296 overlap generation |
| Planet Directory | 1,776 | Superset of both channel inputs |
| Generation union atmosphere | 1,445 | Adds only Volii Alpha to generation population |

The 332 Planet Directory bodies absent from generation are exactly:

| Directory-only class | Count |
|---|---:|
| Orbital, not flagged non-landable | 74 |
| Moon with `PlanetNotLandable = 1` | 29 |
| Planet with `PlanetNotLandable = 1` | 228 |
| Ocean world (`OceanWorld = 1`) | 1 |

Equivalently, the generation population is all 1,444 directory rows that are
Planet or Moon, are not `PlanetNotLandable`, and are not the ocean world. The
directory contains 1,436 base-game and 8 Shattered Space generation bodies; the
atmospheric population contains 296 base-game and 1 Shattered Space body.

### Missing input is not an empty result

Orbitals, the 257 non-landable bodies, and Volii Alpha have no PNDT/biome
generation rows. The future exporter must not infer terrestrial absence or emit
fabricated biome rows for them. A directory row alone is body metadata, not a
resource occurrence.

The current atmosphere export has no resource rows for the orbitals or the 257
non-landable bodies. They therefore contribute no occurrence rows with current
authoritative channels. This does not assert that their resource sets are empty.

Volii Alpha is the required negative control:

```text
PlanetFormID: 0005E3A5
Directory: known; Planet; OceanWorld = 1
Generation input: absent
Atmosphere input: known; Benzene and Water
```

The eventual dataset should emit its two authoritative `ATMOSPHERE` rows with
biome and RSGD fields blank, and emit no unsupported `BIOME` rows. The body must
not be dropped merely because terrestrial generation input is unavailable.

## 9. Compatibility with `planet-all-resources.csv`

The old file remains comparison-only. Its grain is deduplicated
`Planet x Resource`; the proposed grain is occurrence-level, so row-count
comparison is not meaningful.

| Old column | Proposed equivalent | Source authority | Semantics |
|---|---|---|---|
| `SystemName` | `SystemName` | Planet Directory | Same body metadata once the directory becomes a canonical input |
| `PlanetName` | `PlanetName` | Planet Directory/current channel source | Same canonical body-name role |
| `BodyType` | `BodyType` | Planet Directory | Same broad classification; no oracle dependency |
| `PlanetFormID` | `PlanetFormID` | Planet Directory/current channel source | Same stable identity |
| `PlanetEditorID` | `PlanetEditorID` | Planet Directory/current channel source | Same canonical identity |
| `StarSystemID` | `StarSystemID` | Planet Directory | Same numeric body metadata; currently absent from generation input |
| `ParentPlanetID` | `ParentPlanetID` | Planet Directory | Same hierarchy metadata; currently absent from generation input |
| `PlanetID` | `PlanetID` | Planet Directory | Same hierarchy metadata; currently absent from generation input |
| `ResourceCategory` | `ResourceCategory` | Export contract | Narrowed to constant `Inorganic`; Organic is outside this product |
| `ResourceFormID` | `ResourceFormID` | RSGD/IRES/atmosphere | Same identity, repeated for distinct locations/origins |
| `ResourceEditorID` | `ResourceEditorID` | RSGD/IRES/atmosphere | Same identity metadata, independently sourced |
| `ResourceName` | `ResourceName` | RSGD/IRES/atmosphere | Same canonical-name role; no display enrichment |
| `Rarity` | `Rarity` | Static IRES generation data | Changed authority: generation rarity, never oracle rarity |

Capabilities improve by adding location identity, effective RSGD provenance,
generation origin, common-family lineage, record plugin provenance, atmospheric
inheritance lineage, reproducer version, and file-production time. Deduplication
to a planet-resource view, if a consumer needs it, becomes a downstream
projection rather than destructive source behavior.

## 10. Uniqueness and deterministic ordering

### Row identity

Preserve different origins as separate rows.

For a biome occurrence:

```text
PlanetFormID
LocationType                  # BIOME
BiomeIndex
BiomeFormID
ResourceFormID
ResourceOrigin
```

For an atmosphere occurrence:

```text
PlanetFormID
LocationType                  # ATMOSPHERE
AtmosphereFormID
ResourceFormID
```

Atmosphere origin is necessarily `ATMOSPHERE`, so it need not be duplicated in
the atmosphere key even though it remains an output column. These keys should be
validated after filtering to accepted occurrences. A duplicate key is an
invariant failure requiring investigation.

Do not collapse same-biome, same-resource rows across `EVERYWHERE`, `SPECIAL`,
`COMMON_ROOT`, or `DESCENDANT`. Combining provenance into a delimiter-separated
cell would weaken querying and make family-lineage fields ambiguous.

### Ordering

Use an explicit stable sort, independent of dictionary iteration:

```text
StarSystemID numeric
ParentPlanetID numeric
PlanetID numeric
PlanetFormID numeric             # deterministic tie-breaker
LocationType rank                # BIOME, then ATMOSPHERE
BiomeIndex numeric/null-last
BiomeFormID numeric/null-last
AtmosphereFormID numeric/null-last
ResourceOrigin rank              # EVERYWHERE, SPECIAL, COMMON_ROOT, DESCENDANT, ATMOSPHERE
ResourceFormID numeric
```

Names are not sort keys. If later evidence establishes a semantically important
atmospheric resource order, add `AtmosphericResourceIndex` deliberately rather
than relying on input/dictionary traversal.

## 11. Unresolved design questions

The analysis supports defaults, but the following should be explicitly frozen
in the later schema brief:

1. **RSGD source vocabulary.** Prefer a lossless vocabulary matching current
   relationship evidence (`BIOM`, `PNDT`, `PNDT_AND_BIOM`) or define a precise
   mapping to `PNDT_OVERRIDE`; do not label the same-reference case an override
   accidentally.
2. **Planet Directory field provenance.** The upstream exporter source must be
   located/formalized so exact property paths and derivation rules for
   `BodyType`, system/hierarchy IDs, system name, and canonical planet name are
   documented. The values exist, but their extraction implementation was not
   available for this audit.
3. **Atmospheric lineage columns.** This analysis recommends the 41-column
   schema, including the four defining-ATMO fields. If a narrower 37-column
   contract is chosen, the deliberate loss of inherited-definition provenance
   should be recorded and the optional manifest cannot replace row-specific
   lineage.
4. **Version and timestamp formatting.** Recommended defaults are package
   semantic version and UTC ISO 8601 production time. Git SHA, input hashes,
   extraction timestamps, command, and row counts belong in an optional sidecar
   manifest.
5. **Constant category.** Retain `ResourceCategory = Inorganic` for explicitness
   and compatibility, despite its being constant in this first product.

None of these questions blocks 10B's source-export work.

## 12. Recommended follow-up briefs

The evidence supports the proposed split:

```text
10B - xEdit canonical-export revisions
      - extend IRES hierarchy provenance/timestamp
      - formalize/regenerate the Planet Directory exporter/input
      - formalize atmospheric exporter ownership/instructions without a schema change
      - regenerate and audit canonical source datasets

10C - reproducer loader/domain ingestion changes
      - load Planet Directory
      - retain IRES source provenance
      - add typed enriched occurrence access/family-origin access
      - freeze schema vocabulary and cross-input coherence checks

10D - canonical planet-resource-occurrence exporter
      - serialize accepted BIOME and ATMOSPHERE occurrences
      - enforce nullability, keys, and deterministic ordering
      - emit production metadata and optional manifest

10E - candidate-dataset validation and successor assessment
      - validate schema, keys, provenance, coverage, and deterministic regeneration
      - compare projected planet/resource membership to the old oracle without using it
        for production or repair
```

Separating validation into 10E keeps exporter construction and successor
acceptance evidence reviewable. No consumer migration belongs in this sequence.

## Conclusion

The reproducer already has the deterministic occurrence/origin model, complete
biome and effective-RSGD metadata for 1,444 supported generation bodies, and
complete atmosphere provenance for 297 bodies. The existing Planet Directory
demonstrates that complete canonical body metadata is available for the entire
1,776-body directory and should become a fourth reproducer-owned input. The
only identified missing record-level field extraction is IRES parent/child
source-plugin provenance. Everything else is loader/domain integration,
result-view shaping, or exporter work; no oracle enrichment or generation
algorithm change is needed.
