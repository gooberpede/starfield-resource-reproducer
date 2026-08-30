"""Starfield-compatible pseudo-random number generation.

Purpose:
    Provide the deterministic random interface used by later resource generation.
Responsibilities:
    Validate unsigned RSCS seeds, evolve classic 32-bit MT19937 state, perform
    recovered float/index conversions, and expose raw-output draw accounting.
Boundaries:
    This module does not shuffle biomes or make resource-generation decisions.
Evidence notes:
    MT19937 seeding and shared state are PROVEN.  The explicit conversions are
    STRONG matches for the Mimas and Kreet live anchors; equivalent bounded
    constructions have not all been excluded by the available traces.
"""

from dataclasses import dataclass
from struct import pack, unpack


_UINT32_MAX = 0xFFFFFFFF
_STATE_SIZE = 624
_STATE_OFFSET = 397
_MATRIX_A = 0x9908B0DF
_UPPER_MASK = 0x80000000
_LOWER_MASK = 0x7FFFFFFF


def _float32(value: int | float) -> float:
    """Round a Python numeric value to an IEEE-754 binary32 value."""

    return unpack("<f", pack("<f", value))[0]


_UINT32_UNIT_FLOAT32 = _float32(1.0 / (1 << 32))
_OPEN_UPPER_SCALE_FLOAT32 = _float32(0.99999)


@dataclass(frozen=True, slots=True)
class RngDraw:
    """Describe one extracted raw MT19937 word and its public conversion."""

    draw_number: int
    raw_value: int
    operation: str
    converted_value: float | int | None


class StarfieldRng:
    """Stateful RSCS-seeded MT19937 with Starfield-compatible conversions.

    ``draw_count`` counts extracted 32-bit MT19937 words, not public method
    calls.  Every current public draw operation consumes exactly one word.
    """

    def __init__(self, seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise TypeError("seed must be an unsigned 32-bit integer")
        if not 0 <= seed <= _UINT32_MAX:
            raise ValueError("seed must be between 0 and 0xFFFFFFFF inclusive")

        self._seed = seed
        self._state = [0] * _STATE_SIZE
        self._state[0] = seed
        for index in range(1, _STATE_SIZE):
            previous = self._state[index - 1]
            self._state[index] = (
                1812433253 * (previous ^ (previous >> 30)) + index
            ) & _UINT32_MAX
        self._state_index = _STATE_SIZE
        self._draw_count = 0
        self._last_draw: RngDraw | None = None

    @property
    def seed(self) -> int:
        """Return the original unsigned RSCS seed."""

        return self._seed

    @property
    def draw_count(self) -> int:
        """Return the number of raw 32-bit outputs extracted so far."""

        return self._draw_count

    @property
    def last_draw(self) -> RngDraw | None:
        """Return diagnostics for the most recent raw extraction, if any."""

        return self._last_draw

    def next_uint32(self) -> int:
        """Extract the next tempered 32-bit MT19937 output."""

        raw_value = self._extract_uint32()
        self._record_draw(raw_value, "uint32", None)
        return raw_value

    def next_float01(self) -> float:
        """Return the recovered binary32 probability value for one raw word."""

        raw_value = self._extract_uint32()

        # STRONG: all four Mimas anchors equal this binary32 operation sequence.
        # Keeping each rounding step explicit avoids silently substituting Python's
        # double-precision random conversion, which produces different values.
        raw_float = _float32(raw_value)
        unit_value = _float32(raw_float * _UINT32_UNIT_FLOAT32)
        converted = _float32(unit_value * _OPEN_UPPER_SCALE_FLOAT32)

        self._record_draw(raw_value, "float01", converted)
        return converted

    def next_index(self, upper_bound: int) -> int:
        """Return a bounded index while consuming exactly one raw output."""

        if isinstance(upper_bound, bool) or not isinstance(upper_bound, int):
            raise TypeError("upper_bound must be an integer")
        if upper_bound <= 0:
            raise ValueError("upper_bound must be greater than zero")

        raw_value = self._extract_uint32()

        # STRONG: raw modulo reproduces both Kreet live swap choices.  The trace
        # does not yet distinguish this from every equivalent construction.
        # PROVEN: upper_bound == 1 still consumes this raw draw; do not shortcut.
        converted = raw_value % upper_bound

        self._record_draw(raw_value, "index", converted)
        return converted

    def _extract_uint32(self) -> int:
        if self._state_index >= _STATE_SIZE:
            self._twist()

        value = self._state[self._state_index]
        self._state_index += 1

        value ^= value >> 11
        value ^= (value << 7) & 0x9D2C5680
        value ^= (value << 15) & 0xEFC60000
        value ^= value >> 18

        self._draw_count += 1
        return value & _UINT32_MAX

    def _twist(self) -> None:
        for index in range(_STATE_SIZE):
            combined = (self._state[index] & _UPPER_MASK) | (
                self._state[(index + 1) % _STATE_SIZE] & _LOWER_MASK
            )
            twisted = self._state[(index + _STATE_OFFSET) % _STATE_SIZE] ^ (
                combined >> 1
            )
            if combined & 1:
                twisted ^= _MATRIX_A
            self._state[index] = twisted & _UINT32_MAX
        self._state_index = 0

    def _record_draw(
        self,
        raw_value: int,
        operation: str,
        converted_value: float | int | None,
    ) -> None:
        self._last_draw = RngDraw(
            draw_number=self._draw_count,
            raw_value=raw_value,
            operation=operation,
            converted_value=converted_value,
        )
