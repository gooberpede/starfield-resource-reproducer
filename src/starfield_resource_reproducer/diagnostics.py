"""Structured diagnostics for generation research.

Purpose:
    Represent and render auditable generation events without coupling generation
    or validation to a CLI.
Responsibilities:
    Name event kinds, retain operation-specific immutable fields, and attach the
    exact PRNG draw that caused a random decision.
Boundaries:
    This module does not evolve production RNG state or make selections. Its
    counterfactual helper advances an independent RNG solely for research.
Evidence notes:
    Event fields deliberately retain evidence-sensitive details such as bounds,
    ordered thresholds, and whether an empty selector consumed RNG.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from collections.abc import Iterable
from typing import Any

from .domain import FormId
from .prng import RngDraw, StarfieldRng


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
    PLANET_GENERATION_END = "PLANET_GENERATION_END"


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


@dataclass(frozen=True, slots=True)
class CounterfactualFloatDraw:
    """A diagnostics-only shifted float draw that never alters generation."""

    evidence_status: str
    original_draw_number: int
    extra_draws_before: int
    counterfactual_draw: RngDraw


def counterfactual_shifted_float(
    seed: int, original_draw_number: int, extra_draws_before: int
) -> CounterfactualFloatDraw:
    """Return the float at a shifted draw position using an independent RNG.

    COUNTERFACTUAL / NOT RUNTIME-PROVEN: this answers displacement questions
    only. It must never be called by production generation control flow.
    """

    if original_draw_number <= 0:
        raise ValueError("original_draw_number must be positive")
    if extra_draws_before < 0:
        raise ValueError("extra_draws_before must be non-negative")
    rng = StarfieldRng(seed)
    target = original_draw_number + extra_draws_before
    for _ in range(target - 1):
        rng.next_uint32()
    rng.next_float01()
    draw = rng.last_draw
    if draw is None:  # pragma: no cover - guarded by the float call above.
        raise AssertionError("counterfactual draw was not recorded")
    return CounterfactualFloatDraw(
        evidence_status="COUNTERFACTUAL / NOT RUNTIME-PROVEN",
        original_draw_number=original_draw_number,
        extra_draws_before=extra_draws_before,
        counterfactual_draw=draw,
    )


def format_diagnostic_timeline(
    planet_name: str,
    seed: int,
    events: Iterable[DiagnosticEvent],
) -> str:
    """Render structured events in stable generation order for investigation."""

    lines = [f"Planet {planet_name}", f"Seed {seed}"]
    for item in events:
        draw = item.rng_draw
        prefix = f"draw {draw.draw_number}" if draw is not None else "event"
        details: list[str] = []
        if draw is not None:
            details.extend((f"raw={draw.raw_value}", f"converted={draw.converted_value}"))
            if draw.upper_bound is not None:
                details.append(f"upper_bound={draw.upper_bound}")
            if draw.probability_value is not None:
                details.append(f"probability={draw.probability_value}")
            if draw.scaled_value is not None:
                details.append(f"scaled={draw.scaled_value}")
            if draw.accepted is not None:
                details.append(f"accepted={draw.accepted}")
        for name, value in item.fields:
            if name in {
                "biome_indices",
                "biome_name",
                "bound",
                "selected_position",
                "resulting_order",
                "rsgd_editor_id",
                "resolution_source",
                "rarity",
                "candidate_count",
                "candidates",
                "selected_resource",
                "selected_candidate",
                "roll",
                "threshold",
                "included",
                "draw_count_before",
                "draw_count_after",
                "inclusion_rng_consumed",
                "index_rng_consumed",
                "index_raw_equivalent_consumed",
                "structural_node_after",
                "evidence_status",
                "zero_candidate_policy",
                "raw_draws_consumed",
                "raw_values_consumed",
                "operation_types",
                "rng_mechanism",
                "attempts",
                "attempt_count",
                "rejected_attempt_count",
                "probability",
                "scaled",
                "selected_index",
            }:
                rendered = _timeline_value(value)
                details.append(f"{name}={rendered}")
        lines.append(f"{prefix} {item.kind.value}" + (f" {' '.join(details)}" if details else ""))
    return "\n".join(lines)


def _timeline_value(value: Any) -> Any:
    """Reduce domain-rich values to stable, readable timeline labels."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return tuple(_timeline_value(item) for item in value)
    name = getattr(value, "name", None)
    form_id = getattr(value, "form_id", None)
    if name is not None and form_id is not None:
        return f"{name}[{form_id}]"
    return value
