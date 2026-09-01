"""Focused controls for Special state mutation before Common guards.

Purpose: prove that a selected Special occurrence updates shared identity state
before Common guard evaluation and that biome reporting associates occurrences by
PNDT biome index. Selection algorithms and fallback behavior remain covered by
their dedicated suites. The sequencing asserted here is PROVEN LIVE.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from starfield_resource_reproducer.diagnostics import EventKind
from starfield_resource_reproducer.domain import (
    FormId,
    GenerationRarity,
    IRESNode,
    ResourceProvenance,
)
from starfield_resource_reproducer.generation import PlanetResourceState, generate_planet


def _synthetic_special_planet(generation_data, *, duplicate_special: bool):
    planet = generation_data[FormId("0005DEC0")]
    biome = planet.biomes[0]
    template = next(
        entry
        for entry in biome.effective_rsgd.entries
        if entry.resource_rarity is GenerationRarity.COMMON
    )
    everywhere_entries = tuple(
        replace(
            template,
            index=index,
            resource_form_id=FormId(f"FD00{index:04X}"),
            resource_editor_id=f"SyntheticEverywhere{index}",
            resource_name=f"Synthetic Everywhere {index}",
            resource_rarity=GenerationRarity.EVERYWHERE,
            common_chance=Decimal("0"),
            everywhere_chance=Decimal("100"),
        )
        for index in range(7)
    )
    special_id = everywhere_entries[0].resource_form_id if duplicate_special else FormId(
        "FD000100"
    )
    special = replace(
        template,
        index=7,
        resource_form_id=special_id,
        resource_editor_id="SyntheticSpecial",
        resource_name="Synthetic Special",
        resource_rarity=GenerationRarity.SPECIAL,
        common_chance=Decimal("0"),
        special_chance=Decimal("100"),
    )
    common = replace(
        template,
        index=8,
        resource_form_id=FormId("FD000200"),
        resource_editor_id="SyntheticCommon",
        resource_name="Synthetic Common",
        common_chance=Decimal("100"),
    )
    rsgd = replace(
        biome.effective_rsgd,
        form_id=FormId("FD010000"),
        editor_id="SyntheticSpecialGuardRSGD",
        entries=(*everywhere_entries, special, common),
    )
    changed_biome = replace(biome, pndt_rsgd=rsgd, biom_rsgd=None)
    changed_planet = replace(planet, biomes=(changed_biome,))
    graph = {
        common.resource_form_id: IRESNode(
            common.resource_form_id,
            common.resource_editor_id,
            common.resource_name,
            GenerationRarity.COMMON,
            (),
        )
    }
    return changed_planet, graph, special_id, common.resource_form_id


def _event_indices(result, kind):
    return [index for index, item in enumerate(result.events) if item.kind is kind]


def test_new_special_fills_slot_eight_before_shared_common_guard(
    generation_data,
) -> None:
    planet, graph, special_id, _ = _synthetic_special_planet(
        generation_data, duplicate_special=False
    )

    result = generate_planet(planet, graph)

    assert len(result.occupied_resource_ids) == PlanetResourceState.CAPACITY
    assert len(result.special_occurrences) == 1
    special = result.special_occurrences[0]
    assert special.resource.form_id == special_id
    assert special.occupied_new_slot is True
    guards = [
        item
        for item in result.events
        if item.kind is EventKind.COMMON_RESOURCE_CAPACITY_REACHED
    ]
    assert len(guards) == 1
    assert guards[0]["occupied_count"] == PlanetResourceState.CAPACITY
    assert not _event_indices(result, EventKind.COMMON_PASS_BEGIN)
    assert not _event_indices(result, EventKind.COMMON_ROLL)
    assert _event_indices(result, EventKind.COMMON_GUARD_FALLBACK_BEGIN)
    assert result.final_draw_count == 1

    emitted_index = _event_indices(result, EventKind.SPECIAL_EMITTED)[0]
    occurrence_index = next(
        index
        for index, item in enumerate(result.events)
        if item.kind is EventKind.RESOURCE_OCCURRENCE_RECORDED
        and item.get("provenance") is ResourceProvenance.SPECIAL
    )
    slot_index = next(
        index
        for index, item in enumerate(result.events)
        if item.kind is EventKind.RESOURCE_SLOT_OCCUPIED
        and item.get("provenance") is ResourceProvenance.SPECIAL
    )
    guard_index = _event_indices(result, EventKind.COMMON_RESOURCE_CAPACITY_REACHED)[0]
    assert emitted_index < occurrence_index < slot_index < guard_index


def test_duplicate_special_keeps_count_seven_and_allows_normal_common(
    generation_data,
) -> None:
    planet, graph, special_id, common_id = _synthetic_special_planet(
        generation_data, duplicate_special=True
    )

    result = generate_planet(planet, graph)

    assert len(result.special_occurrences) == 1
    special = result.special_occurrences[0]
    assert special.resource.form_id == special_id
    assert special.occupied_new_slot is False
    assert not _event_indices(result, EventKind.COMMON_RESOURCE_CAPACITY_REACHED)
    assert len(_event_indices(result, EventKind.COMMON_ROLL)) == 1
    assert result.biome_results[0].orchestration.common_root.form_id == common_id
    assert result.final_draw_count == 2

    already_index = next(
        index
        for index, item in enumerate(result.events)
        if item.kind is EventKind.RESOURCE_SLOT_ALREADY_OCCUPIED
        and item.get("provenance") is ResourceProvenance.SPECIAL
    )
    common_index = _event_indices(result, EventKind.COMMON_PASS_BEGIN)[0]
    assert already_index < common_index


def test_biome_resource_views_use_index_when_form_id_is_reused(generation_data) -> None:
    planet = generation_data[FormId("0005DEC0")]
    template_biome = planet.biomes[0]
    template_entry = template_biome.effective_rsgd.entries[0]
    shared_biome_id = FormId("FD020000")
    expected: dict[int, FormId] = {}
    biomes = []
    for index in range(2):
        resource_id = FormId(f"FD03{index:04X}")
        expected[index] = resource_id
        entry = replace(
            template_entry,
            index=0,
            resource_form_id=resource_id,
            resource_editor_id=f"IndexEverywhere{index}",
            resource_name=f"Index Everywhere {index}",
            resource_rarity=GenerationRarity.EVERYWHERE,
        )
        rsgd = replace(
            template_biome.effective_rsgd,
            form_id=FormId(f"FD04{index:04X}"),
            entries=(entry,),
        )
        biomes.append(
            replace(
                template_biome,
                index=index,
                form_id=shared_biome_id,
                name=f"Shared FormID Biome {index}",
                pndt_rsgd=rsgd,
                biom_rsgd=None,
            )
        )

    result = generate_planet(replace(planet, biomes=tuple(biomes)), {})
    by_index = {view.biome.index: view for view in result.biome_resource_views()}

    assert {
        index: tuple(resource.form_id for resource in view.resources)
        for index, view in by_index.items()
    } == {index: (resource_id,) for index, resource_id in expected.items()}
