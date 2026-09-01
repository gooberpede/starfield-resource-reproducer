# Architecture

## Objective

Build a small deterministic reference implementation of Starfield planetary inorganic-resource generation.

The design should make it easy to:

1. compare implementation behavior with recovered runtime behavior;
2. inspect every generation decision;
3. replace provisional rules as new evidence arrives;
4. reuse the validated generation engine later in the outpost-planner project.

## Design Principles

### Domain logic is independent of file format

CSV files are inputs, not the architecture.

The generation engine should operate on typed domain objects rather than pandas rows or raw dictionaries.

### Prediction and validation are separate

The generator predicts resources.

The validator compares those predictions with `planet-all-resources.csv`.

Do not let canonical expected results leak into generation decisions.

### PRNG is an explicit dependency

Exact reproduction requires exact RNG consumption.

All random operations should flow through one small PRNG abstraction that can:

- reproduce Bethesda's MT19937 behavior;
- expose the distinct runtime conversion used for each call site;
- expose draw count/position;
- optionally record diagnostic events.

### Diagnostics are part of the architecture

This project is a reverse-engineering instrument.

A generation run should be representable as both:

- final predicted resources;
- an ordered event trace explaining how that result was produced.

## Proposed Repository Layout

```text
.
├── AGENTS.md
├── README.md
├── reproduce.py
├── pyproject.toml
├── src/
│   └── starfield_resource_reproducer/
│       ├── __init__.py
│       ├── cli.py
│       ├── domain.py
│       ├── load_data.py
│       ├── prng.py
│       ├── generation.py
│       ├── candidates.py
│       ├── diagnostics.py
│       └── validation.py
├── tests/
│   ├── test_prng.py
│   ├── test_oberon.py
│   ├── test_mimas.py
│   ├── test_decaran_vii_b.py
│   ├── test_kreet.py
│   └── test_validation.py
├── data/
│   ├── PlanetResourceGeneration_v5.csv
│   ├── Starfield_IRES_Hierarchy.csv
│   └── planet-all-resources.csv
└── docs/
    ├── ARCHITECTURE.md
    ├── BACKLOG.md
    ├── DOMAIN-RULES.md
    └── IMPLEMENTATION-WORKFLOW.md
```

The exact package name can change, but maintain these responsibility boundaries.

## Core Domain Objects

Suggested conceptual objects:

### `ResourceId`

Stable resource identity, centered on FormID.

Display metadata may include EditorID/name/rarity.

### `ResourceNode`

An IRES node:

```text
form_id
editor_id
name
rarity
children[]
```

### `RSGDResourceEntry`

One ordered resource entry in an RSGD:

```text
index
resource
common_chance
uncommon_chance
rare_chance
exotic_chance
unique_chance
special_chance
everywhere_chance
```

Do not discard original order.

### `EffectiveRSGD`

Resolved RSGD definition used for one planet-biome entry.

Retain provenance for diagnostics:

```text
source = PNDT | BIOM | PNDT+BIOM
```

Runtime generation should resolve the effective source using the recovered precedence rule.

### `Biome`

```text
biome_index
form_id
editor_id
name
chance
pndt_rsgd
biom_rsgd
effective_rsgd
```

### `Planet`

```text
form_id
editor_id
name
system
rscs
biomes[]  # in PNDT BiomeIndex order
```

### `FamilyConfiguration`

Planet-wide cached result for a selected Common root.

Conceptually:

```text
root
level_1
level_2
level_3
level_4
emitted_resources
origin_biome
origin_processing_position
origin_effective_rsgd
```

Preserve structural selections even when a level was not emitted.

### `PlanetGenerationResult`

```text
planet
per_biome_results
  common_assignment  # mechanism, guard, candidates, selected family, origin
everywhere_resources
special_resources
family_cache
predicted_resources
predicted_form_ids
events
final_draw_count
```

This is the complete prediction boundary. It contains no canonical-oracle data.

### `PlanetValidationResult`

```text
planet_form_id
predicted_form_ids
expected_form_ids
missing_form_ids
unexpected_form_ids
exact_match
suspected_cause
first_plausible_divergence
```

Readable resource metadata is retained alongside FormID membership, but identity
and comparison semantics remain FormID-based.

## Modules

### `load_data.py`

Responsibilities:

- parse canonical CSV inputs;
- validate schema;
- convert FormIDs consistently;
- group flat PNDT/RSGD rows into domain objects;
- load IRES graph;
- load runtime oracle separately.

No generation decisions.

### `prng.py`

Responsibilities:

- exact 32-bit MT19937 seeding;
- shared game-compatible probability conversion;
- rejection-sampled integer bounded selection for biome shuffle;
- float32-scaled and truncated index selection for descendants;
- draw accounting;
- optional event logging.

The two bounded-choice APIs are intentionally separate:

```text
MT19937 raw uint32
        |
        +--> next_bounded_integer
        |       rejection sampling -> modulo -> biome shuffle
        |
        +--> probability float32
                +--> inclusion rolls
                +--> next_scaled_index -> scale/truncate -> descendants
```

Runtime traces PROVE that these call sites use different mechanisms. A rejected
integer-bounded attempt consumes an additional raw word; a normal descendant
scaled choice consumes exactly one. Do not collapse the APIs into a generic
bounded-index helper without new runtime evidence.

Do not assume Python's `random.Random` is compatible until verified against known trace values.

### `candidates.py`

Responsibilities:

- rarity filtering;
- Common root candidate construction;
- descendant candidate construction from:
  - children(root);
  - children(current structural node);
- deterministic de-duplication preserving runtime order.

Keep structural graph logic out of orchestration code.

### `generation.py`

Responsibilities:

- prepopulate ordered atmospheric occurrences before RNG-backed work;
- run the category-6 / Everywhere pre-pass across every biome/effective RSGD,
  accepting category-6 entries in authored order without consulting DNAM chance
  fields or consuming RNG;
- construct/copy biome list in PNDT order;
- deterministic shuffle;
- iterate shuffled biomes;
- resolve effective RSGD;
- run the recovered ordered cumulative Special selector and immediately record
  any selected Special in shared state before evaluating either Common guard;
- then run the same selector shape for Common only when neither guard fires;
- before Common selection, enforce the five-distinct-tree guard from
  `FUN_1415DCFB0`; a guarded invocation consumes no Common-selector RNG draw;
- after the five-tree guard and before Common selection, enforce the shared
  eight-resource guard recovered from `FUN_1415DCFB0`; at capacity the selector
  is bypassed and consumes no Common-selector RNG;
- after either guard, scan stored effective-RSGD Common roots and assign an
  existing cached family from the preferred matching pool or, when no roots
  match, from the complete cache; the semantically distinct float32-scaled
  fallback choice consumes one draw even at bound one;
- retain each cached family's generation-origin biome/RSGD context and attach an
  explicit assignment mechanism to every biome result;
- retain provenance-specific occurrences independently of resource identity;
- enforce one shared eight-unique-FormID capacity across ATMO, Everywhere,
  Special, Common, and descendants;
- preserve an explicitly partial orchestration result for Brief 03 diagnostics;
- generate immutable Common-family configurations;
- process descendant levels in rarity order with exact draw accounting;
- consume one raw MT word when a descendant level has no candidates while
  retaining the structural node;
- maintain the planet-scope FormID-keyed family cache, reusing cached results
  without invoking descendant generation or consuming descendant RNG;
- expose atmospheric, RSGD/CK-visible, and final player-facing resource channels.

`orchestrate_planet()` stops after Common-root selection. The separate
`generate_planet()` pipeline uses the same outer control flow but runs a new
family immediately after its root is selected, before the shared RNG advances to
the next biome. `generate_planet_families()` remains a compatibility wrapper.
The result is a complete prediction, not a canonical validation result. Its
central invariant is that occurrence count is not slot count: two mechanisms may
contribute the same FormID while only one unique identity occupies shared state.
The Common-tree count is independently the number of FormID-keyed family-cache
entries; it is neither biome count nor shared resource-slot count.

The shared state has two deliberately separate roles. `PlanetResourceState.record()`
implements insertion and provenance-aware de-duplication. The main Common path
also checks `at_capacity` before invoking the selector. Consequently an already
occupied prospective root cannot bypass the control-flow guard merely because a
duplicate occurrence would require no new slot. This pre-Common rule does not
change the earlier Everywhere occurrence ordering or Special mechanics.

**PROVEN LIVE:** within a biome invocation, selected Special insertion precedes
the five-tree and shared-eight Common guards. A new Special FormID can raise the
shared count from seven to eight and force fallback in that same biome. An
already-occupied Special records another occurrence without changing the count.

The guarded fallback records duplicate biome-context occurrences for the cached
root and emitted descendants without occupying new slots. It does not mutate the
cache or run descendant generation. Everywhere and Special assignments remain
independent channels.

`PlanetGenerationResult.biome_resource_views()` associates occurrence context by
PNDT biome index. BIOM FormID remains provenance, but is not assumed unique among
multiple PNDT biome entries on one planet.

No CSV access.

### `diagnostics.py`

Responsibilities:

Represent significant orchestration events as immutable named records with an
optional exact `RngDraw`. Current events include:

```text
PRNG_SEEDED
BIOME_LIST_INITIAL
BIOME_SWAP
BIOME_LIST_SHUFFLED
BIOME_BEGIN
RSGD_RESOLVED
EVERYWHERE_ADDED
SPECIAL_SELECTED
COMMON_CANDIDATE
COMMON_ROLL
COMMON_SELECTED
BIOME_END
PLANET_END
```

Prefer structured events that the deterministic timeline formatter can render
rather than ad-hoc print statements throughout generation code. Diagnostics-only
counterfactual draws use an independent RNG and are explicitly labeled
`COUNTERFACTUAL / NOT RUNTIME-PROVEN`.

Descendant, cache, and emission events are added only with their corresponding
generation stages. Brief 04 adds family begin/end, root emission, per-level
candidate/inclusion/selection/emission, and cache-hit events.

Brief 07B also records atmospheric prepopulation, Everywhere pre-pass boundaries,
provenance occurrences, new-slot occupancy, already-occupied identities, and
capacity rejection. Occurrences remain first-class result data; diagnostics explain
state transitions rather than serving as the only provenance API.

Brief 08C adds a distinct `COMMON_RESOURCE_CAPACITY_REACHED` event for the
pre-Common shared-eight guard. It records the occupied count, capacity, unchanged
draw counts, and `rng_consumed=false`, distinguishing selector suppression from a
later insertion rejection.

Brief 08D adds guarded-fallback begin, candidate, roll, and assignment events.
They distinguish the guard reason, matched versus general pools, fallback RNG,
selected cached family, family origin, and target biome. Fallback is never
reported as `COMMON_SELECTED`, which remains specific to the normal selector.

### `validation.py`

Responsibilities:

- compare the independent RSGD/CK-visible channel with an inorganic canonical body;
- retain atmospheric and final player-facing union channels without treating
  ATMO-only oracle omissions as generation failures;
- compare expected/predicted resource membership by FormID;
- derive the generation/oracle-inorganic intersection and report coverage gaps;
- retain exact, missing-only, unexpected-only, mixed, and generation-error status;
- classify family-, biome-, RSGD-, override-, cache-, and RSCS-aware dimensions;
- aggregate the complete corpus without aborting on one planet error;
- export deterministic machine-readable mismatch rows;
- identify an evidence-qualified first plausible mismatch region.

`validate_all_planets()` owns batch comparison, not generation. The oracle is
supplied only after each independent prediction is complete. Final-set exactness
is reported separately from trace exactness because the corpus oracle does not
contain per-operation RNG traces.

Validation must never alter generator behavior.

### `cli.py` / `reproduce.py`

Thin orchestration layer.

Initial commands:

```text
--planet <name|editorid|formid>
--all
--diagnostic
--mismatches <path>
```

Avoid building a complex CLI framework in v0.1.

## Algorithm Boundary

The reproducer models **planetary resource membership/allocation**, not downstream surface placement.

Do not implement:

- vein geometry;
- cell-level placement;
- extractor placement;
- biome terrain generation;
- flora/fauna generation.

`Cell` generation probabilities from RSGD are outside current scope unless future evidence requires them.

## Canonical Oracle Boundary

`planet-all-resources.csv` contains both inorganic and organic resources.

For current validation:

```text
ResourceCategory == "Inorganic"
```

Only those rows belong to reproducer expected output.

Organic rows are retained in the source dataset but out of scope.

## Error Handling

Fail loudly for malformed canonical static input.

Examples:

- duplicate `BiomeIndex` within a planet;
- conflicting RSCS for one planet;
- missing referenced IRES node;
- duplicate RSGD resource index;
- ambiguous effective RSGD construction.

Do not silently "repair" extraction data.

## Future Integration

Once validated, the core generation package may later be consumed by the outpost planner.

That future integration should depend on the domain API, not on CLI or CSV internals.

The standalone reproducer should remain available as a regression oracle even after integration.
