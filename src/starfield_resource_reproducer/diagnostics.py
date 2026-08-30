"""Structured diagnostics for generation research.

Purpose:
    Represent auditable orchestration events without coupling generation to a CLI.
Responsibilities:
    Name event kinds, retain operation-specific immutable fields, and attach the
    exact PRNG draw that caused a random decision.
Boundaries:
    This module does not render events, evolve RNG state, or make selections.
Evidence notes:
    Event fields deliberately retain evidence-sensitive details such as bounds,
    ordered thresholds, and whether an empty selector consumed RNG.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .domain import FormId
from .prng import RngDraw


class EventKind(str, Enum):
    """Significant stages and decisions in partial planet orchestration."""

    RNG_SEEDED = "RNG_SEEDED"
    BIOME_LIST_INITIAL = "BIOME_LIST_INITIAL"
    SHUFFLE_STEP = "SHUFFLE_STEP"
    BIOME_LIST_SHUFFLED = "BIOME_LIST_SHUFFLED"
    EVERYWHERE_DISCOVERED = "EVERYWHERE_DISCOVERED"
    BIOME_BEGIN = "BIOME_BEGIN"
    RSGD_RESOLVED = "RSGD_RESOLVED"
    SPECIAL_PASS_BEGIN = "SPECIAL_PASS_BEGIN"
    SPECIAL_PASS_RESULT = "SPECIAL_PASS_RESULT"
    COMMON_PASS_BEGIN = "COMMON_PASS_BEGIN"
    COMMON_ROLL = "COMMON_ROLL"
    COMMON_SELECTED = "COMMON_SELECTED"
    FAMILY_BEGIN = "FAMILY_BEGIN"
    ROOT_EMITTED = "ROOT_EMITTED"
    DESCENDANT_LEVEL_BEGIN = "DESCENDANT_LEVEL_BEGIN"
    DESCENDANT_CANDIDATES = "DESCENDANT_CANDIDATES"
    DESCENDANT_INCLUSION_ROLL = "DESCENDANT_INCLUSION_ROLL"
    DESCENDANT_CANDIDATE_SELECTED = "DESCENDANT_CANDIDATE_SELECTED"
    DESCENDANT_EMITTED = "DESCENDANT_EMITTED"
    DESCENDANT_OMITTED = "DESCENDANT_OMITTED"
    FAMILY_END = "FAMILY_END"
    FAMILY_CACHE_HIT = "FAMILY_CACHE_HIT"
    BIOME_END = "BIOME_END"
    PLANET_ORCHESTRATION_END = "PLANET_ORCHESTRATION_END"


@dataclass(frozen=True, slots=True)
class WeightedCandidateDiagnostic:
    """One ordered selector candidate and its unnormalized cumulative threshold."""

    rsgd_index: int
    resource_form_id: FormId
    resource_name: str
    weight_percent: float
    cumulative_threshold: float


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    """One structured event with immutable named fields and optional RNG evidence."""

    kind: EventKind
    fields: tuple[tuple[str, Any], ...] = ()
    operation: str | None = None
    rng_draw: RngDraw | None = None

    def __getitem__(self, name: str) -> Any:
        """Return a named event field for concise diagnostic assertions."""

        for field_name, value in self.fields:
            if field_name == name:
                return value
        raise KeyError(name)

    def get(self, name: str, default: Any = None) -> Any:
        """Return a named field or ``default`` when the event omits it."""

        try:
            return self[name]
        except KeyError:
            return default


def event(
    kind: EventKind,
    *,
    operation: str | None = None,
    rng_draw: RngDraw | None = None,
    **fields: Any,
) -> DiagnosticEvent:
    """Build an event while preserving the caller's deliberate field order."""

    return DiagnosticEvent(kind, tuple(fields.items()), operation, rng_draw)
