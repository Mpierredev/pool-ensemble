from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pool_ensemble.domain.exceptions import EmptyPoolError
from pool_ensemble.domain.models import ChampionPool, MasteryEntry, WeightedChampion

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from pool_ensemble.content.schemas import ChampionProfile

RECENCY_DECAY_DAYS = 180.0
MAX_POOL_SIZE = 8
MIN_CHAMPION_WEIGHT = 0.02


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def build_pool(
    entries: Sequence[MasteryEntry],
    champions: Mapping[str, ChampionProfile],
    now: datetime,
    *,
    decay_days: float = RECENCY_DECAY_DAYS,
    max_size: int = MAX_POOL_SIZE,
    min_weight: float = MIN_CHAMPION_WEIGHT,
) -> ChampionPool:
    """Build a normalized, recency-weighted champion pool from mastery entries."""
    if decay_days <= 0.0:
        raise ValueError("decay_days must be positive")
    if max_size <= 0:
        raise ValueError("max_size must be positive")

    deduped: dict[str, MasteryEntry] = {}
    for entry in entries:
        if entry.points <= 0 or entry.champion_id not in champions:
            continue
        existing = deduped.get(entry.champion_id)
        if existing is None or (entry.points, _to_utc(entry.last_play_time)) > (
            existing.points,
            _to_utc(existing.last_play_time),
        ):
            deduped[entry.champion_id] = entry

    if not deduped:
        raise EmptyPoolError("No valid champion mastery entries found for pool")

    now_utc = _to_utc(now)
    scored: list[tuple[str, int, float]] = []
    for champion_id, entry in deduped.items():
        days_since = max(0.0, (now_utc - _to_utc(entry.last_play_time)).total_seconds() / 86400.0)
        raw_weight = math.log1p(entry.points) * math.exp(-days_since / decay_days)
        scored.append((champion_id, entry.points, raw_weight))

    scored.sort(key=lambda item: (-item[2], item[0]))
    top_scored = scored[:max_size]

    initial_total = sum(item[2] for item in top_scored)
    if initial_total <= 0.0:
        raise EmptyPoolError("Computed weights sum to zero")

    kept = [
        (champion_id, points, raw_weight)
        for idx, (champion_id, points, raw_weight) in enumerate(top_scored)
        if idx == 0 or (raw_weight / initial_total) >= min_weight
    ]

    kept_total = sum(item[2] for item in kept)
    weighted = tuple(
        WeightedChampion(
            champion_id=champion_id,
            weight=raw_weight / kept_total,
            points=points,
        )
        for champion_id, points, raw_weight in kept
    )
    return ChampionPool(entries=weighted)


class PoolBuilder:
    def __init__(
        self,
        *,
        decay_days: float = RECENCY_DECAY_DAYS,
        max_size: int = MAX_POOL_SIZE,
        min_weight: float = MIN_CHAMPION_WEIGHT,
    ) -> None:
        self.decay_days = decay_days
        self.max_size = max_size
        self.min_weight = min_weight

    def build(
        self,
        entries: Sequence[MasteryEntry],
        champions: Mapping[str, ChampionProfile],
        now: datetime,
    ) -> ChampionPool:
        return build_pool(
            entries,
            champions,
            now,
            decay_days=self.decay_days,
            max_size=self.max_size,
            min_weight=self.min_weight,
        )
