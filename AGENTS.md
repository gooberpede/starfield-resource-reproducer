# AGENTS.md

## Purpose

This repository is a research-grade reference implementation of Starfield's planetary resource-generation algorithm.

The immediate goal is to reproduce, from extracted static game data and a planet's Resource Creation Seed (RSCS), the resource distributions observed in the Creation Kit and in verified runtime-derived data.

This is not the outpost planner, a game mod, or a user-facing application. The
algorithm/model is a protected v1.0 baseline within its defined scope. Keep the
reproducer small, transparent, deterministic, testable, and easy to inspect.

## Working Relationship

Development is split deliberately:

- **ChatGPT discussion:** architecture, reverse-engineering interpretation, domain rules, experiment design, and implementation briefs.
- **Codex:** coding, tests, refactors, repository maintenance, and implementation from approved briefs.
- **User:** runs Creation Kit/x64dbg/game-side experiments, supplies traces and extracted datasets, and approves architectural changes.

When an implementation brief exists, treat it as the authoritative scope for that task.

Do not silently broaden a brief.

## Baseline Production CLI

The public v1.0 command line is a production interface, not an oracle-validation
or reverse-engineering diagnostic interface. A bare invocation loads the four
canonical production inputs from the project/package `data/` location, validates
and generates the clean product, and writes relative to the caller's current
working directory. Validation is always enabled; `--validate-only` suppresses
artifact writing rather than adding extra validation. The runtime CLI must not
load `planet-all-resources.csv`, and diagnostic modes remain deferred.

## xEdit Script Working Copies

xEdit scripts may exist in two locations with distinct roles:

- `D:\tools\xEdit.4.1.5p\Edit Scripts\`
  - the active xEdit installation's script directory;
  - use this location when the user asks to inspect, run, or modify installed xEdit scripts.

- `D:\Projects\starfield-resource-reproducer\xedit-scripts\`
  - the repository-maintained copy of relevant xEdit scripts;
  - preserves those scripts in Git for review and version history.

When asked to modify an installed `.pas` script:

1. Treat the copy under `D:\tools\xEdit.4.1.5p\Edit Scripts\` as the active xEdit working copy.
2. Apply the requested change there.
3. Copy the completed script into the repository's `xedit-scripts\` directory using the same filename.
4. Verify that the installed and repository copies are byte-for-byte identical.
5. Preserve valid UTF-8 and run the repository's required encoding and diff checks.

Do not modify installed or repository script copies unless the user explicitly
requests a change. Reading or comparing the scripts does not authorize edits.
Do not assume that editing the repository copy alone updates the active xEdit
installation.

## xEdit Script and Output Standards

These standards apply to newly created xEdit scripts and newly introduced output
files. Existing script and output filenames are legacy names and must not be
changed merely to conform to these standards. Rename an existing file only when
the user explicitly directs it.

### Script Filenames

A new script specific to a game or utility must use:

```text
<Game or Utility> - <Description>.pas
```

Examples:

```text
Starfield - Export Planet Atmospheric Resources.pas
Skyrim - Tree LOD files patcher.pas
NIF - Convert OBJ to NIF.pas
Oblivion - Export all scripts in xml format.pas
Fallout4 - Filter for precombined statics.pas
```

Use the established name or identifier for the game or utility as the prefix.
The spaced ` - ` between the prefix and description is the required structural
separator. Within the prefix and description, separate words with spaces rather
than hyphens or underscores.

A genuinely generic script that is not specific to a game or utility may omit
the prefix. Examples:

```text
Put master references in the same cell as overriding references.pas
Report masters.pas
Worldspace copy landscape area to another worldspace.pas
```

Do not use underscore-separated or hyphen-separated words. Do not encode a
version or revision number in the filename. For example, do not create:

```text
Starfield_ExportDomesticableNPCs.pas
Starfield_ExportPlanetBiomeOrganics_Enhanced.pas
Starfield_ExportPlanetDirectory_PNDTResourceGeneration.pas
Dump_Selected_Records_to_TSV_v2.pas
```

Version history belongs in Git or in appropriate internal metadata, not in the
script filename.

New installed scripts must also be retained under the repository's
`xedit-scripts\` directory using exactly the same filename. Follow the
byte-for-byte synchronization requirements in **xEdit Script Working Copies**.

### Output Location

By default, a new xEdit script must write generated output into the active
xEdit script directory:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\
```

Resolve the active `Edit Scripts` directory through the xEdit runtime where
practical; do not unnecessarily hard-code this workstation-specific absolute
path into a portable script.

Use another output location only when the user or an authoritative
implementation brief explicitly directs it.

Generated output remains in the active `Edit Scripts` directory by default. Do
not copy it into the repository unless the user or an authoritative brief
explicitly requires a repository copy.

### Output Filenames

New output filenames must:

- use lowercase;
- separate words with a single hyphen;
- contain no spaces or underscores;
- omit game or utility prefixes unless one is needed for clarity;
- contain no version or revision number; and
- use an extension that accurately represents the content.

The filename stem should follow this form:

```text
lowercase-words-separated-by-hyphens
```

Acceptable examples:

```text
planet-all-resources.csv
inorganic-resource-dictionary.csv
abbreviations.csv
```

Do not create names such as:

```text
PlanetResourceGeneration_v5.csv
Starfield_PlanetBiomeOrganics_Enhanced.csv
Akila-v5_PlanetResourceGeneration.csv
```

Numbers that are intrinsic to the subject may be used when necessary, but do
not use numbers as filename versions or revisions.

Use content-appropriate extensions:

- `.csv` for comma-separated tabular data;
- `.tsv` for tab-separated tabular data;
- `.txt` for unstructured plain text; and
- another established extension when the output has another defined format.

Choose the output structure and field formatting appropriate to the task unless
the user or an authoritative implementation brief specifies them.

Use a stable output filename. The user or implementation brief should determine
whether an existing output is replaced, rejected, or confirmed before overwrite.

Do not rename an existing output merely to make it conform to this standard.
When extending an existing script, preserve its established output filenames
unless the user explicitly directs a rename. Any genuinely new output introduced
by that change should follow this standard.

## Source of Truth

Use these inputs as distinct sources with distinct roles:

1. `planet-resource-generation.csv`
   - canonical static PNDT -> biome -> effective-RSGD input data;
   - preserves unsigned RSCS, PNDT biome order, RSGD provenance, RSGD resource order, and generation percentages.

2. `ires-hierarchy.csv`
   - canonical static IRES rarity and child-resource graph.

3. `planet-atmospheric-resources.csv`
   - authoritative effective atmospheric inorganic-resource export for the
     current corpus.

4. `planet-directory.csv`
   - canonical PNDT body-directory source export;
   - ingested as independent canonical body metadata keyed by Planet FormID;
   - canonical v4 Solar Array power, Wind Turbine power, and Planetary
     Habitation rank remain metadata and are not inorganic-generation inputs.

5. `planet-all-resources.csv`
   - **canonical verified planet/resource output oracle** for the CK/RSGD-visible
     inorganic channel used by validation;
   - sourced from the game/runtime and used to validate reproducer output;
   - not a complete final planetary-resource oracle because it omits at least
     some atmosphere-derived resources.

`Starfield_InorganicResources_Canonical.csv` is **deprecated**. Do not use it for validation, fixtures, expected results, or implementation decisions.

## Evidence Discipline

The project distinguishes:

- **Proven:** directly supported by live trace, decompilation/static data, or verified runtime output.
- **Strongly supported:** multiple independent observations agree, but no direct proof of universality yet.
- **Hypothesis / provisional:** useful working assumption requiring validation.

Do not silently upgrade a hypothesis to a fact.

If code must implement a provisional rule, document it in code and tests as provisional and make it easy to replace.

## Protected v1.0 Baseline

The model reproduces the full 1,444-body canonical corpus and independent
Creation Kit/retail holdouts. Preserve these constraints:

1. Do not change the algorithm without preserved evidence and an explicit
   evidence classification.
2. Never consult canonical/oracle data during generation. Oracle comparison
   begins only after an independent prediction exists.
3. Keep resource identity/capacity, occurrence provenance, family origin, and
   biome assignment mechanism distinct.
4. Keep the biome-shuffle integer helper, probability conversion,
   Special/Common weighted selector, descendant index, and guard-fallback index
   as distinct RNG primitives/semantics.
5. Do not guess missing PNDT/biome/effective-RSGD input or translate it into an
   empty terrestrial result. Independently known channels may still be reported.
6. Creation Kit function addresses are proven only for the live-traced CK Galaxy
   View Apply path. Do not silently relabel them as retail `Starfield.exe`
   addresses.
7. A future counterexample requires preserved evidence, an evidence
   classification, a focused regression, and only then an implementation change
   followed by full revalidation.
8. Retain all UTF-8 and mojibake safeguards below.

Future contradictory evidence is a falsification/regression to investigate, not
a reason for a heuristic, oracle patch, or planet-specific exception.

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
- Effective atmosphere resources are recorded before the Everywhere pre-pass.
- The Everywhere pre-pass scans every effective RSGD before biome shuffle/main
  generation.
- A selected Special is recorded before the five-tree and shared-eight Common
  guards.
- After five distinct cached Common-family configurations, the five-tree guard
  suppresses normal Common selection and enters fallback.
- The shared resource-ID state is guarded at count eight; the shared-eight guard
  suppresses normal Common selection and enters fallback.
- **STRONG / validated model:** occupancy is deduplicated by resource FormID
  across modeled provenance origins. Do not promote this to universal proof for
  every collision at every engine insertion site without direct evidence.
- Common-family/root selection is cumulative weighted selection over eligible Common entries in RSGD order.
- Do not normalize RSGD root weights.
- A newly selected Common root is emitted unconditionally.
- Descendant levels 1..4 are processed in rarity order.
- At each descendant level, structural candidate choice and emission/inclusion are distinct.
- Structural traversal continues through the selected candidate even if that resource is not emitted.
- Candidate selection consumes an RNG draw even when the candidate set contains exactly one element.
- A previously generated Common family configuration is reused by later biomes that select that family rather than rerolling its descendants.
- Guard fallback prefers cached roots matching the current effective RSGD,
  otherwise uses all cached families, and consumes a distinct scaled-index draw
  even for a one-family pool.

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

The achieved v1.0 milestone is a trustworthy standalone reproducer. Future work
must preserve that baseline unless new evidence falsifies it.

## Documentation

When behavior changes, update the relevant documentation in the same change:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DOMAIN-RULES.md`
- `docs/BACKLOG.md`

Do not rewrite historical evidence merely to make documentation look cleaner. If a recovered rule changes, record the correction explicitly.

### Preserve text encoding

All repository text files must remain valid UTF-8.

Do not introduce mojibake or encoding-corrupted punctuation such as `ÔÇö`, `Ôëê`, `Ã`, `â`, or replacement characters (`�`).

When editing Markdown, source, tests, or other text files:

- preserve existing UTF-8 encoding;
- prefer ordinary ASCII punctuation when there is any uncertainty about tool/editor encoding;
- do not "repair" intentionally quoted mojibake when it is present as an example or test fixture;
- before completion, inspect newly added or modified prose for obvious encoding corruption;
- run `python scripts/check_mojibake.py` before commit; it reports exact files and
  lines for prohibited encoding corruption;
- run `git diff --check`.

If encoding corruption appears in generated or edited text, correct it before reporting the task complete.

### Diff export encoding

When producing a diff for external review, do not pipe `git diff` through PowerShell `Out-File`, `Set-Content`, or similar text commands. Use Git's native `--output=<path>` option so patch bytes are written directly without PowerShell transcoding.

```text
# Do not use:
git diff --cached | Out-File -Encoding utf8 "myDiff.diff"

# Use:
git diff --cached --output="myDiff.diff"
```

## Code Documentation and Comments

Implementation files containing substantive project logic should include a concise module-level header describing the file's intent.

At minimum, the header should cover:

* **Purpose** — why the module exists;
* **Responsibilities** — what concerns belong in this module;
* **Boundaries / Non-responsibilities** — important concerns deliberately kept elsewhere;
* **Domain or evidence notes** — where behavior reflects recovered Starfield rules, provisional assumptions, or externally verified constraints.

Do not use comments to narrate obvious Python syntax or restate what competent readers can infer directly from the code.

Prefer comments that explain **intent, constraints, provenance, and ambiguity**, especially where a future maintainer might reasonably ask "why is this done this way?"

Good comment subjects include:

* why order must be preserved;
* why a value is deliberately not normalized;
* why two apparently redundant data sources are retained separately;
* why a structural selection is preserved even when no resource is emitted;
* why a seemingly unnecessary PRNG draw must still occur;
* why canonical output data must not influence generation;
* whether a behavior is PROVEN, STRONG, or PROVISIONAL;
* where a code path intentionally mirrors an observed runtime sequence;
* why a simpler-looking implementation would be incorrect.

Avoid comments such as:

```python
# Increment the index
index += 1
```

Prefer comments such as:

```python
# RSGDResourceIndex is generation-significant: the runtime selector walks
# entries cumulatively in stored order, so sorting by resource identity here
# would change deterministic output.
```

Public or non-trivial functions/classes should use concise docstrings where their contract, assumptions, return semantics, or domain role are not obvious from the signature.

Comments should remain accurate as behavior changes. When changing a recovered rule, update or remove comments that encode the old interpretation in the same change.

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
