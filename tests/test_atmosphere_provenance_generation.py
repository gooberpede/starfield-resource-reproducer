from starfield_resource_reproducer.diagnostics import EventKind
from starfield_resource_reproducer.domain import FormId, ResourceProvenance, ResourceRef
from starfield_resource_reproducer.generation import (
    PlanetResourceState,
    generate_family,
    generate_planet,
)
from starfield_resource_reproducer.prng import StarfieldRng


CALLISTO = FormId("0005DEBE")
MAAL_VIII = FormId("0005DE6F")
CHLORINE = FormId("000057D5")


def test_callisto_special_then_common_use_one_draw_each(
    generation_data, ires_nodes
) -> None:
    result = generate_planet(generation_data[CALLISTO], ires_nodes)
    selectors = [
        item for item in result.events
        if item.kind in {EventKind.SPECIAL_PASS_RESULT, EventKind.COMMON_ROLL}
    ]
    assert [item.rng_draw.draw_number for item in selectors] == [1, 2]
    assert selectors[0]["selected_resource"].name == "Helium-3"
    assert selectors[1]["selected_resource"].name == "Iron"
    assert [
        item.provenance for item in result.occurrences
        if item.resource.name in {"Helium-3", "Iron"}
    ][:2] == [ResourceProvenance.SPECIAL, ResourceProvenance.COMMON]
    assert [item.resource.name for item in result.special_occurrences] == ["Helium-3"]
    assert result.common_occurrences[0].resource.name == "Iron"
    assert {FormId("000057F5"), FormId("000057C7")} <= result.occupied_resource_ids


def test_maal_atmosphere_precedes_everywhere_and_main_generation(
    generation_data, ires_nodes, atmospheric_resources
) -> None:
    result = generate_planet(
        generation_data[MAAL_VIII],
        ires_nodes,
        atmospheric_records=atmospheric_resources[MAAL_VIII],
    )
    kinds = [item.kind for item in result.events]
    assert kinds.index(EventKind.ATMOSPHERIC_RESOURCE_LOADED) < kinds.index(
        EventKind.EVERYWHERE_PREPASS_BEGIN
    ) < kinds.index(EventKind.BIOME_BEGIN)
    chlorine = result.atmospheric_occurrences[0]
    assert chlorine.resource.form_id == CHLORINE
    assert chlorine.provenance is ResourceProvenance.ATMO
    assert chlorine.occupies_state is True
    assert CHLORINE in result.occupied_resource_ids
    end = next(
        item for item in result.events if item.kind is EventKind.EVERYWHERE_PREPASS_END
    )
    assert end["visited_biome_count"] == 4
    contexts = [
        item for item in result.events
        if item.kind is EventKind.EVERYWHERE_PREPASS_CONTEXT
    ]
    assert [item["biome_index"] for item in contexts] == [0, 1, 2, 3]


def test_duplicate_form_id_preserves_occurrences_but_one_slot(ires_nodes) -> None:
    state = PlanetResourceState()
    node = ires_nodes[CHLORINE]
    resource = ResourceRef(node.form_id, node.editor_id, node.name, node.rarity)
    first, _ = state.record(resource, ResourceProvenance.ATMO)
    second, _ = state.record(resource, ResourceProvenance.COMMON)
    assert [first.provenance, second.provenance] == [
        ResourceProvenance.ATMO, ResourceProvenance.COMMON
    ]
    assert first.occupied_new_slot is True
    assert second.occupied_new_slot is False
    assert state.occupied_resource_ids == frozenset({CHLORINE})


def test_capacity_is_shared_across_all_generation_provenances(ires_nodes) -> None:
    state = PlanetResourceState()
    provenances = [
        ResourceProvenance.ATMO,
        ResourceProvenance.EVERYWHERE,
        ResourceProvenance.SPECIAL,
        ResourceProvenance.COMMON,
        ResourceProvenance.DESCENDANT,
    ]
    nodes = list(ires_nodes.values())[:9]
    for index, node in enumerate(nodes[:8]):
        occurrence, _ = state.record(
            ResourceRef(node.form_id, node.editor_id, node.name, node.rarity),
            provenances[index % len(provenances)],
        )
        assert occurrence.occupies_state is True
    rejected, _ = state.record(
        ResourceRef(nodes[8].form_id, nodes[8].editor_id, nodes[8].name, nodes[8].rarity),
        ResourceProvenance.DESCENDANT,
    )
    assert rejected.occupies_state is False
    assert len(state.occupied_resource_ids) == PlanetResourceState.CAPACITY


def test_descendant_capacity_guard_consumes_no_rng(
    generation_data, ires_nodes
) -> None:
    planet = generation_data[CALLISTO]
    root = planet.biomes[0].effective_rsgd.entries[0]
    state = PlanetResourceState()
    resources = list(ires_nodes.values())[: PlanetResourceState.CAPACITY]
    # Ensure the selected root is already one of the occupied identities so the
    # current engine-shaped model records duplicate provenance without a ninth slot.
    resources[0] = ires_nodes[root.resource_form_id]
    for node in resources:
        state.record(
            ResourceRef(node.form_id, node.editor_id, node.name, node.rarity),
            ResourceProvenance.ATMO,
        )
    rng = StarfieldRng(planet.resource_creation_seed)
    family = generate_family(
        root, ires_nodes, rng, resource_state=state, biome=planet.biomes[0]
    )
    assert rng.draw_count == 0
    assert all(level.inclusion_draw is None for level in family.levels)
    guards = [
        item for item in family.events
        if item.kind is EventKind.RESOURCE_CAPACITY_REACHED
        and item.operation == "descendant_capacity_guard"
    ]
    assert len(guards) == 4
    assert all(item["rng_consumed"] is False for item in guards)
