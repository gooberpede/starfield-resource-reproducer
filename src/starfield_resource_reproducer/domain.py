"""Typed values for canonical Starfield resource data.

Purpose: provide immutable domain objects at the boundary between CSV loading and
later resource-generation work. Responsibilities include stable FormID identity,
static generation categories, ordered biome/RSGD and atmospheric data, the body
directory, the direct IRES graph, and separate runtime-oracle records. Parsing,
PRNG behavior, generation, and prediction validation deliberately live elsewhere. The PNDT-over-BIOM property is
the only recovered runtime rule represented here because its precedence is PROVEN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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


class ResourceProvenance(str, Enum):
    """Stable resource-origin vocabulary for accepted occurrence products."""

    ATMOSPHERE = "ATMOSPHERE"
    ATMO = "ATMOSPHERE"  # Compatibility alias for the pre-10C internal name.
    EVERYWHERE = "EVERYWHERE"
    SPECIAL = "SPECIAL"
    COMMON_ROOT = "COMMON_ROOT"
    COMMON = "COMMON_ROOT"  # Compatibility alias for the pre-10C internal name.
    DESCENDANT = "DESCENDANT"


class CommonAssignmentMechanism(str, Enum):
    """How a biome obtained its Common-family configuration."""

    NEW_FAMILY = "NEW_FAMILY"
    NORMAL_CACHE_REUSE = "NORMAL_CACHE_REUSE"
    GUARD_MATCHED_FALLBACK = "GUARD_MATCHED_FALLBACK"
    GUARD_GENERAL_FALLBACK = "GUARD_GENERAL_FALLBACK"
    NO_COMMON_ASSIGNMENT = "NO_COMMON_ASSIGNMENT"


class CommonGuardReason(str, Enum):
    """The distinct pre-selector guard that entered Common fallback."""

    COMMON_TREE_LIMIT = "COMMON_TREE_LIMIT"
    SHARED_RESOURCE_CAPACITY = "SHARED_RESOURCE_CAPACITY"


class CommonNoAssignmentReason(str, Enum):
    """Why a biome has no Common-family assignment."""

    NORMAL_SELECTOR_NO_RESULT = "NORMAL_SELECTOR_NO_RESULT"
    GUARD_RSGD_HAS_NO_COMMON = "GUARD_RSGD_HAS_NO_COMMON"
    GUARD_EMPTY_FAMILY_CACHE = "GUARD_EMPTY_FAMILY_CACHE"


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
class AtmosphericResourceRecord:
    """One ordered atmospheric-resource export row with source provenance."""

    source_file: str
    extract_timestamp: str
    planet_form_id: FormId
    planet_editor_id: str
    planet_name: str
    body_type: str
    star_system_id: int
    system_name: str
    parent_planet_id: int
    planet_id: int
    atmosphere_form_id: FormId
    atmosphere_editor_id: str
    atmosphere_source_file: str
    atmospheric_resource_count: int
    atmospheric_resource_index: int
    resource_form_id: FormId
    resource_editor_id: str
    resource_name: str
    resource_source_file: str
    defined_by_atmosphere_form_id: FormId
    defined_by_atmosphere_editor_id: str
    defined_by_atmosphere_source_file: str
    atmosphere_inheritance_depth: int


@dataclass(frozen=True, slots=True)
class PlanetDirectoryRecord:
    """Canonical PNDT body metadata keyed by Planet FormID.

    Environmental power and habitation values are v4 directory metadata only;
    they are not reconstructed inorganic-generation inputs.
    """

    source_file: str
    extract_timestamp: str
    planet_form_id: FormId
    planet_editor_id: str
    planet_name: str
    body_type: str
    star_system_id: int
    system_name: str
    parent_planet_id: int
    planet_id: int
    planet_not_landable: bool
    ocean_world: bool
    solar_array_power: int | None
    wind_turbine_power: int | None
    planetary_habitation_rank: int | None


@dataclass(frozen=True, slots=True)
class CanonicalDatasetMetadata:
    """Small file-production descriptor retained outside row domain objects."""

    dataset_name: str
    filename: str
    extract_timestamp: str
    row_count: int


@dataclass(frozen=True, slots=True)
class ResourceOccurrence:
    """One provenance-specific resource contribution or rejected insertion.

    ``occupies_state`` is true both for a new slot and for an already occupied
    FormID. A false value records a capacity-rejected contribution without
    incorrectly presenting it as part of the final planet state.
    """

    resource: ResourceRef
    provenance: ResourceProvenance
    occupies_state: bool
    occupied_new_slot: bool
    biome_index: int | None = None
    biome_form_id: FormId | None = None
    effective_rsgd_form_id: FormId | None = None
    rsgd_source: RSGDSource | None = None
    root_form_id: FormId | None = None
    descendant_rarity: GenerationRarity | None = None
    common_assignment_mechanism: CommonAssignmentMechanism | None = None
    common_guard_reason: CommonGuardReason | None = None
    atmospheric_record: AtmosphericResourceRecord | None = None


@dataclass(frozen=True)
class IRESNode:
    """One IRES resource and its direct children in source edge-list order."""

    form_id: FormId
    editor_id: str
    name: str
    rarity: GenerationRarity
    children: tuple[ResourceRef, ...]
    source_file: str | None = None


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
    atmospheric_resources: dict[
        FormId, tuple[AtmosphericResourceRecord, ...]
    ] = field(default_factory=dict)
    planet_directory: dict[FormId, PlanetDirectoryRecord] = field(default_factory=dict)
    dataset_metadata: dict[str, CanonicalDatasetMetadata] = field(default_factory=dict)
