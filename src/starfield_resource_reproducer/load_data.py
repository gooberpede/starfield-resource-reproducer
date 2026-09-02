"""Load and validate the canonical Starfield CSV datasets.

Purpose: translate flat canonical exports into the immutable objects in ``domain``.
Responsibilities include schema and consistency checks, numeric parsing, grouping,
order preservation, provenance retention, and a separate runtime-oracle boundary.
This module does not read files at import time and does not perform PRNG work,
resource generation, prediction, or mismatch comparison. Static rarity from the
generation/IRES exports is authoritative; oracle rarity remains descriptive only.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TypeVar

from starfield_resource_reproducer.domain import (
    AtmosphericResourceRecord,
    Biome,
    CanonicalDatasetMetadata,
    CanonicalBodyResources,
    CanonicalResource,
    FormId,
    GenerationRarity,
    IRESNode,
    Planet,
    PlanetDirectoryRecord,
    ProjectData,
    ResourceRef,
    RSGDDefinition,
    RSGDResourceEntry,
    RSGDSource,
)


GENERATION_COLUMNS = frozenset(
    {
        "SourceFile",
        "ExtractTimestamp",
        "PlanetFormID",
        "PlanetEditorID",
        "PlanetName",
        "ResourceCreationSeed",
        "BiomeIndex",
        "BiomeFormID",
        "BiomeEditorID",
        "BiomeName",
        "BiomeSourceFile",
        "BiomeChance",
        "BiomeUnknown0Raw",
        "BiomeUnknown0UInt32",
        "RSGDSource",
        "RSGDFormID",
        "RSGDEditorID",
        "RSGDSourceFile",
        "RSGDResourceIndex",
        "ResourceFormID",
        "ResourceEditorID",
        "ResourceName",
        "ResourceRarity",
        "ResourceSourceFile",
        "BiomeCommonChance",
        "BiomeUncommonChance",
        "BiomeRareChance",
        "BiomeExoticChance",
        "BiomeUniqueChance",
        "BiomeSpecialChance",
        "BiomeEverywhereChance",
    }
)

IRES_COLUMNS = frozenset(
    {
        "SourceFile",
        "ExtractTimestamp",
        "FormID",
        "EditorID",
        "Name",
        "Rarity",
        "ChildFormID",
        "ChildEditorID",
        "ChildName",
        "ChildRarity",
        "ChildSourceFile",
    }
)

PLANET_DIRECTORY_COLUMNS = frozenset(
    {
        "SourceFile", "ExtractTimestamp", "PlanetFormID", "PlanetEditorID",
        "PlanetName", "BodyType", "StarSystemID", "SystemName",
        "ParentPlanetID", "PlanetID", "PlanetNotLandable", "OceanWorld",
    }
)

ORACLE_COLUMNS = frozenset(
    {
        "SystemName",
        "PlanetName",
        "BodyType",
        "PlanetFormID",
        "PlanetEditorID",
        "StarSystemID",
        "ParentPlanetID",
        "PlanetID",
        "ResourceCategory",
        "ResourceFormID",
        "ResourceEditorID",
        "ResourceName",
        "Rarity",
    }
)

ATMOSPHERIC_COLUMNS = frozenset(
    {
        "SourceFile", "ExtractTimestamp", "PlanetFormID", "PlanetEditorID",
        "PlanetName", "BodyType", "StarSystemID", "SystemName", "ParentPlanetID",
        "PlanetID", "AtmosphereFormID", "AtmosphereEditorID",
        "AtmosphereSourceFile", "AtmosphericResourceCount",
        "AtmosphericResourceIndex", "ResourceFormID", "ResourceEditorID",
        "ResourceName", "ResourceSourceFile", "ResourceDefinedByAtmosphereFormID",
        "ResourceDefinedByAtmosphereEditorID",
        "ResourceDefinedByAtmosphereSourceFile", "AtmosphereInheritanceDepth",
    }
)


class DataValidationError(ValueError):
    """Canonical input is malformed, incomplete, or internally contradictory."""


def _read_rows(
    path: Path, required_columns: frozenset[str], *, delimiter: str = ","
) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, delimiter=delimiter)
            columns = set(reader.fieldnames or ())
            missing = sorted(required_columns - columns)
            if missing:
                raise DataValidationError(
                    f"{path}: missing required column(s): {', '.join(missing)}"
                )
            rows = [dict(row) for row in reader]
            if not rows:
                raise DataValidationError(f"{path}: canonical data contains no data rows")
            for row_number, row in enumerate(rows, start=2):
                short_fields = sorted(
                    field for field in required_columns if row.get(field) is None
                )
                if short_fields:
                    raise DataValidationError(
                        f"{path}: row {row_number}: missing value(s) for column(s): "
                        f"{', '.join(short_fields)}"
                    )
            return rows
    except DataValidationError:
        raise
    except (OSError, csv.Error) as error:
        raise DataValidationError(f"{path}: could not read canonical data: {error}") from error


def _context(path: Path, row_number: int, detail: str = "") -> str:
    suffix = f" ({detail})" if detail else ""
    return f"{path}: row {row_number}{suffix}"


def _form_id(value: str, context: str, field: str) -> FormId:
    try:
        return FormId(value)
    except (TypeError, ValueError) as error:
        raise DataValidationError(f"{context}: invalid {field} {value!r}: {error}") from error


def _integer(
    value: str,
    context: str,
    field: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    try:
        parsed = int(value, 10)
    except (TypeError, ValueError) as error:
        raise DataValidationError(f"{context}: invalid integer {field}={value!r}") from error
    if minimum is not None and parsed < minimum:
        raise DataValidationError(f"{context}: {field}={parsed} is below {minimum}")
    if maximum is not None and parsed > maximum:
        raise DataValidationError(f"{context}: {field}={parsed} exceeds {maximum}")
    return parsed


def _decimal(value: str, context: str, field: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise DataValidationError(f"{context}: invalid numeric {field}={value!r}") from error
    if not parsed.is_finite():
        raise DataValidationError(f"{context}: {field} must be finite, got {value!r}")
    return parsed


E = TypeVar("E")


def _enum_value(enum_type: type[E], value: str, context: str, field: str) -> E:
    try:
        return enum_type(value)  # type: ignore[call-arg]
    except (TypeError, ValueError) as error:
        raise DataValidationError(f"{context}: invalid {field}={value!r}") from error


def _constant(rows: list[tuple[int, dict[str, str]]], field: str, context: str) -> str:
    values = {row[field] for _, row in rows}
    if len(values) != 1:
        raise DataValidationError(
            f"{context}: conflicting {field} values: {sorted(values)!r}"
        )
    return next(iter(values))


def _extract_timestamp(rows: list[dict[str, str]], path: Path) -> str:
    """Validate and return the one file-wide source extraction timestamp."""

    values = {row["ExtractTimestamp"] for row in rows}
    if len(values) != 1 or "" in values:
        raise DataValidationError(
            f"{path}: expected exactly one nonblank ExtractTimestamp; "
            f"found {sorted(values)!r}"
        )
    return next(iter(values))


def _flag(value: str, context: str, field: str) -> bool:
    """Parse the canonical xEdit numeric flag representation without guessing."""

    if value not in {"0", "1"}:
        raise DataValidationError(
            f"{context}: invalid boolean flag {field}={value!r}; expected '0' or '1'"
        )
    return value == "1"


def _check_resource_metadata(
    registry: dict[FormId, tuple[str, str, GenerationRarity]],
    form_id: FormId,
    editor_id: str,
    name: str,
    rarity: GenerationRarity,
    context: str,
) -> None:
    metadata = (editor_id, name, rarity)
    previous = registry.setdefault(form_id, metadata)
    if previous != metadata:
        raise DataValidationError(
            f"{context}: conflicting resource metadata for {form_id}: "
            f"{previous!r} versus {metadata!r}"
        )


def load_generation_data(path: Path) -> dict[FormId, Planet]:
    """Load static planet/biome/RSGD inputs keyed by canonical Planet FormID."""

    path = Path(path)
    raw_rows = _read_rows(path, GENERATION_COLUMNS)
    _extract_timestamp(raw_rows, path)
    grouped_planets: dict[FormId, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    resource_metadata: dict[FormId, tuple[str, str, GenerationRarity]] = {}

    for row_number, row in enumerate(raw_rows, start=2):
        context = _context(path, row_number)
        blank_fields = sorted(field for field in GENERATION_COLUMNS if row[field] == "")
        if blank_fields:
            raise DataValidationError(
                f"{context}: blank required value(s): {', '.join(blank_fields)}"
            )
        planet_id = _form_id(row["PlanetFormID"], context, "PlanetFormID")
        grouped_planets[planet_id].append((row_number, row))

    planets: dict[FormId, Planet] = {}
    for planet_id, planet_rows in grouped_planets.items():
        planet_context = f"{path}: PlanetFormID {planet_id}"
        editor_id = _constant(planet_rows, "PlanetEditorID", planet_context)
        name = _constant(planet_rows, "PlanetName", planet_context)
        source_file = _constant(planet_rows, "SourceFile", planet_context)
        seed_text = _constant(planet_rows, "ResourceCreationSeed", planet_context)
        seed = _integer(
            seed_text,
            planet_context,
            "ResourceCreationSeed",
            minimum=0,
            maximum=0xFFFFFFFF,
        )

        biome_groups: dict[int, list[tuple[int, dict[str, str]]]] = defaultdict(list)
        for row_number, row in planet_rows:
            biome_index = _integer(
                row["BiomeIndex"],
                _context(path, row_number, f"PlanetFormID {planet_id}"),
                "BiomeIndex",
                minimum=0,
            )
            biome_groups[biome_index].append((row_number, row))

        biomes = tuple(
            _build_biome(
                path,
                planet_id,
                biome_index,
                biome_groups[biome_index],
                resource_metadata,
            )
            for biome_index in sorted(biome_groups)
        )
        planets[planet_id] = Planet(
            form_id=planet_id,
            editor_id=editor_id,
            name=name,
            source_file=source_file,
            resource_creation_seed=seed,
            biomes=biomes,
        )

    return planets


def _build_biome(
    path: Path,
    planet_id: FormId,
    biome_index: int,
    rows: list[tuple[int, dict[str, str]]],
    resource_metadata: dict[FormId, tuple[str, str, GenerationRarity]],
) -> Biome:
    context = f"{path}: PlanetFormID {planet_id}, BiomeIndex {biome_index}"
    biome_id_text = _constant(rows, "BiomeFormID", context)
    editor_id = _constant(rows, "BiomeEditorID", context)
    name = _constant(rows, "BiomeName", context)
    source_file = _constant(rows, "BiomeSourceFile", context)
    chance_text = _constant(rows, "BiomeChance", context)
    unknown0_raw = _constant(rows, "BiomeUnknown0Raw", context)
    unknown0_text = _constant(rows, "BiomeUnknown0UInt32", context)
    biome_id = _form_id(biome_id_text, context, "BiomeFormID")

    definition_groups: dict[
        tuple[RSGDSource, FormId], list[tuple[int, dict[str, str]]]
    ] = defaultdict(list)
    for row_number, row in rows:
        row_context = _context(
            path, row_number, f"PlanetFormID {planet_id}, BiomeIndex {biome_index}"
        )
        source = _enum_value(RSGDSource, row["RSGDSource"], row_context, "RSGDSource")
        rsgd_id = _form_id(row["RSGDFormID"], row_context, "RSGDFormID")
        definition_groups[(source, rsgd_id)].append((row_number, row))

    definitions: dict[RSGDSource, RSGDDefinition] = {}
    for (source, rsgd_id), definition_rows in definition_groups.items():
        if source in definitions:
            raise DataValidationError(
                f"{context}: multiple {source.value} RSGD definitions are ambiguous"
            )
        definitions[source] = _build_rsgd_definition(
            path,
            planet_id,
            biome_index,
            source,
            rsgd_id,
            definition_rows,
            resource_metadata,
        )

    combined = definitions.get(RSGDSource.PNDT_AND_BIOM)
    if combined is not None:
        if len(definitions) != 1:
            raise DataValidationError(
                f"{context}: PNDT+BIOM cannot be combined with separate source definitions"
            )
        # The export uses PNDT+BIOM when both references resolve to the exact same
        # definition. Retaining one shared immutable value preserves that provenance
        # while exposing both source relationships without fabricating a merge.
        pndt_rsgd = combined
        biom_rsgd = combined
    else:
        pndt_rsgd = definitions.get(RSGDSource.PNDT)
        biom_rsgd = definitions.get(RSGDSource.BIOM)

    if pndt_rsgd is None and biom_rsgd is None:
        raise DataValidationError(f"{context}: biome has no RSGD definition")

    return Biome(
        index=biome_index,
        form_id=biome_id,
        editor_id=editor_id,
        name=name,
        source_file=source_file,
        chance=_decimal(chance_text, context, "BiomeChance"),
        unknown0_raw=unknown0_raw,
        unknown0_uint32=_integer(
            unknown0_text, context, "BiomeUnknown0UInt32", minimum=0, maximum=0xFFFFFFFF
        ),
        pndt_rsgd=pndt_rsgd,
        biom_rsgd=biom_rsgd,
    )


def _build_rsgd_definition(
    path: Path,
    planet_id: FormId,
    biome_index: int,
    source: RSGDSource,
    rsgd_id: FormId,
    rows: list[tuple[int, dict[str, str]]],
    resource_metadata: dict[FormId, tuple[str, str, GenerationRarity]],
) -> RSGDDefinition:
    context = (
        f"{path}: PlanetFormID {planet_id}, BiomeIndex {biome_index}, "
        f"{source.value} RSGDFormID {rsgd_id}"
    )
    editor_id = _constant(rows, "RSGDEditorID", context)
    source_file = _constant(rows, "RSGDSourceFile", context)
    entries_by_index: dict[int, RSGDResourceEntry] = {}

    for row_number, row in rows:
        row_context = _context(path, row_number, context.split(": ", 1)[-1])
        index = _integer(
            row["RSGDResourceIndex"], row_context, "RSGDResourceIndex", minimum=0
        )
        if index in entries_by_index:
            raise DataValidationError(
                f"{row_context}: duplicate RSGDResourceIndex {index} for {rsgd_id}"
            )
        resource_id = _form_id(row["ResourceFormID"], row_context, "ResourceFormID")
        rarity = _enum_value(
            GenerationRarity, row["ResourceRarity"], row_context, "ResourceRarity"
        )
        _check_resource_metadata(
            resource_metadata,
            resource_id,
            row["ResourceEditorID"],
            row["ResourceName"],
            rarity,
            row_context,
        )
        entries_by_index[index] = RSGDResourceEntry(
            index=index,
            resource_form_id=resource_id,
            resource_editor_id=row["ResourceEditorID"],
            resource_name=row["ResourceName"],
            resource_rarity=rarity,
            resource_source_file=row["ResourceSourceFile"],
            common_chance=_decimal(row["BiomeCommonChance"], row_context, "BiomeCommonChance"),
            uncommon_chance=_decimal(
                row["BiomeUncommonChance"], row_context, "BiomeUncommonChance"
            ),
            rare_chance=_decimal(row["BiomeRareChance"], row_context, "BiomeRareChance"),
            exotic_chance=_decimal(
                row["BiomeExoticChance"], row_context, "BiomeExoticChance"
            ),
            unique_chance=_decimal(
                row["BiomeUniqueChance"], row_context, "BiomeUniqueChance"
            ),
            special_chance=_decimal(
                row["BiomeSpecialChance"], row_context, "BiomeSpecialChance"
            ),
            everywhere_chance=_decimal(
                row["BiomeEverywhereChance"], row_context, "BiomeEverywhereChance"
            ),
        )

    indices = sorted(entries_by_index)
    expected = list(range(len(indices)))
    if indices != expected:
        raise DataValidationError(
            f"{context}: RSGDResourceIndex values must be contiguous from zero; "
            f"found {indices!r}"
        )
    # RSGDResourceIndex is generation-significant; no other ordering is valid.
    entries = tuple(entries_by_index[index] for index in indices)
    return RSGDDefinition(source, rsgd_id, editor_id, source_file, entries)


def load_ires_hierarchy(path: Path) -> dict[FormId, IRESNode]:
    """Load the direct IRES edge graph, including parent-only and child-only nodes."""

    path = Path(path)
    raw_rows = _read_rows(path, IRES_COLUMNS)
    _extract_timestamp(raw_rows, path)
    metadata: dict[FormId, tuple[str, str, GenerationRarity, str]] = {}
    child_ids: dict[FormId, list[FormId]] = defaultdict(list)
    seen_edges: set[tuple[FormId, FormId]] = set()

    for row_number, row in enumerate(raw_rows, start=2):
        context = _context(path, row_number)
        blank_parent_fields = [
            field for field in ("SourceFile", "FormID", "EditorID", "Name", "Rarity")
            if not row[field]
        ]
        if blank_parent_fields:
            raise DataValidationError(
                f"{context}: blank required value(s): {', '.join(blank_parent_fields)}"
            )
        parent_id = _form_id(row["FormID"], context, "FormID")
        parent_rarity = _enum_value(
            GenerationRarity, row["Rarity"], context, "Rarity"
        )
        parent_metadata = (
            row["EditorID"], row["Name"], parent_rarity, row["SourceFile"]
        )
        previous = metadata.setdefault(parent_id, parent_metadata)
        if previous != parent_metadata:
            raise DataValidationError(
                f"{context}: conflicting resource metadata for {parent_id}: "
                f"{previous!r} versus {parent_metadata!r}"
            )
        child_ids.setdefault(parent_id, [])

        child_fields = (
            row["ChildSourceFile"],
            row["ChildFormID"],
            row["ChildEditorID"],
            row["ChildName"],
            row["ChildRarity"],
        )
        if not any(child_fields):
            continue
        if not all(child_fields):
            raise DataValidationError(
                f"{context}: child identity is only partially populated: {child_fields!r}"
            )
        child_id = _form_id(row["ChildFormID"], context, "ChildFormID")
        child_rarity = _enum_value(
            GenerationRarity, row["ChildRarity"], context, "ChildRarity"
        )
        child_metadata = (
            row["ChildEditorID"], row["ChildName"], child_rarity,
            row["ChildSourceFile"],
        )
        previous = metadata.setdefault(child_id, child_metadata)
        if previous != child_metadata:
            raise DataValidationError(
                f"{context}: conflicting resource metadata for {child_id}: "
                f"{previous!r} versus {child_metadata!r}"
            )
        edge = (parent_id, child_id)
        if edge in seen_edges:
            raise DataValidationError(
                f"{context}: duplicate IRES edge {parent_id} -> {child_id}"
            )
        seen_edges.add(edge)
        child_ids[parent_id].append(child_id)
        child_ids.setdefault(child_id, [])

    nodes: dict[FormId, IRESNode] = {}
    for form_id, (editor_id, name, rarity, source_file) in metadata.items():
        children = tuple(
            ResourceRef(
                child_id,
                metadata[child_id][0],
                metadata[child_id][1],
                metadata[child_id][2],
                metadata[child_id][3],
            )
            for child_id in child_ids[form_id]
        )
        nodes[form_id] = IRESNode(
            form_id, editor_id, name, rarity, children, source_file=source_file
        )
    return nodes


def load_canonical_oracle(path: Path) -> dict[FormId, CanonicalBodyResources]:
    """Load runtime output records with an inorganic FormID membership lookup."""

    path = Path(path)
    raw_rows = _read_rows(path, ORACLE_COLUMNS)
    body_rows: dict[FormId, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    seen_pairs: set[tuple[FormId, FormId]] = set()
    resource_metadata: dict[FormId, tuple[str, str, str]] = {}

    for row_number, row in enumerate(raw_rows, start=2):
        context = _context(path, row_number)
        blank_fields = sorted(field for field in ORACLE_COLUMNS if row[field] == "")
        if blank_fields:
            raise DataValidationError(
                f"{context}: blank required value(s): {', '.join(blank_fields)}"
            )
        planet_id = _form_id(row["PlanetFormID"], context, "PlanetFormID")
        resource_id = _form_id(row["ResourceFormID"], context, "ResourceFormID")
        pair = (planet_id, resource_id)
        if pair in seen_pairs:
            raise DataValidationError(
                f"{context}: duplicate (PlanetFormID, ResourceFormID) pair "
                f"({planet_id}, {resource_id})"
            )
        seen_pairs.add(pair)
        metadata = (row["ResourceEditorID"], row["ResourceName"], row["Rarity"])
        previous = resource_metadata.setdefault(resource_id, metadata)
        if previous != metadata:
            raise DataValidationError(
                f"{context}: conflicting oracle resource metadata for {resource_id}: "
                f"{previous!r} versus {metadata!r}"
            )
        if row["ResourceCategory"] not in {"Inorganic", "Organic"}:
            raise DataValidationError(
                f"{context}: unsupported ResourceCategory={row['ResourceCategory']!r}"
            )
        body_rows[planet_id].append((row_number, row))

    oracle: dict[FormId, CanonicalBodyResources] = {}
    body_fields = (
        "SystemName",
        "PlanetName",
        "BodyType",
        "PlanetEditorID",
        "StarSystemID",
        "ParentPlanetID",
        "PlanetID",
    )
    for planet_id, rows in body_rows.items():
        context = f"{path}: PlanetFormID {planet_id}"
        body_metadata = {field: _constant(rows, field, context) for field in body_fields}
        inorganic: list[CanonicalResource] = []
        organic: list[CanonicalResource] = []
        for row_number, row in rows:
            resource = CanonicalResource(
                resource_form_id=_form_id(
                    row["ResourceFormID"], _context(path, row_number), "ResourceFormID"
                ),
                resource_editor_id=row["ResourceEditorID"],
                resource_name=row["ResourceName"],
                oracle_rarity=row["Rarity"],
                category=row["ResourceCategory"],
            )
            (inorganic if resource.category == "Inorganic" else organic).append(resource)
        oracle[planet_id] = CanonicalBodyResources(
            planet_form_id=planet_id,
            planet_editor_id=body_metadata["PlanetEditorID"],
            planet_name=body_metadata["PlanetName"],
            system_name=body_metadata["SystemName"],
            body_type=body_metadata["BodyType"],
            inorganic_resources=frozenset(
                resource.resource_form_id for resource in inorganic
            ),
            inorganic_resource_records=tuple(inorganic),
            organic_resource_records=tuple(organic),
        )
    return oracle


def load_planet_directory(path: Path) -> dict[FormId, PlanetDirectoryRecord]:
    """Load canonical body-directory metadata keyed only by Planet FormID."""

    path = Path(path)
    raw_rows = _read_rows(path, PLANET_DIRECTORY_COLUMNS)
    _extract_timestamp(raw_rows, path)
    directory: dict[FormId, PlanetDirectoryRecord] = {}
    required_identity = (
        "SourceFile", "PlanetFormID", "PlanetEditorID", "PlanetName", "BodyType",
        "StarSystemID", "SystemName", "ParentPlanetID", "PlanetID",
        "PlanetNotLandable", "OceanWorld",
    )
    for row_number, row in enumerate(raw_rows, start=2):
        context = _context(path, row_number)
        blanks = sorted(field for field in required_identity if not row[field])
        if blanks:
            raise DataValidationError(
                f"{context}: blank required value(s): {', '.join(blanks)}"
            )
        planet_form_id = _form_id(row["PlanetFormID"], context, "PlanetFormID")
        if planet_form_id in directory:
            raise DataValidationError(
                f"{context}: duplicate PlanetFormID {planet_form_id}"
            )
        directory[planet_form_id] = PlanetDirectoryRecord(
            source_file=row["SourceFile"],
            extract_timestamp=row["ExtractTimestamp"],
            planet_form_id=planet_form_id,
            planet_editor_id=row["PlanetEditorID"],
            planet_name=row["PlanetName"],
            body_type=row["BodyType"],
            star_system_id=_integer(
                row["StarSystemID"], context, "StarSystemID", minimum=0
            ),
            system_name=row["SystemName"],
            parent_planet_id=_integer(
                row["ParentPlanetID"], context, "ParentPlanetID", minimum=0
            ),
            planet_id=_integer(row["PlanetID"], context, "PlanetID", minimum=0),
            planet_not_landable=_flag(
                row["PlanetNotLandable"], context, "PlanetNotLandable"
            ),
            ocean_world=_flag(row["OceanWorld"], context, "OceanWorld"),
        )
    return directory


def _dataset_metadata(
    path: Path, required_columns: frozenset[str], dataset_name: str
) -> CanonicalDatasetMetadata:
    """Read only file-level production metadata for the project aggregate."""

    rows = _read_rows(path, required_columns)
    return CanonicalDatasetMetadata(
        dataset_name=dataset_name,
        filename=path.name,
        extract_timestamp=_extract_timestamp(rows, path),
        row_count=len(rows),
    )


def load_atmospheric_resources(
    path: Path,
) -> dict[FormId, tuple[AtmosphericResourceRecord, ...]]:
    """Load ordered atmospheric occurrences from the explicit CSV export."""

    path = Path(path)
    raw_rows = _read_rows(path, ATMOSPHERIC_COLUMNS)
    _extract_timestamp(raw_rows, path)
    grouped: dict[FormId, list[tuple[int, AtmosphericResourceRecord]]] = defaultdict(list)
    seen_pairs: dict[tuple[FormId, FormId], AtmosphericResourceRecord] = {}

    for row_number, row in enumerate(raw_rows, start=2):
        context = _context(path, row_number)
        blank_fields = sorted(field for field in ATMOSPHERIC_COLUMNS if row[field] == "")
        if blank_fields:
            raise DataValidationError(
                f"{context}: blank required value(s): {', '.join(blank_fields)}"
            )
        planet_form_id = _form_id(row["PlanetFormID"], context, "PlanetFormID")
        resource_form_id = _form_id(row["ResourceFormID"], context, "ResourceFormID")
        record = AtmosphericResourceRecord(
            source_file=row["SourceFile"],
            extract_timestamp=row["ExtractTimestamp"],
            planet_form_id=planet_form_id,
            planet_editor_id=row["PlanetEditorID"],
            planet_name=row["PlanetName"],
            body_type=row["BodyType"],
            star_system_id=_integer(row["StarSystemID"], context, "StarSystemID", minimum=0),
            system_name=row["SystemName"],
            parent_planet_id=_integer(
                row["ParentPlanetID"], context, "ParentPlanetID", minimum=0
            ),
            planet_id=_integer(row["PlanetID"], context, "PlanetID", minimum=0),
            atmosphere_form_id=_form_id(
                row["AtmosphereFormID"], context, "AtmosphereFormID"
            ),
            atmosphere_editor_id=row["AtmosphereEditorID"],
            atmosphere_source_file=row["AtmosphereSourceFile"],
            atmospheric_resource_count=_integer(
                row["AtmosphericResourceCount"],
                context,
                "AtmosphericResourceCount",
                minimum=1,
            ),
            atmospheric_resource_index=_integer(
                row["AtmosphericResourceIndex"],
                context,
                "AtmosphericResourceIndex",
                minimum=0,
            ),
            resource_form_id=resource_form_id,
            resource_editor_id=row["ResourceEditorID"],
            resource_name=row["ResourceName"],
            resource_source_file=row["ResourceSourceFile"],
            defined_by_atmosphere_form_id=_form_id(
                row["ResourceDefinedByAtmosphereFormID"],
                context,
                "ResourceDefinedByAtmosphereFormID",
            ),
            defined_by_atmosphere_editor_id=row[
                "ResourceDefinedByAtmosphereEditorID"
            ],
            defined_by_atmosphere_source_file=row[
                "ResourceDefinedByAtmosphereSourceFile"
            ],
            atmosphere_inheritance_depth=_integer(
                row["AtmosphereInheritanceDepth"],
                context,
                "AtmosphereInheritanceDepth",
                minimum=0,
            ),
        )
        pair = (planet_form_id, resource_form_id)
        if pair in seen_pairs:
            qualifier = "contradictory " if seen_pairs[pair] != record else ""
            raise DataValidationError(
                f"{context}: {qualifier}duplicate atmospheric planet/resource row "
                f"({planet_form_id}, {resource_form_id})"
            )
        seen_pairs[pair] = record
        grouped[planet_form_id].append((row_number, record))

    result: dict[FormId, tuple[AtmosphericResourceRecord, ...]] = {}
    for planet_form_id, numbered_records in grouped.items():
        records = [record for _, record in numbered_records]
        planet_context = f"{path}: PlanetFormID {planet_form_id}"
        counts = {record.atmospheric_resource_count for record in records}
        if counts != {len(records)}:
            raise DataValidationError(
                f"{planet_context}: AtmosphericResourceCount values {sorted(counts)!r} "
                f"do not match {len(records)} exported rows"
            )
        indices = sorted(record.atmospheric_resource_index for record in records)
        if indices != list(range(len(records))):
            raise DataValidationError(
                f"{planet_context}: AtmosphericResourceIndex values must be contiguous "
                f"from zero; found {indices!r}"
            )
        identity_fields = (
            "source_file", "extract_timestamp", "planet_editor_id", "planet_name",
            "body_type", "star_system_id", "system_name", "parent_planet_id",
            "planet_id", "atmosphere_form_id",
            "atmosphere_editor_id", "atmosphere_source_file",
        )
        for field_name in identity_fields:
            values = {getattr(record, field_name) for record in records}
            if len(values) != 1:
                raise DataValidationError(
                    f"{planet_context}: conflicting {field_name} values: {sorted(values)!r}"
                )
        result[planet_form_id] = tuple(
            sorted(records, key=lambda record: record.atmospheric_resource_index)
        )
    return result


def validate_canonical_input_coherence(
    planets: dict[FormId, Planet],
    ires_nodes: dict[FormId, IRESNode],
    atmospheric: dict[FormId, tuple[AtmosphericResourceRecord, ...]],
    directory: dict[FormId, PlanetDirectoryRecord],
) -> None:
    """Fail fast when independently exported canonical identities drift."""

    for planet_form_id, planet in planets.items():
        body = directory.get(planet_form_id)
        if body is None:
            raise DataValidationError(
                f"generation PlanetFormID {planet_form_id} is absent from planet directory"
            )
        generation_identity = (planet.editor_id, planet.name, planet.source_file)
        directory_identity = (
            body.planet_editor_id, body.planet_name, body.source_file
        )
        if generation_identity != directory_identity:
            raise DataValidationError(
                f"generation/directory identity conflicts for {planet_form_id}: "
                f"{generation_identity!r} versus {directory_identity!r}"
            )

        for biome in planet.biomes:
            for definition in filter(None, (biome.pndt_rsgd, biome.biom_rsgd)):
                for entry in definition.entries:
                    node = ires_nodes.get(entry.resource_form_id)
                    if node is None:
                        raise DataValidationError(
                            f"generation resource {entry.resource_form_id} has no IRES node"
                        )
                    generated = (
                        entry.resource_editor_id, entry.resource_name,
                        entry.resource_rarity, entry.resource_source_file,
                    )
                    graph = (node.editor_id, node.name, node.rarity, node.source_file)
                    if generated != graph:
                        raise DataValidationError(
                            f"generation/IRES resource identity conflicts for "
                            f"{entry.resource_form_id}: {generated!r} versus {graph!r}"
                        )

    for planet_form_id, records in atmospheric.items():
        body = directory.get(planet_form_id)
        if body is None:
            raise DataValidationError(
                f"atmosphere PlanetFormID {planet_form_id} is absent from planet directory"
            )
        first = records[0]
        atmospheric_body_identity = (
            first.planet_editor_id, first.planet_name, first.body_type,
            first.star_system_id, first.system_name, first.parent_planet_id,
            first.planet_id, first.source_file,
        )
        directory_identity = (
            body.planet_editor_id, body.planet_name, body.body_type,
            body.star_system_id, body.system_name, body.parent_planet_id,
            body.planet_id, body.source_file,
        )
        if atmospheric_body_identity != directory_identity:
            raise DataValidationError(
                f"atmosphere/directory identity conflicts for {planet_form_id}: "
                f"{atmospheric_body_identity!r} versus {directory_identity!r}"
            )
        planet = planets.get(planet_form_id)
        # The atmospheric export may cover bodies outside the current PNDT
        # intersection. Retain them; validate planet identity only on overlap.
        if planet is not None and any(
            (record.planet_editor_id, record.planet_name)
            != (planet.editor_id, planet.name)
            for record in records
        ):
            raise DataValidationError(
                f"atmospheric planet metadata conflicts for {planet_form_id}"
            )
        for record in records:
            node = ires_nodes.get(record.resource_form_id)
            if node is None:
                raise DataValidationError(
                    f"atmospheric resource {record.resource_form_id} has no IRES node"
                )
            if (
                record.resource_editor_id, record.resource_name,
                record.resource_source_file,
            ) != (node.editor_id, node.name, node.source_file):
                raise DataValidationError(
                    f"atmospheric resource metadata conflicts for {record.resource_form_id}: "
                    f"{(record.resource_editor_id, record.resource_name, record.resource_source_file)!r} "
                    f"versus {(node.editor_id, node.name, node.source_file)!r}"
                )


def load_project_data(
    data_dir: Path, *, atmospheric_path: Path | None = None
) -> ProjectData:
    """Load four production inputs plus the isolated validation-only oracle."""

    data_dir = Path(data_dir)
    planets = load_generation_data(data_dir / "planet-resource-generation.csv")
    ires_nodes = load_ires_hierarchy(data_dir / "ires-hierarchy.csv")
    atmospheric = load_atmospheric_resources(
        atmospheric_path or data_dir / "planet-atmospheric-resources.csv"
    )
    directory = load_planet_directory(data_dir / "planet-directory.csv")
    validate_canonical_input_coherence(planets, ires_nodes, atmospheric, directory)
    production_paths = {
        "planet_resource_generation": (
            data_dir / "planet-resource-generation.csv", GENERATION_COLUMNS
        ),
        "ires_hierarchy": (data_dir / "ires-hierarchy.csv", IRES_COLUMNS),
        "planet_atmospheric_resources": (
            atmospheric_path or data_dir / "planet-atmospheric-resources.csv",
            ATMOSPHERIC_COLUMNS,
        ),
        "planet_directory": (data_dir / "planet-directory.csv", PLANET_DIRECTORY_COLUMNS),
    }
    return ProjectData(
        planets=planets,
        ires_nodes=ires_nodes,
        oracle=load_canonical_oracle(data_dir / "planet-all-resources.csv"),
        atmospheric_resources=atmospheric,
        planet_directory=directory,
        dataset_metadata={
            name: _dataset_metadata(Path(path), columns, name)
            for name, (path, columns) in production_paths.items()
        },
    )
