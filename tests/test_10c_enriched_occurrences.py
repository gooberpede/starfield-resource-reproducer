"""Typed accepted-occurrence projection contracts for Brief 10C."""

from __future__ import annotations

from dataclasses import replace

from starfield_resource_reproducer.domain import (
    CommonAssignmentMechanism,
    FormId,
    ResourceProvenance,
)
from starfield_resource_reproducer.generation import generate_planet
from starfield_resource_reproducer.occurrences import (
    LocationType,
    build_enriched_occurrences,
)


MIMAS = FormId("0005DEC0")
JAFFA_VII_B = FormId("0005E216")
VOLII_ALPHA = FormId("0005E3A5")


def _generate(project, planet_id):
    return generate_planet(
        project.planets[planet_id],
        project.ires_nodes,
        atmospheric_records=project.atmospheric_resources.get(planet_id, ()),
    )


def test_enriched_biome_occurrence_has_directory_rsgd_and_resource_context(
    project_data,
) -> None:
    result = _generate(project_data, MIMAS)
    rows = [
        row for row in build_enriched_occurrences(project_data, {MIMAS: result})
        if row.planet_form_id == MIMAS
    ]
    palladium = next(row for row in rows if row.resource_name == "Palladium")

    assert (palladium.planet_name, palladium.body_type) == ("Mimas", "Moon")
    assert palladium.location_type is LocationType.BIOME
    assert palladium.biome_index is not None
    assert palladium.biome_form_id is not None
    assert palladium.effective_rsgd_form_id is not None
    assert palladium.rsgd_source is not None
    assert palladium.resource_origin is ResourceProvenance.DESCENDANT
    assert palladium.resource_source_file == "Starfield.esm"


def test_common_lineage_keeps_original_family_biome_across_reuse_and_fallback(
    project_data,
) -> None:
    result = _generate(project_data, JAFFA_VII_B)
    rows = build_enriched_occurrences(project_data, {JAFFA_VII_B: result})
    common_rows = [
        row for row in rows
        if row.resource_origin in {
            ResourceProvenance.COMMON_ROOT, ResourceProvenance.DESCENDANT
        }
    ]
    mechanisms = {row.common_assignment_mechanism for row in common_rows}
    assert CommonAssignmentMechanism.NEW_FAMILY in mechanisms
    assert CommonAssignmentMechanism.NORMAL_CACHE_REUSE in mechanisms
    assert CommonAssignmentMechanism.GUARD_MATCHED_FALLBACK in mechanisms
    assert CommonAssignmentMechanism.GUARD_GENERAL_FALLBACK in mechanisms
    for row in common_rows:
        assert row.family_root_form_id is not None
        assert row.family_root_editor_id is not None
        assert row.family_origin_biome_index is not None
        assert row.family_origin_biome_form_id is not None

    lead_rows = [row for row in common_rows if row.family_root_form_id == FormId("000057C1")]
    assert len({(row.family_origin_biome_index, row.family_origin_biome_form_id) for row in lead_rows}) == 1


def test_volii_alpha_projects_atmosphere_without_synthetic_generation(project_data) -> None:
    rows = build_enriched_occurrences(project_data, {})
    volii = [row for row in rows if row.planet_form_id == VOLII_ALPHA]
    assert len(volii) == 2
    assert all(row.location_type is LocationType.ATMOSPHERE for row in volii)
    assert all(row.resource_origin is ResourceProvenance.ATMOSPHERE for row in volii)
    assert all(row.atmosphere_form_id is not None for row in volii)
    assert all(row.resource_defined_by_atmosphere_form_id is not None for row in volii)
    assert all(row.atmosphere_inheritance_depth is not None for row in volii)
    assert all(row.biome_index is None and row.effective_rsgd_form_id is None for row in volii)
    assert all(row.family_root_form_id is None for row in volii)


def test_projection_retains_distinct_origins_instead_of_resource_deduplication(
    project_data,
) -> None:
    result = _generate(project_data, MIMAS)
    common = next(
        item for item in result.occurrences
        if item.provenance is ResourceProvenance.COMMON_ROOT
    )
    # Construct only the projection invariant; this is not a claim that Mimas has
    # a second canonical origin for this resource in the shipped corpus.
    distinct_origin = replace(
        common,
        provenance=ResourceProvenance.SPECIAL,
        root_form_id=None,
        common_assignment_mechanism=None,
    )
    result = replace(result, occurrences=(*result.occurrences, distinct_origin))
    rows = [
        row for row in build_enriched_occurrences(project_data, {MIMAS: result})
        if row.planet_form_id == MIMAS
    ]
    keys = [
        (
            row.planet_form_id, row.location_type, row.biome_index,
            row.biome_form_id, row.resource_form_id, row.resource_origin,
        )
        for row in rows
    ]
    assert len(keys) == len(set(keys))
    assert len(rows) == sum(1 for item in result.occurrences if item.occupies_state)
    duplicate_location = [
        row for row in rows
        if row.biome_index == common.biome_index
        and row.resource_form_id == common.resource.form_id
    ]
    assert {row.resource_origin for row in duplicate_location} == {
        ResourceProvenance.COMMON_ROOT,
        ResourceProvenance.SPECIAL,
    }
