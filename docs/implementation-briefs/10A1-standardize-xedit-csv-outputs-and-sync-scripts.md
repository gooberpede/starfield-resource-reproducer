# Brief 10A.1 — Standardize xEdit tabular outputs and synchronize maintained scripts

## Status

Preparatory refactor for `gooberpede/starfield-resource-reproducer`.

This brief follows the canonical occurrence-export gap analysis and prepares the xEdit extraction pipeline for the substantive 10B work.

The task is deliberately narrow:

1. convert the two remaining TSV-producing Starfield export scripts to CSV output;
2. preserve export semantics exactly;
3. establish the four current installed scripts as the repository-maintained copies;
4. remove obsolete legacy script copies from `xedit-scripts/`.

Do **not** implement any 10B data-contract changes in this brief.

Do **not** commit or push unless explicitly asked.

## Standing repository rules

Read and follow the current `AGENTS.md` before making changes.

Active installed scripts:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\
```

Repository-maintained copies:

```text
D:\Projects\starfield-resource-reproducer\xedit-scripts\
```

When modifying an installed script:

1. treat the installed `Edit Scripts` copy as the authoritative working copy;
2. modify it there;
3. copy the completed script to `xedit-scripts\` using the same filename;
4. verify installed and repository copies are byte-for-byte identical;
5. preserve UTF-8 and run required encoding/diff checks.

## Current authoritative installed scripts

```text
Starfield - Export Planet Atmospheric Resources.pas
    -> planet-atmospheric-resources.tsv

Starfield - Export Planet Resource Generation.pas
    -> planet-resource-generation.csv

Starfield - Export Resource Tree.pas
    -> ires-hierarchy.csv

Starfield - Export Planet Directory.pas
    -> planet-directory.tsv
```

These names already conform to the user's current standards.

The repository's existing `xedit-scripts\` directory contains legacy copies. Those legacy copies are not authoritative and may be removed as part of this task.

## Required script changes

Modify only these two installed scripts:

```text
Starfield - Export Planet Atmospheric Resources.pas
Starfield - Export Planet Directory.pas
```

Change their outputs to:

```text
planet-atmospheric-resources.csv
planet-directory.csv
```

The other two installed scripts already emit CSV and must not receive semantic changes:

```text
Starfield - Export Planet Resource Generation.pas
    -> planet-resource-generation.csv

Starfield - Export Resource Tree.pas
    -> ires-hierarchy.csv
```

## CSV conversion requirements

This is a serialization-format refactor only.

For each converted script, preserve exactly:

- row grain;
- selected record population;
- filtering;
- traversal/order;
- column set;
- column order;
- canonical field values;
- source-plugin provenance;
- file-production timestamp behavior;
- header names;
- record/property extraction logic.

The only intended changes are:

```text
delimiter/serialization:
    TSV -> CSV

output filename:
    .tsv -> .csv
```

Do not add, remove, rename, or reorder columns.

Do not introduce 10B fields yet.

## Correct CSV serialization

Do not implement CSV by merely replacing tab characters with commas.

Use correct CSV field escaping.

At minimum:

- comma-separated fields;
- quote a field when required;
- embedded double quotes are escaped by doubling them;
- commas inside values must not create extra columns;
- CR/LF inside a value, if ever encountered, must remain valid CSV rather than corrupting row structure;
- preserve UTF-8 output.

If the two scripts currently duplicate tabular serialization logic, a small local helper inside each script is acceptable.

Do **not** introduce a generalized shared xEdit library/framework in this brief.

## Output-location behavior

Preserve the current/standing behavior:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\
```

is the default output location for generated files.

Do not copy generated CSV outputs into the repository in this brief.

The four current output snapshots already present in `Edit Scripts\` are available for later regression comparison.

## Repository synchronization

After the installed-script changes are complete:

1. remove obsolete legacy `.pas` copies currently under:

```text
D:\Projects\starfield-resource-reproducer\xedit-scripts\
```

2. copy these four current installed scripts into that directory:

```text
Starfield - Export Planet Atmospheric Resources.pas
Starfield - Export Planet Resource Generation.pas
Starfield - Export Resource Tree.pas
Starfield - Export Planet Directory.pas
```

3. verify each installed/repository pair is byte-for-byte identical.

The final repository directory should contain the current maintained script set, not both current and legacy generations.

Do not preserve obsolete legacy scripts merely for historical interest. Their Git history is sufficient.

## xEdit execution boundary

Do not assume that xEdit can be run headlessly or through a supported command-line export workflow.

If Codex can execute the scripts reliably in the installed xEdit environment without unsafe UI automation, it may do so.

If it cannot, that is **not a blocker** for this brief.

In that case:

- make the script changes;
- synchronize repository copies;
- perform static checks;
- report that the user must run the two modified exports manually in xEdit;
- do not invent a fake execution result.

Do not use brittle GUI automation merely to claim the scripts were run.

## Regression comparison plan

The existing old-format snapshots in `Edit Scripts\` provide the before-state:

```text
planet-atmospheric-resources.tsv
planet-directory.tsv
```

After the user runs the modified scripts, the expected new files will be:

```text
planet-atmospheric-resources.csv
planet-directory.csv
```

The semantic regression check must establish:

```text
same columns
same column order
same row count
same row order
same cell values
```

with one expected exception:

```text
ExtractTimestamp
```

may differ because it records file production time and the files are being regenerated.

Do not require byte equality between TSV and CSV outputs.

Do not treat a changed `ExtractTimestamp` as a semantic regression.

If Codex can perform the semantic comparison after fresh CSVs exist, it may report the result. If not, leave the output files untouched and report that comparison is pending user execution/review.

Do not create a new permanent comparison framework or utility unless necessary for a simple one-off check.

## No substantive exporter changes yet

Do **not** implement any findings from Brief 10A beyond serialization normalization.

Specifically, do not yet:

- add IRES `SourceFile`;
- add IRES `ChildSourceFile`;
- add IRES `ExtractTimestamp`;
- alter the Planet Directory schema;
- investigate or change Planet Directory property derivation;
- alter atmospheric-export schema;
- alter Planet Resource Generation schema;
- change reproducer loaders;
- change domain objects;
- change generation behavior;
- create the canonical occurrence exporter.

Those belong to 10B and later briefs.

## Documentation changes

The current `AGENTS.md` already defines script locations, naming, output location, output naming, encoding, and synchronization standards.

Do not rewrite those instructions merely to restate this brief.

Only update documentation if an existing current document explicitly states that either canonical output is TSV and would become factually wrong after this change.

Do not modify unrelated documentation.

## Verification

At minimum:

### Script synchronization

For all four scripts:

```text
installed copy == repository copy byte-for-byte
```

### Static format review

For both modified scripts verify:

```text
output filename uses .csv
delimiter is comma
CSV escaping is correct
header column names/order unchanged
no extraction/filter/order logic changed
```

### Repository checks

Run:

```text
python scripts/check_mojibake.py
git diff --check
```

and any repository-required UTF-8 checks.

If no executable reproducer code changed, the full reproducer test suite is not required solely for this script refactor unless repository policy requires it.

If any non-script implementation file changes unexpectedly, run the appropriate tests and explain why it changed.

## Expected final state

Installed scripts:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\
    Starfield - Export Planet Atmospheric Resources.pas
    Starfield - Export Planet Resource Generation.pas
    Starfield - Export Resource Tree.pas
    Starfield - Export Planet Directory.pas
```

Repository-maintained scripts:

```text
D:\Projects\starfield-resource-reproducer\xedit-scripts\
    Starfield - Export Planet Atmospheric Resources.pas
    Starfield - Export Planet Resource Generation.pas
    Starfield - Export Resource Tree.pas
    Starfield - Export Planet Directory.pas
```

New output contracts:

```text
planet-atmospheric-resources.csv
planet-resource-generation.csv
ires-hierarchy.csv
planet-directory.csv
```

No legacy script copies should remain in `xedit-scripts\`.

## Deliverable report

Report:

1. installed scripts modified;
2. exact serialization changes made;
3. confirmation that export schemas/extraction semantics were not intentionally changed;
4. legacy repository scripts removed;
5. four current scripts copied into `xedit-scripts\`;
6. byte-for-byte synchronization results for all four pairs;
7. whether xEdit execution was possible;
8. whether fresh CSV outputs were produced;
9. whether TSV-vs-CSV semantic regression comparison was performed or remains pending;
10. mojibake/UTF-8/diff-check results;
11. confirmation no 10B data-contract work was performed;
12. confirmation no commit/push was performed.

Suggested commit message after review:

```text
refactor: standardize xedit exports on csv
```
