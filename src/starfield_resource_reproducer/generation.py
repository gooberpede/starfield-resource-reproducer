"""Starfield planetary orchestration and resource-family generation.

Purpose:
    Reproduce control flow from PNDT biome order through Common-family results.
Responsibilities:
    Run the recovered biome shuffle, model provisional Everywhere discovery,
    resolve effective RSGDs, and perform ordered Special/Common selectors using
    one evolving ``StarfieldRng``; generate and cache descendant families while
    emitting structured diagnostics.
Boundaries:
    CSV loading and oracle validation remain separate. ``orchestrate_planet``
    retains the Brief 03 partial boundary; ``generate_planet_families`` adds the
    family layer without representing a final canonical-validation workflow.
Evidence notes:
    Kreet proves the observed shuffle and processing order. The broader loop and
    empty-Special behavior are evidence-qualified below and remain easy to replace.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Callable, Sequence

from .candidates import build_descendant_candidates

from .diagnostics import (
    DiagnosticEvent,
    EventKind,
    WeightedCandidateDiagnostic,
    event,
)
from .domain import (
    Biome,
    FormId,
    GenerationRarity,
    IRESNode,
    Planet,
    RSGDDefinition,
    RSGDResourceEntry,
    RSGDSource,
    ResourceRef,
)
from .prng import RngDraw, StarfieldRng


@dataclass(frozen=True, slots=True)
class BiomeShuffleResult:
    """The shuffled biome sequence and every random swap decision."""

    biomes: tuple[Biome, ...]
    events: tuple[DiagnosticEvent, ...]
    raw_draws_consumed: int


@dataclass(frozen=True, slots=True)
class BiomeOrchestrationResult:
    """Partial per-biome result ending immediately after Common-root selection."""

    biome: Biome
    effective_rsgd: RSGDDefinition
    rsgd_resolution_source: RSGDSource
    special_selection: ResourceRef | None
    common_root: ResourceRef | None
    events: tuple[DiagnosticEvent, ...]


@dataclass(frozen=True, slots=True)
class PlanetOrchestrationResult:
    """Partial planet result that deliberately contains no descendants or final set."""

    planet: Planet
    initial_biomes: tuple[Biome, ...]
    shuffled_biomes: tuple[Biome, ...]
    everywhere_resources: tuple[ResourceRef, ...]
    biome_results: tuple[BiomeOrchestrationResult, ...]
    events: tuple[DiagnosticEvent, ...]
    final_draw_count: int


@dataclass(frozen=True, slots=True)
class DescendantLevelResult:
    """One rarity level's structural choice and independent emission decision."""

    rarity: GenerationRarity
    candidates: tuple[ResourceRef, ...]
    inclusion_roll: float | None
    inclusion_threshold: float
    selected_candidate: ResourceRef | None
    emitted: bool
    inclusion_draw: RngDraw | None
    candidate_draw: RngDraw | None


@dataclass(frozen=True, slots=True)
class ResourceFamilyResult:
    """Immutable generated configuration for one Common root."""

    root: ResourceRef
    levels: tuple[DescendantLevelResult, ...]
    emitted_descendants: tuple[ResourceRef, ...]
    emitted_resources: tuple[ResourceRef, ...]
    emitted_form_ids: frozenset[FormId]
    events: tuple[DiagnosticEvent, ...]


@dataclass(frozen=True, slots=True)
class FamilyAccessResult:
    """One cache lookup, including transparent RNG accounting."""

    family: ResourceFamilyResult
    cache_hit: bool
    draw_count_before: int
    draw_count_after: int
    events: tuple[DiagnosticEvent, ...]


@dataclass(frozen=True, slots=True)
class BiomeFamilyGenerationResult:
    """Outer biome selections plus its optional Common-family configuration."""

    orchestration: BiomeOrchestrationResult
    family_access: FamilyAccessResult | None


@dataclass(frozen=True, slots=True)
class PlanetFamilyGenerationResult:
    """Planet-scope family results without canonical-oracle comparison."""

    planet: Planet
    initial_biomes: tuple[Biome, ...]
    shuffled_biomes: tuple[Biome, ...]
    everywhere_resources: tuple[ResourceRef, ...]
    biome_results: tuple[BiomeFamilyGenerationResult, ...]
    family_cache: Mapping[FormId, ResourceFamilyResult]
    emitted_resources: tuple[ResourceRef, ...]
    emitted_form_ids: frozenset[FormId]
    events: tuple[DiagnosticEvent, ...]
    final_draw_count: int


def shuffle_biomes(
    biomes: Sequence[Biome], rng: StarfieldRng
) -> BiomeShuffleResult:
    """Run the recovered Starfield biome shuffle with transparent swap events.

    STRONG: the ascending target loop exactly reproduces Kreet's two observed
    swaps. Its behavior for all biome counts has not been directly live-traced.
    It executes ``N - 1`` iterations, so a one-biome list consumes no draw.
    """

    working = list(biomes)
    events: list[DiagnosticEvent] = []
    initial_draw_count = rng.draw_count

    for iteration, target_position in enumerate(range(1, len(working))):
        order_before = tuple(biome.index for biome in working)
        bound = target_position + 1
        selected_position = rng.next_index(bound)
        rng_draw = _required_last_draw(rng)
        working[target_position], working[selected_position] = (
            working[selected_position],
            working[target_position],
        )
        events.append(
            event(
                EventKind.SHUFFLE_STEP,
                operation="biome_shuffle_index",
                rng_draw=rng_draw,
                iteration=iteration,
                input_biome_count=len(working),
                target_position=target_position,
                bound=bound,
                selected_position=selected_position,
                swap_left=selected_position,
                swap_right=target_position,
                order_before=order_before,
                resulting_order=tuple(biome.index for biome in working),
            )
        )

    return BiomeShuffleResult(
        biomes=tuple(working),
        events=tuple(events),
        raw_draws_consumed=rng.draw_count - initial_draw_count,
    )


_DESCENDANT_LEVELS = (
    GenerationRarity.UNCOMMON,
    GenerationRarity.RARE,
    GenerationRarity.EXOTIC,
    GenerationRarity.UNIQUE,
)


def generate_family(
    root_entry: RSGDResourceEntry,
    ires_nodes: Mapping[FormId, IRESNode],
    rng: StarfieldRng,
) -> ResourceFamilyResult:
    """Generate a new Common family using the selected root entry's chances."""

    root = root_entry.resource
    current_form_id = root.form_id
    events: list[DiagnosticEvent] = [
        event(
            EventKind.FAMILY_BEGIN,
            operation="begin_resource_family",
            root=root,
            draw_count_before=rng.draw_count,
        ),
        event(
            EventKind.ROOT_EMITTED,
            operation="emit_common_root",
            root=root,
            emitted_resource=root,
            rng_consumed=False,
        ),
    ]
    levels: list[DescendantLevelResult] = []
    emitted_descendants: list[ResourceRef] = []

    for rarity in _DESCENDANT_LEVELS:
        threshold = float(_descendant_chance(root_entry, rarity) / 100)
        events.append(
            event(
                EventKind.DESCENDANT_LEVEL_BEGIN,
                operation="begin_descendant_level",
                root=root,
                rarity=rarity,
                current_structural_form_id=current_form_id,
                draw_count_before=rng.draw_count,
            )
        )
        candidates = build_descendant_candidates(
            root.form_id, current_form_id, rarity, ires_nodes
        )
        events.append(
            event(
                EventKind.DESCENDANT_CANDIDATES,
                operation="build_descendant_candidates",
                root=root,
                rarity=rarity,
                candidates=candidates,
                candidate_count=len(candidates),
                combination_order="children(root) + children(current)",
            )
        )

        if not candidates:
            # PROVISIONAL: no live zero-candidate branch is available. The
            # current interpretation consumes no unexplained draws and retains
            # the current structural node until evidence establishes otherwise.
            events.append(
                event(
                    EventKind.DESCENDANT_OMITTED,
                    operation="skip_empty_descendant_level",
                    root=root,
                    rarity=rarity,
                    selected_candidate=None,
                    reason="no_candidates",
                    evidence_status="PROVISIONAL",
                    inclusion_rng_consumed=False,
                    candidate_rng_consumed=False,
                    structural_node_changed=False,
                    draw_count_after=rng.draw_count,
                )
            )
            levels.append(
                DescendantLevelResult(
                    rarity=rarity,
                    candidates=(),
                    inclusion_roll=None,
                    inclusion_threshold=threshold,
                    selected_candidate=None,
                    emitted=False,
                    inclusion_draw=None,
                    candidate_draw=None,
                )
            )
            continue

        inclusion_roll = rng.next_float01()
        inclusion_draw = _required_last_draw(rng)
        included = inclusion_roll < threshold
        events.append(
            event(
                EventKind.DESCENDANT_INCLUSION_ROLL,
                operation="descendant_inclusion_roll",
                rng_draw=inclusion_draw,
                root=root,
                rarity=rarity,
                roll=inclusion_roll,
                threshold=threshold,
                included=included,
            )
        )

        # PROVEN: selection follows inclusion and consumes a draw even with one
        # candidate. It determines traversal independently of emission.
        selected_index = rng.next_index(len(candidates))
        candidate_draw = _required_last_draw(rng)
        selected = candidates[selected_index]
        previous_form_id = current_form_id
        current_form_id = selected.form_id
        events.append(
            event(
                EventKind.DESCENDANT_CANDIDATE_SELECTED,
                operation="select_descendant_candidate",
                rng_draw=candidate_draw,
                root=root,
                rarity=rarity,
                selected_index=selected_index,
                selected_candidate=selected,
                previous_structural_form_id=previous_form_id,
                current_structural_form_id=current_form_id,
            )
        )
        if included:
            emitted_descendants.append(selected)
        events.append(
            event(
                EventKind.DESCENDANT_EMITTED if included else EventKind.DESCENDANT_OMITTED,
                operation="complete_descendant_emission",
                root=root,
                rarity=rarity,
                selected_candidate=selected,
                emitted=included,
                structural_traversal_continues=True,
            )
        )
        levels.append(
            DescendantLevelResult(
                rarity=rarity,
                candidates=candidates,
                inclusion_roll=inclusion_roll,
                inclusion_threshold=threshold,
                selected_candidate=selected,
                emitted=included,
                inclusion_draw=inclusion_draw,
                candidate_draw=candidate_draw,
            )
        )

    emitted_resources = _unique_resources((root, *emitted_descendants))
    events.append(
        event(
            EventKind.FAMILY_END,
            operation="end_resource_family",
            root=root,
            structural_path=(
                root,
                *(level.selected_candidate for level in levels if level.selected_candidate),
            ),
            emitted_resources=emitted_resources,
            draw_count_after=rng.draw_count,
        )
    )
    return ResourceFamilyResult(
        root=root,
        levels=tuple(levels),
        emitted_descendants=tuple(emitted_descendants),
        emitted_resources=emitted_resources,
        emitted_form_ids=frozenset(resource.form_id for resource in emitted_resources),
        events=tuple(events),
    )


def get_or_generate_family(
    root_entry: RSGDResourceEntry,
    family_cache: MutableMapping[FormId, ResourceFamilyResult],
    ires_nodes: Mapping[FormId, IRESNode],
    rng: StarfieldRng,
) -> FamilyAccessResult:
    """Reuse a planet-scope family or generate and cache it on first selection."""

    draw_count_before = rng.draw_count
    cached = family_cache.get(root_entry.resource_form_id)
    if cached is not None:
        # PROVEN: an existing family is reused instead of rerolling descendants.
        # PROVISIONAL: the recovered bypass currently consumes no additional
        # words; exact cache-branch RNG behavior lacks its own live trace.
        cache_event = event(
            EventKind.FAMILY_CACHE_HIT,
            operation="reuse_resource_family",
            root=cached.root,
            cache_key=root_entry.resource_form_id,
            draw_count_before=draw_count_before,
            draw_count_after=rng.draw_count,
            descendant_rng_consumed=False,
            evidence_status="PROVISIONAL",
        )
        return FamilyAccessResult(
            family=cached,
            cache_hit=True,
            draw_count_before=draw_count_before,
            draw_count_after=rng.draw_count,
            events=(cache_event,),
        )

    family = generate_family(root_entry, ires_nodes, rng)
    family_cache[root_entry.resource_form_id] = family
    return FamilyAccessResult(
        family=family,
        cache_hit=False,
        draw_count_before=draw_count_before,
        draw_count_after=rng.draw_count,
        events=family.events,
    )


def orchestrate_planet(planet: Planet) -> PlanetOrchestrationResult:
    """Run the Brief 03 partial boundary without descendant generation."""

    result = _run_planet(planet, None)
    if not isinstance(result, PlanetOrchestrationResult):  # pragma: no cover
        raise AssertionError("partial orchestration returned a family result")
    return result


def generate_planet_families(
    planet: Planet,
    ires_nodes: Mapping[FormId, IRESNode],
) -> PlanetFamilyGenerationResult:
    """Run outer orchestration and family generation with one evolving RNG."""

    result = _run_planet(planet, ires_nodes)
    if not isinstance(result, PlanetFamilyGenerationResult):  # pragma: no cover
        raise AssertionError("family generation returned a partial result")
    return result


def _run_planet(
    planet: Planet,
    ires_nodes: Mapping[FormId, IRESNode] | None,
) -> PlanetOrchestrationResult | PlanetFamilyGenerationResult:
    """Shared planet pipeline; descendants are enabled only with an IRES graph."""

    # PROVEN: one RSCS-seeded RNG state evolves through shuffle and every biome.
    rng = StarfieldRng(planet.resource_creation_seed)
    initial_biomes = tuple(planet.biomes)
    all_events: list[DiagnosticEvent] = [
        event(
            EventKind.RNG_SEEDED,
            operation="seed_planet_rng",
            seed=planet.resource_creation_seed,
            draw_count=0,
        ),
        event(
            EventKind.BIOME_LIST_INITIAL,
            operation="copy_pndt_biome_order",
            biome_count=len(initial_biomes),
            biome_indices=tuple(biome.index for biome in initial_biomes),
        ),
    ]

    shuffle = shuffle_biomes(initial_biomes, rng)
    all_events.extend(shuffle.events)
    all_events.append(
        event(
            EventKind.BIOME_LIST_SHUFFLED,
            operation="complete_biome_shuffle",
            input_biome_count=len(initial_biomes),
            raw_draws_consumed=shuffle.raw_draws_consumed,
            biome_indices=tuple(biome.index for biome in shuffle.biomes),
        )
    )

    everywhere_resources, everywhere_events = _discover_everywhere(initial_biomes)
    all_events.extend(everywhere_events)

    biome_results: list[BiomeOrchestrationResult] = []
    family_biome_results: list[BiomeFamilyGenerationResult] = []
    family_cache: dict[FormId, ResourceFamilyResult] = {}
    emitted_resources: list[ResourceRef] = list(everywhere_resources)
    for processing_position, biome in enumerate(shuffle.biomes):
        biome_events: list[DiagnosticEvent] = [
            event(
                EventKind.BIOME_BEGIN,
                operation="begin_biome_orchestration",
                processing_position=processing_position,
                biome_index=biome.index,
                biome_form_id=biome.form_id,
                biome_name=biome.name,
                draw_count=rng.draw_count,
            )
        ]
        effective_rsgd = biome.effective_rsgd
        resolution_source = (
            RSGDSource.PNDT if biome.pndt_rsgd is not None else RSGDSource.BIOM
        )
        biome_events.append(
            event(
                EventKind.RSGD_RESOLVED,
                operation="resolve_effective_rsgd",
                biome_index=biome.index,
                rsgd_form_id=effective_rsgd.form_id,
                rsgd_editor_id=effective_rsgd.editor_id,
                resolution_source=resolution_source,
                definition_provenance=effective_rsgd.source,
            )
        )

        special_entry, special_events = _select_weighted(
            rng,
            effective_rsgd,
            GenerationRarity.SPECIAL,
            lambda entry: float(entry.special_chance),
            begin_kind=EventKind.SPECIAL_PASS_BEGIN,
            roll_kind=EventKind.SPECIAL_PASS_RESULT,
            operation="special_selector",
            biome_index=biome.index,
        )
        biome_events.extend(special_events)

        common_entry, common_events = _select_weighted(
            rng,
            effective_rsgd,
            GenerationRarity.COMMON,
            lambda entry: float(entry.common_chance),
            begin_kind=EventKind.COMMON_PASS_BEGIN,
            roll_kind=EventKind.COMMON_ROLL,
            operation="common_root_selector",
            biome_index=biome.index,
        )
        biome_events.extend(common_events)
        biome_events.append(
            event(
                EventKind.COMMON_SELECTED,
                operation="complete_common_root_selector",
                biome_index=biome.index,
                selected_resource=(common_entry.resource if common_entry else None),
            )
        )

        family_access: FamilyAccessResult | None = None
        if special_entry is not None:
            emitted_resources.append(special_entry.resource)
        if ires_nodes is not None and common_entry is not None:
            family_access = get_or_generate_family(
                common_entry, family_cache, ires_nodes, rng
            )
            biome_events.extend(family_access.events)
            emitted_resources.extend(family_access.family.emitted_resources)
        biome_events.append(
            event(
                EventKind.BIOME_END,
                operation="end_biome_orchestration",
                biome_index=biome.index,
                draw_count=rng.draw_count,
                special_selection=(special_entry.resource if special_entry else None),
                common_root=(common_entry.resource if common_entry else None),
            )
        )
        all_events.extend(biome_events)
        orchestration_result = BiomeOrchestrationResult(
            biome=biome,
            effective_rsgd=effective_rsgd,
            rsgd_resolution_source=resolution_source,
            special_selection=(special_entry.resource if special_entry else None),
            common_root=(common_entry.resource if common_entry else None),
            events=tuple(biome_events),
        )
        biome_results.append(orchestration_result)
        if ires_nodes is not None:
            family_biome_results.append(
                BiomeFamilyGenerationResult(orchestration_result, family_access)
            )

    all_events.append(
        event(
            EventKind.PLANET_ORCHESTRATION_END,
            operation="end_planet_orchestration",
            biome_count=len(biome_results),
            final_draw_count=rng.draw_count,
            descendants_implemented=ires_nodes is not None,
        )
    )
    if ires_nodes is not None:
        unique_emitted = _unique_resources(emitted_resources)
        return PlanetFamilyGenerationResult(
            planet=planet,
            initial_biomes=initial_biomes,
            shuffled_biomes=shuffle.biomes,
            everywhere_resources=everywhere_resources,
            biome_results=tuple(family_biome_results),
            family_cache=MappingProxyType(dict(family_cache)),
            emitted_resources=unique_emitted,
            emitted_form_ids=frozenset(
                resource.form_id for resource in unique_emitted
            ),
            events=tuple(all_events),
            final_draw_count=rng.draw_count,
        )
    return PlanetOrchestrationResult(
        planet=planet,
        initial_biomes=initial_biomes,
        shuffled_biomes=shuffle.biomes,
        everywhere_resources=everywhere_resources,
        biome_results=tuple(biome_results),
        events=tuple(all_events),
        final_draw_count=rng.draw_count,
    )


def _discover_everywhere(
    biomes: Sequence[Biome],
) -> tuple[tuple[ResourceRef, ...], tuple[DiagnosticEvent, ...]]:
    # PROVISIONAL: static Everywhere entries are modeled as upstream resources;
    # the exact runtime insertion routine and duplicate behavior remain unknown.
    resources: list[ResourceRef] = []
    events: list[DiagnosticEvent] = []
    seen_form_ids = set()
    for biome in biomes:
        for entry in biome.effective_rsgd.entries:
            if (
                entry.resource_rarity is not GenerationRarity.EVERYWHERE
                or entry.everywhere_chance <= 0
                or entry.resource_form_id in seen_form_ids
            ):
                continue
            seen_form_ids.add(entry.resource_form_id)
            resources.append(entry.resource)
            events.append(
                event(
                    EventKind.EVERYWHERE_DISCOVERED,
                    operation="provisional_upstream_everywhere_discovery",
                    biome_index=biome.index,
                    rsgd_form_id=biome.effective_rsgd.form_id,
                    resource=entry.resource,
                    chance_percent=float(entry.everywhere_chance),
                    evidence_status="PROVISIONAL",
                    rng_consumed=False,
                )
            )
    return tuple(resources), tuple(events)


def _select_weighted(
    rng: StarfieldRng,
    rsgd: RSGDDefinition,
    rarity: GenerationRarity,
    weight_percent: Callable[[RSGDResourceEntry], float],
    *,
    begin_kind: EventKind,
    roll_kind: EventKind,
    operation: str,
    biome_index: int,
) -> tuple[RSGDResourceEntry | None, tuple[DiagnosticEvent, ...]]:
    eligible = tuple(
        entry for entry in rsgd.entries if entry.resource_rarity is rarity
    )
    begin = event(
        begin_kind,
        operation=f"begin_{operation}",
        biome_index=biome_index,
        category=rarity,
        eligible_count=len(eligible),
        draw_count_before=rng.draw_count,
    )

    # STRONG: the recovered category selector obtains its probability value
    # before walking entries. This naturally consumes Mimas draw 1 even though
    # no Special entry is eligible; no synthetic alignment draw is inserted.
    roll = rng.next_float01()
    rng_draw = _required_last_draw(rng)
    cumulative = 0.0
    candidates: list[WeightedCandidateDiagnostic] = []
    selected: RSGDResourceEntry | None = None
    for entry in eligible:
        weight = weight_percent(entry)
        cumulative += weight / 100.0
        candidates.append(
            WeightedCandidateDiagnostic(
                rsgd_index=entry.index,
                resource_form_id=entry.resource_form_id,
                resource_name=entry.resource_name,
                weight_percent=weight,
                cumulative_threshold=cumulative,
            )
        )
        # PROVEN: selector thresholds are cumulative in RSGD order and are not
        # normalized. Equality falls through because the runtime comparison is >.
        if selected is None and cumulative > roll:
            selected = entry

    result = event(
        roll_kind,
        operation=operation,
        rng_draw=rng_draw,
        biome_index=biome_index,
        category=rarity,
        eligible_count=len(eligible),
        rng_consumed=True,
        roll=roll,
        candidates=tuple(candidates),
        selected_resource=(selected.resource if selected else None),
    )
    return selected, (begin, result)


def _descendant_chance(
    root_entry: RSGDResourceEntry, rarity: GenerationRarity
) -> Decimal:
    """Return the selected root entry's percentage for one descendant rarity."""

    chance_by_rarity = {
        GenerationRarity.UNCOMMON: root_entry.uncommon_chance,
        GenerationRarity.RARE: root_entry.rare_chance,
        GenerationRarity.EXOTIC: root_entry.exotic_chance,
        GenerationRarity.UNIQUE: root_entry.unique_chance,
    }
    try:
        return chance_by_rarity[rarity]
    except KeyError as error:  # Defensive: callers use only descendant levels.
        raise ValueError(f"{rarity.value} is not a descendant rarity") from error


def _unique_resources(resources: Sequence[ResourceRef]) -> tuple[ResourceRef, ...]:
    """Preserve generation order while enforcing FormID identity once."""

    result: list[ResourceRef] = []
    seen: set[FormId] = set()
    for resource in resources:
        if resource.form_id not in seen:
            seen.add(resource.form_id)
            result.append(resource)
    return tuple(result)


def _required_last_draw(rng: StarfieldRng) -> RngDraw:
    draw = rng.last_draw
    if draw is None:  # Defensive invariant: only called immediately after a draw.
        raise RuntimeError("expected an RNG draw to have been recorded")
    return draw
