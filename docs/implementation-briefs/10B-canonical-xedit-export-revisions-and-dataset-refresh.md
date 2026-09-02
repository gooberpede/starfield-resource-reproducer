# Brief 10B — Canonical xEdit export revisions and dataset refresh

## Status

Substantive xEdit/data-pipeline brief for:

```text
gooberpede/starfield-resource-reproducer
```

This brief follows:

- Brief 10A — canonical occurrence-export gap analysis;
- Brief 10A.1 — standardize xEdit tabular outputs on CSV and synchronize maintained scripts;
- Brief 10A.2 — add Resource Tree provenance metadata.

The purpose of 10B is to finish the canonical source-export layer needed by the future occurrence exporter.

Do **not** modify reproducer loaders, domain models, generation logic, or occurrence-export code in this brief.

Do **not** modify `starfield-outpost-network`.

Do **not** commit or push unless explicitly asked.

---

# Standing rules

Read and follow the current repository `AGENTS.md` before making changes.

Active xEdit scripts:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\
```

Repository-maintained copies:

```text
D:\Projects\starfield-resource-reproducer\xedit-scripts\
```

Canonical generated datasets are to be copied into:

```text
D:\Projects\starfield-resource-reproducer\data\
```

only when this brief explicitly requires it.

When an installed `.pas` script is modified:

1. modify the installed `Edit Scripts` copy;
2. copy the completed script to `xedit-scripts\` under the same filename;
3. verify installed/repository copies are byte-for-byte identical;
4. preserve valid UTF-8;
5. run required mojibake and diff checks.

Do not use legacy filenames merely because older checked-in data used them.

---

# Current maintained export set

The maintained xEdit export scripts are:

```text
Starfield - Export Planet Atmospheric Resources.pas
    -> planet-atmospheric-resources.csv

Starfield - Export Planet Resource Generation.pas
    -> planet-resource-generation.csv

Starfield - Export Resource Tree.pas
    -> ires-hierarchy.csv

Starfield - Export Planet Directory.pas
    -> planet-directory.csv
```

These four scripts are the canonical source-export pipeline for this phase.

---

# Main objectives

10B has four goals:

1. verify and formalize the canonical provenance of the Planet Directory exporter;
2. verify and formalize the atmospheric exporter’s maintained source/provenance behavior;
3. confirm the Resource Tree provenance additions are correct and complete;
4. replace the repository’s legacy `data/` inputs with the current canonical CSV outputs from `Edit Scripts\`.

No reproducer ingestion changes belong in this brief.

---

# 1. Planet Directory provenance audit

Inspect:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\Starfield - Export Planet Directory.pas
```

and the synchronized repository copy.

The current schema is expected to remain:

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

## Required task

Document the exact source/derivation of every nontrivial field.

For each output column, identify:

- xEdit record type;
- element/path/property read;
- whether value is direct record data or exporter-derived classification/lookup;
- any parent/system relationship traversal;
- any fallback behavior;
- null/blank behavior where applicable.

Pay particular attention to:

```text
PlanetName
BodyType
StarSystemID
SystemName
ParentPlanetID
PlanetID
PlanetNotLandable
OceanWorld
```

The purpose is to eliminate the current uncertainty noted in Brief 10A about exact exporter provenance.

## Important constraint

Do not change the output schema unless the audit reveals a genuine correctness defect.

If a field is exporter-derived rather than a literal stored value, that is acceptable if the derivation is deterministic and based solely on canonical game/plugin data.

If the current logic is sound, preserve it and document it.

If the current logic is not sound or cannot be justified from canonical records, stop and report the issue rather than silently inventing a replacement.

---

# 2. Atmospheric exporter provenance audit

Inspect:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\Starfield - Export Planet Atmospheric Resources.pas
```

and the synchronized repository copy.

Brief 10A found no schema deficiency, but the exporter implementation/provenance should now be treated as maintained canonical source logic.

## Required task

Document and verify the extraction path for at least:

```text
PlanetFormID
PlanetEditorID
PlanetName
SourceFile

AtmosphereFormID
AtmosphereEditorID
AtmosphereSourceFile

ResourceFormID
ResourceEditorID
ResourceName
ResourceRarity
ResourceSourceFile

ResourceDefinedByAtmosphereFormID
ResourceDefinedByAtmosphereEditorID
ResourceDefinedByAtmosphereSourceFile
AtmosphereInheritanceDepth

AtmosphericResourceCount
AtmosphericResourceIndex
```

Confirm:

- `AtmosphereFormID` is the effective planet-associated ATMO record;
- inherited resource definitions retain the defining ATMO identity separately;
- `ResourceSourceFile` is the IRES record’s source plugin, not the ATMO source;
- inheritance depth semantics are deterministic;
- body identity fields are canonical/exporter-derived from game records only;
- one `ExtractTimestamp` value is produced per file.

Do not change the schema unless a correctness defect is discovered.

---

# 3. Resource Tree provenance confirmation

Inspect:

```text
Starfield - Export Resource Tree.pas
```

Confirm the 10A.2 schema:

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

Verify:

- parent `SourceFile` is the parent IRES plugin;
- child `ChildSourceFile` is independently resolved from the child IRES plugin;
- leaf rows leave all child fields blank;
- one `ExtractTimestamp` value repeats across the export;
- graph traversal/order and parent-child semantics remain unchanged.

No new schema change is expected here.

---

# 4. Planet Resource Generation exporter confirmation

Inspect:

```text
Starfield - Export Planet Resource Generation.pas
```

Brief 10A found no schema gap.

Do not change its schema unless a correctness defect is discovered.

Confirm that it continues to provide:

```text
Planet source provenance
Planet identity
ResourceCreationSeed
BiomeIndex
Biome identity/name/source/chance
PNDT/BIOM effective-RSGD relationship
RSGD identity/editor/source
RSGD resource order
resource identity/editor/name/rarity/source
rarity chance fields
one ExtractTimestamp per export file
```

Document any subtle source/derivation rule needed by the future loader.

---

# 5. Canonical dataset regeneration

The four canonical output files currently present in:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\
```

are:

```text
planet-atmospheric-resources.csv
planet-resource-generation.csv
ires-hierarchy.csv
planet-directory.csv
```

If any script is modified during this brief, the user must manually rerun the corresponding xEdit export before that dataset is treated as final.

Do not assume xEdit can be run headlessly.

If Codex cannot execute xEdit reliably:

- complete source audits/static changes;
- identify exactly which exports require rerunning;
- pause dataset-copy completion for those files until fresh outputs are available;
- do not fabricate regenerated files.

If no script changes are required for a given exporter, its existing current CSV may be used.

---

# 6. Replace legacy repository data inputs

Once the four current CSV outputs are confirmed current and valid, copy them from:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\
```

into:

```text
D:\Projects\starfield-resource-reproducer\data\
```

using exactly these filenames:

```text
planet-atmospheric-resources.csv
planet-resource-generation.csv
ires-hierarchy.csv
planet-directory.csv
```

## Remove legacy data files

The existing checked-in legacy datasets have outlived their role as active canonical inputs.

Remove legacy equivalents from `data/`, including old versioned/legacy-named copies such as:

```text
PlanetResourceGeneration_v5.csv
Starfield_IRES_Hierarchy.csv
Starfield_PlanetAtmosphericResources.tsv
```

Also remove any other stale duplicate that represents an older copy of one of the four canonical exports.

## Validation oracle exception

Do **not** remove:

```text
planet-all-resources.csv
```

unless the user explicitly asks.

It remains a validation/comparison oracle for the existing v1.0 reproducer until the future canonical occurrence dataset has been built and accepted.

It must not become a production input.

---

# 7. Data-copy integrity checks

For each CSV copied into `data/`:

```text
source:
D:\tools\xEdit.4.1.5p\Edit Scripts\<file>

destination:
D:\Projects\starfield-resource-reproducer\data\<file>
```

verify byte-for-byte equality immediately after copying.

Also verify:

- valid UTF-8;
- expected header;
- nonzero data rows;
- one repeated `ExtractTimestamp` value where the schema includes it;
- no accidental delimiter regression;
- no duplicate header row;
- no partial/truncated file.

For `ires-hierarchy.csv`, additionally validate:

- every parent row has `SourceFile`;
- every child row has `ChildSourceFile`;
- leaf child provenance remains blank.

For the two recently converted CSVs, preserve the regression evidence already established against their previous TSV forms.

---

# 8. Update documentation/source-of-truth references

Update current documentation that still names legacy canonical input files.

At minimum inspect:

```text
README.md
AGENTS.md
docs/ARCHITECTURE.md
docs/DOMAIN-RULES.md
docs/V1-VALIDATION-BASELINE.md
docs/CANONICAL-OCCURRENCE-EXPORT-GAP-ANALYSIS.md
docs/BACKLOG.md
```

Replace legacy active-input references with:

```text
planet-resource-generation.csv
ires-hierarchy.csv
planet-atmospheric-resources.csv
planet-directory.csv
```

Be careful with historical documents:

- do not rewrite old experiment history merely to make filenames look current;
- historical references to old filenames may remain when they describe what was actually used at the time;
- current-state/source-of-truth sections should use the new filenames.

The current canonical source-of-truth list should distinguish:

```text
production inputs:
    planet-resource-generation.csv
    ires-hierarchy.csv
    planet-atmospheric-resources.csv
    planet-directory.csv

validation-only oracle:
    planet-all-resources.csv
```

---

# 9. Update scripts/tests that reference legacy filenames — only where necessary

Search the repository for active references to:

```text
PlanetResourceGeneration_v5.csv
Starfield_IRES_Hierarchy.csv
Starfield_PlanetAtmosphericResources.tsv
```

Classify each occurrence as:

```text
CURRENT_ACTIVE_REFERENCE
HISTORICAL_REFERENCE
```

Update only active references required for the current repository to remain coherent.

Examples that may require updates:

- default data paths;
- CLI defaults;
- loader tests;
- fixture paths;
- validation scripts;
- README examples.

Do not change loader schemas or domain behavior in this brief.

If merely renaming current files causes loaders/tests to require path updates, those path-only changes are allowed.

Do not implement new Planet Directory ingestion yet. It is acceptable for `planet-directory.csv` to be present in `data/` but not yet loaded by the reproducer.

---

# 10. No 10C work yet

Do not:

- add a Planet Directory loader;
- modify `ProjectData` or domain models for body-directory metadata;
- change IRES loader structures to retain the new source fields;
- add family-origin export shaping;
- create enriched occurrence views;
- create the canonical occurrence exporter;
- alter generation or RNG behavior.

Those belong to 10C and later.

The only code changes allowed outside xEdit scripts are path/reference updates needed because canonical filenames changed.

---

# 11. Verification

Run the repository's normal static safeguards:

```text
python scripts/check_mojibake.py
git diff --check
```

Run the existing reproducer test suite if active data-path references are changed.

Run canonical validation if loader/default-path changes mean the reproducer now reads the newly named generation/IRES/atmosphere datasets.

Expected algorithmic result remains:

```text
1,444 / 1,444 exact
0 mismatches
0 errors
```

No behavioral change is expected.

Verify all four installed/repository script pairs remain byte-for-byte identical.

Verify all copied `Edit Scripts`/`data` CSV pairs are byte-for-byte identical.

---

# 12. Deliverable report

Report:

1. xEdit scripts inspected;
2. any script changes made;
3. Planet Directory field provenance findings;
4. atmospheric provenance findings;
5. Resource Tree provenance confirmation;
6. Planet Resource Generation provenance confirmation;
7. which exporters required manual reruns;
8. four canonical CSVs copied into `data/`;
9. byte-for-byte copy checks;
10. legacy `data/` files removed;
11. active filename/path references updated;
12. historical references deliberately preserved;
13. test/validation results;
14. mojibake/UTF-8/diff-check results;
15. confirmation no 10C ingestion/model work was performed;
16. confirmation no commit/push was performed.

Suggested commit message after review:

```text
refactor: refresh canonical xedit source datasets
```
