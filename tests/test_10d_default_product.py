"""Product-contract and corpus regressions for the Brief 10D default export."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from starfield_resource_reproducer.domain import FormId, ResourceProvenance
from starfield_resource_reproducer.generation import generate_planet
from starfield_resource_reproducer.load_data import load_production_data
from starfield_resource_reproducer.occurrences import build_enriched_occurrences
from starfield_resource_reproducer.product import (
    PRODUCT_COLUMNS,
    ProductValidationError,
    build_manifest,
    build_product,
    collapse_enriched_occurrences,
    compare_biome_projection_to_oracle,
    validate_product_rows,
)


MIMAS = FormId("0005DEC0")
JAFFA_VII_B = FormId("0005E216")
VOLII_ALPHA = FormId("0005E3A5")


def test_production_loader_does_not_load_validation_oracle() -> None:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    production = load_production_data(data_dir)
    assert production.oracle == {}
    assert set(production.dataset_metadata) == {
        "planet_resource_generation", "ires_hierarchy",
        "planet_atmospheric_resources", "planet_directory",
    }


def test_exact_schema_nullability_and_no_diagnostic_lineage(default_product) -> None:
    assert PRODUCT_COLUMNS == (
        "ReproducerVersion", "ExportTimestamp", "SystemName", "PlanetName",
        "BodyType", "PlanetFormID", "PlanetEditorID", "StarSystemID",
        "ParentPlanetID", "PlanetID", "PlanetSourceFile", "LocationType",
        "BiomeIndex", "BiomeFormID", "BiomeEditorID", "BiomeName",
        "BiomeChance", "BiomeSourceFile", "AtmosphereFormID",
        "AtmosphereEditorID", "AtmosphereSourceFile", "ResourceCategory",
        "ResourceFormID", "ResourceEditorID", "ResourceName", "Rarity",
        "ResourceSourceFile", "EffectiveRSGDFormID", "EffectiveRSGDEditorID",
        "RSGDSource", "RSGDSourceFile", "ResourceDefinedByAtmosphereFormID",
        "ResourceDefinedByAtmosphereEditorID",
        "ResourceDefinedByAtmosphereSourceFile", "AtmosphereInheritanceDepth",
    )
    assert tuple(default_product.rows[0]) == PRODUCT_COLUMNS
    assert not {
        "ResourceOrigin", "CommonAssignmentMechanism", "FamilyRootFormID",
        "FamilyRootEditorID", "FamilyOriginBiomeIndex", "FamilyOriginBiomeFormID",
    } & set(PRODUCT_COLUMNS)
    validate_product_rows(default_product.rows)


def test_corpus_location_and_targeted_body_contracts(default_product) -> None:
    rows = default_product.rows
    mimas = [row for row in rows if row["PlanetFormID"] == str(MIMAS)]
    assert any(row["LocationType"] == "BIOME" for row in mimas)

    volii = [row for row in rows if row["PlanetFormID"] == str(VOLII_ALPHA)]
    assert len(volii) == 2
    assert {row["LocationType"] for row in volii} == {"ATMOSPHERE"}

    assert any(
        row["LocationType"] == "ATMOSPHERE"
        and int(row["AtmosphereInheritanceDepth"]) > 0
        for row in rows
    )
    assert any(
        row["PlanetFormID"] == str(JAFFA_VII_B)
        and row["LocationType"] == "BIOME"
        for row in rows
    )

    resource_locations: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for row in rows:
        if row["LocationType"] == "BIOME":
            resource_locations.setdefault(
                (row["PlanetFormID"], row["ResourceFormID"]), set()
            ).add((row["BiomeIndex"], row["BiomeFormID"]))
    assert any(len(locations) > 1 for locations in resource_locations.values())


def test_constructed_multiple_origin_collapse_and_conflict(project_data) -> None:
    generation = generate_planet(
        project_data.planets[MIMAS],
        project_data.ires_nodes,
        atmospheric_records=project_data.atmospheric_resources.get(MIMAS, ()),
    )
    enriched = build_enriched_occurrences(project_data, {MIMAS: generation})
    original = next(row for row in enriched if row.location_type.value == "BIOME")
    duplicate_origin = replace(
        original,
        resource_origin=(
            ResourceProvenance.SPECIAL
            if original.resource_origin is not ResourceProvenance.SPECIAL
            else ResourceProvenance.EVERYWHERE
        ),
    )
    collapsed = collapse_enriched_occurrences(
        (*enriched, duplicate_origin),
        reproducer_version="test",
        export_timestamp="2026-09-03T00:00:00Z",
    )
    assert len(collapsed) == len(enriched)

    conflict = replace(duplicate_origin, resource_name="Conflicting name")
    with pytest.raises(ProductValidationError, match="safe-collapse conflict"):
        collapse_enriched_occurrences(
            (*enriched, conflict),
            reproducer_version="test",
            export_timestamp="2026-09-03T00:00:00Z",
        )


def test_deterministic_regeneration_and_old_oracle_projection(
    project_data, default_product
) -> None:
    repeated = build_product(
        project_data, export_timestamp="2026-09-03T00:00:00Z"
    )
    assert repeated.rows == default_product.rows

    comparison = compare_biome_projection_to_oracle(
        default_product.rows, project_data.oracle
    )
    assert comparison.compared_body_count == 1444
    assert comparison.exact_body_count == 1444
    assert comparison.mismatched_body_ids == ()


def test_biome_identity_audit_matches_canonical_corpus(default_product) -> None:
    audit = default_product.biome_audit
    assert audit.duplicate_index_groups == ()
    assert audit.repeated_form_id_groups == ()
    assert audit.repeated_name_planet_count == 5
    assert len(audit.repeated_name_groups) == 5
    assert {item.planet_name for item in audit.repeated_name_groups} == {
        "Verne I", "Ourea", "Alchiba II", "Eridani I", "Grimsey",
    }


def test_manifest_describes_only_four_production_inputs(
    project_data, default_product
) -> None:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    manifest = build_manifest(project_data, data_dir, default_product)
    assert manifest["schema_version"] == 1
    assert manifest["row_count"] == len(default_product.rows)
    assert [item["filename"] for item in manifest["input_datasets"]] == [
        "planet-resource-generation.csv", "ires-hierarchy.csv",
        "planet-atmospheric-resources.csv", "planet-directory.csv",
    ]
    assert all(len(item["sha256"]) == 64 for item in manifest["input_datasets"])
    assert "planet-all-resources.csv" not in str(manifest)
