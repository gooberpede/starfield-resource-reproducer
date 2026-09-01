# Brief 08C — Read-only audit: biome-local cached-family assignment

## Purpose

Perform a **read-only code audit** of the current reproducer to determine exactly how cached Common-family configurations are represented in per-biome results.

This is a subtask of Brief 08C. It is **not** a new implementation brief.

Do not edit code, tests, documentation, validation artifacts, or generated files. Do not commit or push.

The audit exists to answer one question before we decide what Brief 08D, if any, should contain:

> Does the current reproducer correctly propagate a cached Common family's root and descendants into every later biome that reuses that family, or does it only preserve the family at planet level / cache level?

## New live evidence

A Jaffa VII-b Creation Kit Galaxy View Apply trace through `FUN_1415DCFB0` has now established the following behavior.

### PROVEN LIVE — cached Common-family reuse populates the current biome

A first biome selected Lead (`000057C1`) as its Common root and generated the family:

```text
Lead       000057C1
Tungsten   000057C4
Titanium   000057C6
Dysprosium 000057C2
```

A later biome selected Lead again.

The engine recognized that the Lead family configuration already existed and copied the cached family directly into the current biome work object:

```asm
1415DD229  mov [rdi+50],eax   ; Lead       000057C1
1415DD22F  mov [rdi+54],eax   ; Tungsten   000057C4
1415DD235  mov [rdi+58],eax   ; Titanium   000057C6
1415DD23B  mov [rdi+5C],eax   ; Dysprosium 000057C2
1415DD241  mov [rdi+60],eax   ; 00000000
```

Therefore:

> **PROVEN LIVE:** a Common-family cache hit is not merely a planet-level deduplication/RNG optimization. The cached root and descendant configuration is assigned to the later biome that selects the same Common root.

The cache hit consumes no descendant-generation RNG because the existing family configuration is reused.

## Why this audit is needed

The current reproducer validates **1,444 / 1,444 planet-wide inorganic resource sets**, but a CK sanity-check of per-biome forecasts exposed incorrect biome-local output.

Examples:

```text
Bara VII-d
Hills
  forecast: none
  CK:       Iron
```

```text
Indum IV-d
Swamp
  forecast: Water
  CK:       Water, Iron, Tantalum

Sandy Desert
  forecast: none
  CK:       Copper, Fluorine, Gold, Antimony

Wetlands
  forecast: Water
  CK:       Water, Copper, Fluorine, Gold, Antimony
```

```text
Zeta Ophiuchi I
Swamp
  forecast: Water
  CK:       Water, Lead, Silver

Frozen Dunes
Deciduous Forest
Savanna
  forecast: Water
  CK:       Water, Iron, Alkanes, Tantalum, Ytterbium
```

```text
Jaffa VII-b
Volcanic
Plateau
  forecast: none
  CK:       Lead, Tungsten, Titanium, Dysprosium

Hills
  forecast: none
  CK:       Iron
```

```text
Pyraas VIII-a
Sandy Desert
  forecast: none
  CK:       Chlorine, Chlorosilanes
```

The repeated complete-tree patterns strongly suggest that at least part of the discrepancy is biome-local cached-family propagation rather than incorrect planet-wide generation.

## Audit scope

Inspect the current implementation on the active branch, especially:

```text
src/starfield_resource_reproducer/generation.py
src/starfield_resource_reproducer/domain.py
src/starfield_resource_reproducer/diagnostics.py
src/starfield_resource_reproducer/dossier.py
```

and relevant tests.

Focus on these structures/functions:

- `PlanetGenerationResult`
- `BiomeFamilyGenerationResult`
- `BiomeOrchestrationResult`
- `ResourceFamilyResult`
- `FamilyAccessResult`
- the Common-family cache
- cache-hit handling
- per-biome result construction
- any CLI/report/dossier code that derives biome-local resources

## Questions to answer

### 1. What does a biome result currently contain on a cache hit?

Trace the exact object graph produced when:

```text
Biome A selects Common root X
→ family X generated and cached

Biome B later selects Common root X
→ family cache hit
```

Report whether Biome B's `BiomeFamilyGenerationResult` references the cached `ResourceFamilyResult`.

If yes, identify precisely where and how.

If no, identify where the relationship is lost.

### 2. Are cached family resources already recoverable per biome?

Determine whether, without changing production generation, the current result model already makes this possible:

```python
for biome_result in generation.biome_results:
    if biome_result.family_access is not None:
        biome_resources = biome_result.family_access.family.emitted_resources
```

or an equivalent path.

If that is already correct, say so explicitly.

Then identify whether the faulty field-sheet forecast came from a reporting/interpretation layer rather than from the generation model.

### 3. Does `emitted_resources` mean the right thing for biome assignment?

Inspect `ResourceFamilyResult.emitted_resources`.

Clarify whether it contains:

- the Common root;
- emitted descendants only;
- root + all structurally selected descendants;
- root + only descendants whose inclusion tests emitted them;
- anything filtered by shared planet capacity.

This distinction matters because the CK biome work object stores the reused family configuration, and we need to know which current reproducer field best corresponds to those biome-local slots.

### 4. What happens to a cached family whose original root/descendants were already inserted planet-wide?

Determine whether later cache-hit biome assignment is currently conflated with planet-wide `PlanetResourceState.record()` behavior.

Specifically:

- Does a later cache hit call `record()` again for the root or descendants?
- Does it create additional provenance occurrences?
- Does it merely return the cached family?
- Does any current field incorrectly interpret "not inserted again" as "not present in this biome"?

Report exact current behavior.

### 5. Where did the printed biome forecast likely go wrong?

Find the most likely code/data path that would produce a forecast such as:

```text
Jaffa VII-b / Volcanic → NONE
```

despite the biome selecting/reusing the Lead family.

Possible categories include:

- forecast built only from new `RESOURCE_SLOT_OCCUPIED` events;
- forecast built only from newly generated `family_results`;
- cache hits omitted from biome resource aggregation;
- capacity-skipped Common stages interpreted as empty;
- some other reporting assumption.

Do not change anything. Identify the exact logic or missing logic.

### 6. Distinguish these concepts explicitly

For the audit report, keep these separate:

```text
A. Planet-wide unique resource identity
B. Planet-wide family configuration cache
C. Per-biome Common-family assignment
D. Per-biome Everywhere assignment
E. Per-biome Special assignment
F. Provenance occurrence bookkeeping
```

State which of these the current model represents correctly and which are incomplete or ambiguous.

### 7. Audit the five-tree and eight-resource guards against biome assignment

Determine what the current implementation does when either guard prevents a **new Common selection/generation stage**.

Do not infer new engine behavior.

Simply report:

- what biome-local result the reproducer currently records;
- whether a cached family can still be associated with that biome under current code;
- whether the result model has any way to represent an existing family assigned without a new planet-wide insertion.

This is especially important for cases like Bara VII-d and Jaffa VII-b, where some CK biome assignments may involve more than the straightforward cache-hit path already proven by Jaffa trace 02.

## Required output

Write a concise audit report, preferably:

```text
docs/experiments/08C1-biome-local-cache-assignment-audit.md
```

**But do not create the file unless the user explicitly asks for repository changes.**

For this read-only task, return the report in Codex output only.

The report should include:

1. **Verdict**
   - Is cached-family assignment already represented correctly in the core result model?
   - If not, exactly what is missing?

2. **Code-path walkthrough**
   - first-generation path;
   - cache-hit path;
   - per-biome result construction.

3. **Field-by-field semantics**
   - `BiomeFamilyGenerationResult`
   - `FamilyAccessResult`
   - `ResourceFamilyResult`
   - any relevant per-biome diagnostic fields.

4. **Likely source of the faulty printed forecasts**

5. **Minimal implementation surface for a future fix**
   - identify files/functions that would need modification;
   - do not modify them.

6. **Open cases not explained by ordinary cache-hit reuse**
   - especially Bara VII-d Hills → Iron if the current trace evidence does not already explain it;
   - any capacity-guard or five-tree-guard biome assignments that cannot be represented by the simple cache-hit path.

7. **Evidence classification**
   - mark statements as PROVEN LIVE, PROVEN STATIC, STRONG, PROVISIONAL, or OPEN as appropriate.

## Read-only constraints

Do not:

- edit any file;
- modify tests;
- change diagnostics;
- run formatters that alter files;
- regenerate validation artifacts;
- commit;
- push.

You may:

- write audit reports;
- inspect source;
- inspect tests;
- run read-only commands;
- run tests if they do not mutate tracked files;
- inspect the Jaffa trace files under:

```text
D:\Projects\starfield-resource-research\.local-work\trace64\
```

Relevant trace names include:

```text
jaffa7b-common-01.trace64
jaffa7b-common-02.trace64
```

If trace inspection is useful, keep it secondary to the code audit; the live cached-family assignment behavior above is already established.

## Important framing

Do not treat the current 1,444/1,444 result as proof of per-biome correctness.

It proves the current planet-wide canonical resource-set validation only.

The purpose of this audit is to determine how much of the newly exposed biome-local problem is:

```text
generation-model deficiency
vs
result-model deficiency
vs
reporting/forecast deficiency
```

No implementation should be proposed until those are separated cleanly.
