from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from pydantic import ValidationError

from pool_ensemble.content.schemas import (
    ArchetypeCopy,
    ArchetypeDefinition,
    ChampionProfile,
    ContentBundle,
    CopyBank,
    DataDragonManifest,
    Locale,
    TraitCopy,
    TraitId,
)
from pool_ensemble.domain.exceptions import InvalidContentError

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

ContentValidationError = InvalidContentError


def _load_yaml_object(path: Path) -> object:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InvalidContentError(f"Failed to read YAML file {path}: {exc}") from exc

    try:
        data: object = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise InvalidContentError(f"Invalid YAML syntax in {path}: {exc}") from exc

    if data is None:
        raise InvalidContentError(f"Empty YAML file: {path}")
    return data


def load_manifest(path: Path) -> DataDragonManifest:
    """Load and validate the Data Dragon champion manifest."""
    if not path.is_file():
        raise InvalidContentError(f"Data Dragon manifest not found: {path}")
    raw = _load_yaml_object(path)
    try:
        return DataDragonManifest.model_validate(raw)
    except ValidationError as exc:
        raise InvalidContentError(f"Invalid manifest schema in {path}: {exc}") from exc


def load_champions(
    champions_dir: Path,
    *,
    require_complete: bool = True,
) -> dict[str, ChampionProfile]:
    """Load all champion profiles from YAML files and validate completeness."""
    if not champions_dir.is_dir():
        raise InvalidContentError(f"Champions directory not found: {champions_dir}")

    yaml_files = sorted(champions_dir.glob("*.yaml"))
    if not yaml_files:
        raise InvalidContentError(f"No champion YAML files found in {champions_dir}")

    champions: dict[str, ChampionProfile] = {}
    seen_numeric_ids: dict[int, str] = {}

    for path in yaml_files:
        raw = _load_yaml_object(path)
        try:
            profile = ChampionProfile.model_validate(raw)
        except ValidationError as exc:
            raise InvalidContentError(f"Invalid champion schema in {path}: {exc}") from exc

        expected_stem = profile.id.lower()
        if path.stem != expected_stem:
            raise InvalidContentError(
                f"Champion filename {path.name} must match {expected_stem}.yaml"
            )
        if profile.id in champions:
            raise InvalidContentError(f"Duplicate champion id: {profile.id}")
        if profile.champion_id in seen_numeric_ids:
            other = seen_numeric_ids[profile.champion_id]
            raise InvalidContentError(
                f"Duplicate numeric champion_id {profile.champion_id} ({other} and {profile.id})"
            )
        if require_complete and not profile.is_complete:
            raise InvalidContentError(f"Incomplete champion profile: {profile.id}")

        champions[profile.id] = profile
        seen_numeric_ids[profile.champion_id] = profile.id

    return champions


def load_archetypes(
    archetypes_dir: Path,
    champions: Mapping[str, ChampionProfile],
) -> tuple[ArchetypeDefinition, ...]:
    """Load all archetype definitions and verify signature champion references."""
    if not archetypes_dir.is_dir():
        raise InvalidContentError(f"Archetypes directory not found: {archetypes_dir}")

    yaml_files = sorted(archetypes_dir.glob("*.yaml"))
    if not yaml_files:
        raise InvalidContentError(f"No archetype YAML files found in {archetypes_dir}")

    archetypes: list[ArchetypeDefinition] = []
    seen_ids: set[str] = set()
    chaotic_count = 0
    small_pool_count = 0

    for path in yaml_files:
        raw = _load_yaml_object(path)
        try:
            archetype = ArchetypeDefinition.model_validate(raw)
        except ValidationError as exc:
            raise InvalidContentError(f"Invalid archetype schema in {path}: {exc}") from exc

        if path.stem != archetype.id:
            raise InvalidContentError(
                f"Archetype filename {path.name} must match {archetype.id}.yaml"
            )
        if archetype.id in seen_ids:
            raise InvalidContentError(f"Duplicate archetype id: {archetype.id}")

        for champ_id in archetype.signature_champions:
            if champ_id not in champions:
                raise InvalidContentError(
                    f"Archetype '{archetype.id}' references unknown signature champion '{champ_id}'"
                )

        if archetype.fallback_kind == "chaotic":
            chaotic_count += 1
        elif archetype.fallback_kind == "small_pool":
            small_pool_count += 1

        seen_ids.add(archetype.id)
        archetypes.append(archetype)

    if chaotic_count != 1:
        raise InvalidContentError(
            f"Expected exactly 1 chaotic fallback archetype, found {chaotic_count}"
        )
    if small_pool_count != 1:
        raise InvalidContentError(
            f"Expected exactly 1 small_pool fallback archetype, found {small_pool_count}"
        )

    return tuple(archetypes)


def load_copy_bank(copy_dir: Path, locale: Locale) -> CopyBank:
    """Load localized archetype and trait copy YAML files when present."""
    if not copy_dir.is_dir():
        raise InvalidContentError(f"Copy directory not found: {copy_dir}")

    archetypes: dict[str, ArchetypeCopy] = {}
    traits: dict[TraitId, TraitCopy] = {}

    traits_path = copy_dir / "traits.yaml"
    if traits_path.is_file():
        raw_traits = _load_yaml_object(traits_path)
        entries = raw_traits.get("traits") if isinstance(raw_traits, dict) else raw_traits
        if not isinstance(entries, list):
            raise InvalidContentError(f"Expected list of trait copy entries in {traits_path}")
        for entry in entries:
            try:
                trait_copy = TraitCopy.model_validate(entry)
            except ValidationError as exc:
                raise InvalidContentError(f"Invalid trait copy in {traits_path}: {exc}") from exc
            if trait_copy.trait_id in traits:
                raise InvalidContentError(f"Duplicate trait copy for {trait_copy.trait_id}")
            traits[trait_copy.trait_id] = trait_copy

    archetype_files = sorted(path for path in copy_dir.rglob("*.yaml") if path != traits_path)
    for path in archetype_files:
        raw_copy = _load_yaml_object(path)
        try:
            archetype_copy = ArchetypeCopy.model_validate(raw_copy)
        except ValidationError as exc:
            raise InvalidContentError(f"Invalid archetype copy in {path}: {exc}") from exc
        if archetype_copy.archetype_id in archetypes:
            raise InvalidContentError(f"Duplicate archetype copy for {archetype_copy.archetype_id}")
        archetypes[archetype_copy.archetype_id] = archetype_copy

    return CopyBank(locale=locale, archetypes=archetypes, traits=traits)


def load_content_bundle(
    data_dir: Path,
    *,
    require_complete: bool = True,
) -> ContentBundle:
    """Load champions and archetypes from a repository data directory."""
    champions = load_champions(data_dir / "champions", require_complete=require_complete)
    archetypes = load_archetypes(data_dir / "archetypes", champions)
    return ContentBundle(
        champions=champions,
        champions_by_numeric_id={profile.champion_id: profile for profile in champions.values()},
        archetypes=archetypes,
        archetypes_by_id={archetype.id: archetype for archetype in archetypes},
    )
