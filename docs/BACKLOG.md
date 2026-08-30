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

- [x] Load `PlanetResourceGeneration_v5.csv`.
- [x] Validate required schema.
- [x] Reconstruct planets and ordered biome entries.
- [x] Reconstruct ordered RSGD resource arrays.
- [x] Load `Starfield_IRES_Hierarchy.csv`.
- [x] Reconstruct IRES graph.
- [x] Load `planet-all-resources.csv` as validation oracle.
- [x] Filter validation oracle to `ResourceCategory == Inorganic`.
- [x] Add schema/data-integrity tests.

Acceptance:

- Kreet has exactly three PNDT biome entries in indices 0/1/2;
- Mimas effective RSGD inputs match known worked case;
- duplicate and conflicting rows fail explicitly;
- oracle lookup returns verified inorganic sets by PlanetFormID.

## Phase 2 — PRNG Compatibility Harness

Highest risk before broad implementation.

- [x] Implement candidate MT19937 wrapper.
- [x] Confirm unsigned 32-bit seed handling.
- [x] Reproduce known live trace random values at known draw positions.
- [x] Verify bounded-index conversion used by shuffle/candidate selection.
- [x] Record draw count in diagnostics.
- [x] Do not proceed with broad validation if PRNG mismatch remains unexplained.

Known anchors include Mimas:

```text
RSCS 2008989584
Common selection roll ~= 0.561107993
L1 inclusion        ~= 0.894184828
L2 inclusion        ~= 0.686025143
L3 inclusion        ~= 0.108883217
```

Exact expected draw positions should be specified in the implementation brief once the current trace model is encoded.

Brief 02 reproduces all supplied anchors. The Mimas Common roll is raw draw 2;
the high-level operation responsible for the one-word prefix remains explicitly
unresolved. Bounded modulo conversion and the binary32 float expression are
STRONG compatibility findings rather than universal PROVEN rules.

## Phase 3 — Core Generation v0.1

- [x] Construct biome list in PNDT `BiomeIndex` order.
- [x] Implement deterministic shuffle.
- [x] Implement effective RSGD precedence.
- [x] Implement provisional Everywhere/Water preload.
- [x] Implement Special pass.
- [x] Implement Common cumulative weighted selector.
- [x] Preserve RSGD order.
- [x] Do not normalize weights.
- [x] Implement IRES descendant candidate builder.
- [x] Separate structural choice from inclusion/emission.
- [x] Consume candidate-index RNG with one candidate.
- [x] Implement family configuration cache.
- [x] Emit structured orchestration diagnostics.

## Phase 4 — Worked-Case Regression Tests

### Oberon

- [x] Water present in provisional Everywhere result.
- [x] Nickel selected as Common root.
- [x] no emitted descendants for observed seed.
- [x] complete predicted set matches oracle by FormID.

### Mimas

- [x] Nickel wins against Lead in outer orchestration.
- [x] Cobalt structurally chosen but omitted.
- [x] Platinum structurally chosen but omitted.
- [x] Palladium emitted.
- [x] Tasine structurally chosen but omitted.
- [x] final relevant set matches oracle.
- [x] exact comparison reports no missing/unexpected FormIDs.

### Decaran VII-b

- [x] PNDT RSGD replaces BIOM RSGD.
- [x] Helium-3 selected as Special.
- [x] Uranium root.
- [x] Vytinium reached via ordinary IRES traversal.
- [x] final set matches oracle.
- [x] exact comparison uses FormID despite Helium-3/Helium3 naming.

### Kreet

- [x] initial order `[0, 1, 2]`.
- [x] shuffled processing order `[2, 0, 1]`.
- [x] Volcanic -> Lead + Silver.
- [x] Frozen Volcanic -> Argon + Neon.
- [x] Mountains -> Iron + Alkanes.
- [x] Water present upstream/provisionally.
- [x] final set matches oracle.
- [x] historical deterministic missing-Neon mismatch is preserved diagnostically.
- [x] Argon/Neon inclusion draw and preceding Lead zero-candidate levels are exposed.
- [x] diagnostics-only two-draw displacement counterfactual is labeled unproven.
- [x] compare no-draw, inclusion, index-raw-equivalent, and two-draw policies.
- [x] reproduce Neon at draw 17 when one raw word is consumed at each empty level.
- [x] prove one raw MT word is consumed per zero-candidate level by live trace.

Acceptance:

Oberon, Mimas, Decaran VII-b, and Kreet match exactly. Kreet's two empty Lead
levels advance the stream to Argon's passing Neon roll at draw 17.

### Worked-case validation infrastructure

- [x] Complete oracle-independent planet prediction result.
- [x] Separate FormID-based oracle comparison result.
- [x] Deterministic structured-event timeline formatter.
- [x] Missing/unexpected resource diagnostics with readable metadata.
- [x] Zero-candidate and cache-hit draw accounting.
- [x] Evidence-qualified mismatch classification.

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
- [x] family-cache RNG consumption on repeated-root biomes (Algorab I live proof).
- [x] no-candidate RNG consumption (Algorab I live proof: one raw word).
- [ ] Algorab I Lead structural path / bounded-index interpretation (canonical
  set exact; current model draw 23 versus live-shaped draw 22).
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
