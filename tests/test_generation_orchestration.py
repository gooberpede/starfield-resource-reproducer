import pytest

from starfield_resource_reproducer.diagnostics import EventKind
from starfield_resource_reproducer.domain import FormId, RSGDSource
from starfield_resource_reproducer.generation import orchestrate_planet


def _events(result, kind: EventKind):
    return [event for event in result.events if event.kind is kind]


def test_mimas_empty_special_pass_accounts_for_pre_common_draw(
    generation_data,
) -> None:
    result = orchestrate_planet(generation_data[FormId("0005DEC0")])
    biome_result = result.biome_results[0]

    assert result.shuffled_biomes == result.initial_biomes
    shuffled = _events(result, EventKind.BIOME_LIST_SHUFFLED)[0]
    assert shuffled["raw_draws_consumed"] == 0
    special = _events(result, EventKind.SPECIAL_PASS_RESULT)[0]
    assert special["eligible_count"] == 0
    assert special["rng_consumed"] is True
    assert special.rng_draw.draw_number == 1
    assert special["selected_resource"] is None

    common = _events(result, EventKind.COMMON_ROLL)[0]
    assert common.rng_draw.draw_number == 2
    assert common.rng_draw.raw_value == 2409964464
    assert common["roll"] == pytest.approx(0.561107993, abs=0.0000000005)
    assert [candidate.resource_name for candidate in common["candidates"]] == [
        "Nickel",
        "Lead",
    ]
    assert [candidate.cumulative_threshold for candidate in common["candidates"]] == [
        0.6,
        1.0,
    ]
    assert biome_result.common_root.name == "Nickel"
    assert result.final_draw_count == 2


def test_kreet_orchestration_uses_shuffled_order_and_shared_rng(
    generation_data,
) -> None:
    result = orchestrate_planet(generation_data[FormId("0003F59F")])

    assert [biome.index for biome in result.initial_biomes] == [0, 1, 2]
    assert [biome.index for biome in result.shuffled_biomes] == [2, 0, 1]
    assert [biome.biome.name for biome in result.biome_results] == [
        "Volcanic",
        "Frozen Volcanic",
        "Mountains",
    ]
    assert [biome.effective_rsgd.editor_id for biome in result.biome_results] == [
        "VolcanicDefaultRes_Kreet",
        "FrozenBarrenDefaultRes",
        "MountainDefaultRes_Kreet",
    ]
    assert [biome.rsgd_resolution_source for biome in result.biome_results] == [
        RSGDSource.PNDT,
        RSGDSource.BIOM,
        RSGDSource.PNDT,
    ]
    assert [biome.common_root.name for biome in result.biome_results] == [
        "Lead",
        "Argon",
        "Iron",
    ]
    assert [
        event.rng_draw.draw_number
        for event in _events(result, EventKind.SHUFFLE_STEP)
    ] == [1, 2]
    assert [
        event.rng_draw.draw_number
        for event in _events(result, EventKind.SPECIAL_PASS_RESULT)
    ] == [3, 5, 7]
    assert [
        event.rng_draw.draw_number
        for event in _events(result, EventKind.COMMON_ROLL)
    ] == [4, 6, 8]
    assert result.final_draw_count == 8


def test_decaran_selects_special_then_common_from_pndt_override(
    generation_data,
) -> None:
    result = orchestrate_planet(generation_data[FormId("0005DF7F")])
    biome = result.biome_results[0]

    assert biome.effective_rsgd.editor_id == "UniqueCrateredBarrenVytiniumRes"
    assert biome.rsgd_resolution_source is RSGDSource.PNDT
    assert biome.special_selection.name == "Helium-3"
    assert biome.common_root.name == "Uranium"
    assert _events(result, EventKind.SPECIAL_PASS_RESULT)[0].rng_draw.draw_number == 1
    assert _events(result, EventKind.COMMON_ROLL)[0].rng_draw.draw_number == 2
    assert result.final_draw_count == 2


def test_oberon_discovers_water_upstream_and_selects_nickel(
    generation_data,
) -> None:
    result = orchestrate_planet(generation_data[FormId("0005DECC")])

    assert [resource.name for resource in result.everywhere_resources] == ["Water"]
    everywhere = _events(result, EventKind.EVERYWHERE_DISCOVERED)
    assert len(everywhere) == 1
    assert everywhere[0]["evidence_status"] == "PROVEN_STRUCTURE_OPEN_HELPER_SELECTION"
    assert everywhere[0]["rng_consumed"] is False
    assert result.biome_results[0].special_selection is None
    assert result.biome_results[0].common_root.name == "Nickel"


def test_partial_result_explicitly_stops_before_descendants(generation_data) -> None:
    result = orchestrate_planet(generation_data[FormId("0005DEC0")])
    end = _events(result, EventKind.PLANET_ORCHESTRATION_END)[0]

    assert end["descendants_implemented"] is False
    assert not hasattr(result, "predicted_resources")
    assert not hasattr(result, "family_cache")
