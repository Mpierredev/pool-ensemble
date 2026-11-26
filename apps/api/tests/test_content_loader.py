from __future__ import annotations

from pathlib import Path

import pytest

from pool_ensemble.content.loader import (
    load_archetypes,
    load_champions,
    load_content_bundle,
    load_copy_bank,
)
from pool_ensemble.domain.exceptions import InvalidContentError

REPO_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def _write_minimal_champion(
    path: Path,
    champ_id: str,
    numeric_id: int,
    *,
    review: bool = False,
) -> None:
    path.write_text(
        "\n".join(
            [
                f"id: {champ_id}",
                f"champion_id: {numeric_id}",
                f"name: {champ_id}",
                "roles: {mid: 1.0}",
                "classes: {mage: 1.0}",
                "damage: {magic: 1.0}",
                "style: {burst: 0.8}",
                "mobility: 0.5",
                "difficulty: 0.5",
                f"needs_review: {str(review).lower()}",
            ]
        ),
        encoding="utf-8",
    )


def _write_fallbacks(archetypes_dir: Path) -> None:
    (archetypes_dir / "elenco_caotico.yaml").write_text(
        "\n".join(
            [
                "id: elenco_caotico",
                "fallback_kind: chaotic",
                'palette: {bg: "#111111", accent: "#222222"}',
            ]
        ),
        encoding="utf-8",
    )
    (archetypes_dir / "estreia_temporada.yaml").write_text(
        "\n".join(
            [
                "id: estreia_temporada",
                "fallback_kind: small_pool",
                'palette: {bg: "#111111", accent: "#333333"}',
            ]
        ),
        encoding="utf-8",
    )


def test_load_repository_content_bundle() -> None:
    bundle = load_content_bundle(REPO_DATA_DIR, require_complete=True)

    assert len(bundle.champions) >= 170
    assert len(bundle.archetypes) == 13
    assert "Ahri" in bundle.champions
    assert bundle.champions_by_numeric_id[103].id == "Ahri"
    assert "sitcom_suportes" in bundle.archetypes_by_id


def test_load_champions_rejects_incomplete_profile(tmp_path: Path) -> None:
    champions_dir = tmp_path / "champions"
    champions_dir.mkdir()
    _write_minimal_champion(champions_dir / "ahri.yaml", "Ahri", 103, review=True)

    with pytest.raises(InvalidContentError, match="Incomplete champion"):
        load_champions(champions_dir, require_complete=True)


def test_load_champions_rejects_filename_mismatch(tmp_path: Path) -> None:
    champions_dir = tmp_path / "champions"
    champions_dir.mkdir()
    _write_minimal_champion(champions_dir / "wrong.yaml", "Ahri", 103)

    with pytest.raises(InvalidContentError, match=r"must match ahri\.yaml"):
        load_champions(champions_dir)


def test_load_champions_rejects_duplicate_numeric_id(tmp_path: Path) -> None:
    champions_dir = tmp_path / "champions"
    champions_dir.mkdir()
    _write_minimal_champion(champions_dir / "ahri.yaml", "Ahri", 103)
    _write_minimal_champion(champions_dir / "lux.yaml", "Lux", 103)

    with pytest.raises(InvalidContentError, match="Duplicate numeric champion_id"):
        load_champions(champions_dir)


def test_load_archetypes_rejects_unknown_signature(tmp_path: Path) -> None:
    champions_dir = tmp_path / "champions"
    archetypes_dir = tmp_path / "archetypes"
    champions_dir.mkdir()
    archetypes_dir.mkdir()
    _write_minimal_champion(champions_dir / "ahri.yaml", "Ahri", 103)
    _write_fallbacks(archetypes_dir)
    (archetypes_dir / "anime_magos.yaml").write_text(
        "\n".join(
            [
                "id: anime_magos",
                "weight_vector:",
                "  classes: {mage: 1.0}",
                "signature_champions: [MissingChamp]",
                'palette: {bg: "#111111", accent: "#444444"}',
            ]
        ),
        encoding="utf-8",
    )

    champions = load_champions(champions_dir)
    with pytest.raises(InvalidContentError, match="unknown signature champion"):
        load_archetypes(archetypes_dir, champions)


def test_load_archetypes_requires_both_fallbacks(tmp_path: Path) -> None:
    champions_dir = tmp_path / "champions"
    archetypes_dir = tmp_path / "archetypes"
    champions_dir.mkdir()
    archetypes_dir.mkdir()
    _write_minimal_champion(champions_dir / "ahri.yaml", "Ahri", 103)
    (archetypes_dir / "elenco_caotico.yaml").write_text(
        "\n".join(
            [
                "id: elenco_caotico",
                "fallback_kind: chaotic",
                'palette: {bg: "#111111", accent: "#222222"}',
            ]
        ),
        encoding="utf-8",
    )

    champions = load_champions(champions_dir)
    with pytest.raises(InvalidContentError, match="small_pool fallback"):
        load_archetypes(archetypes_dir, champions)


def test_load_copy_bank_reads_yaml_files(tmp_path: Path) -> None:
    copy_dir = tmp_path / "pt-BR"
    copy_dir.mkdir()
    (copy_dir / "traits.yaml").write_text(
        "\n".join(
            [
                "traits:",
                "  - trait_id: one_trick",
                "    label: Mono campeao",
                "    lines:",
                "      - Um campeao so.",
            ]
        ),
        encoding="utf-8",
    )
    (copy_dir / "sitcom_suportes.yaml").write_text(
        "\n".join(
            [
                "archetype_id: sitcom_suportes",
                "title: Sitcom de Suportes",
                "subtitle: Todo mundo se ajuda",
                "lines:",
                "  - Ninguem ganha a lane.",
            ]
        ),
        encoding="utf-8",
    )

    bank = load_copy_bank(copy_dir, "pt-BR")
    assert bank.archetypes["sitcom_suportes"].title == "Sitcom de Suportes"
    assert bank.traits["one_trick"].label == "Mono campeao"
