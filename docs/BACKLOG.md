# Backlog

## Guiding Rule

Build the smallest implementation that can make falsifiable predictions, then let canonical mismatches direct further reverse engineering.

Do not attempt to implement every theoretical engine edge case before the first full-dataset run.

## Phase 0 — Repository Bootstrap

- [x] Create Python project/environment.
- [x] Add `AGENTS.md` and documentation.
- [x] Add `.gitignore`.
- [x] Add `pyproject.toml`.
- [x] Establish `src/` package layout.
- [x] Establish `tests/`.
- [x] Add canonical data files under an agreed local/data path.
- [x] Ensure deprecated `Starfield_InorganicResources_Canonical.csv` is absent or clearly excluded.

Acceptance:

- clean install;
- tests execute;
- CLI placeholder runs;
- documentation links are valid.

## Phase 1 — Canonical Data Loading

- [ ] Load `PlanetResourceGeneration_v5.csv`.
- [ ] Validate required schema.
- [ ] Reconstruct planets and ordered biome entries.
- [ ] Reconstruct ordered RSGD resource arrays.
- [ ] Load `Starfield_IRES_Hierarchy.csv`.
- [ ] Reconstruct IRES graph.
- [ ] Load `planet-all-resources.csv` as validation oracle.
- [ ] Filter validation oracle to `ResourceCategory == Inorganic`.
- [ ] Add schema/data-integrity tests.

Acceptance:

- Kreet has exactly three PNDT biome entries in indices 0/1/2;
- Mimas effective RSGD inputs match known worked case;
- duplicate and conflicting rows fail explicitly;
- oracle lookup returns verified inorganic sets by PlanetFormID.

## Phase 2 — PRNG Compatibility Harness

Highest risk before broad implementation.

- [ ] Implement candidate MT19937 wrapper.
- [ ] Confirm unsigned 32-bit seed handling.
- [ ] Reproduce known live trace random values at known draw positions.
- [ ] Verify bounded-index conversion used by shuffle/candidate selection.
- [ ] Record draw count in diagnostics.
- [ ] Do not proceed with broad validation if PRNG mismatch remains unexplained.

Known anchors include Mimas:

```text
RSCS 2008989584
Common selection roll ~= 0.561107993
L1 inclusion        ~= 0.894184828
L2 inclusion        ~= 0.686025143
L3 inclusion        ~= 0.108883217
```

Exact expected draw positions should be specified in the implementation brief once the current trace model is encoded.

## Phase 3 — Core Generation v0.1

- [ ] Construct biome list in PNDT `BiomeIndex` order.
- [ ] Implement deterministic shuffle.
- [ ] Implement effective RSGD precedence.
- [ ] Implement provisional Everywhere/Water preload.
- [ ] Implement Special pass.
- [ ] Implement Common cumulative weighted selector.
- [ ] Preserve RSGD order.
- [ ] Do not normalize weights.
- [ ] Implement IRES descendant candidate builder.
- [ ] Separate structural choice from inclusion/emission.
- [ ] Consume candidate-index RNG with one candidate.
- [ ] Implement family configuration cache.
- [ ] Emit structured diagnostics.

## Phase 4 — Worked-Case Regression Tests

### Oberon

- [ ] Water present.
- [ ] Nickel selected.
- [ ] no emitted descendants for observed seed.

### Mimas

- [ ] Nickel wins against Lead.
- [ ] Cobalt structurally chosen but omitted.
- [ ] Platinum structurally chosen but omitted.
- [ ] Palladium emitted.
- [ ] Tasine structurally chosen but omitted.
- [ ] final relevant set matches oracle.

### Decaran VII-b

- [ ] PNDT RSGD replaces BIOM RSGD.
- [ ] Helium-3 selected as Special.
- [ ] Uranium root.
- [ ] Vytinium reached via ordinary IRES traversal.
- [ ] final set matches oracle.

### Kreet

- [ ] initial order `[0, 1, 2]`.
- [ ] shuffled processing order `[2, 0, 1]`.
- [ ] Volcanic -> Lead + Silver.
- [ ] Frozen Volcanic -> Argon + Neon.
- [ ] Mountains -> Iron + Alkanes.
- [ ] Water present upstream/provisionally.
- [ ] final set matches oracle.

Acceptance:

All four cases pass with intermediate diagnostic assertions.

## Phase 5 — Full Canonical Validation

- [ ] Run every body in `planet-all-resources.csv` for which static reproducer inputs exist.
- [ ] Compare inorganic predicted vs canonical sets.
- [ ] Produce summary metrics.
- [ ] Produce mismatch report with:
  - PlanetFormID;
  - planet/system;
  - expected;
  - predicted;
  - missing;
  - unexpected;
  - diagnostic pointer/reason where available.
- [ ] Group mismatches by apparent pattern.

Do not change rules merely to increase aggregate match rate without evidence.

## Phase 6 — Mismatch-Driven Reverse Engineering

Only investigate branches demonstrated to matter.

Possible categories:

- [ ] Everywhere/Water upstream insertion semantics.
- [ ] family-cache RNG consumption on repeated-root biomes.
- [ ] no-candidate RNG consumption.
- [ ] zero/100-percent inclusion draw behavior.
- [ ] five-family limit.
- [ ] eight-resource-slot limit.
- [ ] RSCS = 0 fallback behavior.
- [ ] duplicate suppression.
- [ ] fallback/additional RSGD paths.
- [ ] unusual DLC/plugin data.
- [ ] edge handling for Special/Everywhere interaction.

Each discovered behavior should receive:

1. evidence;
2. a domain-rule update;
3. a focused regression test;
4. an implementation change.

## Phase 7 — Reference Reproducer 1.0

Target:

- exact or near-exact canonical reproduction with all remaining differences understood;
- stable diagnostic CLI;
- documented deterministic algorithm;
- reusable generation package;
- reproducible full-dataset validation report.

## Deferred

Not part of the reproducer bootstrap:

- planner UI;
- outpost logistics solver;
- game-state ingestion;
- organic resource generation;
- surface vein/cell placement;
- graphical interface;
- web deployment.
