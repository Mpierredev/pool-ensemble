from __future__ import annotations

from pool_ensemble.domain.classifier import Classifier, classify_pool
from pool_ensemble.domain.exceptions import (
    DomainError,
    EmptyPoolError,
    InvalidContentError,
    UnknownChampionError,
)
from pool_ensemble.domain.features import FeatureExtractor, extract_features
from pool_ensemble.domain.models import (
    ArchetypeScore,
    ChampionPool,
    ClassificationResult,
    FeatureVector,
    MasteryEntry,
    PoolAnalysis,
    WeightedChampion,
)
from pool_ensemble.domain.pipeline import analyze_pool
from pool_ensemble.domain.pool import PoolBuilder, build_pool
from pool_ensemble.domain.traits import TraitDetector, detect_traits

__all__ = [
    "ArchetypeScore",
    "ChampionPool",
    "ClassificationResult",
    "Classifier",
    "DomainError",
    "EmptyPoolError",
    "FeatureExtractor",
    "FeatureVector",
    "InvalidContentError",
    "MasteryEntry",
    "PoolAnalysis",
    "PoolBuilder",
    "TraitDetector",
    "UnknownChampionError",
    "WeightedChampion",
    "analyze_pool",
    "build_pool",
    "classify_pool",
    "detect_traits",
    "extract_features",
]
