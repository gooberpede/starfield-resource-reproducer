# Canonical xEdit Source Exports

## Purpose and scope

This document records the maintained provenance contract for the four canonical
xEdit source exports. The Planet Directory script and data are synchronized to
the canonical v4 exporter; the other exporters retain their Brief 10B state.
These exports contain only game/plugin record data and deterministic
exporter-derived values; none consults the validation oracle.

These files are source inputs, not generated consumer products. The default
consumer dataset is written under `output/` and is documented separately in
`docs/BIOME-INORGANIC-RESOURCES.md`.

| Exporter | Output |
|---|---|
| `Starfield - Export Planet Atmospheric Resources.pas` | `planet-atmospheric-resources.csv` |
| `Starfield - Export Planet Resource Generation.pas` | `planet-resource-generation.csv` |
| `Starfield - Export Resource Tree.pas` | `ires-hierarchy.csv` |
| `Starfield - Export Planet Directory.pas` | `planet-directory.csv` |

Each exporter captures `FormatDateTime('yyyy-mm-dd hh:nn:ss', Now)` once in
`Initialize` and repeats that local file-production timestamp on every row.
`SourceFile`-style values come from `GetFileName(GetFile(record))`. FormIDs are
eight-digit uppercase fixed FormIDs. Missing optional elements and failed safe
lookups produce blank strings unless a field-specific rule below says otherwise.

## Planet Directory

`Starfield - Export Planet Directory.pas` version 4 is canonical and was tested
for xEdit / SF1Edit 4.1.5p. It is run on selected PNDT records or the PNDT group
and writes `planet-directory.csv` under xEdit's active `ScriptsPath`.

The row grain is one processed `PNDT` main record. Non-`PNDT` selections emit no
row. The exact approved column order is:

```text
SourceFile,ExtractTimestamp,PlanetFormID,PlanetEditorID,PlanetName,BodyType,StarSystemID,SystemName,ParentPlanetID,PlanetID,PlanetNotLandable,OceanWorld,SolarArrayPower,WindTurbinePower,PlanetaryHabitationRank
```

| Column | Record and extraction | Semantics and blank/fallback behavior |
|---|---|---|
| `SourceFile` | `PNDT`; `GetFileName(GetFile(e))` | Direct source-plugin provenance of the processed planet record. |
| `ExtractTimestamp` | Exporter value captured in `Initialize` | One value per output file. |
| `PlanetFormID` | `PNDT`; `FixedFormID(e)` | Direct canonical identity, formatted as eight hex digits. |
| `PlanetEditorID` | `PNDT`; `EditorID(e)` | Direct record metadata. |
| `PlanetName` | `PNDT`; `Body\ANAM - Name` | Direct body name. If blank, the exporter finds the `TESFullName_Component` in `Base Form Components` and reads `Component Data - Fullname\FULL - Name`; blank if neither exists. |
| `BodyType` | `PNDT`; `Body\CNAM - Body type` | Direct xEdit edit value; blank when absent. |
| `StarSystemID` | `PNDT`; `Body\GNAM - Galaxy Data\Star System ID` | Exporter-derived from xEdit's combined display value: trimmed text before the first space. It is a numeric system ID, not a FormID. Blank when the source path is absent. |
| `SystemName` | Same `PNDT` Star System ID display value | Exporter-derived text between the first `(` and following `)`. Blank when that shape is absent. No separate system record is traversed. |
| `ParentPlanetID` | `PNDT`; `Body\GNAM - Galaxy Data\Parent Planet ID` | Direct numeric hierarchy value; blank when absent. No parent `PNDT` lookup is performed. |
| `PlanetID` | `PNDT`; `Body\GNAM - Galaxy Data\Planet ID` | Direct numeric hierarchy value; blank when absent. |
| `PlanetNotLandable` | `PNDT` `Base Form Components` | Deterministic classification. The exporter locates `BGSKeywordForm_Component`, scans `Component Data - Keywords\Keywords\KWDA - Keywords`, and returns `1` when a value contains `PlanetNotLandable [KYWD:000B04F3]`; otherwise `0`. Missing components/keywords are false, not blank. |
| `OceanWorld` | `PNDT` `Biomes` plus linked `BIOM` | Deterministic classification. It returns `1` only when the PNDT has exactly one biome entry, `Biome` resolves to a `BIOM`, and recursive traversal of that BIOM resolves a keyword leaf to `BiomeTypeOcean [KYWD:002C539E]`; otherwise `0`. |
| `SolarArrayPower` | PNDT temperature keyword resolved through `BGSKeywordForm_Component` | Basic Solar Array output: Deep Freeze `2`; Frozen/Cold `4`; Temperate/Hot `6`; Scorched/Inferno `8`. Blank for non-landable bodies or when no recognized temperature keyword is available. Unexpected blanks on landable planets/moons are logged; orbitals are excluded from that warning. |
| `WindTurbinePower` | PNDT atmosphere and pressure keywords resolved through `BGSKeywordForm_Component` | Basic Wind Turbine output: no atmosphere `0`; Thin `3`; Standard/Terrestrial `6`; High/Extreme `10`. A recognized atmosphere without a recognized pressure uses the logged standard/base fallback `6`. Otherwise the value may remain blank when no recognized atmosphere/pressure combination is available. Unexpected blanks on landable planets/moons are logged; orbitals are excluded from that warning. |
| `PlanetaryHabitationRank` | Highest applicable PNDT environment-keyword requirement | Deep Freeze/Inferno gives at least rank `1`; Extreme pressure rank `2`; Corrosive/Toxic rank `3`; Extreme gravity rank `4`; otherwise `0`. Blank for non-landable bodies. |

The first 12 v4 columns remain byte-for-byte value-equivalent to the prior
canonical export aside from the file-wide extraction timestamp. The three v4
fields are canonical directory metadata, not evidenced inorganic-generation
inputs, and they do not alter the generator, validation oracle, or 35-column
consumer product.

## Planet Atmospheric Resources

The row grain is one processed `PNDT` times one effective atmospheric `IRES`.
A planet without a linked ATMO or with an effective empty list emits no rows.

### Planet and effective-atmosphere identity

| Column | Record and extraction | Semantics |
|---|---|---|
| `SourceFile` | `PNDT`; `GetFileName(GetFile(e))` | Planet-record source plugin. |
| `PlanetFormID` / `PlanetEditorID` | `PNDT`; `FixedFormID` / `EditorID` | Direct planet identity. |
| `PlanetName` | `PNDT`; `Body\ANAM - Name`, then `FULL - Name`, then `TESFullName_Component` | Canonical record-only fallback chain; blank if all paths are absent. |
| `BodyType` | `PNDT`; `Body\CNAM - Body type` | Direct xEdit edit value. |
| `StarSystemID` / `SystemName` | `PNDT`; `Body\GNAM - Galaxy Data\Star System ID` | The same deterministic split used by Planet Directory. |
| `ParentPlanetID` / `PlanetID` | `PNDT`; corresponding fields under `Body\GNAM - Galaxy Data` | Direct hierarchy values. |
| `AtmosphereFormID` / `AtmosphereEditorID` / `AtmosphereSourceFile` | First recursively encountered PNDT element whose link resolves to an `ATMO`; the linked record is normalized with `WinningOverride` | Identity and source of the effective planet-associated ATMO record. The recursion remains inside the PNDT element tree and accepts only an `ATMO` link. |

### Effective resource inheritance

ATMO inheritance follows `RFDP - Reflection Parent`. The exporter first uses
`LinksTo`; because xEdit 4.1.5p does not reliably link that leaf, it can parse the
displayed `[ATMO:xxxxxxxx]` fixed FormID and resolve it through the child ATMO's
own file/master context. Resolved parents use `WinningOverride`.

At each depth, starting with the effective ATMO at depth zero:

1. Read `RDIF - Reflection Diff\Diff\Unknown` and scan serialized `LIST` chunks.
2. Accept a non-empty list only when every eight-byte reflected form reference
   resolves to an `IRES`; exactly one valid list is required.
3. Treat a sole zero-count child list as an explicit clear. This remains the
   exporter's documented **PROVISIONAL** rule because xEdit does not expose the
   reflected property identifier.
4. If no local override exists, traverse `RFDP` to the parent and increment the
   depth.
5. At a root with no parent, read `REFL - Reflection\Object Data\Unknown`. One
   valid IRES list supplies the value; no valid IRES list means an effective
   empty root value. Multiple valid lists are reported as ambiguous.

Traversal is capped at 32 parent links and unresolved/ambiguous cases produce a
warning and no rows rather than an invented value.

| Column | Extraction | Semantics |
|---|---|---|
| `ResourceFormID` | Serialized effective list entry, resolved as `IRES` | Direct resource identity in effective list order. |
| `ResourceEditorID` / `ResourceName` | Resolved `IRES`; `EditorID` and full-name fallback logic | Resource record metadata. |
| `ResourceSourceFile` | Resolved `IRES`; `GetFileName(GetFile(resourceRecord))` | The resource's own plugin, independently of both ATMO records. |
| `ResourceDefinedByAtmosphereFormID` / `ResourceDefinedByAtmosphereEditorID` / `ResourceDefinedByAtmosphereSourceFile` | ATMO at which the accepted local/root list was found | Defining ATMO identity is retained separately from the effective planet-associated ATMO. |
| `AtmosphereInheritanceDepth` | Number of RFDP parent steps from effective ATMO to defining ATMO | Deterministic zero-based depth; `0` means locally defined. |
| `AtmosphericResourceCount` | Count of the resolved effective list | Repeated for every resource row for the planet. |
| `AtmosphericResourceIndex` | Zero-based list position | Preserves serialized effective list order. |

The maintained 23-column atmospheric schema does **not** contain a
`ResourceRarity` column. Brief 10B asked that name be audited while also
requiring the already-confirmed schema to remain unchanged. Rarity is direct
`IRES\SNAM - Rarity` data available in `ires-hierarchy.csv` and
`planet-resource-generation.csv`; it is not inferred or emitted by this
exporter. This discrepancy did not justify silently changing the established
schema.

## Resource Tree

The row grain and traversal are unchanged: each selected `IRES` parent emits one
row per direct element in `Child Resources`, in stored order. A missing or empty
array emits one leaf row. An unresolved/non-IRES child reference also emits a
blank-child row rather than fabricated metadata.

Parent fields come independently from the selected parent `IRES`:
`SourceFile` from its source plugin, `FormID`/`EditorID` from record identity,
`Name` from `FULL - Name` then `FULL`, and `Rarity` from `SNAM - Rarity`.
Child fields use the linked child `IRES` independently, including
`ChildSourceFile`; they are all blank on leaf/unresolved rows. The one timestamp
captured at initialization repeats across the file.

This confirms the 10A.2 schema and preserves graph order and parent-child
semantics.

## Planet Resource Generation

The row grain is `PNDT x biome entry x distinct referenced RSGD x ordered RSGD
resource entry`.

- Planet provenance and identity come from the processed `PNDT`. `PlanetName`
  uses `Body\ANAM - Name`, then `TESFullName_Component`.
- `ResourceCreationSeed` reads `PNDT\RSCS - Resource Creation Seed` and converts
  a negative xEdit signed display to the equivalent unsigned 32-bit decimal.
- `BiomeIndex` is the zero-based stored position in `PNDT\Biomes`; no sorting is
  performed. `BiomeChance` reads the entry's `Chance`.
- `BiomeUnknown0Raw` is the first direct biome-entry child whose displayed name
  starts with `Unknown`. `BiomeUnknown0UInt32` strips non-hex characters and
  decodes the first four bytes as little-endian unsigned data.
- Biome identity/source/name come from the linked `BIOM`; the name reads
  `FULL - Name` then `FULL`.
- The PNDT override is the biome entry's `Resource Generation` reference. The
  BIOM relationship checks `RNAM - Resource Generation`, then known alternate
  xEdit labels, then recursively scans only the BIOM element tree for the first
  link resolving to `RSGD`.
- `RSGDSource` is `PNDT`, `BIOM`, or `PNDT+BIOM`. When both references identify
  the same source-record key, one combined set is emitted; different references
  are emitted independently. Missing references are not invented.
- RSGD identity/source fields come from the resolved `RSGD`. `RSGDResourceIndex`
  is the zero-based stored position in its `Resources` array.
- Resource identity/editor/name/rarity/source come from each entry's
  `RNAM - Resource` linked `IRES`; rarity is `SNAM - Rarity`. Unresolved links
  are diagnosed and identity fields remain blank.
- `BiomeCommonChance` reads
  `DNAM - Generation Data\Biome\Common\Chance to Appear`. The Uncommon, Rare,
  Exotic, Unique, Special, and Everywhere columns read their corresponding
  `Chance per Node` paths. Values are not normalized or merged.

The audit found no schema gap or correctness defect. In particular, PNDT and
BIOM relationships are exported distinctly; the reproducer's later effective
RSGD precedence remains a loader/domain concern.

## Repository roles

The four outputs above are canonical production source inputs. Brief 10C loads
all four, retains their file-wide extraction timestamps, and validates compatible
body/resource identities across them. Planet Directory metadata remains distinct
from evidence that a body has terrestrial or atmospheric occurrence input.
`planet-all-resources.csv` remains a validation-only oracle and is never a
production input.
