"""Worked-planet oracle comparison and evidence-qualified mismatch diagnosis.

Purpose: compare complete predictions with verified runtime output by FormID.
Responsibilities: compute exact/missing/unexpected membership and identify the
earliest plausible event region for a mismatch. Boundaries: oracle records never
enter generation and this module never changes RNG state or predicted resources.
Evidence notes: mismatch classifications are heuristic suspicions, not proven
root causes; event evidence remains authoritative over these labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .diagnostics import DiagnosticEvent, EventKind
from .domain import CanonicalBodyResources, CanonicalResource, FormId, ResourceRef
from .generation import PlanetGenerationResult


class MismatchClassification(str, Enum):
    """Evidence-qualified labels for the first plausible mismatch region."""

    DESCENDANT_INCLUSION_MISMATCH = "DESCENDANT_INCLUSION_MISMATCH"
    RNG_CONSUMPTION_SUSPECT = "RNG_CONSUMPTION_SUSPECT"
    EVERYWHERE_MODEL_SUSPECT = "EVERYWHERE_MODEL_SUSPECT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PlanetValidationResult:
    """FormID-based comparison kept separate from generation output."""

    planet_form_id: FormId
    planet_name: str
    predicted_form_ids: frozenset[FormId]
    expected_form_ids: frozenset[FormId]
    missing_form_ids: frozenset[FormId]
    unexpected_form_ids: frozenset[FormId]
    exact_match: bool
    predicted_resources: tuple[ResourceRef, ...]
    expected_resources: tuple[CanonicalResource, ...]
    suspected_cause: MismatchClassification | None
    first_plausible_divergence: DiagnosticEvent | None


def compare_to_oracle(
    generation_result: PlanetGenerationResult,
    canonical_body: CanonicalBodyResources,
) -> PlanetValidationResult:
    """Compare one independent prediction with one canonical body by FormID."""

    if generation_result.planet.form_id != canonical_body.planet_form_id:
        raise ValueError("generation and canonical results describe different planets")
    predicted = generation_result.predicted_form_ids
    expected = canonical_body.inorganic_resources
    missing = expected - predicted
    unexpected = predicted - expected
    cause, divergence = _classify_mismatch(generation_result, missing, unexpected)
    return PlanetValidationResult(
        planet_form_id=generation_result.planet.form_id,
        planet_name=generation_result.planet.name,
        predicted_form_ids=predicted,
        expected_form_ids=expected,
        missing_form_ids=frozenset(missing),
        unexpected_form_ids=frozenset(unexpected),
        exact_match=not missing and not unexpected,
        predicted_resources=generation_result.predicted_resources,
        expected_resources=canonical_body.inorganic_resource_records,
        suspected_cause=cause,
        first_plausible_divergence=divergence,
    )


def _classify_mismatch(
    result: PlanetGenerationResult,
    missing: frozenset[FormId] | set[FormId],
    unexpected: frozenset[FormId] | set[FormId],
) -> tuple[MismatchClassification | None, DiagnosticEvent | None]:
    if not missing and not unexpected:
        return None, None

    zero_events: list[DiagnosticEvent] = []
    for item in result.events:
        if item.kind is EventKind.DESCENDANT_OMITTED and item.get("reason") == "no_candidates":
            zero_events.append(item)
        if item.kind is not EventKind.DESCENDANT_CANDIDATES:
            continue
        candidate_ids = {candidate.form_id for candidate in item["candidates"]}
        if candidate_ids & set(missing):
            if zero_events:
                return MismatchClassification.RNG_CONSUMPTION_SUSPECT, zero_events[0]
            return MismatchClassification.DESCENDANT_INCLUSION_MISMATCH, item

    everywhere_ids = {resource.form_id for resource in result.everywhere_resources}
    if missing & everywhere_ids or unexpected & everywhere_ids:
        return MismatchClassification.EVERYWHERE_MODEL_SUSPECT, None
    return MismatchClassification.UNKNOWN, None
