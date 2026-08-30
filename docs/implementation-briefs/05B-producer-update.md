Please update the Starfield resource reproducer based on the new Algorab I live x64dbg evidence.

Do **not** begin full 1,444-body validation yet.

## New live evidence

Three bounded Algorab I traces were captured:

* Sandy Desert / first Uranium generation
* Rocky Desert / repeated Uranium selection
* Volcanic / Lead generation

The trace evidence establishes:

### 1. Family-cache behavior — PROVEN

The first Uranium biome calls `FUN_14157F120` four times for descendant generation.

The second Uranium biome selects Uranium again but makes **zero calls** to `FUN_14157F120`.

Therefore:

```text
PROVEN:
when a Common root is already present in the planet-scoped family cache,
the cached family is reused and descendant generation is bypassed entirely.

No descendant RNG operations occur on the cache hit.
```

Upgrade the relevant cache-hit evidence status from PROVISIONAL to PROVEN.

### 2. Zero-candidate descendant RNG consumption — PROVEN

In Algorab I's Lead family, the final two descendant calls do not advance the structural node.

Across those calls, the observed RNG-related state advances through consecutive expected MT19937 raw words:

```text
d20 = 2242957990
d21 = 3583630102
d22 = 832141661
```

The two zero-candidate calls consume:

```text
first empty level  -> d21
second empty level -> d22
```

Therefore:

```text
PROVEN:
candidate_count == 0
    -> consume exactly one raw MT19937 word
    -> select no candidate
    -> structural node remains unchanged
```

Do not overstate the semantic operation. We have proven **one raw MT word is consumed**, but not whether the engine conceptually treats it as an inclusion draw, index-related operation, or another helper call.

## Required production change

Change the production zero-candidate behavior from:

```text
CONSUME_NONE
```

to the generic proven behavior:

```text
consume exactly one raw MT word
```

Do not call `next_index(0)`.

Use the smallest appropriate PRNG API or internal raw-advance mechanism.

Update:

* `generation.py`
* relevant diagnostics
* tests
* `docs/DOMAIN-RULES.md`
* `docs/BACKLOG.md`
* any existing 05A experiment note if it records the old unresolved status

Remove or revise obsolete PROVISIONAL comments.

## Required revalidation

Rerun all worked cases.

Expected:

```text
Oberon        exact
Mimas         exact
Decaran VII-b exact
Kreet         exact, including Neon
Algorab I     exact
```

For Kreet specifically, confirm:

```text
Lead Exotic zero-candidate  -> consumes 1 raw word
Lead Unique zero-candidate  -> consumes 1 raw word
Argon Neon inclusion moves to draw 17
raw = 357224398
roll ≈ 0.0831719488
Neon is emitted
```

Report the final Kreet draw count.

## Separate Algorab Lead discrepancy investigation

Do not silently change candidate ordering yet.

The Algorab trace appears to disagree with the reproducer's internal Lead forecast.

Codex previously forecast:

```text
Lead
L1 -> Tungsten
L2 -> Titanium
L3 -> Dysprosium
L4 -> zero candidates
```

But the live trace appears to show:

```text
structural node advances at L1
structural node advances at L2
structural node does NOT advance at L3
structural node does NOT advance at L4
```

This suggests the runtime path may instead be another Lead branch such as:

```text
Lead -> Silver -> Mercury -> empty -> empty
```

or otherwise that candidate ordering/construction differs from the reproducer.

Please investigate this discrepancy using:

* the current `Starfield_IRES_Hierarchy.csv`
* current candidate-construction code
* the known Algorab raw/index draws
* existing Lead-family tests and Kreet evidence

Report:

1. the exact serialized Lead IRES edges and source order;
2. the candidate list the reproducer builds at each Algorab Lead level;
3. the candidate index selected at each level;
4. whether runtime structural-return behavior can be reconciled with the current candidate order;
5. the first precise divergence if it cannot;
6. whether this indicates:

   * incorrect source ordering,
   * incorrect candidate concatenation order,
   * incorrect de-duplication,
   * incorrect structural-node interpretation,
   * or another issue.

Do **not** change candidate ordering merely to fit the trace unless the evidence clearly establishes the generic rule.

If additional x64dbg evidence would resolve the discrepancy, give a minimal trace experiment plan. CK/x64dbg are currently still available.

## Tests

Add or update tests so they lock:

```text
zero-candidate level consumes exactly 1 raw MT word
structural node remains unchanged
cache hit performs no descendant generation/RNG
Kreet now matches exactly
```

Preserve previous Mimas and Decaran assertions.

Run the full test suite.

## Completion report

Please report:

1. files modified/created;
2. production zero-candidate implementation;
3. evidence-status changes;
4. worked-case results and draw counts;
5. whether Kreet is now exact;
6. Algorab Lead discrepancy findings;
7. whether any candidate-order production change was made;
8. any minimal follow-up x64dbg trace requested;
9. test count/results;
10. blockers before Brief 06.

Do not commit or push.
