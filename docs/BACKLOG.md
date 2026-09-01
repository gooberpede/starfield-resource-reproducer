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
- [x] Resolve shuffle and descendant selection as distinct bounded conversions.
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
the empty Special pass accounts for draw 1. The binary32 probability expression
remains STRONG. Brief 05D resolves the Brief 05C conflict: shuffle uses a proven
integer rejection/modulo helper, while descendants use proven float32 scaling
and truncation.

## Phase 3 — Core Generation v0.1

- [x] Construct biome list in PNDT `BiomeIndex` order.
- [x] Implement deterministic shuffle.
- [x] Implement effective RSGD precedence.
- [x] Integrate atmospheric prepopulation as a fourth first-class input.
- [x] Implement the recovered Everywhere/category-6 pre-pass ordering.
- [x] Preserve ATMO/Everywhere/Special/Common/Descendant provenance occurrences.
- [x] Enforce the shared eight-unique-FormID state across all mechanisms.
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

- [x] Run every body in `planet-all-resources.csv` for which static reproducer inputs exist.
- [x] Compare inorganic predicted vs canonical sets.
- [x] Produce summary metrics.
- [x] Produce mismatch report with:
  - PlanetFormID;
  - planet/system;
  - expected;
  - predicted;
  - missing;
  - unexpected;
  - diagnostic pointer/reason where available.
- [x] Group mismatches by apparent pattern.

Brief 06 baseline (current canonical files):

```text
validation population  1,444
FINAL_SET_EXACT        1,281 (88.71%)
mismatches               163
generation errors           0
coverage-only bodies         0
```

The dominant mismatch class is unexpected output on resource-dense multi-biome
planets: 148 are unexpected-only and one mixed mismatch also contains an
unexpected resource. Separately, all 15 missing occurrences are Water, matching
the known PROVISIONAL Everywhere boundary. These are research targets, not
accepted production behavior. The next priority is the resource-slot/family
limit and insertion-order class; Everywhere insertion remains a separate follow-up.

Do not change rules merely to increase aggregate match rate without evidence.

Brief 07B post-integration result:

```text
validation population  1,444
FINAL_SET_EXACT        1,426 (98.75%)
mismatches                18
generation errors          0
coverage-only bodies       0
```

The validator compares the RSGD/CK-visible channel with the still-open oracle
contract and reports atmospheric and final player-facing channels separately.

Brief 08A category-6 correction result:

```text
validation population  1,444
FINAL_SET_EXACT        1,441 (99.79%)
mismatches                 3
generation errors          0
coverage-only bodies       0
```

All 15 Water-only residuals disappeared after the PROVEN LIVE category-6 rule
stopped consulting DNAM Everywhere chance. The remaining research targets are
the two atmospheric/Common Chlorine collisions and Bara VII-d's unexpected
Nickel, consistent with the unresolved five-family guard investigation.

## Phase 6 - Mismatch-Driven Reverse Engineering

Only investigate branches demonstrated to matter.

Possible categories:

- [x] Everywhere/Water pre-main ordering and all-biome work-object traversal.
- [x] category-6 eligibility ignores DNAM Everywhere/Common chance and consumes
  no RNG (Fermi VIII-b live proof).
- [x] family-cache RNG consumption on repeated-root biomes (Algorab I live proof).
- [x] no-candidate RNG consumption (Algorab I live proof: one raw word).
- [x] shuffle versus descendant bounded-index path distinction (Brief 05D live
  proof and separate production APIs).
- [ ] zero/100-percent inclusion draw behavior.
- [ ] five-family limit.
- [x] shared eight-unique-FormID capacity model (STRONG duplicate-slot semantics).
- [ ] RSCS = 0 fallback behavior.
- [ ] duplicate suppression.
- [ ] fallback/additional RSGD paths.
- [ ] unusual DLC/plugin data.
- [x] shared capacity integration for Special/Everywhere/ATMO/families.

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
