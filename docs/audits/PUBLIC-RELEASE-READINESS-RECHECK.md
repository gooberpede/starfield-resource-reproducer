# Public Release Readiness Recheck

## Recheck identity

Recheck date: 2026-09-25

Repository: `gooberpede/starfield-resource-reproducer`

Rechecked baseline:

```text
branch: main
commit: 397362a2b0a60acbd2eea0ab4841690867779b9b
subject: chore: prepare reproducer for public release
origin/main: 397362a2b0a60acbd2eea0ab4841690867779b9b
```

`git ls-remote origin refs/heads/main` independently returned the same commit,
so the local `HEAD`, local `origin/main`, and server-side `origin/main` were
synchronized for this recheck.

The tracked working tree was clean at the start. The user-supplied recheck brief,
`docs/implementation-briefs/REPRODUCER-FINAL-PUBLIC-RELEASE-RECHECK-BRIEF.md`,
was the sole untracked file. It was not part of the rechecked commit or the
reachable-history inventory.

This document is the post-remediation recheck of
[`PUBLIC-RELEASE-READINESS.md`](PUBLIC-RELEASE-READINESS.md), which records the
historical pre-remediation state at
`main @ 13594c419a6691b1a3949f4cacc185121842959d`. The original audit was not
edited; its SHA-256 remained
`4e361c74d02ebeb60e47b065034d2dc54d1afa104792805e612c1143b4de27bc`.

## Executive verdict

```text
READY
```

No new actionable findings were identified.

```text
Unresolved BLOCKER findings:    0
Unresolved SHOULD-FIX findings: 0
```

The repository is technically ready for a coordinated public release with
`gooberpede/starfield-resource-research`. Remaining actions are owner-controlled
release operations and deliberately deferred distribution decisions, not defects
in this baseline.

## Finding disposition

| ID | Recheck disposition | Verification |
|---|---|---|
| PRR-01 | RESOLVED | The complete GPLv3 text is present in `LICENSE`; the project grant and package metadata state `GPL-3.0-or-later`. |
| PRR-02 | RESOLVED | `THIRD-PARTY-NOTICE.md` separates owner-authored GPL material from game-derived records, identifies the project as independent and unofficial, and claims no rightsholder approval. |
| PRR-03 | RESOLVED | README navigation links the research repository, explains ownership, routes issue types, and gives a concrete counterexample evidence checklist. |
| PRR-04 | RESOLVED AS DOCUMENTATION | The supported v1.0 mode is explicitly source checkout plus editable installation. Wheel/non-editable normal execution is explicitly unsupported and deferred. |
| PRR-05 | RESOLVED SEPARATELY | Planet Directory exporter/data/loader/tests retain the approved v4 reconciliation and metadata-only boundary. |
| PRR-06 | RESOLVED | Public xEdit instructions identify version, install location, canonical load set, record selections, run procedure, output location, and filenames. |
| PRR-07 | RESOLVED | Current documentation describes Planet Directory accurately and the repository-wide Markdown check found zero broken internal links. |
| PRR-08 | RESOLVED | `.gitignore` includes the required debugger dump and archive patterns without removing a legitimate tracked file. |
| PRR-09 | PARTIALLY RESOLVED / DEFERRED BY DESIGN | Licence metadata and project URLs are present. Broader package/PyPI metadata remains with the deferred distribution work. |
| PRR-10 | RESOLVED | Index pages frame implementation briefs and experiments as historical records and point readers to current authoritative sources. |
| PRR-11 | RESOLVED AS OWNER-ACTION TRACKING | The backlog records exact GitHub metadata checks and suggested values. Authenticated recheck results and remaining owner actions are below. |
| PRR-12 | DEFERRED BY DESIGN | An annotated `v1.0.0` tag is approved only after this recheck and owner review. Whether to create a GitHub Release remains open and non-blocking. |
| PRR-13 through PRR-19 | NO-ACTION PRESERVED | Secret/privacy, artifact, CLI, algorithm/product, oracle-boundary, hygiene/encoding, and security-policy conclusions remain sound. |

## Material remediation verified

### Licence and third-party boundary

`LICENSE` is the complete 674-line GNU GPL version 3 text. The README,
`THIRD-PARTY-NOTICE.md`, and `pyproject.toml` consistently express the intended
`GPL-3.0-or-later` grant for project-authored material for which the owner holds
the relevant rights.

The notice does not purport to relicense Starfield/Bethesda/ZeniMax-derived
names, identifiers, classifications, relationships, or records. It states that
the project is independent and unofficial, is not affiliated with or endorsed
by Bethesda Game Studios or Microsoft, and claims no rightsholder approval. Its
approach is conceptually aligned with the settled `starfield-outpost-network`
notice while correctly omitting that application's unrelated artwork,
dependency, font, and bundling notices.

### Five-CSV publication boundary

All intended CSVs are tracked and present:

| File | Data rows | Role |
|---|---:|---|
| `data/planet-resource-generation.csv` | 7,920 | Production input |
| `data/ires-hierarchy.csv` | 56 | Production input |
| `data/planet-atmospheric-resources.csv` | 335 | Production input |
| `data/planet-directory.csv` | 1,776 | Production input |
| `data/planet-all-resources.csv` | 7,663 | Validation-only oracle |

README and third-party framing distinguish the four production inputs from the
oracle and deliberately publish all five as game-derived/reference data outside
the owner-authored GPL grant. Code-path inspection and tests confirm that normal
production loading returns an empty oracle mapping, `prepare_product` receives
only the four production paths, and manifest metadata lists only those four
inputs. The production CLI contains no oracle option or oracle load path.

### Planet Directory v4

The tracked and installed copies of all four maintained xEdit scripts were
accessible and byte-identical. For
`Starfield - Export Planet Directory.pas`, both copies had SHA-256:

```text
5fdae92aa88534797d824a79af345301ca80c33e8961627d992dbc9e72710731
```

The script remains version 4. The canonical CSV has 1,776 rows, 1,776 unique
Planet FormIDs, and the exact approved schema:

```text
SourceFile,ExtractTimestamp,PlanetFormID,PlanetEditorID,PlanetName,BodyType,StarSystemID,SystemName,ParentPlanetID,PlanetID,PlanetNotLandable,OceanWorld,SolarArrayPower,WindTurbinePower,PlanetaryHabitationRank
```

The CSV retained its reviewed SHA-256:

```text
c460062747126a2168109739e75742d325cedf54b98577e5a017b5108ec5eb90
```

`SolarArrayPower`, `WindTurbinePower`, and `PlanetaryHabitationRank` remain
directory metadata. They do not enter generation, RNG, oracle comparison, or the
35-column consumer product. The loader and tests retain the exporter contract
that Solar/Wind may be blank when a landable body's environmental combination
is unrecognized; the current canonical corpus has zero such blanks among
landable non-Orbital rows.

### Canonical xEdit reproduction

The public instructions identify xEdit/SF1Edit 4.1.5p, copying scripts into the
active `Edit Scripts` directory, the record/group selection for each exporter,
the Apply Script procedure, `ScriptsPath` output location, expected stable
filename, and replacement/diff expectations.

They document the current canonical v1.0 official ESM load set and roles:

```text
Starfield.esm       base game
ShatteredSpace.esm  Shattered Space DLC / Va'ruun planetary records
SFBGS00D.esm        Terran Armada DLC / new orbital records
SFBGS050.esm        Terran Armada DLC / new X-Tech resource
```

The same instructions state that this set defines the current corpus rather
than a permanent universal rule, that future official DLC can change it, and
that modded exports are a different corpus that must not silently replace the
canonical inputs without an explicit contract/provenance revision.

### README and supported installation

A new technical reader can determine the model's purpose, v1.0 meaning,
validation status, scope/non-scope, supported installation, run/output behavior,
input/oracle roles, xEdit location and regeneration path, repository ownership,
issue routing, counterexample requirements, licence scope, and game-derived-data
boundary from the README.

The direct research link is
`https://github.com/gooberpede/starfield-resource-research`. Algorithm/evidence
counterexamples route there and request the Starfield or Creation Kit version,
body/planet, reproduction steps, observed result, and expected/current
reproducer result. Software, CLI, exporter, and product defects route to this
repository.

The documented command succeeded in the current Python 3.12 environment:

```text
python -m pip install -e ".[dev]"
```

README explicitly limits v1.0 support to a GitHub source checkout plus editable
installation and states that conventional wheel/non-editable execution is not
supported because canonical production data is not packaged. No wheel-support
requirement was imposed by this recheck.

### Historical records, ignore rules, and deferred work

`docs/implementation-briefs/README.md` and `docs/experiments/README.md` identify
their directories as historical records that may retain superseded commands,
old local paths, intermediate terminology, and historical assumptions. They
point to README, current architecture/domain documentation, source, and tests as
authoritative. All eleven formerly broken links in
`docs/experiments/08C1-biome-local-cache-assignment-audit.md` now resolve; the
complete check found zero broken internal Markdown links.

`.gitignore` contains `*.trace64`, `*.dmp`, `*.dd32`, `*.dd64`, `*.zip`,
`*.7z`, and `*.rar`, in addition to executable/binary, Python, generated-output,
and local-work protections. Current ignored generated material consists only of
expected local work, environments, caches, output, and editable-install metadata.

The backlog retains wheel/PyPI distribution, canonical package-data and
installed-resource strategy, non-editable execution, expanded package metadata,
PyPI decision, expanded diagnostics, GitHub metadata owner actions, and the
GitHub Release decision. None has accidentally become a stable public interface.

## Verification results

### Scientific and product baseline

```text
python -m pytest:                 183 passed in 11.52s
canonical validation:            1,444 / 1,444 exact
canonical mismatches:            0
generation errors:               0
product rows:                    7,780
BIOME rows:                      7,445
ATMOSPHERE rows:                 335
product columns:                 35
Volii Alpha BIOME rows:          0
Volii Alpha ATMOSPHERE rows:     2
```

The suite directly asserts deterministic canonical validation, deterministic
product regeneration and ordering, the exact 35-column schema, the four-input
manifest, no production oracle load, and the v4 metadata-only boundary. Source
inspection found no planet-specific FormID exception in production code and no
public diagnostic/oracle CLI flag. No algorithm drift or oracle patching was
found.

A separate direct `load_project_data` / `validate_all_planets` run also reported
1,444 generation planets, 1,444 oracle planets, 1,444 exact matches, zero
mismatches, and zero generation errors.

The generated product header does not contain `SolarArrayPower`,
`WindTurbinePower`, or `PlanetaryHabitationRank`.

### CLI smoke tests

After the editable installation, all required commands were run from a new
caller directory under the system temporary directory with no local `data/`:

| Command | Result |
|---|---|
| `starfield-resource-reproducer --version` | Exit 0; `1.0.0` |
| `starfield-resource-reproducer --help` | Exit 0; documented production options only |
| `starfield-resource-reproducer --validate-only` | Exit 0; 7,780 rows validated; no files written |
| `starfield-resource-reproducer` | Exit 0; product written under caller-local `output/` |

This also confirms that default canonical inputs resolve independently of the
caller's current working directory.

### Encoding, links, and repository hygiene

```text
strict UTF-8 validation:          114 tracked files, 0 failures
mojibake scan:                    passed
Markdown internal-link check:    58 Markdown files, 0 broken links
git diff --check:                 passed before the recheck document
```

Final checks after creating this document are recorded in the completion report
and must also pass before it is retained.

Generated `output/`, `build/`, `dist/`, `*.egg-info/`, pytest/Python caches,
temporary work, and virtual environments remain untracked and covered by ignore
rules. No generated artifact was added to the release inventory.

## History and publication safety

The safety scan covered `HEAD` and all 31 reachable commits. High-confidence
patterns found no provider token, embedded-auth URL, secret assignment, private
key header, or non-noreply author email. Generic path patterns produced two
reviewed false positives only: the original audit's literal `C:\Users\...`
example and the CLI help's `C:\Exports` example. Historical non-sensitive
`D:\Projects\...` and `D:\tools\...` paths remain acceptable in clearly
historical records.

The complete reachable path inventory contains no executable, DLL, PDB, Ghidra
project/database, debugger trace, process/memory dump, game archive/plugin, or
compressed archive. The largest reachable blobs remain expected derived data:

| Approximate size | Reachable path | Assessment |
|---:|---|---|
| 3,270,063 bytes | historical `data/PlanetResourceGeneration_v5.csv` and current `data/planet-resource-generation.csv` | Expected canonical source data |
| 956,217 bytes | `data/planet-all-resources.csv` | Expected validation oracle |
| 197,286 / 187,373 bytes | current/historical `data/planet-directory.csv` | Expected canonical source data |
| 81,077 bytes | historical `validation/full-canonical-mismatches.csv` | Expected derived diagnostic |
| 80,246 bytes | historical/current atmospheric export | Expected canonical source data |
| 72,955 bytes | `validation/07A-dense-planet-events.csv` | Expected focused diagnostic |

Based on the credential scan, full path/extension inventory, manual false-positive
review, and largest-object review, the full reachable history still appears
technically safe to publish as-is. This is a technical publication-safety
finding, not a legal opinion about third-party game-derived records.

## GitHub metadata

Authenticated GitHub API access was available during the recheck and reported:

```text
visibility:     private
default branch: main
archived:       false
description:    unset
homepage:       unset
topics:         unset
```

Private visibility is the expected pre-release state and was not changed.
`main` and the non-archived state pass. Before coordinated visibility change,
the owner should set or confirm the suggested description and topics:

```text
Deterministic Python reference implementation of Starfield's planetary inorganic resource-generation algorithm, validated across 1,444 bodies.
```

```text
starfield
modding
reverse-engineering
python
xedit
bethesda
```

The empty optional homepage is not a release blocker.

## Remaining manual release actions

1. Confirm this recheck document and the companion research-repository readiness
   result are both retained on synchronized `main` branches.
2. Set or verify the reproducer description and topics above.
3. Coordinate the visibility change for both repositories so they become public
   together.
4. Create the annotated `v1.0.0` tag only after the final owner review and at the
   planned release point.
5. Decide separately, later, whether a GitHub Release adds value. Do not publish
   the current wheel to PyPI unless the deferred packaging work is completed.

## Final owner release checklist

- [ ] Confirm both repositories are synchronized.
- [ ] Confirm both repositories have a `READY` final recheck.
- [ ] Verify `main` is the default branch and both repositories are not archived.
- [ ] Verify description and topics.
- [ ] Repeat the secret scan immediately before visibility change if desired.
- [ ] Confirm `LICENSE` and third-party notices.
- [ ] Confirm the deliberate five-CSV publication boundary.
- [ ] Confirm all four xEdit exporters and canonical export documentation.
- [ ] Confirm at least 183 tests pass.
- [ ] Confirm canonical validation is 1,444 / 1,444 exact.
- [ ] Confirm product totals are 7,780 / 7,445 / 335 / 35 columns.
- [ ] Confirm Volii Alpha is 0 BIOME / 2 ATMOSPHERE.
- [ ] Confirm production oracle isolation.
- [ ] Confirm there are no uncommitted tracked changes other than the reviewed
      release documentation being intentionally committed.
- [ ] Make both repositories public together.
- [ ] Create the annotated `v1.0.0` tag after the visibility/release decision as
      planned.
- [ ] Decide separately whether a GitHub Release adds value.

## Release boundary

This recheck created only:

```text
docs/audits/PUBLIC-RELEASE-READINESS-RECHECK.md
```

It did not change repository visibility, create a tag, create a GitHub Release,
publish a wheel or PyPI package, rewrite history, modify the inorganic-generation
algorithm, commit, or push. The original audit remained historically intact.
