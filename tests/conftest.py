from pathlib import Path

import pytest

from starfield_resource_reproducer.domain import (
    AtmosphericResourceRecord,
    CanonicalBodyResources,
    FormId,
    IRESNode,
    Planet,
)
from starfield_resource_reproducer.load_data import (
    load_atmospheric_resources,
    load_canonical_oracle,
    load_generation_data,
    load_ires_hierarchy,
)


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
