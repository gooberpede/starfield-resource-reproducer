from dataclasses import replace

import pytest

from starfield_resource_reproducer.diagnostics import EventKind
from starfield_resource_reproducer.domain import FormId, GenerationRarity, IRESNode
from starfield_resource_reproducer.generation import (
    generate_family,
    generate_planet_families,
    get_or_generate_family,
)
from starfield_resource_reproducer.prng import StarfieldRng


TRACE_ABS_TOLERANCE = 0.0000000005


def _root_entry(planet, name: str):
    return next(
        entry
        for biome in planet.biomes
        for entry in biome.effective_rsgd.entries
        if entry.resource_name == name
    )


def test_mimas_family_path_emission_and_draw_interleaving(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    result = generate_planet_families(
        generation_data[FormId("0005DEC0")], ires_nodes
    )
    access = result.biome_results[0].family_access
    assert access is not None
    family = access.family

    assert [
        family.root.name,
        *[level.selected_candidate.name for level in family.levels],
    ] == [
        "Nickel",
        "Cobalt",
        "Platinum",
        "Palladium",
        "Tasine",
    ]
    assert [resource.name for resource in family.emitted_resources] == [
        "Nickel",
        "Palladium",
    ]
    assert [resource.name for resource in result.emitted_resources] == [
        "Water",
        "Nickel",
        "Palladium",
    ]
    assert [level.emitted for level in family.levels] == [False, False, True, False]
    assert [level.inclusion_draw.draw_number for level in family.levels] == [
        3,
        5,
        7,
        9,
    ]
    assert [level.candidate_draw.draw_number for level in family.levels] == [
        4,
        6,
        8,
        10,
    ]
    assert family.levels[-1].inclusion_roll == pytest.approx(
        0.818136036, abs=TRACE_ABS_TOLERANCE
    )
    rng_events = [event for event in family.events if event.rng_draw is not None]
    assert [event.kind for event in rng_events] == [
        EventKind.DESCENDANT_INCLUSION_ROLL,
        EventKind.DESCENDANT_CANDIDATE_SELECTED,
    ] * 4
    assert [event.rng_draw.draw_number for event in rng_events] == list(range(3, 11))
    selection_events = rng_events[1::2]
    assert all(
        event.operation == "descendant_scaled_index" for event in selection_events
    )
    assert all(
        event["rng_mechanism"] == "float32_scaled_truncation"
        for event in selection_events
    )
    assert all(event["bound"] == 1 for event in selection_events)
    assert all(event.rng_draw.scaled_value is not None for event in selection_events)
    assert result.emitted_form_ids == canonical_oracle[
        FormId("0005DEC0")
    ].inorganic_resources
    assert result.final_draw_count == 10


def test_decaran_uranium_reaches_vytinium_without_special_case(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    result = generate_planet_families(
        generation_data[FormId("0005DF7F")], ires_nodes
    )
    biome = result.biome_results[0]
    access = biome.family_access
    assert access is not None

    assert biome.orchestration.special_selection.name == "Helium-3"
    assert [
        access.family.root.name,
        *[level.selected_candidate.name for level in access.family.levels],
    ] == ["Uranium", "Iridium", "Vanadium", "Plutonium", "Vytinium"]
    assert [resource.name for resource in access.family.emitted_resources] == [
        "Uranium",
        "Iridium",
        "Vytinium",
    ]
    assert [resource.name for resource in result.emitted_resources] == [
        "Helium-3",
        "Uranium",
        "Iridium",
        "Vytinium",
    ]
    assert result.emitted_form_ids == canonical_oracle[
        FormId("0005DF7F")
    ].inorganic_resources


def test_oberon_emits_root_unconditionally_and_no_descendants(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    result = generate_planet_families(
        generation_data[FormId("0005DECC")], ires_nodes
    )
    access = result.biome_results[0].family_access
    assert access is not None

    assert access.family.root.name == "Nickel"
    assert access.family.emitted_descendants == ()
    assert [resource.name for resource in result.emitted_resources] == [
        "Water",
        "Nickel",
    ]
    assert result.emitted_form_ids == canonical_oracle[
        FormId("0005DECC")
    ].inorganic_resources


def test_family_cache_reuses_form_id_without_descendant_draws(
    generation_data, ires_nodes
) -> None:
    mimas = generation_data[FormId("0005DEC0")]
    root_entry = _root_entry(mimas, "Nickel")
    rng = StarfieldRng(mimas.resource_creation_seed)
    rng.next_float01()  # Empty Special pass.
    rng.next_float01()  # Common/root selection.
    cache = {}

    generated = get_or_generate_family(root_entry, cache, ires_nodes, rng)
    after_generation = rng.draw_count
    reused = get_or_generate_family(root_entry, cache, ires_nodes, rng)

    assert generated.cache_hit is False
    assert after_generation == 10
    assert reused.cache_hit is True
    assert reused.family is generated.family
    assert rng.draw_count == after_generation
    assert list(cache) == [root_entry.resource_form_id]
    assert reused.events[0].kind is EventKind.FAMILY_CACHE_HIT
    assert reused.events[0]["descendant_rng_consumed"] is False
    assert reused.events[0]["evidence_status"] == "PROVEN"
    assert reused.events[0]["draw_count_before"] == after_generation
    assert reused.events[0]["draw_count_after"] == after_generation
    assert reused.events[0]["cached_emitted_family"] == generated.family.emitted_resources


def test_zero_candidate_levels_consume_one_raw_word_and_preserve_structure(
    generation_data,
) -> None:
    mimas = generation_data[FormId("0005DEC0")]
    synthetic_id = FormId("FE000001")
    root_entry = replace(
        _root_entry(mimas, "Nickel"),
        resource_form_id=synthetic_id,
        resource_editor_id="SyntheticRoot",
        resource_name="Synthetic Root",
        resource_rarity=GenerationRarity.COMMON,
    )
    graph = {
        synthetic_id: IRESNode(
            synthetic_id,
            "SyntheticRoot",
            "Synthetic Root",
            GenerationRarity.COMMON,
            (),
        )
    }
    rng = StarfieldRng(1)

    family = generate_family(root_entry, graph, rng)

    assert rng.draw_count == 4
    assert all(level.candidates == () for level in family.levels)
    assert all(level.selected_candidate is None for level in family.levels)
    omitted = [
        event
        for event in family.events
        if event.kind is EventKind.DESCENDANT_OMITTED
    ]
    assert len(omitted) == 4
    assert all(event["evidence_status"] == "PROVEN" for event in omitted)
    assert all(event["raw_draws_consumed"] == 1 for event in omitted)
    assert all(
        event["operation_types"] == ("raw_advance_semantics_unknown",)
        for event in omitted
    )
    assert all(event["structural_node_changed"] is False for event in omitted)
