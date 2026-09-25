# Release-Readiness Remediation Brief — `starfield-resource-reproducer`

## Purpose

Remediate the remaining accepted findings from the public-release readiness audit for:

```text
gooberpede/starfield-resource-reproducer
```

PRR-05 (Planet Directory exporter v4 reconciliation) has already been completed separately and committed. Do not reopen it in this task.

This remediation should prepare the reproducer repository for final release-readiness recheck and coordinated public release with:

```text
gooberpede/starfield-resource-research
```

The goal is repository/publication hygiene, documentation, licensing, navigation, and release framing.

Do **not** reopen the recovered inorganic-generation algorithm unless a genuine contradiction is discovered.

---

# 1. Settled decisions

## PRR-01 — licence

Adopt:

```text
GPL-3.0-or-later
```

for project-authored material for which the repository owner holds the relevant rights, including:

```text
Python source
xEdit scripts
tests
project-authored documentation
```

Add the complete GPLv3 licence text at repository root.

Add appropriate package licence metadata.

Do not imply that GPL relicenses Bethesda/ZeniMax-derived data, official names, identifiers, trademarks, or other third-party material.

---

## PRR-02 — third-party/game-derived data framing

Harmonize the reproducer's approach with the existing treatment in:

```text
gooberpede/starfield-outpost-network
THIRD-PARTY-NOTICE.md
```

Do not invent a materially different rights theory for overlapping Starfield-derived data.

The reproducer should clearly state that:

- project-authored material is licensed under GPL-3.0-or-later;
- official Starfield names, identifiers, classifications, relationships, and other game-derived records remain subject to their respective rightsholders' rights;
- those records are not relicensed by the repository's GPL grant;
- the repository distributes normalized technical/modding/reference data, not Bethesda game executables, ESM/BA2 archives, textures, models, audio, complete string tables, or similar raw game assets;
- extraction/runtime provenance documents source and transformation but does not claim Bethesda/ZeniMax approval;
- the project is independent and unofficial and is not affiliated with or endorsed by Bethesda Game Studios or Microsoft.

The owner has already decided to publish the five current CSVs under this framing:

```text
data/planet-resource-generation.csv
data/ires-hierarchy.csv
data/planet-atmospheric-resources.csv
data/planet-directory.csv
data/planet-all-resources.csv
```

The four production inputs and the validation-only oracle must remain clearly distinguished.

Do not reopen the broader practical-risk assessment already performed for the overlapping Starfield reference-data scope in `starfield-outpost-network`.

A concise root third-party notice is preferred. Avoid copying tracker-specific material such as React/Vite/font/favicon notices that do not apply here.

---

## PRR-03 — repository navigation and counterexample routing

Add a direct link to:

```text
https://github.com/gooberpede/starfield-resource-research
```

Clearly explain the two-repository ownership split:

```text
starfield-resource-research
    evidence status
    reverse-engineering findings
    trace/static-analysis provenance
    historical investigation

starfield-resource-reproducer
    executable reference model
    regression suite
    production CLI
    canonical xEdit-derived inputs
    consumer export
```

The reciprocal reproducer link already exists in the research repository.

Counterexample/issue routing must distinguish the repositories:

### Algorithm/evidence counterexamples

Examples:

```text
planet/biome output contradicts recovered algorithm
Creation Kit or retail result contradicts model
new runtime evidence
executable/version drift
evidence-status dispute
```

Route these to:

```text
starfield-resource-research
```

### Software/reproducer defects

Examples:

```text
CLI bug
installation problem
loader/exporter defect
manifest/output issue
test regression
product/schema bug
```

Route these to:

```text
starfield-resource-reproducer
```

Give a concise evidence checklist for algorithm counterexamples, consistent with the research README:

```text
Starfield or Creation Kit version
body/planet
reproduction steps
observed result
expected/current reproducer result
```

Do not duplicate the research repository's evidence record into the reproducer.

---

## PRR-04 — supported installation mode

For v1.0, explicitly support:

```text
GitHub source checkout
+
editable installation
```

using the documented pattern:

```text
python -m pip install -e ".[dev]"
```

The installed console command must remain usable from caller directories that do not contain `data/`.

Explicitly state that conventional wheel/non-editable installation is **not supported for v1.0**, because the canonical production data is not packaged into the wheel.

Do not implement wheel support in this task.

Do not publish a wheel or PyPI package.

Add a backlog item for:

```text
PyPI/wheel distribution
    package canonical production data correctly
    use an installed-resource strategy
    verify non-editable execution
    add expanded package metadata
```

Expanded package metadata belongs with that future packaging task except for licence metadata required now.

---

## PRR-06 — public xEdit instructions

Add concise, reproducible public instructions for the maintained xEdit/SF1Edit exporters.

Document:

```text
supported/tested xEdit/SF1Edit version: 4.1.5p
where scripts are copied/installed
required Starfield/plugin/master loading
what record/group selection to use for each exporter
how to run the script
where output is written
expected output filename
overwrite/review expectations
```

Cover all maintained canonical exporters under:

```text
xedit-scripts/
```

Do not duplicate large script internals in prose.

The Planet Directory exporter is now v4 and must be documented as such.

---

## PRR-07 — documentation consistency and broken links

Apply the remaining PRR-07 remediation.

The stale Planet Directory role was already addressed as part of PRR-05. Do not rework the v4 contract unnecessarily.

Repair the eleven author-machine Markdown links in:

```text
docs/experiments/08C1-biome-local-cache-assignment-audit.md
```

Replace:

```text
D:/Projects/...
```

targets with repository-relative links where the destination exists in the repository.

Preserve useful historical line/address/context references where practical, but do not retain broken machine-local navigation.

Re-run the repository Markdown link check.

Inspect current documentation for any remaining contradictions introduced or exposed by the completed PRR-05 work, but do not turn this task into broad documentation rewriting.

---

## PRR-08 — `.gitignore`

Extend `.gitignore` to protect likely reverse-engineering/debug/archive artifacts, including:

```text
*.trace64
*.dmp
*.dd32
*.dd64
*.zip
*.7z
*.rar
```

Keep existing ignores for binaries, Python artifacts, output, local work, etc.

If a future archive is intentionally publishable, it can be added back explicitly.

Do not remove legitimate tracked files merely because a new ignore pattern would match them historically.

---

## PRR-09 — package metadata

Do only the package metadata required by the present release:

```text
GPL-3.0-or-later licence metadata
```

Project URLs may be added if useful, especially:

```text
Repository
Research
Issues
```

Do not spend release-remediation effort on:

```text
keywords
classifiers
author/maintainer metadata
expanded package-discovery metadata
```

unless they are trivial and clearly useful.

The broader metadata cleanup belongs to the future PyPI/wheel-distribution backlog item.

---

## PRR-10 — historical/process-document framing

Add a concise framing note/index/banner making clear that:

```text
docs/implementation-briefs/
docs/experiments/
```

contain historical engineering/research records and may preserve:

```text
superseded commands
old local paths
intermediate terminology
historical implementation assumptions
```

Current authoritative behavior lives in:

```text
README.md
current contract/domain docs
current source/tests
```

Do not rewrite retained history merely to remove non-sensitive:

```text
D:\Projects\...
D:\tools\...
```

paths.

Do not sanitize historical documents in a way that damages useful provenance.

---

## PRR-11 — GitHub metadata

Where accessible, prepare or set useful repository metadata for public release.

Verify:

```text
default branch = main
repository is not archived
```

Suggested description:

```text
Deterministic Python reference implementation of Starfield's planetary inorganic resource-generation algorithm, validated across 1,444 bodies.
```

Suggested topics:

```text
starfield
modding
reverse-engineering
python
xedit
bethesda
```

If authenticated metadata/settings are unavailable to Codex, record the exact manual owner actions still required rather than guessing.

Do not change repository visibility in this task unless explicitly instructed separately.

---

## PRR-12 — release semantics

The owner has approved an annotated:

```text
v1.0.0
```

tag **after** remediation and final release-readiness recheck.

Do not create the tag during this remediation.

Do not create a GitHub Release during this remediation.

The GitHub Release question remains deliberately deferred and does not block:

```text
remediation
final recheck
tag decision
public visibility decision
```

Document this clearly if release instructions currently imply otherwise.

---

## PRR-13 through PRR-19

No remediation is required.

Preserve the audited conclusions around:

```text
secrets/privacy
proprietary/debug artifacts
production CLI
algorithm/product baseline
oracle boundary
generated-output/encoding hygiene
security-policy posture
```

Do not introduce unnecessary files such as:

```text
SECURITY.md
issue-template suite
Code of Conduct
governance boilerplate
badges
```

unless a concrete new need is found.

---

# 2. Backlog updates

Add or update backlog entries for:

## A. Wheel / PyPI distribution

Include:

```text
package the four canonical production inputs correctly
replace source-tree-relative data lookup with installed-resource handling
support clean non-editable/wheel execution
verify CLI outside repository
add expanded package metadata
decide PyPI publication
```

## B. Expanded diagnostics interface

Retain the already-deferred richer diagnostic CLI/interface work as post-v1.0.

Do not implement it here.

## C. GitHub Release decision

If there is an appropriate backlog/release-notes location, record that the project should decide later whether a GitHub Release adds value beyond:

```text
public repositories
+
annotated v1.0.0 tag
```

Do not force a decision now.

---

# 3. Files to inspect

At minimum inspect:

```text
README.md
pyproject.toml
.gitignore
AGENTS.md
docs/BACKLOG.md
docs/IMPLEMENTATION-WORKFLOW.md
docs/CANONICAL-XEDIT-EXPORTS.md
docs/V1-VALIDATION-BASELINE.md
docs/BIOME-INORGANIC-RESOURCES.md
docs/ARCHITECTURE.md
docs/DOMAIN-RULES.md
docs/experiments/08C1-biome-local-cache-assignment-audit.md
xedit-scripts/
```

Create as needed:

```text
LICENSE
THIRD_PARTY_NOTICES.md
```

Use the existing repository naming convention if there is a strong reason to prefer singular `THIRD-PARTY-NOTICE.md`; consistency within this repository matters more than mechanically copying another repo's filename.

Do not modify:

```text
docs/audits/PUBLIC-RELEASE-READINESS.md
```

The original audit is a historical record of the audited `13594c4` state and must remain unchanged.

A later final recheck should record resolved findings separately.

---

# 4. Scientific and product constraints

This task is not algorithm work.

Do not change:

```text
MT19937 behavior
RNG draw sequence
biome shuffle
Everywhere handling
Special/Common selection
five-tree guard
shared-eight guard
fallback assignment
family caching
occurrence semantics
oracle boundary
```

Protected validation baseline:

```text
1,444 / 1,444 exact
0 mismatches
0 generation errors
```

Protected product baseline:

```text
7,780 rows
7,445 BIOME
335 ATMOSPHERE
35 columns
```

Protected Volii Alpha control:

```text
0 BIOME
2 ATMOSPHERE
```

The production CLI must remain independent of:

```text
data/planet-all-resources.csv
```

Do not add planet-specific exceptions or oracle-derived generation logic.

---

# 5. Third-party notice harmonization

Use the `starfield-outpost-network` treatment as the conceptual reference for overlapping Starfield-derived data.

The reproducer notice should be smaller because it does not need tracker-specific notices for:

```text
favicon artwork
React
Vite
Rolldown
Google Fonts
browser-shipped dependencies
```

Retain the same key boundary:

```text
project-authored GPL-covered material
!=
third-party/game-derived material
```

Prefer concise wording that can be kept consistent across both projects.

If helpful, add a short provenance pointer to the canonical xEdit-export documentation rather than reproducing detailed extraction history in the root notice.

---

# 6. README expectations after remediation

A technically capable Starfield modder should be able to determine quickly:

```text
what the reproducer does
current v1.0 validation status
what it does not model
how to clone/install it
that editable install is the supported v1.0 mode
that wheel/non-editable install is currently unsupported
how to run the production CLI
where output goes
what the four production inputs are
what the validation oracle is
where the canonical xEdit exporters live
how to regenerate the source data
where the research/evidence repository is
which repository should receive which kind of issue/counterexample
how licensing and game-derived data are separated
```

Keep README concise enough to remain a usable landing page.

Prefer links to durable detail documents rather than duplicating them.

---

# 7. Testing and verification

After remediation, run the full verification set.

## Repository hygiene

Run:

```text
git diff --check
strict UTF-8 validation
mojibake scan
Markdown internal-link check
```

Confirm no generated output/build/cache/environment artifacts are tracked.

## Test suite

Run:

```text
python -m pytest
```

Require all current tests to pass.

The post-PRR-05 baseline is at least:

```text
183 passed
```

A higher reviewed count is acceptable.

## Canonical validation

Require:

```text
1,444 / 1,444 exact
0 mismatches
0 generation errors
```

## Product validation

Require:

```text
7,780 total rows
7,445 BIOME
335 ATMOSPHERE
35 columns
```

## Volii Alpha

Require:

```text
0 BIOME
2 ATMOSPHERE
```

## CLI smoke tests

At minimum test:

```text
starfield-resource-reproducer --version
starfield-resource-reproducer --help
starfield-resource-reproducer --validate-only
starfield-resource-reproducer
```

from the supported editable-install workflow and from a caller directory without local `data/`.

Do not attempt to "fix" wheel execution in this task.

## Oracle boundary

Confirm normal production execution does not load:

```text
data/planet-all-resources.csv
```

## xEdit synchronization/documentation

Confirm all tracked maintained exporters are the intended canonical versions and current documentation matches their filenames/version expectations.

PRR-05's completed v4 Planet Directory state must remain intact.

---

# 8. Release-safety checks

Repeat the high-value safety checks from the audit after remediation:

```text
secret-pattern scan over HEAD
secret-pattern scan over reachable history
prohibited binary/debug/archive extension inventory
largest reachable blob review
absolute local-path scan for active instructions
```

Do not print discovered credential values if any are encountered.

Historical non-sensitive drive paths alone are not a defect.

If a genuine secret or prohibited artifact is discovered, stop and report it as a blocker rather than attempting silent cleanup.

---

# 9. Scope controls

Do not:

```text
change repository visibility
create a tag
create a GitHub Release
publish a wheel
publish to PyPI
rewrite history
force-push
implement expanded diagnostics
implement wheel/package-data support
modify the inorganic generation algorithm
reopen PRR-05
edit the original PUBLIC-RELEASE-READINESS.md verdict/findings
```

Do not commit or push unless explicitly asked.

---

# 10. Durable remediation/recheck record

The original audit must remain unchanged:

```text
docs/audits/PUBLIC-RELEASE-READINESS.md
```

Create a separate durable remediation/recheck document only if appropriate for the repository's existing audit pattern.

Preferred eventual path:

```text
docs/audits/PUBLIC-RELEASE-READINESS-RECHECK.md
```

However, this implementation task should primarily perform the approved fixes.

If a final recheck is better treated as a separate subsequent task, do not pre-emptively declare the repository `READY`.

The expected sequence remains:

```text
remediation
→ ChatGPT diff review
→ commit/sync
→ final release-readiness recheck
→ review
→ coordinated public release decision
→ annotated v1.0.0 tag
→ GitHub Release decision later
```

---

# 11. Deliverables back to the user

Report:

1. files changed;
2. PRR findings remediated;
3. licence files/metadata added;
4. exact third-party/game-data framing implemented;
5. confirmation all five CSVs remain published under the settled boundary;
6. README/research-repo navigation changes;
7. issue/counterexample routing added;
8. supported-installation wording added;
9. wheel/PyPI backlog entry added;
10. expanded package-metadata backlog treatment;
11. xEdit public-run instructions added;
12. broken-link repair result;
13. `.gitignore` additions;
14. historical-doc framing added;
15. GitHub metadata changed or remaining manual actions;
16. tag/GitHub Release status;
17. full test result;
18. canonical validation result;
19. production product result;
20. Volii Alpha result;
21. oracle-boundary result;
22. encoding/mojibake/link/`git diff --check` results;
23. secret/history/prohibited-artifact recheck result;
24. confirmation original audit document remained unchanged;
25. confirmation PRR-05 remained intact;
26. confirmation no algorithm semantics changed;
27. confirmation no visibility/tag/release/package-publication/history rewrite occurred;
28. residual issues, if any;
29. recommended commit message.

---

# 12. Acceptance criteria

The remediation is complete when:

- GPL-3.0-or-later clearly covers project-authored material;
- Bethesda/ZeniMax-derived records are clearly outside that GPL grant;
- the third-party/data framing is harmonized with the Outpost Tracker approach;
- all five CSV publication decisions are explicit and consistently documented;
- reproducer ↔ research navigation is clear;
- algorithm/evidence counterexamples and software bugs route to the correct repositories;
- editable/source-checkout installation is clearly the supported v1.0 mode;
- wheel/non-editable installation is explicitly deferred;
- wheel/PyPI + expanded package metadata are in backlog;
- xEdit exporters have public reproducible usage instructions;
- remaining PRR-07 broken links are fixed;
- `.gitignore` protects likely RE/debug/archive artifacts;
- historical process docs are clearly framed as historical;
- GitHub metadata is set or documented for manual owner action;
- `v1.0.0` tag remains planned but uncreated pending final recheck;
- GitHub Release remains deliberately undecided;
- PRR-13 through PRR-19 remain unchanged/no-action;
- original `PUBLIC-RELEASE-READINESS.md` remains unchanged;
- PRR-05 remains resolved and intact;
- all tests and protected validation/product baselines pass;
- no unrelated algorithm or packaging implementation work is introduced.

Suggested commit message after review:

```text
chore: prepare reproducer for public release
```
