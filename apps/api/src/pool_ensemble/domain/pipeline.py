from __future__ import annotations

from typing import TYPE_CHECKING

from pool_ensemble.domain.classifier import classify_pool
from pool_ensemble.domain.features import extract_features
from pool_ensemble.domain.models import PoolAnalysis
from pool_ensemble.domain.pool import build_pool
from pool_ensemble.domain.traits import detect_traits

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from pool_ensemble.content.schemas import ContentBundle
    from pool_ensemble.domain.models import MasteryEntry


def analyze_pool(
    entries: Sequence[MasteryEntry],
    content: ContentBundle,
    now: datetime,
) -> PoolAnalysis:
    """Run the full pure domain pipeline from mastery entries to classification and traits."""
    pool = build_pool(entries, content.champions, now)
    features = extract_features(pool, content.champions)
    classification = classify_pool(pool, features, content.archetypes)
    traits = detect_traits(pool, features, content.champions)
    return PoolAnalysis(
        pool=pool,
        features=features,
        classification=classification,
        traits=traits,
    )
