# Final Release-Readiness Recheck Brief — `starfield-resource-reproducer`

## Purpose

Perform the final release-readiness recheck for:

```text
gooberpede/starfield-resource-reproducer
```

after completion and commit of:

1. PRR-05 Planet Directory exporter v4 reconciliation; and
2. the remaining approved public-release remediation.

This is a **recheck**, not a new remediation task.

The purpose is to determine whether the repository is now:

```text
READY
```

for coordinated public release with:

```text
gooberpede/starfield-resource-research
```

The original audit must remain historically intact.

---

# 1. Recheck posture

Do not reopen settled design decisions unless a concrete contradiction is found.

Do not perform broad remediation during this task.

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
modify the inorganic-generation algorithm
```

Do not commit or push unless explicitly asked.

If a new blocker or material regression is found, report it clearly and stop rather than silently fixing it.

---

# 2. Durable audit history

The original audit remains:

```text
docs/audits/PUBLIC-RELEASE-READINESS.md
```

It records the audited pre-remediation state at:

```text
main @ 13594c419a6691b1a3949f4cacc185121842959d
```

Do not edit it.

Create the final recheck as:

```text
docs/audits/PUBLIC-RELEASE-READINESS-RECHECK.md
```

The recheck should reference the original audit and record which findings were resolved, deferred, or remained no-action.

---

# 3. Expected finding disposition

Verify rather than assume the following expected outcome.

## Resolved by remediation

Expected resolved findings:

```text
PRR-01  Licence
PRR-02  Third-party/data framing
PRR-03  README/navigation and issue routing
PRR-04  Supported installation-mode documentation
PRR-05  Planet Directory exporter v4 reconciliation
PRR-06  Public xEdit instructions
PRR-07  Documentation consistency and broken links
PRR-08  .gitignore hardening
PRR-10  Historical/process-document framing
PRR-11  Repository metadata owner-action tracking
```

PRR-09 is only partially acted upon by design:

```text
licence metadata
project URLs if present
```

Broader PyPI/package metadata is deliberately deferred.

PRR-12 is deliberately deferred in part:

```text
annotated v1.0.0 tag planned after final recheck
GitHub Release decision still deferred
```

## No-action findings

Expected unchanged/no-action:

```text
PRR-13 through PRR-19
```

Do not manufacture work for these findings unless the recheck discovers a new contradiction.

---

# 4. Verify exact current baseline

At the start of the recheck, record:

```text
current branch
current HEAD commit
origin/main commit
working-tree status
repository visibility if accessible
default branch if accessible
archived state if accessible
```

Require:

```text
branch = main
HEAD synchronized with origin/main
clean tracked working tree
```

The user-supplied recheck brief may be untracked; note that separately and exclude it from the audited commit/history inventory if applicable.

Do not assume the previous remediation commit hash; record the actual current synchronized commit.

---

# 5. Licensing and third-party boundary

Verify current repository state contains:

```text
LICENSE
THIRD-PARTY-NOTICE.md
```

Confirm:

- `LICENSE` contains the complete GPLv3 text;
- project licence is expressed as `GPL-3.0-or-later`;
- `pyproject.toml` reflects the intended SPDX/package licence metadata;
- the licence grant clearly applies to project-authored material for which the owner holds the relevant rights;
- Starfield/Bethesda/ZeniMax-derived names, identifiers, classifications, relationships, records, and trademarks are not purportedly relicensed under GPL;
- the project is identified as unofficial/independent;
- no rightsholder approval is claimed.

Confirm the notice remains conceptually harmonized with the settled approach used by `starfield-outpost-network`, without importing irrelevant tracker-specific dependency/artwork notices.

---

# 6. Five-CSV publication boundary

Verify all five intended CSVs remain present:

```text
data/planet-resource-generation.csv
data/ires-hierarchy.csv
data/planet-atmospheric-resources.csv
data/planet-directory.csv
data/planet-all-resources.csv
```

Verify current documentation distinguishes:

```text
four production inputs
vs.
planet-all-resources.csv validation-only oracle
```

Confirm:

- the production CLI does not load the oracle;
- the oracle is not listed as a production manifest input;
- all five CSVs are framed as game-derived/reference data outside the project-authored GPL grant;
- the owner publication decision is documented consistently.

Do not reopen the broader game-data publication-risk assessment absent a genuinely new fact.

---

# 7. PRR-05 Planet Directory v4 preservation

Verify the completed PRR-05 work remains intact.

Expected Planet Directory exporter:

```text
xedit-scripts/Starfield - Export Planet Directory.pas
Version: 4
```

Expected exact schema:

```text
SourceFile,ExtractTimestamp,PlanetFormID,PlanetEditorID,PlanetName,BodyType,StarSystemID,SystemName,ParentPlanetID,PlanetID,PlanetNotLandable,OceanWorld,SolarArrayPower,WindTurbinePower,PlanetaryHabitationRank
```

Expected canonical data:

```text
1,776 rows
1,776 unique PlanetFormIDs
```

Expected v4 metadata fields:

```text
SolarArrayPower
WindTurbinePower
PlanetaryHabitationRank
```

Confirm these remain metadata-only and do not influence:

```text
generation
RNG
oracle comparison
35-column consumer product
```

Confirm current loader behavior still distinguishes:

```text
exporter contract:
    Solar/Wind may be blank on a landable body if v4 cannot resolve a recognized environmental combination

current canonical corpus:
    current landable non-Orbital rows have populated Solar/Wind values
```

Confirm tracked and installed canonical xEdit script copies remain byte-identical if the installed copies are accessible.

---

# 8. Canonical xEdit export documentation

Verify public xEdit instructions are sufficient to reproduce the current canonical source inputs.

The canonical v1.0 official ESM load set must be documented as:

```text
Starfield.esm
ShatteredSpace.esm
SFBGS00D.esm
SFBGS050.esm
```

with roles:

```text
Starfield.esm
    base game

ShatteredSpace.esm
    Shattered Space DLC
    Va'ruun planetary records

SFBGS00D.esm
    Terran Armada DLC
    new orbital records

SFBGS050.esm
    Terran Armada DLC
    new X-Tech resource
```

Verify documentation makes clear that:

- this is the current v1.0 canonical corpus load set;
- it is not a permanent universal rule;
- future official DLC may change the canonical corpus;
- modded ESM/plugin exports represent a different corpus;
- a different corpus must not silently replace the canonical repository inputs without explicit contract/provenance revision.

Also verify for each maintained exporter:

```text
tested xEdit/SF1Edit version
copy/install location
record/group selection
run procedure
output location
expected filename
```

---

# 9. README/public-reader usability

Approach the repository as a technically capable Starfield modder who has never seen the project.

Within five minutes, they should be able to determine:

```text
what the reproducer does
what v1.0 means
validation status
scope and non-scope
how to install it
supported installation mode
unsupported wheel/non-editable state
how to run it
where output goes
what the four production inputs are
what the validation oracle is
where the xEdit exporters live
how to regenerate canonical inputs
where the research/evidence repository is
which repository receives which issue type
how to report an algorithm/evidence counterexample
licence scope
third-party/game-derived-data boundary
```

Verify direct link to:

```text
https://github.com/gooberpede/starfield-resource-research
```

Verify repository ownership split remains clear.

Verify issue routing remains:

```text
algorithm/evidence counterexamples
    -> starfield-resource-research

software/CLI/exporter/product defects
    -> starfield-resource-reproducer
```

Verify algorithm counterexample guidance requests at least:

```text
Starfield or Creation Kit version
body/planet
reproduction steps
observed result
expected/current reproducer result
```

---

# 10. Supported installation mode

Verify documentation accurately states that v1.0 supports:

```text
GitHub source checkout
+
editable installation
```

using:

```text
python -m pip install -e ".[dev]"
```

Confirm installed console execution works from a caller directory without local:

```text
data/
```

Verify documentation explicitly says:

```text
wheel/non-editable normal execution is not supported for v1.0
```

Do not treat this as a blocker, because that limitation is deliberate and documented.

Verify backlog includes future work for:

```text
wheel/PyPI distribution
canonical package-data strategy
installed-resource lookup
non-editable execution
expanded package metadata
PyPI decision
```

---

# 11. Backlog and deferred work

Verify backlog/documentation retains the deliberately deferred items:

```text
wheel/PyPI support
expanded package metadata
expanded diagnostics interface
GitHub repository metadata owner actions
GitHub Release decision
```

Verify no deferred item has accidentally been implemented or exposed as a stable public interface.

The annotated:

```text
v1.0.0
```

tag is approved only **after this final recheck**.

Do not create it during the recheck.

The GitHub Release decision remains open and must not block a READY verdict.

---

# 12. Historical document framing

Verify historical records under:

```text
docs/implementation-briefs/
docs/experiments/
```

are clearly framed as historical engineering/research records.

The framing should make clear that they may retain:

```text
superseded commands
historical assumptions
old local paths
intermediate terminology
```

and that current authoritative behavior lives in:

```text
README.md
current contract/domain documentation
current source/tests
```

Do not require history rewriting for non-sensitive local paths.

Verify the eleven previously broken links in:

```text
docs/experiments/08C1-biome-local-cache-assignment-audit.md
```

are now valid repository-relative links.

---

# 13. `.gitignore`

Verify `.gitignore` includes protection for:

```text
*.trace64
*.dmp
*.dd32
*.dd64
*.zip
*.7z
*.rar
```

along with the existing binary/Python/output/local-work protections.

Confirm no legitimate tracked file was removed merely because of these new patterns.

---

# 14. GitHub metadata

Where authenticated metadata is accessible, verify:

```text
default branch = main
repository is not archived
```

Check description/topics if they were set.

Suggested description remains:

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

If authenticated settings remain unavailable, state that clearly and list the exact manual owner actions remaining.

Lack of authenticated settings access alone is not a release blocker.

Do not change visibility during the recheck.

---

# 15. Protected scientific baseline

Run the complete current test suite:

```text
python -m pytest
```

Expected minimum after PRR-05/remediation:

```text
183 passed
```

A reviewed higher count is acceptable.

Run canonical validation and require:

```text
1,444 / 1,444 exact
0 mismatches
0 generation errors
```

Confirm no:

```text
algorithm drift
oracle patching
planet-specific exception
```

---

# 16. Protected product baseline

Run the production pipeline and require:

```text
7,780 total rows
7,445 BIOME
335 ATMOSPHERE
35 columns
```

Verify:

```text
Volii Alpha
    0 BIOME
    2 ATMOSPHERE
```

Confirm deterministic product ordering/schema remains intact.

Confirm no Solar/Wind/Habitation metadata fields leaked into the 35-column consumer product.

---

# 17. CLI smoke tests

From the supported editable-install workflow, run from a caller directory that does not contain local `data/`:

```text
starfield-resource-reproducer --version
starfield-resource-reproducer --help
starfield-resource-reproducer --validate-only
starfield-resource-reproducer
```

Expected:

```text
all succeed
```

Also verify default canonical inputs resolve independently of caller CWD.

Do not retest wheel support as a release requirement.

If desired, confirm the known unsupported state remains accurately documented rather than accidentally changed.

---

# 18. Oracle boundary

Confirm normal production CLI execution does not load:

```text
data/planet-all-resources.csv
```

Inspect code/import/call paths and tests rather than relying only on documentation.

Confirm manifest metadata includes only the four production inputs.

This remains release-critical.

---

# 19. Safety and history scans

Repeat the high-value safety scans across both:

```text
HEAD
reachable history
```

for:

```text
credentials
tokens
embedded-auth URLs
passwords/secrets
private-key material
personal/private paths
proprietary executables
DLL/PDB
Ghidra project/database
memory/process dumps
debugger traces
game archives/plugins
compressed archives
unexpected large blobs
```

Do not print actual discovered secret values.

Expected result:

```text
no release-blocking secret or prohibited artifact
```

Historical non-sensitive:

```text
D:\Projects\...
D:\tools\...
```

paths are not blockers when confined to clearly historical records.

Inventory largest reachable blobs and confirm they remain expected derived data/artifacts.

---

# 20. Encoding, links, and repository hygiene

Run:

```text
strict UTF-8 validation
mojibake scan
Markdown internal-link check
git diff --check
```

Expected:

```text
0 broken internal Markdown links
no unintended malformed encoding
git diff --check passes
```

Confirm generated artifacts are untracked:

```text
output/
dist/
build/
*.egg-info/
pytest caches
temporary export files
virtual environments
```

---

# 21. Recheck verdict

Return one final verdict:

```text
READY
READY AFTER MINOR FIXES
NOT READY
```

Expected target:

```text
READY
```

Do not force READY if evidence contradicts it.

Classify any new finding as:

```text
BLOCKER
SHOULD-FIX
OPTIONAL
NO-ACTION
```

If no new actionable findings exist, say so explicitly.

---

# 22. Durable recheck document

Create:

```text
docs/audits/PUBLIC-RELEASE-READINESS-RECHECK.md
```

Recommended structure:

## Recheck identity

Record:

```text
date
repository
branch
commit
relationship to original audit
```

## Executive verdict

Expected:

```text
READY
```

## Finding disposition

Summarize:

```text
PRR-01 ... resolved
...
PRR-05 ... resolved separately by v4 reconciliation
...
PRR-09 ... deferred package metadata portion
PRR-12 ... tag approved post-recheck / GitHub Release deferred
PRR-13–19 ... no-action preserved
```

## Material remediation verified

Summarize:

```text
licence
third-party/data boundary
navigation/routing
supported install mode
Planet Directory v4
xEdit public instructions
documentation/link repairs
.gitignore
historical-doc framing
backlog/deferred work
```

## Verification results

Record:

```text
tests
canonical validation
product rows/columns
Volii Alpha
CLI smoke tests
oracle boundary
encoding/mojibake
Markdown links
git diff --check
secret/history scan
artifact/blob inventory
```

## History/publication safety

State explicitly whether full reachable history still appears technically safe to publish.

## Remaining manual release actions

Only include genuine owner actions, for example:

```text
verify GitHub archived/default-branch/description/topics if Codex lacks authenticated settings access
coordinate visibility change for both repositories
create annotated v1.0.0 tag after owner review
decide later whether to create a GitHub Release
```

## Release boundary

Explicitly state that the recheck did not:

```text
change visibility
create a tag
create a GitHub Release
publish a package
rewrite history
commit or push
```

---

# 23. Final release checklist

Include a concise final owner checklist suitable for immediate use before visibility change.

At minimum:

```text
confirm both repos synchronized
confirm both repos READY
verify main/default branch and archived state
verify description/topics
repeat secret scan if desired
confirm LICENSE and third-party notices
confirm five CSV publication boundary
confirm all four xEdit exporters and canonical docs
confirm 183+ tests
confirm 1,444 / 1,444
confirm 7,780 / 7,445 / 335 / 35 columns
confirm Volii Alpha 0 / 2
confirm oracle isolation
confirm no uncommitted tracked changes
make both repositories public together
create annotated v1.0.0 tag after visibility/release decision as planned
decide separately whether a GitHub Release adds value
```

Do not execute these owner actions during the recheck unless explicitly instructed.

---

# 24. Deliverables back to the user

Report:

1. final verdict;
2. exact rechecked branch/commit;
3. whether HEAD == origin/main;
4. whether the tracked working tree was clean before the recheck;
5. current finding disposition;
6. number of unresolved BLOCKER findings;
7. number of unresolved SHOULD-FIX findings;
8. licence verification result;
9. third-party/data-boundary verification result;
10. five-CSV publication-boundary result;
11. PRR-05/v4 preservation result;
12. canonical ESM load-set documentation result;
13. README/navigation/routing result;
14. supported editable-install result;
15. wheel/non-editable documentation result;
16. xEdit documentation result;
17. historical-doc/link result;
18. `.gitignore` result;
19. backlog/deferred-work result;
20. GitHub metadata result or exact manual actions remaining;
21. full test-suite result;
22. canonical 1,444-body result;
23. product row/column result;
24. Volii Alpha result;
25. CLI smoke-test result;
26. oracle-boundary result;
27. encoding/mojibake/link/`git diff --check` result;
28. secret/history scan result;
29. prohibited-artifact/largest-blob result;
30. whether full reachable history appears technically safe to publish;
31. durable recheck file created;
32. files changed by the recheck;
33. confirmation original audit remained unchanged;
34. confirmation no visibility/tag/release/package/history rewrite occurred;
35. remaining owner release actions;
36. recommended commit message for the recheck document.

---

# 25. Acceptance criteria

The final recheck is complete when:

- the current synchronized remediation commit is identified;
- the original audit remains unchanged;
- the separate recheck document exists;
- all resolved PRRs are verified rather than merely assumed;
- deferred items remain intentionally deferred;
- all no-action findings remain sound;
- PRR-05/v4 is preserved;
- licensing and game-derived-data boundaries are coherent;
- README/navigation/issue routing are public-ready;
- supported installation mode is accurate;
- canonical xEdit reproduction instructions are sufficient;
- all tests pass;
- canonical validation remains exact;
- production output remains unchanged;
- Volii Alpha control passes;
- oracle isolation is intact;
- history/safety/artifact scans remain clean;
- link/encoding/repository-hygiene checks pass;
- no release action is performed during the recheck;
- a clear final READY / READY AFTER MINOR FIXES / NOT READY verdict is recorded.

Suggested commit message after review, if the recheck document is retained:

```text
docs: recheck reproducer for public release
```
