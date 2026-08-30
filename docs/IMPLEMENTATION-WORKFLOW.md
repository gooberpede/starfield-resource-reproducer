# Implementation Workflow

## Purpose

Define how architecture/reverse-engineering work in ChatGPT discussions is translated into Codex implementation work without losing evidence, scope, or reproducibility.

## Roles

### User

- owns the repository and approves changes;
- runs Creation Kit, x64dbg, Ghidra, game/runtime, and xEdit experiments as needed;
- supplies datasets/traces;
- decides when to accept or reject implementation proposals.

### ChatGPT

Primary responsibilities:

- architecture;
- domain-rule synthesis;
- reverse-engineering interpretation;
- experiment design;
- implementation specifications;
- review criteria.

When implementation work is ready, ChatGPT produces a downloadable Markdown **implementation brief**.

### Codex

Primary responsibilities:

- inspect repository state;
- implement approved brief;
- add/update tests;
- run tests/validation;
- report exact changes and unresolved issues.

Codex should not independently redefine recovered Starfield behavior merely because another implementation seems cleaner.

## Brief-Driven Development

Prefer one scoped brief per meaningful unit of work.

Suggested location:

```text
docs/implementation-briefs/
```

Suggested naming:

```text
001-project-bootstrap.md
002-data-loader.md
003-prng-validation.md
004-core-generation.md
...
```

An implementation brief should normally contain:

1. context;
2. goal;
3. authoritative inputs;
4. current domain rules relevant to the task;
5. required changes;
6. explicit non-goals;
7. acceptance criteria;
8. required tests;
9. documentation updates;
10. uncertainties/guardrails.

## Before Codex Implements a Brief

Codex should read:

```text
AGENTS.md
README.md
docs/ARCHITECTURE.md
docs/DOMAIN-RULES.md
docs/BACKLOG.md
```

and the specific implementation brief.

Then inspect current code before editing.

Do not assume a brief was written against an unchanged repository.

## Scope Discipline

If a brief asks for a data loader, do not also redesign the CLI, replace the package manager, introduce a database, and refactor unrelated modules.

If a necessary prerequisite is missing:

- make the smallest compatible prerequisite change;
- document it clearly;
- do not expand into speculative architecture.

## Evidence Changes

A domain-rule change is different from a code change.

If new trace evidence corrects the algorithm:

1. update `docs/DOMAIN-RULES.md`;
2. update/add a regression test capturing the new evidence;
3. alter implementation;
4. rerun worked cases;
5. rerun canonical validation where appropriate.

Never make the code "fit" canonical results by silently adding unexplained special cases.

## Canonical Validation

Expected-output oracle:

```text
planet-all-resources.csv
```

Current generation scope:

```text
ResourceCategory == "Inorganic"
```

Deprecated:

```text
Starfield_InorganicResources_Canonical.csv
```

Codex must not reintroduce the deprecated file as an expected-output fixture.

## Validation Ladder

Use progressively broader checks.

### Level 1 — unit behavior

Examples:

- FormID parsing;
- RSGD ordering;
- IRES child candidate construction;
- PRNG conversion.

### Level 2 — worked trace cases

Required baseline:

```text
Oberon
Mimas
Decaran VII-b
Kreet
```

Tests should assert intermediate decisions where evidence exists.

### Level 3 — full canonical comparison

Compare every reproducible inorganic body against `planet-all-resources.csv`.

Produce mismatch artifacts rather than hiding failures.

## Handling Mismatches

A mismatch is research evidence.

For each mismatch classify, where possible:

```text
static-input problem
PRNG-sequence problem
biome-order problem
RSGD-resolution problem
Everywhere/Special problem
Common-selection problem
descendant-graph problem
cache/reuse problem
unknown edge case
```

Do not immediately patch individual planet names.

Prefer smallest groups of mismatches that share a plausible mechanic.

## Implementation Brief Handoff

The user will periodically ask ChatGPT to generate a Markdown brief for Codex.

Expected workflow:

```text
discussion / evidence
        |
        v
ChatGPT implementation brief
        |
        v
user gives brief to Codex
        |
        v
Codex implements + tests
        |
        v
user reports result / diff
        |
        v
ChatGPT + user review architecture/evidence
```

This deliberate separation is a feature: it keeps design/reverse-engineering reasoning distinct from code-edit execution.

## Codex Completion Report

For each brief, Codex should report:

- files changed;
- behavior implemented;
- tests added/changed;
- commands run;
- test results;
- canonical validation impact if applicable;
- assumptions made;
- remaining questions;
- any deviation from the brief.

Avoid vague completion messages such as "implemented successfully" without evidence.

## Git Workflow

Prefer a clean working tree before starting a brief where practical.

Recommended commit style:

```text
feat: add canonical data loader
test: add Mimas descendant regression
fix: preserve RSGD weighted order
docs: record Kreet biome shuffle result
```

One implementation brief may produce more than one commit when that improves reviewability.

## Generated / Local Research Artifacts

Large traces, scratch diffs, transient reports, local extraction dumps, and experimental files should not automatically enter source control.

Use `.gitignore` and an agreed local scratch directory.

Canonical small CSV inputs may be tracked if the repository strategy explicitly chooses to do so.

## Architectural Decisions

For decisions that materially change boundaries, add a short note to `docs/ARCHITECTURE.md`.

Do not create an elaborate ADR system during v0.1 unless the project genuinely needs one.

## Stop Conditions

Codex should stop and report rather than invent behavior when:

- static inputs conflict;
- a required field is absent;
- a test expectation contradicts `docs/DOMAIN-RULES.md`;
- PRNG behavior cannot reproduce known trace anchors;
- a requested change requires choosing between materially different domain interpretations not settled by the brief.

In those cases the issue returns to the architecture/reverse-engineering discussion.
