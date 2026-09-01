# Brief 08B — Enforce the five distinct Common resource-tree limit and revalidate

## Objective

Correct the reproducer so the main per-biome generator stops attempting to create additional **new distinct Common resource trees/families** once five have already been established for the planet-generation run.

Then rerun the full 1,444-body canonical validation corpus and report the new residual mismatch set.

This patch should be narrowly scoped to the five-tree limit recovered from `FUN_1415DCFB0`.

## Evidence basis

### PROVEN STATIC/LIVE — hard-coded five-tree guard

In the live Creation Kit Galaxy View Apply path, `FUN_1415DCFB0` contains:

```asm
1415DD0D3  cmp dword ptr [rsi],5
1415DD0D6  jae 1415DD255
```

The constant `5` is an immediate literal embedded in the compiled instruction. It is not loaded from a runtime configuration value at this guard.

The same function also contains the separate hard-coded shared-resource limit:

```asm
cmp dword ptr [r12],8
```

The five-tree guard and eight-resource guard are distinct mechanisms and must remain distinct in the reproducer.

### PROVEN LIVE — Bara VII-d

Fresh Bara VII-d traces at the five-tree guard showed the low dword at `[rsi]` progressing:

```text
Trace 01   0
Trace 02   1
Trace 03   1
Trace 04   2
Trace 05   2
Trace 06   3
Trace 07   4
Trace 08   5
```

The repeated values demonstrate that this state is not a simple per-biome invocation counter.

At trace 08:

```asm
1415DD0D3  cmp dword ptr [rsi],5
           ; [rsi] == 5

1415DD0D6  jae 1415DD255
```

The branch was taken live to `1415DD255`.

That jump bypasses the subsequent Common-generation block, including:

- the shared-resource `< 8` check in that block;
- the `FUN_141580660(..., category 0)` Common selector call;
- new-family instantiation/handling.

Therefore:

> **PROVEN LIVE:** once five Common resource-tree/family configurations have already been established, `FUN_1415DCFB0` does not perform another Common/category-0 selection attempt for that generator invocation.

### Bara VII-d residual

Before this correction, the reproducer produces one unexpected resource:

```text
Bara VII-d (0005E39F)
unexpected Nickel (000057CB)
```

The reproducer's Common-root sequence is:

```text
Uranium
Uranium   ← repeated/cache-hit family
Chlorine
Copper
Aluminum
Iron
Nickel    ← sixth distinct Common tree/family
```

The engine's live five-tree guard explains why Nickel should not be selected: once five distinct Common trees/families exist, the engine skips the Common selector entirely for later eligible generator invocations.

## Terminology

Use one consistent implementation term such as:

- `Common resource tree`
- `Common family`
- `Common tree configuration`

Prefer the repository's existing terminology if one is already established.

Avoid claiming more structure than the evidence supports. The functional invariant is:

> no more than five **distinct newly established Common root trees/families** are created by this path.

Do not describe the limit as "five biomes", "five Common selections", or "five resources".

## Required implementation change

Locate the main per-biome Common-generation path in `generation.py` (or the relevant domain helper).

Before making a new Common/category-0 selector draw for an invocation that would create another distinct Common tree/family, enforce the five-tree limit.

The reproducer must match the recovered ordering:

```text
if established_common_tree_count >= 5:
    skip Common/category-0 selection for this invocation
else:
    perform ordinary Common selector
    then existing cache/new-family handling
```

The critical RNG consequence is:

> when the five-tree guard is active, the Common selector is not called and its normal MT19937 probability draw is not consumed.

This is essential. Do not select a sixth root and discard it afterward.

## Cache/repeated-family semantics

Preserve the existing family-cache behavior.

A repeated/cache-hit Common root does **not** create a new distinct Common tree/family and must not consume another one of the five tree slots.

The count should therefore represent the number of distinct Common root trees/families already established, not:

- number of per-biome generator calls;
- number of Common selector calls;
- number of emitted resources;
- total resource count.

Do not alter descendant-cache behavior except as necessary to reuse the existing distinct-family state correctly.

## Interaction with the shared eight-resource limit

Keep the limits separate:

```text
maximum distinct Common root trees/families = 5
maximum shared unique resource capacity      = 8
```

Do not merge these into one condition.

Do not reinterpret the five-tree guard as a substitute for the shared resource-capacity guard.

The existing shared-eight behavior should remain unchanged.

## RNG ordering

Preserve all existing proven RNG mechanics.

Specifically:

- biome shuffle unchanged;
- Special/category-5 selector unchanged;
- Common/category-0 selector unchanged when the five-tree guard permits it;
- descendant inclusion and candidate selection unchanged;
- family-cache hits unchanged;
- category-6/Everywhere unchanged;
- atmosphere unchanged.

When the five-tree guard suppresses Common generation, there must be **no Common-selector RNG consumption** for that skipped invocation.

Add a focused RNG-sequence regression if the existing test architecture can assert this cleanly.

## Tests

Add or update tests covering the limit generically.

At minimum:

1. **Five distinct Common roots allowed**
   - establish five distinct Common root trees/families;
   - verify all five can be created under otherwise permissive capacity.

2. **Sixth Common attempt skipped before selector**
   - with five trees already established, process another biome/invocation that would otherwise attempt Common generation;
   - verify the Common selector is not invoked;
   - verify no sixth tree/root is created.

3. **No RNG consumption on skipped sixth attempt**
   - verify the RNG state/next word is unchanged by the suppressed Common-selection stage, using the repository's existing PRNG testing style.

4. **Cache/repeated family does not consume a tree slot**
   - establish a Common root;
   - hit the same root again through the existing cache path;
   - verify distinct-tree count does not increase.

5. **Shared-eight remains independent**
   - preserve or add coverage demonstrating that the five-tree guard does not replace the shared eight-resource capacity behavior.

6. **Bara VII-d regression**
   - verify Nickel `000057CB` is no longer generated for Bara VII-d under the canonical fixture/data;
   - preserve all other Bara VII-d expected output.

Preserve all existing 08A, atmosphere, Everywhere, Special, Common selector, descendant, PNDT override, provenance, and validation tests.

## Documentation

Update the appropriate architecture/evidence/experiment documentation.

Record:

> **PROVEN STATIC/LIVE:** `FUN_1415DCFB0` contains a hard-coded `cmp ...,5` guard for the Common tree/family state.

Record:

> **PROVEN LIVE — Bara VII-d:** with the state count at five, the `jae` branch is taken before the Common/category-0 selector, so no further Common selector draw is consumed for that invocation.

Record the observed Bara progression if useful:

```text
0, 1, 1, 2, 2, 3, 4, 5
```

This supports the interpretation that the state counts distinct established Common tree/family configurations rather than per-biome calls.

Keep wording scoped to the Creation Kit Galaxy View Apply path unless surrounding documentation already states that scope.

Do not upgrade unrelated duplicate/provenance collision semantics.

## Full-corpus validation

After tests pass, rerun the exact full canonical validation workflow used by 08A.

Current baseline after 08A:

```text
Population: 1,444
Exact:      1,441
Mismatches: 3
Errors:     0
Exact rate: 99.79%
```

Current residuals:

```text
Zeta Ophiuchi I (0005E151)
  unexpected Chlorine — atmospheric/Common collision

Indum IV-d (0005E19A)
  unexpected Chlorine — atmospheric/Common collision

Bara VII-d (0005E39F)
  unexpected Nickel — sixth distinct Common tree/family
```

Expected hypothesis only — do not force the implementation to match it:

```text
Population: 1,444
Exact:      1,442
Mismatches: 2
Errors:     0
```

If Bara VII-d remains mismatched or another case changes, report the actual result without adding compensating heuristics.

## Residual analysis

After rerun, report:

- exact match count and rate;
- remaining mismatch identities;
- expected-only vs prediction-only direction;
- unexpected/missing FormIDs;
- whether Bara VII-d is resolved;
- whether either Chlorine collision changes unexpectedly.

Do not modify Chlorine cross-provenance behavior in this patch.

## Explicit non-goals

Do not:

- change atmosphere handling;
- change category-6/Everywhere logic;
- change Special/category-5 mechanics;
- change Common selector weighting/probability logic;
- change descendant mechanics;
- alter MT19937 implementation;
- alter biome shuffle;
- alter PNDT effective-RSGD override behavior;
- change shared-eight semantics;
- change resource occurrence/provenance modeling;
- fix the Zeta Ophiuchi I or Indum IV-d Chlorine collision cases;
- add Bara-specific or Nickel-specific heuristics;
- commit or push.

## Validation

Run:

1. focused/new tests;
2. full test suite;
3. mojibake guard:
   ```text
   python scripts/check_mojibake.py
   ```
4. `git diff --check`;
5. full 1,444-body canonical validation.

All should pass unless a genuine mismatch is being reported for investigation.

## Deliverable

Return:

1. concise implementation summary;
2. exact files changed;
3. tests run and results;
4. confirmation of RNG behavior for the skipped sixth Common attempt;
5. full-corpus before/after comparison;
6. residual mismatch list;
7. documentation/evidence wording changed;
8. confirmation that no commit or push was performed.

Suggested commit message after review:

```text
fix: enforce five Common resource-tree limit
```
