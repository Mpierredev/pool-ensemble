from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from collections.abc import Mapping

RoleName = Literal["top", "jungle", "mid", "bot", "support"]
ClassName = Literal[
    "enchanter",
    "mage",
    "assassin",
    "diver",
    "bruiser",
    "marksman",
    "tank",
    "duelist",
    "specialist",
]
DamageType = Literal["physical", "magic", "true"]
StyleName = Literal[
    "burst",
    "poke",
    "control",
    "pick",
    "engage",
    "dive",
    "peel",
    "skirmish",
    "splitpush",
    "scaling",
    "chaos",
]
TraitId = Literal[
    "one_trick",
    "wide_pool",
    "off_meta",
    "all_roles",
    "single_role",
    "low_mobility",
    "high_mobility",
]
Locale = Literal["pt-BR", "en"]

ROLES: tuple[RoleName, ...] = ("top", "jungle", "mid", "bot", "support")
CLASSES: tuple[ClassName, ...] = (
    "enchanter",
    "mage",
    "assassin",
    "diver",
    "bruiser",
    "marksman",
    "tank",
    "duelist",
    "specialist",
)
DAMAGE_TYPES: tuple[DamageType, ...] = ("physical", "magic", "true")
STYLES: tuple[StyleName, ...] = (
    "burst",
    "poke",
    "control",
    "pick",
    "engage",
    "dive",
    "peel",
    "skirmish",
    "splitpush",
    "scaling",
    "chaos",
)

FEATURE_KEYS: tuple[str, ...] = (
    *(f"roles.{role}" for role in ROLES),
    *(f"classes.{cls}" for cls in CLASSES),
    *(f"damage.{dmg}" for dmg in DAMAGE_TYPES),
    *(f"style.{style}" for style in STYLES),
    "mobility",
    "difficulty",
)
FEATURE_INDEX: dict[str, int] = {key: idx for idx, key in enumerate(FEATURE_KEYS)}


def _validate_unit_mapping(mapping: dict[str, float], field_name: str) -> dict[str, float]:
    for key, value in mapping.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{field_name}.{key} must be between 0.0 and 1.0, got {value}")
    return mapping


class ChampionProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    champion_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    roles: dict[RoleName, float] = Field(default_factory=dict)
    classes: dict[ClassName, float] = Field(default_factory=dict)
    damage: dict[DamageType, float] = Field(default_factory=dict)
    style: dict[StyleName, float] = Field(default_factory=dict)
    mobility: float = Field(ge=0.0, le=1.0)
    difficulty: float = Field(ge=0.0, le=1.0)
    off_meta: bool = False
    tags: tuple[str, ...] = ()
    needs_review: bool = False

    @field_validator("roles", "classes", "damage", "style")
    @classmethod
    def check_unit_values(cls, value: dict[str, float], info: object) -> dict[str, float]:
        field_name = getattr(info, "field_name", "value")
        return _validate_unit_mapping(value, str(field_name))

    @property
    def is_complete(self) -> bool:
        return (
            not self.needs_review
            and bool(self.roles)
            and bool(self.classes)
            and bool(self.damage)
            and bool(self.style)
        )


class FeatureRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    feature: str
    min: float | None = Field(default=None, ge=0.0, le=1.0)
    max: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("feature")
    @classmethod
    def check_known_feature(cls, value: str) -> str:
        if value not in FEATURE_INDEX:
            raise ValueError(f"Unknown feature key: {value}")
        return value

    @model_validator(mode="after")
    def check_bounds(self) -> FeatureRequirement:
        if self.min is None and self.max is None:
            raise ValueError("FeatureRequirement must specify min, max, or both")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("FeatureRequirement min cannot exceed max")
        return self


class ArchetypePalette(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    bg: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    accent: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")


class WeightVector(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    roles: dict[RoleName, float] = Field(default_factory=dict)
    classes: dict[ClassName, float] = Field(default_factory=dict)
    damage: dict[DamageType, float] = Field(default_factory=dict)
    style: dict[StyleName, float] = Field(default_factory=dict)
    mobility: float | None = Field(default=None, ge=0.0, le=1.0)
    difficulty: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("roles", "classes", "damage", "style")
    @classmethod
    def check_unit_values(cls, value: dict[str, float], info: object) -> dict[str, float]:
        field_name = getattr(info, "field_name", "value")
        return _validate_unit_mapping(value, str(field_name))

    def to_flat_dict(self) -> dict[str, float]:
        flat: dict[str, float] = {}
        for role, weight in self.roles.items():
            flat[f"roles.{role}"] = weight
        for cls_name, weight in self.classes.items():
            flat[f"classes.{cls_name}"] = weight
        for dmg, weight in self.damage.items():
            flat[f"damage.{dmg}"] = weight
        for style_name, weight in self.style.items():
            flat[f"style.{style_name}"] = weight
        if self.mobility is not None:
            flat["mobility"] = self.mobility
        if self.difficulty is not None:
            flat["difficulty"] = self.difficulty
        return flat


class ArchetypeDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9_]+$")
    weight_vector: WeightVector = Field(default_factory=WeightVector)
    requires: tuple[FeatureRequirement, ...] = ()
    signature_champions: tuple[str, ...] = ()
    rarity_hint: Literal["common", "uncommon", "rare"] = "common"
    palette: ArchetypePalette
    fallback_kind: Literal["none", "chaotic", "small_pool"] = "none"
    score_bias: float = Field(default=0.0, ge=-0.25, le=0.25)

    @model_validator(mode="after")
    def check_regular_archetype_fields(self) -> ArchetypeDefinition:
        if self.fallback_kind == "none":
            weights = self.weight_vector.to_flat_dict()
            if not any(weight > 0.0 for weight in weights.values()):
                raise ValueError(f"Archetype '{self.id}' must define at least one positive weight")
            if not self.signature_champions:
                raise ValueError(
                    f"Archetype '{self.id}' must define at least one signature champion"
                )
        return self


class ArchetypeCopy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    archetype_id: str = Field(pattern=r"^[a-z0-9_]+$")
    title: str = Field(min_length=1)
    subtitle: str = Field(min_length=1)
    lines: tuple[str, ...] = Field(min_length=1)
    roast_lines: tuple[str, ...] = ()

    @field_validator("lines", "roast_lines")
    @classmethod
    def check_non_empty_lines(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for line in value:
            if not line.strip():
                raise ValueError("Copy lines must not contain blank strings")
        return value


class TraitCopy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    trait_id: TraitId
    label: str = Field(min_length=1)
    lines: tuple[str, ...] = Field(min_length=1)

    @field_validator("lines")
    @classmethod
    def check_non_empty_lines(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for line in value:
            if not line.strip():
                raise ValueError("Trait copy lines must not contain blank strings")
        return value


class CopyBank(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    locale: Locale
    archetypes: dict[str, ArchetypeCopy] = Field(default_factory=dict)
    traits: dict[TraitId, TraitCopy] = Field(default_factory=dict)


class ManifestChampion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    champion_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    ddragon_tags: tuple[str, ...] = ()


class DataDragonManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str = Field(min_length=1)
    champions: tuple[ManifestChampion, ...]


@dataclass(frozen=True)
class ContentBundle:
    champions: Mapping[str, ChampionProfile]
    champions_by_numeric_id: Mapping[int, ChampionProfile]
    archetypes: tuple[ArchetypeDefinition, ...]
    archetypes_by_id: Mapping[str, ArchetypeDefinition]
