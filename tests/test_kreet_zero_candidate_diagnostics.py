import pytest

from starfield_resource_reproducer.diagnostics import EventKind, format_diagnostic_timeline
from starfield_resource_reproducer.domain import FormId, GenerationRarity
from starfield_resource_reproducer.generation import (
    ZeroCandidatePolicy,
    generate_planet,
)


EXPECTED = {
    ZeroCandidatePolicy.CONSUME_NONE: (
        8,
        15,
        1553730631,
        0.3617524802684784,
        False,
        {"Water", "Lead", "Silver", "Argon", "Iron", "Alkanes"},
    ),
    ZeroCandidatePolicy.CONSUME_INCLUSION: (
        10,
        17,
        357224398,
        0.08317194879055023,
        True,
        {"Water", "Lead", "Silver", "Argon", "Neon", "Iron", "Alkanes"},
    ),
    ZeroCandidatePolicy.CONSUME_INDEX_RAW: (
        10,
        17,
        357224398,
        0.08317194879055023,
        True,
        {"Water", "Lead", "Silver", "Argon", "Neon", "Iron", "Alkanes"},
    ),
    ZeroCandidatePolicy.CONSUME_BOTH: (
        12,
        19,
        972349161,
        0.22639042139053345,
        False,
        {
            "Water",
            "Lead",
            "Silver",
            "Argon",
            "Benzene",
            "Carboxylic Acids",
            "Iron",
            "Alkanes",
        },
    ),
}


@pytest.mark.parametrize("policy", list(ZeroCandidatePolicy))
def test_kreet_zero_candidate_counterfactual_matrix(
    generation_data, ires_nodes, policy
) -> None:
    kreet = generation_data[FormId("0003F59F")]
    result = generate_planet(kreet, ires_nodes, zero_candidate_policy=policy)
    lead = next(family for family in result.family_results if family.root.name == "Lead")
    argon = next(family for family in result.family_results if family.root.name == "Argon")
    neon = next(
        level for level in argon.levels if level.rarity is GenerationRarity.EXOTIC
    )
    zero_events = tuple(
        item
        for item in lead.events
        if item.kind is EventKind.DESCENDANT_OMITTED
        and item.get("reason") == "no_candidates"
    )
    expected = EXPECTED[policy]

    assert zero_events[-1]["draw_count_after"] == expected[0]
    assert neon.selected_candidate.name == "Neon"
    assert neon.inclusion_draw.draw_number == expected[1]
    assert neon.inclusion_draw.raw_value == expected[2]
    assert neon.inclusion_roll == pytest.approx(expected[3])
    assert neon.emitted is expected[4]
    assert {resource.name for resource in result.predicted_resources} == expected[5]
    assert result.zero_candidate_policy is policy

    timeline = format_diagnostic_timeline(kreet.name, kreet.resource_creation_seed, result.events)
    assert f"zero_candidate_policy={policy.value}" in timeline
    assert "raw_values_consumed=" in timeline


def test_production_default_remains_no_draw(generation_data, ires_nodes) -> None:
    kreet = generation_data[FormId("0003F59F")]

    default = generate_planet(kreet, ires_nodes)
    explicit = generate_planet(
        kreet,
        ires_nodes,
        zero_candidate_policy=ZeroCandidatePolicy.CONSUME_NONE,
    )

    assert default.zero_candidate_policy is ZeroCandidatePolicy.CONSUME_NONE
    assert default.predicted_form_ids == explicit.predicted_form_ids
    assert default.final_draw_count == explicit.final_draw_count == 28

