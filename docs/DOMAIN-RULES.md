# Domain Rules

## Purpose

This document records the current recovered domain model for Starfield planetary inorganic-resource generation.

Use explicit evidence states:

- **PROVEN** — directly observed in live execution/static authoritative data or independently verified runtime output.
- **STRONG** — strongly supported and suitable as the current general model, but universality has not been exhaustively demonstrated.
- **PROVISIONAL** — implementation assumption to be tested against the canonical oracle.

Do not erase these distinctions.

## Identity and Data Sources

### Planet identity

Use `PlanetFormID` as the primary stable body identity.

### Resource identity

Use `ResourceFormID` as primary resource identity.

EditorID and name are diagnostic/display metadata.

## Rarity / Category Enum

**PROVEN**

```text
0 Common
1 Uncommon
2 Rare
3 Exotic
4 Unique
5 Special
6 Everywhere
```

Authoritative IRES examples:

```text
Helium-3 -> Special
Water    -> Everywhere
```

## Seed and PRNG

### RSCS seeds MT19937

**PROVEN**

For a nonzero planetary Resource Creation Seed:

```text
PNDT.RSCS
    ->
unsigned 32-bit MT19937 seed
```

The same evolving PRNG state is used through subsequent generation.

Exact API/conversion behavior must be validated in `prng.py`; statistical equivalence is insufficient.

### Raw output and draw accounting

**PROVEN for the Mimas and Kreet live anchors; STRONG as the general interface**

The compatibility layer uses the classic 32-bit MT19937 state initialization
and tempering sequence. One diagnostic draw means one extracted raw 32-bit
MT19937 output, regardless of which public conversion consumes it.

Python's `random.Random` API is not used because its integer seeding and helper
conversion/consumption behavior do not reproduce this observable interface.

### Probability float conversion

**STRONG**

The Mimas values are reproduced, to their recorded nine decimal places, by
binary32 arithmetic equivalent to:

```text
float32(float32(raw_uint32) * float32(2^-32))
    * float32(0.99999)
```

with the final multiplication rounded to binary32. This reproduces the known
Common, Uncommon, Rare, and Exotic rolls without weakening trace tolerances.
The available trace does not distinguish every algebraically equivalent
binary32 construction, so the exact source-level expression is not labeled
PROVEN.

### Bounded index conversion

**STRONG**

The current compatible operation consumes one raw output and returns:

```text
raw_uint32 % upper_bound
```

It reproduces both observed Kreet swap choices. A bound of one still consumes a
raw output and returns zero; that consumption behavior is **PROVEN** by Mimas.
Kreet alone does not exclude every bounded construction that produces the same
two choices, so modulo conversion remains STRONG rather than PROVEN.

## Biome List Construction

### Initial list order

**PROVEN for live Kreet case; STRONG as general rule**

The generator constructs the working biome list in PNDT `BiomeIndex` order.

Kreet observed:

```text
0 Frozen Volcanic
1 Mountains
2 Volcanic
```

The runtime working array began in exactly that order.

### Deterministic shuffle

**PROVEN**

The working biome list is shuffled using the RSCS-seeded PRNG before per-biome resource generation.

Kreet observed:

```text
initial:  [0, 1, 2]
shuffled: [2, 0, 1]
```

The generation orchestrator reproduces the observed swaps as target/selected
index pairs `(1, 0)` and `(2, 0)`, consuming the first two raw outputs.

### Biome shuffle RNG consumption

**STRONG**

The recovered loop visits ascending target positions:

```text
target = 1 .. N - 1
bound  = target + 1
selected = next_index(bound)
swap(target, selected)
```

It therefore consumes `N - 1` raw outputs:

```text
N = 1 -> 0 shuffle draws
N = 2 -> 1 shuffle draw, bound 2
N = 3 -> 2 shuffle draws, bounds 2 then 3
```

Kreet directly proves the `N = 3` swaps. The generalized loop, including the
zero-draw `N = 1` case, matches the recovered control flow but has not been
live-traced for every biome count, so it remains STRONG rather than PROVEN.

### Sequential processing

**PROVEN**

The shuffled array is processed sequentially.

Kreet per-biome generator order:

```text
2 Volcanic
0 Frozen Volcanic
1 Mountains
```

## Effective RSGD Resolution

### PNDT overrides BIOM

**PROVEN in Decaran VII-b and independently in ordinary Kreet overrides**

```text
if PNDT biome ResourceGeneration is non-null:
    use PNDT RSGD
else:
    use BIOM.RNAM
```

The BIOM RSGD is not supplemented after a PNDT override in observed cases.

Do not merge the two.

## RSGD Entry Order

**PROVEN**

RSGD resource-array order is semantically significant.

Preserve `RSGDResourceIndex`.

## Everywhere / Water

### Classification

**PROVEN**

Water is category 6 / Everywhere.

### Per-biome generator behavior

**PROVEN**

In the observed `FUN_1415DCFB0` per-biome generator:

- there is a Special/category-5 selector pass;
- there is a Common/category-0 selector pass;
- there is no category-6 weighted-selector pass.

Oberon showed Water already present in working result state and only read, not written, during the traced per-biome routine.

### Upstream insertion

**PROVEN architecturally, mechanism unresolved**

Everywhere resources are populated earlier/upstream.

Exact upstream routine and all edge semantics are not yet reconstructed.

### Reproducer v0.1 handling

**PROVISIONAL**

Model Water/Everywhere from static RSGD/category data sufficiently to reproduce observed planet sets.

If the full canonical comparison shows mismatches, trace/recover the exact upstream path rather than hard-coding planet exceptions.

## Special / Helium-3

### Classification

**PROVEN**

Helium-3 is category 5 / Special.

### Selection

**PROVEN**

The per-biome generator performs a category-5 weighted selector pass.

Decaran VII-b directly demonstrated Helium-3 matching category 5.

### Empty Special selector consumption

**STRONG**

The recovered category-selector call obtains one probability roll before it
walks the ordered RSGD entries. Consequently the Special pass consumes one raw
draw even when the effective RSGD contains zero Special entries, then returns no
selection. This accounts for Mimas raw draw 1 without a dummy draw or planet
special case; its Common roll remains raw draw 2 at `0.5611079931259155`.

Decaran VII-b uses the same call shape: Special/Helium-3 consumes draw 1 and
Common/Uranium consumes draw 2.

## Common / Family Root Selection

### Eligibility

**PROVEN**

Only category-0/Common RSGD entries participate in the Common-root selector.

Water/Everywhere and Helium-3/Special do not compete as Common families.

### Weighted selection

**PROVEN**

Root selection is cumulative weighted selection in RSGD array order.

### No normalization

**PROVEN**

Do not normalize stored weights before selection.

Treat cumulative thresholds using the values as stored.

## Root Emission

**PROVEN**

A newly generated Common-family root is emitted unconditionally.

This also agrees with the large canonical empirical invariant that descendants were never observed without their family root.

## IRES Resource Graph

### Authoritative graph source

**PROVEN**

Resource hierarchy/topology is stored in IRES records:

```text
IRES
├── rarity
└── Child Resources
```

Use `Starfield_IRES_Hierarchy.csv`.

### Serialized graph vs effective candidate path

**PROVEN**

At descendant rarity levels, the runtime candidate builder searches structurally valid children including:

```text
children(root)
+
children(current structural node)
```

filtered for the requested rarity.

This produces effective branching that may differ from a simple parent-chain interpretation.

## Descendant Levels

**PROVEN**

After Common/root generation, levels are processed:

```text
1 Uncommon
2 Rare
3 Exotic
4 Unique
```

## Structural Selection vs Emission

**PROVEN**

At a descendant level:

1. build structurally valid candidate list;
2. select a structural candidate;
3. evaluate inclusion/emission;
4. continue traversal through the selected structural candidate whether or not it was emitted.

Therefore a deeper resource can be emitted while intermediate structural nodes are absent from final output.

Mimas live example:

```text
Nickel       emitted root
Cobalt       structural, omitted
Platinum     structural, omitted
Palladium    structural, emitted
Tasine       structural, omitted
```

## Descendant RNG Consumption

### Inclusion and candidate choice

**PROVEN for Mimas descendant path**

Each descendant level with a valid candidate consumed:

```text
1 inclusion draw
1 candidate-index draw
```

The candidate-index draw occurred even when only one candidate existed.

Exact behavior for zero candidates and other edge branches remains mismatch-driven work.

## Family Configuration Cache

### Planet-wide reuse

**PROVEN in recovered control flow/live analysis; not exercised by Kreet**

If a later biome selects a Common root already generated earlier on the same planet, the existing family descendant configuration is reused instead of being independently rerolled.

Consequences:

- shuffled biome order can determine which biome first establishes a family configuration;
- all biomes using that root share the same descendant pattern for that generation run.

Exact PRNG consumption on cache-hit branches should be verified if canonical mismatches expose it.

## Unique Resources

### Data-driven endpoints

**PROVEN for Vytinium mechanism; STRONG for analogous unique resources**

Vytinium is not generated by a hard-coded Vytinium branch.

Decaran VII-b uses a PNDT RSGD override that:

- forces the Uranium root;
- supplies descendant inclusion probabilities;
- gives Unique a 100% chance.

Normal IRES structural traversal reaches Vytinium.

Apply the same data-driven architecture to other unique-resource cases unless evidence says otherwise.

Do not hard-code:

```text
if planet == Decaran VII-b: add Vytinium
```

## Worked Multi-Biome Example: Kreet

**PROVEN**

Initial PNDT order:

```text
0 Frozen Volcanic
1 Mountains
2 Volcanic
```

Observed shuffled order:

```text
2 Volcanic
0 Frozen Volcanic
1 Mountains
```

Observed family outputs:

```text
Volcanic        -> Lead + Silver
Frozen Volcanic -> Argon + Neon
Mountains       -> Iron + Alkanes
```

Water is supplied upstream/Everywhere.

Final observed inorganic set:

```text
Water
Lead
Silver
Argon
Neon
Iron
Alkanes
```

## Canonical Validation Oracle

Use:

```text
planet-all-resources.csv
```

Filter:

```text
ResourceCategory == "Inorganic"
```

The supplied file contains 7,663 total resource rows across 1,445 bodies and includes both inorganic and organic resources.

`Starfield_InorganicResources_Canonical.csv` is deprecated and must not be used as the oracle.

## Known Unresolved / Mismatch-Driven Rules

Do not block v0.1 on these unless necessary:

- exact upstream Everywhere insertion routine;
- RSCS = 0 fallback path;
- zero-candidate RNG consumption;
- cache-hit RNG consumption details;
- five-family limit;
- eight-resource-slot limit;
- duplicate suppression side effects;
- fallback/additional RSGD iteration;
- unusual Special/Everywhere slot interactions.

The first full canonical run should determine which of these actually matters.
