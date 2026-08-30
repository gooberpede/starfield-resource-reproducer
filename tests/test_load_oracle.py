import csv
from pathlib import Path

import pytest

from conftest import DATA_DIR
from starfield_resource_reproducer.domain import FormId
from starfield_resource_reproducer.load_data import (
    DataValidationError,
    load_canonical_oracle,
    load_project_data,
)


def test_oracle_integrity_counts(canonical_oracle) -> None:
    assert len(canonical_oracle) == 1445
    inorganic_rows = sum(
        len(body.inorganic_resource_records) for body in canonical_oracle.values()
    )
    organic_rows = sum(
        len(body.organic_resource_records) for body in canonical_oracle.values()
    )
    assert inorganic_rows == 6040
    assert organic_rows == 1623
    assert inorganic_rows + organic_rows == 7663
    assert sum(bool(body.inorganic_resources) for body in canonical_oracle.values()) == 1444


def test_oracle_inorganic_lookup_excludes_organic(canonical_oracle) -> None:
    for body in canonical_oracle.values():
        assert all(
            resource.category == "Inorganic"
            for resource in body.inorganic_resource_records
        )
        assert all(
            resource.category == "Organic" for resource in body.organic_resource_records
        )
        assert body.inorganic_resources == frozenset(
            resource.resource_form_id for resource in body.inorganic_resource_records
        )


def test_generation_and_inorganic_oracle_body_sets_match(
    generation_data, canonical_oracle
) -> None:
    inorganic_body_ids = {
        form_id for form_id, body in canonical_oracle.items() if body.inorganic_resources
    }

    assert len(inorganic_body_ids) == 1444
    assert set(generation_data) == inorganic_body_ids


def test_oracle_rarity_remains_descriptive(canonical_oracle) -> None:
    decaran = canonical_oracle[FormId("0005DF7F")]
    helium = next(
        resource
        for resource in decaran.inorganic_resource_records
        if resource.resource_name == "Helium3"
    )

    assert helium.oracle_rarity == "Common"
    assert not hasattr(helium, "resource_rarity")


def test_project_loader_bundles_independent_datasets() -> None:
    project = load_project_data(DATA_DIR)

    assert len(project.planets) == 1444
    assert len(project.ires_nodes) == 47
    assert len(project.oracle) == 1445


def test_oracle_rejects_duplicate_planet_resource_pair(tmp_path: Path) -> None:
    with (DATA_DIR / "planet-all-resources.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source:
        row = next(csv.DictReader(source))
    path = tmp_path / "oracle.csv"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(row))
        writer.writeheader()
        writer.writerows([row, row])

    with pytest.raises(DataValidationError, match="duplicate .* pair"):
        load_canonical_oracle(path)
