from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from pool_ensemble.content.loader import load_champions
from pool_ensemble.domain import EmptyPoolError, MasteryEntry, PoolBuilder, build_pool

REPO_CHAMPIONS_DIR = Path(__file__).resolve().parents[3] / "data" / "champions"
NOW = datetime(2026, 11, 20, 12, 0, 0, tzinfo=UTC)


def test_build_pool_normalizes_weights_to_one() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    entries = [
        MasteryEntry("Janna", 120_000, NOW - timedelta(days=5)),
        MasteryEntry("Lulu", 90_000, NOW - timedelta(days=12)),
        MasteryEntry("Soraka", 60_000, NOW - timedelta(days=30)),
        MasteryEntry("Nami", 40_000, NOW - timedelta(days=60)),
    ]

    pool = PoolBuilder().build(entries, champions, NOW)

    assert len(pool.entries) == 4
    assert math.isclose(sum(entry.weight for entry in pool.entries), 1.0, rel_tol=1e-9)
    assert [entry.champion_id for entry in pool.entries] == ["Janna", "Lulu", "Soraka", "Nami"]


def test_build_pool_recency_decay_can_flip_order() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    entries = [
        MasteryEntry("Ahri", 200_000, NOW - timedelta(days=180)),
        MasteryEntry("Lux", 80_000, NOW - timedelta(days=1)),
    ]

    pool = build_pool(entries, champions, NOW)

    assert pool.entries[0].champion_id == "Lux"
    assert pool.entries[1].champion_id == "Ahri"


def test_build_pool_caps_at_eight_and_drops_below_two_percent() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    champ_ids = [
        "Janna",
        "Lulu",
        "Soraka",
        "Nami",
        "Milio",
        "Sona",
        "Seraphine",
        "Renata",
        "Karma",
        "Taric",
    ]
    entries = [
        MasteryEntry(
            cid,
            150_000 if idx < 6 else 50_000,
            NOW - timedelta(days=1 if idx < 8 else 600),
        )
        for idx, cid in enumerate(champ_ids)
    ]
    entries.append(MasteryEntry("Blitzcrank", 100, NOW - timedelta(days=900)))

    pool = build_pool(entries, champions, NOW)

    assert len(pool.entries) <= 8
    assert all(entry.weight >= 0.02 for entry in pool.entries)
    assert "Blitzcrank" not in {entry.champion_id for entry in pool.entries}
    assert math.isclose(sum(entry.weight for entry in pool.entries), 1.0, rel_tol=1e-9)


def test_build_pool_is_order_invariant_and_deduplicates() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    entries_a = [
        MasteryEntry("Janna", 100_000, NOW - timedelta(days=3)),
        MasteryEntry("Janna", 50_000, NOW - timedelta(days=20)),
        MasteryEntry("Lulu", 80_000, NOW - timedelta(days=5)),
        MasteryEntry("Nami", 60_000, NOW - timedelta(days=8)),
    ]
    entries_b = list(reversed(entries_a))

    pool_a = build_pool(entries_a, champions, NOW)
    pool_b = build_pool(entries_b, champions, NOW)

    assert pool_a == pool_b
    assert len(pool_a.entries) == 3


def test_build_pool_handles_naive_datetimes_and_unknown_or_zero_points() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)
    naive_now = datetime(2026, 11, 20, 12, 0, 0)
    entries = [
        MasteryEntry("UnknownChamp", 100_000, naive_now),
        MasteryEntry("Lux", 0, naive_now),
        MasteryEntry("Ahri", 50_000, naive_now - timedelta(days=4)),
    ]

    pool = build_pool(entries, champions, naive_now)
    assert len(pool.entries) == 1
    assert pool.entries[0].champion_id == "Ahri"
    assert pool.entries[0].weight == 1.0


def test_build_pool_raises_on_empty_or_invalid_entries() -> None:
    champions = load_champions(REPO_CHAMPIONS_DIR)

    with pytest.raises(EmptyPoolError):
        build_pool([], champions, NOW)

    with pytest.raises(EmptyPoolError):
        build_pool([MasteryEntry("Missing", 50_000, NOW)], champions, NOW)
