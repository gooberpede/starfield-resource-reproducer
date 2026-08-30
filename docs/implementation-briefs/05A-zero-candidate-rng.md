# Implementation Brief 05A — Zero-Candidate Descendant RNG Consumption

## Context

Repository:

```text
gooberpede/starfield-resource-reproducer
```

Completed phases:

```text
Brief 00 — Project Bootstrap
Brief 01 — Canonical Data Loading and Domain Model
Brief 02 — PRNG Compatibility Layer
Brief 03 — Generation Orchestration and Shuffle Transparency
Brief 04 — Family Generation and Cache Semantics
Brief 05 — Worked-Case Reproduction and Mismatch Diagnostics
```

Current worked-case status:

```text
Oberon        exact
Mimas         exact
Decaran VII-b exact
Kreet         mismatch: missing Neon only
```

Kreet currently predicts:

```text
Water
Lead
Silver
Argon
Iron
Alkanes
```

Canonical Kreet additionally contains:

```text
Neon
```

The first plausible divergence is now sharply localized to descendant RNG consumption before Argon's Neon decision.

---

# 1. Goal

Resolve the runtime behavior of descendant levels where:

```text
candidate_count == 0
```

Specifically determine whether Starfield consumes:

```text
0 draws
1 inclusion draw
1 index draw
2 draws
or some other sequence
```

when a descendant rarity level has no valid structural candidates.

The immediate target is Kreet's Lead family, which encounters two consecutive zero-candidate levels:

```text
Exotic
Unique
```

before the later Argon family reaches its Neon inclusion decision.

Brief 05A is an evidence-resolution task, not a broader generation rewrite.

---

# 2. Current Evidence

## 2.1 Current production model

The current implementation treats zero-candidate levels as:

```text
no inclusion draw
no candidate-index draw
structural node unchanged
```

This behavior is explicitly PROVISIONAL.

For Kreet Lead:

```text
Exotic:
candidate_count = 0
draw_count 8 -> 8

Unique:
candidate_count = 0
draw_count 8 -> 8
```

Current structural node remains:

```text
Mercury (0027C499)
```

---

## 2.2 Downstream Kreet mismatch

Argon's Neon inclusion currently occurs at:

```text
draw 15
raw uint32 = 1553730631
roll = 0.3617524802684784
threshold = 0.15
```

Therefore Neon is omitted.

---

## 2.3 Counterfactual finding

Brief 05 diagnostics established:

```text
+1 earlier raw draw:
roll = 0.7946245074272156
Neon still omitted

+2 earlier raw draws:
roll = 0.08317194879055023
Neon included
```

This makes the hypothesis:

```text
one raw draw per zero-candidate Lead level
```

particularly plausible.

However, this remains COUNTERFACTUAL and NOT RUNTIME-PROVEN.

Do not encode it into production without evidence.

---

# 3. Required Pre-Implementation Reading

Before editing, read:

```text
AGENTS.md
README.md
docs/ARCHITECTURE.md
docs/BACKLOG.md
docs/DOMAIN-RULES.md
docs/IMPLEMENTATION-WORKFLOW.md

docs/implementation-briefs/00-project-bootstrap.md
docs/implementation-briefs/01-canonical-data-loader.md
docs/implementation-briefs/02-prng-compatibility.md
docs/implementation-briefs/03-generation-orchestration.md
docs/implementation-briefs/04-family-generation.md
docs/implementation-briefs/05-worked-case-validation.md
```

Inspect:

```text
generation.py
candidates.py
diagnostics.py
validation.py
prng.py
```

and current tests.

Do not alter unrelated architecture.

---

# 4. Scope

Brief 05A should do only the minimum required to:

1. make zero-candidate branch behavior easy to vary/test;
2. compare plausible RNG-consumption models;
3. identify which model reproduces Kreet;
4. clearly separate:
   - current production behavior
   - counterfactual models
   - runtime-proven behavior
5. prepare the smallest possible x64dbg experiment if live evidence is still required.

Do not begin full 1,444-body validation.

---

# 5. Zero-Candidate Policy Abstraction

Refactor the current provisional behavior only if needed to make the uncertainty explicit.

A small internal policy/strategy is acceptable, conceptually:

```text
ZeroCandidatePolicy
```

with diagnostic-only/test modes such as:

```text
CONSUME_NONE
CONSUME_INCLUSION
CONSUME_INDEX
CONSUME_BOTH
```

or equivalent.

Important:

> Production behavior must remain the currently evidence-qualified default until runtime evidence justifies changing it.

Do not make a speculative policy the default merely because it fixes Kreet.

---

# 6. Counterfactual Matrix

Add diagnostics/tests that run Kreet under each plausible zero-candidate policy.

At minimum compare:

```text
A. consume 0 draws
B. consume 1 float/inclusion draw
C. consume 1 bounded-index/raw draw
D. consume inclusion + index
```

Where a bounded-index operation is undefined for zero candidates, do not fabricate `next_index(0)`.

Instead model only a raw-consumption equivalent in counterfactual diagnostics, clearly labeled as such.

The output should report:

```text
policy
draw count after Lead family
Argon Neon draw number
Argon Neon raw value
Argon Neon roll
Neon emitted?
final Kreet predicted set
```

---

# 7. Important Distinction: Draw Type vs Draw Count

Do not assume that "one extra draw" means the same high-level operation.

A probability draw and a bounded-index draw may both consume one raw MT word under the current implementation, but the runtime branch semantics still matter.

The code/docs should distinguish:

```text
one raw MT draw consumed
```

from:

```text
one inclusion operation occurred
```

This is important for evidence accuracy.

---

# 8. Static/Decompiled Control-Flow Review

Before asking for a new x64dbg trace, inspect the existing recovered implementation notes/decompiled control flow already encoded in docs/comments.

The target question is narrow:

> Does the descendant function call the inclusion RNG before checking candidate count, after checking candidate count, or only after candidate construction succeeds?

If current source/decompilation already answers this unambiguously, update production behavior accordingly and document the evidence.

Do not rely on stylistic expectations.

---

# 9. Runtime Experiment Preparation

If static evidence is insufficient, Brief 05A should prepare a precise x64dbg experiment plan for the user.

The preferred target remains:

```text
Kreet
Lead family
Exotic zero-candidate level
Unique zero-candidate level
```

The experiment should identify:

```text
entry/exit of each descendant-level call
candidate_count
PRNG state/draw before
whether RNG helper is invoked
PRNG state/draw after
```

No broad trace is needed.

The ideal experiment should answer:

```text
Exotic zero-candidate:
draws consumed = ?

Unique zero-candidate:
draws consumed = ?
```

independently.

---

# 10. Trace Instrumentation Requirements

If Codex can identify suitable existing function addresses from project docs/comments, include exact x64dbg commands in the completion report or a generated experiment note.

If not, report what address/function still needs to be recovered.

Do not invent addresses.

The experiment should minimize manual stepping.

Prefer:

```text
conditional trace
breakpoint around descendant function
PRNG-call breakpoint/logging
```

over manual register archaeology.

---

# 11. Production Change Rule

Production zero-candidate behavior may be changed only if one of these is true:

```text
A. existing decompiled control flow proves it
B. new live trace proves it
```

Counterfactual Kreet matching alone is insufficient.

If behavior becomes proven, update:

```text
generation.py
docs/DOMAIN-RULES.md
tests
```

and remove or downgrade obsolete provisional comments.

---

# 12. Kreet Revalidation

If production behavior changes based on evidence, rerun Kreet.

Expected target:

```text
Water
Lead
Silver
Argon
Neon
Iron
Alkanes
```

If Kreet becomes exact, preserve:

```text
shuffle order
Common roots
family paths
draw timeline
```

and assert exact match.

Do not weaken earlier tests.

---

# 13. If Kreet Still Fails

If zero-candidate behavior is proven and Kreet still misses Neon:

do not continue guessing.

Report the next first divergence precisely.

At that point, the preferred next experiment is a **second multi-biome control planet**.

Purpose:

```text
distinguish general multi-biome/zero-candidate behavior
from Kreet-specific behavior
```

---

# 14. Second Multi-Biome Control Selection

If needed, identify a candidate planet with:

```text
multiple biomes
different Common roots across biomes
at least one zero-candidate descendant level if possible
canonical runtime output available
no known PNDT anomaly unless intentionally testing one
```

Prefer a structurally simple planet.

Do not automatically choose a target without explaining why it is diagnostically useful.

If several candidates fit, report 2–3 ranked options.

Do not begin tracing the second planet automatically.

---

# 15. Kreet-Specific Hypothesis Discipline

If Kreet remains anomalous, possible categories include:

```text
Kreet-specific PNDT overrides
plugin/provenance behavior
resource-family interaction
unmodeled branch in Lead or Argon family
multi-biome state handling
other planet-specific generation data
```

These are only categories.

Do not create a Kreet-specific code path.

---

# 16. Diagnostics

Add or extend events so a zero-candidate level records:

```text
root
current structural node
rarity
candidate_count
draw_count_before
draw_count_after
raw values consumed, if any
operation type(s)
structural node after
evidence status
```

Counterfactual events should be visually/distinctly labeled.

---

# 17. Tests

Suggested new tests:

```text
tests/test_zero_candidate_rng.py
tests/test_kreet_zero_candidate_diagnostics.py
```

Tests should cover:

```text
current production policy
counterfactual consume-1 model
counterfactual consume-2 model
Kreet downstream Neon outcome
```

If runtime evidence resolves the rule, tests should be updated to lock the proven behavior.

---

# 18. No Planet-Specific Fixes

Do not introduce:

```python
if planet == Kreet
if root == Lead
if resource == Neon
```

or equivalent.

All behavior must remain generic.

---

# 19. Evidence Labels

Use:

```text
PROVEN
STRONG
PROVISIONAL
COUNTERFACTUAL
```

Examples:

```python
# COUNTERFACTUAL: consuming one raw word at each empty Lead level moves
# Argon's Neon roll to a passing value. This is diagnostic only.
```

```python
# PROVEN: zero-candidate descendant levels consume one raw MT word before
# returning. [Only use this if static/live evidence establishes it.]
```

---

# 20. Documentation Updates

Update:

```text
docs/DOMAIN-RULES.md
```

only if evidence changes.

Update:

```text
docs/BACKLOG.md
```

with the zero-candidate investigation status.

Update:

```text
docs/ARCHITECTURE.md
```

only if the diagnostic-policy abstraction materially affects architecture.

Do not over-document a temporary testing mechanism.

---

# 21. Acceptance Criteria

Brief 05A is complete when:

- [ ] zero-candidate RNG behavior is isolated as an explicit testable uncertainty.
- [ ] Kreet can be run under multiple counterfactual draw-consumption policies without altering production behavior.
- [ ] diagnostics report downstream Neon roll/draw under each policy.
- [ ] the `+2 raw draws` Kreet result is independently reproduced by tests.
- [ ] existing static/decompiled evidence is reviewed for zero-candidate branch order.
- [ ] production behavior changes only if supported by static or live evidence.
- [ ] if changed, Kreet is revalidated exactly.
- [ ] if still unresolved, a minimal x64dbg experiment plan is produced.
- [ ] if Kreet remains anomalous after rule resolution, candidate second multi-biome controls are identified.
- [ ] no Kreet-specific workaround is introduced.
- [ ] all previous exact worked cases remain exact.
- [ ] canonical CSVs remain unchanged.
- [ ] code-commenting standards are followed.

---

# 22. Completion Report

Codex should report:

1. files created;
2. files modified;
3. current production zero-candidate policy;
4. counterfactual policies tested;
5. Kreet Neon draw/roll under each policy;
6. whether +2 raw draws reproduces Neon;
7. whether existing decompilation proves branch consumption;
8. whether production behavior changed;
9. Kreet exact-match status after any evidence-backed change;
10. minimal x64dbg experiment plan if still unresolved;
11. ranked second multi-biome target options if needed;
12. evidence-status changes;
13. test count/results;
14. blockers before Brief 06.

Do not begin Brief 06 automatically.

---

# 23. Commit Guidance

If this brief only adds diagnostic experimentation:

```text
test: add zero-candidate RNG diagnostics
```

If runtime/static evidence establishes and changes production behavior:

```text
fix: reproduce zero-candidate RNG consumption
```

Track this brief under:

```text
docs/implementation-briefs/05A-zero-candidate-rng.md
```

---

## Next Step

If Kreet becomes exact:

```text
Brief 06 — full 1,444-body canonical validation
```

If Kreet remains anomalous:

```text
targeted second multi-biome runtime control
```

before expanding to the full dataset.
