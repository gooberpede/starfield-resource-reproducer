"""Regression coverage for guarded biome-local Common-family assignment.

Purpose: verify the recovered post-guard fallback, RNG consumption, family-origin
provenance, duplicate occurrence recording, and CK-observed biome assignments.
Boundaries: canonical planet-wide output remains covered by full validation; these
tests do not feed CK expectations into production generation.
Evidence: branches and expected biome sets are PROVEN LIVE per Brief 08D.
"""

from __future__ import annotations

from dataclasses import replace

from starfield_resource_reproducer.diagnostics import EventKind
from starfield_resource_reproducer.domain import (
    CommonAssignmentMechanism,
    CommonGuardReason,
    CommonNoAssignmentReason,
    FormId,
    GenerationRarity,
    ResourceProvenance,
)
from starfield_resource_reproducer.generation import (
    PlanetResourceState,
    _assign_guard_fallback_family,
    generate_planet,
)
from starfield_resource_reproducer.prng import StarfieldRng


PLANETS = {
    "Bara VII-d": FormId("0005E39F"),
    "Jaffa VII-b": FormId("0005E216"),
    "Indum IV-d": FormId("0005E19A"),
    "Zeta Ophiuchi I": FormId("0005E151"),
    "Pyraas VIII-a": FormId("0005DFD9"),
}

H2O = FormId("000083EC")
FE = FormId("000057C7")
TA = FormId("000057C8")
CU = FormId("000057CF")
F = FormId("000057D0")
AU = FormId("000057D2")
SB = FormId("000057D3")
PB = FormId("000057C1")
AG = FormId("000057C3")
HNCN = FormId("000057C9")
YB = FormId("000057CA")
CL = FormId("000057D5")
SIH3CL = FormId("000057D7")
W = FormId("000057C4")
TI = FormId("000057C6")
DY = FormId("000057C2")


def _generate(name, generation_data, ires_nodes, atmospheric_resources):
    planet_id = PLANETS[name]
    return generate_planet(
        generation_data[planet_id],
        ires_nodes,
        atmospheric_records=atmospheric_resources.get(planet_id, ()),
    )


def _view(result, biome_name):
    return next(
        item for item in result.biome_resource_views() if item.biome.name == biome_name
    )


def _ids(view):
    return frozenset(resource.form_id for resource in view.resources)


def test_guard_no_common_entries_assigns_nothing_and_consumes_no_fallback_draw(
    generation_data, ires_nodes, atmospheric_resources
) -> None:
    result = _generate("Jaffa VII-b", generation_data, ires_nodes, atmospheric_resources)
    ocean = _view(result, "Ocean")
    assignment = ocean.common_assignment

    assert assignment.mechanism is CommonAssignmentMechanism.NO_COMMON_ASSIGNMENT
    assert assignment.guard_reason is CommonGuardReason.SHARED_RESOURCE_CAPACITY
    assert assignment.no_assignment_reason is (
        CommonNoAssignmentReason.GUARD_RSGD_HAS_NO_COMMON
    )
    assert assignment.rng_draw is None
    candidates = [
        item
        for item in ocean.common_assignment.rsgd_common_roots
        if item.rarity is GenerationRarity.COMMON
    ]
    assert candidates == []
    assert not any(
        item.kind is EventKind.COMMON_GUARD_FALLBACK_ROLL
        for item in next(
            biome
            for biome in result.biome_results
            if biome.orchestration.biome.name == "Ocean"
        ).orchestration.events
    )


def test_one_match_consumes_one_fallback_draw_and_records_origin_occurrences(
    generation_data, ires_nodes, atmospheric_resources
) -> None:
    result = _generate("Jaffa VII-b", generation_data, ires_nodes, atmospheric_resources)
    volcanic = _view(result, "Volcanic")
    assignment = volcanic.common_assignment

    assert assignment.mechanism is CommonAssignmentMechanism.GUARD_MATCHED_FALLBACK
    assert assignment.rng_draw is not None
    assert assignment.rng_draw.upper_bound == 1
    assert assignment.rng_draw.operation == "fallback_family_index"
    assert assignment.family is not None
    assert assignment.family.origin.biome_name == "Frozen Plains"
    assert assignment.family.origin.processing_position == 0
    assert _ids(volcanic) == {PB, W, TI, DY}
    assert all(
        not item.occupied_new_slot
        and item.common_assignment_mechanism
        is CommonAssignmentMechanism.GUARD_MATCHED_FALLBACK
        for item in volcanic.common_occurrences
    )


def test_multiple_matches_use_only_preferred_pool_and_one_scaled_draw(
    generation_data, ires_nodes, atmospheric_resources
) -> None:
    result = _generate("Jaffa VII-b", generation_data, ires_nodes, atmospheric_resources)
    lead = result.family_cache[PB]
    chlorine = result.family_cache[CL]
    iron = result.family_cache[FE]
    source = next(item for item in result.planet.biomes if item.name == "Volcanic")
    all_entries = (
        entry
        for source_biome in result.planet.biomes
        for entry in source_biome.effective_rsgd.entries
    )
    entries_by_id = {
        entry.resource_form_id: entry
        for entry in all_entries
        if entry.resource_form_id in {PB, CL}
    }
    entries = (entries_by_id[PB], entries_by_id[CL])
    biome = replace(source, pndt_rsgd=replace(source.effective_rsgd, entries=entries))
    state = PlanetResourceState()
    for family in (lead, chlorine, iron):
        for resource in family.emitted_resources:
            state.record(resource, ResourceProvenance.COMMON)
    rng = StarfieldRng(123)

    assignment, events = _assign_guard_fallback_family(
        biome=biome,
        guard_reason=CommonGuardReason.SHARED_RESOURCE_CAPACITY,
        family_cache={PB: lead, CL: chlorine, FE: iron},
        resource_state=state,
        rng=rng,
    )

    assert rng.draw_count == 1
    assert assignment.mechanism is CommonAssignmentMechanism.GUARD_MATCHED_FALLBACK
    assert {item.form_id for item in assignment.candidate_family_roots} == {PB, CL}
    assert FE not in {item.form_id for item in assignment.candidate_family_roots}
    assert len([item for item in events if item.kind is EventKind.COMMON_GUARD_FALLBACK_ROLL]) == 1
    assert not any(item.kind is EventKind.DESCENDANT_LEVEL_BEGIN for item in events)


def test_general_fallback_uses_all_cached_families_and_is_not_normal_reuse(
    generation_data, ires_nodes, atmospheric_resources
) -> None:
    result = _generate("Jaffa VII-b", generation_data, ires_nodes, atmospheric_resources)
    plateau = _view(result, "Plateau")
    rocky = _view(result, "Rocky Desert")

    assert plateau.common_assignment.mechanism is CommonAssignmentMechanism.GUARD_GENERAL_FALLBACK
    assert plateau.common_assignment.rng_draw is not None
    assert plateau.common_assignment.rng_draw.upper_bound == 3
    assert {item.form_id for item in plateau.common_assignment.candidate_family_roots} == {
        PB,
        CL,
        FE,
    }
    assert rocky.common_assignment.mechanism is CommonAssignmentMechanism.NORMAL_CACHE_REUSE
    assert rocky.common_assignment.guard_reason is None


def test_both_guard_types_enter_fallback(
    generation_data, ires_nodes, atmospheric_resources
) -> None:
    bara = _generate("Bara VII-d", generation_data, ires_nodes, atmospheric_resources)
    jaffa = _generate("Jaffa VII-b", generation_data, ires_nodes, atmospheric_resources)

    assert _view(bara, "Hills").common_assignment.guard_reason is CommonGuardReason.COMMON_TREE_LIMIT
    assert _view(jaffa, "Volcanic").common_assignment.guard_reason is CommonGuardReason.SHARED_RESOURCE_CAPACITY


def test_ck_biome_regression_set(
    generation_data, ires_nodes, atmospheric_resources
) -> None:
    expected = {
        "Bara VII-d": {"Hills": {FE}},
        "Jaffa VII-b": {
            "Volcanic": {PB, W, TI, DY},
            "Hills": {FE},
            "Plateau": {PB, W, TI, DY},
        },
        "Indum IV-d": {
            "Swamp": {H2O, FE, TA},
            "Sandy Desert": {CU, F, AU, SB},
            "Wetlands": {H2O, CU, F, AU, SB},
        },
        "Zeta Ophiuchi I": {
            "Swamp": {H2O, PB, AG},
            "Frozen Dunes": {H2O, FE, HNCN, TA, YB},
            "Deciduous Forest": {H2O, FE, HNCN, TA, YB},
            "Savanna": {H2O, FE, HNCN, TA, YB},
        },
        "Pyraas VIII-a": {"Sandy Desert": {CL, SIH3CL}},
    }

    for planet_name, biome_expectations in expected.items():
        result = _generate(
            planet_name, generation_data, ires_nodes, atmospheric_resources
        )
        for biome_name, form_ids in biome_expectations.items():
            assert _ids(_view(result, biome_name)) == form_ids
