"""Build diagnostics-only dense-planet investigation dossiers.

Purpose:
    Enrich a completed production generation trace with insertion and family
    counters for mismatch investigation.
Responsibilities:
    Reconstruct stable event rows, resource and family ledgers, first divergent
    insertions, counterfactual cutoffs, and deterministic CSV output.
Boundaries:
    This module never selects resources, advances production RNG state, or feeds
    canonical membership back into generation. Counterfactuals filter immutable
    recorded results only; they do not model a recovered runtime limit.
Evidence notes:
    Resource counts now mirror the shared unique-FormID state insertion events.
    Family counts mirror completed reproducer cache entries, not a proven runtime
    configuration-capacity field.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from .diagnostics import DiagnosticEvent, EventKind
from .domain import CanonicalBodyResources, FormId, IRESNode, ResourceRef
from .generation import PlanetGenerationResult


@dataclass(frozen=True, slots=True)
class DossierEvent:
    """One generation event enriched with planet-wide diagnostic counters."""

    planet_form_id: FormId
    planet_name: str
    event_index: int
    event_kind: EventKind
    raw_draw_number: int | None
    raw_value: int | None
    biome_runtime_position: int | None
    biome_index: int | None
    biome_editor_id: str | None
    biome_name: str | None
    effective_rsgd_form_id: FormId | None
    effective_rsgd_editor_id: str | None
    operation: str | None
    common_root: ResourceRef | None
    current_structural_node: ResourceRef | None
    candidate_count: int | None
    selected_candidate: ResourceRef | None
    emitted_resource: ResourceRef | None
    cache_hit: bool
    insertion_attempt: bool
    inserted_new_resource: bool
    planet_resource_count_before: int
    planet_resource_count_after: int
    generated_family_count_before: int
    generated_family_count_after: int
    canonical_membership_of_inserted_resource: bool | None
    family_ordinal: int | None


@dataclass(frozen=True, slots=True)
class ResourceInsertion:
    """One unique visible resource insertion reconstructed from the trace."""

    sequence: int
    event_index: int
    biome_runtime_position: int | None
    biome_index: int | None
    biome_name: str | None
    family_root: ResourceRef | None
    resource: ResourceRef
    source_event: str
    cache_hit: bool
    count_after: int
    canonical_member: bool
    family_ordinal: int | None


@dataclass(frozen=True, slots=True)
class FamilyLedgerEntry:
    """One Common-root access in runtime biome-processing order."""

    sequence: int
    biome_runtime_position: int
    biome_index: int
    biome_name: str
    effective_rsgd_editor_id: str
    root: ResourceRef
    cache_hit: bool
    root_emitted: bool
    emitted_descendants: tuple[ResourceRef, ...]
    generated_family_count_before: int
    generated_family_count_after: int


@dataclass(frozen=True, slots=True)
class CutoffResult:
    """A COUNTERFACTUAL set produced by filtering recorded insertions."""

    cutoff_type: str
    threshold: int
    resulting_form_ids: frozenset[FormId]
    assessment: str


@dataclass(frozen=True, slots=True)
class PlanetDossier:
    """Complete diagnostics-only evidence package for one generated planet."""

    generation: PlanetGenerationResult
    canonical: CanonicalBodyResources
    events: tuple[DossierEvent, ...]
    insertions: tuple[ResourceInsertion, ...]
    families: tuple[FamilyLedgerEntry, ...]
    first_divergence: ResourceInsertion | None

    @property
    def missing_form_ids(self) -> frozenset[FormId]:
        return self.canonical.inorganic_resources - self.generation.predicted_form_ids

    @property
    def unexpected_form_ids(self) -> frozenset[FormId]:
        return self.generation.predicted_form_ids - self.canonical.inorganic_resources


_INSERTION_KINDS = {
    EventKind.RESOURCE_SLOT_OCCUPIED,
}


def build_planet_dossier(
    generation: PlanetGenerationResult,
    canonical: CanonicalBodyResources,
    ires_nodes: Mapping[FormId, IRESNode],
) -> PlanetDossier:
    """Annotate a completed prediction without changing or rerunning generation."""

    if generation.planet.form_id != canonical.planet_form_id:
        raise ValueError("generation and canonical results describe different planets")

    seen_resources: set[FormId] = set()
    family_ordinals: dict[FormId, int] = {}
    generated_family_count = 0
    current_family_ordinal: int | None = None
    current_runtime_position: int | None = None
    current_biome = None
    current_rsgd = None
    current_root: ResourceRef | None = None
    rows: list[DossierEvent] = []
    insertions: list[ResourceInsertion] = []

    for event_index, item in enumerate(generation.events, start=1):
        if item.kind is EventKind.BIOME_BEGIN:
            current_runtime_position = item.get("processing_position")
            current_biome = generation.shuffled_biomes[current_runtime_position]
            current_rsgd = None
            current_root = None
            current_family_ordinal = None
        elif item.kind is EventKind.RSGD_RESOLVED and current_biome is not None:
            current_rsgd = current_biome.effective_rsgd
        elif item.kind is EventKind.COMMON_SELECTED:
            current_root = item.get("selected_resource")
        elif item.kind is EventKind.FAMILY_BEGIN:
            root = item.get("root")
            if root is not None:
                current_root = root
                current_family_ordinal = generated_family_count + 1
        elif item.kind is EventKind.FAMILY_CACHE_HIT:
            root = item.get("root")
            if root is not None:
                current_root = root
                current_family_ordinal = family_ordinals.get(root.form_id)

        family_count_before = generated_family_count
        emitted = _emitted_resource(item)
        insertion_attempt = item.kind in _INSERTION_KINDS and emitted is not None
        resource_count_before = len(seen_resources)
        inserted_new = bool(
            insertion_attempt and emitted is not None and emitted.form_id not in seen_resources
        )
        if inserted_new and emitted is not None:
            seen_resources.add(emitted.form_id)

        if item.kind is EventKind.FAMILY_END:
            root = item.get("root")
            if root is not None and root.form_id not in family_ordinals:
                generated_family_count += 1
                family_ordinals[root.form_id] = generated_family_count
                current_family_ordinal = generated_family_count

        selected = item.get("selected_candidate")
        structural_id = item.get("current_structural_form_id")
        if structural_id is None:
            structural_id = item.get("current_structural_node")
        structural = _resource_for(structural_id, ires_nodes)
        raw_draw_number, raw_value = _raw_draw(item)
        canonical_member = (
            emitted.form_id in canonical.inorganic_resources
            if insertion_attempt and emitted is not None
            else None
        )
        row = DossierEvent(
            planet_form_id=generation.planet.form_id,
            planet_name=generation.planet.name,
            event_index=event_index,
            event_kind=item.kind,
            raw_draw_number=raw_draw_number,
            raw_value=raw_value,
            biome_runtime_position=current_runtime_position,
            biome_index=(current_biome.index if current_biome is not None else item.get("biome_index")),
            biome_editor_id=(current_biome.editor_id if current_biome is not None else None),
            biome_name=(current_biome.name if current_biome is not None else None),
            effective_rsgd_form_id=(current_rsgd.form_id if current_rsgd is not None else None),
            effective_rsgd_editor_id=(current_rsgd.editor_id if current_rsgd is not None else None),
            operation=item.operation,
            common_root=item.get("root", current_root),
            current_structural_node=structural,
            candidate_count=item.get(
                "candidate_count", item.get("bound", item.get("eligible_count"))
            ),
            selected_candidate=selected,
            emitted_resource=emitted,
            cache_hit=item.kind is EventKind.FAMILY_CACHE_HIT,
            insertion_attempt=insertion_attempt,
            inserted_new_resource=inserted_new,
            planet_resource_count_before=resource_count_before,
            planet_resource_count_after=len(seen_resources),
            generated_family_count_before=family_count_before,
            generated_family_count_after=generated_family_count,
            canonical_membership_of_inserted_resource=canonical_member,
            family_ordinal=current_family_ordinal,
        )
        rows.append(row)
        if inserted_new and emitted is not None:
            insertions.append(
                ResourceInsertion(
                    sequence=len(insertions) + 1,
                    event_index=event_index,
                    biome_runtime_position=current_runtime_position,
                    biome_index=row.biome_index,
                    biome_name=row.biome_name,
                    family_root=(
                        row.common_root
                        if item.kind in {EventKind.ROOT_EMITTED, EventKind.DESCENDANT_EMITTED}
                        else None
                    ),
                    resource=emitted,
                    source_event=item.kind.value,
                    cache_hit=row.cache_hit,
                    count_after=len(seen_resources),
                    canonical_member=bool(canonical_member),
                    family_ordinal=current_family_ordinal,
                )
            )
        if item.kind is EventKind.BIOME_END:
            current_runtime_position = None
            current_biome = None
            current_rsgd = None
            current_root = None
            current_family_ordinal = None

    families = _family_ledger(generation)
    first_divergence = next(
        (insertion for insertion in insertions if not insertion.canonical_member), None
    )
    return PlanetDossier(
        generation=generation,
        canonical=canonical,
        events=tuple(rows),
        insertions=tuple(insertions),
        families=families,
        first_divergence=first_divergence,
    )


def visible_insertion_cutoffs(
    dossier: PlanetDossier, thresholds: Iterable[int]
) -> tuple[CutoffResult, ...]:
    """COUNTERFACTUAL: retain only the first N visible unique insertions."""

    return tuple(
        _cutoff_result(
            dossier,
            "visible_resource_count",
            threshold,
            (item.resource.form_id for item in dossier.insertions[:threshold]),
        )
        for threshold in thresholds
    )


def family_configuration_cutoffs(
    dossier: PlanetDossier, thresholds: Iterable[int]
) -> tuple[CutoffResult, ...]:
    """COUNTERFACTUAL: suppress resources from Common families after family N."""

    return tuple(
        _cutoff_result(
            dossier,
            "distinct_generated_families",
            threshold,
            (
                item.resource.form_id
                for item in dossier.insertions
                if item.family_ordinal is None or item.family_ordinal <= threshold
            ),
        )
        for threshold in thresholds
    )


_EVENT_CSV_COLUMNS = (
    "PlanetFormID", "PlanetName", "EventIndex", "RawDrawNumber", "RawValue",
    "BiomeRuntimePosition", "BiomeIndex", "BiomeEditorID", "BiomeName",
    "EffectiveRSGDFormID", "EffectiveRSGD", "Operation", "EventKind",
    "CommonRootFormID", "CommonRoot", "CurrentStructuralNodeFormID",
    "CurrentStructuralNode", "CandidateCount", "SelectedCandidateFormID",
    "SelectedCandidate", "EmittedResourceFormID", "EmittedResource",
    "EmittedRarity", "CacheHit", "InsertionAttempt", "InsertedNewResource",
    "PlanetResourceCountBefore", "PlanetResourceCountAfter",
    "GeneratedFamilyCountBefore", "GeneratedFamilyCountAfter",
    "CanonicalMembershipOfInsertedResource", "FamilyOrdinal",
)


def write_dossier_events_csv(dossiers: Iterable[PlanetDossier], path: Path) -> None:
    """Write all dossier event rows in deterministic supplied-planet order."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=_EVENT_CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for dossier in dossiers:
            for item in dossier.events:
                writer.writerow(_event_csv_row(item))


def _family_ledger(generation: PlanetGenerationResult) -> tuple[FamilyLedgerEntry, ...]:
    rows: list[FamilyLedgerEntry] = []
    generated_count = 0
    for runtime_position, biome in enumerate(generation.biome_results):
        access = biome.family_access
        if access is None:
            continue
        before = generated_count
        if not access.cache_hit:
            generated_count += 1
        rows.append(
            FamilyLedgerEntry(
                sequence=len(rows) + 1,
                biome_runtime_position=runtime_position,
                biome_index=biome.orchestration.biome.index,
                biome_name=biome.orchestration.biome.name,
                effective_rsgd_editor_id=biome.orchestration.effective_rsgd.editor_id,
                root=access.family.root,
                cache_hit=access.cache_hit,
                root_emitted=not access.cache_hit,
                emitted_descendants=access.family.emitted_descendants,
                generated_family_count_before=before,
                generated_family_count_after=generated_count,
            )
        )
    return tuple(rows)


def _cutoff_result(
    dossier: PlanetDossier,
    cutoff_type: str,
    threshold: int,
    form_ids: Iterable[FormId],
) -> CutoffResult:
    if threshold < 0:
        raise ValueError("cutoff threshold must be non-negative")
    result = frozenset(form_ids)
    assessment = (
        "COMPATIBLE WITH THIS CASE"
        if result == dossier.canonical.inorganic_resources
        else "INCOMPATIBLE WITH THIS CASE"
    )
    return CutoffResult(cutoff_type, threshold, result, assessment)


def _emitted_resource(item: DiagnosticEvent) -> ResourceRef | None:
    if item.kind is EventKind.RESOURCE_SLOT_OCCUPIED:
        return item.get("resource")
    if item.kind is EventKind.EVERYWHERE_DISCOVERED:
        return item.get("resource")
    if item.kind in {EventKind.SPECIAL_EMITTED, EventKind.ROOT_EMITTED}:
        return item.get("emitted_resource")
    if item.kind is EventKind.DESCENDANT_EMITTED:
        return item.get("selected_candidate")
    return None


def _raw_draw(item: DiagnosticEvent) -> tuple[int | None, int | None]:
    if item.rng_draw is not None:
        return item.rng_draw.draw_number, item.rng_draw.raw_value
    raw_values = item.get("raw_values_consumed", ())
    if len(raw_values) == 1:
        return item.get("draw_count_after"), raw_values[0]
    return None, None


def _resource_for(
    value: object, ires_nodes: Mapping[FormId, IRESNode]
) -> ResourceRef | None:
    if isinstance(value, ResourceRef):
        return value
    if isinstance(value, FormId):
        node = ires_nodes.get(value)
        if node is not None:
            return ResourceRef(node.form_id, node.editor_id, node.name, node.rarity)
    return None


def _event_csv_row(item: DossierEvent) -> dict[str, str]:
    return {
        "PlanetFormID": str(item.planet_form_id),
        "PlanetName": item.planet_name,
        "EventIndex": str(item.event_index),
        "RawDrawNumber": _optional(item.raw_draw_number),
        "RawValue": _optional(item.raw_value),
        "BiomeRuntimePosition": _optional(item.biome_runtime_position),
        "BiomeIndex": _optional(item.biome_index),
        "BiomeEditorID": item.biome_editor_id or "",
        "BiomeName": item.biome_name or "",
        "EffectiveRSGDFormID": _resource_id(item.effective_rsgd_form_id),
        "EffectiveRSGD": item.effective_rsgd_editor_id or "",
        "Operation": item.operation or "",
        "EventKind": item.event_kind.value,
        "CommonRootFormID": _resource_id(item.common_root),
        "CommonRoot": _resource_name(item.common_root),
        "CurrentStructuralNodeFormID": _resource_id(item.current_structural_node),
        "CurrentStructuralNode": _resource_name(item.current_structural_node),
        "CandidateCount": _optional(item.candidate_count),
        "SelectedCandidateFormID": _resource_id(item.selected_candidate),
        "SelectedCandidate": _resource_name(item.selected_candidate),
        "EmittedResourceFormID": _resource_id(item.emitted_resource),
        "EmittedResource": _resource_name(item.emitted_resource),
        "EmittedRarity": (
            item.emitted_resource.rarity.value if item.emitted_resource is not None else ""
        ),
        "CacheHit": str(item.cache_hit).lower(),
        "InsertionAttempt": str(item.insertion_attempt).lower(),
        "InsertedNewResource": str(item.inserted_new_resource).lower(),
        "PlanetResourceCountBefore": str(item.planet_resource_count_before),
        "PlanetResourceCountAfter": str(item.planet_resource_count_after),
        "GeneratedFamilyCountBefore": str(item.generated_family_count_before),
        "GeneratedFamilyCountAfter": str(item.generated_family_count_after),
        "CanonicalMembershipOfInsertedResource": (
            "" if item.canonical_membership_of_inserted_resource is None
            else str(item.canonical_membership_of_inserted_resource).lower()
        ),
        "FamilyOrdinal": _optional(item.family_ordinal),
    }


def _optional(value: object | None) -> str:
    return "" if value is None else str(value)


def _resource_id(value: ResourceRef | FormId | None) -> str:
    if value is None:
        return ""
    return str(value.form_id if isinstance(value, ResourceRef) else value)


def _resource_name(value: ResourceRef | None) -> str:
    return "" if value is None else value.name
