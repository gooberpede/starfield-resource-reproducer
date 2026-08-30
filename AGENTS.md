# AGENTS.md

## Purpose

This repository is a research-grade reference implementation of Starfield's planetary resource-generation algorithm.

The immediate goal is to reproduce, from extracted static game data and a planet's Resource Creation Seed (RSCS), the resource distributions observed in the Creation Kit and in verified runtime-derived data.

This is **not yet** the outpost planner, a game mod, or a user-facing application. Keep the reproducer small, transparent, deterministic, testable, and easy to inspect.

## Working Relationship

Development is split deliberately:

- **ChatGPT discussion:** architecture, reverse-engineering interpretation, domain rules, experiment design, and implementation briefs.
- **Codex:** coding, tests, refactors, repository maintenance, and implementation from approved briefs.
- **User:** runs Creation Kit/x64dbg/game-side experiments, supplies traces and extracted datasets, and approves architectural changes.

When an implementation brief exists, treat it as the authoritative scope for that task.

Do not silently broaden a brief.

## Source of Truth

Use these inputs as distinct sources with distinct roles:

1. `PlanetResourceGeneration_v5.csv`
   - canonical static PNDT -> biome -> effective-RSGD input data;
   - preserves unsigned RSCS, PNDT biome order, RSGD provenance, RSGD resource order, and generation percentages.

2. `Starfield_IRES_Hierarchy.csv`
   - canonical static IRES rarity and child-resource graph.

3. `planet-all-resources.csv`
   - **canonical verified planet/resource output oracle**;
   - sourced from the game/runtime and used to validate reproducer output.

`Starfield_InorganicResources_Canonical.csv` is **deprecated**. Do not use it for validation, fixtures, expected results, or implementation decisions.

## Evidence Discipline

The project distinguishes:

- **Proven:** directly supported by live trace, decompilation/static data, or verified runtime output.
- **Strongly supported:** multiple independent observations agree, but no direct proof of universality yet.
- **Hypothesis / provisional:** useful working assumption requiring validation.

Do not silently upgrade a hypothesis to a fact.

If code must implement a provisional rule, document it in code and tests as provisional and make it easy to replace.

## Current Proven Core Rules

Implementations must preserve the currently recovered behavior unless a later brief explicitly changes it:

- PNDT `RSCS` is used as an unsigned 32-bit MT19937 seed.
- PNDT biome entries are copied in `BiomeIndex` order into the working list.
- The working biome list is deterministically shuffled before resource generation.
- Biomes are processed sequentially in shuffled order using the same evolving PRNG state.
- A non-null PNDT biome Resource Generation reference overrides BIOM `RNAM`.
- Otherwise BIOM `RNAM` supplies the effective RSGD.
- RSGD resource-array order is semantically significant.
- Rarity/category mapping is:
  - 0 Common
  - 1 Uncommon
  - 2 Rare
  - 3 Exotic
  - 4 Unique
  - 5 Special
  - 6 Everywhere
- Water is `Everywhere` and is populated upstream of the per-biome generator observed at `FUN_1415DCFB0`.
- Helium-3 is `Special` and is handled by the per-biome Special pass.
- Common-family/root selection is cumulative weighted selection over eligible Common entries in RSGD order.
- Do not normalize RSGD root weights.
- A newly selected Common root is emitted unconditionally.
- Descendant levels 1..4 are processed in rarity order.
- At each descendant level, structural candidate choice and emission/inclusion are distinct.
- Structural traversal continues through the selected candidate even if that resource is not emitted.
- Candidate selection consumes an RNG draw even when the candidate set contains exactly one element.
- A previously generated Common family configuration is reused by later biomes that select that family rather than rerolling its descendants.

See `docs/DOMAIN-RULES.md` for the maintained domain specification.

## Engineering Priorities

In order:

1. correctness;
2. deterministic reproducibility;
3. traceability/diagnostics;
4. simple code;
5. performance.

This dataset is small. Prefer clear code over premature optimization.

## Architecture Rules

- Keep CSV parsing/loading separate from generation logic.
- Keep PRNG behavior isolated behind a small interface.
- Keep domain objects independent of pandas/dataframe APIs.
- Keep canonical validation separate from prediction.
- Do not hard-code individual planets as algorithmic special cases.
- Do not hard-code unique resources such as Vytinium into generation logic when the data-driven RSGD/IRES mechanism explains them.
- Prefer immutable/value-style domain objects where practical.
- Use FormIDs as stable identities; names are for display and diagnostics.

## Testing Rules

Every behavioral change should include or update tests.

Maintain worked-case regression tests for at least:

- Oberon — simple Nickel root-only control and Water/Everywhere behavior.
- Mimas — Nickel + Palladium; skipped Cobalt/Platinum structural traversal.
- Decaran VII-b — PNDT override, Uranium family, Vytinium, Special/Helium-3.
- Kreet — three-biome PNDT-order -> deterministic shuffle -> per-biome generation.

Tests should assert intermediate decisions where possible, not only final sets.

Full-dataset validation should compare predictions against `planet-all-resources.csv`.

## Diagnostics

The reproducer is a research instrument.

For a single-planet diagnostic run, expose enough detail to answer:

- initial biome order;
- shuffled biome order;
- effective RSGD per biome;
- RNG draw position/value where known;
- Special selection;
- Common/root candidates and weights;
- selected root;
- descendant structural candidate(s);
- inclusion result;
- emitted resources;
- family-cache hits;
- final predicted set;
- canonical set;
- missing/unexpected resources.

Do not hide useful intermediate state behind opaque abstractions.

## Scope Control

Do not add without an explicit brief:

- GUI;
- web server;
- database;
- planner integration;
- game/mod integration;
- packaging/distribution machinery;
- multiprocessing;
- generalized plugin frameworks.

The first milestone is a trustworthy standalone reproducer.

## Documentation

When behavior changes, update the relevant documentation in the same change:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DOMAIN-RULES.md`
- `docs/BACKLOG.md`

Do not rewrite historical evidence merely to make documentation look cleaner. If a recovered rule changes, record the correction explicitly.

## Commits

Prefer small, reviewable commits.

Suggested conventional prefixes:

- `feat:` new reproducer behavior
- `fix:` correctness repair
- `test:` tests/fixtures
- `docs:` documentation
- `refactor:` no intended behavior change
- `chore:` repository/tooling maintenance

A commit should not mix unrelated reverse-engineering assumptions and large refactors.
