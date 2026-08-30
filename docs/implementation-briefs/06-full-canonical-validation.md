# Implementation Brief 06 — Full Canonical Planet Validation

## Context

Repository:

```text
gooberpede/starfield-resource-reproducer
```

Completed work:

```text
00   Project bootstrap
01   Canonical data loaders
02   PRNG compatibility
03   Generation orchestration
04   Family generation
05   Worked-case validation and diagnostics
05A  Zero-candidate RNG investigation
05B  Zero-candidate runtime correction + cache proof
05C  Bounded-index path divergence investigation
05D  Distinct bounded-RNG runtime paths
```

The reproducer now has trace-supported implementations for the major generation mechanics exercised by the worked cases.

Current worked-case status:

```text
Oberon         exact
Mimas          exact
Decaran VII-b  exact
Kreet          exact
Algorab I      exact
```

These cases collectively exercise:

```text
- MT19937 seeded from unsigned 32-bit RSCS;
- deterministic biome shuffling;
- integer rejection-sampled bounded RNG for shuffle;
- effective PNDT-vs-BIOM RSGD resolution;
- Everywhere handling as upstream/provisional static discovery;
- Special/category-5 selection;
- ordered cumulative Common/root selection;
- unconditional root emission;
- IRES descendant candidate construction;
- float32-scaled descendant candidate selection;
- structural continuation through omitted descendants;
- zero-candidate raw-word consumption;
- planet-scoped family cache reuse;
- cache-hit descendant bypass;
- canonical FormID comparison.
```

Brief 06 is the first full-corpus validation pass.

It is primarily an **evidence-gathering and mismatch-classification brief**, not a general repair brief.

---

# 1. Goal

Run the current reproducer across the complete canonical resource-bearing planet corpus and compare predicted inorganic resources against the authoritative runtime oracle.

Brief 06 must:

1. validate every planet represented in the canonical generation dataset and oracle intersection;
2. compare predicted and canonical inorganic resources by FormID;
3. report exact-match coverage;
4. collect all mismatches without stopping at the first one;
5. classify mismatches into reproducible signatures;
6. identify the smallest useful set of representative planets for follow-up;
7. distinguish likely algorithm defects from known model boundaries/data issues;
8. produce machine-readable and human-readable validation outputs;
9. avoid speculative algorithm changes during the validation pass;
10. leave the repository in a state where Brief 07 can target the highest-value mismatch class.

Do not begin broad mismatch repairs automatically.

---

# 2. Required Reading

Before editing, read:

```text
AGENTS.md
README.md
docs/ARCHITECTURE.md
docs/BACKLOG.md
docs/DOMAIN-RULES.md
docs/IMPLEMENTATION-WORKFLOW.md

docs/implementation-briefs/01-canonical-data-loader.md
docs/implementation-briefs/02-prng-compatibility.md
docs/implementation-briefs/03-generation-orchestration.md
docs/implementation-briefs/04-family-generation.md
docs/implementation-briefs/05-worked-case-validation.md
docs/implementation-briefs/05A-zero-candidate-rng.md
docs/implementation-briefs/05B-producer-update.md
docs/implementation-briefs/05C-bounded-index-conversion-correction.md
docs/implementation-briefs/05D-runtime-bounded-rng-split.md

docs/experiments/05A-kreet-zero-candidate-rng.md
docs/experiments/05B-algorab-lead-branch.md
docs/experiments/05C-algorab-bounded-index.md
docs/experiments/05D-runtime-bounded-rng-split.md
```

Inspect current implementations of:

```text
src/starfield_resource_reproducer/load_data.py
src/starfield_resource_reproducer/domain.py
src/starfield_resource_reproducer/prng.py
src/starfield_resource_reproducer/generation.py
src/starfield_resource_reproducer/candidates.py
src/starfield_resource_reproducer/diagnostics.py
src/starfield_resource_reproducer/validation.py
src/starfield_resource_reproducer/cli.py
```

and all current tests.

---

# 3. Canonical Data Sources

Use only the current authoritative datasets.

## 3.1 Generation input

```text
PlanetResourceGeneration_v5.csv
```

This is the static PNDT / BIOM / RSGD extraction.

Known broad properties from prior validation:

```text
7,920 rows
1,444 planets
3,210 planet x biome entries
32 RSGDs
```

Use the loader/domain model already established by Brief 01.

Do not bypass the canonical loader with ad hoc CSV parsing in Brief 06.

## 3.2 IRES hierarchy

```text
Starfield_IRES_Hierarchy.csv
```

Use this as the authoritative serialized resource graph.

Do not substitute hand-maintained family definitions.

## 3.3 Canonical runtime oracle

```text
planet-all-resources.csv
```

Use only rows where:

```text
ResourceCategory == Inorganic
```

Compare by:

```text
PlanetFormID
ResourceFormID
```

Do not compare by resource name.

The oracle `Rarity` column is descriptive metadata only and must not drive generation.

Do not use the deprecated:

```text
Starfield_InorganicResources_Canonical.csv
```

---

# 4. Validation Population

The validation population must be derived from the actual loaded datasets rather than from a hard-coded expected count.

Conceptually:

```text
generation planets
INTERSECT
oracle planets with at least one inorganic resource
```

Report:

```text
generation planet count
oracle inorganic planet count
intersection count
generation-only count
oracle-only count
```

Expected scale is approximately 1,444 generation planets, but do not force that number if the current datasets differ.

Any generation-only or oracle-only bodies must be reported separately and not silently treated as ordinary generation mismatches.

---

# 5. Validation Scope

For each planet in the validation intersection:

1. generate the complete predicted inorganic resource set using the current production algorithm;
2. collect the canonical inorganic resource FormID set;
3. compare them as sets;
4. retain generation diagnostics sufficient to explain mismatches;
5. record final raw MT draw count;
6. record shuffled biome order;
7. record selected Common roots and cache hits;
8. record final predicted resource FormIDs.

The oracle must not influence generation.

Do not use canonical resources to choose branches, reorder candidates, or repair predictions.

---

# 6. Exact-Match Definition

A planet is an exact match iff:

```text
predicted inorganic FormID set
==
canonical inorganic FormID set
```

Ordering is irrelevant for final-set equality.

However, internal generation order and draw counts should remain available diagnostically.

Distinguish:

```text
FINAL_SET_EXACT
```

from any future concept of:

```text
TRACE_EXACT
```

The full corpus generally has no live per-planet trace, so Brief 06 validates canonical final sets only.

Do not imply that a final-set exact result proves every internal RNG path for that planet.

---

# 7. Mismatch Model

For each non-exact planet, calculate at minimum:

```text
missing_from_prediction
unexpected_in_prediction
```

where:

```text
missing_from_prediction =
    canonical - predicted

unexpected_in_prediction =
    predicted - canonical
```

Record FormIDs and human-readable resource names where available.

Also record:

```text
planet FormID
planet EditorID
planet name
RSCS
biome count
shuffled biome order
predicted final draw count
selected Common roots
cache-hit roots
effective RSGDs encountered
```

Do not reduce a mismatch to a single text string.

Create a structured mismatch object suitable for programmatic clustering.

---

# 8. Mismatch Classification

Add deterministic high-level mismatch classification.

At minimum support categories equivalent to:

```text
EXACT
MISSING_ONLY
UNEXPECTED_ONLY
MISSING_AND_UNEXPECTED
DATASET_COVERAGE_MISMATCH
GENERATION_ERROR
```

Where useful, add secondary signatures based on resource/family structure.

Examples:

```text
one missing descendant
one unexpected descendant
missing root
unexpected root
same-family substitution
multiple-family divergence
Everywhere-only discrepancy
Special-resource discrepancy
```

Do not infer causes from these labels.

For example:

```text
SAME_FAMILY_SUBSTITUTION
```

may be a useful structural signature, but it is not by itself proof of an RNG or candidate-order bug.

---

# 9. Family-Aware Mismatch Analysis

Use the IRES hierarchy to classify missing/unexpected ordinary family resources by Common root where mechanically derivable.

Useful fields may include:

```text
missing_family_roots
unexpected_family_roots
missing_descendants_by_root
unexpected_descendants_by_root
```

This should help distinguish:

```text
wrong Common family selected
```

from:

```text
correct root but wrong descendant path
```

Do not hard-code the eight familiar ordinary families.

Derive relationships from the IRES graph and current domain logic.

Special/Everywhere/standalone resources should remain explicitly distinguishable.

---

# 10. Biome / RSGD-Aware Analysis

For mismatched planets, retain enough generation history to answer:

```text
Which effective RSGDs were used?
Which Common roots were selected per biome?
Which roots were cache hits?
Which biome first introduced the divergent family?
```

Where practical, derive signatures such as:

```text
single-biome mismatch
multi-biome mismatch
repeated-root/cache planet
PNDT-override planet
BIOM-only planet
```

These are clustering dimensions, not causal conclusions.

---

# 11. Draw-Count Diagnostics

Record final raw MT draw count per planet.

For mismatches, preserve per-operation draw counts or timeline events through the existing diagnostics.

Useful operation categories include:

```text
shuffle_bounded_integer
Special probability draw
Common probability draw
descendant inclusion
descendant_scaled_index
zero-candidate raw advance
```

If a shuffle rejection occurs, count every rejected raw word.

Do not add hidden compensating draws.

---

# 12. Full-Corpus Validation API

Prefer a reusable validation API rather than embedding the entire workflow in CLI code.

Conceptually, something like:

```python
validate_all_planets(project_data) -> FullValidationResult
```

with result structures such as:

```text
FullValidationResult
PlanetValidationResult
MismatchSummary
MismatchCluster
```

Exact names are up to implementation.

The API should allow tests to inspect structured results without parsing console output.

---

# 13. Machine-Readable Output

Add an exportable machine-readable mismatch report.

Preferred format:

```text
CSV
```

because the dataset is naturally tabular and easy to inspect externally.

A reasonable output file might be:

```text
validation/full-canonical-mismatches.csv
```

Do not require the file to be committed if repository conventions treat generated validation output as local-only.

At minimum include columns equivalent to:

```text
PlanetFormID
PlanetEditorID
PlanetName
RSCS
BiomeCount
FinalDrawCount
MatchStatus
MissingFormIDs
MissingNames
UnexpectedFormIDs
UnexpectedNames
SelectedCommonRoots
CacheHitRoots
EffectiveRSGDs
MismatchSignature
```

Use stable serialization for multi-value cells, e.g. semicolon-separated FormIDs in deterministic order.

If another repository-local output location is already established, follow it.

---

# 14. Human-Readable Summary

Produce a compact Markdown experiment report:

```text
docs/experiments/06-full-canonical-validation.md
```

The report should include:

```text
dataset coverage
exact-match count
mismatch count
exact-match percentage
mismatch category counts
top mismatch signatures
representative planets
known model-boundary observations
recommended next investigation
```

Do not dump all 1,444 planet rows into the Markdown report.

Link or refer to the machine-readable report where appropriate.

---

# 15. Required Aggregate Metrics

Report at minimum:

```text
total validation planets
exact matches
mismatches
exact-match percentage

missing-only planets
unexpected-only planets
missing-and-unexpected planets

total missing resource occurrences
total unexpected resource occurrences
distinct missing resource FormIDs
distinct unexpected resource FormIDs
```

Also report useful distribution summaries:

```text
mismatches by biome count
mismatches by effective RSGD
mismatches by selected Common root
mismatches involving PNDT override
mismatches involving cache reuse
```

If a dimension is awkward or misleading, explain why rather than fabricating it.

---

# 16. Representative Mismatch Selection

Select a small representative set for future live/static investigation.

Aim for approximately:

```text
3-8 representative planets
```

chosen to cover distinct mismatch signatures rather than simply the first failures.

Prefer representatives that are:

```text
small biome count
clear static data
minimal confounding factors
good discriminators between competing hypotheses
```

For each representative, explain why it is useful.

Examples of useful diversity:

```text
single-biome descendant mismatch
BIOM-only multi-biome mismatch
PNDT-override mismatch
cache-related mismatch
Everywhere/Special discrepancy
root-selection mismatch
```

Do not launch x64dbg experiments in Brief 06.

Only identify the best next candidates.

---

# 17. Known Model Boundaries

Treat the following carefully.

## 17.1 Everywhere resources

Current upstream Everywhere handling is still not reconstructed at the exact insertion-routine level.

The reproducer models Everywhere from static effective RSGD/category data.

If mismatches cluster around Water/Everywhere, classify them separately.

Do not immediately hard-code Water exceptions.

## 17.2 Special resources

Special/category-5 selection is substantially established.

If mismatches involve Helium-3 or other Special cases, retain the full Special-pass diagnostics.

Do not assume all Special mismatches have the same cause.

## 17.3 RSCS zero / fallback

If the corpus contains planets with:

```text
RSCS == 0
```

identify them explicitly.

If production fallback behavior is still incomplete or provisional, do not bury those failures among ordinary mismatch statistics.

Create a separate signature/category where appropriate.

Report count and representative cases.

## 17.4 Planet/resource limits

Previously observed runtime code suggested possible limits around generated families/resource slots.

If mismatch signatures correlate with unusually resource-dense planets, flag them.

Do not implement limit behavior in Brief 06 unless it already exists and is evidence-backed.

---

# 18. Error Handling

One malformed planet must not abort the entire corpus run.

For per-planet generation exceptions:

1. capture the error;
2. record a `GENERATION_ERROR` validation result;
3. continue validating remaining planets.

At the end, report:

```text
generation error count
affected planets
exception type/message summary
```

Tests should still fail on unexpected errors where appropriate, but the corpus analysis command should produce the complete diagnostic picture.

---

# 19. Determinism

Run the complete validation at least twice in tests or through a focused determinism check sufficient to establish:

```text
same inputs
-> same per-planet predictions
-> same mismatch classification
-> same aggregate counts
```

Do not introduce nondeterministic iteration over sets/dicts into output ordering.

Sort report rows deterministically, preferably by:

```text
PlanetFormID
```

or another stable canonical key.

---

# 20. Performance

This is only ~1,444 planets and should not require optimization-heavy architecture.

Measure total validation runtime in the completion report.

Do not introduce concurrency unless there is a demonstrated need.

Deterministic, auditable single-process behavior is preferable at this stage.

Avoid caching that risks sharing mutable RNG/generation state across planets.

---

# 21. CLI

Add a clear way to run full validation from the existing CLI if appropriate.

For example:

```text
python -m starfield_resource_reproducer.cli --validate-all
```

Exact syntax should follow current CLI conventions.

Useful optional arguments may include:

```text
--output <path>
--mismatches-only
```

but do not overbuild the CLI.

The core validation functionality must remain callable directly from Python.

---

# 22. Worked-Case Regression Gate

Before accepting full-corpus results, the existing worked cases must remain exact:

```text
Oberon         exact, 10 draws
Mimas          exact, 10 draws
Decaran VII-b  exact, 10 draws
Kreet          exact, 30 draws
Algorab I      exact, 22 draws
```

If any of these regress during Brief 06, stop implementation changes and report the regression.

Do not proceed by weakening their tests.

---

# 23. No Algorithm Repairs in Brief 06

This is critical.

When corpus validation reveals mismatches:

Do not:

```text
change RNG rules
change candidate order
change RSGD precedence
add planet-specific cases
add family-specific cases
alter zero-candidate consumption
alter cache behavior
change Everywhere handling
change Special handling
```

merely to improve the full-corpus percentage.

Brief 06 should expose and classify failures.

Any substantive algorithm correction belongs in a follow-up brief based on evidence.

Small bugs in the new validation/reporting code itself may of course be fixed.

---

# 24. No Oracle Leakage

The canonical oracle may be used only for:

```text
comparison
classification
reporting
test expectations
```

It must never affect generation decisions.

Add a code comment or test protecting this boundary if the architecture makes accidental leakage plausible.

A useful invariant test would generate a planet from static generation/IRES inputs without supplying oracle rows to the generation function.

---

# 25. Tests

Add focused tests for:

```text
exact-set comparison
missing-only mismatch
unexpected-only mismatch
mixed mismatch
dataset coverage mismatch
generation error capture
family-aware signature
stable deterministic ordering
machine-readable row serialization
aggregate counts
```

Add an integration test for the complete corpus if runtime is reasonable.

At minimum assert:

```text
worked cases exact
full run completes
result count equals validation population
aggregate counts are internally consistent
no duplicate planet validation rows
```

Once the first full-corpus baseline is established, it is acceptable to lock the aggregate exact/mismatch counts as a regression baseline, provided the documentation makes clear that mismatches are known research targets rather than expected correctness.

Do not mark mismatched planets as passing generation tests individually merely because they are part of the baseline.

---

# 26. Baseline Philosophy

The first Brief 06 corpus result is a research baseline.

If the result is:

```text
95% exact
```

that does not mean the remaining 5% are acceptable production behavior.

Likewise, if the result is much lower, do not immediately rewrite the algorithm.

The objective is:

```text
measure
cluster
prioritize
investigate
```

not:

```text
force green
```

Document the baseline truthfully.

---

# 27. Documentation Updates

Update:

```text
docs/BACKLOG.md
```

with:

```text
full-corpus validation completed
baseline exact-match coverage
identified mismatch classes
next priority class
```

Update:

```text
README.md
```

with a concise validation-status statement if appropriate.

Do not claim the reproducer is complete unless the evidence warrants that claim.

Update:

```text
docs/ARCHITECTURE.md
```

only if the new validation layer materially changes architecture.

Create:

```text
docs/experiments/06-full-canonical-validation.md
```

as the canonical human-readable research record.

---

# 28. Evidence Vocabulary

Use the repository evidence vocabulary consistently:

```text
PROVEN
STRONG
PROVISIONAL
COUNTERFACTUAL
```

Full-corpus empirical patterns may support statements such as:

```text
STRONG:
mismatches overwhelmingly cluster in ...
```

but do not call a causal explanation PROVEN without static/runtime evidence.

Dataset observations should be distinguished from runtime mechanism proofs.

---

# 29. Acceptance Criteria

Brief 06 is complete when:

- [ ] the complete generation/oracle validation population is derived programmatically;
- [ ] every planet in the intersection is validated;
- [ ] generation-only and oracle-only bodies are reported separately;
- [ ] predictions are compared to canonical inorganic resources by FormID;
- [ ] exact matches and mismatches are represented structurally;
- [ ] missing and unexpected resources are recorded separately;
- [ ] mismatch signatures are deterministic;
- [ ] family-aware mismatch dimensions are available;
- [ ] useful biome/RSGD/cache dimensions are available;
- [ ] generation errors do not abort the corpus run;
- [ ] aggregate metrics are produced;
- [ ] a machine-readable mismatch report is produced;
- [ ] `docs/experiments/06-full-canonical-validation.md` is created;
- [ ] representative follow-up planets are selected;
- [ ] no speculative algorithm repairs are made;
- [ ] oracle data does not influence generation;
- [ ] output ordering is deterministic;
- [ ] the five worked cases remain exact with established draw counts;
- [ ] full test suite passes;
- [ ] canonical CSV files remain unchanged;
- [ ] `git diff --check` passes apart from known line-ending warnings;
- [ ] mojibake scan passes for newly authored/modified prose;
- [ ] validation runtime is reported;
- [ ] the next highest-value investigation is identified;
- [ ] no commit or push is performed.

---

# 30. Completion Report

When finished, report:

1. files created;
2. files modified;
3. validation population counts;
4. exact-match count;
5. mismatch count;
6. exact-match percentage;
7. generation-only/oracle-only counts;
8. mismatch category counts;
9. total missing/unexpected resource occurrences;
10. distinct missing/unexpected resource counts;
11. top mismatch signatures;
12. mismatch distribution by biome count;
13. mismatch distribution by effective RSGD;
14. mismatch distribution by Common root/family where useful;
15. PNDT-override mismatch count;
16. cache-related mismatch count;
17. RSCS-zero/fallback count and status;
18. generation error count;
19. representative follow-up planets and rationale;
20. machine-readable report path;
21. Markdown experiment-report path;
22. CLI/API added;
23. determinism result;
24. total validation runtime;
25. worked-case regression results;
26. test count/results;
27. whether canonical CSVs changed;
28. whether any algorithm behavior changed;
29. recommended scope for Brief 07;
30. blockers/questions before the next investigation.

Do not commit or push.

---

## Suggested commit after review

If the validation implementation and baseline report are approved:

```text
feat: add full canonical validation
```
