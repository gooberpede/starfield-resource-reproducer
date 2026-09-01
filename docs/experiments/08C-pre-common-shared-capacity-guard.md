# Brief 08C Pre-Common Shared-Capacity Guard

## Scope and evidence

This correction implements the shared-eight control-flow guard recovered from
`FUN_1415DCFB0` in the Creation Kit Galaxy View Apply path. It changes only the
main per-biome Common stage.

**PROVEN STATIC/LIVE:** the function checks the established Common-tree count
against five, then the shared resource count against eight, then calls the
Common/category-0 selector. At shared count eight, the selector is bypassed and
its probability draw is not consumed.

**PROVEN LIVE - Indum IV-d:** Common-tree count was `2` and shared-resource count
was `8`. The five-tree guard was inactive; the shared-eight branch was taken and
the Common selector was skipped.

## Implementation

The generator now checks `PlanetResourceState.at_capacity` after the existing
five-tree guard and before `_select_weighted()` for Common. A distinct diagnostic
records the occupied count, capacity, unchanged draw count, and zero RNG
consumption.

The insertion model remains unchanged: a duplicate FormID can still retain
another provenance occurrence without occupying another slot. The new guard
prevents the Common path from reaching that insertion logic when the state was
already full. Everywhere and Special behavior are unchanged.

## Full canonical validation

```text
                         Post-08B   Post-08C
validation population       1,444      1,444
exact matches               1,442      1,444
mismatches                      2          0
generation errors               0          0
exact rate                  99.86%    100.00%
```

Zeta Ophiuchi I (`0005E151`) and Indum IV-d (`0005E19A`) no longer gain a
terrestrial/Common Chlorine occurrence after shared capacity is full. Atmospheric
Chlorine remains represented in each final player-facing union.

## Open question

Later biomes can reach this guard before attempting Common generation. Why
vanilla planets exhibit few or no genuinely empty biomes remains OPEN. Descendant
probabilities, Everywhere or Special resources, planet-wide presentation reuse,
or additional unrecovered behavior may contribute. No fallback behavior is
implemented speculatively.
