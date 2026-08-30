"""Partial Starfield planetary generation orchestration.

Purpose:
    Reproduce the control flow from PNDT biome order through Common-root choice.
Responsibilities:
    Run the recovered biome shuffle, model provisional Everywhere discovery,
    resolve effective RSGDs, and perform ordered Special/Common selectors using
    one evolving ``StarfieldRng`` while emitting structured diagnostics.
Boundaries:
    CSV loading, oracle validation, descendant traversal, resource emission, and
    family caching are intentionally excluded; Brief 04 owns those later stages.
Evidence notes:
    Kreet proves the observed shuffle and processing order. The broader loop and
    empty-Special behavior are evidence-qualified below and remain easy to replace.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from .diagnostics import (
    DiagnosticEvent,
    EventKind,
    WeightedCandidateDiagnostic,
    event,
)
from .domain import (
    Biome,
    GenerationRarity,
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


def orchestrate_planet(planet: Planet) -> PlanetOrchestrationResult:
    """Run one planet through shuffle, Everywhere, Special, and Common stages."""

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
        biome_results.append(
            BiomeOrchestrationResult(
                biome=biome,
                effective_rsgd=effective_rsgd,
                rsgd_resolution_source=resolution_source,
                special_selection=(special_entry.resource if special_entry else None),
                common_root=(common_entry.resource if common_entry else None),
                events=tuple(biome_events),
            )
        )

    all_events.append(
        event(
            EventKind.PLANET_ORCHESTRATION_END,
            operation="end_planet_orchestration",
            biome_count=len(biome_results),
            final_draw_count=rng.draw_count,
            descendants_implemented=False,
        )
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


def _required_last_draw(rng: StarfieldRng) -> RngDraw:
    draw = rng.last_draw
    if draw is None:  # Defensive invariant: only called immediately after a draw.
        raise RuntimeError("expected an RNG draw to have been recorded")
    return draw
