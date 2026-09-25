# Backlog

## v1.0 Baseline

The standalone vanilla inorganic resource reproducer is complete within its
defined scope. The protected baseline is:

```text
canonical planet-wide validation: 1,444 / 1,444 exact
canonical mismatches:              0
generation errors:                 0
fresh CK + retail holdout:          10 / 10 exact
```

Completed work includes canonical data loading, exact MT19937 accounting,
effective-RSGD precedence, atmosphere and Everywhere prepopulation, Special and
Common selection, descendant traversal, family caching, shared identity
capacity, five-tree/shared-eight guards, guarded family fallback, occurrence and
assignment provenance, CK biome regressions, and full-corpus validation.
Brief 10C additionally completed Planet Directory ingestion, canonical extraction
metadata retention, cross-input coherence validation, IRES source provenance,
and the typed enriched accepted-occurrence view without changing generation.
Brief 10D completed the clean 35-column biome/atmosphere inorganic-resource
product, safe occurrence collapse, deterministic serialization, and source-hash
manifest without changing generation.
Brief 10E completed the stable production CLI: bare validated export, individual
input overrides, caller-relative output resolution, overwrite controls, optional
and stale-safe manifests, validate-only execution, concise error handling, and
quiet/verbose operational output. Oracle validation and diagnostic modes are not
part of the public runtime interface.

The earlier active items for unexplained shared-eight empty biomes, missing
post-guard reuse, atmosphere insertion ordering, and central-path v0.1 completion
are **SUPERSEDED / COMPLETED** by the v1.0 model and its regression suite. Their
historical evidence remains in `docs/experiments/` and
`docs/implementation-briefs/`.

## Evidence-Driven Maintenance

Only reopen algorithm work when new evidence falsifies or narrows the baseline.
A counterexample requires:

1. preserved trace, static evidence, or independently verified runtime output;
2. an explicit PROVEN, STRONG, or PROVISIONAL classification;
3. a focused regression that exposes the discrepancy;
4. a rule and implementation change that does not consult the oracle during
   generation;
5. full canonical and CK-regression revalidation.

No planet-specific exceptions or output-fitting heuristics.

## Genuine Open Work

### Version drift detection

- Record executable/data-version identity alongside future evidence captures.
- Detect changes in authoritative exports or recovered call-site behavior.
- Keep Creation Kit addresses distinct from any independently recovered retail
  `Starfield.exe` addresses.

### New falsifications and counterexamples

- Investigate RSCS-zero behavior if a body or direct trace makes it relevant.
- Preserve and investigate any future duplicate-insertion or unusual-data
  counterexample before changing the current proven corpus behavior.
- **OPEN, apparently unreachable and non-blocking:** if a Common guard were
  entered with Common entries present but an empty generated-family cache,
  current evidence does not define engine fallback behavior. Recovered control
  flow appears to prevent this state during normal execution.
- Test future game/DLC data only as a versioned corpus, not as an assumed
  extension of the current baseline.

### Consumer and export API hardening

- Maintain compatibility for the stabilized baseline CLI and serialized product.
- Add compatibility policy and contract tests if an external consumer appears.
- Improve explicit reporting for bodies with independently known channels but no
  PNDT/biome/effective-RSGD input.
- Design an expanded, provenance-rich diagnostic CLI/interface separately from
  the default product; no diagnostic mode exists yet. Retain single-planet RNG,
  family-cache, assignment, and oracle-difference detail without changing the
  stable production CLI.

### Wheel / PyPI distribution

- Package the four canonical production inputs correctly.
- Replace source-tree-relative data lookup with an installed-resource strategy.
- Support and verify clean non-editable/wheel execution, including CLI use from
  outside the repository.
- Add expanded package metadata appropriate to a published distribution.
- Decide whether to publish the package on PyPI.

### Planner integration

- Integrate through the typed generation result API, not CSV or CLI internals.
- Keep the standalone reproducer available as the regression oracle.
- Do not add planner behavior to this repository without an explicit brief.

### Optional release automation

- Create the approved annotated `v1.0.0` tag only after remediation, diff
  review, commit/sync, and the final release-readiness recheck.
- Decide later whether a GitHub Release adds value beyond public repositories
  plus the annotated tag; a GitHub Release is not required for v1.0.
- Add release automation only when an actual recurring release need exists.
- A Git tag or GitHub Release is not part of the v1.0 algorithm designation.

### Public repository metadata (owner action)

Authenticated GitHub repository settings are not available in the current
Codex environment. Before public release, the owner should:

- verify the default branch is `main`;
- verify the repository is not archived;
- set the description to `Deterministic Python reference implementation of
  Starfield's planetary inorganic resource-generation algorithm, validated
  across 1,444 bodies.`; and
- set topics to `starfield`, `modding`, `reverse-engineering`, `python`, `xedit`,
  and `bethesda`.

Do not change visibility as part of remediation; visibility remains a separate
coordinated owner decision.

## Permanently Out of Current Scope

- organic resources and flora/fauna spawning;
- surface vein geometry and cell-level placement;
- extractor placement mechanics;
- arbitrary mod/plugin behavior beyond current loader semantics;
- GUI, web server, database, or planner implementation;
- claims that CK function addresses are retail executable addresses.
