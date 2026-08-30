# Starfield Resource Reproducer

A standalone reference implementation of Starfield's deterministic planetary resource-generation algorithm.

## Status

**Research / pre-v0.1**

The reverse-engineering phase has recovered most of the central generation path from Creation Kit live traces, Ghidra analysis, xEdit extraction, and verified game/runtime observations.

The next milestone is to encode those rules in a small standalone reproducer, validate known worked examples, and then compare predictions across the full canonical dataset.

The isolated PRNG compatibility layer now reproduces the supplied Mimas float
anchors and Kreet biome-swap choices with explicit raw-output draw accounting.
The full resource-generation engine remains the next implementation stage.

## Goal

Given authoritative static inputs for a planet:

- PNDT resource seed and biome entries;
- effective per-biome RSGD data;
- IRES resource hierarchy;

the reproducer should independently predict the resources assigned by the game.

Conceptually:

```text
PNDT / BIOM / RSGD + IRES hierarchy + RSCS
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

At a high level:

```text
PNDT biome entries in BiomeIndex order
             |
             v
      MT19937 seeded by RSCS
             |
             v
 deterministic biome shuffle
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
             |
             +--> Common/root weighted selection (0)
                         |
                         +--> family already generated
                         |       -> reuse cached family result
                         |
                         +--> new family
                                 |
                                 +--> emit root
                                 +--> Uncommon (1)
                                 +--> Rare (2)
                                 +--> Exotic (3)
                                 +--> Unique (4)
```

Water (`Everywhere`, category 6) is already present upstream of the per-biome generator observed in the current traces. Its exact upstream insertion routine is not yet required for v0.1 unless validation shows that the provisional model is insufficient.

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
2. load the three canonical datasets;
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
