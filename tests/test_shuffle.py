from starfield_resource_reproducer.diagnostics import EventKind
from starfield_resource_reproducer.domain import FormId
from starfield_resource_reproducer.generation import shuffle_biomes
from starfield_resource_reproducer.prng import StarfieldRng


def test_shuffle_draw_counts_and_bounds_for_one_two_three_biomes(
    generation_data,
) -> None:
    kreet = generation_data[FormId("0003F59F")]

    expected = {
        1: (0, []),
        2: (1, [2]),
        3: (2, [2, 3]),
    }
    for biome_count, (draw_count, bounds) in expected.items():
        rng = StarfieldRng(kreet.resource_creation_seed)
        result = shuffle_biomes(kreet.biomes[:biome_count], rng)

        assert result.raw_draws_consumed == draw_count
        assert rng.draw_count == draw_count
        assert [event["bound"] for event in result.events] == bounds
        assert all(event.kind is EventKind.SHUFFLE_STEP for event in result.events)
        assert all(
            event.operation == "shuffle_bounded_integer" for event in result.events
        )


def test_kreet_shuffle_records_exact_observed_swaps_and_raw_draws(
    generation_data,
) -> None:
    kreet = generation_data[FormId("0003F59F")]
    result = shuffle_biomes(
        kreet.biomes, StarfieldRng(kreet.resource_creation_seed)
    )

    assert [biome.index for biome in result.biomes] == [2, 0, 1]
    assert [
        (event["swap_left"], event["swap_right"], event["resulting_order"])
        for event in result.events
    ] == [
        (0, 1, (1, 0, 2)),
        (0, 2, (2, 0, 1)),
    ]
    assert [event.rng_draw.draw_number for event in result.events] == [1, 2]
    assert [event.rng_draw.raw_value for event in result.events] == [
        3789400562,
        3546750279,
    ]
    assert [event["attempt_count"] for event in result.events] == [1, 1]
    assert [event["rejected_attempt_count"] for event in result.events] == [0, 0]
    assert [event["rng_mechanism"] for event in result.events] == [
        "integer_rejection_modulo",
        "integer_rejection_modulo",
    ]
    assert [
        tuple(attempt.accepted for attempt in event["attempts"])
        for event in result.events
    ] == [(True,), (True,)]
