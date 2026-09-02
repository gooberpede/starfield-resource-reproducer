import csv
from pathlib import Path

import pytest

from starfield_resource_reproducer.domain import FormId
from starfield_resource_reproducer.load_data import (
    ATMOSPHERIC_COLUMNS,
    DataValidationError,
    load_atmospheric_resources,
    load_project_data,
)


MAAL_VIII = FormId("0005DE6F")
VESTA = FormId("0005E568")


def test_real_atmospheric_csv_preserves_order_and_provenance(
    atmospheric_resources,
) -> None:
    assert sum(len(records) for records in atmospheric_resources.values()) == 335
    assert len(atmospheric_resources) == 297
    assert [record.resource_name for record in atmospheric_resources[VESTA]] == [
        "Benzene", "Water"
    ]
    first = atmospheric_resources[VESTA][0]
    assert first.atmospheric_resource_count == 2
    assert first.atmospheric_resource_index == 0
    assert first.atmosphere_editor_id == "ATMO_Vesta"
    assert first.defined_by_atmosphere_editor_id == "ATMO_Vesta"
    assert first.atmosphere_inheritance_depth == 0
    assert atmospheric_resources[MAAL_VIII][0].resource_name == "Chlorine"


def test_project_data_includes_atmospheric_records() -> None:
    project = load_project_data(Path("data"))
    assert project.atmospheric_resources[MAAL_VIII][0].resource_name == "Chlorine"


def _write_csv(path, rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=sorted(ATMOSPHERIC_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def _row() -> dict[str, str]:
    return {
        "SourceFile": "Starfield.esm", "ExtractTimestamp": "now",
        "PlanetFormID": "0005DE6F", "PlanetEditorID": "MaalVIIIPlanetData",
        "PlanetName": "Maal VIII", "BodyType": "Planet", "StarSystemID": "1",
        "SystemName": "Maal", "ParentPlanetID": "0", "PlanetID": "8",
        "AtmosphereFormID": "0000D4E6", "AtmosphereEditorID": "ATMO_MaalVIII",
        "AtmosphereSourceFile": "Starfield.esm", "AtmosphericResourceCount": "1",
        "AtmosphericResourceIndex": "0", "ResourceFormID": "000057D5",
        "ResourceEditorID": "ResInorgCommonChlorine_G", "ResourceName": "Chlorine",
        "ResourceSourceFile": "Starfield.esm",
        "ResourceDefinedByAtmosphereFormID": "0000D4E6",
        "ResourceDefinedByAtmosphereEditorID": "ATMO_MaalVIII",
        "ResourceDefinedByAtmosphereSourceFile": "Starfield.esm",
        "AtmosphereInheritanceDepth": "0",
    }


def test_malformed_atmospheric_form_id_fails(tmp_path) -> None:
    row = _row()
    row["ResourceFormID"] = "bad"
    path = tmp_path / "atmo.csv"
    _write_csv(path, [row])
    with pytest.raises(DataValidationError, match="invalid ResourceFormID"):
        load_atmospheric_resources(path)


def test_contradictory_duplicate_atmospheric_row_fails(tmp_path) -> None:
    first = _row()
    second = dict(first)
    second["ResourceName"] = "Wrong"
    path = tmp_path / "atmo.csv"
    _write_csv(path, [first, second])
    with pytest.raises(DataValidationError, match="contradictory duplicate"):
        load_atmospheric_resources(path)
