# Brief 09A — Reproducer v1.0 consolidation and evidence baseline

## Status

Implementation/documentation brief for:

`gooberpede/starfield-resource-reproducer`

This brief follows Briefs 08D and 08D.1.

The purpose is **not** to change the recovered generation algorithm. The purpose is to consolidate the repository around the now-validated model, remove stale pre-v0.1/research-phase language, freeze the v1.0 evidence baseline, and make the repository safe to consume as a reference implementation and regression oracle.

Do not commit or push unless explicitly asked.

## Milestone

The reproducer has reached the point where a v1.0 designation is justified within its defined scope.

Current validated state:

```text
canonical planet-wide validation:
    1,444 / 1,444 exact
    0 mismatches
    0 errors

targeted CK biome regressions:
    all known pathological cases exact

fresh independent CK + retail sample:
    10 / 10 bodies exact

fresh-sample atmosphere:
    all atmospheric resources exact

fresh-sample biome-local terrestrial assignment:
    all predicted biome distributions exact

fresh-sample retail planetary scans:
    all resource sets exact
```

The fresh sample was deliberately selected from bodies not used in algorithm discovery or earlier detailed validation.

This is now the repository's **v1.0 evidence baseline**.

## Defined v1.0 scope

The repository is a standalone reference reproducer for **vanilla Starfield inorganic planetary-resource generation** using authoritative static inputs.

Within scope:

```text
PNDT resource seed / ordered biome entries
BIOM
effective per-biome RSGD
IRES hierarchy
effective atmospheric inorganic resources
MT19937 state evolution
biome shuffle
Everywhere
Special
Common root selection
descendant generation
family caching
five-tree guard
shared-eight guard
guard fallback assignment
biome-local assignment provenance
planet-wide final membership
```

The implementation distinguishes:

```text
planet-wide resource identity
planet-wide cached family configuration
biome-local Common-family assignment
Everywhere occurrence
Special occurrence
atmospheric occurrence
family-configuration origin
assignment mechanism
```

Do not broaden v1.0 to organic resources, flora/fauna spawning, extractor placement mechanics, resource vein geometry, arbitrary mod/plugin behaviour beyond current loader semantics, arbitrary future executable versions, or retail `Starfield.exe` function-address equivalence with Creation Kit addresses.

## Canonical input corpus

Document these as the canonical v1.0 inputs:

- `PlanetResourceGeneration_v5.csv` — authoritative PNDT/BIOM/effective-RSGD/RSCS input.
- `Starfield_IRES_Hierarchy.csv` — authoritative IRES rarity and child-resource graph.
- `Starfield_PlanetAtmosphericResources.tsv` — authoritative effective atmospheric inorganic-resource export for the current corpus.
- `planet-all-resources.csv` — canonical planet-wide validation oracle for the CK/RSGD-visible inorganic channel used by the validator, but **not** a complete final planetary-resource oracle because it is proven to omit at least some atmosphere-derived resources.

Preserve the effective-RSGD precedence rule:

```text
if PNDT biome Resource Generation != NULL:
    EffectiveRSGD = PNDT override
else:
    EffectiveRSGD = BIOM.RNAM
```

No merge.

## Proven generation order

Update architecture/domain documentation so the canonical order is unambiguous:

```text
effective atmosphere resources
    ↓
record atmospheric identities into shared planet state
    ↓
Everywhere/category-6 pre-pass over all effective RSGDs
    ↓
construct PNDT biome work objects in BiomeIndex order
    ↓
deterministic MT19937 biome shuffle
    ↓
for each shuffled biome:
        Special/category-5 selector
        ↓
        record selected Special immediately into shared state
        ↓
        five-Common-tree guard
        ↓
        shared-eight guard
        ↓
        if neither guard fires:
            Common/category-0 weighted selector
            ↓
            new family OR normal cache reuse
        else:
            guard fallback assignment
            ↓
            matching cached roots preferred
            otherwise all cached families
            no Common roots → no Common assignment
```

Descendant generation remains Uncommon → Rare → Exotic → Unique, with structural continuation through omitted selected candidates.

## RNG mechanisms

Retain these as separate, explicitly documented primitives:

1. **Biome shuffle bounded integer — PROVEN**  
   Rejection/modulo helper; rejected attempts consume words.

2. **Probability float — PROVEN**
   ```python
   raw_float = float32(raw_uint32)
   unit_value = float32(raw_float * float32(2**-32))
   converted = float32(unit_value * float32(0.99999))
   ```

3. **Special/Common weighted selector — PROVEN**  
   One probability draw before category enumeration, including zero/one/100% candidate cases. Stored RSGD order; cumulative chance; no normalization.

4. **Descendant candidate index — PROVEN**  
   Float32-scaled index from one probability draw for non-empty candidate lists.

5. **Guard-fallback family index — PROVEN**  
   Same float32-scaled arithmetic shape as descendant selection, but retain distinct semantic naming/event provenance. A one-family fallback pool still consumes the draw.

Do not consolidate these mechanisms merely because two share arithmetic.

## Family-cache and biome-assignment semantics

Ensure the v1.0 documentation clearly distinguishes:

```text
NEW_FAMILY
NORMAL_CACHE_REUSE
GUARD_MATCHED_FALLBACK
GUARD_GENERAL_FALLBACK
NO_COMMON_ASSIGNMENT
```

Family origin must remain separate from later assignment mechanism.

Preferred wording:

> family configuration originally generated while processing biome X

Avoid implying that a later biome necessarily copies directly from another biome object.

## Capacity semantics

Document precisely:

### Five-tree guard

**PROVEN LIVE / STATIC in the CK path.**

After five distinct generated/cached Common-family configurations exist, the normal Common selector is suppressed and control enters fallback.

Do not retain older wording that leaves this semantic role merely provisional.

### Shared-eight guard

**PROVEN LIVE / STATIC in the CK path.**

Eight unique resource FormIDs share one planet-wide capacity across origins. Occurrence provenance is separate from unique identity occupancy.

A duplicate FormID occurrence is recorded but does not occupy another slot or increment the count.

A new Special can fill slot eight before the Common guard and force guard fallback.

## Missing-input semantics

Lock in the behaviour demonstrated by Volii Alpha.

If a body lacks PNDT/biome/effective-RSGD input:

```text
do not fabricate biome assignments
do not interpret missing generation input as an empty biome result
```

Independently available origin channels may still be reported.

Example:

```text
atmospheric resources known
biome-local generation unknown / unsupported from current inputs
```

If the existing API already communicates this distinction cleanly, do not add unnecessary abstraction.

## Durable v1.0 validation record

Create:

`docs/V1-VALIDATION-BASELINE.md`

Record:

### Canonical validation

```text
1,444 / 1,444 exact
0 mismatches
0 errors
```

### Targeted CK regression bodies

Include the established discovery/regression set, such as:

```text
Kreet
Callisto
Maal VIII
Fermi VIII-b
Titan
Algorab I
Mimas
Bara VII-d
Indum IV-d
Zeta Ophiuchi I
Jaffa VII-b
Pyraas VIII-a
```

State explicitly that these are discovery/regression cases, not independent holdouts.

### Fresh holdout validation

Record the ten fresh bodies:

```text
Vesta — Lunara
Niira — Narion
Eridani IV — Eridani
Cassiopeia IV-a — Eta Cassiopeia
Cassiopeia II-a — Eta Cassiopeia
Zosma V-a — Zosma
Eridani III-b — Eridani
Luyten's Rock — Luyten's Star
Bardeen V-d — Bardeen
Ka'zaal — Nirah
```

Observed result:

```text
10 / 10 exact
```

For all ten:

- atmosphere matched where present;
- terrestrial resources occurred in exactly the predicted CK biomes;
- retail planetary scans showed exactly the forecast resource set.

Do not invent detailed per-body values unless already present in tracked evidence.

### Volii Alpha negative control

Record:

```text
Volii Alpha absent from PlanetResourceGeneration_v5.csv
atmospheric Benzene + Water available independently
no biome assignment fabricated
```

This validates input-boundary behaviour, not terrestrial generation output.

## Version/status cleanup

The README still contains stale language such as `Research / pre-v0.1` and `First Milestone v0.1`.

Replace that with a clear statement that the **algorithm/model status is v1.0**.

Do not claim a GitHub release/tag exists unless one is actually created.

## README cleanup

Rewrite the README so a new contributor sees the current model first.

Do not lead with implementation-brief chronology (`07B`, `08A`, `08B`, `08C`, `08D`). Move history to implementation/workflow documentation where appropriate.

## Backlog reconciliation

Review `docs/BACKLOG.md`.

Mark completed, superseded, or remove from active backlog any stale items about:

- unexplained shared-eight empty biomes;
- missing post-guard family reuse;
- unresolved atmosphere insertion already settled by live evidence;
- v0.1 central-path completion.

Keep only genuine future work, such as:

```text
future version-drift detection
new falsifications/counterexamples
consumer/export API hardening
planner integration
optional packaging/release automation
```

Do not invent reverse-engineering tasks simply to keep a backlog populated.

## DOMAIN-RULES reconciliation

Review `docs/DOMAIN-RULES.md` end-to-end.

Ensure evidence/status is current for:

```text
atmosphere shared state
Everywhere pre-pass
Special-before-guards
five-tree guard
shared-eight guard
ordinary cache reuse
guard matched fallback
guard general fallback
fallback RNG
family-origin provenance
missing-input behaviour
```

Mark earlier contradicted interpretations **SUPERSEDED**.

## ARCHITECTURE reconciliation

Review `docs/ARCHITECTURE.md`.

The architecture must keep separate:

```text
planet-wide identity/capacity state
resource occurrences/provenance
family configuration cache
family origin
biome Common assignment
atmosphere channel
Everywhere channel
Special channel
Common/Descendant channel
validation oracle
biome-centric reporting
```

Use actual class/type names from the code where they differ.

## Test baseline

Document the current test baseline:

```text
full suite: 138 passed
```

Do not hard-code the count as a contractual assertion.

Preserve targeted regressions for Special filling slot eight, duplicate Special, matched/general fallback, bound-1 fallback draw, family origin, biome-index occurrence association, and CK regression assignments.

## Evidence boundary

Use precise wording:

- Creation Kit function addresses/control flow are **PROVEN for the live-traced CK Galaxy View Apply path**.
- Retail validation independently corroborates predicted outputs.
- Do not claim those CK addresses were independently traced in `Starfield.exe`.

## Falsifiability policy

Add a short policy statement:

> v1.0 is considered complete within its defined scope because the model reproduces the full canonical corpus and independent CK/retail holdout samples. Future contradictory evidence should be treated as a falsification/regression to investigate, not hidden by heuristics or oracle patches.

No planet-specific exceptions.

## AGENTS.md

Audit `AGENTS.md` so coding agents understand that v1.0 is a protected baseline:

1. no algorithm change without evidence;
2. canonical/oracle data never consulted during generation;
3. provenance channels remain distinct;
4. RNG mechanisms remain distinct;
5. missing input is not guessed;
6. CK addresses are not silently relabelled as retail addresses;
7. a future counterexample requires preserved evidence, evidence classification, a focused regression, then an implementation change;
8. retain UTF-8/mojibake safeguards.

## Optional version metadata

If a real version constant/package metadata already exists, update it to `1.0.0` only if appropriate.

Do not add ceremonial release machinery merely for this brief.

A Git tag/GitHub release is out of scope unless explicitly requested.

## Verification

Run:

```text
full test suite
canonical 1,444-body validation
CK regression validation
mojibake guard
git diff --check
```

Expected:

```text
tests pass
1,444 / 1,444 exact
0 mismatches
0 errors
CK regressions unchanged
mojibake passed
diff-check passed except accepted existing line-ending warnings
```

No generation result or RNG sequence should change. If generation behaviour changes, stop and explain why.

## Deliverable

Report:

1. changed files;
2. stale/superseded documentation reconciled;
3. new v1.0 validation-baseline document;
4. README/status changes;
5. backlog changes;
6. AGENTS changes;
7. verification results;
8. confirmation generation behaviour did not change;
9. genuinely remaining OPEN items;
10. no commit/push unless explicitly requested.

Suggested commit message after review:

```text
docs: establish resource reproducer v1.0 baseline
```
