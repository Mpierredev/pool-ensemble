from __future__ import annotations

from typing import TYPE_CHECKING

from pool_ensemble.content.schemas import ROLES, TraitId
from pool_ensemble.domain.exceptions import UnknownChampionError
from pool_ensemble.domain.models import ChampionPool, FeatureVector

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pool_ensemble.content.schemas import ChampionProfile

ONE_TRICK_THRESHOLD = 0.55
WIDE_POOL_MIN_CHAMPIONS = 6
WIDE_POOL_MIN_WEIGHT = 0.05
OFF_META_THRESHOLD = 0.30
ALL_ROLES_MIN_WEIGHT = 0.08
SINGLE_ROLE_RATIO = 0.85
LOW_MOBILITY_THRESHOLD = 0.30
HIGH_MOBILITY_THRESHOLD = 0.72


def detect_traits(
    pool: ChampionPool,
    features: FeatureVector,
    champions: Mapping[str, ChampionProfile],
) -> tuple[TraitId, ...]:
    """Detect independent pool traits from champion weights and feature totals."""
    traits: list[TraitId] = []

    if pool.entries and pool.entries[0].weight >= ONE_TRICK_THRESHOLD:
        traits.append("one_trick")

    significant_count = sum(1 for entry in pool.entries if entry.weight >= WIDE_POOL_MIN_WEIGHT)
    if significant_count >= WIDE_POOL_MIN_CHAMPIONS:
        traits.append("wide_pool")

    off_meta_weight = 0.0
    for entry in pool.entries:
        profile = champions.get(entry.champion_id)
        if profile is None:
            raise UnknownChampionError(f"Unknown champion in pool: {entry.champion_id}")
        if profile.off_meta:
            off_meta_weight += entry.weight
    if off_meta_weight >= OFF_META_THRESHOLD:
        traits.append("off_meta")

    role_weights = [features.get(f"roles.{role}") for role in ROLES]
    all_roles = all(weight >= ALL_ROLES_MIN_WEIGHT for weight in role_weights)
    if all_roles:
        traits.append("all_roles")
    else:
        total_role_weight = sum(role_weights)
        if total_role_weight > 0.0 and max(role_weights) / total_role_weight >= SINGLE_ROLE_RATIO:
            traits.append("single_role")

    mobility = features.get("mobility")
    if mobility <= LOW_MOBILITY_THRESHOLD:
        traits.append("low_mobility")
    elif mobility >= HIGH_MOBILITY_THRESHOLD:
        traits.append("high_mobility")

    return tuple(traits)


class TraitDetector:
    def detect(
        self,
        pool: ChampionPool,
        features: FeatureVector,
        champions: Mapping[str, ChampionProfile],
    ) -> tuple[TraitId, ...]:
        return detect_traits(pool, features, champions)
