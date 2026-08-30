import pytest

from starfield_resource_reproducer.prng import (
    StarfieldRng,
    _OPEN_UPPER_SCALE_FLOAT32,
    _UINT32_UNIT_FLOAT32,
    _float32,
)


def test_algorab_live_draw_reconstructs_scaled_binary32_index_zero() -> None:
    raw = 1826241303
    raw_float = _float32(raw)
    unit_value = _float32(raw_float * _UINT32_UNIT_FLOAT32)
    probability = _float32(unit_value * _OPEN_UPPER_SCALE_FLOAT32)
    scaled = _float32(probability * _float32(2))

    assert raw_float == 1826241280.0
    assert unit_value == 0.42520493268966675
    assert probability == 0.4252006709575653
    assert scaled == 0.8504013419151306
    assert int(scaled) == 0
    assert raw % 2 == 1


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Algorab disproves production modulo for descendants, while a generic "
        "scaled next_index breaks Kreet's proven shuffle"
    ),
)
def test_production_next_index_matches_algorab_live_descendant_result() -> None:
    rng = StarfieldRng(1654436101)
    for _ in range(17):
        rng.next_uint32()

    actual = rng.next_index(2)
    assert rng.draw_count == 18
    assert rng.last_draw is not None
    assert rng.last_draw.raw_value == 1826241303
    assert actual == 0
