# Architecture

## Objective

Maintain a small, deterministic reference implementation of vanilla Starfield
inorganic planetary-resource generation. The v1.0 architecture prioritizes
correctness, inspectable state transitions, and strict separation between
prediction and validation.

## Boundaries

The generator operates only on typed domain objects. CSV loading, generation,
diagnostics, and oracle comparison remain separate concerns.

```text
canonical static inputs                  runtime-derived oracle
          |                                      |
          v                                      |
      load_data.py                               |
          |                                      |
          v                                      |
  typed ProjectData                              |
          |                                      |
          v                                      |
     generation.py                               |
          |                                      |
          v                                      v
 independent PlanetGenerationResult ----> validation.py
```

The oracle is never passed into generation. Validation begins only after an
independent prediction exists.

## Canonical Data Roles

- `planet-resource-generation.csv` supplies authoritative PNDT, BIOM,
  effective-RSGD, RSGD-order, and RSCS inputs.
- `ires-hierarchy.csv` supplies the authoritative IRES rarity and
  ordered child graph.
- `planet-atmospheric-resources.csv` supplies authoritative effective
  atmospheric inorganic-resource records for the current corpus.
- `planet-directory.csv` supplies the canonical PNDT body directory. It is
  staged in `data/` but intentionally has no 10B loader or domain-model path.
- `planet-all-resources.csv` supplies the validator's canonical planet-wide
  CK/RSGD-visible inorganic membership.

The oracle omits at least some atmosphere-derived resources, so it is not a
complete final planetary-resource oracle. `Starfield_InorganicResources_Canonical.csv`
is deprecated.

See `docs/CANONICAL-XEDIT-EXPORTS.md` for the source-record paths, provenance,
fallbacks, and deterministic exporter-derived fields in all four source exports.

## Implemented Domain Objects

### Static input model

- `FormId` is the stable identity type. Names and EditorIDs are display metadata.
- `Planet` owns unsigned RSCS and `Biome` values in PNDT `BiomeIndex` order.
- `Biome` retains both PNDT and BIOM references. Its `effective_rsgd` property
  implements PNDT-over-BIOM precedence without merging.
- `RSGDDefinition` retains its source and ordered `RSGDResourceEntry` sequence.
- `IRESNode` retains rarity and ordered child references.
- `AtmosphericResourceRecord` retains planet, ATMO, resource, source-file, and
  inheritance provenance.
- `CanonicalBodyResources` is validation-only runtime/oracle data.
- `ProjectData` bundles independently loadable inputs without changing their roles.

### Planet-wide identity and capacity

`PlanetResourceState` owns the planet-wide set of occupied resource FormIDs and
the ordered `ResourceOccurrence` log. The CK path is proven to guard the shared
resource-ID state at count eight. The reproducer's STRONG, full-corpus-validated
model treats occupancy as eight unique FormIDs across ATMO, Everywhere, Special,
Common, and emitted descendants.

A repeated FormID records another provenance occurrence but does not occupy
another slot in this validated model. This is not asserted as a universal engine
proof for every same-FormID collision at every insertion site. Identity occupancy
and occurrence provenance are intentionally separate.

### Resource occurrence and provenance

`ResourceOccurrence` records:

- the resource identity;
- `ResourceProvenance` (`ATMO`, `EVERYWHERE`, `SPECIAL`, `COMMON`, or
  `DESCENDANT`);
- whether the occurrence belongs to shared state and whether it occupied a new
  slot;
- biome/effective-RSGD context where applicable;
- Common-family root, assignment mechanism, and guard reason where applicable;
- the complete atmosphere record for ATMO occurrences.

This preserves duplicate channel occurrences without conflating them with unique
capacity occupancy.

### Family cache, origin, and assignment

`ResourceFamilyResult` is the immutable cached configuration for one Common root.
It stores structural descendant levels, emitted resources, diagnostics, and a
`FamilyOrigin`.

`FamilyOrigin` means the family configuration was originally generated while
processing that biome/RSGD context. It does not imply that later assignments copy
from a biome object.

`CommonFamilyAssignment` describes how the current biome receives a family:

```text
NEW_FAMILY
NORMAL_CACHE_REUSE
GUARD_MATCHED_FALLBACK
GUARD_GENERAL_FALLBACK
NO_COMMON_ASSIGNMENT
```

It retains the selected family, guard/no-assignment reason, RSGD Common roots,
fallback pool, and fallback RNG draw. Family origin and current assignment
mechanism remain distinct.

### Biome and planet result views

`BiomeFamilyGenerationResult` contains the outer biome decisions, optional cache
access, and explicit Common assignment.

`BiomeResourceView` is a biome-centric view of Everywhere, Special, and
Common/Descendant occurrences. Association uses PNDT biome index rather than
assuming a BIOM FormID is unique within a planet.

`PlanetGenerationResult` is the complete oracle-independent prediction. It keeps:

- initial and shuffled biome order;
- atmosphere and all provenance occurrences;
- planet-wide occupied identities;
- family cache and family results;
- biome assignments;
- RSGD/CK-visible resources and FormIDs;
- final player-facing union resources and FormIDs;
- structured events and final RNG draw count.

`PlanetValidationResult` belongs to `validation.py` and adds expected, missing,
unexpected, and classification fields. Canonical data never enters
`PlanetGenerationResult`.

## Generation Pipeline

`generation.py` implements this order:

```text
effective atmosphere resources
    -> record ATMO occurrences and identities
    -> Everywhere/category-6 pre-pass over every effective RSGD
    -> build PNDT biome work list in BiomeIndex order
    -> shuffle with the RSCS-seeded MT19937
    -> for each shuffled biome:
         resolve effective RSGD
         -> Special/category-5 selector
         -> record Special immediately in shared state
         -> five-tree guard
         -> shared-eight guard
         -> normal Common selector if unguarded
            -> NEW_FAMILY or NORMAL_CACHE_REUSE
         -> guarded family fallback otherwise
            -> matching cached roots preferred
            -> otherwise all cached families
            -> no RSGD Common roots means NO_COMMON_ASSIGNMENT
```

The Special insertion occurs before either Common guard. A new Special can fill
slot eight and force fallback in the same biome; a duplicate Special records an
occurrence without increasing occupied identity count.

The five-tree guard suppresses normal Common selection after five distinct
cached family configurations. The shared-eight guard suppresses it at eight
unique occupied resource identities. Both are pre-selector controls and consume
no Common-selector draw when they fire.

Guard fallback assigns an existing immutable cached family. It records new
biome-context occurrences but does not mutate the family cache or rerun descendant
generation.

New-family descendant traversal processes Uncommon, Rare, Exotic, then Unique.
Structural selection and emission are separate; traversal continues through an
omitted selected candidate.

## PRNG Architecture

`StarfieldRng` owns the unsigned-RSCS-seeded MT19937 state and draw accounting.
The APIs remain semantically distinct:

```text
next_bounded_integer
    rejection/modulo; biome shuffle; rejected attempts consume words

next_probability
    binary32(raw) * binary32(2^-32), then binary32 * binary32(0.99999)

Special/Common weighted selector
    one probability draw before category enumeration; stored order; cumulative;
    no normalization; draw still occurs for zero/one/100-percent candidates

next_scaled_index
    descendant candidate index from float32-scaled probability

next_fallback_family_index
    guard-fallback family index with distinct semantic/event provenance
```

The last two share an arithmetic shape but must not be consolidated. A fallback
pool of one still consumes its fallback draw.

## Module Responsibilities

### `load_data.py`

Parses and validates the four canonical datasets, reconstructs ordered immutable
domain objects, and fails loudly on malformed or conflicting source data. It
makes no generation decisions.

### `prng.py`

Implements MT19937, the recovered probability conversion, integer bounded helper,
descendant scaled-index helper, fallback scaled-index helper, and exact draw
records.

### `candidates.py`

Builds rarity-specific structural candidates from root and current-node children,
preserving runtime order and first-occurrence de-duplication.

### `generation.py`

Owns the pipeline, shared identity state, family cache, assignments, provenance,
and result assembly. It performs no file or oracle access.

`orchestrate_planet()` retains the earlier partial boundary for diagnostic
research. `generate_planet()` is the complete prediction boundary, and
`generate_planet_families()` is a compatibility wrapper.

### `diagnostics.py`

Defines immutable structured events and deterministic formatting. Diagnostics
explain state changes; they do not substitute for result/provenance APIs.

### `validation.py`

Compares the completed RSGD/CK-visible prediction against the filtered inorganic
oracle by FormID. It retains atmospheric and final player-facing channels
separately, aggregates all bodies, classifies mismatches/errors, and writes a
deterministic mismatch CSV.

### `cli.py` and `reproduce.py`

Provide the thin command-line boundary for full validation and output paths.

## Missing-Input Semantics

A body without PNDT/biome/effective-RSGD input cannot be passed through
biome-local generation. The architecture must not synthesize a `Planet`, fabricate
assignments, or reinterpret missing input as an empty terrestrial result.
Independently loaded channels, such as atmosphere, may still be reported as known.
Volii Alpha is the v1.0 negative control for this model/input boundary, not
evidence about its actual terrestrial biome allocation or a recovered engine rule.

## Validation and Evidence Boundaries

Creation Kit function addresses and control flow are PROVEN only for the
live-traced CK Galaxy View Apply path. Retail validation independently
corroborates outputs; it does not relabel those addresses as `Starfield.exe`
addresses.

The v1.0 evidence baseline is recorded in `docs/V1-VALIDATION-BASELINE.md`.
Future contradictory evidence is a falsification/regression to preserve and
investigate, not a reason to add an oracle patch or planet-specific exception.

## Out of Scope

- organic resources and flora/fauna generation;
- terrain, cell, vein, or extractor placement;
- arbitrary mod/plugin or future-executable behavior;
- GUI, web server, database, planner, or packaging machinery without an explicit
  brief.
