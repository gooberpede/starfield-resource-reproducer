"""Load and validate the three canonical Starfield CSV datasets.

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
    Biome,
    CanonicalBodyResources,
    CanonicalResource,
    FormId,
    GenerationRarity,
    IRESNode,
    Planet,
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
        "FormID",
        "EditorID",
        "Name",
        "Rarity",
        "ChildFormID",
        "ChildEditorID",
        "ChildName",
        "ChildRarity",
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


class DataValidationError(ValueError):
    """Canonical input is malformed, incomplete, or internally contradictory."""


def _read_rows(path: Path, required_columns: frozenset[str]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            columns = set(reader.fieldnames or ())
            missing = sorted(required_columns - columns)
            if missing:
                raise DataValidationError(
                    f"{path}: missing required column(s): {', '.join(missing)}"
                )
            rows = [dict(row) for row in reader]
            if not rows:
                raise DataValidationError(f"{path}: canonical CSV contains no data rows")
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
        raise DataValidationError(f"{path}: could not read canonical CSV: {error}") from error


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
    metadata: dict[FormId, tuple[str, str, GenerationRarity]] = {}
    child_ids: dict[FormId, list[FormId]] = defaultdict(list)
    seen_edges: set[tuple[FormId, FormId]] = set()

    for row_number, row in enumerate(raw_rows, start=2):
        context = _context(path, row_number)
        blank_parent_fields = [
            field for field in ("FormID", "EditorID", "Name", "Rarity") if not row[field]
        ]
        if blank_parent_fields:
            raise DataValidationError(
                f"{context}: blank required value(s): {', '.join(blank_parent_fields)}"
            )
        parent_id = _form_id(row["FormID"], context, "FormID")
        parent_rarity = _enum_value(
            GenerationRarity, row["Rarity"], context, "Rarity"
        )
        _check_resource_metadata(
            metadata,
            parent_id,
            row["EditorID"],
            row["Name"],
            parent_rarity,
            context,
        )
        child_ids.setdefault(parent_id, [])

        child_fields = (
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
        _check_resource_metadata(
            metadata,
            child_id,
            row["ChildEditorID"],
            row["ChildName"],
            child_rarity,
            context,
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
    for form_id, (editor_id, name, rarity) in metadata.items():
        children = tuple(
            ResourceRef(child_id, *metadata[child_id]) for child_id in child_ids[form_id]
        )
        nodes[form_id] = IRESNode(form_id, editor_id, name, rarity, children)
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


def load_project_data(data_dir: Path) -> ProjectData:
    """Load all canonical datasets from an explicit project data directory."""

    data_dir = Path(data_dir)
    return ProjectData(
        planets=load_generation_data(data_dir / "PlanetResourceGeneration_v5.csv"),
        ires_nodes=load_ires_hierarchy(data_dir / "Starfield_IRES_Hierarchy.csv"),
        oracle=load_canonical_oracle(data_dir / "planet-all-resources.csv"),
    )
