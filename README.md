# Starfield Resource Reproducer

A standalone reference implementation of Starfield's deterministic planetary resource-generation algorithm.

## Status

**Research / pre-v0.1**

The reverse-engineering phase has recovered most of the central generation path from Creation Kit live traces, Ghidra analysis, xEdit extraction, and verified game/runtime observations.

The runtime-proven split between biome-shuffle integer bounded selection and
descendant float32-scaled selection is implemented. Brief 07B integrates the
atmospheric export, pre-main Everywhere handling, the recovered category-generic
Special/Common selector, and a shared eight-unique-FormID state. Brief 08A
corrects category-6 eligibility from live Fermi VIII-b evidence. Briefs 08B and
08C add the proven five-distinct-Common-tree and shared-eight pre-selector guards.
Brief 08D implements the proven post-guard assignment of an already-generated
family configuration to the current biome. The complete canonical inorganic
intersection has 1,444 exact matches out of 1,444 with no generation errors.

The generation engine prepopulates atmosphere occurrences, visits every effective
RSGD in the Everywhere pre-pass, and then carries one explicitly accounted PRNG
stream through biome shuffle and per-biome generation. Resource identity/capacity
is separate from occurrence provenance: ATMO, Everywhere, Special, Common, and
Descendant occurrences may share one occupied FormID slot. The
Brief 03 partial orchestration API remains available for outer-decision research;
the family API adds structural descendant paths, independent inclusion/emission,
and FormID-keyed cache reuse. A complete `generate_planet()` prediction API now
assembles final player-facing, RSGD/CK-visible, and atmospheric channels without
consulting the oracle. The validator compares the RSGD/CK-visible channel because
`planet-all-resources.csv` is proven to omit at least some atmospheric resources;
its exact SurveyAggregator contract remains open. It reproduces Oberon, Mimas, Decaran
VII-b, Kreet, and Algorab I exactly. Algorab also agrees internally with its
live Lead trace: scaled descendant selection takes Silver then Mercury and ends
at draw 22. Empty descendant levels consume one raw MT word, while family-cache
hits bypass descendant generation without consuming descendant RNG.

The guarded fallback changes biome-local assignment and subsequent RNG state
without introducing planet-wide identities; the canonical result remains
1,444 / 1,444 exact. CK-observed biome assignments are covered separately because
the canonical planet-wide oracle contains no biome-local mapping.

## Goal

Given authoritative static inputs for a planet:

- PNDT resource seed and biome entries;
- effective per-biome RSGD data;
- IRES resource hierarchy;
- effective atmospheric inorganic-resource records;

the reproducer should independently predict the resources assigned by the game.

Conceptually:

```text
PNDT / BIOM / RSGD + ATMO + IRES hierarchy + RSCS
                     |
                     v
              deterministic model
                     |
                     v
            predicted resources
                     |
                     v
       compare with verified game output
```

The long-term target is exact reproducibility, not merely statistically similar output.

## What This Repository Is Not

At this stage it is not:

- the Starfield outpost planner;
- an in-game mod;
- a GUI application;
- a general-purpose Starfield data extractor.

It is a deliberately small research tool and future regression oracle.

## Canonical Data Inputs

### `PlanetResourceGeneration_v5.csv`

Static PNDT -> biome -> RSGD extraction.

Expected content includes:

- planet identity;
- unsigned 32-bit `RSCS`;
- original `BiomeIndex`;
- biome identity and chance;
- PNDT and BIOM RSGD provenance;
- ordered RSGD resource entries;
- IRES rarity/category;
- Common / Uncommon / Rare / Exotic / Unique / Special / Everywhere generation percentages.

### `Starfield_IRES_Hierarchy.csv`

Canonical static IRES graph:

- resource identity;
- rarity;
- parent -> child relationships.

This is the authoritative resource-tree input.

### `Starfield_PlanetAtmosphericResources.tsv`

First-class atmospheric inorganic-resource input. This TSV preserves ordered
planet/resource rows, atmosphere identity, the defining ATMO record, source files,
and inheritance depth. Absence means the export contains no atmospheric resource
row for that planet; it is not a malformed generation record.

### `planet-all-resources.csv`

**Canonical validation oracle.**

This file was sourced from within the game/runtime and verified independently.

Current supplied dataset:

- 7,663 body/resource rows;
- 1,445 distinct bodies;
- 121 systems;
- 6,040 inorganic rows;
- 1,623 organic rows;
- no null fields;
- no duplicate `(PlanetFormID, ResourceFormID)` pairs.

Columns:

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

The reproducer's initial scope is inorganic generation, so validation should filter this oracle to `ResourceCategory == "Inorganic"`.

### Deprecated dataset

`Starfield_InorganicResources_Canonical.csv` is deprecated.

Do not use it as the expected-output source. In particular, it predates the current verified runtime-derived dataset and does not provide the desired Shattered Space coverage.

## Recovered Algorithm: Current Core Model

At a high level, all mechanisms share capacity for eight unique resource FormIDs
while retaining separate provenance occurrences:

```text
Atmospheric resource prepopulation (no RNG)
             |
             v
Everywhere/category-6 pre-pass over every effective RSGD (no RNG)
             |
             v
PNDT biome entries -> MT19937 deterministic biome shuffle
 integer rejection + modulo
             |
             v
   process shuffled biomes
             |
             +--> effective RSGD
             |       PNDT override if present
             |       otherwise BIOM RNAM
             |
             +--> Special pass (5)
             |       e.g. Helium-3
             |       record selected Special in shared state
             |       before evaluating either Common guard
             |
             +--> Common/root weighted selection (0)
                        normal selector skipped once five Common trees exist
                        normal selector skipped at eight shared resource IDs
                         |
                         +--> guard fallback assignment
                         |       match cached roots present in effective RSGD
                         |       otherwise choose from all cached families
                         |       no Common entries -> no assignment
                         |
                         +--> family already generated
                         |       -> reuse cached family result
                         |
                         +--> new family
                                 |
                                 +--> emit root
                                 +--> descendants use float32 scaled indices
                                 +--> Uncommon (1)
                                 +--> Rare (2)
                                 +--> Exotic (3)
                                 +--> Unique (4)
```

The Everywhere pre-pass visits all biome/effective-RSGD contexts before shuffled
main generation. In the observed Creation Kit Galaxy View Apply path, it emits
category-6 entries in authored RSGD order without consulting a DNAM chance field
or consuming RNG. A one-entry Common RSGD still uses the ordinary weighted
selector and consumes its normal draw; there is no generic one-entry bypass.
Once five distinct Common tree configurations have been established, the main
per-biome path skips the Common selector before its probability draw. This guard
is separate from the shared capacity of eight unique resource FormIDs. PROVEN
STATIC/LIVE control flow in `FUN_1415DCFB0` checks that shared capacity after the
five-tree guard and before the Common selector; at eight occupied IDs, normal
selection is bypassed without consuming its usual RNG draw. **PROVEN LIVE:** both
guards then enter a fallback stage. Matching cached roots in the effective RSGD
form the preferred family pool; otherwise all cached families are eligible. The
float32-scaled fallback choice consumes one draw even for a one-family pool and
copies the cached configuration into the biome without creating new identities.
Within each biome, a selected Special occurrence updates shared resource state
before the five-tree and shared-eight guards. A new Special identity can therefore
fill slot eight and cause that biome to enter Common guard fallback; a duplicate
Special occurrence does not increase the occupied count.

See `docs/DOMAIN-RULES.md` for the detailed rule set and evidence status.

## Known Worked Cases

The initial implementation should reproduce these before attempting full-dataset validation.

### Oberon

Purpose:

- simple root-only control;
- proves category `6 = Everywhere = Water`;
- demonstrates Water is not selected by the per-biome Common/Special selector.

Expected inorganic result includes:

```text
Water
Nickel
```

### Mimas

Purpose:

- weighted Common/root selection;
- descendant RNG consumption;
- structural traversal through omitted resources.

Observed family path:

```text
Nickel
  -> Cobalt      omitted
  -> Platinum    omitted
  -> Palladium   emitted
  -> Tasine      omitted
```

Expected relevant result:

```text
Water
Nickel
Palladium
```

### Decaran VII-b

Purpose:

- PNDT RSGD override;
- `Special = Helium-3`;
- unique-resource generation through normal IRES traversal.

Observed relevant result:

```text
Uranium
Iridium
Vytinium
Helium-3
```

### Kreet

Purpose:

- multi-biome processing;
- PNDT-order construction;
- deterministic shuffle;
- ordinary PNDT RSGD overrides.

Initial PNDT biome order:

```text
0 Frozen Volcanic
1 Mountains
2 Volcanic
```

Observed shuffled processing order:

```text
2 Volcanic
0 Frozen Volcanic
1 Mountains
```

Observed inorganic result:

```text
Water
Lead
Silver
Argon
Neon
Iron
Alkanes
```

## Proposed CLI

The first version should support a diagnostic single-body mode:

```bash
python reproduce.py --planet "Mimas"
```

and eventually whole-dataset validation:

```bash
python reproduce.py --all
```

Single-body mode should prioritize transparent diagnostics over pretty output.

Whole-dataset mode should report:

- bodies tested;
- exact matches;
- mismatches;
- match percentage;
- missing resources;
- unexpected resources;

and write a machine-readable mismatch report.

## First Milestone

**v0.1**

1. establish repository structure and tests;
2. load the four canonical input datasets;
3. validate the exact MT19937 behavior used by the game;
4. implement the recovered central generation path;
5. reproduce Oberon, Mimas, Decaran VII-b, and Kreet;
6. run the complete inorganic validation set;
7. use mismatches to identify only the remaining edge cases that matter.

## Development Workflow

Architecture and reverse-engineering specifications are developed in discussion and handed to Codex as scoped Markdown implementation briefs.

Codex should follow `AGENTS.md` and `docs/IMPLEMENTATION-WORKFLOW.md`.

## Documentation

- `AGENTS.md` — instructions and guardrails for coding agents
- `docs/ARCHITECTURE.md` — intended software decomposition
- `docs/DOMAIN-RULES.md` — recovered Starfield generation rules and evidence status
- `docs/BACKLOG.md` — staged implementation/research backlog
- `docs/IMPLEMENTATION-WORKFLOW.md` — ChatGPT / Codex / user collaboration process
