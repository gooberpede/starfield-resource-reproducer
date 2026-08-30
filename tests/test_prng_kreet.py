from starfield_resource_reproducer.domain import FormId
from starfield_resource_reproducer.prng import StarfieldRng


def _recovered_shuffle_harness(
    values: list[int], rng: StarfieldRng
) -> list[tuple[int, int]]:
    """Exercise only the target/selection steps observed in the Kreet trace."""

    swaps: list[tuple[int, int]] = []
    for target_index in range(1, len(values)):
        selected_index = rng.next_index(target_index + 1)
        swaps.append((target_index, selected_index))
        values[target_index], values[selected_index] = (
            values[selected_index],
            values[target_index],
        )
    return swaps


def test_kreet_live_swap_choices(generation_data) -> None:
    kreet = generation_data[FormId("0003F59F")]
    order = [biome.index for biome in kreet.biomes]
    rng = StarfieldRng(kreet.resource_creation_seed)

    swaps = _recovered_shuffle_harness(order, rng)

    # The runtime described these symmetric swaps as 0<->1 then 0<->2.  The
    # harness records target first, so the same choices are (1, 0), (2, 0).
    assert swaps == [(1, 0), (2, 0)]
    assert order == [2, 0, 1]
    assert rng.draw_count == 2
