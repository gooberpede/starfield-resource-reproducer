# Brief 08C — Enforce shared-eight capacity before Common selection and revalidate

## Objective

Correct the reproducer so the main per-biome Common-generation stage respects the engine's **shared eight-resource capacity guard before the Common/category-0 selector is called**.

Then rerun the full 1,444-body canonical validation corpus and determine whether the two remaining Chlorine mismatches disappear.

This patch should be narrowly scoped to the recovered pre-selector capacity behavior in `FUN_1415DCFB0`.

## Current validation baseline

After Brief 08B:

```text
Population: 1,444
Exact:      1,442
Mismatches: 2
Errors:     0
Exact rate: 99.86%
```

Remaining mismatches:

```text
Zeta Ophiuchi I (0005E151)
  prediction-only Chlorine (000057D5)

Indum IV-d (0005E19A)
  prediction-only Chlorine (000057D5)
```

Both planets have atmospheric Chlorine and Water.

## Evidence basis

### PROVEN STATIC/LIVE — shared-eight guard precedes Common selection

In the Creation Kit Galaxy View Apply path, `FUN_1415DCFB0` contains the following ordering:

```asm
1415DD0D3  cmp dword ptr [rsi],5
1415DD0D6  jae ...

1415DD0DC  cmp dword ptr [r12],8
1415DD0E1  jae 1415DD255

...
1415DD0F2  call FUN_141580660   ; Common/category-0 selector
```

Therefore:

> **PROVEN STATIC/LIVE:** when the shared resource count is already 8, `FUN_1415DCFB0` bypasses the Common/category-0 selector entirely for that invocation.

The guard occurs before the Common probability draw and before any Common root is selected.

### PROVEN LIVE — Indum IV-d

A live Indum IV-d trace showed:

```text
Common-tree count = 2
shared-resource count = 8
```

at the relevant main-generator invocation.

The five-tree guard was not active:

```asm
cmp [rsi],5
; 2 < 5
```

The shared-eight guard was active:

```asm
cmp [r12],8
; 8 == 8

jae 1415DD255
; taken
```

The branch skipped the Common selector entirely.

Thus, at shared count 8:

- no Common/category-0 selector call occurs;
- no Common probability RNG draw is consumed;
- no prospective Common root is chosen;
- no Common provenance occurrence is created for that invocation.

### Why this matters for the remaining Chlorine residuals

The current reproducer models capacity primarily as a **resource insertion** constraint.

Its `PlanetResourceState.record()` behavior intentionally allows a repeated FormID already present through another provenance to be recorded without consuming a new capacity slot.

Conceptually, the current behavior permits:

```text
shared count == 8
→ Common selector still runs
→ selects Chlorine
→ Chlorine already exists via ATMO
→ record Common Chlorine occurrence
→ shared unique count remains 8
```

The engine's recovered control flow does not permit that sequence:

```text
shared count == 8
→ skip Common selector
→ no Common root selected
→ no Common Chlorine occurrence
```

This distinction is sufficient to explain the two remaining prediction-only Chlorine mismatches without introducing Chlorine-specific or ATMO-specific logic.

## Required implementation change

Locate the main per-biome Common-generation stage.

Enforce the shared eight-resource capacity guard **before** the Common/category-0 selector is invoked.

The intended ordering should be equivalent to:

```python
if established_common_tree_count >= COMMON_TREE_LIMIT:
    skip_common_selector(...)
elif resource_state.at_capacity:
    skip_common_selector_due_to_capacity(...)
else:
    common_entry = select_common(...)
```

Preserve the recovered order:

1. five-Common-tree guard;
2. shared-eight-resource guard;
3. Common selector.

Do not select a Common root and then discard it because capacity is full.

## RNG consequence

This is essential:

> when shared resource state is already at capacity before the Common stage, the Common selector is not called and its normal MT19937 probability draw is not consumed.

Add a focused regression proving that the guarded invocation consumes zero Common-selector draws.

Do not alter the RNG behavior of permitted Common selections.

## Distinguish control-flow capacity from insertion capacity

Keep these two concepts explicit:

### Pre-selector control-flow guard

Engine behavior:

```text
shared count >= 8
→ skip Common stage before selection
```

### Resource-state insertion/deduplication

Existing reproducer behavior:

```text
new FormID while count < 8
→ occupies new slot

new FormID while count >= 8
→ rejected

already-present FormID
→ may be represented by another provenance without consuming another slot
```

Do **not** remove or rewrite the provenance-aware resource-state model in this patch.

The new fix is specifically that the main Common-generation path may never reach `record()` when the shared state is already full.

## Everywhere/Water behavior must remain unchanged

Do not generalize this rule to category 6 / Everywhere.

Previously recovered live behavior for `FUN_141548920` shows:

```text
identify category-6 resource
→ write category-6 resource to biome/work-object +0x68
→ invoke shared-resource append path
```

Thus an Everywhere biome occurrence can be established before shared-state insertion/deduplication.

This patch must not change that ordering or suppress Everywhere resources merely because their FormID is already present through ATMO.

No Water-specific behavior should be added.

## Special handling

Do not alter Special/category-5 behavior unless existing code structure requires only a mechanical relocation of a shared guard that is already proven to apply there.

If the exact placement of the shared-eight guard relative to Special is not already proven in the repository, leave Special unchanged.

This brief is specifically about the recovered pre-Common guard.

## Five-tree guard

Preserve Brief 08B exactly.

The five-tree and shared-eight guards remain distinct:

```text
maximum distinct Common tree configurations = 5
maximum shared unique resource capacity      = 8
```

The recovered Common-stage order is:

```text
five-tree guard
    ↓
shared-eight guard
    ↓
Common/category-0 selector
```

Neither limit should be merged into the other.

## Tests

Add or update focused tests.

At minimum:

1. **Shared count below 8 permits Common selection**
   - verify ordinary selector behavior remains unchanged.

2. **Shared count exactly 8 skips Common selector**
   - selector is not invoked;
   - no Common root is produced;
   - no Common occurrence is recorded.

3. **No RNG consumption when capacity guard fires**
   - verify draw count/state is unchanged across the suppressed Common stage.

4. **Already-present prospective FormID does not bypass the guard**
   - construct a state at capacity containing a resource that the Common selector would otherwise be able to select;
   - verify the selector is still skipped entirely;
   - verify no new provenance occurrence is recorded for that Common stage.

   This is the key regression for the Chlorine collision mechanism.

5. **Five-tree guard remains independent**
   - preserve existing tests proving the tree limit prevents selection at five established trees.

6. **Everywhere duplicate provenance remains allowed according to existing behavior**
   - preserve the 08A/Fermi/Maal coverage;
   - do not regress ATMO + Everywhere same-FormID behavior.

7. **Indum IV-d and Zeta Ophiuchi I regression**
   - verify prediction-only terrestrial/Common Chlorine is removed from both;
   - preserve their atmospheric Chlorine identity in the final planetary resource set.

## Diagnostics

If useful, add a distinct diagnostic event for the pre-Common capacity guard, for example:

```text
COMMON_SKIPPED_AT_RESOURCE_CAPACITY
```

or reuse an existing capacity event if it can unambiguously identify:

- operation = pre-Common capacity guard;
- occupied count = 8;
- selector not invoked;
- RNG consumed = false.

Prefer explicit diagnostics if they improve future trace/validation work.

Do not conflate this event with a later failed insertion attempt.

## Documentation

Update architecture/domain/evidence documentation with wording equivalent to:

> **PROVEN STATIC/LIVE:** in `FUN_1415DCFB0`, the shared eight-resource guard is evaluated before the Common/category-0 selector. At count 8, the Common selector is bypassed and consumes no RNG.

Record the Indum IV-d live observation:

```text
Common-tree count = 2
shared-resource count = 8
→ shared-eight branch taken
→ Common selector skipped
```

Clarify that:

> shared capacity is not only an insertion constraint; in the main Common-generation path it is also a control-flow guard.

Do not upgrade the broader cross-provenance duplicate model beyond its existing evidence status.

## Open question exposed by this rule

Record, preferably in the backlog/experiment report rather than implementation code, the following unresolved question:

> If one early biome establishes a Common root plus several descendants, and atmosphere/Everywhere resources already consume additional shared slots, later biomes may reach the shared-eight guard before attempting Common generation. Why do vanilla planets appear to show few or no genuinely empty biomes?

Possible explanations are **OPEN** and must not be implemented speculatively. They may include:

- descendant emission probabilities usually leave more capacity than the worst case;
- later biomes may still receive Everywhere and/or Special resources;
- some resource presentation may reuse planet-wide resources across biome displays;
- additional engine behavior not yet recovered may populate otherwise empty biomes.

Do not add a fallback or "ensure at least one resource per biome" rule.

## Full-corpus validation

After tests pass, rerun the exact full canonical validation workflow.

Expected hypothesis only:

```text
Population: 1,444
Exact:      1,444
Mismatches: 0
Errors:     0
Exact rate: 100.00%
```

Do **not** tune the implementation to force this outcome.

If any mismatches remain or new mismatches appear, report the actual rows and signatures without adding compensating heuristics.

## Explicit non-goals

Do not:

- add Chlorine-specific logic;
- add Water-specific logic;
- add ATMO-vs-Common duplicate special cases;
- alter atmosphere loading;
- alter category-6/Everywhere logic;
- alter Special/category-5 selector mechanics;
- alter Common weighting/probability mechanics;
- alter descendant mechanics;
- alter MT19937;
- alter biome shuffle;
- alter PNDT RSGD override behavior;
- alter five-tree behavior;
- rewrite the provenance model;
- introduce an empty-biome fallback;
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

## Deliverable

Return:

1. concise implementation summary;
2. exact files changed;
3. focused and full test results;
4. confirmation that the capacity-skipped Common stage consumes zero RNG;
5. full-corpus before/after comparison;
6. residual mismatch list, if any;
7. documentation/evidence updates;
8. confirmation that no commit or push was performed.

Suggested commit message after review:

```text
fix: guard Common selection at resource capacity
```
