"""Canonical validation and full-corpus mismatch analysis.

Purpose: compare oracle-independent predictions with verified inorganic runtime
output. Responsibilities include single-planet comparison, corpus coverage,
deterministic structural classification, aggregate metrics, and CSV export.
Validation never supplies oracle information to generation or repairs a
prediction. Final-set equality is empirical agreement, not proof of trace-exact
RNG behavior; mismatch signatures are clustering aids, not causal conclusions.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from time import perf_counter

from .diagnostics import DiagnosticEvent, EventKind
from .domain import (
    CanonicalBodyResources,
    CanonicalResource,
    FormId,
    GenerationRarity,
    IRESNode,
    Planet,
    ProjectData,
    ResourceRef,
)
from .generation import PlanetGenerationResult, PlanetResourceState, generate_planet


class MismatchClassification(str, Enum):
    """Legacy evidence-qualified labels for a first plausible event region."""

    DESCENDANT_INCLUSION_MISMATCH = "DESCENDANT_INCLUSION_MISMATCH"
    RNG_CONSUMPTION_SUSPECT = "RNG_CONSUMPTION_SUSPECT"
    EVERYWHERE_MODEL_SUSPECT = "EVERYWHERE_MODEL_SUSPECT"
    UNKNOWN = "UNKNOWN"


class MatchStatus(str, Enum):
    """Deterministic high-level final-set or corpus-coverage status."""

    EXACT = "EXACT"
    MISSING_ONLY = "MISSING_ONLY"
    UNEXPECTED_ONLY = "UNEXPECTED_ONLY"
    MISSING_AND_UNEXPECTED = "MISSING_AND_UNEXPECTED"
    DATASET_COVERAGE_MISMATCH = "DATASET_COVERAGE_MISMATCH"
    GENERATION_ERROR = "GENERATION_ERROR"


class MismatchSignature(str, Enum):
    """Structural clustering labels that deliberately do not assert a cause."""

    EXACT = "EXACT"
    RSCS_ZERO_FALLBACK = "RSCS_ZERO_FALLBACK"
    EVERYWHERE_ONLY_DISCREPANCY = "EVERYWHERE_ONLY_DISCREPANCY"
    SPECIAL_RESOURCE_DISCREPANCY = "SPECIAL_RESOURCE_DISCREPANCY"
    MISSING_ROOT = "MISSING_ROOT"
    UNEXPECTED_ROOT = "UNEXPECTED_ROOT"
    SAME_FAMILY_SUBSTITUTION = "SAME_FAMILY_SUBSTITUTION"
    ONE_MISSING_DESCENDANT = "ONE_MISSING_DESCENDANT"
    ONE_UNEXPECTED_DESCENDANT = "ONE_UNEXPECTED_DESCENDANT"
    MULTIPLE_FAMILY_DIVERGENCE = "MULTIPLE_FAMILY_DIVERGENCE"
    MISSING_ONLY_OTHER = "MISSING_ONLY_OTHER"
    UNEXPECTED_ONLY_OTHER = "UNEXPECTED_ONLY_OTHER"
    MIXED_OTHER = "MIXED_OTHER"
    GENERATION_ERROR = "GENERATION_ERROR"
    GENERATION_ONLY = "GENERATION_ONLY"
    ORACLE_ONLY = "ORACLE_ONLY"


@dataclass(frozen=True, slots=True)
class FamilyMismatchAnalysis:
    """Mechanically derived Common-root relationships for divergent resources."""

    missing_family_roots: tuple[FormId, ...]
    unexpected_family_roots: tuple[FormId, ...]
    missing_descendants_by_root: tuple[tuple[FormId, tuple[FormId, ...]], ...]
    unexpected_descendants_by_root: tuple[tuple[FormId, tuple[FormId, ...]], ...]


@dataclass(frozen=True, slots=True)
class PlanetValidationResult:
    """Structured final-set comparison and diagnostic dimensions for one planet."""

    planet_form_id: FormId
    planet_editor_id: str
    planet_name: str
    system_name: str
    resource_creation_seed: int
    biome_count: int
    predicted_form_ids: frozenset[FormId]
    atmospheric_form_ids: frozenset[FormId]
    final_player_facing_form_ids: frozenset[FormId]
    expected_form_ids: frozenset[FormId]
    missing_form_ids: frozenset[FormId]
    unexpected_form_ids: frozenset[FormId]
    exact_match: bool
    match_status: MatchStatus
    mismatch_signature: MismatchSignature
    predicted_resources: tuple[ResourceRef, ...]
    atmospheric_resources: tuple[ResourceRef, ...]
    final_player_facing_resources: tuple[ResourceRef, ...]
    expected_resources: tuple[CanonicalResource, ...]
    shuffled_biome_indices: tuple[int, ...]
    shuffled_biome_names: tuple[str, ...]
    final_draw_count: int | None
    selected_common_roots: tuple[FormId, ...]
    cache_hit_roots: tuple[FormId, ...]
    effective_rsgd_form_ids: tuple[FormId, ...]
    effective_rsgd_editor_ids: tuple[str, ...]
    family_analysis: FamilyMismatchAnalysis
    has_pndt_override: bool
    has_cache_reuse: bool
    rscs_zero: bool
    has_atmospheric: bool
    has_everywhere: bool
    has_special: bool
    capacity_reached: bool
    first_divergent_family_biome_index: int | None
    suspected_cause: MismatchClassification | None
    first_plausible_divergence: DiagnosticEvent | None
    events: tuple[DiagnosticEvent, ...]
    generation_error_type: str | None = None
    generation_error_message: str | None = None


@dataclass(frozen=True, slots=True)
class CoverageMismatch:
    """A body present on only one side of the generation/oracle population."""

    planet_form_id: FormId
    source: str
    planet_editor_id: str
    planet_name: str
    signature: MismatchSignature
    match_status: MatchStatus = MatchStatus.DATASET_COVERAGE_MISMATCH


@dataclass(frozen=True, slots=True)
class ValidationAggregates:
    """Stable aggregate metrics over the intersection validation results."""

    total_validation_planets: int
    exact_matches: int
    mismatches: int
    exact_match_percentage: float
    missing_only_planets: int
    unexpected_only_planets: int
    missing_and_unexpected_planets: int
    generation_errors: int
    total_missing_resource_occurrences: int
    total_unexpected_resource_occurrences: int
    distinct_missing_form_ids: tuple[FormId, ...]
    distinct_unexpected_form_ids: tuple[FormId, ...]
    mismatch_status_counts: tuple[tuple[str, int], ...]
    mismatch_signature_counts: tuple[tuple[str, int], ...]
    mismatches_by_biome_count: tuple[tuple[str, int], ...]
    mismatches_by_effective_rsgd: tuple[tuple[str, int], ...]
    mismatches_by_selected_common_root: tuple[tuple[str, int], ...]
    pndt_override_mismatches: int
    cache_reuse_mismatches: int
    rscs_zero_planets: int
    rscs_zero_mismatches: int
    mismatches_by_predicted_count: tuple[tuple[str, int], ...]
    atmospheric_mismatches: int
    everywhere_mismatches: int
    special_mismatches: int
    single_biome_mismatches: int
    multi_biome_mismatches: int
    capacity_reached_mismatches: int
    provenance_validation_available: bool


@dataclass(frozen=True, slots=True)
class FullValidationResult:
    """Complete, deterministically ordered corpus validation outcome."""

    generation_planet_count: int
    oracle_inorganic_planet_count: int
    intersection_count: int
    generation_only: tuple[CoverageMismatch, ...]
    oracle_only: tuple[CoverageMismatch, ...]
    planet_results: tuple[PlanetValidationResult, ...]
    aggregates: ValidationAggregates
    runtime_seconds: float = field(compare=False)

    @property
    def mismatches(self) -> tuple[PlanetValidationResult, ...]:
        """Return all non-exact intersection results, including generation errors."""

        return tuple(result for result in self.planet_results if not result.exact_match)


_EMPTY_FAMILY_ANALYSIS = FamilyMismatchAnalysis((), (), (), ())


def compare_to_oracle(
    generation_result: PlanetGenerationResult,
    canonical_body: CanonicalBodyResources,
    ires_nodes: Mapping[FormId, IRESNode] | None = None,
) -> PlanetValidationResult:
    """Compare one independent prediction with one canonical body by FormID."""

    if generation_result.planet.form_id != canonical_body.planet_form_id:
        raise ValueError("generation and canonical results describe different planets")
    # The runtime oracle omits at least some ATMO-only resources. Compare its
    # still-OPEN contract with the RSGD/CK-visible channel, while separately
    # retaining both ATMO and final player-facing union channels.
    predicted = generation_result.rsgd_form_ids
    expected = canonical_body.inorganic_resources
    missing = frozenset(expected - predicted)
    unexpected = frozenset(predicted - expected)
    status = _match_status(missing, unexpected)
    family_analysis = (
        _analyze_families(missing, unexpected, ires_nodes)
        if ires_nodes is not None
        else _EMPTY_FAMILY_ANALYSIS
    )
    signature = _mismatch_signature(
        generation_result.planet,
        status,
        missing,
        unexpected,
        family_analysis,
        ires_nodes,
    )
    cause, divergence = _classify_mismatch(generation_result, missing, unexpected)
    selected_roots = tuple(
        biome.orchestration.common_root.form_id
        for biome in generation_result.biome_results
        if biome.orchestration.common_root is not None
    )
    cache_roots = tuple(
        biome.family_access.family.root.form_id
        for biome in generation_result.biome_results
        if biome.family_access is not None and biome.family_access.cache_hit
    )
    return PlanetValidationResult(
        planet_form_id=generation_result.planet.form_id,
        planet_editor_id=generation_result.planet.editor_id,
        planet_name=generation_result.planet.name,
        system_name=canonical_body.system_name,
        resource_creation_seed=generation_result.planet.resource_creation_seed,
        biome_count=len(generation_result.planet.biomes),
        predicted_form_ids=predicted,
        expected_form_ids=expected,
        missing_form_ids=missing,
        unexpected_form_ids=unexpected,
        exact_match=status is MatchStatus.EXACT,
        match_status=status,
        mismatch_signature=signature,
        atmospheric_form_ids=frozenset(
            resource.form_id for resource in generation_result.atmospheric_resources
        ),
        final_player_facing_form_ids=generation_result.predicted_form_ids,
        predicted_resources=generation_result.rsgd_resources,
        atmospheric_resources=generation_result.atmospheric_resources,
        final_player_facing_resources=generation_result.predicted_resources,
        expected_resources=canonical_body.inorganic_resource_records,
        shuffled_biome_indices=tuple(
            biome.index for biome in generation_result.shuffled_biomes
        ),
        shuffled_biome_names=tuple(
            biome.name for biome in generation_result.shuffled_biomes
        ),
        final_draw_count=generation_result.final_draw_count,
        selected_common_roots=selected_roots,
        cache_hit_roots=cache_roots,
        effective_rsgd_form_ids=tuple(
            biome.orchestration.effective_rsgd.form_id
            for biome in generation_result.biome_results
        ),
        effective_rsgd_editor_ids=tuple(
            biome.orchestration.effective_rsgd.editor_id
            for biome in generation_result.biome_results
        ),
        family_analysis=family_analysis,
        has_pndt_override=_has_pndt_override(generation_result.planet),
        has_cache_reuse=bool(cache_roots),
        rscs_zero=generation_result.planet.resource_creation_seed == 0,
        has_atmospheric=bool(generation_result.atmospheric_resources),
        has_everywhere=bool(generation_result.everywhere_resources),
        has_special=bool(generation_result.special_resources),
        capacity_reached=(
            len(generation_result.occupied_resource_ids) >= PlanetResourceState.CAPACITY
        ),
        first_divergent_family_biome_index=_first_divergent_family_biome(
            generation_result, family_analysis
        ),
        suspected_cause=cause,
        first_plausible_divergence=divergence,
        events=generation_result.events,
    )


def validate_all_planets(
    project_data: ProjectData,
    *,
    generator: Callable[
        [Planet, Mapping[FormId, IRESNode]], PlanetGenerationResult
    ] = generate_planet,
) -> FullValidationResult:
    """Validate every generation/oracle-inorganic intersection planet.

    The oracle is passed only to comparison after generation completes. Per-body
    exceptions become ``GENERATION_ERROR`` results so one malformed or unsupported
    body cannot hide the rest of the corpus.
    """

    started = perf_counter()
    generation_ids = set(project_data.planets)
    oracle_ids = {
        form_id
        for form_id, body in project_data.oracle.items()
        if body.inorganic_resources
    }
    intersection = sorted(generation_ids & oracle_ids)
    generation_only_ids = sorted(generation_ids - oracle_ids)
    oracle_only_ids = sorted(oracle_ids - generation_ids)

    results: list[PlanetValidationResult] = []
    for form_id in intersection:
        planet = project_data.planets[form_id]
        canonical = project_data.oracle[form_id]
        try:
            # Oracle rows are deliberately absent from this call so they cannot
            # choose, reorder, or repair generation branches.
            if generator is generate_planet:
                generation = generate_planet(
                    planet,
                    project_data.ires_nodes,
                    atmospheric_records=project_data.atmospheric_resources.get(form_id, ()),
                )
            else:
                # Preserve the injectable two-argument test/research generator API.
                generation = generator(planet, project_data.ires_nodes)
            results.append(compare_to_oracle(generation, canonical, project_data.ires_nodes))
        except Exception as error:  # Corpus analysis must retain subsequent bodies.
            results.append(_generation_error_result(planet, canonical, error))

    generation_only = tuple(
        CoverageMismatch(
            form_id,
            "generation_only",
            project_data.planets[form_id].editor_id,
            project_data.planets[form_id].name,
            MismatchSignature.GENERATION_ONLY,
        )
        for form_id in generation_only_ids
    )
    oracle_only = tuple(
        CoverageMismatch(
            form_id,
            "oracle_only",
            project_data.oracle[form_id].planet_editor_id,
            project_data.oracle[form_id].planet_name,
            MismatchSignature.ORACLE_ONLY,
        )
        for form_id in oracle_only_ids
    )
    ordered_results = tuple(results)
    return FullValidationResult(
        generation_planet_count=len(generation_ids),
        oracle_inorganic_planet_count=len(oracle_ids),
        intersection_count=len(intersection),
        generation_only=generation_only,
        oracle_only=oracle_only,
        planet_results=ordered_results,
        aggregates=_aggregate(ordered_results),
        runtime_seconds=perf_counter() - started,
    )


_CSV_COLUMNS = (
    "PlanetFormID", "PlanetEditorID", "PlanetName", "SystemName", "RSCS", "BiomeCount",
    "FinalDrawCount", "MatchStatus", "PredictedFormIDs", "AtmosphericFormIDs",
    "FinalPlayerFacingFormIDs", "ExpectedFormIDs",
    "PredictedCount", "ExpectedCount", "MissingFormIDs", "MissingNames",
    "UnexpectedFormIDs", "UnexpectedNames", "SelectedCommonRoots",
    "CacheHitRoots", "EffectiveRSGDs", "MismatchSignature",
    "ShuffledBiomeOrder", "MissingFamilyRoots", "UnexpectedFamilyRoots",
    "PNDTOverride", "CacheReuse", "RSCSZero", "FirstDivergentFamilyBiomeIndex",
    "GenerationError",
)


def write_mismatch_csv(result: FullValidationResult, path: Path) -> None:
    """Write stable non-exact and coverage rows to a UTF-8 CSV report."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=_CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for planet_result in result.mismatches:
            writer.writerow(mismatch_csv_row(planet_result))
        for coverage in (*result.generation_only, *result.oracle_only):
            writer.writerow(_coverage_csv_row(coverage))


def mismatch_csv_row(result: PlanetValidationResult) -> dict[str, str]:
    """Serialize one structured planet result without nondeterministic set order."""

    predicted_names = {resource.form_id: resource.name for resource in result.predicted_resources}
    expected_names = {
        resource.resource_form_id: resource.resource_name
        for resource in result.expected_resources
    }
    return {
        "PlanetFormID": str(result.planet_form_id),
        "PlanetEditorID": result.planet_editor_id,
        "PlanetName": result.planet_name,
        "SystemName": result.system_name,
        "RSCS": str(result.resource_creation_seed),
        "BiomeCount": str(result.biome_count),
        "FinalDrawCount": "" if result.final_draw_count is None else str(result.final_draw_count),
        "MatchStatus": result.match_status.value,
        "PredictedFormIDs": _join_ids(result.predicted_form_ids),
        "AtmosphericFormIDs": _join_ids(result.atmospheric_form_ids),
        "FinalPlayerFacingFormIDs": _join_ids(result.final_player_facing_form_ids),
        "ExpectedFormIDs": _join_ids(result.expected_form_ids),
        "PredictedCount": str(len(result.predicted_form_ids)),
        "ExpectedCount": str(len(result.expected_form_ids)),
        "MissingFormIDs": _join_ids(result.missing_form_ids),
        "MissingNames": _join_names(result.missing_form_ids, expected_names),
        "UnexpectedFormIDs": _join_ids(result.unexpected_form_ids),
        "UnexpectedNames": _join_names(result.unexpected_form_ids, predicted_names),
        "SelectedCommonRoots": _join_ids_in_order(result.selected_common_roots),
        "CacheHitRoots": _join_ids_in_order(result.cache_hit_roots),
        "EffectiveRSGDs": ";".join(result.effective_rsgd_editor_ids),
        "MismatchSignature": result.mismatch_signature.value,
        "ShuffledBiomeOrder": ";".join(str(index) for index in result.shuffled_biome_indices),
        "MissingFamilyRoots": _join_ids(result.family_analysis.missing_family_roots),
        "UnexpectedFamilyRoots": _join_ids(result.family_analysis.unexpected_family_roots),
        "PNDTOverride": str(result.has_pndt_override).lower(),
        "CacheReuse": str(result.has_cache_reuse).lower(),
        "RSCSZero": str(result.rscs_zero).lower(),
        "FirstDivergentFamilyBiomeIndex": (
            "" if result.first_divergent_family_biome_index is None
            else str(result.first_divergent_family_biome_index)
        ),
        "GenerationError": (
            "" if result.generation_error_type is None
            else f"{result.generation_error_type}: {result.generation_error_message}"
        ),
    }


def format_full_validation_summary(result: FullValidationResult) -> str:
    """Render a compact deterministic console summary for the batch CLI."""

    aggregate = result.aggregates
    return "\n".join(
        (
            f"Generation planets: {result.generation_planet_count}",
            f"Oracle inorganic planets: {result.oracle_inorganic_planet_count}",
            f"Validation intersection: {result.intersection_count}",
            f"Generation-only: {len(result.generation_only)}",
            f"Oracle-only: {len(result.oracle_only)}",
            f"Exact matches: {aggregate.exact_matches}",
            f"Mismatches: {aggregate.mismatches}",
            f"Exact-match percentage: {aggregate.exact_match_percentage:.2f}%",
            f"Prediction-only mismatches: {aggregate.unexpected_only_planets}",
            f"Oracle-only mismatches: {aggregate.missing_only_planets}",
            f"Both-sides mismatches: {aggregate.missing_and_unexpected_planets}",
            f"Generation errors: {aggregate.generation_errors}",
            f"Missing occurrences: {aggregate.total_missing_resource_occurrences}",
            f"Unexpected occurrences: {aggregate.total_unexpected_resource_occurrences}",
            f"Residuals with atmosphere: {aggregate.atmospheric_mismatches}",
            f"Residuals with Everywhere: {aggregate.everywhere_mismatches}",
            f"Residuals with Special: {aggregate.special_mismatches}",
            f"Residuals at capacity: {aggregate.capacity_reached_mismatches}",
            "Full-corpus provenance comparison: not measurable "
            "(no independent expected-provenance oracle)",
            f"Runtime seconds: {result.runtime_seconds:.3f}",
        )
    )


def _match_status(missing: frozenset[FormId], unexpected: frozenset[FormId]) -> MatchStatus:
    if not missing and not unexpected:
        return MatchStatus.EXACT
    if missing and unexpected:
        return MatchStatus.MISSING_AND_UNEXPECTED
    if missing:
        return MatchStatus.MISSING_ONLY
    return MatchStatus.UNEXPECTED_ONLY


def _family_roots_by_resource(
    ires_nodes: Mapping[FormId, IRESNode],
) -> dict[FormId, tuple[FormId, ...]]:
    roots_by_resource: dict[FormId, set[FormId]] = defaultdict(set)
    for root in sorted(
        (node for node in ires_nodes.values() if node.rarity is GenerationRarity.COMMON),
        key=lambda node: node.form_id,
    ):
        pending = [root.form_id]
        visited: set[FormId] = set()
        while pending:
            form_id = pending.pop()
            if form_id in visited:
                continue
            visited.add(form_id)
            roots_by_resource[form_id].add(root.form_id)
            node = ires_nodes.get(form_id)
            if node is not None:
                pending.extend(reversed([child.form_id for child in node.children]))
    return {form_id: tuple(sorted(roots)) for form_id, roots in roots_by_resource.items()}


def _analyze_families(
    missing: frozenset[FormId],
    unexpected: frozenset[FormId],
    ires_nodes: Mapping[FormId, IRESNode],
) -> FamilyMismatchAnalysis:
    roots_by_resource = _family_roots_by_resource(ires_nodes)
    missing_by_root = _resources_by_root(missing, roots_by_resource)
    unexpected_by_root = _resources_by_root(unexpected, roots_by_resource)
    return FamilyMismatchAnalysis(
        missing_family_roots=tuple(sorted(missing_by_root)),
        unexpected_family_roots=tuple(sorted(unexpected_by_root)),
        missing_descendants_by_root=tuple(
            (root, tuple(sorted(resources - {root})))
            for root, resources in sorted(missing_by_root.items()) if resources - {root}
        ),
        unexpected_descendants_by_root=tuple(
            (root, tuple(sorted(resources - {root})))
            for root, resources in sorted(unexpected_by_root.items()) if resources - {root}
        ),
    )


def _resources_by_root(
    resources: Iterable[FormId], roots_by_resource: Mapping[FormId, tuple[FormId, ...]]
) -> dict[FormId, set[FormId]]:
    result: dict[FormId, set[FormId]] = defaultdict(set)
    for resource in resources:
        for root in roots_by_resource.get(resource, ()):
            result[root].add(resource)
    return dict(result)


def _mismatch_signature(
    planet: Planet,
    status: MatchStatus,
    missing: frozenset[FormId],
    unexpected: frozenset[FormId],
    family: FamilyMismatchAnalysis,
    ires_nodes: Mapping[FormId, IRESNode] | None,
) -> MismatchSignature:
    if status is MatchStatus.EXACT:
        return MismatchSignature.EXACT
    if planet.resource_creation_seed == 0:
        return MismatchSignature.RSCS_ZERO_FALLBACK
    rarity_by_id = (
        {form_id: node.rarity for form_id, node in ires_nodes.items()}
        if ires_nodes is not None else {}
    )
    divergent = missing | unexpected
    if divergent and all(rarity_by_id.get(item) is GenerationRarity.EVERYWHERE for item in divergent):
        return MismatchSignature.EVERYWHERE_ONLY_DISCREPANCY
    if divergent and all(rarity_by_id.get(item) is GenerationRarity.SPECIAL for item in divergent):
        return MismatchSignature.SPECIAL_RESOURCE_DISCREPANCY
    if any(rarity_by_id.get(item) is GenerationRarity.COMMON for item in missing):
        return MismatchSignature.MISSING_ROOT
    if any(rarity_by_id.get(item) is GenerationRarity.COMMON for item in unexpected):
        return MismatchSignature.UNEXPECTED_ROOT
    missing_roots = set(family.missing_family_roots)
    unexpected_roots = set(family.unexpected_family_roots)
    if missing and unexpected and missing_roots & unexpected_roots:
        return MismatchSignature.SAME_FAMILY_SUBSTITUTION
    if len(missing_roots | unexpected_roots) > 1:
        return MismatchSignature.MULTIPLE_FAMILY_DIVERGENCE
    if len(missing) == 1 and not unexpected:
        return MismatchSignature.ONE_MISSING_DESCENDANT
    if len(unexpected) == 1 and not missing:
        return MismatchSignature.ONE_UNEXPECTED_DESCENDANT
    if status is MatchStatus.MISSING_ONLY:
        return MismatchSignature.MISSING_ONLY_OTHER
    if status is MatchStatus.UNEXPECTED_ONLY:
        return MismatchSignature.UNEXPECTED_ONLY_OTHER
    return MismatchSignature.MIXED_OTHER


def _has_pndt_override(planet: Planet) -> bool:
    return any(
        biome.pndt_rsgd is not None
        and (biome.biom_rsgd is None or biome.pndt_rsgd.form_id != biome.biom_rsgd.form_id)
        for biome in planet.biomes
    )


def _first_divergent_family_biome(
    result: PlanetGenerationResult, family: FamilyMismatchAnalysis
) -> int | None:
    divergent_roots = set(family.missing_family_roots) | set(family.unexpected_family_roots)
    for biome in result.biome_results:
        root = biome.orchestration.common_root
        if root is not None and root.form_id in divergent_roots:
            return biome.orchestration.biome.index
    return None


def _generation_error_result(
    planet: Planet, canonical: CanonicalBodyResources, error: Exception
) -> PlanetValidationResult:
    return PlanetValidationResult(
        planet_form_id=planet.form_id,
        planet_editor_id=planet.editor_id,
        planet_name=planet.name,
        system_name=canonical.system_name,
        resource_creation_seed=planet.resource_creation_seed,
        biome_count=len(planet.biomes),
        predicted_form_ids=frozenset(),
        atmospheric_form_ids=frozenset(),
        final_player_facing_form_ids=frozenset(),
        expected_form_ids=canonical.inorganic_resources,
        missing_form_ids=canonical.inorganic_resources,
        unexpected_form_ids=frozenset(),
        exact_match=False,
        match_status=MatchStatus.GENERATION_ERROR,
        mismatch_signature=MismatchSignature.GENERATION_ERROR,
        predicted_resources=(),
        atmospheric_resources=(),
        final_player_facing_resources=(),
        expected_resources=canonical.inorganic_resource_records,
        shuffled_biome_indices=(),
        shuffled_biome_names=(),
        final_draw_count=None,
        selected_common_roots=(),
        cache_hit_roots=(),
        effective_rsgd_form_ids=(),
        effective_rsgd_editor_ids=(),
        family_analysis=_EMPTY_FAMILY_ANALYSIS,
        has_pndt_override=_has_pndt_override(planet),
        has_cache_reuse=False,
        rscs_zero=planet.resource_creation_seed == 0,
        has_atmospheric=False,
        has_everywhere=False,
        has_special=False,
        capacity_reached=False,
        first_divergent_family_biome_index=None,
        suspected_cause=None,
        first_plausible_divergence=None,
        events=(),
        generation_error_type=type(error).__name__,
        generation_error_message=str(error),
    )


def _aggregate(results: tuple[PlanetValidationResult, ...]) -> ValidationAggregates:
    status_counts = Counter(result.match_status.value for result in results)
    non_exact = [result for result in results if not result.exact_match]
    signature_counts = Counter(result.mismatch_signature.value for result in non_exact)
    biome_counts = Counter(str(result.biome_count) for result in non_exact)
    predicted_counts = Counter(str(len(result.predicted_form_ids)) for result in non_exact)
    rsgd_counts: Counter[str] = Counter()
    root_counts: Counter[str] = Counter()
    for result in non_exact:
        rsgd_counts.update(set(result.effective_rsgd_editor_ids))
        root_counts.update({str(root) for root in result.selected_common_roots})
    total = len(results)
    exact = status_counts[MatchStatus.EXACT.value]
    return ValidationAggregates(
        total, exact, total - exact, 100.0 * exact / total if total else 0.0,
        status_counts[MatchStatus.MISSING_ONLY.value],
        status_counts[MatchStatus.UNEXPECTED_ONLY.value],
        status_counts[MatchStatus.MISSING_AND_UNEXPECTED.value],
        status_counts[MatchStatus.GENERATION_ERROR.value],
        sum(len(result.missing_form_ids) for result in non_exact),
        sum(len(result.unexpected_form_ids) for result in non_exact),
        tuple(sorted({item for result in non_exact for item in result.missing_form_ids})),
        tuple(sorted({item for result in non_exact for item in result.unexpected_form_ids})),
        _sorted_counts(Counter(result.match_status.value for result in non_exact)),
        _sorted_counts(signature_counts),
        tuple(sorted(biome_counts.items(), key=lambda item: int(item[0]))),
        _sorted_counts(rsgd_counts), _sorted_counts(root_counts),
        sum(result.has_pndt_override for result in non_exact),
        sum(result.has_cache_reuse for result in non_exact),
        sum(result.rscs_zero for result in results),
        sum(result.rscs_zero for result in non_exact),
        tuple(sorted(predicted_counts.items(), key=lambda item: int(item[0]))),
        sum(result.has_atmospheric for result in non_exact),
        sum(result.has_everywhere for result in non_exact),
        sum(result.has_special for result in non_exact),
        sum(result.biome_count == 1 for result in non_exact),
        sum(result.biome_count > 1 for result in non_exact),
        sum(result.capacity_reached for result in non_exact),
        False,
    )


def _sorted_counts(counter: Counter[str]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def _coverage_csv_row(coverage: CoverageMismatch) -> dict[str, str]:
    row = {column: "" for column in _CSV_COLUMNS}
    row.update({
        "PlanetFormID": str(coverage.planet_form_id),
        "PlanetEditorID": coverage.planet_editor_id,
        "PlanetName": coverage.planet_name,
        "MatchStatus": coverage.match_status.value,
        "MismatchSignature": coverage.signature.value,
        "GenerationError": coverage.source,
    })
    return row


def _join_ids(form_ids: Iterable[FormId]) -> str:
    return ";".join(str(form_id) for form_id in sorted(form_ids))


def _join_ids_in_order(form_ids: Iterable[FormId]) -> str:
    return ";".join(str(form_id) for form_id in form_ids)


def _join_names(form_ids: Iterable[FormId], names: Mapping[FormId, str]) -> str:
    return ";".join(names.get(form_id, "") for form_id in sorted(form_ids))


def _classify_mismatch(
    result: PlanetGenerationResult,
    missing: frozenset[FormId] | set[FormId],
    unexpected: frozenset[FormId] | set[FormId],
) -> tuple[MismatchClassification | None, DiagnosticEvent | None]:
    """Retain Brief 05's evidence-qualified first-plausible-region heuristic."""

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
