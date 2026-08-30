from starfield_resource_reproducer.diagnostics import EventKind
from starfield_resource_reproducer.domain import FormId, GenerationRarity
from starfield_resource_reproducer.generation import generate_planet
from starfield_resource_reproducer.validation import compare_to_oracle


def test_algorab_proven_cache_behavior_and_canonical_final_set(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    algorab_id = FormId("0003F599")
    result = generate_planet(generation_data[algorab_id], ires_nodes)
    validation = compare_to_oracle(result, canonical_oracle[algorab_id])

    assert [biome.index for biome in result.shuffled_biomes] == [2, 1, 0]
    assert validation.exact_match is True
    assert {resource.name for resource in result.predicted_resources} == {
        "Uranium",
        "Iridium",
        "Lead",
    }

    sandy, rocky, _volcanic = result.biome_results
    assert sandy.orchestration.biome.editor_id == "DesertSandyNoLife05"
    assert sandy.orchestration.common_root.name == "Uranium"
    assert sandy.family_access is not None
    assert sandy.family_access.cache_hit is False

    assert rocky.orchestration.biome.editor_id == "DesertRockyNoLife07"
    assert rocky.orchestration.common_root.name == "Uranium"
    assert rocky.family_access is not None
    assert rocky.family_access.cache_hit is True
    assert rocky.family_access.draw_count_before == 14
    assert rocky.family_access.draw_count_after == 14
    cache_event = rocky.family_access.events[0]
    assert cache_event.kind is EventKind.FAMILY_CACHE_HIT
    assert cache_event["descendant_rng_consumed"] is False
    assert cache_event["evidence_status"] == "PROVEN"


def test_algorab_scaled_descendant_path_matches_live_lead_trace(
    generation_data, ires_nodes
) -> None:
    """Lock the live Silver branch independently from final-set exactness."""

    result = generate_planet(generation_data[FormId("0003F599")], ires_nodes)
    volcanic = result.biome_results[2]

    assert volcanic.orchestration.common_root.name == "Lead"
    assert volcanic.family_access is not None
    lead = volcanic.family_access.family
    assert [
        tuple(resource.name for resource in level.candidates)
        for level in lead.levels
    ] == [
        ("Silver", "Tungsten"),
        ("Mercury",),
        (),
        (),
    ]
    # Descendant levels remain rarity-ordered; Mercury is the Rare (L2) node.
    assert [level.rarity for level in lead.levels] == [
        GenerationRarity.UNCOMMON,
        GenerationRarity.RARE,
        GenerationRarity.EXOTIC,
        GenerationRarity.UNIQUE,
    ]
    assert tuple(resource.name for resource in lead.levels[1].candidates) == (
        "Mercury",
    )
    assert [
        level.selected_candidate.name if level.selected_candidate else None
        for level in lead.levels
    ] == ["Silver", "Mercury", None, None]

    structural_advancement = tuple(
        level.selected_candidate is not None for level in lead.levels
    )
    assert structural_advancement == (True, True, False, False)

    l1_draw = lead.levels[0].candidate_draw
    assert l1_draw is not None
    assert l1_draw.draw_number == 18
    assert l1_draw.raw_value == 1826241303
    assert l1_draw.upper_bound == 2
    assert l1_draw.probability_value == 0.4252006709575653
    assert l1_draw.scaled_value == 0.8504013419151306
    assert l1_draw.converted_value == 0

    model_empty_events = tuple(
        item
        for item in lead.events
        if item.kind is EventKind.DESCENDANT_OMITTED
        and item.get("reason") == "no_candidates"
    )
    assert [item["requested_rarity"] for item in model_empty_events] == [
        GenerationRarity.EXOTIC,
        GenerationRarity.UNIQUE,
    ]
    assert all(item["structural_node_changed"] is False for item in model_empty_events)
    empty_draws = tuple(
        (item["draw_count_after"], item["raw_values_consumed"][0])
        for item in model_empty_events
    )
    assert empty_draws == ((21, 3583630102), (22, 832141661))
    assert result.final_draw_count == 22
