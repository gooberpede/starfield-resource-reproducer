# Brief 08A — Correct Everywhere/category-6 handling and rerun full canonical validation

## Objective

Apply the reproducer correction established by the Fermi VIII-b and Kreet live traces:

> `FUN_141548920` accepts RSGD resource entries whose referenced IRES category is `6` (`Everywhere`) without consulting the DNAM Everywhere chance field and without consuming RNG.

Then rerun the full 1,444-body canonical validation corpus and report the new residual mismatch set.

## Evidence basis

### PROVEN LIVE — Fermi VIII-b / OceanDefaultRes

`OceanDefaultRes` contains exactly one RSGD resource entry:

- Water `000083EC`
- IRES rarity/category: Everywhere / 6
- Biome/Common Chance to Appear: 100
- Biome/Everywhere Chance to Appear: 0

The live trace through `FUN_141548920` showed:

1. the helper reads the RSGD resource-entry count and iterates the normal resource-entry array;
2. the OceanDefaultRes count is `1`, but there is no `count == 1` shortcut;
3. for the Water entry, the helper tests the referenced IRES category at `+0x2F8`;
4. category `6` passes;
5. the helper reads Water FormID `000083EC` from IRES `+0x70`;
6. Water is written to the biome/work-object category-6 field (`+0x68`);
7. Water is passed to the shared resource-state append path;
8. no DNAM Everywhere chance field is read;
9. no probability/RNG operation occurs in this category-6 helper path.

Therefore the current reproducer gate requiring positive `BiomeEverywhereChance` is incorrect.

### PROVEN LIVE — Kreet control

Kreet has PNDT-level effective-RSGD overrides for two biomes:

- `MountainDefaultRes_Kreet` → Iron / Common / 100
- `VolcanicDefaultRes_Kreet` → Lead / Common / 100

A live `FUN_141580660` trace on a one-entry Common RSGD showed that the ordinary category-0 selector still:

1. performs its normal MT19937 probability draw;
2. invokes the ordinary cumulative chance scanner;
3. selects the sole Common resource through normal weighted-selector machinery.

There is no generic one-entry-RSGD bypass.

This falsifies H4 as a general rule and confirms that the Fermi behavior is category-driven, not entry-count-driven.

## Required code change

Locate the category-6 / Everywhere discovery logic, currently expected to contain a condition equivalent to:

```python
if (
    entry.resource_rarity is not GenerationRarity.EVERYWHERE
    or entry.everywhere_chance <= 0
):
    continue
```

Change it so category-6 eligibility depends on resource category only:

```python
if entry.resource_rarity is not GenerationRarity.EVERYWHERE:
    continue
```

Do **not** replace the removed gate with another chance field, weight, fallback, or heuristic.

## Semantics to preserve

For category 6 / Everywhere:

- scan the effective RSGD's ordinary resource-entry list in stable authored order;
- accept entries whose referenced IRES rarity/category is Everywhere / 6;
- do not consult `BiomeEverywhereChance`;
- do not consult `BiomeCommonChance` as a substitute;
- do not consume RNG;
- preserve existing shared resource-capacity and duplicate/provenance behavior exactly as currently implemented;
- preserve the existing pre-main-generation ordering:
  1. atmosphere
  2. Everywhere/category 6
  3. shuffled per-biome generator
     - Special/category 5
     - Common/category 0
     - descendants.

## Explicit non-goals

Do not change:

- atmosphere loading or ATMO inheritance handling;
- Special/category-5 selector behavior;
- Common/category-0 selector behavior;
- descendant selection or inclusion mechanics;
- MT19937 implementation or RNG call sequence;
- biome shuffle;
- PNDT RSGD override semantics;
- shared resource capacity logic;
- duplicate-slot/provenance semantics;
- Common-family cache behavior;
- five-family guard interpretation/implementation;
- validation oracle semantics;
- the two known atmospheric/Common Chlorine collision cases;
- Bara VII-d handling.

Do not add any Water-specific, Ocean-specific, single-entry-RSGD, fallback, or "ensure every biome has a resource" rule.

## Tests

Add or update focused tests that prove the corrected category-6 behavior.

At minimum:

1. A synthetic/equivalent effective RSGD entry with:
   - rarity/category = Everywhere;
   - `everywhere_chance = 0`;
   - valid resource FormID;
   must still be discovered/emitted by the category-6 pre-pass.

2. The same test should establish that changing `everywhere_chance` between 0 and a positive value does not alter category-6 eligibility.

3. Preserve Maal VIII regression coverage.

4. Add or preserve an OceanDefaultRes/Fermi-style regression if the fixture architecture makes that straightforward:
   - Water / Everywhere;
   - Everywhere chance 0;
   - Water still emitted.

5. Preserve all existing tests for Special, Common, descendants, PRNG, atmosphere, provenance, capacity, and PNDT overrides.

Do not write tests that merely special-case Water or `OceanDefaultRes`; the implementation rule must remain generic to category 6.

## Documentation / comments

Update any code comment or nearby documentation that currently says category-6 exact selection arithmetic is OPEN in a way that implies a positive chance gate is retained.

Use evidence-disciplined wording such as:

> **PROVEN LIVE:** `FUN_141548920` scans effective-RSGD resource entries for IRES category 6 (`Everywhere`) and emits matching entries without consulting DNAM Everywhere chance or consuming RNG.

Keep the claim scoped to the Creation Kit Galaxy View Apply path unless the surrounding document already makes that scope explicit.

Also record:

> **COUNTERFACTUAL / FALSIFIED:** a one-entry effective RSGD is not generically auto-selected; Kreet's one-entry Common RSGD still uses the ordinary category-0 weighted selector and consumes its normal RNG draw.

## Full-corpus validation

After the code/tests pass, rerun the exact full canonical validation workflow used for the current 1,444-body report.

Report:

- total population;
- exact matches;
- mismatches;
- errors;
- exact-match percentage;
- before/after comparison against the current 07B baseline:
  - 1,426 / 1,444 exact
  - 18 mismatches
  - 98.75%.

Generate/update the normal validation artifacts, including the full mismatch CSV.

## Residual analysis

After the rerun, inspect the remaining mismatch rows and report their identities and signatures.

Expected hypothesis only — do not force the implementation to achieve this result:

- the 15 `OceanDefaultRes` Water-only residuals should disappear;
- likely remaining:
  - Zeta Ophiuchi I — unexpected Chlorine, ATMO/Common collision;
  - Indum IV-d — unexpected Chlorine, ATMO/Common collision;
  - Bara VII-d — unexpected Nickel, likely sixth distinct Common-family / five-family guard issue.

If the result differs, report the actual residuals without adding compensating heuristics.

## Deliverable

Return:

1. concise implementation summary;
2. tests run and result;
3. full-corpus before/after validation summary;
4. exact residual mismatch list after the rerun;
5. files changed;
6. any evidence/documentation wording changed.

Do not commit unless explicitly requested.
