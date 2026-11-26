from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from pool_ensemble.content.schemas import FEATURE_INDEX, FEATURE_KEYS, ArchetypeDefinition
from pool_ensemble.domain.exceptions import EmptyPoolError, InvalidContentError
from pool_ensemble.domain.models import (
    ArchetypeScore,
    ChampionPool,
    ClassificationResult,
    FeatureVector,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

MIN_POOL_CHAMPIONS = 3
MIN_PRIMARY_SCORE = 0.42
MIN_SECONDARY_SCORE = 0.36
SECONDARY_MAX_GAP = 0.25
SIGNATURE_BONUS_MAX = 0.12
REQUIREMENT_PENALTY_BASE = 0.25
REQUIREMENT_PENALTY_SCALE = 0.60


def _build_target_vector(archetype: ArchetypeDefinition) -> NDArray[np.float64]:
    values = [0.0] * len(FEATURE_KEYS)
    for feature, weight in archetype.weight_vector.to_flat_dict().items():
        values[FEATURE_INDEX[feature]] = weight
    return np.array(values, dtype=np.float64)


def _cosine_similarity(
    left: np.ndarray[tuple[int], np.dtype[np.float64]],
    right: np.ndarray[tuple[int], np.dtype[np.float64]],
) -> float:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _requirement_penalty(archetype: ArchetypeDefinition, features: FeatureVector) -> float:
    penalty = 0.0
    for req in archetype.requires:
        value = features.get(req.feature)
        if req.min is not None and value < req.min:
            penalty += REQUIREMENT_PENALTY_BASE + REQUIREMENT_PENALTY_SCALE * (req.min - value)
        if req.max is not None and value > req.max:
            penalty += REQUIREMENT_PENALTY_BASE + REQUIREMENT_PENALTY_SCALE * (value - req.max)
    return penalty


def _find_fallbacks(
    archetypes: Sequence[ArchetypeDefinition],
) -> tuple[ArchetypeDefinition, ArchetypeDefinition]:
    chaotic: ArchetypeDefinition | None = None
    small_pool: ArchetypeDefinition | None = None
    for archetype in archetypes:
        if archetype.fallback_kind == "chaotic":
            if chaotic is not None:
                raise InvalidContentError("Multiple chaotic fallback archetypes defined")
            chaotic = archetype
        elif archetype.fallback_kind == "small_pool":
            if small_pool is not None:
                raise InvalidContentError("Multiple small_pool fallback archetypes defined")
            small_pool = archetype
    if chaotic is None or small_pool is None:
        raise InvalidContentError("Both chaotic and small_pool fallback archetypes are required")
    return chaotic, small_pool


def classify_pool(
    pool: ChampionPool,
    features: FeatureVector,
    archetypes: Sequence[ArchetypeDefinition],
) -> ClassificationResult:
    """Classify a weighted pool and its feature vector into primary and secondary archetypes."""
    if not pool.entries:
        raise EmptyPoolError("Cannot classify an empty pool")

    chaotic_fallback, small_pool_fallback = _find_fallbacks(archetypes)

    if len(pool.entries) < MIN_POOL_CHAMPIONS:
        primary = ArchetypeScore(
            archetype_id=small_pool_fallback.id,
            score=1.0,
            percentage=100.0,
        )
        return ClassificationResult(
            primary=primary,
            secondary=None,
            all_scores=(primary,),
        )

    player_vector = features.to_numpy()
    raw_scores: list[tuple[str, float]] = []
    for archetype in archetypes:
        if archetype.fallback_kind != "none":
            continue
        target_vector = _build_target_vector(archetype)
        cosine = _cosine_similarity(player_vector, target_vector)
        signature_set = set(archetype.signature_champions)
        signature_weight = sum(
            entry.weight for entry in pool.entries if entry.champion_id in signature_set
        )
        signature_bonus = SIGNATURE_BONUS_MAX * min(1.0, signature_weight)
        penalty = _requirement_penalty(archetype, features)
        score = min(1.0, max(0.0, cosine + signature_bonus - penalty + archetype.score_bias))
        raw_scores.append((archetype.id, score))

    raw_scores.sort(key=lambda item: (-item[1], item[0]))
    if not raw_scores or raw_scores[0][1] < MIN_PRIMARY_SCORE:
        best_raw = raw_scores[0][1] if raw_scores else 0.0
        primary = ArchetypeScore(
            archetype_id=chaotic_fallback.id,
            score=round(best_raw, 4),
            percentage=100.0,
        )
        ranked = tuple(
            ArchetypeScore(archetype_id=aid, score=round(val, 4), percentage=0.0)
            for aid, val in raw_scores
        )
        return ClassificationResult(primary=primary, secondary=None, all_scores=ranked)

    best_id, best_score = raw_scores[0]
    has_secondary = (
        len(raw_scores) >= 2
        and raw_scores[1][1] >= MIN_SECONDARY_SCORE
        and (best_score - raw_scores[1][1]) <= SECONDARY_MAX_GAP
    )

    if has_secondary:
        second_id, second_score = raw_scores[1]
        score_sum = best_score + second_score
        primary_pct = round(100.0 * best_score / score_sum, 1)
        secondary_pct = round(100.0 - primary_pct, 1)
        primary = ArchetypeScore(
            archetype_id=best_id,
            score=round(best_score, 4),
            percentage=primary_pct,
        )
        secondary_item = ArchetypeScore(
            archetype_id=second_id,
            score=round(second_score, 4),
            percentage=secondary_pct,
        )
        secondary: ArchetypeScore | None = secondary_item
        all_scores = (
            primary,
            secondary_item,
            *(
                ArchetypeScore(archetype_id=aid, score=round(val, 4), percentage=0.0)
                for aid, val in raw_scores[2:]
            ),
        )
    else:
        primary = ArchetypeScore(
            archetype_id=best_id,
            score=round(best_score, 4),
            percentage=100.0,
        )
        secondary = None
        all_scores = (
            primary,
            *(
                ArchetypeScore(archetype_id=aid, score=round(val, 4), percentage=0.0)
                for aid, val in raw_scores[1:]
            ),
        )

    return ClassificationResult(primary=primary, secondary=secondary, all_scores=all_scores)


class Classifier:
    def classify(
        self,
        pool: ChampionPool,
        features: FeatureVector,
        archetypes: Sequence[ArchetypeDefinition],
    ) -> ClassificationResult:
        return classify_pool(pool, features, archetypes)
