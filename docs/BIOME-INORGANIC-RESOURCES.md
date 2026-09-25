# Biome Inorganic Resources Product

## Purpose

`biome-inorganic-resources.csv` is the default consumer-facing export of
known inorganic resource locations. Its grain is:

```text
Planet x Location x Resource
```

Locations are either a planet-local terrestrial biome (`BIOME`) or an effective
atmosphere (`ATMOSPHERE`). The CSV is independently interpretable and deliberately
does not expose generation-path diagnostics or Common-family lineage.

Generate it with:

```bash
starfield-resource-reproducer
```

The default destination is `./output/biome-inorganic-resources.csv`, relative to
the caller's current working directory. If that directory cannot be created or
used, the CLI falls back to `./biome-inorganic-resources.csv`. `--output` accepts
an existing or new directory or an explicit `.csv` path. Missing parent
directories are created; explicit destinations never fall back elsewhere.

Overwrite is the default. `--no-overwrite` rejects an existing requested
artifact without prompting. The sibling manifest is off by default and is
created with `--manifest`; if a sibling manifest already exists, later successful
CSV overwrites refresh it even when `--manifest` is omitted so it cannot become
stale. A custom `my-resources.csv` uses `my-resources.manifest.json`.

## Schema version 1

The CSV has exactly these 35 columns in this order:

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

`ReproducerVersion` is the package version. `ExportTimestamp` is generated once
per run in UTC ISO 8601 form and repeated on every row. `ResourceCategory` is
always `Inorganic`. Resource names are canonical source names without aliases.
FormIDs use eight uppercase hexadecimal digits; numeric IDs are decimal.

Schema version is independent of package version and appears in the manifest.

## Location nullability

BIOME rows require the six biome fields and four effective-RSGD fields. All
atmosphere and defining-atmosphere fields are blank.

ATMOSPHERE rows require the three atmosphere fields, three defining-atmosphere
identity/source fields, and `AtmosphereInheritanceDepth`. All biome and
effective-RSGD fields are blank. Missing terrestrial generation input never
creates a synthetic biome; Volii Alpha therefore has two ATMOSPHERE rows and no
BIOME rows in the current corpus.

## Identity, collapse, and ordering

Biome identity is planet-local:

```text
PlanetFormID + BiomeIndex + BiomeFormID
```

The final uniqueness keys are:

```text
BIOME:      PlanetFormID + LocationType + BiomeIndex + BiomeFormID + ResourceFormID
ATMOSPHERE: PlanetFormID + LocationType + AtmosphereFormID + ResourceFormID
```

The enriched internal occurrence view can contain multiple rows for the same
product key when generation origin or family-assignment lineage differs. The
exporter collapses those rows only after confirming that every retained product
field is identical. Any retained-field disagreement is a hard failure.

Rows are sorted stably by numeric `StarSystemID`, `ParentPlanetID`, `PlanetID`,
`PlanetFormID`, location rank (`BIOME` before `ATMOSPHERE`), null-last numeric
biome index, biome FormID, atmosphere FormID, and resource FormID. Names are not
identity or sort keys.

## Source and validation boundaries

Production loads exactly four canonical inputs:

- `data/planet-resource-generation.csv`
- `data/ires-hierarchy.csv`
- `data/planet-atmospheric-resources.csv`
- `data/planet-directory.csv`

The Planet Directory input uses the canonical v4 schema. Its additional Solar
Array power, Wind Turbine power, and Planetary Habitation rank values remain
metadata and do not add columns to this 35-column consumer product.

These defaults resolve from the project/package canonical data location, not a
`data/` directory in the caller's current working directory. Each input can be
overridden separately with `--resource-generation-file`, `--resource-tree-file`,
`--atmospheric-resources-file`, and `--planet-directory-file`. Relative override
paths resolve from the caller's current working directory.

The generator independently predicts terrestrial resources, then the accepted
occurrence projection adds canonical body/location/resource provenance. Rejected
attempts, failed candidates, no-assignment records, traversal-only records,
resource origin, assignment mechanism, and family lineage are absent from this
default product.

`data/planet-all-resources.csv` remains validation-only. It is not loaded by the
production path and cannot create or repair product rows. Validation projects
BIOME rows to unique `PlanetFormID + ResourceFormID` pairs because the old oracle
does not fully cover atmosphere-derived resources.

## Manifest

The JSON manifest contains the dataset name, schema version, reproducer version,
export timestamp, output filename, row count, per-location row counts, number of
collapsed internal occurrences, and the four production input descriptors. Each
input descriptor records filename, source extraction timestamp, row count, and
SHA-256 digest.

When a manifest is requested or refreshed, both complete contents are derived
from the same in-memory production run and prepared as temporary files before
the CSV and JSON destinations are replaced. A failed build does not serialize
partially validated rows. `--validate-only` executes this same loading,
generation, product-building, and validation path but writes neither artifact.

## Diagnostic scope

The richer accepted-occurrence model remains available in memory for research.
A provenance-rich diagnostic export and related CLI modes are intentionally not
part of schema version 1 and have not been designed here.
