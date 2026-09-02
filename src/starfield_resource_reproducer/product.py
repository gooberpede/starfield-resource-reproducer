"""Build and serialize the default biome inorganic-resource product.

Purpose: turn the provenance-rich accepted-occurrence view into the stable
Planet x Location x Resource consumer dataset. Responsibilities include safe
collapse, product-contract validation, deterministic ordering, source manifests,
and atomic CSV/JSON replacement. Generation, RNG behavior, CSV input parsing,
and diagnostic-mode serialization remain outside this module. The validation
oracle is accepted only by the explicit comparison helper and is never used by
the production path.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable, Mapping, Sequence

from starfield_resource_reproducer import __version__
from starfield_resource_reproducer.domain import (
    CanonicalBodyResources,
    FormId,
    Planet,
    ProjectData,
)
from starfield_resource_reproducer.generation import (
    PlanetGenerationResult,
    generate_planet,
)
from starfield_resource_reproducer.load_data import load_production_data
from starfield_resource_reproducer.occurrences import (
    EnrichedResourceOccurrence,
    LocationType,
    build_enriched_occurrences,
)


SCHEMA_VERSION = 1
OUTPUT_FILENAME = "biome-inorganic-resources.csv"
MANIFEST_FILENAME = "biome-inorganic-resources.manifest.json"
PRODUCT_COLUMNS = (
    "ReproducerVersion", "ExportTimestamp", "SystemName", "PlanetName",
    "BodyType", "PlanetFormID", "PlanetEditorID", "StarSystemID",
    "ParentPlanetID", "PlanetID", "PlanetSourceFile", "LocationType",
    "BiomeIndex", "BiomeFormID", "BiomeEditorID", "BiomeName",
    "BiomeChance", "BiomeSourceFile", "AtmosphereFormID",
    "AtmosphereEditorID", "AtmosphereSourceFile", "ResourceCategory",
    "ResourceFormID", "ResourceEditorID", "ResourceName", "Rarity",
    "ResourceSourceFile", "EffectiveRSGDFormID", "EffectiveRSGDEditorID",
    "RSGDSource", "RSGDSourceFile", "ResourceDefinedByAtmosphereFormID",
    "ResourceDefinedByAtmosphereEditorID",
    "ResourceDefinedByAtmosphereSourceFile", "AtmosphereInheritanceDepth",
)
_BODY_RESOURCE_REQUIRED = (
    "SystemName", "PlanetName", "BodyType", "PlanetFormID", "PlanetEditorID",
    "StarSystemID", "ParentPlanetID", "PlanetID", "PlanetSourceFile",
    "ResourceCategory", "ResourceFormID", "ResourceEditorID", "ResourceName",
    "Rarity", "ResourceSourceFile",
)
_BIOME_REQUIRED = (
    "BiomeIndex", "BiomeFormID", "BiomeEditorID", "BiomeName", "BiomeChance",
    "BiomeSourceFile", "EffectiveRSGDFormID", "EffectiveRSGDEditorID",
    "RSGDSource", "RSGDSourceFile",
)
_ATMOSPHERE_REQUIRED = (
    "AtmosphereFormID", "AtmosphereEditorID", "AtmosphereSourceFile",
    "ResourceDefinedByAtmosphereFormID",
    "ResourceDefinedByAtmosphereEditorID",
    "ResourceDefinedByAtmosphereSourceFile", "AtmosphereInheritanceDepth",
)
_PRODUCTION_DATASET_ORDER = (
    "planet_resource_generation", "ires_hierarchy",
    "planet_atmospheric_resources", "planet_directory",
)
_FORM_ID_COLUMNS = (
    "PlanetFormID", "BiomeFormID", "AtmosphereFormID", "ResourceFormID",
    "EffectiveRSGDFormID", "ResourceDefinedByAtmosphereFormID",
)
_DECIMAL_INTEGER_COLUMNS = (
    "StarSystemID", "ParentPlanetID", "PlanetID", "BiomeIndex",
    "AtmosphereInheritanceDepth",
)


class ProductValidationError(ValueError):
    """A clean product row would violate the documented output contract."""


@dataclass(frozen=True, slots=True)
class DuplicateBiomeGroup:
    """One planet-local repeated biome value and its entry indexes."""

    planet_form_id: FormId
    planet_name: str
    value: str
    biome_indexes: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class BiomeIdentityAudit:
    """Corpus counts for duplicate biome indexes, FormIDs, and names."""

    duplicate_index_groups: tuple[DuplicateBiomeGroup, ...]
    repeated_form_id_groups: tuple[DuplicateBiomeGroup, ...]
    repeated_name_groups: tuple[DuplicateBiomeGroup, ...]

    @property
    def repeated_form_id_planet_count(self) -> int:
        return len({item.planet_form_id for item in self.repeated_form_id_groups})

    @property
    def repeated_name_planet_count(self) -> int:
        return len({item.planet_form_id for item in self.repeated_name_groups})


@dataclass(frozen=True, slots=True)
class ProductBuildResult:
    """Validated, sorted product rows plus construction/audit metrics."""

    rows: tuple[dict[str, str], ...]
    enriched_occurrence_count: int
    collapsed_occurrence_count: int
    biome_row_count: int
    atmosphere_row_count: int
    biome_audit: BiomeIdentityAudit


@dataclass(frozen=True, slots=True)
class OracleProjectionResult:
    """Validation-only comparison of BIOME projection to the old oracle."""

    compared_body_count: int
    exact_body_count: int
    mismatched_body_ids: tuple[FormId, ...]


def utc_export_timestamp() -> str:
    """Return one second-resolution UTC ISO 8601 timestamp for an export run."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def generate_all_planets(
    project: ProjectData,
) -> dict[FormId, PlanetGenerationResult]:
    """Generate every available terrestrial body without reading the oracle."""

    return {
        planet_id: generate_planet(
            planet,
            project.ires_nodes,
            atmospheric_records=project.atmospheric_resources.get(planet_id, ()),
        )
        for planet_id, planet in project.planets.items()
    }


def build_product(
    project: ProjectData,
    *,
    export_timestamp: str | None = None,
    reproducer_version: str = __version__,
) -> ProductBuildResult:
    """Generate, enrich, safely collapse, sort, and validate the product."""

    timestamp = export_timestamp or utc_export_timestamp()
    audit = audit_biome_identities(project.planets.values())
    if audit.duplicate_index_groups:
        example = audit.duplicate_index_groups[0]
        raise ProductValidationError(
            "duplicate BiomeIndex within planet "
            f"{example.planet_form_id}: {example.value}"
        )
    generations = generate_all_planets(project)
    enriched = build_enriched_occurrences(project, generations)
    rows = collapse_enriched_occurrences(
        enriched,
        reproducer_version=reproducer_version,
        export_timestamp=timestamp,
    )
    validate_product_rows(rows)
    biome_count = sum(row["LocationType"] == "BIOME" for row in rows)
    atmosphere_count = len(rows) - biome_count
    return ProductBuildResult(
        rows=rows,
        enriched_occurrence_count=len(enriched),
        collapsed_occurrence_count=len(enriched) - len(rows),
        biome_row_count=biome_count,
        atmosphere_row_count=atmosphere_count,
        biome_audit=audit,
    )


def collapse_enriched_occurrences(
    occurrences: Iterable[EnrichedResourceOccurrence],
    *,
    reproducer_version: str,
    export_timestamp: str,
) -> tuple[dict[str, str], ...]:
    """Project and safely collapse provenance-only duplicate occurrences."""

    collapsed: dict[tuple[str, ...], dict[str, str]] = {}
    for occurrence in occurrences:
        row = _product_row(occurrence, reproducer_version, export_timestamp)
        key = _product_key(row)
        previous = collapsed.get(key)
        if previous is None:
            collapsed[key] = row
            continue
        differing = [column for column in PRODUCT_COLUMNS if previous[column] != row[column]]
        if differing:
            raise ProductValidationError(
                f"safe-collapse conflict for key {key!r}; retained fields differ: "
                + ", ".join(differing)
            )
    return tuple(sorted(collapsed.values(), key=_sort_key))


def audit_biome_identities(planets: Iterable[Planet]) -> BiomeIdentityAudit:
    """Audit planet-local biome indexes, FormIDs, and display names."""

    indexes: list[DuplicateBiomeGroup] = []
    form_ids: list[DuplicateBiomeGroup] = []
    names: list[DuplicateBiomeGroup] = []
    for planet in sorted(planets, key=lambda item: item.form_id.numeric):
        indexes.extend(_duplicate_groups(planet, ((str(b.index), b.index) for b in planet.biomes)))
        form_ids.extend(_duplicate_groups(planet, ((str(b.form_id), b.index) for b in planet.biomes)))
        names.extend(_duplicate_groups(planet, ((b.name, b.index) for b in planet.biomes)))
    return BiomeIdentityAudit(tuple(indexes), tuple(form_ids), tuple(names))


def validate_product_rows(rows: Sequence[Mapping[str, str]]) -> None:
    """Assert the complete 35-column consumer product contract."""

    if len(PRODUCT_COLUMNS) != 35:
        raise AssertionError("product schema must contain exactly 35 columns")
    keys: set[tuple[str, ...]] = set()
    for index, row in enumerate(rows, start=1):
        if tuple(row) != PRODUCT_COLUMNS:
            raise ProductValidationError(f"row {index} has incorrect column order")
        location = row["LocationType"]
        if location not in {"BIOME", "ATMOSPHERE"}:
            raise ProductValidationError(f"row {index} has invalid LocationType {location!r}")
        for column in _BODY_RESOURCE_REQUIRED:
            if row[column] == "":
                raise ProductValidationError(f"row {index} has blank required {column}")
        required = _BIOME_REQUIRED if location == "BIOME" else _ATMOSPHERE_REQUIRED
        blank = _ATMOSPHERE_REQUIRED if location == "BIOME" else _BIOME_REQUIRED
        for column in required:
            if row[column] == "":
                raise ProductValidationError(f"row {index} has blank required {column}")
        for column in blank:
            if row[column] != "":
                raise ProductValidationError(f"row {index} has inapplicable {column}")
        if row["ResourceCategory"] != "Inorganic":
            raise ProductValidationError(f"row {index} has invalid ResourceCategory")
        for column in _FORM_ID_COLUMNS:
            if row[column] and str(FormId(row[column])) != row[column]:
                raise ProductValidationError(
                    f"row {index} has noncanonical {column}: {row[column]!r}"
                )
        for column in _DECIMAL_INTEGER_COLUMNS:
            if row[column] and str(int(row[column])) != row[column]:
                raise ProductValidationError(
                    f"row {index} has noncanonical decimal {column}: {row[column]!r}"
                )
        if row["BiomeChance"]:
            Decimal(row["BiomeChance"])
        key = _product_key(row)
        if key in keys:
            raise ProductValidationError(f"duplicate product key remains: {key!r}")
        keys.add(key)
    if rows:
        if len({row["ReproducerVersion"] for row in rows}) != 1:
            raise ProductValidationError("product has multiple ReproducerVersion values")
        if len({row["ExportTimestamp"] for row in rows}) != 1:
            raise ProductValidationError("product has multiple ExportTimestamp values")
    if list(rows) != sorted(rows, key=_sort_key):
        raise ProductValidationError("product rows are not in deterministic order")
    _serialize_csv(rows).encode("utf-8").decode("utf-8")


def compare_biome_projection_to_oracle(
    rows: Sequence[Mapping[str, str]],
    oracle: Mapping[FormId, CanonicalBodyResources],
) -> OracleProjectionResult:
    """Compare BIOME identities to the validation-only CK/RSGD oracle."""

    projected: dict[FormId, set[FormId]] = {}
    for row in rows:
        if row["LocationType"] == "BIOME":
            projected.setdefault(FormId(row["PlanetFormID"]), set()).add(
                FormId(row["ResourceFormID"])
            )
    expected = {
        body_id: body.inorganic_resources
        for body_id, body in oracle.items()
        if body.inorganic_resources
    }
    mismatches = tuple(
        sorted(
            body_id for body_id, resource_ids in expected.items()
            if frozenset(projected.get(body_id, set())) != resource_ids
        )
    )
    return OracleProjectionResult(
        compared_body_count=len(expected),
        exact_body_count=len(expected) - len(mismatches),
        mismatched_body_ids=mismatches,
    )


def export_default_product(
    project_root: Path,
    *,
    export_timestamp: str | None = None,
) -> ProductBuildResult:
    """Run the four-input production pipeline and atomically write both outputs."""

    project_root = Path(project_root)
    data_dir = project_root / "data"
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    project = load_production_data(data_dir)
    result = build_product(project, export_timestamp=export_timestamp)
    manifest = build_manifest(project, data_dir, result)
    csv_text = _serialize_csv(result.rows)
    manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    csv_temp: Path | None = None
    manifest_temp: Path | None = None
    try:
        csv_temp = _write_temporary(output_dir, OUTPUT_FILENAME, csv_text)
        manifest_temp = _write_temporary(output_dir, MANIFEST_FILENAME, manifest_text)
        os.replace(csv_temp, output_dir / OUTPUT_FILENAME)
        os.replace(manifest_temp, output_dir / MANIFEST_FILENAME)
    finally:
        for path in (csv_temp, manifest_temp):
            if path is not None and path.exists():
                path.unlink()
    return result


def _product_row(
    occurrence: EnrichedResourceOccurrence,
    reproducer_version: str,
    export_timestamp: str,
) -> dict[str, str]:
    values = {
        "ReproducerVersion": reproducer_version,
        "ExportTimestamp": export_timestamp,
        "SystemName": occurrence.system_name,
        "PlanetName": occurrence.planet_name,
        "BodyType": occurrence.body_type,
        "PlanetFormID": occurrence.planet_form_id,
        "PlanetEditorID": occurrence.planet_editor_id,
        "StarSystemID": occurrence.star_system_id,
        "ParentPlanetID": occurrence.parent_planet_id,
        "PlanetID": occurrence.planet_id,
        "PlanetSourceFile": occurrence.planet_source_file,
        "LocationType": occurrence.location_type,
        "BiomeIndex": occurrence.biome_index,
        "BiomeFormID": occurrence.biome_form_id,
        "BiomeEditorID": occurrence.biome_editor_id,
        "BiomeName": occurrence.biome_name,
        "BiomeChance": occurrence.biome_chance,
        "BiomeSourceFile": occurrence.biome_source_file,
        "AtmosphereFormID": occurrence.atmosphere_form_id,
        "AtmosphereEditorID": occurrence.atmosphere_editor_id,
        "AtmosphereSourceFile": occurrence.atmosphere_source_file,
        "ResourceCategory": "Inorganic",
        "ResourceFormID": occurrence.resource_form_id,
        "ResourceEditorID": occurrence.resource_editor_id,
        "ResourceName": occurrence.resource_name,
        "Rarity": occurrence.rarity,
        "ResourceSourceFile": occurrence.resource_source_file,
        "EffectiveRSGDFormID": occurrence.effective_rsgd_form_id,
        "EffectiveRSGDEditorID": occurrence.effective_rsgd_editor_id,
        "RSGDSource": occurrence.rsgd_source,
        "RSGDSourceFile": occurrence.rsgd_source_file,
        "ResourceDefinedByAtmosphereFormID": occurrence.resource_defined_by_atmosphere_form_id,
        "ResourceDefinedByAtmosphereEditorID": occurrence.resource_defined_by_atmosphere_editor_id,
        "ResourceDefinedByAtmosphereSourceFile": occurrence.resource_defined_by_atmosphere_source_file,
        "AtmosphereInheritanceDepth": occurrence.atmosphere_inheritance_depth,
    }
    return {column: _format_value(values[column]) for column in PRODUCT_COLUMNS}


def _format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        rendered = format(value, "f")
        if "." in rendered:
            rendered = rendered.rstrip("0").rstrip(".")
        return rendered or "0"
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _product_key(row: Mapping[str, str]) -> tuple[str, ...]:
    if row["LocationType"] == "BIOME":
        return (
            row["PlanetFormID"], row["LocationType"], row["BiomeIndex"],
            row["BiomeFormID"], row["ResourceFormID"],
        )
    return (
        row["PlanetFormID"], row["LocationType"], row["AtmosphereFormID"],
        row["ResourceFormID"],
    )


def _sort_key(row: Mapping[str, str]) -> tuple[int, ...]:
    null_last = 1 << 64
    return (
        int(row["StarSystemID"]), int(row["ParentPlanetID"]),
        int(row["PlanetID"]), int(row["PlanetFormID"], 16),
        0 if row["LocationType"] == "BIOME" else 1,
        int(row["BiomeIndex"]) if row["BiomeIndex"] else null_last,
        int(row["BiomeFormID"], 16) if row["BiomeFormID"] else null_last,
        int(row["AtmosphereFormID"], 16) if row["AtmosphereFormID"] else null_last,
        int(row["ResourceFormID"], 16),
    )


def _duplicate_groups(
    planet: Planet, values: Iterable[tuple[str, int]]
) -> list[DuplicateBiomeGroup]:
    grouped: dict[str, list[int]] = {}
    for value, index in values:
        grouped.setdefault(value, []).append(index)
    return [
        DuplicateBiomeGroup(planet.form_id, planet.name, value, tuple(indexes))
        for value, indexes in grouped.items() if len(indexes) > 1
    ]


def _serialize_csv(rows: Sequence[Mapping[str, str]]) -> str:
    import io

    destination = io.StringIO(newline="")
    writer = csv.DictWriter(destination, fieldnames=PRODUCT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return destination.getvalue()


def build_manifest(
    project: ProjectData, data_dir: Path, result: ProductBuildResult
) -> dict[str, object]:
    """Build the lightweight source-provenance manifest for a product."""

    export_timestamp = result.rows[0]["ExportTimestamp"] if result.rows else ""
    inputs = []
    for name in _PRODUCTION_DATASET_ORDER:
        metadata = project.dataset_metadata[name]
        path = data_dir / metadata.filename
        inputs.append(
            {
                "filename": metadata.filename,
                "extract_timestamp": metadata.extract_timestamp,
                "row_count": metadata.row_count,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return {
        "dataset": "biome-inorganic-resources",
        "schema_version": SCHEMA_VERSION,
        "reproducer_version": __version__,
        "export_timestamp": export_timestamp,
        "output_filename": OUTPUT_FILENAME,
        "row_count": len(result.rows),
        "location_row_counts": {
            "BIOME": result.biome_row_count,
            "ATMOSPHERE": result.atmosphere_row_count,
        },
        "collapsed_occurrence_count": result.collapsed_occurrence_count,
        "input_datasets": inputs,
    }


def _write_temporary(directory: Path, filename: str, content: str) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", delete=False,
        dir=directory, prefix=f".{filename}.", suffix=".tmp",
    ) as destination:
        destination.write(content)
        destination.flush()
        os.fsync(destination.fileno())
        path = Path(destination.name)
    path.read_bytes().decode("utf-8")
    return path
