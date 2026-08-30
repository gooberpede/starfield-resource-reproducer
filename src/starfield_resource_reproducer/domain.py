"""Typed values for canonical Starfield resource data.

Purpose: provide immutable domain objects at the boundary between CSV loading and
later resource-generation work. Responsibilities include stable FormID identity,
static generation categories, ordered biome/RSGD data, the direct IRES graph, and
separate runtime-oracle records. CSV parsing, PRNG behavior, generation, and
prediction validation deliberately live elsewhere. The PNDT-over-BIOM property is
the only recovered runtime rule represented here because its precedence is PROVEN.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import re


_FORM_ID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$")


@dataclass(frozen=True, order=True)
class FormId:
    """An eight-digit canonical hexadecimal FormID with a derived numeric view."""

    text: str

    def __post_init__(self) -> None:
        value = self.text
        if not isinstance(value, str):
            raise ValueError(f"FormID must be text, got {type(value).__name__}")
        if value.lower().startswith("0x"):
            value = value[2:]
        if not _FORM_ID_PATTERN.fullmatch(value):
            raise ValueError(
                f"FormID must contain exactly 8 hexadecimal digits, got {self.text!r}"
            )
        object.__setattr__(self, "text", value.upper())

    @property
    def numeric(self) -> int:
        """Return the unsigned numeric value without replacing canonical text."""

        return int(self.text, 16)

    def __str__(self) -> str:
        return self.text


class GenerationRarity(str, Enum):
    """Authoritative static generation categories recovered from IRES data."""

    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    EXOTIC = "Exotic"
    UNIQUE = "Unique"
    SPECIAL = "Special"
    EVERYWHERE = "Everywhere"


class RSGDSource(str, Enum):
    """Provenance of an RSGD reference retained by the static export."""

    PNDT = "PNDT"
    BIOM = "BIOM"
    PNDT_AND_BIOM = "PNDT+BIOM"


@dataclass(frozen=True)
class ResourceRef:
    """Stable resource identity and authoritative generation metadata."""

    form_id: FormId
    editor_id: str
    name: str
    rarity: GenerationRarity
    source_file: str | None = None


@dataclass(frozen=True)
class RSGDResourceEntry:
    """One generation-significant RSGD resource-array entry."""

    index: int
    resource_form_id: FormId
    resource_editor_id: str
    resource_name: str
    resource_rarity: GenerationRarity
    resource_source_file: str
    common_chance: Decimal
    uncommon_chance: Decimal
    rare_chance: Decimal
    exotic_chance: Decimal
    unique_chance: Decimal
    special_chance: Decimal
    everywhere_chance: Decimal

    @property
    def resource(self) -> ResourceRef:
        """Expose the entry's resource metadata as a compact reference."""

        return ResourceRef(
            form_id=self.resource_form_id,
            editor_id=self.resource_editor_id,
            name=self.resource_name,
            rarity=self.resource_rarity,
            source_file=self.resource_source_file,
        )


@dataclass(frozen=True)
class RSGDDefinition:
    """One unmerged RSGD definition associated with a particular biome."""

    source: RSGDSource
    form_id: FormId
    editor_id: str
    source_file: str
    entries: tuple[RSGDResourceEntry, ...]


@dataclass(frozen=True)
class Biome:
    """A PNDT biome entry retaining both possible RSGD sources."""

    index: int
    form_id: FormId
    editor_id: str
    name: str
    source_file: str
    chance: Decimal
    unknown0_raw: str
    unknown0_uint32: int
    pndt_rsgd: RSGDDefinition | None
    biom_rsgd: RSGDDefinition | None

    @property
    def effective_rsgd(self) -> RSGDDefinition:
        """Resolve the PROVEN PNDT-over-BIOM static precedence rule."""

        definition = self.pndt_rsgd or self.biom_rsgd
        if definition is None:  # Defensive for manually constructed domain values.
            raise ValueError(f"Biome {self.form_id} has no RSGD definition")
        return definition


@dataclass(frozen=True)
class Planet:
    """Static generation inputs for one planet, with biomes in PNDT order."""

    form_id: FormId
    editor_id: str
    name: str
    source_file: str
    resource_creation_seed: int
    biomes: tuple[Biome, ...]


@dataclass(frozen=True)
class IRESNode:
    """One IRES resource and its direct children in source edge-list order."""

    form_id: FormId
    editor_id: str
    name: str
    rarity: GenerationRarity
    children: tuple[ResourceRef, ...]


@dataclass(frozen=True)
class CanonicalResource:
    """Runtime-oracle resource metadata, intentionally not generation metadata."""

    resource_form_id: FormId
    resource_editor_id: str
    resource_name: str
    oracle_rarity: str
    category: str


@dataclass(frozen=True)
class CanonicalBodyResources:
    """Runtime-oracle records for a body, kept separate from generation inputs."""

    planet_form_id: FormId
    planet_editor_id: str
    planet_name: str
    system_name: str
    body_type: str
    inorganic_resources: frozenset[FormId]
    inorganic_resource_records: tuple[CanonicalResource, ...]
    organic_resource_records: tuple[CanonicalResource, ...]


@dataclass(frozen=True)
class ProjectData:
    """A convenience bundle of independently loadable canonical datasets."""

    planets: dict[FormId, Planet]
    ires_nodes: dict[FormId, IRESNode]
    oracle: dict[FormId, CanonicalBodyResources]
