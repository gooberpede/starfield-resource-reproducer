from decimal import Decimal

import pytest

from starfield_resource_reproducer.domain import (
    Biome,
    FormId,
    GenerationRarity,
    RSGDDefinition,
    RSGDSource,
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("000057cb", "000057CB"),
        ("0x000057CB", "000057CB"),
        ("010026c5", "010026C5"),
    ],
)
def test_form_id_normalizes_canonical_text(source: str, expected: str) -> None:
    form_id = FormId(source)

    assert form_id.text == expected
    assert str(form_id) == expected
    assert form_id.numeric == int(expected, 16)


@pytest.mark.parametrize("value", ["57CB", "000057CG", "0x57CB", "0000057CB", ""])
def test_form_id_rejects_malformed_values(value: str) -> None:
    with pytest.raises(ValueError, match="8 hexadecimal digits"):
        FormId(value)


def test_biome_effective_rsgd_prefers_pndt() -> None:
    pndt = RSGDDefinition(
        RSGDSource.PNDT, FormId("00000001"), "Override", "Starfield.esm", ()
    )
    biom = RSGDDefinition(
        RSGDSource.BIOM, FormId("00000002"), "Default", "Starfield.esm", ()
    )
    biome = Biome(
        index=0,
        form_id=FormId("00000003"),
        editor_id="Biome",
        name="Biome",
        source_file="Starfield.esm",
        chance=Decimal("100"),
        unknown0_raw="00000000",
        unknown0_uint32=0,
        pndt_rsgd=pndt,
        biom_rsgd=biom,
    )

    assert biome.effective_rsgd is pndt
    assert GenerationRarity.SPECIAL.value == "Special"
    assert GenerationRarity.EVERYWHERE.value == "Everywhere"
