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


def test_algorab_current_model_documents_unresolved_lead_trace_mismatch(
    generation_data, ires_nodes
) -> None:
    """Keep modeled behavior distinct from the independently observed trace."""

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
        ("Titanium",),
        ("Dysprosium",),
        (),
    ]
    assert [
        level.selected_candidate.name if level.selected_candidate else None
        for level in lead.levels
    ] == ["Tungsten", "Titanium", "Dysprosium", None]

    # LIVE: Algorab advanced structurally only at L1/L2, and its two empty
    # calls consumed d21/d22. MODEL: the unresolved Tungsten branch also
    # advances at L3 and does not reach its sole empty call until d23.
    live_structural_advancement = (True, True, False, False)
    model_structural_advancement = tuple(
        level.selected_candidate is not None for level in lead.levels
    )
    assert model_structural_advancement == (True, True, True, False)
    assert model_structural_advancement != live_structural_advancement

    model_empty_events = tuple(
        item
        for item in lead.events
        if item.kind is EventKind.DESCENDANT_OMITTED
        and item.get("reason") == "no_candidates"
    )
    assert len(model_empty_events) == 1
    empty = model_empty_events[0]
    assert empty["requested_rarity"] is GenerationRarity.UNIQUE
    assert empty["draw_count_before"] == 22
    assert empty["draw_count_after"] == 23
    assert empty["raw_values_consumed"] == (1749088046,)
    assert empty["structural_node_changed"] is False
    live_empty_draws = ((21, 3583630102), (22, 832141661))
    model_empty_draws = tuple(
        (item["draw_count_after"], item["raw_values_consumed"][0])
        for item in model_empty_events
    )
    assert model_empty_draws == ((23, 1749088046),)
    assert model_empty_draws != live_empty_draws
    live_final_draw_count = 22
    assert result.final_draw_count == 23
    assert result.final_draw_count != live_final_draw_count
