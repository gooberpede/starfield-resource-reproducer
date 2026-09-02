import csv
from decimal import Decimal
from pathlib import Path

import pytest

from conftest import DATA_DIR
from starfield_resource_reproducer.domain import FormId, GenerationRarity
from starfield_resource_reproducer.load_data import (
    DataValidationError,
    load_generation_data,
)


def _oracle_names(canonical_oracle, planet_id: str) -> set[str]:
    return {
        resource.resource_name
        for resource in canonical_oracle[FormId(planet_id)].inorganic_resource_records
    }


def test_kreet_reconstruction(generation_data, canonical_oracle) -> None:
    kreet = generation_data[FormId("0003F59F")]

    assert kreet.resource_creation_seed == 2842708811
    assert [biome.index for biome in kreet.biomes] == [0, 1, 2]
    assert [biome.name for biome in kreet.biomes] == [
        "Frozen Volcanic",
        "Mountains",
        "Volcanic",
    ]
    frozen, mountains, volcanic = kreet.biomes
    assert frozen.pndt_rsgd is None
    assert frozen.effective_rsgd.editor_id == "FrozenBarrenDefaultRes"
    assert mountains.pndt_rsgd.editor_id == "MountainDefaultRes_Kreet"
    assert mountains.biom_rsgd.editor_id == "MountainDefaultRes"
    assert mountains.effective_rsgd is mountains.pndt_rsgd
    assert volcanic.pndt_rsgd.editor_id == "VolcanicDefaultRes_Kreet"
    assert volcanic.biom_rsgd.editor_id == "VolcanicDefaultRes"
    assert volcanic.effective_rsgd is volcanic.pndt_rsgd
    assert _oracle_names(canonical_oracle, "0003F59F") == {
        "Argon",
        "Iron",
        "Lead",
        "Water",
        "Alkanes",
        "Silver",
        "Neon",
    }


def test_mimas_reconstruction(generation_data, canonical_oracle) -> None:
    mimas = generation_data[FormId("0005DEC0")]

    assert mimas.resource_creation_seed == 2008989584
    assert len(mimas.biomes) == 1
    biome = mimas.biomes[0]
    assert biome.name == "Frozen Plains"
    assert biome.effective_rsgd.editor_id == "FrozenBarrenDefaultRes03"
    assert [entry.resource_name for entry in biome.effective_rsgd.entries] == [
        "Water",
        "Nickel",
        "Lead",
    ]
    water, nickel, lead = biome.effective_rsgd.entries
    assert water.everywhere_chance == Decimal("100")
    assert nickel.common_chance == Decimal("60")
    assert lead.common_chance == Decimal("40")
    assert _oracle_names(canonical_oracle, "0005DEC0") == {
        "Water",
        "Nickel",
        "Palladium",
    }


def test_decaran_vii_b_reconstruction(generation_data, canonical_oracle) -> None:
    decaran = generation_data[FormId("0005DF7F")]

    assert decaran.resource_creation_seed == 1633829920
    assert len(decaran.biomes) == 1
    biome = decaran.biomes[0]
    assert biome.name == "Craters"
    assert biome.pndt_rsgd.editor_id == "UniqueCrateredBarrenVytiniumRes"
    assert biome.biom_rsgd.editor_id == "CrateredNoLifeDefaultRes"
    assert biome.effective_rsgd is biome.pndt_rsgd
    helium, uranium = biome.effective_rsgd.entries
    assert (helium.index, helium.resource_name, helium.resource_rarity) == (
        0,
        "Helium-3",
        GenerationRarity.SPECIAL,
    )
    assert helium.special_chance == Decimal("100")
    assert (uranium.index, uranium.resource_name, uranium.resource_rarity) == (
        1,
        "Uranium",
        GenerationRarity.COMMON,
    )
    assert (
        uranium.common_chance,
        uranium.uncommon_chance,
        uranium.rare_chance,
        uranium.exotic_chance,
        uranium.unique_chance,
    ) == tuple(map(Decimal, ("100", "75", "35", "15", "100")))
    assert _oracle_names(canonical_oracle, "0005DF7F") == {
        "Helium3",
        "Uranium",
        "Iridium",
        "Vytinium",
    }
    helium_oracle = next(
        resource
        for resource in canonical_oracle[FormId("0005DF7F")].inorganic_resource_records
        if resource.resource_name == "Helium3"
    )
    assert helium_oracle.resource_form_id == helium.resource_form_id


def test_oberon_reconstruction(generation_data, canonical_oracle) -> None:
    oberon = generation_data[FormId("0005DECC")]

    assert oberon.resource_creation_seed == 555484356
    assert len(oberon.biomes) == 1
    assert [entry.resource_name for entry in oberon.biomes[0].effective_rsgd.entries] == [
        "Water",
        "Nickel",
        "Lead",
    ]
    assert _oracle_names(canonical_oracle, "0005DECC") == {"Water", "Nickel"}


def test_combined_pndt_biom_provenance_is_preserved(generation_data) -> None:
    akila = generation_data[FormId("0005E2B6")]
    savanna = next(biome for biome in akila.biomes if biome.name == "Savanna")

    assert savanna.pndt_rsgd is savanna.biom_rsgd
    assert savanna.effective_rsgd.source.value == "PNDT+BIOM"
    assert savanna.effective_rsgd.editor_id == "SavannaDefaultResSettled"


def test_generation_integrity_counts(generation_data) -> None:
    with (DATA_DIR / "planet-resource-generation.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source:
        assert sum(1 for _ in csv.DictReader(source)) == 7920

    assert len(generation_data) == 1444
    assert sum(len(planet.biomes) for planet in generation_data.values()) == 3210
    assert len(
        {
            definition.form_id
            for planet in generation_data.values()
            for biome in planet.biomes
            for definition in (biome.pndt_rsgd, biome.biom_rsgd)
            if definition is not None
        }
    ) == 32


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _first_generation_row() -> dict[str, str]:
    with (DATA_DIR / "planet-resource-generation.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source:
        return next(csv.DictReader(source))


def test_generation_schema_error_names_file_and_missing_column(tmp_path: Path) -> None:
    path = tmp_path / "generation.csv"
    path.write_text("PlanetFormID\n00000001\n", encoding="utf-8")

    with pytest.raises(DataValidationError) as error:
        load_generation_data(path)

    assert str(path) in str(error.value)
    assert "missing required column(s)" in str(error.value)
    assert "BiomeIndex" in str(error.value)


def test_generation_rejects_conflicting_planet_metadata(tmp_path: Path) -> None:
    first = _first_generation_row()
    second = dict(first, PlanetName="Contradiction")
    path = tmp_path / "generation.csv"
    _write_rows(path, [first, second])

    with pytest.raises(DataValidationError, match="conflicting PlanetName"):
        load_generation_data(path)


def test_generation_rejects_duplicate_rsgd_index(tmp_path: Path) -> None:
    row = _first_generation_row()
    path = tmp_path / "generation.csv"
    _write_rows(path, [row, dict(row)])

    with pytest.raises(DataValidationError, match="duplicate RSGDResourceIndex"):
        load_generation_data(path)
