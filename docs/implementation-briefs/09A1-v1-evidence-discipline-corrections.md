# Brief 09A.1 — Evidence-discipline corrections before v1.0 commit

## Status

Small correction brief for:

```text
gooberpede/starfield-resource-reproducer
```

Apply this on top of the current uncommitted Brief 09A work.

This brief does **not** change generation logic, RNG behavior, validation semantics, or the v1.0 scope. It only corrects evidence labeling and preserves one genuinely OPEN defensive state that should not disappear during consolidation.

Do not commit or push unless explicitly asked.

---

# Purpose

Make three documentation/evidence-discipline corrections before the v1.0 baseline is committed:

1. restore qualified wording around universal same-FormID cross-provenance deduplication;
2. preserve the defensive OPEN case:
   `guard + Common entries + empty global family cache`;
3. rephrase the Volii Alpha section so it is clearly an **input-boundary contract/model behavior**, not a recovered engine rule.

No implementation change is expected.

---

# 1. Restore qualification on duplicate FormID slot semantics

Brief 09A cleanup appears to have upgraded some statements to language equivalent to:

```text
PROVEN LIVE / STATIC:
capacity counts unique IRES FormIDs
and duplicate FormIDs across provenance never consume a second slot
```

That is too strong as a universal engine claim.

## Evidence boundary to preserve

The project has decisive evidence for:

### PROVEN LIVE / STATIC

```text
the CK generation path guards a shared resource-ID state at count 8
```

and for the specific observed reuse paths:

```text
ordinary cached-family reuse does not create a new family configuration
guard fallback copies an existing cached family configuration
```

The reproducer's `PlanetResourceState` models shared occupancy by unique resource FormID and records later occurrences without a second slot. This model is strongly supported by the recovered control flow and by the now-complete validation corpus.

However, unless every possible same-FormID collision across every insertion origin has been directly traced, do **not** state universal cross-origin duplicate-slot behavior as fully PROVEN for all engine insertion sites.

Preferred evidence framing:

```text
PROVEN:
    shared resource-ID state is guarded at eight

STRONG / validated model:
    shared occupancy is deduplicated by resource FormID across the modeled origins
```

or equivalent wording that fits the repository's conventions.

## Required files to audit

At minimum review:

```text
docs/DOMAIN-RULES.md
src/starfield_resource_reproducer/generation.py
```

Also search for newly introduced 09A wording in:

```text
README.md
docs/ARCHITECTURE.md
docs/V1-VALIDATION-BASELINE.md
AGENTS.md
```

if relevant.

## Required code-comment/docstring correction

Where `PlanetResourceState` or module-level comments currently say, in effect:

```text
PROVEN that one unique FormID occupies one slot across all provenance
```

rewrite to distinguish:

```text
runtime-proven shared count/guard
vs
the reproducer's validated unique-FormID occupancy model
```

Do **not** change `PlanetResourceState.record()` behavior.

The implementation stays exactly as it is unless a genuine unrelated defect is discovered.

---

# 2. Preserve the defensive empty-family-cache OPEN case

Brief 08D explicitly retained this state as unresolved:

```text
guard fires
EffectiveRSGD contains one or more Common entries
global generated-family cache is empty
```

Recovered control flow appears to make this state unreachable in normal execution under the proven guards, but no evidence defines what the engine would do if it occurred.

This is therefore still:

```text
OPEN / defensive / apparently unreachable
```

It should not disappear merely because the active backlog was cleaned up for v1.0.

## Required action

Ensure the v1.0 documentation retains this item in an appropriate non-blocking open-questions section.

Good locations include:

```text
docs/DOMAIN-RULES.md
docs/BACKLOG.md
docs/V1-VALIDATION-BASELINE.md
```

Do not put it back into the active reverse-engineering backlog as a blocker.

Preferred wording:

> **OPEN, apparently unreachable:** if a Common guard were entered with Common entries present but no generated family configurations available, current evidence does not define the engine's fallback behavior. The recovered control flow appears to prevent this state in normal execution, so it does not block v1.0.

Do not invent behavior.

---

# 3. Preserve SurveyAggregator semantic uncertainty

The exact upstream semantic contract exposed by `SurveyAggregator` remains unresolved.

This is not a blocker for v1.0, but consolidation should not imply it has been solved.

## Required action

Make sure at least one durable current-state document preserves:

```text
planet-all-resources.csv is a qualified/canonical validation oracle
for the CK/RSGD-visible channel used by the current validator

but the exact SurveyAggregator semantic contract remains unresolved
```

Do not reopen SurveyAggregator reverse engineering as active work.

This is a non-blocking evidence-boundary note only.

Good location:

```text
README.md
docs/V1-VALIDATION-BASELINE.md
or docs/DOMAIN-RULES.md
```

Avoid duplicating the same paragraph everywhere.

---

# 4. Rephrase Volii Alpha evidence heading

The current v1.0 baseline apparently uses wording similar to:

```text
PROVEN by the Volii Alpha negative control
```

for missing-input behavior.

That risks implying an engine-semantic proof.

Volii Alpha instead demonstrates the reproducer's correct **epistemic/input-boundary behavior**:

```text
PNDT/effective-RSGD input absent
atmospheric input independently present
reproducer reports known atmosphere
reproducer does not fabricate biome assignments
```

## Required wording

Use a heading/label such as:

```text
V1.0 INPUT-BOUNDARY RULE
```

or:

```text
VALIDATED MODEL BEHAVIOR
```

Preferred statement:

> If PNDT/biome/effective-RSGD input is unavailable, the v1.0 reproducer may still report independently sourced channels such as atmosphere, but it does not fabricate biome-local assignments.

Also preserve:

```text
this is not evidence about Volii Alpha's actual terrestrial biome allocation
```

Do not label this as a recovered native engine rule.

---

# Non-goals

Do not:

- alter generation logic;
- alter `PlanetResourceState.record()`;
- alter fallback behavior;
- alter RNG code;
- alter canonical validation;
- alter CK regression expectations;
- add planet-specific heuristics;
- reopen resolved reverse-engineering questions;
- downgrade the overall v1.0 milestone.

---

# Verification

Because this should be documentation/comment-only, rerun the normal verification suite:

```text
full tests
canonical 1,444-body validation
focused CK regressions
mojibake guard
git diff --check
```

Expected:

```text
138 tests pass
1,444 / 1,444 exact
0 mismatches
0 errors
CK regressions unchanged
mojibake passed
git diff --check passed except accepted line-ending warnings
```

If any generation behavior changes, stop and explain why.

---

# Deliverable

Report:

1. files changed;
2. exact wording/evidence-status corrections made;
3. confirmation `PlanetResourceState` behavior was unchanged;
4. where the empty-family-cache OPEN case is now preserved;
5. where SurveyAggregator semantic uncertainty is preserved;
6. how Volii Alpha wording was reclassified;
7. verification results;
8. confirmation no commit/push was performed.

Suggested commit message remains:

```text
docs: establish resource reproducer v1.0 baseline
```
