from pathlib import Path

import pytest

from starfield_resource_reproducer.domain import (
    AtmosphericResourceRecord,
    CanonicalBodyResources,
    FormId,
    IRESNode,
    Planet,
    PlanetDirectoryRecord,
    ProjectData,
)
from starfield_resource_reproducer.load_data import (
    load_atmospheric_resources,
    load_canonical_oracle,
    load_generation_data,
    load_ires_hierarchy,
    load_planet_directory,
    load_project_data,
)
from starfield_resource_reproducer.product import build_product


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="session")
def generation_data() -> dict[FormId, Planet]:
    return load_generation_data(DATA_DIR / "planet-resource-generation.csv")


@pytest.fixture(scope="session")
def ires_nodes() -> dict[FormId, IRESNode]:
    return load_ires_hierarchy(DATA_DIR / "ires-hierarchy.csv")


@pytest.fixture(scope="session")
def canonical_oracle() -> dict[FormId, CanonicalBodyResources]:
    return load_canonical_oracle(DATA_DIR / "planet-all-resources.csv")


@pytest.fixture(scope="session")
def atmospheric_resources() -> dict[
    FormId, tuple[AtmosphericResourceRecord, ...]
]:
    return load_atmospheric_resources(
        DATA_DIR / "planet-atmospheric-resources.csv"
    )


@pytest.fixture(scope="session")
def planet_directory() -> dict[FormId, PlanetDirectoryRecord]:
    return load_planet_directory(DATA_DIR / "planet-directory.csv")


@pytest.fixture(scope="session")
def project_data() -> ProjectData:
    return load_project_data(DATA_DIR)


@pytest.fixture(scope="session")
def default_product(project_data):
    return build_product(
        project_data, export_timestamp="2026-09-03T00:00:00Z"
    )
