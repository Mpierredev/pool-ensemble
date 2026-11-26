from __future__ import annotations

import math
from pathlib import Path

import pytest

from pool_ensemble.content.loader import load_champions
from pool_ensemble.domain import (
    ChampionPool,
    EmptyPoolError,
    FeatureExtractor,
    UnknownChampionError,
    WeightedChampion,
    extract_features,
)

REPO_CHAMPIONS_DIR = Path(__file__).resolve().parents[3] / "data" / "champions"


def test_extract_features_computes_weighted_average() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    pool = ChampionPool(
        entries=(
            WeightedChampion("Janna", 0.6, 120_000),
            WeightedChampion("Soraka", 0.4, 80_000),
        )
    )

    features = FeatureExtractor().extract(pool, champions)

    assert math.isclose(features.get("roles.support"), 1.0, rel_tol=1e-9)
    assert math.isclose(features.get("classes.enchanter"), 1.0, rel_tol=1e-9)
    expected_mobility = 0.6 * champions["Janna"].mobility + 0.4 * champions["Soraka"].mobility
    assert math.isclose(features.get("mobility"), expected_mobility, rel_tol=1e-9)

    as_dict = features.to_dict()
    assert all(0.0 <= value <= 1.0 for value in as_dict.values())
    assert features.to_numpy().shape == (30,)


def test_extract_features_is_order_invariant() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    pool_a = ChampionPool(
        entries=(
            WeightedChampion("Ahri", 0.5, 100_000),
            WeightedChampion("Vi", 0.3, 60_000),
            WeightedChampion("Jinx", 0.2, 40_000),
        )
    )
    pool_b = ChampionPool(entries=tuple(reversed(pool_a.entries)))

    features_a = extract_features(pool_a, champions)
    features_b = extract_features(pool_b, champions)

    for key, val_a in features_a.to_dict().items():
        assert math.isclose(val_a, features_b.get(key), rel_tol=1e-9)


def test_extract_features_raises_on_empty_or_unknown_champion() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)

    with pytest.raises(EmptyPoolError):
        extract_features(ChampionPool(entries=()), champions)

    with pytest.raises(UnknownChampionError):
        extract_features(
            ChampionPool(entries=(WeightedChampion("MissingChamp", 1.0, 10_000),)),
            champions,
        )
