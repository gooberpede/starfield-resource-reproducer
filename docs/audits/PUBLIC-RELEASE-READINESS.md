# Public Release Readiness Audit

Audit date: 2026-09-24

Audited repository: `gooberpede/starfield-resource-reproducer`

Audited branch and commit:

```text
main
13594c419a6691b1a3949f4cacc185121842959d
feat: add production command line interface
```

The branch was synchronized with `origin/main` at the start and end of the
audit. The user-supplied audit brief was untracked and therefore was not part of
the audited commit or reachable-history inventory.

## Executive verdict

```text
READY AFTER MINOR FIXES
```

The implementation is technically coherent, deterministic, runnable through
the documented editable-install workflow, and exact against the full canonical
validation corpus. No credential, prohibited binary, debugger dump, archive,
or other release-blocking artifact was found in HEAD or reachable history.

The repository should not be made public quite yet. The remaining work is
release framing and repository hygiene rather than algorithm remediation: add
the intended license, frame third-party/game-derived data, link and distinguish
the research repository, state the supported installation modes, reconcile the
Planet Directory xEdit working copy, add public xEdit instructions, repair a
small set of stale/broken documentation, and extend `.gitignore` for likely
reverse-engineering artifacts.

Finding counts:

```text
BLOCKER:    0
SHOULD-FIX: 8
OPTIONAL:   4
NO-ACTION:  7
```

## Findings table

| ID | Severity | Location | Area | Finding | Why it matters | Recommended remediation |
|---|---|---|---|---|---|---|
| PRR-01 | SHOULD-FIX | CURRENT-TREE | License | No top-level `LICENSE` exists and `pyproject.toml` has no license metadata. | Public visibility alone does not grant users clear permission to use, modify, or redistribute the original code, scripts, and documentation. | Add `GPL-3.0-or-later` for owner-authored material and matching package metadata. Keep the treatment of game-derived data explicit and separate. |
| PRR-02 | SHOULD-FIX | CURRENT-TREE | Third-party/data framing | The repository lacks a concise non-affiliation, rights-holder, legitimate-copy, and game-derived-data notice. Publication of the five CSVs is described technically but not framed as a conscious third-party-content decision. | The CSVs contain derived Bethesda plugin/runtime metadata and names. GPL should not appear to relicense material the owner may not control. | Add a short notice covering Bethesda/ZeniMax ownership, non-affiliation, legitimate access to Starfield/Creation Kit, the technical/modding purpose of the CSVs, and the boundary of the repository license. Make and record the owner's publication decision for each CSV, especially the oracle. |
| PRR-03 | SHOULD-FIX | CURRENT-TREE | README/navigation | The README does not link `https://github.com/gooberpede/starfield-resource-research`, explain the two-repository ownership split, or give a concrete route for reporting a counterexample. | A new reader cannot readily find the evidence/provenance repository or know where falsifying evidence belongs. | Add the direct research-repository link, the split stated in the release brief, and a concise counterexample-reporting path. A reciprocal research-repo link is desirable but outside this audit. |
| PRR-04 | SHOULD-FIX | CURRENT-TREE | Packaging | The wheel builds and installs, but contains no canonical `data/` files. Its console script reports version successfully and then fails normal/validate-only execution because it resolves a nonexistent installed `Lib/data/` path. | A non-editable installation looks valid until runtime. The documented editable path works, so this is not a broken documented path or a GitHub-release blocker. | Either package the four production inputs and resolve them with package resources, or explicitly state that source checkout plus editable install is the supported v1.0 mode and that wheel/non-editable installation is unsupported. Do not publish the current wheel to PyPI. |
| PRR-05 | SHOULD-FIX | CURRENT-TREE | xEdit synchronization | Three installed exporters are byte-identical to their repository copies. The installed `Starfield - Export Planet Directory.pas` is not: it is version 4 and adds `SolarArrayPower`, `WindTurbinePower`, and `PlanetaryHabitationRank`. The checked-in CSV, tracked exporter, and documented 12-column contract remain mutually consistent. | `docs/CANONICAL-XEDIT-EXPORTS.md` says the installed and repository copies are synchronized. A future export from the active installed copy would produce a different schema and could fail the current exact-header loader contract. | Decide which Planet Directory exporter is canonical, then synchronize the active and tracked copies byte-for-byte. If the extra columns belong to another project, keep that variant under a distinct filename rather than silently replacing the canonical working copy. Re-export only if the approved canonical contract changes. |
| PRR-06 | SHOULD-FIX | CURRENT-TREE | xEdit usability | Script headers identify SF1Edit 4.1.5p and correct output names, and all scripts use `ScriptsPath`; however, the public docs do not give a simple install/select/run procedure or clearly state required game/plugin loading. | A technically capable modder can inspect the scripts but is not given a reproducible path from checkout to canonical export. | Add concise public instructions: supported xEdit/SF1Edit version, copy location, plugin/master prerequisites, record/group selection for each exporter, output location, expected filenames, and overwrite/review expectations. |
| PRR-07 | SHOULD-FIX | CURRENT-TREE | Documentation consistency/links | `docs/V1-VALIDATION-BASELINE.md` still says `planet-directory.csv` is staged for later ingestion and unused by v1.0, although it is now a required production input. Eleven Markdown links in `docs/experiments/08C1-biome-local-cache-assignment-audit.md` use author-machine absolute `D:/Projects/...` targets and are broken for public readers. | These are direct contradictions or broken navigation in otherwise strong technical documentation. | Update the Planet Directory role and replace the 11 absolute links with repository-relative links (preserving useful line references only where stable). Re-run the link check. |
| PRR-08 | SHOULD-FIX | CURRENT-TREE | `.gitignore` | Current ignore rules cover binaries, normal Python artifacts, outputs, and local work, but not `*.trace64`, `*.dmp`, `*.dd32`, `*.dd64`, `*.zip`, `*.7z`, or `*.rar`. | No such artifacts are currently tracked, but these are credible outputs of the documented reverse-engineering workflow and could be accidentally committed later. | Add the listed reverse-engineering dump/archive patterns, with any intentionally publishable archive added back explicitly if a future need arises. |
| PRR-09 | OPTIONAL | CURRENT-TREE | Package metadata | `pyproject.toml` has an accurate name, version, description, README, Python requirement, entry point, and dependencies, but no project URLs, keywords, classifiers, or author/maintainer fields. | These fields improve discovery and provenance, especially if packaging is later broadened, but are not necessary for a GitHub-only release. | Add repository, research/evidence, and issue URLs. Add concise keywords/classifiers and authors/maintainers only if desired. |
| PRR-10 | OPTIONAL | BOTH | Historical/process documents | Current engineering history includes workstation-specific `D:\Projects\...` and `D:\tools\...` paths, transient brief wording, and historical pre-10E commands. No `C:\Users\...` profile path, machine name, credential, or private URL was found. | The material is safe but may confuse readers who mistake historical briefs for current instructions. The same non-sensitive paths remain in history even if current files are edited. | Add a short index/banner stating that implementation briefs and experiment notes are historical records and that README/current contract docs are authoritative. Do not rewrite history merely to remove non-sensitive drive paths. |
| PRR-11 | OPTIONAL | CURRENT-TREE | GitHub metadata | The local remote is correct, but description, homepage, topics, archived state, and authenticated visibility could not be queried because GitHub CLI/authenticated repository metadata was unavailable. Public search did not expose this repository. | Good metadata improves discovery after publication, but does not affect code safety. | Before release, verify `main` is default and the repository is not archived. Suggested description: `Deterministic Python reference implementation of Starfield's planetary inorganic resource-generation algorithm, validated across 1,444 bodies.` Suggested topics: `starfield`, `modding`, `reverse-engineering`, `python`, `xedit`, `bethesda`. |
| PRR-12 | OPTIONAL | CURRENT-TREE | Release semantics | Package/model version `1.0.0` is clear and the README correctly says that it does not imply a tag or GitHub Release. | A public repository does not require a GitHub Release, but a tag can make the audited baseline easy to identify. | After remediation and final recheck, publish both repositories together. An annotated `v1.0.0` tag is useful; a GitHub Release is optional. Do not publish a wheel/PyPI package until PRR-04 is resolved. |
| PRR-13 | NO-ACTION | BOTH | Secrets/privacy | Required credential patterns, embedded-auth URLs, private keys, personal email content, profile paths, UNC/private-network paths, and phone/address-like personal data were not found. The sole Git author address is a GitHub noreply address. | No secret-removal or credential-rotation action is indicated. | None. Repeat a secret scan immediately before visibility changes. |
| PRR-14 | NO-ACTION | BOTH | Proprietary/debug artifacts | No `.exe`, `.dll`, `.pdb`, Ghidra project/database, process/memory dump, debugger trace file, BA2/ESM asset, or archive was found in HEAD or reachable history. Text evidence is focused and derived; it is not a large verbatim reconstructive dump. | The object inventory contains expected source, docs, xEdit-derived CSVs, and focused generated diagnostics only. | None, subject to the human publication decision for derived CSVs in PRR-02. |
| PRR-15 | NO-ACTION | CURRENT-TREE | Production CLI | The documented editable installation, console entry point, CWD-independent defaults, output resolution/fallback, four overrides, manifest, no-overwrite, validate-only, quiet/verbose behavior, and exit-code contract are implemented and tested. No diagnostic/oracle mode is public. | The 10E production interface is release-coherent. | Preserve the contract. |
| PRR-16 | NO-ACTION | CURRENT-TREE | Algorithm/product | The full suite passes 177/177. Canonical validation is 1,444/1,444 exact with 0 mismatches and 0 errors. The product has 7,780 rows and 35 columns; Volii Alpha has 0 BIOME and 2 ATMOSPHERE rows. No algorithm drift, oracle patching, or planet-specific code exception was found. | The protected v1.0 baseline remains intact. | None. |
| PRR-17 | NO-ACTION | CURRENT-TREE | Oracle boundary | The CLI calls `prepare_product` -> `load_production_files`, which accepts only the four production paths and returns an empty oracle mapping. The manifest contains only those four inputs. Tests independently assert this boundary. | `planet-all-resources.csv` cannot influence production output. | None. |
| PRR-18 | NO-ACTION | CURRENT-TREE | Generated hygiene/encoding | Generated environments, caches, build products, and output are ignored and untracked. Runs from external caller directories did not dirty the repository. All tracked files decode as strict UTF-8; the mojibake guard and `git diff --check` pass. | Current generated-output and encoding hygiene are sound. | None. |
| PRR-19 | NO-ACTION | CURRENT-TREE | Security policy | The project is a local, dependency-free-at-runtime data processor with no network service, authentication, or privileged integration. | A boilerplate `SECURITY.md` would add little at this stage. | Use normal GitHub private vulnerability reporting if desired; do not add a policy merely for appearance. |

## Explicit blocker list

No release blockers found.

## History safety

All 28 reachable commits were included in the scan. The required sensitive
patterns returned no credentials, tokens, authorization headers, passwords,
API/client secrets, private-key headers, `C:\Users\...` paths, or UNC server
paths. Historical local paths are limited to non-sensitive `D:\Projects\...`
and `D:\tools\...` workflow references. Content email scanning found no email
addresses; Git metadata uses a GitHub noreply author address.

The complete reachable path inventory contains no executable, DLL, PDB,
Ghidra database, debugger trace, dump, game archive/plugin, or compressed
archive. The largest reachable blobs are expected derived data: the current and
historical Planet Resource Generation CSVs (about 3.27 MB each), the validation
oracle (about 0.96 MB), and the Planet Directory (about 0.19 MB). A historical
larger mismatch report is derived diagnostic output, not a raw process trace.

Based on textual scanning, path/extension inventory, and largest-object review,
full reachable history appears safe to expose as-is. This is a technical
publication-safety conclusion, not a legal opinion about game-derived metadata.

## Proprietary/copyright-sensitive material

HEAD and history contain no Starfield or Creation Kit executable, Bethesda
DLL/PDB, extracted asset archive, raw binary dump, Ghidra project, process dump,
or debugger trace file. The repository contains:

- small structured metadata and names derived from game/plugin records;
- xEdit-derived canonical CSV inputs;
- a runtime-derived validation oracle;
- focused technical evidence such as function addresses, experiment notes, and
  deterministic event ledgers; and
- original Python, Pascal/xEdit scripts, tests, and documentation.

Nothing resembles a large verbatim reconstructive dump. The CSV publication
decision still deserves explicit owner review and the notice in PRR-02.

## Packaging and installation

### Tested modes

| Mode | Result |
|---|---|
| Fresh local clone at audited commit, Python 3.12.14, documented `python -m pip install -e ".[dev]"` | PASS. Installation succeeded after normal access to the package index for isolated `setuptools>=68` and pytest dependencies. |
| Editable console command from a directory with no `data/` | PASS. `--version`, `--help`, `--validate-only`, bare generation, manifest generation, no-overwrite, and all four input overrides worked. |
| Fresh-clone test suite | PASS: 177 tests. |
| Source checkout without installation | UNSUPPORTED/UNDOCUMENTED. `python reproduce.py --version` fails because the `src/` package is not on `sys.path`. This is normal for the chosen layout and is not a release defect while installation remains required. |
| Wheel build | PASS. A 61 KB pure-Python wheel was produced. |
| Clean non-editable wheel installation | INSTALL PASS / RUNTIME FAIL. `--version` works; `--validate-only` exits 1 because the four canonical CSVs are absent. |
| Source archive without `.git` | Product execution passes. The suite reports 175 passed and 2 mojibake-guard failures because that guard intentionally calls `git rev-parse`; the true clone passes all 177. |

The exact currently supported release mode is therefore: clone the repository,
create Python 3.12 environment, and install it editable as documented. The
console command may then be run from any caller directory. Wheel/non-editable
use is not currently supported for normal generation.

### CLI contract results

```text
--version:                     exit 0, version 1.0.0
--help:                        exit 0, documented 10E options only
--validate-only:               exit 0, no files written
bare production invocation:   exit 0
four independent overrides:   exit 0
--no-overwrite collision:      exit 1, existing output preserved
usage errors:                  exit 2 (unit-regression coverage)
explicit write failure:        exit 1, no default fallback
```

Actual process tests passed output-as-directory, output-as-filename, combined
directory+filename, and default-output fallback when `./output` was unusable.
The focused CLI suite also covers existing-manifest refresh, manifest collision
semantics, quiet/verbose output, explicit destination failure, and mutual
exclusions.

## Data publication

The four production inputs are necessary to run the documented product. The
oracle is necessary only for research validation and tests. None is included in
the built wheel; editable installation reads them from the checkout.

| File | Purpose/origin | Rows | Extraction timestamp | Production input | Maintained exporter | Required at runtime | In wheel | Publication status |
|---|---|---:|---|---|---|---|---|---|
| `data/planet-resource-generation.csv` | PNDT -> biome -> effective-RSGD records, ordered resource entries, RSCS, and generation percentages; xEdit export | 7,920 | `2026-09-02 21:20:39` | Yes | Yes | Yes | No | Technically necessary and intentionally described; add third-party framing. |
| `data/ires-hierarchy.csv` | IRES rarity and child-resource graph; xEdit export | 56 | `2026-09-02 23:25:44` | Yes | Yes | Yes | No | Technically necessary and intentionally described; add third-party framing. |
| `data/planet-atmospheric-resources.csv` | Effective atmospheric inorganic resources and inheritance provenance; xEdit export with documented provisional reflection handling | 335 | `2026-09-02 23:00:21` | Yes | Yes | Yes | No | Technically necessary and intentionally described; add third-party framing. |
| `data/planet-directory.csv` | Canonical PNDT body metadata; xEdit export | 1,776 | `2026-09-02 22:57:08` | Yes | Yes, but active installed copy has drifted | Yes | No | Technically necessary; reconcile exporter before a future refresh and add third-party framing. |
| `data/planet-all-resources.csv` | Runtime-derived `Planet x Resource` validation oracle: 6,040 inorganic plus 1,623 organic rows | 7,663 | Not present | No; validation only | No maintained exporter in this repository | No | No | Requires the clearest conscious publication decision because exact upstream semantics/provenance remain partly unresolved. Never a production dependency. |

The CSVs contain structured identifiers, names, classifications, percentages,
and relationships, not game binaries or assets. Publication suitability and
runtime necessity are separate questions: the four production CSVs are needed
for the current editable-install product; the oracle is valuable for
reproducibility but not needed by users running the production CLI.

## xEdit scripts

All four tracked files are Pascal source only. They embed no ESM, BA2, executable,
DLL, PDB, or other game asset and contain no machine-local absolute path. They
resolve their output through `ScriptsPath` and use the current canonical output
filenames. Script headers identify xEdit/SF1Edit 4.1.5p.

Installed-copy comparison:

```text
Planet Atmospheric Resources: byte-identical
Planet Resource Generation:   byte-identical
Resource Tree:                 byte-identical
Planet Directory:              different (material schema extension)
```

The tracked scripts themselves are suitable source for publication, subject to
licensing and the documentation/synchronization findings above. No deprecated
script filename is present in `xedit-scripts/`.

## Licensing

Current status: no repository license and no package license metadata.

The preferred `GPL-3.0-or-later` license is suitable for owner-authored Python,
xEdit scripts, tests, and documentation if that is the owner's intended grant.
Practical remediation should include the full license text, SPDX/package
metadata, and a brief third-party-content notice. Downstream distribution of
GPL-covered source should retain notices and provide the corresponding source
under the same terms.

The license notice should state that it applies only to material for which the
repository owner holds the relevant rights. It should not claim to relicense
Bethesda/ZeniMax game-derived CSV content, resource names, plugin names, or
trademarks. Those items should remain attributed to their respective rights
holders and framed as technical/modding interoperability data. This audit makes
no legal conclusion about the applicable rights or exceptions; the five CSVs,
especially the runtime-derived oracle, remain the appropriate scope for a
human/legal publication review.

## README and documentation

The README accurately explains the model, v1.0 scope/non-scope, 1,444-body
validation, 10-body CK/retail holdout, Creation Kit address boundary, editable
installation, production CLI, output destination and grain, the four inputs,
oracle separation, xEdit exporter location, and diagnostic deferral. Its CLI
examples match actual behavior. No old CLI option appears in current user
instructions; old options occur only in clearly historical implementation
briefs.

All README-relative links resolve. Across all tracked Markdown, the 11 broken
links are confined to one experiment document and are author-machine absolute
links. Strict UTF-8 validation passed for every tracked file.

The main public-navigation omissions are PRR-03 and PRR-06. The main factual
documentation defect is the stale Planet Directory role in
`docs/V1-VALIDATION-BASELINE.md`.

## Fresh-reader assessment

A technically capable Starfield modder can understand the algorithm's purpose,
scope, reliability, basic editable installation, invocation, output location,
and validation boundary within five minutes. The most likely confusion points
are:

1. There is no license or third-party-data/non-affiliation notice.
2. The research repository is not linked, so evidence ownership and deeper
   provenance are hard to find.
3. The README does not explicitly warn that a normal wheel installation is
   currently nonfunctional for default generation.
4. The xEdit scripts lack a simple public install/run recipe, and one active
   installed working copy has drifted from the tracked canonical exporter.
5. Counterexample reporting is philosophically described but has no concrete
   destination or evidence checklist on the landing page.

## Public-safe file inventory

### SAFE TO PUBLISH AS-IS

- `src/starfield_resource_reproducer/`: original Python source; technically
  safe, pending repository licensing.
- `tests/` and `scripts/check_mojibake.py`: original tests/tooling.
- `validation/`: small generated mismatch header and a focused deterministic
  382-event model diagnostic; no raw debugger trace.
- `xedit-scripts/*.pas`: source-only exporters with no embedded game asset or
  absolute path; publication-safe after the owner applies the intended license.
- `.gitignore`, `reproduce.py`: no sensitive content, although `.gitignore`
  should be extended before release.

### SAFE BUT SHOULD BE BETTER DOCUMENTED

- `README.md`, `pyproject.toml`, `AGENTS.md`, and current contract/domain docs.
- `docs/experiments/` and `docs/implementation-briefs/`: valuable engineering
  history, but should be clearly labeled historical; one experiment has broken
  author-machine links and briefs contain non-sensitive local drive paths.
- `docs/CANONICAL-XEDIT-EXPORTS.md`: strong provenance detail, but public run
  instructions and current synchronization status need correction.

### REQUIRES HUMAN/LEGAL REVIEW

- `data/*.csv`, separately for each file, with special attention to
  `planet-all-resources.csv` because it is validation-only and lacks an in-repo
  maintained exporter/extraction timestamp.
- Third-party names, identifiers, and trademark references in the CSVs and
  prose, to be handled by concise attribution/non-affiliation framing rather
  than an unsupported relicensing claim.

### MUST NOT BE PUBLIC

No tracked or reachable-history file was identified in this category.

## Security and disclosure posture

The tool performs local deterministic file processing and has no runtime
dependencies, network service, credential handling, or remote execution path.
A dedicated `SECURITY.md`, issue-template suite, Code of Conduct, governance
document, or badge set is not required for initial release. Add such files later
only if they serve an actual support or disclosure workflow.

## Suggested remediation sequence

1. Add `GPL-3.0-or-later`, package license metadata, and the concise
   third-party/non-affiliation/data notice. Record the owner decision to publish
   all five CSVs.
2. Reconcile the installed/tracked Planet Directory exporter and decide whether
   the additional columns belong under a separate script/output contract.
3. Update README navigation: research-repo link and ownership split,
   counterexample reporting, supported editable-install boundary, and xEdit
   install/run instructions.
4. Correct the stale Planet Directory statement and the 11 absolute Markdown
   links; add a short historical-docs framing note.
5. Add reverse-engineering dump/archive ignore patterns.
6. Add optional package/GitHub metadata.
7. Re-run the complete checklist below, then coordinate visibility changes for
   both repositories. Tag `v1.0.0` if desired; a GitHub Release is optional.

## Final release checklist

- Confirm `main` points to the reviewed remediation commit and is synchronized
  with `origin/main`.
- Run a current secret scan over HEAD and all reachable history without printing
  discovered values.
- Inventory largest blobs and prohibited binary/debug/archive extensions.
- Confirm `LICENSE`, package license metadata, and third-party/data notices.
- Confirm all five CSV publication decisions and canonical hashes/row counts.
- Confirm all four tracked xEdit scripts match the intended active working
  copies and that their outputs match documented schemas.
- From a fresh clone and Python 3.12 environment, run the documented install,
  `--version`, `--help`, `--validate-only`, bare generation, `--manifest`,
  `--no-overwrite`, and all four overrides from a CWD without `data/`.
- Run `python -m pytest`; require all 177 current tests (or a reviewed higher
  count) to pass.
- Confirm canonical validation reports `1,444 / 1,444`, 0 mismatches, 0 errors.
- Confirm the product has 35 columns, 7,780 rows (7,445 BIOME and 335
  ATMOSPHERE), and Volii Alpha has exactly 2 ATMOSPHERE / 0 BIOME rows.
- Confirm production CLI/manifest paths do not load or describe
  `planet-all-resources.csv` as a production input.
- Run strict UTF-8 validation, `python scripts/check_mojibake.py`, Markdown link
  checking, and `git diff --check`.
- Confirm generated output/build/cache/environment directories are untracked.
- Verify GitHub description, topics, default branch, archived state, and the
  planned visibility state for both repositories.
- Review the final diff before changing visibility or creating any tag/release.

## Audit actions and non-actions

Created by this audit:

```text
docs/audits/PUBLIC-RELEASE-READINESS.md
```

No source, algorithm, test, canonical data, xEdit script, package metadata,
license, `.gitignore`, or existing documentation file was modified. Temporary
clean clones, environments, wheels, and generated products were created only
outside the repository.

No repository visibility change, tag, GitHub Release, PyPI publication,
history rewrite, commit, or push was performed. No GitHub setting was changed.
Authenticated GitHub metadata was unavailable, so the audit can confirm that no
visibility-changing action occurred, but it does not independently attest the
server-side visibility flag.
