import pytest

from starfield_resource_reproducer.domain import FormId
from starfield_resource_reproducer.prng import StarfieldRng


# The live trace displays nine decimal places.  Half of the final displayed unit
# is the tight tolerance that accommodates decimal rendering without weakening
# the binary32 compatibility assertion.
TRACE_ABS_TOLERANCE = 0.0000000005


def test_mimas_live_float_sequence(generation_data) -> None:
    mimas = generation_data[FormId("0005DEC0")]
    rng = StarfieldRng(mimas.resource_creation_seed)

    # PROVISIONAL prefix: the trace establishes that Common begins at raw draw 2,
    # but the current evidence does not identify the high-level operation that
    # consumed draw 1.  Preserve the known position without naming that operation.
    assert rng.next_uint32() == 253654728

    assert rng.next_float01() == pytest.approx(
        0.561107993, abs=TRACE_ABS_TOLERANCE
    )

    assert rng.next_float01() == pytest.approx(
        0.894184828, abs=TRACE_ABS_TOLERANCE
    )
    assert rng.next_scaled_index(1) == 0

    assert rng.next_float01() == pytest.approx(
        0.686025143, abs=TRACE_ABS_TOLERANCE
    )
    assert rng.next_scaled_index(1) == 0

    assert rng.next_float01() == pytest.approx(
        0.108883217, abs=TRACE_ABS_TOLERANCE
    )
    assert rng.next_scaled_index(1) == 0

    # The observed Mimas path has a fourth descendant level with the same proven
    # inclusion-then-index call shape, although no L4 float value was retained as
    # a numeric anchor in the brief.
    rng.next_float01()
    assert rng.next_scaled_index(1) == 0
    assert rng.draw_count == 10
