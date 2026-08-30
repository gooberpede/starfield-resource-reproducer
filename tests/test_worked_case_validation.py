import pytest

from starfield_resource_reproducer.diagnostics import (
    EventKind,
    format_diagnostic_timeline,
)
from starfield_resource_reproducer.domain import FormId, GenerationRarity
from starfield_resource_reproducer.generation import generate_planet
from starfield_resource_reproducer.validation import compare_to_oracle


WORKED_CASES = {
    "0005DECC": ({"Water", "Nickel"}, 10, True),
    "0005DEC0": ({"Water", "Nickel", "Palladium"}, 10, True),
    "0005DF7F": ({"Helium-3", "Uranium", "Iridium", "Vytinium"}, 10, True),
    "0003F59F": (
        {"Water", "Lead", "Silver", "Argon", "Neon", "Iron", "Alkanes"},
        30,
        True,
    ),
}


@pytest.mark.parametrize(
    ("planet_id", "expected_names", "draw_count", "exact"),
    [(planet_id, *expectation) for planet_id, expectation in WORKED_CASES.items()],
)
def test_complete_worked_case_prediction_and_validation(
    generation_data,
    ires_nodes,
    canonical_oracle,
    planet_id,
    expected_names,
    draw_count,
    exact,
) -> None:
    form_id = FormId(planet_id)
    generation = generate_planet(generation_data[form_id], ires_nodes)
    validation = compare_to_oracle(generation, canonical_oracle[form_id])

    assert {resource.name for resource in generation.predicted_resources} == expected_names
    assert generation.final_draw_count == draw_count
    assert validation.exact_match is exact
    assert validation.predicted_form_ids == generation.predicted_form_ids
    assert validation.expected_form_ids == canonical_oracle[form_id].inorganic_resources
    if exact:
        assert validation.missing_form_ids == frozenset()
        assert validation.unexpected_form_ids == frozenset()


def test_oberon_everywhere_is_explicit_and_separate(generation_data, ires_nodes) -> None:
    generation = generate_planet(generation_data[FormId("0005DECC")], ires_nodes)

    assert [resource.name for resource in generation.everywhere_resources] == ["Water"]
    assert [resource.name for resource in generation.special_resources] == []
    assert generation.family_results[0].root.name == "Nickel"
    everywhere = [event for event in generation.events if event.kind is EventKind.EVERYWHERE_DISCOVERED]
    assert everywhere[0]["evidence_status"] == "PROVISIONAL"


def test_kreet_trace_zero_candidate_consumption_and_exact_match(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    kreet_id = FormId("0003F59F")
    generation = generate_planet(generation_data[kreet_id], ires_nodes)
    validation = compare_to_oracle(generation, canonical_oracle[kreet_id])

    assert [biome.index for biome in generation.initial_biomes] == [0, 1, 2]
    assert [biome.index for biome in generation.shuffled_biomes] == [2, 0, 1]
    assert [result.orchestration.common_root.name for result in generation.biome_results] == [
        "Lead",
        "Argon",
        "Iron",
    ]
    neon_id = next(
        resource.resource_form_id
        for resource in canonical_oracle[kreet_id].inorganic_resource_records
        if resource.resource_name == "Neon"
    )
    assert validation.missing_form_ids == frozenset()
    assert validation.unexpected_form_ids == frozenset()
    assert validation.exact_match is True
    assert neon_id in generation.predicted_form_ids
    assert validation.suspected_cause is None
    assert validation.first_plausible_divergence is None

    zero_events = [
        event
        for event in generation.events
        if event.kind is EventKind.DESCENDANT_OMITTED
        and event.get("reason") == "no_candidates"
    ]
    assert [event["requested_rarity"] for event in zero_events[:2]] == [
        GenerationRarity.EXOTIC,
        GenerationRarity.UNIQUE,
    ]
    assert all(event["root"].name == "Lead" for event in zero_events[:2])
    assert all(event["candidate_count"] == 0 for event in zero_events[:2])
    assert [(event["draw_count_before"], event["draw_count_after"]) for event in zero_events[:2]] == [
        (8, 9),
        (9, 10),
    ]
    assert all(event["inclusion_rng_consumed"] is False for event in zero_events[:2])
    assert all(event["index_rng_consumed"] is False for event in zero_events[:2])
    assert all(event["raw_draws_consumed"] == 1 for event in zero_events[:2])
    assert all(event["evidence_status"] == "PROVEN" for event in zero_events[:2])
    assert all(
        event["current_structural_node"] == event["structural_node_after"]
        for event in zero_events[:2]
    )

    argon = next(family for family in generation.family_results if family.root.name == "Argon")
    neon_level = next(level for level in argon.levels if level.rarity is GenerationRarity.EXOTIC)
    assert neon_level.selected_candidate.name == "Neon"
    assert neon_level.inclusion_draw.draw_number == 17
    assert neon_level.inclusion_draw.raw_value == 357224398
    assert neon_level.inclusion_roll == pytest.approx(0.08317194879055023)
    assert neon_level.inclusion_threshold == 0.15
    assert neon_level.emitted is True

    timeline = format_diagnostic_timeline(
        generation.planet.name, generation.planet.resource_creation_seed, generation.events
    )
    assert timeline.startswith("Planet Kreet\nSeed 2842708811")
    assert "resulting_order=(2, 0, 1)" in timeline
    assert "rsgd_editor_id=VolcanicDefaultRes_Kreet" in timeline
    assert "selected_resource=Lead[000057C1]" in timeline
    assert "draw 17 DESCENDANT_INCLUSION_ROLL raw=357224398" in timeline
    assert "candidate_count=0" in timeline


def test_validation_rejects_mismatched_planet_identity(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    generation = generate_planet(generation_data[FormId("0005DEC0")], ires_nodes)

    with pytest.raises(ValueError, match="different planets"):
        compare_to_oracle(generation, canonical_oracle[FormId("0005DECC")])
