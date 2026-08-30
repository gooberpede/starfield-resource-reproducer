# Full Canonical Validation Baseline

## Scope

Brief 06 ran the unchanged production generator against every planet in the
intersection of:

```text
PlanetResourceGeneration_v5.csv planets
INTERSECT
planet-all-resources.csv bodies with at least one Inorganic row
```

Generation used only the static generation and IRES inputs. Oracle records were
supplied after each prediction completed and were used only for FormID comparison
and reporting. No generation, RNG, candidate-order, cache, Special, or Everywhere
rule changed during this validation pass.

## Dataset coverage

| Population | Count |
| --- | ---: |
| Generation planets | 1,444 |
| Oracle inorganic planets | 1,444 |
| Intersection validated | 1,444 |
| Generation-only | 0 |
| Oracle-only | 0 |

The complete run finished with zero per-planet generation errors. There are no
RSCS-zero planets in this corpus.

## Final-set baseline

| Metric | Count |
| --- | ---: |
| FINAL_SET_EXACT | 1,281 |
| Mismatches | 163 |
| Exact-match percentage | 88.71% |
| Missing-only planets | 14 |
| Unexpected-only planets | 148 |
| Missing-and-unexpected planets | 1 |
| Missing resource occurrences | 15 |
| Unexpected resource occurrences | 324 |
| Distinct missing FormIDs | 1 |
| Distinct unexpected FormIDs | 38 |

`FINAL_SET_EXACT` means predicted and canonical inorganic FormID sets are equal.
It does not imply `TRACE_EXACT`; most corpus planets have no live per-operation
trace.

## Mismatch signatures

| Signature | Planets |
| --- | ---: |
| UNEXPECTED_ROOT | 86 |
| ONE_UNEXPECTED_DESCENDANT | 48 |
| EVERYWHERE_ONLY_DISCREPANCY | 14 |
| UNEXPECTED_ONLY_OTHER | 14 |
| MIXED_OTHER | 1 |

All 15 missing occurrences are Water (`000083EC`). Fourteen planets are
Water-only missing cases. Xi Ophiuchi VII-a is the single mixed case: Water is
missing and Palladium is unexpected.

STRONG empirical pattern: unexpected-resource mismatches overwhelmingly occur
on resource-dense multi-biome predictions. Of the 163 mismatches, 139 predict
more than eight inorganic resources. Another nine predict eight where the oracle
contains seven. This is consistent with the previously observed possibility of
resource-slot/family limits or insertion-order effects, but it does not prove a
specific limit mechanism.

STRONG empirical separation: the Water-only failures align with the known
PROVISIONAL upstream Everywhere model and should not be merged causally with the
resource-density class.

## Distribution by biome count

| Biomes | Mismatches |
| ---: | ---: |
| 2 | 6 |
| 3 | 10 |
| 4 | 55 |
| 5 | 31 |
| 6 | 26 |
| 7 | 24 |
| 8 | 11 |

No single-biome planet mismatches the canonical final set.

## Distribution by effective RSGD

These are multi-label counts: one mismatched planet contributes once to each
distinct effective RSGD it encountered, so the values do not sum to 163.

| Effective RSGD | Mismatched planets |
| --- | ---: |
| OceanDefaultRes | 89 |
| FrozenBarrenDefaultRes | 80 |
| DesertSandDefaultRes | 78 |
| HillsNoLifeDefaultRes | 76 |
| MountainNoLifeDefaultRes | 69 |
| DesertRocksDefaultRes | 66 |
| VolcanicDefaultRes | 45 |
| MountainDefaultRes | 43 |
| FrozenBarrenDefaultRes02 | 42 |
| CanyonsDefaultRes | 40 |
| CrateredNoLifeDefaultRes | 29 |
| ArchipelagoDefaultRes | 27 |
| SavannaDefaultRes | 27 |
| HillsDefaultRes | 24 |
| ForestDeciduousRes | 23 |
| ForestConiferousRes | 21 |
| WetlandsDefaultRes | 18 |
| FrozenBarrenDefaultRes03 | 16 |
| ForestTropicalRes | 12 |
| UniqueFrozenNoLifeIndiciteRes | 1 |
| UniqueTablelandsCanyonsAldumiteRes | 1 |

## Distribution by selected Common root

These are also multi-label counts and describe roots selected anywhere on a
mismatched planet, not proven divergent roots.

| Root | FormID | Mismatched planets |
| --- | --- | ---: |
| Nickel | 000057CB | 102 |
| Uranium | 000057EB | 99 |
| Lead | 000057C1 | 90 |
| Iron | 000057C7 | 89 |
| Chlorine | 000057D5 | 87 |
| Copper | 000057CF | 70 |
| Argon | 000057EA | 59 |
| Aluminum | 000057D6 | 52 |

Seventy mismatches involve a family-cache hit. Two involve a real PNDT override:
Katydid III and Schrodinger II. These dimensions are clustering data only; neither
establishes cache or override defects.

## Representative follow-up planets

| Planet | FormID | Why it is useful |
| --- | --- | --- |
| Huygens VII-b | 0005DE15 | Two biomes, Water-only missing, no cache or PNDT override; a small Everywhere-boundary control. |
| Fermi VII-a | 0005DE3A | Four biomes, 9 predicted vs 8 canonical, one unexpected descendant (Ionic Liquids), with cache reuse. |
| Maal VIII | 0005DE6F | Four biomes, 8 predicted vs 7 canonical, one unexpected descendant (Alkanes), without cache reuse. This discriminates a simple fixed-eight interpretation from a broader slot rule. |
| Fermi III | 0005DE2D | Five biomes, 9 predicted vs 8 canonical, one unexpected Common root (Nickel), without cache reuse. |
| Bohr III | 0005DDF2 | Four biomes, 10 predicted vs 8 canonical, two unexpected descendants, with repeated-root cache reuse. |
| Katydid III | 0005DE7D | Four biomes, PNDT override, 9 predicted vs 8 canonical, one unexpected descendant (Tantalum). |
| Schrodinger II | 0005E0B5 | Four biomes, PNDT override, 9 predicted vs 8 canonical, one unexpected Common root (Nickel). |

## Recommended next investigation

Brief 07 should target the resource-density/slot and insertion-order class before
changing production. Start with Fermi VII-a and Maal VIII: both have a single
unexpected descendant and modest biome counts, but one predicts nine resources
against an eight-resource oracle while the other predicts eight against seven.
Add Fermi III as the minimal root-level discriminator. The experiment should
recover whether the runtime stops adding resources, stops adding families,
reserves a slot for a category, or applies duplicate/insertion behavior at a
specific point in the shuffled biome sequence.

The Everywhere insertion path should remain a separate investigation using
Huygens VII-b. Do not hard-code Water or combine that model boundary with the
resource-density hypothesis.

## Artifacts and reproducibility

Machine-readable report:

```text
validation/full-canonical-mismatches.csv
```

The report contains deterministic rows ordered by PlanetFormID. Multi-value
FormID cells are semicolon-separated in stable order. Two complete validation
runs produced identical per-planet predictions, classifications, aggregate
counts, and CSV content. The measured production validation runtime was about
1.5 seconds per run on the implementation host; test-suite determinism checks
run the corpus twice.
