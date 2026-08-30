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
```

Preserve structural selections even when a level was not emitted.

### `PlanetGenerationResult`

```text
planet
per_biome_results
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
- game-compatible integer/float conversion;
- deterministic bounded index selection;
- draw accounting;
- optional event logging.

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

- construct/copy biome list in PNDT order;
- deterministic shuffle;
- Everywhere provisional handling;
- iterate shuffled biomes;
- resolve effective RSGD;
- Special pass;
- Common weighted selection;
- preserve an explicitly partial orchestration result for Brief 03 diagnostics;
- generate immutable Common-family configurations;
- process descendant levels in rarity order with exact draw accounting;
- consume one raw MT word when a descendant level has no candidates while
  retaining the structural node;
- maintain the planet-scope FormID-keyed family cache, reusing cached results
  without invoking descendant generation or consuming descendant RNG;
- assemble complete planet output from Everywhere, Special, and emitted families.

`orchestrate_planet()` stops after Common-root selection. The separate
`generate_planet()` pipeline uses the same outer control flow but runs a new
family immediately after its root is selected, before the shared RNG advances to
the next biome. `generate_planet_families()` remains a compatibility wrapper.
The result is a complete prediction, not a canonical validation result.

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

### `validation.py`

Responsibilities:

- compare an independent generation result with an inorganic canonical body;
- compare expected/predicted resource membership by FormID;
- produce exact-match status;
- report missing/unexpected FormIDs;
- retain readable metadata;
- identify an evidence-qualified first plausible mismatch region.

Full-dataset aggregation and mismatch-file output remain Brief 06 work.

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
