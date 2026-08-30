# Algorab I Bounded-Index Conversion

## Discriminating descendant trace

```text
Planet:          Algorab I (0003F599)
Biome:           VolcanicRoughNoLife02
Root:            Lead (000057C1)
Candidate order: [Silver, Tungsten]
Draw:            18
Raw:             1826241303 (0x6CDA3B17)
Bound:           2
Old modulo:      1 (Tungsten)
Live result:     0 (Silver)
```

Modulo is therefore PROVEN wrong for this descendant candidate-selection call.
The observed runtime instruction shape is floating-point scaling followed by
integer truncation.

## Reconstructed arithmetic

Reusing the current STRONG binary32 probability conversion gives:

```text
float32(raw)                         = 1826241280.0
float32(raw_float * float32(2^-32))  = 0.42520493268966675
float32(unit * float32(0.99999))     = 0.4252006709575653
float32(probability * float32(2))    = 0.8504013419151306
truncate                             = 0
```

This naturally selects Silver, then Mercury, followed by empty Exotic and
Unique levels. With one raw word per empty level, Algorab ends at draw 22 and
matches its live structural shape. The exact reuse of the `0.99999` probability
factor remains STRONG because the discriminating index does not distinguish
nearby binary32-equivalent formulations.

## Generic-path conflict

Applying the same reconstructed conversion to all current `next_index()` calls
breaks Kreet's PROVEN shuffle selections:

```text
Kreet draw 1: raw 3789400562, bound 2
runtime index 0; scaled index 1

Kreet draw 2: raw 3546750279, bound 3
runtime index 0; scaled index 2
```

Algorab's shuffle still matches under scaling (`1`, then `0`), but Kreet fails
at its first shuffle operation. This is Outcome B from Brief 05C. Production
has not been split into separate bounded APIs and has not been changed to a
generic scaled primitive, because current evidence cannot distinguish:

1. separate runtime conversion paths for shuffle and descendants; or
2. a mistaken interpretation of the recovered shuffle call/returned index.

A diagnostics-only generic-scaled replay gives Kreet:

```text
shuffle order: [0, 1, 2] instead of [2, 0, 1]
Common roots:  Argon, Iron, Lead
final draws:   31
canonical:     mismatch
```

Oberon, Mimas, and Decaran VII-b remain exact in that replay because their
observed candidate-index operations use bound 1. Algorab becomes internally
trace-exact at draw 22.

## Minimal follow-up trace

Trace only Kreet's first biome-shuffle bounded call. Capture:

```text
raw MT word
bound passed to the helper
floating/integer conversion instructions or callee address
returned integer index before the swap
```

Compare that helper/call path directly with Algorab Lead L1. One bounded call is
sufficient to determine whether the engine genuinely uses two paths.
