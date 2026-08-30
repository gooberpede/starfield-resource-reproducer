# Runtime Bounded-RNG Split

## Result

**PROVEN:** biome shuffle and descendant candidate selection use distinct
bounded-random mechanisms. Production mirrors both paths explicitly; the
addresses below are build-specific evidence anchors, not production logic.

## Evidence chain

### Algorab descendant selection

```text
Planet:          Algorab I (0003F599)
Biome:           VolcanicRoughNoLife02
Root:            Lead (000057C1)
Candidate order: [Silver, Tungsten]
Draw:            18
Raw:             1826241303 (0x6CDA3B17)
Bound:           2
Modulo:          1
Runtime index:   0
```

The live instruction path converts the word through binary32 probability
arithmetic, scales by candidate count, and truncates. Reconstructed values are:

```text
probability = 0.4252006709575653
scaled      = 0.8504013419151306
index       = 0
```

This selects Silver, then Mercury, followed by empty Exotic and Unique levels.
Those empty levels consume draws 21 and 22 under the separately proven rule.

### Kreet biome shuffle

The dedicated runtime helper chain is:

```text
FUN_14152CBC0
    -> 0x1401714A8
    -> bounded helper thunk 0x14001D63D
    -> implementation around 0x141587240
```

Observed anchors:

```text
draw 1: raw 3789400562, bound 2, returned index 0
draw 2: raw 3546750279, bound 3, returned index 0
```

The helper repeatedly compares `raw // bound` with
`UINT32_MAX // bound`, rejects outside the accepted quotient range, and returns
`raw % bound` after acceptance. Neither Kreet anchor rejects, but the recovered
control flow proves that a choice may consume more than one MT word.

## Production consequence

The PRNG surface now names the semantics separately:

```text
next_bounded_integer -> integer rejection + modulo -> biome shuffle
next_scaled_index    -> float32 scale + truncate   -> descendants
```

Kreet retains shuffle order `[2, 0, 1]`, Neon at draw 17, exact canonical
membership, and final draw count 30. Algorab now follows the live Lead path,
matches canonical Lead + Uranium + Iridium, and ends at draw 22. No candidate
ordering, zero-candidate, or cache behavior changed.
