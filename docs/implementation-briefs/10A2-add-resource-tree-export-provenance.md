# Brief 10A.2 — Add provenance metadata to the Resource Tree export

## Status

Small preparatory xEdit-export change for:

```text
gooberpede/starfield-resource-reproducer
```

This follows Brief 10A.1 and should be completed before the substantive 10B canonical-export work.

Do **not** change reproducer loaders or generation logic in this brief.

Do **not** commit or push unless explicitly asked.

## Purpose

Bring the Resource Tree export into line with the provenance conventions used by the other canonical xEdit datasets.

Current installed script:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\
Starfield - Export Resource Tree.pas
```

Current output:

```text
ires-hierarchy.csv
```

The current dataset lacks file-production timestamp metadata and IRES source-plugin provenance.

## Required schema change

Add these columns:

```text
SourceFile
ExtractTimestamp
ChildSourceFile
```

`ChildSourceFile` is required in addition to the parent `SourceFile`.

The export grain is:

```text
parent IRES × direct child IRES
```

so parent and child are independently sourced canonical records and may not be assumed to come from the same plugin.

The resulting column order should be:

```text
SourceFile
ExtractTimestamp
FormID
EditorID
Name
Rarity
ChildSourceFile
ChildFormID
ChildEditorID
ChildName
ChildRarity
```

If the existing script has a compelling internal reason for a slightly different placement, stop and report it rather than silently changing the contract.

## Field semantics

### SourceFile

Canonical source plugin of the parent IRES record represented by:

```text
FormID
EditorID
Name
Rarity
```

Use the same source-plugin provenance convention as the other xEdit exporters.

### ExtractTimestamp

One file-production timestamp generated once per export run and repeated identically on every output row.

It describes when `ires-hierarchy.csv` was produced, not when an individual IRES record was authored or modified.

Use the same timestamp formatting convention as the existing canonical xEdit exports.

### ChildSourceFile

Canonical source plugin of the child IRES record represented by:

```text
ChildFormID
ChildEditorID
ChildName
ChildRarity
```

For a leaf-parent row with no child resource, this field must be blank along with the other child fields.

Do not fill it from the parent source file merely because the child is absent or happens to share the same plugin.

## Preserve all existing semantics

Do not change:

- selected IRES population;
- parent/child graph relationships;
- traversal order;
- row grain;
- parent or child FormIDs;
- EditorIDs;
- resource names;
- rarity values;
- leaf-row behavior;
- CSV output filename;
- CSV serialization rules.

This task adds provenance metadata only.

Do not add downstream display aliases or non-canonical enrichment.

## Working-copy rules

Follow current `AGENTS.md`.

1. Modify the installed script at:

```text
D:\tools\xEdit.4.1.5p\Edit Scripts\Starfield - Export Resource Tree.pas
```

2. Copy the completed script to:

```text
D:\Projects\starfield-resource-reproducer\xedit-scripts\Starfield - Export Resource Tree.pas
```

3. Verify installed and repository copies are byte-for-byte identical.

Do not modify the other three xEdit scripts.

## xEdit execution

Do not assume xEdit can run headlessly.

If Codex cannot execute the exporter reliably, complete the script change and static verification, then report that manual xEdit execution is required.

Do not use brittle GUI automation.

## Regression plan

Before overwriting or replacing the existing `ires-hierarchy.csv`, preserve the current output for comparison if needed.

After the user runs the modified exporter, compare old and new datasets semantically.

Expected differences:

```text
new SourceFile column
new ExtractTimestamp column
new ChildSourceFile column
```

After projecting those three new columns away, the new file must match the old file exactly in:

```text
header fields
row count
row order
all parent values
all child values
```

Also validate:

- exactly one `ExtractTimestamp` value occurs across all data rows;
- every nonblank parent IRES row has a nonblank `SourceFile`;
- every row with a nonblank `ChildFormID` has a nonblank `ChildSourceFile`;
- every leaf row with blank `ChildFormID` has blank `ChildSourceFile`.

If any existing semantic value changes, treat that as a regression and investigate rather than accepting it.

## Documentation

Update only current documentation that would become factually wrong about the Resource Tree schema.

Do not begin 10B loader or occurrence-export documentation changes.

## Verification

Run:

```text
python scripts/check_mojibake.py
git diff --check
```

and required UTF-8 checks.

Verify installed and repository script copies are byte-for-byte identical.

If a fresh output is available, report the semantic regression results above.

## Deliverable report

Report:

1. exact columns added;
2. source/provenance logic used for parent and child records;
3. confirmation existing graph extraction semantics were unchanged;
4. installed/repository byte-equality result;
5. whether xEdit execution was possible;
6. whether a fresh `ires-hierarchy.csv` was produced;
7. regression-comparison results or pending manual-run status;
8. encoding/mojibake/diff-check results;
9. confirmation no loader/generation/10B work was performed;
10. confirmation no commit/push was performed.

Suggested commit message after review:

```text
feat: add resource tree export provenance
```
