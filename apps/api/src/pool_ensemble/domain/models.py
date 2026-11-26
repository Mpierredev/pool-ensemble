from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from pool_ensemble.content.schemas import FEATURE_INDEX, FEATURE_KEYS, TraitId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class MasteryEntry:
    champion_id: str
    points: int
    last_play_time: datetime


@dataclass(frozen=True)
class WeightedChampion:
    champion_id: str
    weight: float
    points: int


@dataclass(frozen=True)
class ChampionPool:
    entries: tuple[WeightedChampion, ...]


@dataclass(frozen=True)
class FeatureVector:
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.values) != len(FEATURE_KEYS):
            raise ValueError(
                f"FeatureVector expects {len(FEATURE_KEYS)} values, got {len(self.values)}"
            )

    def get(self, feature: str) -> float:
        idx = FEATURE_INDEX.get(feature)
        if idx is None:
            raise KeyError(f"Unknown feature key: {feature}")
        return self.values[idx]

    def to_dict(self) -> dict[str, float]:
        return dict(zip(FEATURE_KEYS, self.values, strict=True))

    def to_numpy(self) -> NDArray[np.float64]:
        return np.array(self.values, dtype=np.float64)


@dataclass(frozen=True)
class ArchetypeScore:
    archetype_id: str
    score: float
    percentage: float


@dataclass(frozen=True)
class ClassificationResult:
    primary: ArchetypeScore
    secondary: ArchetypeScore | None
    all_scores: tuple[ArchetypeScore, ...]


@dataclass(frozen=True)
class PoolAnalysis:
    pool: ChampionPool
    features: FeatureVector
    classification: ClassificationResult
    traits: tuple[TraitId, ...]
