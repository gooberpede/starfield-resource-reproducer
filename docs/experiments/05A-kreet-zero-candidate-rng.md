# Kreet Zero-Candidate RNG Experiment

## Question

This question was resolved by the Algorab I bounded live traces used in Brief
05B. A zero-candidate descendant call consumes exactly one raw MT19937 word,
selects no candidate, and retains the structural node. The raw-word count is
PROVEN; the engine's high-level operation name remains unknown.

Kreet therefore consumes one word at each empty Lead level. Argon's Neon roll
moves to draw 17 (`357224398`, `0.08317194879055023`) and is emitted.

## Known entry point and missing address

Known:
- per-biome generator: 0x1415DCFB0
- descendant helper:   0x14157F120
- post-fourth-call:    0x1415DD1EB

Still required:
- exact call-site addresses for the four descendant invocations, if useful
- PRNG/helper address or an equivalent way to observe MT state advancement
- verified argument locations for rarity/candidate state in the current build

## Target run

Use Kreet and stop in the Volcanic biome after Common selection chooses Lead.
The two calls of interest occur after Lead reaches Mercury structurally:

1. Exotic, filtered `candidate_count = 0`;
2. Unique, filtered `candidate_count = 0`.

Record the two calls separately; do not infer one from the other.

## Historical breakpoint/log plan

1. Break at `1415DCFB0` and continue until the Kreet Volcanic invocation.
2. From that invocation, break at the recovered descendant-level helper entry
   and return site. Add a condition for the Lead root plus rarity 3 (Exotic) or
   4 (Unique), using the actual argument locations recovered from Ghidra.
3. At helper entry, log the root FormID, current structural FormID, rarity,
   candidate count, and the address/state pointer of the shared PRNG.
4. Put a logging breakpoint on the already identified raw MT extraction/helper
   reached by `next_float01` and bounded-index calls. Condition it on the active
   descendant invocation or the captured PRNG state pointer.
5. Log each RNG-helper hit's caller/return address and raw output. Continue
   automatically to the descendant return breakpoint.
6. At return, log candidate count again, current structural FormID, and PRNG
   state/index. The structural node should remain Mercury; any state/index
   delta gives the raw-word count.

The decisive record for each level is:

```text
rarity | candidate_count | PRNG state/index before | RNG-helper hits
       | raw values | PRNG state/index after | structural node after
```

Interpret zero helper hits and no state change as zero draws. One helper hit is
one raw draw, but classify it as an inclusion operation or index-like operation
only from its call site/control flow. Two helper hits establish two raw draws
and their call order. A state delta without a captured helper hit means the
breakpoint coverage is incomplete and the run should not be treated as proof.

## Historical command limitation

At the time of Brief 05A, exact PRNG-helper details and argument locations were
not recorded in the repository, so commands were deliberately not invented.
The later Algorab I traces supplied the required state-advance evidence.
