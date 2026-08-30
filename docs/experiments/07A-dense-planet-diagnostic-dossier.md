# Dense-Planet Diagnostic Dossier

## 1. Objective

Brief 07A reconstructs the unchanged production timeline for Fermi VII-a, Maal
VIII, and Fermi III. It annotates completed predictions with canonical membership
only after generation, records visible unique resource insertions and completed
reproducer family-cache entries, and evaluates diagnostics-only cutoffs.

No limit, stopping condition, cache change, or insertion suppression is applied.
The complete 382-event dump is in
`validation/07A-dense-planet-events.csv`.

Terminology is deliberately narrow:

- **resource insertion count** is the number of unique FormIDs visibly added by
  the reproducer; it is not a proven runtime slot count;
- **generated-family count** is the number of completed distinct Common-family
  configurations in the reproducer cache; it is not a proven runtime capacity;
- **COUNTERFACTUAL** cutoffs filter recorded insertions after generation and do
  not alter or replay production.

## 2. Evidence status / known limits

**PROVEN:** the three predictions, event order, RNG draws, selections, emissions,
and canonical FormID memberships below are deterministic consequences of the
current reproducer and supplied canonical data.

**PROVEN:** each first divergent resource is absent from the runtime-derived
canonical oracle.

**STRONG:** the broader Brief 06 corpus shape remains consistent with a
planet-wide capacity or insertion-order boundary.

**PROVISIONAL:** a five-family or eight-slot runtime mechanism remains possible,
but no checked-in Ghidra fragment establishes either number or identifies the
state variable being counted.

## 3. Fermi VII-a dossier

### Static inputs and final sets

```text
PlanetFormID: 0005DE3A
RSCS:         4131893178
Initial:      0 Plateau, 1 Frozen Hills, 2 Hills, 3 Sandy Desert
Runtime:      3 Sandy Desert, 2 Hills, 0 Plateau, 1 Frozen Hills
Draws:        34
```

All effective definitions are BIOM RNAM inputs:

| Runtime pos. | BiomeIndex | Biome | Effective RSGD |
| ---: | ---: | --- | --- |
| 0 | 3 | Sandy Desert | DesertSandDefaultRes |
| 1 | 2 | Hills | HillsNoLifeDefaultRes |
| 2 | 0 | Plateau | CanyonsDefaultRes |
| 3 | 1 | Frozen Hills | FrozenBarrenDefaultRes02 |

Predicted (9): Water `000083EC`, Uranium `000057EB`, Nickel `000057CB`,
Cobalt `000057CE`, Platinum `000057CC`, Palladium `000057CD`, Copper
`000057CF`, Fluorine `000057D0`, Ionic Liquids `000057D4`.

Canonical (8): Water `000083EC`, Uranium `000057EB`, Nickel `000057CB`,
Cobalt `000057CE`, Platinum `000057CC`, Palladium `000057CD`, Copper
`000057CF`, Fluorine `000057D0`.

Missing: none. Unexpected: Ionic Liquids `000057D4`.

### Family ledger

An asterisk marks emission. Paths include selected-but-omitted structural nodes.

| Seq | Runtime biome | Root | New/cache | Structural path | Emitted descendants | Families after |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | 0 Sandy Desert | Uranium | new | Uranium* -> Iridium -> Vanadium -> Plutonium -> Vytinium | none | 1 |
| 2 | 1 Hills | Nickel | new | Nickel* -> Cobalt* -> Platinum* -> Palladium* -> Tasine | Cobalt, Platinum, Palladium | 2 |
| 3 | 2 Plateau | Copper | new | Copper* -> Fluorine* -> Tetrafluorides -> Ionic Liquids* -> empty | Fluorine, Ionic Liquids | 3 |
| 4 | 3 Frozen Hills | Copper | cache hit | reused configuration above; no descendant RNG | Fluorine, Ionic Liquids reused | 3 |

The cache hit happens after the divergent Ionic Liquids insertion. It cannot have
caused that first divergence.

### Resource insertion ledger

| Seq | Runtime biome | Family | Resource | Rarity/source | Cache? | Count after | Canonical? |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 1 | upstream | - | Water | Everywhere | no | 1 | yes |
| 2 | 0 Sandy Desert | Uranium | Uranium | Common root | no | 2 | yes |
| 3 | 1 Hills | Nickel | Nickel | Common root | no | 3 | yes |
| 4 | 1 Hills | Nickel | Cobalt | Uncommon descendant | no | 4 | yes |
| 5 | 1 Hills | Nickel | Platinum | Rare descendant | no | 5 | yes |
| 6 | 1 Hills | Nickel | Palladium | Exotic descendant | no | 6 | yes |
| 7 | 2 Plateau | Copper | Copper | Common root | no | 7 | yes |
| 8 | 2 Plateau | Copper | Fluorine | Uncommon descendant | no | 8 | yes |
| 9 | 2 Plateau | Copper | Ionic Liquids | Exotic descendant | no | 9 | **no** |

### First divergence

**PROVEN:** event 93 / insertion 9 emits unexpected Exotic Ionic Liquids. The
causal RNG events immediately before it are draw 30 inclusion
(`raw=510386694`, pass against 0.15) and draw 31 candidate selection
(`raw=4097668562`, one candidate).

State immediately before insertion:

```text
visible resource insertions:             8
completed family-cache entries:           2
new Common roots already emitted:         3
cache hits so far:                        0
runtime biome position / BiomeIndex:      2 / 0
effective RSGD:                           CanyonsDefaultRes
root / descendant level:                 Copper / Exotic
```

## 4. Maal VIII dossier

### Static inputs and final sets

```text
PlanetFormID: 0005DE6F
RSCS:         202360258
Initial:      0 Mountains, 1 Frozen Plains, 2 Sandy Desert, 3 Plateau
Runtime:      1 Frozen Plains, 3 Plateau, 2 Sandy Desert, 0 Mountains
Draws:        42
```

| Runtime pos. | BiomeIndex | Biome | Effective RSGD |
| ---: | ---: | --- | --- |
| 0 | 1 | Frozen Plains | FrozenBarrenDefaultRes03 |
| 1 | 3 | Plateau | CanyonsDefaultRes |
| 2 | 2 | Sandy Desert | DesertSandDefaultRes |
| 3 | 0 | Mountains | MountainNoLifeDefaultRes |

All four definitions are BIOM RNAM inputs.

Predicted (8): Water `000083EC`, Nickel `000057CB`, Copper `000057CF`,
Uranium `000057EB`, Iridium `000057EC`, Vanadium `000057ED`, Iron
`000057C7`, Alkanes `000057C9`.

Canonical (7): Water `000083EC`, Nickel `000057CB`, Copper `000057CF`,
Uranium `000057EB`, Iridium `000057EC`, Vanadium `000057ED`, Iron
`000057C7`.

Missing: none. Unexpected: Alkanes `000057C9`.

### Family ledger

| Seq | Runtime biome | Root | New/cache | Structural path | Emitted descendants | Families after |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | 0 Frozen Plains | Nickel | new | Nickel* -> Cobalt -> Platinum -> Palladium -> Tasine | none | 1 |
| 2 | 1 Plateau | Copper | new | Copper* -> Fluorine -> Gold -> Antimony -> empty | none | 2 |
| 3 | 2 Sandy Desert | Uranium | new | Uranium* -> Iridium* -> Vanadium* -> Plutonium -> Vytinium | Iridium, Vanadium | 3 |
| 4 | 3 Mountains | Iron | new | Iron* -> Alkanes* -> Tantalum -> Ytterbium -> Rothicite | Alkanes | 4 |

### Resource insertion ledger

| Seq | Runtime biome | Family | Resource | Rarity/source | Cache? | Count after | Canonical? |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 1 | upstream | - | Water | Everywhere | no | 1 | yes |
| 2 | 0 Frozen Plains | Nickel | Nickel | Common root | no | 2 | yes |
| 3 | 1 Plateau | Copper | Copper | Common root | no | 3 | yes |
| 4 | 2 Sandy Desert | Uranium | Uranium | Common root | no | 4 | yes |
| 5 | 2 Sandy Desert | Uranium | Iridium | Uncommon descendant | no | 5 | yes |
| 6 | 2 Sandy Desert | Uranium | Vanadium | Rare descendant | no | 6 | yes |
| 7 | 3 Mountains | Iron | Iron | Common root | no | 7 | yes |
| 8 | 3 Mountains | Iron | Alkanes | Uncommon descendant | no | 8 | **no** |

### First divergence

**PROVEN:** event 112 / insertion 8 emits unexpected Uncommon Alkanes. The
causal events are draw 35 inclusion (`raw=1951474139`, pass against 0.5) and
draw 36 selection (`raw=1053488104`, one candidate).

```text
visible resource insertions:             7
completed family-cache entries:           3
new Common roots already emitted:         4
cache hits so far:                        0
runtime biome position / BiomeIndex:      3 / 0
effective RSGD:                           MountainNoLifeDefaultRes
root / descendant level:                 Iron / Uncommon
```

Maal VIII is incompatible with a simple `len(resources) >= 8` stop: the
prediction reaches eight, while the canonical set stops at seven after retaining
the fourth root.

## 5. Fermi III dossier

### Static inputs and final sets

```text
PlanetFormID: 0005DE2D
RSCS:         1248724893
Initial:      0 Ocean, 1 Frozen Mountains, 2 Deciduous Forest,
              3 Sandy Desert, 4 Mountains
Runtime:      4 Mountains, 1 Frozen Mountains, 3 Sandy Desert,
              2 Deciduous Forest, 0 Ocean
Draws:        46
```

| Runtime pos. | BiomeIndex | Biome | Effective RSGD |
| ---: | ---: | --- | --- |
| 0 | 4 | Mountains | MountainDefaultRes |
| 1 | 1 | Frozen Mountains | FrozenBarrenDefaultRes |
| 2 | 3 | Sandy Desert | DesertSandDefaultRes |
| 3 | 2 | Deciduous Forest | ForestDeciduousRes |
| 4 | 0 | Ocean | OceanDefaultRes |

All five definitions are BIOM RNAM inputs.

Predicted (9): Water `000083EC`, Iron `000057C7`, Alkanes `000057C9`,
Argon `000057EA`, Benzene `000057E7`, Uranium `000057EB`, Iridium
`000057EC`, Vanadium `000057ED`, Nickel `000057CB`.

Canonical (8): Water `000083EC`, Iron `000057C7`, Alkanes `000057C9`,
Argon `000057EA`, Benzene `000057E7`, Uranium `000057EB`, Iridium
`000057EC`, Vanadium `000057ED`.

Missing: none. Unexpected: Nickel `000057CB`.

### Family ledger

| Seq | Runtime biome | Root | New/cache | Structural path | Emitted descendants | Families after |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | 0 Mountains | Iron | new | Iron* -> Alkanes* -> Tantalum -> Ytterbium -> Rothicite | Alkanes | 1 |
| 2 | 1 Frozen Mountains | Argon | new | Argon* -> Benzene* -> Carboxylic Acids -> Neon -> Veryl | Benzene | 2 |
| 3 | 2 Sandy Desert | Uranium | new | Uranium* -> Iridium* -> Vanadium* -> Plutonium -> Vytinium | Iridium, Vanadium | 3 |
| 4 | 3 Deciduous Forest | Nickel | new | Nickel* -> Cobalt -> Platinum -> Palladium -> Tasine | none | 4 |

The final Ocean biome selects no Common root.

### Resource insertion ledger

| Seq | Runtime biome | Family | Resource | Rarity/source | Cache? | Count after | Canonical? |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 1 | upstream | - | Water | Everywhere | no | 1 | yes |
| 2 | 0 Mountains | Iron | Iron | Common root | no | 2 | yes |
| 3 | 0 Mountains | Iron | Alkanes | Uncommon descendant | no | 3 | yes |
| 4 | 1 Frozen Mountains | Argon | Argon | Common root | no | 4 | yes |
| 5 | 1 Frozen Mountains | Argon | Benzene | Uncommon descendant | no | 5 | yes |
| 6 | 2 Sandy Desert | Uranium | Uranium | Common root | no | 6 | yes |
| 7 | 2 Sandy Desert | Uranium | Iridium | Uncommon descendant | no | 7 | yes |
| 8 | 2 Sandy Desert | Uranium | Vanadium | Rare descendant | no | 8 | yes |
| 9 | 3 Deciduous Forest | Nickel | Nickel | Common root | no | 9 | **no** |

### First divergence

**PROVEN:** event 110 / insertion 9 unconditionally emits the unexpected Common
root Nickel. Draw 36 (`raw=2810004502`) selected Nickel in the preceding Common
selector; family begin is event 109 and root emission is event 110.

```text
visible resource insertions:             8
completed family-cache entries:           3
new Common roots already emitted:         3
cache hits so far:                        0
runtime biome position / BiomeIndex:      3 / 2
effective RSGD:                           ForestDeciduousRes
root / descendant level:                 Nickel / root
```

Unlike the other two cases, reproducing the canonical set requires suppressing
the entire fourth family before its root insertion.

## 6. Cross-case comparison

| Dimension | Fermi VII-a | Maal VIII | Fermi III |
| --- | ---: | ---: | ---: |
| Predicted / canonical resources | 9 / 8 | 8 / 7 | 9 / 8 |
| First unexpected insertion | 9 | 8 | 9 |
| Visible count immediately before | 8 | 7 | 8 |
| Distinct completed configs immediately before | 2 | 3 | 3 |
| Current family ordinal | 3 | 4 | 4 |
| New roots emitted through that point | 3 | 4 | 3 before / 4 after | 
| Total distinct generated configs | 3 | 4 | 4 |
| Root accesses | 4 | 4 | 4 |
| Cache hits total / before divergence | 1 / 0 | 0 / 0 | 0 / 0 |
| Divergence class | Exotic descendant | Uncommon descendant | Common root |

All three unexpected resources are the last unique insertion. This makes
insertion order important evidence, but it does not identify the counted runtime
state.

## 7. Counterfactual cutoff matrix

### Visible unique insertion count

**COUNTERFACTUAL:** retain only the first N recorded unique insertions.

| N | Fermi VII-a | Maal VIII | Fermi III |
| ---: | --- | --- | --- |
| 5 | incompatible | incompatible | incompatible |
| 6 | incompatible | incompatible | incompatible |
| 7 | incompatible | **compatible** | incompatible |
| 8 | **compatible** | incompatible | **compatible** |

Stopping immediately before each actual first unexpected insertion is compatible
for all three; stopping immediately after it is incompatible. No one fixed
visible threshold from 5 through 8 explains all three.

### Distinct generated Common-family configurations

**COUNTERFACTUAL:** retain upstream/non-family insertions plus insertions belonging
to only the first N distinct Common families.

| N | Fermi VII-a | Maal VIII | Fermi III |
| ---: | --- | --- | --- |
| 3 | incompatible (loses Copper/Fluorine if family 3 is blocked) | incompatible (loses Iron) | **compatible** |
| 4 | incompatible | incompatible | incompatible |
| 5 | incompatible | incompatible | incompatible |

A simple cap on completed cache entries does not explain the partial-family
outcomes in Fermi VII-a or Maal VIII. Fermi III alone is compatible with blocking
the fourth family before root insertion.

### Hypothesis matrix

Here H1 means a fixed eight-visible-resource cap, and H2 means an equivalent
fixed count of the insertion attempts observed here. These dossiers contain no
duplicate visible insertion attempts before divergence, so H2 cannot otherwise
be separated from H1.

| Hypothesis | Fermi VII-a | Maal VIII | Fermi III |
| --- | --- | --- | --- |
| H1 hard cap at eight visible resources | compatible | incompatible | compatible |
| H2 hard cap at eight observed insertion attempts | compatible | incompatible | compatible |
| H3 simple hard cap on distinct Common configurations | incompatible | incompatible | compatible only with cap 3 |
| H4 Everywhere/Special consume visible capacity | not discriminated | not discriminated | not discriminated |
| H5 Everywhere/Special use reserved capacity | not discriminated | not discriminated | not discriminated |
| H6 cache hits consume family/configuration capacity | incompatible as Fermi cause; hit is later | not discriminated | not discriminated |
| H7 cache hits do not consume family/configuration capacity | compatible | not discriminated | not discriminated |
| H8 limit blocks an entire new family before root | incompatible | incompatible | compatible |
| H9 limit allows root but blocks later descendants | compatible | compatible | incompatible |
| H10 insertion priority/order matters at a boundary | compatible | compatible | compatible |

The cases rule out a naïve fixed-eight final-cardinality rule and any single
simple family-count cutoff represented by the reproducer cache. They do not rule
out a compound state variable, reserved categories, per-family insertion policy,
or an order-sensitive container boundary.

## 8. Existing Ghidra evidence

The checked-in Markdown, historical diffs, and repository-local text exports
were searched for resource-slot, family-limit, insertion-container,
`BGSPlanetDataManager`, and structurally relevant 5/8 comparisons. No Ghidra
decompilation/export containing a concrete five-family or eight-slot comparison
survives in the repository.

| Function/address | Repository evidence | Constant/offset | Surrounding operation | Before/after insertion | Scope/status |
| --- | --- | --- | --- | --- | --- |
| `FUN_1415DCFB0` / `0x1415DCFB0` | `AGENTS.md`, `docs/DOMAIN-RULES.md`, 05A/05B records | none retained | per-biome Special/Common generation; Water already upstream | insertion-limit branch not retained | per-biome anchor; PROVEN role, no limit evidence |
| `FUN_14157F120` / `0x14157F120` | 05B, 05C, 05D records and experiments | none retained | descendant-level generation; four rarity calls; bypassed on cache hit | emission decision occurs within/around this path, exact insertion helper absent | family-local anchor; PROVEN call behavior, no 5/8 evidence |
| `FUN_14152CBC0` -> `0x1401714A8` -> `0x14001D63D` -> `0x141587240` | 05D experiment | RNG bound, not 5/8 capacity | biome-shuffle bounded RNG | before per-biome insertion | PROVEN RNG anchor; irrelevant to capacity |
| `BGSPlanetDataManager.cpp`-associated functions | no concrete export found | absent | absent | unknown | requested search term only; no surviving evidence |

The backlog and briefs preserve only contextual labels, "five-family limit" and
"eight-resource-slot limit." They contain no comparison instruction, branch
direction, field/container offset, or proof that either count is planet-wide.
Repeating those labels as recovered mechanism would overstate the evidence.

## 9. Candidate runtime hypotheses

Current evidence favors an order-sensitive or compound insertion state over a
single visible-count or reproducer-cache-count cap:

1. Fermi VII-a permits a third family root and first descendant, then diverges
   on a later descendant before its only cache hit.
2. Maal VIII permits the fourth family root at visible count seven, then diverges
   on that family's first descendant at count eight.
3. Fermi III diverges on the fourth family root at visible count eight.

This may reflect different capacity accounting for roots and descendants, a
container with reserved/category-specific entries, or another state value not
represented by either visible unique count or cache size. Those interpretations
remain **PROVISIONAL**.

## 10. Recommended next live/static experiment

Primary planet: **Maal VIII**. It is the smallest decisive refutation of a fixed
eight-visible-resource stop and retains the fourth root while excluding its
first descendant.

Primary runtime anchor: **`FUN_1415DCFB0` (`0x1415DCFB0`)**, with
`FUN_14157F120` (`0x14157F120`) as the nested Iron/Uncommon descendant anchor.
No repository-held insertion-helper address is reliable enough to name yet.

Recommended automated trace boundary:

1. break on the fourth Maal VIII invocation of `FUN_1415DCFB0` (Mountains,
   BiomeIndex 0, runtime position 3);
2. at that deterministic hit, `StartRunTrace`;
3. run through the Iron root and the nested Uncommon `FUN_14157F120` call until
   the per-biome function returns;
4. `StopRunTrace` and analyze offline for the Iron insertion, Alkanes structural
   selection/inclusion, any insertion-helper call, container count/offset reads,
   and the branch that accepts or suppresses Alkanes.

This single trace distinguishes selection from insertion suppression and should
expose a concrete comparison/field near the boundary. It requires no manual
instruction stepping or register archaeology. If the branch lies in a caller or
callee not yet named, promote that concrete address as the next static Ghidra
anchor.

Water/Everywhere discrepancies, including Huygens VII-b, remain explicitly out
of scope.
