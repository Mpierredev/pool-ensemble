from __future__ import annotations

from typing import TYPE_CHECKING

from pool_ensemble.content.schemas import FEATURE_INDEX, FEATURE_KEYS
from pool_ensemble.domain.exceptions import EmptyPoolError, UnknownChampionError
from pool_ensemble.domain.models import ChampionPool, FeatureVector

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pool_ensemble.content.schemas import ChampionProfile


def _clamp_unit(value: float) -> float:
    return min(1.0, max(0.0, value))


def extract_features(
    pool: ChampionPool,
    champions: Mapping[str, ChampionProfile],
) -> FeatureVector:
    """Compute the weighted feature vector across all dimensions for a champion pool."""
    if not pool.entries:
        raise EmptyPoolError("Cannot extract features from an empty pool")

    totals = [0.0] * len(FEATURE_KEYS)
    for entry in pool.entries:
        profile = champions.get(entry.champion_id)
        if profile is None:
            raise UnknownChampionError(f"Unknown champion in pool: {entry.champion_id}")

        weight = entry.weight
        for role, score in profile.roles.items():
            totals[FEATURE_INDEX[f"roles.{role}"]] += weight * score
        for cls_name, score in profile.classes.items():
            totals[FEATURE_INDEX[f"classes.{cls_name}"]] += weight * score
        for dmg, score in profile.damage.items():
            totals[FEATURE_INDEX[f"damage.{dmg}"]] += weight * score
        for style_name, score in profile.style.items():
            totals[FEATURE_INDEX[f"style.{style_name}"]] += weight * score
        totals[FEATURE_INDEX["mobility"]] += weight * profile.mobility
        totals[FEATURE_INDEX["difficulty"]] += weight * profile.difficulty

    return FeatureVector(values=tuple(_clamp_unit(value) for value in totals))


class FeatureExtractor:
    def extract(
        self,
        pool: ChampionPool,
        champions: Mapping[str, ChampionProfile],
    ) -> FeatureVector:
        return extract_features(pool, champions)
