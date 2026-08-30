# Algorab I Lead Structural-Branch Follow-up

## Current data and model

The serialized Lead edges are, in source order:

```text
000057C1 Lead -> 000057C3 Silver
000057C1 Lead -> 000057C4 Tungsten
000057C3 Silver -> 0027C499 Mercury
000057C4 Tungsten -> 000057C6 Titanium
000057C6 Titanium -> 000057C2 Dysprosium
```

At Algorab draw 18 the current bounded conversion returns:

```text
1826241303 % 2 = 1
```

so the reproducer selects Tungsten. It then builds the single-candidate path
Titanium, Dysprosium, followed by one empty Unique level. The live trace instead
shows structural advancement only at L1 and L2, then two non-advancing calls.
That shape is consistent with Silver -> Mercury -> empty -> empty.

These outcomes must not be conflated:

```text
live trace:    d17/d18 L1, d19/d20 L2, d21 empty L3, d22 empty L4
               final draw position 22
current model: d17/d18 L1, d19/d20 L2, d21/d22 L3, d23 empty L4
               final draw position 23
```

The current model still matches Algorab's canonical final resource set, but its
Lead structural path and final draw position disagree with the live trace.

Candidate concatenation order cannot explain the first divergence because root
and current are both Lead at L1. De-duplication retains the first copy of each
Lead child in serialized order. Reversing source order would make index 1 select
Silver, but the trace has not established such a generic reversal and Kreet must
remain intact. No production ordering change is justified.

The leading alternative is bounded-index conversion: multiplication scaling
would map draw 18 to index 0, while the current STRONG modulo conversion maps it
to index 1. This is a hypothesis, not yet proof.

## Minimal live experiment

Repeat only Algorab I's Volcanic Lead L1 call to `FUN_14157F120`:

1. Break immediately after the bounded candidate-index helper consumes draw 18.
2. Log the helper's returned integer index before it is used.
3. At the descendant return, log the selected structural FormID.

Decisive outcomes:

```text
index 0 / Silver  -> current modulo conversion is wrong for bound 2
index 1 / Silver  -> candidate order differs from the serialized order
index 1 / Tungsten -> L3 non-advance reflects a later candidate/return issue
```

Capturing both the integer result and selected FormID avoids inferring resource
identity from structural-change flags. No broader planet trace is required.
