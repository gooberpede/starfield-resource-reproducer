# v1.0 Validation Baseline

## Purpose

This document freezes the evidence baseline supporting the Starfield Resource
Reproducer v1.0 algorithm/model designation. It records observed outcomes without
turning validation data into generation inputs.

## Defined Scope

v1.0 reproduces vanilla Starfield inorganic planetary-resource generation from
the current authoritative static corpus. It covers PNDT/BIOM/effective-RSGD
inputs, IRES hierarchy, effective atmosphere, MT19937 state evolution, biome
shuffle, Everywhere, Special, Common roots, descendants, family caching, the
five-tree and shared-eight guards, guard fallback, provenance, biome-local
assignment, and planet-wide membership.

It does not cover organics, flora/fauna spawning, extractor placement, resource
vein geometry, arbitrary mods/plugins or future executables, or retail function
address equivalence with Creation Kit addresses.

## Canonical Inputs and Oracle Boundary

- `planet-resource-generation.csv`: authoritative
  PNDT/BIOM/effective-RSGD/RSCS input.
- `ires-hierarchy.csv`: authoritative IRES rarity and child graph.
- `planet-atmospheric-resources.csv`: authoritative effective
  atmospheric inorganic-resource export for this corpus.
- `planet-directory.csv`: canonical PNDT body-directory source export, staged
  for later ingestion and not used by the v1.0 model.
- `planet-all-resources.csv`: canonical planet-wide validation oracle for the
  CK/RSGD-visible inorganic channel used by the validator.

The oracle is not a complete final planetary-resource oracle because it is
proven to omit at least some atmosphere-derived resources. It is never consulted
during generation. Its exact upstream `SurveyAggregator` semantic contract
remains unresolved; that qualification is non-blocking for v1.0.

## Canonical Validation

```text
1,444 / 1,444 exact
0 mismatches
0 errors
```

The full test suite at baseline was:

```text
138 passed
```

This test count records the evidence run and is not a contractual assertion.

## Targeted Creation Kit Regression Bodies

The established discovery and regression set includes:

```text
Kreet
Callisto
Maal VIII
Fermi VIII-b
Titan
Algorab I
Mimas
Bara VII-d
Indum IV-d
Zeta Ophiuchi I
Jaffa VII-b
Pyraas VIII-a
```

These bodies exercise known pathological and discriminating paths, including
Special ordering, atmosphere/identity collisions, zero-candidate RNG, descendant
index conversion, both Common guards, matched/general fallback, bound-one
fallback draws, family origin, and biome-index occurrence association. They are
discovery/regression cases, not independent holdouts.

All tracked CK biome regressions are exact.

## Fresh Holdout Validation

The fresh sample deliberately used bodies that were not part of algorithm
discovery or earlier detailed validation:

```text
Vesta             - Lunara
Niira             - Narion
Eridani IV        - Eridani
Cassiopeia IV-a   - Eta Cassiopeia
Cassiopeia II-a   - Eta Cassiopeia
Zosma V-a         - Zosma
Eridani III-b     - Eridani
Luyten's Rock     - Luyten's Star
Bardeen V-d       - Bardeen
Ka'zaal           - Nirah
```

Observed result:

```text
10 / 10 exact
```

For every holdout body:

- atmosphere matched where present;
- terrestrial resources occurred in exactly the predicted CK biomes;
- retail planetary scans showed exactly the forecast resource set.

No untracked per-body values are inferred here.

## Volii Alpha Input-Boundary Negative Control

**V1.0 INPUT-BOUNDARY RULE / VALIDATED MODEL BEHAVIOR**

```text
Volii Alpha is absent from planet-resource-generation.csv
atmospheric Benzene + Water are available independently
no biome assignment is fabricated
```

This validates the input boundary, not terrestrial generation output. Missing
PNDT/biome/effective-RSGD input means biome-local generation is unknown or
unsupported from the current inputs; it does not mean an empty biome result.
Independently available origin channels can still be reported. This is not
evidence about Volii Alpha's actual terrestrial biome allocation and is not
classified as a recovered native engine rule.

## Evidence Boundary

Creation Kit function addresses and control flow are PROVEN for the live-traced
CK Galaxy View Apply path. Retail validation independently corroborates predicted
outputs. The CK addresses have not been independently traced in
`Starfield.exe`, so this baseline makes no retail address-equivalence claim.

## Falsifiability Policy

v1.0 is considered complete within its defined scope because the model
reproduces the full canonical corpus and independent CK/retail holdout samples.
Future contradictory evidence should be treated as a falsification/regression to
investigate, not hidden by heuristics or oracle patches.

No planet-specific exceptions are permitted.
