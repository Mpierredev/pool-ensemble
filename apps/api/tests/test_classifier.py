from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from pool_ensemble.content.loader import load_content_bundle
from pool_ensemble.domain import (
    ChampionPool,
    Classifier,
    EmptyPoolError,
    InvalidContentError,
    MasteryEntry,
    WeightedChampion,
    analyze_pool,
    classify_pool,
    extract_features,
)

REPO_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
NOW = datetime(2026, 11, 20, 12, 0, 0, tzinfo=UTC)


def _entries_for(champion_ids: list[str]) -> list[MasteryEntry]:
    return [
        MasteryEntry(
            champion_id=cid,
            points=140_000 - idx * 10_000,
            last_play_time=NOW - timedelta(days=idx + 1),
        )
        for idx, cid in enumerate(champion_ids)
    ]


@pytest.mark.parametrize(
    ("champion_ids", "expected_archetype"),
    [
        (["Janna", "Lulu", "Soraka", "Nami"], "sitcom_suportes"),
        (["Ahri", "Syndra", "Lux", "Annie"], "anime_magos"),
        (["Zed", "Talon", "Akali", "Katarina"], "boyband_assassinos"),
        (["Vi", "JarvanIV", "Diana", "Nocturne"], "terror_divers"),
        (["Jinx", "Kaisa", "Caitlyn", "Aphelios"], "novela_marksmen"),
        (["Ornn", "Leona", "Nautilus", "Braum"], "reality_tanks"),
        (["Darius", "Aatrox", "Sett", "Mordekaiser"], "western_duelistas"),
        (["Shaco", "Teemo", "Singed", "Heimerdinger"], "circo_troll_picks"),
        (["Viego", "Graves", "Kindred", "Lillia"], "documentario_selvas"),
        (["Yorick", "Tryndamere", "Nasus", "Trundle"], "faroeste_splitpushers"),
        (["Orianna", "Viktor", "Azir", "Anivia"], "orquestra_controle"),
    ],
)
def test_synthetic_pure_pools_classify_into_expected_archetype(
    champion_ids: list[str],
    expected_archetype: str,
) -> None:
    content = load_content_bundle(REPO_DATA_DIR)
    analysis = analyze_pool(_entries_for(champion_ids), content, NOW)

    assert analysis.classification.primary.archetype_id == expected_archetype


def test_mixed_pool_returns_secondary_with_normalized_percentages() -> None:
    content = load_content_bundle(REPO_DATA_DIR)
    entries = [
        MasteryEntry("Janna", 120_000, NOW - timedelta(days=2)),
        MasteryEntry("Lulu", 100_000, NOW - timedelta(days=3)),
        MasteryEntry("Orianna", 95_000, NOW - timedelta(days=4)),
        MasteryEntry("Viktor", 85_000, NOW - timedelta(days=5)),
    ]

    analysis = analyze_pool(entries, content, NOW)
    result = analysis.classification

    assert result.secondary is not None
    assert math.isclose(
        result.primary.percentage + result.secondary.percentage,
        100.0,
        abs_tol=0.1,
    )


def test_small_pool_returns_estreia_temporada() -> None:
    content = load_content_bundle(REPO_DATA_DIR)

    single = analyze_pool(_entries_for(["Janna"]), content, NOW)
    pair = analyze_pool(_entries_for(["Janna", "Lulu"]), content, NOW)

    assert single.classification.primary.archetype_id == "estreia_temporada"
    assert single.classification.secondary is None
    assert "one_trick" in single.traits

    assert pair.classification.primary.archetype_id == "estreia_temporada"
    assert pair.classification.secondary is None


def test_unfocused_pool_falls_back_to_elenco_caotico() -> None:
    content = load_content_bundle(REPO_DATA_DIR)
    entries = _entries_for(["Garen", "Soraka", "Caitlyn", "Zed", "Anivia", "Braum"])

    analysis = analyze_pool(entries, content, NOW)

    assert analysis.classification.primary.archetype_id == "elenco_caotico"
    assert analysis.classification.secondary is None


def test_classification_is_deterministic_and_order_invariant() -> None:
    content = load_content_bundle(REPO_DATA_DIR)
    entries = _entries_for(["Ahri", "Syndra", "Orianna", "Viktor", "Janna"])

    first = analyze_pool(entries, content, NOW)
    second = analyze_pool(list(reversed(entries)), content, NOW)

    assert first.classification == second.classification


def test_classifier_error_cases() -> None:
    content = load_content_bundle(REPO_DATA_DIR)
    pool = ChampionPool(entries=(WeightedChampion("Ahri", 1.0, 50_000),))
    features = extract_features(pool, content.champions)

    with pytest.raises(EmptyPoolError):
        Classifier().classify(ChampionPool(entries=()), features, content.archetypes)

    no_fallbacks = [arch for arch in content.archetypes if arch.fallback_kind == "none"]
    with pytest.raises(InvalidContentError):
        classify_pool(pool, features, no_fallbacks)
