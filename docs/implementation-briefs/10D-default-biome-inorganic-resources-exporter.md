# Brief 10D — Default canonical biome inorganic resource exporter

## Status

Implementation brief for `gooberpede/starfield-resource-reproducer`.

This brief follows 10A, 10A.1, 10A.2, 10B, and 10C.

The purpose of 10D is to produce the clean default consumer-facing canonical dataset:

```text
output/biome-inorganic-resources.csv
```

This is the first production exporter built on the 10C enriched occurrence model.

The default file must answer:

> Which inorganic resources occur at which terrestrial biome or atmospheric location on each body?

It must **not** expose internal generation-path diagnostics by default.

Do **not** implement diagnostic CLI modes in this brief.
Do **not** modify xEdit scripts.
Do **not** modify `starfield-outpost-network`.
Do **not** commit or push unless explicitly asked.

## Core product grain

The default output grain is:

```text
Planet × Location × Resource
```

not:

```text
Planet × Location × Resource × ResourceOrigin
```

Internal provenance-rich occurrences from 10C may collapse to one product row when they describe the same logical resource at the same logical location.

The output exists to serve downstream consumers without requiring them to understand or collapse generation internals.

The richer 10C model remains the source for future diagnostic/research modes.

## 1. Create and ignore the output directory

Before generating any files, create:

```text
output/
```

at repository root.

Add:

```text
output/
```

to `.gitignore`.

Do not place generated consumer products in `data/`.

`data/` is the canonical input area.

## 2. Default output filename

Use exactly:

```text
output/biome-inorganic-resources.csv
```

No version number or timestamp belongs in the filename.

## 3. Default product schema

Use the clean consumer-oriented schema below.

### Production metadata

```text
ReproducerVersion
ExportTimestamp
```

### Body identity and provenance

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

### Location identity

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

### Resource identity and provenance

```text
ResourceCategory
ResourceFormID
ResourceEditorID
ResourceName
Rarity
ResourceSourceFile
```

### Effective RSGD context

```text
EffectiveRSGDFormID
EffectiveRSGDEditorID
RSGDSource
RSGDSourceFile
```

### Atmospheric defining-ATMO lineage

```text
ResourceDefinedByAtmosphereFormID
ResourceDefinedByAtmosphereEditorID
ResourceDefinedByAtmosphereSourceFile
AtmosphereInheritanceDepth
```

Total default output columns:

```text
35
```

Do **not** include:

```text
ResourceOrigin
CommonAssignmentMechanism
FamilyRootFormID
FamilyRootEditorID
FamilyOriginBiomeIndex
FamilyOriginBiomeFormID
```

Do not add diagnostic/generation columns in the default product.

## 4. Column order

Use exactly this order:

```text
ReproducerVersion
ExportTimestamp
SystemName
PlanetName
BodyType
PlanetFormID
PlanetEditorID
StarSystemID
ParentPlanetID
PlanetID
PlanetSourceFile
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
ResourceCategory
ResourceFormID
ResourceEditorID
ResourceName
Rarity
ResourceSourceFile
EffectiveRSGDFormID
EffectiveRSGDEditorID
RSGDSource
RSGDSourceFile
ResourceDefinedByAtmosphereFormID
ResourceDefinedByAtmosphereEditorID
ResourceDefinedByAtmosphereSourceFile
AtmosphereInheritanceDepth
```

## 5. Field semantics

`ReproducerVersion`: actual package/reproducer version; repeat on every row.

`ExportTimestamp`: generate once per export run; repeat on every row; use UTC ISO 8601. This is distinct from xEdit `ExtractTimestamp`.

`ResourceCategory`: emit constant `Inorganic`.

`ResourceName`: canonical game/export name only. No aliases or display-name enrichment.

## 6. Nullability by location type

Use empty CSV fields for inapplicable values.

### BIOME rows

Required:

```text
BiomeIndex
BiomeFormID
BiomeEditorID
BiomeName
BiomeChance
BiomeSourceFile
EffectiveRSGDFormID
EffectiveRSGDEditorID
RSGDSource
RSGDSourceFile
```

Blank:

```text
AtmosphereFormID
AtmosphereEditorID
AtmosphereSourceFile
ResourceDefinedByAtmosphereFormID
ResourceDefinedByAtmosphereEditorID
ResourceDefinedByAtmosphereSourceFile
AtmosphereInheritanceDepth
```

### ATMOSPHERE rows

Required:

```text
AtmosphereFormID
AtmosphereEditorID
AtmosphereSourceFile
ResourceDefinedByAtmosphereFormID
ResourceDefinedByAtmosphereEditorID
ResourceDefinedByAtmosphereSourceFile
AtmosphereInheritanceDepth
```

Blank:

```text
BiomeIndex
BiomeFormID
BiomeEditorID
BiomeName
BiomeChance
BiomeSourceFile
EffectiveRSGDFormID
EffectiveRSGDEditorID
RSGDSource
RSGDSourceFile
```

Do not invent synthetic biome values.

## 7. LocationType vocabulary

Emit exactly:

```text
BIOME
ATMOSPHERE
```

Do not emit `ATMO`.

## 8. Collapse internal duplicate origins deliberately

Multiple enriched occurrences may map to the same logical product row because they differ only by generation origin or family-assignment provenance.

The default exporter must deliberately collapse such duplicates.

### BIOME uniqueness key

```text
PlanetFormID
LocationType
BiomeIndex
BiomeFormID
ResourceFormID
```

### ATMOSPHERE uniqueness key

```text
PlanetFormID
LocationType
AtmosphereFormID
ResourceFormID
```

`ResourceOrigin` is intentionally absent.

## 9. Safe-collapse invariant

Before collapsing multiple enriched occurrences to one product row, verify that all fields retained in the 35-column default schema are identical for that key.

The only allowed differences are fields intentionally omitted from the default product, such as generation-origin/family-lineage fields.

If rows sharing the same product key disagree on any retained field, fail clearly rather than silently discarding information.

## 10. Biome identity checks

Treat biome identity as planet-local:

```text
PlanetFormID + BiomeIndex + BiomeFormID
```

Do not use `BiomeName` as identity.
Do not use `BiomeFormID` alone as identity.

Audit the canonical corpus for:

1. duplicate `BiomeIndex` within a planet;
2. repeated `BiomeFormID` within a planet;
3. repeated `BiomeName` within a planet.

Report counts and examples.

Policy:

- duplicate `BiomeIndex` within one planet is an invariant failure;
- repeated FormID or name should be reported and understood, not automatically treated as an error unless the source contract is violated;
- IDs/indexes remain identity, not display names.

## 11. Deterministic ordering

Use an explicit stable sort:

```text
StarSystemID numeric
ParentPlanetID numeric
PlanetID numeric
PlanetFormID numeric
LocationType rank
BiomeIndex numeric / null-last
BiomeFormID numeric / null-last
AtmosphereFormID numeric / null-last
ResourceFormID numeric
```

Location rank:

```text
BIOME
ATMOSPHERE
```

Do not use names as sort keys.

Collapse first, then sort.

## 12. Accepted-resource semantics

Build the product only from the 10C enriched accepted-occurrence view.

Exclude rejected attempts, failed candidates, no-assignment diagnostics, and traversal-only records.

## 13. Atmosphere-only bodies

Support bodies with atmosphere data but no terrestrial generation input.

Volii Alpha regression expectation:

```text
2 ATMOSPHERE rows
0 BIOME rows
```

Do not fabricate terrestrial rows.

## 14. Full-corpus production path

Provide one clear programmatic path:

```text
load four canonical production datasets
→ validate coherence
→ generate all terrestrial predictions
→ build enriched accepted occurrences
→ collapse to clean product grain
→ validate uniqueness/nullability/invariants
→ deterministically sort
→ write output/biome-inorganic-resources.csv
```

Reuse existing loader/generation architecture.

## 15. CSV serialization

Use proper CSV serialization:

- UTF-8;
- header row;
- comma delimiter;
- correct quoting;
- deterministic formatting;
- empty string for optional blank fields;
- no index column.

Prefer the Python standard library unless an existing helper is clearly better.

## 16. Numeric/text formatting

Keep formatting deterministic:

```text
FormIDs: canonical 8-digit uppercase hex
integer IDs: decimal
BiomeChance: preserve canonical numeric meaning without float noise
AtmosphereInheritanceDepth: integer
blank optional fields: empty string
```

Do not emit Python enum reprs.

## 17. Lightweight sidecar manifest

Also produce:

```text
output/biome-inorganic-resources.manifest.json
```

The CSV must remain independently interpretable.

Include at minimum:

```text
dataset
schema_version
reproducer_version
export_timestamp
output_filename
row_count
input_datasets
```

For each canonical input:

```text
filename
extract_timestamp
row_count
sha256
```

Inputs:

```text
planet-resource-generation.csv
ires-hierarchy.csv
planet-atmospheric-resources.csv
planet-directory.csv
```

`git_commit` may be included if available reliably, but production must not fail if Git metadata is unavailable.

Do not include the validation oracle as a production input.

## 18. Schema version

Introduce a simple product schema version.

Recommended initial value:

```text
1
```

Document it.

Do not tie schema version directly to package version.

The manifest must carry it.

## 19. Output overwrite behavior

Recommended:

```text
overwrite atomically on successful production
```

Write temporary files in `output/`, complete validation, then replace destinations atomically.

Do not leave partial output files after failure.

## 20. No diagnostic mode yet

Do **not** implement:

```text
--diagnostic-mode
--add-generation-data
```

or equivalent.

The richer 10C model remains available for later diagnostic-output design.

## 21. CLI scope

Do not perform the future CLI-polish project here.

Do not add broad argument parsing for alternate inputs/outputs, help overhaul, graceful exit codes, or diagnostic modes.

A minimal internal entry point to produce the default dataset is allowed if needed.

## 22. Product-contract validation

At minimum assert:

- exactly 35 columns;
- exact column order;
- valid `LocationType`;
- nonblank body/resource identity;
- BIOME/ATMOSPHERE nullability rules;
- no duplicate product keys remain;
- safe-collapse invariant holds;
- one `ReproducerVersion`;
- one `ExportTimestamp`;
- deterministic ordering;
- valid UTF-8.

## 23. Deterministic regeneration test

Run product-building logic twice from identical canonical inputs and confirm semantic identity of content/order.

Because `ExportTimestamp` changes, either inject/freeze the timestamp in tests or normalize it away. Prefer injection if simple.

## 24. Projection validation against old oracle

`data/planet-all-resources.csv` remains validation-only.

Use it only as a comparison surface.

Project the new product to:

```text
PlanetFormID + ResourceFormID
```

deduplicate, then compare the CK/RSGD-visible portion against the existing oracle under established v1.0 validation rules.

Do not use the oracle to create or repair rows.

Be careful that the new product includes atmospheric occurrences and the oracle is not a complete atmosphere oracle.

## 25. Targeted product validation

Add focused checks for:

- a normal terrestrial body;
- same resource appearing across multiple biomes;
- a collapsed-multiple-origin case if canonical, otherwise a clearly labelled constructed projection fixture;
- an atmosphere-inheritance case;
- Volii Alpha: 2 atmosphere rows, 0 biome rows;
- a guard/family-heavy body to prove diagnostic lineage is not leaked into default output.

## 26. Biome-name duplication audit

Explicitly inspect whether any single planet has multiple biome entries with the same `BiomeName`.

Report:

- number of affected planets;
- number of duplicate-name groups;
- representative examples.

Also inspect repeated `BiomeFormID` within one planet.

This is an audit/reporting requirement, not an identity rule.

## 27. Documentation

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

Add a focused product-contract document if useful, for example:

```text
docs/BIOME-INORGANIC-RESOURCES.md
```

Document:

- purpose of `biome-inorganic-resources.csv`;
- Planet × Location × Resource grain;
- 35-column schema;
- nullability;
- deliberate collapse of internal duplicate origins;
- deterministic ordering;
- source/provenance boundaries;
- manifest contents;
- `output/` location;
- validation-only role of `planet-all-resources.csv`;
- future diagnostic mode remains separate and not yet designed.

## 28. Full regression verification

Run all tests.

Expected:

```text
148 existing tests + new 10D tests
all pass
```

Run canonical generation validation:

```text
1,444 / 1,444 exact
0 mismatches
0 errors
```

Run:

```text
python scripts/check_mojibake.py
git diff --check
```

and UTF-8 safeguards.

## 29. Deliverable files

Expected generated output:

```text
output/biome-inorganic-resources.csv
output/biome-inorganic-resources.manifest.json
```

These must remain untracked through `output/` in `.gitignore`.

## 30. Acceptance criteria

10D is complete when:

1. `output/` exists and is gitignored;
2. the CSV is generated from the four canonical inputs through the protected reproducer + 10C enriched model;
3. the default output contains exactly 35 columns;
4. grain is `Planet × Location × Resource`;
5. internal multi-origin rows are safely collapsed;
6. no product-key duplicates remain;
7. nullability and provenance rules hold;
8. deterministic ordering is enforced;
9. atmosphere-only bodies are correct;
10. the manifest is generated;
11. deterministic regeneration tests pass;
12. targeted product validation passes;
13. biome duplicate-name/FormID audit is reported;
14. full tests pass;
15. 1,444/1,444 generation validation remains exact;
16. no diagnostic mode or CLI-polish scope was introduced.

## Deliverable report

Report:

1. files changed;
2. `output/` and `.gitignore` changes;
3. exporter architecture;
4. exact 35-column schema;
5. safe-collapse implementation;
6. final uniqueness keys;
7. deterministic ordering implementation;
8. total generated row count;
9. BIOME row count;
10. ATMOSPHERE row count;
11. number of internal enriched rows collapsed;
12. any safe-collapse conflicts;
13. biome duplicate-name audit results;
14. repeated BiomeFormID audit results;
15. manifest contents;
16. targeted product validation results;
17. old-oracle projection comparison;
18. total test result;
19. canonical 1,444-body validation result;
20. mojibake/UTF-8/diff-check results;
21. confirmation generation/RNG semantics did not change;
22. confirmation no diagnostic mode or broad CLI work was implemented;
23. confirmation no commit/push was performed.

Suggested commit message after review:

```text
feat: export biome inorganic resources
```
