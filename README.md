# Starfield Resource Reproducer

A deterministic reference implementation of vanilla Starfield's inorganic
planetary-resource generation algorithm.

## Status

**Algorithm/model status: v1.0**

Within its defined scope, the model reproduces the complete canonical corpus:

```text
1,444 / 1,444 exact
0 mismatches
0 errors
```

It also reproduces all established Creation Kit biome regressions and a fresh
ten-body holdout checked independently in the Creation Kit and retail game. The
durable evidence record is [docs/V1-VALIDATION-BASELINE.md](docs/V1-VALIDATION-BASELINE.md).

This status describes the validated algorithm and model. It does not imply that
a Git tag or GitHub release exists.

## Scope

The v1.0 reproducer covers:

- PNDT resource seeds and ordered biome entries;
- BIOM and effective per-biome RSGD selection;
- the IRES rarity and child-resource hierarchy;
- effective atmospheric inorganic resources;
- MT19937 state evolution and deterministic biome shuffle;
- Everywhere, Special, Common-root, and descendant generation;
- planet-wide family caching and biome-local family assignment;
- the five-tree and shared-eight guards, including guarded fallback;
- resource identity, occurrence provenance, and family-origin provenance;
- planet-wide final membership and biome-centric reporting.

It does not model organic resources, flora/fauna spawning, resource-vein
geometry, extractor placement, arbitrary mod/plugin behavior, or arbitrary
future executable versions. Creation Kit function addresses in the evidence are
specific to the live-traced CK Galaxy View Apply path; retail results corroborate
the outputs but do not establish address equivalence in `Starfield.exe`.

This repository remains a small research-grade reference implementation and
regression oracle, not an outpost planner, game mod, GUI, or web service.

## Canonical v1.0 Inputs

The canonical source inputs and validation oracle have deliberately different
roles:

- `data/planet-resource-generation.csv` is the authoritative
  PNDT/BIOM/effective-RSGD/RSCS input. It preserves PNDT biome order, RSGD
  provenance, RSGD resource order, and generation percentages.
- `data/ires-hierarchy.csv` is the authoritative IRES rarity and
  child-resource graph, including parent and child source-plugin provenance.
- `data/planet-atmospheric-resources.csv` is the authoritative effective
  atmospheric inorganic-resource export for the current corpus.
- `data/planet-directory.csv` is the canonical PNDT body directory. It is
  the 15-column v4 export, ingested independently and indexed by Planet FormID.
  Its Solar Array power, Wind Turbine power, and Planetary Habitation rank are
  retained as directory metadata only; directory presence does not imply that
  either generation channel exists.
- `data/planet-all-resources.csv` is the canonical planet-wide validation oracle
  for the CK/RSGD-visible inorganic channel used by the validator. It is not a
  complete final planetary-resource oracle because it omits at least some
  atmosphere-derived resources.

`Starfield_InorganicResources_Canonical.csv` is deprecated and must not be used
for validation, fixtures, expected results, or generation decisions.

The generator never consults canonical/oracle output. Validation compares the
independently generated RSGD/CK-visible channel with the filtered inorganic
oracle only after generation is complete.

The extraction paths and exporter-derived classifications for the maintained
source files are documented in
[docs/CANONICAL-XEDIT-EXPORTS.md](docs/CANONICAL-XEDIT-EXPORTS.md).

`ProjectData` retains each production input's extraction timestamp and row
count outside row-level domain objects. Loading also validates body and resource
identity coherence across the four production inputs before generation begins.

After generation, `build_enriched_occurrences` projects accepted state into a
typed body/location/resource/origin view. The stable resource origins are
`ATMOSPHERE`, `EVERYWHERE`, `SPECIAL`, `COMMON_ROOT`, and `DESCENDANT`; effective
RSGD relationship evidence remains `BIOM`, `PNDT`, or `PNDT_AND_BIOM` (the typed
name for source value `PNDT+BIOM`). Common-family rows expose their root and the
original family-generation biome independently of the current assignment
mechanism. The default exporter safely collapses this richer internal view to
the consumer-facing `Planet x Location x Resource` grain documented in
[docs/BIOME-INORGANIC-RESOURCES.md](docs/BIOME-INORGANIC-RESOURCES.md).

## Effective RSGD Rule

The sources are selected, never merged:

```text
if PNDT biome Resource Generation != NULL:
    EffectiveRSGD = PNDT override
else:
    EffectiveRSGD = BIOM.RNAM
```

## Generation Order

```text
effective atmosphere resources
    -> record atmospheric identities in shared planet state
    -> Everywhere/category-6 pre-pass over all effective RSGDs
    -> construct biome work objects in PNDT BiomeIndex order
    -> deterministic MT19937 biome shuffle
    -> process each shuffled biome:
         Special/category-5 selector
         -> record selected Special immediately
         -> five-Common-tree guard
         -> shared-eight guard
         -> normal Common/category-0 selector when neither guard fires
            or guarded cached-family fallback when a guard fires
```

Normal Common selection either creates a new family configuration or reuses the
planet-wide cached configuration for that root. Guard fallback prefers cached
families whose roots occur in the current effective RSGD; otherwise it selects
from all cached families. An RSGD with no Common roots receives no Common-family
assignment.

Descendants are processed Uncommon -> Rare -> Exotic -> Unique. Structural
traversal continues through an omitted selected candidate. Resource identity and
occurrence provenance remain separate, as do family-configuration origin and the
mechanism by which a later biome receives that family.

The five assignment mechanisms are:

```text
NEW_FAMILY
NORMAL_CACHE_REUSE
GUARD_MATCHED_FALLBACK
GUARD_GENERAL_FALLBACK
NO_COMMON_ASSIGNMENT
```

See [docs/DOMAIN-RULES.md](docs/DOMAIN-RULES.md) for evidence classifications and
the complete recovered rules.

## RNG Primitives

The implementation preserves separate semantic operations even when arithmetic
is shared:

1. biome-shuffle bounded integer: rejection/modulo, with rejected attempts
   consuming MT words;
2. probability float: binary32 conversion and `0.99999` scale;
3. Special/Common weighted selector: one probability draw before category
   enumeration, including zero/one/100-percent candidate cases;
4. descendant candidate index: float32-scaled index from one probability draw;
5. guard-fallback family index: the same arithmetic shape as descendant indexing,
   but separate API and event provenance, including a draw at bound one.

## Missing Generation Inputs

**V1.0 input-boundary rule / validated model behavior:**

The reproducer does not fabricate biome assignments. A body absent from the
PNDT/biome/effective-RSGD corpus has unknown or unsupported biome-local
generation, not an empty terrestrial result. Independently available origin
channels can still be reported; Volii Alpha, for example, has atmospheric
Benzene and Water but no fabricated biome assignment. This validates the
reproducer's epistemic/input boundary, not Volii Alpha's actual terrestrial
biome allocation or a native engine rule.

## Usage

Create a Python 3.12 environment and install the project with its test tools:

```bash
python -m pip install -e ".[dev]"
```

Run the validated production pipeline:

```bash
starfield-resource-reproducer
```

The bare command loads and validates the four canonical production inputs,
generates the terrestrial results, builds and validates the clean product, and
writes `./output/biome-inorganic-resources.csv`. Default inputs are resolved
from the project/package `data/` location independently of the caller's current
directory; default output is deliberately relative to the caller. If `./output/`
cannot be used, the command falls back to `./biome-inorganic-resources.csv`.

Common forms include:

```text
starfield-resource-reproducer
starfield-resource-reproducer --manifest
starfield-resource-reproducer --output C:\Exports
starfield-resource-reproducer --output C:\Exports\my-resources.csv --manifest
starfield-resource-reproducer --no-overwrite
starfield-resource-reproducer --validate-only
```

`--output` accepts an existing or new directory, or an explicit `.csv` file.
Overwrite is the default; `--no-overwrite` fails without prompting. A manifest
is off by default and can be requested with `--manifest`; an existing sibling
manifest is always refreshed when its CSV is replaced. `--validate-only` runs
the same complete build and validation path but writes nothing. `--quiet` and
`--verbose` control operational messages and are mutually exclusive.

All four inputs can be overridden independently (relative paths are resolved
from the caller's current directory):

```text
starfield-resource-reproducer \
  --resource-generation-file data/planet-resource-generation.csv \
  --resource-tree-file data/ires-hierarchy.csv \
  --atmospheric-resources-file data/planet-atmospheric-resources.csv \
  --planet-directory-file data/planet-directory.csv
```

The production CLI never loads `planet-all-resources.csv`. Oracle comparison
remains an internal research regression, and diagnostic CLI modes are deferred.

Run the test suite:

```bash
python -m pytest
```

The v1.0 evidence run recorded 138 passing tests. That number is a historical
baseline, not a contractual assertion; the suite may grow.

## Worked Regression Cases

- Oberon: Nickel root-only control plus Water/Everywhere behavior.
- Mimas: Nickel and Palladium, with omitted Cobalt and Platinum retained in the
  structural traversal.
- Decaran VII-b: PNDT override, Uranium family, Vytinium, and Special/Helium-3.
- Kreet: PNDT-order construction, deterministic three-biome shuffle, and exact
  biome-local family outputs.
- Algorab I and the guarded fallback cases: precise descendant, capacity,
  assignment, origin, and RNG regressions.

## Project Documentation

- [AGENTS.md](AGENTS.md): protected-baseline instructions for coding agents.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): implemented decomposition and
  data boundaries.
- [docs/DOMAIN-RULES.md](docs/DOMAIN-RULES.md): recovered behavior and evidence
  status.
- [docs/CANONICAL-XEDIT-EXPORTS.md](docs/CANONICAL-XEDIT-EXPORTS.md): maintained
  source-export provenance contracts.
- [docs/BIOME-INORGANIC-RESOURCES.md](docs/BIOME-INORGANIC-RESOURCES.md): default
  consumer dataset and manifest contract.
- [docs/V1-VALIDATION-BASELINE.md](docs/V1-VALIDATION-BASELINE.md): v1.0 evidence
  baseline.
- [docs/BACKLOG.md](docs/BACKLOG.md): genuine post-v1.0 work.
- [docs/IMPLEMENTATION-WORKFLOW.md](docs/IMPLEMENTATION-WORKFLOW.md): brief-driven
  workflow and implementation history.

## Falsifiability

v1.0 is considered complete within its defined scope because the model
reproduces the full canonical corpus and independent CK/retail holdout samples.
Future contradictory evidence should be treated as a falsification/regression to
investigate, not hidden by heuristics or oracle patches. Planet-specific
algorithm exceptions are not acceptable.
