"""Project accepted generation state into canonical enriched occurrences.

Purpose: provide the typed, deterministic result-shaping boundary that a future
serializer can consume directly. Responsibilities are canonical body/location
joins, resource-origin mapping, effective-RSGD context, family-origin lineage,
and atmospheric defining-ATMO lineage. This module does not parse CSV, consult
the validation oracle, serialize products, or alter protected generation/RNG
behavior. Only accepted (state-occupying) occurrences are projected.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping

from starfield_resource_reproducer.domain import (
    AtmosphericResourceRecord,
    CommonAssignmentMechanism,
    FormId,
    GenerationRarity,
    PlanetDirectoryRecord,
    ProjectData,
    ResourceOccurrence,
    ResourceProvenance,
    RSGDSource,
)
from starfield_resource_reproducer.generation import PlanetGenerationResult


class LocationType(str, Enum):
    """Stable occurrence-location vocabulary."""

    BIOME = "BIOME"
    ATMOSPHERE = "ATMOSPHERE"


@dataclass(frozen=True, slots=True)
class EnrichedResourceOccurrence:
    """One accepted resource occurrence with all canonical 10D context."""

    system_name: str
    planet_name: str
    body_type: str
    planet_form_id: FormId
    planet_editor_id: str
    star_system_id: int
    parent_planet_id: int
    planet_id: int
    planet_source_file: str
    location_type: LocationType
    resource_form_id: FormId
    resource_editor_id: str
    resource_name: str
    rarity: GenerationRarity
    resource_source_file: str
    resource_origin: ResourceProvenance
    biome_index: int | None = None
    biome_form_id: FormId | None = None
    biome_editor_id: str | None = None
    biome_name: str | None = None
    biome_chance: Decimal | None = None
    biome_source_file: str | None = None
    atmosphere_form_id: FormId | None = None
    atmosphere_editor_id: str | None = None
    atmosphere_source_file: str | None = None
    effective_rsgd_form_id: FormId | None = None
    effective_rsgd_editor_id: str | None = None
    rsgd_source: RSGDSource | None = None
    rsgd_source_file: str | None = None
    common_assignment_mechanism: CommonAssignmentMechanism | None = None
    family_root_form_id: FormId | None = None
    family_root_editor_id: str | None = None
    family_origin_biome_index: int | None = None
    family_origin_biome_form_id: FormId | None = None
    resource_defined_by_atmosphere_form_id: FormId | None = None
    resource_defined_by_atmosphere_editor_id: str | None = None
    resource_defined_by_atmosphere_source_file: str | None = None
    atmosphere_inheritance_depth: int | None = None


def build_enriched_occurrences(
    project: ProjectData,
    generation_results: Mapping[FormId, PlanetGenerationResult],
) -> tuple[EnrichedResourceOccurrence, ...]:
    """Project supplied independent predictions and all atmosphere-only bodies.

    Missing generation results remain missing terrestrial state; atmospheric
    source records are still independently representable. The oracle member of
    ``ProjectData`` is deliberately never read.
    """

    body_ids = set(generation_results) | set(project.atmospheric_resources)
    enriched: list[EnrichedResourceOccurrence] = []
    for body_id in sorted(body_ids):
        try:
            body = project.planet_directory[body_id]
        except KeyError as error:
            raise ValueError(
                f"cannot enrich PlanetFormID {body_id}: no directory record"
            ) from error
        result = generation_results.get(body_id)
        if result is not None:
            enriched.extend(_biome_occurrences(body, result))
            accepted_atmosphere = {
                item.atmospheric_record
                for item in result.atmospheric_occurrences
                if item.occupies_state and item.atmospheric_record is not None
            }
        else:
            accepted_atmosphere = set(project.atmospheric_resources.get(body_id, ()))
        for record in project.atmospheric_resources.get(body_id, ()):
            if record in accepted_atmosphere:
                enriched.append(_atmosphere_occurrence(body, record, project))
    return tuple(enriched)


def _body_fields(body: PlanetDirectoryRecord) -> dict[str, object]:
    return {
        "system_name": body.system_name,
        "planet_name": body.planet_name,
        "body_type": body.body_type,
        "planet_form_id": body.planet_form_id,
        "planet_editor_id": body.planet_editor_id,
        "star_system_id": body.star_system_id,
        "parent_planet_id": body.parent_planet_id,
        "planet_id": body.planet_id,
        "planet_source_file": body.source_file,
    }


def _biome_occurrences(
    body: PlanetDirectoryRecord, result: PlanetGenerationResult
) -> list[EnrichedResourceOccurrence]:
    output: list[EnrichedResourceOccurrence] = []
    biomes = {biome.index: biome for biome in result.planet.biomes}
    for occurrence in result.occurrences:
        if (
            not occurrence.occupies_state
            or occurrence.provenance is ResourceProvenance.ATMOSPHERE
        ):
            continue
        if occurrence.biome_index is None:
            raise ValueError(
                f"accepted biome occurrence {occurrence.resource.form_id} has no BiomeIndex"
            )
        biome = biomes[occurrence.biome_index]
        effective = biome.effective_rsgd
        lineage = _family_lineage(occurrence, result)
        resource_source = occurrence.resource.source_file
        if resource_source is None:
            raise ValueError(
                f"resource {occurrence.resource.form_id} has no canonical source file"
            )
        output.append(
            EnrichedResourceOccurrence(
                **_body_fields(body),
                location_type=LocationType.BIOME,
                biome_index=biome.index,
                biome_form_id=biome.form_id,
                biome_editor_id=biome.editor_id,
                biome_name=biome.name,
                biome_chance=biome.chance,
                biome_source_file=biome.source_file,
                resource_form_id=occurrence.resource.form_id,
                resource_editor_id=occurrence.resource.editor_id,
                resource_name=occurrence.resource.name,
                rarity=occurrence.resource.rarity,
                resource_source_file=resource_source,
                resource_origin=occurrence.provenance,
                effective_rsgd_form_id=effective.form_id,
                effective_rsgd_editor_id=effective.editor_id,
                rsgd_source=effective.source,
                rsgd_source_file=effective.source_file,
                **lineage,
            )
        )
    return output


def _family_lineage(
    occurrence: ResourceOccurrence, result: PlanetGenerationResult
) -> dict[str, object]:
    if occurrence.provenance not in {
        ResourceProvenance.COMMON_ROOT,
        ResourceProvenance.DESCENDANT,
    }:
        return {}
    if occurrence.root_form_id is None:
        raise ValueError("Common-family occurrence has no root FormID")
    family = result.family_cache[occurrence.root_form_id]
    return {
        "common_assignment_mechanism": occurrence.common_assignment_mechanism,
        "family_root_form_id": family.root.form_id,
        "family_root_editor_id": family.root.editor_id,
        "family_origin_biome_index": family.origin.biome_index,
        "family_origin_biome_form_id": family.origin.biome_form_id,
    }


def _atmosphere_occurrence(
    body: PlanetDirectoryRecord,
    record: AtmosphericResourceRecord,
    project: ProjectData,
) -> EnrichedResourceOccurrence:
    node = project.ires_nodes[record.resource_form_id]
    return EnrichedResourceOccurrence(
        **_body_fields(body),
        location_type=LocationType.ATMOSPHERE,
        atmosphere_form_id=record.atmosphere_form_id,
        atmosphere_editor_id=record.atmosphere_editor_id,
        atmosphere_source_file=record.atmosphere_source_file,
        resource_form_id=record.resource_form_id,
        resource_editor_id=record.resource_editor_id,
        resource_name=record.resource_name,
        rarity=node.rarity,
        resource_source_file=record.resource_source_file,
        resource_origin=ResourceProvenance.ATMOSPHERE,
        resource_defined_by_atmosphere_form_id=record.defined_by_atmosphere_form_id,
        resource_defined_by_atmosphere_editor_id=record.defined_by_atmosphere_editor_id,
        resource_defined_by_atmosphere_source_file=record.defined_by_atmosphere_source_file,
        atmosphere_inheritance_depth=record.atmosphere_inheritance_depth,
    )
