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

### Distinct bounded-choice mechanisms

**PROVEN**

Starfield uses two different mechanisms at the recovered call sites. They are
not interchangeable.

Biome shuffle uses an integer bounded helper. For current 32-bit bounds it
repeats:

```text
raw = next_uint32()
quotient_threshold = UINT32_MAX // upper_bound
quotient_random = raw // upper_bound
accept only when quotient_random < quotient_threshold
result = accepted_raw % upper_bound
```

Every rejected and accepted attempt consumes one raw MT word, so one shuffle
choice can consume multiple words. A bound of one still enters the helper and
consumes RNG rather than short-circuiting.

Descendant candidate selection instead consumes one raw word, applies the
recovered binary32 probability conversion, multiplies by the binary32 candidate
count, rounds that product to binary32, and truncates it:

```text
probability = float32(float32(raw) * float32(2^-32))
probability = float32(probability * float32(0.99999))
scaled = float32(probability * float32(candidate_count))
index = trunc(scaled)
```

Algorab I draw 18 (`1826241303`, bound 2) produces probability
`0.4252006709575653`, scaled value `0.8504013419151306`, and index 0. Modulo
would produce 1. The discriminating result and scaled/truncation instruction
path are PROVEN; the exact `0.99999` formulation remains STRONG where nearby
binary32-equivalent expressions are not distinguished by the trace.

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
selected = next_bounded_integer(bound)
swap(target, selected)
```

It performs `N - 1` bounded choices. Each choice normally consumes one raw
output but may consume more if the integer helper rejects an attempt:

```text
N = 1 -> 0 bounded choices, 0 raw draws
N = 2 -> 1 bounded choice, bound 2, at least 1 raw draw
N = 3 -> 2 bounded choices, bounds 2 then 3, at least 2 raw draws
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

### Pre-main-generation handling

**PROVEN LIVE in the observed Creation Kit Galaxy View Apply path**

Before any shuffled per-biome generator call, `FUN_141548920` visits every
biome/effective-RSGD work object and scans its ordinary resource-entry array in
stable authored order. Entries whose referenced IRES category is 6 / Everywhere
are emitted into shared planet resource state without consulting DNAM Everywhere
chance, substituting Common chance, or consuming RNG. The traversal does not stop
globally after the first Everywhere resource.

This proves privileged pre-main handling and biome-work association. It does not
prove that the resource is physically generated in every biome. The reproducer
therefore retains a distinct Everywhere pre-pass and does not invent stronger
physical claims.

**COUNTERFACTUAL / FALSIFIED:** a one-entry effective RSGD is not generically
auto-selected. Kreet's one-entry Common RSGDs still use the ordinary category-0
weighted selector and consume its normal RNG draw.

## Atmospheric Resources

### Prepopulation and provenance

**PROVEN in the observed CK path**

Effective inorganic atmospheric resources are prepopulated before Everywhere and
before shuffled main generation. Atmospheric insertion consumes no RNG and is not
an RSGD result. Ordered records from `Starfield_PlanetAtmosphericResources.tsv`
retain their defining ATMO identity, source file, and inheritance depth.

The same IRES FormID may occur through ATMO and an RSGD mechanism. These are two
provenance occurrences, not two resource identities.

## Special / Helium-3

### Classification

**PROVEN**

Helium-3 is category 5 / Special.

### Selection

**PROVEN**

The per-biome generator performs a category-5 weighted selector pass.

Decaran VII-b directly demonstrated Helium-3 matching category 5.

### Shared-state ordering before Common guards

**PROVEN LIVE**

Within one biome invocation, a selected Special resource is written and recorded
in shared planet resource state before the five-tree and shared-eight Common
guards are evaluated. Callisto directly showed Helium-3 appended to shared state
before Common/Iron selection. Therefore a new Special identity can raise the
shared count from seven to eight and force Common guard fallback for that biome.
A duplicate Special FormID records its occurrence without occupying a new slot,
so it does not independently trigger the shared-eight guard.

### Category-generic selector and draw consumption

**PROVEN**

The recovered category-selector call obtains one probability roll before it
walks the ordered RSGD entries. Consequently the Special pass consumes one raw
draw even when the effective RSGD contains zero Special entries, then returns no
selection. This accounts for Mimas raw draw 1 without a dummy draw or planet
special case; its Common roll remains raw draw 2 at `0.5611079931259155`.

The recovered selector consumes one MT word, converts it to the binary32
probability, scans ordered RSGD entries matching the requested category, adds
`chance(category) / 100` cumulatively without normalization, and returns the first
entry for which `roll < cumulative`. It consumes exactly one word for zero, one,
or many eligible entries, including a single 100-percent candidate.

Decaran VII-b uses this call shape: Special/Helium-3 consumes draw 1 and
Common/Uranium consumes draw 2. Callisto independently demonstrates a 100-percent
Special candidate still consuming the first draw before Common consumes the next.

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

### Five distinct Common tree limit

**PROVEN STATIC/LIVE in the Creation Kit Galaxy View Apply path**

`FUN_1415DCFB0` contains a hard-coded `cmp ...,5` guard on the established
Common tree/family state. When the count is at least five, the branch bypasses
the Common/category-0 selector, so its usual MT19937 probability draw is not
consumed for that invocation. This is a pre-selector guard; selecting a sixth
root and discarding it afterward would produce the wrong RNG sequence.

**PROVEN LIVE - Bara VII-d:** the observed state progressed
`0, 1, 1, 2, 2, 3, 4, 5`. At five, the `jae` branch was taken before the Common
selector. Repeated values support that the state counts distinct established
tree configurations rather than biome calls or selector attempts. A repeated
root reuses its cached configuration and does not occupy another tree slot.

The five-tree guard and the separate shared eight-resource guard are distinct
mechanisms.

### Pre-Common shared resource-capacity guard

**PROVEN STATIC/LIVE in the Creation Kit Galaxy View Apply path**

In `FUN_1415DCFB0`, the shared eight-resource guard is evaluated after the
five-Common-tree guard and before the Common/category-0 selector. When the shared
count is at least eight, the branch bypasses the normal selector entirely. No
Common weighted-selector probability draw is consumed and no new root identity
is selected by that path. The earlier interpretation that this ended biome-local
Common assignment is superseded by the guarded fallback rule below.

**PROVEN LIVE - Indum IV-d:** the observed invocation had Common-tree count `2`
and shared-resource count `8`. The five-tree branch was inactive, the shared-eight
branch was taken, and the Common selector was skipped.

This is a control-flow constraint as well as an insertion constraint. A
prospective Common root already present through ATMO cannot exploit duplicate
de-duplication semantics because selection never occurs. The rule is specific to
the recovered main Common path; it does not alter the upstream Everywhere
occurrence ordering or establish new Special behavior.

### Guarded biome-family fallback assignment

**PROVEN LIVE in the Creation Kit Galaxy View Apply path**

After either the five-tree or shared-eight guard suppresses the normal Common
selector, `FUN_1415DCFB0` can assign an already-generated planet-scope family
configuration to the current biome. `FUN_14154C710` scans stored effective-RSGD
entries in order. Common roots matching cached-family roots form a preferred
pool. If Common roots exist but none match, all generated families form the pool.
If the effective RSGD contains no Common roots, no Common family is assigned.

Fallback selection uses `FUN_14015B4A0`, whose probability thunk
`FUN_1401190CD -> FUN_140924800` uses the recovered binary32 probability. The
index is the truncation of `float32(probability * float32(candidate_count))`.
A one-element pool still consumes one RNG draw. The chosen family is not
regenerated: descendant selection/inclusion consumes no RNG, the cache is not
changed, and its existing root plus emitted descendants are recorded as
biome-context occurrences without occupying new resource slots.

Family configuration origin and current assignment mechanism are distinct.
Biome results identify new generation, normal cache reuse, matched guard
fallback, general guard fallback, or no assignment, while the cached family
retains the biome processing context in which that exact configuration originated.
Everywhere and Special assignments remain independent of this Common-family path.

## Shared Planet Resource State

### Capacity identity versus occurrence provenance

**PROVEN:** recovered code guards a shared state at eight resource IDs.

**STRONG / engine-shaped capacity model:** capacity is modeled as eight unique
IRES FormIDs across ATMO, Everywhere, Special, Common roots, and emitted
descendants. A repeated FormID records another provenance occurrence but does not
consume a second slot. Exact duplicate behavior at every insertion site remains
OPEN, so this broader collision model is not labeled universally proven.

There is no Water-, Chlorine-, atmosphere-, or vapor-specific capacity exception.
When the shared state is full, the descendant helper returns the current structural
node and consumes no RNG. Occurrence count and occupied-slot count are deliberately
separate result fields.

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

Candidate order is direct children of the root followed by direct children of
the current structural node, preserving canonical IRES child order. Duplicate
FormIDs are removed by retaining their first occurrence. This is required by the
Mimas L1 observation: when root and current are both Nickel, Cobalt remains one
candidate and the bounded selection uses `upper_bound = 1`.

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
2. consume and evaluate the inclusion roll;
3. consume the candidate-index roll and select a structural candidate;
4. continue traversal through the selected structural candidate whether or not it was emitted.

**Correction recorded in Brief 04:** earlier wording listed structural selection
before inclusion. The recovered Mimas raw sequence proves the runtime call order
is inclusion first, then candidate index. This changes no prior conclusion about
the independence of structural traversal and emission.

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

Other edge branches remain mismatch-driven work.

### Zero-candidate levels

**PROVEN by the Algorab I live trace**

When the filtered candidate list is empty, the descendant call:

```text
consumes exactly one raw MT19937 word
selects no candidate
retains the current structural node
```

The trace does not establish whether the engine describes this as an inclusion
operation, an index-related operation, or another helper call. Production uses
a raw-word advance and diagnostics deliberately do not assign stronger semantics.

## Family Configuration Cache

### Planet-wide reuse

**PROVEN in recovered control flow/live analysis; not exercised by Kreet**

If a later biome selects a Common root already generated earlier on the same planet, the existing family descendant configuration is reused instead of being independently rerolled.

Consequences:

- shuffled biome order can determine which biome first establishes a family configuration;
- all biomes using that root share the same descendant pattern for that generation run.

**PROVEN by the Algorab I repeated-Uranium live trace:** the second Uranium
selection made zero calls to `FUN_14157F120`. The cached configuration is reused,
descendant generation is bypassed entirely, and no descendant RNG words are
consumed on the cache hit.

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

### Brief 05B resolution

**PROVEN zero-candidate consumption; exact worked-case result**

Lead's empty Exotic and Unique levels each consume one raw word, moving Argon's
Neon inclusion to draw 17 (`357224398`) and roll `0.08317194879055023`. The roll
passes its `0.15` threshold, so the production model emits Neon and Kreet matches
the canonical inorganic set exactly. The final production draw count is 30.

## Algorab I Lead Structural Resolution

**PROVEN and reproduced internally**

The serialized Lead edges place Silver before Tungsten. Algorab's live bounded
helper returned index 0 at draw 18, selecting Silver without any candidate
reordering. The resulting path is Lead -> Silver -> Mercury -> empty Exotic ->
empty Unique, matching the observed structural shape and final draw 22.

Production now uses the descendant float32-scaled path for that call, producing
the live-shaped `advance, advance, empty, empty` sequence and final draw count
22. Its canonical inorganic set remains exactly Lead, Uranium, and Iridium.

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

- RSCS = 0 fallback path;
- exact same-FormID duplicate behavior at every insertion site;
- fallback/additional RSGD iteration;
- exact SurveyAggregator contract of `planet-all-resources.csv`.

The first full canonical run should determine which of these actually matters.
