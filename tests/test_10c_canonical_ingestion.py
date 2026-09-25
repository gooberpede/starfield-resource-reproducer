"""Contracts for Brief 10C canonical ingestion and occurrence enrichment."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from starfield_resource_reproducer.domain import FormId
from starfield_resource_reproducer.load_data import (
    DataValidationError,
    IRES_COLUMNS,
    PLANET_DIRECTORY_COLUMNS,
    load_ires_hierarchy,
    load_planet_directory,
    validate_canonical_input_coherence,
)


VOLII_ALPHA = FormId("0005E3A5")


def test_planet_directory_canonical_shape_and_representatives(planet_directory) -> None:
    assert len(planet_directory) == 1776
    assert len(set(planet_directory)) == 1776
    assert planet_directory[FormId("010026BD")].body_type == "Planet"
    moon = planet_directory[FormId("010026C5")]
    assert (moon.body_type, moon.parent_planet_id) == ("Moon", 20)
    orbital = planet_directory[FormId("0102BA29")]
    assert (orbital.body_type, orbital.planet_name) == ("Orbital", "The Oracle")
    assert (
        orbital.solar_array_power,
        orbital.wind_turbine_power,
        orbital.planetary_habitation_rank,
    ) == (None, None, 0)
    non_landable = planet_directory[FormId("010026BD")]
    assert (
        non_landable.solar_array_power,
        non_landable.wind_turbine_power,
        non_landable.planetary_habitation_rank,
    ) == (None, None, None)
    mimas = planet_directory[FormId("0005DEC0")]
    assert (
        mimas.solar_array_power,
        mimas.wind_turbine_power,
        mimas.planetary_habitation_rank,
    ) == (2, 0, 1)
    volii = planet_directory[VOLII_ALPHA]
    assert volii.ocean_world is True
    assert volii.planet_not_landable is False
    assert (
        volii.solar_array_power,
        volii.wind_turbine_power,
        volii.planetary_habitation_rank,
    ) == (6, 10, 0)
    # The v4 contract permits blanks for unrecognized keyword combinations, but
    # every current landable non-Orbital canonical body has recognized values.
    assert all(
        record.solar_array_power is not None
        and record.wind_turbine_power is not None
        for record in planet_directory.values()
        if not record.planet_not_landable and record.body_type != "Orbital"
    )


def test_planet_directory_exact_v4_header_and_canonical_hash() -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "planet-directory.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        assert tuple(next(csv.reader(source))) == PLANET_DIRECTORY_COLUMNS
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "c460062747126a2168109739e75742d325cedf54b98577e5a017b5108ec5eb90"
    )


def test_project_retains_four_production_dataset_metadata(project_data) -> None:
    assert set(project_data.dataset_metadata) == {
        "planet_resource_generation",
        "ires_hierarchy",
        "planet_atmospheric_resources",
        "planet_directory",
    }
    assert project_data.dataset_metadata["planet_directory"].row_count == 1776
    assert all(item.extract_timestamp for item in project_data.dataset_metadata.values())


def test_directory_rejects_duplicate_form_id_and_invalid_flag(tmp_path: Path) -> None:
    row = {
        "SourceFile": "Starfield.esm", "ExtractTimestamp": "now",
        "PlanetFormID": "00000001", "PlanetEditorID": "BodyData",
        "PlanetName": "Body", "BodyType": "Planet", "StarSystemID": "1",
        "SystemName": "System", "ParentPlanetID": "0", "PlanetID": "1",
        "PlanetNotLandable": "0", "OceanWorld": "0",
        "SolarArrayPower": "6", "WindTurbinePower": "6",
        "PlanetaryHabitationRank": "0",
    }
    path = tmp_path / "directory.csv"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=PLANET_DIRECTORY_COLUMNS)
        writer.writeheader()
        writer.writerows([row, row])
    with pytest.raises(DataValidationError, match="duplicate PlanetFormID"):
        load_planet_directory(path)

    row["OceanWorld"] = "yes"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=PLANET_DIRECTORY_COLUMNS)
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(DataValidationError, match="invalid boolean flag OceanWorld"):
        load_planet_directory(path)


def test_directory_rejects_stale_or_malformed_v4_schema(tmp_path: Path) -> None:
    path = tmp_path / "directory.csv"
    stale_columns = PLANET_DIRECTORY_COLUMNS[:-3]
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=stale_columns)
        writer.writeheader()
        writer.writerow({field: "value" for field in stale_columns})
    with pytest.raises(DataValidationError, match="missing required column"):
        load_planet_directory(path)

    reordered_columns = (
        *PLANET_DIRECTORY_COLUMNS[:-2],
        *reversed(PLANET_DIRECTORY_COLUMNS[-2:]),
    )
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=reordered_columns)
        writer.writeheader()
        writer.writerow({field: "value" for field in reordered_columns})
    with pytest.raises(DataValidationError, match="header does not match approved schema"):
        load_planet_directory(path)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("SolarArrayPower", "5"),
        ("WindTurbinePower", "7"),
        ("PlanetaryHabitationRank", "5"),
    ),
)
def test_directory_rejects_invalid_v4_environmental_values(
    tmp_path: Path, field: str, value: str
) -> None:
    row = {
        "SourceFile": "Starfield.esm", "ExtractTimestamp": "now",
        "PlanetFormID": "00000001", "PlanetEditorID": "BodyData",
        "PlanetName": "Body", "BodyType": "Planet", "StarSystemID": "1",
        "SystemName": "System", "ParentPlanetID": "0", "PlanetID": "1",
        "PlanetNotLandable": "0", "OceanWorld": "0", "SolarArrayPower": "6",
        "WindTurbinePower": "6", "PlanetaryHabitationRank": "0",
    }
    row[field] = value
    path = tmp_path / "directory.csv"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=PLANET_DIRECTORY_COLUMNS)
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(DataValidationError, match=f"invalid {field}"):
        load_planet_directory(path)


def test_directory_accepts_blank_solar_and_wind_for_landable_body(
    tmp_path: Path,
) -> None:
    row = {
        "SourceFile": "Starfield.esm", "ExtractTimestamp": "now",
        "PlanetFormID": "00000001", "PlanetEditorID": "BodyData",
        "PlanetName": "Body", "BodyType": "Planet", "StarSystemID": "1",
        "SystemName": "System", "ParentPlanetID": "0", "PlanetID": "1",
        "PlanetNotLandable": "0", "OceanWorld": "0", "SolarArrayPower": "",
        "WindTurbinePower": "", "PlanetaryHabitationRank": "0",
    }
    path = tmp_path / "directory.csv"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=PLANET_DIRECTORY_COLUMNS)
        writer.writeheader()
        writer.writerow(row)

    record = load_planet_directory(path)[FormId("00000001")]
    assert record.solar_array_power is None
    assert record.wind_turbine_power is None


def test_cross_input_coverage_and_atmosphere_only_body(project_data) -> None:
    assert set(project_data.planets) <= set(project_data.planet_directory)
    assert set(project_data.atmospheric_resources) <= set(project_data.planet_directory)
    assert VOLII_ALPHA in project_data.atmospheric_resources
    assert VOLII_ALPHA not in project_data.planets


def test_cross_input_identity_mismatch_has_useful_diagnostic(project_data) -> None:
    planet_id = next(iter(project_data.planets))
    directory = dict(project_data.planet_directory)
    directory[planet_id] = replace(directory[planet_id], planet_name="Wrong")
    with pytest.raises(
        DataValidationError, match=f"generation/directory identity conflicts for {planet_id}"
    ):
        validate_canonical_input_coherence(
            project_data.planets,
            project_data.ires_nodes,
            project_data.atmospheric_resources,
            directory,
        )


def test_ires_parent_and_child_source_plugins_are_independent(tmp_path: Path) -> None:
    row = {
        "SourceFile": "Starfield.esm", "ExtractTimestamp": "now",
        "FormID": "00000001", "EditorID": "Parent", "Name": "Parent",
        "Rarity": "Common", "ChildSourceFile": "ShatteredSpace.esm",
        "ChildFormID": "01000002", "ChildEditorID": "Child",
        "ChildName": "Child", "ChildRarity": "Uncommon",
    }
    path = tmp_path / "ires.csv"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=sorted(IRES_COLUMNS))
        writer.writeheader()
        writer.writerow(row)

    graph = load_ires_hierarchy(path)
    parent = graph[FormId("00000001")]
    child = graph[FormId("01000002")]
    assert parent.source_file == "Starfield.esm"
    assert parent.children[0].source_file == "ShatteredSpace.esm"
    assert child.source_file == "ShatteredSpace.esm"
    assert child.children == ()
