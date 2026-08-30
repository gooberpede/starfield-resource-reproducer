# Kreet Zero-Candidate RNG Experiment

## Question

Determine independently for Kreet's Lead family whether the Exotic and Unique
descendant calls consume zero, one, or two raw MT19937 words when their filtered
candidate count is zero. The production model remains no-draw and PROVISIONAL
until this is established by a live trace.

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

## Minimal breakpoint/log plan

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

## Why exact x64dbg commands are not included yet

The repository does not contain the descendant helper address, PRNG helper
address, argument registers/stack offsets, or verified module relocation for
the user's current executable. Exact `bp`, conditional-expression, and logging
commands would therefore require invented addresses or registers. Once those
four facts are exported from the existing Ghidra/x64dbg work, this plan can be
translated directly into two conditional logging breakpoints with automatic
continue and no manual stepping.

