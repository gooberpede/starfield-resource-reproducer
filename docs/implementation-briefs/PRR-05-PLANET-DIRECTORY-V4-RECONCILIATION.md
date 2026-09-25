# Implementation Brief — PRR-05 Planet Directory Exporter v4 Reconciliation

## Purpose

Resolve PRR-05 from the `starfield-resource-reproducer` public-release audit as a standalone data-contract task before the remaining release-readiness remediation.

The currently installed Planet Directory exporter is the authoritative **v4** implementation:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\Starfield - Export Planet Directory.pas
```

The repository copy under:

```text
xedit-scripts/Starfield - Export Planet Directory.pas
```

is still **v1** and is deprecated.

v4 adds at least:

```text
SolarArrayPower
WindTurbinePower
PlanetaryHabitationRank
```

The repository must be reconciled to v4 without changing inorganic-generation semantics or weakening the protected v1.0 validation baseline.

---

## Scope

This task owns only PRR-05.

It should:

1. inspect the installed v4 exporter and establish its exact current output contract;
2. replace the tracked deprecated v1 exporter with the installed canonical v4 exporter;
3. generate a fresh `planet-directory.csv` using v4;
4. reconcile the reproducer's Planet Directory ingestion/model/tests/documentation with the v4 schema;
5. preserve the three new v4 fields as canonical Planet Directory metadata;
6. make the narrowest coherent implementation changes required by the existing architecture;
7. prove that the inorganic generator and default consumer product remain unchanged in meaning and output;
8. leave the repository ready for the later general release-readiness remediation.

Do **not** address the other PRR findings in this task.

---

## Authoritative decisions

### 1. v4 is canonical

The installed v4 script is the source of truth.

Do not preserve v1 as a competing or alternative canonical exporter.

After reconciliation, the repository copy and the intended installed working copy should be byte-identical.

### 2. The expanded fields are valid

`SolarArrayPower`, `WindTurbinePower`, and `PlanetaryHabitationRank` are intentional additions, not accidental drift.

Do not strip them merely to preserve the former 12-column schema.

### 3. Do not pre-assign new generation semantics

These fields are Planet Directory metadata. They are not currently evidenced as inputs to the reconstructed inorganic generation algorithm.

Integrate them into the data model only as far as required to preserve and expose the canonical Planet Directory contract cleanly.

Do not make them affect generation, assignment, RNG, validation-oracle logic, or the 35-column consumer product unless existing code architecture demonstrably requires a non-semantic representation change.

### 4. Preserve the protected scientific/product baseline

This task must not reopen or modify the reconstructed inorganic-generation algorithm.

The following are protected outcomes:

```text
canonical generation bodies: 1,444
exact matches:               1,444
mismatches:                  0
generation errors:           0

production rows:             7,780
BIOME rows:                  7,445
ATMOSPHERE rows:             335

default product columns:     35

Volii Alpha:
    BIOME rows:              0
    ATMOSPHERE rows:         2
```

The production CLI must remain independent of `planet-all-resources.csv`.

---

## Required investigation before editing

### A. Inspect v4

Read the installed script directly from:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\Starfield - Export Planet Directory.pas
```

Record:

- version header;
- exact output filename;
- exact CSV header and column order;
- field extraction logic for all columns;
- any changes beyond the three known new fields;
- xEdit/SF1Edit version assumptions;
- selection/run assumptions;
- output path behavior.

Do not assume that v4 differs from v1 only by three columns.

### B. Inspect all current consumers of `planet-directory.csv`

Search the repository for:

```text
planet-directory.csv
PlanetDirectory
Planet Directory
SolarArrayPower
WindTurbinePower
PlanetaryHabitationRank
```

Identify:

- loader/header validation;
- typed/domain models;
- project-data structures;
- cross-dataset coherence validation;
- production product construction;
- tests and fixtures;
- manifest/provenance handling;
- documentation;
- implementation/history references that are current rather than historical.

Determine whether the current loader requires an exact header and where the 12-column contract is encoded.

### C. Establish whether downstream consumers rely on exact row/hash values

Before replacing the canonical CSV, identify tests or documentation that pin:

- row count;
- column count;
- header;
- SHA-256;
- extraction timestamp;
- specific sample rows.

Update only the values made obsolete by the approved v4 contract.

---

## Implementation requirements

### 1. Replace the tracked exporter

Replace:

```text
xedit-scripts/Starfield - Export Planet Directory.pas
```

with the authoritative installed v4 script.

Do not keep the deprecated v1 script under another active/canonical filename.

If historical documentation refers to v1, preserve that history where clearly historical; do not rewrite history merely to erase the old version.

### 2. Produce a fresh v4 canonical export

Run v4 against the same intended PNDT population used for the canonical Planet Directory.

Generate:

```text
planet-directory.csv
```

using the exporter's normal output path.

Before replacing the repository data file, verify:

- expected PNDT population is present;
- no accidental plugin/mod contamination is included;
- row grain remains one canonical row per intended body;
- IDs/names/core directory fields remain coherent;
- the new fields are populated according to v4 logic;
- no duplicate natural-grain rows are introduced;
- no unexpected null/blank behavior is introduced in previously required fields.

Record the resulting row count and schema.

### 3. Reconcile loader/schema behavior

Update the loader and typed model so the canonical v4 CSV is accepted deliberately, not through a generic weakening of validation.

Preferred principle:

> validate the approved v4 schema exactly, while representing all canonical fields explicitly enough that silent schema drift remains detectable.

Do not solve this by simply ignoring arbitrary unknown columns unless that is already the deliberate repository-wide contract.

If the current model has a dedicated Planet Directory row/domain object, add the v4 fields there with suitable types.

Preserve existing identity/coherence validation.

### 4. Preserve production semantics

The three added fields must not alter:

- generation eligibility;
- effective RSGD selection;
- atmosphere handling;
- Everywhere/Special/Common/descendant behavior;
- family caching/fallback;
- RNG draw sequence;
- accepted occurrence set;
- consumer product schema/order.

A changed canonical output or RNG ledger is a regression unless a concrete pre-existing bug unrelated to these metadata fields is discovered. If such a contradiction appears, stop and report it rather than folding algorithm work into this task.

### 5. Update canonical data/provenance

Replace the tracked canonical:

```text
data/planet-directory.csv
```

with the approved fresh v4 export.

Update any associated:

- extraction timestamp;
- row count;
- SHA-256;
- schema description;
- manifest/test expectations;
- provenance documentation.

Do not regenerate unrelated canonical inputs.

### 6. Update documentation

At minimum inspect and update as applicable:

```text
README.md
docs/CANONICAL-XEDIT-EXPORTS.md
docs/ARCHITECTURE.md
docs/DOMAIN-RULES.md
docs/V1-VALIDATION-BASELINE.md
docs/BIOME-INORGANIC-RESOURCES.md
AGENTS.md
```

Only update files that actually contain stale Planet Directory contract information.

Current documentation should state that:

- Planet Directory v4 is canonical;
- the v4 schema includes the additional Wind/Solar/Planetary Habitation metadata;
- these fields are directory metadata, not reconstructed inorganic-generation inputs;
- the Planet Directory is a required production input;
- the tracked exporter and canonical CSV are synchronized to v4.

Historical implementation briefs may retain older contracts if clearly historical.

### 7. Synchronize installed and tracked script copies

At the end of the task, compare:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\Starfield - Export Planet Directory.pas
```

and:

```text
xedit-scripts/Starfield - Export Planet Directory.pas
```

They must be byte-identical.

Do not modify the installed v4 script merely to force agreement with deprecated repository behavior.

---

## Testing and verification

### A. Targeted Planet Directory tests

Add/update tests covering:

- exact approved v4 header and column order;
- parsing of all v4 fields;
- typing/normalization of Wind/Solar/Planetary Habitation values;
- representative rows;
- row-count/natural-grain expectations;
- cross-dataset identity coherence;
- failure on malformed or stale schema where appropriate.

### B. Full test suite

Run:

```text
python -m pytest
```

All tests must pass.

The previous audit baseline was:

```text
177 passed
```

A higher reviewed count is expected if new tests are added.

### C. Canonical generation validation

Re-run the complete canonical validation and require:

```text
1,444 / 1,444 exact
0 mismatches
0 generation errors
```

### D. Production product validation

Run the production pipeline and require:

```text
7,780 total rows
7,445 BIOME
335 ATMOSPHERE
35 columns
```

Verify deterministic ordering remains unchanged unless a documented non-semantic provenance field outside the consumer product requires otherwise.

### E. Volii Alpha control

Require:

```text
0 BIOME
2 ATMOSPHERE
```

### F. Oracle boundary

Confirm the normal production CLI still does not load:

```text
data/planet-all-resources.csv
```

### G. CLI smoke tests

At minimum rerun:

```text
starfield-resource-reproducer --validate-only
starfield-resource-reproducer
```

No public CLI option or behavior should change because of this task.

### H. Data/script synchronization checks

Confirm:

- tracked Planet Directory exporter == installed v4 byte-for-byte;
- canonical `planet-directory.csv` was produced by that v4 exporter;
- documented schema == actual v4 output schema;
- no deprecated v1 script remains active in the repository.

---

## Out of scope

Do not address in this task:

- repository `LICENSE`;
- third-party notices/publication framing;
- research-repository navigation/counterexample routing;
- wheel/non-editable installation support;
- PyPI publication;
- expanded package metadata;
- diagnostic CLI expansion;
- the other public-release PRRs;
- GitHub description/topics;
- tags or GitHub Releases;
- visibility changes;
- history rewriting;
- unrelated xEdit exporter changes;
- inorganic algorithm changes.

Wheel/PyPI support and expanded diagnostics are already deferred backlog items.

The remaining release-readiness remediation will be handled in a separate brief after PRR-05 is complete.

---

## Evidence discipline

Do not infer that the new v4 Planet Directory fields participate in inorganic generation merely because they are now canonical directory metadata.

Keep distinct:

```text
canonical metadata contract
vs.
generation input semantics
```

If testing shows the additional columns expose an unexpected dependency or contradiction, document it and stop before changing generation behavior.

Do not use the validation oracle to patch or compensate for any failure.

---

## Deliverables

Return:

1. exact inspected v4 script version/header;
2. exact v4 CSV schema and column order;
3. summary of differences from tracked v1;
4. files changed;
5. loader/model changes;
6. tests added/updated;
7. fresh v4 export row count;
8. confirmation canonical CSV was replaced from v4;
9. confirmation installed/tracked exporter copies are byte-identical;
10. full test result;
11. canonical `1,444 / 1,444` validation result;
12. production `7,780 / 7,445 / 335 / 35-column` result;
13. Volii Alpha result;
14. oracle-boundary result;
15. any documentation/provenance values changed;
16. confirmation no inorganic-generation semantics changed;
17. confirmation no other PRR remediation was performed;
18. `git diff --check` result;
19. concise residual-risk/open-question list;
20. recommended commit message.

Do not commit or push unless explicitly asked.

---

## Acceptance criteria

This task is complete when:

- v4 is the only active canonical Planet Directory exporter in the repository;
- the tracked and installed v4 scripts are byte-identical;
- a fresh v4 `planet-directory.csv` is commit-ready as the canonical input;
- the reproducer deliberately accepts and models the approved v4 schema;
- the three added fields are preserved as canonical metadata;
- current documentation reflects v4 and no longer presents v1/12-column Planet Directory as current;
- all targeted and full tests pass;
- canonical generation remains `1,444 / 1,444`;
- production output remains 7,780 rows with 35 columns;
- Volii Alpha remains 0 BIOME / 2 ATMOSPHERE;
- the production oracle boundary remains intact;
- no unrelated release-readiness or algorithm work has been introduced.

Suggested commit message after review:

```text
refactor: update planet directory exporter to v4
```
