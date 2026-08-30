# Implementation Brief 01 — Canonical Data Loading and Domain Model

## Context

Repository:

```text
gooberpede/starfield-resource-reproducer
```

Brief 00 established the Python project scaffold. Brief 01 is the first domain-facing implementation step.

The repository already contains the three canonical datasets:

```text
data/PlanetResourceGeneration_v5.csv
data/Starfield_IRES_Hierarchy.csv
data/planet-all-resources.csv
```

Their roles are deliberately different:

```text
PlanetResourceGeneration_v5.csv
    static planet / biome / RSGD generation inputs

Starfield_IRES_Hierarchy.csv
    static IRES rarity + resource graph

planet-all-resources.csv
    verified game/runtime output oracle
```

The deprecated dataset:

```text
Starfield_InorganicResources_Canonical.csv
```

must not be introduced or used.

This brief is about **loading, validating, and representing data only**.

Do not implement PRNG behavior or resource generation.

---

## Goal

After Brief 01, application code should be able to load the three canonical CSVs into clean Python domain objects without depending on CSV row dictionaries elsewhere in the program.

The loader should:

1. validate required schemas;
2. normalize identities consistently;
3. reconstruct planets and PNDT biome ordering;
4. reconstruct all RSGDs associated with each biome while preserving resource-array order;
5. expose the proven PNDT-over-BIOM effective-RSGD relationship without discarding the underlying source data;
6. reconstruct the IRES graph;
7. load the runtime oracle separately;
8. expose canonical inorganic resource sets by `PlanetFormID`;
9. fail loudly on malformed or contradictory static data.

This brief should make later PRNG and generation work operate only on domain objects.

---

## Required Pre-Implementation Reading

Before editing, read:

```text
AGENTS.md
README.md
docs/ARCHITECTURE.md
docs/BACKLOG.md
docs/DOMAIN-RULES.md
docs/IMPLEMENTATION-WORKFLOW.md
docs/implementation-briefs/00-project-bootstrap.md
```

Then inspect the current repository tree and current tests.

If Brief 00 has not been committed yet, work from the actual current working tree rather than assuming only `main`.

Do not modify canonical CSV contents.

---

# 1. Canonical Schemas

## 1.1 `PlanetResourceGeneration_v5.csv`

Actual columns:

```text
SourceFile
ExtractTimestamp
PlanetFormID
PlanetEditorID
PlanetName
ResourceCreationSeed
BiomeIndex
BiomeFormID
BiomeEditorID
BiomeName
BiomeSourceFile
BiomeChance
BiomeUnknown0Raw
BiomeUnknown0UInt32
RSGDSource
RSGDFormID
RSGDEditorID
RSGDSourceFile
RSGDResourceIndex
ResourceFormID
ResourceEditorID
ResourceName
ResourceRarity
ResourceSourceFile
BiomeCommonChance
BiomeUncommonChance
BiomeRareChance
BiomeExoticChance
BiomeUniqueChance
BiomeSpecialChance
BiomeEverywhereChance
```

Current verified dataset shape:

```text
7,920 rows
1,444 distinct PlanetFormID values
3,210 distinct (PlanetFormID, BiomeIndex) pairs
32 distinct RSGDs
```

### Important grain

This file is **not** one row per biome.

Its grain is approximately:

```text
planet
× biome
× RSGD source/definition retained for that biome
× ordered RSGD resource entry
```

For a biome with a PNDT override, the export may intentionally contain **both**:

```text
RSGDSource = PNDT
RSGDSource = BIOM
```

Do not collapse those rows before reconstructing the two source definitions.

Example: Kreet Mountains contains both:

```text
PNDT -> MountainDefaultRes_Kreet
BIOM -> MountainDefaultRes
```

The proven runtime rule later chooses PNDT as effective, but the loader must preserve both.

---

## 1.2 `Starfield_IRES_Hierarchy.csv`

Actual columns:

```text
FormID
EditorID
Name
Rarity
ChildFormID
ChildEditorID
ChildName
ChildRarity
```

Current verified dataset shape:

```text
56 rows
47 distinct resource FormIDs
35 non-null child edges
21 rows with no child
```

This is an **edge list**, not a pre-built tree.

A leaf resource is represented by a row whose child columns are blank.

All resource identities should be reconstructed independently of whether they appear as a parent, a child, or both.

---

## 1.3 `planet-all-resources.csv`

Actual columns:

```text
SystemName
PlanetName
BodyType
PlanetFormID
PlanetEditorID
StarSystemID
ParentPlanetID
PlanetID
ResourceCategory
ResourceFormID
ResourceEditorID
ResourceName
Rarity
```

Current verified dataset shape:

```text
7,663 total rows
1,445 distinct bodies
6,040 Inorganic rows
1,623 Organic rows
1,444 bodies with at least one Inorganic row
```

The 1,444 bodies with inorganic output correspond to the 1,444 bodies in `PlanetResourceGeneration_v5.csv`.

This file is the **validation oracle only**.

It must never influence generation decisions.

### Critical rarity warning

The oracle's `Rarity` column is **not the authoritative generation category**.

For example, the oracle describes:

```text
Water     -> Common
Helium3   -> Common
```

whereas the generation data/IRES correctly establishes:

```text
Water     -> Everywhere
Helium-3  -> Special
```

Therefore:

> Never use `planet-all-resources.csv:Rarity` to determine Common/Special/Everywhere generation behavior.

Treat oracle rarity as descriptive output metadata only.

The authoritative generation rarity/category comes from the static generation/IRES datasets.

---

# 2. Required Modules

Create:

```text
src/starfield_resource_reproducer/
├── domain.py
└── load_data.py
```

Existing Brief 00 modules should remain small and should not absorb loader logic.

Do not add generation, PRNG, candidate-selection, or validation-engine modules yet unless a tiny helper is genuinely necessary.

---

# 3. FormID Representation

## Requirement

Do not represent canonical FormIDs only as integers.

A FormID such as:

```text
000057CB
010026C5
```

must retain its eight-digit hexadecimal representation, including leading zeroes.

Use either:

1. a small immutable `FormId` value object; or
2. a rigorously normalized string type at the domain boundary.

A small `FormId` value object is preferred if it remains simple.

### Normalization rules

Canonical internal text form:

```text
8 uppercase hexadecimal characters
no `0x` prefix
```

Examples:

```text
"000057cb" -> "000057CB"
"0x000057CB" -> "000057CB"   # acceptable if helper supports external input
"010026c5" -> "010026C5"
```

Reject malformed values.

If a numeric view is useful, expose it as a derived property rather than replacing the canonical text representation.

Do not reinterpret plugin/load-order semantics in this brief.

---

# 4. Domain Model

Use standard-library dataclasses and enums.

Prefer immutable (`frozen=True`) value/domain objects where practical.

The exact class names may vary slightly, but preserve the responsibilities below.

## 4.1 Generation rarity enum

Create an enum representing the static generation categories:

```text
Common
Uncommon
Rare
Exotic
Unique
Special
Everywhere
```

This should parse `ResourceRarity` from v5 and `Rarity` / `ChildRarity` from the IRES hierarchy.

Do not use the oracle's `Rarity` field as this enum's authoritative source for generation behavior.

---

## 4.2 `ResourceRef` or equivalent

Represents stable resource metadata:

```text
form_id
editor_id
name
rarity
source_file?   # where available
```

It is acceptable for IRES and RSGD resource objects to have distinct classes if that better preserves responsibilities.

Avoid inventing a large inheritance hierarchy.

---

## 4.3 `RSGDResourceEntry`

Represents one ordered RSGD entry.

Required fields:

```text
index
resource_form_id
resource_editor_id
resource_name
resource_rarity
resource_source_file

common_chance
uncommon_chance
rare_chance
exotic_chance
unique_chance
special_chance
everywhere_chance
```

Chances should be parsed as numeric values.

Do not normalize percentages.

Do not reorder entries by rarity, FormID, or name.

---

## 4.4 `RSGDDefinition`

Represents one RSGD definition associated with a biome.

Required fields:

```text
source               # PNDT or BIOM
form_id
editor_id
source_file
entries               # ordered by RSGDResourceIndex
```

`source` should use a small enum such as:

```text
PNDT
BIOM
```

The v5 export may contain a historical/provenance value `PNDT+BIOM` in other contexts. If present in the current data, handle it explicitly and conservatively rather than silently treating it as one side.

Do not merge entries from different RSGD definitions.

---

## 4.5 `Biome`

Required fields:

```text
index
form_id
editor_id
name
source_file
chance
unknown0_raw
unknown0_uint32

pndt_rsgd   # optional
biom_rsgd   # optional
```

Provide an `effective_rsgd` property or method implementing the already-proven static precedence rule:

```text
if pndt_rsgd is present:
    effective_rsgd = pndt_rsgd
else:
    effective_rsgd = biom_rsgd
```

This property may live on `Biome` because the precedence rule is established domain behavior.

However:

- preserve both source RSGDs;
- do not delete or overwrite the BIOM definition when PNDT exists;
- do not merge their entries.

If neither exists, fail during loading unless the canonical data demonstrates a legitimate case that the current documents already describe.

---

## 4.6 `Planet`

Required fields:

```text
form_id
editor_id
name
source_file
resource_creation_seed
biomes
```

`resource_creation_seed` must be parsed as an unsigned 32-bit integer:

```text
0 <= RSCS <= 0xFFFFFFFF
```

`biomes` must be stored in ascending `BiomeIndex` order.

This order is semantically significant and will be the input to the future deterministic shuffle.

Do not sort biomes by chance/name/FormID.

---

## 4.7 `IRESNode`

Required fields:

```text
form_id
editor_id
name
rarity
children
```

`children` should preserve the order present in the CSV edge list unless evidence or extraction semantics later establishes another ordering rule.

Do not infer transitive children.

For example, Nickel should directly expose:

```text
Cobalt
Palladium
```

not Platinum or Tasine as direct children.

---

## 4.8 Oracle models

Keep oracle data separate from generation-domain models.

A simple model such as:

```text
CanonicalResource
CanonicalBodyResources
```

is appropriate.

A canonical resource record may contain:

```text
resource_form_id
resource_editor_id
resource_name
oracle_rarity
```

A body/oracle object should expose at least:

```text
planet_form_id
planet_editor_id
planet_name
system_name
body_type
inorganic_resources
```

Store canonical inorganic membership as a set/frozenset of FormIDs while retaining metadata for diagnostics.

Do not place the oracle's expected resource set onto the `Planet` generation-input object.

The generator must eventually be able to operate without an oracle loaded.

---

# 5. Loader API

Provide a small public loader API in `load_data.py`.

A good shape would be conceptually:

```python
load_generation_data(path: Path) -> dict[FormId, Planet]

load_ires_hierarchy(path: Path) -> dict[FormId, IRESNode]

load_canonical_oracle(path: Path) -> dict[FormId, CanonicalBodyResources]
```

Optionally also provide:

```python
load_project_data(data_dir: Path) -> ProjectData
```

where `ProjectData` simply bundles the three independently loaded datasets.

Do not make module import automatically read files.

Do not depend on the current working directory inside core loaders.

Paths must be explicit or resolved by a thin project-level helper.

Use the standard library `csv` module.

Do not add pandas.

---

# 6. Static Data Validation

The loaders must be deliberately defensive.

Raise a clear project-specific exception such as:

```text
DataValidationError
```

for malformed or contradictory canonical input.

Do not silently repair data.

## 6.1 Schema validation

Each loader must verify required column names before processing rows.

An error should name:

```text
file
missing column(s)
```

Extra columns may be tolerated.

---

## 6.2 Planet consistency

Within one `PlanetFormID`, reject conflicting values for fields that should be constant, including at least:

```text
PlanetEditorID
PlanetName
SourceFile
ResourceCreationSeed
```

Validate RSCS is an unsigned 32-bit integer.

---

## 6.3 Biome consistency

Within one:

```text
(PlanetFormID, BiomeIndex)
```

reject conflicting biome identity/metadata such as:

```text
BiomeFormID
BiomeEditorID
BiomeName
BiomeSourceFile
BiomeChance
BiomeUnknown0Raw
BiomeUnknown0UInt32
```

Biome indices for a planet must be unique after grouping and should form the canonical ordered list.

Do not require them to be globally unique.

---

## 6.4 RSGD consistency

Within one biome and RSGD definition:

- reject conflicting RSGD metadata;
- reject duplicate `RSGDResourceIndex`;
- sort entries only by integer `RSGDResourceIndex`;
- preferably assert indices form a contiguous zero-based sequence if the current canonical data satisfies that invariant.

If a non-contiguous case exists in canonical data, preserve it and report rather than inventing missing entries.

---

## 6.5 Resource metadata consistency

When the same resource FormID is encountered repeatedly in a static input dataset, conflicting identity metadata should fail.

At minimum detect conflicts in:

```text
EditorID
Name
generation rarity
```

Do not attempt to reconcile spelling differences automatically.

---

## 6.6 IRES validation

For a given `FormID`, parent metadata must be consistent across rows.

For a given child FormID, child metadata must also be consistent.

When the same FormID appears once as a child and elsewhere as a parent, metadata should agree.

Blank child fields represent no edge.

Do not create a fake blank child node.

Reject half-populated child identities, for example:

```text
ChildFormID present
ChildEditorID absent
```

unless the actual canonical file demonstrates and documents such a case.

---

## 6.7 Oracle validation

Validate:

- `(PlanetFormID, ResourceFormID)` is unique;
- body metadata is consistent for each `PlanetFormID`;
- resource identity metadata is consistent for repeated resource FormIDs.

Load both Organic and Inorganic source rows if convenient, but expose a clear inorganic-only lookup for current reproducer use.

At minimum:

```python
oracle[planet_id].inorganic_resources
```

must contain only rows where:

```text
ResourceCategory == "Inorganic"
```

Do not discard organic rows from the source merely because they are out of scope if preserving them costs little, but current domain/API requirements only need the inorganic subset.

---

# 7. Known-Case Data Tests

Add focused loader/domain tests using the real canonical CSVs.

These tests are **data reconstruction tests**, not generation tests.

They should establish that the loader sees the same inputs we have already verified manually.

## 7.1 Kreet

Expected:

```text
PlanetFormID: 0003F59F
RSCS:         2842708811
Biome count:  3
Biome order:  [0, 1, 2]
```

Biome identities:

```text
0 Frozen Volcanic
1 Mountains
2 Volcanic
```

Kreet Mountains must preserve both:

```text
PNDT -> MountainDefaultRes_Kreet
BIOM -> MountainDefaultRes
```

and:

```text
effective_rsgd == MountainDefaultRes_Kreet
```

Kreet Volcanic must preserve both:

```text
PNDT -> VolcanicDefaultRes_Kreet
BIOM -> VolcanicDefaultRes
```

and choose PNDT as effective.

Frozen Volcanic has no PNDT override and should use:

```text
FrozenBarrenDefaultRes
```

The canonical oracle inorganic set for Kreet must contain exactly:

```text
Argon
Iron
Lead
Water
Alkanes
Silver
Neon
```

Do not test shuffled biome order here; that belongs to the future generation/PRNG briefs.

---

## 7.2 Mimas

Expected:

```text
PlanetFormID: 0005DEC0
RSCS:         2008989584
Biome count:  1
Biome:        Frozen Plains
Effective RSGD:
    FrozenBarrenDefaultRes03
```

RSGD resource order must be:

```text
0 Water
1 Nickel
2 Lead
```

with:

```text
Water  -> EverywhereChance 100
Nickel -> CommonChance 60
Lead   -> CommonChance 40
```

Canonical oracle inorganic set:

```text
Water
Nickel
Palladium
```

Again, do not generate Palladium in this brief. Only verify the oracle contains it.

---

## 7.3 Decaran VII-b

Expected:

```text
PlanetFormID: 0005DF7F
RSCS:         1633829920
Biome count:  1
Biome:        Craters
```

Preserve both:

```text
PNDT -> UniqueCrateredBarrenVytiniumRes
BIOM -> CrateredNoLifeDefaultRes
```

Effective RSGD must be PNDT.

The PNDT RSGD ordered entries are:

```text
0 Helium-3  Special
1 Uranium   Common
```

Relevant chances:

```text
Helium-3 Special = 100

Uranium:
Common   = 100
Uncommon = 75
Rare     = 35
Exotic   = 15
Unique   = 100
```

Canonical oracle inorganic set:

```text
Helium3
Uranium
Iridium
Vytinium
```

Note the naming difference:

```text
static generation data: Helium-3
oracle:                 Helium3
```

Matching must ultimately use FormID, not name.

---

## 7.4 Oberon

Expected:

```text
PlanetFormID: 0005DECC
RSCS:         555484356
Biome count:  1
```

Effective RSGD ordered entries:

```text
0 Water
1 Nickel
2 Lead
```

Canonical oracle inorganic set:

```text
Water
Nickel
```

No generation should occur in this brief.

---

# 8. IRES Graph Tests

Use the real hierarchy.

At minimum verify direct edges:

## Nickel

```text
Nickel
├─ Cobalt      Uncommon
└─ Palladium   Exotic
```

Do not expect Platinum as a direct Nickel child.

## Uranium

```text
Uranium
├─ Iridium     Uncommon
├─ Vanadium    Rare
└─ Plutonium   Exotic
```

## Copper

```text
Copper
├─ Fluorine    Uncommon
└─ Gold        Rare
```

Also verify leaf handling, e.g. a leaf node has:

```text
children == ()
```

or equivalent empty immutable collection.

---

# 9. Whole-Dataset Integrity Tests

In addition to worked cases, add inexpensive integrity assertions against the supplied canonical data.

Expected current counts:

```text
Generation planets:       1,444
Planet-biome pairs:       3,210
Generation rows:          7,920

IRES distinct resources:     47
IRES direct edges:            35

Oracle total rows:         7,663
Oracle bodies:             1,445
Oracle inorganic rows:     6,040
Oracle organic rows:       1,623
Oracle inorganic bodies:   1,444
```

Also assert:

```text
set(generation PlanetFormID)
==
set(oracle PlanetFormID having Inorganic rows)
```

This is a useful cross-source integrity check.

Do not make tests depend on row order of `planet-all-resources.csv`.

---

# 10. Numeric Parsing

Use explicit parsing helpers rather than scattered `int()` / `float()` calls.

At minimum parse:

```text
ResourceCreationSeed      -> int
BiomeIndex                -> int
BiomeUnknown0UInt32       -> int
RSGDResourceIndex         -> int

BiomeChance               -> numeric
BiomeCommonChance         -> numeric
BiomeUncommonChance       -> numeric
BiomeRareChance           -> numeric
BiomeExoticChance         -> numeric
BiomeUniqueChance         -> numeric
BiomeSpecialChance        -> numeric
BiomeEverywhereChance     -> numeric
```

Do not divide percentages by 100 in the loader.

Store the source percentages as percentages.

The later generation engine will decide where/how to convert them.

Do not attempt float32 emulation in this brief.

---

# 11. Provenance Preservation

Preserve these fields where present:

```text
SourceFile
BiomeSourceFile
RSGDSourceFile
ResourceSourceFile
```

They are not decorative.

They may matter when DLC/plugin behavior is investigated.

Do not collapse all provenance to `Starfield.esm`.

---

# 12. No Algorithm Leakage

Brief 01 must not implement:

- MT19937;
- random draws;
- deterministic shuffle;
- root weighted selection;
- Special selection;
- Everywhere insertion;
- descendant candidates;
- inclusion rolls;
- family cache;
- result prediction;
- mismatch comparison.

The only "selection" allowed is the already-established static property:

```text
Biome.effective_rsgd
```

which resolves PNDT-over-BIOM precedence.

Do not use the oracle to infer or fill missing static generation data.

---

# 13. CLI Scope

Do not add `--planet` or `--all` yet.

If useful for manual verification, a tiny developer-only loader function/test is preferable to expanding the CLI prematurely.

The CLI remains the Brief 00 bootstrap surface.

---

# 14. Error Design

Create a small explicit exception type, e.g.:

```python
class DataValidationError(ValueError):
    ...
```

Errors should include useful context such as:

```text
dataset/file
row where practical
PlanetFormID
BiomeIndex
RSGDFormID
field/value
```

Avoid raw `KeyError` or cryptic unpacking errors escaping for canonical validation failures.

No elaborate error hierarchy is required.

---

# 15. Suggested File Shape

A reasonable implementation outcome is:

```text
src/starfield_resource_reproducer/
├── __init__.py
├── cli.py
├── domain.py
└── load_data.py

tests/
├── test_cli.py
├── test_package.py
├── test_domain.py
├── test_load_generation_data.py
├── test_load_ires.py
└── test_load_oracle.py
```

Codex may combine test files if that improves clarity.

Do not create unused placeholder modules from the future architecture.

---

# 16. Required Validation

Run:

```powershell
python -m pytest
```

using Codex's validated Python environment.

If editable-install validation is appropriate after package changes, also run:

```powershell
python -m pip install -e ".[dev]"
```

or the environment-equivalent command Codex used successfully in Brief 00.

Tests must include:

- Brief 00 tests;
- schema validation;
- FormID normalization;
- generation dataset reconstruction;
- IRES reconstruction;
- oracle reconstruction;
- known-case assertions;
- whole-dataset integrity counts.

Do not require the user to create a local `.venv` for this brief.

---

# 17. Acceptance Criteria

Brief 01 is complete when:

- [ ] `domain.py` exists with small typed domain objects.
- [ ] `load_data.py` loads all three canonical CSVs using the standard library.
- [ ] No new runtime dependency has been added.
- [ ] FormIDs preserve canonical 8-digit uppercase hex representation.
- [ ] RSCS is represented as unsigned 32-bit integer data.
- [ ] Planet biomes are reconstructed in `BiomeIndex` order.
- [ ] RSGD entries preserve `RSGDResourceIndex` order.
- [ ] PNDT and BIOM RSGDs are both preserved where both exist.
- [ ] `Biome.effective_rsgd` uses PNDT when present, otherwise BIOM.
- [ ] IRES direct-child graph is reconstructed correctly.
- [ ] Oracle data remains separate from generation-domain data.
- [ ] Oracle inorganic lookup is by FormID, not by resource name.
- [ ] Oracle `Rarity` is not used as generation rarity/category.
- [ ] Kreet, Mimas, Decaran VII-b, and Oberon loader tests pass.
- [ ] Dataset integrity/count tests pass.
- [ ] Generation and oracle inorganic body FormID sets match.
- [ ] Invalid/conflicting canonical input produces clear validation errors.
- [ ] No PRNG or resource-generation behavior is implemented.
- [ ] Canonical CSV files remain byte-for-byte unchanged.
- [ ] New substantive modules comply with the project code-documentation standard

---

# 18. Documentation Updates

Update `docs/ARCHITECTURE.md` only if the implemented domain/loading boundaries materially differ from the current documented architecture.

Update `docs/BACKLOG.md` to mark genuinely completed **Phase 1 — Canonical Data Loading** items.

Do not mark:

```text
PRNG compatibility
core generation
worked-case generation
full canonical validation
```

as complete.

If a canonical-data invariant discovered during implementation contradicts this brief, do not silently alter the loader to fit the brief. Report it and preserve the actual data.

---

# 19. Commit Guidance

Suggested commit:

```text
feat: add canonical data loaders
```

If domain types and loader implementation naturally form separate reviewable commits, acceptable alternatives are:

```text
feat: add resource generation domain model
feat: add canonical data loaders
```

Keep documentation bookkeeping separate only if useful.

Do not commit generated caches or environment directories.

The implementation brief itself is now intended to be tracked under:

```text
docs/implementation-briefs/
```

unless the user explicitly says otherwise.

---

# 20. Codex Completion Report

When finished, report:

1. files created;
2. files modified;
3. domain objects introduced;
4. loader public API;
5. validation rules implemented;
6. test count and result;
7. observed dataset counts;
8. known-case validation results;
9. whether all 1,444 inorganic oracle bodies match the generation-input body set;
10. whether any canonical-data anomalies were discovered;
11. any deviations from this brief;
12. blockers/questions for Brief 02.

Do not begin Brief 02 automatically.

---

## Next Planned Brief

If Brief 01 passes cleanly, Brief 02 will isolate the highest-risk algorithmic dependency:

```text
MT19937 / PRNG compatibility and exact draw behavior
```

It should consume the domain objects created here but still avoid implementing the full resource-generation engine.
