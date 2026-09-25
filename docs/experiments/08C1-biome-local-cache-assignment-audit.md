## Verdict

Cached-family assignment is already represented correctly for an ordinary cache hit:

```text
Biome selects root X
→ cache lookup finds family X
→ biome_result.family_access.family references cached family X
```

The later biome references the exact cached `ResourceFamilyResult`; its root and emitted descendants are recoverable through:

```python
biome_result.family_access.family.emitted_resources
```

However, the model cannot represent cached-family assignment when the five-tree or shared-eight guard fires. Both guard paths set `common_entry = None`, so no cache key is selected, `family_access` remains `None`, and the biome has no link to an existing family. Most of the reported incorrect forecasts are on these guard paths, so they are not explained solely by faulty reporting.

Planet-wide 1,444/1,444 validation does not test this missing biome-local relationship.

## Code-path walkthrough

### First generation

After Common selection, `_run_planet()` calls `get_or_generate_family()` at [generation.py](../../src/starfield_resource_reproducer/generation.py#L959).

For a new root:

1. `generate_family()` records the root.
2. Descendant inclusion and candidate selection run.
3. Included, capacity-accepted descendants enter `emitted_descendants`.
4. `emitted_resources` becomes the accepted root plus emitted descendants.
5. The resulting `ResourceFamilyResult` is cached by root FormID.
6. The biome receives a `FamilyAccessResult` referencing that family.

### Ordinary cache hit

At [generation.py](../../src/starfield_resource_reproducer/generation.py#L642):

- `cached = family_cache[root_form_id]`;
- no descendant-generation RNG is consumed;
- `FamilyAccessResult.family` is the cached object;
- `cache_hit=True`;
- the cached root and `cached.emitted_descendants` are passed through `PlanetResourceState.record()` again with the later biome’s context;
- those records normally have `occupied_new_slot=False`, because the FormIDs already occupy planet-wide state.

The returned `FamilyAccessResult` is attached directly to the current `BiomeFamilyGenerationResult` at [generation.py](../../src/starfield_resource_reproducer/generation.py#L991).

Existing tests prove object identity and zero descendant RNG consumption at [test_family_generation.py](../../tests/test_family_generation.py#L147). Algorab also verifies a later biome receives `family_access` with `cache_hit=True` at [test_algorab_live_evidence.py](../../tests/test_algorab_live_evidence.py#L8).

### Guard paths

The current code behaves differently when either guard fires:

- Five-tree guard: [generation.py](../../src/starfield_resource_reproducer/generation.py#L883)
- Shared-eight guard: [generation.py](../../src/starfield_resource_reproducer/generation.py#L898)

Both set:

```python
common_entry = None
```

Consequently:

- `BiomeOrchestrationResult.common_root` is `None`;
- `get_or_generate_family()` is not called;
- `BiomeFamilyGenerationResult.family_access` is `None`;
- no cached family can be linked to that biome;
- no Common/descendant biome occurrences are created.

The planet-level `family_cache` still contains existing families, but the result contains no information identifying which, if any, should be assigned to the guarded biome.

## Field semantics

| Field | Current meaning |
|---|---|
| `BiomeFamilyGenerationResult.orchestration` | Biome, effective RSGD, selected Special, and selected Common root. A guard records no Common root. |
| `BiomeFamilyGenerationResult.family_access` | The new or cached family accessed for this biome. Correct for an ordinary successful Common selection; `None` on guard paths. |
| `FamilyAccessResult.family` | Exact new or cached `ResourceFamilyResult`. |
| `FamilyAccessResult.cache_hit` | Whether this biome reused an existing family configuration. |
| `ResourceFamilyResult.root` | Common root. |
| `emitted_descendants` | Only descendants whose inclusion test passed and whose resource-state recording was accepted. |
| `emitted_resources` | Accepted root plus `emitted_descendants`. |
| `levels[].selected_candidate` | Structural candidates, including candidates not emitted. These are not all included in `emitted_resources`. |
| `ResourceOccurrence` | Provenance contribution with biome context and planet-state insertion/deduplication outcome. |

`emitted_resources` does not include structurally selected descendants that failed inclusion. It is also filtered by shared capacity during the family’s original generation. For ordinary cache reuse, it is the best existing representation of the family configuration assigned to the biome.

## Planet state versus biome assignment

The current model separates most concepts, but not completely:

| Concept | Audit result |
|---|---|
| A. Planet-wide unique identities | Represented by `PlanetResourceState` and `occupied_resource_ids`. |
| B. Planet-wide family cache | Represented correctly by the FormID-keyed `family_cache`. |
| C. Per-biome Common-family assignment | Correct for ordinary selections and cache hits; missing on guard paths. |
| D. Per-biome Everywhere assignment | Recoverable through biome-context `EVERYWHERE` occurrences. The planet-level `everywhere_resources` field alone loses biome mapping. |
| E. Per-biome Special assignment | Represented by `special_selection` and biome-context Special occurrences. |
| F. Provenance bookkeeping | Cache hits create new biome-context occurrences without occupying new slots. This is separate from the cached-family object reference. |

A reporting layer must not equate `occupied_new_slot=False` with “not present in this biome.”

## Likely source of incorrect forecasts

No dedicated biome field-sheet forecast implementation exists in the repository.

Two reporting hazards do exist:

1. The dossier insertion ledger only treats `RESOURCE_SLOT_OCCUPIED` as an insertion at [dossier.py](../../src/starfield_resource_reproducer/dossier.py#L129). It therefore omits cache-hit resources, which produce `RESOURCE_SLOT_ALREADY_OCCUPIED`.

2. The family ledger includes cache hits, but sets `root_emitted=not access.cache_hit` at [dossier.py](../../src/starfield_resource_reproducer/dossier.py#L342). That means “newly emitted/inserted,” not “assigned to this biome,” and could be misinterpreted.

For an ordinary cache hit, reporting should read `biome.family_access.family.emitted_resources`, not only new slot events or unique `planet.family_results`.

However, the named `NONE` forecasts are principally guard-path results:

| Planet/biome | Current reproducer path |
|---|---|
| Bara VII-d — Hills | Five-tree guard |
| Indum IV-d — Sandy Desert, Wetlands, Swamp | Shared-eight guard |
| Zeta Ophiuchi I — Frozen Dunes, Deciduous Forest, Savanna, Swamp | Shared-eight guard |
| Jaffa VII-b — Volcanic, Plateau, Hills | Shared-eight guard |
| Pyraas VIII-a — Sandy Desert | Five-tree guard |

Even a correct `family_access.family.emitted_resources` reporter returns nothing for these biomes because `family_access` is genuinely `None`.

## Jaffa evidence classification

- **PROVEN LIVE:** a later biome selecting Lead receives the complete cached Lead configuration: Lead, Tungsten, Titanium, and Dysprosium.
- **PROVEN STATIC (current code):** an ordinary cache hit attaches the cached `ResourceFamilyResult` to the later biome and consumes no descendant RNG.
- **STRONG:** `family_access.family.emitted_resources` is the best current correspondence to the reused CK family slots.
- **OPEN:** how Jaffa Volcanic and Plateau receive Lead after the current model’s shared-eight guard. The supplied cache-hit evidence does not prove that a guard directly chooses or copies a particular cached family.
- **OPEN:** Bara Hills → Iron and the analogous Indum, Zeta, and Pyraas guard-path assignments. Ordinary cache-hit reuse cannot explain them because the current model never selects a root on those invocations.

## Minimal future implementation surface

For ordinary cache hits, no production-generation change is required. A future biome report could aggregate:

- `family_access.family.emitted_resources`;
- biome-context Everywhere occurrences;
- biome-context Special occurrences.

Likely reporting changes would be confined to a new reporting helper and, if reused, [dossier.py](../../src/starfield_resource_reproducer/dossier.py).

Guard-path assignments require additional engine evidence before implementation. If recovered, the likely surface would include:

- guard handling in `_run_planet()` in [generation.py](../../src/starfield_resource_reproducer/generation.py);
- an explicit biome-assignment representation distinct from Common selection and planet-wide insertion;
- corresponding diagnostics and focused biome-assignment tests.

No files were edited, no tests or validation artifacts were regenerated, and no commit or push was performed. The only worktree item remains the supplied untracked audit brief.
