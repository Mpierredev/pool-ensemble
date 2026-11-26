from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from pool_ensemble.content.loader import load_champions
from pool_ensemble.domain import (
    ChampionPool,
    MasteryEntry,
    TraitDetector,
    UnknownChampionError,
    WeightedChampion,
    build_pool,
    detect_traits,
    extract_features,
)

REPO_CHAMPIONS_DIR = Path(__file__).resolve().parents[3] / "data" / "champions"
NOW = datetime(2026, 11, 20, 12, 0, 0, tzinfo=UTC)


def test_detect_one_trick_trait_on_single_and_heavy_main_pool() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    single_pool = build_pool([MasteryEntry("Ahri", 200_000, NOW)], champions, NOW)
    single_features = extract_features(single_pool, champions)

    assert "one_trick" in detect_traits(single_pool, single_features, champions)

    skewed_pool = ChampionPool(
        entries=(
            WeightedChampion("Ahri", 0.70, 500_000),
            WeightedChampion("Lux", 0.30, 50_000),
        )
    )
    skewed_features = extract_features(skewed_pool, champions)
    assert "one_trick" in TraitDetector().detect(skewed_pool, skewed_features, champions)


def test_detect_wide_pool_and_off_meta_traits() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    pool = ChampionPool(
        entries=(
            WeightedChampion("Teemo", 0.25, 100_000),
            WeightedChampion("Singed", 0.20, 80_000),
            WeightedChampion("Shaco", 0.15, 60_000),
            WeightedChampion("Bard", 0.15, 60_000),
            WeightedChampion("Ivern", 0.15, 60_000),
            WeightedChampion("Zilean", 0.10, 40_000),
        )
    )
    features = extract_features(pool, champions)
    traits = detect_traits(pool, features, champions)

    assert "wide_pool" in traits
    assert "off_meta" in traits


def test_detect_single_role_and_all_roles_traits() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)

    single_role_pool = build_pool(
        [
            MasteryEntry("Jinx", 120_000, NOW - timedelta(days=1)),
            MasteryEntry("Caitlyn", 100_000, NOW - timedelta(days=2)),
            MasteryEntry("Aphelios", 80_000, NOW - timedelta(days=3)),
        ],
        champions,
        NOW,
    )
    single_role_features = extract_features(single_role_pool, champions)
    single_role_traits = detect_traits(single_role_pool, single_role_features, champions)
    assert "single_role" in single_role_traits
    assert "all_roles" not in single_role_traits

    all_roles_pool = ChampionPool(
        entries=(
            WeightedChampion("Darius", 0.2, 50_000),
            WeightedChampion("Vi", 0.2, 50_000),
            WeightedChampion("Ahri", 0.2, 50_000),
            WeightedChampion("Jinx", 0.2, 50_000),
            WeightedChampion("Janna", 0.2, 50_000),
        )
    )
    all_roles_features = extract_features(all_roles_pool, champions)
    all_roles_traits = detect_traits(all_roles_pool, all_roles_features, champions)
    assert "all_roles" in all_roles_traits
    assert "single_role" not in all_roles_traits


def test_detect_mobility_traits() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)

    slow_pool = ChampionPool(
        entries=(
            WeightedChampion("Xerath", 0.5, 50_000),
            WeightedChampion("Velkoz", 0.5, 50_000),
        )
    )
    slow_features = extract_features(slow_pool, champions)
    assert "low_mobility" in detect_traits(slow_pool, slow_features, champions)

    fast_pool = ChampionPool(
        entries=(
            WeightedChampion("Akali", 0.5, 50_000),
            WeightedChampion("Katarina", 0.5, 50_000),
        )
    )
    fast_features = extract_features(fast_pool, champions)
    assert "high_mobility" in detect_traits(fast_pool, fast_features, champions)


def test_detect_traits_raises_on_unknown_champion() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    valid_pool = ChampionPool(entries=(WeightedChampion("Ahri", 1.0, 50_000),))
    features = extract_features(valid_pool, champions)

    with pytest.raises(UnknownChampionError):
        detect_traits(
            ChampionPool(entries=(WeightedChampion("MissingChamp", 1.0, 50_000),)),
            features,
            champions,
        )
