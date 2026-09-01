# Brief 08A.1 — Mojibake cleanup and automated repository guardrail

## Objective

Clean up the mojibake identified during review of the 08A diff and add a reusable repository-level check so future text changes fail loudly with exact filenames and line numbers instead of relying on visual inspection.

This is a **cleanup/guardrail task only**. Do not alter generation behavior, validation semantics, tests unrelated to text integrity, or the 08A implementation itself.

## Context

`AGENTS.md` already prohibits mojibake, including the sequence:

```text
ÔÇö
```

However, review of the 08A diff showed mojibake in changed Markdown content. The user cannot reliably distinguish a mangled em dash visually and should not be asked to hunt large documents manually.

The repository therefore needs a machine-checkable invariant.

## Required cleanup

Inspect the files touched by 08A and fix any actual mojibake sequences introduced or present in the changed regions.

Known examples seen in review include text equivalent to:

```text
## Phase 6 ÔÇö Mismatch-Driven Reverse Engineering

# Brief 08A ÔÇö Correct Everywhere/category-6 handling...
### PROVEN LIVE ÔÇö Fermi VIII-b / OceanDefaultRes
### PROVEN LIVE ÔÇö Kreet control
Expected hypothesis only ÔÇö do not force...
Zeta Ophiuchi I ÔÇö unexpected Chlorine...
Indum IV-d ÔÇö unexpected Chlorine...
Bara VII-d ÔÇö unexpected Nickel...
```

Replace corrupted punctuation with the intended valid Unicode character, normally an em dash:

```text
—
```

Do not blindly replace arbitrary byte sequences without first confirming they are mojibake.

## Automated guardrail

Add a small reusable repository check that scans tracked text files for known mojibake markers and exits nonzero when any are found.

### Behavior

The check should:

1. scan repository text files only;
2. skip binary/generated cache/build directories;
3. report:
   - relative filename;
   - line number;
   - offending marker or a short escaped representation;
4. exit with status `1` if any violation exists;
5. exit `0` when clean;
6. be deterministic and fast enough for routine local use.

### Initial marker set

At minimum detect these common corruption markers:

```text
ÔÇö
â€”
â€“
â€˜
â€™
â€œ
â€
Â 
```

You may add a few additional highly characteristic UTF-8/Windows-1252 mojibake sequences if they are low-risk.

Avoid overbroad matching that would flag valid non-English Unicode text.

## Implementation preference

Use the simplest maintainable approach that fits the existing repository tooling.

Acceptable examples:

- a small Python script under `scripts/` or equivalent;
- a focused pytest test that scans tracked text files;
- both, if the project convention makes that useful.

Prefer a standalone script plus a thin test only if that does not create unnecessary duplication.

If using Git to enumerate files, prefer tracked files so local scratch/output files do not create noise.

## Documentation

Update `AGENTS.md` or nearby contributor documentation only as needed to point to the automated check.

Keep the wording concise, e.g.:

> Run the mojibake check before commit; it reports exact files and lines for prohibited encoding corruption.

Do not expand this into a general style-guide rewrite.

## Validation

Run:

1. the new mojibake check;
2. the relevant test suite;
3. `git diff --check`.

All must pass.

Also deliberately verify the guardrail once with a temporary local test fixture or equivalent so you know it actually fails on a known marker, then remove/revert that temporary corruption before finishing.

Do **not** leave a deliberately corrupted fixture committed unless the implementation uses a unit-test fixture isolated from the repository scan target.

## Non-goals

Do not:

- change category-6/Everywhere logic;
- touch validation mismatch logic;
- alter generated validation outputs except if line-ending/encoding normalization is genuinely required;
- rewrite large Markdown files for style;
- normalize all punctuation globally;
- introduce an encoding migration;
- commit or push.

## Deliverable

Return:

1. files changed;
2. mojibake instances corrected;
3. description of the new guardrail;
4. exact command to run it locally;
5. validation results;
6. confirmation that no commit/push was performed.

Suggested commit message after review:

```text
chore: add mojibake validation guard
```
