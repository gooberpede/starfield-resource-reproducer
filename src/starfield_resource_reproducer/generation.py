"""Starfield planetary orchestration and resource-family generation.

Purpose:
    Reproduce control flow from PNDT biome order through Common-family results.
Responsibilities:
    Prepopulate atmosphere and Everywhere resources, run the recovered biome
    shuffle, resolve effective RSGDs, and perform the category-generic ordered
    Special/Common selector using one evolving ``StarfieldRng``; maintain shared
    unique-FormID capacity, provenance occurrences, cached families, and diagnostics.
Boundaries:
    CSV loading and oracle validation remain separate. ``orchestrate_planet``
    retains the Brief 03 partial boundary; ``generate_planet_families`` adds the
    family layer; ``generate_planet`` exposes the complete prediction boundary.
Evidence notes:
    The pre-main ordering, selector draw behavior, and five-tree/shared-eight
    pre-Common guards are PROVEN. Treating duplicate provenance occurrences as one
    occupied slot is the current STRONG engine-shaped capacity model and remains
    explicit rather than being upgraded to universal proof.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
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
    AtmosphericResourceRecord,
    Biome,
    FormId,
    GenerationRarity,
    IRESNode,
    Planet,
    RSGDDefinition,
    RSGDResourceEntry,
    RSGDSource,
    ResourceRef,
    ResourceOccurrence,
    ResourceProvenance,
)
from .prng import RngDraw, StarfieldRng


COMMON_TREE_LIMIT = 5


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


class ZeroCandidatePolicy(str, Enum):
    """Evidence-qualified empty-descendant RNG policies for diagnostics.

    ``CONSUME_RAW`` is the PROVEN production default. Live Algorab I evidence
    establishes one raw MT word of consumption without identifying the engine's
    high-level operation. The other values remain COUNTERFACTUAL modes.
    """

    CONSUME_RAW = "CONSUME_RAW"
    CONSUME_NONE = "CONSUME_NONE"
    CONSUME_INCLUSION = "CONSUME_INCLUSION"
    CONSUME_BOTH = "CONSUME_BOTH"


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
class PlanetGenerationResult:
    """Complete deterministic planet prediction, independent of the oracle."""

    planet: Planet
    initial_biomes: tuple[Biome, ...]
    shuffled_biomes: tuple[Biome, ...]
    atmospheric_occurrences: tuple[ResourceOccurrence, ...]
    everywhere_resources: tuple[ResourceRef, ...]
    biome_results: tuple[BiomeFamilyGenerationResult, ...]
    family_cache: Mapping[FormId, ResourceFamilyResult]
    special_resources: tuple[ResourceRef, ...]
    family_results: tuple[ResourceFamilyResult, ...]
    occurrences: tuple[ResourceOccurrence, ...]
    occupied_resource_ids: frozenset[FormId]
    rsgd_resources: tuple[ResourceRef, ...]
    rsgd_form_ids: frozenset[FormId]
    predicted_resources: tuple[ResourceRef, ...]
    predicted_form_ids: frozenset[FormId]
    events: tuple[DiagnosticEvent, ...]
    final_draw_count: int
    zero_candidate_policy: ZeroCandidatePolicy

    @property
    def emitted_resources(self) -> tuple[ResourceRef, ...]:
        """Compatibility name retained for the Brief 04 API."""

        return self.predicted_resources

    @property
    def emitted_form_ids(self) -> frozenset[FormId]:
        """Compatibility name retained for the Brief 04 API."""

        return self.predicted_form_ids

    @property
    def atmospheric_resources(self) -> tuple[ResourceRef, ...]:
        """Return accepted ATMO-channel identities in stable input order."""

        return _resources_from_occurrences(self.atmospheric_occurrences)

    def occurrences_for(
        self, provenance: ResourceProvenance
    ) -> tuple[ResourceOccurrence, ...]:
        """Return all accepted and rejected contributions for one mechanism."""

        return tuple(item for item in self.occurrences if item.provenance is provenance)

    @property
    def everywhere_occurrences(self) -> tuple[ResourceOccurrence, ...]:
        return self.occurrences_for(ResourceProvenance.EVERYWHERE)

    @property
    def special_occurrences(self) -> tuple[ResourceOccurrence, ...]:
        return self.occurrences_for(ResourceProvenance.SPECIAL)

    @property
    def common_occurrences(self) -> tuple[ResourceOccurrence, ...]:
        return self.occurrences_for(ResourceProvenance.COMMON)

    @property
    def descendant_occurrences(self) -> tuple[ResourceOccurrence, ...]:
        return self.occurrences_for(ResourceProvenance.DESCENDANT)


class PlanetResourceState:
    """Shared eight-slot identity state with independent provenance occurrences.

    STRONG / engine-shaped model: capacity counts unique IRES FormIDs. Repeating
    a FormID through another provenance records another occurrence but consumes
    no second slot. New identities are rejected once eight IDs are occupied.
    """

    CAPACITY = 8

    def __init__(self) -> None:
        self._occupied: dict[FormId, ResourceRef] = {}
        self._occurrences: list[ResourceOccurrence] = []

    @property
    def occupied_resource_ids(self) -> frozenset[FormId]:
        return frozenset(self._occupied)

    @property
    def occupied_resources(self) -> tuple[ResourceRef, ...]:
        return tuple(self._occupied.values())

    @property
    def occurrences(self) -> tuple[ResourceOccurrence, ...]:
        return tuple(self._occurrences)

    @property
    def at_capacity(self) -> bool:
        return len(self._occupied) >= self.CAPACITY

    def record(
        self,
        resource: ResourceRef,
        provenance: ResourceProvenance,
        **context: object,
    ) -> tuple[ResourceOccurrence, tuple[DiagnosticEvent, ...]]:
        """Record provenance and try to occupy the shared FormID state."""

        before = len(self._occupied)
        already_occupied = resource.form_id in self._occupied
        accepted = already_occupied or before < self.CAPACITY
        occupied_new = accepted and not already_occupied
        if occupied_new:
            self._occupied[resource.form_id] = resource
        occurrence = ResourceOccurrence(
            resource=resource,
            provenance=provenance,
            occupies_state=accepted,
            occupied_new_slot=occupied_new,
            **context,
        )
        self._occurrences.append(occurrence)
        occurrence_event = event(
            EventKind.RESOURCE_OCCURRENCE_RECORDED,
            operation="record_resource_occurrence",
            resource=resource,
            provenance=provenance,
            accepted=accepted,
            occupied_new_slot=occupied_new,
            occupied_count_before=before,
            occupied_count_after=len(self._occupied),
        )
        if occupied_new:
            slot_kind = EventKind.RESOURCE_SLOT_OCCUPIED
        elif already_occupied:
            slot_kind = EventKind.RESOURCE_SLOT_ALREADY_OCCUPIED
        else:
            slot_kind = EventKind.RESOURCE_CAPACITY_REACHED
        slot_event = event(
            slot_kind,
            operation="update_shared_resource_state",
            resource=resource,
            provenance=provenance,
            capacity=self.CAPACITY,
            occupied_count_before=before,
            occupied_count_after=len(self._occupied),
        )
        return occurrence, (occurrence_event, slot_event)


# Brief 04 callers may continue importing the earlier conceptual name.
PlanetFamilyGenerationResult = PlanetGenerationResult


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
        # PROVEN: biome shuffle uses the integer rejection/modulo helper. It is
        # not interchangeable with descendant float32 scaled selection.
        selected_position = rng.next_bounded_integer(bound)
        rng_draw = _required_last_draw(rng)
        attempts = rng.last_bounded_attempts
        working[target_position], working[selected_position] = (
            working[selected_position],
            working[target_position],
        )
        events.append(
            event(
                EventKind.SHUFFLE_STEP,
                operation="shuffle_bounded_integer",
                rng_draw=rng_draw,
                rng_mechanism="integer_rejection_modulo",
                iteration=iteration,
                input_biome_count=len(working),
                target_position=target_position,
                bound=bound,
                selected_position=selected_position,
                attempts=attempts,
                attempt_count=len(attempts),
                rejected_attempt_count=sum(
                    attempt.accepted is False for attempt in attempts
                ),
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
    *,
    zero_candidate_policy: ZeroCandidatePolicy = ZeroCandidatePolicy.CONSUME_RAW,
    resource_state: PlanetResourceState | None = None,
    biome: Biome | None = None,
) -> ResourceFamilyResult:
    """Generate a new Common family using the selected root entry's chances."""

    _validate_zero_candidate_policy(zero_candidate_policy)
    state = resource_state or PlanetResourceState()
    root = root_entry.resource
    current_form_id = root.form_id
    events: list[DiagnosticEvent] = [
        event(
            EventKind.FAMILY_BEGIN,
            operation="begin_resource_family",
            root=root,
            draw_count_before=rng.draw_count,
        ),
    ]
    root_occurrence, root_state_events = state.record(
        root,
        ResourceProvenance.COMMON,
        biome_index=(biome.index if biome is not None else None),
        biome_form_id=(biome.form_id if biome is not None else None),
        effective_rsgd_form_id=(biome.effective_rsgd.form_id if biome is not None else None),
        rsgd_source=(biome.effective_rsgd.source if biome is not None else None),
        root_form_id=root.form_id,
    )
    events.append(
        event(
            EventKind.ROOT_EMITTED,
            operation="emit_common_root",
            root=root,
            emitted_resource=root,
            emitted=root_occurrence.occupies_state,
            occupied_new_slot=root_occurrence.occupied_new_slot,
            rng_consumed=False,
        )
    )
    events.extend(root_state_events)
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
        if state.at_capacity:
            # PROVEN descendant helper guard: full shared identity state returns
            # the current structural node without consuming RNG.
            current = _resource_from_graph(current_form_id, ires_nodes)
            events.append(
                event(
                    EventKind.RESOURCE_CAPACITY_REACHED,
                    operation="descendant_capacity_guard",
                    root=root,
                    rarity=rarity,
                    current_structural_node=current_form_id,
                    selected_candidate=current,
                    capacity=state.CAPACITY,
                    occupied_count=len(state.occupied_resource_ids),
                    rng_consumed=False,
                    draw_count_before=rng.draw_count,
                    draw_count_after=rng.draw_count,
                    evidence_status="PROVEN",
                )
            )
            levels.append(
                DescendantLevelResult(
                    rarity=rarity,
                    candidates=(),
                    inclusion_roll=None,
                    inclusion_threshold=threshold,
                    selected_candidate=current,
                    emitted=False,
                    inclusion_draw=None,
                    candidate_draw=None,
                )
            )
            continue
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
            consumed_draws = _consume_zero_candidate_rng(rng, zero_candidate_policy)
            is_production_policy = (
                zero_candidate_policy is ZeroCandidatePolicy.CONSUME_RAW
            )
            evidence_status = (
                "PROVEN"
                if is_production_policy
                else "COUNTERFACTUAL / NOT RUNTIME-PROVEN"
            )
            events.append(
                event(
                    EventKind.DESCENDANT_OMITTED,
                    operation=(
                        "consume_empty_descendant_raw"
                        if is_production_policy
                        else "counterfactual_empty_descendant_level"
                    ),
                    root=root,
                    current_structural_node=current_form_id,
                    rarity=rarity,
                    requested_rarity=rarity,
                    candidate_count=0,
                    selected_candidate=None,
                    reason="no_candidates",
                    evidence_status=evidence_status,
                    zero_candidate_policy=zero_candidate_policy,
                    inclusion_rng_consumed=any(
                        draw.operation == "float01" for draw in consumed_draws
                    ),
                    index_rng_consumed=False,
                    index_raw_equivalent_consumed=(
                        zero_candidate_policy is ZeroCandidatePolicy.CONSUME_BOTH
                    ),
                    raw_draws_consumed=len(consumed_draws),
                    raw_values_consumed=tuple(
                        draw.raw_value for draw in consumed_draws
                    ),
                    operation_types=_zero_candidate_operation_types(
                        zero_candidate_policy
                    ),
                    structural_node_changed=False,
                    structural_node_after=current_form_id,
                    draw_count_before=rng.draw_count - len(consumed_draws),
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

        # PROVEN: descendant selection follows inclusion through the runtime's
        # float32 probability-scaling path, even with one candidate. This is not
        # interchangeable with the shuffle's integer rejection/modulo helper.
        selected_index = rng.next_scaled_index(len(candidates))
        candidate_draw = _required_last_draw(rng)
        selected = candidates[selected_index]
        previous_form_id = current_form_id
        current_form_id = selected.form_id
        events.append(
            event(
                EventKind.DESCENDANT_CANDIDATE_SELECTED,
                operation="descendant_scaled_index",
                rng_draw=candidate_draw,
                rng_mechanism="float32_scaled_truncation",
                root=root,
                rarity=rarity,
                bound=len(candidates),
                probability=candidate_draw.probability_value,
                scaled=candidate_draw.scaled_value,
                selected_index=selected_index,
                selected_candidate=selected,
                previous_structural_form_id=previous_form_id,
                current_structural_form_id=current_form_id,
            )
        )
        emitted = False
        if included:
            occurrence, state_events = state.record(
                selected,
                ResourceProvenance.DESCENDANT,
                biome_index=(biome.index if biome is not None else None),
                biome_form_id=(biome.form_id if biome is not None else None),
                effective_rsgd_form_id=(
                    biome.effective_rsgd.form_id if biome is not None else None
                ),
                rsgd_source=(biome.effective_rsgd.source if biome is not None else None),
                root_form_id=root.form_id,
                descendant_rarity=rarity,
            )
            emitted = occurrence.occupies_state
            if emitted:
                emitted_descendants.append(selected)
            events.extend(state_events)
        events.append(
            event(
                EventKind.DESCENDANT_EMITTED if emitted else EventKind.DESCENDANT_OMITTED,
                operation="complete_descendant_emission",
                root=root,
                rarity=rarity,
                selected_candidate=selected,
                emitted=emitted,
                inclusion_passed=included,
                reason=(None if emitted or not included else "capacity_rejected"),
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
                emitted=emitted,
                inclusion_draw=inclusion_draw,
                candidate_draw=candidate_draw,
            )
        )

    root_resources = (root,) if root_occurrence.occupies_state else ()
    emitted_resources = _unique_resources((*root_resources, *emitted_descendants))
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
    *,
    zero_candidate_policy: ZeroCandidatePolicy = ZeroCandidatePolicy.CONSUME_RAW,
    resource_state: PlanetResourceState | None = None,
    biome: Biome | None = None,
) -> FamilyAccessResult:
    """Reuse a planet-scope family or generate and cache it on first selection."""

    draw_count_before = rng.draw_count
    cached = family_cache.get(root_entry.resource_form_id)
    if cached is not None:
        # PROVEN by the Algorab I repeated-Uranium trace: a cache hit bypasses
        # descendant generation entirely and consumes no descendant RNG words.
        cache_event = event(
            EventKind.FAMILY_CACHE_HIT,
            operation="reuse_resource_family",
            root=cached.root,
            cache_key=root_entry.resource_form_id,
            draw_count_before=draw_count_before,
            draw_count_after=rng.draw_count,
            descendant_rng_consumed=False,
            cached_emitted_family=cached.emitted_resources,
            evidence_status="PROVEN",
        )
        state_events: list[DiagnosticEvent] = []
        if resource_state is not None:
            cached_occurrence_resources = (cached.root, *cached.emitted_descendants)
            for index, resource in enumerate(cached_occurrence_resources):
                _, recorded = resource_state.record(
                    resource,
                    (ResourceProvenance.COMMON if index == 0 else ResourceProvenance.DESCENDANT),
                    biome_index=(biome.index if biome is not None else None),
                    biome_form_id=(biome.form_id if biome is not None else None),
                    effective_rsgd_form_id=(
                        biome.effective_rsgd.form_id if biome is not None else None
                    ),
                    rsgd_source=(biome.effective_rsgd.source if biome is not None else None),
                    root_form_id=cached.root.form_id,
                    descendant_rarity=(None if index == 0 else resource.rarity),
                )
                state_events.extend(recorded)
        return FamilyAccessResult(
            family=cached,
            cache_hit=True,
            draw_count_before=draw_count_before,
            draw_count_after=rng.draw_count,
            events=(cache_event, *state_events),
        )

    family = generate_family(
        root_entry,
        ires_nodes,
        rng,
        zero_candidate_policy=zero_candidate_policy,
        resource_state=resource_state,
        biome=biome,
    )
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
    *,
    zero_candidate_policy: ZeroCandidatePolicy = ZeroCandidatePolicy.CONSUME_RAW,
    atmospheric_records: Sequence[AtmosphericResourceRecord] = (),
) -> PlanetFamilyGenerationResult:
    """Compatibility wrapper for :func:`generate_planet`."""

    return generate_planet(
        planet,
        ires_nodes,
        zero_candidate_policy=zero_candidate_policy,
        atmospheric_records=atmospheric_records,
    )


def generate_planet(
    planet: Planet,
    ires_nodes: Mapping[FormId, IRESNode],
    *,
    zero_candidate_policy: ZeroCandidatePolicy = ZeroCandidatePolicy.CONSUME_RAW,
    atmospheric_records: Sequence[AtmosphericResourceRecord] = (),
) -> PlanetGenerationResult:
    """Generate the complete predicted inorganic set without oracle input."""

    _validate_zero_candidate_policy(zero_candidate_policy)
    result = _run_planet(
        planet,
        ires_nodes,
        zero_candidate_policy=zero_candidate_policy,
        atmospheric_records=atmospheric_records,
    )
    if not isinstance(result, PlanetGenerationResult):  # pragma: no cover
        raise AssertionError("family generation returned a partial result")
    return result


def _run_planet(
    planet: Planet,
    ires_nodes: Mapping[FormId, IRESNode] | None,
    *,
    zero_candidate_policy: ZeroCandidatePolicy = ZeroCandidatePolicy.CONSUME_RAW,
    atmospheric_records: Sequence[AtmosphericResourceRecord] = (),
) -> PlanetOrchestrationResult | PlanetGenerationResult:
    """Shared planet pipeline; descendants are enabled only with an IRES graph."""

    # PROVEN: one RSCS-seeded RNG state evolves through shuffle and every biome.
    rng = StarfieldRng(planet.resource_creation_seed)
    resource_state = PlanetResourceState()
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

    atmospheric_occurrences: list[ResourceOccurrence] = []
    if ires_nodes is not None:
        for record in atmospheric_records:
            if record.planet_form_id != planet.form_id:
                raise ValueError(
                    f"atmospheric record {record.planet_form_id} does not belong to {planet.form_id}"
                )
            resource = _resource_from_graph(record.resource_form_id, ires_nodes)
            occurrence, state_events = resource_state.record(
                resource,
                ResourceProvenance.ATMO,
                atmospheric_record=record,
            )
            atmospheric_occurrences.append(occurrence)
            all_events.append(
                event(
                    EventKind.ATMOSPHERIC_RESOURCE_LOADED,
                    operation="prepopulate_atmospheric_resource",
                    resource=resource,
                    atmospheric_resource_index=record.atmospheric_resource_index,
                    atmosphere_form_id=record.atmosphere_form_id,
                    inheritance_depth=record.atmosphere_inheritance_depth,
                    occupied=occurrence.occupies_state,
                    rng_consumed=False,
                    evidence_status="PROVEN",
                )
            )
            all_events.extend(state_events)

    everywhere_resources, everywhere_events = _discover_everywhere(
        initial_biomes, resource_state
    )
    all_events.extend(everywhere_events)

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

    biome_results: list[BiomeOrchestrationResult] = []
    family_biome_results: list[BiomeFamilyGenerationResult] = []
    family_cache: dict[FormId, ResourceFamilyResult] = {}
    special_resources: list[ResourceRef] = []
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

        # PROVEN STATIC/LIVE in FUN_1415DCFB0: the five-tree guard is evaluated
        # before the shared-eight guard, and both precede the category-0 selector.
        # The cache is keyed by root FormID, so cache hits do not consume another
        # tree slot. A capacity-skipped invocation must not consume selector RNG,
        # even when its prospective root already occupies a provenance-neutral slot.
        if ires_nodes is not None and len(family_cache) >= COMMON_TREE_LIMIT:
            common_entry = None
            biome_events.append(
                event(
                    EventKind.COMMON_TREE_LIMIT_REACHED,
                    operation="skip_common_selector_at_tree_limit",
                    biome_index=biome.index,
                    established_common_tree_count=len(family_cache),
                    common_tree_limit=COMMON_TREE_LIMIT,
                    draw_count_before=rng.draw_count,
                    draw_count_after=rng.draw_count,
                    rng_consumed=False,
                    evidence_status="PROVEN_STATIC_LIVE",
                )
            )
        elif ires_nodes is not None and resource_state.at_capacity:
            common_entry = None
            biome_events.append(
                event(
                    EventKind.COMMON_RESOURCE_CAPACITY_REACHED,
                    operation="skip_common_selector_at_resource_capacity",
                    biome_index=biome.index,
                    occupied_count=len(resource_state.occupied_resource_ids),
                    capacity=resource_state.CAPACITY,
                    draw_count_before=rng.draw_count,
                    draw_count_after=rng.draw_count,
                    rng_consumed=False,
                    evidence_status="PROVEN_STATIC_LIVE",
                )
            )
        else:
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
            special_occurrence, state_events = resource_state.record(
                special_entry.resource,
                ResourceProvenance.SPECIAL,
                biome_index=biome.index,
                biome_form_id=biome.form_id,
                effective_rsgd_form_id=effective_rsgd.form_id,
                rsgd_source=effective_rsgd.source,
            )
            if special_occurrence.occupies_state:
                special_resources.append(special_entry.resource)
            biome_events.append(
                event(
                    EventKind.SPECIAL_EMITTED,
                    operation="emit_special_resource",
                    biome_index=biome.index,
                    emitted_resource=special_entry.resource,
                    emitted=special_occurrence.occupies_state,
                    occupied_new_slot=special_occurrence.occupied_new_slot,
                    rng_consumed=False,
                )
            )
            biome_events.extend(state_events)
        if ires_nodes is not None and common_entry is not None:
            family_access = get_or_generate_family(
                common_entry,
                family_cache,
                ires_nodes,
                rng,
                zero_candidate_policy=zero_candidate_policy,
                resource_state=resource_state,
                biome=biome,
            )
            biome_events.extend(family_access.events)
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
        occurrences = resource_state.occurrences
        rsgd_occurrences = tuple(
            item
            for item in occurrences
            if item.provenance is not ResourceProvenance.ATMO and item.occupies_state
        )
        rsgd_resources = _resources_from_occurrences(rsgd_occurrences)
        unique_emitted = resource_state.occupied_resources
        all_events.append(
            event(
                EventKind.PLANET_GENERATION_END,
                operation="assemble_predicted_inorganic_resources",
                predicted_resources=unique_emitted,
                predicted_form_ids=frozenset(resource.form_id for resource in unique_emitted),
                final_draw_count=rng.draw_count,
            )
        )
        return PlanetGenerationResult(
            planet=planet,
            initial_biomes=initial_biomes,
            shuffled_biomes=shuffle.biomes,
            atmospheric_occurrences=tuple(atmospheric_occurrences),
            everywhere_resources=everywhere_resources,
            biome_results=tuple(family_biome_results),
            family_cache=MappingProxyType(dict(family_cache)),
            special_resources=_unique_resources(special_resources),
            family_results=tuple(family_cache.values()),
            occurrences=occurrences,
            occupied_resource_ids=resource_state.occupied_resource_ids,
            rsgd_resources=rsgd_resources,
            rsgd_form_ids=frozenset(resource.form_id for resource in rsgd_resources),
            predicted_resources=unique_emitted,
            predicted_form_ids=frozenset(
                resource.form_id for resource in unique_emitted
            ),
            events=tuple(all_events),
            final_draw_count=rng.draw_count,
            zero_candidate_policy=zero_candidate_policy,
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
    resource_state: PlanetResourceState,
) -> tuple[tuple[ResourceRef, ...], tuple[DiagnosticEvent, ...]]:
    # PROVEN LIVE in the observed Creation Kit Galaxy View Apply path:
    # FUN_141548920 scans effective-RSGD entries in authored order and emits IRES
    # category 6 without reading a DNAM chance field or consuming RNG.
    resources: list[ResourceRef] = []
    events: list[DiagnosticEvent] = [
        event(
            EventKind.EVERYWHERE_PREPASS_BEGIN,
            operation="begin_everywhere_prepass",
            biome_count=len(biomes),
            rng_consumed=False,
            evidence_status="PROVEN",
        )
    ]
    for biome in biomes:
        events.append(
            event(
                EventKind.EVERYWHERE_PREPASS_CONTEXT,
                operation="visit_everywhere_prepass_context",
                biome_index=biome.index,
                biome_form_id=biome.form_id,
                rsgd_form_id=biome.effective_rsgd.form_id,
                rsgd_editor_id=biome.effective_rsgd.editor_id,
                rng_consumed=False,
            )
        )
        for entry in biome.effective_rsgd.entries:
            if entry.resource_rarity is not GenerationRarity.EVERYWHERE:
                continue
            occurrence, state_events = resource_state.record(
                entry.resource,
                ResourceProvenance.EVERYWHERE,
                biome_index=biome.index,
                biome_form_id=biome.form_id,
                effective_rsgd_form_id=biome.effective_rsgd.form_id,
                rsgd_source=biome.effective_rsgd.source,
            )
            if occurrence.occupies_state:
                resources.append(entry.resource)
            events.append(
                event(
                    EventKind.EVERYWHERE_DISCOVERED,
                    operation="everywhere_prepass_resource",
                    biome_index=biome.index,
                    rsgd_form_id=biome.effective_rsgd.form_id,
                    resource=entry.resource,
                    evidence_status="PROVEN_LIVE",
                    occupied=occurrence.occupies_state,
                    occupied_new_slot=occurrence.occupied_new_slot,
                    rng_consumed=False,
                )
            )
            events.extend(state_events)
    unique = _unique_resources(resources)
    events.append(
        event(
            EventKind.EVERYWHERE_PREPASS_END,
            operation="end_everywhere_prepass",
            visited_biome_count=len(biomes),
            resources=unique,
            occupied_count=len(resource_state.occupied_resource_ids),
            rng_consumed=False,
        )
    )
    return unique, tuple(events)


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

    # PROVEN: the recovered category-generic selector obtains its probability value
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


def _consume_zero_candidate_rng(
    rng: StarfieldRng, policy: ZeroCandidatePolicy
) -> tuple[RngDraw, ...]:
    """Apply one diagnostic empty-level policy without fabricating index(0).

    PROVEN: Algorab I establishes exactly one raw word for an empty level while
    leaving the structural node unchanged. The trace does not establish which
    high-level RNG operation consumed it, so production uses raw extraction.
    Other modes remain COUNTERFACTUAL diagnostics.
    """

    draws: list[RngDraw] = []
    if policy in {
        ZeroCandidatePolicy.CONSUME_INCLUSION,
        ZeroCandidatePolicy.CONSUME_BOTH,
    }:
        rng.next_float01()
        draws.append(_required_last_draw(rng))
    if policy in {
        ZeroCandidatePolicy.CONSUME_RAW,
        ZeroCandidatePolicy.CONSUME_BOTH,
    }:
        # Do not fabricate a bounded choice with zero candidates. For
        # CONSUME_RAW this is the smallest exact representation of the proven
        # raw-word advancement. In the two-draw counterfactual it remains an
        # index-like raw equivalent.
        rng.next_uint32()
        draws.append(_required_last_draw(rng))
    return tuple(draws)


def _zero_candidate_operation_types(
    policy: ZeroCandidatePolicy,
) -> tuple[str, ...]:
    """Describe semantics without upgrading raw consumption into an operation."""

    if policy is ZeroCandidatePolicy.CONSUME_RAW:
        return ("raw_advance_semantics_unknown",)
    if policy is ZeroCandidatePolicy.CONSUME_NONE:
        return ()
    if policy is ZeroCandidatePolicy.CONSUME_INCLUSION:
        return ("inclusion",)
    return ("inclusion", "index_raw_equivalent")


def _validate_zero_candidate_policy(policy: ZeroCandidatePolicy) -> None:
    """Reject strings so diagnostic modes cannot be enabled accidentally."""

    if not isinstance(policy, ZeroCandidatePolicy):
        raise TypeError("zero_candidate_policy must be a ZeroCandidatePolicy")


def _unique_resources(resources: Sequence[ResourceRef]) -> tuple[ResourceRef, ...]:
    """Preserve generation order while enforcing FormID identity once."""

    result: list[ResourceRef] = []
    seen: set[FormId] = set()
    for resource in resources:
        if resource.form_id not in seen:
            seen.add(resource.form_id)
            result.append(resource)
    return tuple(result)


def _resources_from_occurrences(
    occurrences: Sequence[ResourceOccurrence],
) -> tuple[ResourceRef, ...]:
    """Return accepted unique identities while retaining occurrence data elsewhere."""

    return _unique_resources(
        tuple(item.resource for item in occurrences if item.occupies_state)
    )


def _resource_from_graph(
    form_id: FormId, ires_nodes: Mapping[FormId, IRESNode]
) -> ResourceRef:
    try:
        node = ires_nodes[form_id]
    except KeyError as error:
        raise ValueError(f"IRES graph has no node for resource {form_id}") from error
    return ResourceRef(node.form_id, node.editor_id, node.name, node.rarity)


def _required_last_draw(rng: StarfieldRng) -> RngDraw:
    draw = rng.last_draw
    if draw is None:  # Defensive invariant: only called immediately after a draw.
        raise RuntimeError("expected an RNG draw to have been recorded")
    return draw
