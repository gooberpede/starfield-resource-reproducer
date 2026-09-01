"""Starfield-compatible pseudo-random number generation.

Purpose:
    Provide the deterministic random interface used by later resource generation.
Responsibilities:
    Validate unsigned RSCS seeds, evolve classic 32-bit MT19937 state, perform
    recovered probability and bounded-choice conversions, and expose raw-output
    draw accounting.
Boundaries:
    This module does not shuffle biomes or make resource-generation decisions.
Evidence notes:
    MT19937 seeding and shared state are PROVEN. The probability conversion is
    a STRONG match for Mimas. Runtime traces PROVE that biome shuffle uses an
    integer rejection/modulo helper while descendant and guarded-family selection
    use semantically distinct float32 probability scaling operations. These
    mechanisms are deliberately not interchangeable.
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
    upper_bound: int | None = None
    probability_value: float | None = None
    scaled_value: float | None = None
    quotient_threshold: int | None = None
    quotient_random: int | None = None
    accepted: bool | None = None


class StarfieldRng:
    """Stateful RSCS-seeded MT19937 with Starfield-compatible conversions.

    ``draw_count`` counts extracted 32-bit MT19937 words, not public method
    calls. A rejection-sampled bounded integer call may consume multiple words.

    PROVEN: Starfield uses distinct bounded-random mechanisms for biome shuffle
    and descendant candidate selection. Do not consolidate
    ``next_bounded_integer`` and ``next_scaled_index`` without new runtime
    evidence: their arithmetic and raw-word consumption can differ.
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
        self._last_bounded_attempts: tuple[RngDraw, ...] = ()

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

    @property
    def last_bounded_attempts(self) -> tuple[RngDraw, ...]:
        """Return all attempts from the most recent integer bounded choice."""

        return self._last_bounded_attempts

    def next_uint32(self) -> int:
        """Extract the next tempered 32-bit MT19937 output."""

        raw_value = self._extract_uint32()
        self._last_bounded_attempts = ()
        self._record_draw(raw_value, "uint32", None)
        return raw_value

    def next_float01(self) -> float:
        """Return the recovered binary32 probability value for one raw word."""

        raw_value = self._extract_uint32()
        self._last_bounded_attempts = ()
        probability = _probability_from_raw(raw_value)
        self._record_draw(
            raw_value,
            "float01",
            probability,
            probability_value=probability,
        )
        return probability

    def next_bounded_integer(self, upper_bound: int) -> int:
        """Return the rejection-sampled integer choice used by biome shuffle.

        Each rejected and accepted attempt consumes one MT word. The runtime's
        traced 32-bit inequality accepts only when ``raw // upper_bound`` is
        strictly less than ``UINT32_MAX // upper_bound``; the accepted result is
        then ``raw % upper_bound``. Bound one is not short-circuited.
        """

        _validate_upper_bound(upper_bound)
        quotient_threshold = _UINT32_MAX // upper_bound
        attempts: list[RngDraw] = []
        while True:
            raw_value = self._extract_uint32()
            quotient_random = raw_value // upper_bound
            accepted = quotient_random < quotient_threshold
            converted = raw_value % upper_bound if accepted else None
            attempts.append(
                self._record_draw(
                    raw_value,
                    "bounded_integer_attempt",
                    converted,
                    upper_bound=upper_bound,
                    quotient_threshold=quotient_threshold,
                    quotient_random=quotient_random,
                    accepted=accepted,
                )
            )
            if accepted:
                self._last_bounded_attempts = tuple(attempts)
                # ``converted`` is an integer on the accepted branch; keeping
                # rejection represented as None makes every attempt auditable.
                assert converted is not None
                return converted

    def next_scaled_index(self, upper_bound: int) -> int:
        """Return the float32-scaled choice used for descendant candidates."""

        _validate_upper_bound(upper_bound)
        raw_value = self._extract_uint32()
        self._last_bounded_attempts = ()
        probability = _probability_from_raw(raw_value)
        scaled = _float32(probability * _float32(upper_bound))
        converted = int(scaled)
        self._record_draw(
            raw_value,
            "scaled_index",
            converted,
            upper_bound=upper_bound,
            probability_value=probability,
            scaled_value=scaled,
        )
        return converted

    def next_fallback_family_index(self, upper_bound: int) -> int:
        """Return the PROVEN float32-scaled guard-fallback family choice.

        This deliberately has its own semantic operation even though its binary32
        arithmetic is bit-compatible with descendant candidate selection. Bound
        one still consumes a raw MT word.
        """

        _validate_upper_bound(upper_bound)
        raw_value = self._extract_uint32()
        self._last_bounded_attempts = ()
        probability = _probability_from_raw(raw_value)
        scaled = _float32(probability * _float32(upper_bound))
        converted = int(scaled)
        self._record_draw(
            raw_value,
            "fallback_family_index",
            converted,
            upper_bound=upper_bound,
            probability_value=probability,
            scaled_value=scaled,
        )
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
        *,
        upper_bound: int | None = None,
        probability_value: float | None = None,
        scaled_value: float | None = None,
        quotient_threshold: int | None = None,
        quotient_random: int | None = None,
        accepted: bool | None = None,
    ) -> RngDraw:
        draw = RngDraw(
            draw_number=self._draw_count,
            raw_value=raw_value,
            operation=operation,
            converted_value=converted_value,
            upper_bound=upper_bound,
            probability_value=probability_value,
            scaled_value=scaled_value,
            quotient_threshold=quotient_threshold,
            quotient_random=quotient_random,
            accepted=accepted,
        )
        self._last_draw = draw
        return draw


def _probability_from_raw(raw_value: int) -> float:
    """Apply the recovered binary32 probability conversion to one MT word."""

    # STRONG: all four Mimas anchors equal this exact binary32 operation order.
    # Explicit rounding avoids Python double precision changing boundary cases.
    raw_float = _float32(raw_value)
    unit_value = _float32(raw_float * _UINT32_UNIT_FLOAT32)
    return _float32(unit_value * _OPEN_UPPER_SCALE_FLOAT32)


def _validate_upper_bound(upper_bound: int) -> None:
    """Validate bounds shared by the two semantically distinct choice paths."""

    if isinstance(upper_bound, bool) or not isinstance(upper_bound, int):
        raise TypeError("upper_bound must be an integer")
    if upper_bound <= 0:
        raise ValueError("upper_bound must be greater than zero")
    if upper_bound > _UINT32_MAX:
        raise ValueError("upper_bound must fit in an unsigned 32-bit integer")
