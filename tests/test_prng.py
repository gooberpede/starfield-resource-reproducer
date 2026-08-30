import pytest

from starfield_resource_reproducer.prng import StarfieldRng


@pytest.mark.parametrize("seed", [0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF])
def test_accepts_unsigned_uint32_seeds(seed: int) -> None:
    assert StarfieldRng(seed).seed == seed


@pytest.mark.parametrize("seed", [-1, 0x100000000])
def test_rejects_out_of_range_seeds(seed: int) -> None:
    with pytest.raises(ValueError, match="0xFFFFFFFF"):
        StarfieldRng(seed)


@pytest.mark.parametrize("seed", [True, 1.0, "1", None])
def test_rejects_non_integer_seeds(seed: object) -> None:
    with pytest.raises(TypeError, match="unsigned 32-bit integer"):
        StarfieldRng(seed)  # type: ignore[arg-type]


def test_classic_mt19937_reference_outputs() -> None:
    rng = StarfieldRng(5489)

    assert [rng.next_uint32() for _ in range(10)] == [
        3499211612,
        581869302,
        3890346734,
        3586334585,
        545404204,
        4161255391,
        3922919429,
        949333985,
        2715962298,
        1323567403,
    ]


def test_instances_are_deterministic_and_independent() -> None:
    first = StarfieldRng(2008989584)
    second = StarfieldRng(2008989584)

    assert [first.next_uint32() for _ in range(5)] == [
        second.next_uint32() for _ in range(5)
    ]
    first.next_uint32()
    assert first.draw_count == 6
    assert second.draw_count == 5


def test_draw_count_and_last_draw_describe_raw_outputs() -> None:
    rng = StarfieldRng(2008989584)

    assert rng.draw_count == 0
    assert rng.last_draw is None

    value = rng.next_float01()

    assert rng.draw_count == 1
    assert rng.last_draw is not None
    assert (
        rng.last_draw.draw_number,
        rng.last_draw.raw_value,
        rng.last_draw.operation,
        rng.last_draw.converted_value,
    ) == (1, 253654728, "float01", value)


def test_scaled_index_one_returns_zero_and_consumes_a_draw() -> None:
    rng = StarfieldRng(2008989584)

    assert rng.next_scaled_index(1) == 0
    assert rng.draw_count == 1
    assert rng.last_draw is not None
    assert rng.last_draw.raw_value == 253654728
    assert rng.last_draw.probability_value == 0.05905799940228462
    assert rng.last_draw.scaled_value == 0.05905799940228462


def test_bounded_integer_one_consumes_a_draw_without_short_circuiting() -> None:
    rng = StarfieldRng(2008989584)

    assert rng.next_bounded_integer(1) == 0
    assert rng.draw_count == 1
    assert len(rng.last_bounded_attempts) == 1
    assert rng.last_bounded_attempts[0].accepted is True


@pytest.mark.parametrize("method_name", ["next_bounded_integer", "next_scaled_index"])
@pytest.mark.parametrize("upper_bound", [0, -1])
def test_bounded_operations_reject_non_positive_bounds(
    method_name: str, upper_bound: int
) -> None:
    rng = StarfieldRng(1)

    with pytest.raises(ValueError, match="greater than zero"):
        getattr(rng, method_name)(upper_bound)
    assert rng.draw_count == 0


@pytest.mark.parametrize("method_name", ["next_bounded_integer", "next_scaled_index"])
@pytest.mark.parametrize("upper_bound", [True, 1.5, "2"])
def test_bounded_operations_reject_non_integer_bounds(
    method_name: str, upper_bound: object
) -> None:
    rng = StarfieldRng(1)

    with pytest.raises(TypeError, match="must be an integer"):
        getattr(rng, method_name)(upper_bound)
    assert rng.draw_count == 0


class _ScriptedRawRng(StarfieldRng):
    """Feed production conversion logic exact raw words for boundary tests."""

    def __init__(self, raw_values: tuple[int, ...]) -> None:
        super().__init__(0)
        self._scripted_values = iter(raw_values)

    def _extract_uint32(self) -> int:
        self._draw_count += 1
        return next(self._scripted_values)


def test_bounded_integer_rejects_then_consumes_a_second_raw_word() -> None:
    rng = _ScriptedRawRng((0xFFFFFFFF, 4))

    assert rng.next_bounded_integer(3) == 1
    assert rng.draw_count == 2
    assert [attempt.raw_value for attempt in rng.last_bounded_attempts] == [
        0xFFFFFFFF,
        4,
    ]
    assert [attempt.accepted for attempt in rng.last_bounded_attempts] == [
        False,
        True,
    ]
    assert (
        rng.last_bounded_attempts[0].quotient_random
        == rng.last_bounded_attempts[0].quotient_threshold
    )
    assert [attempt.quotient_threshold for attempt in rng.last_bounded_attempts] == [
        0xFFFFFFFF // 3,
        0xFFFFFFFF // 3,
    ]
    assert rng.last_draw is rng.last_bounded_attempts[-1]
