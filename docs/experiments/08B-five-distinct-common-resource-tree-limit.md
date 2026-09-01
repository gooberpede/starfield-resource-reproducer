# Brief 08B Five Distinct Common Resource-Tree Limit

## Scope and evidence

This correction implements the hard-coded Common-tree guard recovered from
`FUN_1415DCFB0` in the Creation Kit Galaxy View Apply path. The separate compiled
checks compare the established Common-tree state with five and the shared
resource state with eight; they remain independent in the reproducer.

**PROVEN STATIC/LIVE:** `FUN_1415DCFB0` contains a hard-coded `cmp ...,5` guard.
When five Common tree configurations already exist, its branch bypasses the
Common/category-0 selector and therefore consumes no selector probability draw.

**PROVEN LIVE - Bara VII-d:** the observed state sequence was
`0, 1, 1, 2, 2, 3, 4, 5`. The branch was taken at five. The repeated values agree
with distinct established family configurations, including cache reuse, rather
than a biome or selector-call count.

## Implementation

The planet-scope FormID-keyed family cache is the established-tree state. Before
each Common selector, the generator checks whether that cache already contains
five entries. If so, it emits a diagnostic guard event and skips the selector
without advancing MT19937. Cache-hit behavior and the separate shared capacity
of eight unique resource FormIDs are unchanged.

## Full canonical validation

```text
                         Post-08A   Post-08B
validation population       1,444      1,444
exact matches               1,441      1,442
mismatches                      3          2
generation errors               0          0
exact rate                  99.79%     99.86%
```

Bara VII-d (`0005E39F`) is now exact; Nickel (`000057CB`) is no longer selected
as a sixth distinct Common tree. The remaining mismatches are unchanged:

| Planet | FormID | Direction | Residual |
|---|---|---|---|
| Zeta Ophiuchi I | `0005E151` | prediction-only | unexpected Chlorine `000057D5` |
| Indum IV-d | `0005E19A` | prediction-only | unexpected Chlorine `000057D5` |

Both residuals remain atmospheric/Common Chlorine collisions. Cross-provenance
collision semantics were deliberately not changed by this correction.
